#!/usr/bin/env python3
"""cg-migrate-config — Add the modular ``suites:`` field to compound-gpid.local.md.

Idempotent and backward-compatible: an existing config without ``suites:`` is
treated as ``cg``-only and migrated non-destructively; re-running is a no-op.

Usage:
    python3 scripts/cg_migrate_config.py [--root <path>] [--check]

Exit codes:
    0  Success (migrated, no-op, or check passed).
    1  Error (file missing and not check, or write failed).
"""
from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

LOCAL_CONFIG_PATH = "compound-gpid.local.md"
SUITES_DEFAULT = "[cg]"


@dataclass
class MigrationResult:
    changed: bool
    error: str | None = None


def _frontmatter_bounds(text: str) -> tuple[int, int] | None:
    """Return (start, end) offsets of the YAML frontmatter block, or None."""
    if not text.lstrip("\ufeff\r\n").startswith("---"):
        return None
    start = text.index("---")
    end_marker = text.find("\n---", start + 3)
    if end_marker == -1:
        return None
    return start, end_marker


def _has_suites(frontmatter: str) -> bool:
    for line in frontmatter.splitlines():
        if line.startswith("suites:"):
            return True
    return False


def migrate_file_text(text: str) -> tuple[str, bool]:
    """Return (new_text, changed). Non-destructive; preserves all fields."""
    bounds = _frontmatter_bounds(text)
    if bounds is None:
        return text, False
    start, end = bounds
    frontmatter = text[start:end]
    if _has_suites(frontmatter):
        return text, False
    insert = f"\nsuites: {SUITES_DEFAULT}\n"
    new_text = text[:end] + insert + text[end:]
    return new_text, True


def migrate_local_config(path: Path) -> MigrationResult:
    """Migrate one compound-gpid.local.md path. Returns a MigrationResult."""
    if not path.exists():
        return MigrationResult(changed=False, error=f"config file not found: {path}")
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        return MigrationResult(changed=False, error=f"could not read config: {exc}")
    if bounds := _frontmatter_bounds(text):
        if not _has_suites(text[bounds[0]:bounds[1]]):
            new_text, _ = migrate_file_text(text)
            try:
                path.write_text(new_text, encoding="utf-8")
            except OSError as exc:
                return MigrationResult(changed=False, error=f"could not write config: {exc}")
            return MigrationResult(changed=True)
    return MigrationResult(changed=False)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Migrate a project config to the modular schema.")
    parser.add_argument("--root", default=".", help="Project root directory (default: .)")
    parser.add_argument("--check", action="store_true", help="Check mode: report whether migration is needed, do not write")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    path = root / LOCAL_CONFIG_PATH
    if not path.exists():
        print(f"Error: {LOCAL_CONFIG_PATH} not found at {root}", file=sys.stderr)
        return 2 if not args.check else 0

    text = path.read_text(encoding="utf-8")
    bounds = _frontmatter_bounds(text)
    needs = bounds is not None and not _has_suites(text[bounds[0]:bounds[1]])
    if args.check:
        print("migration-needed" if needs else "up-to-date")
        return 0 if not needs else 0

    result = migrate_local_config(path)
    print("migrated" if result.changed else "no-op" if not result.error else "error")
    if result.error:
        print(f"Error: {result.error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
