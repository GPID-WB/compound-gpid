"""Common read-operation outcome helpers with stable findings."""
from __future__ import annotations

from typing import Any, Mapping, Optional

from skill_management import contracts
from skill_management.planning import OperationOutcome
from skill_management.services import catalog


def catalog_failure(
    error: catalog.CatalogError,
    *,
    data: Optional[Mapping[str, Any]] = None,
) -> OperationOutcome:
    """Convert a catalog input failure to one stable contract result.

    Args:
        error: Catalog service failure.
        data: Operation-contract-compatible failure data.

    Returns:
        Failed read outcome with manifest health.

    Example:
        ``return catalog_failure(error)``
    """
    return OperationOutcome(
        data=dict(data or {}),
        findings=(
            contracts.ContractFinding(
                "/manifest",
                "catalog.invalid-input",
                "error",
                str(error),
                error.remediation,
            ),
        ),
        manifest_health=error.manifest_health,
        exit_code=contracts.EXIT_CONTRACT,
    )


def usage_failure(
    code: str,
    message: str,
    remediation: str,
    *,
    path: str = "/arguments",
    data: Optional[Mapping[str, Any]] = None,
    manifest_health: Optional[str] = None,
) -> OperationOutcome:
    """Return one stable usage failure from a focused operation.

    Args:
        code: Stable finding code.
        message: User-facing failure detail.
        remediation: Exact corrective action.
        path: Finding path.
        data: Contract-compatible operation data.
        manifest_health: Optional resolved health.

    Returns:
        Usage-failure outcome.

    Example:
        ``return usage_failure("skill.unknown", "Unknown.", "Use find.")``
    """
    return OperationOutcome(
        data=dict(data or {}),
        findings=(
            contracts.ContractFinding(
                path, code, "error", message, remediation
            ),
        ),
        manifest_health=manifest_health,
        exit_code=contracts.EXIT_USAGE,
    )
