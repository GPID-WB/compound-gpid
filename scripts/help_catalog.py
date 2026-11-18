"""Generate source-cited help data, separate from projected project inventory.

Example: ``refresh_catalog(Path('.'))`` refreshes installation tooling only.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import secure_fs
from brain.utils import _quoted_scalar_complete, parse_frontmatter
from skill_management.services.registry import matching_asset_owners

CATALOG_PATH = "scripts/help_catalog.json"
GUIDES = ("docs/workflows/index.md", "docs/help/index.md", "docs/installation.md")
COMMAND = re.compile(r"/(?P<id>(?:cg|cr)-[a-z][a-z0-9-]*)(?![a-z0-9-])")


def _text(root: Path, source: str) -> str:
    """Read installation source as untrusted UTF-8 data through secure_fs."""
    return secure_fs.secure_read_bytes(
        root, source, reject_hardlinks=True, max_bytes=4 * 1024 * 1024,
    ).decode("utf-8-sig").replace("\r\n", "\n").replace("\r", "\n")


def _sections(lines: list[str]) -> list[tuple[str, str, int, int]]:
    """Split Markdown at real headings, preserving fenced-code lines verbatim."""
    sections = []
    stack: list[tuple[int, str]] = []
    heading, platform, start, fence = "Introduction", "all", 0, ""
    for index, line in enumerate(lines):
        marker = re.match(r"^\s{0,3}(`{3,}|~{3,})", line)
        if marker:
            run = marker.group(1)
            if not fence:
                fence = run
            elif run[0] == fence[0] and len(run) >= len(fence):
                fence = ""
            continue
        match = re.match(r"^(#{1,6})\s+(.+?)\s*#*\s*$", line)
        if fence or not match:
            continue
        if index > start:
            sections.append((heading, platform, start, index))
        depth, heading = len(match.group(1)), match.group(2)
        stack = [(level, title) for level, title in stack if level < depth]
        stack.append((depth, heading))
        ancestry = " ".join(title for _, title in stack).casefold()
        inherited = platform if re.match(r"Step \d", heading) else "all"
        platform = "macos" if "macos" in ancestry else (
            "windows" if "windows" in ancestry else inherited)
        start = index
    if len(lines) > start:
        sections.append((heading, platform, start, len(lines)))
    return sections


def _requirements(body: str, owner: str, registry: dict) -> list[str]:
    """Collect suite dependencies mentioned in a returned excerpt before filtering."""
    required = {owner}
    for match in COMMAND.finditer(body):
        command = match.group("id")
        owners = matching_asset_owners(
            registry, f".github/prompts/{command}.prompt.md")
        required.update(owners or (f"suite-{command[:2]}",))
    for source in re.findall(r"\.github/(?:prompts|skills|agents|instructions|shared)/[^\s`<>\])]+", body):
        required.update(matching_asset_owners(registry, source))
    return sorted(required)


def _record(source: str, heading: str, lines: list[str], start: int, end: int,
            *, owner: str, platform: str, registry: dict, kind: str = "guide",
            identifier: str = "", summary: str = "") -> dict[str, Any]:
    """Keep exact source text and its context rather than rewriting instructions."""
    body = "\n".join(lines[start:end])
    required = _requirements("\n".join((heading, body, summary)), owner, registry)
    return {
        "id": identifier or f"{source}:{start + 1}", "kind": kind,
        "owner": owner, "required_owners": required, "platform": platform,
        "source": source, "heading": heading,
        "start_line": start + 1, "end_line": end, "body": body,
        "summary": summary,
        "prerequisites": [line for line in lines[start:end]
                          if re.search(r"prerequisite|requires?|before|only for", line, re.I)],
        "warnings": [line for line in lines[start:end]
                     if re.search(r"warn|never|must not|do not|discard|preserve|approval", line, re.I)],
        "general_setup": source in GUIDES[1:] and required == ["kernel"],
    }


def build_catalog(root: Path) -> dict[str, Any]:
    """Extract deterministic command metadata and selected verbatim guides.

    Args:
        root: Installation checkout containing canonical prompts and guides.
    Returns:
        JSON-compatible catalog, with source lines relative to this installation.
    Raises:
        ValueError, OSError: Required sources are malformed, missing or unsafe.
    Example:
        ``catalog = build_catalog(Path('.'))``
    """
    root = root.resolve()
    registry = json.loads(_text(root, ".github/shared/module-registry.json"))
    if (not isinstance(registry, dict)
            or not isinstance(registry.get("modules"), list)
            or not all(isinstance(m, dict) and isinstance(m.get("id"), str)
                       and isinstance(m.get("ownedAssets"), list)
                       for m in registry["modules"])):
        raise ValueError("Help catalog requires a valid module registry")
    records = []
    prompts = sorted((root / ".github/prompts").glob("*.prompt.md"))
    if not prompts:
        raise ValueError("Help catalog requires canonical command prompts")
    for prompt in prompts:
        source = prompt.relative_to(root).as_posix()
        content = _text(root, source)
        metadata = parse_frontmatter(content, source=prompt)
        description = metadata.get("description")
        if not isinstance(description, str) or not description.strip():
            raise ValueError(f"Help command description missing or invalid: {source}")
        owners = matching_asset_owners(registry, source)
        if len(owners) != 1:
            raise ValueError(f"Help command needs exactly one owner: {source}")
        lines = content.splitlines()
        index = next((i for i, line in enumerate(lines)
                      if line.startswith("description:")), None)
        if index is None:
            raise ValueError(f"Help description source line missing: {source}")
        end = index + 1
        raw_value = lines[index].partition(":")[2].strip()
        if raw_value.startswith(("'", '"')):
            # Match the parser's quoted continuation, including unindented lines.
            while (end < len(lines) and lines[end].strip() != "---"
                   and not _quoted_scalar_complete(raw_value)):
                raw_value = " ".join(part for part in (
                    raw_value, lines[end].strip()) if part)
                end += 1
        else:
            while end < len(lines) and lines[end].startswith((" ", "\t")):
                end += 1
        identifier = prompt.name[:-len(".prompt.md")]
        records.append(_record(
            source, identifier, lines, index, end, owner=owners[0],
            platform="all", registry=registry, kind="command",
            identifier=identifier, summary=description))
    for source in GUIDES:
        lines = _text(root, source).splitlines()
        if not lines or not any(line.startswith("# ") for line in lines):
            raise ValueError(f"Help guide has no title: {source}")
        platform_context: dict[str, dict] = {}
        for heading, platform, start, end in _sections(lines):
            if heading.casefold() in {"windows installation", "macos installation"}:
                platform_context[platform] = _record(
                    source, heading, lines, start, end,
                    owner="kernel", platform=platform, registry=registry)
            table_rows = [i for i in range(start, end)
                          if lines[i].startswith("|")]
            ranges = [(start, end)]
            if table_rows:
                # Each row has independent suite eligibility; no mixed table leak.
                ranges = [(i, i + 1) for i in table_rows
                          if not re.match(r"^\|[ :|-]+\|$", lines[i])]
                if table_rows[0] > start:
                    ranges.insert(0, (start, table_rows[0]))
                if table_rows[-1] + 1 < end:
                    ranges.append((table_rows[-1] + 1, end))
            for first, last in ranges:
                if not "\n".join(lines[first:last]).strip():
                    continue
                body = "\n".join(lines[first:last])
                required = _requirements(body, "kernel", registry)
                owner = next((item for item in required if item != "kernel"), "kernel")
                record = _record(source, heading, lines, first, last,
                                 owner=owner, platform=platform, registry=registry)
                context = platform_context.get(platform)
                if context and context["start_line"] != record["start_line"]:
                    for field in ("prerequisites", "warnings"):
                        record[field] = list(dict.fromkeys(context[field] + record[field]))
                    record["context_source"] = {key: context[key] for key in (
                        "source", "heading", "start_line", "end_line")}
                    record["required_owners"] = sorted(set(record["required_owners"])
                                                        | set(context["required_owners"]))
                    record["general_setup"] = (record["general_setup"]
                                                and record["required_owners"] == ["kernel"])
                records.append(record)
    return {"schema_version": 1, "records": sorted(records, key=lambda r: r["id"])}


def refresh_catalog(root: Path, *, dry_run: bool = False) -> dict[str, Any]:
    """Build catalog and publish only outside dry-run; return generated data.

    Args:
        root: Installation checkout; e.g. ``refresh_catalog(Path('.'), dry_run=True)``.
        dry_run: Validate/extract without creating or changing any file.
    Returns:
        Deterministic catalog data.
    Raises:
        ValueError, OSError: Invalid input or failed publication.
    """
    data = build_catalog(root)
    if not dry_run:
        content = (json.dumps(data, ensure_ascii=True, indent=2) + "\n").encode()
        secure_fs.secure_write_bytes(root.resolve(), CATALOG_PATH, content)
    return data
