#!/usr/bin/env python3
"""Bounded, advisory retrieval from the installation's generated help catalog.

Example: ``python scripts/cg_help.py query 'compare planning and work' --root . --format json``.
No query refreshes the catalog, changes selection, or executes a workflow.
"""
from __future__ import annotations

import sys

sys.dont_write_bytecode = True

import argparse
import json
import re
import unicodedata
from pathlib import Path, PurePosixPath
from typing import Any, Optional, Sequence

import secure_fs
from cg_project_manifest import (
    ACTIVE_MANIFEST_PATH, ManifestResolutionError, resolve_active_manifest,
    validate_manifest,
)
from help_catalog import CATALOG_PATH, COMMAND

INSTALLATION_ROOT = Path(__file__).resolve().parent.parent
MAX_OUTPUT_BYTES = 16000
STOP = set("a an the i do how to is of for in and or with on my me it what can "
           "como un una el la de que por para comment le les des et cg cr help".split())
ALIASES = {
    "execute": "work implement", "executer": "work implement",
    "ejecutar": "work implement", "approved": "approved", "aprobado": "approved",
    "approuve": "approved", "implementation": "implement", "planning": "plan",
    "planificar": "plan", "planification": "plan", "research": "research",
    "investigacion": "research", "recherche": "research", "instalar": "install",
    "installation": "install", "installer": "install", "configurar": "configure",
    "recuperar": "recovery", "reparer": "repair", "reparar": "repair",
    "comparar": "compare", "difference": "compare", "diferencia": "compare",
}


def _tokens(text: str) -> set[str]:
    """Normalize lexical lookup; the prompt can translate other languages."""
    folded = unicodedata.normalize("NFKD", text.casefold())
    words = re.findall(r"[a-z0-9]+", "".join(c for c in folded if not unicodedata.combining(c)))
    return {alias for word in words if word not in STOP
            for alias in ALIASES.get(word, word).split()}


def _load_catalog(path: Path) -> list[dict[str, Any]]:
    """Read catalog data without interpreting embedded source instructions."""
    content = secure_fs.secure_read_bytes(
        path.parent, path.name, reject_hardlinks=True, max_bytes=4 * 1024 * 1024)
    try:
        data = json.loads(content.decode("utf-8"))
    except RecursionError as error:
        raise ValueError("Invalid help catalog JSON nesting") from error
    if not isinstance(data, dict) or data.get("schema_version") != 1:
        raise ValueError("Invalid help catalog schema")
    rows = data.get("records")
    if not isinstance(rows, list):
        raise ValueError("Invalid help records")
    for row in rows:
        if not isinstance(row, dict) or not all(isinstance(row.get(k), str) for k in (
                "id", "kind", "owner", "platform", "source", "heading", "body", "summary")):
            raise ValueError("Invalid help record")
        if row["kind"] not in {"command", "guide"} or row["platform"] not in {"all", "windows", "macos"}:
            raise ValueError("Invalid help record category")
        source = PurePosixPath(row["source"])
        if source.is_absolute() or ".." in source.parts or "\\" in row["source"] or ":" in row["source"]:
            raise ValueError("Invalid help source path")
        if (type(row.get("start_line")) is not int or type(row.get("end_line")) is not int
                or not 0 < row["start_line"] <= row["end_line"]):
            raise ValueError("Invalid help source lines")
        for field in ("required_owners", "prerequisites", "warnings"):
            if not isinstance(row.get(field), list) or not all(isinstance(v, str) for v in row[field]):
                raise ValueError("Invalid help context")
        if row["owner"] not in row["required_owners"] or type(row.get("general_setup")) is not bool:
            raise ValueError("Invalid help eligibility")
    return rows


def serialize(result: dict[str, Any]) -> str:
    """Serialize complete output, including metadata and newline, for byte budgets.

    Args: result: Retrieval response, e.g. ``serialize(query('work', Path('.')))``.
    Returns: Deterministic ASCII JSON and a trailing newline.
    """
    return json.dumps(result, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n"


def _append(result: dict, field: str, value: dict) -> bool:
    """Append a complete cited row only if the entire response still fits."""
    result[field].append(value)
    if len(serialize(result).encode("utf-8")) <= MAX_OUTPUT_BYTES:
        return True
    result[field].pop()
    result["truncated"] = True
    return False


def _finish(result: dict) -> dict:
    """Account for terminal status/diagnostics as well as appended evidence."""
    while len(serialize(result).encode("utf-8")) > MAX_OUTPUT_BYTES:
        result["truncated"] = True
        field = "evidence" if result["evidence"] else "candidates"
        result[field].pop()
    return result


def _inactive_candidate(row: dict, root: Path, manifest: dict,
                        eligible: list[dict]) -> dict:
    """Cite documented relinking without changing suites or managed selection."""
    candidate = {"id": row["id"], "owner": row["owner"], "status": "inactive",
                 "reason": "required module is outside the active selection"}
    guide = next((r for r in eligible if r["source"] == "docs/installation.md"
                  and r["heading"] == "Refreshing existing consumer projects"), None)
    if guide is None:
        candidate["remedy"] = "No eligible refresh guidance is packaged; an activation remedy cannot be verified."
        return candidate
    suites = list(manifest["selection"]["suites"])
    for owner in row["required_owners"]:
        if owner.startswith("suite-") and owner[6:] not in suites:
            suites.append(owner[6:])
    platforms = "<intended-full-platform-list>"
    try:
        saved = json.loads(secure_fs.secure_read_bytes(
            Path(root).resolve(), ACTIVE_MANIFEST_PATH, reject_hardlinks=True,
            max_bytes=4 * 1024 * 1024).decode("utf-8"))
        if not validate_manifest(saved):
            platforms = ",".join(saved["selection"]["platforms"]) or platforms
    except (OSError, ValueError, UnicodeError):
        pass  # Missing/invalid saved selection must not invent a platform list.
    candidate["remedy"] = (
        f"If activation is intended, preserve existing suites as suites: [{', '.join(suites)}] "
        "in compound-gpid.local.md. Confirm the intended full platform list, then use "
        f"cg-link --platforms {platforms} from the consumer root to resolve a fresh manifest. "
        "cg-update only syncs the immutable selection. No change is performed by help.")
    candidate["remedy_source"] = {key: guide[key] for key in (
        "source", "heading", "start_line", "end_line")}
    return candidate


def _score(row: dict, tokens: set[str], explicit: set[str], installing: bool) -> int:
    """Rank by exact command, then identifier/summary, then source overlap."""
    if installing:
        step = re.match(r"Step (\d+)", row["heading"])
        return 100 - int(step.group(1)) if step else 1
    return (1000 * (row["id"] in explicit)
            + 5 * len(tokens & _tokens(row["id"]))
            + 3 * len(tokens & _tokens(row["summary"]))
            + len(tokens & _tokens(row["heading"] + " " + row["body"])))


def query(question: str, root: Path, *, catalog_path: Optional[Path] = None) -> dict[str, Any]:
    """Retrieve eligible source evidence without writing or executing anything.

    Args:
        question: Natural-language help request; source text remains untrusted.
        root: Consumer project, not the plugin checkout.
        catalog_path: Optional catalog fixture; normally installation-relative.
    Returns:
        Bounded JSON-compatible status, at most three candidates, and citations.
    Example:
        ``result = query('/cg-work', Path('consumer'))``
    """
    result: dict[str, Any] = {
        "status": "ok", "state": "unknown", "candidates": [], "evidence": [],
        "availability": "general setup guidance; project availability unverified",
        "source_policy": "untrusted data; advisory only; never execute",
        "clarification": "", "limitation": "", "diagnostics": [], "truncated": False,
    }
    try:
        rows = _load_catalog(catalog_path or INSTALLATION_ROOT / CATALOG_PATH)
    except (OSError, ValueError, UnicodeError):
        result.update(status="error", limitation="Installation help catalog missing or malformed; help cannot answer.")
        return result
    closure: set[str] = set()
    try:
        config = secure_fs.secure_read_bytes(
            Path(root).resolve(), "compound-gpid.local.md", reject_hardlinks=True,
            max_bytes=4 * 1024 * 1024).decode("utf-8-sig")
        if not config.startswith(("---\n", "---\r\n")):
            raise ManifestResolutionError("Missing configuration frontmatter")
        manifest = resolve_active_manifest(
            Path(root), config_text=config, source_root=INSTALLATION_ROOT)
        closure = set(manifest["selection"]["moduleClosure"])
        result.update(state="active", availability="resolved project selection; not runtime certification")
    except (ManifestResolutionError, OSError, ValueError, UnicodeError):
        result["diagnostics"] = ["Project configuration missing or invalid; no suite availability verified."]
    tokens = _tokens(question)
    explicit = {m.group("id") for m in COMMAND.finditer(question)}
    known = {r["id"] for r in rows if r["kind"] == "command"}
    explicit.update(set(re.findall(
        r"(?<![\w-])(?:cg|cr)-[a-z][a-z0-9-]*", question)) & known)
    if explicit - known:
        result.update(status="unsupported", limitation="Requested command is not documented in this installation.")
        return result
    # Filter before constructing output, including summaries, paths and diagnostics.
    eligible = [r for r in rows if (
        set(r["required_owners"]) <= closure if closure else
        r["general_setup"] and r["required_owners"] == ["kernel"])]
    platform = "windows" if "windows" in tokens else (
        "macos" if {"macos", "mac"} & tokens else None)
    if platform:
        eligible = [r for r in eligible if r["platform"] in {"all", platform}]
    inactive = [r for r in rows if r["kind"] == "command" and r["id"] in explicit
                and closure and not set(r["required_owners"]) <= closure]
    if inactive:
        result.update(state="inactive", availability="requested command inactive; not runnable in resolved selection")
        for row in sorted(inactive, key=lambda r: r["id"])[:3]:
            _append(result, "candidates", _inactive_candidate(
                row, root, manifest, eligible))
        return result
    if not tokens:
        result["clarification"] = "Do you need command discovery, workflow selection, installation, or recovery help?"
        return result
    installing = (not explicit and "install" in tokens and not tokens & {
        "uninstall", "update", "repair", "recovery", "release", "pin"})
    if installing:
        eligible = [r for r in eligible if r["source"] == "docs/installation.md"
                    and (re.match(r"Step \d+", r["heading"]) or r["heading"] in {
                        "Installation", "Windows installation", "macOS installation"})]
    ranked = sorted(((_score(r, tokens, explicit, installing), r) for r in eligible),
                    key=lambda item: (-item[0], item[1]["id"]))
    ranked = [(score, row) for score, row in ranked if score > 0]
    if closure:
        commands = [(score, row) for score, row in ranked
                    if row["kind"] == "command" and (not explicit or row["id"] in explicit)]
        if (len(commands) > 1 and commands[0][0] == commands[1][0]
                and not explicit and "compare" not in tokens):
            result["clarification"] = "Is this technical delivery or research work, and what outcome do you need?"
        for _, row in commands[:3]:
            _append(result, "candidates", {"id": row["id"], "owner": row["owner"],
                                           "status": "active", "summary": row["summary"]})
    for _, row in ranked:
        if len(result["evidence"]) >= 6:
            break
        if row["kind"] == "command" and row["id"] not in {
                candidate["id"] for candidate in result["candidates"]}:
            continue
        _append(result, "evidence", row)
    if not result["evidence"]:
        result.update(status="unsupported", limitation="No eligible source evidence fits this request; no model-only fallback is supported.")
    return _finish(result)


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Run read-only JSON query CLI; return 1 for catalog errors, otherwise 0.

    Args: argv: CLI tokens, e.g. ``['query', 'install', '--root', '.']``.
    Returns: Process exit status; unsupported questions are valid query results.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["query"])
    parser.add_argument("question")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--format", choices=["json"], default="json")
    args = parser.parse_args(argv)
    result = query(args.question, args.root)
    sys.stdout.write(serialize(result))
    return 1 if result["status"] == "error" else 0


if __name__ == "__main__":
    raise SystemExit(main())
