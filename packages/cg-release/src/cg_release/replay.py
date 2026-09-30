"""Fresh confirmed-proposal replay for admission and exact sealed preparation."""

from cg_release.authority import actor_role, authorize_resume
from cg_release.cli import parse_args
from cg_release.context import Context
from cg_release.events import ControllerError
from cg_release.models import Request
from cg_release.preview import (
    Proposal,
    Snapshot,
    create_proposal,
    request_from_proposal,
)
from cg_release.source import acquire_snapshot


def revalidate(
    context: Context,
    request: Request,
    *,
    resuming_actor_id: int | None = None,
    sealed: bool = False,
) -> tuple[Proposal, Snapshot]:
    """Recompute exact confirmed inputs, e.g. revalidate(context, request, sealed=True).

    Sealed replay excludes only a verified own reservation. All current remote
    history, actor, policy and source checks remain required before preparation.
    """
    if (
        request.repository_id != context.policy.repository_id
        or request.host != context.policy.host
        or request.policy_sha != context.policy_sha
    ):
        raise ControllerError(
            "E_STALE_PROPOSAL", "Request repository or policy identity changed."
        )
    actor_role(context.api, request.requester_id)
    if resuming_actor_id is not None:
        authorize_resume(
            context.api, context.policy, context.default, request, resuming_actor_id
        )
    arguments = [
        "start",
        "--branch",
        request.source_branch,
        "--line",
        request.line,
        "--yes",
    ]
    arguments += (
        ["--bump", request.requested_bump]
        if request.requested_bump
        else ["--version", request.version]
    )
    if request.requested_channel is not None:
        arguments += ["--channel", request.requested_channel]
    if request.sign:
        arguments += ["--sign"]
    if request.override_reason is not None:
        arguments += [
            "--allow-non-deployment-branch",
            "--reason",
            request.override_reason,
        ]
    args = parse_args(arguments)
    state = acquire_snapshot(
        args,
        cwd=context.api.cwd,
        origin=(context.api.host, context.api.slug),
        requester_id=request.requester_id,
        deadline=context.api.deadline,
        clock=context.api.clock,
        api_factory=lambda *a, **k: context.api,
        **({"sealed_request": request} if sealed else {}),
    )
    proposal = create_proposal(state, args)
    if request_from_proposal(proposal, nonce=request.nonce) != request:
        raise ControllerError(
            "E_STALE_PROPOSAL", "Confirmed proposal no longer reproduces exactly."
        )
    if resuming_actor_id is not None:
        authorize_resume(
            context.api, context.policy, context.default, request, resuming_actor_id
        )
    context.api.remaining()
    return proposal, state
