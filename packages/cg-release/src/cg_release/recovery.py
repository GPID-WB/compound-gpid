"""Non-destructive lineage, owner, journal-mirror and post-publication checks."""

import re
from urllib.parse import quote

from cg_release.events import ControllerError
from cg_release.prepare_stage import checkpoint


def check_lineage(api, branch: str, release_sha: str, *, tagged: bool) -> None:
    """Require tip equality before tagging and ancestry afterwards.

    Args: tagged is true only after verifying the exact stored annotated object.
    Raises: ControllerError when deletion/rewriting requires maintainer recovery.
    Example: check_lineage(api, 'main', sha, tagged=True).
    """
    try:
        tip = api.branch(branch)["commit"]["sha"]
        if not isinstance(tip, str) or not re.fullmatch(r"[0-9a-f]{40}", tip):
            raise ValueError
        if tip == release_sha:
            return
        if not tagged:
            raise ValueError
        compared = api.get(
            f"compare/{quote(release_sha, safe='')}...{quote(tip, safe='')}"
        )
        if (
            compared["status"] != "ahead"
            or compared["merge_base_commit"]["sha"] != release_sha
            or compared["base_commit"]["sha"] != release_sha
        ):
            raise ValueError
    except (ValueError, KeyError, TypeError, AttributeError):
        raise ControllerError(
            "E_LINEAGE",
            "Source tip or ancestry changed; reviewed maintainer recovery is required.",
        ) from None
    except ControllerError as error:
        if error.code != "E_NOT_FOUND":
            raise
        raise ControllerError(
            "E_LINEAGE",
            "Source branch is missing; reviewed maintainer recovery is required.",
        ) from None


def owner_available(
    owner: dict, run: dict, *, now: int, effects_reconciled: bool
) -> bool:
    """Permit reassignment only after terminal-run, credential and effect proof.

    Example: owner_available(owner, run, now=100, effects_reconciled=True).
    Expiry must be the trusted credential issuer's upper lifetime bound, not age
    guessed from the last journal update. Missing evidence returns False.
    """
    return (
        isinstance(owner, dict)
        and isinstance(run, dict)
        and type(owner.get("run_id")) is int
        and owner["run_id"] > 0
        and type(run.get("id")) is int
        and run["id"] == owner["run_id"]
        and run.get("status") == "completed"
        and run.get("run_attempt") == 1
        and type(owner.get("credential_expires_at")) is int
        and type(now) is int
        and now > owner["credential_expires_at"]
        and effects_reconciled is True
    )


def verify_restore(mirror: list[dict], restored: list[dict]) -> None:
    """Reject rewritten history, e.g. verify_restore(backup, remote).

    The caller must first validate both journals' ancestry, event chain and writer
    with Journal.events(). This comparison is not permission to push or force a ref.
    """
    if not mirror or len(restored) < len(mirror) or restored[: len(mirror)] != mirror:
        raise ControllerError(
            "E_RESTORE",
            "Restored journal does not preserve the verified mirror prefix.",
        )


def finish_hooks(
    journal, record, *, required: set[str], verified: dict, before_write=None
):
    """Complete only remotely verified exact-release hooks, e.g. finish_hooks(...).

    Args: verified comes from trusted profile verifiers, never source hook output.
    Returns: Published while hooks are absent; complete only for the entire set.
    Raises: ControllerError for wrong-release or extra evidence.
    """
    if record.state == "complete":
        return record
    if record.state != "published" or not record.published:
        raise ControllerError(
            "E_HOOK", "Hook completion requires verified publication first."
        )
    if set(verified) - required or any(
        not isinstance(v, dict)
        or v.get("verified") is not True
        or v.get("release_sha") != record.evidence["publication-receipt"]["release_sha"]
        for v in verified.values()
    ):
        raise ControllerError(
            "E_HOOK", "Hook evidence is unverified or identifies another release."
        )
    if set(verified) != required:
        return record
    return checkpoint(
        journal,
        record,
        "publication-hooks",
        verified,
        "complete",
        before_write=before_write,
    )


def finish_published(context, record, *, resuming_actor_id=None):
    """Resume verified post-publication work without another Release write."""
    import os
    import time

    from cg_release.hook_authority import authorize_hooks, required_hooks
    from cg_release.publication_control import active_owner, release_owner
    from cg_release.publication_reconcile import inspect_publication
    from cg_release.publication_remote import GitHubPublicationRemote
    from cg_release.published_history import published_inputs

    actor_id = authorize_hooks(context, record, resuming_actor_id)

    def fresh():
        authorize_hooks(
            context, context.journal.get(record.request_id), actor_id, fresh=True
        )

    required = required_hooks(record)
    if required and context.policy.gpid_profile != "v1":
        raise ControllerError(
            "E_HOOK_POLICY", "Current policy cannot remove sealed required hooks."
        )
    inspect_publication(
        record, published_inputs(record), GitHubPublicationRemote(context.api)
    )
    owner = active_owner(context.journal.records())
    if owner is not None and owner[0] == record.request_id:
        run = context.api.get(f"actions/runs/{owner[1]['run_id']}")
        now = int(time.time())
        if not owner_available(owner[1], run, now=now, effects_reconciled=True):
            return record
        record = release_owner(
            context.journal,
            record,
            run_id=int(os.environ["GITHUB_RUN_ID"]),
            now=now,
            terminal_proof={"run": run, "effects_reconciled": True},
            before_write=fresh,
        )
    from cg_release.hooks import verified_hooks

    verified = verified_hooks(context, record, resuming_actor_id=resuming_actor_id)
    record = context.journal.get(record.request_id)
    return finish_hooks(
        context.journal,
        record,
        required=required,
        verified=verified,
        before_write=fresh,
    )
