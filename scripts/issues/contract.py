"""Readiness contract: types, constants, parsing, and path validation.

This module is the public compatibility surface.  Implementation lives in
``contract_types`` (data classes and exit codes) and ``contract_parsing``
(fence-aware Markdown helpers and path validation).  All existing imports from
``issues.contract`` continue to work unchanged.
"""
from __future__ import annotations

from .contract_parsing import (  # noqa: F401
    CHECKBOX_RE,
    CLOSE_KEYWORDS,
    CODE_SPAN_RE,
    COPILOT_LOGINS,
    FEATURE_ID_FORMAT_RE,
    FEATURE_ID_LINE_RE,
    LIST_ITEM_RE,
    MARKER_RE,
    REQUIRED_SECTIONS,
    RISK_CLASSES,
    SECTION_HEADER_RE,
    UNCHECKED_BOX_RE,
    _brackets_unbalanced,
    _is_overbroad_allowed_path,
    _iter_fence_state,
    _non_fence_lines,
    _section_detail,
    _section_nonempty,
    copilot_assignees,
    find_feature_id,
    find_marker,
    is_copilot_assignee,
    parse_sections,
    pr_closes_issue,
    strip_bom,
    validate_path_entry,
)
from .contract_types import (  # noqa: F401
    EXIT_API,
    EXIT_CONFIG,
    EXIT_NOT_READY,
    EXIT_READY,
    EXIT_REASONS,
    ApiError,
    ConfigError,
    ReadinessError,
    ReadinessResult,
    RuleResult,
)
