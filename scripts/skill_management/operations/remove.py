"""Immutable-evidence, reference-safe skill removal through common plan/apply."""
from __future__ import annotations

from typing import Any, Dict, Mapping, Tuple

from skill_management import contracts, planning
from skill_management.operations import _maintenance
from skill_management.services import (
    lifecycle,
    provenance,
    registry,
    release_attestation,
)


def _data(
    status: str,
    identifier: str = "",
    origin: str = "",
    tombstone_digest: str = "",
    grace_evidence: str = "",
    removed_paths: Tuple[str, ...] = (),
    remaining_references: Tuple[str, ...] = (),
) -> Dict[str, Any]:
    return {
        "status": status,
        "skillId": identifier,
        "origin": origin,
        "tombstoneDigest": tombstone_digest,
        "graceEvidence": grace_evidence,
        "removedPaths": list(removed_paths),
        "remainingReferences": list(remaining_references),
    }


def _migration_paths(value: Any) -> Tuple[str, ...]:
    paths = tuple(item.strip() for item in str(value or "").split(",") if item.strip())
    if len(set(paths)) != len(paths):
        raise ValueError("migrations must contain unique repository-relative paths")
    return paths


def handle(*, context: Any, request: Mapping[str, Any]) -> planning.OperationOutcome:
    """Plan or apply exact owned-only deletion and tombstone publication."""
    try:
        arguments = request.get("arguments", {})
        positionals = arguments.get("positionals", [])
        if not isinstance(positionals, list) or len(positionals) != 1:
            raise ValueError("remove requires one skill identifier")
        identifier = str(positionals[0])
        desired = lifecycle.plan_removal(
            context.project_root,
            context.source_root,
            identifier,
            str(arguments.get("approver", "")),
            str(arguments.get("review_reference", "")),
            _migration_paths(arguments.get("migrations")),
            role=context.role,
            grace_exception=bool(arguments.get("grace_exception")),
            grace_reason=str(arguments.get("grace_reason", "")),
        )
        data = _data(
            "planned" if request["phase"] == "plan" else "committed",
            identifier,
            desired.origin,
            desired.tombstone_digest,
            desired.grace_evidence,
            desired.removed_paths,
            desired.remaining_references,
        )
        if request["phase"] == "plan":
            stored = planning.store_plan(context.project_root, desired.plan)
            return planning.OperationOutcome(
                changed=True,
                data=data,
                actions=tuple(
                    item.to_public_dict() for item in desired.plan.actions
                ),
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
        )
    except (
        planning.PlanRoleError,
        planning.StalePlanError,
        planning.ConcurrentMutationError,
        planning.PlanReplayError,
    ) as error:
        return _maintenance.failure(
            "remove",
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
        release_attestation.ReleaseAttestationError,
    ) as error:
        exit_code = (
            contracts.EXIT_ROLE_CONTEXT
            if "maintainer context" in str(error).casefold()
            else contracts.EXIT_LIFECYCLE_CONFLICT
        )
        return _maintenance.failure(
            "remove", error, exit_code=exit_code, data=_data("blocked")
        )
