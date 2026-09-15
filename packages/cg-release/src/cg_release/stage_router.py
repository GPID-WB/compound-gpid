"""Bounded stage routing; publication itself runs only in its protected job."""

from cg_release.build_stage import build_step
from cg_release.prepare_stage import prepare_step
from cg_release.publication_stage import publication_step


def advance(context, record, *, resuming_actor_id=None):
    """Run one durable stage, e.g. advance(context, existing_record)."""
    if record.state == "complete" and context.policy.gpid_profile:
        from cg_release.profile_docs import docs_step

        docs_step(context, record, resuming_actor_id=resuming_actor_id)
        return record
    if record.state in {"queued", "awaiting-review"}:
        return prepare_step(context, record, resuming_actor_id=resuming_actor_id)
    if record.state == "building":
        return build_step(context, record, resuming_actor_id=resuming_actor_id)
    if record.state == "awaiting-approval":
        record = build_step(context, record, resuming_actor_id=resuming_actor_id)
    if record.state == "published":
        from cg_release.recovery import finish_published

        return finish_published(context, record, resuming_actor_id=resuming_actor_id)
    if record.state in {"awaiting-approval", "publishing"}:
        return publication_step(context, record, resuming_actor_id=resuming_actor_id)
    return record
