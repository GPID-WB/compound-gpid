#!/usr/bin/env python3
"""cg-project-projection — Manifest-driven project-local platform projection.

Renders a deterministic, side-effect-free projection plan from the validated
active manifest (``.compound-gpid/active-manifest.json``) plus the canonical
``.github/`` source, then publishes it through a journaled, recoverable
per-root activation transaction into the selected project root.

Design invariants:

- The plan reads **only** the validated active manifest for selection; raw
  project config is never re-parsed at publish time. Selected platform ids come
  exclusively from the manifest's canonical ordered set.
- The canonical renderer (``cg_generate_targets``) stays the single source of
  output bytes. This module only defines the *source-root / output-root*
  boundary and the durable per-root activation transaction.
- Every destination path and SHA-256 is enumerated before any write
  (pure ``ProjectionPlan``); publication is a separate, journaled apply step.
- The target mapping is used only to validate eligibility and output layout
  (declared managed and optional user roots), never to choose selection.

Usage:
    python scripts/cg_project_projection.py --project-root <path> --plan
    python scripts/cg_project_projection.py --project-root <path> --stage
    python scripts/cg_project_projection.py --project-root <path> --publish
    python scripts/cg_project_projection.py --project-root <path> --recover
    python scripts/cg_project_projection.py --project-root <path> --verify

Exit codes:
    0  Success.
    1  Fatal error (planning, staging, publication, recovery, or validation).
    2  Missing or invalid project root.
"""
from __future__ import annotations

import sys

if sys.version_info < (3, 8):
    print(
        f"cg-project-projection requires Python 3.8+; found {sys.version.split()[0]}",
        file=sys.stderr,
    )
    sys.exit(1)

import argparse
import hashlib
import json
import os
import re
import stat
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Dict, Mapping, Optional, Sequence, Tuple
import uuid

_UUID_HEX_PATTERN = re.compile(r"^[0-9a-f]{32}$")

_scripts_dir = str(Path(__file__).parent)
if _scripts_dir not in sys.path:
    sys.path.insert(0, _scripts_dir)

import cg_generate_targets as generator  # noqa: E402
import cg_project_manifest as manifest_module  # noqa: E402
import cg_context_budget as budget  # noqa: E402
import secure_fs  # noqa: E402
from skill_management.services import registry as registry_service  # noqa: E402

ACTIVE_MANIFEST_PATH = ".compound-gpid/active-manifest.json"
OWNERSHIP_STATE_PATH = ".compound-gpid/projection-ownership.json"
TRANSACTION_JOURNAL_PATH = ".compound-gpid/projection-transaction.json"
TARGET_MAPPING_RELATIVE = ".github/shared/target-mapping.json"
STAGING_DIRNAME = ".compound-gpid/staging"
GENERATIONS_DIRNAME = ".compound-gpid/generations"
ACTIVE_POINTER_DIRNAME = ".compound-gpid/active"
RETIRED_DIRNAME = ".compound-gpid/retired"
COPILOT_SKILL_ROOT = ".github/skills"
COPILOT_MIGRATION_BACKUP = ".compound-gpid/copilot-skills-link.previous"

SHA256_PATTERN = set("0123456789abcdef")
MAX_MANAGED_STATE_BYTES = 8 * 1024 * 1024


class ProjectionError(ValueError):
    """Raised when a projection plan or publication step is unsafe or invalid."""


@dataclass(frozen=True)
class ProjectionEntry:
    """One fully planned project-local output (mirrors generator.OutputEntry)."""

    platform: str
    destination: str
    source: str
    kind: str
    content: bytes
    sha256: str
    executable: bool
    origin: str
    provenance_identity: str


@dataclass(frozen=True)
class ProjectionPlan:
    """Pure, deterministic plan: exact destinations and hashes before any write."""

    manifest_digest: str
    desired_plan_digest: str
    platforms: Tuple[str, ...]
    entries: Tuple[ProjectionEntry, ...]
    by_platform: Mapping[str, Tuple[ProjectionEntry, ...]]
    source_resident_platforms: Tuple[str, ...]

    def entry_map(self) -> Dict[str, ProjectionEntry]:
        return {entry.destination: entry for entry in self.entries}


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _is_sha256(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(char in SHA256_PATTERN for char in value)
    )


def _is_safe_relative(value: Any) -> bool:
    """Return whether a string is a safe project-relative POSIX path (no escape)."""
    if not isinstance(value, str) or not value:
        return False
    if "\\" in value or "\x00" in value:
        return False
    pure = PurePosixPath(value)
    if pure.is_absolute() or any(part in ("", ".", "..") for part in pure.parts):
        return False
    return True


def load_active_manifest(root: Path) -> dict[str, Any]:
    """Read and structurally validate the committed active manifest."""
    path = root / ACTIVE_MANIFEST_PATH
    if not path.exists():
        raise ProjectionError(
            f"{ACTIVE_MANIFEST_PATH} not found at {root}; run cg-project-manifest "
            "to resolve it first"
        )
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ProjectionError(f"{ACTIVE_MANIFEST_PATH} is malformed: {exc}") from exc
    errors = manifest_module.validate_manifest(data)
    if errors:
        raise ProjectionError(
            f"{ACTIVE_MANIFEST_PATH} is invalid: " + "; ".join(errors[:5])
        )
    return data


def load_target_mapping(root: Path) -> dict[str, Any]:
    """Load target-mapping.json from the canonical source root."""
    return generator.load_target_mapping(root)


def _manifest_closure_globs(source_root: Path, manifest: dict[str, Any]) -> list[str]:
    """Owned-asset globs for the manifest's resolved module closure.

    The globs come from the committed manifest's ``moduleClosure`` (resolved at
    manifest time), never by re-deriving selection from raw config.
    """
    closure, registry = _manifest_closure(source_root, manifest)
    return budget.loadable_asset_globs(registry, closure)


def _manifest_closure(
    source_root: Path, manifest: dict[str, Any]
) -> tuple[set[str], dict[str, Any]]:
    """Return (closure ids, registry) from the manifest's moduleClosure."""
    closure = set(manifest.get("selection", {}).get("moduleClosure", []))
    registry_path = source_root / ".github/shared/module-registry.json"
    if not registry_path.exists():
        raise ProjectionError(
            ".github/shared/module-registry.json not found at source root; "
            "a manifest-driven projection requires the versioned registry"
        )
    try:
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ProjectionError(f"module registry is malformed: {exc}") from exc
    return closure, registry


def validate_declared_roots(mapping: dict[str, Any]) -> None:
    """Validate declared managed/optional user roots and reject collisions."""
    declared: list[tuple[str, str, str]] = []
    for target in mapping.get("targets", []):
        if not isinstance(target, dict):
            continue
        tid = target.get("id", "?")
        roots = target.get("projectRoots")
        if roots is None:
            gtp = target.get("generatedTreePath")
            if gtp is not None:
                errors = generator.validate_repo_relative_path(
                    f"targets[{tid}].generatedTreePath", gtp
                )
                if errors:
                    raise ProjectionError("; ".join(errors))
            continue
        if not isinstance(roots, dict):
            raise ProjectionError(f"targets[{tid}].projectRoots must be an object")
        for kind in ("managed", "optionalUser"):
            entries = roots.get(kind)
            if entries is None:
                continue
            if not isinstance(entries, list):
                raise ProjectionError(
                    f"targets[{tid}].projectRoots.{kind} must be an array"
                )
            for index, value in enumerate(entries):
                errors = generator.validate_repo_relative_path(
                    f"targets[{tid}].projectRoots.{kind}[{index}]", value
                )
                if errors:
                    raise ProjectionError("; ".join(errors))
                declared.append((tid, kind, value))

    def _portable_key(value: str) -> tuple[str, ...]:
        import unicodedata

        return tuple(
            unicodedata.normalize("NFC", part).casefold().rstrip(". ")
            for part in PurePosixPath(value).parts
        )

    keys: list[tuple[tuple[str, ...], str, str, str]] = [
        (_portable_key(value), tid, kind, value) for tid, kind, value in declared
    ]
    for index, (first_key, first_tid, first_kind, first_value) in enumerate(keys):
        for second_key, second_tid, second_kind, second_value in keys[index + 1:]:
            if first_key == second_key:
                raise ProjectionError(
                    f"project root collision: {first_tid}.{first_kind} '{first_value}' "
                    f"and {second_tid}.{second_kind} '{second_value}'"
                )
            if (
                first_key == second_key[:len(first_key)]
                or second_key == first_key[:len(second_key)]
            ):
                raise ProjectionError(
                    f"project root file/directory prefix conflict: '{first_value}' "
                    f"and '{second_value}'"
                )


def _load_canonical_assets(
    source_root: Path, manifest: dict[str, Any]
) -> dict[str, list[dict[str, Any]]]:
    """Scan canonical assets filtered by the manifest's committed closure globs."""
    globs = _manifest_closure_globs(source_root, manifest)
    return generator.scan_canonical_assets(source_root, loadable_globs=globs)


def _load_projection_assets(
    source_root: Path,
    project_root: Path,
    manifest: dict[str, Any],
    combined_snapshot: Optional[registry_service.CombinedRegistrySnapshot] = None,
) -> dict[str, list[dict[str, Any]]]:
    """Return canonical assets plus exactly selected project bundles."""
    assets = _load_canonical_assets(source_root, manifest)
    if combined_snapshot is None:
        try:
            snapshot = registry_service.load_combined_registry_snapshot(
                project_root, source_root
            )
        except registry_service.RegistryValidationError as error:
            raise ProjectionError(str(error)) from error
    else:
        snapshot = combined_snapshot
    closure = set(manifest.get("selection", {}).get("moduleClosure", []))
    canonical_inventories = []
    canonical_identities: Dict[str, str] = {}
    canonical_supported: Dict[str, Sequence[str]] = {}
    for inventory in snapshot.canonical_bundles:
        skill_path = f"{inventory.source_path}/SKILL.md"
        owner = snapshot.canonical.owner_for_asset(skill_path)
        if owner not in closure:
            continue
        capability = snapshot.canonical.capability_for_owner(owner)
        record = snapshot.canonical_provenance_by_id(inventory.identifier)
        if record is None:
            identity = (
                str(capability.get("sourceProvenance"))
                if capability is not None
                else "canonical/.github"
            )
        else:
            source = record.get("source", {})
            identity = (
                f"{source.get('repository', '')}@{source.get('commit', '')}:"
                f"{source.get('path', '')}"
            )
        canonical_inventories.append(inventory)
        canonical_identities[inventory.identifier] = identity
        canonical_supported[inventory.identifier] = (
            capability.get("supportedPlatforms", [])
            if capability
            else list(manifest.get("selection", {}).get("platforms", []))
        )
    try:
        assets = generator.replace_bundle_inventories(
            assets,
            canonical_inventories,
            provenance_identities=canonical_identities,
            supported_platforms=canonical_supported,
        )
    except ValueError as error:
        raise ProjectionError(
            f"staged canonical bundle inventory is invalid: {error}"
        ) from error
    selected = manifest.get("selection", {}).get("selectedProjectSkills", {})
    if not isinstance(selected, dict):
        raise ProjectionError("active manifest selectedProjectSkills must be an object")
    inventories = []
    identities: Dict[str, str] = {}
    supported: Dict[str, Sequence[str]] = {}
    selected_ids = set()
    for capability_id, identifier in sorted(selected.items()):
        if not isinstance(capability_id, str) or not isinstance(identifier, str):
            raise ProjectionError("selectedProjectSkills must map strings to strings")
        record = snapshot.project_capability_by_id(capability_id)
        if record is None or record.get("id") != identifier:
            raise ProjectionError(
                f"selectedProjectSkills does not match project registry: {capability_id}"
            )
        if identifier in selected_ids:
            raise ProjectionError(
                f"selectedProjectSkills maps multiple capabilities to bundle {identifier}"
            )
        inventory = snapshot.project_bundle_by_id(identifier)
        if inventory is None:
            raise ProjectionError(f"selected project bundle is missing: {identifier}")
        provenance = snapshot.provenance_by_id(identifier)
        source = provenance.get("source", {})
        identities[identifier] = (
            f"{source.get('repository', '')}@{source.get('commit', '')}:"
            f"{source.get('path', '')}"
        )
        supported[identifier] = record["supportedPlatforms"]
        inventories.append(inventory)
        selected_ids.add(identifier)
    try:
        return generator.add_bundle_inventories(
            assets,
            inventories,
            provenance_identities=identities,
            supported_platforms=supported,
        )
    except ValueError as error:
        raise ProjectionError(f"projection bundle inventory is invalid: {error}") from error


def _validate_capability_alignment(
    source_root: Path,
    project_root: Path,
    manifest: dict[str, Any],
    combined_snapshot: Optional[registry_service.CombinedRegistrySnapshot] = None,
) -> None:
    """Reject manifests that record unknown or non-owning capabilities.

    The manifest's explicit ``selection.capabilities`` must be known registry
    capability ids, and every recorded capability must be owned by a module in
    the manifest's resolved ``moduleClosure`` (an unknown or detached capability
    would mean the closure globs cannot guarantee its inventory).
    """
    if combined_snapshot is not None:
        registry = combined_snapshot.canonical.to_dict()
    else:
        registry_path = source_root / ".github/shared/module-registry.json"
        if not registry_path.exists():
            raise ProjectionError(
                ".github/shared/module-registry.json not found at source root; "
                "a manifest-driven projection requires the versioned registry"
            )
        try:
            registry = json.loads(registry_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ProjectionError(f"module registry is malformed: {exc}") from exc
    capability_by_id = {
        cap.get("id"): cap
        for cap in registry.get("capabilities", [])
        if isinstance(cap, dict) and cap.get("id")
    }
    if combined_snapshot is None:
        try:
            combined = registry_service.load_combined_registry_snapshot(
                project_root, source_root
            )
        except registry_service.RegistryValidationError as error:
            raise ProjectionError(str(error)) from error
    else:
        combined = combined_snapshot
    project_capabilities = {
        str(item["capability"]): str(item["id"])
        for item in combined.project_records
    }
    explicit = manifest.get("selection", {}).get("capabilities", [])
    unknown = [
        capability for capability in explicit
        if capability not in capability_by_id and capability not in project_capabilities
    ]
    if unknown:
        raise ProjectionError(
            f"active manifest records unknown capability id(s): {', '.join(sorted(unknown))}"
        )
    closure = set(manifest.get("selection", {}).get("moduleClosure", []))
    for capability_id in explicit:
        if capability_id in project_capabilities:
            selected = manifest.get("selection", {}).get(
                "selectedProjectSkills", {}
            )
            if selected.get(capability_id) != project_capabilities[capability_id]:
                raise ProjectionError(
                    f"active manifest project capability {capability_id!r} has no exact bundle selection"
                )
            continue
        owner = capability_by_id[capability_id].get("owningModule")
        if owner not in closure:
            raise ProjectionError(
                f"active manifest capability '{capability_id}' owner '{owner}' "
                "is not in the resolved module closure"
            )


def _validate_manifest_freshness(
    source_root: Path,
    project_root: Path,
    manifest: dict[str, Any],
    platforms: Sequence[str],
    config_text: Optional[str] = None,
    combined_snapshot: Optional[registry_service.CombinedRegistrySnapshot] = None,
) -> None:
    """Fail closed when the committed manifest is stale relative to source.

    Re-resolves config, both registries, provenance, source revision, catalog,
    selected project bundles, desired plan, and platforms. Any immutable-field
    difference closes the publish boundary.
    """
    try:
        current = manifest_module.resolve_active_manifest(
            project_root,
            config_text=config_text,
            platforms=list(platforms),
            source_root=source_root,
            combined_snapshot=combined_snapshot,
        )
    except (OSError, UnicodeError, ValueError) as error:
        raise ProjectionError(f"active manifest inputs are invalid: {error}") from error
    stale_fields = manifest_module.manifest_stale(manifest, current)
    if stale_fields:
        raise ProjectionError(
            "active manifest is stale: " + ", ".join(stale_fields)
            + "; re-run cg-link to re-resolve before publishing"
        )


def build_projection_plan(
    source_root: Path,
    manifest: dict[str, Any],
    mapping: Optional[dict[str, Any]] = None,
    assets: Optional[dict[str, list[dict[str, Any]]]] = None,
    project_root: Optional[Path] = None,
    config_text: Optional[str] = None,
    combined_snapshot: Optional[registry_service.CombinedRegistrySnapshot] = None,
) -> ProjectionPlan:
    """Build a pure projection plan from the validated active manifest.

    Selected platform ids come exclusively from ``manifest["selection"]
    ["platforms"]``. The target mapping validates eligibility/output layout only.
    No writes occur.
    """
    source_root = Path(source_root).resolve()
    project_root = (
        Path(project_root).resolve() if project_root is not None else source_root
    )
    canonical_text = manifest_module.canonical_manifest_bytes(manifest)
    manifest_digest = _sha256_bytes(canonical_text.encode("utf-8"))
    selection = manifest.get("selection", {})
    platforms = tuple(selection.get("platforms", []))
    if not platforms:
        raise ProjectionError("active manifest declares no selected platforms")
    desired_plan_digest = selection.get("desiredPlanDigest")
    if not _is_sha256(desired_plan_digest):
        raise ProjectionError("active manifest has no valid desiredPlanDigest")

    mapping = mapping if mapping is not None else load_target_mapping(source_root)
    validate_declared_roots(mapping)
    by_id = {t.get("id"): t for t in mapping.get("targets", []) if isinstance(t, dict)}
    unknown = [p for p in platforms if p not in by_id]
    if unknown:
        raise ProjectionError(
            f"active manifest selects unknown platform id(s): {', '.join(unknown)}"
        )

    # Fail closed when the committed manifest is stale relative to the live
    # source: the registry digest/schema and the recomputed desired plan digest
    # must match the manifest's immutable selection record. This is the
    # R4/R5 "no stale selection can publish runtime files" boundary.
    _validate_manifest_freshness(
        source_root,
        project_root,
        manifest,
        platforms,
        config_text=config_text,
        combined_snapshot=combined_snapshot,
    )

    _validate_capability_alignment(
        source_root,
        project_root,
        manifest,
        combined_snapshot=combined_snapshot,
    )

    eligibility = manifest.get("platformEligibility", {})
    if eligibility.get("platforms") != list(platforms):
        raise ProjectionError(
            "active manifest platformEligibility does not match selection.platforms"
        )

    assets = (
        assets
        if assets is not None
        else _load_projection_assets(
            source_root,
            project_root,
            manifest,
            combined_snapshot=combined_snapshot,
        )
    )
    projected_platforms = tuple(
        p for p in platforms
        if by_id[p].get("generatedTreePath") is not None
        or by_id[p].get("projectedCategories")
    )
    if not projected_platforms:
        raise ProjectionError(
            "active manifest selects no platforms with a generated projection tree"
        )
    selected_targets = [by_id[p] for p in projected_platforms]
    restricted_mapping = {
        "schemaVersion": 1,
        "description": "manifest-driven projection",
        "targets": selected_targets,
    }
    try:
        generation_plan = generator.build_generation_plan(
            source_root, restricted_mapping, assets
        )
    except (generator.MappingValidationError, generator.PathSafetyError, ValueError) as exc:
        raise ProjectionError(f"projection planning failed: {exc}") from exc

    entries: list[ProjectionEntry] = []
    by_platform: Dict[str, list[ProjectionEntry]] = {p: [] for p in projected_platforms}
    for entry in generation_plan.entries:
        if not _is_safe_relative(entry.destination):
            raise ProjectionError(f"unsafe projection destination: {entry.destination!r}")
        projected = ProjectionEntry(
            platform=entry.target_id,
            destination=entry.destination,
            source=entry.source,
            kind=entry.kind,
            content=entry.content,
            sha256=entry.sha256,
            executable=entry.executable,
            origin=entry.origin,
            provenance_identity=entry.provenance_identity,
        )
        entries.append(projected)
        by_platform[entry.target_id].append(projected)

    source_resident = tuple(
        platform for platform in projected_platforms
        if platform == "copilot" and source_root == project_root
    )
    return ProjectionPlan(
        manifest_digest=manifest_digest,
        desired_plan_digest=desired_plan_digest,
        platforms=projected_platforms,
        entries=tuple(sorted(entries, key=lambda entry: entry.destination)),
        by_platform={platform: tuple(items) for platform, items in by_platform.items()},
        source_resident_platforms=source_resident,
    )


# ---------------------------------------------------------------------------
# Staging (pure materialization into a project-local safe sibling)
# ---------------------------------------------------------------------------

def _platform_root_name(plan: ProjectionPlan, platform: str) -> str:
    """First path component of a platform's destinations (e.g. ``.kilo``)."""
    for entry in plan.by_platform[platform]:
        return PurePosixPath(entry.destination).parts[0]
    raise ProjectionError(f"platform {platform} has no projected destinations")


def _stage_tree(project_root: Path, plan: ProjectionPlan, tx_id: str) -> Path:
    """Materialize the projection into ``.compound-gpid/staging/<tx_id>/``.

    Each platform's files live under ``staging/<tx_id>/<platform-root>/...``
    (e.g. ``.kilo/commands/cg-work.md``). Writes are root-anchored no-follow via
    ``secure_fs``; the staged inventory is re-validated (hashes, adapters,
    unplanned files) before it is returned.
    """
    staging_root = project_root / STAGING_DIRNAME / tx_id
    staging_root.mkdir(parents=True, exist_ok=True)
    for platform in plan.platforms:
        for entry in plan.by_platform[platform]:
            secure_fs.secure_write_bytes(
                staging_root,
                Path(entry.destination),
                entry.content,
                executable=entry.executable,
            )
    _validate_staged_tree(staging_root, plan)
    return staging_root


def _inventory_staged_destinations(
    staging_root: Path,
) -> dict[str, str]:
    """Map staged leaf destinations -> sha256, rejecting unsafe routes.

    Each file is stored at ``staging_root/<destination>``, so the inventory key
    is the destination itself (e.g. ``.kilo/commands/cg-work.md``). Staging
    writes are root-anchored no-follow, so no staged path can escape via a
    link; the final regular-file check here is defense in depth.
    """
    inventory: dict[str, str] = {}
    scan_root = _windows_scannable_path(staging_root)
    for path in sorted(scan_root.rglob("*")):
        if path.is_symlink() or not path.is_file():
            continue
        relative = path.relative_to(scan_root).as_posix()
        if not _is_safe_relative(relative):
            raise ProjectionError(f"staged path escapes staging root: {relative!r}")
        inventory[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
    return inventory


def _validate_staged_tree(
    staging_root: Path,
    plan: ProjectionPlan,
) -> None:
    """Validate staged inventory: exact set, durability, hashes, adapters."""
    expected: dict[str, ProjectionEntry] = plan.entry_map()

    actual = _inventory_staged_destinations(staging_root)
    missing = sorted(set(expected) - set(actual))
    if missing:
        raise ProjectionError(
            "staged projection is missing planned destinations: " + ", ".join(missing[:5])
        )
    unexpected = sorted(set(actual) - set(expected))
    if unexpected:
        raise ProjectionError(
            "staged projection contains unplanned destinations: " + ", ".join(unexpected[:5])
        )
    for key, entry in expected.items():
        if actual[key] != entry.sha256:
            raise ProjectionError(f"staged file hash mismatch for {key}")

    _validate_staged_markdown_utf8(staging_root)

    adapter_requirements = {
        "kilo": ".kilo/AGENTS.md",
        "opencode": ".opencode/AGENTS.md",
        "claude-code": ".claude/CLAUDE.md",
        "codex": ".agents/AGENTS.md",
    }
    destination_set = set(expected)
    for platform in plan.platforms:
        required = adapter_requirements.get(platform)
        if required is not None and required not in destination_set:
            raise ProjectionError(
                f"{platform} projection is missing root adapter {required}"
            )


def _validate_staged_markdown_utf8(staging_root: Path) -> None:
    """Reject staged Markdown that is not decodable as UTF-8 (fail closed)."""
    for path in sorted(_windows_scannable_path(staging_root).rglob("*.md")):
        if path.is_symlink() or not path.is_file():
            continue
        try:
            path.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            raise ProjectionError(f"staged Markdown is not valid UTF-8: {path}") from exc


def _windows_scannable_path(path: Path) -> Path:
    """Return a pathlib root that can enumerate paths beyond MAX_PATH."""
    if os.name == "nt":
        return Path(secure_fs._windows_long_path(path))  # pylint: disable=protected-access
    return path


# ---------------------------------------------------------------------------
# Managed state (journal + ownership) and live-root materialization
# ---------------------------------------------------------------------------

def _write_managed_json(project_root: Path, relative: str, payload: dict) -> None:
    secure_fs.secure_write_bytes(
        project_root,
        Path(relative),
        (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8"),
    )


def _read_managed_json(project_root: Path, relative: str) -> dict[str, Any]:
    try:
        content = secure_fs.secure_read_bytes(
            project_root,
            Path(relative),
            reject_hardlinks=True,
            max_bytes=MAX_MANAGED_STATE_BYTES,
        )
    except FileNotFoundError:
        return {}
    except (OSError, ValueError) as error:
        raise ProjectionError(
            f"managed state path is unsafe: {relative}: {error}"
        ) from error
    try:
        data = json.loads(content.decode("utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as error:
        raise ProjectionError(f"managed state is malformed: {relative}: {error}") from error
    if not isinstance(data, dict):
        raise ProjectionError(f"managed state must be a JSON object: {relative}")
    return data


def _reject_unsafe_destination(project_root: Path, relative: str) -> None:
    """Reject a planned/stale destination whose ancestors or leaf are unsafe.

    No-follow containment: any existing ancestor link/reparse point, a leaf
    that is a link/reparse point, or a leaf that is a hard link (``nlink > 1``)
    is rejected before any mutation. Source/identity swaps are also rejected by
    re-validating ancestors immediately before the write.
    """
    if not _is_safe_relative(relative):
        raise ProjectionError(f"unsafe projection destination: {relative!r}")
    try:
        secure_fs.revalidate_destination_ancestors(
            project_root, project_root / Path(*PurePosixPath(relative).parts)
        )
    except secure_fs.SecureMutationError as exc:
        raise ProjectionError(str(exc)) from exc
    leaf = project_root / Path(*PurePosixPath(relative).parts)
    if leaf.is_symlink():
        raise ProjectionError(f"destination is a link/reparse point: {relative}")
    if leaf.exists():
        try:
            metadata = os.lstat(leaf)
        except OSError as exc:
            raise ProjectionError(f"cannot stat destination: {relative}") from exc
        if not stat.S_ISREG(metadata.st_mode):
            raise ProjectionError(f"destination is not a regular file: {relative}")
        if metadata.st_nlink > 1:
            raise ProjectionError(f"destination is a hard link: {relative}")


def _previous_ownership(project_root: Path) -> dict[str, dict[str, Any]]:
    state = _read_managed_json(project_root, OWNERSHIP_STATE_PATH)
    if state:
        errors = manifest_module.validate_ownership_state(state)
        if errors:
            raise ProjectionError("; ".join(errors))
    entries = state.get("entries")
    return entries if isinstance(entries, dict) else {}


def _is_within_relative(relative: str, root_relative: str) -> bool:
    """Return whether a portable relative path is at or below one root."""
    path_parts = PurePosixPath(relative).parts
    root_parts = PurePosixPath(root_relative).parts
    return path_parts[:len(root_parts)] == root_parts


def _project_root_for_destination(project_root: Path, relative: str) -> Path:
    return project_root / Path(*PurePosixPath(relative).parts)


def _materialize_platform(
    project_root: Path,
    platform: str,
    root_name: str,
    entries: Sequence[ProjectionEntry],
    previous_entries: dict[str, dict[str, Any]],
    warnings: list[str],
) -> dict[str, dict[str, Any]]:
    """Sync one platform's live project root from its validated generation.

    Write policy:
      - A planned destination is overwritten only when it is absent, matches
        the planned bytes, or matches the previous managed checksum (a revert
        to the last managed state). Anything else is treated as user-owned and
        preserved with a reconciliation warning.
      - Only files recorded in the previous ownership **under this platform's
        managed root** but absent from the plan are considered for stale
        removal, and only when their current bytes still match the recorded
        checksum; modified stale files are preserved with a warning. Stale
        cleanup never touches another selected platform's files.
      - Destinations crossing a link/reparse point or carrying an unsafe leaf
        (link or hard link) are rejected before mutation.
    Returns the new ownership entries for this platform.
    """
    new_entries: dict[str, dict[str, Any]] = {}
    written_destinations = {entry.destination for entry in entries}
    root_prefix = PurePosixPath(root_name)

    for entry in entries:
        relative = entry.destination
        _reject_unsafe_destination(project_root, relative)
        destination = _project_root_for_destination(project_root, relative)
        planned_bytes = entry.content
        previous_record = previous_entries.get(relative)
        previous_sha = str(previous_record.get("sha256", "")) if isinstance(previous_record, dict) else ""
        can_write = not destination.exists()
        if not can_write:
            current = _regular_file_hash(destination)
            if current == entry.sha256:
                can_write = True
            elif previous_sha and current == previous_sha:
                can_write = True
            else:
                warnings.append(
                    f"{platform}: {relative} was modified or is user-owned; preserving it"
                )
                continue
        if can_write:
            secure_fs.secure_write_bytes(
                project_root,
                Path(relative),
                planned_bytes,
                executable=entry.executable,
            )
            new_entries[relative] = {
                "sha256": entry.sha256,
                "platform": platform,
                "source": entry.source,
                "kind": entry.kind,
                "preserved": False,
                "origin": entry.origin,
                "provenanceIdentity": entry.provenance_identity,
            }

    for relative, record in sorted(previous_entries.items()):
        if relative in written_destinations:
            continue
        # Only consider stale removal for files under THIS platform's managed
        # root; never delete another selected platform's projected files.
        if not _is_within_relative(relative, root_prefix.as_posix()):
            continue
        previous_sha = str(record.get("sha256", "")) if isinstance(record, dict) else ""
        if not previous_sha:
            continue
        _reject_unsafe_destination(project_root, relative)
        destination = _project_root_for_destination(project_root, relative)
        if not destination.exists():
            continue
        current = _regular_file_hash(destination)
        if current == previous_sha:
            secure_fs.secure_delete_verified(
                project_root,
                PurePosixPath(relative),
                previous_sha,
            )
            warnings.append(f"{platform}: {relative} - removed stale managed file")
        else:
            warnings.append(
                f"{platform}: {relative} is stale but user-modified; preserving it"
            )

    return new_entries


def _is_link_or_reparse_path(path: Path) -> bool:
    """Return whether an existing path is a symlink, junction, or reparse point."""
    try:
        metadata = os.lstat(str(path))
    except FileNotFoundError:
        return False
    return stat.S_ISLNK(metadata.st_mode) or bool(
        getattr(metadata, "st_file_attributes", 0) & 0x400
    )


def _managed_copilot_link(
    project_root: Path, source_root: Path
) -> bool:
    """Return whether the Copilot skill root is the exact legacy managed link."""
    skills = project_root / COPILOT_SKILL_ROOT
    if not _is_link_or_reparse_path(skills):
        return False
    try:
        actual = skills.resolve(strict=True)
        expected = (source_root / COPILOT_SKILL_ROOT).resolve(strict=True)
    except OSError as error:
        raise ProjectionError(f"Copilot skill link cannot be resolved safely: {error}") from error
    return actual == expected


def _remove_link_no_follow(path: Path) -> None:
    """Remove one verified link or junction without traversing its target."""
    if not _is_link_or_reparse_path(path):
        raise ProjectionError(f"Refusing to remove non-link path: {path}")
    try:
        if path.is_symlink():
            path.unlink()
        else:
            os.rmdir(str(path))
    except OSError as error:
        raise ProjectionError(f"Cannot remove managed link safely: {path}: {error}") from error


def _recover_copilot_migration(project_root: Path, source_root: Path) -> None:
    """Recover the narrow legacy Copilot skill-root migration."""
    backup = project_root / COPILOT_MIGRATION_BACKUP
    if not backup.exists() and not _is_link_or_reparse_path(backup):
        return
    if not _is_link_or_reparse_path(backup):
        raise ProjectionError("Copilot migration backup is not a managed link")
    try:
        if backup.resolve(strict=True) != (source_root / COPILOT_SKILL_ROOT).resolve(
            strict=True
        ):
            raise ProjectionError("Copilot migration backup is user-owned")
    except OSError as error:
        raise ProjectionError(f"Copilot migration backup is unsafe: {error}") from error
    skills = project_root / COPILOT_SKILL_ROOT
    if not skills.exists() and not _is_link_or_reparse_path(skills):
        skills.parent.mkdir(parents=True, exist_ok=True)
        os.rename(str(backup), str(skills))
        return
    if _is_link_or_reparse_path(skills) or not skills.is_dir():
        raise ProjectionError("Copilot migration destination changed concurrently")
    ownership = _read_managed_json(project_root, OWNERSHIP_STATE_PATH)
    entries = ownership.get("entries", {}) if ownership else {}
    has_committed_copilot = isinstance(entries, dict) and any(
        _is_within_relative(path, COPILOT_SKILL_ROOT) for path in entries
    )
    if has_committed_copilot:
        _remove_link_no_follow(backup)
        return
    if any(skills.iterdir()):
        raise ProjectionError(
            "Interrupted Copilot migration has unowned destination content; preserve it and reconcile manually"
        )
    skills.rmdir()
    os.rename(str(backup), str(skills))


def _prepare_copilot_migration(
    project_root: Path,
    source_root: Path,
    plan: ProjectionPlan,
) -> bool:
    """Replace only an exact managed Copilot skill link with a real parent."""
    if "copilot" not in plan.platforms or "copilot" in plan.source_resident_platforms:
        return False
    skills = project_root / COPILOT_SKILL_ROOT
    if _is_link_or_reparse_path(skills):
        if not _managed_copilot_link(project_root, source_root):
            raise ProjectionError(
                "Copilot skill root is an unmanaged or user-owned link; refusing migration"
            )
        backup = project_root / COPILOT_MIGRATION_BACKUP
        if backup.exists() or _is_link_or_reparse_path(backup):
            raise ProjectionError("Copilot migration backup already exists")
        backup.parent.mkdir(parents=True, exist_ok=True)
        os.rename(str(skills), str(backup))
        skills.mkdir(parents=True, exist_ok=False)
        return True
    if skills.exists() and not skills.is_dir():
        raise ProjectionError("Copilot skill root is not a real directory")
    return False


def _planned_bundle_files(plan: ProjectionPlan) -> Dict[str, set[str]]:
    """Return exact planned file inventories for every managed skill bundle."""
    bundle_roots = {
        str(PurePosixPath(entry.destination).parent): entry.platform
        for entry in plan.entries
        if entry.kind == "skill"
        and not (
            entry.platform in plan.source_resident_platforms
            and entry.origin == "plugin-canonical"
        )
    }
    result: Dict[str, set[str]] = {root: set() for root in bundle_roots}
    for entry in plan.entries:
        if (
            entry.platform in plan.source_resident_platforms
            and entry.origin == "plugin-canonical"
        ):
            continue
        for root in result:
            if _is_within_relative(entry.destination, root):
                result[root].add(entry.destination)
                break
    return result


def _inventory_regular_files_no_follow(root: Path, project_root: Path) -> set[str]:
    """Inventory one existing managed bundle without following any link."""
    result = set()
    pending = [root]
    while pending:
        directory = pending.pop()
        with os.scandir(str(directory)) as entries:
            ordered = sorted(entries, key=lambda item: item.name, reverse=True)
        for entry in ordered:
            path = Path(entry.path)
            relative = path.relative_to(project_root).as_posix()
            metadata = entry.stat(follow_symlinks=False)
            if stat.S_ISLNK(metadata.st_mode) or bool(
                getattr(metadata, "st_file_attributes", 0) & 0x400
            ):
                raise ProjectionError(
                    f"managed bundle contains a link or reparse point: {relative}"
                )
            if stat.S_ISDIR(metadata.st_mode):
                pending.append(path)
            elif stat.S_ISREG(metadata.st_mode):
                result.add(relative)
            else:
                raise ProjectionError(
                    f"managed bundle contains a non-regular entry: {relative}"
                )
    return result


def _preflight_projection_destinations(
    project_root: Path,
    source_root: Path,
    plan: ProjectionPlan,
) -> None:
    """Reject every selected collision before migration or publication writes."""
    previous = _previous_ownership(project_root)
    legacy_copilot_link = _managed_copilot_link(project_root, source_root)
    for entry in plan.entries:
        if entry.platform in plan.source_resident_platforms:
            continue
        if entry.platform == "copilot" and legacy_copilot_link:
            continue
        _reject_unsafe_destination(project_root, entry.destination)
        destination = _project_root_for_destination(project_root, entry.destination)
        if not destination.exists():
            continue
        current = _regular_file_hash(destination)
        prior = previous.get(entry.destination)
        prior_sha = str(prior.get("sha256", "")) if isinstance(prior, dict) else ""
        if current not in {entry.sha256, prior_sha}:
            raise ProjectionError(
                f"selected destination is modified or user-owned; collision: {entry.destination}"
            )
    if legacy_copilot_link:
        return
    for bundle_root, expected in _planned_bundle_files(plan).items():
        path = project_root / Path(*PurePosixPath(bundle_root).parts)
        if not path.exists():
            continue
        if _is_link_or_reparse_path(path) or not path.is_dir():
            raise ProjectionError(f"managed bundle root is not a real directory: {bundle_root}")
        actual = _inventory_regular_files_no_follow(path, project_root)
        unexpected = sorted(actual - expected)
        if unexpected:
            raise ProjectionError(
                "managed bundle contains unexpected user-owned files: "
                + ", ".join(unexpected[:5])
            )


def publish_projection(
    project_root: Path,
    plan: ProjectionPlan,
    mapping: Optional[dict[str, Any]] = None,
    source_root: Optional[Path] = None,
) -> dict[str, Any]:
    """Publish a projection through a durable per-root activation journal.

    Sequence (root-anchored no-follow writes and same-volume renames only):
      1. Recover any prior interrupted publication.
      2. Stage the complete projection in a project-local safe sibling and
         validate it (inventory set, hashes, required root adapters).
      3. Journal ``prepared`` with the transaction id, old/new generation
         identities, planned hashes, and per-platform state.
      4. For each platform: rename the validated staged root into a versioned
         project-local generation directory, then materialize the live project
         root through checksum-gated writes (preserving modified files) and
         switch that platform's small active-root pointer.
      5. Commit ownership state only after every pointer is switched.
      6. Set the journal state to ``committed`` and remove verified old
         generations.
    Returns the committed ownership state.
    """
    project_root = Path(project_root).resolve()
    source_root = (
        Path(source_root).resolve() if source_root is not None else project_root
    )
    if not project_root.is_dir():
        raise ProjectionError(f"Project root is not a directory: {project_root}")
    if project_root.is_symlink():
        raise ProjectionError(f"Project root is a symlink: {project_root}")
    state_dir = project_root / ".compound-gpid"
    if state_dir.is_symlink() or (state_dir.exists() and not state_dir.is_dir()):
        raise ProjectionError("Refusing to publish: .compound-gpid is a symlink or not a directory")
    if mapping is not None:
        validate_declared_roots(mapping)

    recover_projection(project_root)
    _recover_copilot_migration(project_root, source_root)
    _preflight_projection_destinations(project_root, source_root, plan)
    published_platforms = tuple(
        platform for platform in plan.platforms
        if platform not in plan.source_resident_platforms
    )
    if not published_platforms:
        existing = _read_managed_json(project_root, OWNERSHIP_STATE_PATH)
        return existing or {
            "schemaVersion": 1,
            "entries": {},
            "activeAdapters": {},
            "warnings": [],
        }
    tx_id = uuid.uuid4().hex
    previous_entries = _previous_ownership(project_root)

    staging_root = _stage_tree(project_root, plan, tx_id)
    migrated_copilot = _prepare_copilot_migration(project_root, source_root, plan)
    active_dir = project_root / ACTIVE_POINTER_DIRNAME
    active_dir.mkdir(parents=True, exist_ok=True)
    generation_dir = project_root / GENERATIONS_DIRNAME / tx_id

    platform_records: dict[str, dict[str, Any]] = {}
    for platform in published_platforms:
        platform_records[platform] = {
            "root": _platform_root_name(plan, platform),
            "plannedHashes": {
                entry.destination: entry.sha256
                for entry in plan.by_platform[platform]
            },
            "state": "staged",
        }
    journal = {
        "schemaVersion": 1,
        "state": "prepared",
        "transactionId": tx_id,
        "platforms": platform_records,
    }
    _write_managed_json(project_root, TRANSACTION_JOURNAL_PATH, journal)

    warnings: list[str] = []
    ownership_entries: dict[str, dict[str, Any]] = {}
    active_adapters: dict[str, str] = {}

    for platform in published_platforms:
        root_name = _platform_root_name(plan, platform)
        source_arena = staging_root / root_name
        generation_arena = generation_dir / root_name
        if generation_arena.exists():
            raise ProjectionError(
                f"generation destination already exists: {generation_arena}"
            )
        generation_arena.parent.mkdir(parents=True, exist_ok=True)
        os.rename(str(source_arena), str(generation_arena))
        try:
            materialized = _materialize_platform(
                project_root,
                platform,
                root_name,
                plan.by_platform[platform],
                previous_entries,
                warnings,
            )
        except BaseException:
            # A rejected destination (link/hard-link/collision) must not leave a
            # wedged prepared journal: roll back the incomplete generation and
            # mark the journal rolled-back so the next link/update can recover.
            try:
                _remove_tree_no_follow(generation_dir)
                generation_dir.rmdir()
            except OSError:
                pass
            journal["state"] = "rolled-back"
            _write_managed_json(project_root, TRANSACTION_JOURNAL_PATH, journal)
            raise
        ownership_entries.update(materialized)
        pointer_rel = f"{ACTIVE_POINTER_DIRNAME}/{platform}.json"
        active_adapters[platform] = pointer_rel
        payload = {
            "schemaVersion": 1,
            "platform": platform,
            "root": root_name,
            "transactionId": tx_id,
            "generation": tx_id,
            "active": True,
        }
        _write_managed_json(project_root, pointer_rel, payload)

    ownership = {
        "schemaVersion": 1,
        "generated": tx_id,
        "transactionId": tx_id,
        "entries": ownership_entries,
        "activeAdapters": active_adapters,
        "warnings": warnings,
        "note": "Mutable projection ownership state: per-file expected/current checksums, preservation state, and stale-deletion authorization only. Drift here never invalidates selection.",
    }
    _write_managed_json(project_root, OWNERSHIP_STATE_PATH, ownership)

    journal["state"] = "committed"
    _write_managed_json(project_root, TRANSACTION_JOURNAL_PATH, journal)
    if migrated_copilot:
        backup = project_root / COPILOT_MIGRATION_BACKUP
        if backup.exists() or _is_link_or_reparse_path(backup):
            _remove_link_no_follow(backup)

    # Remove verified old generations / retired pointers and staging temp root.
    retired_dir = project_root / RETIRED_DIRNAME / tx_id
    if retired_dir.is_dir():
        for path in sorted(retired_dir.glob("*.json")):
            if not path.is_symlink():
                path.unlink()
        try:
            retired_dir.rmdir()
        except OSError:
            pass
    staging_transaction = project_root / STAGING_DIRNAME / tx_id
    if staging_transaction.is_dir():
        _remove_tree_no_follow(staging_transaction)

    return ownership


def _remove_tree_no_follow(root: Path) -> None:
    """Delete a tree without following any link/reparse entry (children only)."""
    for child in sorted(_windows_scannable_path(root).glob("*"), reverse=True):
        if child.is_symlink():
            child.unlink()
        elif child.is_dir():
            _remove_tree_no_follow(child)
            try:
                child.rmdir()
            except OSError:
                pass
        else:
            child.unlink()


def recover_projection(project_root: Path) -> dict[str, Any]:
    """Complete or roll back an interrupted publication using the journal.

    Reads ``projection-transaction.json``. A ``committed`` journal is a no-op.
    A ``prepared`` journal either:
      - completes the remaining per-platform pointer switches when every staged
        generation root validates, or
      - rolls all already-switched pointers back to the prior generation.
    Returns the reconciled ownership state.
    """
    project_root = Path(project_root).resolve()
    journal = _read_managed_json(project_root, TRANSACTION_JOURNAL_PATH)
    if not journal or journal.get("state") != "prepared":
        return _read_managed_json(project_root, OWNERSHIP_STATE_PATH)

    tx_id = journal.get("transactionId")
    if not isinstance(tx_id, str) or not _UUID_HEX_PATTERN.fullmatch(tx_id):
        # A journal whose transactionId does not match the tool-issued
        # ``uuid.uuid4().hex`` shape is untrusted: fail closed rather than
        # resolving a crafted path or deleting anything.
        raise ProjectionError("journal has an invalid transactionId (expected 32-char lowercase hex)")
    platforms = journal.get("platforms")
    if not isinstance(platforms, dict) or not platforms:
        raise ProjectionError("journal has no valid platforms map")

    generations_root = project_root / GENERATIONS_DIRNAME
    if generations_root.is_symlink():
        raise ProjectionError(
            "journal generation root is a symlink or reparse point: "
            f"{GENERATIONS_DIRNAME}"
        )
    if generations_root.exists() and not generations_root.is_dir():
        raise ProjectionError(
            f"journal generation root is not a directory: {GENERATIONS_DIRNAME}"
        )
    generation_base = generations_root.resolve()
    try:
        generation_dir = (project_root / GENERATIONS_DIRNAME / tx_id).resolve()
        generation_dir.relative_to(generation_base)
    except ValueError as exc:
        raise ProjectionError("journal generation path escapes .compound-gpid/generations") from exc

    valid = True
    for platform, record in platforms.items():
        if not isinstance(record, dict):
            valid = False
            break
        root_name = record.get("root")
        if not isinstance(root_name, str) or not _is_safe_relative(root_name):
            valid = False
            break
        if len(PurePosixPath(root_name).parts) != 1:
            valid = False
            break
        arena = generation_dir / root_name
        if not arena.is_dir() or arena.is_symlink():
            valid = False
            break
        try:
            arena.relative_to(generation_dir)
        except ValueError:
            valid = False
            break

    if valid:
        previous_entries = _previous_ownership(project_root)
        warnings: list[str] = []
        ownership_entries: dict[str, dict[str, Any]] = {}
        active_adapters: dict[str, str] = {}
        for platform, record in platforms.items():
            root_name = record["root"]
            generation_arena = generation_dir / root_name
            entries = (_staged_entries_from_generation(
                generation_arena, platform, record
            ))
            materialized = _materialize_platform(
                project_root,
                platform,
                root_name,
                entries,
                previous_entries,
                warnings,
            )
            ownership_entries.update(materialized)
            pointer_rel = f"{ACTIVE_POINTER_DIRNAME}/{platform}.json"
            active_adapters[platform] = pointer_rel
            _write_managed_json(project_root, pointer_rel, {
                "schemaVersion": 1,
                "platform": platform,
                "root": root_name,
                "transactionId": tx_id,
                "generation": tx_id,
                "active": True,
            })
        _write_managed_json(project_root, OWNERSHIP_STATE_PATH, {
            "schemaVersion": 1,
            "generated": tx_id,
            "transactionId": tx_id,
            "entries": ownership_entries,
            "activeAdapters": active_adapters,
            "warnings": warnings,
            "note": "Recovered ownership state after interrupted publication.",
        })
        journal["state"] = "committed"
        _write_managed_json(project_root, TRANSACTION_JOURNAL_PATH, journal)
    else:
        # Roll back: remove the incomplete generation and reset the journal.
        try:
            _remove_tree_no_follow(generation_dir)
            generation_dir.rmdir()
        except OSError:
            pass
        journal["state"] = "rolled-back"
        _write_managed_json(project_root, TRANSACTION_JOURNAL_PATH, journal)

    return _read_managed_json(project_root, OWNERSHIP_STATE_PATH)


def _staged_entries_from_generation(
    generation_arena: Path,
    platform: str,
    record: dict[str, Any],
) -> list[ProjectionEntry]:
    """Reconstruct ProjectionEntry records from a validated generation arena.

    The generation directory is untrusted local state, so every planned
    destination is re-validated with the same path rules as planning
    (``_validate_repo_relative_path``) and required to live under the recorded
    platform root before any bytes are materialized. Fail closed on any invalid
    key, root mismatch, symlink source, or hash mismatch.
    """
    planned = record.get("plannedHashes")
    if not isinstance(planned, dict):
        raise ProjectionError(f"journal record for {platform} has no plannedHashes")
    root_name = record.get("root")
    if not isinstance(root_name, str) or not _is_safe_relative(root_name):
        raise ProjectionError(f"journal record for {platform} has an unsafe root")
    root_prefix = PurePosixPath(root_name)
    if not root_prefix.parts or any(
        part in (".", "..") for part in root_prefix.parts
    ):
        raise ProjectionError(f"journal record for {platform} has an unsafe root")
    entries: list[ProjectionEntry] = []
    for relative, expected_sha in planned.items():
        if not _is_safe_relative(relative):
            raise ProjectionError(f"journal planned destination is unsafe: {relative!r}")
        errors = generator.validate_repo_relative_path(
            f"journal planned destination", relative
        )
        if errors:
            raise ProjectionError(f"journal planned destination is invalid: {relative!r}: " + "; ".join(errors))
        dest_parts = PurePosixPath(relative).parts
        if not dest_parts or dest_parts[:len(root_prefix.parts)] != root_prefix.parts:
            raise ProjectionError(
                f"journal planned destination {relative!r} is outside platform root {root_name!r}"
            )
        try:
            arena_rel = PurePosixPath(relative).relative_to(root_prefix)
        except ValueError as exc:
            raise ProjectionError(
                f"journal planned destination {relative!r} is outside platform root {root_name!r}"
            ) from exc
        source_file = generation_arena / Path(*arena_rel.parts)
        if not source_file.is_file() or source_file.is_symlink():
            raise ProjectionError(f"generation is missing planned file: {relative}")
        try:
            source_file.relative_to(generation_arena)
        except ValueError:
            raise ProjectionError(f"generation source escapes arena: {relative}") from None
        filesystem_source = _windows_scannable_path(source_file)
        actual = _regular_file_hash(filesystem_source)
        if not _is_sha256(expected_sha) or actual != expected_sha:
            raise ProjectionError(f"generation hash mismatch for {relative}")
        entries.append(ProjectionEntry(
            platform=platform,
            destination=relative,
            source="recovered-generation",
            kind="recovered",
            content=filesystem_source.read_bytes(),
            sha256=expected_sha,
            executable=os.access(filesystem_source, os.X_OK),
            origin="recovered",
            provenance_identity="recovered-generation",
        ))
    return entries


def verify_projection(
    project_root: Path, plan: Optional[ProjectionPlan] = None
) -> list[str]:
    """Verify ownership and, when supplied, the exact desired projection plan."""
    project_root = Path(project_root).resolve()
    problems: list[str] = []
    try:
        ownership = _read_managed_json(project_root, OWNERSHIP_STATE_PATH)
    except ProjectionError as exc:
        return [str(exc)]
    if not ownership and plan is None:
        return []
    entries = ownership.get("entries")
    if not isinstance(entries, dict):
        entries = {}
        problems.append("projection-ownership.json has no valid entries")
    active_adapters = ownership.get("activeAdapters")
    if entries and (not isinstance(active_adapters, dict) or not active_adapters):
        problems.append("projection-ownership.json has no activeAdapters")
    for destination, record in sorted(entries.items()):
        if not _is_safe_relative(destination):
            problems.append(f"{destination}: unsafe ownership destination")
            continue
        expected_sha = str(record.get("sha256", "")) if isinstance(record, dict) else ""
        if not _is_sha256(expected_sha):
            problems.append(f"{destination}: invalid ownership sha256")
            continue
        path = project_root / Path(*PurePosixPath(destination).parts)
        filesystem_path = _windows_scannable_path(path)
        if not filesystem_path.exists():
            problems.append(f"{destination}: projected file is missing")
            continue
        if filesystem_path.is_symlink() or not filesystem_path.is_file():
            problems.append(f"{destination}: projected path is not a regular file")
            continue
        try:
            if _regular_file_hash(filesystem_path) != expected_sha:
                problems.append(f"{destination}: projected file drifted from ownership")
        except ProjectionError as exc:
            problems.append(str(exc))

    if plan is None:
        return sorted(set(problems))

    expected = {
        entry.destination: entry
        for entry in plan.entries
        if not (
            entry.platform in plan.source_resident_platforms
            and entry.origin == "plugin-canonical"
        )
    }
    resident = {
        entry.destination: entry
        for entry in plan.entries
        if entry.platform in plan.source_resident_platforms
        and entry.origin == "plugin-canonical"
    }
    for destination, entry in sorted({**expected, **resident}.items()):
        path = project_root / Path(*PurePosixPath(destination).parts)
        if _is_link_or_reparse_path(path) or not path.is_file():
            problems.append(f"{destination}: planned destination is missing or not regular")
            continue
        try:
            if _regular_file_hash(path) != entry.sha256:
                problems.append(f"{destination}: planned destination digest mismatch")
        except ProjectionError as error:
            problems.append(str(error))
    for destination, entry in sorted(expected.items()):
        record = entries.get(destination)
        if not isinstance(record, dict):
            problems.append(f"{destination}: planned destination has no ownership entry")
            continue
        exact_fields = {
            "sha256": entry.sha256,
            "platform": entry.platform,
            "source": entry.source,
            "kind": entry.kind,
            "origin": entry.origin,
            "provenanceIdentity": entry.provenance_identity,
        }
        for field, value in exact_fields.items():
            if record.get(field) != value:
                problems.append(
                    f"{destination}: ownership {field} does not match desired plan"
                )
    unexpected_owned = sorted(set(entries) - set(expected))
    for destination in unexpected_owned:
        problems.append(f"{destination}: unexpected ownership entry")
    for bundle_root, expected_files in _planned_bundle_files(plan).items():
        path = project_root / Path(*PurePosixPath(bundle_root).parts)
        if not path.is_dir() or _is_link_or_reparse_path(path):
            problems.append(f"{bundle_root}: managed bundle root is missing or unsafe")
            continue
        try:
            actual_files = _inventory_regular_files_no_follow(path, project_root)
        except ProjectionError as error:
            problems.append(str(error))
            continue
        for unexpected in sorted(actual_files - expected_files):
            problems.append(f"{unexpected}: unexpected file in managed bundle")
        for missing in sorted(expected_files - actual_files):
            problems.append(f"{missing}: missing file in managed bundle")
    return sorted(set(problems))


def _regular_file_hash(path: Path) -> str:
    if path.is_symlink() or not path.is_file():
        raise ProjectionError(f"Path is not a regular file: {path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _cli_plan(project_root: Path, source_root: Path) -> int:
    manifest = load_active_manifest(project_root)
    mapping = load_target_mapping(source_root)
    plan = build_projection_plan(
        source_root, manifest, mapping=mapping, project_root=project_root
    )
    print(json.dumps({
        "platforms": list(plan.platforms),
        "count": len(plan.entries),
        "desiredPlanDigest": plan.desired_plan_digest,
        "destinations": [entry.destination for entry in plan.entries],
    }, indent=2, sort_keys=True))
    return 0


def _cli_verify(project_root: Path, source_root: Path) -> int:
    manifest = load_active_manifest(project_root)
    plan = build_projection_plan(
        source_root, manifest, project_root=project_root
    )
    problems = verify_projection(project_root, plan)
    for problem in problems:
        print(f"VERIFY: {problem}", file=sys.stderr)
    if problems:
        return 1
    print("VERIFIED")
    return 0


def sync_consumer_projection(
    project_root: Path,
    source_root: Path,
    mappings: Optional[dict[str, Any]] = None,
) -> tuple[dict[str, Any], ProjectionPlan]:
    """Run the full link/update projection pipeline for a consumer project.

    Ordered pipeline used by ``cg-link``/``cg-update``/``cg-unlink``:
      1. Journal recovery (completes or rolls back any interrupted publication).
      2. Manifest resolution from the committed active manifest (side-effect-free).
      3. Pure projection planning (distinct selected inventories, no leaks).
      4. Staged, journaled per-root activation publication.
      5. Post-publish ownership verification.
    Returns ``(ownership_state, plan)``. Raises ``ProjectionError`` on any
    step so the caller fails closed before reporting success.
    """
    project_root = Path(project_root).resolve()
    source_root = Path(source_root).resolve()
    recover_projection(project_root)
    manifest = load_active_manifest(project_root)
    mapping = mappings if mappings is not None else load_target_mapping(source_root)
    plan = build_projection_plan(
        source_root, manifest, mapping=mapping, project_root=project_root
    )
    ownership = publish_projection(
        project_root, plan, mapping=mapping, source_root=source_root
    )
    problems = verify_projection(project_root, plan)
    if problems:
        raise ProjectionError("; ".join(problems))
    return ownership, plan


def _declared_managed_roots(project_root: Path) -> set[str]:
    """Return exact declared managed project roots.

    Reads ``target-mapping.json`` (``projectRoots.managed``) from the project
    root when present; otherwise falls back to the canonical native roots for
    generated-tree platforms. Unlink/stale deletion is confined to these roots
    so a forged or stale ownership entry can never authorize deletion of an
    arbitrary project file.
    """
    mapping_path = project_root / TARGET_MAPPING_RELATIVE
    roots: set[str] = set()
    if mapping_path.exists():
        try:
            mapping = json.loads(mapping_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            mapping = {}
        for target in mapping.get("targets", []):
            if not isinstance(target, dict):
                continue
            block = target.get("projectRoots")
            if isinstance(block, dict):
                for value in block.get("managed", []):
                    if isinstance(value, str) and _is_safe_relative(value):
                        roots.add(PurePosixPath(value).as_posix())
                continue
            gtp = target.get("generatedTreePath")
            if isinstance(gtp, str) and _is_safe_relative(gtp):
                roots.add(PurePosixPath(gtp).as_posix())
    if not roots:
        # Mapping unavailable: canonical native generated-tree roots only.
        for native in (".kilo", ".claude", ".agents", ".opencode"):
            roots.add(native)
        roots.add(COPILOT_SKILL_ROOT)
    return roots


def unlink_consumer_projection(project_root: Path) -> tuple[int, list[str]]:
    """Remove only checksum-owned projection files; leave user roots intact.

    Uses the committed ownership records to delete files whose current bytes
    still match the recorded checksum, **and whose leading path component is a
    declared managed root** (from ``target-mapping.json`` or the recorded
    ``activeAdapters``), then removes empty managed directories. User-modified
    files, files outside a declared managed root, and any other project content
    are preserved. Returns ``(removed_count, warnings)``.
    """
    project_root = Path(project_root).resolve()
    try:
        ownership = _read_managed_json(project_root, OWNERSHIP_STATE_PATH)
    except ProjectionError as exc:
        raise ProjectionError(str(exc)) from exc
    entries = ownership.get("entries")
    if not isinstance(entries, dict):
        raise ProjectionError("projection-ownership.json has no valid entries")
    managed_roots = _declared_managed_roots(project_root)
    removed = 0
    warnings: list[str] = []
    for relative, record in sorted(entries.items()):
        expected_sha = str(record.get("sha256", "")) if isinstance(record, dict) else ""
        if not _is_sha256(expected_sha) or not _is_safe_relative(relative):
            warnings.append(f"{relative}: invalid ownership record; preserved")
            continue
        if not any(
            _is_within_relative(relative, managed_root)
            for managed_root in managed_roots
        ):
            warnings.append(
                f"{relative}: outside declared managed roots; preserved"
            )
            continue
        destination = _project_root_for_destination(project_root, relative)
        if not destination.exists():
            continue
        _reject_unsafe_destination(project_root, relative)
        if destination.is_symlink() or not destination.is_file():
            warnings.append(f"{relative}: not a regular file; preserved")
            continue
        current = _regular_file_hash(destination)
        if current == expected_sha:
            secure_fs.secure_delete_verified(
                project_root,
                PurePosixPath(relative),
                expected_sha,
            )
            removed += 1
        else:
            warnings.append(f"{relative}: user-modified; preserved")
    _prune_managed_dirs_no_follow(project_root)
    return removed, warnings


def _prune_managed_dirs_no_follow(project_root: Path) -> None:
    """Remove empty managed platform roots bottom-up (never following links)."""
    try:
        ownership = _read_managed_json(project_root, OWNERSHIP_STATE_PATH)
    except ProjectionError:
        ownership = {}
    entries = ownership.get("entries")
    root_names: set[str] = set()
    if isinstance(entries, dict):
        for relative in entries:
            parts = PurePosixPath(relative).parts
            if parts and _is_safe_relative(relative):
                if len(parts) >= 3 and parts[:2] == (".github", "skills"):
                    root_names.add(PurePosixPath(*parts[:3]).as_posix())
                else:
                    root_names.add(parts[0])
    # Prune empty leading roots bottom-up, refusing to touch junctions/symlinks.
    for root_name in sorted(root_names, key=len, reverse=True):
        root_dir = project_root / Path(*PurePosixPath(root_name).parts)
        if root_dir.is_symlink():
            continue
        if not root_dir.is_dir():
            continue
        # Walk deepest-first so nested empty directories are also removed.
        _prune_empty_dir_no_follow(root_dir)


def _prune_empty_dir_no_follow(dir_path: Path) -> None:
    """Recursively remove empty subdirectories then the directory itself.

    ``Path.__exit__``-style recursion is avoided: children are removed bottom-up
    only when they are empty regular directories, never following a link.
    """
    for child in sorted(dir_path.iterdir()):
        if child.is_symlink():
            continue
        if child.is_dir():
            _prune_empty_dir_no_follow(child)
    try:
        dir_path.rmdir()
    except OSError:
        # Not empty (user edits or retained files) -- leave untouched.
        pass


def _cli_sync(project_root: Path, source_root: Path) -> int:
    ownership, _plan = sync_consumer_projection(project_root, source_root)
    print(f"SYNCED {len(ownership.get('entries', {}))} files")
    return 0


def _cli_unlink_projection(project_root: Path) -> int:
    removed, warnings = unlink_consumer_projection(project_root)
    for warning in warnings:
        print(f"WARNING: {warning}", file=sys.stderr)
    print(f"UNLINKED {removed} checksum-owned files")
    return 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Manifest-driven project-local platform projection."
    )
    parser.add_argument("--project-root", default=".", help="Output/project root (default: current directory)")
    parser.add_argument("--source-root", default=None, help="Canonical .github source root (default: --project-root)")
    parser.add_argument("--plan", action="store_true", help="Build a pure projection plan (no writes)")
    parser.add_argument("--stage", action="store_true", help="Stage the projection (for tests)")
    parser.add_argument("--publish", action="store_true", help="Publish via journaled per-root activation")
    parser.add_argument("--recover", action="store_true", help="Recover an interrupted publication")
    parser.add_argument("--verify", action="store_true", help="Verify published ownership")
    parser.add_argument("--sync", action="store_true", help="Full link/update pipeline: recover + plan + publish + verify")
    parser.add_argument("--unlink", action="store_true", help="Remove only checksum-owned projection files")
    args = parser.parse_args(argv)

    project_root = Path(args.project_root).resolve()
    if not project_root.is_dir():
        print(f"Error: project root does not exist or is not a directory: {project_root}", file=sys.stderr)
        return 2
    source_root = Path(args.source_root).resolve() if args.source_root else project_root
    if not source_root.is_dir():
        print(f"Error: source root does not exist or is not a directory: {source_root}", file=sys.stderr)
        return 2

    try:
        if args.plan:
            return _cli_plan(project_root, source_root)
        if args.publish:
            manifest = load_active_manifest(project_root)
            mapping = load_target_mapping(source_root)
            plan = build_projection_plan(
                source_root,
                manifest,
                mapping=mapping,
                project_root=project_root,
            )
            ownership = publish_projection(
                project_root,
                plan,
                mapping=mapping,
                source_root=source_root,
            )
            print(f"PUBLISHED {len(ownership.get('entries', {}))} files")
            return 0
        if args.stage:
            manifest = load_active_manifest(project_root)
            mapping = load_target_mapping(source_root)
            plan = build_projection_plan(
                source_root,
                manifest,
                mapping=mapping,
                project_root=project_root,
            )
            tx_id = uuid.uuid4().hex
            staging = _stage_tree(project_root, plan, tx_id)
            print(f"STAGED {staging}")
            return 0
        if args.recover:
            recover_projection(project_root)
            print("RECOVERED")
            return 0
        if args.verify:
            return _cli_verify(project_root, source_root)
        if args.sync:
            return _cli_sync(project_root, source_root)
        if args.unlink:
            return _cli_unlink_projection(project_root)
        parser.print_help()
        return 1
    except (ProjectionError, generator.PathSafetyError, ValueError, OSError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
