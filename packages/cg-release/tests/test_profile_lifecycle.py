"""Actual GPID CLI, journal, provider, worker, process and evidence PR lifecycle."""

import hashlib
import json

import pytest
from profile_transport import ProfileTransport, snapshot_bytes
from test_phase5_transport import publisher
from test_worker_e2e import start, worker

from cg_release import build_worker, publish_worker, source
from cg_release.composition_journal import CompositionJournal
from cg_release.context import context_for
from cg_release.github import GitHubReads
from cg_release.publication_credentials import role_runner


def connect(world, monkeypatch):
    """Replace only process/transport and wall-clock boundaries, never verifiers."""
    monkeypatch.setattr(source, "run_process", world.run)
    monkeypatch.setitem(GitHubReads.__init__.__kwdefaults__, "runner", world.run)
    monkeypatch.setattr(
        publish_worker, "role_runner", lambda role: role_runner(role, runner=world.run)
    )
    monkeypatch.setattr(publish_worker.time, "time", lambda: world.wall_time)


def context(world, locator, tmp_path, *, writable=True):
    return context_for(
        locator,
        cwd=tmp_path,
        clock=world.clock,
        deadline=world.clock() + 120,
        writable=writable,
    )


def prepared(
    world, monkeypatch, capsys, tmp_path, *, version="1.1.0", register_builds=True
):
    connect(world, monkeypatch)
    locator = start(world, capsys, version=version)
    for state in ["queued", "awaiting-review"]:
        code, result = worker(world, monkeypatch, capsys, locator)
        assert code == 0 and result["observed"] == state, result
    assert len(world.prs) == 1 and not world.publication_writes
    world.merge()
    for state in ["building", "building"]:
        code, result = worker(world, monkeypatch, capsys, locator)
        assert code == 0 and result["observed"] == state, result
    current = context(world, locator, tmp_path).journal.get(locator)
    tickets = [v for k, v in current.evidence.items() if k.startswith("build-request-")]
    assert len(tickets) == 2
    if not register_builds:
        return locator, tickets
    for index, sealed in enumerate(sorted(tickets, key=lambda t: t["workflow_path"])):
        run_id = 21 + index
        world.begin_build(sealed, run_id)
        env = world.environment()
        env.update(
            GITHUB_RUN_ID=str(run_id),
            GITHUB_ACTOR_ID="77",
            GITHUB_WORKFLOW_REF=f"{world.slug}/{sealed['workflow_path']}@refs/heads/main",
            GITHUB_OUTPUT=str(tmp_path / "build-output"),
        )
        for key, value in env.items():
            monkeypatch.setenv(key, value)
        assert (
            build_worker.main(
                [
                    "register",
                    "--request-id",
                    locator,
                    "--nonce",
                    sealed["dispatch_nonce"],
                ]
            )
            == 0
        )
        capsys.readouterr()
        world.finish_build("v" + version)
        code, result = worker(world, monkeypatch, capsys, locator)
        assert code == 0, result
    code, result = worker(world, monkeypatch, capsys, locator)
    assert code == 0 and result["observed"] == "awaiting-approval", result
    assert not world.publication_writes and len(world.prs) == 1
    return locator, world.dispatches[-1]["inputs"]["nonce"]


@pytest.fixture
def published_profile(monkeypatch, capsys, tmp_path, installed_profile):
    world = ProfileTransport(tmp_path)
    locator, nonce = prepared(world, monkeypatch, capsys, tmp_path)
    world.begin_publication()
    code, result = publisher(
        world, monkeypatch, capsys, tmp_path, locator, nonce, "seal"
    )
    assert code == 0, json.dumps(result)
    assert not world.publication_writes
    code, result = publisher(
        world, monkeypatch, capsys, tmp_path, locator, nonce, "publish"
    )
    assert code == 0 and result["observed"] == "published", json.dumps(result)
    code, result = worker(world, monkeypatch, capsys, locator)
    assert code == 0 and result["observed"] == "published", json.dumps(result)
    return world, locator


def test_real_lifecycle_requires_exact_committed_evidence_and_deployment(
    published_profile, monkeypatch, tmp_path, capsys
):
    from cg_release.profile_deploy import authorize_deployment
    from cg_release.profile_worker import compose, register
    from cg_release.recovery import finish_published

    world, locator = published_profile
    ctx = context(world, locator, tmp_path)
    record = ctx.journal.get(locator)
    original_receipt = record.evidence["publication-receipt"]
    release_sha = original_receipt["release_sha"]
    tree = world.prep_commits[release_sha]["tree"]["sha"]
    entries = {r["path"]: r["sha"] for r in world.git.flat[tree]["tree"]}
    assert (
        world.objects[entries["releases/v1.1.0.json"]]
        == world.objects[entries["releases/latest.json"]]
    )
    assert len(world.prs) == 2 and world.tags["v1.1.0"]["commit"] == release_sha
    assert record.state == "published"
    world.merge()
    item = CompositionJournal(ctx.journal).records()[-1]
    world.begin_docs(item)
    env = world.environment()
    env.update(
        GITHUB_RUN_ID="55",
        GITHUB_ACTOR_ID="77",
        GITHUB_WORKFLOW_REF=f"{world.slug}/{item.ticket['workflow_path']}@refs/heads/main",
    )
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    register(ctx, record, item.ticket["nonce"], env)
    dev = tmp_path / "dev-artifact"
    dev.mkdir()
    (dev / "dev-docs.json").write_bytes(
        snapshot_bytes(None, item.ticket["dev_sha"], 55, "dev")
    )
    before_downloads = len(world.downloads)
    output = compose(ctx, record, item.ticket["nonce"], tmp_path / "composition")
    assert len(world.downloads) - before_downloads == 2
    manifest = (tmp_path / "composition/deployment/.docs-deployment.json").read_bytes()
    assert hashlib.sha256(manifest).hexdigest() == output["manifest_sha256"]
    env["EXPECTED_MANIFEST"] = output["manifest_sha256"]
    assert authorize_deployment(ctx, record, item.ticket["nonce"], env) == output
    assert finish_published(ctx, ctx.journal.get(locator)).state == "published"
    world.deploy_docs()
    final = finish_published(ctx, ctx.journal.get(locator))
    assert final.state == "complete" and set(final.evidence["publication-hooks"]) == {
        "docs",
        "evidence",
    }
    assert final.evidence["publication-receipt"] == original_receipt
    binding = final.evidence["profile-evidence-binding"]
    assert len(final.evidence["profile-evidence-pr"]["edits"]) == 9
    from cg_release.profile_attestations import attestation_edits
    from cg_release.source_blobs import commit_tree, read_blobs

    rows = final.evidence["profile-evidence-pr"]["edits"]
    actual = read_blobs(
        ctx.api, commit_tree(ctx.api, binding["head"]), [r["path"] for r in rows]
    )
    path = ".github/shared/skill-management/release-attestations/v1.1.0.json"
    _, expected_edits = attestation_edits(
        ctx.api,
        commit_tree(ctx.api, final.evidence["profile-evidence-inputs"]["base"]),
        path,
        actual[path].content,
    )
    assert len(expected_edits) == 9
    assert {r.path: r.content for r in expected_edits} == {
        p: b.content for p, b in actual.items()
    }
    assert binding["head"] != release_sha
    assert json.loads(manifest)["stableTag"] == "v1.1.0"


@pytest.mark.parametrize("actor", [7, 456])
def test_delayed_actor_revocation_prevents_all_worker_effects(
    published_profile, tmp_path, actor
):
    from cg_release.events import ControllerError
    from cg_release.profile_worker import register

    world, locator = published_profile
    ctx = context(world, locator, tmp_path)
    item = CompositionJournal(ctx.journal).records()[-1]
    world.roles[actor] = "read"
    before = world.writes
    with pytest.raises(ControllerError):
        register(ctx, ctx.journal.get(locator), item.ticket["nonce"], {})
    assert world.writes == before


def test_missing_adopted_stable_snapshot_blocks_start_before_any_mutation(
    monkeypatch, tmp_path, capsys, installed_profile
):
    from cg_release import cli

    world = ProfileTransport(tmp_path, baseline=False)
    connect(world, monkeypatch)
    code = cli.main(
        ["start", "--version", "1.1.0-rc.1", "--branch", "feature", "--yes", "--json"],
        clock=world.clock,
    )
    result = json.loads(capsys.readouterr().out.splitlines()[-1])
    assert code != 0 and result["code"] == "E_DOCS_STABLE"
    assert (
        world.writes == 0
        and not world.issues
        and not world.prep_writes
        and not world.publication_writes
    )


def test_first_maintenance_cannot_hide_newer_adopted_stable(
    monkeypatch, tmp_path, capsys, installed_profile
):
    from cg_release import cli
    from cg_release.models import Policy, canonical_bytes, load_record

    world = ProfileTransport(tmp_path, baseline=False)
    raw = world.policy.model_dump(mode="json")
    raw["bootstrap"].append(
        {**raw["bootstrap"][0], "release_id": 72, "tag": "v1.9.0", "version": "1.9.0"}
    )
    raw["release_lines"] = [
        {
            "id": "maintenance",
            "branches": ["feature"],
            "minimum_core": [1, 0, 0],
            "maximum_core_exclusive": [1, 2, 0],
        },
        {
            "id": "current",
            "branches": ["main"],
            "minimum_core": [1, 2, 0],
            "maximum_core_exclusive": [2, 0, 0],
        },
    ]
    for item in raw["bootstrap"][:-1]:
        item["line"] = "maintenance"
    world.policy = load_record(Policy, canonical_bytes(raw))
    world.release_rows.append({**world.release_rows[0], "id": 72, "tag_name": "v1.9.0"})
    world.tags["v1.9.0"] = world.tags["v1.0.0"]
    world.tag_nodes.append({**world.tag_nodes[0], "name": "v1.9.0"})
    for sha in world.branches.values():
        world.install_profile_source(sha)
    connect(world, monkeypatch)
    code = cli.main(
        [
            "start",
            "--version",
            "1.1.0",
            "--branch",
            "feature",
            "--yes",
            "--json",
            "--allow-non-deployment-branch",
            "--reason",
            "Reviewed maintenance",
        ],
        clock=world.clock,
    )
    result = json.loads(capsys.readouterr().out.splitlines()[-1])
    assert code != 0 and result["code"] == "E_DOCS_STABLE", result
    assert world.writes == 0 and not world.issues and not world.prep_writes
