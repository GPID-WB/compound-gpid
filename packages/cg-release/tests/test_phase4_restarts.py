"""Process loss at actual wire commits must not strand build tickets or claims."""

import base64
import json

import pytest
from phase4_transport import Phase4Transport
from test_worker_e2e import start, worker

from cg_release import build_worker, source
from cg_release.build_stage import build_step
from cg_release.context import context_for
from cg_release.events import ControllerError
from cg_release.github import GitHubReads


class ProcessStopped(BaseException):
    """Simulate process death, not a recoverable HTTP error."""


@pytest.fixture
def lifecycle(monkeypatch, tmp_path, capsys):
    world = Phase4Transport(tmp_path)
    original = world.run
    fault = {"operation": None, "after": False, "hit": False}

    def transport(tool, argv, **kwargs):
        event = None
        if tool == "gh" and argv[-1] == "graphql" and kwargs.get("input_text"):
            payload = json.loads(kwargs["input_text"])
            additions = payload["variables"]["input"]["fileChanges"]["additions"]
            event = next(
                (
                    json.loads(base64.b64decode(row["contents"]))
                    for row in additions
                    if row["path"].startswith("events/")
                ),
                None,
            )
        stop = (
            event is not None
            and event["audit"].get("operation") == fault["operation"]
            and not fault["hit"]
        )
        if stop:
            fault["hit"] = True
            if not fault["after"]:
                raise ProcessStopped
        result = original(tool, argv, **kwargs)
        if stop:
            raise ProcessStopped
        return result

    monkeypatch.setattr(source, "run_process", transport)
    monkeypatch.setitem(GitHubReads.__init__.__kwdefaults__, "runner", transport)
    locator = start(world, capsys)
    assert worker(world, monkeypatch, capsys, locator)[0] == 0
    assert (
        worker(world, monkeypatch, capsys, locator)[1]["observed"] == "awaiting-review"
    )
    world.merge()
    assert worker(world, monkeypatch, capsys, locator)[1]["observed"] == "building"

    def context():
        return context_for(
            locator, cwd=tmp_path, clock=world.clock, deadline=world.clock() + 120
        )

    def registration(sealed):
        world.begin_build(sealed)
        env = world.environment()
        env.update(
            GITHUB_RUN_ID="21",
            GITHUB_ACTOR_ID="77",
            GITHUB_WORKFLOW_REF=f"{world.slug}/{sealed['workflow_path']}@refs/heads/main",
            GITHUB_OUTPUT=str(tmp_path / "registration-output"),
        )
        for key, value in env.items():
            monkeypatch.setenv(key, value)
        return [
            "register",
            "--request-id",
            locator,
            "--nonce",
            sealed["dispatch_nonce"],
        ]

    return world, locator, context, fault, registration


@pytest.mark.parametrize("after", [False, True])
def test_initial_ticket_process_loss_resumes_without_nonce_conflict(
    lifecycle, monkeypatch, capsys, after
):
    world, locator, context, fault, _ = lifecycle
    fault.update(operation="build-request-1", after=after)
    with pytest.raises(ProcessStopped):
        worker(world, monkeypatch, capsys, locator)
    retained = context().journal.get(locator)
    assert retained.intent is None
    nonce = retained.evidence.get("build-request-1", {}).get("dispatch_nonce")
    code, event = worker(world, monkeypatch, capsys, locator)
    assert code == 0 and event["step"] == "build-dispatch-1", event
    current = context().journal.get(locator)
    assert (
        nonce is None or current.evidence["build-request-1"]["dispatch_nonce"] == nonce
    )
    events = context().journal.events()
    assert (
        len([e for e in events if e["audit"].get("operation") == "build-request-1"])
        == 1
    )


@pytest.mark.parametrize("after", [False, True])
def test_replacement_ticket_process_loss_retains_ready_evidence(
    lifecycle, monkeypatch, capsys, after
):
    world, locator, context, fault, registration = lifecycle
    assert worker(world, monkeypatch, capsys, locator)[0] == 0
    sealed = context().journal.get(locator).evidence["build-request-1"]
    assert build_worker.main(registration(sealed)) == 0
    world.finish_build()
    assert (
        worker(world, monkeypatch, capsys, locator)[1]["observed"]
        == "awaiting-approval"
    )
    original = world.get

    def expired(endpoint, **kwargs):
        result = original(endpoint, **kwargs)
        if endpoint == "actions/runs/21/artifacts":
            result["artifacts"][0]["expired"] = True
        return result

    monkeypatch.setattr(world, "get", expired)
    fault.update(operation="build-request-2", after=after)
    with pytest.raises(ProcessStopped):
        worker(world, monkeypatch, capsys, locator)
    retained = context().journal.get(locator)
    assert retained.intent is None and "build-validated-1" in retained.evidence
    nonce = retained.evidence.get("build-request-2", {}).get("dispatch_nonce")
    code, event = worker(world, monkeypatch, capsys, locator)
    assert code == 0, event
    if event["step"] == "build-request-2":
        code, event = worker(world, monkeypatch, capsys, locator)
    assert code == 0 and event["step"] == "build-dispatch-2", event
    current = context().journal.get(locator)
    assert (
        nonce is None or current.evidence["build-request-2"]["dispatch_nonce"] == nonce
    )
    assert (
        current.evidence["build-request-2"]["dispatch_nonce"]
        != sealed["dispatch_nonce"]
    )


@pytest.mark.parametrize("after", [False, True])
def test_registration_process_loss_does_not_issue_second_claim(
    lifecycle, monkeypatch, tmp_path, capsys, after
):
    world, locator, context, fault, registration = lifecycle
    assert worker(world, monkeypatch, capsys, locator)[0] == 0
    sealed = context().journal.get(locator).evidence["build-request-1"]
    args = registration(sealed)
    fault.update(operation="build-registration-1", after=after)
    with pytest.raises(ProcessStopped):
        build_worker.main(args)
    retained = context().journal.get(locator)
    assert retained.intent is None and not (tmp_path / "registration-output").exists()
    if not after:
        assert build_worker.main(args) == 0
    else:
        assert retained.evidence["build-registration-1"]["run_id"] == 21
        assert build_worker.main(args) == 2
        capsys.readouterr()
        assert not (tmp_path / "registration-output").exists()
        world.build.update(status="completed", conclusion="failure")
        before = len(context().journal.events())
        with pytest.raises(ControllerError) as caught:
            build_step(context(), context().journal.get(locator))
        assert caught.value.code == "E_BUILD_EVIDENCE"
        assert len(context().journal.events()) == before
        code, event = worker(world, monkeypatch, capsys, locator)
        assert code == 0 and event["step"] == "build-request-2", event
        current = context().journal.get(locator)
        assert (
            current.evidence["build-request-2"]["dispatch_nonce"]
            != sealed["dispatch_nonce"]
        )
        assert (
            current.evidence["build-registration-1"]
            == retained.evidence["build-registration-1"]
        )
