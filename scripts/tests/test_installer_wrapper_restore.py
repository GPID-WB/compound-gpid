"""Offline proof for exact old installer-output recognition and restoration."""
from __future__ import annotations

import os
from pathlib import Path
import subprocess

import pytest

from scripts.cg_restore_installer_wrappers import (
    KNOWN_PATHS, SHELL_NAMES, _shell_outputs, restore_installer_wrappers,
)

ROOT = Path(__file__).resolve().parents[2]


def _old(path: str) -> bytes:
    """Read a committed 9021 fixture source, never a live installation."""
    return subprocess.run(
        ["git", "-C", str(ROOT), "show", f"v1.2.0.9021:{path}"],
        capture_output=True, check=True,
    ).stdout


def _git(root: Path, *args: str) -> bytes:
    """Run Git only in the disposable fixture repository."""
    return subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, check=True,
    ).stdout


@pytest.fixture
def clone(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Build a minimal real Git fixture from committed old installer files."""
    home = tmp_path / "h"
    home.mkdir()
    for key in ("HOME", "USERPROFILE", "APPDATA", "LOCALAPPDATA", "XDG_CONFIG_HOME"):
        monkeypatch.setenv(key, str(home))
    monkeypatch.setenv("PROFILE", str(home / "profile.ps1"))
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", os.devnull)
    monkeypatch.setenv("GIT_ALLOW_PROTOCOL", "file")
    monkeypatch.setenv("GIT_TERMINAL_PROMPT", "0")
    root = tmp_path / "i"
    root.mkdir()
    for relative in sorted(KNOWN_PATHS | {"install.ps1", "scripts/install.sh"}):
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(_old(relative))
        if relative.startswith("bin/") and relative not in (
            "bin/cg-brain-init", "bin/cg-autopilot-control", "bin/cg-help",
        ) and not relative.endswith(".cmd"):
            path.chmod(0o755)
    (root / ".gitattributes").write_text("*.cmd text eol=crlf\n", encoding="ascii")
    _git(root, "init", "-q")
    _git(root, "add", "--all")
    _git(root, "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
         "-c", "commit.gpgSign=false", "commit", "-qm", "fixture")
    # Materialize the normal CMD CRLF checkout rather than LF archive bytes.
    _git(root, "restore", "--source=HEAD", "--worktree", "--", "bin")
    return root


def test_committed_old_templates_cover_all_twelve_rewrites() -> None:
    """Both published old tags have the same twelve recognized shell outputs."""
    source = _old("scripts/install.sh").decode("utf-8")
    outputs = _shell_outputs(source)
    expected = set(KNOWN_PATHS) - {
        f"bin/cg-{name}" for name in
        ("kilo", "skill", "help", "render-artifact", "release", "publish-markdown")
    } - {f"bin/cg-{name}.cmd" for name in ("link", "unlink", "update")}
    assert set(outputs) == expected
    old_9020 = subprocess.run(
        ["git", "-C", str(ROOT), "show", "v1.2.0.9020:scripts/install.sh"],
        capture_output=True, check=True,
    ).stdout
    assert old_9020 == source.encode("utf-8")


def test_exact_old_output_is_restored_and_clone_is_clean(clone: Path) -> None:
    """Recognize exact generated output, including old chmod-only residue."""
    outputs = _shell_outputs(_old("scripts/install.sh").decode("utf-8"))
    for relative, content in outputs.items():
        (clone / relative).write_bytes(content)
    for name in SHELL_NAMES:
        (clone / f"bin/cg-{name}").chmod(0o755)
    restored = restore_installer_wrappers(clone)
    assert set(outputs) <= set(restored)
    assert _git(clone, "diff", "--name-only", "HEAD") == b""


@pytest.mark.parametrize("relative", ["bin/cg-brain-init", "user.txt"])
def test_user_changes_block_without_restoring_any_file(clone: Path, relative: str) -> None:
    """Unknown paths and same-name user edits are not installer ownership proof."""
    if relative == "user.txt":
        (clone / relative).write_bytes(b"original\n")
        _git(clone, "add", "--", relative)
        _git(clone, "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
             "-c", "commit.gpgSign=false", "commit", "-qm", "user fixture")
    outputs = _shell_outputs(_old("scripts/install.sh").decode("utf-8"))
    generated = clone / "bin/cg-index"
    generated.write_bytes(outputs["bin/cg-index"])
    edited = clone / relative
    edited.write_bytes(b"user-customized content\n")
    before = generated.read_bytes()
    with pytest.raises(ValueError, match="[Uu]ser|Tracked"):
        restore_installer_wrappers(clone)
    assert generated.read_bytes() == before
    assert edited.read_bytes() == b"user-customized content\n"


def test_staged_wrapper_change_is_preserved(clone: Path) -> None:
    """Even a recognized wrapper cannot authorize discarding staged work."""
    path = clone / "bin/cg-index"
    path.write_bytes(_shell_outputs(_old("scripts/install.sh").decode("utf-8"))["bin/cg-index"])
    _git(clone, "add", "--", "bin/cg-index")
    before = path.read_bytes()
    with pytest.raises(ValueError, match="Staged"):
        restore_installer_wrappers(clone)
    assert path.read_bytes() == before
    assert _git(clone, "diff", "--cached", "--name-only").strip() == b"bin/cg-index"


def test_user_line_ending_edit_is_not_exact_installer_output(clone: Path) -> None:
    """One changed newline cannot authorize restoration of a generated wrapper."""
    path = clone / "bin/cg-index"
    generated = _shell_outputs(_old("scripts/install.sh").decode("utf-8"))["bin/cg-index"]
    edited = generated.replace(b"\n", b"\r\n", 1)
    path.write_bytes(edited)
    with pytest.raises(ValueError, match="User-modified installer wrapper"):
        restore_installer_wrappers(clone)
    assert path.read_bytes() == edited


@pytest.mark.skipif(os.name == "nt", reason="Windows does not track POSIX executable mode")
def test_user_removed_executable_mode_is_preserved(clone: Path) -> None:
    """The installer adds execute permission; removing it is not its output."""
    path = clone / "bin/cg-index"
    path.chmod(0o644)
    with pytest.raises(ValueError, match="User-modified wrapper mode"):
        restore_installer_wrappers(clone)
    assert not path.stat().st_mode & 0o100
