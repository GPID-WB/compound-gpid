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
from pathlib import Path
from typing import Any, Optional

MODULE_REGISTRY_PATH = ".github/shared/module-registry.json"
LOCAL_CONFIG_PATH = "compound-gpid.local.md"


def read_active_suites(config_text: str) -> list[str]:
    """Extract the ``suites:`` field from a compound-gpid.local.md frontmatter.

    Absent or invalid values default to ``["cg"]`` (backward compatible).
    Supports inline flow lists including quoted elements (e.g.
    ``suites: ["cg", "cr"]``).
    """
    if not config_text.lstrip("\ufeff\r\n").startswith("---"):
        return ["cg"]
    try:
        block = config_text.lstrip("\ufeff\r\n").split("---", 2)[1]
    except IndexError:
        return ["cg"]
    for line in block.splitlines():
        if line.startswith("suites:"):
            raw = line.partition(":")[2].strip()
            cleaned = raw.strip("[]")
            # Split on commas then strip quotes and whitespace per element,
            # matching both [cg, cr] and ["cg", "cr"].
            values = [v.strip().strip("\"' ").replace(" ", "") for v in cleaned.split(",") if v.strip()]
            values = [v for v in values if v]
            if values:
                return values
    return ["cg"]


def resolve_active_suite_ids(registry: dict, active_suites: list[str]) -> set[str]:
    """Map user-facing suite names (e.g. ``cg``, ``cr``) to module ids.

    A suite module matches when its id equals the requested name or ends with
    ``-<name>`` (e.g. ``suite-cg`` matches ``cg``). Names that resolve to no
    suite module are dropped (callers may warn).
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


def _resolve_active_suite_ids(registry: dict, active_suites: list[str]) -> set[str]:
    """Back-compat wrapper: map user-facing suite names to module ids."""
    return resolve_active_suite_ids(registry, active_suites)


def loadable_modules(registry: dict, active_suites: list[str]) -> list[dict]:
    """Modules whose assets are loadable for the active suite configuration."""
    all_ids = {m.get("id") for m in registry.get("modules", []) if isinstance(m, dict)}
    unknown_suites = [s for s in active_suites if s not in all_ids and not any(
        sid.endswith(f"-{s}") for sid in all_ids
    )]
    if unknown_suites:
        raise ValueError(
            "unknown active suite name(s), refusing to generate an empty tree: "
            + ", ".join(sorted(unknown_suites))
        )
    active = _resolve_active_suite_ids(registry, active_suites)
    # Kernel is always loadable.
    kernel_ids = {
        m.get("id")
        for m in registry.get("modules", [])
        if isinstance(m, dict) and m.get("layer") == "kernel"
    }
    loadable_ids: set[str] = set(kernel_ids)
    for suite in active:
        loadable_ids |= transitive_dependencies(registry, suite)
    return [m for m in registry.get("modules", []) if isinstance(m, dict) and m.get("id") in loadable_ids]


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


def filtered_manifest(registry: dict, active_suites: list[str]) -> dict:
    """Produce the filtered asset manifest (module ids + loadable globs)."""
    loadable = loadable_modules(registry, active_suites)
    ids = {m["id"] for m in loadable}
    return {
        "schemaVersion": 1,
        "activeSuites": active_suites,
        "loadableModules": sorted(ids),
        "loadableAssetGlobs": loadable_asset_globs(registry, ids),
    }


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Compute the context-budget filtered asset manifest."
    )
    parser.add_argument("--root", default=".", help="Project root directory (default: .)")
    parser.add_argument("--config", default=LOCAL_CONFIG_PATH, help="Relative path to compound-gpid.local.md")
    parser.add_argument("--output", default=None, help="Write filtered manifest JSON to this path")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    if not root.is_dir():
        print(f"Error: project root does not exist or is not a directory: {root}", file=sys.stderr)
        return 2

    try:
        registry = load_registry(root)
    except FileNotFoundError:
        print(f"Error: {MODULE_REGISTRY_PATH} not found at {root}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as exc:
        print(f"Error: {MODULE_REGISTRY_PATH} is malformed JSON: {exc}", file=sys.stderr)
        return 1

    config_path = root / args.config
    config_text = config_path.read_text(encoding="utf-8") if config_path.exists() else ""
    active = read_active_suites(config_text)
    manifest = filtered_manifest(registry, active)

    if args.output:
        out = root / args.output
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    else:
        print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
