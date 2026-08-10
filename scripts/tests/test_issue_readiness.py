"""Deterministic tests for the Copilot issue readiness validator.

All tests use inline fixtures and mocked GitHub responses. No test depends on
live GitHub state, and no test performs any GitHub mutation.
"""
from __future__ import annotations

import io
import json
import subprocess
import sys
from pathlib import Path

import pytest

from issues.readiness import (
    ApiError,
    ConfigError,
    EXIT_API,
    EXIT_CONFIG,
    EXIT_NOT_READY,
    EXIT_READY,
    FixtureClient,
    GhCliClient,
    IssueRecord,
    PR_LIST_LIMIT,
    PRRecord,
    RuleResult,
    _classify_gh_error,
    _default_run_gh,
    _brackets_unbalanced,
    _extract_checkboxes,
    _extract_path_entries,
    _extract_risk_class,
    _has_blocking_dependency,
    _PROJECT_STATUS_QUERY,
    _verification_commands_nonempty,
    _is_overbroad_allowed_path,
    copilot_assignees,
    is_copilot_assignee,
    main,
    pr_closes_issue,
    render_json,
    result_to_dict,
    validate_contract,
    validate_path_entry,
    validate_readiness,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_JSON = REPO_ROOT / "scripts" / "tests" / "fixtures" / "ready_issue.json"


GOOD_BODY = """\
<!-- compound-gpid-tracked: example-ready-issue -->

## Summary

Example implementation-ready issue used as a non-production fixture.

## Roadmap linkage

- **Feature ID:** `example-ready-issue`
- **Roadmap milestone:** `workflow-maturity`

## Ready for Copilot

- [x] Human has reviewed and approved this execution contract
- [x] Roadmap feature has been created and linked to this issue
- [x] Exact allowed-path closure has been confirmed
- [x] Project Status has been changed from `Backlog` to `Ready`

## Outcome

The example behavior is implemented and objectively verified.

## Acceptance criteria

- [ ] The example module produces the expected output
- [ ] The focused test suite passes

## Scope

Included:

- update one example module
- update the focused tests

## Non-goals

- no GitHub Actions workflow changes
- no new dependencies

## Expected allowed paths

- `docs/example.md`
- `scripts/example.py`
- `scripts/tests/test_example.py`

## Prohibited paths

- `.github/workflows/**`
- `roadmap.json`
- `tests/Run-Tests.ps1`

## Verification commands

```bash
python -m pytest scripts/tests/test_example.py -q
```

## Dependencies / blockers

None currently known.

## Risk class

`low`

## Human review instructions

- Confirm the diff touches only allowed paths
- Confirm every acceptance criterion is objectively met

## Blocked-stop conditions

- Copilot edits any prohibited path
- Required CI is red after fix attempts are exhausted
"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class FakeClient:
    """In-memory GitHub client for tests. Records every call (all reads)."""

    def __init__(
        self,
        body: str = GOOD_BODY,
        prs: list[PRRecord] | None = None,
        status: str | None = "Ready",
        assignees: list[str] | None = None,
        state: str = "OPEN",
        number: int = 9001,
    ) -> None:
        self._issue = IssueRecord(
            number=number,
            title="Example issue",
            body=body,
            state=state,
            assignees=list(assignees or ["example-maintainer"]),
            labels=["cg:roadmap"],
        )
        self._prs = list(prs or [])
        self._status = status
        self.calls: list[tuple[str, int]] = []

    def get_issue(self, issue_number: int) -> IssueRecord:
        self.calls.append(("get_issue", issue_number))
        return self._issue

    def get_open_closing_prs(self, issue_number: int) -> list[PRRecord]:
        self.calls.append(("get_open_closing_prs", issue_number))
        return self._prs

    def get_project_status(self, issue_number: int) -> str | None:
        self.calls.append(("get_project_status", issue_number))
        return self._status


class RaisingClient:
    """Client whose first call raises, to test failure-mode exit codes."""

    def __init__(self, error: Exception) -> None:
        self._error = error
        self.calls: list[str] = []

    def get_issue(self, issue_number: int) -> IssueRecord:
        self.calls.append("get_issue")
        raise self._error

    def get_open_closing_prs(self, issue_number: int) -> list[PRRecord]:
        self.calls.append("get_open_closing_prs")
        raise self._error

    def get_project_status(self, issue_number: int) -> str | None:
        self.calls.append("get_project_status")
        raise self._error


def _section_lines(body: str, name: str) -> list[str]:
    out: list[str] = []
    capture = False
    for line in body.splitlines():
        if line.startswith("## ") and line[3:].strip() == name:
            capture = True
            out.append(line)
            continue
        if capture and line.startswith("## "):
            capture = False
        if capture:
            out.append(line)
    return out


def remove_section(body: str, name: str) -> str:
    result: list[str] = []
    skip = False
    for line in body.splitlines():
        if line.startswith("## ") and line[3:].strip() == name:
            skip = True
            continue
        if skip and line.startswith("## "):
            skip = False
        if not skip:
            result.append(line)
    return "\n".join(result) + "\n"


def duplicate_section(body: str, name: str) -> str:
    sec = _section_lines(body, name)
    if not sec:
        return body
    return body.rstrip("\n") + "\n" + "\n".join(sec) + "\n"


def replace_section_body(body: str, name: str, new_content: str) -> str:
    result: list[str] = []
    in_section = False
    for line in body.splitlines():
        if line.startswith("## ") and line[3:].strip() == name:
            result.append(line)
            result.append(new_content)
            in_section = True
            continue
        if in_section and line.startswith("## "):
            in_section = False
        if not in_section:
            result.append(line)
    return "\n".join(result) + "\n"


def _rule(result, rule_id: str) -> RuleResult:
    for item in result.rules:
        if item.id == rule_id:
            return item
    raise AssertionError(f"rule {rule_id} not present in result")


def _failed_ids(result) -> set[str]:
    return {rule.id for rule in result.rules if not rule.passed}


def _contract_by_id(body: str) -> dict[str, RuleResult]:
    return {rule.id: rule for rule in validate_contract(body)}


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


def test_happy_path_contract_and_state_ready() -> None:
    result = validate_readiness(9001, FakeClient())

    assert result.ready is True
    assert result.exit_code == EXIT_READY
    assert result.exit_reason == "ready"
    assert _failed_ids(result) == set()


def test_happy_path_all_rules_present() -> None:
    result = validate_readiness(9001, FakeClient())
    ids = [rule.id for rule in result.rules]
    assert ids == [f"R{n:03d}" for n in range(1, 22)]


# ---------------------------------------------------------------------------
# Contract-rule failure scenarios
# ---------------------------------------------------------------------------


def test_missing_required_section_fails() -> None:
    body = remove_section(GOOD_BODY, "Acceptance criteria")
    result = validate_readiness(9001, FakeClient(body=body))

    assert result.exit_code == EXIT_NOT_READY
    assert "R004" in _failed_ids(result)
    assert "Acceptance criteria" in _rule(result, "R004").detail


def test_duplicate_critical_section_fails() -> None:
    body = duplicate_section(GOOD_BODY, "Risk class")
    result = validate_readiness(9001, FakeClient(body=body))

    assert result.exit_code == EXIT_NOT_READY
    assert "R005" in _failed_ids(result)
    assert "Risk class" in _rule(result, "R005").detail


def test_unchecked_readiness_confirmation_fails() -> None:
    body = replace_section_body(
        GOOD_BODY, "Ready for Copilot",
        "- [x] Human has reviewed and approved this execution contract\n"
        "- [ ] Roadmap feature has been created and linked to this issue\n"
        "- [x] Exact allowed-path closure has been confirmed\n"
        "- [x] Project Status has been changed from `Backlog` to `Ready`",
    )
    result = validate_readiness(9001, FakeClient(body=body))

    assert result.exit_code == EXIT_NOT_READY
    assert "R006" in _failed_ids(result)
    assert "unchecked" in _rule(result, "R006").detail


def test_feature_id_marker_mismatch_fails() -> None:
    body = GOOD_BODY.replace(
        "<!-- compound-gpid-tracked: example-ready-issue -->",
        "<!-- compound-gpid-tracked: a-different-feature -->",
    )
    result = validate_readiness(9001, FakeClient(body=body))

    assert "R001" not in _failed_ids(result)
    assert "R002" not in _failed_ids(result)
    assert "R003" in _failed_ids(result)
    assert result.exit_code == EXIT_NOT_READY


def test_missing_allowed_paths_fails() -> None:
    body = replace_section_body(GOOD_BODY, "Expected allowed paths", "None.")
    result = validate_readiness(9001, FakeClient(body=body))

    assert "R010" in _failed_ids(result)
    assert result.exit_code == EXIT_NOT_READY


def test_empty_roadmap_linkage_fails_required_contract() -> None:
    body = replace_section_body(GOOD_BODY, "Roadmap linkage", "")
    result = validate_readiness(9001, FakeClient(body=body))

    assert "R004" in _failed_ids(result)
    assert "Roadmap linkage" in _rule(result, "R004").detail
    assert result.exit_code == EXIT_NOT_READY


def test_missing_prohibited_paths_fails() -> None:
    body = replace_section_body(GOOD_BODY, "Prohibited paths", "None.")
    result = validate_readiness(9001, FakeClient(body=body))

    assert "R011" in _failed_ids(result)
    assert result.exit_code == EXIT_NOT_READY


def test_path_traversal_and_absolute_paths_fail() -> None:
    body = replace_section_body(
        GOOD_BODY, "Expected allowed paths",
        "- `/etc/passwd`\n"
        "- `../escape`\n"
        "- `a/../../b`\n"
        "- `C:\\windows\\system`\n"
        "- `docs/ok.md`\n",
    )
    result = validate_readiness(9001, FakeClient(body=body))

    assert "R012" in _failed_ids(result)
    assert "4 unsafe" in _rule(result, "R012").detail


def test_overbroad_allowed_paths_fail() -> None:
    body = replace_section_body(
        GOOD_BODY, "Expected allowed paths",
        "- `**`\n- `*`\n- `.`\n- `docs/ok.md`\n",
    )
    result = validate_readiness(9001, FakeClient(body=body))

    assert "R012" in _failed_ids(result)
    assert "overbroad" in _rule(result, "R012").detail


def test_broad_glob_allowed_as_prohibited_path() -> None:
    body = replace_section_body(GOOD_BODY, "Prohibited paths", "- `.github/workflows/**`")
    result = validate_readiness(9001, FakeClient(body=body))

    assert "R011" not in _failed_ids(result)
    assert "R012" not in _failed_ids(result)


def test_empty_verification_commands_fails() -> None:
    body = replace_section_body(
        GOOD_BODY, "Verification commands",
        "Run the tests manually and look at the output.",
    )
    result = validate_readiness(9001, FakeClient(body=body))

    assert "R008" in _failed_ids(result)
    assert result.exit_code == EXIT_NOT_READY


def test_invalid_risk_classification_fails() -> None:
    body = replace_section_body(GOOD_BODY, "Risk class", "`critical`")
    result = validate_readiness(9001, FakeClient(body=body))

    assert "R009" in _failed_ids(result)
    assert result.exit_code == EXIT_NOT_READY


def test_blocked_dependency_fails() -> None:
    body = replace_section_body(
        GOOD_BODY, "Dependencies / blockers",
        "- [ ] Depends on #5 being resolved\n"
        "- blocked by #5",
    )
    result = validate_readiness(9001, FakeClient(body=body))

    assert "R014" in _failed_ids(result)
    assert result.exit_code == EXIT_NOT_READY


def test_resolved_dependency_is_not_blocking() -> None:
    body = replace_section_body(
        GOOD_BODY, "Dependencies / blockers",
        "- [x] Depends on #5 (resolved)",
    )
    result = validate_readiness(9001, FakeClient(body=body))

    assert "R014" not in _failed_ids(result)


def test_negated_blocked_by_is_not_blocking() -> None:
    body = replace_section_body(
        GOOD_BODY, "Dependencies / blockers",
        "This issue is not blocked by anything else.",
    )
    result = validate_readiness(9001, FakeClient(body=body))

    assert "R014" not in _failed_ids(result)


def test_same_line_negation_does_not_mask_real_blocker() -> None:
    body = replace_section_body(
        GOOD_BODY, "Dependencies / blockers",
        "This is not blocked by A but is blocked by B.",
    )
    result = validate_readiness(9001, FakeClient(body=body))

    assert "R014" in _failed_ids(result)


@pytest.mark.parametrize(
    "prose",
    [
        "This issue cannot be blocked by anything else.",
        "This issue can't be blocked by external requests.",
        "This is not blocked by anything else.",
        "Nothing blocks this issue.",
    ],
)
def test_non_blocking_prose_is_not_blocking(prose: str) -> None:
    body = replace_section_body(
        GOOD_BODY, "Dependencies / blockers", prose,
    )
    result = validate_readiness(9001, FakeClient(body=body))

    assert "R014" not in _failed_ids(result)


def test_bare_unchecked_dependency_item_is_blocking() -> None:
    body = replace_section_body(
        GOOD_BODY, "Dependencies / blockers", "- [ ]",
    )
    result = validate_readiness(9001, FakeClient(body=body))

    assert "R014" in _failed_ids(result)


def test_missing_marker_fails() -> None:
    body = GOOD_BODY.replace(
        "<!-- compound-gpid-tracked: example-ready-issue -->\n\n", "", 1
    )
    result = validate_readiness(9001, FakeClient(body=body))

    assert "R001" in _failed_ids(result)


def test_missing_feature_id_line_fails() -> None:
    body = GOOD_BODY.replace("- **Feature ID:** `example-ready-issue`\n", "")
    result = validate_readiness(9001, FakeClient(body=body))

    assert "R002" in _failed_ids(result)
    assert "R003" in _failed_ids(result)


def test_duplicate_feature_id_line_fails() -> None:
    body = GOOD_BODY.replace(
        "- **Feature ID:** `example-ready-issue`\n",
        "- **Feature ID:** `example-ready-issue`\n- **Feature ID:** `other-id`\n",
    )
    result = validate_readiness(9001, FakeClient(body=body))

    assert "R002" in _failed_ids(result)


def test_malformed_feature_id_format_fails() -> None:
    body = GOOD_BODY.replace("`example-ready-issue`", "`Bad_Id`", 1)
    result = validate_readiness(9001, FakeClient(body=body))

    assert "R002" in _failed_ids(result)
    assert "R003" in _failed_ids(result)


def test_empty_acceptance_criteria_fails_but_section_present() -> None:
    body = replace_section_body(GOOD_BODY, "Acceptance criteria", "")
    result = validate_readiness(9001, FakeClient(body=body))

    assert "R007" in _failed_ids(result)
    assert "R004" not in _failed_ids(result)


@pytest.mark.parametrize(
    "section, rule_id",
    [
        ("Blocked-stop conditions", "R013"),
        ("Outcome", "R015"),
        ("Scope", "R016"),
        ("Non-goals", "R017"),
        ("Human review instructions", "R018"),
    ],
)
def test_nonempty_section_absent_fails(section: str, rule_id: str) -> None:
    body = remove_section(GOOD_BODY, section)
    result = validate_readiness(9001, FakeClient(body=body))

    assert rule_id in _failed_ids(result)
    assert result.exit_code == EXIT_NOT_READY


@pytest.mark.parametrize(
    "section, rule_id",
    [
        ("Blocked-stop conditions", "R013"),
        ("Outcome", "R015"),
        ("Scope", "R016"),
        ("Non-goals", "R017"),
        ("Human review instructions", "R018"),
    ],
)
def test_nonempty_section_empty_fails_but_section_present(section: str, rule_id: str) -> None:
    body = replace_section_body(GOOD_BODY, section, "")
    result = validate_readiness(9001, FakeClient(body=body))

    assert rule_id in _failed_ids(result)
    assert "R004" not in _failed_ids(result)
    assert result.exit_code == EXIT_NOT_READY


def test_empty_issue_body_fails_all_contract_rules() -> None:
    result = validate_readiness(9001, FakeClient(body=""))

    assert result.ready is False
    assert result.exit_code == EXIT_NOT_READY
    contract_ids = {"R001", "R002", "R003", "R004", "R006", "R007",
                    "R008", "R009", "R010", "R011", "R013",
                    "R015", "R016", "R017", "R018"}
    assert contract_ids <= _failed_ids(result)
    # R005, R012, R014 are expected not to fail on an empty body.
    assert _failed_ids(result) & {"R005", "R012", "R014"} == set()


def test_whitespace_only_body_fails_all_contract_rules() -> None:
    result = validate_readiness(9001, FakeClient(body="   \n\t\n  "))

    assert result.ready is False
    contract_ids = {"R001", "R002", "R003", "R004", "R006", "R007",
                    "R008", "R009", "R010", "R011", "R013",
                    "R015", "R016", "R017", "R018"}
    assert contract_ids <= _failed_ids(result)
    # R005, R012, R014 are expected not to fail on an empty body.
    assert _failed_ids(result) & {"R005", "R012", "R014"} == set()


def test_risk_class_in_prose_is_not_accepted() -> None:
    body = replace_section_body(
        GOOD_BODY, "Risk class", "We have low confidence in the timeline.",
    )
    result = validate_readiness(9001, FakeClient(body=body))

    assert "R009" in _failed_ids(result)


def test_tilde_fence_is_ignored() -> None:
    body = GOOD_BODY + "\n## Notes\n\n~~~\n## Expected allowed paths\n- `evil`\n~~~\n"
    by_id = _contract_by_id(body)

    assert by_id["R010"].passed is True
    assert by_id["R012"].passed is True


def test_project_status_none_is_not_ready() -> None:
    result = validate_readiness(9001, FakeClient(status=None))

    assert "R019" in _failed_ids(result)
    assert result.state["projectStatus"] is None
    assert result.exit_code == EXIT_NOT_READY


# ---------------------------------------------------------------------------
# State-rule failure scenarios
# ---------------------------------------------------------------------------


def test_existing_open_implementation_pr_fails() -> None:
    pr = PRRecord(
        number=42, title="Impl", body="Closes #9001\n\nImplementation work.",
        url="https://github.com/o/r/pull/42", head_ref="copilot/x", author="Copilot",
    )
    result = validate_readiness(9001, FakeClient(prs=[pr]))

    assert "R020" in _failed_ids(result)
    assert result.exit_code == EXIT_NOT_READY
    assert result.state["openClosingPRs"][0]["number"] == 42


def test_copilot_already_assigned_fails() -> None:
    result = validate_readiness(9001, FakeClient(assignees=["copilot-swe-agent[bot]", "randrescastaneda"]))

    assert "R021" in _failed_ids(result)
    assert result.exit_code == EXIT_NOT_READY
    assert result.state["copilotAssigned"] is True


def test_project_status_not_ready_fails() -> None:
    result = validate_readiness(9001, FakeClient(status="Backlog"))

    assert "R019" in _failed_ids(result)
    assert result.exit_code == EXIT_NOT_READY
    assert result.state["projectStatus"] == "Backlog"


# ---------------------------------------------------------------------------
# API / network / config failure modes
# ---------------------------------------------------------------------------


def test_api_network_failure_exit_code() -> None:
    result = validate_readiness(127, RaisingClient(ApiError("HTTP 502 Bad Gateway")))

    assert result.exit_code == EXIT_API
    assert result.exit_reason == "api_error"
    assert result.ready is False
    assert result.errors and result.errors[0]["type"] == "api_error"
    assert result.rules == []


def test_config_failure_exit_code() -> None:
    result = validate_readiness(127, RaisingClient(ConfigError("gh CLI not found")))

    assert result.exit_code == EXIT_CONFIG
    assert result.exit_reason == "config_error"
    assert result.ready is False
    assert result.errors and result.errors[0]["type"] == "config_error"


# ---------------------------------------------------------------------------
# JSON output and exit-code behavior
# ---------------------------------------------------------------------------


def test_json_output_shape_for_ready() -> None:
    result = validate_readiness(9001, FakeClient())
    payload = json.loads(render_json(result))

    assert payload["ready"] is True
    assert payload["exitCode"] == EXIT_READY
    assert payload["exitReason"] == "ready"
    assert payload["summary"] == "READY"
    assert len(payload["rules"]) == 21
    assert payload["failedRules"] == []
    assert payload["state"]["projectStatus"] == "Ready"
    assert payload["errors"] == []


def test_json_output_shape_for_not_ready() -> None:
    result = validate_readiness(9001, FakeClient(status="Backlog"))
    payload = json.loads(render_json(result))

    assert payload["ready"] is False
    assert payload["exitCode"] == EXIT_NOT_READY
    assert payload["failedRules"]
    failed_ids = {item["id"] for item in payload["failedRules"]}
    assert "R019" in failed_ids


def test_cli_fixture_ready_exit_zero() -> None:
    buf = io.StringIO()
    rc = main(["--fixture", str(FIXTURE_JSON), "--dry-run", "--json"], out=buf)

    assert rc == EXIT_READY
    payload = json.loads(buf.getvalue())
    assert payload["ready"] is True
    assert payload["dryRun"] is True


def test_cli_live_not_ready_exit_two() -> None:
    buf = io.StringIO()
    rc = main(["--issue", "9001", "--dry-run"], client=FakeClient(status="Backlog"), out=buf)

    assert rc == EXIT_NOT_READY
    assert "NOT READY" in buf.getvalue()


def test_cli_live_api_error_exit_four() -> None:
    buf = io.StringIO()
    rc = main(
        ["--issue", "127", "--dry-run", "--json"],
        client=RaisingClient(ApiError("network down")),
        out=buf,
    )

    assert rc == EXIT_API
    payload = json.loads(buf.getvalue())
    assert payload["exitCode"] == EXIT_API


def test_cli_live_config_error_exit_three() -> None:
    buf = io.StringIO()
    rc = main(
        ["--issue", "1", "--dry-run", "--json"],
        client=RaisingClient(ConfigError("gh CLI not found")),
        out=buf,
    )

    assert rc == EXIT_CONFIG
    payload = json.loads(buf.getvalue())
    assert payload["exitCode"] == EXIT_CONFIG


def test_cli_missing_fixture_exit_config() -> None:
    rc = main(
        ["--fixture", "does-not-exist.json", "--dry-run"],
        out=io.StringIO(), err=io.StringIO(),
    )

    assert rc == EXIT_CONFIG


def test_cli_empty_fixture_path_exit_config() -> None:
    buf = io.StringIO()
    rc = main(["--fixture", "", "--dry-run", "--json"], out=buf)

    assert rc == EXIT_CONFIG
    assert json.loads(buf.getvalue())["exitCode"] == EXIT_CONFIG


def test_legacy_readiness_module_is_directly_executable() -> None:
    completed = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "issues" / "readiness.py"),
         "--fixture", str(FIXTURE_JSON), "--dry-run", "--json"],
        cwd=REPO_ROOT, capture_output=True, text=True,
    )

    assert completed.returncode == EXIT_READY, completed.stderr
    assert json.loads(completed.stdout)["ready"] is True


def test_readiness_facade_preserves_historical_helpers() -> None:
    assert _extract_checkboxes(["- [x] ready"]) == [True]
    assert _extract_path_entries(["- `scripts/example.py`"]) == ["scripts/example.py"]
    assert _extract_risk_class(["`low`"]) == "low"
    assert _has_blocking_dependency(["None currently known."]) == (False, "")
    assert _verification_commands_nonempty(["```bash", "pytest", "```"])
    assert _brackets_unbalanced("[path") is True
    assert "query ReadinessStatus" in _PROJECT_STATUS_QUERY


def test_cli_requires_a_source() -> None:
    with pytest.raises(SystemExit) as exc:
        main([], out=io.StringIO(), err=io.StringIO())
    assert exc.value.code == EXIT_CONFIG


def test_cli_rejects_both_issue_and_fixture() -> None:
    with pytest.raises(SystemExit) as exc:
        main(
            ["--issue", "1", "--fixture", str(FIXTURE_JSON)],
            out=io.StringIO(), err=io.StringIO(),
        )
    assert exc.value.code == EXIT_CONFIG


def test_cli_non_integer_issue_exit_config() -> None:
    with pytest.raises(SystemExit) as exc:
        main(["--issue", "abc", "--dry-run"], out=io.StringIO(), err=io.StringIO())
    assert exc.value.code == EXIT_CONFIG


def test_cli_human_output_config_label() -> None:
    buf = io.StringIO()
    rc = main(
        ["--issue", "1", "--dry-run"],
        client=RaisingClient(ConfigError("gh CLI not found")),
        out=buf,
    )
    assert rc == EXIT_CONFIG
    assert "CANNOT COMPLETE (config)" in buf.getvalue()


def test_cli_human_output_api_label() -> None:
    buf = io.StringIO()
    rc = main(
        ["--issue", "1", "--dry-run"],
        client=RaisingClient(ApiError("network down")),
        out=buf,
    )
    assert rc == EXIT_API
    assert "CANNOT COMPLETE (api/network)" in buf.getvalue()


def test_cli_fixture_invalid_json_exit_config(tmp_path) -> None:
    bad = tmp_path / "bad.json"
    bad.write_text("{ not json", encoding="utf-8")
    rc = main(["--fixture", str(bad), "--dry-run"], out=io.StringIO())
    assert rc == EXIT_CONFIG


def test_cli_fixture_invalid_body_file_path_exit_config(tmp_path) -> None:
    fixture = tmp_path / "fixture.json"
    fixture.write_text(
        json.dumps({
            "issue": {"number": 7, "body": ""},
            "bodyFile": "\x00",
        }),
        encoding="utf-8",
    )

    rc = main(["--fixture", str(fixture), "--dry-run"], out=io.StringIO())

    assert rc == EXIT_CONFIG


def test_cli_fixture_deeply_nested_json_exit_config(tmp_path) -> None:
    fixture = tmp_path / "fixture.json"
    fixture.write_text("[" * 3000 + "0" + "]" * 3000, encoding="utf-8")

    rc = main(["--fixture", str(fixture), "--dry-run"], out=io.StringIO())

    assert rc == EXIT_CONFIG


def test_cli_fixture_missing_body_file_exit_config(tmp_path) -> None:
    fixture = tmp_path / "fixture.json"
    fixture.write_text(
        json.dumps({"issue": {"number": 7, "body": ""}, "bodyFile": "missing.md"}),
        encoding="utf-8",
    )
    rc = main(["--fixture", str(fixture), "--dry-run"], out=io.StringIO())
    assert rc == EXIT_CONFIG


def test_fixture_client_normalizes_gh_wire_format() -> None:
    client = FixtureClient(str(FIXTURE_JSON))
    issue = client.get_issue(9001)

    assert issue.assignees == ["example-maintainer"]
    assert issue.labels == ["cg:roadmap"]


@pytest.mark.parametrize(
    "issue_overrides",
    [
        {"assignees": ["example-maintainer"]},
        {"labels": ["cg:roadmap"]},
        {"assignees": [{"login": 42}]},
        {"labels": [{"name": None}]},
    ],
)
def test_fixture_client_rejects_malformed_assignee_or_label_shapes(
    tmp_path, issue_overrides: dict,
) -> None:
    issue = {
        "number": 9001,
        "title": "Fixture",
        "body": "",
        "state": "OPEN",
        "assignees": [{"login": "example-maintainer"}],
        "labels": [{"name": "cg:roadmap"}],
    }
    issue.update(issue_overrides)
    fixture = tmp_path / "fixture.json"
    fixture.write_text(
        json.dumps({"issue": issue, "projectStatus": "Ready"}),
        encoding="utf-8",
    )

    with pytest.raises(ConfigError):
        FixtureClient(str(fixture))


def test_fixture_client_rejects_malformed_pr_shape(tmp_path) -> None:
    fixture = tmp_path / "fixture.json"
    fixture.write_text(json.dumps({
        "issue": {
            "number": 9001, "title": "Fixture", "body": "", "state": "OPEN",
            "assignees": [], "labels": [],
        },
        "openClosingPRs": [{
            "number": 42, "title": "PR", "body": "", "url": "u",
            "headRef": "wrong-key", "author": {"login": "human"},
        }],
        "projectStatus": "Ready",
    }), encoding="utf-8")

    with pytest.raises(ConfigError, match="headRefName"):
        FixtureClient(str(fixture))


# ---------------------------------------------------------------------------
# No-mutation guarantee
# ---------------------------------------------------------------------------


def test_validation_calls_only_read_methods() -> None:
    client = FakeClient()
    validate_readiness(9001, client)

    assert [call[0] for call in client.calls] == [
        "get_issue", "get_open_closing_prs", "get_project_status",
    ]


class RecordingRunner:
    """Records gh arg lists and returns canned JSON for read commands."""

    READ_PAIRS = {("issue", "view"), ("pr", "list"), ("api", "graphql"), ("repo", "view")}

    def __init__(self, issue_json, pr_json, graphql_json, repo_json) -> None:
        self.calls: list[list[str]] = []
        self._issue = issue_json
        self._pr = pr_json
        self._gql = graphql_json
        self._repo = repo_json

    def __call__(self, args: list[str]) -> subprocess.CompletedProcess:
        self.calls.append(list(args))
        if args[:2] == ["repo", "view"]:
            stdout = json.dumps(self._repo)
        elif args[:2] == ["issue", "view"]:
            stdout = json.dumps(self._issue)
        elif args[:2] == ["pr", "list"]:
            stdout = json.dumps(self._pr)
        elif args[:2] == ["api", "graphql"]:
            stdout = json.dumps(self._gql)
        else:
            stdout = "[]"
        return subprocess.CompletedProcess(args=["gh", *args], returncode=0, stdout=stdout, stderr="")


def test_gh_cli_client_only_issues_read_commands() -> None:
    runner = RecordingRunner(
        issue_json={
            "number": 127, "title": "t", "body": GOOD_BODY, "state": "OPEN",
            "assignees": [{"login": "randrescastaneda"}],
            "labels": [{"name": "cg:roadmap"}],
        },
        pr_json=[],
        graphql_json={
            "data": {"repository": {"issue": {"projectItems": {"nodes": [
                {"project": {"title": "CompoundGPID-progress"},
                 "fieldValueByName": {"name": "Ready"}},
            ]}}}},
        },
        repo_json={"nameWithOwner": "GPID-WB/compound-gpid"},
    )
    client = GhCliClient(runner=runner)

    issue = client.get_issue(127)
    assert issue.body == GOOD_BODY
    assert issue.assignees == ["randrescastaneda"]

    prs = client.get_open_closing_prs(127)
    assert prs == []

    status = client.get_project_status(127)
    assert status == "Ready"

    for call in runner.calls:
        assert tuple(call[:2]) in RecordingRunner.READ_PAIRS, f"non-read gh command: {call}"


def test_gh_cli_client_classifies_errors() -> None:
    def _completed(stderr: str, returncode: int = 1) -> subprocess.CompletedProcess:
        return subprocess.CompletedProcess(args=["gh"], returncode=returncode, stdout="", stderr=stderr)

    with pytest.raises(ConfigError):
        _classify_gh_error(_completed("HTTP 404: Not Found"), ["issue", "view", "9"])
    with pytest.raises(ConfigError):
        _classify_gh_error(_completed("could not find issue 9"), ["issue", "view", "9"])
    with pytest.raises(ConfigError):
        _classify_gh_error(_completed("HTTP 403: Forbidden (scope)"), ["api", "graphql"])
    with pytest.raises(ConfigError):
        _classify_gh_error(
            _completed("gh: Field 'name' doesn't exist on type 'ProjectV2'"),
            ["api", "graphql"],
        )
    with pytest.raises(ApiError):
        _classify_gh_error(_completed("HTTP 502 Bad Gateway"), ["api", "graphql"])
    with pytest.raises(ApiError):
        _classify_gh_error(_completed("rate limit exceeded"), ["pr", "list"])
    with pytest.raises(ApiError):
        _classify_gh_error(_completed("gh command timed out"), ["pr", "list"])
    with pytest.raises(ConfigError):
        _classify_gh_error(_completed("", returncode=1), ["issue", "view", "9"])
    with pytest.raises(ApiError):
        _classify_gh_error(_completed("something unrecognized", returncode=2), ["pr", "list"])


def test_gh_project_status_graphql_errors_raise_config() -> None:
    runner = RecordingRunner(
        issue_json={"number": 1, "title": "t", "body": "", "state": "OPEN",
                    "assignees": [], "labels": []},
        pr_json=[],
        graphql_json={"errors": [{"message": "Field 'x' missing"}]},
        repo_json={"nameWithOwner": "GPID-WB/compound-gpid"},
    )
    client = GhCliClient(runner=runner)
    with pytest.raises(ConfigError):
        client.get_project_status(1)


def test_gh_project_status_canonical_only_ignores_other_project() -> None:
    runner = RecordingRunner(
        issue_json={"number": 1, "title": "t", "body": "", "state": "OPEN",
                    "assignees": [], "labels": []},
        pr_json=[],
        graphql_json={"data": {"repository": {"issue": {"projectItems": {"nodes": [
            {"project": {"title": "Other Project"}, "fieldValueByName": {"name": "Ready"}},
            {"project": {"title": "CompoundGPID-progress"}, "fieldValueByName": None},
        ]}}}}},
        repo_json={"nameWithOwner": "GPID-WB/compound-gpid"},
    )
    client = GhCliClient(runner=runner)
    assert client.get_project_status(1) is None


def test_gh_project_status_none_when_not_in_any_project() -> None:
    runner = RecordingRunner(
        issue_json={"number": 1, "title": "t", "body": "", "state": "OPEN",
                    "assignees": [], "labels": []},
        pr_json=[],
        graphql_json={"data": {"repository": {"issue": {"projectItems": {"nodes": []}}}}},
        repo_json={"nameWithOwner": "GPID-WB/compound-gpid"},
    )
    client = GhCliClient(runner=runner)
    assert client.get_project_status(1) is None


def test_gh_project_status_absent_issue_returns_none() -> None:
    runner = RecordingRunner(
        issue_json={"number": 1, "title": "t", "body": "", "state": "OPEN",
                    "assignees": [], "labels": []},
        pr_json=[],
        graphql_json={"data": {"repository": {"issue": None}}},
        repo_json={"nameWithOwner": "GPID-WB/compound-gpid"},
    )
    client = GhCliClient(runner=runner)

    assert client.get_project_status(1) is None


def test_gh_project_status_non_mapping_graphql_payload_raises_api_error() -> None:
    runner = RecordingRunner(
        issue_json={"number": 1, "title": "t", "body": "", "state": "OPEN",
                    "assignees": [], "labels": []},
        pr_json=[],
        graphql_json=[1, 2],
        repo_json={"nameWithOwner": "GPID-WB/compound-gpid"},
    )
    client = GhCliClient(runner=runner)

    with pytest.raises(ApiError, match="expected object"):
        client.get_project_status(1)


def test_gh_project_status_missing_nested_payload_raises_api_error() -> None:
    runner = RecordingRunner(
        issue_json={"number": 1, "title": "t", "body": "", "state": "OPEN",
                    "assignees": [], "labels": []},
        pr_json=[],
        graphql_json={"data": {"repository": {"issue": {"projectItems": {"nodes": {}}}}}},
        repo_json={"nameWithOwner": "GPID-WB/compound-gpid"},
    )
    client = GhCliClient(runner=runner)

    with pytest.raises(ApiError, match="nodes is not a list"):
        client.get_project_status(1)


def test_gh_project_status_non_mapping_node_raises_api_error() -> None:
    runner = RecordingRunner(
        issue_json={"number": 1, "title": "t", "body": "", "state": "OPEN",
                    "assignees": [], "labels": []},
        pr_json=[],
        graphql_json={"data": {"repository": {"issue": {"projectItems": {"nodes": ["bad"]}}}}},
        repo_json={"nameWithOwner": "GPID-WB/compound-gpid"},
    )
    client = GhCliClient(runner=runner)

    with pytest.raises(ApiError, match="nodes item"):
        client.get_project_status(1)


def test_gh_project_status_absent_project_value_returns_none() -> None:
    runner = RecordingRunner(
        issue_json={"number": 1, "title": "t", "body": "", "state": "OPEN",
                    "assignees": [], "labels": []},
        pr_json=[],
        graphql_json={"data": {"repository": {"issue": {"projectItems": {"nodes": [
            {"project": None},
        ]}}}}},
        repo_json={"nameWithOwner": "GPID-WB/compound-gpid"},
    )
    client = GhCliClient(runner=runner)

    assert client.get_project_status(1) is None


def test_gh_project_status_malformed_field_value_raises_api_error() -> None:
    runner = RecordingRunner(
        issue_json={"number": 1, "title": "t", "body": "", "state": "OPEN",
                    "assignees": [], "labels": []},
        pr_json=[],
        graphql_json={"data": {"repository": {"issue": {"projectItems": {"nodes": [
            {"project": {"title": "CompoundGPID-progress"}, "fieldValueByName": "bad"},
        ]}}}}},
        repo_json={"nameWithOwner": "GPID-WB/compound-gpid"},
    )
    client = GhCliClient(runner=runner)

    with pytest.raises(ApiError, match="fieldValueByName"):
        client.get_project_status(1)


def test_gh_cli_malformed_json_raises_api_error() -> None:
    def runner(args):
        return subprocess.CompletedProcess(args=["gh", *args], returncode=0, stdout="not json", stderr="")

    client = GhCliClient(runner=runner)
    with pytest.raises(ApiError):
        client.get_issue(127)


def test_gh_cli_deeply_nested_json_raises_api_error() -> None:
    def runner(args):
        return subprocess.CompletedProcess(
            args=["gh", *args], returncode=0,
            stdout="[" * 3000 + "0" + "]" * 3000, stderr="",
        )

    with pytest.raises(ApiError):
        GhCliClient(runner=runner).get_issue(127)


def test_gh_cli_typed_invalid_issue_payload_raises_api_error() -> None:
    def runner(args):
        payload = json.dumps({"number": "abc", "title": "t", "body": "", "state": "OPEN",
                              "assignees": [], "labels": []})
        return subprocess.CompletedProcess(args=["gh", *args], returncode=0, stdout=payload, stderr="")

    client = GhCliClient(runner=runner)
    with pytest.raises(ApiError):
        client.get_issue(127)


def test_gh_cli_typed_invalid_repo_payload_raises_api_error() -> None:
    def runner(args):
        return subprocess.CompletedProcess(args=["gh", *args], returncode=0, stdout="[1, 2]", stderr="")

    client = GhCliClient(runner=runner)
    with pytest.raises(ApiError):
        client.get_project_status(127)


def test_gh_cli_invalid_name_with_owner_type_raises_api_error() -> None:
    def runner(args):
        if args[:2] == ["repo", "view"]:
            payload = json.dumps({"nameWithOwner": 42})
        else:
            payload = "{}"
        return subprocess.CompletedProcess(
            args=["gh", *args], returncode=0, stdout=payload, stderr=""
        )

    with pytest.raises(ApiError, match="nameWithOwner is not a string"):
        GhCliClient(runner=runner).get_project_status(127)


def test_gh_cli_valid_name_without_owner_separator_is_config_error() -> None:
    def runner(args):
        payload = json.dumps({"nameWithOwner": "repo-only"})
        return subprocess.CompletedProcess(
            args=["gh", *args], returncode=0, stdout=payload, stderr=""
        )

    with pytest.raises(ConfigError, match="could not determine repository"):
        GhCliClient(runner=runner).get_project_status(127)


def test_gh_cli_typed_invalid_pr_payload_raises_api_error() -> None:
    def runner(args):
        payload = json.dumps([{"number": "abc", "title": "t", "body": "Closes #127",
                               "url": "u", "headRefName": "b", "author": {"login": "x"}}])
        return subprocess.CompletedProcess(args=["gh", *args], returncode=0, stdout=payload, stderr="")

    client = GhCliClient(runner=runner)
    with pytest.raises(ApiError):
        client.get_open_closing_prs(127)


def test_gh_cli_client_parses_closing_prs() -> None:
    runner = RecordingRunner(
        issue_json={"number": 127, "title": "t", "body": "", "state": "OPEN",
                    "assignees": [], "labels": []},
        pr_json=[
            {"number": 10, "title": "A", "body": "Closes #127", "url": "u1",
             "headRefName": "b1", "author": {"login": "Copilot"}},
            {"number": 11, "title": "B", "body": "Refs #127", "url": "u2",
             "headRefName": "b2", "author": {"login": "human"}},
            {"number": 12, "title": "C", "body": "Fixes #128", "url": "u3",
             "headRefName": "b3", "author": {"login": "human"}},
        ],
        graphql_json={"data": {"repository": {"issue": {"projectItems": {"nodes": []}}}}},
        repo_json={"nameWithOwner": "GPID-WB/compound-gpid"},
    )
    client = GhCliClient(runner=runner)
    prs = client.get_open_closing_prs(127)

    assert [pr.number for pr in prs] == [10]
    assert prs[0].author == "Copilot"


def test_gh_cli_malformed_repo_view_raises_api_error() -> None:
    def runner(args):
        if args[:2] == ["repo", "view"]:
            return subprocess.CompletedProcess(args=["gh", *args], returncode=0, stdout="not json", stderr="")
        return subprocess.CompletedProcess(
            args=["gh", *args], returncode=0,
            stdout="{}", stderr="",
        )

    client = GhCliClient(runner=runner)
    with pytest.raises(ApiError):
        client.get_project_status(127)


def test_gh_cli_pr_list_uses_exact_documented_argv() -> None:
    expected = [
        "pr", "list", "--state", "open", "--json",
        "number,title,body,url,headRefName,author", "--limit", str(PR_LIST_LIMIT),
    ]
    closing_pr = {
        "number": 42,
        "title": "Implementation",
        "body": "Closes #127",
        "url": "https://github.com/GPID-WB/compound-gpid/pull/42",
        "headRefName": "feature/readiness",
        "author": {"login": "octocat"},
    }

    def runner(args):
        assert args == expected, f"unexpected gh argv: {args!r}"
        assert "--page" not in args
        return subprocess.CompletedProcess(
            args=["gh", *args], returncode=0,
            stdout=json.dumps([closing_pr]), stderr="",
        )

    client = GhCliClient(runner=runner)
    prs = client.get_open_closing_prs(127)

    assert [pr.number for pr in prs] == [42]
    assert prs[0].head_ref == "feature/readiness"


def test_gh_cli_pr_list_limit_fails_closed() -> None:
    items = [
        {"number": n, "title": f"P{n}", "body": "", "url": "u",
         "headRefName": "b", "author": {"login": "human"}}
        for n in range(PR_LIST_LIMIT)
    ]

    def runner(args):
        return subprocess.CompletedProcess(
            args=["gh", *args], returncode=0,
            stdout=json.dumps(items), stderr="",
        )

    with pytest.raises(ApiError, match="potentially truncated"):
        GhCliClient(runner=runner).get_open_closing_prs(127)


def test_default_run_gh_is_argv_safe(monkeypatch) -> None:
    captured: dict = {}

    def fake_run(args, **kwargs):
        captured["args"] = args
        captured["kwargs"] = kwargs
        return subprocess.CompletedProcess(args=["gh", *args], returncode=0, stdout="", stderr="")

    monkeypatch.setattr("issues.gh_process.subprocess.run", fake_run)
    result = _default_run_gh(["issue", "view", "1"])

    assert captured["args"] == ["gh", "issue", "view", "1"]
    assert not isinstance(captured["args"], str)
    assert captured["kwargs"].get("shell") in (None, False)
    assert result.returncode == 0


def test_default_run_gh_missing_cli_raises_config(monkeypatch) -> None:
    def fake_run(args, **kwargs):
        raise FileNotFoundError()

    monkeypatch.setattr("issues.gh_process.subprocess.run", fake_run)
    with pytest.raises(ConfigError):
        _default_run_gh(["issue", "view", "1"])


def test_default_run_gh_timeout_raises_api(monkeypatch) -> None:
    def fake_run(args, **kwargs):
        raise subprocess.TimeoutExpired(cmd=["gh", *args], timeout=60)

    monkeypatch.setattr("issues.gh_process.subprocess.run", fake_run)
    with pytest.raises(ApiError):
        _default_run_gh(["issue", "view", "1"])


def test_default_run_gh_undecodable_output_raises_api(monkeypatch) -> None:
    def fake_run(args, **kwargs):
        raise UnicodeDecodeError("utf-8", b"\xff", 0, 1, "invalid start byte")

    monkeypatch.setattr("issues.gh_process.subprocess.run", fake_run)
    with pytest.raises(ApiError):
        _default_run_gh(["issue", "view", "1"])


def test_default_run_gh_execution_os_error_raises_config(monkeypatch) -> None:
    def fake_run(args, **kwargs):
        raise PermissionError("permission denied")

    monkeypatch.setattr("issues.gh_process.subprocess.run", fake_run)
    with pytest.raises(ConfigError):
        _default_run_gh(["issue", "view", "1"])


# ---------------------------------------------------------------------------
# Pure helper units
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "entry, ok",
    [
        ("docs/foo.md", True),
        ("scripts/**/*.py", True),
        (".github/workflows/**", True),
        ("**", True),
        ("a/b/[0-9].md", True),
        ("roadmap.json", True),
        ("docs/my file.md", True),
        (".", True),
        ("/etc/passwd", False),
        (" /etc/passwd", False),
        ("../escape", False),
        (" ../escape", False),
        ("   ", False),
        ("\t/etc/passwd", False),
        ("a/../../b", False),
        ("..", False),
        ("C:/drive", False),
        ("C:\\drive", False),
        ("c:foo", False),
        ("//server/share", False),
        ("a//b", False),
        ("trailing/", False),
        ("a/[unbalanced.md", False),
        ("", False),
        ("a\\b", False),
        ("has\x00nul", False),
    ],
)
def test_validate_path_entry(entry: str, ok: bool) -> None:
    assert (validate_path_entry(entry) is None) == ok


@pytest.mark.parametrize(
    "entry, overbroad",
    [
        ("docs/foo.md", False),
        ("scripts/**/*.py", False),
        (".github/workflows/**", False),
        ("a*/b", False),
        ("docs", False),
        ("**", True),
        ("*", True),
        (".", True),
        ("..", True),
        ("*.*", True),
    ],
)
def test_is_overbroad_allowed_path(entry: str, overbroad: bool) -> None:
    assert _is_overbroad_allowed_path(entry) == overbroad


@pytest.mark.parametrize(
    "body, n, closes",
    [
        ("Closes #127", 127, True),
        ("fixes #127", 127, True),
        ("Resolves #127", 127, True),
        ("this will resolve #127 eventually", 127, True),
        ("Refs #127", 127, False),
        ("Closes #128 not 127", 127, False),
        ("closes #12", 127, False),
        ("Closes https://github.com/o/r/issues/127", 127, True),
        ("", 127, False),
        ("Closes #127\nCloses #127", 127, True),
    ],
)
def test_pr_closes_issue(body: str, n: int, closes: bool) -> None:
    assert pr_closes_issue(body, n) == closes


@pytest.mark.parametrize(
    "login, expected",
    [
        ("Copilot", False),
        ("copilot", False),
        ("copilot-swe-agent", False),
        ("copilot-swe-agent[bot]", True),
        ("github-copilot[bot]", False),
        ("copilot-x", False),
        ("copilotbot", False),
        ("randrescastaneda", False),
        ("", False),
        ("NotCopilot", False),
    ],
)
def test_is_copilot_assignee(login: str, expected: bool) -> None:
    assert is_copilot_assignee(login) == expected


def test_copilot_assignees_filters_only_copilot() -> None:
    assert copilot_assignees(["copilot-swe-agent[bot]", "randrescastaneda"]) == ["copilot-swe-agent[bot]"]
    assert copilot_assignees(["randrescastaneda"]) == []


# ---------------------------------------------------------------------------
# Contract is untrusted: injection / fence boundaries
# ---------------------------------------------------------------------------


def test_marker_and_feature_id_inside_code_fence_are_ignored() -> None:
    body = GOOD_BODY + (
        "\n## Notes\n\n```\n<!-- compound-gpid-tracked: fake-id -->\n"
        "**Feature ID:** `fake-id`\n```\n"
    )
    result = validate_contract(body)
    # The fenced fake marker/id must not be picked up; R001-R003 still pass.
    by_id = {rule.id: rule for rule in result}
    assert by_id["R001"].passed is True
    assert by_id["R002"].passed is True
    assert by_id["R003"].passed is True


def test_fenced_section_header_is_not_treated_as_a_section() -> None:
    body = GOOD_BODY + "\n## Notes\n\n```\n## Expected allowed paths\n- `evil`\n```\n"
    result = validate_contract(body)
    by_id = {rule.id: rule for rule in result}
    # The real Expected allowed paths section is still found and safe.
    assert by_id["R004"].passed is True
    assert by_id["R010"].passed is True
    assert by_id["R012"].passed is True


def test_bom_is_stripped() -> None:
    result = validate_contract("\ufeff" + GOOD_BODY)
    by_id = {rule.id: rule for rule in result}
    assert by_id["R001"].passed is True


def test_fixture_bodyfile_traversal_raises_config(tmp_path) -> None:
    fixture = tmp_path / "fixture.json"
    fixture.write_text(
        json.dumps({
            "issue": {"number": 7, "body": ""},
            "bodyFile": "../../../etc/passwd",
        }),
        encoding="utf-8",
    )
    with pytest.raises(ConfigError, match="escapes"):
        FixtureClient(str(fixture))


def test_fixture_bodyfile_absolute_path_raises_config(tmp_path) -> None:
    fixture = tmp_path / "fixture.json"
    fixture.write_text(
        json.dumps({
            "issue": {"number": 7, "body": ""},
            "bodyFile": "/etc/passwd",
        }),
        encoding="utf-8",
    )
    with pytest.raises(ConfigError, match="escapes"):
        FixtureClient(str(fixture))


def test_fixture_bodyfile_valid_in_directory(tmp_path) -> None:
    body_file = tmp_path / "body.md"
    body_file.write_text("hello", encoding="utf-8")
    fixture = tmp_path / "fixture.json"
    fixture.write_text(
        json.dumps({
            "issue": {"number": 7, "body": ""},
            "bodyFile": "body.md",
        }),
        encoding="utf-8",
    )
    client = FixtureClient(str(fixture))
    assert client.get_issue(7).body == "hello"


def test_graphql_rate_limit_raises_api() -> None:
    from issues.gh_process import _classify_graphql_errors
    with pytest.raises(ApiError, match="transient"):
        _classify_graphql_errors([{"message": "API rate limit exceeded"}])


def test_graphql_timeout_raises_api() -> None:
    from issues.gh_process import _classify_graphql_errors
    with pytest.raises(ApiError, match="transient"):
        _classify_graphql_errors([{"message": "timeout"}])


def test_graphql_server_error_raises_api() -> None:
    from issues.gh_process import _classify_graphql_errors
    with pytest.raises(ApiError, match="server error"):
        _classify_graphql_errors([{"message": "Internal error occurred"}])


def test_graphql_config_error_preserved() -> None:
    from issues.gh_process import _classify_graphql_errors
    with pytest.raises(ConfigError, match="GraphQL error"):
        _classify_graphql_errors([{"message": "Field 'x' missing"}])


def test_graphql_none_errors_noop() -> None:
    from issues.gh_process import _classify_graphql_errors
    _classify_graphql_errors(None)


def test_project_status_pagination_fail_closed() -> None:
    runner = RecordingRunner(
        issue_json={"number": 1, "title": "t", "body": "", "state": "OPEN",
                    "assignees": [], "labels": []},
        pr_json=[],
        graphql_json={"data": {"repository": {"issue": {"projectItems": {
            "nodes": [{"project": {"title": "Other"}, "fieldValueByName": {"name": "x"}}],
            "pageInfo": {"hasNextPage": True},
        }}}}},
        repo_json={"nameWithOwner": "GPID-WB/compound-gpid"},
    )
    client = GhCliClient(runner=runner)
    with pytest.raises(ApiError, match="truncated"):
        client.get_project_status(1)


def test_project_status_target_found_on_page() -> None:
    runner = RecordingRunner(
        issue_json={"number": 1, "title": "t", "body": "", "state": "OPEN",
                    "assignees": [], "labels": []},
        pr_json=[],
        graphql_json={"data": {"repository": {"issue": {"projectItems": {
            "nodes": [
                {"project": {"title": "CompoundGPID-progress"},
                 "fieldValueByName": {"name": "Ready"}},
            ],
            "pageInfo": {"hasNextPage": True},
        }}}}},
        repo_json={"nameWithOwner": "GPID-WB/compound-gpid"},
    )
    client = GhCliClient(runner=runner)
    assert client.get_project_status(1) == "Ready"


def test_r019_detail_conditional_ready() -> None:
    result = validate_readiness(9001, FakeClient())
    by_id = {rule.id: rule for rule in result.rules}
    assert by_id["R019"].passed is True
    assert by_id["R019"].detail == "Project Status is 'Ready'"


def test_r019_detail_conditional_not_ready() -> None:
    result = validate_readiness(9001, FakeClient(status="Backlog"))
    by_id = {rule.id: rule for rule in result.rules}
    assert by_id["R019"].passed is False
    assert "expected" in by_id["R019"].detail


def test_result_to_dict_has_stable_keys() -> None:
    result = validate_readiness(9001, FakeClient())
    payload = result_to_dict(result)
    expected_keys = {
        "issue", "ready", "dryRun", "exitCode", "exitReason", "summary",
        "rules", "failedRules", "state", "errors",
    }
    assert set(payload) == expected_keys
    assert {rule["id"] for rule in payload["rules"]} == {
        f"R{n:03d}" for n in range(1, 22)
    }
