"""Execute durable post-publication composition and replay with a real journal."""

import pytest
from test_profile_lifecycle import context
from test_profile_lifecycle import published_profile as published_profile

from cg_release.composition_journal import CompositionJournal
from cg_release.events import ControllerError
from cg_release.prepare_stage import checkpoint
from cg_release.profile_docs import docs_step
from cg_release.profile_worker import register


@pytest.fixture
def docs_context(published_profile, tmp_path):
    world, locator = published_profile
    ctx = context(world, locator, tmp_path)
    item = CompositionJournal(ctx.journal).records()[-1]
    world.begin_docs(item)
    environment = world.environment()
    environment.update(
        GITHUB_RUN_ID="55",
        GITHUB_ACTOR_ID="77",
        GITHUB_WORKFLOW_REF=f"{world.slug}/{item.ticket['workflow_path']}@refs/heads/main",
    )
    return ctx, ctx.journal.get(locator), world, item, environment


def test_dispatch_once_and_register_actual_run(docs_context):
    context, record, world, item, environment = docs_context
    before = len(world.dispatches)
    assert docs_step(context, record) is None
    assert docs_step(context, record) is None
    assert len(world.dispatches) == before
    register(context, record, item.ticket["nonce"], environment)
    assert (
        CompositionJournal(context.journal)
        .records()[-1]
        .evidence["registration"]["run_id"]
        == 55
    )
    with pytest.raises(ControllerError):
        register(
            context,
            record,
            item.ticket["nonce"],
            environment,
        )


def test_dev_advance_refreshes_composition_not_release_build(docs_context):
    context, record, world, item, environment = docs_context
    register(context, record, item.ticket["nonce"], environment)
    world.docs_runs[55].update(status="completed", conclusion="success")
    world.branches["dev"] = "e" * 40
    before = record.evidence
    assert docs_step(context, record) is None
    after = context.journal.get(record.request_id)
    assert (
        CompositionJournal(context.journal).records()[-1].ticket["dev_sha"] == "e" * 40
    )
    assert after.evidence == before


def test_complete_record_accepts_only_mutable_docs_events(
    published_profile, monkeypatch, tmp_path, capsys
):
    from test_profile_lifecycle import (
        test_real_lifecycle_requires_exact_committed_evidence_and_deployment,
    )

    test_real_lifecycle_requires_exact_committed_evidence_and_deployment(
        published_profile, monkeypatch, tmp_path, capsys
    )
    world, locator = published_profile
    ctx = context(world, locator, tmp_path)
    record = ctx.journal.get(locator)
    before = record.evidence
    world.branches["dev"] = "e" * 40
    assert docs_step(ctx, record) is None
    current = ctx.journal.get(locator)
    assert current.state == "complete" and current.evidence == before
    with pytest.raises(ControllerError):
        checkpoint(
            ctx.journal, current, "replacement-release", {"bad": True}, "complete"
        )


def test_wrong_registered_completion_run_cannot_complete(docs_context):
    context, record, world, item, environment = docs_context
    register(context, record, item.ticket["nonce"], environment)
    world.docs_runs[55].update(status="completed", conclusion="success", id=56)
    with pytest.raises(ControllerError):
        docs_step(context, record)
    assert context.journal.get(record.request_id).state == "published"
