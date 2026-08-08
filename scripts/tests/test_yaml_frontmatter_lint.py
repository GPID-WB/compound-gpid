"""Regression tests for the yaml-frontmatter-lint validator.

Runs the validator as a subprocess (never imports it) so running these tests
does not create a ``__pycache__`` inside the skill bundle, which would be
picked up by the platform-tree generator and trip the drift gate.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = REPO_ROOT / ".github/skills/cg-skill-yaml-frontmatter-lint" / "validate_yaml_frontmatter.py"

pytestmark = pytest.mark.skipif(not VALIDATOR.is_file(), reason="validator not present in this checkout")


def _run_validator(root: Path, *extra: str) -> subprocess.CompletedProcess:
    cmd = [sys.executable, str(VALIDATOR), "-Path", str(root), *extra]
    return subprocess.run(cmd, capture_output=True, text=True, cwd=str(REPO_ROOT), check=False)


def _write_bom_only_valid_file(tmp_path: Path) -> Path:
    agent = tmp_path / "agents" / "cg-bom.md"
    agent.parent.mkdir(parents=True)
    agent.write_bytes(b"\xef\xbb\xbf---\ndescription: \"ok\"\nmode: subagent\n---\nbody\n")
    skill = tmp_path / "skills" / "cg-skill-test" / "SKILL.md"
    skill.parent.mkdir(parents=True)
    skill.write_text("---\nname: cg-skill-test\ndescription: \"ok\"\n---\nbody\n", encoding="utf-8")
    return agent


def test_reports_bom_only_violation_without_fix(tmp_path: Path) -> None:
    """A BOM-only file is flagged but left untouched without -Fix."""
    agent = _write_bom_only_valid_file(tmp_path)
    result = _run_validator(tmp_path)
    assert "R3-no-bom" in result.stdout
    assert agent.read_bytes().startswith(b"\xef\xbb\xbf")


def test_fix_removes_bom_only_violation(tmp_path: Path) -> None:
    """-Fix removes a UTF-8 BOM even when no other fix applies."""
    agent = _write_bom_only_valid_file(tmp_path)
    first = _run_validator(tmp_path, "-Fix")
    assert first.returncode == 1  # reports violations that existed at scan time
    assert not agent.read_bytes().startswith(b"\xef\xbb\xbf")

    second = _run_validator(tmp_path)
    assert second.returncode == 0
    assert "passed validation" in second.stdout
