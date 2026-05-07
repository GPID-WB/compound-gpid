#!/usr/bin/env python3
"""cg-index — Compound GPID knowledge indexer.

Scans .cg-docs/solutions/ and produces two artifacts:
  - .cg-docs/search-index.json  (metadata-only, for quick lookups)
  - .cg-docs/DIGEST.md          (human-readable summaries, active entries only)

Usage:
    cg-index [--index] [--digest] [--all] [--root <path>] [--version] [--help]

Modes:
    --index    Build search-index.json (default when no mode flag is given).
    --digest   Build DIGEST.md.
    --all      Build both artifacts (equivalent to --index --digest).
    --root     Override the project root (defaults to cwd).
    --version  Print version and exit.

Exit codes:
    0  Success (even if some files were skipped due to parse warnings).
    1  Fatal error (no .cg-docs/solutions/ directory, unwritable output, etc.).

Requirements: Python 3.8+, stdlib only (no third-party packages).
"""

from __future__ import annotations

import sys

if sys.version_info < (3, 8):
    print(
        f"cg-index requires Python 3.8+; found {sys.version.split()[0]}",
        file=sys.stderr,
    )
    sys.exit(1)

import argparse
import json
import os
import re
import tempfile
import warnings
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Version
# ---------------------------------------------------------------------------

__version__ = "0.1.0"

# ---------------------------------------------------------------------------
# Frontmatter parser (regex-based, best-effort, no PyYAML dependency)
# ---------------------------------------------------------------------------

# Scalar YAML patterns
_BARE_TRUE = re.compile(r"^(true|yes)$", re.IGNORECASE)
_BARE_FALSE = re.compile(r"^(false|no)$", re.IGNORECASE)
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_INT_RE = re.compile(r"^-?\d+$")

# Inline list: [a, b, c] or ["a", "b"]
_INLINE_LIST_RE = re.compile(r"^\[([^\]]*)\]$")
_COMMA_SPLIT_RE = re.compile(r",(?=(?:[^\"']*[\"'][^\"']*[\"'])*[^\"']*$)")


def _coerce(value: str) -> Any:
    """Coerce a YAML scalar string to a Python type."""
    v = value.strip()
    if _BARE_TRUE.match(v):
        return True
    if _BARE_FALSE.match(v):
        return False
    if _DATE_RE.match(v):
        return v  # Keep dates as strings (ISO 8601)
    if _INT_RE.match(v):
        return int(v)
    # Strip optional surrounding quotes
    if (v.startswith('"') and v.endswith('"')) or \
       (v.startswith("'") and v.endswith("'")):
        return v[1:-1]
    return v


def _parse_inline_list(raw: str) -> Optional[List[Any]]:
    """Parse an inline YAML list like [a, b] or ["x", "y"] into a Python list.
    Returns None if the string does not look like an inline list.
    """
    m = _INLINE_LIST_RE.match(raw.strip())
    if not m:
        return None
    inner = m.group(1).strip()
    if not inner:
        return []
    # Split on commas NOT inside quotes (simple case -- no nested structures)
    items: List[Any] = []
    for item in _COMMA_SPLIT_RE.split(inner):
        items.append(_coerce(item.strip()))
    return items


def parse_frontmatter(text: str) -> Dict[str, Any]:
    """Extract YAML frontmatter from markdown text.

    Handles only the simple key: value pairs used in .cg-docs/ files:
      - Scalars (strings, booleans, integers, dates)
      - Inline lists: [a, b, c]
      - Quoted strings: "value" or 'value'
      - Multi-line arrays (dash-prefixed) — emits a warning, collects items

    Strips a leading UTF-8 BOM (\ufeff) and any leading blank lines before
    the frontmatter delimiter, since PowerShell here-strings add a leading
    \r\n before the first line of content.

    Returns an empty dict if no frontmatter block is found.
    """
    # Strip leading BOM and blank lines (PowerShell here-strings add \r\n
    # before the first content line; real files may have a UTF-8 BOM)
    clean = text.lstrip("\ufeff\r\n")
    if not clean.startswith("---"):
        return {}

    end = clean.find("\n---", 3)
    if end == -1:
        return {}

    block = clean[3:end].strip()
    result: Dict[str, Any] = {}
    current_key: Optional[str] = None
    current_list: Optional[List[str]] = None

    for line in block.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        # Continuation of a block list (  - item)
        if stripped.startswith("- ") and current_key is not None and current_list is not None:
            current_list.append(_coerce(stripped[2:].strip()))
            continue

        # Flush any in-progress block list before processing new key
        if current_list is not None:
            if current_list:  # only store non-empty block lists
                result[current_key] = current_list  # type: ignore[assignment]
            current_key = None
            current_list = None

        if ":" not in stripped:
            continue

        key, _, raw_value = stripped.partition(":")
        key = key.strip()
        raw_value = raw_value.strip()

        if not raw_value:
            # Possibly a block-list key (next lines start with "- ")
            current_key = key
            current_list = []
            warnings.warn(
                f"Frontmatter key '{key}' has a multi-line value; "
                "only simple scalars and inline lists are fully supported.",
                stacklevel=2,
            )
            continue

        inline = _parse_inline_list(raw_value)
        if inline is not None:
            result[key] = inline
        else:
            result[key] = _coerce(raw_value)

    # Flush trailing block list
    if current_list is not None and current_key is not None and current_list:
        result[current_key] = current_list

    return result


# ---------------------------------------------------------------------------
# Body parser: extract a plain-text summary (~100 words)
# ---------------------------------------------------------------------------

_HEADING_RE = re.compile(r"^#{1,6}\s+")
_FENCED_RE = re.compile(r"^```")
_PROBLEM_HEADING_RE = re.compile(r"^#{1,2}\s+Problem\b", re.IGNORECASE)


def extract_summary(text: str, max_words: int = 100) -> str:
    """Extract a ~100-word plain-text summary from markdown body.

    Strategy (in order of preference):
    1. Content immediately following a "## Problem" heading.
    2. First non-heading, non-empty prose paragraph after frontmatter.

    Skips heading lines, fenced code blocks, and blank lines at the start.
    Truncates to max_words words, appending "..." if truncated.
    """
    # Strip leading BOM and blank lines (mirrors parse_frontmatter)
    clean = text.lstrip("\ufeff\r\n")

    # Strip frontmatter
    body = clean
    if clean.startswith("---"):
        end = clean.find("\n---", 3)
        if end != -1:
            body = clean[end + 4:].lstrip("\n")

    lines = body.splitlines()

    # --- Pass 1: look for ## Problem section ---
    problem_lines: List[str] = []
    in_problem = False
    in_fence = False

    for line in lines:
        if _FENCED_RE.match(line):
            in_fence = not in_fence
        if in_fence:
            continue
        if _HEADING_RE.match(line):
            if in_problem:
                break  # next heading ends the section
            if _PROBLEM_HEADING_RE.match(line):
                in_problem = True
            continue
        if in_problem and line.strip():
            problem_lines.append(line.strip())

    if problem_lines:
        return _truncate(" ".join(problem_lines), max_words)

    # --- Pass 2: first non-heading prose paragraph ---
    prose_lines: List[str] = []
    in_fence = False
    in_prose = False

    for line in lines:
        if _FENCED_RE.match(line):
            in_fence = not in_fence
        if in_fence:
            continue
        if _HEADING_RE.match(line):
            if in_prose:
                break
            continue
        stripped = line.strip()
        if stripped:
            in_prose = True
            prose_lines.append(stripped)
        elif in_prose:
            break  # blank line ends a paragraph

    if prose_lines:
        return _truncate(" ".join(prose_lines), max_words)

    return ""


def _truncate(text: str, max_words: int) -> str:
    """Truncate text to at most max_words whitespace-delimited words, appending '...' if truncated."""
    words = text.split()
    if len(words) <= max_words:
        return text
    return " ".join(words[:max_words]) + "..."


# ---------------------------------------------------------------------------
# Solution entry
# ---------------------------------------------------------------------------

@dataclass
class SolutionEntry:
    """Parsed representation of a single .cg-docs/solutions/ file."""
    path: Path
    frontmatter: Dict[str, Any]
    summary: str

    @property
    def rel_path(self) -> str:
        """Path relative to the repo root (forward slashes)."""
        return self.path.as_posix()

    @property
    def slug(self) -> str:
        """Filename stem, used as the unique identifier across the index."""
        return self.path.stem

    @property
    def date_str(self) -> str:
        """ISO date string from frontmatter; empty string if absent."""
        return str(self.frontmatter.get("date", ""))

    @property
    def title(self) -> str:
        """Frontmatter title, falling back to the filename stem."""
        return str(self.frontmatter.get("title", self.slug))

    @property
    def category(self) -> str:
        """Derived from the parent directory name."""
        return self.path.parent.name

    @property
    def status(self) -> str:
        """Frontmatter status lowercased; empty string if absent."""
        return str(self.frontmatter.get("status", "")).lower()

    @property
    def tags(self) -> List[str]:
        """List of tag strings; empty list if frontmatter 'tags' is absent or not a list."""
        raw = self.frontmatter.get("tags", [])
        if isinstance(raw, list):
            return [str(t) for t in raw]
        return []

    def to_index_record(self) -> Dict[str, Any]:
        """Return a dict for one record in search-index.json.

        Keys: slug, title, date, category, status, tags, path.
        """
        return {
            "slug":     self.slug,
            "title":    self.title,
            "date":     self.date_str,
            "category": self.category,
            "status":   self.status,
            "tags":     self.tags,
            "path":     self.rel_path,
        }

    def to_digest_block(self) -> str:
        """Return a markdown block for DIGEST.md.

        Format: ## heading, metadata lines (date, category, status, tags, path),
        optional summary paragraph, trailing blank line.
        """
        lines = [
            f"## {self.title}",
            "",
            f"date: {self.date_str}",
            f"category: {self.category}",
            f"status: {self.status}",
        ]
        if self.tags:
            lines.append(f"tags: {', '.join(self.tags)}")
        lines.append(f"path: {self.rel_path}")
        if self.summary:
            lines.append("")
            lines.append(self.summary)
        lines.append("")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Scanner
# ---------------------------------------------------------------------------

def scan_solutions(solutions_dir: Path, root: Path) -> List[SolutionEntry]:
    """Recursively scan solutions_dir for *.md files and return parsed entries.

    Files are skipped (with a warning) if:
      - They cannot be read.
      - They have no parseable frontmatter.

    Returns entries sorted by date descending, then title ascending.
    Low probability of slug collision (two different categories with the same
    filename stem); if it happens, a warning is emitted with both paths.
    """
    entries: List[SolutionEntry] = []
    seen_slugs: Dict[str, Path] = {}

    for md_file in sorted(solutions_dir.rglob("*.md")):
        try:
            text = md_file.read_text(encoding="utf-8")
        except OSError as exc:
            warnings.warn(f"Skipping {md_file}: {exc}")
            continue

        fm = parse_frontmatter(text)
        if not fm:
            warnings.warn(
                f"Skipping {md_file}: no frontmatter found. "
                "Add a --- block with at least a 'title' and 'date' field."
            )
            continue

        missing_fields = [f for f in ("title", "date") if not fm.get(f)]
        if missing_fields:
            warnings.warn(
                f"{md_file}: missing required field(s): {', '.join(missing_fields)}. "
                "Add them to prevent silent fallback behaviour."
            )

        summary = extract_summary(text)

        # Make path relative to repo root
        try:
            rel = md_file.relative_to(root)
        except ValueError:
            rel = md_file

        entry = SolutionEntry(path=rel, frontmatter=fm, summary=summary)

        # Slug collision check
        if entry.slug in seen_slugs:
            warnings.warn(
                f"Slug collision: '{entry.slug}' appears in both "
                f"'{seen_slugs[entry.slug]}' and '{rel}'. "
                "Consider renaming one file to make slugs unique across all categories."
            )
        seen_slugs[entry.slug] = rel

        entries.append(entry)

    # Sort: date descending (empty dates sort last), then title ascending
    def sort_key(e: SolutionEntry) -> Tuple[int, str]:
        d = e.date_str if e.date_str else "0000-00-00"
        try:
            return (-int(d.replace("-", "")), e.title.lower())
        except ValueError:
            return (0, e.title.lower())

    entries.sort(key=sort_key)
    return entries


# ---------------------------------------------------------------------------
# Output builders
# ---------------------------------------------------------------------------

def _write_atomic(path: Path, content: str) -> None:
    """Write content to path atomically using a temp file + os.replace().

    Prevents partially written files on process kill or other interruptions.
    """
    fd, tmp_path = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(content)
        os.replace(tmp_path, path)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def build_index(entries: List[SolutionEntry], out_path: Path) -> None:
    """Write search-index.json (metadata only, all statuses included)."""
    records = [e.to_index_record() for e in entries]
    payload = {
        "generated": date.today().isoformat(),
        "count": len(records),
        "entries": records,
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    _write_atomic(out_path, json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    print(f"[cg-index] Wrote {len(records)} entries to {out_path}")


def build_digest(entries: List[SolutionEntry], out_path: Path) -> None:
    """Write DIGEST.md (active entries only, one-field-per-line format)."""
    for e in entries:
        if e.status == "":
            warnings.warn(
                f"{e.rel_path}: no 'status' field; treating as active in DIGEST.",
                stacklevel=2,
            )
    active = [e for e in entries if e.status in ("active", "")]
    lines = [
        "# Compound GPID — Solution Digest",
        "",
        f"_Generated {date.today().isoformat()} · {len(active)} active solutions_",
        "",
    ]
    for entry in active:
        lines.append(entry.to_digest_block())

    out_path.parent.mkdir(parents=True, exist_ok=True)
    _write_atomic(out_path, "\n".join(lines))
    print(f"[cg-index] Wrote {len(active)} active entries to {out_path}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_arg_parser() -> argparse.ArgumentParser:
    """Build and return the CLI argument parser for cg-index."""
    parser = argparse.ArgumentParser(
        prog="cg-index",
        description="Compound GPID knowledge indexer.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--index",
        action="store_true",
        help="Build search-index.json (metadata only).",
    )
    parser.add_argument(
        "--digest",
        action="store_true",
        help="Build DIGEST.md (active entries, human-readable summaries).",
    )
    parser.add_argument(
        "--all",
        dest="all_",
        action="store_true",
        help="Build both search-index.json and DIGEST.md.",
    )
    parser.add_argument(
        "--root",
        metavar="PATH",
        default=None,
        help="Project root directory (defaults to current working directory).",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"cg-index {__version__}",
    )
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    """Run cg-index CLI.

    argv defaults to sys.argv[1:] when None. Returns an int exit code
    (0 on success, 1 on fatal error).
    """
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    # Resolve root
    root = Path(args.root).resolve() if args.root else Path.cwd()

    solutions_dir = root / ".cg-docs" / "solutions"
    if not solutions_dir.is_dir():
        print(
            f"[cg-index] ERROR: {solutions_dir} does not exist.\n"
            "Run cg-index from a project root containing a .cg-docs/solutions/ directory.",
            file=sys.stderr,
        )
        return 1

    # Default: --index when no mode flag is given
    do_index  = args.index or args.all_
    do_digest = args.digest or args.all_
    if not do_index and not do_digest:
        do_index = True

    try:
        with warnings.catch_warnings(record=True) as captured:
            warnings.simplefilter("always")
            entries = scan_solutions(solutions_dir, root)
            for w in captured:
                print(f"[cg-index] WARNING: {w.message}", file=sys.stderr)
    except OSError as exc:
        print(f"[cg-index] ERROR: {exc}", file=sys.stderr)
        return 1

    try:
        if do_index:
            build_index(entries, root / ".cg-docs" / "search-index.json")
        if do_digest:
            build_digest(entries, root / ".cg-docs" / "DIGEST.md")
    except OSError as exc:
        print(f"[cg-index] ERROR writing output: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
