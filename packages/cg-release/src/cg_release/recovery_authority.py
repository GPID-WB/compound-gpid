"""Explicit authority replacement only for an exact verified maintainer recovery."""

from cg_release.authority import actor_role, authorize_resume
from cg_release.events import ControllerError
from cg_release.policy import approval_route


def authorize_record(context, record, actor_id=None):
    """Apply ordinary authority or the record's current audited replacement grant."""
    from cg_release.stranded_recovery import recovery_grant

    grant = recovery_grant(context, record)
    request = record.request
    if grant is None:
        return authorize_resume(
            context.api,
            context.policy,
            context.default,
            request,
            request.requester_id if actor_id is None else actor_id,
        )
    actor_id = grant.actor_id if actor_id is None else actor_id
    if actor_role(context.api, actor_id) not in {"maintain", "admin"}:
        raise ControllerError(
            "E_RECOVERY_AUTHORITY",
            "Audited recovery requires current maintainer authority.",
        )
    approval_route(
        context.policy,
        request.source_branch,
        request.version,
        actor_role(context.api, grant.actor_id),
        context.default,
        request.override_reason or grant.directive.reason,
    )
