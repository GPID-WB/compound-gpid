#!/usr/bin/env python3
"""Compact local summaries for noisy Compound GPID command surfaces."""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Optional, Union


OUTPUT_ROOT = Path(".cg-docs/token/outputs")
TREE_EXCLUDES = {
    ".git",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "__pycache__",
    "node_modules",
    ".venv",
    "venv",
    "renv",
    "outputs",
}
SECRET_PATTERNS = [
    re.compile(r"(?i)\b(token|password|api[_-]?key|secret)\s*=\s*([^\s\"']+)"),
    re.compile(r"(?i)\b(token|password|api[_-]?key|secret)\s*:\s*([^\s\"',}]+)"),
]
MODEL_BODY_EXCLUDED_PREFIXES = (".cg-docs/views/",)


class SummaryError(RuntimeError):
    """Expected user-facing summary failure."""


def estimate_tokens(text: str) -> int:
    return (len(text) + 3) // 4


def redact(text: str) -> str:
    redacted = text
    for pattern in SECRET_PATTERNS:
        redacted = pattern.sub(lambda match: f"{match.group(1)}=<redacted>", redacted)
    return redacted


def resolve_root(root: Union[str, Path]) -> Path:
    return Path(root).expanduser().resolve()


def utc_run_id(now: Optional[datetime] = None) -> str:
    current = now or datetime.now(timezone.utc)
    return current.strftime("%Y%m%d-%H%M%S")


def output_dir(root: Path, kind: str, run_id: Optional[str] = None) -> Path:
    safe_kind = re.sub(r"[^a-z0-9_-]+", "-", kind.lower()).strip("-") or "summary"
    return root / OUTPUT_ROOT / f"{run_id or utc_run_id()}-{safe_kind}"


def write_artifact(root: Path, kind: str, filename: str, text: str, run_id: Optional[str] = None) -> str:
    directory = output_dir(root, kind, run_id)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / filename
    path.write_text(redact(text), encoding="utf-8")
    return path.relative_to(root).as_posix()


def run_git(root: Path, args: list[str], check: bool = False) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if check and result.returncode != 0:
        raise SummaryError(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result


def display_path(path: Path, root: Path) -> str:
    """Return a POSIX relative path when contained, otherwise an absolute path."""
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return str(path)


def summarize_last_run(payload: dict[str, Any]) -> dict[str, Any]:
    failed = payload.get("failedTests") or payload.get("failures") or []
    if not isinstance(failed, list):
        failed = []
    failure_summaries = []
    for item in failed[:10]:
        if isinstance(item, dict):
            failure_summaries.append({
                "name": item.get("name") or item.get("test") or item.get("title") or "unknown",
                "message": item.get("message") or item.get("error") or item.get("failureMessage"),
                "file": item.get("file") or item.get("path"),
            })
        else:
            failure_summaries.append({"name": str(item), "message": None, "file": None})
    return {
        "total": payload.get("totalCount", payload.get("total")),
        "passed": payload.get("passedCount", payload.get("passed")),
        "failed": payload.get("failedCount", payload.get("failed")),
        "skipped": payload.get("skippedCount", payload.get("skipped")),
        "filtered_files": payload.get("filteredFiles"),
        "ran_at": payload.get("ranAt"),
        "failure_summaries": failure_summaries,
    }


def test_summary(root: Path, input_path: Optional[Path] = None, run_id: Optional[str] = None) -> dict[str, Any]:
    source = input_path or root / "tests/last-run.json"
    if not source.exists():
        return {
            "kind": "test",
            "available": False,
            "reason": f"{display_path(source, root)} not found",
            "note": "Run the repository safe test command first; this wrapper reads existing results only.",
        }
    raw = source.read_text(encoding="utf-8")
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SummaryError(f"Invalid JSON in {source}: {exc}") from exc
    artifact = write_artifact(root, "test", source.name, raw, run_id)
    summary = summarize_last_run(payload)
    summary.update({
        "kind": "test",
        "available": True,
        "source": display_path(source, root),
        "raw_artifact": artifact,
        "estimated_summary_tokens": 0,
    })
    summary["estimated_summary_tokens"] = estimate_tokens(json.dumps(summary, sort_keys=True))
    return summary


def risk_tags_for_paths(paths: Iterable[str]) -> list[str]:
    tags: set[str] = set()
    for path in paths:
        suffix = Path(path).suffix.lower()
        parts = set(Path(path).parts)
        if path.startswith(".github/") or "prompts" in parts or "skills" in parts:
            tags.add("prompt-or-skill")
        if path.startswith("tests/") or "/tests/" in path or path.startswith("scripts/tests/"):
            tags.add("tests")
        if suffix == ".py":
            tags.add("python")
        if suffix in {".ps1", ".psm1"}:
            tags.add("powershell")
        if path == "roadmap.json" or ".cg-docs/plans/" in path:
            tags.add("roadmap")
        if path.startswith("docs/") or path.startswith(".cg-docs/"):
            tags.add("docs")
        if "token" in path.lower():
            tags.add("token")
    return sorted(tags)


def parse_hunks(diff_text: str) -> dict[str, int]:
    hunks: Counter[str] = Counter()
    current: Optional[str] = None
    for line in diff_text.splitlines():
        if line.startswith("diff --git "):
            parts = line.split()
            current = parts[-1][2:] if len(parts) >= 4 and parts[-1].startswith("b/") else None
        elif current and line.startswith("@@ "):
            hunks[current] += 1
    return dict(sorted(hunks.items()))


def is_model_body_excluded(path: str) -> bool:
    """Return whether a changed path is listed but excluded from raw patches."""
    normalized = path.replace("\\", "/")
    return any(normalized.startswith(prefix) for prefix in MODEL_BODY_EXCLUDED_PREFIXES)


def diff_summary(root: Path, run_id: Optional[str] = None) -> dict[str, Any]:
    diff = run_git(
        root,
        ["diff", "--no-ext-diff", "--", ".", ":(exclude).cg-docs/views/**"],
        check=True,
    ).stdout
    stat = run_git(root, ["diff", "--stat"], check=False).stdout
    name_only = run_git(root, ["diff", "--name-only"], check=False).stdout
    untracked_output = run_git(root, ["ls-files", "--others", "--exclude-standard"], check=False).stdout
    tracked_files = [line for line in name_only.splitlines() if line.strip()]
    untracked_files = [line for line in untracked_output.splitlines() if line.strip()]
    files = sorted(dict.fromkeys([*tracked_files, *untracked_files]))
    excluded_body_paths = [path for path in files if is_model_body_excluded(path)]
    raw_artifact = write_artifact(root, "diff", "git-diff.patch", diff, run_id)
    stat_artifact = write_artifact(root, "diff", "git-diff-stat.txt", stat, run_id)
    summary = {
        "kind": "diff",
        "available": True,
        "changed_file_count": len(files),
        "changed_files": files[:80],
        "tracked_files": tracked_files[:80],
        "untracked_files": untracked_files[:80],
        "excluded_body_paths": excluded_body_paths[:80],
        "truncated_files": len(files) > 80,
        "hunks_by_file": parse_hunks(diff),
        "risk_tags": risk_tags_for_paths(files),
        "stat": stat.strip().splitlines()[-12:],
        "raw_artifact": raw_artifact,
        "stat_artifact": stat_artifact,
        "estimated_summary_tokens": 0,
    }
    summary["estimated_summary_tokens"] = estimate_tokens(json.dumps(summary, sort_keys=True))
    return summary


def default_base_ref(root: Path) -> Optional[str]:
    head = run_git(root, ["symbolic-ref", "refs/remotes/origin/HEAD", "--short"])
    if head.returncode == 0 and head.stdout.strip():
        return head.stdout.strip()
    for candidate in ("origin/main", "origin/master", "main", "master"):
        result = run_git(root, ["rev-parse", "--verify", candidate])
        if result.returncode == 0:
            return candidate
    return None


def log_summary(root: Path, base: Optional[str] = None, run_id: Optional[str] = None) -> dict[str, Any]:
    base_ref = base or default_base_ref(root)
    if not base_ref:
        return {"kind": "log", "available": False, "reason": "No base ref found for branch-local log summary."}
    merge_base = run_git(root, ["merge-base", base_ref, "HEAD"])
    if merge_base.returncode != 0:
        return {"kind": "log", "available": False, "base": base_ref, "reason": merge_base.stderr.strip()}
    base_sha = merge_base.stdout.strip()
    log = run_git(root, ["log", "--first-parent", "--oneline", f"{base_sha}..HEAD"], check=True).stdout
    changed = run_git(root, ["diff", "--name-only", f"{base_sha}...HEAD"], check=False).stdout
    files = [line for line in changed.splitlines() if line.strip()]
    raw_artifact = write_artifact(root, "log", "git-log.txt", log, run_id)
    commits = [{"sha": line.split(maxsplit=1)[0], "subject": line.split(maxsplit=1)[1] if " " in line else ""} for line in log.splitlines() if line]
    summary = {
        "kind": "log",
        "available": True,
        "base": base_ref,
        "merge_base": base_sha,
        "first_parent_commit_count": len(commits),
        "commits": commits[:40],
        "truncated_commits": len(commits) > 40,
        "notable_files": files[:80],
        "risk_tags": risk_tags_for_paths(files),
        "raw_artifact": raw_artifact,
        "estimated_summary_tokens": 0,
    }
    summary["estimated_summary_tokens"] = estimate_tokens(json.dumps(summary, sort_keys=True))
    return summary


def should_skip_dir(path: Path, root: Path) -> bool:
    rel_parts = path.relative_to(root).parts
    if not rel_parts:
        return False
    if path.name in TREE_EXCLUDES:
        return True
    return rel_parts[:3] == (".cg-docs", "token", "outputs")


def tree_summary(root: Path, max_entries: int = 120) -> dict[str, Any]:
    entries: list[str] = []
    skipped_dirs: list[str] = []
    for current, dirs, files in os.walk(root):
        current_path = Path(current)
        dirs[:] = sorted(d for d in dirs if not should_skip_dir(current_path / d, root))
        skipped_dirs.extend(
            (current_path / d).relative_to(root).as_posix()
            for d in set(os.listdir(current_path)).intersection(TREE_EXCLUDES)
            if (current_path / d).is_dir()
        )
        rel_current = current_path.relative_to(root).as_posix()
        if rel_current == ".":
            rel_current = ""
        for filename in sorted(files):
            rel = f"{rel_current}/{filename}".strip("/")
            if rel.startswith(".cg-docs/token/outputs/"):
                continue
            entries.append(rel)
            if len(entries) >= max_entries:
                return {
                    "kind": "tree",
                    "available": True,
                    "root": str(root),
                    "max_entries": max_entries,
                    "entries": entries,
                    "truncated": True,
                    "skipped_dirs": sorted(set(skipped_dirs))[:40],
                }
    return {
        "kind": "tree",
        "available": True,
        "root": str(root),
        "max_entries": max_entries,
        "entries": entries,
        "truncated": False,
        "skipped_dirs": sorted(set(skipped_dirs))[:40],
    }


def normalize_severity(value: Any) -> str:
    text = str(value or "unknown").lower()
    if text in {"error", "err", "fatal", "failure", "failed"}:
        return "error"
    if text in {"warning", "warn"}:
        return "warning"
    if text in {"information", "info", "hint"}:
        return "info"
    return text or "unknown"


def flatten_problem_items(payload: Any) -> list[Any]:
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for key in ("problems", "diagnostics", "items", "errors", "warnings"):
            value = payload.get(key)
            if isinstance(value, list):
                return value
    return []


def summarize_json_problems(payload: Any) -> dict[str, Any]:
    items = flatten_problem_items(payload)
    counts: Counter[str] = Counter()
    samples: list[dict[str, Any]] = []
    for item in items:
        if isinstance(item, dict):
            severity = normalize_severity(item.get("severity") or item.get("level") or item.get("type"))
            counts[severity] += 1
            if len(samples) < 10:
                samples.append({
                    "severity": severity,
                    "message": item.get("message") or item.get("text") or item.get("title"),
                    "file": item.get("file") or item.get("path") or item.get("source"),
                })
        else:
            counts["unknown"] += 1
            if len(samples) < 10:
                samples.append({"severity": "unknown", "message": str(item), "file": None})
    return {"problem_count": sum(counts.values()), "severity_counts": dict(sorted(counts.items())), "samples": samples}


def summarize_text_problems(text: str) -> dict[str, Any]:
    counts: Counter[str] = Counter()
    samples: list[dict[str, Any]] = []
    for line in text.splitlines():
        upper = line.upper()
        if "ERROR" in upper or "FATAL" in upper or "FAILED" in upper:
            severity = "error"
        elif "WARN" in upper:
            severity = "warning"
        elif "INFO" in upper:
            severity = "info"
        else:
            continue
        counts[severity] += 1
        if len(samples) < 10:
            samples.append({"severity": severity, "message": line.strip(), "file": None})
    return {"problem_count": sum(counts.values()), "severity_counts": dict(sorted(counts.items())), "samples": samples}


def problems_summary(root: Path, input_path: Optional[Path] = None, run_id: Optional[str] = None) -> dict[str, Any]:
    if input_path is None:
        return {
            "kind": "problems",
            "available": False,
            "reason": "No diagnostics file was provided.",
            "usage": "Pass --input path/to/problems.json or a text diagnostics log.",
        }
    source = input_path if input_path.is_absolute() else root / input_path
    if not source.exists():
        return {"kind": "problems", "available": False, "reason": f"{source} not found"}
    raw = source.read_text(encoding="utf-8")
    artifact = write_artifact(root, "problems", source.name, raw, run_id)
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        details = summarize_text_problems(raw)
        parser = "text"
    else:
        details = summarize_json_problems(payload)
        parser = "json"
    details.update({
        "kind": "problems",
        "available": True,
        "parser": parser,
        "source": display_path(source, root),
        "raw_artifact": artifact,
        "estimated_summary_tokens": 0,
    })
    details["estimated_summary_tokens"] = estimate_tokens(json.dumps(details, sort_keys=True))
    return details


def to_markdown(summary: dict[str, Any]) -> str:
    lines = [f"# {summary.get('kind', 'summary').title()} Summary", ""]
    for key, value in summary.items():
        if key == "kind":
            continue
        if isinstance(value, (list, dict)):
            rendered = json.dumps(value, indent=2, sort_keys=True)
            lines.extend([f"## {key}", "```json", rendered, "```", ""])
        else:
            lines.append(f"- **{key}**: {value}")
    return "\n".join(lines).rstrip() + "\n"


def emit(summary: dict[str, Any], output_format: str) -> None:
    if output_format == "json":
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(to_markdown(summary), end="")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Summarize noisy local command outputs without changing validation semantics.")
    parser.add_argument("--root", default=".", help="Repository root. Defaults to current directory.")
    parser.add_argument("--format", choices=("json", "md"), default="json", help="Output format.")
    parser.add_argument("--run-id", help=argparse.SUPPRESS)
    subparsers = parser.add_subparsers(dest="command", required=True)

    def add_common_options(subparser: argparse.ArgumentParser) -> None:
        subparser.add_argument("--root", default=argparse.SUPPRESS, help="Repository root. Defaults to current directory.")
        subparser.add_argument("--format", choices=("json", "md"), default=argparse.SUPPRESS, help="Output format.")
        subparser.add_argument("--run-id", default=argparse.SUPPRESS, help=argparse.SUPPRESS)

    test = subparsers.add_parser("test", help="Summarize tests/last-run.json without running tests.")
    add_common_options(test)
    test.add_argument("--input", type=Path, help="Optional last-run JSON path.")

    diff = subparsers.add_parser("diff", help="Summarize current git diff and store full patch.")
    add_common_options(diff)

    log = subparsers.add_parser("log", help="Summarize branch-local first-parent commits.")
    add_common_options(log)
    log.add_argument("--base", help="Base ref. Defaults to origin HEAD, origin/main, or main.")

    tree = subparsers.add_parser("tree", help="Summarize a bounded repository tree.")
    add_common_options(tree)
    tree.add_argument("--max-entries", type=int, default=120)

    problems = subparsers.add_parser("problems", help="Summarize optional diagnostics JSON/text.")
    add_common_options(problems)
    problems.add_argument("--input", type=Path, help="Diagnostics JSON/text path.")

    return parser


def summary_from_args(args: argparse.Namespace) -> dict[str, Any]:
    root = resolve_root(args.root)
    if args.command == "test":
        input_path = args.input
        if input_path is not None and not input_path.is_absolute():
            input_path = root / input_path
        return test_summary(root, input_path, args.run_id)
    if args.command == "diff":
        return diff_summary(root, args.run_id)
    if args.command == "log":
        return log_summary(root, args.base, args.run_id)
    if args.command == "tree":
        if args.max_entries < 1:
            raise SummaryError("--max-entries must be at least 1")
        return tree_summary(root, args.max_entries)
    if args.command == "problems":
        return problems_summary(root, args.input, args.run_id)
    raise SummaryError(f"Unknown command: {args.command}")


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        summary = summary_from_args(args)
    except SummaryError as exc:
        parser.error(str(exc))
    emit(summary, args.format)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
