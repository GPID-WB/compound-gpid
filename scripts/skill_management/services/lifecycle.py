"""Pure deprecation and reference-safe removal desired-state planning."""
from __future__ import annotations

import hashlib
import json
import os
import stat
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from skill_management import contracts, paths as path_policy, planning
from skill_management.context import CANONICAL_SOURCE_ORIGIN
from skill_management.services import (
    bundles,
    provenance,
    references,
    registry,
    release_attestation,
    runtime,
)


class LifecyclePlanningError(ValueError):
    """Raised when lifecycle evidence cannot prove one safe desired state."""


@dataclass(frozen=True)
class DeprecationDesiredState:
    """Complete deprecation plan and public lifecycle evidence."""

    plan: planning.LifecyclePlan
    origin: str
    active_warning: bool
    deprecated_record_digest: str


@dataclass(frozen=True)
class RemovalDesiredState:
    """Complete removal plan and public destructive-operation evidence."""

    plan: planning.LifecyclePlan
    origin: str
    tombstone_digest: str
    grace_evidence: str
    removed_paths: Tuple[str, ...]
    remaining_references: Tuple[str, ...]


@dataclass(frozen=True)
class MigrationRecord:
    """One validated versioned migration and its exact source digest."""

    path: str
    value: Mapping[str, Any]
    digest: str


def _canonical_json_file(value: Mapping[str, Any]) -> bytes:
    return (
        json.dumps(value, indent=2, ensure_ascii=False, sort_keys=False) + "\n"
    ).encode("utf-8")


def _project_registry_state(project_root: Path) -> Tuple[Dict[str, Any], bytes]:
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
        raise LifecyclePlanningError(str(error)) from error
    return value, content


def _canonical_provenance_bytes(
    source_root: Path, snapshot: registry.CombinedRegistrySnapshot
) -> Dict[str, bytes]:
    result = {}
    for record in snapshot.canonical_provenance_records:
        identifier = str(record["skillId"])
        path = f"{provenance.CANONICAL_PROVENANCE_ROOT}/{identifier}.json"
        content = runtime.read_optional_bytes(
            source_root, path, max_bytes=contracts.MAX_CONTRACT_BYTES
        )
        if content is None:
            raise LifecyclePlanningError(
                f"Committed canonical provenance is missing: {identifier}"
            )
        result[identifier] = content
    return result


def _target(
    snapshot: registry.CombinedRegistrySnapshot, identifier: str
) -> Tuple[str, bundles.BundleInventory, Optional[Dict[str, Any]], Dict[str, Any]]:
    project_record = snapshot.project_record_by_id(identifier)
    if project_record is not None:
        inventory = snapshot.project_bundle_by_id(identifier)
        if inventory is None:
            raise LifecyclePlanningError(f"Project bundle is missing: {identifier}")
        return (
            "project-imported",
            inventory,
            project_record,
            snapshot.provenance_by_id(identifier),
        )
    inventory = snapshot.canonical_bundle_by_id(identifier)
    if inventory is None:
        tombstone = snapshot.provenance_record_by_id(identifier)
        if tombstone is not None and tombstone.get("lifecycle") == "removed":
            raise LifecyclePlanningError(
                f"Skill identifier is permanently reserved by a tombstone: {identifier}"
            )
        raise LifecyclePlanningError(f"Unknown skill identifier: {identifier}")
    record = snapshot.canonical_provenance_by_id(identifier)
    if record is None:
        record = {}
    return "plugin-canonical", inventory, None, record


def _current_canonical_record(
    snapshot: registry.CombinedRegistrySnapshot,
    inventory: bundles.BundleInventory,
    record: Mapping[str, Any],
    approver: str,
    review_reference: str,
    revision: str,
) -> Dict[str, Any]:
    if record:
        return dict(record)
    repository = CANONICAL_SOURCE_ORIGIN
    if repository.casefold().endswith(".git"):
        repository = repository[:-4]
    return provenance.provenance_record(
        inventory.identifier,
        "plugin-canonical",
        repository,
        inventory.source_path,
        revision,
        inventory.digest,
        "created",
        approver,
        review_reference,
    )


def _successor_record(
    snapshot: registry.CombinedRegistrySnapshot,
    successor_id: str,
    origin: str,
) -> Optional[Mapping[str, Any]]:
    if origin == "project-imported":
        record = snapshot.project_record_by_id(successor_id)
        if record is None or record.get("lifecycle") != "current":
            return None
        return record
    inventory = snapshot.canonical_bundle_by_id(successor_id)
    if inventory is None:
        return None
    record = snapshot.canonical_provenance_by_id(successor_id)
    if record is not None and record.get("lifecycle") != "current":
        return None
    return record or {"skillId": successor_id, "lifecycle": "current"}


def _validate_successor(
    snapshot: registry.CombinedRegistrySnapshot,
    identifier: str,
    successor_id: str,
    origin: str,
) -> None:
    if identifier == successor_id:
        raise LifecyclePlanningError("A skill cannot succeed itself")
    if _successor_record(snapshot, successor_id, origin) is None:
        other_origin_exists = (
            snapshot.project_record_by_id(successor_id) is not None
            or snapshot.canonical_bundle_by_id(successor_id) is not None
        )
        if other_origin_exists:
            raise LifecyclePlanningError(
                "A successor must be current and from the same origin"
            )
        raise LifecyclePlanningError("Successor is missing, deprecated, or removed")
    edges = {}  # type: Dict[str, str]
    for record in snapshot.project_records:
        if record.get("lifecycle") == "deprecated" and isinstance(
            record.get("successorId"), str
        ):
            edges[str(record["id"])] = str(record["successorId"])
    for record in snapshot.canonical_provenance_records:
        if record.get("lifecycle") == "deprecated" and isinstance(
            record.get("successorId"), str
        ):
            edges[str(record["skillId"])] = str(record["successorId"])
    edges[identifier] = successor_id
    current = identifier
    seen = set()
    while current in edges:
        if current in seen:
            raise LifecyclePlanningError("Successor graph contains a cycle")
        seen.add(current)
        current = edges[current]


def _active_state(
    project_root: Path,
    source_root: Path,
    snapshot: registry.CombinedRegistrySnapshot,
    identifier: str,
    origin: str,
) -> bool:
    import cg_project_manifest as manifest_module

    try:
        manifest = manifest_module.resolve_active_manifest(
            project_root,
            source_root=source_root,
            combined_snapshot=snapshot,
        )
    except (OSError, UnicodeError, ValueError) as error:
        raise LifecyclePlanningError(
            f"Cannot resolve current active state: {error}"
        ) from error
    if origin == "project-imported":
        return identifier in set(
            manifest.get("selection", {})
            .get("selectedProjectSkills", {})
            .values()
        )
    inventory = snapshot.canonical_bundle_by_id(identifier)
    assert inventory is not None
    owner = snapshot.canonical.owner_for_asset(
        f"{inventory.source_path}/SKILL.md"
    )
    return owner in set(manifest.get("selection", {}).get("moduleClosure", []))


def _bindings_with_references(
    project_root: Path,
    source_root: Path,
    snapshot: registry.CombinedRegistrySnapshot,
    digest: str,
) -> planning.PlanBindings:
    current = runtime.plan_bindings(project_root, source_root, snapshot)
    return planning.PlanBindings(
        current.source_revision,
        current.configuration_digest,
        current.canonical_registry_digest,
        current.project_registry_digest,
        current.manifest_digest,
        current.provenance_digest,
        digest,
        current.bundle_inventory_digest,
    )


def _provenance_action(
    path: str,
    before: Optional[bytes],
    after: bytes,
    description: str,
    *,
    kind: str = "write-file",
) -> planning.PlannedAction:
    return planning.PlannedAction(
        kind,
        path,
        description,
        planning.ExpectedMutation(path, before, after, "provenance"),
    )


def plan_deprecation(
    project_root: Path,
    source_root: Path,
    identifier: str,
    successor_id: str,
    approver: str,
    review_reference: str,
    *,
    role: str,
) -> DeprecationDesiredState:
    """Plan one same-origin acyclic deprecation through the common transaction."""
    provenance.validate_audit_metadata(approver, review_reference)
    project = Path(project_root).resolve(strict=True)
    source = Path(source_root).resolve(strict=True)
    snapshot = registry.load_combined_registry_snapshot(project, source)
    origin, inventory, project_record, current_record = _target(snapshot, identifier)
    if current_record and current_record.get("lifecycle") != "current":
        raise LifecyclePlanningError("Only a current skill can be deprecated")
    _validate_successor(snapshot, identifier, successor_id, origin)
    if origin == "plugin-canonical" and (role != "maintainer" or project != source):
        raise LifecyclePlanningError(
            "Plugin deprecation requires canonical maintainer context"
        )
    reference_target = next(
        item
        for item in references.targets_from_snapshot(snapshot)
        if item.identifier == identifier
    )
    reference_report = references.scan_references(
        project, source, (reference_target,)
    )
    if any(item.severity == "error" for item in reference_report.findings):
        raise LifecyclePlanningError(
            "Reference inventory is incomplete or unsafe: "
            + reference_report.findings[0].message
        )
    current_bindings = runtime.plan_bindings(project, source, snapshot)
    if origin == "plugin-canonical":
        current_record = _current_canonical_record(
            snapshot,
            inventory,
            current_record,
            approver,
            review_reference,
            current_bindings.source_revision,
        )
    deprecated = provenance.append_deprecation(
        current_record,
        successor_id,
        approver,
        review_reference,
        current_bindings.source_revision,
    )
    actions = []  # type: List[planning.PlannedAction]
    project_registry, project_registry_before = _project_registry_state(project)
    project_provenance_bytes = runtime.current_project_provenance_bytes(
        project, snapshot
    )
    canonical_provenance_bytes = _canonical_provenance_bytes(source, snapshot)
    if origin == "project-imported":
        records = [dict(item) for item in snapshot.project_records]
        for record in records:
            if record.get("id") == identifier:
                record["lifecycle"] = "deprecated"
                record["successorId"] = successor_id
        registry_after = runtime.project_registry_bytes(records)
        project_registry = {
            "schema": "cg-project-skill-registry-v1",
            "schemaVersion": 1,
            "records": sorted(records, key=lambda item: item["id"]),
        }
        project_provenance_bytes[identifier] = runtime.provenance_bytes(deprecated)
        provenance_records = [
            deprecated if item.get("skillId") == identifier else dict(item)
            for item in snapshot.provenance_records
        ]
        future = registry.build_combined_registry_snapshot(
            project,
            snapshot.canonical,
            project_registry,
            registry_after,
            snapshot.project_bundles,
            provenance_records,
            project_provenance_bytes,
        )
        provenance_path = f"{registry.PROVENANCE_ROOT}/{identifier}.json"
        actions.append(
            _provenance_action(
                provenance_path,
                runtime.read_optional_bytes(
                    project, provenance_path, max_bytes=contracts.MAX_CONTRACT_BYTES
                ),
                project_provenance_bytes[identifier],
                "Publish the immutable project deprecation record.",
            )
        )
        actions.append(
            planning.PlannedAction(
                "update-registry",
                registry.PROJECT_REGISTRY_PATH,
                "Record the project successor and deprecated lifecycle state.",
                planning.ExpectedMutation(
                    registry.PROJECT_REGISTRY_PATH,
                    project_registry_before,
                    registry_after,
                    "registry",
                ),
            )
        )
    else:
        canonical_provenance_bytes[identifier] = runtime.provenance_bytes(deprecated)
        provenance_records = [
            deprecated if item.get("skillId") == identifier else dict(item)
            for item in snapshot.canonical_provenance_records
        ]
        if not any(item.get("skillId") == identifier for item in provenance_records):
            provenance_records.append(deprecated)
        future = registry.build_combined_registry_snapshot(
            project,
            snapshot.canonical,
            project_registry,
            project_registry_before,
            snapshot.project_bundles,
            snapshot.provenance_records,
            project_provenance_bytes,
            canonical_bundles=snapshot.canonical_bundles,
            canonical_provenance_records=provenance_records,
            canonical_provenance_bytes=canonical_provenance_bytes,
        )
        provenance_path = (
            f"{provenance.CANONICAL_PROVENANCE_ROOT}/{identifier}.json"
        )
        actions.append(
            _provenance_action(
                provenance_path,
                runtime.read_optional_bytes(
                    source, provenance_path, max_bytes=contracts.MAX_CONTRACT_BYTES
                ),
                canonical_provenance_bytes[identifier],
                "Publish the immutable canonical deprecation record.",
            )
        )
    config = runtime.read_optional_bytes(
        project, runtime.CONFIG_PATH, max_bytes=contracts.MAX_CONTRACT_BYTES
    )
    if config is None:
        raise LifecyclePlanningError(f"{runtime.CONFIG_PATH} is missing")
    refresh, checks = runtime.runtime_refresh_actions(project, source, future, config)
    actions.extend(refresh)
    active_warning = _active_state(
        project, source, snapshot, identifier, origin
    )
    plan = planning.LifecyclePlan(
        "deprecate",
        role,
        {
            "skillId": identifier,
            "successorId": successor_id,
            "origin": origin,
            "approver": approver,
            "reviewReference": review_reference,
            "deprecatedRecordDigest": deprecated["deprecatedRecordDigest"],
            "activeWarning": active_warning,
        },
        _bindings_with_references(
            project, source, snapshot, reference_report.digest
        ),
        tuple(actions),
        checks,
    )
    return DeprecationDesiredState(
        plan,
        origin,
        active_warning,
        str(deprecated["deprecatedRecordDigest"]),
    )


def _migration_schema() -> Dict[str, Any]:
    return contracts.load_contract(
        Path(__file__).resolve().parents[3],
        contracts.CONTRACTS_ROOT / "migration-v1.schema.json",
    )


def load_migrations(
    project_root: Path,
    paths: Sequence[str],
    identifier: str,
) -> Tuple[MigrationRecord, ...]:
    """Load exact versioned migration records without following links."""
    root = Path(project_root).resolve(strict=True)
    schema = _migration_schema()
    records = []
    seen_ids = set()
    seen_edits = {}  # type: Dict[Tuple[str, ...], str]
    for relative in sorted(paths):
        try:
            content = runtime.read_optional_bytes(
                root, relative, max_bytes=contracts.MAX_CONTRACT_BYTES
            )
        except (OSError, ValueError) as error:
            raise LifecyclePlanningError(
                f"Migration record is unsafe: {relative}: {error}"
            ) from error
        if content is None:
            raise LifecyclePlanningError(f"Migration record is missing: {relative}")
        try:
            value = contracts.load_contract_bytes(content, source=relative)
        except ValueError as error:
            raise LifecyclePlanningError(str(error)) from error
        findings = contracts.validate_instance(value, schema)
        if findings:
            raise LifecyclePlanningError(
                f"Migration record is invalid: {relative}: {findings[0].code}"
            )
        if value.get("skillId") != identifier:
            raise LifecyclePlanningError(
                f"Migration record targets another skill: {relative}"
            )
        provenance.validate_audit_metadata(
            str(value["reviewer"]), str(value["approvalReference"])
        )
        migration_id = str(value["id"])
        if migration_id in seen_ids:
            raise LifecyclePlanningError("Migration identifiers must be unique")
        seen_ids.add(migration_id)
        for edit in value["edits"]:
            edit_path = str(edit["path"])
            portable = path_policy.portable_path_key(edit_path)
            prior = seen_edits.get(portable)
            if prior is not None:
                raise LifecyclePlanningError(
                    f"Migration paths collide portably: {prior} and {edit_path}"
                )
            seen_edits[portable] = edit_path
        records.append(
            MigrationRecord(relative, value, hashlib.sha256(content).hexdigest())
        )
    return tuple(records)


def _migration_actions(
    project_root: Path,
    migrations: Sequence[MigrationRecord],
) -> Tuple[planning.PlannedAction, ...]:
    actions = []
    for migration in migrations:
        for edit in migration.value["edits"]:
            path = str(edit["path"])
            if not contracts.migration_path_allowed(path):
                raise LifecyclePlanningError(
                    "Migration can edit only bounded project documentation or "
                    f"reference text files: {path}"
                )
            try:
                current = runtime.read_optional_bytes(
                    project_root,
                    path,
                    max_bytes=references.MAX_REFERENCE_FILE_BYTES,
                )
            except (OSError, ValueError) as error:
                raise LifecyclePlanningError(
                    f"Migration source path is not bounded regular text: {path}: {error}"
                ) from error
            if current is None:
                raise LifecyclePlanningError(f"Migration source path is missing: {path}")
            try:
                current.decode("utf-8-sig")
                metadata = os.lstat(project_root / PurePosixPath(path))
            except (OSError, UnicodeError) as error:
                raise LifecyclePlanningError(
                    f"Migration source path is not bounded regular UTF-8 text: {path}: {error}"
                ) from error
            if stat.S_IMODE(metadata.st_mode) & 0o111:
                raise LifecyclePlanningError(
                    f"Migration cannot edit an executable file: {path}"
                )
            expected = str(edit["expectedSha256"])
            if hashlib.sha256(current).hexdigest() != expected:
                raise LifecyclePlanningError(
                    f"Migration source digest is stale: {path}"
                )
            replacement = str(edit["replacement"]).encode("utf-8")
            if len(replacement) > references.MAX_REFERENCE_FILE_BYTES:
                raise LifecyclePlanningError(
                    f"Migration replacement exceeds the reference byte ceiling: {path}"
                )
            if replacement == current:
                raise LifecyclePlanningError(f"Migration has no byte change: {path}")
            actions.append(
                planning.PlannedAction(
                    "apply-migration",
                    path,
                    f"Apply reviewed digest-bound migration {migration.value['id']}.",
                    planning.ExpectedMutation(
                        path, current, replacement, "source", False
                    ),
                )
            )
    return tuple(actions)


def _inventory_delete_actions(
    inventory: bundles.BundleInventory,
) -> Tuple[planning.PlannedAction, ...]:
    return tuple(
        planning.PlannedAction(
            "delete-file",
            item.source_path,
            "Delete one exact registered skill source resource.",
            planning.ExpectedMutation(
                item.source_path, item.content, None, "source", False
            ),
        )
        for item in inventory.files
    )


def _canonical_registry_after_removal(
    snapshot: registry.CombinedRegistrySnapshot,
    inventory: bundles.BundleInventory,
) -> Tuple[registry.RegistrySnapshot, bytes]:
    value = snapshot.canonical.to_dict()
    skill_path = f"{inventory.source_path}/SKILL.md"
    owner_id = snapshot.canonical.owner_for_asset(skill_path)
    future_inventories = tuple(
        item
        for item in snapshot.canonical_bundles
        if item.identifier != inventory.identifier
    )
    future_assets = {
        item.source_path for bundle in future_inventories for item in bundle.files
    }
    for module in value.get("modules", []):
        if not isinstance(module, dict) or module.get("id") != owner_id:
            continue
        retained = []
        for pattern in module.get("ownedAssets", []):
            matches_target = any(
                registry.glob_match(pattern, item.source_path)
                for item in inventory.files
            )
            matches_future = any(
                registry.glob_match(pattern, path) for path in future_assets
            )
            if matches_target and not matches_future:
                continue
            retained.append(pattern)
        module["ownedAssets"] = retained
    owner_has_future_skill = False
    for future in future_inventories:
        future_owner = snapshot.canonical.owner_for_asset(
            f"{future.source_path}/SKILL.md"
        )
        if future_owner == owner_id:
            owner_has_future_skill = True
            break
    if not owner_has_future_skill:
        value["capabilities"] = [
            item
            for item in value.get("capabilities", [])
            if not isinstance(item, dict) or item.get("owningModule") != owner_id
        ]
    content = _canonical_json_file(value)
    return (
        registry.RegistrySnapshot.from_data(
            snapshot.canonical.source_root,
            value,
            digest=hashlib.sha256(content).hexdigest(),
        ),
        content,
    )


def _staged_map(
    project_root: Path,
    source_root: Path,
    actions: Sequence[planning.PlannedAction],
) -> Dict[Tuple[str, str], Optional[bytes]]:
    root_kind = "project" if project_root == source_root else "project"
    return {
        (root_kind, action.mutation.path): action.mutation.after
        for action in actions
        if action.mutation is not None
    }


def _grace(
    project: Path,
    source: Path,
    origin: str,
    identifier: str,
    record: Mapping[str, Any],
    inventory: bundles.BundleInventory,
    *,
    grace_exception: bool,
    grace_reason: str,
    review_reference: str,
) -> Tuple[str, str]:
    digest = str(record["deprecatedRecordDigest"])
    if origin == "plugin-canonical":
        if grace_exception:
            raise LifecyclePlanningError(
                "A grace exception cannot replace plugin release attestations"
            )
        evidence = release_attestation.verify_plugin_grace(
            source,
            identifier,
            digest,
            f"{provenance.CANONICAL_PROVENANCE_ROOT}/{identifier}.json",
            inventory.source_path,
        )
        return evidence.summary, evidence.removed_revision
    if release_attestation.project_is_git_repository(project):
        if grace_exception:
            raise LifecyclePlanningError(
                "A Git project cannot bypass descendant revision grace"
            )
        evidence = release_attestation.verify_project_grace(
            project,
            identifier,
            digest,
            f"{registry.PROVENANCE_ROOT}/{identifier}.json",
            inventory.source_path,
        )
        return evidence.summary, evidence.removed_revision
    if not grace_exception or not grace_reason.strip():
        raise LifecyclePlanningError(
            "A non-Git project requires an explicit project-specific grace exception"
        )
    exception_digest = hashlib.sha256(
        contracts.canonical_json_bytes(
            {
                "skillId": identifier,
                "reason": grace_reason,
                "reviewReference": review_reference,
            }
        )
    ).hexdigest()
    return (
        f"project-grace-exception:{exception_digest}",
        f"grace-exception:{exception_digest}",
    )


def plan_removal(
    project_root: Path,
    source_root: Path,
    identifier: str,
    approver: str,
    review_reference: str,
    migration_paths: Sequence[str],
    *,
    role: str,
    grace_exception: bool = False,
    grace_reason: str = "",
) -> RemovalDesiredState:
    """Plan exact owned-only removal after a staged zero-reference rescan."""
    provenance.validate_audit_metadata(approver, review_reference)
    project = Path(project_root).resolve(strict=True)
    source = Path(source_root).resolve(strict=True)
    snapshot = registry.load_combined_registry_snapshot(project, source)
    origin, inventory, project_record, current_record = _target(snapshot, identifier)
    if not current_record or current_record.get("lifecycle") != "deprecated":
        raise LifecyclePlanningError("Removal requires a deprecated skill")
    successor_id = str(current_record.get("successorId", ""))
    _validate_successor(snapshot, identifier, successor_id, origin)
    if _active_state(project, source, snapshot, identifier, origin):
        raise LifecyclePlanningError(
            "Removal is blocked while the deprecated skill is active"
        )
    if origin == "plugin-canonical" and (role != "maintainer" or project != source):
        raise LifecyclePlanningError(
            "Plugin removal requires canonical maintainer context"
        )
    grace_summary, removed_revision = _grace(
        project,
        source,
        origin,
        identifier,
        current_record,
        inventory,
        grace_exception=grace_exception,
        grace_reason=grace_reason,
        review_reference=review_reference,
    )
    migrations = load_migrations(project, migration_paths, identifier)
    target = next(
        item
        for item in references.targets_from_snapshot(snapshot)
        if item.identifier == identifier
    )
    current_references = references.scan_references(project, source, (target,))
    if any(item.severity == "error" for item in current_references.findings):
        raise LifecyclePlanningError(
            "Reference inventory is incomplete or unsafe: "
            + current_references.findings[0].message
        )
    removed_record = provenance.append_removal(
        current_record,
        removed_revision,
        approver,
        review_reference,
        tuple(
            {"id": item.value["id"], "digest": item.digest}
            for item in migrations
        ),
    )
    actions = list(_inventory_delete_actions(inventory))
    project_registry, project_registry_before = _project_registry_state(project)
    project_provenance_bytes = runtime.current_project_provenance_bytes(
        project, snapshot
    )
    canonical_provenance_bytes = _canonical_provenance_bytes(source, snapshot)
    if origin == "project-imported":
        records = [
            dict(item) for item in snapshot.project_records if item.get("id") != identifier
        ]
        registry_after = runtime.project_registry_bytes(records)
        project_registry = {
            "schema": "cg-project-skill-registry-v1",
            "schemaVersion": 1,
            "records": sorted(records, key=lambda item: item["id"]),
        }
        project_provenance_bytes[identifier] = runtime.provenance_bytes(removed_record)
        provenance_records = [
            removed_record if item.get("skillId") == identifier else dict(item)
            for item in snapshot.provenance_records
        ]
        future = registry.build_combined_registry_snapshot(
            project,
            snapshot.canonical,
            project_registry,
            registry_after,
            tuple(
                item for item in snapshot.project_bundles if item.identifier != identifier
            ),
            provenance_records,
            project_provenance_bytes,
        )
        provenance_path = f"{registry.PROVENANCE_ROOT}/{identifier}.json"
        actions.append(
            _provenance_action(
                provenance_path,
                runtime.read_optional_bytes(
                    project, provenance_path, max_bytes=contracts.MAX_CONTRACT_BYTES
                ),
                project_provenance_bytes[identifier],
                "Publish the immutable project tombstone.",
                kind="write-tombstone",
            )
        )
        actions.append(
            planning.PlannedAction(
                "update-registry",
                registry.PROJECT_REGISTRY_PATH,
                "Remove only the deprecated project registry record.",
                planning.ExpectedMutation(
                    registry.PROJECT_REGISTRY_PATH,
                    project_registry_before,
                    registry_after,
                    "registry",
                ),
            )
        )
    else:
        future_registry, registry_after = _canonical_registry_after_removal(
            snapshot, inventory
        )
        registry_before = runtime.read_optional_bytes(
            source,
            registry.MODULE_REGISTRY_PATH,
            max_bytes=contracts.MAX_CONTRACT_BYTES,
        )
        if registry_before is None:
            raise LifecyclePlanningError("Canonical module registry is missing")
        canonical_provenance_bytes[identifier] = runtime.provenance_bytes(
            removed_record
        )
        provenance_records = [
            removed_record if item.get("skillId") == identifier else dict(item)
            for item in snapshot.canonical_provenance_records
        ]
        future = registry.build_combined_registry_snapshot(
            project,
            future_registry,
            project_registry,
            project_registry_before,
            snapshot.project_bundles,
            snapshot.provenance_records,
            project_provenance_bytes,
            canonical_bundles=tuple(
                item
                for item in snapshot.canonical_bundles
                if item.identifier != identifier
            ),
            canonical_provenance_records=provenance_records,
            canonical_provenance_bytes=canonical_provenance_bytes,
        )
        provenance_path = (
            f"{provenance.CANONICAL_PROVENANCE_ROOT}/{identifier}.json"
        )
        actions.append(
            _provenance_action(
                provenance_path,
                runtime.read_optional_bytes(
                    source, provenance_path, max_bytes=contracts.MAX_CONTRACT_BYTES
                ),
                canonical_provenance_bytes[identifier],
                "Publish the immutable canonical tombstone.",
                kind="write-tombstone",
            )
        )
        if registry_before != registry_after:
            actions.append(
                planning.PlannedAction(
                    "update-registry",
                    registry.MODULE_REGISTRY_PATH,
                    "Remove only ownership patterns that no future asset uses.",
                    planning.ExpectedMutation(
                        registry.MODULE_REGISTRY_PATH,
                        registry_before,
                        registry_after,
                        "registry",
                    ),
                )
            )
    migration_actions = _migration_actions(project, migrations)
    actions = list(migration_actions) + actions
    config = runtime.read_optional_bytes(
        project, runtime.CONFIG_PATH, max_bytes=contracts.MAX_CONTRACT_BYTES
    )
    if config is None:
        raise LifecyclePlanningError(f"{runtime.CONFIG_PATH} is missing")
    refresh, checks = runtime.runtime_refresh_actions(project, source, future, config)
    actions.extend(refresh)
    staged = _staged_map(project, source, actions)
    staged_report = references.scan_references(
        project, source, (target,), staged=staged
    )
    if any(item.severity == "error" for item in staged_report.findings):
        raise LifecyclePlanningError(
            "Staged reference inventory is incomplete or unsafe: "
            + staged_report.findings[0].message
        )
    remaining = tuple(
        sorted(
            {
                f"{item.root}:{item.path}:{item.line}"
                for item in staged_report.active
            }
        )
    )
    if remaining:
        raise LifecyclePlanningError(
            "Removal requires zero active references after staged migrations: "
            + ", ".join(remaining[:5])
        )
    source_paths = tuple(item.source_path for item in inventory.files)
    removal_check = planning.InventoryCheck(inventory.source_path, ())
    tombstone_digest = hashlib.sha256(
        contracts.canonical_json_bytes(removed_record["tombstone"])
    ).hexdigest()
    plan = planning.LifecyclePlan(
        "remove",
        role,
        {
            "skillId": identifier,
            "origin": origin,
            "successorId": successor_id,
            "approver": approver,
            "reviewReference": review_reference,
            "migrationDigests": [item.digest for item in migrations],
            "graceEvidence": grace_summary,
            "graceException": grace_exception,
            "graceReason": grace_reason,
            "tombstoneDigest": tombstone_digest,
            "stagedReferenceDigest": staged_report.digest,
        },
        _bindings_with_references(
            project, source, snapshot, current_references.digest
        ),
        tuple(actions),
        (removal_check,) + checks,
    )
    return RemovalDesiredState(
        plan,
        origin,
        tombstone_digest,
        grace_summary,
        tuple(sorted(source_paths)),
        remaining,
    )
