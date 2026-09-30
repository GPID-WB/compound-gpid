"""Bounded publication dispatch; only a later protected job can publish objects."""

import os
import re
import secrets
import time

from cg_release.events import ControllerError
from cg_release.journal_checkpoint import atomic_publication_checkpoint
from cg_release.models import canonical_bytes


def dispatch_payload(context, record, ticket):
    """Return the locator/nonce, e.g. dispatch_payload(context, record, ticket)."""
    return {
        "ref": context.default,
        "inputs": {"request_id": record.request_id, "nonce": ticket["nonce"]},
    }


def publication_step(context, record, *, resuming_actor_id=None):
    """Dispatch once and return, e.g. publication_step(context, record).

    Explicit resume starts a fresh run/seal after the prior run is terminal.
    A lost dispatch response remains unknown until that exact run seals its inputs.
    """
    if record.state not in {"awaiting-approval", "publishing", "published"}:
        return record
    journal, api = context.journal, context.api
    from cg_release.stranded_recovery import recovery_grant

    grant = recovery_grant(context, record)
    if record.publication_started and not record.published:
        from cg_release.publication_inputs import verify_release_gates
        from cg_release.publication_rebuild import begin_rebuild
        from cg_release.publication_remote import GitHubPublicationRemote

        remote = GitHubPublicationRemote(api)
        release = remote.observe_release(record.request.tag)
        if release is None or release.get("draft") is True:
            try:
                verify_release_gates(context, record)
            except ControllerError as error:
                if error.code != "E_REBUILD_REQUIRED" or resuming_actor_id is None:
                    raise
                return begin_rebuild(
                    context,
                    record,
                    remote,
                    actor_id=resuming_actor_id,
                    run_id=int(os.environ["GITHUB_RUN_ID"]),
                    now=int(time.time()),
                )
    tickets = [
        (int(k.rsplit("-", 1)[1]), v)
        for k, v in record.evidence.items()
        if re.fullmatch(r"publication-request-[1-9][0-9]*", k)
    ]
    number, ticket = max(tickets) if tickets else (0, None)
    seals = [
        s
        for k, s in record.evidence.items()
        if k.startswith("publication-seal-")
        and ticket
        and s.get("nonce") == ticket["nonce"]
    ]
    registration = record.evidence.get(f"publication-registration-{number}")
    if ticket and not seals and registration is None and resuming_actor_id is not None:
        from cg_release.publication_registration import discover_publication

        if (
            f"publication-dispatch-{number}" in record.evidence
            or f"publication-dispatch-intent-{number}" in record.evidence
        ):
            record = discover_publication(context, record, number)
            registration = record.evidence.get(f"publication-registration-{number}")
    if len(seals) > 1:
        raise ControllerError(
            "E_APPROVAL", "A publication request has multiple run seals."
        )
    if seals or registration:
        run = api.get(f"actions/runs/{(seals[0] if seals else registration)['run_id']}")
        rebuilt = any(k.startswith("publication-rebuild-") for k in record.evidence)
        if run.get("status") != "completed" or (
            resuming_actor_id is None and not rebuilt
        ):
            return record
        ticket = None
    if ticket is None:
        number += 1
        reconfirmers = sorted(
            ({resuming_actor_id} if resuming_actor_id else set())
            | ({grant.actor_id} if grant is not None else set())
        )
        ticket = {
            "nonce": secrets.token_hex(16),
            "mode": "recovery" if tickets or record.publication_started else "initial",
            "reconfirmers": reconfirmers,
        }
        record = atomic_publication_checkpoint(
            journal, record, f"publication-request-{number}", ticket, record.state
        )
    operation = f"publication-dispatch-{number}"
    if operation in record.evidence:
        return record
    intent_key = f"publication-dispatch-intent-{number}"
    if intent_key in record.evidence:
        raise ControllerError(
            "E_DISPATCH_UNKNOWN",
            "Publication dispatch is unresolved; await its seal rather than replay.",
        )
    payload = dispatch_payload(context, record, ticket)
    record = atomic_publication_checkpoint(
        journal, record, intent_key, payload, record.state
    )
    result = api.runner(
        "gh",
        [
            "api",
            "--method",
            "POST",
            "--hostname",
            api.host,
            "--include",
            "--input",
            "-",
            f"repos/{api.slug}/actions/workflows/release-controller-publish.yml/dispatches",
        ],
        cwd=api.cwd,
        timeout=min(api.read_seconds, api.remaining()),
        allow_failure=True,
        input_text=canonical_bytes(payload).decode(),
    )
    if result.returncode or not re.match(r"HTTP/[0-9.]+ 204(?: |\r?\n)", result.stdout):
        raise ControllerError(
            "E_DISPATCH_UNKNOWN",
            "Publication dispatch outcome requires exact seal reconciliation.",
        )
    record = journal.get(record.request_id)
    if operation in record.evidence:
        return record
    return atomic_publication_checkpoint(
        journal, record, operation, payload, record.state
    )
