"""Current authority and immutable completion requirements for published hooks."""

import re

from cg_release.context import Context
from cg_release.events import ControllerError
from cg_release.journal import digest
from cg_release.journal_models import Record
from cg_release.recovery_authority import authorize_record
from cg_release.stranded_recovery import recovery_grant


def seal_required_hooks(context, record, *, actor_id=None):
    """Retain original requirements; e.g. seal_required_hooks(ctx, record).

    Appends one immutable journal checkpoint only when absent. Original tickets
    remain evidence for records created before the separate requirement checkpoint.
    """
    from cg_release.prepare_stage import checkpoint

    if "required-hooks" in record.evidence:
        return record
    original = any(
        v.get("profile_version") == "v1"
        for k, v in record.evidence.items()
        if re.fullmatch(r"build-request-[1-9][0-9]*", k)
    )
    return checkpoint(
        context.journal,
        record,
        "required-hooks",
        {
            "stages": ["docs", "evidence"]
            if original or context.policy.gpid_profile == "v1"
            else []
        },
        record.state,
        before_write=lambda: authorize_hooks(
            context, context.journal.get(record.request_id), actor_id, fresh=True
        ),
    )


def authorize_hooks(
    context: Context,
    record: Record,
    actor_id: int | None = None,
    *,
    fresh: bool = False,
) -> int:
    """Check policy and both principals before effects; return the applicable actor.

    Example: authorize_hooks(context, record, sealed['authority_actor_id'], fresh=True).
    A maintainer grant replaces the old requester only for its exact immutable
    request. Fresh mode finishes repository/default checks before final human
    authority. Callers must finish optional state reads first and recheck after
    required intervening operations. Identity/permission calls for principals and
    the later GitHub effect remain separate; this is not atomic authorization.
    """
    grant = recovery_grant(context, record)
    expected = grant.directive.policy_digest if grant else record.request.policy_digest
    if not context.policy.enabled or digest(context.policy) != expected:
        raise ControllerError(
            "E_HOOK_POLICY", "Bound policy changed; reviewed recovery is required."
        )
    actor_id = (
        actor_id
        if actor_id is not None
        else (grant.actor_id if grant else record.request.requester_id)
    )
    if fresh:
        repo = context.api.get("")
        branch = context.api.branch(context.default)
        if (
            repo.get("id") != context.policy.repository_id
            or repo.get("default_branch") != context.default
            or branch.get("protected") is not True
            or branch.get("commit", {}).get("sha") != context.policy_sha
        ):
            raise ControllerError(
                "E_HOOK_POLICY",
                "Protected default policy changed during hook execution.",
            )
    authorize_record(context, record, actor_id)
    return actor_id


def required_hooks(record: Record) -> set[str]:
    """Read requirements from the approved build, never the current profile flag.

    Example: required_hooks(published_record) returns {'docs', 'evidence'} for GPID.
    Missing, substituted, or mixed build identities stop completion.
    """
    from cg_release.published_history import published_inputs

    inputs = published_inputs(record)
    builds = [
        value
        for key, value in record.evidence.items()
        if re.fullmatch(r"build-validated-[1-9][0-9]*", key)
        and digest(value) == inputs.get("build_digest")
    ]
    try:
        if len(builds) != 1 or not builds[0]["gates"]:
            raise ValueError
        profiles = set()
        for gate in builds[0]["gates"].values():
            ticket = record.evidence[f"build-request-{gate['request']}"]
            if (
                ticket["release_sha"] != inputs["release_sha"]
                or ticket["request_digest"] != record.request.proposal_digest
            ):
                raise ValueError
            profiles.add(ticket["profile_version"])
        if len(profiles) != 1 or not profiles <= {None, "v1"}:
            raise ValueError
        # Replacement tickets cannot remove an original approved requirement.
        original = record.evidence.get("required-hooks", {}).get("stages")
        if original is not None and original not in ([], ["docs", "evidence"]):
            raise ValueError
        archived = [
            v
            for k, v in record.evidence.items()
            if re.fullmatch(r"build-request-[1-9][0-9]*", k)
        ]
        needs_profile = profiles == {"v1"} or any(
            v["profile_version"] == "v1" for v in archived
        )
        return {"docs", "evidence"} if original or needs_profile else set()
    except (KeyError, ValueError, TypeError):
        raise ControllerError(
            "E_HOOK", "Immutable required hook evidence is unavailable."
        ) from None
