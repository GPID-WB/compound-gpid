"""Tests for bounded reads in the shared secure filesystem layer."""
from __future__ import annotations

# pylint: disable=no-member,protected-access,unexpected-keyword-arg

from io import BytesIO
import hashlib
import os
from pathlib import Path
import stat

import pytest

import secure_fs
from secure_fs import SecureMutationError, secure_read_bytes


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


def test_secure_create_captures_identity_and_preserves_existing_callers(tmp_path: Path) -> None:
    """An exclusive create returns an identity that permits later in-place edits."""
    identity = secure_fs.secure_create_bytes(tmp_path, "query.txt", b"")
    target = tmp_path / "query.txt"
    target.write_bytes(b"updated in place")
    assert secure_read_bytes(tmp_path, "query.txt", expected_identity=identity) == b"updated in place"
    assert secure_read_bytes(tmp_path, "query.txt") == b"updated in place"
    secure_fs.secure_delete_verified(tmp_path, "query.txt", hashlib.sha256(b"updated in place").hexdigest(),
                                     expected_identity=identity)
    assert not target.exists()


def test_secure_create_never_replaces_an_existing_empty_file(tmp_path: Path) -> None:
    """Equal empty bytes do not authorize ownership of a pre-existing file."""
    target = tmp_path / "query.txt"
    target.write_bytes(b"")
    before = target.stat()
    with pytest.raises(OSError):
        secure_fs.secure_create_bytes(tmp_path, "query.txt", b"")
    assert target.stat().st_ino == before.st_ino and target.read_bytes() == b""


@pytest.mark.parametrize("operation", ["read", "delete"])
@pytest.mark.parametrize("timing", ["before-call", "pinned-boundary"])
def test_expected_identity_rejects_equal_content_replacement(
    tmp_path: Path, operation: str, timing: str,
) -> None:
    """Prepare-time identity is checked on the opened handle, not a content hash."""
    content = b"same bytes"
    identity = secure_fs.secure_create_bytes(tmp_path, "query.txt", content)
    target = tmp_path / "query.txt"

    def replace_equal(path: Path) -> None:
        path.rename(tmp_path / "original.txt")
        path.write_bytes(content)

    if timing == "before-call":
        replace_equal(target)
    hook = replace_equal if timing == "pinned-boundary" else None
    with pytest.raises(SecureMutationError, match="identity|changed"):
        if operation == "read":
            secure_read_bytes(tmp_path, "query.txt", expected_identity=identity, before_open=hook)
        else:
            secure_fs.secure_delete_verified(tmp_path, "query.txt", hashlib.sha256(content).hexdigest(),
                                             expected_identity=identity, before_unlink=hook)
    assert target.read_bytes() == content
    assert (tmp_path / "original.txt").read_bytes() == content


def test_expected_identity_is_not_transferable_to_another_root(tmp_path: Path) -> None:
    """Identical relative names and bytes in two roots remain different files."""
    first, second = tmp_path / "first", tmp_path / "second"
    first.mkdir()
    second.mkdir()
    identity = secure_fs.secure_create_bytes(first, "query.txt", b"query")
    (second / "query.txt").write_bytes(b"query")
    with pytest.raises(SecureMutationError, match="identity|changed"):
        secure_read_bytes(second, "query.txt", expected_identity=identity)
    assert (second / "query.txt").read_bytes() == b"query"


def test_expected_identity_does_not_disable_hardlink_rejection(tmp_path: Path) -> None:
    """A prepared identity is not authority to read newly aliased content."""
    identity = secure_fs.secure_create_bytes(tmp_path, "query.txt", b"query")
    os.link(tmp_path / "query.txt", tmp_path / "alias.txt")
    with pytest.raises(SecureMutationError):
        secure_read_bytes(tmp_path, "query.txt", expected_identity=identity, reject_hardlinks=True)


def test_expected_identity_delete_still_requires_authorized_bytes(tmp_path: Path) -> None:
    """Identity and the existing digest authorization are both required."""
    identity = secure_fs.secure_create_bytes(tmp_path, "query.txt", b"original")
    target = tmp_path / "query.txt"
    target.write_bytes(b"changed in place")
    with pytest.raises(SecureMutationError):
        secure_fs.secure_delete_verified(tmp_path, "query.txt", hashlib.sha256(b"original").hexdigest(),
                                         expected_identity=identity)
    assert target.read_bytes() == b"changed in place"


def test_identity_only_delete_never_reads_oversized_payload(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An explicit None digest permits deletion by prepared identity without I/O reads."""
    identity = secure_fs.secure_create_bytes(tmp_path, "query.txt", b"")
    target = tmp_path / "query.txt"
    with target.open("wb") as handle:
        handle.seek(2 * 1024 * 1024)
        handle.write(b"x")

    def reject_payload_read(*_args, **_kwargs):
        raise AssertionError("identity-only deletion must not read payload bytes")

    with monkeypatch.context() as guarded:
        guarded.setattr(secure_fs, "_windows_read_all", reject_payload_read)
        guarded.setattr(os, "fdopen", reject_payload_read)
        secure_fs.secure_delete_verified(tmp_path, "query.txt", None,
                                         expected_identity=identity)
    assert not target.exists()
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("identity", [None, (), (1, 2), (1, 2, 3, 4),
                                      (True, 2, 3), (1, -2, 3), (1, 2, "3"), [1, 2, 3]])
def test_identity_only_delete_requires_valid_identity_before_io(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, identity,
) -> None:
    """Absent or malformed identity cannot authorize even an empty file deletion."""
    target = tmp_path / "query.txt"
    target.write_bytes(b"keep")

    def reject_backend(*_args, **_kwargs):
        raise AssertionError("invalid identity must fail before filesystem access")

    monkeypatch.setattr(secure_fs, "_secure_delete_windows", reject_backend)
    monkeypatch.setattr(secure_fs, "_secure_delete_posix", reject_backend)
    with pytest.raises(ValueError, match="identity"):
        secure_fs.secure_delete_verified(tmp_path, "query.txt", None,
                                         expected_identity=identity)
    assert target.read_bytes() == b"keep"


@pytest.mark.parametrize("replacement", ["equal-bytes", "hardlink", "directory"])
def test_identity_only_delete_rejects_replaced_or_aliased_file(
    tmp_path: Path, replacement: str,
) -> None:
    """Identity-only authority keeps type, alias, and pinned-boundary checks."""
    identity = secure_fs.secure_create_bytes(tmp_path, "query.txt", b"keep")
    target = tmp_path / "query.txt"

    def replace_at_boundary(path: Path) -> None:
        if replacement == "hardlink":
            os.link(path, tmp_path / "alias.txt")
        else:
            path.rename(tmp_path / "original.txt")
            if replacement == "directory":
                path.mkdir()
            else:
                path.write_bytes(b"keep")

    with pytest.raises(SecureMutationError):
        secure_fs.secure_delete_verified(tmp_path, "query.txt", None,
            expected_identity=identity, before_unlink=replace_at_boundary)
    assert target.exists()
    if replacement == "directory":
        assert target.is_dir() and (tmp_path / "original.txt").read_bytes() == b"keep"
    else:
        assert target.read_bytes() == b"keep"
        saved = "alias.txt" if replacement == "hardlink" else "original.txt"
        assert (tmp_path / saved).read_bytes() == b"keep"


def test_identity_only_delete_preserves_concurrent_winner_on_rollback(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A failed deletion retains both the concurrent file and owned recovery bytes."""
    identity = secure_fs.secure_create_bytes(tmp_path, "query.txt", b"owned")
    target = tmp_path / "query.txt"

    def fail_disposal(_handle) -> None:
        target.write_bytes(b"concurrent")
        raise OSError("disposal failed")

    original_unlink = os.unlink

    def fail_unlink(path, *args, **kwargs) -> None:
        if str(path).endswith(".stale"):
            target.write_bytes(b"concurrent")
            raise OSError("disposal failed")
        original_unlink(path, *args, **kwargs)

    with monkeypatch.context() as failure:
        failure.setattr(secure_fs, "_windows_dispose_handle", fail_disposal)
        failure.setattr(os, "unlink", fail_unlink)
        with pytest.raises(SecureMutationError, match="preserved"):
            secure_fs.secure_delete_verified(tmp_path, "query.txt", None,
                                             expected_identity=identity)
    assert target.read_bytes() == b"concurrent"
    recovery = list(tmp_path.glob(".query.txt.*.stale"))
    assert len(recovery) == 1 and recovery[0].read_bytes() == b"owned"
