"""Admitted recovery grants retain original hooks and replace immutable compositions."""

import pytest
from test_profile_lifecycle import context
from test_profile_lifecycle import published_profile as published_profile

from cg_release.composition_journal import CompositionJournal
from cg_release.events import ControllerError
from cg_release.journal import digest
from cg_release.models import canonical_bytes
from cg_release.profile_docs import docs_step
from cg_release.recovery_models import PublicTag, RecoveryDirective
from cg_release.stranded_recovery import recover_publication


def admit_grant(ctx, record, *, run_id=99, **fields):
    """Use actual admission and signed fixture journal, not seeded grants."""
    binding = record.evidence["review-binding"]
    spec = RecoveryDirective(
        operation="source-exception",
        repository_id=123,
        policy_digest=digest(ctx.policy),
        reason="Reviewed offline recovery",
        request=record.request,
        tag=PublicTag(**record.evidence["publication-tag-object"]),
        release_sha=binding["release_sha"],
        release_tree=binding["release_tree"],
        **fields,
    )
    recover_publication(
        ctx, spec, actor_id=8, run_id=run_id, directive_digest=digest(spec)
    )
    return ctx.journal.get(record.request_id)


def test_admitted_policy_recovery_replaces_terminal_composition_and_revoked_actor(
    published_profile, tmp_path
):
    world, locator = published_profile
    ctx = context(world, locator, tmp_path)
    store = CompositionJournal(ctx.journal)
    old = store.records()[-1]
    world.begin_docs(old)
    world.docs_runs[55].update(status="completed", conclusion="cancelled")
    ctx.policy = ctx.policy.model_copy(
        update={
            "profile": ctx.policy.profile.model_copy(update={"composition_retries": 4})
        }
    )
    world.policy = ctx.policy
    record = admit_grant(ctx, ctx.journal.get(locator))
    world.roles[old.ticket["authority_actor_id"]] = "read"
    receipt = canonical_bytes(record.evidence["publication-receipt"])
    docs_step(ctx, record)
    rows = store.records()
    assert len(rows) == 2 and rows[0].ticket == old.ticket
    assert rows[1].ticket["authority_actor_id"] == 8
    assert (
        canonical_bytes(ctx.journal.get(locator).evidence["publication-receipt"])
        == receipt
    )


def test_replacement_build_cannot_remove_original_profile_after_admitted_grant(
    published_profile, tmp_path
):
    from cg_release.build_stage import make_ticket

    world, locator = published_profile
    ctx = context(world, locator, tmp_path)
    ctx.policy = ctx.policy.model_copy(update={"gpid_profile": None, "profile": None})
    world.policy = ctx.policy
    record = admit_grant(ctx, ctx.journal.get(locator))
    before = world.writes
    with pytest.raises(ControllerError, match="original.*hook|profile"):
        make_ticket(ctx, record, nonce="c" * 32, resuming_actor_id=8)
    assert world.writes == before


def test_admitted_deleted_source_recovery_uses_explicit_evidence_base(
    tmp_path, monkeypatch, capsys, installed_profile
):
    from profile_transport import ProfileTransport
    from test_phase5_transport import publisher
    from test_profile_lifecycle import prepared

    from cg_release.hooks import selected_profile
    from cg_release.profile_evidence import evidence_step

    world = ProfileTransport(tmp_path)
    locator, nonce = prepared(world, monkeypatch, capsys, tmp_path)
    world.begin_publication()
    for operation in ["seal", "publish"]:
        code, result = publisher(
            world, monkeypatch, capsys, tmp_path, locator, nonce, operation
        )
        assert code == 0, result
    ctx = context(world, locator, tmp_path)
    record = ctx.journal.get(locator)
    assert "profile-evidence-inputs" not in record.evidence
    record = admit_grant(
        ctx,
        record,
        allow_source_exception=True,
        evidence_base={
            "branch": "main",
            "sha": world.branches["main"],
            "created_at": "2026-09-12T00:00:00Z",
        },
    )
    del world.branches[record.request.source_branch]
    before = list(world.publication_writes)
    assert evidence_step(ctx, record, selected_profile(ctx.policy).attestation) is None
    current = ctx.journal.get(locator)
    inputs = current.evidence["profile-evidence-recovery-99-inputs"]
    assert inputs["branch"] == "main" and inputs["recovery_review"].startswith(
        "Reviewed recovery "
    )
    assert world.prs[-1]["base"]["ref"] == "main"
    assert world.publication_writes == before


def test_admitted_recovery_preserves_old_evidence_and_creates_new_attempt(
    published_profile, tmp_path
):
    from cg_release.hooks import selected_profile
    from cg_release.profile_evidence import evidence_step

    world, locator = published_profile
    ctx = context(world, locator, tmp_path)
    record = ctx.journal.get(locator)
    old = {
        k: canonical_bytes(v)
        for k, v in record.evidence.items()
        if k.startswith("profile-evidence-") or k == "publication-receipt"
    }
    old_pr = canonical_bytes(world.prs[-1])
    record = admit_grant(
        ctx,
        record,
        allow_source_exception=True,
        evidence_base={
            "branch": "main",
            "sha": world.branches["main"],
            "created_at": "2026-09-12T00:00:00Z",
        },
    )
    del world.branches[record.request.source_branch]
    before, count = list(world.publication_writes), len(world.prs)
    profile = selected_profile(ctx.policy)
    assert evidence_step(ctx, record, profile.attestation) is None
    assert len(world.prs) == count + 1
    assert canonical_bytes(world.prs[-2]) == old_pr
    current = ctx.journal.get(locator)
    assert all(canonical_bytes(current.evidence[k]) == v for k, v in old.items())
    assert evidence_step(ctx, current, profile.attestation) is None
    assert len(world.prs) == count + 1
    world.merge()
    ctx = context(world, locator, tmp_path)
    assert evidence_step(ctx, ctx.journal.get(locator), profile.attestation)["verified"]
    assert world.publication_writes == before


def test_prereceipt_tag_recovery_cannot_select_generic_replacement_build(
    tmp_path, monkeypatch, capsys, installed_profile
):
    from profile_transport import ProfileTransport
    from test_phase5_transport import publisher
    from test_profile_lifecycle import prepared

    from cg_release.build_stage import make_ticket

    world = ProfileTransport(tmp_path)
    locator, nonce = prepared(world, monkeypatch, capsys, tmp_path)
    world.begin_publication()
    assert (
        publisher(world, monkeypatch, capsys, tmp_path, locator, nonce, "seal")[0] == 0
    )
    world.fault = ("tag", "after")
    with pytest.raises(KeyboardInterrupt):
        publisher(world, monkeypatch, capsys, tmp_path, locator, nonce, "publish")
    ctx = context(world, locator, tmp_path)
    record = ctx.journal.get(locator)
    assert "publication-receipt" not in record.evidence
    assert record.evidence["required-hooks"] == {"stages": ["docs", "evidence"]}
    ctx.policy = ctx.policy.model_copy(update={"gpid_profile": None, "profile": None})
    world.policy = ctx.policy
    record = admit_grant(ctx, record)
    before = list(world.publication_writes)
    with pytest.raises(ControllerError, match="original required profile"):
        make_ticket(ctx, record, nonce="d" * 32, resuming_actor_id=8)
    assert world.publication_writes == before


def test_final_run_read_cannot_outlast_admitted_grant_principal(
    published_profile, tmp_path, monkeypatch
):
    from test_profile_stranded_lifecycle import deploy_current

    world, locator = published_profile
    ctx = context(world, locator, tmp_path)
    admit_grant(ctx, ctx.journal.get(locator))
    before = list(world.publication_writes)

    def start_revocation():
        get = world.get

        def revoked(endpoint, **kwargs):
            value = get(endpoint, **kwargs)
            if endpoint == "actions/runs/55":
                world.roles[8] = "read"
            return value

        world.get = revoked

    with pytest.raises(ControllerError, match="grant|authority"):
        deploy_current(
            world,
            ctx,
            locator,
            tmp_path / "revoked-docs",
            monkeypatch,
            55,
            start_revocation,
        )
    assert not world.deployments and world.publication_writes == before
