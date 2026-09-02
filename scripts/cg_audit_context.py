#!/usr/bin/env python3
"""cg-audit-context — Compound GPID context and model-governance audit.

Inventories context-contributing files, estimates token burden with chars / 4,
counts prompt and agent references, inventories model declarations, detects
duplicate paragraph blocks, and writes JSON/Markdown reports.

Usage:
    python scripts/cg_audit_context.py [--root <path>] [--output-dir <path>] [--format json|md|both] [--baseline context-audit.json] [--recommendations] [--token-output-dir <path>] [--no-token-artifacts]

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
        f"cg-audit-context requires Python 3.8+; found {sys.version.split()[0]}",
        file=sys.stderr,
    )
    sys.exit(1)

import argparse
import csv
import hashlib
import io
import json
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Sequence

_scripts_dir = str(Path(__file__).parent)
if _scripts_dir not in sys.path:
    sys.path.insert(0, _scripts_dir)

from brain.utils import parse_frontmatter, write_atomic  # noqa: E402

DISCLAIMER = "Token estimates are heuristic (chars/4) and intended for directional audit use."

SCAN_CATEGORIES = {
    "prompts": ".github/prompts/**/*.prompt.md",
    "agents": ".github/agents/**/*.agent.md",
    "skills": ".github/skills/**/SKILL.md",
    "instructions": ".github/instructions/**/*.instructions.md",
    "shared": ".github/shared/**/*",
    "template": ".github/copilot-instructions.template.md",
    "docs": "docs/**/*.md",
    "brain": ".cg-docs/BRAIN*.md",
    "brain_index": ".cg-docs/brain-index.json",
    "context": "compound-gpid.context.md",
    "roadmap": "roadmap.json",
}

TOKEN_ARTIFACT_FILENAMES = (
    "TOKEN-BUDGET.md",
    "TOKEN-DASHBOARD.md",
    "token-audit.json",
    "context-map.json",
    "regression-check.json",
    "workflow-costs.csv",
    "large-context-warnings.md",
)

MODEL_CATALOG_PATH = ".github/shared/model-catalog.json"
MODEL_ROLES = {
    "inherited",
    "coding",
    "review",
    "reasoning",
    "mechanical",
    "fallback",
    "research-execution",
}

THRESHOLD_INSTRUCTION_IMMEDIATE = 1500
THRESHOLD_INSTRUCTION_CRITICAL = 3000
THRESHOLD_PROMPT_IMMEDIATE = 3000
THRESHOLD_PROMPT_REVIEW = 1500
THRESHOLD_AGENT_REVIEW = 1500
THRESHOLD_SKILL_IMMEDIATE = 2000
THRESHOLD_SKILL_REVIEW = 1200
THRESHOLD_REFS_IMMEDIATE = 5
THRESHOLD_DUPLICATE_FILES = 3
THRESHOLD_DUPLICATE_TOKENS = 1000
THRESHOLD_HIGH_FREQ_PROMPT_WARN = 5000
THRESHOLD_HIGH_FREQ_PROMPT_FAIL = 6000
THRESHOLD_ALWAYS_ON_WARN = 4500
THRESHOLD_ALWAYS_ON_FAIL = 6000

FILE_REF_RE = re.compile(
    r"\b(?:compound-gpid(?:\.context|\.local)?\.md|roadmap\.json|BRAIN(?:-\d+|-log)?\.md|"
    r"brain-index\.json|context\.md|model-guide\.md|copilot-instructions(?:\.template)?\.md)\b",
    re.IGNORECASE,
)
AGENT_REF_RE = re.compile(r"@cg-[a-z-]+")
SKILL_REF_RE = re.compile(r"cg-skill-[a-z-]+")
TOOL_REF_RE = re.compile(r"\b(?:read_file|edit_file|run_in_terminal|grep_search|semantic_search)\b")
LOAD_VERB_RE = re.compile(r"\b(?:must read|load .+skill|consult|dispatch)\b", re.IGNORECASE)
WORKFLOW_TOOL_REF_RE = re.compile(
    r"\b(?:read_file|edit_file|run_in_terminal|grep_search|semantic_search|"
    r"execution_subagent|apply_patch|Task|TodoWrite|TodoRead|AskUserQuestion)\b"
)
WORKFLOW_PATH_REF_RE = re.compile(
    r"(?P<path>"
    r"(?:\.github|\.cg-docs|docs|scripts|tests)[\\/][A-Za-z0-9._/@+\-]+"
    r"|\. tests[\\/][A-Za-z0-9._/@+\-]+"
    r"|compound-gpid(?:\.context|\.local)?\.md"
    r"|roadmap\.json"
    r"|BRAIN(?:-\d+|-log)?\.md"
    r"|brain-index\.json"
    r"|context\.md"
    r"|model-guide\.md"
    r"|copilot-instructions(?:\.template)?\.md"
    r")",
    re.IGNORECASE,
)
WORKFLOW_SOURCE_PATH_PREFIXES = (
    ".github/shared/",
    ".github/prompts/",
    ".github/agents/",
    ".github/skills/",
    ".github/instructions/",
    ".cg-docs/cost/",
    ".cg-docs/token/",
    ".cg-docs/plans/",
    ".cg-docs/strategy/",
    ".cg-docs/reviews/",
    ".cg-docs/work-reports/",
    ".cg-docs/solutions/",
    ".cg-docs/brainstorms/",
    "docs/",
    "scripts/",
    "tests/",
)
WORKFLOW_SOURCE_EXACT_PATHS = {
    ".cg-docs/brain-index.json",
    ".cg-docs/charter.md",
    "compound-gpid.md",
    "compound-gpid.local.md",
    "compound-gpid.context.md",
    "roadmap.json",
    "brain-index.json",
    "context.md",
    "model-guide.md",
    "copilot-instructions.md",
    "copilot-instructions.template.md",
}
ESCALATION_RE = re.compile(r"\b(?:escalat|opus required|borderline|frontier|highest capability)\b", re.IGNORECASE)
_COPILOT_SUFFIX_RE = re.compile(r"\s*\(copilot\)\s*$", re.IGNORECASE)
_PARAGRAPH_SEP_RE = re.compile(r"\n\s*\n")
CONDITIONAL_ROUTING_RE = re.compile(
    r"\b(?:deterministic preflight|risk-class routing|route-aware|resolved mode|staged mode)\b",
    re.IGNORECASE,
)
BROAD_DISPATCH_RE = re.compile(
    r"\b(?:dispatch all|all standard agents|broad fan-out|broad default dispatch)\b",
    re.IGNORECASE,
)
CONTEXT_RISK_ARTIFACT_RE = re.compile(
    r"(?:\.cg-docs/BRAIN(?:-\d+|-NN|-log)?\.md|BRAIN(?:-\d+|-NN|-log)?\.md|"
    r"\.cg-docs/brain-index\.json|brain-index\.json|compound-gpid\.context\.md|"
    r"roadmap\.json|\.cg-docs/|\.cg-docs\b)",
    re.IGNORECASE,
)
CONTEXT_RISK_ACTION_RE = re.compile(
    r"\b(?:read|reading|load|loading|open|scan|search|consult|parse|re-read|rebuild|generate|run)\b",
    re.IGNORECASE,
)
CONTEXT_BROAD_RE = re.compile(
    r"\b(?:read|reading|load|loading|open|scan|search|consult|parse|re-read)\s+(?:the\s+)?"
    r"(?:full|whole|all|entire|any|every)?\s*(?:file|body|artifact|artifacts|directory|"
    r"files|partitions|records|context|roadmap|brain)?",
    re.IGNORECASE,
)
CONTEXT_ALLOWED_RE = re.compile(
    r"\b(?:targeted|matching snippets?|matched topic|topic sections?|headings?|frontmatter|"
    r"titles?|status fields?|structured fields?|feature fields?|milestone fields?|"
    r"Context expansion:|because|skip silently|only|narrowest|query-first|metadata|"
    r"selectively|relevant|related|similar|verify|verification|matching|needed|"
    r"justified|compute|computed)\b",
    re.IGNORECASE,
)
CONTEXT_NEGATION_RE = re.compile(
    r"(?:❌|\b(?:do not|don't|must not|never|without|not|mustn't)\b)",
    re.IGNORECASE,
)
CONTEXT_MAINTENANCE_RE = re.compile(
    r"\b(?:cg-index --brain|rebuild|regenerates?|generate|written by cg-index|"
    r"roadmap commands|setup|audit|tooling|maintenance)\b",
    re.IGNORECASE,
)

ORDINARY_MODEL_PICKER_PROMPTS = {
    ".github/prompts/cg-brainstorm.prompt.md",
    ".github/prompts/cg-ideate.prompt.md",
    ".github/prompts/cg-plan-review.prompt.md",
    ".github/prompts/cg-plan.prompt.md",
    ".github/prompts/cg-review-repos.prompt.md",
    ".github/prompts/cg-strategy.prompt.md",
}

WORKFLOW_REGISTRY = (
    {"workflow_id": "cg-brainstorm", "workflow": "/cg-brainstorm", "path": ".github/prompts/cg-brainstorm.prompt.md"},
    {"workflow_id": "cg-plan", "workflow": "/cg-plan", "path": ".github/prompts/cg-plan.prompt.md"},
    {"workflow_id": "cg-work", "workflow": "/cg-work", "path": ".github/prompts/cg-work.prompt.md"},
    {"workflow_id": "cg-review", "workflow": "/cg-review", "path": ".github/prompts/cg-review.prompt.md"},
    {"workflow_id": "cg-fix-triage", "workflow": "/cg-fix-triage", "path": ".github/prompts/cg-fix-triage.prompt.md"},
    {"workflow_id": "cg-compound", "workflow": "/cg-compound", "path": ".github/prompts/cg-compound.prompt.md"},
    {"workflow_id": "cg-resume", "workflow": "/cg-resume", "path": ".github/prompts/cg-resume.prompt.md"},
    {"workflow_id": "cg-diagnose", "workflow": "/cg-diagnose", "path": ".github/prompts/cg-diagnose.prompt.md"},
    {"workflow_id": "cg-token-audit", "workflow": "/cg-token-audit", "path": ".github/prompts/cg-token-audit.prompt.md"},
)

BENCHMARK_PROMPTS = {
    row["workflow"]: row["path"]
    for row in WORKFLOW_REGISTRY
}

HIGH_FREQUENCY_PROMPTS = set(BENCHMARK_PROMPTS.values())

ORDINARY_CONTEXT_GUARDRAIL_PROMPTS = {
    ".github/prompts/cg-brainstorm.prompt.md",
    ".github/prompts/cg-plan.prompt.md",
    ".github/prompts/cg-work.prompt.md",
    ".github/prompts/cg-review.prompt.md",
    ".github/prompts/cg-resume.prompt.md",
}

BROAD_CONTEXT_GUARDRAIL_ARTIFACTS = (
    ".cg-docs/",
    ".cg-docs",
    "BRAIN-log.md",
    "BRAIN-NN.md",
    "BRAIN-01.md",
    "brain-index.json",
    "compound-gpid.context.md",
    "roadmap.json",
)

DOCS_ONLY_WARNING_PREFIXES = ("docs/",)

ACCEPT_WARNING_PATHS = {
    ".github/agents/cg-roadmap.agent.md",
    ".github/agents/cg-release-scanner.agent.md",
    ".github/agents/cg-learnings-researcher.agent.md",
    ".github/prompts/cg-compound-refresh.prompt.md",
    ".github/prompts/cg-issues.prompt.md",
    ".github/prompts/cg-review-repos.prompt.md",
    ".github/prompts/cg-setup.prompt.md",
    ".github/prompts/cg-strategy.prompt.md",
    ".github/prompts/cg-token-audit.prompt.md",
}

FIX_WARNING_PATHS = {
    ".github/agents/cg-wiki.agent.md",
    ".github/prompts/cg-diagnose.prompt.md",
    ".github/prompts/cg-fixbug.prompt.md",
    ".github/prompts/cg-fix-problems.prompt.md",
    ".github/prompts/cg-ideate.prompt.md",
    ".github/prompts/cg-plan-review.prompt.md",
    ".github/prompts/cg-wiki.prompt.md",
}

EXPECTED_REVIEW_AGENT_COUNTS = {
    "light": 2,
    "standard": 8,
    "data-risk": 8,
    "architecture": 8,
    "full": 10,
}

RELEASE_READINESS_CHECKLIST = [
    "Audit generated successfully.",
    "Guardrail failures are zero, or warnings are documented as maintenance-intentional.",
    "Ordinary model-picker prompts still omit model:.",
    "Premium model usage remains zero.",
    "Model catalog covers every prompt and agent with one role assignment.",
    "OpenAI-first, Haiku mechanical-only, and Sonnet fallback/cross-vendor checks are reviewed.",
    "Exact GPT frontmatter support is validated in VS Code/Copilot before broad GPT prompt edits.",
    "/cg-review and /cg-work remain conditional, not broad, dispatch workflows.",
    "Broad Brain/context reads are targeted, justified, or maintenance-only.",
    "Top remaining optimization candidates are reviewed and accepted or filed as future work.",
    "Python audit tests pass.",
    "Pester safe runner passes in VS Code/PowerShell.",
    "Manual VS Code/Copilot runtime checklist is complete.",
]


def estimate_tokens(text: str) -> int:
    """Return the heuristic token estimate: ``len(text) // 4``.

    Uses chars/4 as a directional approximation. Returns 0 for strings shorter
    than 4 characters (integer floor division). For ASCII-dominant content this
    heuristic is reliable; CJK-heavy files may be underestimated.

    Args:
        text: The full text to estimate.

    Returns:
        Integer token estimate (≥ 0).

    Example::

        estimate_tokens("a" * 400)  # 100
    """
    return len(text) // 4


def rel_path(path: Path, root: Path) -> str:
    """Return the path relative to root as a POSIX string.

    Args:
        path: Absolute path to convert.
        root: Repository root to relativize against.

    Returns:
        POSIX-style relative path string, or absolute POSIX path if outside root.
    """
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def scan_files(root: Path) -> tuple[list[dict[str, Any]], dict[str, dict[str, int]]]:
    """Scan all configured SCAN_CATEGORIES under root and return file records.

    Skips unreadable files with a :mod:`warnings` warning rather than aborting.
    Resolves symlinks to avoid counting the same inode twice.

    Args:
        root: Repository root path.

    Returns:
        Tuple of (files, by_category) where ``files`` is a list of per-file
        dicts (``path``, ``category``, ``characters``, ``estimated_tokens``) and
        ``by_category`` is a dict of category totals.
    """
    files: list[dict[str, Any]] = []
    seen: set[Path] = set()
    by_category: dict[str, dict[str, int]] = {
        name: {"files": 0, "characters": 0, "estimated_tokens": 0}
        for name in SCAN_CATEGORIES
    }

    for category, pattern in SCAN_CATEGORIES.items():
        for path in sorted(root.glob(pattern)):
            if not path.is_file():
                continue
            resolved = path.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            try:
                content = path.read_text(encoding="utf-8-sig")
            except UnicodeDecodeError as exc:
                import warnings
                warnings.warn(f"Skipping {path}: {exc}")
                continue
            chars = len(content)
            tokens = estimate_tokens(content)
            record = {
                "path": rel_path(path, root),
                "category": category,
                "characters": chars,
                "estimated_tokens": tokens,
            }
            files.append(record)
            totals = by_category[category]
            totals["files"] += 1
            totals["characters"] += chars
            totals["estimated_tokens"] += tokens

    return files, by_category


def classify_model_tier(model: str | None) -> str:
    """Classify a model string into a governance tier.

    Args:
        model: Model name from frontmatter (e.g., ``"Claude Sonnet 4.6 (copilot)"``).

    Returns:
        One of ``"premium"``, ``"standard"``, ``"economy"``, ``"missing"``, or ``"unknown"``.

    Example::

        classify_model_tier("Claude Opus 4.6")   # "premium"
        classify_model_tier(None)                 # "missing"
    """
    if not model:
        return "missing"
    normalized = normalize_model_name(model)
    catalog_model = model_catalog_model_lookup({}).get(normalized)
    if catalog_model:
        return str(catalog_model.get("tier", "unknown"))
    if "Opus" in model:
        return "premium"
    if "Sonnet" in model:
        return "standard"
    if "Haiku" in model:
        return "economy"
    return "unknown"


def normalize_model_name(model: str | None) -> str:
    """Strip the ``(copilot)`` vendor suffix from a model string.

    Args:
        model: Raw model string, possibly ``None``.

    Returns:
        Normalised string with suffix removed and whitespace stripped.
        Returns empty string for ``None`` or empty input.

    Example::

        normalize_model_name("Claude Sonnet 4.6 (copilot)")  # "Claude Sonnet 4.6"
    """
    return _COPILOT_SUFFIX_RE.sub("", model or "").strip()


def load_model_catalog(root: Path) -> dict[str, Any]:
    """Load the durable model governance catalog.

    Returns an empty catalog shape when the file is absent so tests can build
    minimal temporary repositories without copying the production catalog.
    """
    path = root / MODEL_CATALOG_PATH
    empty = {
        "schemaVersion": 0,
        "policy": {},
        "frontmatterSupport": [],
        "models": [],
        "assignments": [],
    }
    if not path.exists():
        return empty
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        return {**empty, "load_error": f"{path}: {exc}"}
    for key in empty:
        payload.setdefault(key, empty[key])
    return payload


def model_catalog_model_lookup(catalog: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Return model metadata keyed by normalized model name."""
    return {
        normalize_model_name(str(row.get("name", ""))): row
        for row in catalog.get("models", [])
        if row.get("name")
    }


def model_catalog_support_lookup(catalog: dict[str, Any]) -> dict[str, str]:
    """Return frontmatter support status keyed by normalized model name."""
    return {
        normalize_model_name(str(row.get("model", ""))): str(row.get("status", "unknown"))
        for row in catalog.get("frontmatterSupport", [])
        if row.get("model")
    }


def model_catalog_assignment_lookup(catalog: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Return expected prompt/agent assignments keyed by repository path."""
    return {
        str(row.get("path")): row
        for row in catalog.get("assignments", [])
        if row.get("path")
    }


def extract_model_declarations(root: Path, files: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    """Extract model governance metadata from all prompt and agent files.

    Args:
        root: Repository root path.
        files: File records from :func:`scan_files`.

    Returns:
        List of dicts with keys: ``path``, ``category``, ``model``, ``model_tier``,
        ``has_escalation_condition``, ``tools``.
    """
    catalog = load_model_catalog(root)
    model_lookup = model_catalog_model_lookup(catalog)
    support_lookup = model_catalog_support_lookup(catalog)
    assignment_lookup = model_catalog_assignment_lookup(catalog)
    declarations: list[dict[str, Any]] = []
    for file_record in files:
        if file_record["category"] not in ("prompts", "agents"):
            continue
        path = root / file_record["path"]
        content = path.read_text(encoding="utf-8-sig")
        fm = parse_frontmatter(content)
        model = fm.get("model")
        if model is not None:
            model = str(model)
        path_string = file_record["path"]
        normalized = normalize_model_name(model)
        catalog_model = model_lookup.get(normalized, {})
        assignment = assignment_lookup.get(path_string, {})
        model_tier = (
            "model-picker"
            if model is None and path_string in ORDINARY_MODEL_PICKER_PROMPTS
            else str(catalog_model.get("tier") or classify_model_tier(model))
        )
        declarations.append({
            "path": path_string,
            "category": file_record["category"],
            "model": model,
            "normalized_model": normalized,
            "model_tier": model_tier,
            "vendor": catalog_model.get("vendor") or ("inherited" if model_tier == "model-picker" else "unknown"),
            "family": catalog_model.get("family") or ("Auto" if model_tier == "model-picker" else "unknown"),
            "role": assignment.get("role", "unknown"),
            "preferred_model": assignment.get("preferredModel"),
            "frontmatter_mode": assignment.get("frontmatterMode"),
            "frontmatter_support": support_lookup.get(normalized) if normalized else None,
            "catalog_policy_status": catalog_model.get("policyStatus"),
            "catalog_rationale": assignment.get("rationale"),
            "has_escalation_condition": bool(ESCALATION_RE.search(content)),
            "tools": fm.get("tools"),
        })
    return declarations


def parse_model_guide(path: Path) -> dict[str, str]:
    """Parse ``### Prompts`` / ``### Agents`` assignment tables from the model-guide.

    Reads H3-keyed pipe-delimited tables. Returns an empty dict if the file
    does not exist or contains no matching H3 sections.

    Args:
        path: Path to ``docs/model-guide.md``.

    Returns:
        Dict mapping filename (e.g., ``"cg-review.prompt.md"``) to model string.

    Example::

        guide = parse_model_guide(root / "docs" / "model-guide.md")
        guide.get("cg-review.prompt.md")  # "Claude Sonnet 4.6 (copilot)"
    """
    if not path.exists():
        return {}
    guide = parse_model_guide_assignments(path)
    return {filename: row["model"] for filename, row in guide.items()}


def parse_model_guide_assignments(path: Path) -> dict[str, dict[str, str]]:
    """Parse model-guide assignment tables with ``File | Model | Role | Rationale``.

    The parser remains tolerant of the older two-column table form, but returns
    empty role/rationale values for those rows.
    """
    if not path.exists():
        return {}
    guide: dict[str, dict[str, str]] = {}
    in_table = False
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        stripped = line.strip()
        if stripped in ("### Prompts", "### Agents"):
            in_table = True
            continue
        if in_table and stripped.startswith("### "):
            in_table = False
        if not in_table or not stripped.startswith("|"):
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if len(cells) < 2 or cells[0] in ("File",) or cells[0].startswith("---") or cells[0].startswith(":---"):
            continue
        filename = cells[0].strip("` ")
        model = cells[1].strip("` ")
        role = cells[2].strip("` ") if len(cells) > 2 else ""
        rationale = cells[3].strip("` ") if len(cells) > 3 else ""
        if filename and filename != "---------------":
            guide[filename] = {"model": model, "role": role, "rationale": rationale}
    return guide


def model_guide_matches_declaration(declaration: dict[str, Any], expected: str | None) -> bool:
    """Return whether a model-guide value matches one prompt/agent declaration.

    Inherited/model-picker prompts intentionally omit ``model:`` frontmatter.
    The model guide documents those rows as ``Copilot model picker`` so humans
    can distinguish them from missing metadata; treat that wording as equivalent
    to absent frontmatter only when the catalog role is explicitly inherited.
    """
    if not expected:
        return True
    actual = normalize_model_name(declaration.get("model"))
    guide_value = normalize_model_name(expected)
    if actual == guide_value:
        return True
    if declaration.get("model") is None and declaration.get("role") == "inherited":
        return guide_value.lower() in {"copilot model picker", "model picker", "inherited"}
    return False


def build_model_inventory(root: Path, files: Sequence[dict[str, Any]]) -> dict[str, Any]:
    """Build the full model governance inventory including drift detection.

    Args:
        root: Repository root path.
        files: File records from :func:`scan_files`.

    Returns:
        Dict with keys: ``declarations``, ``missing``, ``drift``,
        ``premium_usage``, ``ordinary_model_picker_violations``.
    """
    declarations = extract_model_declarations(root, files)
    catalog = load_model_catalog(root)
    assignment_lookup = model_catalog_assignment_lookup(catalog)
    support_lookup = model_catalog_support_lookup(catalog)
    guide = parse_model_guide(root / "docs" / "model-guide.md")
    missing = [d for d in declarations if d["model_tier"] == "missing"]
    missing_catalog_assignments = [d for d in declarations if d["role"] == "unknown"]
    invalid_catalog_roles = [
        d for d in declarations
        if d["role"] != "unknown" and d["role"] not in MODEL_ROLES
    ]
    stale_model_names = [
        d for d in declarations
        if d["model"] is not None and d["vendor"] == "unknown"
    ]
    openai_first_violations = []
    haiku_role_violations = []
    sonnet_role_violations = []
    frontmatter_support_gaps = []
    for declaration in declarations:
        if declaration["model"] is None:
            continue
        role = declaration.get("role")
        vendor = declaration.get("vendor")
        normalized = declaration.get("normalized_model")
        preferred = declaration.get("preferred_model")
        preferred_support = support_lookup.get(normalize_model_name(str(preferred))) if preferred else None
        if role in ("coding", "review", "reasoning") and vendor == "anthropic":
            if role == "review" and declaration.get("frontmatter_mode") == "manual-cross-vendor":
                sonnet_role_violations.append(declaration)
            else:
                openai_first_violations.append(declaration)
        if role != "mechanical" and normalized == "Claude Haiku 4.5":
            haiku_role_violations.append(declaration)
        if normalized == "Claude Sonnet 4.6" and role not in ("fallback",):
            if declaration.get("frontmatter_mode") != "manual-cross-vendor":
                sonnet_role_violations.append(declaration)
        if preferred and preferred_support in ("picker-only", "unsupported", "not-tested", None):
            frontmatter_support_gaps.append({**declaration, "preferred_model_support": preferred_support or "missing"})
    catalog_paths = set(assignment_lookup)
    declaration_paths = {d["path"] for d in declarations}
    unused_catalog_assignments = sorted(catalog_paths - declaration_paths)
    drift = []
    for declaration in declarations:
        expected = guide.get(Path(declaration["path"]).name)
        if expected and not model_guide_matches_declaration(declaration, expected):
            drift.append(
                {
                    "path": declaration["path"],
                    "frontmatter_model": declaration["model"],
                    "model_guide_model": expected,
                }
            )
    premium_usage = [d for d in declarations if d["model_tier"] == "premium"]
    ordinary_model_picker_violations = [
        d for d in declarations
        if d["path"] in ORDINARY_MODEL_PICKER_PROMPTS and d["model"] is not None
    ]
    return {
        "declarations": declarations,
        "missing": missing,
        "missing_catalog_assignments": missing_catalog_assignments,
        "invalid_catalog_roles": invalid_catalog_roles,
        "stale_model_names": stale_model_names,
        "openai_first_violations": openai_first_violations,
        "haiku_role_violations": haiku_role_violations,
        "sonnet_role_violations": sonnet_role_violations,
        "frontmatter_support_gaps": frontmatter_support_gaps,
        "unused_catalog_assignments": unused_catalog_assignments,
        "drift": drift,
        "premium_usage": premium_usage,
        "ordinary_model_picker_violations": ordinary_model_picker_violations,
        "catalog": {
            "path": MODEL_CATALOG_PATH,
            "load_error": catalog.get("load_error"),
            "assignment_count": len(assignment_lookup),
        },
    }


def count_references(path: str, content: str) -> dict[str, Any]:
    """Count all context-file and tool reference types in a file's content.

    Args:
        path: Relative path string (used as the ``path`` key in the returned row).
        content: Full text content of the file.

    Returns:
        Dict with keys: ``path``, ``file_refs``, ``agent_refs``, ``skill_refs``,
        ``tool_refs``, ``load_verbs``, ``total_refs``.
    """
    file_refs = len(FILE_REF_RE.findall(content))
    agent_refs = len(AGENT_REF_RE.findall(content))
    skill_refs = len(SKILL_REF_RE.findall(content))
    tool_refs = len(TOOL_REF_RE.findall(content))
    load_verbs = len(LOAD_VERB_RE.findall(content))
    total_refs = file_refs + agent_refs + skill_refs + tool_refs + load_verbs
    return {"path": path, "file_refs": file_refs, "agent_refs": agent_refs,
            "skill_refs": skill_refs, "tool_refs": tool_refs,
            "load_verbs": load_verbs, "total_refs": total_refs}


def build_reference_matrix(root: Path, files: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    """Build a reference-count matrix for all prompt and agent files, sorted by total refs.

    Args:
        root: Repository root path.
        files: File records from :func:`scan_files`.

    Returns:
        List of reference-count dicts (see :func:`count_references`), sorted descending by ``total_refs``.
    """
    rows = []
    for file_record in files:
        if file_record["category"] not in ("prompts", "agents"):
            continue
        path = root / file_record["path"]
        rows.append(count_references(file_record["path"], path.read_text(encoding="utf-8-sig")))
    return sorted(rows, key=lambda row: (-row["total_refs"], row["path"]))


def count_dispatch_burden(path: str, content: str) -> dict[str, Any]:
    """Return a directional prompt dispatch-burden signal.

    Distinguishes prompts whose review agent references are explicitly
    conditional (risk-class routing) from prompts that encode broad dispatch
    as the default posture. Does not estimate runtime call counts.

    Args:
        path: Relative path string (used as the ``path`` key).
        content: Full text content of the prompt file.

    Returns:
        Dict with keys: ``path``, ``dispatch_refs``, ``conditional_routing``,
        ``broad_dispatch``, ``burden_level``.
    """
    dispatch_refs = len(set(AGENT_REF_RE.findall(content)))
    conditional_routing = bool(CONDITIONAL_ROUTING_RE.search(content))
    broad_dispatch = bool(BROAD_DISPATCH_RE.search(content)) and not conditional_routing
    if conditional_routing:
        burden_level = "conditional"
    elif broad_dispatch or dispatch_refs >= 8:
        burden_level = "broad"
    elif dispatch_refs:
        burden_level = "limited"
    else:
        burden_level = "none"
    return {
        "path": path,
        "dispatch_refs": dispatch_refs,
        "conditional_routing": conditional_routing,
        "broad_dispatch": broad_dispatch,
        "burden_level": burden_level,
    }


def build_dispatch_burden(root: Path, files: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    """Build a dispatch-burden signal table for all prompt files.

    Args:
        root: Repository root path.
        files: File records from :func:`scan_files`.

    Returns:
        List of dispatch-burden dicts (see :func:`count_dispatch_burden`), broad-first.
    """
    rows = []
    for file_record in files:
        if file_record["category"] != "prompts":
            continue
        path = root / file_record["path"]
        rows.append(count_dispatch_burden(file_record["path"], path.read_text(encoding="utf-8-sig")))
    return sorted(rows, key=lambda row: (row["burden_level"] != "broad", row["path"]))


def classify_context_loading_line(_path: str, line: str) -> dict[str, Any] | None:
    """Classify one line as a context-loading signal, if applicable.

    Args:
        line: Single line of text.

    Returns:
        ``None`` for irrelevant lines, otherwise a dict with ``level`` and
        ``reason``. Levels are ``risk``, ``justified``, or ``targeted``.
    """
    stripped = " ".join(line.strip().split())
    if not stripped or not CONTEXT_RISK_ARTIFACT_RE.search(stripped):
        return None
    has_action = bool(CONTEXT_RISK_ACTION_RE.search(stripped))
    if not has_action:
        return None
    pure_write_action = re.search(r"\b(?:delete|replace|rename|move|modify|write)\b", stripped, re.IGNORECASE)
    load_action = re.search(r"\b(?:read|reading|load|loading|open|scan|search|consult|parse|re-read)\b", stripped, re.IGNORECASE)
    if pure_write_action and not load_action:
        return None

    artifact = CONTEXT_RISK_ARTIFACT_RE.search(stripped).group(0)
    broad = bool(CONTEXT_BROAD_RE.search(stripped))
    allowed = bool(CONTEXT_ALLOWED_RE.search(stripped))
    negated = bool(CONTEXT_NEGATION_RE.search(stripped))
    maintenance = bool(CONTEXT_MAINTENANCE_RE.search(stripped))

    if negated:
        return {"level": "targeted", "artifact": artifact, "reason": "targeted or guarded context-loading instruction"}
    if re.search(r"\.cg-docs/BRAIN\.md|`?BRAIN\.md`?", stripped) and "BRAIN-log.md" not in stripped:
        return {"level": "targeted", "artifact": artifact, "reason": "agent-facing Brain meta-index"}
    if "brain-index.json" in stripped and not maintenance and not negated and not allowed:
        return {"level": "risk", "artifact": "brain-index.json", "reason": "prompt may read tooling index wholesale"}
    if maintenance and (allowed or "cg-index --brain" in stripped):
        return {"level": "justified", "artifact": artifact, "reason": "maintenance/tooling workflow"}
    if "Context expansion:" in stripped:
        return {"level": "justified", "artifact": artifact, "reason": "explicit expansion rationale"}
    if broad and not allowed and not negated:
        return {"level": "risk", "artifact": artifact, "reason": "broad context-loading instruction"}
    if allowed or negated:
        return {"level": "targeted", "artifact": artifact, "reason": "targeted or guarded context-loading instruction"}
    if artifact.lower() in ("compound-gpid.context.md", "roadmap.json") and re.search(r"\bread\b", stripped, re.IGNORECASE):
        return {"level": "risk", "artifact": artifact, "reason": "unqualified large artifact read"}
    return {"level": "targeted", "artifact": artifact, "reason": "context artifact reference with loading verb"}


def build_context_loading_risks(root: Path, files: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    """Collect broad context-loading signals from prompt, agent, skill, shared, and doc files."""
    scanned_categories = {"prompts", "agents", "skills", "instructions", "shared", "docs"}
    rows: list[dict[str, Any]] = []
    for file_record in files:
        if file_record["category"] not in scanned_categories:
            continue
        path = root / file_record["path"]
        try:
            lines = path.read_text(encoding="utf-8-sig").splitlines()
        except UnicodeDecodeError:
            continue
        for line_number, line in enumerate(lines, start=1):
            classification = classify_context_loading_line(file_record["path"], line)
            if not classification:
                continue
            snippet = " ".join(line.strip().split())[:220]
            rows.append(
                {
                    "path": file_record["path"],
                    "line": line_number,
                    "level": classification["level"],
                    "artifact": classification["artifact"],
                    "reason": classification["reason"],
                    "snippet": snippet,
                }
            )
    order = {"risk": 0, "justified": 1, "targeted": 2}
    return sorted(rows, key=lambda row: (order.get(row["level"], 9), row["path"], row["line"]))


def iter_paragraph_blocks(content: str) -> Iterable[str]:
    """Yield paragraph blocks of at least 4 non-blank lines from content.

    Args:
        content: Full text of a file.

    Returns:
        Iterator over multi-line paragraph strings (blank-line separated, ≥4 lines).
    """
    for block in _PARAGRAPH_SEP_RE.split(content):
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        if len(lines) >= 4:
            yield "\n".join(lines)


def normalize_block(block: str) -> str:
    """Normalise a paragraph block by collapsing internal whitespace.

    Args:
        block: Raw paragraph string.

    Returns:
        String with each line's internal whitespace collapsed to single spaces.
    """
    lines = [" ".join(line.strip().split()) for line in block.splitlines()]
    return "\n".join(lines).strip()


def detect_duplicates(root: Path, files: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    """Detect paragraph blocks that appear verbatim across multiple files.

    Blocks must be ≥4 lines. Deduplication uses SHA-256 of the normalised block.
    Only blocks appearing in ≥ ``THRESHOLD_DUPLICATE_FILES`` files are returned.

    Args:
        root: Repository root path.
        files: File records from :func:`scan_files`.

    Returns:
        List of dicts with keys: ``block_preview``, ``file_count``,
        ``total_chars``, ``estimated_tokens``, ``files``.
    """
    blocks: dict[str, dict[str, Any]] = {}
    for file_record in files:
        path = root / file_record["path"]
        content = path.read_text(encoding="utf-8-sig")
        for block in iter_paragraph_blocks(content):
            normalized = normalize_block(block)
            digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
            entry = blocks.setdefault(
                digest,
                {"block": normalized[:80], "files": set(), "total_chars": 0},
            )
            entry["files"].add(file_record["path"])
            entry["total_chars"] += len(normalized)

    duplicates = []
    for entry in blocks.values():
        files_for_block = sorted(entry["files"])
        if len(files_for_block) >= THRESHOLD_DUPLICATE_FILES:
            duplicates.append(
                {
                    "block_preview": entry["block"][:80],
                    "file_count": len(files_for_block),
                    "total_chars": entry["total_chars"],
                    "total_redundant_tokens": entry["total_chars"] // 4,
                    "files": files_for_block,
                }
            )
    return sorted(duplicates, key=lambda row: (-row["file_count"], -row["total_chars"]))


def _has_broad_tools(tools: Any) -> bool:
    if tools is None:
        return False
    if isinstance(tools, list):
        values = [str(v).lower() for v in tools]
    else:
        values = [str(tools).lower()]
    joined = " ".join(values)
    return "edit" in joined or "write" in joined or "run" in joined or "*" in joined


def classify_optimization_candidates(
    files: Sequence[dict[str, Any]],
    reference_matrix: Sequence[dict[str, Any]],
    model_inventory: dict[str, Any],
    duplicates: Sequence[dict[str, Any]],
) -> dict[str, Any]:
    """Classify files into immediate, needs-review, and acceptable buckets.

    Args:
        files: File records from :func:`scan_files`.
        reference_matrix: Output of :func:`build_reference_matrix`.
        model_inventory: Output of :func:`build_model_inventory`.
        duplicates: Output of :func:`detect_duplicates`.

    Returns:
        Dict with keys: ``immediate`` (list), ``needs_review`` (list),
        ``acceptable_count`` (int).
    """
    refs_by_path = {row["path"]: row for row in reference_matrix}
    models_by_path = {row["path"]: row for row in model_inventory["declarations"]}
    drift_paths = {row["path"] for row in model_inventory["drift"]}
    immediate: list[dict[str, Any]] = []
    needs_review: list[dict[str, Any]] = []
    classified_paths: set[str] = set()

    def add(bucket: list[dict[str, Any]], path: str, category: str, reason: str) -> None:
        bucket.append({"path": path, "category": category, "reason": reason})
        classified_paths.add(path)

    for file_record in files:
        path = file_record["path"]
        category = file_record["category"]
        tokens = int(file_record["estimated_tokens"])
        refs = refs_by_path.get(path, {"total_refs": 0})
        model = models_by_path.get(path)
        reasons_immediate: list[str] = []
        reasons_review: list[str] = []

        if category == "instructions" and tokens >= THRESHOLD_INSTRUCTION_IMMEDIATE:
            reasons_immediate.append(f"instruction estimated tokens >= {THRESHOLD_INSTRUCTION_IMMEDIATE}")
        if category == "prompts":
            if tokens >= THRESHOLD_PROMPT_IMMEDIATE:
                reasons_immediate.append(f"prompt estimated tokens >= {THRESHOLD_PROMPT_IMMEDIATE}")
            elif tokens >= THRESHOLD_PROMPT_REVIEW:
                reasons_review.append("prompt size exceeds review threshold")
        if category == "agents" and tokens >= THRESHOLD_AGENT_REVIEW:
            reasons_review.append(f"agent estimated tokens >= {THRESHOLD_AGENT_REVIEW}")
        if category == "skills":
            if tokens >= THRESHOLD_SKILL_IMMEDIATE:
                reasons_immediate.append(f"skill estimated tokens >= {THRESHOLD_SKILL_IMMEDIATE}")
            elif tokens >= THRESHOLD_SKILL_REVIEW:
                reasons_review.append(f"skill estimated tokens >= {THRESHOLD_SKILL_REVIEW}")
        if refs["total_refs"] >= THRESHOLD_REFS_IMMEDIATE:
            reasons_review.append(f"reference count >= {THRESHOLD_REFS_IMMEDIATE}")
        if model:
            if model["model_tier"] == "premium" and not model["has_escalation_condition"]:
                reasons_immediate.append("premium model without escalation condition")
            if category == "agents" and model["model_tier"] == "premium" and _has_broad_tools(model.get("tools")):
                reasons_immediate.append("agent has broad tools and premium model")
            if model["model_tier"] == "missing" and refs["total_refs"] >= 3:
                reasons_review.append("missing model in high-reference prompt/agent")
            if path in {
                violation["path"]
                for violation in model_inventory.get("ordinary_model_picker_violations", [])
            }:
                reasons_immediate.append("ordinary prompt hard-codes model instead of inheriting model picker")
        if path in drift_paths:
            reasons_review.append("model guide drift")

        if reasons_immediate:
            add(immediate, path, category, "; ".join(reasons_immediate + reasons_review))
        elif reasons_review:
            add(needs_review, path, category, "; ".join(reasons_review))

    for duplicate in duplicates:
        if (
            duplicate["file_count"] >= THRESHOLD_DUPLICATE_FILES
            and duplicate["total_redundant_tokens"] >= THRESHOLD_DUPLICATE_TOKENS
        ):
            dup_reason = f"duplicate block appears in {duplicate['file_count']} files"
            immediate.append({"path": "(duplicate block)", "category": "duplicates", "reason": dup_reason})

    return {"immediate": immediate, "needs_review": needs_review,
            "acceptable_count": max(0, len(files) - len(classified_paths))}


def _count_context_levels(rows: Sequence[dict[str, Any]], path: str | None = None) -> dict[str, int]:
    """Count context-loading signal levels, optionally limited to one path."""
    selected = [row for row in rows if path is None or row.get("path") == path]
    return {
        "risk": sum(1 for row in selected if row.get("level") == "risk"),
        "justified": sum(1 for row in selected if row.get("level") == "justified"),
        "targeted": sum(1 for row in selected if row.get("level") == "targeted"),
    }


def validate_workflow_registry(registry: Sequence[dict[str, str]]) -> None:
    """Validate stable workflow registry rows.

    Args:
        registry: Sequence of dicts with ``workflow_id``, ``workflow``, and
            ``path`` keys.

    Raises:
        ValueError: If a required key is missing or a workflow id is duplicated.
    """
    seen: set[str] = set()
    for index, row in enumerate(registry, start=1):
        for key in ("workflow_id", "workflow", "path"):
            if not row.get(key):
                raise ValueError(f"Workflow registry row {index} is missing {key}")
        workflow_id = row["workflow_id"]
        if workflow_id in seen:
            raise ValueError(f"Duplicate workflow_id: {workflow_id}")
        seen.add(workflow_id)


def _observability(status: str, measurement_note: str) -> dict[str, str]:
    return {"status": status, "measurement_note": measurement_note}


def workflow_observability(available: bool) -> dict[str, dict[str, str]]:
    """Return Phase 1.1 observability statuses for one workflow row.

    Runtime-only quantities are intentionally marked ``not_observed`` until
    future command-output instrumentation exists.
    """
    source_status = "observed" if available else "not_observed"
    static_status = "partially_observed" if available else "not_observed"
    return {
        "prompt_source": _observability(
            source_status,
            "Derived from the workflow prompt file when it exists.",
        ),
        "estimated_token_pressure": _observability(
            source_status,
            "Estimated with the repository chars/4 heuristic; this is not a provider token count.",
        ),
        "files_read": _observability(
            static_status,
            "Static prompt text references files, but actual runtime reads require transcript or wrapper instrumentation.",
        ),
        "skills_loaded": _observability(
            static_status,
            "Static prompt text references skills, but actual runtime skill loading depends on execution path.",
        ),
        "agents_dispatched": _observability(
            static_status,
            "Static prompt text references agents; conditional routing means actual dispatch is runtime-dependent.",
        ),
        "mcp_tool_usage": _observability(
            static_status,
            "Static prompt text references known tools; actual MCP/tool calls are runtime-dependent.",
        ),
        "command_output_size": _observability(
            "not_observed",
            "Phase 1.1 excludes command-output summary wrappers, so output bytes are not instrumented.",
        ),
        "summary_size": _observability(
            "not_observed",
            "Phase 1.1 has no transcript summary instrumentation; track this in the command-output phase.",
        ),
    }


def validate_observability_matrix(observability: dict[str, dict[str, str]]) -> None:
    """Validate that every observability metric has a known status."""
    allowed = {"observed", "partially_observed", "not_observed", "not_applicable"}
    for metric, row in observability.items():
        status = row.get("status")
        if not status:
            raise ValueError(f"Observability metric {metric} is missing status")
        if status not in allowed:
            raise ValueError(f"Observability metric {metric} has invalid status: {status}")


def _unique_matches(pattern: re.Pattern[str], content: str) -> list[str]:
    return sorted({match.group(0) for match in pattern.finditer(content)})


def _line_matches_with_action(pattern: re.Pattern[str], content: str) -> list[str]:
    values: set[str] = set()
    for line in content.splitlines():
        if not (CONTEXT_RISK_ACTION_RE.search(line) or LOAD_VERB_RE.search(line)):
            continue
        values.update(match.group(0) for match in pattern.finditer(line))
    return sorted(values)


def _normalize_workflow_path_reference(value: str) -> str:
    path = value.strip().strip("`'\"()[]{}<>,;:")
    while path.endswith("."):
        path = path[:-1]
    path = path.replace("\\", "/")
    if path.startswith("./"):
        path = path[2:]
    if path.startswith(". tests/"):
        path = "tests/" + path[len(". tests/"):]
    return path


def _is_workflow_source_path(path: str) -> bool:
    if path in WORKFLOW_SOURCE_EXACT_PATHS:
        return True
    if re.fullmatch(r"BRAIN(?:-\d+|-log)?\.md", path, re.IGNORECASE):
        return True
    if re.fullmatch(r"\.cg-docs/BRAIN(?:-\d+|-log)?\.md", path, re.IGNORECASE):
        return True
    return path.startswith(WORKFLOW_SOURCE_PATH_PREFIXES)


def _workflow_path_matches(content: str, *, require_action: bool = False) -> list[str]:
    values: set[str] = set()
    for line in content.splitlines():
        if require_action and not (CONTEXT_RISK_ACTION_RE.search(line) or LOAD_VERB_RE.search(line)):
            continue
        for match in WORKFLOW_PATH_REF_RE.finditer(line):
            path = _normalize_workflow_path_reference(match.group("path"))
            if _is_workflow_source_path(path):
                values.add(path)
    return sorted(values)


def _large_context_warning_status(path: str, candidates: dict[str, Any]) -> str:
    for row in candidates.get("immediate", []):
        if row.get("path") == path:
            return "immediate"
    for row in candidates.get("needs_review", []):
        if row.get("path") == path:
            return "needs_review"
    return "none"


def _duplicate_pressure_for_path(path: str, duplicates: Sequence[dict[str, Any]]) -> int:
    return sum(
        int(row.get("total_redundant_tokens", 0))
        for row in duplicates
        if path in row.get("files", [])
    )


def build_workflow_telemetry(root: Path, report: dict[str, Any]) -> dict[str, Any]:
    """Build Phase 1.1 workflow-level token/context telemetry.

    The telemetry is deterministic and source-derived. It intentionally marks
    runtime-only fields as unobserved rather than inferring transcript behavior.
    """
    validate_workflow_registry(WORKFLOW_REGISTRY)
    files_by_path = {row["path"]: row for row in report.get("files", [])}
    refs_by_path = {row["path"]: row for row in report.get("reference_matrix", [])}
    dispatch_by_path = {row["path"]: row for row in report.get("dispatch_burden", [])}
    models_by_path = {
        row["path"]: row
        for row in report.get("model_inventory", {}).get("declarations", [])
    }
    context_rows = report.get("context_loading_risks", [])
    duplicates = report.get("duplicates", [])
    candidates = report.get("optimization_candidates", {})
    workflow_rows: list[dict[str, Any]] = []
    observability_matrix: dict[str, dict[str, dict[str, str]]] = {}

    for workflow in WORKFLOW_REGISTRY:
        path_string = workflow["path"]
        file_row = files_by_path.get(path_string)
        prompt_path = root / path_string
        content = prompt_path.read_text(encoding="utf-8-sig") if prompt_path.exists() else ""
        ref_row = refs_by_path.get(path_string, {})
        dispatch_row = dispatch_by_path.get(path_string, {})
        model_row = models_by_path.get(path_string, {})
        context_counts = _count_context_levels(context_rows, path_string)
        observability = workflow_observability(file_row is not None)
        validate_observability_matrix(observability)
        observability_matrix[workflow["workflow_id"]] = observability
        file_references = _workflow_path_matches(content)
        likely_file_reads = _workflow_path_matches(content, require_action=True)
        tool_references = _unique_matches(WORKFLOW_TOOL_REF_RE, content)
        file_ref_count = max(int(ref_row.get("file_refs", 0)), len(file_references))
        tool_ref_count = max(int(ref_row.get("tool_refs", 0)), len(tool_references))
        agent_ref_count = int(ref_row.get("agent_refs", 0))
        skill_ref_count = int(ref_row.get("skill_refs", 0))
        load_verb_count = int(ref_row.get("load_verbs", 0))
        workflow_rows.append({
            "workflow_id": workflow["workflow_id"],
            "workflow": workflow["workflow"],
            "path": path_string,
            "available": file_row is not None,
            "characters": int(file_row["characters"]) if file_row else None,
            "estimated_tokens": int(file_row["estimated_tokens"]) if file_row else None,
            "total_refs": file_ref_count + agent_ref_count + skill_ref_count + tool_ref_count + load_verb_count,
            "file_refs": file_ref_count,
            "agent_refs": agent_ref_count,
            "skill_refs": skill_ref_count,
            "tool_refs": tool_ref_count,
            "load_verbs": load_verb_count,
            "file_references": file_references,
            "likely_file_reads": likely_file_reads,
            "skill_references": _unique_matches(SKILL_REF_RE, content),
            "likely_skill_loads": _line_matches_with_action(SKILL_REF_RE, content),
            "agent_references": _unique_matches(AGENT_REF_RE, content),
            "tool_references": tool_references,
            "model": model_row.get("model"),
            "model_tier": model_row.get("model_tier"),
            "context_risk_count": context_counts["risk"],
            "context_justified_count": context_counts["justified"],
            "context_targeted_count": context_counts["targeted"],
            "dispatch_refs": int(dispatch_row.get("dispatch_refs", 0)),
            "conditional_routing": bool(dispatch_row.get("conditional_routing", False)),
            "dispatch_burden": dispatch_row.get("burden_level", "none"),
            "repeated_context_tokens": _duplicate_pressure_for_path(path_string, duplicates),
            "large_context_warning_status": _large_context_warning_status(path_string, candidates),
            "observability": observability,
        })

    return {
        "schema_version": 1,
        "workflows": workflow_rows,
        "observability_matrix": observability_matrix,
        "measurement_note": "Workflow telemetry is deterministic source analysis; runtime behavior is partially or not observed unless explicitly instrumented.",
    }


def _review_agent_counts_from_contract(root: Path) -> dict[str, Any]:
    """Return statically measurable review-agent counts from the shared contract.

    The contract intentionally uses shorthand for risk routes ("all standard
    agents"). This parser resolves those shorthand rows against the explicit
    standard and full rows so guardrails can detect accidental count drift.
    """
    path = root / ".github" / "shared" / "review-routing.contract.md"
    if not path.exists():
        return {"available": False, "counts": {}, "path": rel_path(path, root)}
    content = path.read_text(encoding="utf-8-sig")
    counts: dict[str, int] = {}
    row_text: dict[str, str] = {}
    for mode in EXPECTED_REVIEW_AGENT_COUNTS:
        match = re.search(rf"\|\s*`{re.escape(mode)}`\s*\|\s*(.*?)\s*\|", content, re.IGNORECASE)
        if match:
            row_text[mode] = match.group(1)
            counts[mode] = len(set(AGENT_REF_RE.findall(match.group(1))))
    standard_count = counts.get("standard", EXPECTED_REVIEW_AGENT_COUNTS["standard"])
    for mode in ("data-risk", "architecture"):
        if "all `standard` agents" in row_text.get(mode, "") or "all standard agents" in row_text.get(mode, ""):
            counts[mode] = standard_count
    if "full" in row_text and "all `standard` agents" in row_text["full"]:
        extra_agents = len(set(AGENT_REF_RE.findall(row_text["full"])))
        counts["full"] = standard_count + extra_agents
    return {"available": True, "counts": counts, "path": rel_path(path, root)}


def build_benchmark_summary(root: Path, report: dict[str, Any]) -> dict[str, Any]:
    """Build Phase 6 benchmark rows from an existing audit report.

    Args:
        root: Repository root.
        report: Partial or complete audit report with file, model, reference,
            dispatch, and context-loading sections.

    Returns:
        Dict containing workflow rows, aggregate model/context signals, and
        static review-agent counts.
    """
    context_rows = report.get("context_loading_risks", [])
    telemetry = report.get("workflow_telemetry") or build_workflow_telemetry(root, report)
    workflows: list[dict[str, Any]] = [
        {
            "workflow_id": row.get("workflow_id"),
            "workflow": row["workflow"],
            "path": row["path"],
            "available": row.get("available"),
            "characters": row.get("characters"),
            "estimated_tokens": row.get("estimated_tokens"),
            "total_refs": row.get("total_refs", 0),
            "file_refs": row.get("file_refs", 0),
            "agent_refs": row.get("agent_refs", 0),
            "skill_refs": row.get("skill_refs", 0),
            "tool_refs": row.get("tool_refs", 0),
            "load_verbs": row.get("load_verbs", 0),
            "model": row.get("model"),
            "model_tier": row.get("model_tier"),
            "context_risk_count": row.get("context_risk_count", 0),
            "context_justified_count": row.get("context_justified_count", 0),
            "context_targeted_count": row.get("context_targeted_count", 0),
            "dispatch_refs": row.get("dispatch_refs", 0),
            "conditional_routing": row.get("conditional_routing", False),
            "dispatch_burden": row.get("dispatch_burden", "none"),
            "command_output_status": row.get("observability", {}).get("command_output_size", {}).get("status"),
            "summary_output_status": row.get("observability", {}).get("summary_size", {}).get("status"),
        }
        for row in telemetry.get("workflows", [])
    ]

    brain_skill = root / ".github" / "skills" / "cg-skill-brain-query" / "SKILL.md"
    brain_text = brain_skill.read_text(encoding="utf-8-sig") if brain_skill.exists() else ""
    brain_rows = [
        row for row in context_rows
        if row.get("artifact") in ("BRAIN-log.md", "BRAIN-NN.md", "brain-index.json", ".cg-docs/", ".cg-docs")
        or "BRAIN" in str(row.get("artifact", ""))
        or "brain-index.json" in str(row.get("snippet", ""))
    ]
    brain_counts = _count_context_levels(brain_rows)
    workflows.append(
        {
            "workflow": "Knowledge Brain/context lookup",
            "path": ".github/skills/cg-skill-brain-query/SKILL.md",
            "available": brain_skill.exists(),
            "characters": len(brain_text) if brain_text else None,
            "estimated_tokens": estimate_tokens(brain_text) if brain_text else None,
            "total_refs": 0,
            "file_refs": 0,
            "agent_refs": 0,
            "skill_refs": 0,
            "load_verbs": 0,
            "model": None,
            "model_tier": None,
            "context_risk_count": brain_counts["risk"],
            "context_justified_count": brain_counts["justified"],
            "context_targeted_count": brain_counts["targeted"],
            "dispatch_refs": 0,
            "conditional_routing": False,
            "dispatch_burden": "none",
            "query_first": bool(
                re.search(r"query-first|Match Topics|matched topic", brain_text, re.IGNORECASE)
                and re.search(r"BRAIN\.md", brain_text)
            ),
        }
    )

    model_inventory = report.get("model_inventory", {})
    return {
        "workflows": workflows,
        "model_governance": {
            "premium_usage_count": len(model_inventory.get("premium_usage", [])),
            "missing_model_count": len(model_inventory.get("missing", [])),
            "model_drift_count": len(model_inventory.get("drift", [])),
            "ordinary_model_picker_violations": len(model_inventory.get("ordinary_model_picker_violations", [])),
            "openai_first_violations": len(model_inventory.get("openai_first_violations", [])),
            "haiku_role_violations": len(model_inventory.get("haiku_role_violations", [])),
            "sonnet_role_violations": len(model_inventory.get("sonnet_role_violations", [])),
        },
        "context_loading": _count_context_levels(context_rows),
        "review_agent_counts": _review_agent_counts_from_contract(root),
        "comparison": None,
    }


def compare_benchmark_to_baseline(current: dict[str, Any], baseline: dict[str, Any]) -> dict[str, Any]:
    """Compare current benchmark output with a previous audit JSON payload."""
    current_benchmark = current.get("benchmark", {})
    baseline_benchmark = baseline.get("benchmark") or _legacy_benchmark_from_report(baseline)
    baseline_rows = {
        row.get("workflow"): row
        for row in baseline_benchmark.get("workflows", [])
    }
    workflow_deltas: list[dict[str, Any]] = []
    for current_row in current_benchmark.get("workflows", []):
        workflow = current_row.get("workflow")
        previous = baseline_rows.get(workflow, {})
        delta = {
            "workflow": workflow,
            "path": current_row.get("path"),
            "baseline_available": bool(previous),
            "estimated_tokens_delta": None,
            "total_refs_delta": None,
            "context_risk_count_delta": None,
            "dispatch_refs_delta": None,
            "dispatch_burden_before": previous.get("dispatch_burden"),
            "dispatch_burden_after": current_row.get("dispatch_burden"),
        }
        for key in ("estimated_tokens", "total_refs", "context_risk_count", "dispatch_refs"):
            if current_row.get(key) is not None and previous.get(key) is not None:
                delta[f"{key}_delta"] = int(current_row[key]) - int(previous[key])
        workflow_deltas.append(delta)

    current_model = current_benchmark.get("model_governance", {})
    baseline_model = baseline_benchmark.get("model_governance", {})
    model_delta: dict[str, Any] = {}
    for key in ("premium_usage_count", "ordinary_model_picker_violations", "missing_model_count", "model_drift_count"):
        if current_model.get(key) is not None and baseline_model.get(key) is not None:
            model_delta[f"{key}_delta"] = int(current_model[key]) - int(baseline_model[key])
    return {"workflows": workflow_deltas, "model_governance": model_delta}


def _legacy_benchmark_from_report(report: dict[str, Any]) -> dict[str, Any]:
    """Build comparable benchmark rows from older audit JSON without ``benchmark``."""
    files_by_path = {row.get("path"): row for row in report.get("files", [])}
    refs_by_path = {row.get("path"): row for row in report.get("reference_matrix", [])}
    dispatch_by_path = {row.get("path"): row for row in report.get("dispatch_burden", [])}
    models_by_path = {
        row.get("path"): row
        for row in report.get("model_inventory", {}).get("declarations", [])
    }
    context_rows = report.get("context_loading_risks", [])
    workflows: list[dict[str, Any]] = []
    for workflow, path in BENCHMARK_PROMPTS.items():
        file_row = files_by_path.get(path, {})
        ref_row = refs_by_path.get(path, {})
        dispatch_row = dispatch_by_path.get(path, {})
        context_counts = _count_context_levels(context_rows, path)
        workflows.append(
            {
                "workflow": workflow,
                "path": path,
                "estimated_tokens": file_row.get("estimated_tokens"),
                "total_refs": ref_row.get("total_refs"),
                "context_risk_count": context_counts["risk"],
                "dispatch_refs": dispatch_row.get("dispatch_refs"),
                "dispatch_burden": dispatch_row.get("burden_level"),
                "model_tier": models_by_path.get(path, {}).get("model_tier"),
            }
        )
    brain_path = ".github/skills/cg-skill-brain-query/SKILL.md"
    brain_file = files_by_path.get(brain_path, {})
    brain_counts = _count_context_levels([
        row for row in context_rows
        if "BRAIN" in str(row.get("artifact", "")) or "brain-index.json" in str(row.get("snippet", ""))
    ])
    workflows.append(
        {
            "workflow": "Knowledge Brain/context lookup",
            "path": brain_path,
            "estimated_tokens": brain_file.get("estimated_tokens"),
            "total_refs": 0,
            "context_risk_count": brain_counts["risk"],
            "dispatch_refs": 0,
            "dispatch_burden": "none",
            "model_tier": None,
        }
    )
    inventory = report.get("model_inventory", {})
    return {
        "workflows": workflows,
        "model_governance": {
            "premium_usage_count": len(inventory.get("premium_usage", [])),
            "ordinary_model_picker_violations": len(inventory.get("ordinary_model_picker_violations", [])),
            "missing_model_count": len(inventory.get("missing", [])),
            "model_drift_count": len(inventory.get("drift", [])),
            "openai_first_violations": len(inventory.get("openai_first_violations", [])),
            "haiku_role_violations": len(inventory.get("haiku_role_violations", [])),
            "sonnet_role_violations": len(inventory.get("sonnet_role_violations", [])),
        },
    }


def _is_context_guardrail_failure(row: dict[str, Any]) -> bool:
    """Return whether a context-loading risk should fail Phase 6 guardrails."""
    if row.get("level") != "risk" or row.get("path") not in ORDINARY_CONTEXT_GUARDRAIL_PROMPTS:
        return False
    snippet = str(row.get("snippet", ""))
    snippet_lower = snippet.lower()
    if "reject any directive" in snippet_lower or "generate a 3-5 step lightweight inline plan" in snippet_lower:
        return False
    artifact = str(row.get("artifact", ""))
    return any(target.lower() in artifact.lower() or target.lower() in snippet.lower()
               for target in BROAD_CONTEXT_GUARDRAIL_ARTIFACTS)


def _text_contains_all(text: str, patterns: Sequence[str]) -> bool:
    return all(re.search(pattern, text, re.IGNORECASE | re.DOTALL) for pattern in patterns)


def build_guardrails(root: Path, report: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    """Classify Phase 6 benchmark guardrail failures and warnings."""
    failures: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []

    def fail(path: str, reason: str) -> None:
        failures.append({"path": path, "reason": reason})

    def warn(path: str, reason: str) -> None:
        warnings.append({"path": path, "reason": reason})

    for violation in report.get("model_inventory", {}).get("ordinary_model_picker_violations", []):
        fail(violation["path"], "ordinary prompt hard-codes model instead of inheriting model picker")
    for premium in report.get("model_inventory", {}).get("premium_usage", []):
        fail(premium["path"], "premium model usage requires explicit future allowlist and rationale")
    for drift in report.get("model_inventory", {}).get("drift", []):
        fail(drift["path"], "model guide drift")
    inventory = report.get("model_inventory", {})
    if inventory.get("catalog", {}).get("load_error"):
        fail(MODEL_CATALOG_PATH, f"model catalog could not be parsed: {inventory['catalog']['load_error']}")
    for row in inventory.get("missing_catalog_assignments", []):
        fail(row["path"], "prompt/agent is missing a model-catalog role assignment")
    for row in inventory.get("invalid_catalog_roles", []):
        fail(row["path"], f"invalid model-catalog role: {row.get('role')}")
    for path in inventory.get("unused_catalog_assignments", []):
        fail(path, "model-catalog assignment has no matching prompt/agent file")
    for row in inventory.get("stale_model_names", []):
        fail(row["path"], f"frontmatter model is not in model catalog: {row.get('model')}")
    for row in inventory.get("openai_first_violations", []):
        fail(row["path"], f"{row.get('role')} workflow is not OpenAI-first: {row.get('model')}")
    for row in inventory.get("haiku_role_violations", []):
        fail(row["path"], "Haiku is allowed only for mechanical workflows")
    for row in inventory.get("sonnet_role_violations", []):
        fail(row["path"], "Sonnet requires fallback or cross-vendor rationale and must not be a blanket default")
    for row in inventory.get("frontmatter_support_gaps", []):
        warn(row["path"], f"preferred model frontmatter support is {row.get('preferred_model_support')}: {row.get('preferred_model')}")

    for row in report.get("files", []):
        path = row["path"]
        tokens = int(row["estimated_tokens"])
        if path in HIGH_FREQUENCY_PROMPTS:
            if tokens > THRESHOLD_HIGH_FREQ_PROMPT_FAIL:
                fail(path, f"high-frequency prompt estimated tokens > {THRESHOLD_HIGH_FREQ_PROMPT_FAIL}")
            elif tokens > THRESHOLD_HIGH_FREQ_PROMPT_WARN:
                warn(path, f"high-frequency prompt estimated tokens > {THRESHOLD_HIGH_FREQ_PROMPT_WARN}")
    always_on_tokens = sum(
        int(row["estimated_tokens"])
        for row in report.get("files", [])
        if row["category"] == "instructions" or row["path"] == ".github/copilot-instructions.md"
    )
    if always_on_tokens > THRESHOLD_ALWAYS_ON_FAIL:
        fail("(always-on instructions)", f"always-on instruction estimated tokens > {THRESHOLD_ALWAYS_ON_FAIL}")
    elif always_on_tokens > THRESHOLD_ALWAYS_ON_WARN:
        warn("(always-on instructions)", f"always-on instruction estimated tokens > {THRESHOLD_ALWAYS_ON_WARN}")

    for row in report.get("context_loading_risks", []):
        if _is_context_guardrail_failure(row):
            fail(row["path"], f"broad context-loading risk for {row['artifact']}: {row['snippet']}")
        elif row.get("level") == "risk":
            warn(row["path"], f"context-loading risk requires review: {row['artifact']}")

    review_path = root / ".github" / "prompts" / "cg-review.prompt.md"
    review_text = review_path.read_text(encoding="utf-8-sig") if review_path.exists() else ""
    if not _text_contains_all(
        review_text,
        [
            r"explicit user mode wins",
            r"Auto risk-class routing applies only.*no explicit mode",
            r"(Users can explicitly request `?full`?|explicit.*full)",
            r"(thorough.*full|full.*thorough)",
            r"(mode:verify.*light-only|verify mode.*light-only)",
        ],
    ):
        fail(".github/prompts/cg-review.prompt.md", "/cg-review route precedence or explicit full/verify guard drifted")

    work_path = root / ".github" / "prompts" / "cg-work.prompt.md"
    work_text = work_path.read_text(encoding="utf-8-sig") if work_path.exists() else ""
    if not _text_contains_all(
        work_text,
        [
            r"review:auto",
            r"review:manual",
            r"review:none",
            r"(default.*review:manual.*no agent dispatch|No review arg defaults to `review:manual`.*no agent dispatch)",
            r"review:auto.*route-aware",
        ],
    ):
        fail(".github/prompts/cg-work.prompt.md", "/cg-work review:auto/manual/none behavior drifted")

    brain_path = root / ".github" / "skills" / "cg-skill-brain-query" / "SKILL.md"
    brain_text = brain_path.read_text(encoding="utf-8-sig") if brain_path.exists() else ""
    if not _text_contains_all(
        brain_text,
        [
            r"BRAIN\.md",
            r"(matched topic|Match Topics|query-first)",
            r"(must not read it wholesale|prompt agents must not read it wholesale)",
        ],
    ):
        fail(".github/skills/cg-skill-brain-query/SKILL.md", "Knowledge Brain query-first or no-wholesale-index rule drifted")

    counts = report.get("benchmark", {}).get("review_agent_counts", {}).get("counts", {})
    for mode, expected in EXPECTED_REVIEW_AGENT_COUNTS.items():
        actual = counts.get(mode)
        if actual != expected:
            fail(".github/shared/review-routing.contract.md", f"review route agent counts drifted for {mode}: expected {expected}, found {actual}")

    return {"failures": failures, "warnings": warnings}


def _matching_context_risk(warning: dict[str, Any], report: dict[str, Any]) -> dict[str, Any] | None:
    """Return the context-loading row behind a guardrail warning, if available."""
    reason = str(warning.get("reason", ""))
    marker = "context-loading risk requires review:"
    if marker not in reason:
        return None
    artifact = reason.split(marker, 1)[1].strip()
    for row in report.get("context_loading_risks", []):
        if row.get("path") == warning.get("path") and str(row.get("artifact")) == artifact:
            return row
    return None


def classify_guardrail_warning(warning: dict[str, Any], report: dict[str, Any] | None = None) -> dict[str, str]:
    """Classify one guardrail warning for closure triage.

    Classifications:
    - ``fix``: unnecessary broad or always-on context that should be reduced.
    - ``accept``: intentional maintenance, safety, or governance read.
    - ``docs-only``: wording in documentation, not runtime broad loading.
    """
    report = report or {}
    path = str(warning.get("path", ""))
    reason = str(warning.get("reason", ""))
    context_row = _matching_context_risk(warning, report)
    snippet = str((context_row or {}).get("snippet", ""))

    if path.startswith(DOCS_ONLY_WARNING_PREFIXES):
        return {
            "classification": "docs-only",
            "rationale": "Documentation wording can mention broad artifacts without causing runtime prompt loading.",
            "action": "Keep as documentation unless wording misleads users.",
        }
    if "high-frequency prompt estimated tokens" in reason:
        return {
            "classification": "fix",
            "rationale": "High-frequency entrypoints directly affect routine token cost.",
            "action": "Slim the prompt or split only with an explicit caller load point.",
        }
    if "preferred model frontmatter support" in reason:
        return {
            "classification": "accept",
            "rationale": "Governance warning documents an external support check, not context loading.",
            "action": "Keep until exact model frontmatter support is validated.",
        }
    snippet_lower = snippet.lower()
    if "reject any directive" in snippet_lower or "generate a 3-5 step lightweight inline plan" in snippet_lower:
        return {
            "classification": "accept",
            "rationale": "The flagged line is a safety or goal-execution guard, not a read directive.",
            "action": "Retain the guardrail wording.",
        }
    if path in ACCEPT_WARNING_PATHS:
        return {
            "classification": "accept",
            "rationale": "Maintenance, roadmap, setup, release, or research workflow intentionally inspects broad project state.",
            "action": "Keep the read and document the maintenance rationale.",
        }
    if path in FIX_WARNING_PATHS:
        return {
            "classification": "fix",
            "rationale": "Ordinary user-facing workflow should not require broad context by default.",
            "action": "Convert to staged, targeted, or on-demand loading.",
        }
    if path.startswith(".github/prompts/") and "context-loading risk requires review" in reason:
        return {
            "classification": "fix",
            "rationale": "Prompt-level broad context warning needs targeted wording unless proven maintenance-only.",
            "action": "Narrow the read or add an explicit accepted rationale.",
        }
    return {
        "classification": "accept",
        "rationale": "Reviewed warning has no ordinary always-on or broad-loading action attached.",
        "action": "Keep under review in future audits.",
    }


def build_reviewed_warnings(report: dict[str, Any]) -> dict[str, Any]:
    """Build reviewed fix/accept/docs-only guardrail warning rows."""
    items: list[dict[str, Any]] = []
    counts = {"fix": 0, "accept": 0, "docs-only": 0}
    for warning in report.get("guardrails", {}).get("warnings", []):
        review = classify_guardrail_warning(warning, report)
        classification = review["classification"]
        counts[classification] = counts.get(classification, 0) + 1
        context_row = _matching_context_risk(warning, report) or {}
        items.append({
            **warning,
            **review,
            "line": context_row.get("line"),
            "artifact": context_row.get("artifact"),
            "snippet": context_row.get("snippet"),
        })
    return {"counts": counts, "items": items}


def build_token_efficiency_recommendations(report: dict[str, Any]) -> list[dict[str, Any]]:
    """Return user-facing token-use recommendations grounded in audit evidence."""
    recommendations: list[dict[str, Any]] = []

    def add(priority: str, category: str, title: str, evidence: str, advice: str) -> None:
        recommendations.append({
            "priority": priority,
            "category": category,
            "title": title,
            "evidence": evidence,
            "advice": advice,
        })

    guardrails = report.get("guardrails", {})
    if guardrails.get("failures"):
        add(
            "high",
            "guardrails",
            "Fix audit failures before optimizing cost.",
            f"{len(guardrails['failures'])} guardrail failure(s) are present.",
            "Resolve failures first; they are stronger than advisory token recommendations.",
        )

    reviewed = report.get("reviewed_warnings", {})
    fix_count = reviewed.get("counts", {}).get("fix", 0)
    if fix_count:
        fix_paths = ", ".join(sorted({row["path"] for row in reviewed.get("items", []) if row["classification"] == "fix"})[:6])
        add(
            "high",
            "context-loading",
            "Reduce prompt warnings classified as fix.",
            f"{fix_count} warning(s) classified as fix: {fix_paths}.",
            "Slim the named entrypoints or convert broad reads to staged, targeted, on-demand loading.",
        )

    workflow_rows = report.get("benchmark", {}).get("workflows", [])
    expensive_workflows = [
        row for row in workflow_rows
        if row.get("estimated_tokens") is not None and int(row["estimated_tokens"]) > THRESHOLD_HIGH_FREQ_PROMPT_WARN
    ]
    for row in expensive_workflows:
        add(
            "high",
            "entrypoint-size",
            f"Slim {row['workflow']}.",
            f"{row['path']} is estimated at {row['estimated_tokens']} tokens.",
            "Keep safety-critical routing inline, but move rarely used workflow detail behind explicit skills or targeted contracts.",
        )

    by_category = report.get("summary", {}).get("by_category", {})
    context_tokens = int(by_category.get("context", {}).get("estimated_tokens", 0))
    brain_tokens = int(by_category.get("brain", {}).get("estimated_tokens", 0))
    brain_index_tokens = int(by_category.get("brain_index", {}).get("estimated_tokens", 0))
    if context_tokens or brain_tokens or brain_index_tokens:
        add(
            "medium",
            "project-context",
            "Use query-first project context.",
            f"context={context_tokens}, brain={brain_tokens}, brain_index={brain_index_tokens} estimated tokens.",
            "Use the Brain meta-index and targeted sections; avoid loading full context, Brain partitions, or brain-index records by default.",
        )

    docs_tokens = int(by_category.get("docs", {}).get("estimated_tokens", 0))
    if docs_tokens:
        add(
            "low",
            "documentation",
            "Treat docs size as opt-in cost.",
            f"docs category is estimated at {docs_tokens} tokens.",
            "Do not optimize docs for runtime unless prompts or skills load them automatically.",
        )

    review_rows = [row for row in workflow_rows if row.get("workflow") == "/cg-review"]
    if review_rows:
        review = review_rows[0]
        add(
            "medium",
            "review-routing",
            "Match review depth to risk.",
            f"/cg-review dispatch burden is {review.get('dispatch_burden')} with {review.get('dispatch_refs')} referenced agents.",
            "Use light or standard reviews for low-risk changes; reserve full review for broad, risky, or explicitly requested checks.",
        )

    add(
        "low",
        "model-selection",
        "Use cheaper models for planning and advisory work when quality allows.",
        "Model governance keeps ordinary planning prompts on the model picker.",
        "Use stronger models for implementation, high-risk review, and architecture; use lighter models for simple planning or documentation passes.",
    )
    return recommendations


def _deterministic_generated_stamp(root: Path) -> str:
    """Return a deterministic generated stamp when git metadata is available."""
    git_dir = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "--git-dir"],
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    if git_dir.returncode != 0:
        return datetime.now().isoformat(timespec="seconds")

    head_sha = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    head_time = subprocess.run(
        ["git", "-C", str(root), "show", "-s", "--format=%cI", "HEAD"],
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    if head_sha.returncode == 0 and head_time.returncode == 0:
        sha = head_sha.stdout.strip()
        commit_time = head_time.stdout.strip()
        if sha and commit_time:
            return f"{commit_time}@{sha[:12]}"

    return datetime.now().isoformat(timespec="seconds")


def build_report(root: Path) -> dict[str, Any]:
    """Build the complete audit report for a Compound GPID project root.

    Args:
        root: Resolved path to the repository root (must contain ``.github/prompts/``).

    Returns:
        Nested dict with keys: ``generated``, ``disclaimer``, ``summary``, ``files``,
        ``reference_matrix``, ``dispatch_burden``, ``model_inventory``,
        ``duplicates``, ``optimization_candidates``.
    """
    files, by_category = scan_files(root)
    reference_matrix = build_reference_matrix(root, files)
    dispatch_burden = build_dispatch_burden(root, files)
    model_inventory = build_model_inventory(root, files)
    duplicates = detect_duplicates(root, files)
    context_loading_risks = build_context_loading_risks(root, files)
    candidates = classify_optimization_candidates(files, reference_matrix, model_inventory, duplicates)
    total_characters = 0
    total_estimated_tokens = 0
    for file_record in files:
        total_characters += int(file_record["characters"])
        total_estimated_tokens += int(file_record["estimated_tokens"])
    generated_timestamp = _deterministic_generated_stamp(root)
    report: dict[str, Any] = {
        "generated": generated_timestamp,
        "generated_kind": "volatile",
        "disclaimer": DISCLAIMER,
        "summary": {
            "total_files": len(files),
            "total_characters": total_characters,
            "total_estimated_tokens": total_estimated_tokens,
            "by_category": by_category,
        },
        "files": sorted(files, key=lambda row: row["path"]),
        "reference_matrix": reference_matrix,
        "dispatch_burden": dispatch_burden,
        "model_inventory": model_inventory,
        "context_loading_risks": context_loading_risks,
        "duplicates": duplicates,
        "optimization_candidates": candidates,
    }
    report["workflow_telemetry"] = build_workflow_telemetry(root, report)
    report["benchmark"] = build_benchmark_summary(root, report)
    report["guardrails"] = build_guardrails(root, report)
    report["reviewed_warnings"] = build_reviewed_warnings(report)
    report["recommendations"] = build_token_efficiency_recommendations(report)
    return report


def markdown_table(headers: Sequence[str], rows: Sequence[Sequence[Any]]) -> list[str]:
    """Render a Markdown table from headers and row data.

    Args:
        headers: Column header strings.
        rows: Sequence of row sequences; each cell is stringified via ``str()``.

    Returns:
        List of Markdown table lines (header, separator, data rows).

    Example::

        markdown_table(["A", "B"], [[1, 2], [3, 4]])
        # ["| A | B |", "| --- | --- |", "| 1 | 2 |", "| 3 | 4 |"]
    """
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(cell) for cell in row) + " |")
    return lines


def render_markdown(report: dict[str, Any]) -> str:
    """Render the audit report as a Markdown string.

    Args:
        report: Output of :func:`build_report`.

    Returns:
        Full Markdown document as a single string.
    """
    lines = [
        "# Context and Model-Governance Audit",
        "",
        f"_Generated: {report['generated']}_",
        "",
        f"> {report['disclaimer']}",
        "",
        "## Summary",
        "",
        f"- Total files: {report['summary']['total_files']}",
        f"- Total characters: {report['summary']['total_characters']}",
        f"- Total estimated tokens: {report['summary']['total_estimated_tokens']}",
        "",
    ]
    category_rows = [
        [cat, totals["files"], totals["characters"], totals["estimated_tokens"]]
        for cat, totals in report["summary"]["by_category"].items()
    ]
    lines.extend(markdown_table(["Category", "Files", "Characters", "Estimated Tokens"], category_rows))
    lines.extend(["", "## Top 15 Largest Files", ""])
    largest = sorted(report["files"], key=lambda row: -row["estimated_tokens"])[:15]
    lines.extend(markdown_table(["Path", "Category", "Characters", "Estimated Tokens"], [
        [r["path"], r["category"], r["characters"], r["estimated_tokens"]] for r in largest
    ]))
    lines.extend(["", "## Benchmark Summary", ""])
    benchmark = report.get("benchmark", {})
    workflow_rows = benchmark.get("workflows", [])
    if workflow_rows:
        lines.extend(markdown_table(
            [
                "Workflow",
                "Path",
                "Tokens",
                "Refs",
                "Model Tier",
                "Context Risk",
                "Dispatch",
                "Conditional",
            ],
            [
                [
                    row["workflow"],
                    row["path"],
                    row.get("estimated_tokens"),
                    row.get("total_refs"),
                    row.get("model_tier") or "",
                    row.get("context_risk_count"),
                    row.get("dispatch_burden"),
                    row.get("conditional_routing"),
                ]
                for row in workflow_rows
            ],
        ))
    else:
        lines.append("- No benchmark rows available")
    model_governance = benchmark.get("model_governance", {})
    context_loading = benchmark.get("context_loading", {})
    lines.extend([
        "",
        f"- Premium model usage count: {model_governance.get('premium_usage_count', 0)}",
        f"- Ordinary model-picker violations: {model_governance.get('ordinary_model_picker_violations', 0)}",
        f"- Missing model declarations: {model_governance.get('missing_model_count', 0)}",
        f"- Model drift count: {model_governance.get('model_drift_count', 0)}",
        f"- OpenAI-first violations: {model_governance.get('openai_first_violations', 0)}",
        f"- Haiku role violations: {model_governance.get('haiku_role_violations', 0)}",
        f"- Sonnet role violations: {model_governance.get('sonnet_role_violations', 0)}",
        f"- Context loading signals: risk={context_loading.get('risk', 0)}, justified={context_loading.get('justified', 0)}, targeted={context_loading.get('targeted', 0)}",
    ])
    review_counts = benchmark.get("review_agent_counts", {}).get("counts", {})
    if review_counts:
        lines.extend(["", "### Review-Agent Counts", ""])
        lines.extend(markdown_table(["Mode", "Static Agent Count", "Expected"], [
            [mode, review_counts.get(mode), EXPECTED_REVIEW_AGENT_COUNTS[mode]]
            for mode in EXPECTED_REVIEW_AGENT_COUNTS
        ]))
    comparison = benchmark.get("comparison")
    lines.extend(["", "### Before/After Comparison", ""])
    if comparison and comparison.get("workflows"):
        lines.extend(markdown_table(
            ["Workflow", "Token Delta", "Ref Delta", "Context Risk Delta", "Dispatch Delta", "Burden Before", "Burden After"],
            [
                [
                    row["workflow"],
                    row.get("estimated_tokens_delta"),
                    row.get("total_refs_delta"),
                    row.get("context_risk_count_delta"),
                    row.get("dispatch_refs_delta"),
                    row.get("dispatch_burden_before"),
                    row.get("dispatch_burden_after"),
                ]
                for row in comparison["workflows"]
            ],
        ))
        model_delta = comparison.get("model_governance", {})
        lines.extend([
            "",
            f"- Premium usage delta: {model_delta.get('premium_usage_count_delta', 0)}",
            f"- Ordinary model-picker violation delta: {model_delta.get('ordinary_model_picker_violations_delta', 0)}",
            f"- Missing model delta: {model_delta.get('missing_model_count_delta', 0)}",
            f"- Model drift delta: {model_delta.get('model_drift_count_delta', 0)}",
        ])
    else:
        lines.append("- No baseline supplied; current audit is the baseline.")
    lines.extend(["", "## Guardrails", ""])
    guardrails = report.get("guardrails", {"failures": [], "warnings": []})
    failures = guardrails.get("failures", [])
    warnings = guardrails.get("warnings", [])
    lines.extend([f"- **FAIL** {row['path']}: {row['reason']}" for row in failures] or ["- Failures: 0"])
    lines.extend([f"- **WARN** {row['path']}: {row['reason']}" for row in warnings] or ["- Warnings: 0"])
    lines.extend(["", "## Reviewed Warning Classifications", ""])
    reviewed_warnings = report.get("reviewed_warnings", {})
    reviewed_items = reviewed_warnings.get("items", [])
    reviewed_counts = reviewed_warnings.get("counts", {})
    lines.extend([
        f"- Fix: {reviewed_counts.get('fix', 0)}",
        f"- Accept: {reviewed_counts.get('accept', 0)}",
        f"- Docs-only: {reviewed_counts.get('docs-only', 0)}",
        "",
    ])
    if reviewed_items:
        lines.extend(markdown_table(["Classification", "Path", "Artifact", "Reason", "Rationale", "Action"], [
            [
                row["classification"],
                row["path"],
                row.get("artifact") or "",
                row["reason"],
                row["rationale"].replace("|", "\\|"),
                row["action"].replace("|", "\\|"),
            ]
            for row in reviewed_items
        ]))
    else:
        lines.append("- No warnings to classify.")
    lines.extend(["", "## Token Efficiency Recommendations", ""])
    recommendations = report.get("recommendations", [])
    if recommendations:
        lines.extend(markdown_table(["Priority", "Category", "Recommendation", "Evidence", "Advice"], [
            [
                row["priority"],
                row["category"],
                row["title"].replace("|", "\\|"),
                row["evidence"].replace("|", "\\|"),
                row["advice"].replace("|", "\\|"),
            ]
            for row in recommendations
        ]))
    else:
        lines.append("- None")
    lines.extend(["", "## Release-Readiness Checklist", ""])
    lines.extend([f"- [ ] {item}" for item in RELEASE_READINESS_CHECKLIST])
    lines.extend(["", "## Prompt Reference Matrix", ""])
    lines.extend(markdown_table(["Path", "File", "Agent", "Skill", "Tool", "Load", "Total"], [
        [r["path"], r["file_refs"], r["agent_refs"], r["skill_refs"], r["tool_refs"], r["load_verbs"], r["total_refs"]]
        for r in report["reference_matrix"]
    ]))
    lines.extend(["", "## Review Dispatch Burden", ""])
    lines.extend(markdown_table(["Path", "Dispatch Refs", "Conditional Routing", "Broad Dispatch", "Burden"], [
        [r["path"], r["dispatch_refs"], r["conditional_routing"], r["broad_dispatch"], r["burden_level"]]
        for r in report.get("dispatch_burden", [])
    ]))
    lines.extend(["", "## Context Loading Risks", ""])
    context_rows = report.get("context_loading_risks", [])
    if context_rows:
        lines.extend(markdown_table(["Level", "Path", "Line", "Artifact", "Reason", "Snippet"], [
            [
                r["level"],
                r["path"],
                r["line"],
                r["artifact"],
                r["reason"],
                r["snippet"].replace("|", "\\|"),
            ]
            for r in context_rows[:80]
        ]))
        risk_count = sum(1 for r in context_rows if r["level"] == "risk")
        justified_count = sum(1 for r in context_rows if r["level"] == "justified")
        targeted_count = sum(1 for r in context_rows if r["level"] == "targeted")
        lines.extend([
            "",
            f"- Risk signals: {risk_count}",
            f"- Justified full/maintenance signals: {justified_count}",
            f"- Targeted/guarded signals: {targeted_count}",
        ])
    else:
        lines.append("- None")
    lines.extend(["", "## Model Inventory", ""])
    catalog_info = report["model_inventory"].get("catalog", {})
    lines.extend([
        f"- Catalog: `{catalog_info.get('path', MODEL_CATALOG_PATH)}`",
        f"- Catalog assignments: {catalog_info.get('assignment_count', 0)}",
    ])
    if catalog_info.get("load_error"):
        lines.append(f"- Catalog load error: {catalog_info['load_error']}")
    lines.extend([""])
    lines.extend(markdown_table(["Path", "Category", "Model", "Vendor", "Family", "Role", "Tier", "Preferred", "Support"], [
        [
            d["path"],
            d["category"],
            d["model"] or "(model picker)",
            d.get("vendor", ""),
            d.get("family", ""),
            d.get("role", ""),
            d["model_tier"],
            d.get("preferred_model") or "",
            d.get("frontmatter_support") or "",
        ]
        for d in report["model_inventory"]["declarations"]
    ]))
    lines.extend(["", "## Model Policy Violations", ""])
    policy_sections = [
        ("Missing catalog assignments", "missing_catalog_assignments", "role assignment missing"),
        ("Invalid catalog roles", "invalid_catalog_roles", "invalid role"),
        ("Stale model names", "stale_model_names", "model not in catalog"),
        ("OpenAI-first violations", "openai_first_violations", "not OpenAI-first"),
        ("Haiku role violations", "haiku_role_violations", "Haiku outside mechanical role"),
        ("Sonnet role violations", "sonnet_role_violations", "Sonnet lacks fallback/cross-vendor role"),
        ("Preferred model support gaps", "frontmatter_support_gaps", "frontmatter support not confirmed"),
    ]
    for title, key, reason in policy_sections:
        rows = report["model_inventory"].get(key, [])
        lines.append(f"### {title}")
        if rows:
            lines.extend([
                f"- {d['path']}: {d.get('model') or '(model picker)'}; role={d.get('role')}; preferred={d.get('preferred_model')}; support={d.get('preferred_model_support', d.get('frontmatter_support'))}; {reason}"
                for d in rows
            ])
        else:
            lines.append("- None")
        lines.append("")
    lines.extend(["", "## Missing Model Declarations", ""])
    missing = report["model_inventory"]["missing"]
    lines.extend([f"- {d['path']}" for d in missing] or ["- None"])
    lines.extend(["", "## Model Drift", ""])
    drift = report["model_inventory"]["drift"]
    lines.extend([f"- {d['path']}: frontmatter `{d['frontmatter_model']}` vs model-guide `{d['model_guide_model']}`"
                  for d in drift] or ["- None"])
    lines.extend(["", "## Premium Model Usage", ""])
    premium = report["model_inventory"]["premium_usage"]
    lines.extend([f"- {d['path']}: {d['model']} (escalation condition: {d['has_escalation_condition']})"
                  for d in premium] or ["- None"])
    lines.extend(["", "## Ordinary Prompt Model-Picker Violations", ""])
    ordinary_violations = report["model_inventory"].get("ordinary_model_picker_violations", [])
    lines.extend([f"- {d['path']}: frontmatter model `{d['model']}`"
                  for d in ordinary_violations] or ["- None"])
    lines.extend(["", "## Duplicate Paragraphs", ""])
    lines.extend(markdown_table(["Preview", "Files", "Estimated Tokens"], [
        [d["block_preview"].replace("|", "\\|"), d["file_count"], d["total_redundant_tokens"]]
        for d in report["duplicates"]
    ]) if report["duplicates"] else ["- None"])
    lines.extend(["", "## Immediate Optimization Candidates", ""])
    lines.extend([f"- {c['path']} ({c['category']}): {c['reason']}"
                  for c in report["optimization_candidates"]["immediate"]] or ["- None"])
    lines.extend(["", "## Needs Review", ""])
    lines.extend([f"- {c['path']} ({c['category']}): {c['reason']}"
                  for c in report["optimization_candidates"]["needs_review"]] or ["- None"])
    lines.append("")
    return "\n".join(lines)


def render_recommendations_markdown(report: dict[str, Any]) -> str:
    """Render a compact user-facing token advice report."""
    lines = [
        "# Token Efficiency Advice",
        "",
        f"_Generated: {report['generated']}_",
        "",
        f"> {report['disclaimer']}",
        "",
    ]
    guardrails = report.get("guardrails", {})
    reviewed = report.get("reviewed_warnings", {})
    counts = reviewed.get("counts", {})
    lines.extend([
        "## Current Audit",
        "",
        f"- Guardrail failures: {len(guardrails.get('failures', []))}",
        f"- Guardrail warnings: {len(guardrails.get('warnings', []))}",
        f"- Warning classification: fix={counts.get('fix', 0)}, accept={counts.get('accept', 0)}, docs-only={counts.get('docs-only', 0)}",
        "",
        "## Recommended Actions",
        "",
    ])
    recommendations = report.get("recommendations", [])
    if recommendations:
        lines.extend([
            f"- **{row['priority']} / {row['category']}**: {row['title']} "
            f"Evidence: {row['evidence']} Advice: {row['advice']}"
            for row in recommendations
        ])
    else:
        lines.append("- No token-efficiency recommendations.")
    warning_items = reviewed.get("items", [])
    lines.extend(["", "## Warning Review", ""])
    if warning_items:
        lines.extend([
            f"- **{row['classification']}** `{row['path']}`: {row['rationale']} Action: {row['action']}"
            for row in warning_items
        ])
    else:
        lines.append("- No warnings.")
    lines.append("")
    return "\n".join(lines)


def build_token_audit_artifact(report: dict[str, Any]) -> dict[str, Any]:
    """Return the canonical workflow-token baseline payload."""
    return {
        "schema_version": 1,
        "generated": report.get("generated"),
        "generated_kind": report.get("generated_kind", "volatile"),
        "disclaimer": report.get("disclaimer", DISCLAIMER),
        "summary": report.get("summary", {}),
        "workflow_telemetry": report.get("workflow_telemetry", {}),
        "benchmark": report.get("benchmark", {}),
        "guardrails": report.get("guardrails", {}),
        "reviewed_warnings": report.get("reviewed_warnings", {}),
        "optimization_candidates": report.get("optimization_candidates", {}),
        "measurement_policy": {
            "token_estimate": "chars/4 heuristic",
            "savings_claims": "hypotheses until measured with comparable repository probes",
            "runtime_fields": "not inferred when not deterministically observed",
        },
    }


def build_context_map_artifact(report: dict[str, Any]) -> dict[str, Any]:
    """Return workflow-to-context reference mapping for token artifacts."""
    context_rows_by_path: dict[str, list[dict[str, Any]]] = {}
    for row in report.get("context_loading_risks", []):
        context_rows_by_path.setdefault(row.get("path", ""), []).append({
            "line": row.get("line"),
            "level": row.get("level"),
            "artifact": row.get("artifact"),
            "reason": row.get("reason"),
            "snippet": row.get("snippet"),
        })

    workflows = []
    for row in report.get("workflow_telemetry", {}).get("workflows", []):
        path = row.get("path", "")
        workflows.append({
            "workflow_id": row.get("workflow_id"),
            "workflow": row.get("workflow"),
            "path": path,
            "available": row.get("available"),
            "file_references": row.get("file_references", []),
            "likely_file_reads": row.get("likely_file_reads", []),
            "skill_references": row.get("skill_references", []),
            "likely_skill_loads": row.get("likely_skill_loads", []),
            "agent_references": row.get("agent_references", []),
            "tool_references": row.get("tool_references", []),
            "context_loading_signals": context_rows_by_path.get(path, []),
            "observability": row.get("observability", {}),
        })

    return {
        "schema_version": 1,
        "generated": report.get("generated"),
        "generated_kind": report.get("generated_kind", "volatile"),
        "measurement_note": report.get("workflow_telemetry", {}).get("measurement_note"),
        "workflows": workflows,
    }


def _workflow_budget_status(row: dict[str, Any]) -> dict[str, Any]:
    """Return deterministic budget status for one workflow row."""
    tokens = row.get("estimated_tokens")
    status = "unknown" if tokens is None else "pass"
    threshold_warning = None
    threshold_failure = None
    if row.get("path") in HIGH_FREQUENCY_PROMPTS and tokens is not None:
        token_count = int(tokens)
        threshold_warning = THRESHOLD_HIGH_FREQ_PROMPT_WARN
        threshold_failure = THRESHOLD_HIGH_FREQ_PROMPT_FAIL
        if token_count > THRESHOLD_HIGH_FREQ_PROMPT_FAIL:
            status = "fail"
        elif token_count > THRESHOLD_HIGH_FREQ_PROMPT_WARN:
            status = "warn"
    return {
        "workflow": row.get("workflow"),
        "path": row.get("path"),
        "estimated_tokens": tokens,
        "status": status,
        "threshold_warning": threshold_warning,
        "threshold_failure": threshold_failure,
    }


def build_token_regression_check(report: dict[str, Any]) -> dict[str, Any]:
    """Build a compact machine-readable token regression summary."""
    guardrails = report.get("guardrails", {})
    failures = guardrails.get("failures", [])
    warnings = guardrails.get("warnings", [])
    benchmark = report.get("benchmark", {})
    comparison = benchmark.get("comparison")
    workflow_budget = [
        _workflow_budget_status(row)
        for row in benchmark.get("workflows", [])
    ]

    if failures:
        status = "fail"
    elif comparison and comparison.get("workflows"):
        status = "pass"
    else:
        status = "baseline"

    return {
        "schema_version": 1,
        "generated": report.get("generated"),
        "generated_kind": report.get("generated_kind", "volatile"),
        "status": status,
        "status_reason": {
            "fail": "Deterministic guardrail failures are present.",
            "pass": "No deterministic guardrail failures were found for a comparable baseline run.",
            "baseline": "No baseline comparison was supplied; current audit is the baseline.",
        }[status],
        "failures": failures,
        "warnings": warnings,
        "workflow_budget": workflow_budget,
        "comparison": {
            "status": "available" if comparison and comparison.get("workflows") else "not_supplied",
            "workflows": (comparison or {}).get("workflows", []),
            "model_governance": (comparison or {}).get("model_governance", {}),
        },
        "measurement_policy": {
            "token_estimate": "chars/4 heuristic",
            "savings_claims": "not made without comparable repository probes",
            "failure_rule": "guardrail failures fail the regression check; advisory warnings remain warnings",
        },
    }


def render_workflow_costs_csv(report: dict[str, Any]) -> str:
    """Render workflow telemetry as stable CSV."""
    output = io.StringIO()
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow([
        "workflow_id",
        "workflow",
        "path",
        "available",
        "estimated_tokens",
        "total_refs",
        "file_refs",
        "skill_refs",
        "agent_refs",
        "tool_refs",
        "load_verbs",
        "context_risk_count",
        "context_justified_count",
        "context_targeted_count",
        "dispatch_refs",
        "dispatch_burden",
        "command_output_status",
        "summary_output_status",
    ])
    for row in report.get("workflow_telemetry", {}).get("workflows", []):
        observability = row.get("observability", {})
        writer.writerow([
            row.get("workflow_id"),
            row.get("workflow"),
            row.get("path"),
            row.get("available"),
            row.get("estimated_tokens"),
            row.get("total_refs"),
            row.get("file_refs"),
            row.get("skill_refs"),
            row.get("agent_refs"),
            row.get("tool_refs"),
            row.get("load_verbs"),
            row.get("context_risk_count"),
            row.get("context_justified_count"),
            row.get("context_targeted_count"),
            row.get("dispatch_refs"),
            row.get("dispatch_burden"),
            observability.get("command_output_size", {}).get("status"),
            observability.get("summary_size", {}).get("status"),
        ])
    return output.getvalue()


def render_token_dashboard_markdown(report: dict[str, Any]) -> str:
    """Render a compact token dashboard for maintainers."""
    regression = build_token_regression_check(report)
    telemetry = report.get("workflow_telemetry", {})
    workflows = telemetry.get("workflows", [])
    guardrails = report.get("guardrails", {})
    reviewed = report.get("reviewed_warnings", {}).get("counts", {})
    context_loading = report.get("benchmark", {}).get("context_loading", {})
    top_workflows = sorted(
        workflows,
        key=lambda row: int(row.get("estimated_tokens") or 0),
        reverse=True,
    )[:5]
    lines = [
        "# Token Dashboard",
        "",
        f"_Generated: {report.get('generated')}_",
        "",
        f"> {report.get('disclaimer', DISCLAIMER)}",
        "",
        "This dashboard is an observability artifact, not evidence of token",
        "savings. Treat savings claims as hypotheses until measured with",
        "comparable repository probes.",
        "",
        "## Regression Status",
        "",
        f"- Status: `{regression['status']}`",
        f"- Reason: {regression['status_reason']}",
        f"- Guardrail failures: {len(guardrails.get('failures', []))}",
        f"- Guardrail warnings: {len(guardrails.get('warnings', []))}",
        f"- Baseline comparison: {regression['comparison']['status']}",
        "",
        "## Source Scope",
        "",
        f"- Source files counted: {report.get('summary', {}).get('total_files', 0)}",
        f"- Source estimated tokens: {report.get('summary', {}).get('total_estimated_tokens', 0)}",
        f"- Workflow rows: {len(workflows)}",
        "",
        "## Highest Workflow Budgets",
        "",
    ]
    lines.extend(markdown_table(
        ["Workflow", "Path", "Tokens", "Refs", "Context Risk", "Budget Status"],
        [
            [
                row.get("workflow"),
                row.get("path"),
                row.get("estimated_tokens"),
                row.get("total_refs"),
                row.get("context_risk_count"),
                _workflow_budget_status(row).get("status"),
            ]
            for row in top_workflows
        ],
    ) if top_workflows else ["- No workflow rows available."])
    lines.extend([
        "",
        "## Context and Warning Summary",
        "",
        f"- Context loading signals: risk={context_loading.get('risk', 0)}, justified={context_loading.get('justified', 0)}, targeted={context_loading.get('targeted', 0)}",
        f"- Reviewed warnings: fix={reviewed.get('fix', 0)}, accept={reviewed.get('accept', 0)}, docs-only={reviewed.get('docs-only', 0)}",
        "",
        "## Observability Boundaries",
        "",
        "- `baseline`: no comparable baseline was supplied.",
        "- `pass`: comparable baseline supplied and no deterministic guardrail failures were found.",
        "- `fail`: deterministic guardrail failures are present.",
        "- Runtime command-output size and summary size remain explicit observed/not_observed fields.",
        "",
    ])
    return "\n".join(lines)


def render_token_budget_markdown(report: dict[str, Any]) -> str:
    """Render a human-readable workflow token budget baseline."""
    telemetry = report.get("workflow_telemetry", {})
    workflows = telemetry.get("workflows", [])
    measured = sum(1 for row in workflows if row.get("available"))
    missing = len(workflows) - measured
    lines = [
        "# Workflow Token Budget Baseline",
        "",
        f"_Generated: {report.get('generated')}_",
        "",
        f"> {report.get('disclaimer', DISCLAIMER)}",
        "",
        "This is a baseline artifact, not evidence of token savings. Treat any",
        "token-saving claim as a hypothesis until measured with comparable",
        "repository probes.",
        "",
        "## Source Scope",
        "",
        f"- Source files counted: {report.get('summary', {}).get('total_files', 0)}",
        f"- Source estimated tokens: {report.get('summary', {}).get('total_estimated_tokens', 0)}",
        f"- Workflow rows: {len(workflows)}",
        f"- Workflows with prompt source observed: {measured}",
        f"- Workflows without prompt source observed: {missing}",
        "",
        "Generated `.cg-docs/cost/` and `.cg-docs/token/` outputs are audit",
        "artifacts. They are not part of the normal workflow source-pressure scan.",
        "",
        "## Workflow Budgets",
        "",
    ]
    lines.extend(markdown_table(
        [
            "Workflow",
            "Path",
            "Tokens",
            "Refs",
            "Context Risk",
            "Dispatch",
            "Command Output",
            "Summary",
        ],
        [
            [
                row.get("workflow"),
                row.get("path"),
                row.get("estimated_tokens"),
                row.get("total_refs"),
                row.get("context_risk_count"),
                row.get("dispatch_burden"),
                row.get("observability", {}).get("command_output_size", {}).get("status"),
                row.get("observability", {}).get("summary_size", {}).get("status"),
            ]
            for row in workflows
        ],
    ))
    lines.extend([
        "",
        "## Observability Boundaries",
        "",
        "- `observed`: measured from repository source files.",
        "- `partially_observed`: statically visible in prompt text, but actual",
        "  runtime behavior depends on the execution path.",
        "- `not_observed`: not instrumented in Phase 1.1 and not inferred.",
        "",
        "Command-output size and summary size are intentionally `not_observed`",
        "until command-output summary wrappers or transcript instrumentation exist.",
        "",
    ])
    return "\n".join(lines)


def render_large_context_warnings_markdown(report: dict[str, Any]) -> str:
    """Render large context warning candidates without copying large bodies."""
    candidates = report.get("optimization_candidates", {})
    immediate = candidates.get("immediate", [])
    needs_review = candidates.get("needs_review", [])
    duplicates = report.get("duplicates", [])
    lines = [
        "# Large Context Warnings",
        "",
        f"_Generated: {report.get('generated')}_",
        "",
        f"> {report.get('disclaimer', DISCLAIMER)}",
        "",
        "This file lists large or repeated context signals by path and reason only.",
        "It intentionally avoids copying large prompt, instruction, skill, or",
        "duplicate block bodies.",
        "",
        "## Immediate",
        "",
    ]
    lines.extend([
        f"- `{row['path']}` ({row['category']}): {row['reason']}"
        for row in immediate
    ] or ["- None"])
    lines.extend(["", "## Needs Review", ""])
    lines.extend([
        f"- `{row['path']}` ({row['category']}): {row['reason']}"
        for row in needs_review
    ] or ["- None"])
    lines.extend(["", "## Repeated Context Blocks", ""])
    if duplicates:
        lines.extend(markdown_table(
            ["Preview", "Files", "Estimated Redundant Tokens"],
            [
                [
                    row.get("block_preview", "").replace("|", "\\|"),
                    row.get("file_count"),
                    row.get("total_redundant_tokens"),
                ]
                for row in duplicates
            ],
        ))
    else:
        lines.append("- None")
    lines.append("")
    return "\n".join(lines)


def write_token_artifacts(report: dict[str, Any], output_dir: Path) -> list[Path]:
    """Write the additive `.cg-docs/token/` workflow baseline artifacts."""
    output_dir.mkdir(parents=True, exist_ok=True)
    artifacts = {
        "TOKEN-BUDGET.md": render_token_budget_markdown(report),
        "TOKEN-DASHBOARD.md": render_token_dashboard_markdown(report),
        "token-audit.json": json.dumps(
            build_token_audit_artifact(report),
            indent=2,
            ensure_ascii=False,
            sort_keys=True,
        ) + "\n",
        "context-map.json": json.dumps(
            build_context_map_artifact(report),
            indent=2,
            ensure_ascii=False,
            sort_keys=True,
        ) + "\n",
        "regression-check.json": json.dumps(
            build_token_regression_check(report),
            indent=2,
            ensure_ascii=False,
            sort_keys=True,
        ) + "\n",
        "workflow-costs.csv": render_workflow_costs_csv(report),
        "large-context-warnings.md": render_large_context_warnings_markdown(report),
    }
    written: list[Path] = []
    for name in TOKEN_ARTIFACT_FILENAMES:
        path = output_dir / name
        write_atomic(path, artifacts[name])
        written.append(path)
    return written


def write_outputs(report: dict[str, Any], output_dir: Path, fmt: str, recommendations: bool = False) -> list[Path]:
    """Write the audit report to disk in the requested format(s).

    Args:
        report: Output of :func:`build_report`.
        output_dir: Directory to write output files into (created if absent).
        fmt: One of ``"json"``, ``"md"``, or ``"both"``.
        recommendations: Whether to also write ``token-advice.md``.

    Returns:
        List of :class:`~pathlib.Path` objects for the files written.

    Raises:
        ValueError: If ``fmt`` is not one of the accepted values.

    Example::

        paths = write_outputs(report, Path(".cg-docs/cost"), "both")
    """
    if fmt not in ("json", "md", "both"):
        raise ValueError(f"Unknown format {fmt!r}; expected 'json', 'md', or 'both'")
    output_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    if fmt in ("json", "both"):
        json_path = output_dir / "context-audit.json"
        write_atomic(json_path, json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + "\n")
        written.append(json_path)
    if fmt in ("md", "both"):
        md_path = output_dir / "context-audit.md"
        write_atomic(md_path, render_markdown(report))
        written.append(md_path)
    if recommendations:
        advice_path = output_dir / "token-advice.md"
        write_atomic(advice_path, render_recommendations_markdown(report))
        written.append(advice_path)
    return written


def build_arg_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser for cg-audit-context.

    Returns:
        Configured :class:`~argparse.ArgumentParser` instance.
    """
    parser = argparse.ArgumentParser(
        prog="cg-audit-context",
        description="Compound GPID context and model-governance audit.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--root", metavar="PATH", default=None,
                        help="Project root (defaults to parent of scripts/).")
    parser.add_argument("--output-dir", metavar="PATH", default=None,
                        help="Output directory (defaults to .cg-docs/cost/).")
    parser.add_argument("--format", choices=("json", "md", "both"), default="both", help="Report format to write.")
    parser.add_argument("--baseline", metavar="PATH", default=None,
                        help="Optional previous context-audit.json for before/after benchmark deltas.")
    parser.add_argument("--recommendations", action="store_true",
                        help="Also write a compact token-advice.md recommendation report.")
    parser.add_argument("--token-output-dir", metavar="PATH", default=None,
                        help="Output directory for workflow token baseline artifacts (defaults to .cg-docs/token/).")
    parser.add_argument("--no-token-artifacts", action="store_true",
                        help="Do not write the additive .cg-docs/token/ workflow baseline artifacts.")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Entry point for the cg-audit-context CLI.

    Args:
        argv: Argument list (defaults to ``sys.argv[1:]`` when ``None``).

    Returns:
        Exit code: 0 success, 1 fatal error, 2 invalid project root.

    Raises:
        SystemExit: Via :func:`sys.exit` when called as ``__main__``.

    Example::

        sys.exit(main(["--root", "/path/to/project", "--format", "json"]))
    """
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    root = Path(args.root).resolve() if args.root else Path(__file__).resolve().parent.parent
    if not (root / ".github" / "prompts").is_dir():
        print(
            f"[cg-audit-context] ERROR: {root} is not a Compound GPID root; missing .github/prompts/",
            file=sys.stderr,
        )
        return 2
    output_dir = Path(args.output_dir) if args.output_dir else Path(".cg-docs") / "cost"
    if not output_dir.is_absolute():
        output_dir = root / output_dir
    token_output_dir = Path(args.token_output_dir) if args.token_output_dir else Path(".cg-docs") / "token"
    if not token_output_dir.is_absolute():
        token_output_dir = root / token_output_dir
    try:
        report = build_report(root)
        if args.baseline:
            baseline_path = Path(args.baseline)
            if not baseline_path.is_absolute():
                baseline_path = root / baseline_path
            try:
                baseline = json.loads(baseline_path.read_text(encoding="utf-8-sig"))
            except (OSError, json.JSONDecodeError) as exc:
                print(f"[cg-audit-context] ERROR: baseline {baseline_path}: {exc}", file=sys.stderr)
                return 1
            report["benchmark"]["comparison"] = compare_benchmark_to_baseline(report, baseline)
        written = write_outputs(report, output_dir, args.format, args.recommendations)
        if not args.no_token_artifacts:
            written.extend(write_token_artifacts(report, token_output_dir))
    except (OSError, UnicodeDecodeError) as exc:
        print(f"[cg-audit-context] ERROR: {exc}", file=sys.stderr)
        return 1
    for path in written:
        print(f"[cg-audit-context] Wrote {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
