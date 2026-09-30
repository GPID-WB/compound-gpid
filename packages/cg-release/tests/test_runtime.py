"""Enabled start, sealed status, and authority-checked resume stay phase bounded."""

import json
from dataclasses import replace

import pytest
from journal_store import MemoryStore
from test_admission import Inbox
from test_preview import snapshot

from cg_release import cli, runtime
from cg_release.cli import parse_args
from cg_release.events import ControllerError
from cg_release.journal import Journal
from cg_release.models import Policy, load_record
from cg_release.preview import create_proposal


def test_enabled_start_emits_intent_and_verified_receipt(monkeypatch, capsys):
    state = snapshot()
    policy = json.loads(state.policy_raw)
    policy["enabled"] = True
    state = replace(state, policy_raw=json.dumps(policy).encode())
    args = parse_args(["start", "--version", "1.0.0", "--yes", "--json"])
    proposal = create_proposal(state, args)
    request = runtime.request_from_proposal(proposal, nonce="a" * 32)
    inbox = Inbox(request)
    context = runtime.Context(
        None,
        load_record(Policy, state.policy_raw),
        state.policy_sha,
        state.default_branch,
        Journal(MemoryStore()),
    )
    monkeypatch.setattr(cli, "acquire_snapshot", lambda *a, **k: state)
    monkeypatch.setattr(runtime, "context_for", lambda *a, **k: context)
    monkeypatch.setattr(runtime, "request_from_proposal", lambda p: request)
    monkeypatch.setattr(runtime, "check_submission", lambda *a: None)
    monkeypatch.setattr(runtime, "GitHubInbox", lambda api: inbox)
    assert cli.main(vars_to_args(args)) == 0
    events = [json.loads(line) for line in capsys.readouterr().out.splitlines()]
    assert [e["kind"] for e in events] == ["preview", "submission-intent", "receipt"]
    assert inbox.writes == 1


def vars_to_args(args):
    return ["start", "--version", args.version, "--yes", "--json"]


def test_interrupt_after_intent_retains_unknown_outcome(monkeypatch, capsys):
    from test_lifecycle import receipt_fixture

    from cg_release.models import Event

    locator = receipt_fixture().request_id
    monkeypatch.setattr(cli, "acquire_snapshot", lambda *args, **kwargs: snapshot())

    def interrupted(proposal, emit, **kwargs):
        emit(Event(kind="submission-intent", request_id=locator, step="submission"))
        raise KeyboardInterrupt

    monkeypatch.setattr(runtime, "start", interrupted)
    assert cli.main(["start", "--version", "1.0.0", "--yes", "--json"]) == 2
    events = [json.loads(line) for line in capsys.readouterr().out.splitlines()]
    assert events[-1]["request_id"] == locator
    assert events[-1]["code"] == "E_SUBMISSION_UNKNOWN"
    assert "no release was submitted" not in events[-1]["message"]


def test_unresolved_status_and_resume_never_create_an_issue(monkeypatch):
    from test_lifecycle import receipt_fixture

    receipt = receipt_fixture()
    policy = load_record(Policy, snapshot().policy_raw)
    context = runtime.Context(
        None, policy, receipt.request.policy_sha, "main", Journal(MemoryStore())
    )
    monkeypatch.setattr(runtime, "context_for", lambda *a, **k: context)
    monkeypatch.setattr(
        runtime, "GitHubInbox", lambda api: Inbox(receipt.request, accepted=False)
    )
    with pytest.raises(ControllerError) as caught:
        runtime.status(receipt.request_id, deadline=100)
    assert caught.value.code == "E_SUBMISSION_UNKNOWN"


def test_sealed_status_ignores_later_issue_edits(monkeypatch):
    from test_lifecycle import receipt_fixture

    receipt = receipt_fixture()
    journal = Journal(MemoryStore())
    journal.admit(receipt.request)
    context = runtime.Context(
        None,
        load_record(Policy, snapshot().policy_raw),
        receipt.request.policy_sha,
        "main",
        journal,
    )
    monkeypatch.setattr(runtime, "context_for", lambda *a, **k: context)
    monkeypatch.setattr(
        runtime,
        "GitHubInbox",
        lambda api: pytest.fail("Sealed status must not trust current issue body"),
    )
    event = runtime.status(receipt.request_id, deadline=100)
    assert event.observed == "queued" and event.step == "admitted"


@pytest.mark.parametrize("revoked", [False, True])
@pytest.mark.parametrize("reviewed_default_advanced", [False, True])
def test_resume_dispatches_once_only_after_fresh_actor_checks(
    monkeypatch, tmp_path, revoked, reviewed_default_advanced
):
    import subprocess

    from test_authority import Controls

    from cg_release.models import Event

    state = snapshot()
    raw = json.loads(state.policy_raw)
    raw["enabled"] = True
    state = replace(state, policy_raw=json.dumps(raw).encode())
    proposal = create_proposal(
        state, parse_args(["start", "--version", "1.0.0", "--yes"])
    )
    request = runtime.request_from_proposal(proposal)
    api = Controls()
    current_policy_sha = "e" * 40 if reviewed_default_advanced else state.policy_sha
    calls = []
    api.slug = state.slug
    api.branch = lambda name: {
        "name": name,
        "protected": True,
        "commit": {"sha": current_policy_sha},
    }
    api.actor = lambda: {"id": state.actor_id}
    api.cwd, api.read_seconds = tmp_path, 20
    api.remaining = lambda: 20
    api.runner = lambda tool, argv, **kwargs: (
        calls.append((argv, kwargs))
        or subprocess.CompletedProcess(argv, 0, "HTTP/2.0 204 No Content\n\n", "")
    )
    journal = Journal(MemoryStore())
    record = journal.admit(request)
    if reviewed_default_advanced:
        from cg_release.prepare_stage import checkpoint

        record = checkpoint(journal, record, "prepare", {"ok": True}, "awaiting-review")
        record = checkpoint(
            journal,
            record,
            "review-binding",
            {"release_sha": current_policy_sha, "release_tree": "f" * 40},
            "building",
        )
    context = runtime.Context(
        api,
        load_record(Policy, state.policy_raw),
        current_policy_sha,
        state.default_branch,
        journal,
    )
    monkeypatch.setattr(runtime, "context_for", lambda *a, **k: context)
    monkeypatch.setattr(
        runtime,
        "status",
        lambda *a, **k: Event(
            kind="status", version="1.0.0", observed="queued", step="admitted"
        ),
    )

    def role(*args):
        if revoked:
            raise ControllerError("E_AUTHORITY", "Role revoked.")
        return "maintain"

    monkeypatch.setattr("cg_release.authority.actor_role", role)
    if revoked:
        with pytest.raises(ControllerError):
            runtime.resume(record.request_id, deadline=100)
        assert not calls
    else:
        result = runtime.resume(record.request_id, deadline=100)
        assert result.observed == "reconciliation-requested" and len(calls) == 1
        assert json.loads(calls[0][1]["input_text"])["ref"] == state.default_branch
