"""Descriptor-derived read-only help operation."""
from __future__ import annotations

from typing import Any, Mapping

from skill_management import contracts
from skill_management.operations._common import catalog_failure, usage_failure
from skill_management.planning import OperationOutcome
from skill_management.services import catalog


def handle(*, context: Any, request: Mapping[str, Any]) -> OperationOutcome:
    """List complete operations or inspect one operation descriptor.

    Args:
        context: Resolved skill-management context.
        request: Validated common request envelope.

    Returns:
        Descriptor-derived help outcome in lexical order.

    Example:
        ``handle(context=context, request=request)``
    """
    try:
        status = catalog.inspect_manifest(context.project_root, context.source_root)
    except catalog.CatalogError as error:
        return catalog_failure(
            error,
            data={
                "manifestHealth": error.manifest_health,
                "prospective": error.manifest_health in ("missing", "stale"),
                "remediation": error.remediation,
                "operations": [],
            },
        )
    records, findings = contracts.discover_operation_descriptors(context.source_root)
    data = {
        "manifestHealth": status.health,
        "prospective": status.health != "fresh",
        "remediation": status.remediation,
        "operations": [
            {
                "operation": record.operation,
                "roles": list(record.descriptor["roles"]),
                "phases": list(record.descriptor["phases"]),
                "workflow": record.descriptor["workflow"],
                "documentation": record.descriptor["documentation"],
            }
            for record in records
        ],
    }
    if findings:
        return OperationOutcome(
            data=data,
            findings=findings,
            manifest_health=status.health,
            exit_code=contracts.EXIT_CONTRACT,
        )
    positionals = request["arguments"].get("positionals", [])
    if positionals:
        operation = positionals[0]
        data["operations"] = [
            row for row in data["operations"] if row["operation"] == operation
        ]
        if not data["operations"]:
            return usage_failure(
                "operation.unknown",
                f"Unknown operation: {operation!r}.",
                "Run `help` without an operation to list complete operations.",
                path="/arguments/positionals/0",
                data=data,
                manifest_health=status.health,
            )
    return OperationOutcome(data=data, manifest_health=status.health)
