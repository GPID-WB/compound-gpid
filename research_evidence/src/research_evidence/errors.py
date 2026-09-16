"""Created 2026-08-12. Domain errors for the evidence workbench."""
from __future__ import annotations


class EvidenceWorkbenchError(Exception):
    """Base error for expected workbench failures.

    Args:
        message: Human-readable explanation of the failure.

    Returns:
        An exception instance suitable for explicit error handling.

    Example:
        ``raise EvidenceWorkbenchError("capability unavailable")``.
    """


class PathPolicyError(EvidenceWorkbenchError):
    """Signal a project-root, resource-root, or URL policy violation.

    Args:
        message: Human-readable explanation of the rejected path.

    Returns:
        An exception instance describing the path-policy failure.

    Example:
        ``raise PathPolicyError("URL resources are not allowed")``.
    """


class NetworkAccessDenied(EvidenceWorkbenchError):
    """Signal an outbound non-loopback network attempt.

    Args:
        message: Human-readable explanation of the denied network action.

    Returns:
        An exception instance describing the network-policy failure.

    Example:
        ``raise NetworkAccessDenied("outbound network is disabled")``.
    """


class InventoryValidationError(EvidenceWorkbenchError):
    """Signal incomplete or unsafe dependency activation metadata.

    Args:
        message: Human-readable explanation of the invalid inventory entry.

    Returns:
        An exception instance describing the inventory failure.

    Example:
        ``raise InventoryValidationError("missing caveat")``.
    """
