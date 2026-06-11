"""Legacy search-index and digest builders for cg-index.

These helpers preserve the deprecated ``--index`` and ``--digest`` modes while
keeping the main ``cg_index.py`` entry point focused on CLI orchestration.
"""
from __future__ import annotations

import json
import warnings
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

from brain.utils import extract_summary, parse_frontmatter, write_atomic


@dataclass
class SolutionEntry:
    """Parsed representation of a single ``.cg-docs/solutions/`` file."""

    path: Path
    frontmatter: dict[str, Any]
    summary: str

    @property
    def rel_path(self) -> str:
        """Path relative to the repo root, using forward slashes."""
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
    def tags(self) -> list[str]:
        """List of tag strings, or an empty list when absent."""
        raw = self.frontmatter.get("tags", [])
        if isinstance(raw, list):
            return [str(t) for t in raw]
        return []

    def to_index_record(self) -> dict[str, Any]:
        """Return a ``search-index.json`` record."""
        return {
            "slug": self.slug,
            "title": self.title,
            "date": self.date_str,
            "category": self.category,
            "status": self.status,
            "tags": self.tags,
            "path": self.rel_path,
        }

    def to_digest_block(self) -> str:
        """Return a markdown block for ``DIGEST.md``."""
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


def _relative_solution_path(md_file: Path, root: Path) -> Path | None:
    """Return the repo-relative path, skipping out-of-tree symlink targets."""
    try:
        resolved = md_file.resolve(strict=True)
        resolved.relative_to(root.resolve(strict=True))
        return md_file.relative_to(root)
    except ValueError:
        warnings.warn(
            f"Skipping {md_file}: resolved path is outside the project root.",
            stacklevel=3,
        )
        return None
    except OSError as exc:
        warnings.warn(f"Skipping {md_file}: {exc}", stacklevel=3)
        return None


def scan_solutions(
    solutions_dir: Path,
    root: Path,
    *,
    want_summary: bool = False,
) -> list[SolutionEntry]:
    """Recursively scan solution markdown files and return parsed entries."""
    entries: list[SolutionEntry] = []
    seen_slugs: dict[str, Path] = {}

    for md_file in sorted(solutions_dir.rglob("*.md")):
        rel = _relative_solution_path(md_file, root)
        if rel is None:
            continue

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

        entry = SolutionEntry(
            path=rel,
            frontmatter=fm,
            summary=extract_summary(text) if want_summary else "",
        )

        if entry.slug in seen_slugs:
            warnings.warn(
                f"Slug collision: '{entry.slug}' appears in both "
                f"'{seen_slugs[entry.slug]}' and '{rel}'. "
                "Consider renaming one file to make slugs unique across all categories.",
                stacklevel=2,
            )
        seen_slugs[entry.slug] = rel
        entries.append(entry)

    def sort_key(entry: SolutionEntry) -> tuple[int, str]:
        date_str = entry.date_str if entry.date_str else "0000-00-00"
        try:
            return (-int(date_str.replace("-", "")), entry.title.lower())
        except ValueError:
            return (0, entry.title.lower())

    entries.sort(key=sort_key)
    return entries


def build_index(entries: list[SolutionEntry], out_path: Path) -> None:
    """Write ``search-index.json`` containing metadata for all entries."""
    records = [entry.to_index_record() for entry in entries]
    payload = {
        "generated": date.today().isoformat(),
        "count": len(records),
        "entries": records,
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    write_atomic(out_path, json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    print(f"[cg-index] Wrote {len(records)} entries to {out_path}")


def build_digest(entries: list[SolutionEntry], out_path: Path) -> None:
    """Write ``DIGEST.md`` containing active solution entries."""
    for entry in entries:
        if entry.status == "":
            warnings.warn(
                f"{entry.rel_path}: no 'status' field; treating as active in DIGEST.",
                stacklevel=2,
            )
    active = [entry for entry in entries if entry.status in ("active", "")]
    lines = [
        "# Compound GPID — Solution Digest",
        "",
        f"_Generated {date.today().isoformat()} · {len(active)} active solutions_",
        "",
    ]
    for entry in active:
        lines.append(entry.to_digest_block())

    out_path.parent.mkdir(parents=True, exist_ok=True)
    write_atomic(out_path, "\n".join(lines))
    print(f"[cg-index] Wrote {len(active)} active entries to {out_path}")
