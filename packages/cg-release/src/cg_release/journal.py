"""Append-only event transactions with parent-bound, non-replacing reservations."""

import re
from collections.abc import Callable
from datetime import UTC, datetime

from cg_release.admission import Locator, Receipt
from cg_release.events import ControllerError
from cg_release.journal_models import Record, Store, digest, validate_event_header
from cg_release.journal_rules import retained_evidence, validate_transition
from cg_release.models import Request, canonical_bytes, load_record
from cg_release.verification import verification_guard


class Journal:
    """Read/replay every event and serialize request/reservation changes together."""

    def __init__(self, store: Store) -> None:
        """Use a protected store, e.g. Journal(store); no bootstrap is implicit."""
        self.store = store
        self.last_verified_records = {}

    def _read(self) -> tuple[str, list[dict], dict[str, Record]]:
        from cg_release.composition_journal import replay_composition
        from cg_release.github import decode_json
        from cg_release.queue import QueueCursor, validate_cursor

        check = verification_guard(self.store)
        anchor, history = self.store.history()
        check()
        parent, previous, records, events = anchor, "0" * 64, {}, []
        cursor = QueueCursor()
        recoveries, compositions = set(), {}
        repository_id = getattr(
            getattr(self.store, "policy", None), "repository_id", None
        )
        if not anchor:
            raise ControllerError(
                "E_JOURNAL", "Journal anchor or history bound is invalid."
            )
        try:
            for revision, transaction in enumerate(history, 1):
                check()
                event = decode_json(transaction.event.decode("utf-8"))
                claimed = validate_event_header(
                    event,
                    transaction,
                    revision=revision,
                    parent=parent,
                    previous=previous,
                    writer=self.store.writer,
                )
                entity = event["record"].get(
                    "directive", event["record"].get("request")
                )
                if entity is not None:
                    if (
                        repository_id is not None
                        and entity["repository_id"] != repository_id
                    ):
                        raise ValueError("journal cannot mix repository identities")
                    repository_id = entity["repository_id"]
                if event["record"].get("kind") == "recovery":
                    from cg_release.recovery_audit import validate_audit
                    from cg_release.recovery_models import RecoveryAudit

                    recovery = load_record(
                        RecoveryAudit, canonical_bytes(event["record"])
                    )
                    validate_audit(recovery, event["audit"], recoveries)
                elif event["record"].get("kind") == "queue":
                    next_cursor = load_record(
                        QueueCursor, canonical_bytes(event["record"])
                    )
                    validate_cursor(cursor, next_cursor, event["audit"])
                    cursor = next_cursor
                elif event["record"].get("kind") == "composition":
                    replay_composition(records, compositions, event)
                else:
                    record = load_record(Record, canonical_bytes(event["record"]))
                    validate_transition(records, record, event["audit"])
                    records[record.request_id] = record
                previous, parent = claimed, transaction.commit
                events.append(event)
        except (ValueError, KeyError, TypeError, UnicodeError, AttributeError):
            raise ControllerError(
                "E_JOURNAL", "Journal chain, writer, or transition is invalid."
            ) from None
        self.last_verified_records = records
        return parent, events, records

    def _change(
        self, request_id: str, change: Callable[[Record | None], tuple[Record, dict]]
    ) -> Record:
        for _attempt in range(3):
            parent, events, records = self._read()
            prior = records.get(request_id)
            record, audit = change(prior)
            if record == prior:
                return record
            try:
                validate_transition(records, record, audit)
            except ValueError:
                raise ControllerError(
                    "E_TRANSITION", "Request transition or audit evidence is invalid."
                ) from None
            event = {
                "schema_version": 1,
                "revision": len(events) + 1,
                "parent": parent,
                "previous": events[-1]["digest"] if events else "0" * 64,
                "record": record.model_dump(mode="json"),
                "audit": audit,
                "occurred_at": datetime.now(UTC).isoformat(),
            }
            event["digest"] = digest(event)
            try:
                self.store.append(parent, canonical_bytes(event), record)
            except ControllerError as error:
                # Always read back, including after a lost response. Only a proved
                # competing head allows rebuilding the transaction on a new parent.
                observed_parent, _, observed = self._read()
                if observed.get(request_id) == record:
                    return record
                if error.code != "E_CAS" or observed_parent == parent:
                    raise
                continue
            observed = self._read()[2].get(request_id)
            if observed != record:
                raise ControllerError(
                    "E_JOURNAL", "Written journal result did not read back."
                )
            return record
        raise ControllerError("E_CAS", "Journal contention exceeds retry bound.")

    def admit(
        self, request: Request, *, receipt: Receipt | None = None, revalidate=None
    ) -> Record:
        """Atomically seal inputs and reserve identity, e.g. journal.admit(request).

        Caller must first verify inbox, fresh proposal, protections, and authority.
        Raises ControllerError for a nonce or normalized-version conflict.
        """
        request = load_record(Request, canonical_bytes(request))
        locator = Locator.from_request(request).encode()

        def change(prior):
            if prior is not None:
                if prior.request != request:
                    raise ControllerError(
                        "E_REQUEST_CONFLICT", "Sealed inputs cannot change."
                    )
                return prior, {}
            if receipt is not None and (
                receipt.request != request or receipt.request_id != locator
            ):
                raise ControllerError(
                    "E_REQUEST_CONFLICT", "Receipt does not match admitted request."
                )
            if revalidate is not None:
                revalidate(request)
            return Record(request_id=locator, request=request, receipt=receipt), {
                "operation": "admit"
            }

        return self._change(locator, change)

    def get(self, request_id: str) -> Record:
        """Read one sealed identity, e.g. journal.get(locator); fail if absent."""
        Locator.decode(request_id)
        record = self._read()[2].get(request_id)
        if record is None:
            raise ControllerError(
                "E_REQUEST_MISSING", "No sealed journal record matches locator."
            )
        return record

    def records(self) -> list[Record]:
        """Return validated current records, e.g. for a bounded queue scan."""
        return list(self._read()[2].values())

    def reservations(self) -> list[str]:
        """Return active normalized identities, including failed/published requests."""
        return [
            r.request.version.split("+")[0]
            for r in self.records()
            if r.state != "abandoned"
        ]

    def events(self) -> list[dict]:
        """Return verified events, e.g. for checkpoint evidence; never raw logs."""
        return self._read()[1]

    def intent(self, request_id: str, operation: str, input_digest: str) -> Record:
        """Persist intent before one external write, e.g. intent(id, 'prepare', sha)."""
        prior = self.get(request_id)
        intent = {"operation": operation, "digest": input_digest}
        return self._change(
            request_id,
            lambda current: (
                current.model_copy(update={"intent": intent})
                if current == prior
                else self._stale(),
                intent,
            ),
        )

    def result(
        self,
        request_id: str,
        operation: str,
        input_digest: str,
        state: str,
        *,
        error_code: str | None = None,
        retryable: bool = False,
        evidence: dict | None = None,
    ) -> Record:
        """Persist reconciled results, e.g. result(id, op, sha, 'awaiting-review')."""
        if (
            type(retryable) is not bool
            or (
                state == "failed"
                and (
                    not isinstance(error_code, str)
                    or not re.fullmatch(r"E_[A-Z0-9_]+", error_code)
                )
            )
            or (state != "failed" and (error_code is not None or retryable))
        ):
            raise ControllerError(
                "E_TRANSITION", "Failure result requires a typed code and retryability."
            )
        prior = self.get(request_id)
        retained = retained_evidence(prior, operation, input_digest, evidence)
        record = load_record(
            Record,
            canonical_bytes(
                {
                    **prior.model_dump(mode="json"),
                    "state": state,
                    "checkpoint": prior.checkpoint if state == "failed" else operation,
                    "intent": None,
                    "error": error_code,
                    "failed_step": operation if state == "failed" else None,
                    "retryable": retryable,
                    "publication_started": prior.publication_started
                    or state == "publishing",
                    "published": prior.published or state == "published",
                    "evidence": retained,
                }
            ),
        )
        return self._change(
            request_id,
            lambda current: (
                record if current == prior else self._stale(),
                {"operation": operation, "digest": input_digest},
            ),
        )

    @staticmethod
    def _stale():
        raise ControllerError(
            "E_STALE_STATE", "Request changed; reconcile before continuing."
        )

    def abandon(
        self,
        request_id: str,
        *,
        actor_id: int,
        role: str,
        reason: str,
        effects_absent: bool,
    ) -> Record:
        """Retire only an audited untagged reservation; no remote deletion occurs.

        Args: current maintainer authority and reconciled absence are caller evidence.
        Returns: Abandoned record retaining all history, e.g. from trusted workflow.
        Raises: ControllerError on missing authority, reason, or absence proof.
        """
        prior = self.get(request_id)
        audit = {
            "operation": "abandon",
            "actor_id": actor_id,
            "role": role,
            "reason": reason,
            "effects_absent": effects_absent,
        }
        return self._change(
            request_id,
            lambda current: (
                current.model_copy(update={"state": "abandoned"})
                if current == prior
                else self._stale(),
                audit,
            ),
        )
