"""Exit codes, data types, and error classes for the readiness validator."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


EXIT_READY = 0
EXIT_NOT_READY = 2
EXIT_CONFIG = 3
EXIT_API = 4

EXIT_REASONS = {
    EXIT_READY: "ready",
    EXIT_NOT_READY: "validation_failure",
    EXIT_CONFIG: "config_error",
    EXIT_API: "api_error",
}


class ReadinessError(Exception):
    """Base class for readiness validator failures."""


class ConfigError(ReadinessError):
    """Local configuration failure such as bad arguments or missing ``gh``."""


class ApiError(ReadinessError):
    """GitHub API, network, truncation, or malformed-response failure."""


@dataclass
class RuleResult:
    """Result for one stable readiness rule.

    Attributes:
        id: Stable rule identifier such as ``R001``.
        name: Human-readable rule name.
        passed: Whether the rule was satisfied.
        detail: Diagnostic detail string for JSON and human output.
    """

    id: str
    name: str
    passed: bool
    detail: str = ""


@dataclass
class ReadinessResult:
    """Complete validator result, including rules, state, and errors.

    Attributes:
        issue: Issue number, or ``None`` when validation failed early.
        ready: ``True`` only when every rule passed.
        exit_code: Documented exit code (0, 2, 3, or 4).
        exit_reason: Machine-readable exit reason string.
        rules: Ordered list of rule results.
        state: GitHub state snapshot emitted in JSON output.
        errors: Error entries for config/API failures.
        dry_run: Always ``True``; the validator never mutates.
    """

    issue: Optional[int]
    ready: bool
    exit_code: int
    exit_reason: str
    rules: list[RuleResult] = field(default_factory=list)
    state: dict = field(default_factory=dict)
    errors: list[dict] = field(default_factory=list)
    dry_run: bool = True
