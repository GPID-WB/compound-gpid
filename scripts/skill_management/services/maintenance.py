"""Pure Phase 5 canonical creation, vendoring, and imported-update planning."""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from skill_management import contracts, planning
from skill_management.context import CANONICAL_SOURCE_ORIGIN
from skill_management.services import bundles, catalog, provenance, registry, runtime


_FULL_SHA = re.compile(r"^[0-9a-f]{40}$")
_IDENTIFIER = re.compile(r"^[a-z][a-z0-9-]*$")


class MaintenancePlanningError(ValueError):
    """Raised when Phase 5 desired state cannot be proved safe and complete."""


@dataclass(frozen=True)
class CapabilityMetadata:
    """Explicit canonical capability metadata required for registration."""

    identifier: str
    owner: str
    suites: Tuple[str, ...]
    platforms: Tuple[str, ...]
    activation_cost: str
    triggers: Tuple[str, ...]
    selectors: Tuple[Mapping[str, str], ...]

    def to_record(self, source_provenance: str) -> Dict[str, Any]:
        """Return one complete inactive explicit-only capability record."""
        return {
            "id": self.identifier,
            "owningModule": self.owner,
            "activationMode": "explicit-only",
            "supportedSuites": list(self.suites),
            "supportedPlatforms": list(self.platforms),
            "sourceProvenance": source_provenance,
            "activationCost": self.activation_cost,
            "taskTriggers": list(self.triggers),
            "configSelectors": [dict(item) for item in self.selectors],
        }


def _canonical_registry_bytes(value: Mapping[str, Any]) -> bytes:
    return (
        json.dumps(value, indent=2, ensure_ascii=False, sort_keys=False) + "\n"
    ).encode("utf-8")


def _current_project_registry(
    project_root: Path,
) -> Tuple[Dict[str, Any], bytes]:
    content = runtime.read_optional_bytes(
        project_root,
        registry.PROJECT_REGISTRY_PATH,
        max_bytes=contracts.MAX_CONTRACT_BYTES,
    )
    if content is None:
        value = {
            "schema": "cg-project-skill-registry-v1",
            "schemaVersion": 1,
            "records": [],
        }
        return value, contracts.canonical_json_bytes(value)
    try:
        value = contracts.load_contract_bytes(
            content, source=registry.PROJECT_REGISTRY_PATH
        )
    except ValueError as error:
        raise MaintenancePlanningError(str(error)) from error
    return value, content


def _current_canonical_provenance_bytes(
    source_root: Path,
    snapshot: registry.CombinedRegistrySnapshot,
) -> Dict[str, bytes]:
    result = {}
    for record in snapshot.canonical_provenance_records:
        identifier = str(record["skillId"])
        relative = f"{provenance.CANONICAL_PROVENANCE_ROOT}/{identifier}.json"
        content = runtime.read_optional_bytes(
            source_root, relative, max_bytes=contracts.MAX_CONTRACT_BYTES
        )
        if content is None:
            raise MaintenancePlanningError(
                f"Committed canonical provenance is missing: {identifier}"
            )
        result[identifier] = content
    return result


def _retarget_inventory(
    inventory: bundles.BundleInventory,
    source_path: str,
    origin: str,
) -> bundles.BundleInventory:
    return bundles.bundle_inventory_from_files(
        inventory.identifier,
        source_path,
        origin,
        {item.bundle_path: item.content for item in inventory.files},
    )


def _replace_inventory(
    inventories: Sequence[bundles.BundleInventory],
    replacement: bundles.BundleInventory,
) -> Tuple[bundles.BundleInventory, ...]:
    result = [
        item for item in inventories if item.identifier != replacement.identifier
    ]
    result.append(replacement)
    return tuple(sorted(result, key=lambda item: item.identifier))


def _inventory_actions(
    current: Optional[bundles.BundleInventory],
    future: bundles.BundleInventory,
    description: str,
) -> Tuple[planning.PlannedAction, ...]:
    before = {item.bundle_path: item for item in current.files} if current else {}
    after = {item.bundle_path: item for item in future.files}
    actions = []
    for bundle_path in sorted(set(before) | set(after)):
        old = before.get(bundle_path)
        new = after.get(bundle_path)
        old_bytes = old.content if old is not None else None
        new_bytes = new.content if new is not None else None
        if old_bytes == new_bytes:
            continue
        if new is not None:
            source_path = new.source_path
        else:
            assert old is not None
            source_path = old.source_path
        actions.append(
            planning.PlannedAction(
                "write-file" if new is not None else "delete-file",
                source_path,
                description,
                planning.ExpectedMutation(
                    source_path, old_bytes, new_bytes, "source", False
                ),
            )
        )
    return tuple(actions)


def _fresh_inactive_owner(
    project_root: Path,
    source_root: Path,
    owner: str,
) -> None:
    try:
        status = catalog.inspect_manifest(project_root, source_root)
    except catalog.CatalogError as error:
        raise MaintenancePlanningError(str(error)) from error
    if status.health != "fresh":
        raise MaintenancePlanningError(
            "Permanent registration requires a fresh active manifest to prove "
            "inactivity"
        )
    closure = set(status.committed.get("selection", {}).get("moduleClosure", []))
    if owner in closure:
        raise MaintenancePlanningError(
            f"Owner module {owner!r} is active; a new skill would not be "
            "initially inactive"
        )


def _validate_capability_assignment(
    current: registry.CombinedRegistrySnapshot,
    future_registry: Dict[str, Any],
    metadata: CapabilityMetadata,
) -> None:
    modules = {
        str(item.get("id")): item
        for item in future_registry.get("modules", [])
        if isinstance(item, dict)
    }
    owner = modules.get(metadata.owner)
    if owner is None or owner.get("layer") != "capability":
        raise MaintenancePlanningError(
            "Permanent skill owner must be one explicit capability-layer module"
        )
    existing = current.canonical.capability_by_id(metadata.identifier)
    expected = metadata.to_record(
        str(existing.get("sourceProvenance", "canonical/.github"))
        if existing
        else "canonical/.github"
    )
    if existing is not None:
        if existing.get("activationMode") != "explicit-only":
            raise MaintenancePlanningError(
                "Existing capability assignment must be explicit-only"
            )
        comparable = dict(existing)
        if comparable != expected:
            raise MaintenancePlanningError(
                "Existing capability metadata does not match the explicit "
                "registration metadata"
            )
        return
    assigned = current.canonical.capability_for_owner(metadata.owner)
    if assigned is not None:
        raise MaintenancePlanningError(
            f"Owner module {metadata.owner!r} already has capability {assigned['id']!r}"
        )
    future_registry.setdefault("capabilities", []).append(expected)


def plan_canonical_add(
    project_root: Path,
    source_root: Path,
    candidate: bundles.BundleInventory,
    metadata: CapabilityMetadata,
    provenance_record: Mapping[str, Any],
    *,
    operation: str,
    role: str,
    policy_digest: str,
    review_evidence_digest: str,
    license_id: str = "",
) -> planning.LifecyclePlan:
    """Plan one inactive created or vendored canonical skill transaction."""
    project = Path(project_root).resolve(strict=True)
    source = Path(source_root).resolve(strict=True)
    if project != source:
        raise MaintenancePlanningError(
            "Canonical mutation requires equal project and source roots"
        )
    current = registry.load_combined_registry_snapshot(project, source)
    identifier = candidate.identifier
    if _IDENTIFIER.fullmatch(identifier) is None:
        raise MaintenancePlanningError("Permanent skill identifier is invalid")
    if current.identifier_reserved(identifier):
        raise MaintenancePlanningError(
            f"Skill identifier is already active or reserved by a tombstone: {identifier}"
        )
    if candidate.source_path != f".github/skills/{identifier}":
        candidate = _retarget_inventory(
            candidate, f".github/skills/{identifier}", "plugin-canonical"
        )
    declared_owner = candidate.frontmatter.get("owner")
    declared_capability = candidate.frontmatter.get("capability")
    if declared_owner is not None and declared_owner != metadata.owner:
        raise MaintenancePlanningError("Candidate frontmatter owner mismatch")
    if declared_capability is not None and declared_capability != metadata.identifier:
        raise MaintenancePlanningError("Candidate frontmatter capability mismatch")
    _fresh_inactive_owner(project, source, metadata.owner)

    future_registry = current.canonical.to_dict()
    if not any(
        item.get("id") == metadata.owner
        for item in future_registry.get("modules", [])
        if isinstance(item, dict)
    ):
        future_registry.setdefault("modules", []).append(
            {
                "id": metadata.owner,
                "layer": "capability",
                "displayName": " ".join(
                    part.capitalize() for part in metadata.owner.split("-")
                ),
                "description": (
                    f"Explicit owner module for permanent skill {identifier}."
                ),
                "dependsOn": ["kernel"],
                "ownedAssets": [],
                "ambiguous": [],
            }
        )
    _validate_capability_assignment(current, future_registry, metadata)
    owner = next(
        item for item in future_registry["modules"] if item.get("id") == metadata.owner
    )
    skill_path = f".github/skills/{identifier}/SKILL.md"
    if not any(
        registry.glob_match(pattern, skill_path)
        for pattern in owner.get("ownedAssets", [])
    ):
        owner.setdefault("ownedAssets", []).append(f".github/skills/{identifier}/")
    registry_bytes = _canonical_registry_bytes(future_registry)
    future_canonical_snapshot = registry.RegistrySnapshot.from_data(
        source,
        future_registry,
        digest=hashlib.sha256(registry_bytes).hexdigest(),
    )

    project_registry, project_registry_bytes = _current_project_registry(project)
    project_provenance_bytes = runtime.current_project_provenance_bytes(
        project, current
    )
    canonical_provenance_bytes = _current_canonical_provenance_bytes(source, current)
    canonical_provenance_bytes[identifier] = runtime.provenance_bytes(
        provenance_record
    )
    canonical_provenance_records = [
        dict(item) for item in current.canonical_provenance_records
    ] + [dict(provenance_record)]
    future_snapshot = registry.build_combined_registry_snapshot(
        project,
        future_canonical_snapshot,
        project_registry,
        project_registry_bytes,
        current.project_bundles,
        current.provenance_records,
        project_provenance_bytes,
        canonical_bundles=tuple(current.canonical_bundles) + (candidate,),
        canonical_provenance_records=canonical_provenance_records,
        canonical_provenance_bytes=canonical_provenance_bytes,
    )
    actions = list(
        _inventory_actions(
            None, candidate, "Publish one approved inactive canonical skill resource."
        )
    )
    provenance_path = (
        f"{provenance.CANONICAL_PROVENANCE_ROOT}/{identifier}.json"
    )
    actions.append(
        planning.PlannedAction(
            "write-file",
            provenance_path,
            "Publish immutable canonical skill provenance and audit metadata.",
            planning.ExpectedMutation(
                provenance_path,
                None,
                canonical_provenance_bytes[identifier],
                "provenance",
            ),
        )
    )
    registry_before = runtime.read_optional_bytes(
        source,
        registry.MODULE_REGISTRY_PATH,
        max_bytes=contracts.MAX_CONTRACT_BYTES,
    )
    if registry_before is None:
        raise MaintenancePlanningError("Canonical module registry is missing")
    actions.append(
        planning.PlannedAction(
            "update-registry",
            registry.MODULE_REGISTRY_PATH,
            "Register exact permanent skill ownership and capability metadata.",
            planning.ExpectedMutation(
                registry.MODULE_REGISTRY_PATH,
                registry_before,
                registry_bytes,
                "registry",
            ),
        )
    )
    config = runtime.read_optional_bytes(
        project, runtime.CONFIG_PATH, max_bytes=contracts.MAX_CONTRACT_BYTES
    )
    if config is None:
        raise MaintenancePlanningError(f"{runtime.CONFIG_PATH} is missing")
    runtime_actions, checks = runtime.runtime_refresh_actions(
        project, source, future_snapshot, config
    )
    actions.extend(runtime_actions)
    source_paths = tuple(item.source_path for item in candidate.files)
    return planning.LifecyclePlan(
        operation,
        role,
        {
            "skillId": identifier,
            "owner": metadata.owner,
            "capability": metadata.identifier,
            "suites": list(metadata.suites),
            "platforms": list(metadata.platforms),
            "activationCost": metadata.activation_cost,
            "triggers": list(metadata.triggers),
            "selectors": [dict(item) for item in metadata.selectors],
            "candidateDigest": candidate.digest,
            "policyDigest": policy_digest,
            "reviewEvidenceDigest": review_evidence_digest,
            "approver": provenance_record["history"][0]["approval"]["actor"],
            "reviewReference": provenance_record["history"][0]["approval"][
                "reviewReference"
            ],
            "license": license_id,
        },
        runtime.plan_bindings(project, source, current),
        tuple(actions),
        (planning.InventoryCheck(candidate.source_path, source_paths),) + checks,
    )


def _updated_project_record(
    current: registry.CombinedRegistrySnapshot,
    identifier: str,
    bundle_digest: str,
) -> Tuple[List[Dict[str, Any]], bytes, Dict[str, Any]]:
    records = [dict(item) for item in current.project_records]
    selected = None
    for record in records:
        if record.get("id") == identifier:
            record["bundleDigest"] = bundle_digest
            selected = record
            break
    if selected is None:
        raise MaintenancePlanningError(f"Unknown project skill: {identifier}")
    content = runtime.project_registry_bytes(records)
    return records, content, selected


def plan_imported_update(
    project_root: Path,
    source_root: Path,
    identifier: str,
    candidate: bundles.BundleInventory,
    new_commit: str,
    approver: str,
    review_reference: str,
    policy_digest: str,
    review_evidence_digest: str,
    license_id: str,
    *,
    role: str,
) -> Tuple[planning.LifecyclePlan, Tuple[Dict[str, Any], ...], str]:
    """Plan one immutable-origin project or plugin imported-skill update."""
    if _FULL_SHA.fullmatch(new_commit) is None:
        raise MaintenancePlanningError("Imported skill update requires one full SHA")
    project = Path(project_root).resolve(strict=True)
    source = Path(source_root).resolve(strict=True)
    current = registry.load_combined_registry_snapshot(project, source)
    project_record = current.project_record_by_id(identifier)
    if project_record is not None:
        current_inventory = current.project_bundle_by_id(identifier)
        record = current.provenance_by_id(identifier)
        origin_scope = "project-imported"
        future_source_path = str(project_record["sourcePath"])
    else:
        current_inventory = current.canonical_bundle_by_id(identifier)
        record = current.canonical_provenance_by_id(identifier)
        origin_scope = "plugin-canonical"
        future_source_path = f".github/skills/{identifier}"
    if current_inventory is None or record is None:
        raise MaintenancePlanningError(
            "Update is allowed only for skills with valid pinned upstream provenance"
        )
    history = record.get("history", [])
    if not history or history[0].get("event") != "imported":
        raise MaintenancePlanningError(
            "Locally created skills have no imported upstream and cannot update"
        )
    source_identity = record.get("source", {})
    old_commit = str(source_identity.get("commit", ""))
    if new_commit == old_commit:
        raise MaintenancePlanningError("Imported skill update requires a new full SHA")
    if candidate.identifier != identifier:
        raise MaintenancePlanningError("Imported skill identifier is immutable")
    future_inventory = _retarget_inventory(
        candidate, future_source_path, origin_scope
    )
    changes = provenance.redacted_inventory_diff(
        current_inventory, future_inventory
    )
    updated_provenance = provenance.append_update(
        record,
        new_commit,
        future_inventory.digest,
        approver,
        review_reference,
        policy_digest,
        review_evidence_digest,
        changes,
    )

    actions = list(
        _inventory_actions(
            current_inventory,
            future_inventory,
            "Publish one admitted immutable-source skill update resource.",
        )
    )
    project_registry, project_registry_before = _current_project_registry(project)
    project_provenance_bytes = runtime.current_project_provenance_bytes(
        project, current
    )
    canonical_provenance_bytes = _current_canonical_provenance_bytes(source, current)
    if origin_scope == "project-imported":
        project_records, project_registry_after, _selected = _updated_project_record(
            current, identifier, future_inventory.digest
        )
        project_registry = {
            "schema": "cg-project-skill-registry-v1",
            "schemaVersion": 1,
            "records": project_records,
        }
        project_provenance_bytes[identifier] = runtime.provenance_bytes(
            updated_provenance
        )
        project_provenance_records = [
            updated_provenance if item.get("skillId") == identifier else dict(item)
            for item in current.provenance_records
        ]
        future_snapshot = registry.build_combined_registry_snapshot(
            project,
            current.canonical,
            project_registry,
            project_registry_after,
            _replace_inventory(current.project_bundles, future_inventory),
            project_provenance_records,
            project_provenance_bytes,
        )
        provenance_path = f"{registry.PROVENANCE_ROOT}/{identifier}.json"
        provenance_before = runtime.read_optional_bytes(
            project, provenance_path, max_bytes=contracts.MAX_CONTRACT_BYTES
        )
        actions.append(
            planning.PlannedAction(
                "write-file",
                provenance_path,
                "Append the approved source, policy, diff, and content history.",
                planning.ExpectedMutation(
                    provenance_path,
                    provenance_before,
                    project_provenance_bytes[identifier],
                    "provenance",
                ),
            )
        )
        actions.append(
            planning.PlannedAction(
                "update-registry",
                registry.PROJECT_REGISTRY_PATH,
                "Update only the project bundle digest; preserve identity metadata.",
                planning.ExpectedMutation(
                    registry.PROJECT_REGISTRY_PATH,
                    project_registry_before,
                    project_registry_after,
                    "registry",
                ),
            )
        )
    else:
        if project != source or role != "maintainer":
            raise MaintenancePlanningError(
                "Plugin imported-skill update requires canonical maintainer context"
            )
        canonical_provenance_bytes[identifier] = runtime.provenance_bytes(
            updated_provenance
        )
        canonical_provenance_records = [
            updated_provenance if item.get("skillId") == identifier else dict(item)
            for item in current.canonical_provenance_records
        ]
        future_snapshot = registry.build_combined_registry_snapshot(
            project,
            current.canonical,
            project_registry,
            project_registry_before,
            current.project_bundles,
            current.provenance_records,
            project_provenance_bytes,
            canonical_bundles=_replace_inventory(
                current.canonical_bundles, future_inventory
            ),
            canonical_provenance_records=canonical_provenance_records,
            canonical_provenance_bytes=canonical_provenance_bytes,
        )
        provenance_path = (
            f"{provenance.CANONICAL_PROVENANCE_ROOT}/{identifier}.json"
        )
        provenance_before = runtime.read_optional_bytes(
            source, provenance_path, max_bytes=contracts.MAX_CONTRACT_BYTES
        )
        actions.append(
            planning.PlannedAction(
                "write-file",
                provenance_path,
                "Append the approved source, policy, diff, and content history.",
                planning.ExpectedMutation(
                    provenance_path,
                    provenance_before,
                    canonical_provenance_bytes[identifier],
                    "provenance",
                ),
            )
        )
    config = runtime.read_optional_bytes(
        project, runtime.CONFIG_PATH, max_bytes=contracts.MAX_CONTRACT_BYTES
    )
    if config is None:
        raise MaintenancePlanningError(f"{runtime.CONFIG_PATH} is missing")
    runtime_actions, checks = runtime.runtime_refresh_actions(
        project, source, future_snapshot, config
    )
    actions.extend(runtime_actions)
    source_paths = tuple(item.source_path for item in future_inventory.files)
    diff_digest = provenance.redacted_diff_digest(changes)
    plan = planning.LifecyclePlan(
        "update",
        role,
        {
            "skillId": identifier,
            "origin": origin_scope,
            "repository": source_identity.get("repository"),
            "path": source_identity.get("path"),
            "oldCommit": old_commit,
            "newCommit": new_commit,
            "oldBundleDigest": current_inventory.digest,
            "newBundleDigest": future_inventory.digest,
            "policyDigest": policy_digest,
            "reviewEvidenceDigest": review_evidence_digest,
            "diffDigest": diff_digest,
            "approver": approver,
            "reviewReference": review_reference,
            "license": license_id,
        },
        runtime.plan_bindings(project, source, current),
        tuple(actions),
        (planning.InventoryCheck(future_inventory.source_path, source_paths),) + checks,
    )
    return plan, changes, origin_scope


def canonical_repository() -> str:
    """Return the normalized public canonical repository identity."""
    value = CANONICAL_SOURCE_ORIGIN.rstrip("/")
    return value[:-4] if value.casefold().endswith(".git") else value
