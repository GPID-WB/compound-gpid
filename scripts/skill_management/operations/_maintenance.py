"""Shared Phase 5 operation parsing and stable failure helpers."""
from __future__ import annotations

import json
from typing import Any, Dict, Mapping, Sequence, Tuple

from skill_management import contracts, planning
from skill_management.services import maintenance


SUITES = ("cg", "cr")
PLATFORMS = ("copilot", "claude-code", "codex", "opencode", "kilo")
ACTIVATION_COSTS = ("low", "medium", "high")


def comma_values(
    value: Any,
    label: str,
    *,
    allowed: Sequence[str] = (),
    required: bool = True,
) -> Tuple[str, ...]:
    """Parse one deterministic comma-separated argument."""
    items = tuple(item.strip() for item in str(value or "").split(",") if item.strip())
    if required and not items:
        raise ValueError(f"{label} must not be empty")
    if len(set(items)) != len(items):
        raise ValueError(f"{label} must contain unique values")
    if allowed and any(item not in allowed for item in items):
        raise ValueError(f"{label} must be a subset of {', '.join(allowed)}")
    return tuple(item for item in allowed if item in items) if allowed else items


def selectors(value: Any) -> Tuple[Mapping[str, str], ...]:
    """Parse strict selector JSON from one CLI-safe string argument."""
    try:
        parsed = json.loads(str(value))
    except json.JSONDecodeError as error:
        raise ValueError("selectors must be one JSON array") from error
    if not isinstance(parsed, list):
        raise ValueError("selectors must be one JSON array")
    result = []
    for item in parsed:
        if not isinstance(item, dict) or set(item) != {"field", "operator", "value"}:
            raise ValueError(
                "Each selector must contain only field, operator, and value"
            )
        if any(not isinstance(item[key], str) or not item[key] for key in item):
            raise ValueError("Selector fields must be non-empty strings")
        result.append(dict(item))
    return tuple(result)


def resource_classes(value: Any) -> Dict[str, str]:
    """Parse exact resource-to-approved-class JSON metadata."""
    if value in (None, ""):
        return {}
    try:
        parsed = json.loads(str(value))
    except json.JSONDecodeError as error:
        raise ValueError("resource-classes must be one JSON object") from error
    if not isinstance(parsed, dict) or any(
        not isinstance(path, str)
        or not path
        or not isinstance(class_name, str)
        or not class_name
        for path, class_name in parsed.items()
    ):
        raise ValueError("resource-classes must map paths to non-empty class names")
    return dict(parsed)


def capability_metadata(arguments: Mapping[str, Any]) -> maintenance.CapabilityMetadata:
    """Build complete explicit canonical capability metadata from arguments."""
    activation_cost = str(arguments.get("activation_cost", ""))
    if activation_cost not in ACTIVATION_COSTS:
        raise ValueError(
            "activation-cost must be one of " + ", ".join(ACTIVATION_COSTS)
        )
    return maintenance.CapabilityMetadata(
        str(arguments.get("capability", "")),
        str(arguments.get("owner", "")),
        comma_values(arguments.get("suites"), "suites", allowed=SUITES),
        comma_values(arguments.get("platforms"), "platforms", allowed=PLATFORMS),
        activation_cost,
        comma_values(arguments.get("triggers"), "triggers"),
        selectors(arguments.get("selectors", "[]")),
    )


def failure(
    operation: str,
    error: Exception,
    *,
    exit_code: int = contracts.EXIT_CONTRACT,
    data: Mapping[str, Any],
) -> planning.OperationOutcome:
    """Convert one expected Phase 5 failure to a stable operation result."""
    return planning.OperationOutcome(
        data=dict(data),
        findings=(
            contracts.ContractFinding(
                "/arguments",
                f"{operation}.invalid",
                "error",
                str(error),
                "Use complete immutable metadata and create a new reviewed plan.",
            ),
        ),
        exit_code=exit_code,
    )


def transaction_exit(error: Exception) -> int:
    """Map common transaction exceptions to their reserved stable exit code."""
    if isinstance(error, planning.PlanRoleError):
        return contracts.EXIT_ROLE_CONTEXT
    if isinstance(error, (planning.StalePlanError, planning.ConcurrentMutationError)):
        return contracts.EXIT_STALE_PLAN
    if isinstance(error, planning.PlanReplayError):
        return contracts.EXIT_LIFECYCLE_CONFLICT
    return contracts.EXIT_CONTRACT
