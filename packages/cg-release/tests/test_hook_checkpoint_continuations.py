"""Real post-publication checkpoint continuations retain effects but renew authority."""

from contextlib import nullcontext

import pytest
from hook_continuation_probe import assert_prefix, revoke_after
from profile_transport import ProfileTransport
from test_phase5_transport import publisher
from test_profile_lifecycle import context, prepared
from test_profile_lifecycle import published_profile as published_profile
from test_profile_stranded_lifecycle import deploy_current

from cg_release.composition_journal import CompositionJournal
from cg_release.events import ControllerError
from cg_release.hooks import selected_profile
from cg_release.profile_docs import docs_step
from cg_release.profile_evidence import evidence_step
from cg_release.recovery import finish_published


@pytest.fixture
def published_without_hooks(tmp_path, monkeypatch, capsys, installed_profile, request):
    world = ProfileTransport(tmp_path)
    locator, nonce = prepared(world, monkeypatch, capsys, tmp_path)
    world.begin_publication()
    code, value = publisher(
        world, monkeypatch, capsys, tmp_path, locator, nonce, "seal"
    )
    assert code == 0, value
    if getattr(request, "param", False):
        world.checkpoint_fault = ("publication-owner-release-41:atomic", "before")
        with pytest.raises(KeyboardInterrupt):
            publisher(world, monkeypatch, capsys, tmp_path, locator, nonce, "publish")
        capsys.readouterr()
    else:
        code, value = publisher(
            world, monkeypatch, capsys, tmp_path, locator, nonce, "publish"
        )
        assert code == 0, value
    ctx = context(world, locator, tmp_path)
    record = ctx.journal.get(locator)
    assert record.published and "profile-evidence-inputs" not in record.evidence
    return world, locator, ctx


@pytest.mark.parametrize("principal", [None, "requester", "resumer"])
@pytest.mark.parametrize(
    "point", ["inputs-intent", "pr-created", "pr-result", "binding-intent"]
)
def test_evidence_continuations_recheck_before_each_journal_operation(
    published_without_hooks, principal, point
):
    world, locator, ctx = published_without_hooks
    record = ctx.journal.get(locator)
    actor = (
        None
        if principal is None
        else (record.request.requester_id if principal == "requester" else 8)
    )
    targets = {
        "inputs-intent": "profile-evidence-inputs",
        "pr-result": "profile-evidence-pr",
        "binding-intent": "profile-evidence-binding",
    }

    def selected(event):
        return event["audit"]["operation"] == targets.get(point) and (
            (event["record"].get("intent") is None) == (point == "pr-result")
        )

    probe = revoke_after(ctx.journal, world.roles, actor, selected)
    original, created = ctx.api.runner, len(world.prs)

    def after_pr(tool, argv, **kwargs):
        value = original(tool, argv, **kwargs)
        if (
            point == "pr-created"
            and argv[:3] == ["api", "--method", "POST"]
            and argv[-1] == f"repos/{world.slug}/pulls"
            and actor
        ):
            world.roles[actor] = "read"
            probe["revoked"] = True
        return value

    ctx.api.runner = after_pr
    with pytest.raises(ControllerError, match="authority") if actor else nullcontext():
        assert (
            evidence_step(
                ctx,
                record,
                selected_profile(ctx.policy).attestation,
                resuming_actor_id=8,
            )
            is None
        )
    current = ctx.journal.get(locator)
    assert_prefix(ctx.journal, probe)
    if actor:
        assert probe["revoked"] and "profile-evidence-binding" not in current.evidence
        if point == "inputs-intent":
            assert "profile-evidence-inputs" not in current.evidence
            assert len(world.prs) == created
        elif point == "pr-created":
            assert "profile-evidence-pr" not in current.evidence
            assert current.intent["operation"] == "profile-evidence-pr"
        elif point == "pr-result":
            assert "profile-evidence-pr" in current.evidence and current.intent is None
        else:
            assert current.intent["operation"] == "profile-evidence-binding"
    else:
        assert (
            "profile-evidence-binding" in current.evidence
            and len(world.prs) == created + 1
        )


@pytest.mark.parametrize("principal", [None, "requester", "resumer"])
@pytest.mark.parametrize("point", ["namespace-intent", "namespace-result"])
def test_namespace_checkpoint_cannot_authorize_next_composition(
    published_without_hooks, principal, point
):
    world, locator, ctx = published_without_hooks
    record = ctx.journal.get(locator)
    actor = (
        None
        if principal is None
        else (record.request.requester_id if principal == "requester" else 8)
    )
    probe = revoke_after(
        ctx.journal,
        world.roles,
        actor,
        lambda e: (
            e["audit"]["operation"] == "profile-docs-journal"
            and ((e["record"].get("intent") is None) == (point == "namespace-result"))
        ),
    )
    before = list(world.dispatches)
    with pytest.raises(ControllerError, match="authority") if actor else nullcontext():
        assert docs_step(ctx, record, resuming_actor_id=8) is None
    assert_prefix(ctx.journal, probe)
    if actor:
        assert probe["revoked"] and not CompositionJournal(ctx.journal).records()
        assert world.dispatches == before
        if point == "namespace-intent":
            assert "profile-docs-journal" not in ctx.journal.get(locator).evidence
    else:
        assert len(CompositionJournal(ctx.journal).records()) == 1


@pytest.mark.parametrize("principal", [None, "requester", "resumer"])
@pytest.mark.parametrize("point", ["deployment-read", "completion-intent"])
def test_complete_hooks_renews_authority_after_verification_and_intent(
    published_profile, tmp_path, monkeypatch, principal, point
):
    world, locator = published_profile
    ctx = context(world, locator, tmp_path)
    record = ctx.journal.get(locator)
    acting = CompositionJournal(ctx.journal).records()[-1].ticket["authority_actor_id"]
    actor = (
        None
        if principal is None
        else (record.request.requester_id if principal == "requester" else acting)
    )
    deploy_current(world, ctx, locator, tmp_path / "final-docs", monkeypatch, 55)
    world.merge()
    ctx = context(world, locator, tmp_path)
    probe = revoke_after(
        ctx.journal,
        world.roles,
        actor if point == "completion-intent" else None,
        lambda e: (
            e["audit"]["operation"] == "publication-hooks"
            and e["record"].get("intent") is not None
        ),
    )
    original = world.get

    def after_deployment(endpoint, **kwargs):
        value = original(endpoint, **kwargs)
        if (
            point == "deployment-read"
            and endpoint == "deployments/900/statuses"
            and actor
        ):
            world.roles[actor] = "read"
            probe["revoked"] = True
        return value

    world.get = after_deployment
    with pytest.raises(ControllerError, match="authority") if actor else nullcontext():
        assert (
            finish_published(
                ctx, ctx.journal.get(locator), resuming_actor_id=acting
            ).state
            == "complete"
        )
    assert_prefix(ctx.journal, probe)
    if actor:
        current = ctx.journal.get(locator)
        assert probe["revoked"] and current.state == "published"
        assert "publication-hooks" not in current.evidence


@pytest.mark.parametrize("published_without_hooks", [True], indirect=True)
@pytest.mark.parametrize("principal", [None, "requester", "resumer"])
def test_owner_release_after_run_read_requires_current_authority(
    published_without_hooks, principal
):
    world, locator, ctx = published_without_hooks
    record = ctx.journal.get(locator)
    actor = (
        None
        if principal is None
        else (record.request.requester_id if principal == "requester" else 8)
    )
    run_id = 41
    world.publication_runs[run_id].update(status="completed", conclusion="success")
    world.wall_time += 3601
    original, revoked = world.get, False
    probe = revoke_after(ctx.journal, world.roles, None, lambda e: False)

    def after_run(endpoint, **kwargs):
        nonlocal revoked
        value = original(endpoint, **kwargs)
        if endpoint == f"actions/runs/{run_id}" and actor:
            world.roles[actor] = "read"
            revoked = True
        return value

    world.get = after_run
    with pytest.raises(ControllerError, match="authority") if actor else nullcontext():
        finish_published(ctx, record, resuming_actor_id=8)
    assert_prefix(ctx.journal, probe)
    if actor:
        assert (
            revoked
            and f"publication-owner-release-{run_id}"
            not in ctx.journal.get(locator).evidence
        )
