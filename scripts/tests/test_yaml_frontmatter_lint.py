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
    """Run the validator on ``root`` and return the completed subprocess.

    Parameters
    ----------
    root : Path
        Directory tree to scan (contains ``agents/`` and ``skills/`` subdirs).
    *extra : str
        Extra CLI arguments to pass through, e.g. ``"-Fix"``.

    Returns
    -------
    subprocess.CompletedProcess
        Captured stdout/stderr and exit code. Run as a subprocess so the
        script's module is never imported (no ``__pycache__`` in the bundle).

    Example
    -------
    >>> result = _run_validator(tmp_path)
    >>> result.returncode == 0
    True
    """
    cmd = [sys.executable, str(VALIDATOR), "-Path", str(root), *extra]
    return subprocess.run(cmd, capture_output=True, text=True, cwd=str(REPO_ROOT), check=False)


def _write_bom_only_valid_file(tmp_path: Path) -> Path:
    """Create a valid tree with one agent that has only a UTF-8 BOM violation.

    Parameters
    ----------
    tmp_path : Path
        pytest-provided temporary directory.

    Returns
    -------
    Path
        Path to the BOM-prefixed agent file that was written.

    Example
    -------
    >>> agent = _write_bom_only_valid_file(tmp_path)
    >>> agent.read_bytes().startswith(b"\\xef\\xbb\\xbf")
    True
    """
    agent = tmp_path / "agents" / "cg-bom.md"
    agent.parent.mkdir(parents=True)
    agent.write_bytes(b"\xef\xbb\xbf---\ndescription: \"ok\"\nmode: subagent\n---\nbody\n")
    skill = tmp_path / "skills" / "cg-skill-test" / "SKILL.md"
    skill.parent.mkdir(parents=True)
    skill.write_text("---\nname: cg-skill-test\ndescription: \"ok\"\n---\nbody\n", encoding="utf-8")
    return agent


def _agent_with_description(tmp_path: Path, desc_line: str) -> Path:
    """Create a valid tree whose agent uses the given ``description:`` line.

    Parameters
    ----------
    tmp_path : Path
        pytest-provided temporary directory.
    desc_line : str
        The exact ``description: ...`` frontmatter line to write (may be empty
        value, quoted, malformed, etc.).

    Returns
    -------
    Path
        Path to the agent file that was written.

    Example
    -------
    >>> _agent_with_description(tmp_path, 'description: "ok"')
    """
    agent = tmp_path / "agents" / "cg-x.md"
    agent.parent.mkdir(parents=True)
    agent.write_text(f"---\n{desc_line}\nmode: subagent\n---\nbody\n", encoding="utf-8")
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


@pytest.mark.parametrize(
    "desc_line,expect_clean",
    [
        ('description: "ok"', True),
        ('description: "a \\"b\\""', True),   # escaped embedded quote is valid
        ("description: 'a ''b'''", True),     # single-quoted with escaped quote
        ("description: ", False),             # empty value after the colon
        ('description: "a"b"', False),        # malformed: unescaped embedded quote
        ("description: a: b", False),         # unquoted colon-space breaks parsing
    ],
)
def test_description_matcher_is_line_scoped_and_escape_aware(
    tmp_path: Path, desc_line: str, expect_clean: bool
) -> None:
    """Rule 1 must be line-scoped and escape-aware (empty / escaped / malformed).

    An empty ``description:`` value is reported, a value is never matched
    across lines, valid escaped quoted scalars pass, and malformed quoted
    values (unescaped embedded quote) and unquoted colon-space values fail.
    """
    _agent_with_description(tmp_path, desc_line)
    out = _run_validator(tmp_path).stdout
    if expect_clean:
        assert "passed validation" in out
    else:
        assert "R1-quoted-description" in out
