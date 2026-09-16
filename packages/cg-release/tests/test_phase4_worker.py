"""Real Phase 4 lifecycle; only provider, time and environment are fake."""

import pytest
from phase4_transport import Phase4Transport
from test_worker_e2e import start, worker

from cg_release import build_worker, source
from cg_release.build_control import ticket
from cg_release.context import context_for
from cg_release.github import GitHubReads


@pytest.mark.parametrize("lost", [None, "pulls"])
def test_real_phase4_pipeline_and_reuse_without_duplicate_build(
    monkeypatch, tmp_path, capsys, lost
):
    world = Phase4Transport(tmp_path)
    world.lost_preparation = lost
    monkeypatch.setattr(source, "run_process", world.run)
    monkeypatch.setitem(GitHubReads.__init__.__kwdefaults__, "runner", world.run)
    locator = start(world, capsys)
    assert worker(world, monkeypatch, capsys, locator)[1]["observed"] == "queued"
    code, event = worker(world, monkeypatch, capsys, locator)
    assert code == 0 and event["observed"] == "awaiting-review", event
    world.merge()
    code, event = worker(world, monkeypatch, capsys, locator)
    assert code == 0 and event["observed"] == "building", event
    code, event = worker(world, monkeypatch, capsys, locator)
    assert code == 0 and event["step"] == "build-dispatch-1", event
    context = context_for(
        locator, cwd=tmp_path, deadline=world.clock() + 120, clock=world.clock
    )
    _, sealed = ticket(context.journal.get(locator))
    world.begin_build(sealed)
    env = world.environment()
    env.update(
        GITHUB_RUN_ID="21",
        GITHUB_ACTOR_ID="77",
        GITHUB_WORKFLOW_REF=f"{world.slug}/{sealed['workflow_path']}@refs/heads/main",
        GITHUB_OUTPUT=str(tmp_path / "job-output"),
    )
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    assert (
        build_worker.main(
            ["register", "--request-id", locator, "--nonce", sealed["dispatch_nonce"]]
        )
        == 0
    )
    world.finish_build()
    code, event = worker(world, monkeypatch, capsys, locator)
    assert code == 0 and event["observed"] == "awaiting-approval", event
    count = len(world.dispatches)
    writes = list(world.prep_writes)
    code, event = worker(world, monkeypatch, capsys, locator)
    assert code == 0 and event["observed"] == "awaiting-approval", event
    # Phase 5 adds one protected-publication dispatch, not a duplicate build.
    assert count == 1 and len(world.dispatches) == 2 and world.prep_writes == writes
    assert world.dispatches[-1]["inputs"]["request_id"] == locator
    code, event = worker(world, monkeypatch, capsys, locator)
    assert code == 0 and len(world.dispatches) == 2, event
    world.build["run_attempt"] = 2
    code, event = worker(world, monkeypatch, capsys, locator)
    assert code == 2 and event["code"] == "E_BUILD_EVIDENCE", event
