"""Complete read-only validation over shared lifecycle services."""
from __future__ import annotations

from typing import Any, Mapping

from skill_management import contracts
from skill_management.operations._common import usage_failure
from skill_management.planning import OperationOutcome
from skill_management.services import validation


def handle(*, context: Any, request: Mapping[str, Any]) -> OperationOutcome:
    """Validate one known skill or all current and tombstoned skill records."""
    arguments = request["arguments"]
    positionals = arguments.get("positionals", [])
    if bool(arguments.get("all")) == bool(positionals):
        return usage_failure(
            "arguments.validation-scope",
            "Specify exactly one skill identifier or --all.",
            "Use `validate <id>` or `validate --all`.",
            data={
                "manifestHealth": "invalid",
                "validatedIds": [],
                "descriptorOperations": [],
            },
            manifest_health="invalid",
        )
    identifier = str(positionals[0]) if positionals else None
    try:
        report = validation.validate_skills(
            context.project_root,
            context.source_root,
            identifier=identifier,
        )
    except validation.UnknownSkillError as error:
        return usage_failure(
            "skill.unknown",
            str(error),
            "Run `find` to list current and deprecated skill identifiers.",
            path="/arguments/positionals/0",
            data={
                "manifestHealth": "invalid",
                "validatedIds": [],
                "descriptorOperations": [],
            },
            manifest_health="invalid",
        )
    exit_code = (
        contracts.EXIT_CONTRACT
        if any(item.severity == "error" for item in report.findings)
        else contracts.EXIT_SUCCESS
    )
    return OperationOutcome(
        data={
            "manifestHealth": report.manifest_health,
            "validatedIds": list(report.validated_ids),
            "descriptorOperations": list(report.descriptor_operations),
        },
        findings=report.findings,
        manifest_health=report.manifest_health,
        exit_code=exit_code,
    )
