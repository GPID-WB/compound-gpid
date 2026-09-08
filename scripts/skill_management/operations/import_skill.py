"""Project import operation through bounded acquisition and common apply."""
from __future__ import annotations

import hashlib
from typing import Any, Mapping, Sequence, Tuple

from skill_management import contracts, planning
from skill_management.context import WriteContextError, require_maintainer_write_context
from skill_management.operations import _maintenance
from skill_management.providers.github import (
    GitHubAcquisitionError,
    GitHubProvider,
    normalize_public_github_origin,
    normalize_source_path,
)
from skill_management.services import admission, maintenance, provenance, runtime


def _finding(code: str, message: str, remediation: str, path: str) -> contracts.ContractFinding:
    return contracts.ContractFinding(path, code, "error", message, remediation)


def _split(value: str, allowed: Sequence[str], label: str) -> Tuple[str, ...]:
    items = tuple(item.strip() for item in value.split(",") if item.strip())
    if not items or len(set(items)) != len(items) or any(item not in allowed for item in items):
        raise ValueError(f"{label} must be a comma-separated subset of {', '.join(allowed)}")
    return tuple(item for item in allowed if item in items)


def _arguments(request: Mapping[str, Any]) -> Tuple[str, str, str, str, Tuple[str, ...], Tuple[str, ...]]:
    arguments = request.get("arguments", {})
    positionals = arguments.get("positionals", [])
    if not isinstance(positionals, list) or len(positionals) != 3:
        raise ValueError("import requires <origin> <path> <full-sha>")
    origin = normalize_public_github_origin(str(positionals[0]))
    source_path = normalize_source_path(str(positionals[1]))
    commit = str(positionals[2])
    license_id = str(arguments.get("license", ""))
    suites = _split(str(arguments.get("suites", "cg,cr")), ("cg", "cr"), "suites")
    platforms = _split(
        str(arguments.get("platforms", "copilot,claude-code,codex,opencode,kilo")),
        ("copilot", "claude-code", "codex", "opencode", "kilo"),
        "platforms",
    )
    return origin, source_path, commit, license_id, suites, platforms


def _failure(error: Exception, *, security: bool = False) -> planning.OperationOutcome:
    return planning.OperationOutcome(
        data={"status": "blocked", "skillId": "", "reviewEvidence": ""},
        findings=(
            _finding(
                "import.security" if security else "import.invalid",
                str(error),
                "Use one exact public GitHub origin, path, full SHA, approved license, and clean admitted bundle.",
                "/arguments",
            ),
        ),
        exit_code=contracts.EXIT_SECURITY if security else contracts.EXIT_CONTRACT,
    )


def handle(*, context: Any, request: Mapping[str, Any]) -> planning.OperationOutcome:
    """Plan or apply one project import or maintainer-only plugin vendor."""
    try:
        origin, source_path, commit, license_id, suites, platforms = _arguments(request)
        arguments = request.get("arguments", {})
        scope = str(arguments.get("scope", "project"))
        if scope not in {"project", "plugin"}:
            raise ValueError("import scope must be project or plugin")
        policy = admission.load_admission_policy(context.source_root)
        source_path = admission.require_allowed_source_path(source_path, policy)
        if scope == "plugin":
            require_maintainer_write_context(context)
            if not admission.repository_allowed_for_plugin(origin, policy):
                raise admission.AdmissionPolicyError(
                    "Plugin repository is not on the canonical allowlist"
                )
            metadata = _maintenance.capability_metadata(arguments)
            approver = str(arguments.get("approver", ""))
            review_reference = str(arguments.get("review_reference", ""))
            provenance.validate_audit_metadata(approver, review_reference)
            review_scope = "plugin-vendor"
        else:
            metadata = None
            approver = ""
            review_reference = ""
            review_scope = "project-import"
        if request["phase"] == "plan":
            acquired = GitHubProvider().acquire(
                origin, commit, source_path, policy.acquisition_limits
            )
            admission.validate_acquired_source(
                acquired, origin, commit, source_path
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
                origin,
                commit,
                source_path,
                license_id,
                policy,
                review_scope=review_scope,
            )
        if not quarantined.admission.ok:
            first = quarantined.admission.findings[0]
            raise GitHubAcquisitionError(
                f"Admission rejected {first.path or 'bundle'}: {first.code}"
            )
        evidence_digest = hashlib.sha256(quarantined.evidence_bytes).hexdigest()
        if scope == "project":
            plan = runtime.plan_project_import(
                context.project_root,
                context.source_root,
                quarantined.inventory,
                origin=origin,
                source_path=source_path,
                commit=commit,
                suites=suites,
                platforms=platforms,
                policy_digest=policy.digest,
                review_evidence_digest=evidence_digest,
                license_id=license_id,
                role=context.role,
            )
        else:
            assert metadata is not None
            record = provenance.provenance_record(
                quarantined.inventory.identifier,
                "plugin-canonical",
                origin,
                source_path,
                commit,
                quarantined.inventory.digest,
                "imported",
                approver,
                review_reference,
                policy_digest=policy.digest,
                review_evidence_digest=evidence_digest,
            )
            plan = maintenance.plan_canonical_add(
                context.project_root,
                context.source_root,
                quarantined.inventory,
                metadata,
                record,
                operation="import",
                role=context.role,
                policy_digest=policy.digest,
                review_evidence_digest=evidence_digest,
                license_id=license_id,
            )
        if request["phase"] == "plan":
            stored = planning.store_plan(context.project_root, plan)
            return planning.OperationOutcome(
                changed=True,
                data={
                    "status": "planned",
                    "skillId": quarantined.inventory.identifier,
                    "reviewEvidence": quarantined.evidence_path,
                },
                actions=tuple(action.to_public_dict() for action in plan.actions),
                plan_digest=stored.digest,
            )
        result = planning.apply_plan(
            context.project_root, plan, str(request["planDigest"])
        )
        return planning.OperationOutcome(
            changed=True,
            data={
                "status": result.state,
                "skillId": quarantined.inventory.identifier,
                "reviewEvidence": quarantined.evidence_path,
            },
            actions=tuple(action.to_public_dict() for action in plan.actions),
        )
    except WriteContextError as error:
        outcome = _failure(error)
        return planning.OperationOutcome(
            data=outcome.data,
            findings=outcome.findings,
            exit_code=contracts.EXIT_ROLE_CONTEXT,
        )
    except (GitHubAcquisitionError, admission.AdmissionPolicyError) as error:
        return _failure(error, security=True)
    except planning.PlanRoleError as error:
        outcome = _failure(error)
        return planning.OperationOutcome(
            data=outcome.data,
            findings=outcome.findings,
            exit_code=contracts.EXIT_ROLE_CONTEXT,
        )
    except (planning.StalePlanError, planning.ConcurrentMutationError) as error:
        outcome = _failure(error)
        return planning.OperationOutcome(
            data=outcome.data,
            findings=outcome.findings,
            exit_code=contracts.EXIT_STALE_PLAN,
        )
    except planning.PlanReplayError as error:
        outcome = _failure(error)
        return planning.OperationOutcome(
            data=outcome.data,
            findings=outcome.findings,
            exit_code=contracts.EXIT_LIFECYCLE_CONFLICT,
        )
    except (
        ValueError,
        OSError,
        maintenance.MaintenancePlanningError,
        provenance.ProvenanceValidationError,
    ) as error:
        return _failure(error)
