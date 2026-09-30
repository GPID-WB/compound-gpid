"""Regression tests for the yaml-frontmatter-lint validator.

Runs the validator as a subprocess (never imports it) so running these tests
does not create a ``__pycache__`` inside the skill bundle, which would be
picked up by the platform-tree generator and trip the drift gate.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = REPO_ROOT / ".github/skills/cg-skill-yaml-frontmatter-lint" / "validate_yaml_frontmatter.py"
PS_VALIDATOR = REPO_ROOT / ".github/skills/cg-skill-yaml-frontmatter-lint" / "Invoke-YamlLint.ps1"

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


def _copy_tracked_adapter_tree(adapter: str, destination: Path) -> Path:
    """Materialize only release-shipped adapter metadata for linting.

    Gitignored local prototypes may live below an adapter's ``skills``
    directory, but they are not part of the committed release inventory.
    """
    result = subprocess.run(
        ["git", "ls-files", "--", f"{adapter}/agents", f"{adapter}/skills"],
        cwd=str(REPO_ROOT), capture_output=True, text=True, check=True,
    )
    adapter_root = destination / adapter.lstrip(".")
    for relative_text in result.stdout.splitlines():
        relative = Path(relative_text)
        if relative.name != "SKILL.md" and not (
            relative.parent.name == "agents" and relative.suffix == ".md"
        ):
            continue
        source = REPO_ROOT / relative
        target = adapter_root / relative.relative_to(adapter)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    return adapter_root


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
    with agent.open("w", encoding="utf-8", newline="") as handle:
        handle.write(f"---\n{desc_line}\nmode: subagent\n---\nbody\n")
    skill = tmp_path / "skills" / "cg-skill-test" / "SKILL.md"
    skill.parent.mkdir(parents=True)
    with skill.open("w", encoding="utf-8", newline="") as handle:
        handle.write("---\nname: cg-skill-test\ndescription: \"ok\"\n---\nbody\n")
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
        ("description: 'a ''b'''", False),    # hygiene requires double quotes
        ("description: safe plain scalar", False),
        ("description: ", False),             # empty value after the colon
        ('description: "a"b"', False),        # malformed: unescaped embedded quote
        ("description: a: b", False),         # unquoted colon-space breaks parsing
    ],
)
def test_description_matcher_is_line_scoped_and_escape_aware(
    tmp_path: Path, desc_line: str, expect_clean: bool
) -> None:
    """Rule 1 requires line-safe, valid double-quoted descriptions.

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


@pytest.mark.parametrize("adapter", (".github", ".agents", ".kilo", ".opencode", ".claude"))
def test_every_shipped_adapter_tree_passes_frontmatter_lint(
    adapter: str, tmp_path: Path,
) -> None:
    """The release gate scans every canonical and generated adapter tree."""
    root = REPO_ROOT / adapter
    if not root.is_dir():
        pytest.skip(f"adapter tree not present: {adapter}")
    tracked_root = _copy_tracked_adapter_tree(adapter, tmp_path)
    result = _run_validator(tracked_root)
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize(
    "raw,rule",
    [
        (b'---\nname: cg-skill-test\ndescription: "non-ASCII \xe2\x80\x94"\n---\nbody\n', "R2-ascii-frontmatter"),
        ('---\nname: cg-skill-test\ndescription: "ok"\n---\nO(n\u00c2\u00b2)\n'.encode("utf-8"), "R5-mojibake"),
        (b'---\r\nname: cg-skill-test\r\ndescription: "ok"\r\n---\r\nbody\r\n', "R6-lf-endings"),
    ],
)
def test_hygiene_rules_and_windows_validator_parity(tmp_path: Path, raw: bytes, rule: str) -> None:
    """Python and PowerShell entries agree on ASCII, mojibake, and LF rules."""
    skill = tmp_path / "skills" / "cg-skill-test" / "SKILL.md"
    skill.parent.mkdir(parents=True)
    skill.write_bytes(raw)
    python_result = _run_validator(tmp_path)
    assert python_result.returncode == 1
    assert rule in python_result.stdout

    if os.name == "nt":
        powershell = shutil.which("powershell.exe") or shutil.which("pwsh.exe")
        assert powershell, "PowerShell is required for Windows validator parity"
        ps_result = subprocess.run(
            [powershell, "-NoProfile", "-File", str(PS_VALIDATOR), "-Path", str(tmp_path)],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
            check=False,
        )
        assert ps_result.returncode == 1
        assert rule in ps_result.stdout + ps_result.stderr


def test_description_continuation_cannot_supply_agent_mode(tmp_path: Path) -> None:
    """A mode-looking line inside an open description is not a mode field."""
    root = tmp_path / ".kilo"
    agent = root / "agents" / "cg-x.md"
    agent.parent.mkdir(parents=True)
    agent.write_text(
        '---\ndescription: "continued\nmode: subagent"\n---\nbody\n',
        encoding="utf-8",
        newline="",
    )
    result = _run_validator(root)
    assert result.returncode == 1
    assert "Missing required field: mode" in result.stdout

    if os.name == "nt":
        powershell = shutil.which("powershell.exe") or shutil.which("pwsh.exe")
        assert powershell
        ps_result = subprocess.run(
            [powershell, "-NoProfile", "-File", str(PS_VALIDATOR), "-Path", str(root)],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
            check=False,
        )
        assert ps_result.returncode == 1
        assert "Missing required field: mode" in ps_result.stdout + ps_result.stderr


def test_block_scalar_content_cannot_supply_agent_mode(tmp_path: Path) -> None:
    """An indented mode lookalike inside a block scalar is not metadata."""
    root = tmp_path / ".kilo"
    agent = root / "agents" / "cg-x.md"
    agent.parent.mkdir(parents=True)
    agent.write_text(
        '---\ndescription: "ok"\nnotes: |\n  mode: subagent\n---\nbody\n',
        encoding="utf-8",
        newline="",
    )
    result = _run_validator(root)
    assert result.returncode == 1
    assert "Missing required field: mode" in result.stdout

    if os.name == "nt":
        powershell = shutil.which("powershell.exe") or shutil.which("pwsh.exe")
        assert powershell
        ps_result = subprocess.run(
            [powershell, "-NoProfile", "-File", str(PS_VALIDATOR), "-Path", str(root)],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
            check=False,
        )
        assert ps_result.returncode == 1
        assert "Missing required field: mode" in ps_result.stdout + ps_result.stderr


@pytest.mark.parametrize("mode_line", ("mode:subagent", "mode: bogus", "mode:"))
def test_agent_mode_requires_valid_yaml_separator_and_value(tmp_path: Path, mode_line: str) -> None:
    """Malformed or unsupported mode scalars fail both validator entries."""
    root = tmp_path / ".kilo"
    agent = root / "agents" / "cg-x.md"
    agent.parent.mkdir(parents=True)
    agent.write_text(
        f'---\ndescription: "ok"\n{mode_line}\n---\nbody\n',
        encoding="utf-8",
        newline="",
    )
    result = _run_validator(root)
    assert result.returncode == 1
    assert "Missing required field: mode" in result.stdout

    if os.name == "nt":
        powershell = shutil.which("powershell.exe") or shutil.which("pwsh.exe")
        assert powershell
        ps_result = subprocess.run(
            [powershell, "-NoProfile", "-File", str(PS_VALIDATOR), "-Path", str(root)],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
            check=False,
        )
        assert ps_result.returncode == 1
        assert "Missing required field: mode" in ps_result.stdout + ps_result.stderr


@pytest.mark.parametrize("mode_line", ('mode: "subagent"', "mode: subagent # delegated agent"))
def test_agent_mode_accepts_semantic_yaml_scalars(tmp_path: Path, mode_line: str) -> None:
    """Quoted mode values and inline comments remain valid YAML metadata."""
    root = tmp_path / ".kilo"
    agent = root / "agents" / "cg-x.md"
    agent.parent.mkdir(parents=True)
    agent.write_text(
        f'---\ndescription: "ok"\n{mode_line}\n---\nbody\n',
        encoding="utf-8",
        newline="",
    )
    assert _run_validator(root).returncode == 0

    if os.name == "nt":
        powershell = shutil.which("powershell.exe") or shutil.which("pwsh.exe")
        assert powershell
        ps_result = subprocess.run(
            [powershell, "-NoProfile", "-File", str(PS_VALIDATOR), "-Path", str(root)],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
            check=False,
        )
        assert ps_result.returncode == 0, ps_result.stdout + ps_result.stderr


@pytest.mark.parametrize(
    "relative,frontmatter,field",
    [
        ("agents/cg-x.md", 'description: "one"\ndescription: "two"\nmode: subagent', "description"),
        ("agents/cg-x.md", 'description: "ok"\nmode: subagent\nmode: bogus', "mode"),
        ("skills/cg-skill-test/SKILL.md", 'name: cg-skill-test\nname: duplicate\ndescription: "ok"', "name"),
    ],
)
def test_duplicate_required_metadata_is_rejected(
    tmp_path: Path,
    relative: str,
    frontmatter: str,
    field: str,
) -> None:
    """Duplicate root metadata fails regardless of duplicate ordering."""
    root = tmp_path / ".kilo"
    path = root / relative
    path.parent.mkdir(parents=True)
    path.write_text(f"---\n{frontmatter}\n---\nbody\n", encoding="utf-8", newline="")
    result = _run_validator(root)
    assert result.returncode == 1
    assert f"Duplicate required field: {field}" in result.stdout

    if os.name == "nt":
        powershell = shutil.which("powershell.exe") or shutil.which("pwsh.exe")
        assert powershell
        ps_result = subprocess.run(
            [powershell, "-NoProfile", "-File", str(PS_VALIDATOR), "-Path", str(root)],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
            check=False,
        )
        assert ps_result.returncode == 1
        assert f"Duplicate required field: {field}" in ps_result.stdout + ps_result.stderr
