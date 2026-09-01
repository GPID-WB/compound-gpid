"""Read-only provenance and reference audit over complete validation services."""
from __future__ import annotations

from typing import Any, Mapping

from skill_management import contracts
from skill_management.operations._common import usage_failure
from skill_management.planning import OperationOutcome
from skill_management.services import references, validation


def handle(*, context: Any, request: Mapping[str, Any]) -> OperationOutcome:
    """Audit lifecycle validity and classified references without mutation."""
    arguments = request.get("arguments", {})
    positionals = arguments.get("positionals", [])
    if not isinstance(positionals, list) or len(positionals) > 1:
        return usage_failure(
            "arguments.audit-scope",
            "Audit accepts at most one exact skill identifier.",
            "Use `audit`, `audit <id>`, or one documented audit filter.",
            data={
                "manifestHealth": "invalid",
                "auditedIds": [],
                "filters": [],
                "referenceDigest": references.empty_reference_report().digest,
                "references": [],
            },
            manifest_health="invalid",
        )
    provenance_selected = bool(arguments.get("provenance"))
    references_selected = bool(arguments.get("references"))
    if not provenance_selected and not references_selected:
        provenance_selected = True
        references_selected = True
    filters = []
    if provenance_selected:
        filters.append("provenance")
    if references_selected:
        filters.append("references")
    identifier = str(positionals[0]) if positionals else None
    try:
        report = validation.validate_skills(
            context.project_root,
            context.source_root,
            identifier=identifier,
            include_provenance=provenance_selected,
            include_references=references_selected,
        )
    except validation.UnknownSkillError as error:
        return usage_failure(
            "skill.unknown",
            str(error),
            "Run `find` to list current and deprecated skill identifiers.",
            path="/arguments/positionals/0",
            data={
                "manifestHealth": "invalid",
                "auditedIds": [],
                "filters": filters,
                "referenceDigest": references.empty_reference_report().digest,
                "references": [],
            },
            manifest_health="invalid",
        )
    reference_rows = (
        [item.to_dict() for item in report.reference_report.references]
        if references_selected
        else []
    )
    exit_code = (
        contracts.EXIT_CONTRACT
        if any(item.severity == "error" for item in report.findings)
        else contracts.EXIT_SUCCESS
    )
    return OperationOutcome(
        data={
            "manifestHealth": report.manifest_health,
            "auditedIds": list(report.validated_ids),
            "filters": filters,
            "referenceDigest": report.reference_report.digest,
            "references": reference_rows,
        },
        findings=report.findings,
        manifest_health=report.manifest_health,
        exit_code=exit_code,
    )
