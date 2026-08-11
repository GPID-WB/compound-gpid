"""Readiness orchestration over a client and the pure contract rules."""
from __future__ import annotations

from .clients import IssueRecord, PRRecord
from .contract import (
    ApiError,
    ConfigError,
    EXIT_API,
    EXIT_CONFIG,
    EXIT_NOT_READY,
    EXIT_READY,
    EXIT_REASONS,
    ReadinessResult,
    RuleResult,
    copilot_assignees,
)
from .contract_rules import validate_contract


READY_STATUS = "Ready"


def _error_result(
    issue_number: int | None,
    exit_code: int,
    message: str,
    dry_run: bool,
) -> ReadinessResult:
    """Build a result for a validation run that could not complete."""
    return ReadinessResult(
        issue=issue_number,
        ready=False,
        exit_code=exit_code,
        exit_reason=EXIT_REASONS[exit_code],
        rules=[],
        state={},
        errors=[{"type": EXIT_REASONS[exit_code], "message": message}],
        dry_run=dry_run,
    )


def validate_readiness(
    issue_number: int,
    client,
    *,
    dry_run: bool = True,
) -> ReadinessResult:
    """Evaluate contract and live/fixture GitHub state without mutations.

    Args:
        issue_number: Issue number supplied to the client read methods.
        client: Object implementing ``get_issue``, ``get_open_closing_prs``,
            and ``get_project_status``.
        dry_run: Output flag retained for the CLI contract; validation is always
            read-only.

    Returns:
        A :class:`ReadinessResult`. Configuration and API failures are returned
        as exit-code 3 or 4 results rather than raised to the CLI.

    Example:
        ``result = validate_readiness(127, client)`` yields a result whose
        ``exit_code`` is one of the documented readiness exit codes.
    """
    try:
        issue: IssueRecord = client.get_issue(issue_number)
        prs: list[PRRecord] = client.get_open_closing_prs(issue_number)
        status = client.get_project_status(issue_number)
    except ConfigError as error:
        return _error_result(issue_number, EXIT_CONFIG, str(error), dry_run)
    except ApiError as error:
        return _error_result(issue_number, EXIT_API, str(error), dry_run)

    contract_rules = validate_contract(issue.body)
    assigned_copilot = copilot_assignees(issue.assignees)
    state_rules = [
        RuleResult(
            "R019", "project-status-ready", status == READY_STATUS,
            f"Project Status is {READY_STATUS!r}" if status == READY_STATUS
            else f"Project Status is {status!r}, expected {READY_STATUS!r}",
        ),
        RuleResult(
            "R020", "no-open-closing-pr", len(prs) == 0,
            f"{len(prs)} open PR(s) close this issue"
            + (f" (#{prs[0].number})" if prs else ""),
        ),
        RuleResult(
            "R021", "copilot-not-assigned", len(assigned_copilot) == 0,
            f"Copilot assignee(s): {assigned_copilot}"
            if assigned_copilot else "no Copilot assignee",
        ),
    ]
    rules = contract_rules + state_rules
    ready = all(rule.passed for rule in rules)
    exit_code = EXIT_READY if ready else EXIT_NOT_READY
    return ReadinessResult(
        issue=issue_number,
        ready=ready,
        exit_code=exit_code,
        exit_reason=EXIT_REASONS[exit_code],
        rules=rules,
        state={
            "issueState": issue.state,
            "projectStatus": status,
            "openClosingPRs": [{"number": pr.number, "url": pr.url} for pr in prs],
            "copilotAssigned": bool(assigned_copilot),
            "assignees": list(issue.assignees),
        },
        errors=[],
        dry_run=dry_run,
    )
