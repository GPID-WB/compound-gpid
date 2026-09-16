"""Read-only authority check after the Pages queue and artifact upload."""

import re

from cg_release.context import Context
from cg_release.controller import verify_run
from cg_release.events import ControllerError
from cg_release.hook_authority import authorize_hooks
from cg_release.journal import digest
from cg_release.journal_models import Record


def authorize_deployment(
    context: Context, record: Record, nonce: str, environment: dict[str, str]
) -> dict:
    """Recheck policy and principals; return the exact registered composition.

    Example: authorize_deployment(context, record, nonce, dict(os.environ)).
    EXPECTED_MANIFEST is the digest emitted by the trusted composer, not source.
    Call immediately before deploy-pages. This function makes no journal writes.
    """
    from cg_release.profile_worker import current_composition, current_ticket

    item = current_composition(record, nonce, journal=context.journal)
    sealed = item.ticket
    authorize_hooks(context, record, sealed.get("authority_actor_id"), fresh=True)
    verify_run(context, environment, workflow=sealed["workflow_path"])
    run_id = int(environment["GITHUB_RUN_ID"])
    result = item.evidence.get("composition")
    if (
        sealed.get("policy_digest") != digest(context.policy)
        or not result
        or not re.fullmatch(r"[0-9a-f]{64}", result.get("manifest_sha256", ""))
        or result.get("run_id") != run_id
        or result.get("request_digest") != digest(sealed)
        or result.get("manifest_sha256") != environment.get("EXPECTED_MANIFEST")
        or item.evidence.get("registration")
        != {"run_id": run_id, "request_digest": digest(sealed)}
    ):
        raise ControllerError(
            "E_HOOK", "Deployment lacks its exact registered composition."
        )
    current_ticket(record, nonce, journal=context.journal)
    authorize_hooks(context, record, sealed["authority_actor_id"], fresh=True)
    return result
