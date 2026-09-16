"""Atomic publication seals and repository-wide owner claims through the control App."""

import re

from cg_release.events import ControllerError
from cg_release.journal_checkpoint import atomic_publication_checkpoint
from cg_release.publication_rules import active_owner
from cg_release.recovery import owner_available


def publication_ticket(record, nonce):
    """Read the current dispatch ticket, e.g. publication_ticket(record, nonce)."""
    tickets = [
        (int(k.rsplit("-", 1)[1]), v)
        for k, v in record.evidence.items()
        if re.fullmatch(r"publication-request-[1-9][0-9]*", k)
    ]
    if not tickets or max(tickets)[1]["nonce"] != nonce:
        raise ControllerError(
            "E_PUBLICATION_REQUEST", "Publication ticket is absent or superseded."
        )
    return max(tickets)


def store_seal(journal, record, seal):
    """Claim one run/digest, e.g. store_seal(journal, record, seal)."""
    if "publication-tag-object" in record.evidence:
        from cg_release.publication_capacity import preflight_publication

        projected = record.model_copy(
            update={
                "evidence": {
                    **record.evidence,
                    f"publication-seal-{seal['run_id']}": seal,
                }
            }
        )
        preflight_publication(
            journal,
            projected,
            seal["inputs"],
            record.evidence["publication-tag-object"],
            seal["run_id"],
        )
    return atomic_publication_checkpoint(
        journal, record, f"publication-seal-{seal['run_id']}", seal, record.state
    )


def acquire_owner(journal, record, *, run_id: int, expires_at: int, now: int):
    """Acquire the repository writer after approval, e.g. acquire_owner(...).

    The caller derives the credential expiry from the trusted token-issuance step.
    Claims conflict atomically with other requests even on a CAS sibling retry.
    """
    if (
        type(run_id) is not int
        or run_id <= 0
        or type(expires_at) is not int
        or type(now) is not int
        or not now < expires_at <= now + 3600
    ):
        raise ControllerError(
            "E_OWNER", "Publication owner credential bound is invalid."
        )
    owner = active_owner(journal.records())
    if owner is not None:
        if owner[0] == record.request_id and owner[1]["run_id"] == run_id:
            return journal.get(record.request_id)
        raise ControllerError(
            "E_OWNER",
            "Another publisher owns this repository; age alone cannot release it.",
        )
    return atomic_publication_checkpoint(
        journal,
        record,
        f"publication-owner-{run_id}",
        {"run_id": run_id, "credential_expires_at": expires_at},
        record.state,
    )


def release_owner(
    journal, record, *, run_id: int, terminal_proof=None, now=None, before_write=None
):
    """Release this job's owner or a terminal/expired/reconciled prior owner.

    Args: terminal_proof is fresh trusted run metadata plus effects_reconciled.
    Returns: Immutable owner-release checkpoint; no ref, tag or asset is deleted.
    Example: ``release_owner(journal, record, run_id=current_run)`` after verification.
    Post-publication recovery supplies before_write after all owner/state reads.
    """
    current = journal.get(record.request_id)
    owner = active_owner(journal.records())
    if owner is None:
        return current
    if owner[0] != record.request_id:
        raise ControllerError("E_OWNER", "Owner belongs to another request.")
    value = owner[1]
    if run_id != value["run_id"] and (
        terminal_proof is None
        or not owner_available(
            value,
            terminal_proof["run"],
            now=now,
            effects_reconciled=terminal_proof["effects_reconciled"],
        )
    ):
        raise ControllerError(
            "E_OWNER", "Prior owner lacks terminal, credential or reconciliation proof."
        )
    if before_write is not None:
        before_write()
    return atomic_publication_checkpoint(
        journal,
        current,
        f"publication-owner-release-{value['run_id']}",
        {
            "run_id": value["run_id"],
            "released_by": run_id,
            "terminal_proof": None
            if terminal_proof is None
            else {
                "run": {
                    k: terminal_proof["run"][k] for k in ("id", "run_attempt", "status")
                },
                "effects_reconciled": terminal_proof["effects_reconciled"],
            },
        },
        current.state,
    )
