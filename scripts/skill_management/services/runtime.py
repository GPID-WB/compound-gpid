"""Pure desired-state planning for project import and explicit activation."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

import secure_fs

import cg_project_manifest as manifest_module
import cg_project_projection as projection_module
from skill_management import contracts, planning
from skill_management.providers.github import (
    normalize_public_github_origin,
    normalize_source_path,
)
from skill_management.services import bundles, config_editor, registry


CONFIG_PATH = "compound-gpid.local.md"
ACTIVE_MANIFEST_PATH = ".compound-gpid/active-manifest.json"
OWNERSHIP_PATH = projection_module.OWNERSHIP_STATE_PATH
_FULL_SHA = re.compile(r"^[0-9a-f]{40}$")
_REPARSE_POINT_FLAG = 0x400


class RuntimePlanningError(ValueError):
    """Raised when a complete runtime desired state cannot be planned safely."""


def _read_optional(root: Path, relative: str, *, max_bytes: int = 64 * 1024 * 1024) -> Optional[bytes]:
    try:
        return secure_fs.secure_read_bytes(
            root,
            PurePosixPath(relative),
            reject_hardlinks=True,
            max_bytes=max_bytes,
        )
    except FileNotFoundError:
        return None


def _sha(content: Optional[bytes]) -> str:
    return hashlib.sha256(b"<absent>" if content is None else content).hexdigest()


def _source_revision(source_root: Path) -> str:
    environment = os.environ.copy()
    for name in tuple(environment):
        if name.startswith("GIT_"):
            environment.pop(name, None)
    environment["GIT_TERMINAL_PROMPT"] = "0"
    try:
        result = subprocess.run(
            ["git", "-C", str(source_root), "rev-parse", "--verify", "HEAD^{commit}"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
            stdin=subprocess.DEVNULL,
            env=environment,
        )
    except (OSError, subprocess.TimeoutExpired):
        return "0" * 40
    revision = result.stdout.strip().casefold()
    return revision if result.returncode == 0 and _FULL_SHA.fullmatch(revision) else "0" * 40


def _bundle_inventory_digest(snapshot: registry.CombinedRegistrySnapshot) -> str:
    rows = [
        {"id": item.identifier, "origin": item.origin, "digest": item.digest}
        for item in tuple(snapshot.canonical_bundles) + tuple(snapshot.project_bundles)
    ]
    return hashlib.sha256(contracts.canonical_json_bytes(rows)).hexdigest()


def _bindings(
    project_root: Path,
    source_root: Path,
    snapshot: registry.CombinedRegistrySnapshot,
) -> planning.PlanBindings:
    config = _read_optional(project_root, CONFIG_PATH, max_bytes=contracts.MAX_CONTRACT_BYTES)
    if config is None:
        raise RuntimePlanningError(f"{CONFIG_PATH} is missing")
    manifest = _read_optional(
        project_root, ACTIVE_MANIFEST_PATH, max_bytes=contracts.MAX_CONTRACT_BYTES
    )
    return planning.PlanBindings(
        _source_revision(source_root),
        _sha(config),
        snapshot.canonical_digest,
        snapshot.project_registry_digest,
        _sha(manifest),
        snapshot.provenance_digest,
        hashlib.sha256(contracts.canonical_json_bytes([])).hexdigest(),
        _bundle_inventory_digest(snapshot),
    )


def _future_inventory(
    inventory: bundles.BundleInventory,
) -> bundles.BundleInventory:
    source_path = f".compound-gpid/skills/{inventory.identifier}"
    files = tuple(
        bundles.BundleFile(
            f"{source_path}/{item.bundle_path}",
            item.bundle_path,
            item.content,
            item.sha256,
            item.executable,
        )
        for item in inventory.files
    )
    return bundles.BundleInventory(
        inventory.identifier,
        source_path,
        "project-imported",
        dict(inventory.frontmatter),
        files,
        inventory.digest,
    )


def _project_registry_bytes(records: Sequence[Mapping[str, Any]]) -> bytes:
    value = {
        "schema": "cg-project-skill-registry-v1",
        "schemaVersion": 1,
        "records": sorted((dict(item) for item in records), key=lambda item: item["id"]),
    }
    return contracts.canonical_json_bytes(value) + b"\n"


def _provenance_bytes(record: Mapping[str, Any]) -> bytes:
    return contracts.canonical_json_bytes(dict(record)) + b"\n"


def _current_provenance_bytes(
    project_root: Path,
    snapshot: registry.CombinedRegistrySnapshot,
) -> Dict[str, bytes]:
    result = {}
    for record in snapshot.provenance_records:
        identifier = str(record["skillId"])
        content = _read_optional(
            project_root,
            f"{registry.PROVENANCE_ROOT}/{identifier}.json",
            max_bytes=contracts.MAX_CONTRACT_BYTES,
        )
        if content is None:
            raise RuntimePlanningError(f"Committed provenance is missing: {identifier}")
        result[identifier] = content
    return result


def read_optional_bytes(
    root: Path, relative: str, *, max_bytes: int = 64 * 1024 * 1024
) -> Optional[bytes]:
    """Read one optional managed file through the common secure boundary."""
    return _read_optional(root, relative, max_bytes=max_bytes)


def plan_bindings(
    project_root: Path,
    source_root: Path,
    snapshot: registry.CombinedRegistrySnapshot,
) -> planning.PlanBindings:
    """Return all common plan bindings for a validated current snapshot."""
    return _bindings(project_root, source_root, snapshot)


def current_project_provenance_bytes(
    project_root: Path,
    snapshot: registry.CombinedRegistrySnapshot,
) -> Dict[str, bytes]:
    """Return exact current project provenance bytes by immutable identifier."""
    return _current_provenance_bytes(project_root, snapshot)


def project_registry_bytes(records: Sequence[Mapping[str, Any]]) -> bytes:
    """Serialize one deterministic project registry desired state."""
    return _project_registry_bytes(records)


def provenance_bytes(record: Mapping[str, Any]) -> bytes:
    """Serialize one deterministic append-only provenance record."""
    return _provenance_bytes(record)


def runtime_refresh_actions(
    project_root: Path,
    source_root: Path,
    future_snapshot: registry.CombinedRegistrySnapshot,
    config_bytes: bytes,
    *,
    config_before: Optional[bytes] = None,
) -> Tuple[Tuple[planning.PlannedAction, ...], Tuple[planning.InventoryCheck, ...]]:
    """Plan exact manifest, target, projection, and ownership convergence."""
    return _runtime_actions(
        project_root,
        source_root,
        future_snapshot,
        config_bytes,
        config_before=config_before,
    )


def _current_ownership(project_root: Path) -> Dict[str, Any]:
    content = _read_optional(
        project_root, OWNERSHIP_PATH, max_bytes=contracts.MAX_CONTRACT_BYTES
    )
    if content is None:
        return {"entries": {}}
    try:
        value = contracts.load_contract_bytes(content, source=OWNERSHIP_PATH)
    except ValueError as error:
        raise RuntimePlanningError(f"Projection ownership is invalid: {error}") from error
    errors = manifest_module.validate_ownership_state(value)
    if errors:
        raise RuntimePlanningError("Projection ownership is invalid: " + "; ".join(errors))
    return value


def _managed_projection_entries(
    plan: projection_module.ProjectionPlan,
) -> Tuple[projection_module.ProjectionEntry, ...]:
    return tuple(
        entry
        for entry in plan.entries
        if not (
            entry.platform in plan.source_resident_platforms
            and entry.origin == "plugin-canonical"
        )
    )


def _regular_inventory(project_root: Path, relative_root: str) -> Tuple[str, ...]:
    root = project_root / Path(*PurePosixPath(relative_root).parts)
    try:
        metadata = os.lstat(str(root))
    except FileNotFoundError:
        return ()
    if stat.S_ISLNK(metadata.st_mode) or bool(
        getattr(metadata, "st_file_attributes", 0) & _REPARSE_POINT_FLAG
    ) or not stat.S_ISDIR(metadata.st_mode):
        raise RuntimePlanningError(f"Managed bundle root is unsafe: {relative_root}")
    files = []
    pending = [root]
    while pending:
        directory = pending.pop()
        with os.scandir(str(directory)) as entries:
            ordered = sorted(entries, key=lambda item: item.name, reverse=True)
        for entry in ordered:
            metadata = entry.stat(follow_symlinks=False)
            path = Path(entry.path)
            relative = path.relative_to(project_root).as_posix()
            if stat.S_ISLNK(metadata.st_mode) or bool(
                getattr(metadata, "st_file_attributes", 0) & _REPARSE_POINT_FLAG
            ):
                raise RuntimePlanningError(f"Managed bundle contains a link: {relative}")
            if stat.S_ISDIR(metadata.st_mode):
                pending.append(path)
            elif stat.S_ISREG(metadata.st_mode):
                files.append(relative)
            else:
                raise RuntimePlanningError(
                    f"Managed bundle contains a non-regular entry: {relative}"
                )
    return tuple(sorted(files))


def _projection_inventory_checks(
    project_root: Path,
    entries: Sequence[projection_module.ProjectionEntry],
    *,
    allowed_stale_paths: Sequence[str] = (),
) -> Tuple[planning.InventoryCheck, ...]:
    bundle_roots = {
        str(PurePosixPath(entry.destination).parent)
        for entry in entries
        if entry.kind == "skill"
    }
    checks = []
    for bundle_root in sorted(bundle_roots):
        expected = tuple(
            sorted(
                entry.destination
                for entry in entries
                if PurePosixPath(entry.destination).parts[
                    : len(PurePosixPath(bundle_root).parts)
                ]
                == PurePosixPath(bundle_root).parts
            )
        )
        actual = _regular_inventory(project_root, bundle_root)
        unexpected = sorted(
            set(actual) - set(expected) - set(allowed_stale_paths)
        )
        if unexpected:
            raise RuntimePlanningError(
                "Managed bundle contains unexpected user-owned files: "
                + ", ".join(unexpected[:5])
            )
        checks.append(planning.InventoryCheck(bundle_root, expected))
    return tuple(checks)


def _runtime_actions(
    project_root: Path,
    source_root: Path,
    future_snapshot: registry.CombinedRegistrySnapshot,
    config_bytes: bytes,
    *,
    config_before: Optional[bytes] = None,
) -> Tuple[Tuple[planning.PlannedAction, ...], Tuple[planning.InventoryCheck, ...]]:
    try:
        future_manifest = manifest_module.resolve_active_manifest(
            project_root,
            config_text=config_bytes.decode("utf-8"),
            source_root=source_root,
            combined_snapshot=future_snapshot,
        )
        projection_plan = projection_module.build_projection_plan(
            source_root,
            future_manifest,
            project_root=project_root,
            config_text=config_bytes.decode("utf-8"),
            combined_snapshot=future_snapshot,
        )
    except (OSError, UnicodeError, ValueError) as error:
        raise RuntimePlanningError(f"Desired runtime state is invalid: {error}") from error
    actions = []  # type: List[planning.PlannedAction]
    if config_before is not None and config_before != config_bytes:
        actions.append(
            planning.PlannedAction(
                "update-config",
                CONFIG_PATH,
                "Publish the exact strict explicit-capability config edit.",
                planning.ExpectedMutation(
                    CONFIG_PATH, config_before, config_bytes, "config"
                ),
            )
        )
    manifest_bytes = manifest_module.canonical_manifest_bytes(future_manifest).encode("utf-8")
    manifest_before = _read_optional(
        project_root, ACTIVE_MANIFEST_PATH, max_bytes=contracts.MAX_CONTRACT_BYTES
    )
    if manifest_before != manifest_bytes:
        actions.append(
            planning.PlannedAction(
                "update-manifest",
                ACTIVE_MANIFEST_PATH,
                "Publish the exact active manifest resolved from all bound inputs.",
                planning.ExpectedMutation(
                    ACTIVE_MANIFEST_PATH, manifest_before, manifest_bytes, "manifest"
                ),
            )
        )

    ownership = _current_ownership(project_root)
    previous_entries = ownership.get("entries", {})
    if not isinstance(previous_entries, dict):
        raise RuntimePlanningError("Projection ownership entries are invalid")
    managed_entries = _managed_projection_entries(projection_plan)
    desired_paths = {entry.destination for entry in managed_entries}
    ownership_entries = {}
    generated_group = project_root == source_root
    for entry in managed_entries:
        current = _read_optional(project_root, entry.destination)
        prior = previous_entries.get(entry.destination)
        prior_sha = str(prior.get("sha256", "")) if isinstance(prior, dict) else ""
        if current is not None:
            current_sha = hashlib.sha256(current).hexdigest()
            if current != entry.content and current_sha != prior_sha:
                raise RuntimePlanningError(
                    f"Selected destination is modified or user-owned: {entry.destination}"
                )
        if current != entry.content:
            publish_group = "generated" if generated_group and entry.platform != "copilot" else "projection"
            actions.append(
                planning.PlannedAction(
                    "publish-projection",
                    entry.destination,
                    f"Publish exact {entry.platform} runtime bytes.",
                    planning.ExpectedMutation(
                        entry.destination,
                        current,
                        entry.content,
                        publish_group,
                        entry.executable,
                    ),
                )
            )
        ownership_entries[entry.destination] = {
            "sha256": entry.sha256,
            "platform": entry.platform,
            "source": entry.source,
            "kind": entry.kind,
            "preserved": False,
            "origin": entry.origin,
            "provenanceIdentity": entry.provenance_identity,
        }
    for relative, record in sorted(previous_entries.items()):
        if relative in desired_paths:
            continue
        if not isinstance(relative, str) or not isinstance(record, dict):
            raise RuntimePlanningError("Projection ownership record is malformed")
        current = _read_optional(project_root, relative)
        if current is None:
            continue
        previous_sha = record.get("sha256")
        if hashlib.sha256(current).hexdigest() != previous_sha:
            raise RuntimePlanningError(
                f"Modified stale managed file will not be deleted: {relative}"
            )
        actions.append(
            planning.PlannedAction(
                "publish-projection",
                relative,
                "Delete one stale checksum-owned projection file.",
                planning.ExpectedMutation(relative, current, None, "projection"),
            )
        )
    ownership_value = {
        "schemaVersion": 1,
        "generated": projection_plan.manifest_digest,
        "entries": {
            path: ownership_entries[path] for path in sorted(ownership_entries)
        },
        "activeAdapters": {
            platform: f"managed:{platform}"
            for platform in sorted({entry.platform for entry in managed_entries})
        },
        "warnings": [],
        "note": "Exact lifecycle projection ownership; success requires desired-plan parity.",
    }
    ownership_bytes = contracts.canonical_json_bytes(ownership_value) + b"\n"
    ownership_before = _read_optional(
        project_root, OWNERSHIP_PATH, max_bytes=contracts.MAX_CONTRACT_BYTES
    )
    if ownership_before != ownership_bytes:
        actions.append(
            planning.PlannedAction(
                "verify",
                OWNERSHIP_PATH,
                "Publish exact projection ownership after all host bytes.",
                planning.ExpectedMutation(
                    OWNERSHIP_PATH, ownership_before, ownership_bytes, "ownership"
                ),
            )
        )
    stale_paths = tuple(
        action.mutation.path
        for action in actions
        if action.mutation is not None and action.mutation.after is None
    )
    checks = _projection_inventory_checks(
        project_root, managed_entries, allowed_stale_paths=stale_paths
    )
    return tuple(actions), checks


def plan_project_import(
    project_root: Path,
    source_root: Path,
    candidate: bundles.BundleInventory,
    *,
    origin: str,
    source_path: str,
    commit: str,
    suites: Sequence[str],
    platforms: Sequence[str],
    policy_digest: str = "0" * 64,
    review_evidence_digest: str = "0" * 64,
    license_id: str = "",
    role: str = "consumer",
) -> planning.LifecyclePlan:
    """Plan one approved inactive project import and complete runtime refresh."""
    project = Path(project_root).resolve(strict=True)
    source = Path(source_root).resolve(strict=True)
    normalized_origin = normalize_public_github_origin(origin)
    normalized_source_path = normalize_source_path(source_path)
    if _FULL_SHA.fullmatch(commit) is None:
        raise RuntimePlanningError("Project import commit must be one full SHA")
    if not re.fullmatch(r"[0-9a-f]{64}", policy_digest) or not re.fullmatch(
        r"[0-9a-f]{64}", review_evidence_digest
    ):
        raise RuntimePlanningError("Project import policy and evidence digests are invalid")
    current = registry.load_combined_registry_snapshot(project, source)
    identifier = candidate.identifier
    if current.identifier_reserved(identifier):
        raise RuntimePlanningError(
            f"Project skill identifier already exists or is reserved: {identifier}"
        )
    future_inventory = _future_inventory(candidate)
    if any(item.executable for item in future_inventory.files):
        raise RuntimePlanningError("Imported project skill contains executable content")
    ordered_suites = tuple(item for item in ("cg", "cr") if item in set(suites))
    canonical_platforms = tuple(manifest_module.canonical_platform_ids(source))
    ordered_platforms = tuple(item for item in canonical_platforms if item in set(platforms))
    if not ordered_suites or not ordered_platforms:
        raise RuntimePlanningError("Project import requires eligible suites and platforms")
    record = {
        "id": identifier,
        "origin": "project-imported",
        "owner": "project-local",
        "capability": f"project-skill-{identifier}",
        "activationMode": "explicit-only",
        "sourcePath": future_inventory.source_path,
        "supportedSuites": list(ordered_suites),
        "supportedPlatforms": list(ordered_platforms),
        "admission": "approved",
        "lifecycle": "current",
        "provenanceId": identifier,
        "bundleDigest": future_inventory.digest,
    }
    review_reference = (
        f"{normalized_origin}@{commit}:{normalized_source_path}#"
        f"evidence-sha256={review_evidence_digest}"
    )
    provenance_record = {
        "schema": "cg-skill-provenance-v1",
        "schemaVersion": 1,
        "skillId": identifier,
        "origin": "project-imported",
        "admission": "approved",
        "lifecycle": "current",
        "source": {
            "repository": normalized_origin,
            "path": normalized_source_path,
            "commit": commit,
            "bundleDigest": future_inventory.digest,
        },
        "history": [
            {
                "sequence": 1,
                "event": "imported",
                "commit": commit,
                "bundleDigest": future_inventory.digest,
                "approval": {
                    "actor": "project-user",
                    "reviewReference": review_reference,
                },
            }
        ],
        "migrations": [],
    }
    records = [dict(item) for item in current.project_records] + [record]
    registry_bytes = _project_registry_bytes(records)
    registry_value = json.loads(registry_bytes.decode("utf-8"))
    provenance_records = [dict(item) for item in current.provenance_records] + [
        provenance_record
    ]
    provenance_bytes = _current_provenance_bytes(project, current)
    provenance_bytes[identifier] = _provenance_bytes(provenance_record)
    future_snapshot = registry.build_combined_registry_snapshot(
        project,
        current.canonical,
        registry_value,
        registry_bytes,
        tuple(current.project_bundles) + (future_inventory,),
        provenance_records,
        provenance_bytes,
    )
    actions = []  # type: List[planning.PlannedAction]
    for item in future_inventory.files:
        current_bytes = _read_optional(project, item.source_path)
        if current_bytes is not None:
            raise RuntimePlanningError(f"Project import destination already exists: {item.source_path}")
        actions.append(
            planning.PlannedAction(
                "write-file",
                item.source_path,
                "Publish one admitted inactive project skill resource.",
                planning.ExpectedMutation(
                    item.source_path, None, item.content, "source", False
                ),
            )
        )
    provenance_path = f"{registry.PROVENANCE_ROOT}/{identifier}.json"
    actions.append(
        planning.PlannedAction(
            "write-file",
            provenance_path,
            "Publish append-only project import provenance.",
            planning.ExpectedMutation(
                provenance_path,
                None,
                provenance_bytes[identifier],
                "provenance",
            ),
        )
    )
    current_registry = _read_optional(
        project, registry.PROJECT_REGISTRY_PATH, max_bytes=contracts.MAX_CONTRACT_BYTES
    )
    actions.append(
        planning.PlannedAction(
            "update-registry",
            registry.PROJECT_REGISTRY_PATH,
            "Register the admitted project skill as inactive explicit-only state.",
            planning.ExpectedMutation(
                registry.PROJECT_REGISTRY_PATH,
                current_registry,
                registry_bytes,
                "registry",
            ),
        )
    )
    config = _read_optional(project, CONFIG_PATH, max_bytes=contracts.MAX_CONTRACT_BYTES)
    assert config is not None
    runtime_actions, checks = _runtime_actions(
        project, source, future_snapshot, config
    )
    actions.extend(runtime_actions)
    return planning.LifecyclePlan(
        "import",
        role,
        {
            "origin": normalized_origin,
            "path": normalized_source_path,
            "commit": commit,
            "candidateDigest": candidate.digest,
            "policyDigest": policy_digest,
            "reviewEvidenceDigest": review_evidence_digest,
            "license": license_id,
            "suites": list(ordered_suites),
            "platforms": list(ordered_platforms),
        },
        _bindings(project, source, current),
        tuple(actions),
        checks,
    )


def plan_capability_change(
    project_root: Path,
    source_root: Path,
    capability: str,
    *,
    activate: bool,
    role: str = "consumer",
) -> planning.LifecyclePlan:
    """Plan one explicit capability config/manifest/projection transaction."""
    project = Path(project_root).resolve(strict=True)
    source = Path(source_root).resolve(strict=True)
    snapshot = registry.load_combined_registry_snapshot(project, source)
    config = _read_optional(project, CONFIG_PATH, max_bytes=contracts.MAX_CONTRACT_BYTES)
    if config is None:
        raise RuntimePlanningError(f"{CONFIG_PATH} is missing")
    project_record = snapshot.project_capability_by_id(capability)
    canonical_record = snapshot.canonical.capability_by_id(capability)
    if project_record is None and canonical_record is None:
        raise RuntimePlanningError(f"Unknown capability: {capability}")
    if activate and project_record is not None and project_record.get("lifecycle") != "current":
        raise RuntimePlanningError("A deprecated project skill cannot be newly activated")
    if activate and canonical_record is not None:
        owner = canonical_record.get("owningModule")
        for inventory in snapshot.canonical_bundles:
            inventory_owner = snapshot.canonical.owner_for_asset(
                f"{inventory.source_path}/SKILL.md"
            )
            lifecycle_record = snapshot.canonical_provenance_by_id(
                inventory.identifier
            )
            if (
                inventory_owner == owner
                and lifecycle_record is not None
                and lifecycle_record.get("lifecycle") != "current"
            ):
                raise RuntimePlanningError(
                    "A capability containing a deprecated canonical skill cannot be newly activated"
                )
    try:
        edit = config_editor.plan_capability_edit(
            config, capability, activate=activate
        )
    except config_editor.ConfigEditError as error:
        raise RuntimePlanningError(str(error)) from error
    if not edit.changed:
        return planning.LifecyclePlan(
            "activate" if activate else "deactivate",
            role,
            {"capability": capability, "noop": True},
            _bindings(project, source, snapshot),
            (),
        )
    try:
        future_manifest = manifest_module.resolve_active_manifest(
            project,
            config_text=edit.after.decode("utf-8"),
            source_root=source,
            combined_snapshot=snapshot,
        )
    except (UnicodeError, ValueError) as error:
        raise RuntimePlanningError(f"Capability edit does not resolve strictly: {error}") from error
    if not activate and canonical_record is not None:
        if capability in future_manifest["selection"].get("derivedCapabilities", []):
            raise RuntimePlanningError(
                f"Capability {capability} remains selector-derived and cannot be deactivated"
            )
        owner = canonical_record.get("owningModule")
        if owner in future_manifest["selection"].get("moduleClosure", []):
            raise RuntimePlanningError(
                f"Capability {capability} remains dependency-required and cannot be deactivated"
            )
    runtime_actions, checks = _runtime_actions(
        project,
        source,
        snapshot,
        edit.after,
        config_before=config,
    )
    return planning.LifecyclePlan(
        "activate" if activate else "deactivate",
        role,
        {"capability": capability, "activate": activate},
        _bindings(project, source, snapshot),
        runtime_actions,
        checks,
    )
