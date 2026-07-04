#!/usr/bin/env python3
"""cg-generate-targets — Generate native platform trees from canonical .github/ source.

Reads .github/ canonical assets (prompts, agents, skills, instructions, shared
contracts) and .github/shared/target-mapping.json, then emits platform-specific
native trees for Claude Code, Codex, and OpenCode.

Usage:
    python3 scripts/cg_generate_targets.py [--root <path>] [--target <platform>] [--all] [--dry-run]

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
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

_scripts_dir = str(Path(__file__).parent)
if _scripts_dir not in sys.path:
    sys.path.insert(0, _scripts_dir)

from brain.utils import parse_frontmatter, write_atomic  # noqa: E402

TARGET_MAPPING_PATH = ".github/shared/target-mapping.json"
MODEL_CATALOG_PATH = ".github/shared/model-catalog.json"

CANONICAL_PROMPTS_GLOB = ".github/prompts/*.prompt.md"
CANONICAL_AGENTS_GLOB = ".github/agents/*.agent.md"
CANONICAL_SKILLS_GLOB = ".github/skills/cg-skill-*/SKILL.md"
CANONICAL_INSTRUCTIONS_GLOB = ".github/instructions/*.instructions.md"


# ---------------------------------------------------------------------------
# Schema validation (stdlib-only — no jsonschema dependency)
# ---------------------------------------------------------------------------

REQUIRED_TARGET_FIELDS = {"id", "name", "generatedTreePath", "modelMappingMode", "capabilities", "formats", "outputPaths"}
REQUIRED_CAPABILITY_FIELDS = {"supportsNativeCommands", "supportsNativeSkills", "supportsNativeSubagents", "supportsMultiVendorModels", "requiresRootAdapter"}
REQUIRED_FORMAT_FIELDS = {"commandFormat", "skillFormat", "agentFormat"}
REQUIRED_OUTPUT_PATH_FIELDS = {"commands", "skills", "agents"}
VALID_MODEL_MAPPING_MODES = {"role-only", "tier", "exact"}
VALID_ROLES = {"coding", "review", "reasoning", "mechanical", "inherited", "fallback", "cross-vendor-review"}


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


def validate_target_mapping(data: dict[str, Any]) -> list[str]:
    """Validate target-mapping.json structure. Returns list of error messages (empty = valid)."""
    errors: list[str] = []
    if "schemaVersion" not in data:
        errors.append("Missing required field: schemaVersion")
    elif not isinstance(data["schemaVersion"], int):
        errors.append("schemaVersion must be an integer")
    if "targets" not in data:
        errors.append("Missing required field: targets")
        return errors
    if not isinstance(data["targets"], list) or len(data["targets"]) == 0:
        errors.append("targets must be a non-empty array")
        return errors

    seen_ids: set[str] = set()
    for i, target in enumerate(data["targets"]):
        prefix = f"targets[{i}]"
        if not isinstance(target, dict):
            errors.append(f"{prefix}: must be an object")
            continue

        for field in REQUIRED_TARGET_FIELDS:
            if field not in target:
                errors.append(f"{prefix}: missing required field '{field}'")

        tid = target.get("id", "")
        if not isinstance(tid, str) or not tid:
            errors.append(f"{prefix}: id must be a non-empty string")
        elif tid in seen_ids:
            errors.append(f"{prefix}: duplicate target id '{tid}'")
        else:
            seen_ids.add(tid)

        mode = target.get("modelMappingMode")
        if mode not in VALID_MODEL_MAPPING_MODES:
            errors.append(f"{prefix}: modelMappingMode must be one of {VALID_MODEL_MAPPING_MODES}, got '{mode}'")

        errors.extend(_validate_capabilities(prefix, target.get("capabilities", {})))
        errors.extend(_validate_formats(prefix, target.get("formats", {})))
        errors.extend(_validate_output_paths(prefix, target.get("outputPaths", {})))

        gtp = target.get("generatedTreePath")
        if gtp is not None and not isinstance(gtp, str):
            errors.append(f"{prefix}: generatedTreePath must be a string or null")

    return errors


# ---------------------------------------------------------------------------
# Canonical asset scanning
# ---------------------------------------------------------------------------

def scan_canonical_assets(root: Path) -> dict[str, list[dict[str, Any]]]:
    """Scan .github/ canonical assets and return structured metadata.

    Returns dict with keys: prompts, agents, skills, instructions.
    Each value is a list of dicts with: path, relative_path, frontmatter, body.
    """
    assets: dict[str, list[dict[str, Any]]] = {
        "prompts": [],
        "agents": [],
        "skills": [],
        "instructions": [],
    }

    for pattern, category in [
        (CANONICAL_PROMPTS_GLOB, "prompts"),
        (CANONICAL_AGENTS_GLOB, "agents"),
        (CANONICAL_SKILLS_GLOB, "skills"),
        (CANONICAL_INSTRUCTIONS_GLOB, "instructions"),
    ]:
        for path in sorted(root.glob(pattern)):
            if not path.is_file():
                continue
            content = path.read_text(encoding="utf-8")
            fm = parse_frontmatter(content)
            rel = str(path.relative_to(root)).replace("\\", "/")
            assets[category].append({
                "path": str(path),
                "relative_path": rel,
                "frontmatter": fm,
                "body": content,
                "filename": path.name,
            })

    return assets


def load_target_mapping(root: Path) -> dict[str, Any]:
    """Load target-mapping.json from .github/shared/."""
    mapping_path = root / TARGET_MAPPING_PATH
    if not mapping_path.exists():
        raise FileNotFoundError(f"Target mapping not found at: {mapping_path}")
    return json.loads(mapping_path.read_text(encoding="utf-8"))


def load_model_catalog(root: Path) -> dict[str, Any]:
    """Load model-catalog.json from .github/shared/."""
    catalog_path = root / MODEL_CATALOG_PATH
    if not catalog_path.exists():
        return {"models": [], "assignments": [], "frontmatterSupport": []}
    return json.loads(catalog_path.read_text(encoding="utf-8"))


def get_role_for_asset(rel_path: str, catalog: dict[str, Any]) -> Optional[str]:
    """Look up the canonical role for an asset from the model catalog assignments."""
    for assignment in catalog.get("assignments", []):
        if assignment.get("path") == rel_path:
            return assignment.get("role")
    return None


# ---------------------------------------------------------------------------
# Model mapping resolution
# ---------------------------------------------------------------------------

def resolve_model(target: dict[str, Any], role: Optional[str]) -> Optional[str]:
    """Resolve a canonical role to a platform-specific model value.

    Returns None for inherited/unmapped roles.
    """
    if role is None:
        return None
    mode = target.get("modelMappingMode", "role-only")
    mapping = target.get("modelMapping", {})

    if mode == "role-only":
        return None
    if role in mapping:
        mapped = mapping[role]
        return mapped if isinstance(mapped, str) else None
    if role == "inherited":
        return None
    return mapping.get("fallback")


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
        skill_name = Path(skill["relative_path"]).parent.name
        entries.append({"path": f"{skill_dir}/{skill_name}/SKILL.md", "source": skill["relative_path"], "type": "skill"})
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

    if gtp is None:
        return manifest

    manifest.extend(_manifest_commands(target, assets["prompts"]))
    manifest.extend(_manifest_skills(target, assets["skills"]))
    manifest.extend(_manifest_agents(target, assets["agents"]))

    if output_paths.get("rootAdapter"):
        manifest.append({"path": output_paths["rootAdapter"], "source": "adapter", "type": "root-adapter"})

    if output_paths.get("modelMapping"):
        manifest.append({"path": output_paths["modelMapping"], "source": "model-catalog", "type": "model-mapping"})

    if output_paths.get("config"):
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
        extra_fields: Platform-specific fields to inject (e.g. {'model': 'sonnet'}).
            None values are omitted.
    Returns:
        Formatted file content with new frontmatter + stripped body.
    """
    desc = fm.get("description", "")
    field_lines = ""
    for key, value in extra_fields.items():
        if value is not None:
            field_lines += f"{key}: {value}\n"
    body_text = body.split("---", 2)[-1].lstrip() if "---" in body else body
    return f"---\ndescription: {desc}\n{field_lines}---\n\n{body_text}"


def _with_opencode_arguments(body: str) -> str:
    """Append OpenCode slash-command arguments to a command template body."""
    return (
        f"{body.rstrip()}\n\n"
        "## OpenCode Invocation Arguments\n\n"
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


def emit_for_target(
    root: Path,
    target: dict[str, Any],
    assets: dict[str, list[dict[str, Any]]],
    catalog: dict[str, Any],
    dry_run: bool = False,
) -> list[str]:
    """Emit native files for a single target. Returns list of written paths.

    Phase 1: emits passthrough copies with frontmatter adaptation.
    Phase 2-4: platform-specific emitters will override this.
    """
    written: list[str] = []
    output_paths = target.get("outputPaths", {})
    gtp = target.get("generatedTreePath")

    if gtp is None:
        return written

    manifest = build_output_manifest(target, assets)

    if dry_run:
        for entry in manifest:
            written.append(entry["path"])
        return written

    lookups = _build_asset_lookup(assets)

    for entry in manifest:
        out_path = root / entry["path"]
        out_path.parent.mkdir(parents=True, exist_ok=True)

        if entry["type"] == "command":
            source = lookups["prompts"].get(entry["source"])
            if source is None:
                raise ValueError(f"Manifest references unknown prompt: {entry['source']}")
            content = _emit_command(source, target, catalog)
            write_atomic(out_path, content)
        elif entry["type"] == "skill":
            source = lookups["skills"].get(entry["source"])
            if source is None:
                raise ValueError(f"Manifest references unknown skill: {entry['source']}")
            write_atomic(out_path, source["body"])
        elif entry["type"] == "agent":
            source = lookups["agents"].get(entry["source"])
            if source is None:
                raise ValueError(f"Manifest references unknown agent: {entry['source']}")
            content = _emit_agent(source, target, catalog)
            write_atomic(out_path, content)
        elif entry["type"] == "fallback-agent":
            source = lookups["agents"].get(entry["source"])
            if source is None:
                raise ValueError(f"Manifest references unknown agent: {entry['source']}")
            content = _emit_fallback_agent(source, target, catalog)
            write_atomic(out_path, content)
        elif entry["type"] == "root-adapter":
            content = _emit_root_adapter(target)
            write_atomic(out_path, content)
        elif entry["type"] == "model-mapping":
            content = _emit_model_mapping(target, catalog)
            write_atomic(out_path, content)
        elif entry["type"] == "config":
            content = _emit_config(target)
            write_atomic(out_path, content)

        written.append(entry["path"])

    return written


def _emit_command(
    source: dict[str, Any],
    target: dict[str, Any],
    catalog: dict[str, Any],
) -> str:
    """Emit a platform-native command file from a canonical prompt."""
    fm = source["frontmatter"]
    body = source["body"]
    role = get_role_for_asset(source["relative_path"], catalog)
    model = resolve_model(target, role)

    if target["id"] in ("claude-code", "codex"):
        return _format_frontmatter(fm, body, {"model": model})
    elif target["id"] == "opencode":
        return _format_frontmatter(fm, _with_opencode_arguments(body), {})
    else:
        return body


def _emit_agent(
    source: dict[str, Any],
    target: dict[str, Any],
    catalog: dict[str, Any],
) -> str:
    """Emit a platform-native agent/subagent file from a canonical agent."""
    fm = source["frontmatter"]
    body = source["body"]
    role = get_role_for_asset(source["relative_path"], catalog)
    model = resolve_model(target, role)
    agent_format = target.get("formats", {}).get("agentFormat", "")

    if "toml" in agent_format:
        desc = fm.get("description", "")
        model_line = f'model = "{model}"' if model else '# model = "inherited"'
        tools = fm.get("tools", [])
        if isinstance(tools, list):
            tools_str = ", ".join(f'"{t}"' for t in tools)
        else:
            tools_str = ""
        body_text = body.split("---", 2)[-1].strip() if "---" in body else body
        return f'[[subagent]]\nname = "{source["filename"].replace(".agent.md", "")}"\ndescription = "{desc}"\n{model_line}\ntools = [{tools_str}]\n\n# Instructions\n\n{body_text}\n'
    elif target["id"] in ("claude-code",):
        return _format_frontmatter(fm, body, {"model": model})
    elif target["id"] == "opencode":
        return _format_frontmatter(fm, body, {"mode": "subagent"})
    else:
        return body


def _emit_fallback_agent(
    source: dict[str, Any],
    target: dict[str, Any],
    catalog: dict[str, Any],
) -> str:
    """Emit a fallback skill/instruction file for an agent (Codex without native subagent support)."""
    fm = source["frontmatter"]
    body = source["body"]
    desc = fm.get("description", "")
    body_text = body.split("---", 2)[-1].strip() if "---" in body else body
    return f"# Agent: {source['filename'].replace('.agent.md', '')}\n\n> {desc}\n\n{body_text}\n"


def _emit_root_adapter(target: dict[str, Any]) -> str:
    """Emit a minimal root adapter file for the platform."""
    tid = target["id"]
    name = target["name"]
    gtp = target.get("generatedTreePath", "")
    return f"# Compound GPID — {name} Adapter\n\nThis file is generated from `.github/shared/target-mapping.json`.\nIt maps Compound GPID `/cg-*` commands to native {name} paths under `{gtp}/`.\n\n## Command Dispatch\n\n`/cg-<name> [args...]` → `{gtp}/commands/cg-<name>.md`\n\n## Skills\n\nLoad skill files from `{gtp}/skills/cg-skill-*/SKILL.md`.\n\n## Agents\n\nAgent specs are under `{gtp}/agents/`.\n"


def _emit_model_mapping(target: dict[str, Any], catalog: dict[str, Any]) -> str:
    """Emit a platform-specific model mapping artifact."""
    tid = target["id"]
    mode = target.get("modelMappingMode", "role-only")
    mapping = target.get("modelMapping", {})

    artifact = {
        "platform": tid,
        "modelMappingMode": mode,
        "mapping": mapping,
        "source": ".github/shared/model-catalog.json",
        "note": "Generated from canonical role assignments. Exact model names are validated where possible; unvalidated names are marked not-tested."
    }
    return json.dumps(artifact, indent=2, ensure_ascii=False) + "\n"


def _emit_config(target: dict[str, Any]) -> str:
    """Emit a platform config file (e.g. opencode.json)."""
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
    parser.add_argument("--target", default=None, help="Target platform ID to generate (e.g. claude-code, codex, opencode)")
    parser.add_argument("--all", action="store_true", help="Generate all non-copilot targets")
    parser.add_argument("--dry-run", action="store_true", help="Report what would be written without writing")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    if not root.is_dir():
        print(f"Error: project root does not exist or is not a directory: {root}", file=sys.stderr)
        return 2

    try:
        target_mapping = load_target_mapping(root)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as e:
        print(f"Error: target-mapping.json is malformed: {e}", file=sys.stderr)
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

    catalog = load_model_catalog(root)
    assets = scan_canonical_assets(root)

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
    for target in targets_to_run:
        tid = target["id"]
        if args.dry_run:
            manifest = build_output_manifest(target, assets)
            print(f"[dry-run] {tid}: {len(manifest)} files would be written")
            for entry in manifest:
                print(f"  {entry['path']} ({entry['type']})")
            all_written.extend(entry["path"] for entry in manifest)
        else:
            written = emit_for_target(root, target, assets, catalog, dry_run=False)
            print(f"[generated] {tid}: {len(written)} files written")
            all_written.extend(written)

    print(f"\nTotal: {len(all_written)} files {'would be written' if args.dry_run else 'written'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
