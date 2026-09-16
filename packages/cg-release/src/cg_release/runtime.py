"""Four-command runtime using protected policy and portable remote identity."""

import hashlib
import re
import time

from cg_release.admission import Locator, discover, submit
from cg_release.authority import actor_role, authorize_resume
from cg_release.context import Context, context_for
from cg_release.events import ControllerError
from cg_release.inbox import GitHubInbox
from cg_release.models import Event, Request, canonical_bytes
from cg_release.policy import approval_route
from cg_release.preview import Proposal, request_from_proposal
from cg_release.progress import stage_timings
from cg_release.read_session import ReadSession


def check_submission(context: Context, request: Request) -> None:
    """Recheck authority, exact inputs, refs, and reservations before writing."""
    from cg_release.history import adopted_history

    policy, api = context.policy, context.api
    if not policy.enabled:
        raise ControllerError(
            "E_SUBMISSION_UNAVAILABLE",
            "Publishing policy is disabled; no issue will be created.",
        )
    if (
        request.policy_sha != context.policy_sha
        or request.policy_digest != hashlib.sha256(canonical_bytes(policy)).hexdigest()
        or api.branch(request.source_branch)["commit"]["sha"] != request.source_sha
        or api.branch(context.default)["commit"]["sha"] != context.policy_sha
    ):
        raise ControllerError(
            "E_STALE_PROPOSAL", "Confirmed source or trusted policy changed."
        )
    actor = api.actor()
    if actor["id"] != request.requester_id:
        raise ControllerError(
            "E_AUTHORITY", "Authenticated submission actor differs from requester."
        )
    role = actor_role(api, request.requester_id)
    approval_route(
        policy,
        request.source_branch,
        request.version,
        role,
        context.default,
        request.override_reason,
    )
    _, occupied = adopted_history(api, policy)
    occupied += context.journal.reservations()
    if request.version.split("+")[0] in {v.split("+")[0] for v in occupied}:
        raise ControllerError(
            "E_COLLISION", "Confirmed release identity is already occupied."
        )
    api.remaining()


def start(
    proposal: Proposal, emit, *, deadline: float, clock=time.monotonic, api_factory=None
) -> None:
    """Submit after confirmation and fresh checks; no publication or PR write."""
    if not proposal.inputs["publishing_enabled"]:
        raise ControllerError(
            "E_SUBMISSION_UNAVAILABLE",
            "Trusted policy is disabled; no request was submitted.",
        )
    request = request_from_proposal(proposal)
    context = context_for(
        Locator.from_request(request).encode(),
        deadline=deadline,
        clock=clock,
        api_factory=api_factory or ReadSession(),
    )
    check_submission(context, request)
    submit(request, GitHubInbox(context.api), emit)


def status(
    request_id: str, *, deadline: float, clock=time.monotonic, api_factory=None
) -> Event:
    """Read sealed state first; otherwise resolve the unedited provisional inbox."""
    context = context_for(
        request_id,
        deadline=deadline,
        clock=clock,
        api_factory=api_factory or ReadSession(),
    )
    try:
        record = context.journal.get(request_id)
    except ControllerError as error:
        if error.code != "E_REQUEST_MISSING":
            raise
        receipt = discover(request_id, GitHubInbox(context.api))
        failure = next(
            (
                event["record"]["failures"][str(receipt.number)]
                for event in reversed(context.journal.events())
                if event["record"].get("kind") == "queue"
                and str(receipt.number) in event["record"]["failures"]
            ),
            None,
        )
        return Event(
            kind="status",
            request_id=request_id,
            version=receipt.request.version,
            observed="failed" if failure else "queued",
            step="pending-validation",
            expected="admission",
            code=failure,
            message="Admission rejected; inspect failure."
            if failure
            else "Durable inbox request; admission pending.",
            next_action=receipt.url,
        )
    return Event(
        kind="status",
        request_id=request_id,
        version=record.request.version,
        observed=record.state,
        step=record.checkpoint,
        expected="reconciliation" if record.intent else record.state,
        message="Verified journal state; publication and completion are distinct.",
        next_action="Use resume for reconciliation; do not repeat start.",
        proposal={
            "pending_intent": record.intent,
            "error": record.error,
            "failed_step": record.failed_step,
            "retryable": record.retryable,
            "published": record.published,
            "timings": stage_timings(context.journal, request_id),
            "receipt": record.receipt.model_dump(mode="json", exclude={"request"})
            if record.receipt
            else None,
        },
    )


def resume(
    request_id: str, *, deadline: float, clock=time.monotonic, api_factory=None
) -> Event:
    """Resolve first, then dispatch once on protected default; never recreate issues."""
    api_factory = api_factory or ReadSession()
    observed = status(
        request_id, deadline=deadline, clock=clock, api_factory=api_factory
    )
    context = context_for(
        request_id, deadline=deadline, clock=clock, api_factory=api_factory
    )
    api, policy = context.api, context.policy
    if not policy.enabled:
        raise ControllerError(
            "E_DISABLED", "Policy is disabled; reconciliation dispatch is blocked."
        )
    Locator.decode(request_id)
    reviewed_release = False
    record = None
    try:
        record = context.journal.get(request_id)
        request = record.request
        reviewed_release = "review-binding" in record.evidence
    except ControllerError as error:
        if error.code != "E_REQUEST_MISSING":
            raise
        request = discover(request_id, GitHubInbox(api)).request
    from cg_release.stranded_recovery import current_policy_digest

    allowed_policy = (
        current_policy_digest(context, record)
        if record is not None
        else request.policy_digest
    )
    if (
        request.policy_sha != context.policy_sha and not reviewed_release
    ) or allowed_policy != hashlib.sha256(canonical_bytes(policy)).hexdigest():
        raise ControllerError(
            "E_STALE_POLICY",
            "Policy changed; reviewed maintainer recovery is required.",
        )
    if record is None:
        authorize_resume(api, policy, context.default, request, api.actor()["id"])
    else:
        from cg_release.recovery_authority import authorize_record

        authorize_record(context, record, api.actor()["id"])
    if observed.observed in {"complete", "abandoned"}:
        return observed
    if api.branch(context.default)["commit"]["sha"] != context.policy_sha:
        raise ControllerError(
            "E_STALE_PROPOSAL", "Policy changed before resume dispatch."
        )
    payload = {
        "ref": context.default,
        "inputs": {"operation": "reconcile", "request_id": request_id},
    }
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
            f"repos/{api.slug}/actions/workflows/release-controller.yml/dispatches",
        ],
        cwd=api.cwd,
        timeout=min(api.read_seconds, api.remaining()),
        allow_failure=True,
        input_text=canonical_bytes(payload).decode(),
    )
    if result.returncode or not re.match(r"HTTP/[0-9.]+ 204(?: |\r?\n)", result.stdout):
        raise ControllerError(
            "E_DISPATCH_UNKNOWN",
            "Resume dispatch outcome is unknown; inspect status before retry.",
        )
    return Event(
        kind="status",
        request_id=request_id,
        version=observed.version,
        observed="reconciliation-requested",
        step=observed.step,
        message="Trusted reconciliation requested; this is not completion.",
    )
