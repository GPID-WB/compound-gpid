"""Valid deployed docs do not waive an independent evidence PR failure."""

import pytest
from profile_transport import snapshot_bytes
from test_profile_lifecycle import context
from test_profile_lifecycle import published_profile as published_profile

from cg_release.composition_journal import CompositionJournal
from cg_release.events import ControllerError
from cg_release.profile_deploy import authorize_deployment
from cg_release.profile_docs import docs_step
from cg_release.profile_worker import compose, register
from cg_release.recovery import finish_published


@pytest.mark.parametrize(
    "damage",
    [
        "open",
        "review",
        "canonical",
        "native",
        "ownership",
        "missing-canonical",
        "missing-native",
        "missing-ownership",
    ],
)
def test_deployed_docs_cannot_complete_with_invalid_evidence(
    published_profile, tmp_path, monkeypatch, damage
):
    world, locator = published_profile
    ctx = context(world, locator, tmp_path)
    record = ctx.journal.get(locator)
    receipt = record.evidence["publication-receipt"]
    store = CompositionJournal(ctx.journal)
    item = store.records()[-1]
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
    result = compose(ctx, record, item.ticket["nonce"], tmp_path / "composition")
    env["EXPECTED_MANIFEST"] = result["manifest_sha256"]
    authorize_deployment(ctx, record, item.ticket["nonce"], env)
    world.deploy_docs()
    assert docs_step(ctx, ctx.journal.get(locator))["verified"] is True
    if damage != "open":
        world.merge()
    get = world.get

    def altered(endpoint, **kwargs):
        value = get(endpoint, **kwargs)
        if (
            damage == "review"
            and endpoint.startswith("pulls/")
            and endpoint.endswith("/reviews")
        ):
            return [{**r, "commit_id": "0" * 40} for r in value]
        return value

    world.get = altered
    category = damage.removeprefix("missing-")
    if category in {"canonical", "native", "ownership"}:
        pr = world.prs[-1]
        tree = world.prep_commits[pr["head"]["sha"]]["tree"]["sha"]
        rows = world.git.flat[tree]["tree"]
        target = next(
            r
            for r in rows
            if (
                r["path"].startswith(
                    ".github/shared/skill-management/release-attestations/"
                )
                if category == "canonical"
                else r["path"].startswith(
                    ".kilo/shared/skill-management/release-attestations/"
                )
                if category == "native"
                else r["path"] == ".kilo/.compound-gpid-generated.json"
            )
        )
        if damage.startswith("missing-"):
            files = {
                r["path"]: world.objects[r["sha"]] for r in rows if r is not target
            }
            world.prep_commits[pr["head"]["sha"]]["tree"]["sha"] = world.git.tree(files)
        else:
            # Corrupt one provider blob, retaining real verification and hashing.
            world.objects[target["sha"]] = b"altered evidence\n"
    before = list(world.publication_writes)
    try:
        assert finish_published(ctx, ctx.journal.get(locator)).state == "published"
    except ControllerError:
        assert damage != "open"
    assert ctx.journal.get(locator).state == "published"
    assert ctx.journal.get(locator).evidence["publication-receipt"] == receipt
    assert world.publication_writes == before
