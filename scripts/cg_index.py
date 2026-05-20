#!/usr/bin/env python3
"""cg-index — Compound GPID knowledge indexer.

Scans .cg-docs/ artifacts and roadmap.json, then builds a rich multi-file
brain knowledge index.

Usage:
    cg-index [--brain] [--root <path>] [--version] [--help]

    # Legacy (deprecated — use --brain):
    cg-index [--index] [--digest] [--all] [--root <path>]

Modes:
    --brain    Build the full brain knowledge index: BRAIN.md, BRAIN-01.md,
               BRAIN-log.md, brain-index.json.  Also removes legacy
               DIGEST.md and search-index.json on success.
    --index    (DEPRECATED) Build search-index.json only.
    --digest   (DEPRECATED) Build DIGEST.md only.
    --all      (DEPRECATED) Alias for --brain.
    --root     Override the project root (defaults to cwd).
    --version  Print version and exit.

Exit codes:
    0  Success (even if some files were skipped due to parse warnings).
    1  Fatal error (no .cg-docs/ directory, unwritable output, etc.).

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
import warnings
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Version — imported from brain to avoid duplication (architecture P1.11 fix)
# ---------------------------------------------------------------------------

# __version__ defined in brain/__init__.py; imported lazily after sys.path bootstrap below.

# ---------------------------------------------------------------------------
# sys.path bootstrap — brain sub-modules live in scripts/brain/
# ---------------------------------------------------------------------------

_scripts_dir = str(Path(__file__).parent)
if _scripts_dir not in sys.path:
    sys.path.insert(0, _scripts_dir)

from brain.utils import (  # noqa: E402
    _coerce,
    _parse_inline_list,
    parse_frontmatter,
    extract_summary,
    _write_atomic,
    _truncate,
)
from brain import __version__  # noqa: E402


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

    Files are skipped (with a warning) if they cannot be read, have no
    parseable frontmatter, or are missing required ``title``/``date`` fields.
    Slug collisions (two files with the same stem in different categories)
    emit a warning.

    Args:
        solutions_dir: Root directory of the solutions tree (e.g.
            ``.cg-docs/solutions/``).
        root: Project root — used to compute relative paths in output.

    Returns:
        List of :class:`SolutionEntry` objects sorted by date descending,
        then title ascending.  Empty-date entries sort last.

    Example:
        >>> from pathlib import Path
        >>> from scripts.cg_index import scan_solutions
        >>> entries = scan_solutions(Path(".cg-docs/solutions"), Path("."))
        >>> print(len(entries), "solutions found")
    """
    entries: List[SolutionEntry] = []
    seen_slugs: Dict[str, Path] = {}

    for md_file in sorted(solutions_dir.rglob("*.md")):
        try:
            text = md_file.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            warnings.warn(f"Skipping {md_file}: {exc}", stacklevel=2)
            continue

        fm = parse_frontmatter(text)
        if not fm:
            warnings.warn(
                f"Skipping {md_file}: no frontmatter found. "
                "Add a --- block with at least a 'title' and 'date' field.",
                stacklevel=2,
            )
            continue

        missing_fields = [f for f in ("title", "date") if not fm.get(f)]
        if missing_fields:
            warnings.warn(
                f"{md_file}: missing required field(s): {', '.join(missing_fields)}. "
                "Add them to prevent silent fallback behaviour.",
                stacklevel=2,
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
                "Consider renaming one file to make slugs unique across all categories.",
                stacklevel=2,
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

def build_index(entries: List[SolutionEntry], out_path: Path) -> None:
    """Write ``search-index.json`` containing metadata for all entries.

    All entries are included regardless of status.  The output is an atomic
    write via a temp file + ``os.replace()`` to prevent partial files.

    Args:
        entries: List of :class:`SolutionEntry` objects to serialise.
        out_path: Destination path for ``search-index.json``.
            Parent directories are created automatically.

    Returns:
        None.  Prints a confirmation line to stdout.

    Example:
        >>> build_index(entries, Path(".cg-docs/search-index.json"))
    """
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
    """Write ``DIGEST.md`` containing only active solution entries.

    Entries with ``status: active`` or no status field are included.  All
    other statuses (``archived``, ``draft``, etc.) are silently excluded.
    Entries with no status field emit a warning.

    Args:
        entries: Full list of :class:`SolutionEntry` objects.
        out_path: Destination path for ``DIGEST.md``.
            Parent directories are created automatically.

    Returns:
        None.  Prints a confirmation line to stdout.

    Example:
        >>> build_digest(entries, Path(".cg-docs/DIGEST.md"))
    """
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
    """Build and return the CLI argument parser for ``cg-index``.

    Returns:
        Configured :class:`argparse.ArgumentParser` with ``--brain``,
        ``--index``, ``--digest``, ``--all``, ``--root``, and ``--version``
        flags.

    Example:
        >>> parser = build_arg_parser()
        >>> args = parser.parse_args(["--brain"])
        >>> args.brain
        True
    """
    parser = argparse.ArgumentParser(
        prog="cg-index",
        description="Compound GPID knowledge indexer.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--brain",
        action="store_true",
        help="Build the full brain knowledge index (BRAIN.md, BRAIN-log.md, brain-index.json).",
    )
    parser.add_argument(
        "--index",
        action="store_true",
        help="[DEPRECATED] Build search-index.json (metadata only). Use --brain instead.",
    )
    parser.add_argument(
        "--digest",
        action="store_true",
        help="[DEPRECATED] Build DIGEST.md (active entries). Use --brain instead.",
    )
    parser.add_argument(
        "--all",
        dest="all_",
        action="store_true",
        help="[DEPRECATED] Alias for --brain. Use --brain instead.",
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
    """Run the ``cg-index`` CLI.

    Args:
        argv: Argument list to parse.  Defaults to ``sys.argv[1:]`` when
            ``None``.

    Returns:
        Integer exit code: ``0`` on success, ``1`` on fatal error.

    Example:
        >>> import sys
        >>> sys.exit(main(["--brain"]))
    """
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    # Resolve root
    root = Path(args.root).resolve() if args.root else Path.cwd()

    # --all is deprecated; redirect to --brain
    do_brain = getattr(args, "brain", False) or args.all_
    do_index = args.index
    do_digest = args.digest

    # Emit deprecation notices for legacy flags
    for flag, condition in (("--all", args.all_), ("--index", args.index), ("--digest", args.digest)):
        if condition:
            print(
                f"[cg-index] DEPRECATED: {flag} is deprecated. Use --brain instead.",
                file=sys.stderr,
            )

    # When --all is passed, suppress the legacy index/digest runs — brain only
    if args.all_:
        do_index = False
        do_digest = False

    # -----------------------------------------------------------------------
    # Brain mode (--brain or --all redirect)
    # -----------------------------------------------------------------------
    if do_brain:
        cg_docs_dir = root / ".cg-docs"
        if not cg_docs_dir.is_dir():
            print(
                f"[cg-index] ERROR: {cg_docs_dir} does not exist.\n"
                "Run cg-index from a project root containing a .cg-docs/ directory.",
                file=sys.stderr,
            )
            return 1
        try:
            from brain import build_brain
            from brain.renderer import render_brain
            with warnings.catch_warnings(record=True) as captured:
                warnings.simplefilter("always")
                data = build_brain(root)
                render_brain(data, out_dir=cg_docs_dir)
            for w in captured:
                print(f"[cg-index] WARNING: {w.message!s}", file=sys.stderr)
            print(
                f"[cg-index] Brain index written to {cg_docs_dir} "
                f"({len(data.entities)} entities, {len(data.topics)} topics, "
                f"{len(data.edges)} edges)"
            )
        except ImportError as exc:
            print(
                f"[cg-index] ERROR: brain package not available ({exc}).\n"
                "Reinstall compound-gpid or run: pip install -e scripts/",
                file=sys.stderr,
            )
            return 1
        except OSError as exc:
            print(f"[cg-index] ERROR: {exc}", file=sys.stderr)
            return 1
        # Delete legacy files outside the brain-build try block so that a
        # locked or missing legacy file does not cause a false exit-1 after
        # a successful brain write.
        for legacy_name in ("DIGEST.md", "search-index.json"):
            legacy_path = cg_docs_dir / legacy_name
            if legacy_path.exists():
                try:
                    legacy_path.unlink()
                    print(f"[cg-index] Removed legacy {legacy_name}")
                except OSError as exc:
                    print(
                        f"[cg-index] WARNING: could not remove legacy {legacy_name}: {exc}",
                        file=sys.stderr,
                    )
        return 0

    # -----------------------------------------------------------------------
    # Legacy mode (--index / --digest / default)
    # -----------------------------------------------------------------------
    solutions_dir = root / ".cg-docs" / "solutions"
    if not solutions_dir.is_dir():
        print(
            f"[cg-index] ERROR: {solutions_dir} does not exist.\n"
            "Run cg-index from a project root containing a .cg-docs/solutions/ directory.",
            file=sys.stderr,
        )
        return 1

    # Default: --index when no mode flag is given
    if not do_index and not do_digest:
        do_index = True

    try:
        with warnings.catch_warnings(record=True) as captured:
            warnings.simplefilter("always")
            entries = scan_solutions(solutions_dir, root)
            if do_index:
                build_index(entries, root / ".cg-docs" / "search-index.json")
            if do_digest:
                build_digest(entries, root / ".cg-docs" / "DIGEST.md")
        for w in captured:
            print(f"[cg-index] WARNING: {w.message!s}", file=sys.stderr)
    except OSError as exc:
        print(f"[cg-index] ERROR: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
