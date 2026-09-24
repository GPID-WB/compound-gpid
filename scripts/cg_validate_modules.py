#!/usr/bin/env python3
"""cg-validate-modules — Validate the Compound GPID module registry.

Validates the three-layer module registry (kernel / capability packs / suites)
defined in ``.github/shared/module-registry.json``: schema conformance, unique
module ids, that every declared asset exists, that every canonical asset has
exactly one owning module, that dependency edges respect layer rules, and that
the dependency graph is acyclic.

Usage:
    python3 scripts/cg_validate_modules.py [--root <path>] [--report]
    python3 scripts/cg_validate_modules.py [--root <path>] --check-ownership
    python3 scripts/cg_validate_modules.py [--root <path>] --check-dependencies
    python3 scripts/cg_validate_modules.py [--root <path>] --check-cross-suite

Exit codes:
    0  All selected checks pass.
    1  Validation failed (including missing/malformed registry).
    2  Missing or invalid project root.

Requirements: Python 3.8+, stdlib only.
"""
from __future__ import annotations

import sys

if sys.version_info < (3, 8):
    print(
        "cg-validate-modules requires Python 3.8+; found "
        f"{sys.version.split()[0]}",
        file=sys.stderr,
    )
    sys.exit(1)

import argparse
import functools
import json
import re
from fnmatch import fnmatchcase
from pathlib import Path, PurePosixPath
from typing import Dict, Iterable, List, Optional, Tuple

MODULE_REGISTRY_PATH = ".github/shared/module-registry.json"
VALID_LAYERS = {"kernel", "capability", "suite"}

# Reuses the generator's canonical runtime dependency regex (Phase 2, Step 4).
CANONICAL_RUNTIME_PATH_PATTERN = re.compile(
    r"(?<![A-Za-z0-9_.-])\.github/(prompts|skills|agents|instructions|shared)/"
    r"[^\s`'\"<>)/][^\s`'\"<>)]*"
)
# Name-form references: @agent and <prefix>-skill-<name> (namespace-agnostic).
AGENT_REF_PATTERN = re.compile(r"@(?:cg|cr)-[a-z0-9-]+")
SKILL_REF_PATTERN = re.compile(r"(?<![A-Za-z0-9_.-])(?:cg|cr)-skill-[a-z0-9-]+")

# Lower layers each layer may depend on, per R4 (Active-Suite Dependency Rules).
_ALLOWED_DEPENDENCY_LAYERS = {
    "kernel": set(),
    "capability": {"kernel", "capability"},
    "suite": {"kernel", "capability"},
}

MODULE_ID_PATTERN = re.compile(r"^[a-z][a-z0-9-]*$")

# ---------------------------------------------------------------------------
# Canonical asset enumeration (mirrors cg_generate_targets.py)
# ---------------------------------------------------------------------------


def _canonical_categories(root: Path) -> Dict[str, List[str]]:
    """Return POSIX repository-relative canonical asset paths per category."""
    assets: Dict[str, List[str]] = {
        "prompts": [],
        "agents": [],
        "skills": [],
        "instructions": [],
        "shared": [],
    }
    prompt_globs = [".github/prompts/*.prompt.md", ".github/prompts/*.md"]
    agent_globs = [".github/agents/*.agent.md"]
    skill_globs = [".github/skills/*/SKILL.md"]
    instruction_globs = [".github/instructions/*.instructions.md"]
    shared_globs = [".github/shared/*"]
    for category, globs in (
        ("prompts", prompt_globs),
        ("agents", agent_globs),
        ("skills", skill_globs),
        ("instructions", instruction_globs),
        ("shared", shared_globs),
    ):
        for pattern in globs:
            for path in sorted(root.glob(pattern)):
                rel = path.relative_to(root).as_posix()
                if category == "prompts" and rel in assets["prompts"]:
                    continue
                if category == "shared" and path.name.startswith("."):
                    continue
                assets[category].append(rel)
    return assets


@functools.lru_cache(maxsize=16)
def canonical_assets(root: Path) -> List[str]:
    """Return every canonical asset path (POSIX, repo-relative), sorted.

    Memoized: the inventory is re-scanned repeatedly by the reference scanners;
    the tree is effectively immutable within a validation run.
    """
    collected = set()
    for paths in _canonical_categories(root).values():
        collected.update(paths)
    return sorted(collected)


def _normalize_path(path: str) -> str:
    """Normalize to a POSIX, '.'-free, repository-relative path."""
    value = PurePosixPath(path.replace("\\", "/")).as_posix()
    return value.lstrip("./")


def _glob_match(pattern: str, asset: str) -> bool:
    """Return whether an owned-assets glob pattern matches a canonical asset.

    Directory patterns are given with a trailing '/'; they match any asset at
    or below the directory. File patterns use per-component fnmatch semantics
    so '*' never crosses a '/' boundary.
    """
    is_dir = pattern.endswith("/")
    pattern = _normalize_path(pattern)
    asset = _normalize_path(asset)
    pparts = PurePosixPath(pattern).parts
    aparts = PurePosixPath(asset).parts
    if len(aparts) < len(pparts):
        return False
    if len(aparts) == len(pparts) and not is_dir:
        return all(fnmatchcase(ac, pc) for pc, ac in zip(pparts, aparts))
    if is_dir:
        return all(fnmatchcase(ac, pc) for pc, ac in zip(pparts, aparts))
    return False


def _frontmatter_owner(content: str) -> Optional[str]:
    """Extract an optional ``owner:`` field from canonical frontmatter."""
    if not content.lstrip("\ufeff\r\n").startswith("---"):
        return None
    try:
        block = content.lstrip("\ufeff\r\n").split("---", 2)[1]
    except IndexError:
        return None
    for line in block.splitlines():
        if line.startswith("owner:"):
            value = line.partition(":")[2].strip().strip("\"'")
            return value or None
    return None


# ---------------------------------------------------------------------------
# Schema validation
# ---------------------------------------------------------------------------


def load_registry(root: Path) -> Tuple[Optional[dict], Optional[str]]:
    """Load and parse the module registry. Returns (data, error)."""
    path = root / MODULE_REGISTRY_PATH
    if not path.exists():
        return None, f"Module registry not found at: {MODULE_REGISTRY_PATH}"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return None, f"Module registry is malformed JSON: {exc}"
    if not isinstance(data, dict):
        return None, "Module registry must be a JSON object"
    return data, None


def validate_registry_schema(registry: dict) -> List[str]:
    """Validate the registry structure. Returns list of error messages."""
    errors: List[str] = []
    if "schemaVersion" not in registry:
        errors.append("Missing required field: schemaVersion")
    elif type(registry["schemaVersion"]) is not int or registry["schemaVersion"] != 1:
        errors.append("schemaVersion must be the integer 1")
    if "description" not in registry:
        errors.append("Missing required field: description")
    elif not isinstance(registry["description"], str):
        errors.append("description must be a string")
    modules = registry.get("modules")
    if "modules" not in registry:
        errors.append("Missing required field: modules")
        return errors
    if not isinstance(modules, list) or not modules:
        errors.append("modules must be a non-empty array")
        return errors

    seen_ids: set[str] = set()
    for index, module in enumerate(modules):
        prefix = f"modules[{index}]"
        if not isinstance(module, dict):
            errors.append(f"{prefix}: must be an object")
            continue
        mid = module.get("id")
        if not isinstance(mid, str) or not mid:
            errors.append(f"{prefix}: id must be a non-empty string")
        elif not MODULE_ID_PATTERN.fullmatch(mid):
            errors.append(f"{prefix}: id must start with a lowercase letter and contain only lowercase letters, digits, and hyphens")
        elif mid in seen_ids:
            errors.append(f"{prefix}: duplicate module id '{mid}'")
        else:
            seen_ids.add(mid)

        layer = module.get("layer")
        if layer not in VALID_LAYERS:
            errors.append(f"{prefix}: layer must be one of {sorted(VALID_LAYERS)}, got {layer!r}")

        for field in ("displayName", "description", "dependsOn", "ownedAssets"):
            if field not in module:
                errors.append(f"{prefix}: missing required field '{field}'")

        depends_on = module.get("dependsOn", [])
        if "dependsOn" in module and not isinstance(depends_on, list):
            errors.append(f"{prefix}.dependsOn: must be an array")
        elif "dependsOn" in module:
            for dep_index, dep in enumerate(depends_on):
                if not isinstance(dep, str) or not dep:
                    errors.append(f"{prefix}.dependsOn[{dep_index}]: must be a non-empty string")

        owned_assets = module.get("ownedAssets", [])
        if "ownedAssets" in module and not isinstance(owned_assets, list):
            errors.append(f"{prefix}.ownedAssets: must be an array")
        else:
            for asset_index, asset in enumerate(owned_assets):
                if isinstance(asset, str) and asset:
                    continue
                errors.append(f"{prefix}.ownedAssets[{asset_index}]: must be a non-empty string")

        ambiguous = module.get("ambiguous", [])
        if not isinstance(ambiguous, list):
            errors.append(f"{prefix}.ambiguous: must be an array")
        else:
            for amb_index, entry in enumerate(ambiguous):
                if not isinstance(entry, dict) or not isinstance(entry.get("asset"), str):
                    errors.append(f"{prefix}.ambiguous[{amb_index}]: must be an object with an 'asset' string")
                elif not isinstance(entry.get("note"), str):
                    errors.append(f"{prefix}.ambiguous[{amb_index}]: must include a 'note' resolution string")
    for module in modules:
        if not isinstance(module, dict):
            continue
        mid = module.get("id")
        if not mid:
            continue
        for dep in module.get("dependsOn", []):
            if isinstance(dep, str) and dep not in seen_ids:
                errors.append(f"module '{mid}' depends on unknown module '{dep}'")
    return errors


def _layer_of(registry: dict, module_id: str) -> Optional[str]:
    for module in registry.get("modules", []):
        if isinstance(module, dict) and module.get("id") == module_id:
            return module.get("layer")
    return None


def check_layer_rules(registry: dict) -> List[str]:
    """Verify dependency edges respect layer rules and ids resolve."""
    errors: List[str] = []
    ids = {module.get("id") for module in registry.get("modules", []) if isinstance(module, dict)}
    adjacency: Dict[str, List[str]] = {}
    for module in registry.get("modules", []):
        if not isinstance(module, dict):
            continue
        mid = module.get("id")
        if not mid:
            continue
        layer = module.get("layer")
        adjacency[mid] = []
        for dep in module.get("dependsOn", []):
            if dep not in ids:
                errors.append(f"module '{mid}' depends on unknown module '{dep}'")
                continue
            adjacency[mid].append(dep)
            dep_layer = _layer_of(registry, dep)
            allowed = _ALLOWED_DEPENDENCY_LAYERS.get(layer, set())
            if dep_layer not in allowed:
                errors.append(
                    f"module '{mid}' ({layer}) depends on '{dep}' ({dep_layer}); "
                    f"allowed dependency layers: {sorted(allowed) or 'none'}"
                )
    cycle = _first_cycle(adjacency)
    if cycle:
        errors.append("dependency graph contains a cycle: " + " -> ".join(cycle))
    return errors


def _first_cycle(adjacency: Dict[str, List[str]]) -> Optional[List[str]]:
    """Return one cycle in the dependency graph, or None if acyclic."""
    WHITE, GRAY, BLACK = 0, 1, 2
    color: Dict[str, int] = {}
    stack: List[str] = []
    cycle_path: List[str] = []

    def visit(node: str) -> bool:
        color[node] = GRAY
        stack.append(node)
        for neighbor in adjacency.get(node, []):
            if neighbor not in color:
                color[neighbor] = WHITE
            if color[neighbor] == GRAY:
                start = stack.index(neighbor)
                cycle_path.extend(stack[start:] + [neighbor])
                return True
            if color[neighbor] == WHITE and visit(neighbor):
                return True
        stack.pop()
        color[node] = BLACK
        return False

    for node in adjacency:
        if color.get(node, WHITE) == WHITE:
            if visit(node):
                return cycle_path
    return None


# ---------------------------------------------------------------------------
# Ownership closure
# ---------------------------------------------------------------------------


def check_owned_assets_exist(registry: dict, assets: Iterable[str]) -> List[str]:
    """Verify every declared owned-assets pattern matches a canonical asset."""
    errors: List[str] = []
    asset_set = set(assets)
    for module in registry.get("modules", []):
        if not isinstance(module, dict):
            continue
        mid = module.get("id")
        for pattern in module.get("ownedAssets", []):
            if not isinstance(pattern, str):
                continue
            if not any(_glob_match(pattern, asset) for asset in asset_set):
                errors.append(f"module '{mid}' declares owned asset '{pattern}' but no canonical asset matches")
    return errors


def check_ownership_closure(registry: dict, assets: Iterable[str]) -> List[str]:
    """Verify every canonical asset has exactly one owning module."""
    errors: List[str] = []
    owners_by_asset: Dict[str, List[str]] = {asset: [] for asset in assets}
    for module in registry.get("modules", []):
        if not isinstance(module, dict):
            continue
        mid = module.get("id")
        for pattern in module.get("ownedAssets", []):
            if not isinstance(pattern, str):
                continue
            for asset in owners_by_asset:
                if _glob_match(pattern, asset):
                    owners_by_asset[asset].append(mid)
    for asset in sorted(owners_by_asset):
        owners = owners_by_asset[asset]
        if not owners:
            errors.append(f"canonical asset has no owning module: {asset}")
        elif len(owners) > 1:
            errors.append(f"canonical asset is owned by more than one module: {asset} -> {sorted(owners)}")
    return errors


def check_frontmatter_ownership(root: Path, registry: dict, assets: Iterable[str]) -> List[str]:
    """Cross-validate optional frontmatter ``owner:`` fields against the registry."""
    errors: List[str] = []
    owners_by_asset: Dict[str, List[str]] = {asset: [] for asset in assets}
    for module in registry.get("modules", []):
        if not isinstance(module, dict):
            continue
        mid = module.get("id")
        for pattern in module.get("ownedAssets", []):
            if not isinstance(pattern, str):
                continue
            for asset in owners_by_asset:
                if _glob_match(pattern, asset):
                    owners_by_asset[asset].append(mid)
    for asset in sorted(owners_by_asset):
        owners = owners_by_asset[asset]
        if len(owners) != 1:
            continue
        expected = owners[0]
        path = root / asset
        if not path.exists():
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        declared = _frontmatter_owner(content)
        if declared is not None and declared != expected:
            errors.append(
                f"frontmatter owner '{declared}' on {asset} disagrees with "
                f"registry owner '{expected}'"
            )
    return errors


def check_no_physical_relocation(root: Path) -> List[str]:
    """C2: verify .github/ remains the canonical runtime source.

    No physical package-tree relocation to packages/kernel/, packages/suites/,
    etc. The registry may declare modules over the canonical tree only.
    """
    errors: List[str] = []
    packages_roots = sorted(p for p in root.glob("packages/*/") if p.is_dir())
    if packages_roots:
        names = ", ".join(p.relative_to(root).as_posix() for p in packages_roots)
        errors.append(
            "C2 violation: physical package relocation detected under packages/: "
            f"{names}. The registry must stay logical over .github/."
        )
    return errors


def check_ambiguous_entries(registry: dict) -> List[str]:
    """Require every ambiguous entry to carry a resolution note."""
    errors: List[str] = []
    for module in registry.get("modules", []):
        if not isinstance(module, dict):
            continue
        mid = module.get("id")
        for entry in module.get("ambiguous", []):
            if isinstance(entry, dict):
                if "note" not in entry or not isinstance(entry["note"], str) or not entry["note"]:
                    errors.append(
                        f"module '{mid}' ambiguous asset {entry.get('asset')!r} lacks a resolution note"
                    )
            else:
                errors.append(f"module '{mid}' ambiguous entry must be an object with 'asset' and 'note'")
    return errors


def empty_module_warnings(registry: dict) -> List[str]:
    """Return warnings for modules that declare no owned assets."""
    warnings: List[str] = []
    for module in registry.get("modules", []):
        if not isinstance(module, dict):
            continue
        mid = module.get("id")
        owned_assets = module.get("ownedAssets", [])
        if not isinstance(owned_assets, list) or not owned_assets:
            warnings.append(f"module '{mid}' declares no owned assets (empty module)")
    return warnings


# ---------------------------------------------------------------------------
# Dependency closure and cross-suite reference checks (Phase 2, Step 4)
# ---------------------------------------------------------------------------


def _module_by_id(registry: dict, module_id: str) -> Optional[dict]:
    for module in registry.get("modules", []):
        if isinstance(module, dict) and module.get("id") == module_id:
            return module
    return None


def _resolve_asset_owner(registry: dict, asset: str) -> Optional[str]:
    """Map a canonical path to its owning module via registry ownedAssets globs."""
    owners: List[str] = []
    for module in registry.get("modules", []):
        if not isinstance(module, dict):
            continue
        mid = module.get("id")
        for pattern in module.get("ownedAssets", []):
            if isinstance(pattern, str) and _glob_match(pattern, asset):
                owners.append(mid)
    unique = sorted(set(owners))
    if len(unique) == 1:
        return unique[0]
    return None


def _owner_map(registry: dict, assets: Iterable[str]) -> Dict[str, Optional[str]]:
    """Build asset -> owning module (single-owner) once, for O(1) lookups."""
    mapping: Dict[str, Optional[str]] = {}
    for asset in assets:
        mapping[asset] = _resolve_asset_owner(registry, asset)
    return mapping


def _transitive_dependency_closure(registry: dict, module_id: str) -> set[str]:
    """Full recursive dependency closure for a module (dependsOn + theirs)."""
    closure: set[str] = set()
    frontier = list(_module_by_id(registry, module_id).get("dependsOn", []) if _module_by_id(registry, module_id) else [])
    while frontier:
        dep = frontier.pop()
        if dep in closure:
            continue
        closure.add(dep)
        dep_module = _module_by_id(registry, dep)
        if dep_module:
            frontier.extend(dep_module.get("dependsOn", []))
    return closure


def _resolve_name_reference(
    registry: dict,
    name: str,
    assets: Optional[Iterable[str]] = None,
) -> Optional[str]:
    """Map a bare agent or skill name to its canonical asset path, if owned.

    Accepts ``@cg-<name>`` / ``@cr-<name>`` agent references and
    ``<prefix>-skill-<name>`` skill references. Returns the canonical repo
    path (e.g. ``.github/agents/cg-roadmap.agent.md``) or None.
    """
    asset_set = set(assets) if assets is not None else set(canonical_assets("."))
    if name.startswith("@"):
        agent_name = name[1:]
        candidate = f".github/agents/{agent_name}.agent.md"
        return candidate if candidate in asset_set else None
    if "-skill-" in name:
        candidate = f".github/skills/{name}/SKILL.md"
        return candidate if candidate in asset_set else None
    return None


def _strip_fenced_code(text: str) -> str:
    """Remove closed or unterminated Markdown fenced code blocks."""
    output: list[str] = []
    fence_character: Optional[str] = None
    fence_length = 0
    for line in text.splitlines(keepends=True):
        match = re.match(r"^[ \t]{0,3}(`{3,}|~{3,})", line)
        if fence_character is None:
            if match:
                fence_character = match.group(1)[0]
                fence_length = len(match.group(1))
            else:
                output.append(line)
        elif match and match.group(1)[0] == fence_character and len(match.group(1)) >= fence_length:
            fence_character = None
            fence_length = 0
    return "".join(output)


def _module_references(
    root: Path,
    registry: dict,
    module_id: str,
    owners: Optional[Dict[str, Optional[str]]] = None,
    assets: Optional[Iterable[str]] = None,
) -> Dict[str, List[str]]:
    """Scan one module's owned canonical asset bodies for references.

    Returns {referenced_path: [owning_module_ids...]} for each reference that
    resolves to a known canonical asset. Detects explicit ``.github/...`` path
    references; the caller decides which suffix forms are load-bearing.
    """
    module = _module_by_id(registry, module_id)
    if module is None:
        return {}
    if owners is None or assets is None:
        assets = canonical_assets(root)
        owners = _owner_map(registry, assets)
    referenced: Dict[str, List[str]] = {}
    for pattern in module.get("ownedAssets", []):
        if not isinstance(pattern, str):
            continue
        for canonical in assets:
            if not _glob_match(pattern, canonical):
                continue
            path = root / canonical
            if not path.exists():
                continue
            if canonical == "github/shared/module-registry.json" or canonical == ".github/shared/module-registry.json":
                # The registry is tooling data; its ownedAssets glob strings are
                # declarations, not runtime references.
                continue
            try:
                content = _strip_fenced_code(path.read_text(encoding="utf-8"))
            except (OSError, UnicodeDecodeError):
                continue
            for match in CANONICAL_RUNTIME_PATH_PATTERN.finditer(content):
                reference = ".github/" + match.group(0).removeprefix(".github/").rstrip(".,;:")
                owner = owners.get(reference)
                if owner:
                    referenced.setdefault(reference, []).append(owner)
    return referenced


def _module_name_references(
    root: Path,
    registry: dict,
    module_id: str,
    owners: Optional[Dict[str, Optional[str]]] = None,
    assets: Optional[Iterable[str]] = None,
) -> Dict[str, List[str]]:
    """Scan for name-form references (@agent and <prefix>-skill-<name>).

    Used by the cross-suite gate to catch couplings that path-form scanning
    misses (e.g. a cr-* prompt dispatching @cg-* agents by bare name).
    """
    module = _module_by_id(registry, module_id)
    if module is None:
        return {}
    if owners is None or assets is None:
        assets = canonical_assets(root)
        owners = _owner_map(registry, assets)
    asset_set = set(assets)
    referenced: Dict[str, List[str]] = {}
    name_patterns = (AGENT_REF_PATTERN, SKILL_REF_PATTERN)
    for pattern in module.get("ownedAssets", []):
        if not isinstance(pattern, str):
            continue
        for canonical in assets:
            if not _glob_match(pattern, canonical):
                continue
            path = root / canonical
            if not path.exists():
                continue
            if canonical.endswith("module-registry.json"):
                continue
            try:
                content = _strip_fenced_code(path.read_text(encoding="utf-8"))
            except (OSError, UnicodeDecodeError):
                continue
            for name_re in name_patterns:
                for name_match in name_re.finditer(content):
                    reference = _resolve_name_reference(registry, name_match.group(0), asset_set)
                    if reference:
                        owner = owners.get(reference)
                        if owner:
                            referenced.setdefault(reference, []).append(owner)
    return referenced


def check_cross_suite_references(root: Path) -> List[str]:
    """V9/R4 gate: no asset in one suite references an asset owned by another
    suite, except through a module the referencing suite depends on (directly
    or transitively via kernel/capability packs). Also fails on cycles/layer
    violations and on references outside the referencing module's closure.
    """
    registry, error = load_registry(root)
    if error:
        return [error]
    assert registry is not None
    errors = validate_registry_schema(registry)
    if errors:
        return errors
    errors.extend(check_layer_rules(registry))

    suites = sorted(
        module.get("id")
        for module in registry.get("modules", [])
        if isinstance(module, dict) and module.get("layer") == "suite"
    )
    assets = list(canonical_assets(root))
    owner_map = _owner_map(registry, assets)
    for suite_id in suites:
        closure = _transitive_dependency_closure(registry, suite_id)
        refs = dict(_module_references(root, registry, suite_id, owner_map, assets))
        for reference, ref_owners in _module_name_references(root, registry, suite_id, owner_map, assets).items():
            refs.setdefault(reference, []).extend(ref_owners)
        for target, ref_owners in sorted(refs.items()):
            owner = sorted(set(ref_owners))[0] if ref_owners else None
            if owner is None:
                continue
            owner_module = _module_by_id(registry, owner)
            if owner_module and owner_module.get("layer") == "suite" and owner != suite_id:
                errors.append(
                    f"suite '{suite_id}' references '{target}' owned by suite '{owner}' "
                    f"(cross-suite reference; route through a capability pack)"
                )
                continue
            if owner not in closure and owner != suite_id:
                errors.append(
                    f"suite '{suite_id}' references '{target}' owned by '{owner}' which is "
                    f"outside its transitive dependency closure"
                )
    return errors


def check_unresolved_dependencies(root: Path) -> List[str]:
    """Phase 2 Step 4: any canonical path referenced by an asset not in the
    referencing module's transitive dependency closure is an error."""
    registry, error = load_registry(root)
    if error:
        return [error]
    assert registry is not None
    errors = validate_registry_schema(registry)
    if errors:
        return errors
    errors.extend(check_layer_rules(registry))
    for module in registry.get("modules", []):
        if not isinstance(module, dict):
            continue
        mid = module.get("id")
        closure = _transitive_dependency_closure(registry, mid)
        refs = _module_references(root, registry, mid)
        for target, owners in sorted(refs.items()):
            owner = sorted(set(owners))[0] if owners else None
            if owner is None or owner == mid or owner in closure:
                continue
            errors.append(
                f"module '{mid}' references '{target}' owned by '{owner}' which is "
                f"outside its transitive dependency closure"
            )
    return errors


# ---------------------------------------------------------------------------
# Aggregate checks and report
# ---------------------------------------------------------------------------


def check_ownership(root: Path) -> List[str]:
    """Run schema + ownership checks. Return error messages (empty = valid)."""
    registry, error = load_registry(root)
    if error:
        return [error]
    assert registry is not None
    errors = validate_registry_schema(registry)
    if errors:
        return errors
    errors.extend(check_no_physical_relocation(root))
    assets = canonical_assets(root)
    errors.extend(check_owned_assets_exist(registry, assets))
    errors.extend(check_ownership_closure(registry, assets))
    errors.extend(check_frontmatter_ownership(root, registry, assets))
    errors.extend(check_ambiguous_entries(registry))
    return errors


def check_dependencies(root: Path) -> List[str]:
    """Run schema + dependency + closure checks. Empty list = valid.

    V4: dependency graph acyclic and cross-suite-safe; every canonical runtime
    reference within the referencing module's transitive dependency closure.
    """
    registry, error = load_registry(root)
    if error:
        return [error]
    assert registry is not None
    errors = validate_registry_schema(registry)
    if errors:
        return errors
    errors.extend(check_layer_rules(registry))
    errors.extend(check_unresolved_dependencies(root))
    return errors


def check_cross_suite(root: Path) -> List[str]:
    """V9: verify no direct cross-suite dependency (cr-* <-> cg-* without a
    shared capability pack) and acyclic/layer-safe dependency graph."""
    registry, error = load_registry(root)
    if error:
        return [error]
    assert registry is not None
    errors = validate_registry_schema(registry)
    if errors:
        return errors
    errors.extend(check_layer_rules(registry))
    errors.extend(check_cross_suite_references(root))
    return errors


def _ownership_report(root: Path, registry: dict) -> List[str]:
    """Produce an ownership report table (asset -> module)."""
    lines: List[str] = ["# Module Registry Ownership Report"]
    assets = canonical_assets(root)
    owners_by_asset: Dict[str, List[str]] = {asset: [] for asset in assets}
    for module in registry.get("modules", []):
        if not isinstance(module, dict):
            continue
        mid = module.get("id")
        for pattern in module.get("ownedAssets", []):
            if not isinstance(pattern, str):
                continue
            for asset in sorted(owners_by_asset):
                if _glob_match(pattern, asset):
                    owners_by_asset[asset].append(mid)
    lines.append("")
    lines.append("| Asset | Module |")
    lines.append("|-------|--------|")
    for asset in sorted(owners_by_asset):
        owners = owners_by_asset[asset]
        label = ", ".join(sorted(owners)) if owners else "**UNOWNED**"
        lines.append(f"| `{asset}` | {label} |")
    multi = {a: o for a, o in owners_by_asset.items() if len(o) > 1}
    unowned = [a for a, o in owners_by_asset.items() if not o]
    if multi:
        lines.append("")
        lines.append("## Multi-Owned Assets")
        for asset, owners in sorted(multi.items()):
            lines.append(f"- `{asset}` -> {sorted(owners)}")
    if unowned:
        lines.append("")
        lines.append("## Unowned Assets")
        for asset in unowned:
            lines.append(f"- `{asset}`")
    lines.append("")
    lines.append(f"Total assets: {len(owners_by_asset)}; unowned: {len(unowned)}; multi-owned: {len(multi)}.")
    return lines


def main(
    argv: Optional[List[str]] = None,
    *,
    root_override: Optional[Path] = None,
) -> int:
    parser = argparse.ArgumentParser(
        description="Validate the Compound GPID module registry."
    )
    parser.add_argument("--root", default=".", help="Project root directory (default: current directory)")
    parser.add_argument("--report", action="store_true", help="Print the ownership report and validate")
    parser.add_argument("--check-ownership", action="store_true", help="Run schema + ownership closure checks")
    parser.add_argument("--check-dependencies", action="store_true", help="Run schema + dependency/cycle/layer checks")
    parser.add_argument("--check-cross-suite", action="store_true", help="Run cross-suite dependency checks")
    args = parser.parse_args(argv)

    root = (root_override or Path(args.root)).resolve()
    if not root.is_dir():
        print(f"Error: project root does not exist or is not a directory: {root}", file=sys.stderr)
        return 2

    registry, error = load_registry(root)
    if error:
        print(f"Error: {error}", file=sys.stderr)
        return 1

    assert registry is not None

    if args.report:
        for line in _ownership_report(root, registry):
            print(line)
        errors = check_ownership(root) + check_dependencies(root) + check_cross_suite(root)
    else:
        selected = [
            name for name, flag in (
                ("ownership", args.check_ownership),
                ("dependencies", args.check_dependencies),
                ("cross-suite", args.check_cross_suite),
            )
            if flag
        ]
        if not selected:
            selected = ["ownership", "dependencies", "cross-suite"]
        errors: List[str] = []
        if "ownership" in selected:
            errors.extend(check_ownership(root))
        if "dependencies" in selected:
            errors.extend(check_dependencies(root))
        if "cross-suite" in selected:
            errors.extend(check_cross_suite(root))

    if errors:
        print("Module registry validation failed:", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return 1
    print(f"Validated {MODULE_REGISTRY_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
