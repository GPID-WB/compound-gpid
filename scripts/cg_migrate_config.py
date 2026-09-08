#!/usr/bin/env python3
"""cg-migrate-config — Migrate compound-gpid.local.md to the strict schema.

Idempotent and backward-compatible: an existing config without a ``suites:``
field is treated as ``cg``-only (the only documented absent-``suites`` legacy
default) and migrated non-destructively; re-running is a no-op. Malformed or
unrecognized config inputs fail loudly instead of being silently migrated, and
the migration emits a ``config-schema-version`` marker so compatibility expiry
becomes an explicit error rather than an implicit fallback.

Usage:
    python3 scripts/cg_migrate_config.py [--root <path>] [--check]

Exit codes:
    0  Success (migrated, no-op, or check found up-to-date config).
    1  Check mode found migration is needed, strict validation failed, or a
       write/read failure occurred.
    2  Config file is missing.
"""
from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

from parsing_utils import parse_strict_config

LOCAL_CONFIG_PATH = "compound-gpid.local.md"
SUITES_DEFAULT = "[cg]"
CONFIG_SCHEMA_VERSION_FIELD = "config-schema-version"
SUPPORTED_CONFIG_SCHEMA_VERSION = "2"


@dataclass
class MigrationResult:
    changed: bool
    error: str | None = None


def _frontmatter_bounds(text: str) -> tuple[int, int] | None:
    """Return (start, end) offsets of the YAML frontmatter block, or None."""
    stripped = text.lstrip("\ufeff\r\n")
    if not stripped.startswith("---"):
        return None
    start = text.index("---")
    end_marker = text.find("\n---", start + 3)
    if end_marker == -1:
        return None
    return start, end_marker


def migrate_file_text(text: str) -> tuple[str, bool, str | None]:
    """Return (new_text, changed, error). Non-destructive; preserves all fields."""
    bounds = _frontmatter_bounds(text)
    if bounds is None:
        return text, False, "missing top-level frontmatter delimiter '---'"
    start, end = bounds
    parsed = parse_strict_config(text)
    if parsed.errors:
        return text, False, "strict config validation failed: " + parsed.errors[0]

    version = parsed.scalar(CONFIG_SCHEMA_VERSION_FIELD)
    if version is not None and version != SUPPORTED_CONFIG_SCHEMA_VERSION:
        return (
            text,
            False,
            f"config schema version {version!r} is not the supported version "
            f"({SUPPORTED_CONFIG_SCHEMA_VERSION}); migrate explicitly before strict resolution",
        )

    insert: list[str] = []
    if not parsed.suites:
        insert.append(f"suites: {SUITES_DEFAULT}")
    if version is None:
        insert.append(f'{CONFIG_SCHEMA_VERSION_FIELD}: "{SUPPORTED_CONFIG_SCHEMA_VERSION}"')
    if not insert:
        return text, False, None
    new_text = text[:end] + "\n" + "\n".join(insert) + "\n" + text[end:]
    return new_text, True, None


def migrate_local_config(path: Path) -> MigrationResult:
    """Migrate one compound-gpid.local.md path. Returns a MigrationResult."""
    if not path.exists():
        return MigrationResult(changed=False, error=f"config file not found: {path}")
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        return MigrationResult(changed=False, error=f"could not read config: {exc}")
    new_text, changed, error = migrate_file_text(text)
    if error:
        return MigrationResult(changed=False, error=error)
    if not changed:
        return MigrationResult(changed=False)
    try:
        path.write_text(new_text, encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        return MigrationResult(changed=False, error=f"could not write config: {exc}")
    return MigrationResult(changed=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Migrate a project config to the strict schema.")
    parser.add_argument("--root", default=".", help="Project root directory (default: .)")
    parser.add_argument("--check", action="store_true", help="Check mode: report whether migration is needed, do not write")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    path = root / LOCAL_CONFIG_PATH
    if not path.exists():
        print(f"Error: {LOCAL_CONFIG_PATH} not found at {root}", file=sys.stderr)
        return 2

    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        print(f"Error: could not read config: {exc}", file=sys.stderr)
        return 1
    new_text, changed, error = migrate_file_text(text)
    if error:
        print("invalid", file=sys.stderr)
        print(f"Error: {error}", file=sys.stderr)
        return 1
    needs = changed
    if args.check:
        print("migration-needed" if needs else "up-to-date")
        return 1 if needs else 0

    result = migrate_local_config(path)
    print("migrated" if result.changed else "no-op" if not result.error else "error")
    if result.error:
        print(f"Error: {result.error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
