"""Append and replay permanent recovery audits with ordinary journal CAS semantics."""

from datetime import UTC, datetime

from cg_release.events import ControllerError
from cg_release.models import canonical_bytes, load_record
from cg_release.recovery_models import RecoveryAudit


def validate_audit(record, audit, seen):
    """Reject a changed or duplicated recovery directive during full replay."""
    from cg_release.journal import digest

    if (
        record.directive_digest != digest(record.directive)
        or record.directive_digest in seen
        or audit
        != {"operation": "recovery", "directive_digest": record.directive_digest}
    ):
        raise ValueError("recovery audit identity changed")
    seen.add(record.directive_digest)


def record_audit(
    journal, directive, *, policy_sha, actor_id, run_id, before_write=None
):
    """Append once after read-back, e.g. record_audit(journal, directive, ...)."""
    from cg_release.journal import digest

    record = RecoveryAudit(
        directive=directive,
        directive_digest=digest(directive),
        policy_sha=policy_sha,
        actor_id=actor_id,
        run_id=run_id,
    )
    for _ in range(3):
        parent, events, _ = journal._read()
        for event in events:
            if (
                event["record"].get("kind") == "recovery"
                and event["record"]["directive_digest"] == record.directive_digest
            ):
                stored = load_record(RecoveryAudit, canonical_bytes(event["record"]))
                if stored.directive != directive:
                    raise ControllerError(
                        "E_RECOVERY_CONFLICT", "An audited recovery directive changed."
                    )
                return stored
        event = {
            "schema_version": 1,
            "revision": len(events) + 1,
            "parent": parent,
            "previous": events[-1]["digest"] if events else "0" * 64,
            "record": record.model_dump(mode="json"),
            "audit": {
                "operation": "recovery",
                "directive_digest": record.directive_digest,
            },
            "occurred_at": datetime.now(UTC).isoformat(),
        }
        event["digest"] = digest(event)
        if before_write is not None:
            before_write()
        try:
            journal.store.append(parent, canonical_bytes(event), record)
        except ControllerError as error:
            observed_parent, observed_events, _ = journal._read()
            for observed in observed_events:
                if (
                    observed["record"].get("kind") == "recovery"
                    and observed["record"]["directive_digest"]
                    == record.directive_digest
                ):
                    return load_record(
                        RecoveryAudit, canonical_bytes(observed["record"])
                    )
            if error.code != "E_CAS" or observed_parent == parent:
                raise
    for event in journal.events():
        if (
            event["record"].get("kind") == "recovery"
            and event["record"]["directive_digest"] == record.directive_digest
        ):
            return load_record(RecoveryAudit, canonical_bytes(event["record"]))
    raise ControllerError(
        "E_WRITE_UNKNOWN", "Recovery audit needs journal read-back reconciliation."
    )
