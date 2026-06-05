#!/usr/bin/env python3
"""cg-audit-context — Compound GPID context and model-governance audit.

Inventories context-contributing files, estimates token burden with chars / 4,
counts prompt and agent references, inventories model declarations, detects
duplicate paragraph blocks, and writes JSON/Markdown reports.

Usage:
    python scripts/cg_audit_context.py [--root <path>] [--output-dir <path>] [--format json|md|both]

Exit codes:
    0  Success.
    1  Fatal error.
    2  Missing or invalid project root.

Requirements: Python 3.8+, stdlib only (no third-party packages).
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
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

_scripts_dir = str(Path(__file__).parent)
if _scripts_dir not in sys.path:
    sys.path.insert(0, _scripts_dir)

from brain.utils import parse_frontmatter  # noqa: E402

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

FILE_REF_RE = re.compile(
    r"\b(?:compound-gpid(?:\.context|\.local)?\.md|roadmap\.json|BRAIN(?:-\d+|-log)?\.md|"
    r"brain-index\.json|context\.md|model-guide\.md|copilot-instructions(?:\.template)?\.md)\b",
    re.IGNORECASE,
)
AGENT_REF_RE = re.compile(r"@cg-[a-z-]+")
SKILL_REF_RE = re.compile(r"cg-skill-[a-z-]+")
TOOL_REF_RE = re.compile(r"\b(?:read_file|edit_file|run_in_terminal|grep_search|semantic_search)\b")
LOAD_VERB_RE = re.compile(r"\b(?:must read|load .+skill|consult|dispatch)\b", re.IGNORECASE)
ESCALATION_RE = re.compile(r"\b(?:escalat|opus required|borderline|frontier|highest capability)\b", re.IGNORECASE)


def estimate_tokens(text: str) -> int:
    """Return the plan's heuristic token estimate: characters // 4."""
    return len(text) // 4


def rel_path(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def scan_files(root: Path) -> Tuple[List[Dict[str, Any]], Dict[str, Dict[str, int]]]:
    """Scan all configured categories and return per-file and category totals."""
    files: List[Dict[str, Any]] = []
    seen: set = set()
    by_category: Dict[str, Dict[str, int]] = {
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
            content = path.read_text(encoding="utf-8-sig")
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


def classify_model_tier(model: Optional[str]) -> str:
    if not model:
        return "missing"
    if "Opus" in model:
        return "premium"
    if "Sonnet" in model:
        return "standard"
    if "Haiku" in model:
        return "economy"
    return "unknown"


def normalize_model_name(model: Optional[str]) -> str:
    return re.sub(r"\s*\(copilot\)\s*$", "", model or "", flags=re.IGNORECASE).strip()

def extract_model_declarations(root: Path, files: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    declarations: List[Dict[str, Any]] = []
    for file_record in files:
        if file_record["category"] not in ("prompts", "agents"):
            continue
        path = root / file_record["path"]
        content = path.read_text(encoding="utf-8-sig")
        fm = parse_frontmatter(content)
        model = fm.get("model")
        if model is not None:
            model = str(model)
        declarations.append({
            "path": file_record["path"],
            "category": file_record["category"],
            "model": model,
            "model_tier": classify_model_tier(model),
            "has_escalation_condition": bool(ESCALATION_RE.search(content)),
            "tools": fm.get("tools"),
        })
    return declarations


def parse_model_guide(path: Path) -> Dict[str, str]:
    """Parse docs/model-guide.md prompt/agent tables into filename -> model."""
    if not path.exists():
        return {}
    guide: Dict[str, str] = {}
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
        if len(cells) < 2 or cells[0] in ("File", "------"):
            continue
        filename = cells[0].strip("` ")
        model = cells[1].strip("` ")
        if filename and filename != "---------------":
            guide[filename] = model
    return guide


def build_model_inventory(root: Path, files: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    declarations = extract_model_declarations(root, files)
    guide = parse_model_guide(root / "docs" / "model-guide.md")
    missing = [d for d in declarations if not d["model"]]
    drift = []
    for declaration in declarations:
        expected = guide.get(Path(declaration["path"]).name)
        if expected and normalize_model_name(declaration["model"]) != normalize_model_name(expected):
            drift.append(
                {
                    "path": declaration["path"],
                    "frontmatter_model": declaration["model"],
                    "model_guide_model": expected,
                }
            )
    premium_usage = [d for d in declarations if d["model_tier"] == "premium"]
    return {
        "declarations": declarations,
        "missing": missing,
        "drift": drift,
        "premium_usage": premium_usage,
    }


def count_references(path: str, content: str) -> Dict[str, Any]:
    file_refs = len(FILE_REF_RE.findall(content))
    agent_refs = len(AGENT_REF_RE.findall(content))
    skill_refs = len(SKILL_REF_RE.findall(content))
    tool_refs = len(TOOL_REF_RE.findall(content))
    load_verbs = len(LOAD_VERB_RE.findall(content))
    total_refs = file_refs + agent_refs + skill_refs + tool_refs + load_verbs
    return {"path": path, "file_refs": file_refs, "agent_refs": agent_refs,
            "skill_refs": skill_refs, "tool_refs": tool_refs,
            "load_verbs": load_verbs, "total_refs": total_refs}


def build_reference_matrix(root: Path, files: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows = []
    for file_record in files:
        if file_record["category"] not in ("prompts", "agents"):
            continue
        path = root / file_record["path"]
        rows.append(count_references(file_record["path"], path.read_text(encoding="utf-8-sig")))
    return sorted(rows, key=lambda row: (-row["total_refs"], row["path"]))


def iter_paragraph_blocks(content: str) -> Iterable[str]:
    for block in re.split(r"\n\s*\n", content):
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        if len(lines) >= 4:
            yield "\n".join(lines)


def normalize_block(block: str) -> str:
    lines = [" ".join(line.strip().split()) for line in block.splitlines()]
    return "\n".join(lines).strip()


def detect_duplicates(root: Path, files: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    blocks: Dict[str, Dict[str, Any]] = {}
    for file_record in files:
        path = root / file_record["path"]
        content = path.read_text(encoding="utf-8-sig")
        for block in iter_paragraph_blocks(content):
            normalized = normalize_block(block)
            digest = hashlib.md5(normalized.encode("utf-8")).hexdigest()
            entry = blocks.setdefault(
                digest,
                {"block": normalized, "files": set(), "total_chars": 0},
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
                    "estimated_tokens": entry["total_chars"] // 4,
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
    files: Sequence[Dict[str, Any]],
    reference_matrix: Sequence[Dict[str, Any]],
    model_inventory: Dict[str, Any],
    duplicates: Sequence[Dict[str, Any]],
) -> Dict[str, Any]:
    refs_by_path = {row["path"]: row for row in reference_matrix}
    models_by_path = {row["path"]: row for row in model_inventory["declarations"]}
    drift_paths = {row["path"] for row in model_inventory["drift"]}
    immediate: List[Dict[str, Any]] = []
    needs_review: List[Dict[str, Any]] = []
    classified_paths: set = set()

    def add(bucket: List[Dict[str, Any]], path: str, category: str, reason: str) -> None:
        bucket.append({"path": path, "category": category, "reason": reason})
        classified_paths.add(path)

    for file_record in files:
        path = file_record["path"]
        category = file_record["category"]
        chars = int(file_record["characters"])
        tokens = int(file_record["estimated_tokens"])
        refs = refs_by_path.get(path, {"total_refs": 0})
        model = models_by_path.get(path)
        reasons_immediate: List[str] = []
        reasons_review: List[str] = []

        if category == "instructions" and tokens >= THRESHOLD_INSTRUCTION_IMMEDIATE:
            reasons_immediate.append(f"instruction estimated tokens >= {THRESHOLD_INSTRUCTION_IMMEDIATE}")
        if category == "prompts":
            if tokens >= THRESHOLD_PROMPT_IMMEDIATE:
                reasons_immediate.append(f"prompt estimated tokens >= {THRESHOLD_PROMPT_IMMEDIATE}")
            elif chars >= THRESHOLD_PROMPT_IMMEDIATE or tokens >= THRESHOLD_PROMPT_REVIEW:
                reasons_review.append(f"prompt size exceeds review threshold")
        if category == "agents" and tokens >= THRESHOLD_AGENT_REVIEW:
            reasons_review.append(f"agent estimated tokens >= {THRESHOLD_AGENT_REVIEW}")
        if category == "skills":
            if tokens >= THRESHOLD_SKILL_IMMEDIATE:
                reasons_immediate.append(f"skill estimated tokens >= {THRESHOLD_SKILL_IMMEDIATE}")
            elif tokens >= THRESHOLD_SKILL_REVIEW:
                reasons_review.append(f"skill estimated tokens >= {THRESHOLD_SKILL_REVIEW}")
        if refs["total_refs"] >= THRESHOLD_REFS_IMMEDIATE:
            reasons_immediate.append(f"reference count >= {THRESHOLD_REFS_IMMEDIATE}")
        if model:
            if model["model_tier"] == "premium" and not model["has_escalation_condition"]:
                reasons_immediate.append("premium model without escalation condition")
            if category == "agents" and model["model_tier"] == "premium" and _has_broad_tools(model.get("tools")):
                reasons_immediate.append("agent has broad tools and premium model")
            if model["model_tier"] == "missing" and refs["total_refs"] >= 3:
                reasons_review.append("missing model in high-reference prompt/agent")
        if path in drift_paths:
            reasons_review.append("model guide drift")

        if reasons_immediate:
            add(immediate, path, category, "; ".join(reasons_immediate))
        elif reasons_review:
            add(needs_review, path, category, "; ".join(reasons_review))

    for duplicate in duplicates:
        if (
            duplicate["file_count"] >= THRESHOLD_DUPLICATE_FILES
            and duplicate["estimated_tokens"] >= THRESHOLD_DUPLICATE_TOKENS
        ):
            add(immediate, "(duplicate block)", "duplicates",
                f"duplicate block appears in {duplicate['file_count']} files")

    return {"immediate": immediate, "needs_review": needs_review,
            "acceptable_count": max(0, len(files) - len(classified_paths))}


def build_report(root: Path) -> Dict[str, Any]:
    files, by_category = scan_files(root)
    reference_matrix = build_reference_matrix(root, files)
    model_inventory = build_model_inventory(root, files)
    duplicates = detect_duplicates(root, files)
    candidates = classify_optimization_candidates(files, reference_matrix, model_inventory, duplicates)
    return {"generated": datetime.now().isoformat(timespec="seconds"), "disclaimer": DISCLAIMER,
            "summary": {"total_files": len(files),
                        "total_characters": sum(int(f["characters"]) for f in files),
                        "total_estimated_tokens": sum(int(f["estimated_tokens"]) for f in files),
                        "by_category": by_category},
            "files": sorted(files, key=lambda row: row["path"]),
            "reference_matrix": reference_matrix, "model_inventory": model_inventory,
            "duplicates": duplicates, "optimization_candidates": candidates}


def markdown_table(headers: Sequence[str], rows: Sequence[Sequence[Any]]) -> List[str]:
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(cell) for cell in row) + " |")
    return lines


def render_markdown(report: Dict[str, Any]) -> str:
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
    lines.extend(["", "## Prompt Reference Matrix", ""])
    lines.extend(markdown_table(["Path", "File", "Agent", "Skill", "Tool", "Load", "Total"], [
        [r["path"], r["file_refs"], r["agent_refs"], r["skill_refs"], r["tool_refs"], r["load_verbs"], r["total_refs"]]
        for r in report["reference_matrix"]
    ]))
    lines.extend(["", "## Model Inventory", ""])
    lines.extend(markdown_table(["Path", "Category", "Model", "Tier"], [
        [d["path"], d["category"], d["model"] or "(missing)", d["model_tier"]]
        for d in report["model_inventory"]["declarations"]
    ]))
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
    lines.extend(["", "## Duplicate Paragraphs", ""])
    lines.extend(markdown_table(["Preview", "Files", "Estimated Tokens"], [
        [d["block_preview"].replace("|", "\\|"), d["file_count"], d["estimated_tokens"]]
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


def write_outputs(report: Dict[str, Any], output_dir: Path, fmt: str) -> List[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    written: List[Path] = []
    if fmt in ("json", "both"):
        json_path = output_dir / "context-audit.json"
        json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        written.append(json_path)
    if fmt in ("md", "both"):
        md_path = output_dir / "context-audit.md"
        md_path.write_text(render_markdown(report), encoding="utf-8")
        written.append(md_path)
    return written


def build_arg_parser() -> argparse.ArgumentParser:
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
    return parser


def main(argv: Optional[List[str]] = None) -> int:
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
    try:
        report = build_report(root)
        written = write_outputs(report, output_dir, args.format)
    except (OSError, UnicodeDecodeError) as exc:
        print(f"[cg-audit-context] ERROR: {exc}", file=sys.stderr)
        return 1
    for path in written:
        print(f"[cg-audit-context] Wrote {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
