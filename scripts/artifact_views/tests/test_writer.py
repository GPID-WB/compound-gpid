"""Tests for secure atomic artifact-view mutation."""
from __future__ import annotations

import inspect
import os
from pathlib import Path, PureWindowsPath
import stat

import pytest

# pylint: disable=import-error
from artifact_views.errors import ArtifactWriteError
from artifact_views.writer import ViewDestination, write_view
import secure_fs
from secure_fs import (
    SecureMutationError,
    normalize_relative_path,
    secure_read_bytes,
    supports_secure_dir_fd,
)
# pylint: enable=import-error


def _destination(root: Path) -> Path:
    return root / ".cg-docs/views/plans/example.html"


def _view(relative: Path) -> ViewDestination:
    return ViewDestination.from_path(relative)


def test_secure_write_creates_expected_view(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()

    written = write_view(
        root,
        _view(Path(".cg-docs/views/plans/example.html")),
        b"<!doctype html>\n",
    )

    assert written == _destination(root)
    assert written.read_bytes() == b"<!doctype html>\n"
    if os.name != "nt":
        assert written.stat().st_mode & 0o777 == 0o644


@pytest.mark.skipif(os.name == "nt", reason="POSIX executable mode semantics")
def test_new_executable_uses_restrictive_default_mode(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()

    written = secure_fs.secure_write_bytes(
        root,
        Path("bin/tool"),
        b"#!/bin/sh\n",
        executable=True,
    )

    assert written.stat().st_mode & 0o777 == 0o755


@pytest.mark.skipif(os.name == "nt", reason="POSIX umask semantics")
def test_new_files_respect_restrictive_process_umask(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    previous = os.umask(0o077)
    try:
        regular = secure_fs.secure_write_bytes(root, Path("views/a.html"), b"a")
        executable = secure_fs.secure_write_bytes(
            root,
            Path("bin/tool"),
            b"tool",
            executable=True,
        )
    finally:
        os.umask(previous)

    assert regular.stat().st_mode & 0o777 == 0o600
    assert executable.stat().st_mode & 0o777 == 0o700


def test_windows_path_components_normalize_to_portable_relative_path() -> None:
    assert normalize_relative_path(PureWindowsPath("views", "plans", "a.html")) == (
        "views/plans/a.html"
    )


# pylint: disable=protected-access
def test_windows_rename_payload_includes_base_and_flexible_filename_bytes() -> None:
    rename_implementation = inspect.getsource(secure_fs._windows_rename_handle)
    directory_implementation = inspect.getsource(secure_fs._windows_open_directory)

    assert '("Flags", wintypes.DWORD)' in rename_implementation
    assert '("FileName", wintypes.WCHAR * 1)' in rename_implementation
    assert "ctypes.sizeof(RenameInformation) + len(encoded_name)" in rename_implementation
    assert "RenameInformation.FileName.offset" in rename_implementation
    assert "0x0020 | 0x0080" in directory_implementation
# pylint: enable=protected-access


@pytest.mark.skipif(os.name == "nt", reason="POSIX mode preservation semantics")
def test_existing_regular_view_mode_is_preserved(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    destination = _destination(root)
    destination.parent.mkdir(parents=True)
    destination.write_bytes(b"old")
    destination.chmod(0o640)

    write_view(root, _view(destination.relative_to(root)), b"new")

    assert destination.read_bytes() == b"new"
    assert destination.stat().st_mode & 0o777 == 0o640


def test_destination_symlink_is_rejected_without_outside_write(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    outside = tmp_path / "outside.html"
    destination = _destination(root)
    destination.parent.mkdir(parents=True)
    outside.write_bytes(b"outside")
    try:
        destination.symlink_to(outside)
    except OSError as error:
        if os.name == "nt" and getattr(error, "winerror", None) == 1314:
            pytest.skip("Windows symlink privilege is unavailable")
        raise

    with pytest.raises(ArtifactWriteError, match="symlink|link|regular"):
        write_view(root, _view(destination.relative_to(root)), b"new")

    assert outside.read_bytes() == b"outside"
    assert destination.is_symlink()


def test_interrupted_replace_preserves_previous_valid_view(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    destination = _destination(root)
    destination.parent.mkdir(parents=True)
    destination.write_bytes(b"valid-old")

    def interrupt(_path: Path) -> None:
        raise OSError("simulated interruption")

    with pytest.raises(ArtifactWriteError, match="simulated interruption"):
        write_view(
            root,
            _view(destination.relative_to(root)),
            b"new",
            before_replace=interrupt,
        )

    assert destination.read_bytes() == b"valid-old"
    assert not list(destination.parent.glob("*.tmp"))


@pytest.mark.backend_posix
@pytest.mark.skipif(not supports_secure_dir_fd(), reason="requires POSIX dir_fd support")
def test_mutation_boundary_ancestor_swap_cannot_escape_project(
    tmp_path: Path,
) -> None:
    root = tmp_path / "repo"
    outside = tmp_path / "outside"
    destination = _destination(root)
    destination.parent.mkdir(parents=True)
    destination.write_bytes(b"valid-old")
    outside.mkdir()
    displaced = root / ".cg-docs/views/plans-displaced"

    def swap_ancestor(_path: Path) -> None:
        destination.parent.rename(displaced)
        destination.parent.symlink_to(outside, target_is_directory=True)

    with pytest.raises(ArtifactWriteError):
        write_view(
            root,
            _view(destination.relative_to(root)),
            b"new",
            before_replace=swap_ancestor,
        )

    assert list(outside.iterdir()) == []
    assert (displaced / destination.name).read_bytes() == b"valid-old"


@pytest.mark.backend_posix
@pytest.mark.skipif(not supports_secure_dir_fd(), reason="requires POSIX dir_fd support")
def test_source_read_uses_pinned_parent_when_lexical_ancestor_is_swapped(
    tmp_path: Path,
) -> None:
    root = tmp_path / "repo"
    source = root / ".cg-docs/plans/example.md"
    source.parent.mkdir(parents=True)
    source.write_bytes(b"canonical")
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "example.md").write_bytes(b"outside-secret")
    displaced = root / ".cg-docs/plans-displaced"

    def swap_ancestor(_path: Path) -> None:
        source.parent.rename(displaced)
        source.parent.symlink_to(outside, target_is_directory=True)

    content = secure_read_bytes(
        root,
        Path(".cg-docs/plans/example.md"),
        before_open=swap_ancestor,
    )

    assert content == b"canonical"
    assert content != b"outside-secret"


def test_unknown_non_windows_fallback_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    monkeypatch.setattr(secure_fs, "supports_secure_dir_fd", lambda: False)
    monkeypatch.setattr(secure_fs, "is_windows_host", lambda: False)

    with pytest.raises(SecureMutationError, match="secure handle-relative"):
        secure_fs.secure_write_bytes(root, Path("views/a.html"), b"new")


@pytest.mark.backend_windows
@pytest.mark.skipif(os.name != "nt", reason="requires Windows handle semantics")
def test_windows_parent_pin_blocks_boundary_swap(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    destination = _destination(root)
    destination.parent.mkdir(parents=True)
    destination.write_bytes(b"old")
    displaced = root / ".cg-docs/views/plans-displaced"
    swap_blocked = False

    def attempt_swap(_path: Path) -> None:
        nonlocal swap_blocked
        try:
            destination.parent.rename(displaced)
        except OSError:
            swap_blocked = True

    write_view(
        root,
        _view(destination.relative_to(root)),
        b"new",
        before_replace=attempt_swap,
    )

    assert swap_blocked is True
    assert destination.read_bytes() == b"new"


@pytest.mark.backend_windows
@pytest.mark.skipif(os.name != "nt", reason="requires Windows handle semantics")
def test_windows_source_parent_pin_blocks_boundary_swap(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    source = root / ".cg-docs/plans/example.md"
    source.parent.mkdir(parents=True)
    source.write_bytes(b"canonical")
    displaced = root / ".cg-docs/plans-displaced"
    swap_blocked = False

    def attempt_swap(_path: Path) -> None:
        nonlocal swap_blocked
        try:
            source.parent.rename(displaced)
        except OSError:
            swap_blocked = True

    content = secure_read_bytes(
        root,
        Path(".cg-docs/plans/example.md"),
        before_open=attempt_swap,
    )

    assert swap_blocked is True
    assert content == b"canonical"


@pytest.mark.backend_windows
@pytest.mark.skipif(os.name != "nt", reason="requires Windows handle semantics")
def test_windows_target_collision_preserves_concurrent_and_previous_bytes(
    tmp_path: Path,
) -> None:
    root = tmp_path / "repo"
    destination = _destination(root)
    destination.parent.mkdir(parents=True)
    destination.write_bytes(b"previous-valid")

    def create_concurrent_target(_path: Path) -> None:
        destination.write_bytes(b"concurrent-user")

    with pytest.raises(ArtifactWriteError):
        write_view(
            root,
            _view(destination.relative_to(root)),
            b"new-render",
            before_replace=create_concurrent_target,
        )

    assert destination.read_bytes() == b"concurrent-user"
    recovery_files = list(destination.parent.glob(f".{destination.name}.*.previous"))
    assert len(recovery_files) == 1
    assert recovery_files[0].read_bytes() == b"previous-valid"


@pytest.mark.backend_posix
@pytest.mark.skipif(not supports_secure_dir_fd(), reason="requires POSIX dir_fd support")
def test_posix_target_collision_preserves_concurrent_and_previous_bytes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "repo"
    destination = _destination(root)
    destination.parent.mkdir(parents=True)
    destination.write_bytes(b"previous-valid")

    def create_concurrent_target(original: Path, _quarantine: Path) -> None:
        original.write_bytes(b"concurrent-user")

    monkeypatch.setattr(
        secure_fs,
        "_after_secure_quarantine",
        create_concurrent_target,
    )

    with pytest.raises(ArtifactWriteError, match="occupied|exists|collision"):
        write_view(root, _view(destination.relative_to(root)), b"new-render")

    assert destination.read_bytes() == b"concurrent-user"
    recovery_files = list(destination.parent.glob(f".{destination.name}.*.previous"))
    assert len(recovery_files) == 1
    assert recovery_files[0].read_bytes() == b"previous-valid"


# pylint: disable=protected-access
def test_posix_writer_uses_no_replace_publication_primitive() -> None:
    implementation = inspect.getsource(secure_fs._secure_write_posix)

    assert "_posix_rename_noreplace" in implementation
    assert "os.replace(" not in implementation
# pylint: enable=protected-access


@pytest.mark.backend_posix
@pytest.mark.skipif(not supports_secure_dir_fd(), reason="requires POSIX dir_fd support")
def test_posix_precommit_directory_flush_failure_restores_previous_view(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "repo"
    destination = _destination(root)
    destination.parent.mkdir(parents=True)
    destination.write_bytes(b"previous-valid")
    original_fsync = os.fsync

    def fail_directory_flush(file_descriptor: int) -> None:
        if stat.S_ISDIR(os.fstat(file_descriptor).st_mode):
            raise OSError("directory flush failed")
        original_fsync(file_descriptor)

    monkeypatch.setattr(os, "fsync", fail_directory_flush)

    with pytest.raises(ArtifactWriteError, match="directory flush failed"):
        write_view(root, _view(destination.relative_to(root)), b"new-render")

    assert destination.read_bytes() == b"previous-valid"


@pytest.mark.backend_posix
@pytest.mark.skipif(not supports_secure_dir_fd(), reason="requires POSIX dir_fd support")
def test_posix_postcommit_cleanup_failure_reports_preserved_recovery(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "repo"
    destination = _destination(root)
    destination.parent.mkdir(parents=True)
    destination.write_bytes(b"previous-valid")
    original_unlink = os.unlink

    def preserve_previous(path, *args, **kwargs):
        if isinstance(path, str) and path.endswith(".previous"):
            raise PermissionError("preserve recovery")
        return original_unlink(path, *args, **kwargs)

    monkeypatch.setattr(os, "unlink", preserve_previous)

    with pytest.warns(RuntimeWarning, match="recovery.*previous"):
        write_view(root, _view(destination.relative_to(root)), b"new-render")

    assert destination.read_bytes() == b"new-render"
    recovery_files = list(destination.parent.glob(f".{destination.name}.*.previous"))
    assert len(recovery_files) == 1
    assert recovery_files[0].read_bytes() == b"previous-valid"


@pytest.mark.backend_windows
@pytest.mark.skipif(os.name != "nt", reason="requires Windows handle semantics")
def test_windows_postcommit_disposal_failure_reports_preserved_recovery(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "repo"
    destination = _destination(root)
    destination.parent.mkdir(parents=True)
    destination.write_bytes(b"previous-valid")

    monkeypatch.setattr(
        secure_fs,
        "_windows_dispose_handle",
        lambda _handle: (_ for _ in ()).throw(OSError("dispose failed")),
    )

    with pytest.warns(RuntimeWarning, match="recovery.*previous"):
        write_view(root, _view(destination.relative_to(root)), b"new-render")

    assert destination.read_bytes() == b"new-render"
    recovery_files = list(destination.parent.glob(f".{destination.name}.*.previous"))
    assert len(recovery_files) == 1
    assert recovery_files[0].read_bytes() == b"previous-valid"


def test_windows_unpublished_temporary_cleanup_is_handle_relative() -> None:
    implementation = inspect.getsource(
        secure_fs._secure_write_windows  # pylint: disable=protected-access
    )

    assert "temporary_path.unlink" not in implementation
    assert "_windows_dispose_handle(temporary_handle)" in implementation


def test_traversal_and_absolute_destinations_fail(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()

    for destination in (Path("../outside.html"), tmp_path / "absolute.html"):
        with pytest.raises(ArtifactWriteError, match="relative|escape|absolute"):
            ViewDestination.from_path(destination)


def test_writer_failure_guidance_is_command_neutral(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    monkeypatch.setattr(
        "artifact_views.writer.secure_write_bytes",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError("failed")),
    )

    with pytest.raises(ArtifactWriteError) as caught:
        write_view(
            root,
            _view(
                Path(".cg-docs/views/documents/example.html")
            ),
            b"new",
        )

    rendered = str(caught.value)
    assert "cg-render-artifact" not in rendered
    assert "cg-publish-markdown" not in rendered


def test_writer_rejects_untyped_raw_destination(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()

    with pytest.raises(TypeError, match="ViewDestination"):
        write_view(
            root,
            Path(".cg-docs/views/documents/example.html"),
            b"new",
        )


@pytest.mark.skipif(os.name == "nt", reason="POSIX os.open permission injection")
def test_read_only_parent_failure_preserves_previous_view(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "repo"
    destination = _destination(root)
    destination.parent.mkdir(parents=True)
    destination.write_bytes(b"valid-old")

    original_open = os.open

    def deny_temporary(path, flags, *args, **kwargs):
        if isinstance(path, str) and path.endswith(".tmp"):
            raise PermissionError("read-only parent")
        return original_open(path, flags, *args, **kwargs)

    monkeypatch.setattr(os, "open", deny_temporary)
    with pytest.raises(ArtifactWriteError, match="read-only parent"):
        write_view(root, _view(destination.relative_to(root)), b"new")

    assert destination.read_bytes() == b"valid-old"
