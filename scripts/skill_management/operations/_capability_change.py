"""Shared thin operation adapter for activate and deactivate."""
from __future__ import annotations

from typing import Any, Mapping

from skill_management import contracts, planning
from skill_management.services import runtime


def handle_change(
    *,
    context: Any,
    request: Mapping[str, Any],
    activate: bool,
) -> planning.OperationOutcome:
    """Route one capability edit through pure runtime planning and common apply."""
    arguments = request.get("arguments", {})
    positionals = arguments.get("positionals", [])
    capability = str(positionals[0]) if isinstance(positionals, list) and len(positionals) == 1 else ""
    operation = "activate" if activate else "deactivate"
    if not capability:
        return _failure(operation, "One capability identifier is required.", contracts.EXIT_USAGE)
    try:
        plan = runtime.plan_capability_change(
            context.project_root,
            context.source_root,
            capability,
            activate=activate,
            role=context.role,
        )
        if not plan.actions:
            return planning.OperationOutcome(
                changed=False,
                data={"status": "no-op", "capability": capability},
            )
        if request["phase"] == "plan":
            stored = planning.store_plan(context.project_root, plan)
            return planning.OperationOutcome(
                changed=True,
                data={"status": "planned", "capability": capability},
                actions=tuple(action.to_public_dict() for action in plan.actions),
                plan_digest=stored.digest,
            )
        result = planning.apply_plan(
            context.project_root, plan, str(request["planDigest"])
        )
        return planning.OperationOutcome(
            changed=True,
            data={"status": result.state, "capability": capability},
            actions=tuple(action.to_public_dict() for action in plan.actions),
        )
    except planning.StalePlanError as error:
        return _failure(operation, str(error), contracts.EXIT_STALE_PLAN)
    except planning.PlanRoleError as error:
        return _failure(operation, str(error), contracts.EXIT_ROLE_CONTEXT)
    except planning.PlanReplayError as error:
        return _failure(operation, str(error), contracts.EXIT_LIFECYCLE_CONFLICT)
    except planning.ConcurrentMutationError as error:
        return _failure(operation, str(error), contracts.EXIT_STALE_PLAN)
    except (ValueError, OSError, runtime.RuntimePlanningError) as error:
        return _failure(operation, str(error), contracts.EXIT_LIFECYCLE_CONFLICT)


def _failure(operation: str, message: str, exit_code: int) -> planning.OperationOutcome:
    return planning.OperationOutcome(
        data={"status": "blocked", "capability": ""},
        findings=(
            contracts.ContractFinding(
                "/arguments",
                f"{operation}.blocked",
                "error",
                message,
                "Repair strict config or runtime state, then create and review a new plan.",
            ),
        ),
        exit_code=exit_code,
    )
