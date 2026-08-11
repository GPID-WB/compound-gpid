"""Controlled single-issue Copilot dispatcher orchestration (Stage 3).

This module implements the bounded Stage 3 dispatcher: a manually triggered,
single-issue assignment pipeline that reuses the Stage 2 readiness validator
(``issues.orchestration.validate_readiness``) without reproducing its parsing
or validation rules.

Guarantees enforced here:

- A dry run is a true zero-mutation path (no assign, Project update, comment,
  label, or any other GitHub mutation).
- Before any non-dry-run mutation: readiness is validated, duplicate and
  idempotency checks are performed, then readiness is revalidated immediately
  before assignment. The run fails closed if either validation fails or the
  GitHub state changed between the two validations.
- Mutation order is fixed: assign only ``copilot-swe-agent[bot]``; only after a
  successful assignment is the issue Project ``Status`` changed to
  ``In progress``; then an audit comment describing the result is added.
- ``In progress`` is never set before a successful assignment.
- If assignment succeeds but the Project update fails, the dispatcher does not
  unassign Copilot automatically, does not speculate about rollback, leaves an
  observable audit/failure comment, exits non-zero, and reports the manual
  recovery procedure.
- A repeat dispatch for an already-assigned issue or an existing implementation
  PR is an idempotent no-op with a clear explanation.

Responsibility split (mirrors the readiness modules with an acyclic import
graph): contract/constants live in :mod:`issues.dispatch_contract`; rendering
in :mod:`issues.dispatch_render`; the CLI in :mod:`issues.dispatch_cli`;
process/temp-file helpers in :mod:`issues.dispatch_util`; Project-v2 GraphQL in
:mod:`issues.dispatch_project`; the mutation client in
:mod:`issues.dispatch_client`. This module owns orchestration and re-exports the
public names so existing imports (``scripts/issue_dispatch.py``, tests, the
workflow) keep working unchanged.
"""
from __future__ import annotations

from typing import Optional

from .contract import (
    ApiError,
    ConfigError,
    EXIT_API,
    EXIT_CONFIG,
    EXIT_NOT_READY,
    EXIT_READY,
)
from .dispatch_contract import (
    COPILOT_ASSIGN_LOGIN,
    DispatchResult,
    EXIT_ASSIGN_FAILED,
    EXIT_PROJECT_UPDATE_FAILED,
    EXIT_RECHECK_FAILED,
    IN_PROGRESS_STATUS,
)
from .dispatch_client import DispatchMutator
from .orchestration import validate_readiness


def _state_failed_reason(state: dict) -> Optional[str]:
    """Return the idempotent no-op reason when the state is already dispatched.

    Args:
        state: The readiness result ``state`` dictionary.

    Returns:
        A reason string, or ``None`` when the issue is not already handled.
    """
    if state.get("copilotAssigned"):
        return "Copilot is already assigned"
    open_prs = state.get("openClosingPRs") or []
    if open_prs:
        numbers = ", ".join(f"#{pr['number']}" for pr in open_prs)
        return f"an existing open implementation PR ({numbers}) closes this issue"
    return None


def _try_comment(
    mutator: DispatchMutator,
    issue_number: int,
    body: str,
    log: list,
    messages: list,
    label: str,
) -> None:
    """Write one audit comment, recording success or failure in the log.

    Args:
        mutator: Mutation client whose ``comment`` is invoked.
        issue_number: Issue number to comment on.
        body: Comment body text.
        log: Ordered mutation log to append ``comment:<label>`` or
            ``comment:failed``.
        messages: Human-readable messages to extend on failure.

    Raises:
        ApiError: When the comment fails with an API/network error.
        ConfigError: When the comment fails due to a configuration error.
    """
    try:
        mutator.comment(issue_number, body)
        log.append(f"comment:{label}")
    except (ApiError, ConfigError) as error:
        log.append("comment:failed")
        messages.append(f"could not write {label} audit comment: {error}")


def run_dispatch(
    issue_number: int,
    read_client,
    mutator: DispatchMutator,
    *,
    dry_run: bool = True,
) -> DispatchResult:
    """Run the bounded single-issue dispatch sequence.

    Args:
        issue_number: Issue number to dispatch.
        read_client: Read-only client implementing the readiness interface
            (``get_issue``, ``get_open_closing_prs``, ``get_project_status``).
        mutator: Mutation client exposing ``assign``, ``set_project_status``,
            and ``comment`` (see ``DispatchMutator``).
        dry_run: When true, validate and report only; never call a mutation.

    Returns:
        A :class:`DispatchResult` describing the outcome, exit code, and the
        ordered mutation log.

    Example:
        ``result = run_dispatch(127, client, mutator, dry_run=True)`` performs
        a zero-mutation dry run.
    """
    log: list = []
    messages: list = []

    if issue_number < 1:
        messages.append(f"invalid issue number {issue_number}; must be positive")
        return DispatchResult(
            None, "config-error", EXIT_CONFIG, log, messages, dry_run
        )

    first = validate_readiness(issue_number, read_client, dry_run=True)
    if first.exit_code in (EXIT_CONFIG, EXIT_API):
        messages.extend(error["message"] for error in first.errors)
        return DispatchResult(
            issue_number,
            "config-error" if first.exit_code == EXIT_CONFIG else "api-error",
            first.exit_code,
            log,
            messages,
            dry_run,
        )

    if not first.ready:
        reason = _state_failed_reason(first.state or {})
        if reason is not None:
            messages.append(
                f"Idempotent no-op: {reason}. No new assignment performed."
            )
            if not dry_run:
                _try_comment(
                    mutator,
                    issue_number,
                    f"Dispatch no-op (idempotent): {reason} "
                    f"({COPILOT_ASSIGN_LOGIN}). No new assignment performed.",
                    log,
                    messages,
                    "idempotent-noop",
                )
            return DispatchResult(
                issue_number, "idempotent-noop", EXIT_READY, log, messages, dry_run
            )
        messages.append("Readiness validation failed; no dispatch performed.")
        messages.extend(f"  {rule.id}  {rule.name}  - {rule.detail}"
                        for rule in first.rules if not rule.passed)
        return DispatchResult(
            issue_number, "not-ready", EXIT_NOT_READY, log, messages, dry_run
        )

    if dry_run:
        messages.append("READY: dry-run only, zero mutations performed.")
        return DispatchResult(issue_number, "dry-run", EXIT_READY, log, messages, True)

    # Revalidate immediately before assignment so a state change between the
    # initial validation and the assignment fails closed.
    second = validate_readiness(issue_number, read_client, dry_run=True)
    if second.exit_code in (EXIT_CONFIG, EXIT_API):
        messages.extend(error["message"] for error in second.errors)
        return DispatchResult(
            issue_number,
            "config-error" if second.exit_code == EXIT_CONFIG else "api-error",
            second.exit_code,
            log,
            messages,
            dry_run,
        )
    if not second.ready:
        messages.append(
            "Readiness changed between validation and assignment; failing "
            "closed. No assignment and no Project Status change performed."
        )
        return DispatchResult(
            issue_number, "state-changed", EXIT_RECHECK_FAILED, log, messages, dry_run
        )

    try:
        mutator.assign(issue_number, COPILOT_ASSIGN_LOGIN)
        log.append(f"assign:{COPILOT_ASSIGN_LOGIN}")
    except (ApiError, ConfigError) as error:
        log.append("assign:failed")
        _try_comment(
            mutator,
            issue_number,
            f"Dispatch failed: assigning {COPILOT_ASSIGN_LOGIN} errored: "
            f"{error}. The issue remains Ready; no Project Status change "
            "was made.",
            log,
            messages,
            "assign-failed",
        )
        messages.append(f"Assignment failed: {error}")
        return DispatchResult(
            issue_number, "assign-failed", EXIT_ASSIGN_FAILED, log, messages, dry_run
        )

    try:
        mutator.set_project_status(issue_number, IN_PROGRESS_STATUS)
        log.append(f"project:{IN_PROGRESS_STATUS}")
    except (ApiError, ConfigError) as error:
        log.append("project:failed")
        recovery = (
            "Manual recovery: do NOT unassign Copilot. Inspect the PROJECT_SYNC "
            "token/scope and Project item, then set the issue Project Status to "
            "'In progress' manually or re-run dispatch after correcting the "
            "credential; do not reassign while Copilot remains assigned."
        )
        _try_comment(
            mutator,
            issue_number,
            f"Assignment succeeded but Project Status update to "
            f"{IN_PROGRESS_STATUS!r} failed: {error}. {COPILOT_ASSIGN_LOGIN} "
            "remains assigned. " + recovery,
            log,
            messages,
            "project-failed",
        )
        messages.append(f"Project Status update failed: {error}")
        messages.append(recovery)
        return DispatchResult(
            issue_number,
            "project-update-failed",
            EXIT_PROJECT_UPDATE_FAILED,
            log,
            messages,
            dry_run,
        )

    _try_comment(
        mutator,
        issue_number,
        f"Dispatched to {COPILOT_ASSIGN_LOGIN}; issue Project Status set "
        f"to {IN_PROGRESS_STATUS!r}.",
        log,
        messages,
        "dispatched",
    )
    messages.append(
        f"Dispatched to {COPILOT_ASSIGN_LOGIN}; Project Status set to "
        f"{IN_PROGRESS_STATUS!r}."
    )
    return DispatchResult(
        issue_number, "dispatched", EXIT_READY, log, messages, dry_run
    )


# Facade re-exports so `from issues.dispatch import main, build_parser,
# render_json, ...` keep working for the CLI shim, tests, and the workflow.
from .dispatch_cli import _emit, build_parser, main  # noqa: E402
from .dispatch_render import render_human, render_json, result_to_dict  # noqa: E402
