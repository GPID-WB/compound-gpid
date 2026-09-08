"""Complete read-only skill validation shared by validate, audit, and removal."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Dict, List, Optional, Sequence, Tuple

import cg_project_projection as projection_module
import cg_validate_modules as module_validator

from skill_management import contracts
from skill_management.services import admission, bundles, catalog, references, registry


class UnknownSkillError(ValueError):
    """Raised when a read operation selects an unknown immutable identifier."""


@dataclass(frozen=True)
class ValidationReport:
    """One complete deterministic side-effect-free validation result."""

    manifest_health: str
    validated_ids: Tuple[str, ...]
    descriptor_operations: Tuple[str, ...]
    findings: Tuple[contracts.ContractFinding, ...]
    reference_report: references.ReferenceReport


def _finding(
    code: str,
    severity: str,
    path: str,
    message: str,
    remediation: str,
) -> contracts.ContractFinding:
    return contracts.ContractFinding(path, code, severity, message, remediation)


def _manifest(
    project_root: Path, source_root: Path
) -> Tuple[str, Optional[Dict[str, Any]], List[contracts.ContractFinding]]:
    try:
        status = catalog.inspect_manifest(project_root, source_root)
    except catalog.CatalogError as error:
        return "invalid", None, [
            _finding(
                "manifest.invalid",
                "error",
                "/manifest",
                str(error),
                catalog.INVALID_REMEDIATION,
            )
        ]
    if status.health == "fresh":
        return "fresh", dict(status.committed or {}), []
    return status.health, None, [
        _finding(
            f"manifest.{status.health}",
            "warning",
            "/manifest",
            f"Active manifest is {status.health}; runtime availability is not verified.",
            status.remediation,
        )
    ]


def _ownership_findings(source_root: Path) -> List[contracts.ContractFinding]:
    try:
        module_validator.canonical_assets.cache_clear()
        assets = module_validator.canonical_assets(source_root)
        value, error = module_validator.load_registry(source_root)
        if error or value is None:
            raise ValueError(error or "Canonical module registry is unavailable")
        errors = module_validator.check_owned_assets_exist(value, assets)
        errors.extend(module_validator.check_ownership_closure(value, assets))
    except (OSError, UnicodeError, ValueError) as error:
        errors = [str(error)]
    return [
        _finding(
            "registry.ownership",
            "error",
            registry.MODULE_REGISTRY_PATH,
            message,
            "Assign every canonical asset to exactly one valid owner and rerun validation.",
        )
        for message in sorted(set(errors))
    ]


def _policy_findings(
    source_root: Path,
    inventories: Sequence[bundles.BundleInventory],
) -> List[contracts.ContractFinding]:
    try:
        policy = admission.load_admission_policy(source_root)
    except (OSError, ValueError, admission.AdmissionPolicyError) as error:
        return [
            _finding(
                "policy.invalid",
                "error",
                ".github/shared/vendor-policy.json",
                str(error),
                "Repair the canonical non-data resource policy.",
            )
        ]
    included_codes = {
        "admission.binary",
        "admission.blocked-extension",
        "admission.encoding",
        "admission.executable",
        "admission.file-count",
        "admission.file-size",
        "admission.json",
        "admission.lfs",
        "admission.opaque-class",
        "admission.path",
        "admission.total-size",
        "bundle.reference-escape",
        "bundle.reference-missing",
    }
    findings = []
    for inventory in inventories:
        result = admission.admit_inventory(inventory, policy)
        for item in result.findings:
            if item.code not in included_codes:
                continue
            findings.append(
                _finding(
                    item.code,
                    "error",
                    f"{inventory.source_path}/{item.path}".rstrip("/"),
                    item.message,
                    "Remove the prohibited resource or declare an approved non-data class.",
                )
            )
    return findings


def _baseline_bundle_findings(
    source_root: Path,
    identifier: Optional[str],
) -> Tuple[List[contracts.ContractFinding], Tuple[str, ...]]:
    """Collect bundle findings even when a combined snapshot cannot load."""
    findings = []
    validated_ids = []
    try:
        canonical = registry.load_registry_snapshot(source_root)
    except registry.RegistryValidationError:
        canonical = None
    try:
        paths = bundles.list_canonical_bundle_paths(source_root)
    except bundles.BundleValidationError as error:
        return [
            _finding(
                "bundle.inventory",
                "error",
                ".github/skills",
                str(error),
                "Repair the canonical skill root and rerun validation.",
            )
        ], ()
    for source_path in paths:
        skill_id = PurePosixPath(source_path).name
        if identifier is not None and skill_id != identifier:
            continue
        validated_ids.append(skill_id)
        try:
            inventory = bundles.inventory_bundle(
                source_root, source_path, origin="plugin-canonical"
            )
        except bundles.BundleValidationError as error:
            message = str(error)
            code = (
                "bundle.frontmatter"
                if "SKILL.md" in message or "frontmatter" in message
                else "bundle.inventory"
            )
            findings.append(
                _finding(
                    code,
                    "error",
                    f"{source_path}/SKILL.md",
                    message,
                    "Repair the complete bundle and its SKILL.md metadata.",
                )
            )
            inventory = None
        if inventory is not None:
            for issue in bundles.validate_markdown_references(inventory):
                findings.append(
                    _finding(
                        issue.code,
                        "error",
                        issue.path,
                        issue.message,
                        issue.remediation,
                    )
                )
        if canonical is not None:
            skill_path = f"{source_path}/SKILL.md"
            try:
                owner = canonical.owner_for_asset(skill_path)
            except registry.RegistryValidationError as error:
                findings.append(
                    _finding(
                        "registry.owner-multiple",
                        "error",
                        skill_path,
                        str(error),
                        "Assign exactly one canonical owner to the bundle.",
                    )
                )
            else:
                if owner is None:
                    findings.append(
                        _finding(
                            "registry.owner-missing",
                            "error",
                            skill_path,
                            "Canonical skill has no owning module.",
                            "Add one exact ownedAssets assignment in the canonical registry.",
                        )
                    )
    return findings, tuple(sorted(validated_ids))


def _provenance_findings(
    snapshot: registry.CombinedRegistrySnapshot,
    selected_ids: Sequence[str],
) -> List[contracts.ContractFinding]:
    findings = []
    selected = set(selected_ids)
    for inventory in snapshot.canonical_bundles:
        if inventory.identifier not in selected:
            continue
        if snapshot.canonical_provenance_by_id(inventory.identifier) is None:
            findings.append(
                _finding(
                    "provenance.missing",
                    "warning",
                    f".github/shared/skill-management/provenance/{inventory.identifier}.json",
                    "Canonical skill has no committed lifecycle provenance.",
                    "Create provenance before the skill enters a destructive lifecycle transition.",
                )
            )
    return findings


def _lifecycle_findings(
    snapshot: registry.CombinedRegistrySnapshot,
    target_by_id: Dict[str, references.ReferenceTarget],
    reference_report: references.ReferenceReport,
) -> List[contracts.ContractFinding]:
    findings = []
    active_by_id = {}  # type: Dict[str, List[references.ReferenceRecord]]
    for item in reference_report.active:
        active_by_id.setdefault(item.skill_id, []).append(item)
    for identifier in sorted(target_by_id):
        provenance_record = snapshot.provenance_record_by_id(identifier)
        lifecycle = (
            str(provenance_record.get("lifecycle"))
            if provenance_record is not None
            else "current"
        )
        for item in active_by_id.get(identifier, []):
            if lifecycle == "deprecated":
                findings.append(
                    _finding(
                        "reference.deprecated-active",
                        "warning",
                        item.path,
                        f"Active content still references deprecated skill {identifier!r}.",
                        f"Migrate this reference to successor {provenance_record.get('successorId')!r}.",
                    )
                )
            elif lifecycle == "removed":
                findings.append(
                    _finding(
                        "reference.removed-active",
                        "error",
                        item.path,
                        f"Active content references removed skill {identifier!r}.",
                        "Replace the reference with the tombstone successor.",
                    )
                )
    return findings


def _projection_findings(
    project_root: Path,
    source_root: Path,
    snapshot: registry.CombinedRegistrySnapshot,
    manifest: Optional[Dict[str, Any]],
) -> List[contracts.ContractFinding]:
    if manifest is None:
        return []
    try:
        plan = projection_module.build_projection_plan(
            source_root,
            manifest,
            project_root=project_root,
            combined_snapshot=snapshot,
        )
        problems = projection_module.verify_projection(project_root, plan)
    except (OSError, UnicodeError, ValueError) as error:
        problems = [str(error)]
    return [
        _finding(
            "projection.drift",
            "error",
            "/projection",
            problem,
            "Regenerate and publish the exact desired target and projection plan.",
        )
        for problem in sorted(set(problems))
    ]


def _empty_reference_report() -> references.ReferenceReport:
    return references.empty_reference_report()


def validate_skills(
    project_root: Path,
    source_root: Path,
    *,
    identifier: Optional[str],
    include_provenance: bool = True,
    include_references: bool = True,
) -> ValidationReport:
    """Validate one known skill or every current and tombstoned skill.

    Args:
        project_root: Project and projection root.
        source_root: Canonical source root.
        identifier: Optional exact immutable skill identifier.
        include_provenance: Include provenance completeness findings.
        include_references: Build and evaluate the complete reference report.

    Returns:
        Stable complete read-only validation report.

    Example:
        ``validate_skills(project, source, identifier=None)``
    """
    project = Path(project_root).resolve(strict=True)
    source = Path(source_root).resolve(strict=True)
    findings = list(contracts.descriptor_completeness_findings(source))
    descriptor_records, descriptor_findings = contracts.discover_operation_descriptors(
        source
    )
    findings.extend(descriptor_findings)
    descriptor_operations = tuple(item.operation for item in descriptor_records)
    manifest_health, committed_manifest, manifest_findings = _manifest(project, source)
    findings.extend(manifest_findings)
    baseline_findings, baseline_ids = _baseline_bundle_findings(source, identifier)
    findings.extend(baseline_findings)
    snapshot = None  # type: Optional[registry.CombinedRegistrySnapshot]
    try:
        snapshot = registry.load_combined_registry_snapshot(project, source)
    except registry.RegistryValidationError as error:
        findings.append(
            _finding(
                "registry.invalid",
                "error",
                registry.MODULE_REGISTRY_PATH,
                str(error),
                "Repair canonical/project registries, provenance, and bundle inputs.",
            )
        )
    findings.extend(_ownership_findings(source))
    if snapshot is None:
        return ValidationReport(
            "invalid" if manifest_health == "fresh" else manifest_health,
            baseline_ids,
            descriptor_operations,
            contracts.sort_findings(findings),
            _empty_reference_report(),
        )
    targets = references.targets_from_snapshot(snapshot)
    target_by_id = {item.identifier: item for item in targets}
    if identifier is not None and identifier not in target_by_id:
        raise UnknownSkillError(f"Unknown skill identifier: {identifier!r}")
    selected_ids = (
        (identifier,) if identifier is not None else tuple(sorted(target_by_id))
    )
    inventories = tuple(
        item
        for item in tuple(snapshot.canonical_bundles) + tuple(snapshot.project_bundles)
        if item.identifier in set(selected_ids)
    )
    findings.extend(_policy_findings(source, inventories))
    if include_provenance:
        findings.extend(_provenance_findings(snapshot, selected_ids))
    if include_references:
        reference_report = references.scan_references(
            project,
            source,
            tuple(target_by_id[item] for item in selected_ids),
        )
        findings.extend(reference_report.findings)
        findings.extend(
            _lifecycle_findings(snapshot, target_by_id, reference_report)
        )
    else:
        reference_report = _empty_reference_report()
    findings.extend(
        _projection_findings(
            project, source, snapshot, committed_manifest if manifest_health == "fresh" else None
        )
    )
    return ValidationReport(
        manifest_health,
        tuple(sorted(selected_ids)),
        descriptor_operations,
        contracts.sort_findings(findings),
        reference_report,
    )
