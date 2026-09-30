"""Successor-bound skill deprecation through common plan/apply."""
from __future__ import annotations

from typing import Any, Dict, Mapping

from skill_management import contracts, planning
from skill_management.operations import _maintenance
from skill_management.services import lifecycle, provenance, registry


def _data(
    status: str,
    identifier: str = "",
    successor_id: str = "",
    origin: str = "",
    active_warning: bool = False,
    record_digest: str = "",
) -> Dict[str, Any]:
    return {
        "status": status,
        "skillId": identifier,
        "successorId": successor_id,
        "origin": origin,
        "activeWarning": active_warning,
        "deprecatedRecordDigest": record_digest,
    }


def handle(*, context: Any, request: Mapping[str, Any]) -> planning.OperationOutcome:
    """Plan or apply one immutable same-origin skill deprecation."""
    try:
        arguments = request.get("arguments", {})
        positionals = arguments.get("positionals", [])
        if not isinstance(positionals, list) or len(positionals) != 2:
            raise ValueError("deprecate requires <skill-id> <successor-id>")
        identifier = str(positionals[0])
        successor_id = str(positionals[1])
        desired = lifecycle.plan_deprecation(
            context.project_root,
            context.source_root,
            identifier,
            successor_id,
            str(arguments.get("approver", "")),
            str(arguments.get("review_reference", "")),
            role=context.role,
        )
        data = _data(
            "planned" if request["phase"] == "plan" else "committed",
            identifier,
            successor_id,
            desired.origin,
            desired.active_warning,
            desired.deprecated_record_digest,
        )
        warning = ()
        if desired.active_warning:
            warning = (
                contracts.ContractFinding(
                    "/lifecycle",
                    "deprecate.active-migration",
                    "warning",
                    "The deprecated skill remains active during migration.",
                    "Migrate active references, then deactivate the skill before removal.",
                ),
            )
        if request["phase"] == "plan":
            stored = planning.store_plan(context.project_root, desired.plan)
            return planning.OperationOutcome(
                changed=True,
                data=data,
                actions=tuple(
                    item.to_public_dict() for item in desired.plan.actions
                ),
                findings=warning,
                plan_digest=stored.digest,
            )
        result = planning.apply_plan(
            context.project_root, desired.plan, str(request["planDigest"])
        )
        data["status"] = result.state
        return planning.OperationOutcome(
            changed=True,
            data=data,
            actions=tuple(item.to_public_dict() for item in desired.plan.actions),
            findings=warning,
        )
    except (
        planning.PlanRoleError,
        planning.StalePlanError,
        planning.ConcurrentMutationError,
        planning.PlanReplayError,
    ) as error:
        return _maintenance.failure(
            "deprecate",
            error,
            exit_code=_maintenance.transaction_exit(error),
            data=_data("blocked"),
        )
    except (
        ValueError,
        OSError,
        lifecycle.LifecyclePlanningError,
        provenance.ProvenanceValidationError,
        registry.RegistryValidationError,
    ) as error:
        exit_code = (
            contracts.EXIT_ROLE_CONTEXT
            if "maintainer context" in str(error).casefold()
            else contracts.EXIT_LIFECYCLE_CONFLICT
        )
        return _maintenance.failure(
            "deprecate", error, exit_code=exit_code, data=_data("blocked")
        )
