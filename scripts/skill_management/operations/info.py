"""Read-only exact skill inspection operation."""
from __future__ import annotations

from typing import Any, Mapping

from skill_management.operations._common import catalog_failure, usage_failure
from skill_management.planning import OperationOutcome
from skill_management.services import catalog


def handle(*, context: Any, request: Mapping[str, Any]) -> OperationOutcome:
    """Inspect one canonical skill by immutable identifier.

    Args:
        context: Resolved skill-management context.
        request: Validated common request envelope.

    Returns:
        Full catalog record outcome.

    Example:
        ``handle(context=context, request=request)``
    """
    identifier = request["arguments"]["positionals"][0]
    try:
        resolution = catalog.resolve_catalog(context)
        rows = catalog.filter_catalog_rows(
            resolution.rows, id_query=identifier, exact_id=True
        )
    except catalog.CatalogError as error:
        return catalog_failure(
            error,
            data={
                "manifestHealth": error.manifest_health,
                "prospective": error.manifest_health in ("missing", "stale"),
                "remediation": error.remediation,
            },
        )
    base_data = {
        "manifestHealth": resolution.manifest_health,
        "prospective": resolution.prospective,
        "remediation": resolution.remediation,
    }
    if not rows:
        return usage_failure(
            "skill.unknown",
            f"Unknown canonical skill identifier: {identifier!r}.",
            "Run `find` to list canonical skill identifiers.",
            path="/arguments/positionals/0",
            data=base_data,
            manifest_health=resolution.manifest_health,
        )
    base_data["record"] = catalog.public_record(rows[0], full=True)
    return OperationOutcome(
        data=base_data,
        manifest_health=resolution.manifest_health,
    )
