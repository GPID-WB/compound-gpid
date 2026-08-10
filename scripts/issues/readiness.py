"""Compatibility facade for the modular readiness validator.

The implementation is divided by responsibility across ``contract``,
``contract_rules``, ``clients``, ``orchestration``, ``render``, and ``cli``.
This module intentionally re-exports the historical public and test-facing
symbols so existing imports and the ``scripts/issue_readiness.py`` entry point
continue to work unchanged.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Optional, Sequence, TextIO

# Keep the historical file directly executable as well as importable as
# ``issues.readiness``.
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    __package__ = "issues"

from .cli import (
    _ReadinessArgumentParser,
    _emit,
    build_parser,
    main as _cli_main,
)
from .clients import (
    GH_TIMEOUT_SECONDS,
    PR_LIST_LIMIT,
    PROJECT_TITLE,
    FixtureClient,
    GhCliClient,
    IssueRecord,
    PRRecord,
    _classify_gh_error,
    _default_run_gh,
)
from .contract import (
    CHECKBOX_RE,
    CLOSE_KEYWORDS,
    CODE_SPAN_RE,
    EXIT_API,
    EXIT_CONFIG,
    EXIT_NOT_READY,
    EXIT_READY,
    EXIT_REASONS,
    FEATURE_ID_FORMAT_RE,
    FEATURE_ID_LINE_RE,
    LIST_ITEM_RE,
    MARKER_RE,
    REQUIRED_SECTIONS,
    RISK_CLASSES,
    SECTION_HEADER_RE,
    UNCHECKED_BOX_RE,
    ApiError,
    ConfigError,
    ReadinessError,
    ReadinessResult,
    RuleResult,
    _is_overbroad_allowed_path,
    _iter_fence_state,
    _non_fence_lines,
    _section_detail,
    _section_nonempty,
    _brackets_unbalanced,
    copilot_assignees,
    find_feature_id,
    find_marker,
    is_copilot_assignee,
    parse_sections,
    pr_closes_issue,
    strip_bom,
    validate_path_entry,
)
from .contract_rules import (
    _extract_checkboxes,
    _extract_path_entries,
    _extract_risk_class,
    _has_blocking_dependency,
    _verification_commands_nonempty,
    validate_contract,
)
from .gh_client import _PROJECT_STATUS_QUERY
from .orchestration import READY_STATUS, _error_result, validate_readiness
from .render import render_human, render_json, result_to_dict


def main(
    argv: Optional[Sequence[str]] = None,
    *,
    client=None,
    out: TextIO = sys.stdout,
    err: TextIO = sys.stderr,
) -> int:
    """Run the compatibility CLI facade.

    Args:
        argv: Command arguments, defaulting to ``sys.argv[1:]``.
        client: Optional injected readiness client for tests or embedders.
        out: Stream receiving human or JSON output.
        err: Stream receiving parser usage errors.

    Returns:
        The documented readiness exit code: 0, 2, 3, or 4.

    Raises:
        SystemExit: When command-line arguments are missing, conflicting, or
            invalid.

    Example:
        ``main(["--issue", "127", "--dry-run"], client=client)`` performs a
        read-only validation through the historical import path.
    """
    return _cli_main(
        argv,
        client=client,
        out=out,
        err=err,
        fixture_client_cls=FixtureClient,
        gh_client_cls=GhCliClient,
        validate_fn=validate_readiness,
    )


__all__ = [
    "ApiError", "ConfigError", "ReadinessError", "RuleResult", "ReadinessResult",
    "IssueRecord", "PRRecord", "GhCliClient", "FixtureClient",
    "EXIT_READY", "EXIT_NOT_READY", "EXIT_CONFIG", "EXIT_API", "EXIT_REASONS",
    "READY_STATUS", "PROJECT_TITLE", "GH_TIMEOUT_SECONDS", "PR_LIST_LIMIT",
    "MARKER_RE", "FEATURE_ID_LINE_RE", "FEATURE_ID_FORMAT_RE", "RISK_CLASSES",
    "REQUIRED_SECTIONS", "SECTION_HEADER_RE", "CHECKBOX_RE", "UNCHECKED_BOX_RE",
    "LIST_ITEM_RE", "CODE_SPAN_RE", "CLOSE_KEYWORDS", "strip_bom",
    "parse_sections", "find_marker", "find_feature_id", "validate_path_entry",
    "pr_closes_issue", "is_copilot_assignee", "copilot_assignees",
    "validate_contract", "validate_readiness", "result_to_dict", "render_json",
    "render_human", "build_parser", "main",
]


if __name__ == "__main__":
    raise SystemExit(main())
