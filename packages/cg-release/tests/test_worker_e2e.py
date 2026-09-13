"""Real Phase 3 transport integration; later Phase 4 execution is isolated."""

import json

import pytest
from worker_transport import WorkerTransport

from cg_release import cli, controller, source
from cg_release.github import GitHubReads


@pytest.fixture
def world(monkeypatch, tmp_path):
    server = WorkerTransport(tmp_path)
    monkeypatch.setattr(source, "run_process", server.run)
    monkeypatch.setitem(GitHubReads.__init__.__kwdefaults__, "runner", server.run)
    # Keep the original admission/replay/queue assertions scoped to Phase 3.
    # test_phase4_worker executes the new router and transports without this stub.
    monkeypatch.setattr(controller, "advance", lambda context, record, **kwargs: record)
    return server


def start(world, capsys, *, version="1.0.0"):
    code = cli.main(
        [
            "start",
            "--version",
            version,
            "--branch",
            "feature",
            "--yes",
            "--json",
            "--allow-non-deployment-branch",
            "--reason",
            "Reviewed override",
        ],
        clock=world.clock,
    )
    events = [json.loads(line) for line in capsys.readouterr().out.splitlines()]
    assert code == 0, json.dumps(events)
    assert [event["kind"] for event in events] == [
        "preview",
        "submission-intent",
        "receipt",
    ]
    return events[-1]["request_id"]


def worker(world, monkeypatch, capsys, locator=None, *, operation="reconcile"):
    for key, value in world.environment().items():
        monkeypatch.setenv(key, value)
    args = ["--operation", operation]
    if locator:
        args += ["--request-id", locator]
    code = controller.main(args, clock=world.clock)
    events = [json.loads(line) for line in capsys.readouterr().out.splitlines()]
    return code, events[-1]


def test_confirmed_start_worker_second_machine_status_and_resume(
    world, monkeypatch, capsys
):
    locator = start(world, capsys)
    code, event = worker(world, monkeypatch, capsys, locator)
    assert code == 0 and event["step"] == "admitted", event
    assert world.writes == 1
    world.calls.clear()
    assert cli.main(["status", locator, "--json"], clock=world.clock) == 0
    assert json.loads(capsys.readouterr().out)["observed"] == "queued"
    assert all(tool != "git" for tool, _ in world.calls)
    world.actor = 456
    assert cli.main(["resume", locator, "--json"], clock=world.clock) == 0
    assert json.loads(capsys.readouterr().out)["observed"] == "reconciliation-requested"
    assert world.dispatches == [
        {"ref": "main", "inputs": {"operation": "reconcile", "request_id": locator}}
    ]
    assert worker(world, monkeypatch, capsys, locator)[0] == 0
    assert world.writes == 1 and len(world.issues) == 1


def test_direct_manual_override_rejects_write_only_resumer(world, monkeypatch, capsys):
    locator = start(world, capsys)
    world.roles[456] = "write"
    code, event = worker(world, monkeypatch, capsys, locator)
    assert code == 2 and event["code"] == "E_AUTHORITY"
    assert world.writes == 0


def test_manual_resumer_revocation_during_replay_blocks_commit(
    world, monkeypatch, capsys
):
    locator = start(world, capsys)
    world.resumer_checks = 0
    world.resumer_revoke_after = 2
    code, event = worker(world, monkeypatch, capsys, locator)
    assert code == 2 and event["code"] == "E_AUTHORITY"
    assert world.writes == 0


@pytest.mark.parametrize("change", ["policy", "source", "role", "tag"])
def test_worker_revalidates_stale_inputs_and_external_tag_race(
    world, monkeypatch, capsys, change
):
    locator = start(world, capsys)
    expected = "E_STALE_PROPOSAL"
    if change == "policy":
        world.install_source("c" * 40)
        world.branches["main"] = "c" * 40
    elif change == "source":
        world.install_source("e" * 40)
        world.branches["feature"] = "e" * 40
    elif change == "role":
        world.roles[7] = "read"
        expected = "E_AUTHORITY"
    else:
        world.tag_nodes = [
            {"name": "v1.0.0", "target": {"__typename": "Commit", "oid": "b" * 40}}
        ]
        expected = "E_INCOMPLETE_PUBLICATION"
    code, event = worker(world, monkeypatch, capsys, locator)
    assert code == 2 and event["code"] == expected, event
    assert world.writes == 0


def test_scheduled_scan_skips_budget_exhaustion_and_reaches_healthy_request(
    world, monkeypatch, capsys
):
    first = start(world, capsys)
    world.actor = 8
    second = start(world, capsys, version="1.0.1")
    world.event = "schedule"
    world.roles[456] = "write"
    world.slow_users = {7}
    for _ in range(3):
        world.now = 0
        code, event = worker(world, monkeypatch, capsys, operation="scan")
        assert code == 0, event
        assert event["proposal"]["failures"]["1"] == "E_ITEM_DEADLINE"
        assert world.now < 120
    world.slow_users.clear()
    assert cli.main(["status", second, "--json"], clock=world.clock) == 0
    assert json.loads(capsys.readouterr().out)["step"] == "admitted"
    assert cli.main(["status", first, "--json"], clock=world.clock) == 0
    assert json.loads(capsys.readouterr().out)["code"] == "E_ITEM_DEADLINE"


def test_checkpoint_failure_replays_without_duplicate_admission(
    world, monkeypatch, capsys
):
    locator = start(world, capsys)
    world.event = "schedule"
    world.fail_checkpoint = True
    code, event = worker(world, monkeypatch, capsys, operation="scan")
    assert code == 2 and event["code"] == "E_TIMEOUT"
    assert world.writes == 1
    world.fail_checkpoint = False
    world.now = 0
    assert worker(world, monkeypatch, capsys, operation="scan")[0] == 0
    assert world.writes == 2
    assert cli.main(["status", locator, "--json"], clock=world.clock) == 0
    assert json.loads(capsys.readouterr().out)["step"] == "admitted"


def test_item_timeout_after_acceptance_is_reconciled_from_signed_journal(
    world, monkeypatch, capsys
):
    locator = start(world, capsys)
    world.event = "schedule"
    world.expire_after_acceptance = True
    code, event = worker(world, monkeypatch, capsys, operation="scan")
    assert code == 0 and event["proposal"]["failures"]["1"] == "E_ITEM_DEADLINE"
    assert world.writes == 2
    world.expire_after_acceptance = False
    world.event = "workflow_dispatch"
    assert worker(world, monkeypatch, capsys, locator)[0] == 0
    assert world.writes == 2
