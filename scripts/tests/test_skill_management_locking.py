"""Held-handle lifecycle lock tests."""
from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys

import pytest

from skill_management import locking


def test_lock_is_held_until_context_exit(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()

    with locking.project_lifecycle_lock(project, timeout=0.0):
        with pytest.raises(locking.LockTimeoutError):
            with locking.project_lifecycle_lock(project, timeout=0.0):
                pass

    with locking.project_lifecycle_lock(project, timeout=0.0):
        assert (project / locking.LOCK_PATH).is_file()


def test_stale_lock_file_without_held_lock_does_not_block(tmp_path: Path) -> None:
    project = tmp_path / "project"
    lock_path = project / locking.LOCK_PATH
    lock_path.parent.mkdir(parents=True)
    lock_path.write_bytes(b"stale diagnostic bytes\n")

    with locking.project_lifecycle_lock(project, timeout=0.0):
        assert lock_path.exists()


def test_subprocess_exit_releases_os_lock_but_leaves_stale_file(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    code = (
        "from pathlib import Path; import os; "
        "from skill_management.locking import project_lifecycle_lock; "
        "lock=project_lifecycle_lock(Path(os.environ['LOCK_PROJECT']), timeout=0); "
        "lock.__enter__(); os._exit(0)"
    )
    environment = os.environ.copy()
    environment["LOCK_PROJECT"] = str(project)
    subprocess.run(
        [sys.executable, "-c", code],
        cwd=str(Path(__file__).resolve().parents[1]),
        env=environment,
        check=True,
        timeout=30,
    )

    assert (project / locking.LOCK_PATH).is_file()
    with locking.project_lifecycle_lock(project, timeout=0.0):
        pass


@pytest.mark.skipif(os.name != "nt", reason="Windows reparse-handle check")
def test_windows_reparse_lock_handle_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = tmp_path / "project"
    project.mkdir()
    original = locking.secure_fs._windows_handle_attributes
    calls = {"count": 0}

    def mark_leaf_reparse(handle):
        calls["count"] += 1
        return original(handle) | (0x400 if calls["count"] == 1 else 0)

    monkeypatch.setattr(
        locking.secure_fs, "_windows_handle_attributes", mark_leaf_reparse
    )
    with pytest.raises(locking.LockSecurityError, match="reparse"):
        with locking.project_lifecycle_lock(project, timeout=0.0):
            pass


def test_timeout_uses_injected_monotonic_clock(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    ticks = iter((10.0, 10.2, 10.6))

    with locking.project_lifecycle_lock(project, timeout=0.0):
        with pytest.raises(locking.LockTimeoutError):
            with locking.project_lifecycle_lock(
                project,
                timeout=0.5,
                monotonic=lambda: next(ticks),
                sleeper=lambda _seconds: None,
            ):
                pass


def test_lock_leaf_link_is_rejected(
    tmp_path: Path, require_symlink_support: None
) -> None:
    project = tmp_path / "project"
    state = project / ".compound-gpid"
    state.mkdir(parents=True)
    outside = tmp_path / "outside.lock"
    outside.write_bytes(b"outside")
    (project / locking.LOCK_PATH).symlink_to(outside)

    with pytest.raises(locking.LockSecurityError):
        with locking.project_lifecycle_lock(project, timeout=0.0):
            pass

    assert outside.read_bytes() == b"outside"


@pytest.mark.skipif(os.name == "nt", reason="POSIX directory-link fixture")
def test_lock_ancestor_link_is_rejected(
    tmp_path: Path, require_symlink_support: None
) -> None:
    project = tmp_path / "project"
    project.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (project / ".compound-gpid").symlink_to(outside, target_is_directory=True)

    with pytest.raises(locking.LockSecurityError):
        with locking.project_lifecycle_lock(project, timeout=0.0):
            pass
