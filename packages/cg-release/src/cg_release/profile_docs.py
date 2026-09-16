"""Durable GPID composition requests; immutable assets and mutable dev are separate."""

import secrets
import time

from cg_release.composition_journal import CompositionJournal
from cg_release.events import ControllerError
from cg_release.hook_authority import authorize_hooks
from cg_release.journal import digest
from cg_release.prepare_stage import checkpoint
from cg_release.profile_dispatch import dispatch, recover_dispatch
from cg_release.profile_docs_verify import verify_deployment
from cg_release.profile_selection import acquire
from cg_release.profile_selection import selection as selection
from cg_release.stranded_recovery import recovery_grant


def docs_step(context, record, *, resuming_actor_id=None):
    """Advance bounded composition, e.g. docs_step(ctx, published, resuming_actor_id=7).

    Returns: A verified raw HookResult dictionary, or None while pending. Checks
    fresh request/resumer authority before effects. Composition events are separate
    64 KiB records; immutable release evidence is never expanded for dev refreshes.
    Raises: ControllerError for missing setup, stale authority, conflict or retry
    exhaustion. Writes only journal records and a sealed default-ref dispatch.
    """
    api, journal = context.api, context.journal
    store = CompositionJournal(journal)
    records = store.records()
    item = records[-1] if records else None
    grant = recovery_grant(context, record)
    if resuming_actor_id is None and grant is not None:
        resuming_actor_id = grant.actor_id
    elif resuming_actor_id is None and item is not None:
        resuming_actor_id = item.ticket["authority_actor_id"]
    actor_id = authorize_hooks(context, record, resuming_actor_id, fresh=True)
    snapshots, stable = selection(context)
    owners = sorted(
        (r for r in journal.records() if r.published),
        key=lambda r: (r.request.tag != stable, r.request_id),
    )
    owner = owners[0]
    authorize_hooks(context, owner, actor_id, fresh=True)
    desired = {
        "releases": snapshots,
        "stable_tag": stable,
        "dev_sha": api.branch("dev")["commit"]["sha"],
        "controller_sha": context.policy_sha,
        "controller_ref": context.default,
        "workflow_path": context.policy.profile.docs_workflow,
        "repository_id": context.policy.repository_id,
        "authority_actor_id": actor_id,
        "policy_digest": digest(context.policy),
    }
    repairs = 0
    if item is not None:
        item_owner = journal.get(item.request_id)
        authorize_hooks(context, item_owner, actor_id, fresh=True)
        changed_policy = item.ticket["policy_digest"] != digest(context.policy)
        if changed_policy and recovery_grant(context, item_owner) is None:
            raise ControllerError(
                "E_HOOK_POLICY", "Composition policy binding changed."
            )
        if (
            not changed_policy
            and "dispatch" not in item.evidence
            and item.intent is None
        ):
            dispatch(context, item_owner, item)
            return None
        item, run, terminal = recover_dispatch(
            context, item_owner, item, actor_id=actor_id
        )
        if not terminal:
            return None
        unchanged = all(item.ticket.get(k) == v for k, v in desired.items())
        successful = (
            run is not None
            and run.get("conclusion") == "success"
            and "registration" in item.evidence
        )
        if unchanged and successful:
            acquire(api, snapshots, download=False)
            return verify_deployment(context, record, item, run)
        if unchanged:
            repairs = item.ticket["repair_attempts"] + 1
            if repairs > context.policy.profile.composition_retries:
                raise ControllerError(
                    "E_RETRY_BUDGET", "Composition repair budget is exhausted."
                )
    acquire(api, snapshots, download=False)
    sealed = {
        **desired,
        "nonce": secrets.token_hex(16),
        "repair_attempts": repairs,
        "created_at": time.time(),
    }
    authorize_hooks(context, owner, actor_id, fresh=True)
    if "profile-docs-journal" not in owner.evidence:
        owner = checkpoint(
            journal,
            owner,
            "profile-docs-journal",
            {
                "schema_version": 1,
                "namespace": "compositions",
                "repository_id": context.policy.repository_id,
            },
            owner.state,
            before_write=lambda: authorize_hooks(
                context, journal.get(owner.request_id), actor_id, fresh=True
            ),
        )
        authorize_hooks(context, owner, actor_id, fresh=True)
    item = store.create(owner, sealed)
    dispatch(context, owner, item)
    return None
