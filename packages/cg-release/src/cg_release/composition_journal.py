"""Independent bounded composition records in the existing append-only journal."""

from datetime import UTC, datetime
from typing import Annotated, Literal

from pydantic import Field

from cg_release.events import ControllerError
from cg_release.journal_models import digest
from cg_release.models import (
    Digest,
    Positive,
    VersionedRecord,
    canonical_bytes,
    load_record,
)


class Composition(VersionedRecord):
    """One immutable ticket and its bounded results, not a release reservation."""

    schema_version: Literal[1] = 1
    kind: Literal["composition"] = "composition"
    request_id: Annotated[str, Field(max_length=4096)]
    number: Positive
    key: Digest
    ticket: dict
    intent: dict | None = None
    evidence: Annotated[dict, Field(max_length=8)] = Field(default_factory=dict)


def validate_composition(records, compositions, current, audit) -> None:
    """Validate append/replay, e.g. validate_composition(records, prior, item, audit).

    Returns None. Raises ValueError on missing publication, replacement or invalid
    sequencing. All prior records and event bytes remain unchanged; no I/O occurs.
    """
    parent = records.get(current.request_id)
    prior = compositions.get(current.key)
    if (
        parent is None
        or not parent.published
        or parent.state not in {"published", "complete"}
        or current.key
        != digest({"request_id": current.request_id, "number": current.number})
        or len(canonical_bytes(current)) > 63000
    ):
        raise ValueError("invalid composition identity or bound")
    if prior is None:
        latest = max(compositions.values(), key=lambda c: c.number, default=None)
        if (
            current.number
            != max((c.number for c in compositions.values()), default=0) + 1
            or current.intent
            or current.evidence
            or audit != {"operation": "composition-create"}
            or (
                latest is not None
                and not ({"terminal", "absence"} & set(latest.evidence))
            )
        ):
            raise ValueError("invalid composition creation")
    elif (
        current.number != max(c.number for c in compositions.values())
        or current.ticket != prior.ticket
        or current.request_id != prior.request_id
        or current.number != prior.number
        or any(current.evidence.get(k) != v for k, v in prior.evidence.items())
    ):
        raise ValueError("immutable composition changed")
    elif current.intent is not None:
        if (
            prior.intent not in (None, current.intent)
            or prior.evidence != current.evidence
            or audit
            != {"operation": "composition-intent", "digest": digest(current.intent)}
        ):
            raise ValueError("unreconciled composition intent")
    else:
        operation = audit.get("stage")
        if (
            operation
            not in {
                "dispatch",
                "registration",
                "composition",
                "terminal",
                "absence-first",
                "absence",
                "deployment",
            }
            or set(current.evidence) - set(prior.evidence) != {operation}
            or audit
            != {
                "operation": "composition-result",
                "stage": operation,
                "digest": digest(current.evidence[operation]),
            }
            or (
                prior.intent is not None
                and operation not in {"dispatch", "terminal", "absence"}
            )
            or (
                operation == "registration"
                and current.evidence[operation].get("request_digest")
                != digest(current.ticket)
            )
        ):
            raise ValueError("invalid composition result")
    compositions[current.key] = current


class CompositionJournal:
    """Use the same authenticated CAS/event chain; never raise or compact its limits."""

    def __init__(self, journal):
        """Bind verified history, e.g. CompositionJournal(context.journal)."""
        self.journal = journal

    def records(self) -> list[Composition]:
        """Read compositions from verified history; reject corrupt history."""
        return self._from_events(self.journal.events())

    @staticmethod
    def _from_events(events) -> list[Composition]:
        """Project an already authenticated operation-local event view."""
        result = {}
        for event in events:
            if event["record"].get("kind") == "composition":
                item = load_record(Composition, canonical_bytes(event["record"]))
                result[item.key] = item
        return sorted(result.values(), key=lambda item: item.number)

    def create(self, record, ticket: dict) -> Composition:
        """Seal one ticket, e.g. create(published, desired); writes one CAS event.

        Returns the new record. Raises ControllerError on competing state or an
        invalid published parent. Does not alter the immutable release record.
        """
        number = max((c.number for c in self.records()), default=0) + 1
        value = Composition(
            request_id=record.request_id,
            number=number,
            key=digest({"request_id": record.request_id, "number": number}),
            ticket=ticket,
        )
        return self._append(None, value, {"operation": "composition-create"})

    def intent(self, item, payload: dict) -> Composition:
        """Seal dispatch intent before I/O, e.g. intent(item, payload); CAS write."""
        return self._append(
            item,
            item.model_copy(update={"intent": payload}),
            {"operation": "composition-intent", "digest": digest(payload)},
        )

    def save(self, item, stage: str, result: dict) -> Composition:
        """Append an exact result, e.g. save(item, 'registration', result).

        Returns the read-back record; identical results are idempotent. Raises
        ControllerError on conflicting results or stale state; history is retained.
        """
        if stage in item.evidence:
            if item.evidence[stage] != result:
                raise ControllerError(
                    "E_HOOK", "Composition result cannot be replaced."
                )
            return item
        current = item.model_copy(
            update={"intent": None, "evidence": {**item.evidence, stage: result}}
        )
        return self._append(
            item,
            current,
            {
                "operation": "composition-result",
                "stage": stage,
                "digest": digest(result),
            },
        )

    def _append(self, previous, current, audit):
        for _ in range(3):
            parent, events, records = self.journal._read()
            items = {item.key: item for item in self._from_events(events)}
            if items.get(current.key) == current:
                return current
            if items.get(current.key) != previous:
                raise ControllerError(
                    "E_STALE_STATE", "Composition changed; reconcile before writing."
                )
            try:
                current = load_record(Composition, canonical_bytes(current))
                validate_composition(records, items, current, audit)
            except ValueError:
                raise ControllerError(
                    "E_HOOK", "Composition transition or bound is invalid."
                ) from None
            event = {
                "schema_version": 1,
                "revision": len(events) + 1,
                "parent": parent,
                "previous": events[-1]["digest"] if events else "0" * 64,
                "record": current.model_dump(mode="json"),
                "audit": audit,
                "occurred_at": datetime.now(UTC).isoformat(),
            }
            event["digest"] = digest(event)
            try:
                self.journal.store.append(parent, canonical_bytes(event), current)
            except ControllerError as error:
                actual = {item.key: item for item in self.records()}.get(current.key)
                if actual == current:
                    return current
                if error.code == "E_CAS" and self.journal._read()[0] != parent:
                    continue
                raise
            if {item.key: item for item in self.records()}.get(current.key) != current:
                raise ControllerError("E_JOURNAL", "Composition did not read back.")
            return current
        raise ControllerError("E_CAS", "Composition contention exceeds retry bound.")


def replay_composition(records, compositions, event) -> None:
    """Decode one event, e.g. replay_composition(records, prior, event).

    Returns None, updates the in-memory verified view. Raises on invalid schema or
    transition. This is the same validation used before a CAS write; no I/O occurs.
    """
    current = load_record(Composition, canonical_bytes(event["record"]))
    validate_composition(records, compositions, current, event["audit"])
