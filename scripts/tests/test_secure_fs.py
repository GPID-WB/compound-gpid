"""Tests for bounded reads in the shared secure filesystem layer."""
from __future__ import annotations

# pylint: disable=no-member,protected-access,unexpected-keyword-arg

from io import BytesIO
import hashlib
import os
from pathlib import Path
import stat
from types import SimpleNamespace

import pytest

import secure_fs
from secure_fs import SecureMutationError, secure_read_bytes


@pytest.mark.parametrize("tag,linked", (
    (0xA000000C, True), (0xA0000003, True), (0x9000001A, False), (0, False),
))
def test_windows_reparse_attributes_only_block_real_links(tag: int, linked: bool) -> None:
    """Cloud-folder reparse attributes alone are not link ownership conflicts."""
    metadata = SimpleNamespace(st_mode=stat.S_IFDIR, st_file_attributes=0x400,
                               st_reparse_tag=tag)
    assert secure_fs._is_link_or_reparse(metadata) is linked


@pytest.mark.parametrize("tag,linked", (
    (0xA000000C, True), (0xA0000003, True), (0x9000001A, False),
))
def test_pinned_windows_handle_inspects_reparse_tag(
    monkeypatch: pytest.MonkeyPatch, tag: int, linked: bool,
) -> None:
    """Pinned cloud directories pass; pinned junction/symlink handles fail."""
    import ctypes
    from ctypes import wintypes

    class Kernel:
        def GetFileInformationByHandle(self, handle, pointer):
            pointer._obj.dwFileAttributes = 0x410
            return True

        def GetFileInformationByHandleEx(self, handle, kind, pointer, size):
            assert kind == 9
            pointer._obj.ReparseTag = tag
            return True

    closed = []
    monkeypatch.setattr(secure_fs, "_windows_api", lambda: (ctypes, wintypes, Kernel()))
    monkeypatch.setattr(secure_fs, "_windows_close_handle", closed.append)
    if linked:
        with pytest.raises(SecureMutationError, match="not a safe directory"):
            secure_fs._windows_require_safe_handle(123, Path("cloud"), directory=True)
        assert closed == [123]
    else:
        secure_fs._windows_require_safe_handle(123, Path("cloud"), directory=True)
        assert closed == []


def test_bounded_secure_read_accepts_exact_limit(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    (root / "source.bin").write_bytes(b"1234")

    assert secure_read_bytes(root, "source.bin", max_bytes=4) == b"1234"


@pytest.mark.backend_posix
@pytest.mark.skipif(
    not secure_fs.supports_secure_dir_fd(),
    reason="requires POSIX dir_fd support",
)
def test_secure_delete_reports_committed_deletion_when_directory_flush_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    target = root / "stale.bin"
    content = b"stale content"
    target.write_bytes(content)
    original_fsync = os.fsync

    def fail_directory_flush(file_descriptor: int) -> None:
        if stat.S_ISDIR(os.fstat(file_descriptor).st_mode):
            raise OSError("directory flush failed")
        original_fsync(file_descriptor)

    monkeypatch.setattr(os, "fsync", fail_directory_flush)

    with pytest.warns(RuntimeWarning, match="Deletion committed"):
        secure_fs.secure_delete_verified(
            root,
            "stale.bin",
            hashlib.sha256(content).hexdigest(),
        )

    assert not target.exists()
    assert list(root.glob("*.stale")) == []


@pytest.mark.backend_windows
@pytest.mark.skipif(os.name != "nt", reason="requires Windows handle semantics")
def test_windows_staging_creates_and_removes_long_directory_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    request: pytest.FixtureRequest,
) -> None:
    """Create and remove real long staging directories through pinned handles."""
    relative = (
        Path(".cg-stage-" + "s" * 32)
        / ("a" * 80)
        / ("b" * 80)
        / ("c" * 80)
        / "payload.bin"
    )
    staging_parent = tmp_path / relative.parent
    assert len(str(staging_parent)) > 260
    created: list[str] = []
    original_mkdir = os.mkdir

    def create_directory(
        path: str | os.PathLike[str],
        mode: int = 0o777,
        *,
        dir_fd: int | None = None,
    ) -> None:
        assert isinstance(path, str) and path.startswith("\\\\?\\")
        original_mkdir(path, mode, dir_fd=dir_fd)
        created.append(path)

    monkeypatch.setattr(os, "mkdir", create_directory)
    try:
        handles, parent, _parent_handle, _name = secure_fs._windows_pin_parent_chain(
            tmp_path, relative.as_posix(), create=True
        )
        try:
            assert parent == staging_parent
            assert os.path.isdir(created[-1])
            request.node.user_properties.append(
                ("max_actual_staging_path_length", len(str(parent)))
            )
        finally:
            secure_fs._windows_close_handles(handles)
    finally:
        for directory in reversed(created):
            os.rmdir(directory)

    assert not os.path.exists(secure_fs._windows_long_path(staging_parent))
    assert not (tmp_path / relative.parts[0]).exists()


@pytest.mark.backend_windows
@pytest.mark.skipif(os.name != "nt", reason="requires Windows handle semantics")
def test_windows_delete_preserves_winner_and_quarantine_on_rollback_collision(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    target = root / "stale.bin"
    content = b"stale content"
    target.write_bytes(content)

    def fail_disposal(_handle) -> None:
        target.write_bytes(b"concurrent user content")
        raise OSError("disposal failed")

    monkeypatch.setattr(secure_fs, "_windows_dispose_handle", fail_disposal)

    with pytest.raises(SecureMutationError, match="recovery preserved"):
        secure_fs.secure_delete_verified(
            root,
            "stale.bin",
            hashlib.sha256(content).hexdigest(),
        )

    assert target.read_bytes() == b"concurrent user content"
    recovery_files = list(root.glob(f".{target.name}.*.stale"))
    assert len(recovery_files) == 1
    assert recovery_files[0].read_bytes() == content


def test_bounded_secure_read_rejects_known_oversize_before_read(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    (root / "source.bin").write_bytes(b"12345")
    called = False
    original = secure_fs._read_stream_bounded

    def observe_read(*args, **kwargs):
        nonlocal called
        called = True
        return original(*args, **kwargs)

    monkeypatch.setattr(secure_fs, "_read_stream_bounded", observe_read)

    with pytest.raises(SecureMutationError, match="exceeds.*4"):
        secure_read_bytes(root, "source.bin", max_bytes=4)

    assert called is False


def test_bounded_stream_detects_growth_at_limit_plus_one() -> None:
    stream = BytesIO(b"12345")

    with pytest.raises(SecureMutationError, match="grew beyond.*4"):
        secure_fs._read_stream_bounded(
            stream,
            max_bytes=4,
            source_path=Path("source.bin"),
        )

    assert stream.tell() == 5


@pytest.mark.parametrize("max_bytes", (-1, -10))
def test_bounded_secure_read_rejects_negative_limit(
    tmp_path: Path,
    max_bytes: int,
) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    (root / "source.bin").write_bytes(b"data")

    with pytest.raises(ValueError, match="non-negative"):
        secure_read_bytes(root, "source.bin", max_bytes=max_bytes)
