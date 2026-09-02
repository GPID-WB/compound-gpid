"""Read-only ``find`` operation over the canonical catalog service."""
from __future__ import annotations

from typing import Any, Mapping

from skill_management.operations._common import catalog_failure, usage_failure
from skill_management.planning import OperationOutcome
from skill_management.services import catalog


def handle(*, context: Any, request: Mapping[str, Any]) -> OperationOutcome:
    """Find canonical skills with composable metadata filters.

    Args:
        context: Resolved skill-management context.
        request: Validated common request envelope.

    Returns:
        Read-only catalog outcome.

    Example:
        ``handle(context=context, request=request)``
    """
    arguments = request["arguments"]
    try:
        resolution = catalog.resolve_catalog(context)
        available = None
        if arguments.get("available"):
            available = True
        elif arguments.get("unavailable"):
            available = False
        if arguments.get("available") and arguments.get("unavailable"):
            return usage_failure(
                "arguments.availability-conflict",
                "--available and --unavailable cannot be used together.",
                "Select at most one availability filter.",
                data={
                    "manifestHealth": resolution.manifest_health,
                    "prospective": resolution.prospective,
                    "remediation": resolution.remediation,
                    "records": [],
                },
                manifest_health=resolution.manifest_health,
            )
        rows = catalog.filter_catalog_rows(
            resolution.rows,
            id_query=arguments.get("id"),
            exact_id=bool(arguments.get("exact")),
            capability=arguments.get("capability"),
            suite=arguments.get("suite"),
            platform=arguments.get("platform"),
            available=available,
            cost=arguments.get("cost"),
            owner=arguments.get("owner"),
            provenance=arguments.get("provenance"),
        )
    except catalog.CatalogError as error:
        return catalog_failure(
            error,
            data={
                "manifestHealth": error.manifest_health,
                "prospective": error.manifest_health in ("missing", "stale"),
                "remediation": error.remediation,
                "records": [],
            },
        )
    data = {
        "manifestHealth": resolution.manifest_health,
        "prospective": resolution.prospective,
        "remediation": resolution.remediation,
        "records": [
            catalog.public_record(row, full=bool(arguments.get("full")))
            for row in rows
        ],
    }
    if arguments.get("exact") and arguments.get("id") and not rows:
        return usage_failure(
            "skill.unknown",
            f"Unknown canonical skill identifier: {arguments['id']!r}.",
            "Run `find` without --exact to search canonical identifiers and purposes.",
            path="/arguments/id",
            data=data,
            manifest_health=resolution.manifest_health,
        )
    return OperationOutcome(
        data=data,
        manifest_health=resolution.manifest_health,
    )
