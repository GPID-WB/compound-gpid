"""Canonical catalog construction and prospective manifest health resolution."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from skill_management.services import bundles
from skill_management.services.registry import (
    CombinedRegistrySnapshot,
    RegistrySnapshot,
    RegistryValidationError,
    load_combined_registry_snapshot,
    load_registry_snapshot,
)


ACTIVE_MANIFEST_PATH = ".compound-gpid/active-manifest.json"
MISSING_REMEDIATION = (
    "Run `cg-link` or `cg-update` to generate "
    "`.compound-gpid/active-manifest.json`."
)
STALE_REMEDIATION = (
    "Run `cg-update` to regenerate `.compound-gpid/active-manifest.json`."
)
INVALID_REMEDIATION = (
    "Repair the strict configuration, canonical registry, source bundles, or "
    "manifest, then run `cg-update`."
)


class CatalogError(ValueError):
    """Raised when invalid inputs prevent safe canonical discovery."""

    def __init__(
        self,
        message: str,
        *,
        manifest_health: str = "invalid",
        remediation: Optional[str] = None,
    ) -> None:
        super().__init__(message)
        self.manifest_health = manifest_health
        self.remediation = remediation or INVALID_REMEDIATION


@dataclass(frozen=True)
class ManifestStatus:
    """Validated active-manifest health and in-memory current resolution."""

    health: str
    committed: Optional[Mapping[str, Any]]
    current: Mapping[str, Any]
    stale_fields: Tuple[str, ...]
    remediation: str


@dataclass(frozen=True)
class CatalogResolution:
    """Resolved canonical catalog rows with explicit runtime-state limits."""

    rows: Tuple[Dict[str, Any], ...]
    manifest_health: str
    prospective: bool
    remediation: str
    stale_fields: Tuple[str, ...]
    registry_digest: str


@dataclass(frozen=True)
class RouteResult:
    """Manifest-aware capability routing result for legacy command shims."""

    found: bool
    capability_id: Optional[str] = None
    inactive_reason: Optional[str] = None
    selector: Optional[Any] = None
    remedy: Optional[str] = None
    message: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Return the stable legacy route representation."""
        return {
            "found": self.found,
            "capabilityId": self.capability_id,
            "inactiveReason": self.inactive_reason,
            "selector": self.selector,
            "remedy": self.remedy,
            "message": self.message,
        }

    def __str__(self) -> str:
        if self.found:
            return f"Capability '{self.capability_id}' is active and available."
        parts = [self.message]
        if self.inactive_reason:
            parts.append(f"Reason: {self.inactive_reason}")
        if self.selector:
            parts.append(f"Selector: {self.selector}")
        if self.remedy:
            parts.append(f"Remedy: {self.remedy}")
        return "\n".join(parts)


def _roots(context: Any) -> Tuple[Path, Path]:
    project_root = Path(context.project_root).resolve()
    source_root = Path(context.source_root).resolve()
    return project_root, source_root


def inspect_manifest(project_root: Path, source_root: Path) -> ManifestStatus:
    """Resolve ``fresh``, ``missing``, ``stale``, or ``invalid`` manifest health.

    Args:
        project_root: Consumer project root containing strict config and manifest.
        source_root: Canonical Compound GPID source root.

    Returns:
        Manifest status with a side-effect-free current resolution.

    Raises:
        CatalogError: If current inputs or committed manifest are invalid.

    Example:
        ``status = inspect_manifest(project, source)``
    """
    import cg_project_manifest as manifest_module

    path = Path(project_root) / ACTIVE_MANIFEST_PATH
    committed = None
    if path.exists():
        try:
            committed = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            raise CatalogError(
                f"Active manifest is unreadable or malformed: {error}"
            ) from error
        errors = manifest_module.validate_manifest(committed)
        if errors:
            raise CatalogError(
                "Active manifest is structurally invalid: " + "; ".join(errors)
            )
    try:
        current = manifest_module.resolve_active_manifest(
            Path(project_root), source_root=Path(source_root)
        )
    except (OSError, UnicodeError, ValueError) as error:
        raise CatalogError(f"Prospective catalog inputs are invalid: {error}") from error
    if committed is None:
        return ManifestStatus("missing", None, current, (), MISSING_REMEDIATION)
    stale_fields = tuple(manifest_module.manifest_stale(committed, current))
    if stale_fields:
        return ManifestStatus(
            "stale", committed, current, stale_fields, STALE_REMEDIATION
        )
    return ManifestStatus("fresh", committed, current, (), "No remediation required.")


def _snapshot(
    source_root: Path,
    registry: Optional[Any],
) -> RegistrySnapshot:
    if isinstance(registry, RegistrySnapshot):
        return registry
    if registry is None:
        return load_registry_snapshot(source_root)
    return RegistrySnapshot.from_data(source_root, registry)


def build_catalog_rows(
    source_root: Path,
    manifest: Mapping[str, Any],
    registry: Optional[Any] = None,
    *,
    manifest_health: str = "fresh",
    project_snapshot: Optional[CombinedRegistrySnapshot] = None,
) -> List[Dict[str, Any]]:
    """Build deterministic canonical and optional project catalog rows.

    Args:
        source_root: Canonical source root. External/global roots are not scanned.
        manifest: Valid committed or in-memory active manifest.
        registry: Optional validated snapshot or parsed fixture registry.
        manifest_health: ``fresh``, ``missing``, or ``stale``.

    Returns:
        Sorted full catalog rows.

    Raises:
        CatalogError: If a bundle or owner record is invalid.

    Example:
        ``rows = build_catalog_rows(root, manifest, snapshot)``
    """
    if manifest_health not in ("fresh", "missing", "stale"):
        raise CatalogError(f"Unsupported manifest health: {manifest_health}")
    try:
        snapshot = _snapshot(Path(source_root), registry)
        import cg_context_budget as budget

        closure = set(manifest.get("selection", {}).get("moduleClosure", []))
        closure_globs = sorted(
            budget.loadable_asset_globs(snapshot.to_dict(), closure)
        )
        rows = []
        if project_snapshot is None:
            canonical_inventories = tuple(
                bundles.inventory_bundle(
                    Path(source_root), source_path, origin="plugin-canonical"
                )
                for source_path in bundles.list_canonical_bundle_paths(
                    Path(source_root)
                )
            )
        else:
            canonical_inventories = project_snapshot.canonical_bundles
        for inventory in canonical_inventories:
            identifier = inventory.identifier
            source_path = inventory.source_path
            skill_path = f"{source_path}/SKILL.md"
            frontmatter = inventory.frontmatter
            owner = snapshot.owner_for_asset(skill_path)
            if owner is None:
                raise CatalogError(f"Canonical skill has no owner: {skill_path}")
            capability = snapshot.capability_for_owner(owner)
            selected = any(
                _glob_match(pattern, skill_path) for pattern in closure_globs
            )
            prospective = manifest_health != "fresh"
            if prospective:
                availability = "prospective"
                reason = (
                    f"Manifest is {manifest_health}; no active or projected state is claimed."
                )
            elif selected:
                availability = "active"
                reason = None
            else:
                availability = "inactive"
                reason = f"module '{owner}' is not in the selected manifest closure"
            supported_suites = list(capability.get("supportedSuites", [])) if capability else []
            supported_platforms = list(capability.get("supportedPlatforms", [])) if capability else []
            canonical_provenance = (
                project_snapshot.canonical_provenance_by_id(identifier)
                if project_snapshot is not None
                else None
            )
            if canonical_provenance is not None:
                source = canonical_provenance.get("source", {})
                source_provenance = (
                    f"{source.get('repository', '')}@{source.get('commit', '')}:"
                    f"{source.get('path', '')}"
                )
            else:
                source_provenance = (
                    capability.get("sourceProvenance")
                    if capability
                    else "canonical/.github"
                )
            lifecycle = (
                str(canonical_provenance.get("lifecycle"))
                if canonical_provenance is not None
                else "current"
            )
            successor_id = (
                canonical_provenance.get("successorId")
                if canonical_provenance is not None
                else None
            )
            row = {
                "id": identifier,
                "purpose": str(frontmatter.get("description", "")),
                "capability": capability.get("id") if capability else None,
                "availability": availability,
                "manifestHealth": manifest_health,
                "activationCost": capability.get("activationCost") if capability else None,
                "origin": "plugin-canonical",
                "sourcePath": skill_path,
                "sourceProvenance": source_provenance,
                "provenanceIdentity": source_provenance,
                "eligibility": {
                    "supportedSuites": supported_suites,
                    "supportedPlatforms": supported_platforms,
                } if capability else None,
                "supportedSuites": supported_suites,
                "supportedPlatforms": supported_platforms,
                "selectors": list(capability.get("configSelectors", [])) if capability else [],
                "taskTriggers": list(capability.get("taskTriggers", [])) if capability else [],
                "inactiveReason": reason,
                "prospectiveReason": reason if prospective else None,
                "importStatus": "canonical",
                "owner": owner,
                "lifecycle": lifecycle,
                "successorId": successor_id,
            }
            if not prospective:
                row["available"] = selected
            rows.append(row)
        if project_snapshot is not None:
            selected_projects = manifest.get("selection", {}).get(
                "selectedProjectSkills", {}
            )
            if not isinstance(selected_projects, Mapping):
                raise CatalogError("selectedProjectSkills must be an object")
            inventory_by_id = {
                item.identifier: item for item in project_snapshot.project_bundles
            }
            for record in project_snapshot.project_records:
                identifier = str(record["id"])
                inventory = inventory_by_id.get(identifier)
                if inventory is None:
                    raise CatalogError(
                        f"Project registry bundle is missing from snapshot: {identifier}"
                    )
                capability_id = str(record["capability"])
                selected = selected_projects.get(capability_id) == identifier
                prospective = manifest_health != "fresh"
                if prospective:
                    availability = "prospective"
                    reason = (
                        f"Manifest is {manifest_health}; no active or projected state is claimed."
                    )
                elif selected:
                    availability = "active"
                    reason = None
                else:
                    availability = "inactive"
                    reason = (
                        f"explicit capability '{capability_id}' is not selected"
                    )
                provenance_record = project_snapshot.provenance_by_id(identifier)
                source = provenance_record.get("source", {})
                provenance_identity = (
                    f"{source.get('repository', '')}@{source.get('commit', '')}:"
                    f"{source.get('path', '')}"
                )
                row = {
                    "id": identifier,
                    "purpose": str(inventory.frontmatter.get("description", "")),
                    "capability": capability_id,
                    "availability": availability,
                    "manifestHealth": manifest_health,
                    "activationCost": "high",
                    "origin": "project-imported",
                    "sourcePath": f"{record['sourcePath']}/SKILL.md",
                    "sourceProvenance": provenance_identity,
                    "provenanceIdentity": provenance_identity,
                    "eligibility": {
                        "supportedSuites": list(record["supportedSuites"]),
                        "supportedPlatforms": list(record["supportedPlatforms"]),
                    },
                    "supportedSuites": list(record["supportedSuites"]),
                    "supportedPlatforms": list(record["supportedPlatforms"]),
                    "selectors": [],
                    "taskTriggers": [],
                    "inactiveReason": reason,
                    "prospectiveReason": reason if prospective else None,
                    "importStatus": str(record["admission"]),
                    "owner": "project-local",
                    "lifecycle": str(record["lifecycle"]),
                    "successorId": record.get("successorId"),
                }
                if not prospective:
                    row["available"] = selected
                rows.append(row)
        return sorted(rows, key=lambda row: row["id"])
    except CatalogError:
        raise
    except (OSError, UnicodeError, ValueError) as error:
        raise CatalogError(f"Canonical catalog inputs are invalid: {error}") from error


def _path_name(source_path: str) -> str:
    """Return the final POSIX path component for a canonical bundle path."""
    return source_path.rsplit("/", 1)[-1]


def _glob_match(pattern: str, asset: str) -> bool:
    from skill_management.paths import glob_match

    return glob_match(pattern, asset)


def resolve_catalog(context: Any) -> CatalogResolution:
    """Resolve canonical catalog rows for one separated project/source context.

    Args:
        context: Object with ``project_root`` and ``source_root`` paths.

    Returns:
        Catalog resolution with explicit manifest health.

    Raises:
        CatalogError: If config, registry, manifest, owner, or bundle input fails.

    Example:
        ``resolution = resolve_catalog(skill_management_context)``
    """
    project_root, source_root = _roots(context)
    try:
        combined = load_combined_registry_snapshot(project_root, source_root)
        snapshot = combined.canonical
        status = inspect_manifest(project_root, source_root)
        selected_manifest = (
            status.committed if status.health == "fresh" else status.current
        )
        assert selected_manifest is not None
        rows = build_catalog_rows(
            source_root,
            selected_manifest,
            snapshot,
            manifest_health=status.health,
            project_snapshot=combined,
        )
    except CatalogError:
        raise
    except RegistryValidationError as error:
        raise CatalogError(str(error)) from error
    return CatalogResolution(
        tuple(rows),
        status.health,
        status.health != "fresh",
        status.remediation,
        status.stale_fields,
        combined.combined_digest(),
    )


def filter_catalog_rows(
    rows: Sequence[Mapping[str, Any]],
    *,
    id_query: Optional[str] = None,
    exact_id: bool = False,
    capability: Optional[str] = None,
    suite: Optional[str] = None,
    platform: Optional[str] = None,
    available: Optional[bool] = None,
    cost: Optional[str] = None,
    owner: Optional[str] = None,
    provenance: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Apply deterministic composable filters to catalog rows.

    Args:
        rows: Full catalog rows.
        id_query: Identifier or purpose query.
        exact_id: Require exact identifier equality.
        capability: Capability identifier filter.
        suite: Supported suite filter.
        platform: Supported platform filter.
        available: Fresh active-state filter.
        cost: Activation-cost filter.
        owner: Owner module filter.
        provenance: Source provenance filter.

    Returns:
        Sorted detached matching rows.

    Raises:
        CatalogError: If an active-state filter is used on prospective rows.

    Example:
        ``filter_catalog_rows(rows, id_query="python")``
    """
    result = [dict(row) for row in rows]
    if available is not None and any(
        row.get("manifestHealth") != "fresh" for row in result
    ):
        raise CatalogError(
            "Availability filters require a fresh active manifest.",
            manifest_health=str(result[0].get("manifestHealth", "missing"))
            if result
            else "missing",
            remediation=(
                MISSING_REMEDIATION
                if result and result[0].get("manifestHealth") == "missing"
                else STALE_REMEDIATION
            ),
        )
    if id_query:
        query = id_query.casefold()
        if exact_id:
            result = [row for row in result if row.get("id") == id_query]
        else:
            result = [
                row
                for row in result
                if query in str(row.get("id", "")).casefold()
                or query in str(row.get("purpose", "")).casefold()
            ]
    if capability:
        result = [row for row in result if row.get("capability") == capability]
    if suite:
        result = [row for row in result if suite in row.get("supportedSuites", [])]
    if platform:
        result = [
            row for row in result if platform in row.get("supportedPlatforms", [])
        ]
    if available is not None:
        result = [row for row in result if row.get("available") is available]
    if cost:
        result = [row for row in result if row.get("activationCost") == cost]
    if owner:
        result = [row for row in result if row.get("owner") == owner]
    if provenance:
        result = [
            row for row in result if row.get("sourceProvenance") == provenance
        ]
    return sorted(result, key=lambda row: str(row.get("id", "")))


def manifest_catalog_records(
    source_root: Path,
    manifest: Mapping[str, Any],
    registry: Optional[Any] = None,
    *,
    project_snapshot: Optional[CombinedRegistrySnapshot] = None,
) -> List[Dict[str, Any]]:
    """Return compact manifest records from the canonical catalog builder.

    Args:
        source_root: Canonical source root.
        manifest: In-memory current active manifest.
        registry: Optional registry snapshot or parsed registry.

    Returns:
        Sorted compact records with capability identifiers, not owner ids.

    Example:
        ``manifest["catalogRecords"] = manifest_catalog_records(...)``
    """
    rows = build_catalog_rows(
        source_root,
        manifest,
        registry,
        manifest_health="fresh",
        project_snapshot=project_snapshot,
    )
    return [
        {
            "id": row["id"],
            "purpose": row["purpose"],
            "capability": row["capability"],
            "available": row["available"],
            "activationCost": row["activationCost"],
            "lifecycle": row["lifecycle"],
        }
        for row in rows
    ]


def public_record(row: Mapping[str, Any], *, full: bool) -> Dict[str, Any]:
    """Project one internal catalog row to deterministic operation output.

    Args:
        row: Full internal catalog row.
        full: Whether to include inspection fields.

    Returns:
        JSON-contract-compatible record with absent null fields omitted.

    Example:
        ``public_record(row, full=False)``
    """
    compact_fields = (
        "id",
        "purpose",
        "capability",
        "availability",
        "manifestHealth",
        "activationCost",
        "origin",
        "lifecycle",
    )
    full_fields = compact_fields + (
        "owner",
        "sourcePath",
        "provenanceIdentity",
        "selectors",
        "supportedSuites",
        "supportedPlatforms",
        "inactiveReason",
        "prospectiveReason",
        "taskTriggers",
        "successorId",
    )
    fields = full_fields if full else compact_fields
    return {field: row[field] for field in fields if row.get(field) is not None}


def route_capability(
    source_root: Path,
    capability_id: str,
    manifest: Mapping[str, Any],
    registry: Any,
) -> RouteResult:
    """Route one capability only against an explicit fresh manifest.

    Args:
        source_root: Canonical source root associated with the registry.
        capability_id: Stable capability identifier.
        manifest: Fresh validated active manifest.
        registry: Registry snapshot or parsed canonical registry.

    Returns:
        Active route or a structured hard stop. This API never resolves a
        prospective route and never scans external/global skill locations.

    Example:
        ``route_capability(root, "python", manifest, snapshot)``
    """
    snapshot = _snapshot(Path(source_root), registry)
    capability = snapshot.capability_by_id(capability_id)
    if capability is None:
        return RouteResult(
            False,
            capability_id,
            message=f"Unknown capability id: '{capability_id}'.",
            remedy=(
                "Check the available capabilities with `cg-find-skill` and use "
                "a declared capability id."
            ),
        )
    closure = set(manifest.get("selection", {}).get("moduleClosure", []))
    owner = capability.get("owningModule")
    if owner in closure:
        return RouteResult(True, capability_id)
    selectors = capability.get("configSelectors", [])
    supported_suites = capability.get("supportedSuites", [])
    active_suites = manifest.get("selection", {}).get("suites", [])
    if selectors:
        selector_description = "; ".join(
            f"{selector.get('field', '?')} {selector.get('operator', '?')} "
            f"{selector.get('value', '?')}"
            for selector in selectors
            if isinstance(selector, dict)
        )
        inactive_reason = (
            f"config selector(s) did not match: {selector_description}"
        )
        remedy = (
            "Add the appropriate field value to compound-gpid.local.md "
            f"(e.g. {selector_description}) and run `cg-update`."
        )
    elif supported_suites:
        inactive_reason = (
            f"supported suite(s) {supported_suites} not in active suites {active_suites}"
        )
        remedy = (
            f"Add one of {supported_suites} to the `suites:` field in "
            "compound-gpid.local.md and run `cg-update`."
        )
    else:
        inactive_reason = f"module '{owner}' not in selected closure"
        remedy = "Run `cg-update` to regenerate the projection."
    return RouteResult(
        False,
        capability_id,
        inactive_reason,
        selectors[0] if selectors else None,
        remedy,
        f"Capability '{capability_id}' is declared but not active in the current manifest.",
    )
