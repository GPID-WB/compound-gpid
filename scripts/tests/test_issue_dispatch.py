"""Deterministic tests for the Stage 3 Copilot issue dispatcher.

All tests use inline fixtures, fake read clients, and fake mutation clients.
No test performs any GitHub mutation and no test depends on live GitHub state.
The workflow-level constraints (trigger, concurrency, permissions, trusted
checkout, secret isolation) are checked statically against the YAML source.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from issues.contract import (
    ApiError,
    ConfigError,
    COPILOT_LOGINS,
    EXIT_API,
    EXIT_CONFIG,
    EXIT_NOT_READY,
    EXIT_READY,
)
from issues.client_models import IssueRecord, PRRecord
from issues.dispatch import (
    COPILOT_ASSIGN_LOGIN,
    EXIT_ASSIGN_FAILED,
    EXIT_PROJECT_UPDATE_FAILED,
    EXIT_RECHECK_FAILED,
    IN_PROGRESS_STATUS,
    build_parser,
    main,
    render_json,
    run_dispatch,
)
from issues.dispatch_client import GhDispatchMutator
from issues.dispatch_util import SOURCE_CREDENTIAL_ENVS


REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "copilot-dispatch.yml"
WORKFLOWS_DIR = REPO_ROOT / ".github" / "workflows"


GOOD_BODY = """\
<!-- compound-gpid-tracked: example-dispatch-issue -->

## Roadmap linkage

- **Feature ID:** `example-dispatch-issue`
- **Roadmap milestone:** `workflow-maturity`

## Ready for Copilot

- [x] Human has reviewed and approved this execution contract
- [x] Roadmap feature has been created and linked to this issue
- [x] Exact allowed-path closure has been confirmed
- [x] Project Status has been changed from `Backlog` to `Ready`

## Outcome

The dispatch behavior is implemented and verified.

## Acceptance criteria

- [ ] The dispatcher assigns only copilot-swe-agent[bot]
- [ ] The focused dispatcher tests pass

## Scope

- update the dispatcher script and its tests

## Non-goals

- no scheduling or automatic batching

## Expected allowed paths

- `scripts/issues/dispatch.py`
- `scripts/issues/dispatch_client.py`
- `scripts/tests/test_issue_dispatch.py`

## Prohibited paths

- `.github/workflows/**`
- `roadmap.json`

## Verification commands

```bash
python -m pytest scripts/tests/test_issue_dispatch.py -q
```

## Dependencies / blockers

None currently known.

## Risk class

`low`

## Human review instructions

- Confirm the fixed mutation order and the audit comment trail.

## Blocked-stop conditions

- any assignment or Project Status change before readiness validation
"""


class FakeReadClient:
    """Stateful read-only client that mirrors the readiness client interface."""

    def __init__(
        self,
        *,
        body: str = GOOD_BODY,
        status: str = "Ready",
        prs: list | None = None,
        assignees: list | None = None,
        flip_after: int | None = None,
        flip_status: str = "Backlog",
        raise_error: Exception | None = None,
        raise_after: int | None = None,
    ) -> None:
        self._issue = IssueRecord(
            number=9002,
            title="Example dispatch issue",
            body=body,
            state="OPEN",
            assignees=list(assignees or ["example-maintainer"]),
            labels=["cg:roadmap"],
        )
        self._prs = list(prs or [])
        self._status = status
        self._flip_after = flip_after
        self._flip_status = flip_status
        self._raise_error = raise_error
        self._raise_after = raise_after
        self.status_calls = 0

    def _maybe_raise(self) -> None:
        if self._raise_error is not None and (
            self._raise_after is None or self.status_calls >= self._raise_after
        ):
            raise self._raise_error

    def get_issue(self, issue_number: int) -> IssueRecord:
        self._maybe_raise()
        return self._issue

    def get_open_closing_prs(self, issue_number: int) -> list:
        self._maybe_raise()
        return self._prs

    def get_project_status(self, issue_number: int) -> str | None:
        self.status_calls += 1
        self._maybe_raise()
        if (
            self._flip_after is not None
            and self.status_calls > self._flip_after
        ):
            return self._flip_status
        return self._status


class FakeMutator:
    """Records every mutation call; can be programmed to fail per operation."""

    def __init__(
        self,
        *,
        fail_assign: Exception | None = None,
        fail_project: Exception | None = None,
        fail_comment: Exception | None = None,
    ) -> None:
        self.calls: list = []
        self.fail_assign = fail_assign
        self.fail_project = fail_project
        self.fail_comment = fail_comment

    def assign(self, issue_number: int, login: str) -> None:
        self.calls.append(("assign", issue_number, login))
        if self.fail_assign is not None:
            raise self.fail_assign

    def set_project_status(self, issue_number: int, status: str) -> None:
        self.calls.append(("project", issue_number, status))
        if self.fail_project is not None:
            raise self.fail_project

    def comment(self, issue_number: int, body: str) -> None:
        self.calls.append(("comment", issue_number, body))
        if self.fail_comment is not None:
            raise self.fail_comment


def _ready_client(**kwargs) -> FakeReadClient:
    return FakeReadClient(**kwargs)


# ---------------------------------------------------------------------------
# Dry-run zero mutations
# ---------------------------------------------------------------------------


class TestDryRun:
    def test_dry_run_ready_performs_zero_mutations(self) -> None:
        client = _ready_client()
        mutator = FakeMutator()
        result = run_dispatch(9002, client, mutator, dry_run=True)
        assert result.outcome == "dry-run"
        assert result.exit_code == EXIT_READY
        assert result.mutation_log == []
        assert mutator.calls == []

    def test_dry_run_not_ready_performs_zero_mutations(self) -> None:
        client = _ready_client(status="Backlog")
        mutator = FakeMutator()
        result = run_dispatch(9002, client, mutator, dry_run=True)
        assert result.outcome == "not-ready"
        assert result.exit_code == EXIT_NOT_READY
        assert mutator.calls == []

    def test_dry_run_idempotent_performs_zero_mutations(self) -> None:
        client = _ready_client(assignees=["copilot-swe-agent[bot]"])
        mutator = FakeMutator()
        result = run_dispatch(9002, client, mutator, dry_run=True)
        assert result.outcome == "idempotent-noop"
        assert result.exit_code == EXIT_READY
        assert mutator.calls == []


# ---------------------------------------------------------------------------
# Initial readiness failure
# ---------------------------------------------------------------------------


class TestInitialReadinessFailure:
    def test_non_positive_issue_number_fails_closed(self) -> None:
        client = _ready_client()
        mutator = FakeMutator()
        result = run_dispatch(0, client, mutator, dry_run=False)
        assert result.outcome == "config-error"
        assert result.exit_code == EXIT_CONFIG
        assert mutator.calls == []
        result = run_dispatch(-3, client, mutator, dry_run=False)
        assert result.outcome == "config-error"
        assert result.exit_code == EXIT_CONFIG
        assert mutator.calls == []

    def test_not_ready_state_fails_closed(self) -> None:
        client = _ready_client(status="Backlog")
        mutator = FakeMutator()
        result = run_dispatch(9002, client, mutator, dry_run=False)
        assert result.outcome == "not-ready"
        assert result.exit_code == EXIT_NOT_READY
        assert mutator.calls == []

    def test_config_error_fails_closed_without_mutation(self) -> None:
        client = _ready_client(raise_error=ConfigError("gh missing"))
        mutator = FakeMutator()
        result = run_dispatch(9002, client, mutator, dry_run=False)
        assert result.outcome == "config-error"
        assert result.exit_code == EXIT_CONFIG
        assert mutator.calls == []

    def test_api_error_fails_closed_without_mutation(self) -> None:
        client = _ready_client(raise_error=ApiError("HTTP 500"))
        mutator = FakeMutator()
        result = run_dispatch(9002, client, mutator, dry_run=False)
        assert result.outcome == "api-error"
        assert result.exit_code == EXIT_API
        assert mutator.calls == []


# ---------------------------------------------------------------------------
# Duplicate dispatch / idempotent no-op
# ---------------------------------------------------------------------------


def _closing_pr(issue_number: int = 9002) -> list:
    return [
        PRRecord(
            number=9100,
            title="Implementation",
            body=f"Closes #{issue_number}",
            url="https://github.invalid/pull/9100",
            head_ref="copilot/impl",
            author="copilot-swe-agent[bot]",
        )
    ]


class TestIdempotentNoOp:
    def test_already_assigned_is_idempotent_noop_live(self) -> None:
        client = _ready_client(assignees=["copilot-swe-agent[bot]"])
        mutator = FakeMutator()
        result = run_dispatch(9002, client, mutator, dry_run=False)
        assert result.outcome == "idempotent-noop"
        assert result.exit_code == EXIT_READY
        assert [call[0] for call in mutator.calls] == ["comment"]
        assert all(call[0] != "assign" for call in mutator.calls)
        assert all(call[0] != "project" for call in mutator.calls)

    def test_existing_open_pr_is_idempotent_noop_live(self) -> None:
        client = _ready_client(prs=_closing_pr())
        mutator = FakeMutator()
        result = run_dispatch(9002, client, mutator, dry_run=False)
        assert result.outcome == "idempotent-noop"
        assert result.exit_code == EXIT_READY
        assert [call[0] for call in mutator.calls] == ["comment"]

    def test_idempotent_noop_explains_reason(self) -> None:
        client = _ready_client(assignees=["copilot-swe-agent[bot]"])
        mutator = FakeMutator()
        result = run_dispatch(9002, client, mutator, dry_run=False)
        assert "no-op" in result.messages[0].lower()
        comment_body = mutator.calls[0][2]
        assert "already assigned" in comment_body.lower()


# ---------------------------------------------------------------------------
# Readiness changes before the second validation
# ---------------------------------------------------------------------------


class TestRevalidation:
    def test_state_change_between_validations_fails_closed(self) -> None:
        client = _ready_client(flip_after=1, flip_status="Backlog")
        mutator = FakeMutator()
        result = run_dispatch(9002, client, mutator, dry_run=False)
        assert result.outcome == "state-changed"
        assert result.exit_code == EXIT_RECHECK_FAILED
        assert mutator.calls == []

    def test_second_validation_runs_before_any_mutation(self) -> None:
        client = _ready_client(flip_after=1, flip_status="In progress")
        mutator = FakeMutator()
        result = run_dispatch(9002, client, mutator, dry_run=False)
        assert result.outcome == "state-changed"
        assert mutator.calls == []

    def test_second_validation_config_error_fails_closed(self) -> None:
        client = _ready_client(raise_error=ConfigError("gh missing"), raise_after=2)
        mutator = FakeMutator()
        result = run_dispatch(9002, client, mutator, dry_run=False)
        assert result.outcome == "config-error"
        assert result.exit_code == EXIT_CONFIG
        assert mutator.calls == []

    def test_second_validation_api_error_fails_closed(self) -> None:
        client = _ready_client(raise_error=ApiError("HTTP 500"), raise_after=2)
        mutator = FakeMutator()
        result = run_dispatch(9002, client, mutator, dry_run=False)
        assert result.outcome == "api-error"
        assert result.exit_code == EXIT_API
        assert mutator.calls == []


# ---------------------------------------------------------------------------
# Assignment failure
# ---------------------------------------------------------------------------


class TestAssignmentFailure:
    def test_assign_failure_leaves_status_untouched(self) -> None:
        client = _ready_client()
        mutator = FakeMutator(fail_assign=ApiError("assign 403"))
        result = run_dispatch(9002, client, mutator, dry_run=False)
        assert result.outcome == "assign-failed"
        assert result.exit_code == EXIT_ASSIGN_FAILED
        assert [call[0] for call in mutator.calls] == ["assign", "comment"]
        assert all(call[0] != "project" for call in mutator.calls)

    def test_assign_failure_comments_error(self) -> None:
        client = _ready_client()
        mutator = FakeMutator(fail_assign=ApiError("HTTP 403"))
        result = run_dispatch(9002, client, mutator, dry_run=False)
        assert result.exit_code == EXIT_ASSIGN_FAILED
        comment_body = mutator.calls[1][2]
        assert "failed" in comment_body.lower()
        assert "no Project Status change" in comment_body


# ---------------------------------------------------------------------------
# Assignment succeeds but Project update fails
# ---------------------------------------------------------------------------


class TestProjectUpdateFailure:
    def test_project_failure_keeps_assignee_and_exits_nonzero(self) -> None:
        client = _ready_client()
        mutator = FakeMutator(fail_project=ApiError("graphql 400"))
        result = run_dispatch(9002, client, mutator, dry_run=False)
        assert result.outcome == "project-update-failed"
        assert result.exit_code == EXIT_PROJECT_UPDATE_FAILED
        assert [call[0] for call in mutator.calls] == ["assign", "project", "comment"]

    def test_project_failure_documents_manual_recovery(self) -> None:
        client = _ready_client()
        mutator = FakeMutator(fail_project=ConfigError("missing PROJECT_SYNC_TOKEN"))
        result = run_dispatch(9002, client, mutator, dry_run=False)
        assert result.exit_code == EXIT_PROJECT_UPDATE_FAILED
        comment_body = mutator.calls[2][2]
        assert "Manual recovery" in comment_body
        assert "remains assigned" in comment_body
        assert "do not unassign" in comment_body.lower()

    def test_no_unassign_method_exists(self) -> None:
        assert not hasattr(GhDispatchMutator, "unassign")
        assert not hasattr(FakeMutator, "unassign")


# ---------------------------------------------------------------------------
# Audit-comment write failure on every branch
# ---------------------------------------------------------------------------


class TestCommentFailure:
    def test_comment_failure_still_marks_dispatched(self) -> None:
        client = _ready_client()
        mutator = FakeMutator(fail_comment=ApiError("comment 403"))
        result = run_dispatch(9002, client, mutator, dry_run=False)
        assert result.outcome == "dispatched"
        assert result.exit_code == EXIT_READY
        assert result.mutation_log[-1] == "comment:failed"
        assert [call[0] for call in mutator.calls] == ["assign", "project", "comment"]

    def test_comment_failure_on_assignment_failure_branch(self) -> None:
        client = _ready_client()
        mutator = FakeMutator(
            fail_assign=ApiError("assign 403"), fail_comment=ApiError("comment 403")
        )
        result = run_dispatch(9002, client, mutator, dry_run=False)
        assert result.outcome == "assign-failed"
        assert result.exit_code == EXIT_ASSIGN_FAILED
        assert result.mutation_log == ["assign:failed", "comment:failed"]

    def test_comment_failure_on_project_failure_branch(self) -> None:
        client = _ready_client()
        mutator = FakeMutator(
            fail_project=ApiError("graphql 400"), fail_comment=ApiError("comment 403")
        )
        result = run_dispatch(9002, client, mutator, dry_run=False)
        assert result.outcome == "project-update-failed"
        assert result.exit_code == EXIT_PROJECT_UPDATE_FAILED
        assert "comment:failed" in result.mutation_log
        assert [call[0] for call in mutator.calls] == ["assign", "project", "comment"]

    def test_comment_failure_on_idempotent_noop_branch(self) -> None:
        client = _ready_client(assignees=["copilot-swe-agent[bot]"])
        mutator = FakeMutator(fail_comment=ApiError("comment 403"))
        result = run_dispatch(9002, client, mutator, dry_run=False)
        assert result.outcome == "idempotent-noop"
        assert result.exit_code == EXIT_READY
        assert result.mutation_log == ["comment:failed"]


# ---------------------------------------------------------------------------
# Mutation ordering and audit-comment trail
# ---------------------------------------------------------------------------


class TestMutationOrdering:
    def test_success_order_is_assign_then_project_then_comment(self) -> None:
        client = _ready_client()
        mutator = FakeMutator()
        result = run_dispatch(9002, client, mutator, dry_run=False)
        assert result.outcome == "dispatched"
        assert result.exit_code == EXIT_READY
        assert [call[0] for call in mutator.calls] == ["assign", "project", "comment"]
        assert result.mutation_log == [
            f"assign:{COPILOT_ASSIGN_LOGIN}",
            f"project:{IN_PROGRESS_STATUS}",
            "comment:dispatched",
        ]

    def test_project_update_never_before_assignment(self) -> None:
        client = _ready_client()
        mutator = FakeMutator(fail_assign=ApiError("HTTP 403"))
        run_dispatch(9002, client, mutator, dry_run=False)
        project_indexes = [
            index for index, call in enumerate(mutator.calls) if call[0] == "project"
        ]
        assign_indexes = [
            index for index, call in enumerate(mutator.calls) if call[0] == "assign"
        ]
        for project_index in project_indexes:
            for assign_index in assign_indexes:
                assert project_index > assign_index

    def test_success_audit_comment_describes_result(self) -> None:
        client = _ready_client()
        mutator = FakeMutator()
        run_dispatch(9002, client, mutator, dry_run=False)
        comment_body = mutator.calls[2][2]
        assert COPILOT_ASSIGN_LOGIN in comment_body
        assert IN_PROGRESS_STATUS in comment_body


# ---------------------------------------------------------------------------
# Exact Copilot bot identity
# ---------------------------------------------------------------------------


class TestBotIdentity:
    def test_login_is_exact_canonical_bot(self) -> None:
        assert COPILOT_ASSIGN_LOGIN == "copilot-swe-agent[bot]"
        assert COPILOT_ASSIGN_LOGIN in COPILOT_LOGINS

    def test_assign_called_with_exact_login(self) -> None:
        client = _ready_client()
        mutator = FakeMutator()
        run_dispatch(9002, client, mutator, dry_run=False)
        assert mutator.calls[0][0] == "assign"
        assert mutator.calls[0][2] == COPILOT_ASSIGN_LOGIN


# ---------------------------------------------------------------------------
# CLI wiring
# ---------------------------------------------------------------------------


class TestCli:
    def test_dry_run_flag_defaults_to_true(self) -> None:
        args = build_parser().parse_args(["--issue", "9002"])
        assert args.dry_run is True

    def test_no_dry_run_flag_flips_mode(self) -> None:
        args = build_parser().parse_args(["--issue", "9002", "--no-dry-run"])
        assert args.dry_run is False

    def test_issue_argument_required(self) -> None:
        with pytest.raises(SystemExit) as excinfo:
            build_parser().parse_args([])
        assert excinfo.value.code == EXIT_CONFIG

    def test_non_integer_issue_uses_config_exit(self) -> None:
        with pytest.raises(SystemExit) as excinfo:
            build_parser().parse_args(["--issue", "abc"])
        assert excinfo.value.code == EXIT_CONFIG

    def test_main_returns_dispatch_result_exit(self) -> None:
        client = _ready_client()
        mutator = FakeMutator()
        code = main(
            ["--issue", "9002"],
            read_client=client,
            mutator=mutator,
            dispatch_fn=run_dispatch,
        )
        assert code == EXIT_READY
        assert mutator.calls == []

    def test_main_no_dry_run_exercises_live_sequence(self) -> None:
        client = _ready_client()
        mutator = FakeMutator()
        code = main(
            ["--issue", "9002", "--no-dry-run"],
            read_client=client,
            mutator=mutator,
            dispatch_fn=run_dispatch,
        )
        assert code == EXIT_READY
        assert [call[0] for call in mutator.calls] == ["assign", "project", "comment"]

    def test_json_output_has_schema_fields(self) -> None:
        result = run_dispatch(9002, _ready_client(), FakeMutator(), dry_run=True)
        payload = json.loads(render_json(result))
        for field in (
            "issue", "outcome", "dryRun", "exitCode", "exitReason",
            "mutations", "messages",
        ):
            assert field in payload
        assert payload["outcome"] == "dry-run"

    def test_exit_code_literals_are_distinct(self) -> None:
        assert EXIT_ASSIGN_FAILED == 5
        assert EXIT_PROJECT_UPDATE_FAILED == 6
        assert EXIT_RECHECK_FAILED == 7


# ---------------------------------------------------------------------------
# Mutation client units (no live GitHub)
# ---------------------------------------------------------------------------


class _StubRunner:
    """Runner that returns queued stdout responses, recording each call."""

    def __init__(self, responses: list[str] | None = None) -> None:
        self.calls: list = []
        self._responses = list(responses or ["{}"])
        self._index = 0

    def __call__(self, args: list, token: str) -> object:
        self.calls.append({"args": list(args), "token": token})
        stdout = self._responses[min(self._index, len(self._responses) - 1)]
        self._index += 1
        return _StubResult(stdout)


class _StubResult:
    def __init__(self, stdout: str) -> None:
        self.stdout = stdout
        self.returncode = 0
        self.stderr = ""


def _assign_response(login: str = "copilot-swe-agent[bot]") -> str:
    return json.dumps({"number": 9002, "assignees": [{"login": login}]})


def _project_item_response(number: int = 9002) -> str:
    return json.dumps({
        "data": {
            "node": {
                "items": {
                    "nodes": [
                        {"id": "item-1", "content": {"number": number}},
                    ],
                    "pageInfo": {"hasNextPage": False},
                },
            },
        },
    })


def _mutation_success_response() -> str:
    return json.dumps({
        "data": {
            "updateProjectV2ItemFieldValue": {
                "projectV2Item": {"id": "item-1"},
            },
        },
    })


class TestGhDispatchMutator:
    def test_assign_and_comment_use_assign_token(self, monkeypatch) -> None:
        runner = _StubRunner([
            json.dumps({"defaultBranchRef": {"name": "main"}}),
            _assign_response(), "{}",
        ])
        monkeypatch.setenv("COPILOT_ASSIGN_TOKEN", "assign-token")
        monkeypatch.setenv("PROJECT_SYNC_TOKEN", "project-token")
        mutator = GhDispatchMutator(runner=runner, owner="OWNER", name="REPO")
        mutator.assign(9002, "copilot-swe-agent[bot]")
        mutator.comment(9002, "audit body")
        assert len(runner.calls) == 3
        assert "--repo" in runner.calls[0]["args"]
        repo_idx = runner.calls[0]["args"].index("--repo")
        assert runner.calls[0]["args"][repo_idx + 1] == "OWNER/REPO"
        for call in runner.calls[1:]:
            assert call["token"] == "assign-token"

    def test_project_update_uses_project_token(self, monkeypatch) -> None:
        runner = _StubRunner([
            _project_item_response(), _mutation_success_response(),
        ])
        monkeypatch.setenv("COPILOT_ASSIGN_TOKEN", "assign-token")
        monkeypatch.setenv("PROJECT_SYNC_TOKEN", "project-token")
        mutator = GhDispatchMutator(runner=runner, owner="OWNER", name="REPO")
        mutator.set_project_status(9002, "In progress")
        assert len(runner.calls) == 2
        assert runner.calls[0]["token"] == "project-token"
        assert runner.calls[1]["token"] == "project-token"

    def test_missing_token_fails_closed(self, monkeypatch) -> None:
        runner = _StubRunner()
        monkeypatch.delenv("COPILOT_ASSIGN_TOKEN", raising=False)
        mutator = GhDispatchMutator(runner=runner, owner="OWNER", name="REPO")
        with pytest.raises(ConfigError):
            mutator.assign(9002, "copilot-swe-agent[bot]")
        assert runner.calls == []

    def test_unsupported_status_fails_closed(self, monkeypatch) -> None:
        runner = _StubRunner()
        monkeypatch.setenv("COPILOT_ASSIGN_TOKEN", "assign-token")
        monkeypatch.setenv("PROJECT_SYNC_TOKEN", "project-token")
        mutator = GhDispatchMutator(runner=runner, owner="OWNER", name="REPO")
        with pytest.raises(ConfigError):
            mutator.set_project_status(9002, "Done")
        assert runner.calls == []

    def test_issue_not_on_project_fails_closed(self, monkeypatch) -> None:
        runner = _StubRunner([
            json.dumps({"data": {"node": {"items": {
                "nodes": [{"id": "other-item", "content": {"number": 9999}}],
                "pageInfo": {"hasNextPage": False},
            }}}}),
        ])
        monkeypatch.setenv("COPILOT_ASSIGN_TOKEN", "assign-token")
        monkeypatch.setenv("PROJECT_SYNC_TOKEN", "project-token")
        mutator = GhDispatchMutator(runner=runner, owner="OWNER", name="REPO")
        with pytest.raises(ConfigError):
            mutator.set_project_status(9002, "In progress")

    def test_assign_noop_response_fails_closed(self, monkeypatch) -> None:
        runner = _StubRunner([
            json.dumps({"defaultBranchRef": {"name": "main"}}),
            "{}",
        ])
        monkeypatch.setenv("COPILOT_ASSIGN_TOKEN", "assign-token")
        monkeypatch.setenv("PROJECT_SYNC_TOKEN", "project-token")
        mutator = GhDispatchMutator(runner=runner, owner="OWNER", name="REPO")
        with pytest.raises(ApiError):
            mutator.assign(9002, "copilot-swe-agent[bot]")
        assert len(runner.calls) == 2

    def test_assign_rejects_non_copilot_login(self, monkeypatch) -> None:
        runner = _StubRunner()
        monkeypatch.setenv("COPILOT_ASSIGN_TOKEN", "assign-token")
        monkeypatch.setenv("PROJECT_SYNC_TOKEN", "project-token")
        mutator = GhDispatchMutator(runner=runner, owner="OWNER", name="REPO")
        with pytest.raises(ConfigError):
            mutator.assign(9002, "someone-else[bot]")
        assert runner.calls == []

    def test_mutation_noop_response_fails_closed(self, monkeypatch) -> None:
        runner = _StubRunner([
            json.dumps({"defaultBranchRef": {"name": "main"}}),
            _project_item_response(),
            json.dumps({"data": {"updateProjectV2ItemFieldValue": None}}),
        ])
        monkeypatch.setenv("COPILOT_ASSIGN_TOKEN", "assign-token")
        monkeypatch.setenv("PROJECT_SYNC_TOKEN", "project-token")
        mutator = GhDispatchMutator(runner=runner, owner="OWNER", name="REPO")
        with pytest.raises(ApiError):
            mutator.set_project_status(9002, "In progress")

    def test_project_scan_truncated_fails_closed(self, monkeypatch) -> None:
        runner = _StubRunner([
            json.dumps({"data": {"node": {"items": {
                "nodes": [{"id": "other-item", "content": {"number": 9999}}],
                "pageInfo": {"hasNextPage": True, "endCursor": "cursor-1"},
            }}}}),
            json.dumps({"data": {"node": {"items": {
                "nodes": [{"id": "other-item", "content": {"number": 9999}}],
                "pageInfo": {"hasNextPage": True, "endCursor": "cursor-2"},
            }}}}),
        ])
        monkeypatch.setenv("COPILOT_ASSIGN_TOKEN", "assign-token")
        monkeypatch.setenv("PROJECT_SYNC_TOKEN", "project-token")
        mutator = GhDispatchMutator(runner=runner, owner="OWNER", name="REPO")
        with pytest.raises(ApiError):
            mutator.set_project_status(9002, "In progress")

    def test_pagination_finds_issue_on_first_page(self, monkeypatch) -> None:
        runner = _StubRunner([
            _project_item_response(9002),
            _mutation_success_response(),
        ])
        monkeypatch.setenv("COPILOT_ASSIGN_TOKEN", "assign-token")
        monkeypatch.setenv("PROJECT_SYNC_TOKEN", "project-token")
        mutator = GhDispatchMutator(runner=runner, owner="OWNER", name="REPO")
        mutator.set_project_status(9002, "In progress")
        assert len(runner.calls) == 2

    def test_pagination_finds_issue_on_later_page(self, monkeypatch) -> None:
        page1 = json.dumps({"data": {"node": {"items": {
            "nodes": [{"id": "item-1", "content": {"number": 8001}}],
            "pageInfo": {"hasNextPage": True, "endCursor": "cursor-1"},
        }}}})
        page2 = json.dumps({"data": {"node": {"items": {
            "nodes": [{"id": "item-2", "content": {"number": 9002}}],
            "pageInfo": {"hasNextPage": False},
        }}}})
        runner = _StubRunner([page1, page2, _mutation_success_response()])
        monkeypatch.setenv("COPILOT_ASSIGN_TOKEN", "assign-token")
        monkeypatch.setenv("PROJECT_SYNC_TOKEN", "project-token")
        mutator = GhDispatchMutator(runner=runner, owner="OWNER", name="REPO")
        mutator.set_project_status(9002, "In progress")
        assert len(runner.calls) == 3
        assert "after=cursor-1" in runner.calls[1]["args"]

    def test_pagination_exhaustion_without_match_fails_closed(
        self, monkeypatch
    ) -> None:
        page1 = json.dumps({"data": {"node": {"items": {
            "nodes": [{"id": "item-1", "content": {"number": 8001}}],
            "pageInfo": {"hasNextPage": True, "endCursor": "cursor-1"},
        }}}})
        page2 = json.dumps({"data": {"node": {"items": {
            "nodes": [{"id": "item-2", "content": {"number": 8002}}],
            "pageInfo": {"hasNextPage": False},
        }}}})
        runner = _StubRunner([page1, page2])
        monkeypatch.setenv("COPILOT_ASSIGN_TOKEN", "assign-token")
        monkeypatch.setenv("PROJECT_SYNC_TOKEN", "project-token")
        mutator = GhDispatchMutator(runner=runner, owner="OWNER", name="REPO")
        with pytest.raises(ConfigError):
            mutator.set_project_status(9002, "In progress")

    def test_pagination_malformed_page_info_fails_closed(
        self, monkeypatch
    ) -> None:
        runner = _StubRunner([
            json.dumps({"data": {"node": {"items": {
                "nodes": [{"id": "item-1", "content": {"number": 8001}}],
                "pageInfo": {"hasNextPage": True, "endCursor": 12345},
            }}}}),
        ])
        monkeypatch.setenv("COPILOT_ASSIGN_TOKEN", "assign-token")
        monkeypatch.setenv("PROJECT_SYNC_TOKEN", "project-token")
        mutator = GhDispatchMutator(runner=runner, owner="OWNER", name="REPO")
        with pytest.raises(ApiError):
            mutator.set_project_status(9002, "In progress")

    def test_pagination_repeated_cursor_fails_closed(self, monkeypatch) -> None:
        page = json.dumps({"data": {"node": {"items": {
            "nodes": [{"id": "item-1", "content": {"number": 8001}}],
            "pageInfo": {"hasNextPage": True, "endCursor": "cursor-1"},
        }}}})
        runner = _StubRunner([page, page])
        monkeypatch.setenv("COPILOT_ASSIGN_TOKEN", "assign-token")
        monkeypatch.setenv("PROJECT_SYNC_TOKEN", "project-token")
        mutator = GhDispatchMutator(runner=runner, owner="OWNER", name="REPO")
        with pytest.raises(ApiError, match="did not advance"):
            mutator.set_project_status(9002, "In progress")

    def test_pagination_page_limit_exceeded_fails_closed(
        self, monkeypatch
    ) -> None:
        import issues.dispatch_client as dc

        monkeypatch.setattr(dc, "_MAX_PROJECT_PAGES", 2)

        def _page(cursor):
            return json.dumps({"data": {"node": {"items": {
                "nodes": [{"id": "x", "content": {"number": 8001}}],
                "pageInfo": {"hasNextPage": True, "endCursor": cursor},
            }}}})

        runner = _StubRunner([_page("a"), _page("b"), _page("c")])
        monkeypatch.setenv("COPILOT_ASSIGN_TOKEN", "assign-token")
        monkeypatch.setenv("PROJECT_SYNC_TOKEN", "project-token")
        mutator = GhDispatchMutator(runner=runner, owner="OWNER", name="REPO")
        with pytest.raises(ApiError, match="exceeded"):
            mutator.set_project_status(9002, "In progress")

    def test_pagination_graphql_errors_fails_closed(self, monkeypatch) -> None:
        runner = _StubRunner([
            json.dumps({"data": None, "errors": [{"message": "not authorized"}]}),
        ])
        monkeypatch.setenv("COPILOT_ASSIGN_TOKEN", "assign-token")
        monkeypatch.setenv("PROJECT_SYNC_TOKEN", "project-token")
        mutator = GhDispatchMutator(runner=runner, owner="OWNER", name="REPO")
        with pytest.raises(ConfigError):
            mutator.set_project_status(9002, "In progress")

    def test_repo_resolution_sets_base_branch_from_default(self, monkeypatch) -> None:
        captured_bodies: list = []

        class RecordingRunner(_StubRunner):
            def __call__(self, args, token):
                result = super().__call__(args, token)
                for argument in args:
                    path = Path(argument)
                    if path.exists() and path.suffix == ".json":
                        captured_bodies.append(
                            json.loads(path.read_text(encoding="utf-8"))
                        )
                return result

        runner = RecordingRunner([
            json.dumps({
                "nameWithOwner": "OWNER/REPO",
                "defaultBranchRef": {"name": "dev"},
            }),
            _assign_response(),
        ])
        monkeypatch.setenv("COPILOT_ASSIGN_TOKEN", "assign-token")
        monkeypatch.setenv("PROJECT_SYNC_TOKEN", "project-token")
        mutator = GhDispatchMutator(runner=runner)
        mutator.assign(9002, "copilot-swe-agent[bot]")
        assert runner.calls[0]["args"][:3] == ["repo", "view", "--json"]
        assert "repos/OWNER/REPO/issues/9002/assignees" in runner.calls[1]["args"]
        assert len(captured_bodies) == 1
        assert captured_bodies[0]["agent_assignment"]["base_branch"] == "dev"
        assert captured_bodies[0]["assignees"] == ["copilot-swe-agent[bot]"]

    def test_repo_resolution_missing_slash_is_config_error(self, monkeypatch) -> None:
        runner = _StubRunner([json.dumps({"nameWithOwner": "NO-SLASH"})])
        monkeypatch.setenv("COPILOT_ASSIGN_TOKEN", "assign-token")
        monkeypatch.setenv("PROJECT_SYNC_TOKEN", "project-token")
        mutator = GhDispatchMutator(runner=runner)
        with pytest.raises(ConfigError):
            mutator.assign(9002, "copilot-swe-agent[bot]")

    def test_repo_resolution_wrong_shape_is_api_error(self, monkeypatch) -> None:
        runner = _StubRunner(["[1, 2]"])
        monkeypatch.setenv("COPILOT_ASSIGN_TOKEN", "assign-token")
        monkeypatch.setenv("PROJECT_SYNC_TOKEN", "project-token")
        mutator = GhDispatchMutator(runner=runner)
        with pytest.raises(ApiError):
            mutator.assign(9002, "copilot-swe-agent[bot]")

    def test_repo_resolution_resolves_default_branch_with_overrides(
        self, monkeypatch
    ) -> None:
        runner = _StubRunner([
            json.dumps({"defaultBranchRef": {"name": "develop"}}),
            _assign_response(),
        ])
        monkeypatch.setenv("COPILOT_ASSIGN_TOKEN", "assign-token")
        monkeypatch.setenv("PROJECT_SYNC_TOKEN", "project-token")
        mutator = GhDispatchMutator(runner=runner, owner="O", name="R")
        mutator.assign(9002, "copilot-swe-agent[bot]")
        assert "repo" in runner.calls[0]["args"]
        assert "view" in runner.calls[0]["args"]
        assert "--repo" in runner.calls[0]["args"]
        repo_idx = runner.calls[0]["args"].index("--repo")
        assert runner.calls[0]["args"][repo_idx + 1] == "O/R"
        assert mutator._base_branch == "develop"

    def test_override_missing_default_branch_is_config_error(
        self, monkeypatch
    ) -> None:
        runner = _StubRunner([
            json.dumps({"defaultBranchRef": None}),
        ])
        monkeypatch.setenv("COPILOT_ASSIGN_TOKEN", "assign-token")
        monkeypatch.setenv("PROJECT_SYNC_TOKEN", "project-token")
        mutator = GhDispatchMutator(runner=runner, owner="O", name="R")
        with pytest.raises(ConfigError, match="defaultBranchRef"):
            mutator.assign(9002, "copilot-swe-agent[bot]")

    def test_override_empty_default_branch_name_is_config_error(
        self, monkeypatch
    ) -> None:
        runner = _StubRunner([
            json.dumps({"defaultBranchRef": {"name": ""}}),
        ])
        monkeypatch.setenv("COPILOT_ASSIGN_TOKEN", "assign-token")
        monkeypatch.setenv("PROJECT_SYNC_TOKEN", "project-token")
        mutator = GhDispatchMutator(runner=runner, owner="O", name="R")
        with pytest.raises(ConfigError, match="defaultBranchRef"):
            mutator.assign(9002, "copilot-swe-agent[bot]")

    def test_auto_resolve_missing_default_branch_is_config_error(
        self, monkeypatch
    ) -> None:
        runner = _StubRunner([
            json.dumps({"nameWithOwner": "OWNER/REPO", "defaultBranchRef": None}),
        ])
        monkeypatch.setenv("COPILOT_ASSIGN_TOKEN", "assign-token")
        monkeypatch.setenv("PROJECT_SYNC_TOKEN", "project-token")
        mutator = GhDispatchMutator(runner=runner)
        with pytest.raises(ConfigError, match="defaultBranchRef"):
            mutator.assign(9002, "copilot-swe-agent[bot]")

    def test_assignment_and_comment_target_same_repository(
        self, monkeypatch
    ) -> None:
        runner = _StubRunner([
            json.dumps({
                "nameWithOwner": "OWNER/REPO",
                "defaultBranchRef": {"name": "main"},
            }),
            _assign_response(),
            "{}",
        ])
        monkeypatch.setenv("COPILOT_ASSIGN_TOKEN", "assign-token")
        monkeypatch.setenv("PROJECT_SYNC_TOKEN", "project-token")
        mutator = GhDispatchMutator(runner=runner)
        mutator.assign(9002, "copilot-swe-agent[bot]")
        mutator.comment(9002, "audit body")
        assert "repos/OWNER/REPO/issues/9002/assignees" in runner.calls[1]["args"]
        assert "--repo" in runner.calls[2]["args"]
        repo_idx = runner.calls[2]["args"].index("--repo")
        assert runner.calls[2]["args"][repo_idx + 1] == "OWNER/REPO"

    def test_strict_node_non_mapping_raises_api_error(self, monkeypatch) -> None:
        runner = _StubRunner([
            json.dumps({"defaultBranchRef": {"name": "main"}}),
            json.dumps({"data": {"node": {"items": {
                "nodes": ["not-a-mapping"],
                "pageInfo": {"hasNextPage": False},
            }}}}),
        ])
        monkeypatch.setenv("COPILOT_ASSIGN_TOKEN", "assign-token")
        monkeypatch.setenv("PROJECT_SYNC_TOKEN", "project-token")
        mutator = GhDispatchMutator(runner=runner, owner="OWNER", name="REPO")
        with pytest.raises(ApiError):
            mutator.set_project_status(9002, "In progress")

    def test_strict_content_wrong_shape_raises_api_error(self, monkeypatch) -> None:
        runner = _StubRunner([
            json.dumps({"defaultBranchRef": {"name": "main"}}),
            json.dumps({"data": {"node": {"items": {
                "nodes": [{"id": "item-1", "content": "oops"}],
                "pageInfo": {"hasNextPage": False},
            }}}}),
        ])
        monkeypatch.setenv("COPILOT_ASSIGN_TOKEN", "assign-token")
        monkeypatch.setenv("PROJECT_SYNC_TOKEN", "project-token")
        mutator = GhDispatchMutator(runner=runner, owner="OWNER", name="REPO")
        with pytest.raises(ApiError):
            mutator.set_project_status(9002, "In progress")

    def test_unwritable_temp_file_fails_closed(self, monkeypatch) -> None:
        import issues.dispatch_util as dispatch_util

        def _explode(*args, **kwargs):
            raise OSError(28, "No space left on device")

        monkeypatch.setattr(dispatch_util.tempfile, "NamedTemporaryFile", _explode)
        monkeypatch.setenv("COPILOT_ASSIGN_TOKEN", "assign-token")
        monkeypatch.setenv("PROJECT_SYNC_TOKEN", "project-token")
        runner = _StubRunner([
            json.dumps({"defaultBranchRef": {"name": "main"}}),
        ])
        mutator = GhDispatchMutator(runner=runner, owner="OWNER", name="REPO")
        with pytest.raises(ApiError):
            mutator.assign(9002, "copilot-swe-agent[bot]")


# ---------------------------------------------------------------------------
# Per-subprocess credential isolation
# ---------------------------------------------------------------------------


class TestCredentialIsolation:
    def test_source_credential_env_names_defined(self) -> None:
        assert "COPILOT_ASSIGN_TOKEN" in SOURCE_CREDENTIAL_ENVS
        assert "PROJECT_SYNC_TOKEN" in SOURCE_CREDENTIAL_ENVS

    def test_default_mutation_runner_removes_source_credentials(
        self, monkeypatch
    ) -> None:
        import issues.dispatch_util as dispatch_util

        captured_env: dict = {}

        def _capture_run_gh(args, env=None):
            if env is not None:
                captured_env.update(env)
            return _StubResult("{}")

        monkeypatch.setattr(dispatch_util, "_default_run_gh", _capture_run_gh)
        monkeypatch.setenv("COPILOT_ASSIGN_TOKEN", "assign-secret")
        monkeypatch.setenv("PROJECT_SYNC_TOKEN", "project-secret")
        monkeypatch.setenv("GH_TOKEN", "existing-token")
        dispatch_util._default_mutation_runner(["api", "graphql"], "target-token")
        assert captured_env.get("GH_TOKEN") == "target-token"
        assert "COPILOT_ASSIGN_TOKEN" not in captured_env
        assert "PROJECT_SYNC_TOKEN" not in captured_env

    def test_assignment_subprocess_has_no_source_credentials(
        self, monkeypatch
    ) -> None:
        import issues.dispatch_util as dispatch_util

        captured_envs: list = []

        def _capture_run_gh(args, env=None):
            if env is not None:
                captured_envs.append(dict(env))
            text = "{}"
            if "repo" in args and "view" in args:
                text = json.dumps({
                    "nameWithOwner": "OWNER/REPO",
                    "defaultBranchRef": {"name": "main"},
                })
            elif "assignees" in str(args):
                text = _assign_response()
            return _StubResult(text)

        monkeypatch.setattr(dispatch_util, "_default_run_gh", _capture_run_gh)
        monkeypatch.setenv("COPILOT_ASSIGN_TOKEN", "assign-secret")
        monkeypatch.setenv("PROJECT_SYNC_TOKEN", "project-secret")
        mutator = GhDispatchMutator(owner="OWNER", name="REPO")
        mutator.assign(9002, "copilot-swe-agent[bot]")
        mutator.comment(9002, "audit body")
        assert len(captured_envs) >= 2, (
            f"expected at least 2 subprocess calls, got {len(captured_envs)}"
        )
        for env in captured_envs:
            assert "COPILOT_ASSIGN_TOKEN" not in env, (
                "assignment subprocess must not receive COPILOT_ASSIGN_TOKEN"
            )
            assert "PROJECT_SYNC_TOKEN" not in env, (
                "assignment subprocess must not receive PROJECT_SYNC_TOKEN"
            )

    def test_project_subprocess_has_no_source_credentials(
        self, monkeypatch
    ) -> None:
        import issues.dispatch_util as dispatch_util

        captured_envs: list = []

        def _capture_run_gh(args, env=None):
            if env is not None:
                captured_envs.append(dict(env))
            text = "{}"
            if "graphql" in args:
                query_text = str(args)
                if "SetProjectStatus" in query_text:
                    text = _mutation_success_response()
                else:
                    text = _project_item_response()
            return _StubResult(text)

        monkeypatch.setattr(dispatch_util, "_default_run_gh", _capture_run_gh)
        monkeypatch.setenv("COPILOT_ASSIGN_TOKEN", "assign-secret")
        monkeypatch.setenv("PROJECT_SYNC_TOKEN", "project-secret")
        mutator = GhDispatchMutator(owner="OWNER", name="REPO")
        mutator.set_project_status(9002, "In progress")
        assert len(captured_envs) >= 2, (
            f"expected at least 2 subprocess calls, got {len(captured_envs)}"
        )
        for env in captured_envs:
            assert "COPILOT_ASSIGN_TOKEN" not in env, (
                "project subprocess must not receive COPILOT_ASSIGN_TOKEN"
            )
            assert "PROJECT_SYNC_TOKEN" not in env, (
                "project subprocess must not receive PROJECT_SYNC_TOKEN"
            )


# ---------------------------------------------------------------------------
# Workflow static constraints
# ---------------------------------------------------------------------------


class WorkflowTextMixin:
    @pytest.fixture()
    def workflow_text(self) -> str:
        return WORKFLOW.read_text(encoding="utf-8")


class TestWorkflowConstraints(WorkflowTextMixin):
    def test_trigger_is_workflow_dispatch_only(self, workflow_text) -> None:
        assert "workflow_dispatch:" in workflow_text
        assert "pull_request:" not in workflow_text
        assert "pull_request_target:" not in workflow_text
        assert "schedule:" not in workflow_text
        assert "cron" not in workflow_text

    def test_inputs_declared(self, workflow_text) -> None:
        assert "issue_number:" in workflow_text
        assert "dry_run:" in workflow_text
        assert "required: true" in workflow_text
        assert "default: true" in workflow_text

    def test_concurrency_one_no_cancel(self, workflow_text) -> None:
        assert "group: copilot-dispatch" in workflow_text
        assert "cancel-in-progress: false" in workflow_text
        for line in workflow_text.splitlines():
            if "group:" in line:
                value = line.split(":", 1)[1].strip()
                assert value == "copilot-dispatch", (
                    f"concurrency group must be exactly copilot-dispatch, got {value!r}"
                )

    def test_least_privilege_permissions(self, workflow_text) -> None:
        assert "permissions:" in workflow_text
        assert "contents: read" in workflow_text
        # Every permissions: block (top-level and job-level) must only grant
        # read scopes — no write scope of any kind may appear in any block.
        for text in workflow_text.split("permissions:")[1:]:
            block = text.split("\n\n")[0]
            for line in block.splitlines():
                stripped = line.strip()
                if not stripped:
                    continue
                if stripped == "contents: read" or stripped.startswith("#"):
                    continue
                assert ": write" not in stripped and "write-all" not in stripped, (
                    f"permissions block must only grant read scopes, got {stripped!r}"
                )
        assert "pull-requests: write" not in workflow_text
        assert "issues: write" not in workflow_text
        assert "write-all" not in workflow_text

    def test_trusted_default_branch_checkout(self, workflow_text) -> None:
        assert "ref: ${{ github.event.repository.default_branch }}" in workflow_text

    def test_persist_credentials_false_on_checkout(self, workflow_text) -> None:
        assert "persist-credentials: false" in workflow_text

    def test_dispatch_job_references_protected_environment(self, workflow_text) -> None:
        lines = workflow_text.splitlines()
        in_dispatch_job = False
        found_environment = False
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("dispatch:"):
                in_dispatch_job = True
            elif in_dispatch_job and stripped and not stripped.startswith("#"):
                if stripped.startswith("environment:"):
                    value = stripped.split(":", 1)[1].strip()
                    if value == "copilot-dispatch":
                        found_environment = True
                if stripped.startswith("name:") or stripped.startswith("runs-on:") or stripped.startswith("jobs:"):
                    if stripped.startswith("jobs:"):
                        in_dispatch_job = False
        assert found_environment, (
            "dispatch job must reference environment: copilot-dispatch"
        )

    def test_no_scheduling_batching_or_automation(self, workflow_text) -> None:
        for forbidden in (
            "schedule:", "- cron", "issues:", "auto-merge", "roadmap",
            "milestone", "batch", "poll",
        ):
            assert forbidden not in workflow_text

    def test_both_secrets_referenced_separately(self, workflow_text) -> None:
        assert "COPILOT_ASSIGN_TOKEN: ${{ secrets.COPILOT_ASSIGN_TOKEN }}" in workflow_text
        assert "PROJECT_SYNC_TOKEN: ${{ secrets.PROJECT_SYNC_TOKEN }}" in workflow_text

    def test_dry_run_defaults_true_in_workflow(self, workflow_text) -> None:
        assert "default: true" in workflow_text


class TestSecretIsolationAcrossWorkflows:
    @staticmethod
    def _workflow_files() -> list:
        return sorted(
            list(WORKFLOWS_DIR.glob("*.yml")) + list(WORKFLOWS_DIR.glob("*.yaml"))
        )

    @staticmethod
    def _references_dispatch_secret(text: str) -> bool:
        lowered = text.lower()
        for name in ("copilot_assign_token", "project_sync_token"):
            if name in lowered:
                return True
        return False

    def test_only_dispatch_workflow_references_dispatch_secrets(self) -> None:
        secret_owners = [
            workflow_file.name
            for workflow_file in self._workflow_files()
            if self._references_dispatch_secret(
                workflow_file.read_text(encoding="utf-8")
            )
        ]
        assert secret_owners == ["copilot-dispatch.yml"]

    def test_pull_request_workflows_never_reference_dispatch_secrets(self) -> None:
        found = []
        for workflow_file in self._workflow_files():
            text = workflow_file.read_text(encoding="utf-8")
            lowered = text.lower()
            is_pr_triggered = (
                "pull_request:" in lowered or "pull_request_target:" in lowered
            )
            references_secret = self._references_dispatch_secret(text)
            if is_pr_triggered and references_secret:
                found.append(workflow_file.name)
        assert found == [], found

    def test_pull_request_workflows_never_reference_dispatch_environment(self) -> None:
        found = []
        for workflow_file in self._workflow_files():
            text = workflow_file.read_text(encoding="utf-8")
            lowered = text.lower()
            is_pr_triggered = (
                "pull_request:" in lowered or "pull_request_target:" in lowered
            )
            references_env = "copilot-dispatch" in lowered
            if is_pr_triggered and references_env:
                found.append(workflow_file.name)
        assert found == [], found


# ---------------------------------------------------------------------------
# Active-state integrity
# ---------------------------------------------------------------------------


ACTIVE_STATE = REPO_ROOT / ".cg-docs" / "active-state" / "current.json"


class TestActiveStateIntegrity:
    def test_current_json_has_no_duplicate_keys(self) -> None:
        raw = ACTIVE_STATE.read_text(encoding="utf-8-sig")
        duplicates: list[str] = []

        def _collect_dupes(pairs):
            seen: dict = {}
            for key, value in pairs:
                if key in seen:
                    duplicates.append(key)
                seen[key] = value
            return seen

        json.loads(raw, object_pairs_hook=_collect_dupes)
        assert duplicates == [], (
            f"current.json contains duplicate keys: {duplicates}"
        )

    def test_blocked_current_json_has_valid_blocking_decision(self) -> None:
        data = json.loads(ACTIVE_STATE.read_text(encoding="utf-8-sig"))
        decisions = data.get("unresolvedDecisions", [])
        assert isinstance(decisions, list)
        for decision in decisions:
            assert isinstance(decision, dict)
            assert isinstance(decision.get("id"), str) and decision["id"].strip()
            assert isinstance(decision.get("summary"), str) and decision["summary"].strip()
            assert isinstance(decision.get("blocking"), bool)
        if data.get("status") == "blocked":
            assert any(decision["blocking"] for decision in decisions)

    def test_handoff_targets_dev_branch(self) -> None:
        text = ACTIVE_STATE.read_text(encoding="utf-8-sig")
        next_cmd = json.loads(text).get("nextCommand", "")
        assert "main" not in next_cmd.lower() or "dev" in next_cmd.lower(), (
            "nextCommand must reference dev, not main"
        )
