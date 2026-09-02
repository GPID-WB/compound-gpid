#!/usr/bin/env python3
"""cg-project-manifest — Resolve and validate the committed active project manifest.

Consumes the strict project configuration (``compound-gpid.local.md``) plus the
versioned module registry and produces one canonical, side-effect-free
``active-manifest.json``. The manifest records config/registry hashes, schema
versions, source revision, selected suites, derived and explicit capabilities,
the resolved module closure, selected platform ids in canonical order, platform
eligibility, the certified Kilo launch requirement, compact catalog records,
and the desired projection plan digest with canonical JSON ordering so
independent runs are comparable.

Immutable selection validity is separated from mutable projection ownership:
the active manifest is rejected only when immutable selection fields differ;
per-file ownership checksums and stale-deletion authorization live in
``projection-ownership.json``; the publication journal lives in
``projection-transaction.json``. Neither influences selection validity.

Usage:
    python scripts/cg_project_manifest.py [--root <path>] [--output <path>]
        [--source-root <path>]
        [--platforms copilot,kilo]
        [--validate] [--check-stale <manifest>] [--ensure-state]

Exit codes:
    0  Success.
    1  Resolution/validation failure.
    2  Missing or invalid project root.
"""
from __future__ import annotations

import sys

if sys.version_info < (3, 8):
    print(
        f"cg-project-manifest requires Python 3.8+; found {sys.version.split()[0]}",
        file=sys.stderr,
    )
    sys.exit(1)

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any, Optional

_scripts_dir = str(Path(__file__).parent)
if _scripts_dir not in sys.path:
    sys.path.insert(0, _scripts_dir)

import cg_audit_context as audit  # noqa: E402
import cg_context_budget as budget  # noqa: E402
from skill_management.services import catalog as catalog_service  # noqa: E402
from skill_management.services import registry as registry_service  # noqa: E402

MODULE_REGISTRY_PATH = ".github/shared/module-registry.json"
LOCAL_CONFIG_PATH = "compound-gpid.local.md"
TARGET_MAPPING_PATH = ".github/shared/target-mapping.json"

ACTIVE_MANIFEST_PATH = ".compound-gpid/active-manifest.json"
OWNERSHIP_STATE_PATH = ".compound-gpid/projection-ownership.json"
TRANSACTION_JOURNAL_PATH = ".compound-gpid/projection-transaction.json"

HEADER = "compound-gpid-active-manifest-v1"
SUPPORTED_CONFIG_SCHEMA_VERSION = "2"


class ManifestResolutionError(ValueError):
    """Raised when strict config or registry inputs cannot resolve a manifest."""


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def source_revision(root: Path) -> str:
    """Return ``<commit-time>@<short-sha>`` or the deterministic sentinel.

    A non-git root records ``"unknown-revision"`` (never wall-clock time) so
    independent resolver runs remain byte-comparable.
    """
    try:
        head_sha = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        if head_sha.returncode != 0 or not head_sha.stdout.strip():
            return "unknown-revision"
        head_time = subprocess.run(
            ["git", "-C", str(root), "show", "-s", "--format=%cI", "HEAD"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return "unknown-revision"
    if head_sha.returncode == 0 and head_time.returncode == 0:
        sha = head_sha.stdout.strip()
        stamp = head_time.stdout.strip()
        if sha and stamp:
            return f"{stamp}@{sha[:12]}"
    return "unknown-revision"


def canonical_platform_ids(root: Path) -> list[str]:
    """Canonical ordered platform ids from the target mapping (file order).

    Raises ``ManifestResolutionError`` when the mapping is absent, not a JSON
    object, lacks a non-empty ``targets`` list, or a target has no id, so a
    malformed mapping can never produce a silently empty platform set.
    """
    path = root / TARGET_MAPPING_PATH
    if not path.exists():
        raise ManifestResolutionError(f"{TARGET_MAPPING_PATH} not found at {root}")
    try:
        mapping = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ManifestResolutionError(f"{TARGET_MAPPING_PATH} is malformed: {exc}") from exc
    if not isinstance(mapping, dict):
        raise ManifestResolutionError(f"{TARGET_MAPPING_PATH} must be a JSON object")
    targets = mapping.get("targets")
    if not isinstance(targets, list) or not targets:
        raise ManifestResolutionError(f"{TARGET_MAPPING_PATH} must declare a non-empty 'targets' array")
    ids: list[str] = []
    for target in targets:
        platform_id = target.get("id") if isinstance(target, dict) else None
        if not isinstance(platform_id, str) or not platform_id:
            raise ManifestResolutionError(f"{TARGET_MAPPING_PATH} contains a target without an 'id'")
        if platform_id not in ids:
            ids.append(platform_id)
    return ids


def _load_registry(root: Path) -> dict:
    try:
        return registry_service.load_registry_snapshot(root).to_dict()
    except registry_service.RegistryValidationError as exc:
        raise ManifestResolutionError(str(exc)) from exc


def registry_digest(root: Path) -> tuple[str, Optional[int]]:
    """Return (sha256 of registry bytes, schemaVersion) for staleness checks."""
    try:
        snapshot = registry_service.load_registry_snapshot(root)
    except registry_service.RegistryValidationError as exc:
        raise ManifestResolutionError(str(exc)) from exc
    version = snapshot.registry.get("schemaVersion")
    return snapshot.digest, version if isinstance(version, int) else None


def config_digest(config_text: str) -> str:
    """Stable digest of the raw project config text (BOM and bytes exact)."""
    return _sha256_bytes(config_text.encode("utf-8"))


def desired_plan_digest(
    closure_ids: list[str],
    globs: list[str],
    platforms: list[str],
    selected_project_skills: Optional[dict[str, str]] = None,
    project_bundle_records: Optional[list[dict[str, str]]] = None,
) -> str:
    """Deterministic digest of the desired projection plan inputs."""
    canonical = json.dumps(
        {
            "closure": closure_ids,
            "globs": globs,
            "platforms": platforms,
            "selectedProjectSkills": selected_project_skills or {},
            "projectBundles": project_bundle_records or [],
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return _sha256_bytes(canonical.encode("utf-8"))


def _capability_records(registry: dict) -> list[dict]:
    capabilities = registry.get("capabilities")
    return [cap for cap in capabilities if isinstance(cap, dict)] if isinstance(capabilities, list) else []


def _platform_eligibility(
    registry: dict,
    closure_ids: set[str],
    platforms: list[str],
    project_records: Optional[list[dict[str, Any]]] = None,
    selected_project_skills: Optional[dict[str, str]] = None,
) -> dict[str, Any]:
    """Per-capability and per-platform eligibility for the selected closure."""
    records = _capability_records(registry)
    capabilities_used: dict[str, Any] = {}
    for cap in records:
        if cap.get("owningModule") in closure_ids:
            capabilities_used[cap.get("id")] = cap
    rows: list[dict[str, Any]] = []
    for capability_id in sorted(capabilities_used):
        capability = capabilities_used[capability_id]
        supported = capability.get("supportedPlatforms")
        if not isinstance(supported, list):
            supported = []
        supported_set = {p for p in supported if isinstance(p, str)}
        rows.append({
            "id": capability_id,
            "module": capability.get("owningModule"),
            "supportedPlatforms": sorted(supported_set),
            "eligiblePlatforms": sorted(p for p in platforms if p in supported_set),
            "ineligiblePlatforms": sorted(p for p in platforms if p not in supported_set),
        })
    selected_projects = selected_project_skills or {}
    for record in sorted(project_records or [], key=lambda item: item["capability"]):
        capability_id = record["capability"]
        if selected_projects.get(capability_id) != record["id"]:
            continue
        supported_set = set(record["supportedPlatforms"])
        rows.append({
            "id": capability_id,
            "module": "project-local",
            "supportedPlatforms": list(record["supportedPlatforms"]),
            "eligiblePlatforms": [p for p in platforms if p in supported_set],
            "ineligiblePlatforms": [p for p in platforms if p not in supported_set],
        })
    return {
        "platforms": list(platforms),
        "capabilities": rows,
        "allEligible": all(
            not row["ineligiblePlatforms"]
            for row in rows
        ),
    }


def _catalog_records(
    root: Path,
    closure_ids: list[str],
    registry: dict,
    *,
    project_snapshot: Optional[registry_service.CombinedRegistrySnapshot] = None,
    selected_project_skills: Optional[dict[str, str]] = None,
) -> list[dict[str, Any]]:
    """Build compact records through the canonical catalog service."""
    try:
        manifest = {
            "selection": {
                "moduleClosure": closure_ids,
                "selectedProjectSkills": selected_project_skills or {},
            }
        }
        return catalog_service.manifest_catalog_records(
            root,
            manifest,
            registry,
            project_snapshot=project_snapshot,
        )
    except catalog_service.CatalogError as exc:
        raise ManifestResolutionError(str(exc)) from exc


def resolve_active_manifest(
    root: Path,
    config_text: Optional[str] = None,
    platforms: Optional[list[str]] = None,
    source_root: Optional[Path] = None,
    combined_snapshot: Optional[registry_service.CombinedRegistrySnapshot] = None,
) -> dict[str, Any]:
    """Resolve the canonical active manifest. Side-effect-free.

    Raises:
        ManifestResolutionError: For strict-config errors, unknown suites or
            capabilities, malformed registry/target mapping, or unknown
            platform ids.
    """
    root = Path(root).resolve()
    source_root = Path(source_root).resolve() if source_root is not None else root
    if config_text is None:
        config_path = root / LOCAL_CONFIG_PATH
        if not config_path.exists():
            raise ManifestResolutionError(f"{LOCAL_CONFIG_PATH} not found at {root}")
        config_text = config_path.read_text(encoding="utf-8")

    # Strict config parsing (resolver inputs never use the lenient parser).
    from parsing_utils import parse_strict_config

    parsed = parse_strict_config(config_text)
    if parsed.errors:
        raise ManifestResolutionError("; ".join(parsed.errors[:5]))

    config_schema_version = parsed.scalar("config-schema-version")
    if config_schema_version is not None and config_schema_version != SUPPORTED_CONFIG_SCHEMA_VERSION:
        raise ManifestResolutionError(
            f"config schema version {config_schema_version!r} is not the supported version "
            f"({SUPPORTED_CONFIG_SCHEMA_VERSION}); migrate explicitly before strict resolution"
        )

    if combined_snapshot is None:
        try:
            combined_snapshot = registry_service.load_combined_registry_snapshot(
                root, source_root
            )
        except registry_service.RegistryValidationError as exc:
            raise ManifestResolutionError(str(exc)) from exc
    elif (
        combined_snapshot.project_root != root
        or combined_snapshot.canonical.source_root != source_root
    ):
        raise ManifestResolutionError(
            "Injected combined registry snapshot does not match resolver roots"
        )
    registry = combined_snapshot.canonical.to_dict()
    available_platforms = canonical_platform_ids(source_root)
    selected_platforms = list(platforms) if platforms is not None else list(available_platforms)
    unknown_platforms = [p for p in selected_platforms if p not in available_platforms]
    if unknown_platforms:
        raise ManifestResolutionError(
            f"unknown platform id(s): {', '.join(sorted(unknown_platforms))}; "
            f"available: {', '.join(available_platforms)}"
        )

    suites = parsed.suites or ["cg"]  # only a genuinely absent suites field defaults
    settings = parsed.settings
    explicit = list(parsed.capabilities)
    canonical_capability_ids = {
        cap.get("id") for cap in _capability_records(registry)
    }
    project_capability_by_id = {
        record["capability"]: record
        for record in combined_snapshot.project_records
    }
    known_capability_ids = canonical_capability_ids | set(project_capability_by_id)
    unknown_capabilities = [c for c in explicit if c not in known_capability_ids]
    if unknown_capabilities:
        raise ManifestResolutionError(
            f"unknown explicit capability id(s): {', '.join(sorted(unknown_capabilities))}"
        )

    canonical_explicit = [
        capability for capability in explicit
        if capability in canonical_capability_ids
    ]
    try:
        selected_project_skills = combined_snapshot.select_project_skills(
            tuple(explicit), tuple(suites), tuple(selected_platforms)
        )
    except registry_service.RegistryValidationError as exc:
        raise ManifestResolutionError(str(exc)) from exc

    try:
        loadable_ids = budget.loadable_module_ids(
            registry, suites, config=settings, capabilities=canonical_explicit
        )
    except ValueError as exc:
        raise ManifestResolutionError(str(exc)) from exc
    closure_ids = sorted(loadable_ids)
    closure_globs = sorted(budget.loadable_asset_globs(registry, loadable_ids))
    derived_ids = budget.capability_ids_by_selector(registry, settings, suites)
    registry_hash = combined_snapshot.canonical_digest
    registry_version = combined_snapshot.canonical.registry.get("schemaVersion")
    registry_schema = registry_version if isinstance(registry_version, int) else None

    catalog_records = _catalog_records(
        source_root,
        closure_ids,
        registry,
        project_snapshot=combined_snapshot,
        selected_project_skills=selected_project_skills,
    )
    project_bundle_records = [
        {
            "id": str(record["id"]),
            "capability": str(record["capability"]),
            "bundleDigest": str(record["bundleDigest"]),
            "provenanceId": str(record["provenanceId"]),
        }
        for record in combined_snapshot.project_records
    ]
    selected_project_bundle_records = [
        record for record in project_bundle_records
        if selected_project_skills.get(record["capability"]) == record["id"]
    ]
    catalog_digest = _sha256_bytes(
        json.dumps(
            {
                "records": catalog_records,
                "projectBundles": project_bundle_records,
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    )
    manifest: dict[str, Any] = {
        "header": HEADER,
        "schemaVersion": 1,
        "generated": audit._deterministic_generated_stamp(source_root),
        "selection": {
            "configDigest": config_digest(config_text),
            "configSchemaVersion": config_schema_version,
            "registryDigest": registry_hash,
            "registrySchemaVersion": registry_schema,
            "projectRegistryDigest": combined_snapshot.project_registry_digest,
            "provenanceDigest": combined_snapshot.provenance_digest,
            "sourceRevision": source_revision(source_root),
            "suites": suites,
            "capabilities": explicit,
            "derivedCapabilities": derived_ids,
            "moduleClosure": closure_ids,
            "selectedProjectSkills": selected_project_skills,
            "platforms": selected_platforms,
            "catalogDigest": catalog_digest,
            "desiredPlanDigest": desired_plan_digest(
                closure_ids,
                closure_globs,
                selected_platforms,
                selected_project_skills,
                selected_project_bundle_records,
            ),
        },
        "platformEligibility": _platform_eligibility(
            registry,
            loadable_ids,
            selected_platforms,
            project_records=[dict(record) for record in combined_snapshot.project_records],
            selected_project_skills=selected_project_skills,
        ),
        "certifiedKiloLaunchRequired": False,
        "certifiedKiloLaunchNote": (
            "Set by cg-link/cg-update preflight; True requires the certified "
            "`cg-kilo` launcher for combined Kilo+Codex configurations."
        ),
        "catalogRecords": catalog_records,
    }
    return manifest


def canonical_manifest_bytes(manifest: dict[str, Any]) -> str:
    """Deterministic serialization for hashing and byte-stable comparison."""
    return json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def immutable_selection_fields(manifest: dict[str, Any]) -> dict[str, Any]:
    """The subset of the manifest that determines stale selection."""
    selection = manifest.get("selection", {})
    return {
        "configDigest": selection.get("configDigest"),
        "registryDigest": selection.get("registryDigest"),
        "registrySchemaVersion": selection.get("registrySchemaVersion"),
        "projectRegistryDigest": selection.get("projectRegistryDigest"),
        "provenanceDigest": selection.get("provenanceDigest"),
        "sourceRevision": selection.get("sourceRevision"),
        "moduleClosure": selection.get("moduleClosure"),
        "selectedProjectSkills": selection.get("selectedProjectSkills"),
        "platforms": selection.get("platforms"),
        "catalogDigest": selection.get("catalogDigest"),
        "desiredPlanDigest": selection.get("desiredPlanDigest"),
    }


def manifest_stale(committed: dict[str, Any], current: dict[str, Any]) -> list[str]:
    """Compare immutable selection fields. Returns stale-field names (empty = fresh)."""
    stale: list[str] = []
    committed_fields = immutable_selection_fields(committed)
    for field, value in immutable_selection_fields(current).items():
        if committed_fields.get(field) != value:
            stale.append(field)
    return stale


def validate_manifest(manifest: Any) -> list[str]:
    """Structural validation of a manifest. Returns error messages (empty = valid).

    Canonical JSON ordering is enforced at write time by
    :func:`canonical_manifest_bytes` (``sort_keys=True``); this structural pass
    validates identity, required fields, and field types.
    """
    errors: list[str] = []
    if not isinstance(manifest, dict):
        return ["manifest must be a JSON object"]
    if manifest.get("header") != HEADER:
        errors.append(f"header must be {HEADER!r}")
    selection = manifest.get("selection")
    if not isinstance(selection, dict):
        errors.append("selection must be an object")
        return errors
    for field in (
        "configDigest", "registryDigest", "registrySchemaVersion",
        "projectRegistryDigest", "provenanceDigest", "sourceRevision",
        "suites", "moduleClosure", "selectedProjectSkills", "platforms",
        "catalogDigest", "desiredPlanDigest",
    ):
        if field not in selection:
            errors.append(f"selection missing {field}")
    if "configDigest" in selection and not isinstance(selection["configDigest"], str):
        errors.append("selection.configDigest must be a string")
    if "registryDigest" in selection and not isinstance(selection["registryDigest"], str):
        errors.append("selection.registryDigest must be a string")
    if "registrySchemaVersion" in selection and not isinstance(selection["registrySchemaVersion"], int):
        errors.append("selection.registrySchemaVersion must be an integer")
    for field in (
        "projectRegistryDigest", "provenanceDigest", "catalogDigest"
    ):
        if field in selection and not (
            isinstance(selection[field], str)
            and len(selection[field]) == 64
            and all(char in "0123456789abcdef" for char in selection[field])
        ):
            errors.append(f"selection.{field} must be a 64-char hex digest")
    if "desiredPlanDigest" in selection and not (
        isinstance(selection["desiredPlanDigest"], str)
        and len(selection["desiredPlanDigest"]) == 64
        and all(char in "0123456789abcdef" for char in selection["desiredPlanDigest"])
    ):
        errors.append("selection.desiredPlanDigest must be a 64-char hex digest")
    for field in ("suites", "moduleClosure", "platforms"):
        value = selection.get(field)
        if value is None:
            continue
        if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
            errors.append(f"selection.{field} must be a list of strings")
    selected_projects = selection.get("selectedProjectSkills")
    if selected_projects is not None and (
        not isinstance(selected_projects, dict)
        or any(
            not isinstance(key, str) or not isinstance(value, str)
            for key, value in selected_projects.items()
        )
    ):
        errors.append("selection.selectedProjectSkills must be a string map")
    elif isinstance(selected_projects, dict):
        if len(set(selected_projects.values())) != len(selected_projects):
            errors.append(
                "selection.selectedProjectSkills must map one capability to one unique bundle"
            )
        for capability, identifier in selected_projects.items():
            if capability != f"project-skill-{identifier}":
                errors.append(
                    "selection.selectedProjectSkills keys must match project-skill-<bundle-id>"
                )
    return errors


def validate_ownership_state(state: dict[str, Any]) -> list[str]:
    """Shape validation for projection-ownership.json with recovery guidance."""
    errors: list[str] = []
    if not isinstance(state, dict):
        return ["projection-ownership.json must be a JSON object"]
    if state.get("schemaVersion") != 1:
        errors.append("projection-ownership.json schemaVersion must be 1")
    entries = state.get("entries")
    if entries is None:
        errors.append("projection-ownership.json is missing 'entries'")
    elif not isinstance(entries, dict):
        errors.append("projection-ownership.json 'entries' must be an object of path -> checksum records")
    return errors


def validate_transaction_journal(journal: dict[str, Any]) -> list[str]:
    """Shape validation for projection-transaction.json with recovery guidance."""
    errors: list[str] = []
    if not isinstance(journal, dict):
        return ["projection-transaction.json must be a JSON object"]
    if journal.get("schemaVersion") != 1:
        errors.append("projection-transaction.json schemaVersion must be 1")
    if "state" not in journal:
        errors.append("projection-transaction.json is missing 'state'")
    if "transactionId" not in journal:
        errors.append("projection-transaction.json is missing 'transactionId'")
    return errors


def ensure_managed_state(root: Path, manifest: dict[str, Any]) -> list[str]:
    """Idempotently create managed state records without touching user content.

    Only writes ``projection-ownership.json``/``projection-transaction.json``
    when absent; refuses to overwrite existing (possibly user-owned) files and
    reports them for reconciliation. A user-owned file or symlink at
    ``.compound-gpid`` is reported for reconciliation instead of raising or
    traversing it.
    """
    state_dir = root / ".compound-gpid"
    if state_dir.is_symlink():
        return ["reconcile before publishing: .compound-gpid is a symlink; do not follow it"]
    if state_dir.exists() and not state_dir.is_dir():
        return ["reconcile before publishing: .compound-gpid exists but is not a directory"]
    state_dir.mkdir(parents=True, exist_ok=True)
    payloads = {
        OWNERSHIP_STATE_PATH: {
            "schemaVersion": 1,
            "generated": manifest.get("generated"),
            "entries": {},
            "note": "Mutable projection ownership state: per-file expected/current checksums, preservation state, and stale-deletion authorization only. Drift here never invalidates selection.",
        },
        TRANSACTION_JOURNAL_PATH: {
            "schemaVersion": 1,
            "state": "empty",
            "transactionId": None,
            "note": "Durable per-root publication journal used to recover interrupted projection publication.",
        },
    }
    warnings: list[str] = []
    for relative, payload in payloads.items():
        path = root / relative
        if path.exists():
            # User or managed content already present: never overwrite.
            warnings.append(f"existing file preserved (not overwritten): {relative}")
            continue
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return warnings


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Resolve and validate the active project manifest.")
    parser.add_argument("--root", default=".", help="Project root directory (default: .)")
    parser.add_argument("--source-root", default=None, help="Compound GPID source root for registry and catalog inputs (default: project root)")
    parser.add_argument("--output", default=ACTIVE_MANIFEST_PATH, help="Output manifest path (default: .compound-gpid/active-manifest.json)")
    parser.add_argument("--platforms", default=None, help="Comma-separated selected platform ids (default: all canonical)")
    parser.add_argument("--validate", action="store_true", help="Validate instead of writing")
    parser.add_argument("--check-stale", default=None, metavar="PATH", help="Compare a committed manifest and report stale fields")
    parser.add_argument("--ensure-state", action="store_true", help="Idempotently create managed state records")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    if not root.is_dir():
        print(f"Error: project root does not exist or is not a directory: {root}", file=sys.stderr)
        return 2
    source_root = Path(args.source_root).resolve() if args.source_root else root
    if not source_root.is_dir():
        print(f"Error: source root does not exist or is not a directory: {source_root}", file=sys.stderr)
        return 2

    try:
        platforms = None
        if args.platforms:
            platforms = [item.strip() for item in args.platforms.split(",") if item.strip()]
        manifest = resolve_active_manifest(root, platforms=platforms, source_root=source_root)
    except ManifestResolutionError as exc:
        print(f"Error: manifest resolution failed: {exc}", file=sys.stderr)
        return 1

    validation_errors = validate_manifest(manifest)
    if validation_errors:
        print("Active manifest validation failed:", file=sys.stderr)
        for error in validation_errors:
            print(f"  - {error}", file=sys.stderr)
        return 1

    if args.check_stale:
        committed_path = Path(args.check_stale)
        if not committed_path.is_absolute():
            committed_path = root / committed_path
        try:
            committed = json.loads(committed_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            print(f"Error: cannot read committed manifest {committed_path}: {exc}", file=sys.stderr)
            return 1
        stale = manifest_stale(committed, manifest)
        if stale:
            print("STALE: " + ", ".join(stale))
            return 1
        print("FRESH")
        return 0

    if args.validate:
        print(json.dumps({"valid": True, "closure": len(manifest["selection"]["moduleClosure"])}, indent=2))
        return 0

    output = root / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(canonical_manifest_bytes(manifest), encoding="utf-8")
    print(f"[cg-project-manifest] Wrote {output}")
    if args.ensure_state:
        ensure_managed_state(root, manifest)
        print(f"[cg-project-manifest] Managed state ensured under {root / '.compound-gpid'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
