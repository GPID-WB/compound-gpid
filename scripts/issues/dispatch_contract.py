"""Shared dispatch contract types and constants (leaf module, no imports)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .contract import EXIT_REASONS

# The exact Copilot coding-agent login. Anything else must never be assigned,
# enforced at the credential-holding boundary by the mutation client and used
# as the canonical identity by orchestration. Single source of truth.
COPILOT_ASSIGN_LOGIN = "copilot-swe-agent[bot]"

# The only Project Status value the dispatcher ever sets, shared by the
# orchestration and mutation modules (single source of truth).
IN_PROGRESS_STATUS = "In progress"

# Dispatcher exit codes extend the readiness contract (0/2/3/4).
EXIT_ASSIGN_FAILED = 5
EXIT_PROJECT_UPDATE_FAILED = 6
EXIT_RECHECK_FAILED = 7

EXIT_REASONS_DISPATCH = {
    **EXIT_REASONS,
    EXIT_ASSIGN_FAILED: "assign_failed",
    EXIT_PROJECT_UPDATE_FAILED: "project_update_failed",
    EXIT_RECHECK_FAILED: "state_changed_before_assignment",
}


@dataclass
class DispatchResult:
    """Result of one dispatch attempt with an ordered mutation log.

    Attributes:
        issue: Issue number, or ``None`` on early failure.
        outcome: Stable outcome string such as ``dry-run``, ``dispatched``,
            ``idempotent-noop``, ``not-ready``, ``state-changed``,
            ``assign-failed``, or ``project-update-failed``.
        exit_code: Documented dispatcher exit code.
        mutation_log: Ordered labels of every attempted mutation, used for
            audit and for verifying mutation ordering.
        messages: Human-readable explanation lines.
        dry_run: Whether this was a dry run (true means zero mutations).
    """

    issue: Optional[int]
    outcome: str
    exit_code: int
    mutation_log: list
    messages: list
    dry_run: bool = True
