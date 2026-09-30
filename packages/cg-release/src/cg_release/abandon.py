"""Audited maintainer abandonment after excluding known remote effects."""

from cg_release.authority import actor_role
from cg_release.events import ControllerError
from cg_release.github import MAX_PAGES
from cg_release.models import Event
from cg_release.runtime import Context


def abandon_request(
    context: Context, request_id: str, actor_id: int, reason: str, run_id: int
) -> Event:
    """Retire an untagged request through a trusted workflow; never delete objects.

    Example: abandon_request(context, locator, maintainer_id, 'Superseded', run_id).
    Missing, partial, or active-run evidence blocks retirement.
    """
    record = context.journal.get(request_id)
    api = context.api
    role = actor_role(api, actor_id)
    actor_role(api, record.request.requester_id)
    if (
        role not in {"maintain", "admin"}
        or not isinstance(reason, str)
        or not 1 <= len(reason.strip()) <= 1024
    ):
        raise ControllerError(
            "E_AUTHORITY", "Abandon needs a current maintainer and bounded reason."
        )
    if (
        record.publication_started
        or record.published
        or record.state
        not in {"queued", "awaiting-review", "building", "awaiting-approval", "failed"}
        or record.intent is not None
    ):
        raise ControllerError(
            "E_ABANDON_UNSAFE",
            "Unreconciled effects or publication history prevent abandonment.",
        )
    if any(ref["ref"] == "refs/tags/" + record.request.tag for ref in api.refs()):
        raise ControllerError(
            "E_ABANDON_UNSAFE", "A tag exists; its reservation cannot be retired."
        )
    if any(
        release["tag_name"] == record.request.tag for release in api.pages("releases")
    ):
        raise ControllerError(
            "E_ABANDON_UNSAFE", "A Release or draft exists; retain its reservation."
        )
    try:
        api.branch("release-controller/" + record.request.nonce)
    except ControllerError as error:
        if error.code != "E_NOT_FOUND":
            raise
    else:
        raise ControllerError(
            "E_ABANDON_UNSAFE", "Preparation branch requires inspected recovery."
        )
    seen = set()
    for page in range(1, MAX_PAGES + 1):
        value = api.get("actions/runs", page=page)
        try:
            rows = value["workflow_runs"]
            if not isinstance(rows, list) or type(value["total_count"]) is not int:
                raise ValueError
            for run in rows:
                if type(run["id"]) is not int or run["id"] in seen:
                    raise ValueError
                seen.add(run["id"])
                if run["id"] != run_id and run["status"] != "completed":
                    raise ControllerError(
                        "E_ABANDON_UNSAFE",
                        "Another workflow can still mutate remote state.",
                    )
            if len(rows) < 100:
                if len(seen) != value["total_count"]:
                    raise ValueError
                break
        except (ValueError, KeyError, TypeError, AttributeError):
            raise ControllerError(
                "E_ABANDON_UNSAFE", "Workflow absence proof is incomplete."
            ) from None
    else:
        raise ControllerError(
            "E_ABANDON_UNSAFE", "Workflow inventory exceeds the verification bound."
        )
    context.journal.abandon(
        request_id, actor_id=actor_id, role=role, reason=reason, effects_absent=True
    )
    return Event(
        kind="status",
        request_id=request_id,
        version=record.request.version,
        observed="abandoned",
        step="maintainer-abandon",
        message="Audited reservation retirement; history is retained.",
    )
