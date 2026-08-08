"""Tests for compound-gpid.local.md modular-schema config migration.

Run from repo root:
    python -m pytest scripts/tests/test_config_migration.py -q
"""
from __future__ import annotations

from pathlib import Path

import cg_migrate_config as migration

LEGACY_CONFIG = """---
language: "both"
project-type: "tool"
review-depth: "thorough"
r-syntax: "data.table-collapse"
created: "2026-03-04"
cg-schema-version: "2026-04-07-r-syntax-dialect"
---
# Compound GPID — Project Config

This file configures Compound GPID for this project.
"""

MODERN_CONFIG = """---
language: "both"
project-type: "tool"
review-depth: "thorough"
suites: [cg, cr]
created: "2026-03-04"
cg-schema-version: "2026-04-07-r-syntax-dialect"
---
# Compound GPID — Project Config
"""


def _write(root: Path, content: str = LEGACY_CONFIG) -> Path:
    path = root / "compound-gpid.local.md"
    path.write_text(content, encoding="utf-8")
    return path


def _read_suites(content: str) -> str | None:
    for line in content.splitlines():
        if line.startswith("suites:"):
            return line.partition(":")[2].strip()
    return None


class TestMigration:
    def test_legacy_config_gains_cg_default(self, tmp_path: Path) -> None:
        path = _write(tmp_path)
        result = migration.migrate_local_config(path)
        assert result.changed is True
        content = path.read_text(encoding="utf-8")
        assert _read_suites(content) == "[cg]"

    def test_rerun_is_noop(self, tmp_path: Path) -> None:
        path = _write(tmp_path)
        migration.migrate_local_config(path)
        first = path.read_text(encoding="utf-8")
        result = migration.migrate_local_config(path)
        assert result.changed is False
        assert path.read_text(encoding="utf-8") == first

    def test_config_already_has_suites_unchanged(self, tmp_path: Path) -> None:
        path = _write(tmp_path, MODERN_CONFIG)
        result = migration.migrate_local_config(path)
        assert result.changed is False
        assert _read_suites(path.read_text(encoding="utf-8")) == "[cg, cr]"

    def test_other_frontmatter_fields_preserved(self, tmp_path: Path) -> None:
        path = _write(tmp_path)
        migration.migrate_local_config(path)
        content = path.read_text(encoding="utf-8")
        for field in ("language", "project-type", "review-depth", "r-syntax", "created", "cg-schema-version"):
            assert f"{field}:" in content, f"field lost: {field}"
        assert "# Compound GPID — Project Config" in content

    def test_missing_file_reports_no_change(self, tmp_path: Path) -> None:
        missing = tmp_path / "compound-gpid.local.md"
        result = migration.migrate_local_config(missing)
        assert result.changed is False
        assert result.error is not None
