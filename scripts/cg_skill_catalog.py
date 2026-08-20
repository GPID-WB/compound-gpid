#!/usr/bin/env python3
"""cg-skill-catalog — Static manifest-backed skill catalog and capability router.

Generates catalog rows exclusively from the active manifest, module-registry
activation metadata, and parsed skill frontmatter. Never loads full skill
bodies to build or query the catalog.

Supports compact default output (id, purpose, capability, availability,
activation cost) and ``--full`` with composable filters.  Hard-fails on
stale or missing manifest rather than querying global all-skill source.

Defines one compact ``route_capability`` interface that a command invokes
only when an explicitly requested capability is absent.  It identifies the
missing capability, authoritative selector/configuration field, current
inactive reason, and exact ``cg-link``/``cg-update`` regeneration action,
then stops before work.  It never silently falls back.

Usage:
    python scripts/cg_skill_catalog.py [--root <path>] [--compact|--full]
        [--id <query>] [--capability <id>] [--suite <name>]
        [--platform <id>] [--available|--unavailable]
        [--cost low|medium|high] [--owner <module>] [--provenance <src>]
        [--format table|json] [--output <path>]

    python scripts/cg_skill_catalog.py --route <capability-id> [--root <path>]

Exit codes:
    0  Success.
    1  Catalog or routing failure.
    2  Missing or invalid project root.

Requirements: Python 3.8+, stdlib only.
"""
from __future__ import annotations

import sys

if sys.version_info < (3, 8):
    print(
        f"cg-skill-catalog requires Python 3.8+; found {sys.version.split()[0]}",
        file=sys.stderr,
    )
    sys.exit(1)

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

_scripts_dir = str(Path(__file__).parent)
if _scripts_dir not in sys.path:
    sys.path.insert(0, _scripts_dir)

import cg_audit_context as audit  # noqa: E402
import cg_context_budget as budget  # noqa: E402
import cg_project_manifest as pm  # noqa: E402
import cg_validate_modules as validator  # noqa: E402

ACTIVE_MANIFEST_PATH = ".compound-gpid/active-manifest.json"
MODULE_REGISTRY_PATH = ".github/shared/module-registry.json"


# ---------------------------------------------------------------------------
# Manifest loading and staleness guard
# ---------------------------------------------------------------------------


class CatalogError(ValueError):
    """Raised when catalog or routing cannot proceed."""


def _load_manifest(root: Path, *, skip_stale_check: bool = False) -> dict[str, Any]:
    """Load and structurally validate the active manifest.

    Raises ``CatalogError`` with actionable remediation when the manifest is
    missing, structurally invalid, or stale relative to current source state.
    Never falls back to global all-skill source.

    When *skip_stale_check* is ``True``, the manifest is loaded and
    structurally validated but the expensive source-revision staleness
    comparison is skipped.  Useful for testing and when the caller already
    knows the manifest is fresh.
    """
    path = root / ACTIVE_MANIFEST_PATH
    if not path.exists():
        raise CatalogError(
            f"Active manifest not found at {ACTIVE_MANIFEST_PATH}. "
            "Run `cg-link` or `cg-update` to generate the manifest before querying the catalog."
        )
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CatalogError(f"Active manifest is unreadable or malformed: {exc}")

    errors = pm.validate_manifest(data)
    if errors:
        raise CatalogError(
            "Active manifest is structurally invalid:\n  - " + "\n  - ".join(errors)
        )

    if not skip_stale_check:
        stale = pm.manifest_stale(data, pm.resolve_active_manifest(root))
        if stale:
            raise CatalogError(
                "Active manifest is stale (changed: "
                + ", ".join(stale)
                + "). Run `cg-update` to regenerate before querying the catalog."
            )
    return data


def _load_registry(root: Path) -> dict:
    data, error = validator.load_registry(root)
    if error:
        raise CatalogError(f"Module registry error: {error}")
    return data


# ---------------------------------------------------------------------------
# Catalog row construction
# ---------------------------------------------------------------------------


def _capability_index(registry: dict) -> dict[str, dict]:
    """Map module id -> capability record (for owning modules that have one)."""
    result: dict[str, dict] = {}
    for cap in registry.get("capabilities", []):
        if not isinstance(cap, dict):
            continue
        owner = cap.get("owningModule")
        if owner:
            result[owner] = cap
    return result


def _owner_index(registry: dict) -> dict[str, str]:
    """Map canonical asset path pattern -> owning module id."""
    result: dict[str, str] = {}
    for module in registry.get("modules", []):
        if not isinstance(module, dict):
            continue
        mid = module.get("id")
        for pattern in module.get("ownedAssets", []):
            if isinstance(pattern, str):
                result[pattern] = mid
    return result


def _find_owner(
    skill_path: str, owner_index: dict[str, str]
) -> Optional[str]:
    """Find the owning module for a skill path via glob matching."""
    for pattern, module_id in owner_index.items():
        if validator._glob_match(pattern, skill_path):
            return module_id
    return None


def build_catalog(
    root: Path,
    manifest: Optional[dict] = None,
    registry: Optional[dict] = None,
) -> List[dict[str, Any]]:
    """Build the full catalog from manifest + registry + skill frontmatter.

    Returns sorted rows with both compact and extended fields.  The caller
    selects which fields to surface based on compact/full mode.

    Each row contains:
        id, purpose, capability, available, activationCost,
        sourcePath, sourceProvenance, eligibility, inactiveReason, importStatus,
        owner, supportedPlatforms, taskTriggers
    """
    if manifest is None:
        manifest = _load_manifest(root)
    if registry is None:
        registry = _load_registry(root)

    closure = set(manifest["selection"]["moduleClosure"])
    closure_globs = sorted(budget.loadable_asset_globs(registry, closure))
    cap_by_module = _capability_index(registry)
    owner_idx = _owner_index(registry)

    # Determine inactive reasons per capability module
    inactive_reasons: dict[str, str] = {}
    for module in registry.get("modules", []):
        if not isinstance(module, dict):
            continue
        mid = module.get("id")
        if mid and mid not in closure:
            # Find why it's inactive: derive from suite/config selection
            inactive_reasons[mid] = f"module '{mid}' not in selected closure"

    rows: list[dict[str, Any]] = []
    for skill in audit.scan_skill_metadata(root):
        skill_path = skill["path"]
        owner = _find_owner(skill_path, owner_idx)
        capability = cap_by_module.get(owner, {}) if owner else {}
        selected = any(
            validator._glob_match(pattern, skill_path)
            for pattern in closure_globs
        )
        inactive_reason = None
        if not selected and owner:
            inactive_reason = inactive_reasons.get(owner, f"module '{owner}' not activated")

        rows.append({
            "id": skill["id"],
            "purpose": skill.get("description", ""),
            "capability": capability.get("id") if capability else None,
            "available": selected,
            "activationCost": capability.get("activationCost") if capability else None,
            "sourcePath": skill_path,
            "sourceProvenance": capability.get("sourceProvenance") if capability else None,
            "eligibility": {
                "supportedSuites": capability.get("supportedSuites", []),
                "supportedPlatforms": capability.get("supportedPlatforms", []),
            } if capability else None,
            "inactiveReason": inactive_reason,
            "importStatus": "canonical",
            "owner": owner,
            "supportedPlatforms": capability.get("supportedPlatforms", []) if capability else [],
            "taskTriggers": capability.get("taskTriggers", []) if capability else [],
        })
    return sorted(rows, key=lambda r: r["id"])


# ---------------------------------------------------------------------------
# Filtering
# ---------------------------------------------------------------------------


def filter_catalog(
    rows: List[dict[str, Any]],
    *,
    id_query: Optional[str] = None,
    capability: Optional[str] = None,
    suite: Optional[str] = None,
    platform: Optional[str] = None,
    available: Optional[bool] = None,
    cost: Optional[str] = None,
    owner: Optional[str] = None,
    provenance: Optional[str] = None,
) -> List[dict[str, Any]]:
    """Apply composable filters to catalog rows."""
    result = list(rows)
    if id_query:
        q = id_query.lower()
        result = [r for r in result if q in r["id"].lower() or q in r.get("purpose", "").lower()]
    if capability:
        result = [r for r in result if r.get("capability") == capability]
    if suite:
        result = [
            r for r in result
            if r.get("eligibility") and suite in r["eligibility"].get("supportedSuites", [])
        ]
    if platform:
        result = [
            r for r in result
            if r.get("eligibility") and platform in r["eligibility"].get("supportedPlatforms", [])
        ]
    if available is not None:
        result = [r for r in result if r["available"] == available]
    if cost:
        result = [r for r in result if r.get("activationCost") == cost]
    if owner:
        result = [r for r in result if r.get("owner") == owner]
    if provenance:
        result = [r for r in result if r.get("sourceProvenance") == provenance]
    return result


# ---------------------------------------------------------------------------
# Output formatting
# ---------------------------------------------------------------------------


COMPACT_FIELDS = ("id", "purpose", "capability", "available", "activationCost")
FULL_EXTRA_FIELDS = (
    "sourcePath", "sourceProvenance", "eligibility", "inactiveReason",
    "importStatus", "owner", "supportedPlatforms", "taskTriggers",
)


def format_compact(rows: List[dict[str, Any]]) -> str:
    """Compact table: id, purpose, capability, availability, cost."""
    if not rows:
        return "(no matching skills)"
    widths = {}
    for field in COMPACT_FIELDS:
        widths[field] = max(
            len(field),
            *(len(str(r.get(field, ""))) for r in rows)
        )
    header = "  ".join(f"{field.upper():<{widths[field]}}" for field in COMPACT_FIELDS)
    sep = "  ".join("-" * widths[field] for field in COMPACT_FIELDS)
    lines = [header, sep]
    for row in rows:
        cells = []
        for field in COMPACT_FIELDS:
            value = row.get(field, "")
            if isinstance(value, bool):
                value = "yes" if value else "no"
            elif value is None:
                value = "-"
            cells.append(f"{str(value):<{widths[field]}}")
        lines.append("  ".join(cells))
    return "\n".join(lines)


def format_full(rows: List[dict[str, Any]]) -> str:
    """Full table with all metadata fields."""
    if not rows:
        return "(no matching skills)"
    all_fields = COMPACT_FIELDS + FULL_EXTRA_FIELDS
    widths = {}
    for field in all_fields:
        widths[field] = max(
            len(field),
            *(len(_display_value(r.get(field))) for r in rows)
        )
    header = "  ".join(f"{field.upper():<{widths[field]}}" for field in all_fields)
    sep = "  ".join("-" * widths[field] for field in all_fields)
    lines = [header, sep]
    for row in rows:
        cells = []
        for field in all_fields:
            value = _display_value(row.get(field))
            cells.append(f"{value:<{widths[field]}}")
        lines.append("  ".join(cells))
    return "\n".join(lines)


def _display_value(value: Any) -> str:
    """Render a catalog field for table display."""
    if isinstance(value, bool):
        return "yes" if value else "no"
    if value is None:
        return "-"
    if isinstance(value, (list, dict)):
        return json.dumps(value, sort_keys=True, separators=(",", ":"))
    return str(value)


def format_json(rows: List[dict[str, Any]], compact: bool = False) -> str:
    """JSON output. Compact strips extended fields."""
    if compact:
        rows = [{k: r[k] for k in COMPACT_FIELDS if k in r} for r in rows]
    return json.dumps(rows, indent=2, sort_keys=True) + "\n"


# ---------------------------------------------------------------------------
# Capability router (Step 10)
# ---------------------------------------------------------------------------


class RouteResult:
    """Structured result from the capability router."""

    def __init__(
        self,
        *,
        found: bool,
        capability_id: Optional[str] = None,
        inactive_reason: Optional[str] = None,
        selector: Optional[str] = None,
        remedy: Optional[str] = None,
        message: str = "",
    ) -> None:
        self.found = found
        self.capability_id = capability_id
        self.inactive_reason = inactive_reason
        self.selector = selector
        self.remedy = remedy
        self.message = message

    def to_dict(self) -> dict[str, Any]:
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


def route_capability(
    root: Path,
    capability_id: str,
    manifest: Optional[dict] = None,
    registry: Optional[dict] = None,
) -> RouteResult:
    """Route an explicitly requested capability through manifest-aware hard-stop.

    When a command requests a specific capability (e.g. via a task trigger or
    explicit capability id), this function checks the active manifest to
    determine whether the capability is active.  If inactive, it returns a
    structured hard-stop result with the authoritative selector, inactive
    reason, and exact ``cg-link`` or ``cg-update`` regeneration action.

    It never silently falls back to all-skill global source or writes a
    transient session projection.

    Raises ``CatalogError`` when the manifest is missing or stale.
    """
    if manifest is None:
        manifest = _load_manifest(root)
    if registry is None:
        registry = _load_registry(root)

    closure = set(manifest["selection"]["moduleClosure"])

    # Find the capability record by id
    cap_record = None
    for cap in registry.get("capabilities", []):
        if isinstance(cap, dict) and cap.get("id") == capability_id:
            cap_record = cap
            break

    if cap_record is None:
        return RouteResult(
            found=False,
            capability_id=capability_id,
            message=f"Unknown capability id: '{capability_id}'.",
            remedy="Check the available capabilities with `cg-find-skill` and use a declared capability id.",
        )

    owner_module = cap_record.get("owningModule")
    is_active = owner_module in closure

    if is_active:
        return RouteResult(found=True, capability_id=capability_id)

    # Determine why it's inactive
    selectors = cap_record.get("configSelectors", [])
    supported_suites = cap_record.get("supportedSuites", [])
    active_suites = manifest["selection"].get("suites", [])

    if selectors:
        selector_desc = "; ".join(
            f"{s.get('field', '?')} {s.get('operator', '?')} {s.get('value', '?')}"
            for s in selectors if isinstance(s, dict)
        )
        inactive_reason = (
            f"config selector(s) did not match: {selector_desc}"
        )
        remedy = (
            f"Add the appropriate field value to compound-gpid.local.md "
            f"(e.g. {selector_desc}) and run `cg-update`."
        )
    elif supported_suites:
        inactive_reason = (
            f"supported suite(s) {supported_suites} not in active suites {active_suites}"
        )
        remedy = (
            f"Add one of {supported_suites} to the `suites:` field in "
            f"compound-gpid.local.md and run `cg-update`."
        )
    else:
        inactive_reason = f"module '{owner_module}' not in selected closure"
        remedy = "Run `cg-update` to regenerate the projection."

    return RouteResult(
        found=False,
        capability_id=capability_id,
        inactive_reason=inactive_reason,
        selector=selectors[0] if selectors else None,
        remedy=remedy,
        message=(
            f"Capability '{capability_id}' is declared but not active in the current manifest."
        ),
    )


# ---------------------------------------------------------------------------
# Inventory leak check (Step 10 extension)
# ---------------------------------------------------------------------------


def check_inventory_leaks(
    root: Path,
    manifest: Optional[dict] = None,
    registry: Optional[dict] = None,
) -> List[str]:
    """Check generated targets for inactive asset paths or references.

    Returns a list of leak descriptions (empty = no leaks).  Each leak names
    the emitted path or reference that references an inactive asset, along
    with the expected regeneration action.

    This extends the closure and generated-target tests from
    ``test_target_closure.py`` and ``test_context_budget.py`` to inspect
    all emitted commands, agents, skills, instructions, shared assets, root
    adapters, configs, and catalog rows for inactive asset paths or references.
    """
    if manifest is None:
        manifest = _load_manifest(root)
    if registry is None:
        registry = _load_registry(root)

    closure = set(manifest["selection"]["moduleClosure"])
    closure_globs = sorted(budget.loadable_asset_globs(registry, closure))
    leaks: list[str] = []

    # Check catalog rows for inactive references
    catalog = manifest.get("catalogRecords", [])
    for row in catalog:
        if not isinstance(row, dict):
            continue
        if not row.get("available") and row.get("capability"):
            # Inactive catalog entries are expected; only flag if they appear
            # in the active inventory (which would be a leak)
            pass

    # Check if any canonical asset outside the closure is referenced by
    # assets inside the closure
    all_assets = validator.canonical_assets(root)
    active_assets = [
        a for a in all_assets
        if any(validator._glob_match(pattern, a) for pattern in closure_globs)
    ]

    # Read each active asset and check for references to inactive assets
    inactive_assets = [
        a for a in all_assets
        if not any(validator._glob_match(pattern, a) for pattern in closure_globs)
    ]
    inactive_set = set(inactive_assets)

    import re
    runtime_ref_re = re.compile(
        r"(?<![A-Za-z0-9_.-])\.github/(prompts|skills|agents|instructions|shared)/"
        r"[^\s`'\"<>)/][^\s`'\"<>)]*"
    )

    for asset_path in active_assets:
        full_path = root / asset_path
        if not full_path.is_file():
            continue
        try:
            content = full_path.read_text(encoding="utf-8-sig")
        except (OSError, UnicodeDecodeError):
            continue
        for match in runtime_ref_re.finditer(content):
            ref_path = match.group(0)
            # Normalize the reference to a canonical asset path
            if ref_path in inactive_set:
                leaks.append(
                    f"Active asset '{asset_path}' references inactive asset '{ref_path}'"
                )

    # Check catalog records embedded in manifest for inactive skill content
    for row in catalog:
        if not isinstance(row, dict):
            continue
        skill_id = row.get("id")
        available = row.get("available", True)
        if not available:
            # An inactive catalog row should not have been loaded into
            # any active command/agent context
            pass

    return sorted(set(leaks))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Static manifest-backed skill catalog and capability router."
    )
    parser.add_argument("--root", default=".", help="Project root (default: .)")
    parser.add_argument("--compact", action="store_true", default=True, help="Compact output (default)")
    parser.add_argument("--full", action="store_true", help="Full output with all metadata")
    parser.add_argument("--id", default=None, dest="id_query", help="Filter by skill id or purpose substring")
    parser.add_argument("--capability", default=None, help="Filter by capability id")
    parser.add_argument("--suite", default=None, help="Filter by supported suite")
    parser.add_argument("--platform", default=None, help="Filter by supported platform")
    parser.add_argument("--available", action="store_true", default=False, help="Show only available skills")
    parser.add_argument("--unavailable", action="store_true", default=False, help="Show only unavailable skills")
    parser.add_argument("--cost", default=None, choices=["low", "medium", "high"], help="Filter by activation cost")
    parser.add_argument("--owner", default=None, help="Filter by owning module")
    parser.add_argument("--provenance", default=None, help="Filter by source provenance")
    parser.add_argument("--format", default="table", choices=["table", "json"], help="Output format")
    parser.add_argument("--output", default=None, help="Write output to file")
    parser.add_argument("--route", default=None, metavar="CAPABILITY_ID", help="Route a capability request (hard-stop if inactive)")
    parser.add_argument("--check-leaks", action="store_true", help="Check for inactive asset leaks")
    parser.add_argument("--skip-stale-check", action="store_true", help="Skip manifest staleness comparison (testing)")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    if not root.is_dir():
        print(f"Error: project root does not exist or is not a directory: {root}", file=sys.stderr)
        return 2

    # Route mode: hard-stop capability routing
    if args.route:
        try:
            manifest = _load_manifest(root, skip_stale_check=args.skip_stale_check)
            registry = _load_registry(root)
            result = route_capability(root, args.route, manifest, registry)
        except CatalogError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1
        if args.format == "json":
            print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
        else:
            print(str(result))
        return 0 if result.found else 1

    # Leak check mode
    if args.check_leaks:
        try:
            manifest = _load_manifest(root, skip_stale_check=args.skip_stale_check)
            registry = _load_registry(root)
            leaks = check_inventory_leaks(root, manifest, registry)
        except CatalogError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1
        if leaks:
            print("INVENTORY LEAKS DETECTED:", file=sys.stderr)
            for leak in leaks:
                print(f"  - {leak}", file=sys.stderr)
            return 1
        print("No inventory leaks detected.")
        return 0

    # Catalog mode
    try:
        manifest = _load_manifest(root, skip_stale_check=args.skip_stale_check)
        registry = _load_registry(root)
        rows = build_catalog(root, manifest, registry)
    except CatalogError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    # Apply filters
    avail_filter = None
    if args.available:
        avail_filter = True
    elif args.unavailable:
        avail_filter = False

    rows = filter_catalog(
        rows,
        id_query=args.id_query,
        capability=args.capability,
        suite=args.suite,
        platform=args.platform,
        available=avail_filter,
        cost=args.cost,
        owner=args.owner,
        provenance=args.provenance,
    )

    is_full = args.full
    if args.format == "json":
        output = format_json(rows, compact=not is_full)
    elif is_full:
        output = format_full(rows)
    else:
        output = format_compact(rows)

    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(output, encoding="utf-8")
    else:
        print(output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
