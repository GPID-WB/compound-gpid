"""Atomic controller-only checkpoints; external effects still require an intent."""

import re

from cg_release.events import ControllerError
from cg_release.journal import digest
from cg_release.journal_rules import retained_evidence


def atomic_build_checkpoint(
    journal, record, operation: str, evidence: dict, state: str
):
    """Commit a whole ticket/registration once, e.g. before dispatch or source output.

    No provider action occurs inside this transaction. A lost write response uses
    the journal's exact read-back reconciliation. Another writer cannot claim a
    completed registration, even when its proposed bytes would be identical.
    """
    if state != "building" or not re.fullmatch(
        r"build-(?:request|registration)-[1-9][0-9]*", operation
    ):
        raise ControllerError(
            "E_TRANSITION", "Atomic checkpoint is outside build data scope."
        )
    identity = digest(evidence)
    audit = {"operation": operation, "digest": identity, "atomic": True}

    def change(current):
        if (
            current != record
            or current.intent is not None
            or operation in current.evidence
        ):
            raise ControllerError(
                "E_STALE_STATE", "Build checkpoint changed or was already consumed."
            )
        retained = retained_evidence(current, operation, identity, evidence)
        return current.model_copy(
            update={"state": state, "checkpoint": operation, "evidence": retained}
        ), audit

    return journal._change(record.request_id, change)


def atomic_publication_checkpoint(journal, record, operation, evidence, state):
    """Persist exact public data before a publication effect.

    An interrupted local checkpoint is wholly absent or wholly present; there is
    no digest-only intent that loses the signed object's exact bytes.
    Example: atomic_publication_checkpoint(journal, record, op, evidence, state).
    """
    if not (
        operation == "publication-tag-object"
        or re.fullmatch(
            r"publication-(?:seal|owner|owner-release|request|resume|exception|dispatch|dispatch-intent|registration)-[1-9][0-9]*",
            operation,
        )
    ):
        raise ControllerError("E_TRANSITION", "Unsupported atomic publication record.")
    identity = digest(evidence)

    def change(current):
        if (
            current != record
            or (current.intent is not None and operation == "publication-tag-object")
            or operation in current.evidence
        ):
            raise ControllerError(
                "E_STALE_STATE", "Publication checkpoint already changed."
            )
        return current.model_copy(
            update={
                "state": state,
                "checkpoint": operation,
                "publication_started": current.publication_started
                or state == "publishing",
                "evidence": retained_evidence(current, operation, identity, evidence),
            }
        ), {"operation": operation, "digest": identity, "publication_atomic": True}

    return journal._change(record.request_id, change)
