#!/usr/bin/env python3
"""cg-generate-targets — Generate native platform trees from canonical .github/ source.

Reads .github/ canonical assets (prompts, agents, skills, instructions, shared
contracts) and .github/shared/target-mapping.json, then emits platform-specific
native trees for Claude Code, Codex, OpenCode, and Kilo.

Usage:
    python3 scripts/cg_generate_targets.py [--root <path>] [--target <platform>] [--all] [--dry-run]
    python3 scripts/cg_generate_targets.py [--root <path>] --all [--active-suites <comma-separated-suite-names>]

Exit codes:
    0  Success.
    1  Fatal error.
    2  Missing or invalid project root.

Requirements: Python 3.8+, stdlib only (no third-party packages); requires scripts/brain/ from this repository.
"""
from __future__ import annotations

import sys

if sys.version_info < (3, 8):
    print(
        f"cg-generate-targets requires Python 3.8+; found {sys.version.split()[0]}",
        file=sys.stderr,
    )
    sys.exit(1)

import argparse
import functools
import hashlib
import json
import os
import re
import stat
import subprocess
import unicodedata
import urllib.parse
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Dict, Iterable, Mapping, Optional, Sequence, Tuple

import secure_fs
from skill_management import paths as path_policy
from skill_management.services import bundles as bundle_service

TARGET_MAPPING_PATH = ".github/shared/target-mapping.json"
MODULE_REGISTRY_PATH = ".github/shared/module-registry.json"


@functools.lru_cache(maxsize=1)
def _get_parse_frontmatter():
    """Lazy-load parse_frontmatter to defer sys.path mutation until first call."""
    scripts_dir = str(Path(__file__).parent)
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    from brain.utils import parse_frontmatter
    return parse_frontmatter


OWNERSHIP_MANIFEST_NAME = ".compound-gpid-generated.json"
MAX_OWNERSHIP_MANIFEST_BYTES = 8 * 1024 * 1024
MAX_CANONICAL_ASSET_BYTES = 4 * 1024 * 1024
MAX_CANONICAL_CONTROL_BYTES = 4 * 1024 * 1024
MAX_SHARED_FILE_BYTES = 4 * 1024 * 1024
MAX_SHARED_TOTAL_BYTES = 64 * 1024 * 1024
MAX_SHARED_FILES = 5000
MAX_SHARED_DEPTH = 32
OWNERSHIP_POLICY_VERSION = 1
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")

CANONICAL_PROMPTS_GLOB = ".github/prompts/*.prompt.md"
CANONICAL_AGENTS_GLOB = ".github/agents/*.agent.md"
CANONICAL_SKILLS_GLOB = ".github/skills/*/SKILL.md"
CANONICAL_INSTRUCTIONS_GLOB = ".github/instructions/*.instructions.md"
MARKDOWN_LINK_PATTERN = bundle_service.MARKDOWN_LINK_PATTERN
MARKDOWN_REFERENCE_PATTERN = bundle_service.MARKDOWN_REFERENCE_PATTERN
CANONICAL_RUNTIME_PATH_PATTERN = re.compile(
    r"(?<![A-Za-z0-9_.-])\.github/(prompts|skills|agents|instructions|shared)/"
    r"[^\s`'\"<>)/][^\s`'\"<>)]*"
)


# ---------------------------------------------------------------------------
# Schema validation (stdlib-only — no jsonschema dependency)
# ---------------------------------------------------------------------------

REQUIRED_TARGET_FIELDS = {"id", "name", "generatedTreePath", "capabilities", "formats", "outputPaths"}
REQUIRED_CAPABILITY_FIELDS = {"supportsNativeCommands", "supportsNativeSkills", "supportsNativeSubagents", "supportsMultiVendorModels", "requiresRootAdapter"}
REQUIRED_FORMAT_FIELDS = {"commandFormat", "skillFormat", "agentFormat"}
REQUIRED_OUTPUT_PATH_FIELDS = {"commands", "skills", "agents", "instructions", "shared"}
VALID_INSTALL_UNIT_TYPES = {"directory", "file"}
VALID_INSTALL_UNIT_STRATEGIES = {"link-directory", "copy-directory", "managed-copy", "generated-copy", "config-copy-or-snippet"}
VALID_PROJECTED_CATEGORIES = {"skills"}
TARGET_ID_PATTERN = re.compile(r"^[a-z][a-z0-9-]*$")
WINDOWS_RESERVED_NAMES = {
    "con", "prn", "aux", "nul",
    *(f"com{i}" for i in range(1, 10)),
    *(f"lpt{i}" for i in range(1, 10)),
}


class PathSafetyError(ValueError):
    """Raised when a mapped path can escape or is not portable."""


class MappingValidationError(ValueError):
    """Raised when target mapping validation fails."""


@dataclass(frozen=True)
class OutputEntry:
    """One fully rendered, deterministic generator output."""

    target_id: str
    destination: str
    source: str
    kind: str
    content: bytes
    sha256: str
    executable: bool
    origin: str = "plugin-canonical"
    provenance_identity: str = "canonical/.github"


@dataclass(frozen=True)
class TargetResult:
    """Sorted rendered outputs for one target."""

    target_id: str
    target_root: str
    entries: Tuple[OutputEntry, ...]


@dataclass(frozen=True)
class GenerationPlan:
    """Complete rendered output plan, ready for a write-only commit."""

    entries: Tuple[OutputEntry, ...]
    by_target: Mapping[str, TargetResult]


@dataclass(frozen=True)
class CommitResult:
    """Outputs committed for selected targets."""

    target_ids: Tuple[str, ...]
    entries: Tuple[OutputEntry, ...]


@dataclass(frozen=True)
class OwnedFile:
    """Validated ownership metadata from a prior target manifest."""

    path: str
    sha256: str


@dataclass(frozen=True)
class TargetCommitPlan:
    """A fully preflighted target mutation."""

    result: TargetResult
    stale_files: Tuple[OwnedFile, ...]
    manifest_path: Path
    manifest_content: bytes
    expected_states: Mapping[str, secure_fs.ExpectedFileState]
    manifest_expected_state: secure_fs.ExpectedFileState


@dataclass(frozen=True)
class CanonicalControlSnapshot:
    """Canonical generator controls captured through secure file handles."""

    target_mapping: dict[str, Any]
    target_mapping_content: bytes
    module_registry: Optional[dict[str, Any]]


def portable_path_key(value: str) -> tuple[str, ...]:
    """Return a case-insensitive, Unicode-normalized Windows-portable key."""
    return path_policy.portable_path_key(value)


def validate_repo_relative_path(label: str, value: Any) -> list[str]:
    """Validate a portable POSIX repository-relative path."""
    return path_policy.validate_repo_relative_path(label, value)


def _portable_path_key(value: str) -> tuple[str, ...]:
    """Compatibility alias for callers migrating to :func:`portable_path_key`."""
    return portable_path_key(value)


def _validate_repo_relative_path(label: str, value: Any) -> list[str]:
    """Compatibility alias for callers migrating to the public path helper."""
    return validate_repo_relative_path(label, value)


def _is_within(path: str, parent: str) -> bool:
    """Return whether a normalized repository path is at or below parent."""
    path_parts = PurePosixPath(path).parts
    parent_parts = PurePosixPath(parent).parts
    return path_parts[:len(parent_parts)] == parent_parts


def _is_python_cache_path(value: str) -> bool:
    """Return whether a path names a Python interpreter cache artifact."""
    parts = PurePosixPath(value.replace("\\", "/")).parts
    return "__pycache__" in parts or parts[-1].casefold().endswith(".pyc")


def _decode_canonical_text(content: bytes) -> str:
    """Decode captured UTF-8 text and normalize all line endings to LF."""
    return (
        content.decode("utf-8-sig", errors="strict")
        .replace("\r\n", "\n")
        .replace("\r", "\n")
    )


def _validate_capabilities(prefix: str, caps: Any) -> list[str]:
    """Validate a target's capabilities block."""
    errors: list[str] = []
    if not isinstance(caps, dict):
        errors.append(f"{prefix}.capabilities: must be an object")
        return errors
    for field in REQUIRED_CAPABILITY_FIELDS:
        if field not in caps:
            errors.append(f"{prefix}.capabilities: missing required field '{field}'")
        elif not isinstance(caps[field], bool):
            errors.append(f"{prefix}.capabilities.{field}: must be a boolean")
    return errors


def _validate_formats(prefix: str, formats: Any) -> list[str]:
    """Validate a target's formats block."""
    errors: list[str] = []
    if not isinstance(formats, dict):
        errors.append(f"{prefix}.formats: must be an object")
        return errors
    for field in REQUIRED_FORMAT_FIELDS:
        if field not in formats:
            errors.append(f"{prefix}.formats: missing required field '{field}'")
        elif not isinstance(formats[field], str):
            errors.append(f"{prefix}.formats.{field}: must be a string")
    if "fallbackAgentFormat" in formats and not isinstance(formats["fallbackAgentFormat"], str):
        errors.append(f"{prefix}.formats.fallbackAgentFormat: must be a string")
    return errors


def _validate_output_paths(prefix: str, output_paths: Any) -> list[str]:
    """Validate a target's outputPaths block."""
    errors: list[str] = []
    if not isinstance(output_paths, dict):
        errors.append(f"{prefix}.outputPaths: must be an object")
        return errors
    for field in REQUIRED_OUTPUT_PATH_FIELDS:
        if field not in output_paths:
            errors.append(f"{prefix}.outputPaths: missing required field '{field}'")
        elif not isinstance(output_paths[field], str):
            errors.append(f"{prefix}.outputPaths.{field}: must be a string")
    return errors


def _validate_install_units(prefix: str, install_units: Any) -> list[str]:
    """Validate optional project-local install-unit metadata for a target."""
    errors: list[str] = []
    if install_units is None:
        return errors
    if not isinstance(install_units, list):
        return [f"{prefix}.installUnits: must be an array"]
    for i, unit in enumerate(install_units):
        unit_prefix = f"{prefix}.installUnits[{i}]"
        if not isinstance(unit, dict):
            errors.append(f"{unit_prefix}: must be an object")
            continue
        for field in ("type", "source", "target", "strategy"):
            if field not in unit:
                errors.append(f"{unit_prefix}: missing required field '{field}'")
        unit_type = unit.get("type")
        if unit_type not in VALID_INSTALL_UNIT_TYPES:
            errors.append(f"{unit_prefix}.type: must be one of {VALID_INSTALL_UNIT_TYPES}, got '{unit_type}'")
        strategy = unit.get("strategy")
        if strategy not in VALID_INSTALL_UNIT_STRATEGIES:
            errors.append(f"{unit_prefix}.strategy: must be one of {VALID_INSTALL_UNIT_STRATEGIES}, got '{strategy}'")
        for field in ("source", "target"):
            if field in unit and not isinstance(unit[field], str):
                errors.append(f"{unit_prefix}.{field}: must be a string")
            elif field in unit:
                errors.extend(_validate_repo_relative_path(f"{unit_prefix}.{field}", unit[field]))
        expected_type = "directory" if strategy in ("link-directory", "copy-directory") else "file"
        if strategy in VALID_INSTALL_UNIT_STRATEGIES and unit_type in VALID_INSTALL_UNIT_TYPES and unit_type != expected_type:
            errors.append(f"{unit_prefix}: strategy '{strategy}' requires type '{expected_type}', not '{unit_type}'")
        if "manualSnippet" in unit and not isinstance(unit["manualSnippet"], str):
            errors.append(f"{unit_prefix}.manualSnippet: must be a string")
    return errors


def _validate_project_roots(prefix: str, project_roots: Any) -> list[str]:
    """Validate the optional declared managed/optional user project roots block."""
    errors: list[str] = []
    if project_roots is None:
        return errors
    if not isinstance(project_roots, dict):
        return [f"{prefix}.projectRoots: must be an object"]
    for kind in ("managed", "optionalUser"):
        entries = project_roots.get(kind)
        if entries is None:
            continue
        if not isinstance(entries, list):
            errors.append(f"{prefix}.projectRoots.{kind}: must be an array")
            continue
        for i, value in enumerate(entries):
            errors.extend(_validate_repo_relative_path(
                f"{prefix}.projectRoots.{kind}[{i}]", value
            ))
    return errors


def _validate_projected_categories(prefix: str, categories: Any) -> list[str]:
    """Validate the optional category-level projection declaration."""
    if categories is None:
        return []
    if not isinstance(categories, list) or not categories:
        return [f"{prefix}.projectedCategories: must be a non-empty array"]
    errors = []
    if len(categories) != len(set(categories)):
        errors.append(f"{prefix}.projectedCategories: entries must be unique")
    unknown = [item for item in categories if item not in VALID_PROJECTED_CATEGORIES]
    if unknown:
        errors.append(
            f"{prefix}.projectedCategories: unsupported categories {unknown!r}"
        )
    return errors


def validate_target_mapping(data: dict[str, Any]) -> list[str]:
    """Validate target-mapping.json structure. Returns list of error messages (empty = valid)."""
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["target mapping must be an object"]
    if "schemaVersion" not in data:
        errors.append("Missing required field: schemaVersion")
    elif type(data["schemaVersion"]) is not int or data["schemaVersion"] != 1:
        errors.append("schemaVersion must be the integer 1")
    if "description" not in data:
        errors.append("Missing required field: description")
    elif not isinstance(data["description"], str):
        errors.append("description must be a string")
    if "targets" not in data:
        errors.append("Missing required field: targets")
        return errors
    if not isinstance(data["targets"], list) or len(data["targets"]) == 0:
        errors.append("targets must be a non-empty array")
        return errors

    seen_ids: set[str] = set()
    generated_roots: list[tuple[str, str]] = []
    for i, target in enumerate(data["targets"]):
        prefix = f"targets[{i}]"
        if not isinstance(target, dict):
            errors.append(f"{prefix}: must be an object")
            continue

        for field in REQUIRED_TARGET_FIELDS:
            if field not in target:
                errors.append(f"{prefix}: missing required field '{field}'")

        if "name" in target and not isinstance(target["name"], str):
            errors.append(f"{prefix}.name: must be a string")

        tid = target.get("id", "")
        if not isinstance(tid, str) or not tid:
            errors.append(f"{prefix}: id must be a non-empty string")
        elif not TARGET_ID_PATTERN.fullmatch(tid):
            errors.append(f"{prefix}: id must start with a lowercase letter and contain only lowercase letters, digits, and hyphens")
        elif tid in seen_ids:
            errors.append(f"{prefix}: duplicate target id '{tid}'")
        else:
            seen_ids.add(tid)

        if "modelMappingMode" in target:
            errors.append(f"{prefix}: modelMappingMode is not supported; targets inherit the user's platform selection")
        if "modelMapping" in target:
            errors.append(f"{prefix}: modelMapping is not supported; targets inherit the user's platform selection")

        errors.extend(_validate_capabilities(prefix, target.get("capabilities", {})))
        errors.extend(_validate_formats(prefix, target.get("formats", {})))
        errors.extend(_validate_output_paths(prefix, target.get("outputPaths", {})))
        errors.extend(_validate_install_units(prefix, target.get("installUnits")))
        errors.extend(_validate_project_roots(prefix, target.get("projectRoots")))
        errors.extend(
            _validate_projected_categories(
                prefix, target.get("projectedCategories")
            )
        )

        gtp = target.get("generatedTreePath")
        if gtp is not None and not isinstance(gtp, str):
            errors.append(f"{prefix}: generatedTreePath must be a string or null")
        elif isinstance(gtp, str):
            errors.extend(_validate_repo_relative_path(f"{prefix}.generatedTreePath", gtp))
            if _is_within(gtp, ".github"):
                errors.append(f"{prefix}.generatedTreePath: generated destination must be outside canonical .github")
            generated_roots.append((prefix, gtp))

        output_paths = target.get("outputPaths")
        if isinstance(output_paths, dict):
            if "modelMapping" in output_paths:
                errors.append(f"{prefix}.outputPaths.modelMapping is not supported")
            output_items: list[tuple[str, str]] = []
            for field, value in output_paths.items():
                label = f"{prefix}.outputPaths.{field}"
                errors.extend(_validate_repo_relative_path(label, value))
                if isinstance(gtp, str) and isinstance(value, str) and not _is_within(value, gtp):
                    errors.append(f"{label}: path is outside generatedTreePath '{gtp}'")
                if isinstance(value, str):
                    output_items.append((label, value))
            for index, (first_label, first) in enumerate(output_items):
                first_key = _portable_path_key(first)
                for second_label, second in output_items[index + 1:]:
                    second_key = _portable_path_key(second)
                    if first_key == second_key:
                        errors.append(f"{first_label} and {second_label}: portable path collision")
                    elif first_key == second_key[:len(first_key)] or second_key == first_key[:len(second_key)]:
                        errors.append(f"{first_label} and {second_label}: file/directory prefix conflict")

        projected_categories = target.get("projectedCategories")
        if isinstance(projected_categories, list):
            roots = target.get("projectRoots", {})
            managed = roots.get("managed", []) if isinstance(roots, dict) else []
            expected_roots = [
                target.get("outputPaths", {}).get(category)
                for category in projected_categories
            ]
            if managed != expected_roots:
                errors.append(
                    f"{prefix}.projectRoots.managed: must exactly match projected category roots"
                )
        elif isinstance(target.get("projectRoots"), dict):
            for kind in ("managed", "optionalUser"):
                for root_value in target["projectRoots"].get(kind, []):
                    if isinstance(root_value, str) and _is_within(root_value, ".github"):
                        errors.append(
                            f"{prefix}.projectRoots.{kind}: .github roots require projectedCategories"
                        )

        if isinstance(gtp, str) and isinstance(target.get("installUnits"), list):
            for unit_index, unit in enumerate(target["installUnits"]):
                if isinstance(unit, dict) and isinstance(unit.get("source"), str) and not _is_within(unit["source"], gtp):
                    errors.append(f"{prefix}.installUnits[{unit_index}].source: path is outside generatedTreePath '{gtp}'")

    for index, (first_prefix, first) in enumerate(generated_roots):
        first_key = _portable_path_key(first)
        for second_prefix, second in generated_roots[index + 1:]:
            second_key = _portable_path_key(second)
            if first_key == second_key[:len(first_key)] or second_key == first_key[:len(second_key)]:
                errors.append(f"{first_prefix} and {second_prefix}: generated tree roots overlap")

    return errors


def validate_mapping_paths(root: Path, data: dict[str, Any]) -> None:
    """Reject mapped paths whose existing filesystem ancestors escape root."""
    root = root.resolve()
    values: list[tuple[str, str]] = []
    for index, target in enumerate(data.get("targets", [])):
        if not isinstance(target, dict):
            continue
        for label, value in [(f"targets[{index}].generatedTreePath", target.get("generatedTreePath"))]:
            if isinstance(value, str):
                values.append((label, value))
        for field, value in target.get("outputPaths", {}).items():
            if isinstance(value, str):
                values.append((f"targets[{index}].outputPaths.{field}", value))
        for unit_index, unit in enumerate(target.get("installUnits", [])):
            if isinstance(unit, dict):
                for field in ("source", "target"):
                    if isinstance(unit.get(field), str):
                        values.append((f"targets[{index}].installUnits[{unit_index}].{field}", unit[field]))
    for label, value in values:
        candidate = root / value
        ancestor = candidate
        while not ancestor.exists() and ancestor != root:
            ancestor = ancestor.parent
        resolved = ancestor.resolve()
        try:
            resolved.relative_to(root)
        except ValueError as exc:
            raise PathSafetyError(f"{label}: existing ancestor escapes repository root") from exc


def build_generation_plan(
    root: Path,
    mapping: dict[str, Any],
    assets: dict[str, list[dict[str, Any]]],
) -> GenerationPlan:
    """Validate and fully render every generated target without writing files."""
    errors = validate_target_mapping(mapping)
    if errors:
        raise MappingValidationError("target-mapping.json validation failed:\n- " + "\n- ".join(errors))
    validate_mapping_paths(root, mapping)
    by_target: dict[str, TargetResult] = {}
    lookups = _build_asset_lookup(assets)
    for target in mapping["targets"]:
        if (
            target.get("generatedTreePath") is None
            and not target.get("projectedCategories")
        ):
            continue
        render_context = (lookups, _runtime_destination_map(target, assets))
        rendered = tuple(sorted(
            (_render_output_entry(target, entry, assets, render_context)
             for entry in build_output_manifest(target, assets)),
            key=lambda entry: entry.destination,
        ))
        _validate_output_namespace(target["id"], rendered)
        target_root = target.get("generatedTreePath")
        if target_root is None:
            target_root = target["projectRoots"]["managed"][0]
        by_target[target["id"]] = TargetResult(target["id"], target_root, rendered)
    entries = tuple(sorted(
        (entry for result in by_target.values() for entry in result.entries),
        key=lambda entry: entry.destination,
    ))
    return GenerationPlan(entries, by_target)


def _validate_output_namespace(
    target_id: str,
    entries: Sequence[OutputEntry],
) -> None:
    """Reject unsafe, colliding, and file/directory-conflicting outputs."""
    paths: list[tuple[tuple[str, ...], OutputEntry]] = []
    for entry in entries:
        errors = _validate_repo_relative_path(
            f"{target_id} output '{entry.destination}'", entry.destination
        )
        if errors:
            raise PathSafetyError("; ".join(errors))
        paths.append((_portable_path_key(entry.destination), entry))

    ordered = sorted(paths, key=lambda item: item[0])
    for (first_key, first), (second_key, second) in zip(ordered, ordered[1:]):
        if first_key == second_key:
            raise ValueError(
                f"{target_id} output namespace collision: "
                f"{first.destination} and {second.destination}"
            )
        if first_key == second_key[:len(first_key)]:
            raise ValueError(
                f"{target_id} output file/directory namespace conflict: "
                f"{first.destination} and {second.destination}"
            )


# ---------------------------------------------------------------------------
# Canonical asset scanning
# ---------------------------------------------------------------------------

def _load_module_registry(root: Path) -> Optional[dict[str, Any]]:
    """Return a securely captured module registry, or ``None`` when absent."""
    try:
        content = secure_fs.secure_read_bytes(
            root,
            MODULE_REGISTRY_PATH,
            reject_hardlinks=True,
            max_bytes=MAX_CANONICAL_CONTROL_BYTES,
        )
    except FileNotFoundError:
        return None
    try:
        data = json.loads(content.decode("utf-8", errors="strict"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def _registry_owned_skill_dir_names(
    root: Path,
    registry: Optional[dict[str, Any]],
) -> Optional[set[str]]:
    """Return skill directory names owned by a registered module.

    Returns None when the module registry is absent (caller falls back to the
    legacy ``cg-skill-*`` glob). When the registry is present, every canonical
    skill directory containing ``SKILL.md`` must match a registry ``ownedAssets``
    pattern; only registered directories are returned for active-suite filtering.
    """
    if registry is None:
        return None
    skills_dir = root / ".github/skills"
    names: set[str] = set()
    if not skills_dir.is_dir():
        return names
    for entry in sorted(skills_dir.iterdir()):
        if not entry.is_dir() or entry.is_symlink():
            continue
        skill_file = entry / "SKILL.md"
        if not skill_file.exists():
            continue
        candidate = f".github/skills/{entry.name}/SKILL.md"
        if any(
            isinstance(pattern, str)
            and path_policy.glob_match(pattern, candidate)
            for module in registry.get("modules", [])
            if isinstance(module, dict)
            for pattern in module.get("ownedAssets", [])
        ):
            names.add(entry.name)
        else:
            raise ValueError(
                "Unowned canonical skill directory contains SKILL.md: "
                f".github/skills/{entry.name}"
            )
    return names


def _loadable_owned_asset_globs(
    active_suites: Optional[Sequence[str]],
    registry: Optional[dict[str, Any]],
) -> Optional[set[str]]:
    """Return owned-asset glob patterns loadable under the active suites.

    With a module registry, omitted suites mean all public suites (cg and cr),
    not every internal module. Repositories without a registry retain the
    legacy unfiltered fixture behavior. Explicit suites derive the loadable
    module set through cg_context_budget.
    """
    if active_suites is None and (
        registry is None or registry.get("schemaVersion") != 2
    ):
        return None
    selected_suites = tuple(active_suites) if active_suites is not None else ("cg", "cr")
    try:
        import cg_context_budget as context
    except ImportError as exc:
        raise ValueError(
            "cg_context_budget.py is required when --active-suites is used"
        ) from exc
    if registry is None:
        raise ValueError(
            "--active-suites requires module-registry.json at .github/shared; "
            "refusing to generate an unfiltered or empty tree"
        )
    loadable = context.loadable_modules(registry, list(selected_suites))
    ids = {module["id"] for module in loadable}
    return set(context.loadable_asset_globs(registry, ids))


def scan_canonical_assets(
    root: Path,
    active_suites: Optional[Sequence[str]] = None,
    loadable_globs: Optional[Iterable[str]] = None,
    control_snapshot: Optional[CanonicalControlSnapshot] = None,
) -> dict[str, list[dict[str, Any]]]:
    """Scan .github/ canonical assets and return structured metadata.

    Returns dict with keys: prompts, agents, skills, instructions.
    Each value is a list of dicts with: path, relative_path, frontmatter, body.

    When ``active_suites`` is provided, only assets owned by loadable modules
    (active suites + their transitive dependencies + kernel) are returned; all
    other assets are excluded from the scan (context-budget enforcement).

    When ``loadable_globs`` is provided, it is used verbatim as the loadable
    owned-asset filter instead of deriving globs from ``active_suites``. This
    lets the manifest-driven projection planner restrict rendering to the
    committed active manifest's resolved closure rather than re-deriving
    selection from raw project config at publish time.
    """
    assets: dict[str, list[dict[str, Any]]] = {
        "prompts": [],
        "agents": [],
        "skills": [],
        "instructions": [],
        "prompt_support": [],
        "shared": [],
    }

    module_registry = (
        control_snapshot.module_registry
        if control_snapshot is not None
        else _load_module_registry(root)
    )
    captured_controls = (
        {TARGET_MAPPING_PATH: control_snapshot.target_mapping_content}
        if control_snapshot is not None
        else {}
    )

    if loadable_globs is not None:
        loadable_filter = set(loadable_globs)
    else:
        loadable_filter = _loadable_owned_asset_globs(
            active_suites,
            module_registry,
        )

    def _is_loadable(rel_path: str) -> bool:
        if loadable_filter is None:
            return True
        return any(
            path_policy.glob_match(pattern, rel_path)
            for pattern in loadable_filter
        )

    required_roots = {
        "prompts": root / ".github/prompts",
        "agents": root / ".github/agents",
        "skills": root / ".github/skills",
        "instructions": root / ".github/instructions",
        "shared": root / ".github/shared",
    }
    for category, path in required_roots.items():
        if path.is_symlink() or not path.is_dir():
            raise ValueError(f"Required canonical {category} root is missing or invalid: {path.relative_to(root)}")

    for pattern, category in [
        (CANONICAL_PROMPTS_GLOB, "prompts"),
        (CANONICAL_AGENTS_GLOB, "agents"),
        (CANONICAL_SKILLS_GLOB, "skills"),
        (CANONICAL_INSTRUCTIONS_GLOB, "instructions"),
        (".github/prompts/*.md", "prompt_support"),
    ]:
        for path in sorted(root.glob(pattern)):
            if category == "prompt_support" and path.name.endswith(".prompt.md"):
                continue
            if path.is_symlink():
                raise ValueError(f"Canonical asset is a symlink: {path.relative_to(root)}")
            if not stat.S_ISREG(path.lstat().st_mode):
                raise ValueError(f"Canonical asset is not a regular file: {path.relative_to(root)}")
            rel = str(path.relative_to(root)).replace("\\", "/")
            if not _is_loadable(rel):
                continue
            asset = {
                "path": str(path),
                "relative_path": rel,
                "filename": path.name,
                "origin": "plugin-canonical",
                "provenance_identity": "canonical/.github",
            }
            if category != "skills":
                content_bytes = secure_fs.secure_read_bytes(
                    root,
                    PurePosixPath(rel),
                    reject_hardlinks=True,
                    max_bytes=MAX_CANONICAL_ASSET_BYTES,
                )
                content = _decode_canonical_text(content_bytes)
                asset["frontmatter"] = _get_parse_frontmatter()(
                    content,
                    source=path,
                )
                asset["body"] = content
            assets[category].append(asset)

    shared_paths = path_policy.inventory_shared_assets(
        root,
        include_globs=loadable_filter,
        max_files=MAX_SHARED_FILES,
        max_depth=MAX_SHARED_DEPTH,
    )
    if len(shared_paths) > MAX_SHARED_FILES:
        raise ValueError(
            f"Canonical shared inventory exceeds {MAX_SHARED_FILES} files"
        )
    total_shared_bytes = 0
    for relative_path in shared_paths:
        if relative_path == ".github/shared/module-registry.json":
            # Registry glob declarations are canonical tooling data, not runtime
            # shared content, and must not be dependency-rewritten.
            continue
        if not _is_loadable(relative_path):
            continue
        relative = PurePosixPath(relative_path)
        if len(relative.parts) > MAX_SHARED_DEPTH:
            raise ValueError(
                f"Canonical shared path exceeds depth {MAX_SHARED_DEPTH}: {relative_path}"
            )
        path = root / Path(*relative.parts)
        content_bytes = captured_controls.get(relative_path)
        if content_bytes is None:
            content_bytes = secure_fs.secure_read_bytes(
                root,
                relative,
                reject_hardlinks=True,
                max_bytes=MAX_SHARED_FILE_BYTES,
            )
        total_shared_bytes += len(content_bytes)
        if total_shared_bytes > MAX_SHARED_TOTAL_BYTES:
            raise ValueError(
                f"Canonical shared content exceeds {MAX_SHARED_TOTAL_BYTES} bytes"
            )
        try:
            content = _decode_canonical_text(content_bytes)
        except UnicodeDecodeError as error:
            raise ValueError(
                f"Canonical shared file is not valid UTF-8: {relative_path}"
            ) from error
        frontmatter = _get_parse_frontmatter()(content, source=path)
        shared_relative_path = path.relative_to(root / ".github/shared").as_posix()
        assets["shared"].append({
            "path": str(path),
            "relative_path": relative_path,
            "frontmatter": frontmatter,
            "body": content,
            "content": content.encode("utf-8"),
            "filename": path.name,
            "category_relative_path": shared_relative_path,
        })

    owned_skill_names = _registry_owned_skill_dir_names(root, module_registry)
    if owned_skill_names is None:
        print(
            "[deprecation] module-registry.json not found; falling back to "
            "cg-skill-* glob-based skill discovery",
            file=sys.stderr,
        )
        assets["skills"] = [
            skill for skill in assets["skills"]
            if Path(skill["path"]).parent.name.startswith("cg-skill-")
        ]
        canonical_skill_roots = tuple(sorted(
            (root / ".github/skills").glob("cg-skill-*")
        ))
    else:
        assets["skills"] = [
            skill for skill in assets["skills"]
            if Path(skill["path"]).parent.name in owned_skill_names
        ]
        canonical_skill_roots = tuple(sorted(
            root / ".github/skills" / name
            for name in sorted(owned_skill_names)
            if _is_loadable(f".github/skills/{name}/SKILL.md")
        ))
    scanned_skill_roots = {Path(skill["path"]).parent for skill in assets["skills"]}
    for skill_root in canonical_skill_roots:
        if skill_root.is_symlink():
            raise ValueError(f"Canonical skill directory is a symlink: {skill_root.name}")
        if not skill_root.is_dir():
            raise ValueError(f"Canonical skill entry is not a directory: {skill_root.name}")
        if skill_root not in scanned_skill_roots:
            raise ValueError(f"Canonical skill is missing regular SKILL.md: {skill_root.name}")

    git_executables = _git_executable_paths(root)
    for skill in assets["skills"]:
        skill_root = Path(skill["path"]).parent
        skill["bundle_files"] = _inventory_skill_bundle(
            root,
            skill_root,
            git_executables=git_executables,
        )
        skill_file = next(
            item for item in skill["bundle_files"]
            if item["bundle_relative_path"] == "SKILL.md"
        )
        skill_content = skill_file["content"].decode(
            "utf-8-sig",
            errors="strict",
        )
        skill["frontmatter"] = _get_parse_frontmatter()(
            skill_content,
            source=Path(skill["path"]),
        )
        skill["body"] = skill_content
        skill["executable"] = skill_file["executable"]
        skill["origin"] = "plugin-canonical"
        skill["provenance_identity"] = "canonical/.github"
        _validate_bundle_markdown_references(skill["bundle_files"])

    for category in required_roots:
        if not assets[category] and active_suites is None and loadable_globs is None:
            raise ValueError(f"Required canonical {category} inventory is empty")

    return assets


def _git_executable_paths(root: Path) -> Optional[set[str]]:
    """Return executable paths from the Git index, or None outside Git."""
    try:
        top_level = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
            stdin=subprocess.DEVNULL,
        )
        if (
            top_level.returncode != 0
            or Path(top_level.stdout.strip()).resolve(strict=True) != root.resolve(strict=True)
        ):
            return None
        result = subprocess.run(
            ["git", "-C", str(root), "ls-files", "--stage", "--", ".github/skills"],
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
            stdin=subprocess.DEVNULL,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    executable = set()
    for line in result.stdout.splitlines():
        metadata, separator, path = line.partition("\t")
        if separator and metadata.split(" ", 1)[0] == "100755":
            executable.add(path.replace("\\", "/"))
    return executable


def _inventory_skill_bundle(
    root: Path,
    skill_root: Path,
    *,
    git_executables: Optional[set[str]] = None,
) -> list[dict[str, Any]]:
    """Inventory regular files below a skill without following filesystem links."""
    source_path = skill_root.relative_to(root).as_posix()
    inventory = bundle_service.inventory_bundle(
        root,
        source_path,
        origin="plugin-canonical",
        executable_paths=tuple(git_executables) if git_executables is not None else None,
        validate_frontmatter=False,
    )
    return [
        {
            "path": str(root / item.source_path),
            "relative_path": item.source_path,
            "bundle_relative_path": item.bundle_path,
            "content": bundle_service.normalized_content(item),
            "executable": item.executable,
            "origin": inventory.origin,
            "provenance_identity": "canonical/.github",
        }
        for item in inventory.files
    ]


def skill_asset_from_inventory(
    inventory: bundle_service.BundleInventory,
    *,
    provenance_identity: str,
    supported_platforms: Optional[Sequence[str]] = None,
) -> dict[str, Any]:
    """Convert one validated bundle inventory to renderer-neutral skill data.

    Args:
        inventory: Complete canonical or project bundle inventory.
        provenance_identity: Stable redacted provenance identity.
        supported_platforms: Optional platform eligibility restriction.

    Returns:
        A skill asset accepted by the existing target renderer.

    Raises:
        ValueError: If the inventory has no UTF-8 ``SKILL.md`` file.

    Example:
        ``skill_asset_from_inventory(project_bundle, provenance_identity="repo@sha")``
    """
    bundle_files = []
    skill_content = None
    for item in inventory.files:
        content = bundle_service.normalized_content(item)
        if item.bundle_path == "SKILL.md":
            try:
                skill_content = content.decode("utf-8")
            except UnicodeDecodeError as error:
                raise ValueError(
                    f"Skill entry is not valid UTF-8: {item.source_path}"
                ) from error
        bundle_files.append(
            {
                "path": item.source_path,
                "relative_path": item.source_path,
                "bundle_relative_path": item.bundle_path,
                "content": content,
                "executable": item.executable,
                "origin": inventory.origin,
                "provenance_identity": provenance_identity,
            }
        )
    if skill_content is None:
        raise ValueError(f"Skill bundle has no SKILL.md: {inventory.source_path}")
    skill_file = next(
        item for item in bundle_files if item["bundle_relative_path"] == "SKILL.md"
    )
    return {
        "path": str(Path(inventory.source_path) / "SKILL.md"),
        "relative_path": f"{inventory.source_path}/SKILL.md",
        "frontmatter": dict(inventory.frontmatter),
        "body": skill_content,
        "filename": "SKILL.md",
        "bundle_files": bundle_files,
        "executable": skill_file["executable"],
        "origin": inventory.origin,
        "provenance_identity": provenance_identity,
        "supported_platforms": (
            tuple(supported_platforms) if supported_platforms is not None else None
        ),
    }


def add_bundle_inventories(
    assets: dict[str, list[dict[str, Any]]],
    inventories: Sequence[bundle_service.BundleInventory],
    *,
    provenance_identities: Mapping[str, str],
    supported_platforms: Mapping[str, Sequence[str]],
) -> dict[str, list[dict[str, Any]]]:
    """Return detached renderer assets with validated bundles added.

    Args:
        assets: Existing canonical renderer asset inventory.
        inventories: Additional source-neutral bundle inventories.
        provenance_identities: Stable identity by bundle identifier.
        supported_platforms: Eligibility set by bundle identifier.

    Returns:
        Detached assets with a deterministic combined skill list.

    Raises:
        ValueError: If source or destination identities collide portably.

    Example:
        ``combined = add_bundle_inventories(canonical, project_bundles, ...)``
    """
    result = {key: list(value) for key, value in assets.items()}
    skills = list(result.get("skills", []))
    seen = {
        path_policy.portable_path_key(Path(item["relative_path"]).parent.name):
        item["relative_path"]
        for item in skills
    }
    for inventory in inventories:
        key = path_policy.portable_path_key(inventory.identifier)
        if key in seen:
            raise ValueError(
                "Skill output identity collision between origins: "
                f"{seen[key]} and {inventory.source_path}"
            )
        identity = provenance_identities.get(inventory.identifier)
        if not identity:
            raise ValueError(
                f"Missing provenance identity for bundle {inventory.identifier}"
            )
        asset = skill_asset_from_inventory(
            inventory,
            provenance_identity=identity,
            supported_platforms=supported_platforms.get(inventory.identifier, ()),
        )
        skills.append(asset)
        seen[key] = asset["relative_path"]
    result["skills"] = sorted(skills, key=lambda item: item["relative_path"])
    return result


def replace_bundle_inventories(
    assets: dict[str, list[dict[str, Any]]],
    inventories: Sequence[bundle_service.BundleInventory],
    *,
    provenance_identities: Mapping[str, str],
    supported_platforms: Mapping[str, Sequence[str]],
) -> dict[str, list[dict[str, Any]]]:
    """Replace selected canonical skill assets with staged inventories.

    This is the pure counterpart to canonical lifecycle publication. It lets
    manifest and projection planning render exact future bytes before source
    files are live while retaining the existing platform renderer.
    """
    identifiers = {item.identifier for item in inventories}
    detached = {key: list(value) for key, value in assets.items()}
    detached["skills"] = [
        item
        for item in detached.get("skills", [])
        if Path(item["relative_path"]).parent.name not in identifiers
    ]
    return add_bundle_inventories(
        detached,
        inventories,
        provenance_identities=provenance_identities,
        supported_platforms=supported_platforms,
    )


def _skill_bundle_content(path: Path) -> bytes:
    """Compatibility shim for shared deterministic bundle normalization."""
    content = path.read_bytes()
    file = bundle_service.BundleFile(
        path.as_posix(),
        path.name,
        content,
        hashlib.sha256(content).hexdigest(),
        False,
    )
    return bundle_service.normalized_content(file)


def _validate_bundle_markdown_references(
    bundle_files: list[dict[str, Any]],
) -> None:
    """Validate local Markdown references against files in one skill bundle."""
    files = tuple(
        bundle_service.BundleFile(
            item["relative_path"],
            item["bundle_relative_path"],
            item["content"],
            hashlib.sha256(item["content"]).hexdigest(),
            bool(item.get("executable", False)),
        )
        for item in bundle_files
    )
    inventory = bundle_service.BundleInventory(
        "fixture",
        ".github/skills/fixture",
        "plugin-canonical",
        {},
        files,
        "0" * 64,
    )
    issues = bundle_service.validate_markdown_references(inventory)
    if issues:
        issue = issues[0]
        raise ValueError(f"{issue.message}: {issue.path}")


def _strip_fenced_code(text: str) -> str:
    """Compatibility shim for the shared Markdown reference service."""
    return bundle_service.strip_fenced_code(text)


def _load_target_mapping_snapshot(root: Path) -> tuple[dict[str, Any], bytes]:
    """Securely capture and parse target-mapping.json exactly once."""
    mapping_path = root / TARGET_MAPPING_PATH
    try:
        content = secure_fs.secure_read_bytes(
            root,
            TARGET_MAPPING_PATH,
            reject_hardlinks=True,
            max_bytes=MAX_CANONICAL_CONTROL_BYTES,
        )
    except FileNotFoundError as error:
        raise FileNotFoundError(
            f"Target mapping not found at: {mapping_path}"
        ) from error
    return json.loads(content.decode("utf-8", errors="strict")), content


def load_target_mapping(root: Path) -> dict[str, Any]:
    """Load target-mapping.json from securely captured canonical bytes."""
    mapping, _content = _load_target_mapping_snapshot(root)
    return mapping


def capture_canonical_controls(root: Path) -> CanonicalControlSnapshot:
    """Capture controls once for parsing, selection, and target rendering."""
    target_mapping, target_mapping_content = _load_target_mapping_snapshot(root)
    return CanonicalControlSnapshot(
        target_mapping,
        target_mapping_content,
        _load_module_registry(root),
    )


def load_generation_inputs(
    root: Path,
    active_suites: Optional[Sequence[str]] = None,
    loadable_globs: Optional[Iterable[str]] = None,
) -> tuple[dict[str, Any], dict[str, list[dict[str, Any]]]]:
    """Capture and parse all canonical generation inputs without reopening them."""
    controls = capture_canonical_controls(root)
    assets = scan_canonical_assets(
        root,
        active_suites=active_suites,
        loadable_globs=loadable_globs,
        control_snapshot=controls,
    )
    return controls.target_mapping, assets


# ---------------------------------------------------------------------------
# Output manifest (for dry-run and drift detection)
# ---------------------------------------------------------------------------

def _manifest_commands(target: dict[str, Any], prompts: list[dict[str, Any]]) -> list[dict[str, str]]:
    """Build manifest entries for command files."""
    cmd_dir = target.get("outputPaths", {}).get("commands", "")
    entries: list[dict[str, str]] = []
    for prompt in prompts:
        filename = prompt["filename"].replace(".prompt.md", ".md")
        entries.append({"path": f"{cmd_dir}/{filename}", "source": prompt["relative_path"], "type": "command"})
    return entries


def _manifest_skills(target: dict[str, Any], skills: list[dict[str, Any]]) -> list[dict[str, str]]:
    """Build manifest entries for skill files."""
    skill_dir = target.get("outputPaths", {}).get("skills", "")
    entries: list[dict[str, str]] = []
    for skill in skills:
        supported = skill.get("supported_platforms")
        if supported is not None and target["id"] not in supported:
            continue
        skill_name = Path(skill["relative_path"]).parent.name
        bundle_files = skill.get("bundle_files")
        if bundle_files is None:
            entries.append({"path": f"{skill_dir}/{skill_name}/SKILL.md", "source": skill["relative_path"], "type": "skill"})
            continue
        for bundle_file in bundle_files:
            kind = "skill" if bundle_file["bundle_relative_path"] == "SKILL.md" else "skill-resource"
            entries.append({
                "path": f"{skill_dir}/{skill_name}/{bundle_file['bundle_relative_path']}",
                "source": bundle_file["relative_path"],
                "type": kind,
            })
    return entries


def _manifest_agents(target: dict[str, Any], agents: list[dict[str, Any]]) -> list[dict[str, str]]:
    """Build manifest entries for agent files, including fallback skills if configured."""
    agent_dir = target.get("outputPaths", {}).get("agents", "")
    agent_format = target.get("formats", {}).get("agentFormat", "")
    fallback_format = target.get("formats", {}).get("fallbackAgentFormat")
    fallback_dir = target.get("outputPaths", {}).get("skills", "")
    entries: list[dict[str, str]] = []
    for agent in agents:
        if "toml" in agent_format:
            filename = agent["filename"].replace(".agent.md", ".toml")
        else:
            filename = agent["filename"].replace(".agent.md", ".md")
        entries.append({"path": f"{agent_dir}/{filename}", "source": agent["relative_path"], "type": "agent"})
        if fallback_format:
            fallback_filename = agent["filename"].replace(".agent.md", ".md")
            entries.append({"path": f"{fallback_dir}/{fallback_filename}", "source": agent["relative_path"], "type": "fallback-agent"})
    return entries


def _manifest_passthrough(
    target: dict[str, Any], assets: list[dict[str, Any]], root_name: str, kind: str
) -> list[dict[str, str]]:
    """Build entries for target-local Markdown support resources."""
    destination_root = target["outputPaths"][root_name]
    return [
        {
            "path": (
                f"{destination_root}/"
                f"{asset.get('category_relative_path', asset['filename'])}"
            ),
            "source": asset["relative_path"],
            "type": kind,
        }
        for asset in assets
    ]


def build_output_manifest(
    target: dict[str, Any],
    assets: dict[str, list[dict[str, Any]]],
) -> list[dict[str, str]]:
    """Build a manifest of files that would be generated for this target.

    Returns a list of {path, source, type} dicts.
    """
    manifest: list[dict[str, str]] = []
    output_paths = target.get("outputPaths", {})
    gtp = target.get("generatedTreePath")

    projected_categories = target.get("projectedCategories")
    if gtp is None and not projected_categories:
        return manifest

    categories = set(projected_categories or (
        "commands", "skills", "agents", "instructions", "shared"
    ))
    if "commands" in categories:
        manifest.extend(_manifest_commands(target, assets["prompts"]))
        manifest.extend(_manifest_passthrough(
            target, assets["prompt_support"], "commands", "prompt-support"
        ))
    if "skills" in categories:
        manifest.extend(_manifest_skills(target, assets["skills"]))
    if "agents" in categories:
        manifest.extend(_manifest_agents(target, assets["agents"]))
    if "instructions" in categories:
        manifest.extend(_manifest_passthrough(
            target, assets["instructions"], "instructions", "instruction"
        ))
    if "shared" in categories:
        manifest.extend(_manifest_passthrough(
            target, assets["shared"], "shared", "shared"
        ))

    if not projected_categories and output_paths.get("rootAdapter"):
        manifest.append({"path": output_paths["rootAdapter"], "source": "adapter", "type": "root-adapter"})

    if not projected_categories and output_paths.get("config"):
        manifest.append({"path": output_paths["config"], "source": "target-mapping", "type": "config"})

    return manifest


# ---------------------------------------------------------------------------
# Emitter dispatch (Phase 2-4 will add platform-specific emitters)
# ---------------------------------------------------------------------------

def _format_frontmatter(
    fm: dict[str, Any],
    body: str,
    extra_fields: dict[str, Optional[str]],
) -> str:
    """Format a native file with frontmatter from canonical source.

    Args:
        fm: Canonical frontmatter dict (must contain 'description' at minimum).
        body: Full canonical file body (including original frontmatter).
        extra_fields: Platform-specific fields to inject. None values are omitted.
    Returns:
        Formatted file content with new frontmatter + stripped body.
    """
    # Descriptions are always JSON/YAML double-quoted and ASCII-escaped. This
    # prevents colon-space corruption and keeps generated frontmatter byte-safe
    # across Windows, macOS, cloud sync, and strict YAML implementations.
    desc = json.dumps(str(fm.get("description", "")), ensure_ascii=True)
    field_lines = ""
    for key, value in extra_fields.items():
        if value is not None:
            field_lines += f"{key}: {_yaml_scalar(value)}\n"
    body_text = body.split("---", 2)[-1].lstrip() if "---" in body else body
    return f"---\ndescription: {desc}\n{field_lines}---\n\n{body_text}"


def _yaml_scalar(value: Any) -> str:
    """Serialize a deterministic YAML-compatible scalar."""
    text = str(value)
    if re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._ /-]*", text) and text.casefold() not in {
        "null", "true", "false", "yes", "no", "on", "off",
    }:
        return text
    return json.dumps(text, ensure_ascii=False)


def _with_arguments_block(body: str, target_id: str) -> str:
    """Append platform-appropriate argument placeholder to a command template body."""
    if target_id == "opencode":
        heading = "OpenCode Invocation Arguments"
    else:
        heading = "Invocation Arguments"
    return (
        f"{body.rstrip()}\n\n"
        f"## {heading}\n\n"
        "User-provided slash-command arguments:\n\n"
        "```text\n"
        "$ARGUMENTS\n"
        "```\n"
    )


def _build_asset_lookup(assets: dict[str, list[dict[str, Any]]]) -> dict[str, dict[str, dict[str, Any]]]:
    """Build per-category lookup dicts keyed by relative_path for O(1) access."""
    lookups: dict[str, dict[str, dict[str, Any]]] = {}
    for category, items in assets.items():
        lookups[category] = {item["relative_path"]: item for item in items}
    return lookups


def _runtime_destination_map(
    target: dict[str, Any], assets: dict[str, list[dict[str, Any]]]
) -> dict[str, str]:
    """Classify canonical runtime files and map each exact dependency to its output."""
    paths = target["outputPaths"]
    destinations: dict[str, str] = {}
    for prompt in assets["prompts"]:
        name = prompt["filename"].replace(".prompt.md", ".md")
        destinations[prompt["relative_path"]] = f"{paths['commands']}/{name}"
    for support in assets["prompt_support"]:
        destinations[support["relative_path"]] = f"{paths['commands']}/{support['filename']}"
    for agent in assets["agents"]:
        suffix = ".toml" if "toml" in target["formats"]["agentFormat"] else ".md"
        name = agent["filename"].replace(".agent.md", suffix)
        destinations[agent["relative_path"]] = f"{paths['agents']}/{name}"
    for instruction in assets["instructions"]:
        destinations[instruction["relative_path"]] = (
            f"{paths['instructions']}/{instruction['filename']}"
        )
    for shared in assets["shared"]:
        relative = shared.get("category_relative_path", shared["filename"])
        destinations[shared["relative_path"]] = f"{paths['shared']}/{relative}"
    for skill in assets["skills"]:
        supported = skill.get("supported_platforms")
        if supported is not None and target["id"] not in supported:
            continue
        skill_name = Path(skill["relative_path"]).parent.name
        for item in skill["bundle_files"]:
            destinations[item["relative_path"]] = (
                f"{paths['skills']}/{skill_name}/{item['bundle_relative_path']}"
            )
    return destinations


def _rewrite_runtime_dependencies(
    text: str,
    target: dict[str, Any],
    assets: dict[str, list[dict[str, Any]]],
    source_identity: str,
    destinations: Optional[Mapping[str, str]] = None,
) -> str:
    """Rewrite exact canonical runtime dependencies, rejecting unsafe or missing ones."""
    if destinations is None:
        destinations = _runtime_destination_map(target, assets)

    def replace(match: re.Match[str]) -> str:
        raw = match.group(0).rstrip(".,;:")
        suffix = match.group(0)[len(raw):]
        decoded = urllib.parse.unquote(raw)
        errors = _validate_repo_relative_path(
            f"runtime dependency in {source_identity}", decoded
        )
        runtime_parts = PurePosixPath(decoded).parts[2:]
        if any(re.match(r"^[A-Za-z]:", part) for part in runtime_parts):
            errors.append(
                f"runtime dependency in {source_identity}: drive-qualified component"
            )
        if errors:
            raise PathSafetyError("unsafe runtime dependency: " + "; ".join(errors))
        destination = destinations.get(decoded)
        if destination is None:
            raise ValueError(
                f"unresolved runtime dependency in {source_identity}: {raw}"
            )
        return destination + suffix

    rewritten = CANONICAL_RUNTIME_PATH_PATTERN.sub(replace, text)
    for unresolved in CANONICAL_RUNTIME_PATH_PATTERN.finditer(rewritten):
        raw = unresolved.group(0).rstrip(".,;:")
        decoded = urllib.parse.unquote(raw)
        # Hybrid Copilot projection deliberately keeps non-skill topology at
        # canonical .github paths. An exact identity destination is resolved,
        # even though its rendered text still contains the canonical path.
        if destinations.get(decoded) == decoded:
            continue
        raise ValueError(
            f"unresolved canonical runtime dependency in {source_identity}: "
            f"{unresolved.group(0)}"
        )
    return rewritten


def _render_output_entry(
    target: dict[str, Any],
    manifest_entry: dict[str, str],
    assets: dict[str, list[dict[str, Any]]],
    render_context: Optional[
        Tuple[dict[str, dict[str, dict[str, Any]]], Mapping[str, str]]
    ] = None,
) -> OutputEntry:
    """Render one manifest entry into final bytes without filesystem writes."""
    if render_context is None:
        lookups = _build_asset_lookup(assets)
        destinations = _runtime_destination_map(target, assets)
    else:
        lookups, destinations = render_context
    kind = manifest_entry["type"]
    source_identity = manifest_entry["source"]
    source = None
    category = {
        "command": "prompts", "skill": "skills", "agent": "agents",
        "fallback-agent": "agents",
        "prompt-support": "prompt_support", "instruction": "instructions",
        "shared": "shared",
    }.get(kind)
    if kind == "skill-resource":
        for skill in assets["skills"]:
            source = next(
                (item for item in skill.get("bundle_files", [])
                 if item["relative_path"] == source_identity),
                None,
            )
            if source is not None:
                break
        if source is None:
            raise ValueError(f"Manifest references unknown skill resource: {source_identity}")
    elif category is not None:
        source = lookups[category].get(source_identity)
        if source is None:
            raise ValueError(f"Manifest references unknown {category[:-1]}: {source_identity}")

    if kind == "command":
        text = _emit_command(source, target)
    elif kind == "skill":
        text = source["body"]
    elif kind == "skill-resource":
        content = source["content"]
    elif kind == "agent":
        text = _emit_agent(source, target)
    elif kind == "fallback-agent":
        text = _emit_fallback_agent(source, target)
    elif kind in ("prompt-support", "instruction"):
        text = source["body"]
    elif kind == "shared":
        content = source.get("content", source["body"].encode("utf-8"))
    elif kind == "root-adapter":
        text = _emit_root_adapter(target)
    elif kind == "config":
        text = _emit_config(target)
    else:
        raise ValueError(f"Unsupported output type: {kind}")

    if kind not in ("skill-resource", "shared"):
        if kind in ("command", "skill", "agent", "fallback-agent",
                    "prompt-support", "instruction"):
            text = _rewrite_runtime_dependencies(
                text, target, assets, source_identity, destinations
            )
        content = text.encode("utf-8")
    elif source_identity.casefold().endswith((".md", ".markdown")) or (
        kind == "shared"
        and source_identity.startswith(".github/shared/skill-management/operations/")
        and source_identity.casefold().endswith(".json")
    ):
        text = content.decode("utf-8")
        text = _rewrite_runtime_dependencies(
            text, target, assets, source_identity, destinations
        )
        content = text.encode("utf-8")
    executable = bool(source.get("executable", False)) if source is not None else False
    origin = str(source.get("origin", "plugin-canonical")) if source is not None else "plugin-canonical"
    provenance_identity = (
        str(source.get("provenance_identity", "canonical/.github"))
        if source is not None
        else "canonical/.github"
    )
    return OutputEntry(
        target["id"], str(PurePosixPath(manifest_entry["path"])),
        str(PurePosixPath(source_identity)), kind, content,
        hashlib.sha256(content).hexdigest(), executable, origin,
        provenance_identity,
    )


def _write_atomic_bytes(path: Path, content: bytes) -> None:
    """Atomically replace path with exact bytes from a generation plan."""
    secure_fs.secure_write_bytes(path.parent, Path(path.name), content)


def _ownership_manifest_bytes(result: TargetResult) -> bytes:
    """Serialize deterministic ownership metadata for one target."""
    data = {
        "schemaVersion": 1,
        "target": result.target_id,
        "policyVersion": OWNERSHIP_POLICY_VERSION,
        "files": [
            {
                "path": entry.destination,
                "source": entry.source,
                "kind": entry.kind,
                "sha256": entry.sha256,
                "executable": entry.executable,
            }
            for entry in result.entries
        ],
    }
    return (json.dumps(data, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def _read_prior_ownership_manifest(
    root: Path,
    result: TargetResult,
) -> Dict[str, OwnedFile]:
    """Read and strictly validate a target's prior ownership manifest."""
    owned, _expected_state = _read_prior_ownership_manifest_snapshot(root, result)
    return owned


def _read_prior_ownership_manifest_snapshot(
    root: Path,
    result: TargetResult,
) -> tuple[Dict[str, OwnedFile], secure_fs.ExpectedFileState]:
    """Parse ownership and preserve the exact pinned manifest state."""
    relative_path = PurePosixPath(
        result.target_root,
        OWNERSHIP_MANIFEST_NAME,
    )
    manifest_path = root / relative_path
    if not root.exists():
        return {}, secure_fs.ExpectedFileState.absent()
    try:
        content = secure_fs.secure_read_bytes(
            root,
            relative_path,
            reject_hardlinks=True,
            max_bytes=MAX_OWNERSHIP_MANIFEST_BYTES,
        )
    except FileNotFoundError:
        return {}, secure_fs.ExpectedFileState.absent()
    except OSError as exc:
        raise ValueError(f"Ownership manifest is unsafe: {manifest_path}") from exc
    try:
        data = json.loads(content.decode("utf-8", errors="strict"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"Ownership manifest is malformed: {manifest_path}") from exc
    if not isinstance(data, dict) or set(data) != {
        "schemaVersion", "target", "policyVersion", "files"
    }:
        raise ValueError(f"Ownership manifest has an invalid schema: {manifest_path}")
    if type(data["schemaVersion"]) is not int or data["schemaVersion"] != 1:
        raise ValueError(f"Ownership manifest has an unsupported schemaVersion: {manifest_path}")
    if data["target"] != result.target_id:
        raise ValueError(f"Ownership manifest target does not match {result.target_id}")
    if type(data["policyVersion"]) is not int or data["policyVersion"] != OWNERSHIP_POLICY_VERSION:
        raise ValueError(f"Ownership manifest has an unsupported policyVersion: {manifest_path}")
    if not isinstance(data["files"], list):
        raise ValueError(f"Ownership manifest files must be an array: {manifest_path}")

    owned: Dict[str, OwnedFile] = {}
    manifest_destination = f"{result.target_root}/{OWNERSHIP_MANIFEST_NAME}"
    for index, item in enumerate(data["files"]):
        label = f"ownership manifest files[{index}]"
        if not isinstance(item, dict) or set(item) != {
            "path", "source", "kind", "sha256", "executable"
        }:
            raise ValueError(f"{label} has an invalid schema")
        path = item["path"]
        path_errors = _validate_repo_relative_path(f"{label}.path", path)
        if path_errors:
            raise ValueError("; ".join(path_errors))
        if _is_python_cache_path(path):
            raise ValueError(f"{label}.path references Python cache artifact: {path}")
        if not _is_within(path, result.target_root) or path == result.target_root:
            raise ValueError(f"{label}.path is outside target root '{result.target_root}'")
        if path == manifest_destination:
            raise ValueError(f"{label}.path must not own the manifest itself")
        if path in owned:
            raise ValueError(f"Ownership manifest has duplicate destination: {path}")
        if not isinstance(item["source"], str) or not item["source"]:
            raise ValueError(f"{label}.source must be a non-empty string")
        if _is_python_cache_path(item["source"]):
            raise ValueError(
                f"{label}.source references Python cache artifact: {item['source']}"
            )
        if not isinstance(item["kind"], str) or not item["kind"]:
            raise ValueError(f"{label}.kind must be a non-empty string")
        if not isinstance(item["sha256"], str) or not SHA256_PATTERN.fullmatch(item["sha256"]):
            raise ValueError(f"{label}.sha256 is not a lowercase SHA-256 digest")
        if type(item["executable"]) is not bool:
            raise ValueError(f"{label}.executable must be a boolean")
        owned[path] = OwnedFile(path, item["sha256"])
    return owned, secure_fs.ExpectedFileState.from_bytes(content)


def _regular_file_hash(path: Path, label: str) -> str:
    """Hash a regular non-symlink file, rejecting replacement types."""
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"{label} is not a regular file: {path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _matches_expected_content(current: bytes, expected: bytes) -> bool:
    """Return whether text checkout EOLs normalize to exact planned bytes."""
    if current == expected:
        return True
    if b"\r\n" not in current:
        return False
    return current.replace(b"\r\n", b"\n") == expected


def _revalidate_destination_ancestors(root: Path, destination: Path) -> None:
    """Reject a destination whose existing ancestor changed into a link or non-directory."""
    try:
        secure_fs.revalidate_destination_ancestors(root, destination)
    except secure_fs.SecureMutationError as exc:
        raise PathSafetyError(str(exc)) from exc


def _supports_secure_dir_fd() -> bool:
    """Return whether this host supports no-follow handle-relative mutation."""
    return secure_fs.supports_secure_dir_fd()


def _open_relative_parent(root: Path, relative_path: str, *, create: bool) -> tuple[int, str]:
    """Open a repository-relative parent without following symlink components."""
    return secure_fs.open_relative_parent(root, relative_path, create=create)


def _secure_write_entry(
    root: Path,
    entry: OutputEntry,
    expected_state: secure_fs.ExpectedFileState,
) -> None:
    """Atomically write an output through a root-anchored no-follow parent handle."""
    try:
        secure_fs.secure_write_bytes(
            root,
            Path(entry.destination),
            entry.content,
            executable=entry.executable,
            before_replace=_before_secure_replace,
            expected_state=expected_state,
        )
    except secure_fs.SecureMutationError as exc:
        if "quarantine preserved" in str(exc):
            raise ValueError(str(exc)) from exc
        raise


def _secure_delete_stale(root: Path, stale: OwnedFile) -> None:
    """Quarantine, verify, and delete a stale file through one pinned parent handle."""
    try:
        secure_fs.secure_delete_verified(
            root,
            PurePosixPath(stale.path),
            stale.sha256,
            before_unlink=_before_secure_unlink,
        )
    except secure_fs.SecureMutationError as exc:
        raise ValueError(str(exc)) from exc


def _before_secure_replace(_path: Path) -> None:
    """Test hook immediately before handle-relative replacement."""


def _before_secure_unlink(_path: Path) -> None:
    """Test hook immediately before handle-relative stale quarantine."""


def _preflight_target_commit(root: Path, result: TargetResult) -> TargetCommitPlan:
    """Validate ownership, conflicts, and stale files before mutation."""
    owned, manifest_expected_state = _read_prior_ownership_manifest_snapshot(
        root,
        result,
    )
    expected = {entry.destination: entry for entry in result.entries}
    target_root = root / result.target_root
    manifest_path = target_root / OWNERSHIP_MANIFEST_NAME
    expected_states: Dict[str, secure_fs.ExpectedFileState] = {}

    for entry in result.entries:
        destination = root / entry.destination
        ancestor = destination.parent
        while ancestor != root and ancestor != target_root.parent:
            if ancestor.exists() and (ancestor.is_symlink() or not ancestor.is_dir()):
                raise ValueError(f"Expected destination has a non-directory ancestor: {entry.destination}")
            if ancestor == target_root:
                break
            ancestor = ancestor.parent
        if not destination.exists() and not destination.is_symlink():
            expected_states[entry.destination] = secure_fs.ExpectedFileState.absent()
            continue
        if destination.is_symlink() or not destination.is_file():
            raise ValueError(
                f"Expected destination is not a regular file: {destination}"
            )
        current_bytes = destination.read_bytes()
        current_hash = hashlib.sha256(current_bytes).hexdigest()
        prior = owned.get(entry.destination)
        allowed_hashes = {entry.sha256}
        if prior is not None:
            allowed_hashes.add(prior.sha256)
        is_owned = current_hash in allowed_hashes
        if not is_owned and b"\r\n" in current_bytes:
            normalized_hash = hashlib.sha256(
                current_bytes.replace(b"\r\n", b"\n")
            ).hexdigest()
            is_owned = normalized_hash in allowed_hashes
        if not is_owned:
            is_owned = _matches_expected_content(current_bytes, entry.content)
        if not is_owned:
            ownership = "owned" if prior is not None else "unowned"
            raise ValueError(f"Conflicting {ownership} expected destination: {entry.destination}")
        expected_states[entry.destination] = secure_fs.ExpectedFileState(
            True,
            current_hash,
        )

    stale_files = tuple(owned[path] for path in sorted(set(owned) - set(expected)))
    for stale in stale_files:
        path = root / stale.path
        if not path.exists() and not path.is_symlink():
            continue
        current_hash = _regular_file_hash(path, "Stale owned path")
        if current_hash != stale.sha256:
            raise ValueError(f"Modified stale owned file will not be deleted: {stale.path}")

    return TargetCommitPlan(
        result,
        stale_files,
        manifest_path,
        _ownership_manifest_bytes(result),
        expected_states,
        manifest_expected_state,
    )


def commit_generation_plan(
    root: Path,
    plan: GenerationPlan,
    selected_target_ids: Sequence[str],
) -> CommitResult:
    """Atomically write exact planned bytes for selected targets."""
    target_ids = tuple(sorted(set(selected_target_ids)))
    unknown = [target_id for target_id in target_ids if target_id not in plan.by_target]
    if unknown:
        raise ValueError(f"Targets are not present in generation plan: {', '.join(unknown)}")
    commit_plans = tuple(
        _preflight_target_commit(root, plan.by_target[target_id])
        for target_id in target_ids
    )
    entries = tuple(entry for commit_plan in commit_plans
                    for entry in commit_plan.result.entries)
    for commit_plan in commit_plans:
        for entry in commit_plan.result.entries:
            _secure_write_entry(
                root,
                entry,
                commit_plan.expected_states[entry.destination],
            )
    for commit_plan in commit_plans:
        for stale in commit_plan.stale_files:
            stale_path = root / stale.path
            # Match the preflight tolerance for stale entries that no longer
            # exist on disk (e.g. bytecode caches removed after a prior
            # manifest was committed): the Windows secure-delete path pins
            # every parent directory and would fail on a missing ancestor.
            if not stale_path.exists() and not stale_path.is_symlink():
                continue
            _secure_delete_stale(root, stale)
        commit_plan.manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_entry = OutputEntry(
            commit_plan.result.target_id,
            commit_plan.manifest_path.relative_to(root).as_posix(),
            "generated ownership manifest",
            "manifest",
            commit_plan.manifest_content,
            hashlib.sha256(commit_plan.manifest_content).hexdigest(),
            False,
        )
        _secure_write_entry(
            root,
            manifest_entry,
            commit_plan.manifest_expected_state,
        )
    return CommitResult(target_ids, entries)


def emit_for_target(
    root: Path,
    target: dict[str, Any],
    assets: dict[str, list[dict[str, Any]]],
    dry_run: bool = False,
) -> list[str]:
    """Emit native files for a single target. Returns list of written paths.

    Phase 1: emits passthrough copies with frontmatter adaptation.
    Phase 2-4: platform-specific emitters will override this.
    """
    if target.get("generatedTreePath") is None:
        return []
    mapping = {"schemaVersion": 1, "description": "single target", "targets": [target]}
    plan = build_generation_plan(root, mapping, assets)
    result = plan.by_target[target["id"]]
    if not dry_run:
        commit_generation_plan(root, plan, (target["id"],))
    return [entry.destination for entry in result.entries]


def _emit_command(
    source: dict[str, Any],
    target: dict[str, Any],
) -> str:
    """Emit a platform-native command file from a canonical prompt."""
    fm = source["frontmatter"]
    body = source["body"]
    if target["id"] in ("claude-code", "codex"):
        return _format_frontmatter(fm, body, {})
    elif target["id"] in ("opencode", "kilo"):
        return _format_frontmatter(fm, _with_arguments_block(body, target["id"]), {})
    else:
        return body


def _emit_agent(
    source: dict[str, Any],
    target: dict[str, Any],
) -> str:
    """Emit a platform-native agent/subagent file from a canonical agent."""
    fm = source["frontmatter"]
    body = source["body"]
    agent_format = target.get("formats", {}).get("agentFormat", "")

    if "toml" in agent_format:
        desc = json.dumps(str(fm.get("description", "")), ensure_ascii=False)
        tools = fm.get("tools", [])
        if isinstance(tools, list):
            tools_str = ", ".join(json.dumps(str(tool), ensure_ascii=False) for tool in tools)
        else:
            tools_str = ""
        body_text = body.split("---", 2)[-1].strip() if "---" in body else body
        name = json.dumps(source["filename"].replace(".agent.md", ""), ensure_ascii=False)
        instructions = json.dumps(body_text, ensure_ascii=False)
        return f'[[subagent]]\nname = {name}\ndescription = {desc}\ntools = [{tools_str}]\ninstructions = {instructions}\n'
    elif target["id"] in ("claude-code",):
        return _format_frontmatter(fm, body, {})
    elif target["id"] in ("opencode", "kilo"):
        return _format_frontmatter(fm, body, {"mode": "subagent"})
    else:
        return body


def _emit_fallback_agent(
    source: dict[str, Any],
    _target: dict[str, Any],
) -> str:
    """Emit a fallback skill/instruction file for an agent (Codex without native subagent support)."""
    fm = source["frontmatter"]
    body = source["body"]
    desc = fm.get("description", "")
    body_text = body.split("---", 2)[-1].strip() if "---" in body else body
    return f"# Agent: {source['filename'].replace('.agent.md', '')}\n\n> {desc}\n\n{body_text}\n"


def _emit_root_adapter(target: dict[str, Any]) -> str:
    """Emit a minimal root adapter file for the platform."""
    name = target["name"]
    paths = target["outputPaths"]
    adapter = f"# Compound GPID — {name} Adapter\n\nThis file is generated from the target mapping.\nIt maps Compound GPID `/cg-*` commands to native {name} paths.\n\n## Command Dispatch\n\n`/cg-<name> [args...]` -> `{paths['commands']}/cg-<name>.md`\n\n## Skills\n\nLoad skill files from `{paths['skills']}/*-skill-*/SKILL.md`.\n\n## Agents\n\nAgent specs are under `{paths['agents']}/`.\n\n## Instructions And Contracts\n\nLanguage instructions are under `{paths['instructions']}/`; shared contracts are under `{paths['shared']}/`.\n"
    if target["id"] == "kilo":
        adapter += (
            "\n## Cross-Adapter Skill Discovery\n\n"
            "Kilo auto-discovers `.agents/skills` and `.claude/skills` in addition to "
            "`skills.paths`. As of the 2026-08-20 Kilo schema, project config has no "
            "supported `only`, `exclude`, or auto-discovery switch; the process-level "
            "`KILO_DISABLE_EXTERNAL_SKILLS` flag is not portable to VS Code/Positron "
            "project installs. When Kilo and another adapter are linked together, "
            "`cg-link` therefore keeps the adapter path as a junction/symlink but "
            "points it at an adapter-specific managed mirror under "
            "`.compound-gpid/kilo-compat-skills/`. This keeps every Kilo-reachable "
            "`SKILL.md` inside the project trust boundary while preserving each "
            "adapter's generated content. This workaround complements upstream Kilo "
            "#12391/PR #12846 and remains necessary for Kilo versions that reject "
            "auto-discovered compatibility skills resolving outside the project.\n"
        )
    return adapter


def _emit_config(target: dict[str, Any]) -> str:
    """Emit a platform config file (e.g. opencode.json, kilo.json)."""
    tid = target["id"]
    output_paths = target.get("outputPaths", {})
    if tid == "opencode":
        config = {
            "$schema": "https://opencode.ai/config.json",
            "instructions": [output_paths.get("rootAdapter", ".opencode/AGENTS.md")],
            "skills": {
                "paths": [output_paths.get("skills", ".opencode/skills")],
            },
        }
        return json.dumps(config, indent=2, ensure_ascii=False) + "\n"

    if tid == "kilo":
        config = {
            "$schema": "https://app.kilo.ai/config.json",
            "instructions": [output_paths.get("rootAdapter", ".kilo/AGENTS.md")],
            "skills": {
                "paths": [output_paths.get("skills", ".kilo/skills")],
            },
            # Mirrors are scanned through their adapter links. Ignore direct
            # watcher churn under the backing directory; this is not the trust
            # boundary fix and does not disable compatibility auto-discovery.
            "watcher": {
                "ignore": [".compound-gpid/kilo-compat-skills/**"],
            },
        }
        return json.dumps(config, indent=2, ensure_ascii=False) + "\n"

    config = {
        "platform": tid,
        "commands": output_paths.get("commands", ""),
        "skills": output_paths.get("skills", ""),
        "agents": output_paths.get("agents", ""),
    }
    return json.dumps(config, indent=2, ensure_ascii=False) + "\n"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate native platform trees from canonical .github/ source."
    )
    parser.add_argument("--root", default=".", help="Project root directory (default: current directory)")
    parser.add_argument("--target", default=None, help="Target platform ID to generate (e.g. claude-code, codex, opencode, kilo)")
    parser.add_argument("--all", action="store_true", help="Generate all non-copilot targets")
    parser.add_argument("--dry-run", action="store_true", help="Report what would be written without writing")
    parser.add_argument("--active-suites", default=None, metavar="SUITES",
                        help="Comma-separated active suite names (e.g. 'cg' or 'cg,cr') to enforce the context budget; "
                             "omitted means no context-budget filtering")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    if not root.is_dir():
        print(f"Error: project root does not exist or is not a directory: {root}", file=sys.stderr)
        return 2

    try:
        controls = capture_canonical_controls(root)
        target_mapping = controls.target_mapping
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as e:
        print(f"Error: target-mapping.json is malformed: {e}", file=sys.stderr)
        return 1
    except (OSError, UnicodeDecodeError) as e:
        print(f"Error: target-mapping.json is unsafe or unreadable: {e}", file=sys.stderr)
        return 1

    errors = validate_target_mapping(target_mapping)
    if errors:
        print("Error: target-mapping.json validation failed:", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return 1

    if not args.target and not args.all:
        print("Error: must specify --target <platform> or --all", file=sys.stderr)
        return 1

    active_suites: Optional[list[str]] = None
    if args.active_suites:
        active_suites = [item.strip() for item in args.active_suites.split(",") if item.strip()]

    try:
        assets = scan_canonical_assets(
            root,
            active_suites=active_suites,
            control_snapshot=controls,
        )
        generation_plan = build_generation_plan(root, target_mapping, assets)
    except (ValueError, OSError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    targets_to_run: list[dict[str, Any]] = []
    for target in target_mapping["targets"]:
        tid = target.get("id", "")
        gtp = target.get("generatedTreePath")
        if gtp is None:
            if tid == args.target:
                print(f"[skip] {tid}: generatedTreePath is null — no files to generate")
            continue
        if args.all or tid == args.target:
            targets_to_run.append(target)

    if not targets_to_run:
        if args.target:
            requested_target = next((t for t in target_mapping["targets"] if t.get("id") == args.target), None)
            if requested_target and requested_target.get("generatedTreePath") is None:
                print(f"[skip] {args.target}: generatedTreePath is null — no files to generate")
                return 0
        requested = args.target or "all"
        available = [t["id"] for t in target_mapping["targets"] if t.get("generatedTreePath")]
        print(f"Error: no matching target for '{requested}'. Available: {', '.join(available)}", file=sys.stderr)
        return 1

    all_written: list[str] = []
    committed_by_target: dict[str, tuple[OutputEntry, ...]] = {}
    if not args.dry_run:
        try:
            committed = commit_generation_plan(
                root,
                generation_plan,
                tuple(target["id"] for target in targets_to_run),
            )
        except (ValueError, OSError) as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1
        committed_by_target = {
            target_id: tuple(
                entry for entry in committed.entries if entry.target_id == target_id
            )
            for target_id in committed.target_ids
        }

    for target in targets_to_run:
        tid = target["id"]
        if args.dry_run:
            result = generation_plan.by_target[tid]
            print(f"[dry-run] {tid}: {len(result.entries)} files would be written")
            for entry in result.entries:
                print(f"  {entry.destination} ({entry.kind})")
            all_written.extend(entry.destination for entry in result.entries)
        else:
            entries = committed_by_target[tid]
            print(f"[generated] {tid}: {len(entries)} files written")
            all_written.extend(entry.destination for entry in entries)

    print(f"\nTotal: {len(all_written)} files {'would be written' if args.dry_run else 'written'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
