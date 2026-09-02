"""Maintainer-only permanent skill creation through common plan/apply."""
from __future__ import annotations

import hashlib
from typing import Any, Mapping

from skill_management import contracts, planning
from skill_management.context import WriteContextError, require_maintainer_write_context
from skill_management.operations import _maintenance
from skill_management.services import (
    admission,
    bundles,
    maintenance,
    provenance,
    registry,
    runtime,
)


def _failure_data() -> Mapping[str, Any]:
    return {
        "status": "blocked",
        "skillId": "",
        "owner": "",
        "capability": "",
        "availability": "inactive",
    }


def handle(*, context: Any, request: Mapping[str, Any]) -> planning.OperationOutcome:
    """Plan or apply one complete inactive permanent canonical skill."""
    try:
        require_maintainer_write_context(context)
        arguments = request.get("arguments", {})
        positionals = arguments.get("positionals", [])
        if not isinstance(positionals, list) or len(positionals) != 1:
            raise ValueError("create requires one permanent skill identifier")
        if arguments.get("scope") != "permanent":
            raise ValueError("create requires scope permanent")
        metadata = _maintenance.capability_metadata(arguments)
        approver = str(arguments.get("approver", ""))
        review_reference = str(arguments.get("review_reference", ""))
        provenance.validate_audit_metadata(approver, review_reference)
        candidate = bundles.scaffold_permanent_bundle(
            context.source_root,
            str(positionals[0]),
            str(arguments.get("description", "")),
            metadata.owner,
            metadata.identifier,
            references=_maintenance.comma_values(
                arguments.get("references"), "references", required=False
            ),
            workflows=_maintenance.comma_values(
                arguments.get("workflows"), "workflows", required=False
            ),
            examples=_maintenance.comma_values(
                arguments.get("examples"), "examples", required=False
            ),
            resources=_maintenance.comma_values(
                arguments.get("resources"), "resources", required=False
            ),
            resource_classes=_maintenance.resource_classes(
                arguments.get("resource_classes")
            ),
        )
        policy = admission.load_admission_policy(context.source_root)
        admitted = admission.admit_inventory(candidate, policy)
        if not admitted.ok:
            first = admitted.findings[0]
            raise admission.AdmissionPolicyError(
                f"Created bundle resource is rejected: {first.path or 'bundle'}: "
                f"{first.message}"
            )
        current = registry.load_combined_registry_snapshot(
            context.project_root, context.source_root
        )
        source_revision = runtime.plan_bindings(
            context.project_root, context.source_root, current
        ).source_revision
        evidence_digest = hashlib.sha256(admitted.evidence_bytes).hexdigest()
        record = provenance.provenance_record(
            candidate.identifier,
            "plugin-canonical",
            maintenance.canonical_repository(),
            candidate.source_path,
            source_revision,
            candidate.digest,
            "created",
            approver,
            review_reference,
            policy_digest=policy.digest,
            review_evidence_digest=evidence_digest,
        )
        plan = maintenance.plan_canonical_add(
            context.project_root,
            context.source_root,
            candidate,
            metadata,
            record,
            operation="create",
            role=context.role,
            policy_digest=policy.digest,
            review_evidence_digest=evidence_digest,
        )
        data = {
            "status": "planned" if request["phase"] == "plan" else "committed",
            "skillId": candidate.identifier,
            "owner": metadata.owner,
            "capability": metadata.identifier,
            "availability": "inactive",
        }
        if request["phase"] == "plan":
            stored = planning.store_plan(context.project_root, plan)
            return planning.OperationOutcome(
                changed=True,
                data=data,
                actions=tuple(item.to_public_dict() for item in plan.actions),
                plan_digest=stored.digest,
            )
        result = planning.apply_plan(
            context.project_root, plan, str(request["planDigest"])
        )
        data["status"] = result.state
        return planning.OperationOutcome(
            changed=True,
            data=data,
            actions=tuple(item.to_public_dict() for item in plan.actions),
        )
    except WriteContextError as error:
        return _maintenance.failure(
            "create",
            error,
            exit_code=contracts.EXIT_ROLE_CONTEXT,
            data=_failure_data(),
        )
    except admission.AdmissionPolicyError as error:
        return _maintenance.failure(
            "create",
            error,
            exit_code=contracts.EXIT_SECURITY,
            data=_failure_data(),
        )
    except (
        planning.PlanRoleError,
        planning.StalePlanError,
        planning.ConcurrentMutationError,
        planning.PlanReplayError,
    ) as error:
        return _maintenance.failure(
            "create",
            error,
            exit_code=_maintenance.transaction_exit(error),
            data=_failure_data(),
        )
    except (
        ValueError,
        OSError,
        bundles.BundleValidationError,
        maintenance.MaintenancePlanningError,
        provenance.ProvenanceValidationError,
        registry.RegistryValidationError,
    ) as error:
        return _maintenance.failure("create", error, data=_failure_data())
