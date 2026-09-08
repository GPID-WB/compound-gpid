#!/usr/bin/env python3
"""cg-context-budget — Context-budget enforcement for module suites.

Reads the module registry and the active suites declared in
``compound-gpid.local.md``'s ``suites:`` field (default ``[cg]``), computes the
set of loadable modules (active suites + their transitive dependencies +
kernel), and produces a filtered asset manifest that the canonical generator
uses to emit only loadable assets to platform trees.

Usage:
    python3 scripts/cg_context_budget.py [--root <path>] [--config compound-gpid.local.md]
        [--output <manifest.json>]

Exit codes:
    0  Success.
    1  Fatal error.
    2  Missing or invalid project root.
"""
from __future__ import annotations

import sys

if sys.version_info < (3, 8):
    print(
        f"cg-context-budget requires Python 3.8+; found {sys.version.split()[0]}",
        file=sys.stderr,
    )
    sys.exit(1)

import argparse
import json
import re
from pathlib import Path
from typing import Any, Optional

from parsing_utils import _strip_yaml_comment

MODULE_REGISTRY_PATH = ".github/shared/module-registry.json"
LOCAL_CONFIG_PATH = "compound-gpid.local.md"


def read_active_suites(config_text: str) -> list[str]:
    """Extract the ``suites:`` field from a compound-gpid.local.md frontmatter.

    Absent or invalid values default to ``["cg"]`` (backward compatible).
    Supports inline flow lists (``suites: [cg, cr]``, including quoted
    elements and trailing comments) and block sequences (``suites:\n  - cg\n
    - cr``), skipping comment/blank lines inside a block.
    """
    if not config_text.lstrip("\ufeff\r\n").startswith("---"):
        return ["cg"]
    try:
        block = config_text.lstrip("\ufeff\r\n").split("---", 2)[1]
    except IndexError:
        return ["cg"]
    lines = block.splitlines()
    for index, line in enumerate(lines):
        if line.startswith("suites:"):
            raw = line.partition(":")[2].strip()
            raw = _strip_yaml_comment(raw)
            if raw:
                # Inline flow list.
                cleaned = raw.strip("[]")
                values = [
                    v.strip().strip("\"' ")
                    for v in cleaned.split(",")
                    if v.strip() and not v.strip().startswith("#")
                ]
            else:
                # Block sequence following the header; skip comments/blank lines.
                values = []
                for following in lines[index + 1:]:
                    stripped = following.strip()
                    if not stripped:
                        continue
                    if stripped.startswith("#"):
                        continue
                    if not stripped.startswith("-"):
                        break
                    item = _strip_yaml_comment(stripped[1:].strip().strip("\"' "))
                    if item:
                        values.append(item)
            values = [v for v in values if v]
            if values:
                return values
    return ["cg"]


def resolve_active_suite_ids(registry: dict, active_suites: list[str]) -> set[str]:
    """Map user-facing suite names (e.g. ``cg``, ``cr``) to module ids.

    A suite module matches when its id equals the requested name or ends with
    ``-<name>`` (e.g. ``suite-cg`` matches ``cg``). Resolves against
    suite-layer modules only, so capability-pack id suffixes (``r`` →
    ``cap-language-r``) are never silently treated as suites.
    """
    suite_ids = {
        m.get("id")
        for m in registry.get("modules", [])
        if isinstance(m, dict) and m.get("layer") == "suite"
    }
    resolved: set[str] = set()
    for requested in active_suites:
        if requested in suite_ids:
            resolved.add(requested)
            continue
        for sid in suite_ids:
            if sid.endswith(f"-{requested}"):
                resolved.add(sid)
    return resolved


def load_registry(root: Path, registry: Optional[dict] = None) -> dict:
    """Return the module registry dict (injected for tests or loaded from disk)."""
    if registry is not None:
        return registry
    path = root / MODULE_REGISTRY_PATH
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("module registry must be a JSON object")
    return data


def transitive_dependencies(registry: dict, module_id: str) -> set[str]:
    """Full closure of ``dependsOn`` for a module (including itself)."""
    closure: set[str] = set()
    frontier = [module_id]
    by_id = {m.get("id"): m for m in registry.get("modules", []) if isinstance(m, dict)}
    while frontier:
        current = frontier.pop()
        if current in closure:
            continue
        closure.add(current)
        module = by_id.get(current)
        if module:
            frontier.extend(module.get("dependsOn", []))
    return closure


def loadable_modules(
    registry: dict,
    active_suites: list[str],
    config: Optional[dict] = None,
    capabilities: Optional[list[str]] = None,
) -> list[dict]:
    """Modules whose assets are loadable for the active suite configuration."""
    ids = loadable_module_ids(registry, active_suites, config=config, capabilities=capabilities)
    return [m for m in registry.get("modules", []) if isinstance(m, dict) and m.get("id") in ids]


def _selector_matches(selector: dict, config: dict) -> bool:
    """Return whether a config selector matches a parsed strict config dict."""
    field = selector.get("field")
    operator = selector.get("operator", "equals")
    value = selector.get("value")
    actual = config.get(field)
    if actual is None:
        return False
    if not isinstance(actual, str):
        actual = str(actual)
    normalized = actual.strip().lower()
    if operator == "equals":
        return normalized == str(value).strip().lower()
    if operator == "contains":
        # Legacy: the project-local "language: both" selector convention
        # denotes every configured language.
        if normalized == "both":
            return True
        # Token-based containment so a single-character selector like "r" does
        # not match inside an unrelated word (e.g. "repository").
        tokens = [token.strip(" ,;()[]{}") for token in re.split(r"[/,\s]+", normalized) if token]
        return str(value).lower() in tokens or any(token.startswith(str(value).lower()) for token in tokens)
    return False


def _capability_eligible(capability: dict, active_suites: list[str], config: Optional[dict]) -> bool:
    """Whether a capability is eligible for the active suite selection.

    Selector-driven capabilities require at least one config selector match (or
    the legacy absent-config path) AND at least one supported suite active.
    Suite-eligibility capabilities activate when any of their ``supportedSuites``
    is among the user-facing active suite names.
    """
    if capability.get("activationMode") == "explicit-only":
        return False
    supported = {s for s in capability.get("supportedSuites", []) if isinstance(s, str)}
    suite_ok = bool(supported & set(active_suites))
    selectors = capability.get("configSelectors")
    if isinstance(selectors, list) and selectors:
        matched_selector = (config is None) or any(_selector_matches(sel, config or {}) for sel in selectors)
        return matched_selector and suite_ok
    return suite_ok


def capability_module_ids(
    registry: dict,
    active_suites: list[str],
    config: Optional[dict] = None,
) -> set[str]:
    """Module ids activated by registry capability records (R3/R4).

    - Capability records with non-empty ``configSelectors`` are derived from
      the parsed config. When ``config`` is ``None`` (legacy resolver input) all
      selector-driven capabilities are activated so existing generator output
      stays byte-identical (still constrained by suite eligibility).
    - Capability records with empty ``configSelectors`` are activated when at
      least one active suite is in their ``supportedSuites`` eligibility set.
    """
    capabilities = registry.get("capabilities")
    if not isinstance(capabilities, list):
        return set()
    ids: set[str] = set()
    for capability in capabilities:
        if not isinstance(capability, dict):
            continue
        module_id = capability.get("owningModule")
        if not module_id:
            continue
        if _capability_eligible(capability, active_suites, config):
            ids.add(module_id)
    return ids


def explicit_capability_module_ids(
    registry: dict,
    capabilities: Optional[list[str]],
) -> set[str]:
    """Map explicit capability names to owning module ids plus their closure.

    Additive only: explicit capabilities may extend the derived baseline but
    never subtract it. Unknown names, records without an owning module, or
    owning modules missing from the registry fail loudly. Capability features
    are disabled on legacy v1 registries without a ``capabilities`` array.
    """
    if not capabilities:
        return set()
    records = registry.get("capabilities")
    if not isinstance(records, list):
        return set()
    by_id = {
        cap.get("id"): cap
        for cap in records
        if isinstance(cap, dict) and cap.get("id")
    }
    module_ids = {
        module.get("id")
        for module in registry.get("modules", [])
        if isinstance(module, dict)
    }
    ids: set[str] = set()
    for name in capabilities:
        capability = by_id.get(name)
        if capability is None:
            raise ValueError(
                f"unknown explicit capability name: {name}; "
                "use a declared capability id from the module registry"
            )
        module_id = capability.get("owningModule")
        if not module_id:
            raise ValueError(
                f"capability '{name}' has no owningModule; cannot resolve its activation"
            )
        if module_id not in module_ids:
            raise ValueError(
                f"capability '{name}' owningModule {module_id!r} is not a declared registry module"
            )
        ids.add(module_id)
        ids |= transitive_dependencies(registry, module_id)
    return ids


def loadable_module_ids(
    registry: dict,
    active_suites: list[str],
    config: Optional[dict] = None,
    capabilities: Optional[list[str]] = None,
) -> set[str]:
    """Deterministic set of loadable module ids.

    Always includes kernel and the transitive ``dependsOn`` closure of each
    selected suite, then augments with config-derived and explicit capabilities
    (additive). Raises ``ValueError`` for unknown active suite names so an
    unresolved or unsupported profile can never silently produce an empty or
    partial tree.
    """
    suite_ids = {
        m.get("id")
        for m in registry.get("modules", [])
        if isinstance(m, dict) and m.get("layer") == "suite"
    }
    resolved = resolve_active_suite_ids(registry, active_suites)
    unknown_suites = [
        name for name in active_suites
        if name not in suite_ids
        and not any(sid.endswith(f"-{name}") for sid in suite_ids)
    ]
    if unknown_suites:
        raise ValueError(
            "unknown active suite name(s), refusing to generate an empty tree: "
            + ", ".join(sorted(unknown_suites))
        )
    kernel_ids = {
        m.get("id")
        for m in registry.get("modules", [])
        if isinstance(m, dict) and m.get("layer") == "kernel"
    }
    loadable_ids: set[str] = set(kernel_ids)
    for suite in resolved:
        loadable_ids |= transitive_dependencies(registry, suite)
    loadable_ids |= capability_module_ids(registry, active_suites, config)
    loadable_ids |= explicit_capability_module_ids(registry, capabilities)
    return loadable_ids


def inventory_digest(
    registry: dict,
    active_suites: list[str],
    config: Optional[dict] = None,
    capabilities: Optional[list[str]] = None,
) -> str:
    """Return a stable SHA-256 digest of the selected loadable inventory.

    Deterministic across runs for the same registry, suite selection, config,
    and capabilities: the sorted loadable module id set plus the sorted loadable
    asset globs are hashed. Used by the projection benchmark to detect inventory
    drift between profiles and baselines.
    """
    import hashlib

    ids = loadable_module_ids(registry, active_suites, config=config, capabilities=capabilities)
    globs = loadable_asset_globs(registry, ids)
    canonical = json.dumps(
        {"ids": sorted(ids), "globs": sorted(globs)},
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def capability_ids_by_selector(
    registry: dict,
    config: dict,
    active_suites: list[str],
) -> list[str]:
    """Return capability record ids activated for the selection (ordered).

    Additive and deterministic: language selectors derive language packs; empty
    selectors activate when a supported suite is active. Suite eligibility and
    (when present) selector matching both apply. Used by the active manifest
    resolver to record which capabilities are derived vs explicit.
    """
    capabilities = registry.get("capabilities")
    if not isinstance(capabilities, list):
        return []
    resolved: list[str] = []
    for capability in capabilities:
        if not isinstance(capability, dict):
            continue
        if _capability_eligible(capability, active_suites, config or {}):
            capability_id = capability.get("id")
            if capability_id:
                resolved.append(capability_id)
    return sorted(resolved)


def loadable_asset_globs(registry: dict, loadable_ids: set[str]) -> list[str]:
    """Owned-asset globs (directories) for the loadable modules."""
    globs: list[str] = []
    for module in registry.get("modules", []):
        if not isinstance(module, dict) or module.get("id") not in loadable_ids:
            continue
        for pattern in module.get("ownedAssets", []):
            if isinstance(pattern, str):
                globs.append(pattern)
    return sorted(set(globs))


def filtered_manifest(
    registry: dict,
    active_suites: list[str],
    config: Optional[dict] = None,
    capabilities: Optional[list[str]] = None,
    project_snapshot: Optional[Any] = None,
    platforms: Optional[list[str]] = None,
) -> dict:
    """Produce the filtered asset manifest (module ids + loadable globs).

    Note: ``schemaVersion`` was raised to 2 and a ``capabilities`` key was
    added when manifest-driven selection landed; the generator consumes
    ``loadable_modules``/``loadable_asset_globs`` directly, and the authoritative
    resolution artifact is ``.compound-gpid/active-manifest.json`` (see
    ``cg_project_manifest.py`` and ``docs/configuration.md``).
    """
    explicit = capabilities or []
    project_capabilities = {
        str(record["capability"])
        for record in getattr(project_snapshot, "project_records", ())
    }
    canonical_explicit = [
        capability for capability in explicit
        if capability not in project_capabilities
    ]
    loadable = loadable_modules(
        registry,
        active_suites,
        config=config,
        capabilities=canonical_explicit,
    )
    ids = {m["id"] for m in loadable}
    selected_projects = {}
    if project_snapshot is not None:
        selected_projects = project_snapshot.select_project_skills(
            tuple(explicit),
            tuple(active_suites),
            tuple(platforms or ("copilot", "claude-code", "codex", "opencode", "kilo")),
        )
    return {
        "schemaVersion": 2,
        "activeSuites": active_suites,
        "capabilities": capabilities or [],
        "selectedProjectSkills": selected_projects,
        "loadableModules": sorted(ids),
        "loadableAssetGlobs": loadable_asset_globs(registry, ids),
    }


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Compute the context-budget filtered asset manifest."
    )
    parser.add_argument("--root", default=".", help="Project root directory (default: .)")
    parser.add_argument("--source-root", default=None, help="Canonical source root (default: project root)")
    parser.add_argument("--config", default=LOCAL_CONFIG_PATH, help="Relative path to compound-gpid.local.md")
    parser.add_argument("--output", default=None, help="Write filtered manifest JSON to this path")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    if not root.is_dir():
        print(f"Error: project root does not exist or is not a directory: {root}", file=sys.stderr)
        return 2

    source_root = Path(args.source_root).resolve() if args.source_root else root
    try:
        from skill_management.services import registry as registry_service
        combined = registry_service.load_combined_registry_snapshot(root, source_root)
        registry = combined.canonical.to_dict()
    except FileNotFoundError:
        print(f"Error: {MODULE_REGISTRY_PATH} not found at {root}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as exc:
        print(f"Error: {MODULE_REGISTRY_PATH} is malformed JSON: {exc}", file=sys.stderr)
        return 1
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    config_path = root / args.config
    if not config_path.exists():
        print(f"Error: {args.config} not found at {root}", file=sys.stderr)
        return 1
    try:
        config_text = config_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        print(f"Error: could not read {args.config}: {exc}", file=sys.stderr)
        return 1
    try:
        from parsing_utils import parse_strict_config
        parsed = parse_strict_config(config_text)
    except ImportError:
        parsed = None
    if parsed is not None and parsed.errors:
        print("Strict project-config validation failed:", file=sys.stderr)
        for error in parsed.errors:
            print(f"  - {error}", file=sys.stderr)
        return 1
    settings = parsed.settings if parsed is not None else {}
    explicit = parsed.capabilities if parsed is not None else []
    if parsed is not None:
        active = parsed.suites or ["cg"]
    else:  # pragma: no cover - standard environment always ships parsing_utils
        active = read_active_suites(config_text)
    try:
        manifest = filtered_manifest(
            registry,
            active,
            config=settings,
            capabilities=explicit,
            project_snapshot=combined,
        )
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if args.output:
        out = root / args.output
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    else:
        print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
