"""Audited return to exact-source builds without clearing publication history."""

import re

from cg_release.authority import actor_role
from cg_release.events import ControllerError
from cg_release.journal import digest
from cg_release.journal_rules import retained_evidence
from cg_release.publication_control import active_owner, release_owner
from cg_release.publication_reconcile import inspect_publication
from cg_release.recovery_authority import authorize_record


def begin_rebuild(context, record, remote, *, actor_id: int, run_id: int, now: int):
    """Suspend one reconciled effect before an exact rebuild, e.g. begin_rebuild(...).

    Only a current maintainer may start this recovery. A prior owner must be
    terminal with expired credentials. Neither tags nor assets are written here.
    """
    if (
        record.state not in {"publishing", "awaiting-approval"}
        or record.published
        or not record.publication_started
        or type(run_id) is not int
        or run_id <= 0
        or actor_role(context.api, actor_id) not in {"maintain", "admin"}
    ):
        raise ControllerError(
            "E_REBUILD",
            "Exact rebuild requires an unpublished request and current maintainer.",
        )
    authorize_record(context, record, actor_id)
    seals = [v for k, v in record.evidence.items() if k.startswith("publication-seal-")]
    if not seals:
        raise ControllerError(
            "E_REBUILD", "Original approved publication inputs are missing."
        )
    snapshot = inspect_publication(record, seals[-1]["inputs"], remote)
    release = remote.observe_release(record.request.tag)
    if release is not None and release.get("draft") is False:
        raise ControllerError(
            "E_REBUILD", "Published release bytes must be reconciled, not rebuilt."
        )
    owner = active_owner(context.journal.records())
    if owner is not None:
        prior_run = context.api.get(f"actions/runs/{owner[1]['run_id']}")
        if run_id == owner[1]["run_id"]:
            raise ControllerError(
                "E_REBUILD",
                "Active publisher cannot rebuild under its live credential.",
            )
        record = release_owner(
            context.journal,
            record,
            run_id=run_id,
            now=now,
            terminal_proof={"run": prior_run, "effects_reconciled": True},
        )
    number = 1 + max(
        (
            int(k.rsplit("-", 1)[1])
            for k in record.evidence
            if re.fullmatch(r"publication-rebuild-[1-9][0-9]*", k)
        ),
        default=0,
    )
    operation = f"publication-rebuild-{number}"
    value = {
        "actor_id": actor_id,
        "run_id": run_id,
        "snapshot": snapshot,
        "suspended_intent": record.intent,
        "release_sha": seals[-1]["inputs"]["release_sha"],
        "release_tree": seals[-1]["inputs"]["release_tree"],
        "previous_build_digest": seals[-1]["inputs"]["build_digest"],
    }
    identity = digest(value)

    def change(current):
        if current != record:
            raise ControllerError("E_STALE_STATE", "Rebuild checkpoint changed.")
        return current.model_copy(
            update={
                "state": "building",
                "intent": None,
                "checkpoint": operation,
                "evidence": retained_evidence(current, operation, identity, value),
            }
        ), {"operation": operation, "digest": identity, "publication_atomic": True}

    return context.journal._change(record.request_id, change)


def verify_rebuild_source(context, record):
    """Recheck exact tag and checkpoint-dependent lineage for a recovery build."""
    from cg_release.publication_remote import GitHubPublicationRemote
    from cg_release.stranded_recovery import source_lineage

    observed = GitHubPublicationRemote(context.api).observe_tag(record.request.tag)
    saved = record.evidence["publication-tag-object"]
    sha = record.evidence["review-binding"]["release_sha"]
    if observed is not None and observed != {
        "oid": saved["oid"],
        "commit": sha,
        "type": "tag",
    }:
        raise ControllerError(
            "E_TAG_CONFLICT", "Recovery build found another tag identity."
        )
    source_lineage(context, record, tagged=observed is not None)
