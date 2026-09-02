"""Imported-skill immutable-source update through common plan/apply."""
from __future__ import annotations

import hashlib
import re
from typing import Any, Mapping

from skill_management import contracts, planning
from skill_management.context import WriteContextError, require_maintainer_write_context
from skill_management.operations import _maintenance
from skill_management.providers.github import GitHubAcquisitionError, GitHubProvider
from skill_management.services import admission, maintenance, provenance, registry


_FULL_SHA = re.compile(r"^[0-9a-f]{40}$")


def _data(
    status: str,
    identifier: str = "",
    origin: str = "",
    review_evidence: str = "",
    diff=(),
) -> Mapping[str, Any]:
    changes = [dict(item) for item in diff]
    return {
        "status": status,
        "skillId": identifier,
        "origin": origin,
        "reviewEvidence": review_evidence,
        "diffDigest": provenance.redacted_diff_digest(changes),
        "diff": changes,
    }


def handle(*, context: Any, request: Mapping[str, Any]) -> planning.OperationOutcome:
    """Plan or apply one imported skill transition to an explicit new full SHA."""
    try:
        arguments = request.get("arguments", {})
        positionals = arguments.get("positionals", [])
        if not isinstance(positionals, list) or len(positionals) != 2:
            raise ValueError("update requires <skill-id> <new-full-sha>")
        identifier = str(positionals[0])
        new_commit = str(positionals[1])
        if _FULL_SHA.fullmatch(new_commit) is None:
            raise ValueError("update requires one new full SHA")
        snapshot = registry.load_combined_registry_snapshot(
            context.project_root, context.source_root
        )
        project_record = snapshot.project_record_by_id(identifier)
        if project_record is not None:
            record = snapshot.provenance_by_id(identifier)
            origin_scope = "project-imported"
            review_scope = "project-update"
        else:
            record = snapshot.canonical_provenance_by_id(identifier)
            origin_scope = "plugin-canonical"
            review_scope = "plugin-update"
        if record is None:
            raise maintenance.MaintenancePlanningError(
                "Update is allowed only for skills with valid pinned upstream "
                "provenance"
            )
        history = record.get("history", [])
        if not history or history[0].get("event") != "imported":
            raise maintenance.MaintenancePlanningError(
                "Locally created skills have no imported upstream and cannot update"
            )
        source = record.get("source", {})
        old_commit = str(source.get("commit", ""))
        if new_commit == old_commit:
            return planning.OperationOutcome(
                changed=False,
                data=_data("unchanged", identifier, origin_scope),
            )
        approver = str(arguments.get("approver", ""))
        review_reference = str(arguments.get("review_reference", ""))
        provenance.validate_audit_metadata(approver, review_reference)
        policy = admission.load_admission_policy(context.source_root)
        repository = str(source.get("repository", ""))
        source_path = admission.require_allowed_source_path(
            str(source.get("path", "")), policy
        )
        if origin_scope == "plugin-canonical":
            require_maintainer_write_context(context)
            if not admission.repository_allowed_for_plugin(repository, policy):
                raise admission.AdmissionPolicyError(
                    "Plugin update repository is not on the canonical allowlist"
                )
        license_id = str(arguments.get("license", ""))
        if request["phase"] == "plan":
            acquired = GitHubProvider().acquire(
                repository,
                new_commit,
                source_path,
                policy.acquisition_limits,
            )
            admission.validate_acquired_source(
                acquired, repository, new_commit, source_path
            )
            quarantined = admission.materialize_quarantine(
                context.project_root,
                acquired,
                license_id,
                policy,
                review_scope=review_scope,
            )
        else:
            quarantined = admission.load_quarantined_candidate(
                context.project_root,
                repository,
                new_commit,
                source_path,
                license_id,
                policy,
                review_scope=review_scope,
            )
        if not quarantined.admission.ok:
            first = quarantined.admission.findings[0]
            raise admission.AdmissionPolicyError(
                f"Update admission rejected {first.path or 'bundle'}: {first.code}"
            )
        evidence_digest = hashlib.sha256(quarantined.evidence_bytes).hexdigest()
        plan, changes, planned_origin = maintenance.plan_imported_update(
            context.project_root,
            context.source_root,
            identifier,
            quarantined.inventory,
            new_commit,
            approver,
            review_reference,
            policy.digest,
            evidence_digest,
            license_id,
            role=context.role,
        )
        data = _data(
            "planned" if request["phase"] == "plan" else "committed",
            identifier,
            planned_origin,
            quarantined.evidence_path,
            changes,
        )
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
            "update",
            error,
            exit_code=contracts.EXIT_ROLE_CONTEXT,
            data=_data("blocked"),
        )
    except (GitHubAcquisitionError, admission.AdmissionPolicyError) as error:
        return _maintenance.failure(
            "update",
            error,
            exit_code=contracts.EXIT_SECURITY,
            data=_data("blocked"),
        )
    except (
        planning.PlanRoleError,
        planning.StalePlanError,
        planning.ConcurrentMutationError,
        planning.PlanReplayError,
    ) as error:
        return _maintenance.failure(
            "update",
            error,
            exit_code=_maintenance.transaction_exit(error),
            data=_data("blocked"),
        )
    except (
        ValueError,
        OSError,
        maintenance.MaintenancePlanningError,
        provenance.ProvenanceValidationError,
        registry.RegistryValidationError,
    ) as error:
        return _maintenance.failure("update", error, data=_data("blocked"))
