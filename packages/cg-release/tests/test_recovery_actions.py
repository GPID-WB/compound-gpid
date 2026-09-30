"""Reviewed maintainer recovery restores verified history without a force update."""

import json
import subprocess
from types import SimpleNamespace

import pytest
from test_lifecycle import receipt_fixture
from test_remote_faults import Server

from cg_release.events import ControllerError
from cg_release.github_journal import GitHubJournalStore
from cg_release.journal import Journal, digest
from cg_release.recovery_actions import restore_journal
from cg_release.recovery_models import RecoveryDirective


@pytest.fixture
def restore_case(tmp_path):
    server = Server(tmp_path)
    journal = Journal(
        GitHubJournalStore(server, server.policy, bot_id=77, writable=True)
    )
    journal.admit(receipt_fixture().request)
    mirror = server.current
    spec = RecoveryDirective(
        schema_version=1,
        operation="journal-restore",
        repository_id=123,
        policy_digest=digest(server.policy),
        reason="Restore reviewed mirror",
        mirror_head=mirror,
        expected_head=None,
    )
    branch = server.branch
    server.current = None

    def observed(name):
        if server.current is None:
            raise ControllerError("E_NOT_FOUND", "Missing state branch")
        return branch(name)

    server.branch = observed
    runner = server.runner
    writes = []

    def run(tool, args, **kwargs):
        if "/git/refs" in args[-1]:
            payload = json.loads(kwargs["input_text"])
            writes.append(payload)
            if "PATCH" in args:
                assert server.current is not None and payload["force"] is False
            else:
                assert server.current is None
            server.current = payload["sha"]
            return subprocess.CompletedProcess(
                args, 0, "HTTP/2.0 201 Created\n\n{}", ""
            )
        return runner(tool, args, **kwargs)

    server.runner = run
    server.refs = lambda: []
    server.pages = lambda endpoint: []
    context = SimpleNamespace(
        api=server,
        policy=server.policy,
        journal=journal,
        policy_sha="d" * 40,
        default="main",
    )
    return context, spec, writes


def test_missing_branch_restore_preserves_events_and_records_audit(restore_case):
    context, spec, writes = restore_case
    result = restore_journal(
        context, spec, actor_id=456, run_id=91, directive_digest=digest(spec)
    )
    assert result.kind == "status" and result.observed == "journal-restored"
    assert len(writes) == 1 and writes[0]["sha"] == spec.mirror_head
    assert context.journal.get(receipt_fixture().request_id).state == "queued"
    events = context.journal.events()
    assert events[-1]["record"]["kind"] == "recovery"
    restore_journal(
        context, spec, actor_id=456, run_id=91, directive_digest=digest(spec)
    )
    assert len(writes) == 1 and context.journal.events() == events


def test_corrupt_mirror_or_new_unknown_remote_objects_block_restore(restore_case):
    context, spec, writes = restore_case
    context.api.commits[spec.mirror_head]["commit"]["verification"]["verified"] = False
    with pytest.raises(ControllerError):
        restore_journal(
            context, spec, actor_id=456, run_id=91, directive_digest=digest(spec)
        )
    assert not writes


@pytest.mark.parametrize(
    "conflict",
    ["unknown-tag", "unknown-release", "unreadable-ref", "divergent-history"],
)
def test_restore_never_overwrites_unknown_or_divergent_remote_state(
    restore_case, conflict
):
    context, spec, writes = restore_case
    if conflict == "unknown-tag":
        context.api.refs = lambda: [
            {
                "repository_id": 123,
                "ref": "refs/tags/v9.0.0",
                "object": {"type": "tag", "sha": "9" * 40},
            }
        ]
    if conflict == "unknown-release":
        context.api.pages = lambda endpoint: [{"tag_name": "v9.0.0", "id": 900}]
    if conflict == "unreadable-ref":

        def denied(name):
            raise ControllerError("E_FORBIDDEN", "No ref read authority")

        context.api.branch = denied
    if conflict == "divergent-history":
        context.api.current = context.policy.journal_root
        context.journal.admit(
            receipt_fixture().request.model_copy(
                update={"nonce": "f" * 32, "version": "1.1.0", "tag": "v1.1.0"}
            )
        )
    with pytest.raises(ControllerError):
        restore_journal(
            context, spec, actor_id=456, run_id=91, directive_digest=digest(spec)
        )
    assert not writes


def test_reviewed_root_fast_forward_and_lost_audit_response_are_idempotent(
    restore_case,
):
    context, spec, writes = restore_case
    context.api.current = context.policy.journal_root
    context.api.lost = True
    spec = spec.model_copy(update={"expected_head": context.policy.journal_root})
    restore_journal(
        context, spec, actor_id=456, run_id=91, directive_digest=digest(spec)
    )
    assert writes == [{"sha": spec.mirror_head, "force": False}]
    assert (
        len(
            [
                e
                for e in context.journal.events()
                if e["record"].get("kind") == "recovery"
            ]
        )
        == 1
    )
