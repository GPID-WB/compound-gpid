"""A fresh journal adopts an existing tag, with no inbox or preparation PR record."""

from profile_transport import ProfileTransport, snapshot_bytes
from test_phase5_transport import publisher
from test_profile_lifecycle import connect, context, prepared
from test_worker_e2e import worker

from cg_release import build_worker
from cg_release.composition_journal import CompositionJournal
from cg_release.journal import digest
from cg_release.models import canonical_bytes
from cg_release.profile_deploy import authorize_deployment
from cg_release.profile_worker import compose, register
from cg_release.recovery import finish_published
from cg_release.recovery_models import PublicTag, RecoveryDirective
from cg_release.signing import create_tag
from cg_release.stranded_recovery import recover_publication


def deploy_current(
    world, ctx, locator, root, monkeypatch, run_id, before_authorize=None
):
    root.mkdir()
    record = ctx.journal.get(locator)
    item = CompositionJournal(ctx.journal).records()[-1]
    world.begin_docs(item, run_id)
    env = world.environment()
    env.update(
        GITHUB_RUN_ID=str(run_id),
        GITHUB_ACTOR_ID="77",
        GITHUB_WORKFLOW_REF=f"{world.slug}/{item.ticket['workflow_path']}@refs/heads/main",
    )
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    register(ctx, record, item.ticket["nonce"], env)
    dev = root / "dev-artifact"
    dev.mkdir()
    (dev / "dev-docs.json").write_bytes(
        snapshot_bytes(None, item.ticket["dev_sha"], run_id, "dev")
    )
    result = compose(ctx, record, item.ticket["nonce"], root / "composition")
    env["EXPECTED_MANIFEST"] = result["manifest_sha256"]
    if before_authorize:
        before_authorize()
    authorize_deployment(ctx, record, item.ticket["nonce"], env)
    world.deploy_docs(run_id)


def test_real_stranded_admission_build_publish_docs_and_evidence_without_inbox(
    tmp_path, monkeypatch, capsys, installed_profile
):
    # Produce valid source bytes in a separate fixture repository, then import
    # only those immutable Git inputs into the initially empty target server.
    # No journal, receipt, hook result, grant or PR is copied into the target.
    source_dir, target_dir = tmp_path / "source", tmp_path / "target"
    source_dir.mkdir()
    target_dir.mkdir()
    source = ProfileTransport(source_dir)
    locator, _ = prepared(source, monkeypatch, capsys, source_dir)
    original = context(source, locator, source_dir).journal.get(locator)
    release_sha = original.evidence["review-binding"]["release_sha"]
    release_tree = original.evidence["review-binding"]["release_tree"]
    files = {
        r["path"]: source.objects[r["sha"]]
        for r in source.git.flat[release_tree]["tree"]
    }
    world = ProfileTransport(target_dir)
    assert world.git.tree(files) == release_tree
    world.objects.update(world.git.blobs)
    world.trees.update(world.git.trees)
    world.prep_commits[release_sha] = source.prep_commits[release_sha]
    world.branches["feature"] = release_sha
    tag = create_tag(
        original.request.tag,
        release_sha,
        "Fixture",
        "fixture@example.invalid",
        1789171200,
    )
    world.tags[original.request.tag] = {"oid": tag["oid"], "commit": release_sha}
    world.tag_text[tag["oid"]] = tag["text"]
    world.tag_nodes.append(
        {
            "name": original.request.tag,
            "target": {"oid": tag["oid"], "__typename": "Tag"},
        }
    )
    connect(world, monkeypatch)
    get = world.get

    def independent_source_ci(endpoint, **kwargs):
        value = get(endpoint, **kwargs)
        if endpoint == "actions/runs":
            value["workflow_runs"].append(
                dict(
                    id=18,
                    run_attempt=1,
                    head_sha=release_sha,
                    status="completed",
                    conclusion="success",
                    check_suite_id=15,
                    path=".github/workflows/release-controller-ci.yml",
                )
            )
            value["total_count"] += 1
        return value

    world.get = independent_source_ci
    ctx = context(world, locator, target_dir)
    assert not ctx.journal.records() and not world.issues and not world.prs
    from cg_release.source_blobs import commit_tree

    assert commit_tree(ctx.api, release_sha) == release_tree
    spec = RecoveryDirective(
        operation="stranded-publication",
        repository_id=123,
        policy_digest=digest(ctx.policy),
        reason="Reviewed exact stranded tag",
        request=original.request,
        tag=PublicTag(**tag),
        release_sha=release_sha,
        release_tree=release_tree,
        evidence_base={
            "branch": "main",
            "sha": world.branches["main"],
            "created_at": "2026-09-12T00:00:00Z",
        },
    )
    recover_publication(ctx, spec, actor_id=8, run_id=99, directive_digest=digest(spec))
    recovered = ctx.journal.get(locator)
    assert (
        recovered.receipt is None
        and "pr_number" not in recovered.evidence["review-binding"]
    )
    for _ in range(2):
        code, result = worker(world, monkeypatch, capsys, locator)
        assert code == 0, result
    tickets = [
        v
        for k, v in ctx.journal.get(locator).evidence.items()
        if k.startswith("build-request-")
    ]
    assert len(tickets) == 2
    for n, sealed in enumerate(sorted(tickets, key=lambda t: t["workflow_path"])):
        run_id = 21 + n
        world.begin_build(sealed, run_id)
        env = world.environment()
        env.update(
            GITHUB_RUN_ID=str(run_id),
            GITHUB_ACTOR_ID="77",
            GITHUB_WORKFLOW_REF=f"{world.slug}/{sealed['workflow_path']}@refs/heads/main",
            GITHUB_OUTPUT=str(target_dir / "build-output"),
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
        world.finish_build(original.request.tag)
        code, result = worker(world, monkeypatch, capsys, locator)
        assert code == 0, result
    code, result = worker(world, monkeypatch, capsys, locator)
    assert code == 0 and result["observed"] == "awaiting-approval", result
    nonce = world.dispatches[-1]["inputs"]["nonce"]
    world.begin_publication()
    for operation in ["seal", "publish"]:
        code, result = publisher(
            world, monkeypatch, capsys, target_dir, locator, nonce, operation
        )
        assert code == 0, result
    code, result = worker(world, monkeypatch, capsys, locator)
    assert code == 0 and result["observed"] == "published", result
    ctx = context(world, locator, target_dir)
    record = ctx.journal.get(locator)
    receipt = canonical_bytes(record.evidence["publication-receipt"])
    deploy_current(world, ctx, locator, target_dir / "first-docs", monkeypatch, 55)
    world.merge()
    ctx = context(world, locator, target_dir)
    # Evidence merged into default advances the controller revision. The exact
    # new revision must compose/deploy again, without rebuilding release assets.
    assert finish_published(ctx, ctx.journal.get(locator)).state == "published"
    assert len(CompositionJournal(ctx.journal).records()) == 2
    deploy_current(world, ctx, locator, target_dir / "second-docs", monkeypatch, 56)
    assert finish_published(ctx, ctx.journal.get(locator)).state == "complete"
    final = ctx.journal.get(locator)
    assert (
        final.receipt is None
        and canonical_bytes(final.evidence["publication-receipt"]) == receipt
    )
    assert world.tags[original.request.tag]["oid"] == tag["oid"]
    assert world.publication_writes.count("tag") == 0
    assert len(world.prs) == 1 and not world.issues
    assert len(final.evidence["profile-evidence-recovery-99-pr"]["edits"]) == 9
