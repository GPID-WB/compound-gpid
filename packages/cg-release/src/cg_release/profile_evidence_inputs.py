"""Immutable per-recovery evidence attempts; prior inputs and PRs are never replaced."""

import hashlib

from cg_release.events import ControllerError
from cg_release.hook_authority import authorize_hooks
from cg_release.prepare_stage import checkpoint
from cg_release.stranded_recovery import recovery_grant, source_lineage


def evidence_inputs(context, record, actor_id, path):
    """Select/seal an authorized attempt, e.g. evidence_inputs(ctx, rec, actor, path).

    Returns (prefix, normalized input view, current record). A reviewed explicit
    evidence base creates a separate attempt bound to its admitted grant, including
    when original evidence inputs/PRs exist. No original evidence is overwritten.
    Unreconciled prior external intents are not cleared or treated as absent.
    """
    grant = recovery_grant(context, record)
    destination = grant.directive.evidence_base if grant else None
    prefix = "profile-evidence" + (f"-recovery-{grant.run_id}" if destination else "")
    key = prefix + "-inputs"
    if key not in record.evidence:
        if destination:
            branch, base, created_at = (
                destination.branch,
                destination.sha,
                destination.created_at,
            )
            observed = context.api.branch(branch)
            if (
                observed.get("protected") is not True
                or observed["commit"]["sha"] != base
            ):
                raise ControllerError(
                    "E_HOOK", "Reviewed recovery evidence base changed."
                )
        else:
            if record.receipt is None:
                raise ControllerError(
                    "E_HOOK", "Recovery lacks its reviewed evidence PR base."
                )
            branch = record.request.source_branch
            base = context.api.branch(branch)["commit"]["sha"]
            created_at = record.receipt.created_at
            source_lineage(context, record, tagged=True)
        nonce_label = "evidence" if prefix == "profile-evidence" else prefix
        inputs = dict(
            base=base,
            branch=branch,
            created_at=created_at,
            path=path,
            nonce=hashlib.sha256(
                (record.request.nonce + ":" + nonce_label).encode()
            ).hexdigest()[:32],
        )
        if destination:
            inputs.update(
                grant_digest=grant.directive_digest,
                recovery_review=f"Reviewed recovery {grant.policy_sha} directive "
                f"{grant.directive_digest} run {grant.run_id}",
            )
        authorize_attempt(context, record.request_id, inputs, actor_id)
        record = checkpoint(
            context.journal,
            record,
            key,
            inputs,
            "published",
            before_write=lambda: authorize_attempt(
                context, record.request_id, inputs, actor_id
            ),
        )
    inputs = dict(record.evidence[key])
    # Preserve older ordinary checkpoints while reading their implicit fields.
    if not destination and record.receipt is not None:
        inputs.setdefault("branch", record.request.source_branch)
        inputs.setdefault("created_at", record.receipt.created_at)
    authorize_attempt(context, record.request_id, inputs, actor_id)
    return prefix, inputs, record


def authorize_attempt(context, request_id, inputs, actor_id):
    """Fresh authority/attempt selection, e.g. authorize_attempt(ctx, id, data, 8).

    GET-only. Raises if a newer admitted grant supersedes this evidence attempt.
    Does not require an unchanged branch tip after the exact PR has merged.
    """
    current = context.journal.get(request_id)
    grant = recovery_grant(context, current)
    selected = (
        grant.directive_digest if grant and grant.directive.evidence_base else None
    )
    if selected != inputs.get("grant_digest"):
        raise ControllerError("E_HOOK", "Evidence recovery attempt was superseded.")
    authorize_hooks(context, current, actor_id, fresh=True)
