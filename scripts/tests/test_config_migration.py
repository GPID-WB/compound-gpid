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

CURRENT_CONFIG = """---
language: "both"
project-type: "tool"
review-depth: "thorough"
suites: [cg, cr]
created: "2026-03-04"
cg-schema-version: "2026-04-07-r-syntax-dialect"
config-schema-version: "2"
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
    def test_legacy_config_gains_cg_default_and_version_marker(self, tmp_path: Path) -> None:
        path = _write(tmp_path)
        result = migration.migrate_local_config(path)
        assert result.changed is True
        content = path.read_text(encoding="utf-8")
        assert _read_suites(content) == "[cg]"
        assert migration.CONFIG_SCHEMA_VERSION_FIELD + ":" in content

    def test_rerun_is_noop(self, tmp_path: Path) -> None:
        path = _write(tmp_path)
        migration.migrate_local_config(path)
        first = path.read_text(encoding="utf-8")
        result = migration.migrate_local_config(path)
        assert result.changed is False
        assert path.read_text(encoding="utf-8") == first

    def test_modern_suites_config_gains_only_version_marker(self, tmp_path: Path) -> None:
        path = _write(tmp_path, MODERN_CONFIG)
        result = migration.migrate_local_config(path)
        assert result.changed is True
        content = path.read_text(encoding="utf-8")
        assert _read_suites(content) == "[cg, cr]"
        assert migration.CONFIG_SCHEMA_VERSION_FIELD + ":" in content

    def test_current_config_is_noop(self, tmp_path: Path) -> None:
        path = _write(tmp_path, CURRENT_CONFIG)
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

    def test_advisory_fence_does_not_hide_existing_suite_selection(self, tmp_path: Path) -> None:
        config = """---
language: "both"
model-advisory:
  notes: |
    ---
suites: [cr]
---
# config
"""
        path = _write(tmp_path, config)

        result = migration.migrate_local_config(path)

        assert result.changed is True
        content = path.read_text(encoding="utf-8")
        assert content.count("suites:") == 1
        assert _read_suites(content) == "[cr]"
        assert migration.CONFIG_SCHEMA_VERSION_FIELD + ":" in content

    def test_nested_advisory_schema_marker_does_not_suppress_migration(self, tmp_path: Path) -> None:
        config = """---
language: "both"
model-advisory:
  config-schema-version: "2"
suites: [cg]
---
# config
"""
        path = _write(tmp_path, config)

        result = migration.migrate_local_config(path)

        assert result.changed is True
        top_level_markers = [
            line for line in path.read_text(encoding="utf-8").splitlines()
            if line.startswith("config-schema-version:")
        ]
        assert top_level_markers == ['config-schema-version: "2"']

    def test_malformed_present_suites_fails_closed(self, tmp_path: Path) -> None:
        for bad_suites in ("suites:", "suites: []", 'suites: "cg"', "suites: [cg, cg]"):
            config = LEGACY_CONFIG.replace("review-depth: \"thorough\"\n", f"review-depth: \"thorough\"\n{bad_suites}\n")
            path = _write(tmp_path, config)
            result = migration.migrate_local_config(path)
            assert result.changed is False
            assert result.error is not None, f"expected failure for {bad_suites!r}"
            assert path.read_text(encoding="utf-8") == config

    def test_unrecognized_key_fails_closed(self, tmp_path: Path) -> None:
        config = LEGACY_CONFIG.replace("r-syntax:", "bogus-key:", 1)
        path = _write(tmp_path, config)
        result = migration.migrate_local_config(path)
        assert result.changed is False
        assert "unrecognized config key" in (result.error or "")

    def test_newer_config_schema_version_fails_explicitly(self, tmp_path: Path) -> None:
        config = CURRENT_CONFIG.replace('config-schema-version: "2"', 'config-schema-version: "9"')
        path = _write(tmp_path, config)
        result = migration.migrate_local_config(path)
        assert result.changed is False
        assert "is not the supported version" in (result.error or "")

    def test_missing_file_reports_no_change(self, tmp_path: Path) -> None:
        missing = tmp_path / "compound-gpid.local.md"
        result = migration.migrate_local_config(missing)
        assert result.changed is False
        assert result.error is not None


class TestMigrationCli:
    def test_check_reports_needed_with_exit_1(self, tmp_path: Path, capsys) -> None:
        _write(tmp_path, LEGACY_CONFIG)
        assert migration.main(["--root", str(tmp_path), "--check"]) == 1
        assert "migration-needed" in capsys.readouterr().out

    def test_check_reports_up_to_date_with_exit_0(self, tmp_path: Path, capsys) -> None:
        _write(tmp_path, CURRENT_CONFIG)
        assert migration.main(["--root", str(tmp_path), "--check"]) == 0
        assert "up-to-date" in capsys.readouterr().out

    def test_missing_file_returns_exit_2(self, tmp_path: Path, capsys) -> None:
        assert migration.main(["--root", str(tmp_path), "--check"]) == 2
        assert "not found" in capsys.readouterr().err

    def test_no_frontmatter_config_fails_closed(self, tmp_path: Path) -> None:
        path = _write(tmp_path, "# Just a body with no frontmatter\n")
        result = migration.migrate_local_config(path)
        assert result.changed is False
        assert result.error is not None
        assert "frontmatter" in (result.error or "")

    def test_invalid_utf8_fails_closed(self, tmp_path: Path) -> None:
        path = tmp_path / "compound-gpid.local.md"
        path.write_bytes(b"---\nlanguage: \"both\"\n\xff\xfe\n---\n")
        result = migration.migrate_local_config(path)
        assert result.changed is False
        assert result.error is not None
