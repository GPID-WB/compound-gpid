"""Adversarial data at real reader/acquisition and pre-effect worker boundaries."""

import json

import pytest
from profile_transport import ProfileTransport, snapshot_bytes
from test_profile_lifecycle import connect, context
from test_profile_lifecycle import published_profile as published_profile

from cg_release.composition_journal import CompositionJournal
from cg_release.events import ControllerError
from cg_release.github import GitHubReads
from cg_release.profile_source import source_blobs
from cg_release.profile_worker import compose, register


@pytest.mark.parametrize("location", ["main", "feature"])
def test_durable_payload_on_either_exact_tree_blocks_older_source(tmp_path, location):
    world = ProfileTransport(tmp_path)
    files = {**world.files, "releases/v1.8.0.json": b'{"tag":"v1.8.0"}\n'}
    world.install_profile_source(world.branches[location], files)
    api = GitHubReads("github.com", world.slug, cwd=tmp_path, runner=world.run)
    before = world.writes
    with pytest.raises(ControllerError, match="Durable payload"):
        source_blobs(
            api,
            world.commits[world.branches["feature"]]["commit"]["tree"]["sha"],
            "v1.1.0",
            default_tree=world.commits[world.branches["main"]]["commit"]["tree"]["sha"],
        )
    assert world.writes == before and not world.prep_writes


@pytest.mark.parametrize(
    "damage", ["dev-sha", "asset-bytes", "job", "cancelled", "expected-manifest"]
)
def test_worker_verifies_all_inputs_before_effect(
    published_profile, tmp_path, monkeypatch, damage
):
    from cg_release.profile_deploy import authorize_deployment

    world, locator = published_profile
    ctx = context(world, locator, tmp_path)
    record = ctx.journal.get(locator)
    item = CompositionJournal(ctx.journal).records()[-1]
    world.begin_docs(item)
    env = world.environment()
    env.update(
        GITHUB_RUN_ID="55",
        GITHUB_ACTOR_ID="77",
        GITHUB_WORKFLOW_REF=f"{world.slug}/{item.ticket['workflow_path']}@refs/heads/main",
    )
    register(ctx, record, item.ticket["nonce"], env)
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    dev = tmp_path / "dev-artifact"
    dev.mkdir()
    raw = snapshot_bytes(
        None, "0" * 40 if damage == "dev-sha" else item.ticket["dev_sha"], 55, "dev"
    )
    (dev / "dev-docs.json").write_bytes(raw)
    if damage == "asset-bytes":
        world.asset_rows[80]["bytes"] += b" "
    elif damage == "job":
        world.docs_jobs[55][1]["run_attempt"] = 2
    elif damage == "cancelled":
        world.docs_runs[55].update(status="completed", conclusion="cancelled")
    root = tmp_path / "composition"
    if damage == "expected-manifest":
        compose(ctx, record, item.ticket["nonce"], root)
        env["EXPECTED_MANIFEST"] = "0" * 64
        before = world.writes
        with pytest.raises(ControllerError):
            authorize_deployment(ctx, record, item.ticket["nonce"], env)
        assert world.writes == before
    else:
        before = world.writes
        with pytest.raises(ControllerError):
            compose(ctx, record, item.ticket["nonce"], root)
        assert not root.exists() and world.writes == before
    assert ctx.journal.get(locator).state == "published"


def test_uncertain_accepted_dispatch_is_discovered_and_registered_once(
    published_profile, tmp_path
):
    from cg_release.profile_docs import docs_step

    world, locator = published_profile
    ctx = context(world, locator, tmp_path)
    store = CompositionJournal(ctx.journal)
    world.begin_docs(store.records()[-1])
    world.docs_runs[55].update(status="completed", conclusion="cancelled")
    runner = ctx.api.runner
    lost = False

    def transport(tool, args, **kwargs):
        nonlocal lost
        result = runner(tool, args, **kwargs)
        if not lost and args[-1].endswith("/dispatches"):
            lost = True
            raise ControllerError(
                "E_TIMEOUT", "Synthetic response lost after acceptance."
            )
        return result

    ctx.api.runner = transport
    with pytest.raises(ControllerError):
        docs_step(ctx, ctx.journal.get(locator))
    item = store.records()[-1]
    assert item.intent and "dispatch" not in item.evidence
    world.begin_docs(item, 56)
    before = len(world.dispatches)
    assert docs_step(ctx, ctx.journal.get(locator)) is None
    env = world.environment()
    env.update(
        GITHUB_RUN_ID="56",
        GITHUB_ACTOR_ID="77",
        GITHUB_WORKFLOW_REF=f"{world.slug}/{item.ticket['workflow_path']}@refs/heads/main",
    )
    register(ctx, ctx.journal.get(locator), item.ticket["nonce"], env)
    assert len(world.dispatches) == before
    assert store.records()[-1].intent is None


def test_valid_reviewed_baseline_allows_first_prerelease_submission(
    monkeypatch, tmp_path, capsys, installed_profile
):
    from cg_release import cli

    world = ProfileTransport(tmp_path)
    connect(world, monkeypatch)
    code = cli.main(
        ["start", "--version", "1.1.0-rc.1", "--branch", "feature", "--yes", "--json"],
        clock=world.clock,
    )
    rows = [json.loads(line) for line in capsys.readouterr().out.splitlines()]
    assert code == 0 and rows[-1]["kind"] == "receipt", rows
    assert (
        len(world.issues) == 1
        and not world.prep_writes
        and not world.publication_writes
    )


def test_registered_run_removed_by_retention_uses_bounded_absence_proof(
    published_profile, tmp_path
):
    from cg_release.profile_docs import docs_step

    world, locator = published_profile
    ctx = context(world, locator, tmp_path)
    store = CompositionJournal(ctx.journal)
    item = store.records()[-1]
    world.begin_docs(item)
    env = world.environment()
    env.update(
        GITHUB_RUN_ID="55",
        GITHUB_ACTOR_ID="77",
        GITHUB_WORKFLOW_REF=f"{world.slug}/{item.ticket['workflow_path']}@refs/heads/main",
    )
    register(ctx, ctx.journal.get(locator), item.ticket["nonce"], env)
    world.deleted_doc_runs.add(55)
    del world.docs_runs[55]
    assert docs_step(ctx, ctx.journal.get(locator)) is None
    world.wall_time += 121
    assert docs_step(ctx, ctx.journal.get(locator)) is None
    world.wall_time += 121
    assert docs_step(ctx, ctx.journal.get(locator)) is None
    assert len(store.records()) == 2 and "absence" in store.records()[0].evidence
