"""Root-anchored, no-follow mutation helpers shared by repository writers."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import os
from pathlib import Path, PurePath, PurePosixPath, PureWindowsPath
import stat
import sys
from typing import BinaryIO, Callable, Optional, Tuple, Union
import uuid
import warnings

BeforeReplace = Optional[Callable[[Path], None]]
BeforeOpen = Optional[Callable[[Path], None]]
_REPARSE_POINT_FLAG = 0x400
_SUPPORTS_SECURE_DIR_FD = (
    os.name != "nt"
    and os.open in os.supports_dir_fd
    and hasattr(os, "O_NOFOLLOW")
)
_POSIX_RENAME_EXCL = 0x00000004
_RENAME_NOREPLACE = 1


class SecureMutationError(OSError):
    """A path identity or type changed at a secure mutation boundary."""


@dataclass(frozen=True)
class ExpectedFileState:
    """Authorized destination state carried into a pinned write transaction."""

    exists: bool
    sha256: Optional[str] = None

    def __post_init__(self) -> None:
        if self.exists != (self.sha256 is not None):
            raise ValueError(
                "Existing expected state requires a SHA-256; absent state cannot "
                "carry one."
            )
        if self.sha256 is not None and (
            len(self.sha256) != 64
            or any(character not in "0123456789abcdef" for character in self.sha256)
        ):
            raise ValueError("Expected destination SHA-256 must be lowercase hex.")

    @classmethod
    def absent(cls) -> "ExpectedFileState":
        """Return an authorization requiring the destination to stay absent.

        Args:
            None.

        Returns:
            Expected state that rejects any destination present at write time.

        Example:
            ``ExpectedFileState.absent()`` authorizes first publication only.
        """
        return cls(False)

    @classmethod
    def from_bytes(cls, content: bytes) -> "ExpectedFileState":
        """Return an authorization for one exact destination byte sequence.

        Args:
            content: Exact destination bytes observed during ownership checks.

        Returns:
            Expected state carrying the lowercase SHA-256 of ``content``.

        Example:
            Use this state to bind publication to the bytes that were authorized.
        """
        return cls(True, hashlib.sha256(content).hexdigest())


def _after_secure_quarantine(_original: Path, _quarantine: Path) -> None:
    """Test hook immediately after a handle-relative quarantine rename."""


def supports_secure_dir_fd() -> bool:
    """Return whether this host supports pinned handle-relative replacement.

    Args:
        None.

    Returns:
        ``True`` when ``dir_fd`` and no-follow traversal are available.

    Example:
        >>> isinstance(supports_secure_dir_fd(), bool)
        True
    """
    return _SUPPORTS_SECURE_DIR_FD and _supports_posix_rename_noreplace()


def is_windows_host() -> bool:
    """Return whether the active runtime uses Windows filesystem semantics.

    Args:
        None.

    Returns:
        ``True`` on Windows and ``False`` on other hosts.

    Example:
        Tests may replace this narrow platform boundary without mutating
        ``os.name`` globally.
    """
    return os.name == "nt"


def normalize_relative_path(relative_path: Union[str, PurePath]) -> str:
    """Validate and normalize one portable root-relative mutation path.

    Args:
        relative_path: Path below a caller-supplied mutation root.

    Returns:
        A POSIX relative path with no traversal components.

    Raises:
        SecureMutationError: If the path is absolute, empty, or traverses.

    Example:
        >>> normalize_relative_path(Path("views/plan.html"))
        'views/plan.html'
    """
    if isinstance(relative_path, PureWindowsPath):
        if relative_path.is_absolute() or relative_path.anchor:
            raise SecureMutationError(
                f"Mutation path must be relative and cannot escape its root: "
                f"{str(relative_path)!r}."
            )
        text = PurePosixPath(*relative_path.parts).as_posix()
    elif isinstance(relative_path, PurePath):
        text = relative_path.as_posix()
    else:
        text = str(relative_path)
    if not text:
        raise SecureMutationError("Mutation path must be a non-empty relative path.")
    if "\\" in text or "\x00" in text:
        raise SecureMutationError(
            "Mutation path must use POSIX separators and contain no NUL."
        )
    pure = PurePosixPath(text)
    if pure.is_absolute() or any(part in {"", ".", ".."} for part in pure.parts):
        raise SecureMutationError(
            f"Mutation path must be relative and cannot escape its root: {text!r}."
        )
    return str(pure)


def open_relative_parent(
    root: Path,
    relative_path: str,
    *,
    create: bool,
) -> Tuple[int, str]:
    """Open a relative parent through no-follow directory handles.

    Args:
        root: Existing mutation root directory.
        relative_path: Validated POSIX path below ``root``.
        create: Whether missing parent directories may be created.

    Returns:
        ``(parent_fd, basename)``. The caller owns ``parent_fd``.

    Raises:
        OSError: If a component is a link, non-directory, or inaccessible.

    Example:
        The returned descriptor is intentionally consumed by secure writers;
        callers must close it after use.
    """
    normalized = normalize_relative_path(relative_path)
    parts = PurePosixPath(normalized).parts
    flags = (
        os.O_RDONLY
        | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_NOFOLLOW", 0)
    )
    descriptor = os.open(root, flags)
    try:
        for part in parts[:-1]:
            if create:
                try:
                    os.mkdir(part, dir_fd=descriptor)
                except FileExistsError:
                    pass
            child = os.open(part, flags, dir_fd=descriptor)
            os.close(descriptor)
            descriptor = child
        return descriptor, parts[-1]
    except BaseException:
        os.close(descriptor)
        raise


def secure_write_bytes(
    root: Path,
    relative_path: Path,
    content: bytes,
    *,
    executable: Optional[bool] = None,
    before_replace: BeforeReplace = None,
    expected_state: Optional[ExpectedFileState] = None,
) -> Path:
    """Atomically replace one root-relative regular file without following links.

    On capable POSIX hosts the parent is pinned with ``dir_fd`` and
    ``O_NOFOLLOW``. Other hosts reject links/reparse points and compare every
    existing component identity immediately before replacement.

    Args:
        root: Existing project or generated-tree root.
        relative_path: Destination below ``root``.
        content: Exact bytes to write.
        executable: ``True`` to add execute bits, ``False`` to remove them, or
            ``None`` to preserve an existing mode unchanged.
        before_replace: Optional test hook invoked at the final mutation boundary.
        expected_state: Optional authorized absence or exact prior-byte digest.

    Returns:
        The lexical destination path below ``root``.

    Raises:
        SecureMutationError: If containment, identity, or file type is unsafe.
        OSError: If filesystem mutation fails.

    Example:
        >>> import tempfile
        >>> root = Path(tempfile.mkdtemp())
        >>> secure_write_bytes(root, Path("views/a.html"), b"ok").read_bytes()
        b'ok'
    """
    root = Path(root)
    normalized = normalize_relative_path(relative_path)
    if not root.exists() or root.is_symlink() or not root.is_dir():
        raise SecureMutationError(
            f"Mutation root must be an existing regular directory: {root}."
        )
    destination = root / PurePosixPath(normalized)
    if supports_secure_dir_fd():
        _secure_write_posix(
            root,
            normalized,
            content,
            executable=executable,
            before_replace=before_replace,
            expected_state=expected_state,
        )
    elif is_windows_host():
        _secure_write_windows(
            root,
            normalized,
            content,
            executable=executable,
            before_replace=before_replace,
            expected_state=expected_state,
        )
    else:
        raise SecureMutationError(
            "This platform has no secure handle-relative replacement backend."
        )
    return destination


def secure_read_bytes(
    root: Path,
    relative_path: Union[str, PurePath],
    *,
    before_open: BeforeOpen = None,
    reject_hardlinks: bool = False,
    max_bytes: Optional[int] = None,
) -> bytes:
    """Read one root-relative regular file through pinned no-follow handles.

    Args:
        root: Existing project root directory.
        relative_path: File below ``root``.
        before_open: Optional test hook after the parent is pinned and before
            the final file handle is opened.
        reject_hardlinks: Reject files with more than one filesystem link.
        max_bytes: Optional maximum returned byte count. The pinned handle is
            inspected before allocation and read at most this value plus one.

    Returns:
        Exact file bytes from the pinned source identity.

    Raises:
        SecureMutationError: If containment or file type is unsafe.
        OSError: If the file cannot be opened or read.

    Example:
        ``secure_read_bytes(root, Path("plan.md"))`` returns pinned file bytes.
    """
    root = Path(root)
    if max_bytes is not None and max_bytes < 0:
        raise ValueError("Secure read byte limit must be non-negative.")
    normalized = normalize_relative_path(relative_path)
    if not root.exists() or root.is_symlink() or not root.is_dir():
        raise SecureMutationError(
            f"Read root must be an existing regular directory: {root}."
        )
    if supports_secure_dir_fd():
        return _secure_read_posix(
            root,
            normalized,
            before_open=before_open,
            reject_hardlinks=reject_hardlinks,
            max_bytes=max_bytes,
        )
    if is_windows_host():
        return _secure_read_windows(
            root,
            normalized,
            before_open=before_open,
            reject_hardlinks=reject_hardlinks,
            max_bytes=max_bytes,
        )
    raise SecureMutationError(
        "This platform has no secure handle-relative read backend."
    )


def secure_delete_verified(
    root: Path,
    relative_path: Union[str, PurePath],
    expected_sha256: str,
    *,
    before_unlink: BeforeOpen = None,
) -> None:
    """Quarantine, verify, and delete one root-relative regular file.

    The quarantine rename and final deletion are handle-relative. A changed file
    is restored to its original name before an error is raised.

    Args:
        root: Existing generated-tree root.
        relative_path: Owned file below ``root``.
        expected_sha256: Lowercase digest authorized for deletion.
        before_unlink: Optional test hook at the final mutation boundary.

    Returns:
        ``None`` after verified deletion, or when the file is already absent.

    Raises:
        SecureMutationError: If identity, type, or content is unsafe.
        OSError: If a filesystem operation fails.

    Example:
        ``secure_delete_verified(root, Path("old.md"), expected_digest)``.
    """
    root = Path(root)
    normalized = normalize_relative_path(relative_path)
    if supports_secure_dir_fd():
        _secure_delete_posix(
            root,
            normalized,
            expected_sha256,
            before_unlink=before_unlink,
        )
        return
    if is_windows_host():
        _secure_delete_windows(
            root,
            normalized,
            expected_sha256,
            before_unlink=before_unlink,
        )
        return
    raise SecureMutationError(
        "This platform has no secure handle-relative deletion backend."
    )


def revalidate_destination_ancestors(root: Path, destination: Path) -> None:
    """Reject links, reparse points, and non-directories below a mutation root.

    Args:
        root: Existing mutation root.
        destination: Lexical destination below ``root``.

    Raises:
        SecureMutationError: If containment or an ancestor is unsafe.

    Returns:
        ``None`` after every existing ancestor is validated.

    Example:
        ``revalidate_destination_ancestors(root, root / "views/plan.html")``.
    """
    root = Path(root)
    destination = Path(destination)
    try:
        relative = destination.relative_to(root)
    except ValueError as error:
        raise SecureMutationError(
            f"Destination escapes mutation root: {destination}."
        ) from error
    current = root
    for part in relative.parts[:-1]:
        current = current / part
        if not current.exists() and not current.is_symlink():
            continue
        metadata = os.lstat(current)
        if _is_link_or_reparse(metadata) or not stat.S_ISDIR(metadata.st_mode):
            raise SecureMutationError(
                f"Destination ancestor is a link, reparse point, or non-directory: "
                f"{current}."
            )


def _secure_write_posix(
    root: Path,
    relative_path: str,
    content: bytes,
    *,
    executable: Optional[bool],
    before_replace: BeforeReplace,
    expected_state: Optional[ExpectedFileState],
) -> None:
    parent_fd, name = open_relative_parent(root, relative_path, create=True)
    temporary = f".{name}.{uuid.uuid4().hex}.tmp"
    previous = f".{name}.{uuid.uuid4().hex}.previous"
    file_fd: Optional[int] = None
    previous_quarantined = False
    published = False
    committed = False
    try:
        original_target = _stat_target(parent_fd, name)
        if original_target is not None and not stat.S_ISREG(original_target.st_mode):
            raise SecureMutationError(
                f"Destination target is not a regular file: {root / relative_path}."
            )
        _verify_expected_existence(
            expected_state,
            original_target is not None,
            relative_path,
        )
        creation_mode = 0o777 if executable is True else 0o666
        file_fd = os.open(
            temporary,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL,
            creation_mode,
            dir_fd=parent_fd,
        )
        assert file_fd is not None
        with os.fdopen(file_fd, "wb", closefd=False) as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        if original_target is not None:
            _posix_fchmod(
                file_fd,
                _replacement_mode(original_target, executable),
            )
        _verify_parent_identity(root, relative_path, parent_fd)
        _verify_target_identity(parent_fd, name, original_target, root / relative_path)
        if original_target is not None:
            _posix_rename_noreplace(parent_fd, name, previous)
            previous_quarantined = True
            _verify_expected_posix_bytes(
                parent_fd,
                previous,
                expected_state,
                relative_path,
            )
            _after_secure_quarantine(
                root / PurePosixPath(relative_path),
                root / PurePosixPath(relative_path).parent / previous,
            )
        if before_replace is not None:
            before_replace(root / relative_path)
        _verify_parent_identity(root, relative_path, parent_fd)
        _posix_rename_noreplace(parent_fd, temporary, name)
        published = True
        os.fsync(parent_fd)
        committed = True
        if previous_quarantined:
            try:
                os.unlink(previous, dir_fd=parent_fd)
            except OSError as cleanup_error:
                warnings.warn(
                    f"Publication committed; recovery preserved as {previous}: "
                    f"{cleanup_error}",
                    RuntimeWarning,
                    stacklevel=2,
                )
            else:
                previous_quarantined = False
                try:
                    os.fsync(parent_fd)
                except OSError as cleanup_error:
                    warnings.warn(
                        "Publication committed; recovery cleanup durability could "
                        f"not be confirmed: {cleanup_error}",
                        RuntimeWarning,
                        stacklevel=2,
                    )
    except BaseException as publication_error:
        if not committed:
            try:
                if published:
                    _unlink_posix_if_identity(
                        parent_fd,
                        name,
                        os.fstat(file_fd),
                        relative_path,
                    )
                    published = False
                if previous_quarantined:
                    _posix_rename_noreplace(parent_fd, previous, name)
                    previous_quarantined = False
            except OSError as rollback_error:
                raise SecureMutationError(
                    f"Publication failed and rollback could not restore "
                    f"{relative_path}; recovery preserved as {previous}: "
                    f"{rollback_error}"
                ) from publication_error
        raise
    finally:
        if file_fd is not None:
            os.close(file_fd)
        if not published:
            try:
                os.unlink(temporary, dir_fd=parent_fd)
            except FileNotFoundError:
                pass
            except OSError as cleanup_error:
                warnings.warn(
                    f"Temporary publication file could not be removed: "
                    f"{cleanup_error}",
                    RuntimeWarning,
                    stacklevel=2,
                )
        os.close(parent_fd)


def _secure_read_posix(
    root: Path,
    relative_path: str,
    *,
    before_open: BeforeOpen,
    reject_hardlinks: bool,
    max_bytes: Optional[int],
) -> bytes:
    parent_fd, name = open_relative_parent(root, relative_path, create=False)
    file_fd: Optional[int] = None
    try:
        if before_open is not None:
            before_open(root / relative_path)
        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
        file_fd = os.open(name, flags, dir_fd=parent_fd)
        assert file_fd is not None
        metadata = os.fstat(file_fd)
        if not stat.S_ISREG(metadata.st_mode):
            raise SecureMutationError(
                f"Source is not a regular file: {root / relative_path}."
            )
        if reject_hardlinks and metadata.st_nlink != 1:
            raise SecureMutationError(
                f"Source has multiple hard links and is unsafe for model context: "
                f"{root / relative_path}."
            )
        source_path = root / relative_path
        _reject_oversize(metadata.st_size, max_bytes, source_path)
        with os.fdopen(file_fd, "rb", closefd=False) as handle:
            return _read_stream_bounded(
                handle,
                max_bytes=max_bytes,
                source_path=source_path,
            )
    finally:
        if file_fd is not None:
            os.close(file_fd)
        os.close(parent_fd)


def _secure_delete_posix(
    root: Path,
    relative_path: str,
    expected_sha256: str,
    *,
    before_unlink: BeforeOpen,
) -> None:
    parent_fd, name = open_relative_parent(root, relative_path, create=False)
    quarantine = f".{name}.{uuid.uuid4().hex}.stale"
    quarantined = False
    committed = False
    try:
        if before_unlink is not None:
            before_unlink(root / relative_path)
        try:
            os.replace(
                name,
                quarantine,
                src_dir_fd=parent_fd,
                dst_dir_fd=parent_fd,
            )
        except FileNotFoundError:
            return
        quarantined = True
        _after_secure_quarantine(
            root / PurePosixPath(relative_path),
            root / PurePosixPath(relative_path).parent / quarantine,
        )
        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
        quarantine_fd = os.open(quarantine, flags, dir_fd=parent_fd)
        assert quarantine_fd is not None
        with os.fdopen(quarantine_fd, "rb") as handle:
            actual_sha256 = hashlib.sha256(handle.read()).hexdigest()
        if actual_sha256 != expected_sha256:
            _restore_posix_quarantine(parent_fd, quarantine, name, relative_path)
            quarantined = False
            raise SecureMutationError(
                f"Stale owned file changed before deletion: {relative_path}."
            )
        os.unlink(quarantine, dir_fd=parent_fd)
        quarantined = False
        committed = True
        try:
            os.fsync(parent_fd)
        except OSError as durability_error:
            warnings.warn(
                f"Deletion committed; directory durability could not be confirmed "
                f"for {relative_path}: {durability_error}",
                RuntimeWarning,
                stacklevel=2,
            )
    except BaseException as deletion_error:
        if not committed and quarantined:
            # If the primary error is already a SecureMutationError from a
            # failed restore (the original name is occupied by a concurrent
            # winner), re-raise it directly — retrying the restore would fail
            # the same way and mask the actionable "quarantine preserved" cause.
            if isinstance(deletion_error, SecureMutationError):
                raise
            try:
                _restore_posix_quarantine(parent_fd, quarantine, name, relative_path)
                quarantined = False
            except OSError as rollback_error:
                raise SecureMutationError(
                    f"Deletion failed and rollback could not restore "
                    f"{relative_path}; recovery preserved as {quarantine}: "
                    f"{rollback_error}"
                ) from deletion_error
        raise
    finally:
        os.close(parent_fd)


def _restore_posix_quarantine(
    parent_fd: int,
    quarantine: str,
    name: str,
    relative_path: str,
) -> None:
    try:
        os.link(
            quarantine,
            name,
            src_dir_fd=parent_fd,
            dst_dir_fd=parent_fd,
            follow_symlinks=False,
        )
    except FileExistsError as error:
        raise SecureMutationError(
            f"Could not restore changed file {relative_path}; original name is "
            f"occupied and quarantine preserved as {quarantine}."
        ) from error
    os.unlink(quarantine, dir_fd=parent_fd)


def _secure_write_windows(
    root: Path,
    relative_path: str,
    content: bytes,
    *,
    executable: Optional[bool],
    before_replace: BeforeReplace,
    expected_state: Optional[ExpectedFileState],
) -> None:
    del executable
    handles, parent, _parent_handle, name = _windows_pin_parent_chain(
        root,
        relative_path,
        create=True,
    )
    temporary_name = f".{name}.{uuid.uuid4().hex}.tmp"
    temporary_path = parent / temporary_name
    temporary_handle = None
    existing_handle = None
    previous_name = f".{name}.{uuid.uuid4().hex}.previous"
    previous_quarantined = False
    published = False
    try:
        temporary_handle = _windows_create_file(temporary_path, write=True)
        _windows_write_all(temporary_handle, content)
        try:
            existing_handle = _windows_open_regular(
                parent / name,
                read=True,
                delete=True,
                share_delete=False,
            )
        except FileNotFoundError:
            existing_handle = None
        _verify_expected_existence(expected_state, existing_handle is not None, relative_path)
        if existing_handle is not None:
            _windows_copy_readonly_attribute(existing_handle, temporary_handle)
            _windows_rename_handle(
                existing_handle,
                parent / previous_name,
                replace=False,
            )
            previous_quarantined = True
            _verify_expected_windows_bytes(
                existing_handle,
                expected_state,
                relative_path,
            )
            _after_secure_quarantine(
                root / PurePosixPath(relative_path),
                parent / previous_name,
            )
        if before_replace is not None:
            before_replace(root / PurePosixPath(relative_path))
        _windows_rename_handle(
            temporary_handle,
            parent / name,
            replace=False,
        )
        published = True
        if existing_handle is not None:
            try:
                _windows_dispose_handle(existing_handle)
            except OSError as cleanup_error:
                warnings.warn(
                    f"Publication committed; recovery preserved as {previous_name}: "
                    f"{cleanup_error}",
                    RuntimeWarning,
                    stacklevel=2,
                )
            else:
                previous_quarantined = False
    except BaseException as publication_error:
        if not published and existing_handle is not None and previous_quarantined:
            try:
                _windows_rename_handle(
                    existing_handle,
                    parent / name,
                    replace=False,
                )
                previous_quarantined = False
            except OSError as rollback_error:
                raise SecureMutationError(
                    f"Publication failed and rollback could not restore "
                    f"{relative_path}; recovery preserved as {previous_name}: "
                    f"{rollback_error}"
                ) from publication_error
        raise
    finally:
        if existing_handle is not None:
            _windows_close_handle(existing_handle)
        if temporary_handle is not None:
            if not published:
                try:
                    _windows_dispose_handle(temporary_handle)
                except OSError:
                    pass
            _windows_close_handle(temporary_handle)
        _windows_close_handles(handles)


def _secure_read_windows(
    root: Path,
    relative_path: str,
    *,
    before_open: BeforeOpen,
    reject_hardlinks: bool,
    max_bytes: Optional[int],
) -> bytes:
    handles, parent, _parent_handle, name = _windows_pin_parent_chain(
        root,
        relative_path,
        create=False,
    )
    file_handle = None
    try:
        if before_open is not None:
            before_open(root / PurePosixPath(relative_path))
        file_handle = _windows_open_regular(parent / name, read=True, delete=False)
        if reject_hardlinks and _windows_handle_link_count(file_handle) != 1:
            raise SecureMutationError(
                f"Source has multiple hard links and is unsafe for model context: "
                f"{root / PurePosixPath(relative_path)}."
            )
        source_path = root / PurePosixPath(relative_path)
        _reject_oversize(_windows_handle_size(file_handle), max_bytes, source_path)
        content = _windows_read_all(file_handle, max_bytes=max_bytes)
        if max_bytes is not None and len(content) > max_bytes:
            raise SecureMutationError(
                f"Source grew beyond secure read limit {max_bytes}: {source_path}."
            )
        return content
    finally:
        if file_handle is not None:
            _windows_close_handle(file_handle)
        _windows_close_handles(handles)


def _secure_delete_windows(
    root: Path,
    relative_path: str,
    expected_sha256: str,
    *,
    before_unlink: BeforeOpen,
) -> None:
    handles, parent, _parent_handle, name = _windows_pin_parent_chain(
        root,
        relative_path,
        create=False,
    )
    file_handle = None
    quarantine = f".{name}.{uuid.uuid4().hex}.stale"
    quarantined = False
    committed = False
    rollback_error = None
    try:
        if before_unlink is not None:
            before_unlink(root / PurePosixPath(relative_path))
        try:
            file_handle = _windows_open_regular(parent / name, read=True, delete=True)
        except FileNotFoundError:
            return
        _windows_rename_handle(file_handle, parent / quarantine, replace=False)
        quarantined = True
        actual_sha256 = hashlib.sha256(_windows_read_all(file_handle)).hexdigest()
        if actual_sha256 != expected_sha256:
            raise SecureMutationError(
                f"Stale owned file changed before deletion: {relative_path}."
            )
        _windows_dispose_handle(file_handle)
        quarantined = False
        committed = True
    except BaseException:
        if not committed and quarantined:
            try:
                _windows_rename_handle(file_handle, parent / name, replace=False)
                quarantined = False
            except OSError as error:
                rollback_error = SecureMutationError(
                    f"Deletion failed and rollback could not restore "
                    f"{relative_path}; recovery preserved as {quarantine}: "
                    f"{error}"
                )
        raise
    finally:
        if file_handle is not None:
            _windows_close_handle(file_handle)
        _windows_close_handles(handles)
        if rollback_error is not None:
            raise rollback_error


def _windows_pin_parent_chain(
    root: Path,
    relative_path: str,
    *,
    create: bool,
):
    parts = PurePosixPath(relative_path).parts
    handles = []
    current = root
    try:
        root_handle = _windows_open_directory(current)
        handles.append(root_handle)
        for part in parts[:-1]:
            current = current / part
            if create:
                try:
                    current.mkdir()
                except FileExistsError:
                    pass
            child_handle = _windows_open_directory(current)
            handles.append(child_handle)
        return handles, current, handles[-1], parts[-1]
    except BaseException:
        _windows_close_handles(handles)
        raise


def _windows_api():
    import ctypes
    from ctypes import wintypes

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CreateFileW.restype = wintypes.HANDLE
    kernel32.CreateFileW.argtypes = (
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.LPVOID,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.HANDLE,
    )
    kernel32.GetFileInformationByHandle.restype = wintypes.BOOL
    kernel32.GetFileInformationByHandle.argtypes = (wintypes.HANDLE, wintypes.LPVOID)
    kernel32.WriteFile.restype = wintypes.BOOL
    kernel32.WriteFile.argtypes = (
        wintypes.HANDLE,
        wintypes.LPCVOID,
        wintypes.DWORD,
        wintypes.LPDWORD,
        wintypes.LPVOID,
    )
    kernel32.ReadFile.restype = wintypes.BOOL
    kernel32.ReadFile.argtypes = (
        wintypes.HANDLE,
        wintypes.LPVOID,
        wintypes.DWORD,
        wintypes.LPDWORD,
        wintypes.LPVOID,
    )
    kernel32.FlushFileBuffers.restype = wintypes.BOOL
    kernel32.FlushFileBuffers.argtypes = (wintypes.HANDLE,)
    kernel32.SetFilePointerEx.restype = wintypes.BOOL
    kernel32.SetFilePointerEx.argtypes = (
        wintypes.HANDLE,
        ctypes.c_longlong,
        ctypes.POINTER(ctypes.c_longlong),
        wintypes.DWORD,
    )
    kernel32.SetFileInformationByHandle.restype = wintypes.BOOL
    kernel32.SetFileInformationByHandle.argtypes = (
        wintypes.HANDLE,
        ctypes.c_int,
        wintypes.LPVOID,
        wintypes.DWORD,
    )
    kernel32.CloseHandle.restype = wintypes.BOOL
    kernel32.CloseHandle.argtypes = (wintypes.HANDLE,)
    return ctypes, wintypes, kernel32


def _windows_open_directory(path: Path):
    ctypes, wintypes, kernel32 = _windows_api()
    handle = kernel32.CreateFileW(
        str(path),
        0x0020 | 0x0080,
        0x00000001 | 0x00000002,
        None,
        3,
        0x02000000 | 0x00200000,
        None,
    )
    if handle == wintypes.HANDLE(-1).value:
        _windows_raise_last_error(ctypes, f"Could not pin directory: {path}")
    _windows_require_safe_handle(handle, path, directory=True)
    return handle


def _windows_open_regular(
    path: Path,
    *,
    read: bool,
    delete: bool,
    share_delete: bool = False,
):
    ctypes, wintypes, kernel32 = _windows_api()
    access = (0x80000000 if read else 0) | (0x00010000 if delete else 0)
    handle = kernel32.CreateFileW(
        str(path),
        access,
        0x00000001 | 0x00000002 | (0x00000004 if share_delete else 0),
        None,
        3,
        0x00200000 | 0x08000000,
        None,
    )
    if handle == wintypes.HANDLE(-1).value:
        error = ctypes.get_last_error()
        if error in (2, 3):
            raise FileNotFoundError(path)
        raise ctypes.WinError(error, f"Could not open regular file: {path}")
    _windows_require_safe_handle(handle, path, directory=False)
    return handle


def _windows_copy_readonly_attribute(source_handle, target_handle) -> None:
    source_attributes = _windows_handle_attributes(source_handle)
    _windows_set_readonly_attribute(
        target_handle,
        bool(source_attributes & 0x00000001),
    )


def _windows_handle_attributes(handle) -> int:
    ctypes, wintypes, kernel32 = _windows_api()

    class FileInformation(ctypes.Structure):
        _fields_ = [
            ("dwFileAttributes", wintypes.DWORD),
            ("ftCreationTime", wintypes.FILETIME),
            ("ftLastAccessTime", wintypes.FILETIME),
            ("ftLastWriteTime", wintypes.FILETIME),
            ("dwVolumeSerialNumber", wintypes.DWORD),
            ("nFileSizeHigh", wintypes.DWORD),
            ("nFileSizeLow", wintypes.DWORD),
            ("nNumberOfLinks", wintypes.DWORD),
            ("nFileIndexHigh", wintypes.DWORD),
            ("nFileIndexLow", wintypes.DWORD),
        ]

    information = FileInformation()
    if not kernel32.GetFileInformationByHandle(handle, ctypes.byref(information)):
        _windows_raise_last_error(ctypes, "Could not inspect file handle")
    return information.dwFileAttributes


def _windows_handle_link_count(handle) -> int:
    ctypes, wintypes, kernel32 = _windows_api()

    class FileInformation(ctypes.Structure):
        _fields_ = [
            ("dwFileAttributes", wintypes.DWORD),
            ("ftCreationTime", wintypes.FILETIME),
            ("ftLastAccessTime", wintypes.FILETIME),
            ("ftLastWriteTime", wintypes.FILETIME),
            ("dwVolumeSerialNumber", wintypes.DWORD),
            ("nFileSizeHigh", wintypes.DWORD),
            ("nFileSizeLow", wintypes.DWORD),
            ("nNumberOfLinks", wintypes.DWORD),
            ("nFileIndexHigh", wintypes.DWORD),
            ("nFileIndexLow", wintypes.DWORD),
        ]

    information = FileInformation()
    if not kernel32.GetFileInformationByHandle(handle, ctypes.byref(information)):
        _windows_raise_last_error(ctypes, "Could not inspect file link count")
    return information.nNumberOfLinks


def _windows_set_readonly_attribute(handle, readonly: bool) -> None:
    ctypes, wintypes, kernel32 = _windows_api()

    class FileBasicInfo(ctypes.Structure):
        _fields_ = [
            ("CreationTime", ctypes.c_longlong),
            ("LastAccessTime", ctypes.c_longlong),
            ("LastWriteTime", ctypes.c_longlong),
            ("ChangeTime", ctypes.c_longlong),
            ("FileAttributes", wintypes.DWORD),
        ]

    information = FileBasicInfo(
        0,
        0,
        0,
        0,
        0x00000001 if readonly else 0x00000080,
    )
    if not kernel32.SetFileInformationByHandle(
        handle,
        0,
        ctypes.byref(information),
        ctypes.sizeof(information),
    ):
        _windows_raise_last_error(ctypes, "Could not preserve file attributes")


def _windows_create_file(path: Path, *, write: bool):
    ctypes, wintypes, kernel32 = _windows_api()
    access = (0x40000000 if write else 0) | 0x00010000
    handle = kernel32.CreateFileW(
        str(path),
        access,
        0x00000001 | 0x00000002 | 0x00000004,
        None,
        1,
        0x00000080 | 0x00200000,
        None,
    )
    if handle == wintypes.HANDLE(-1).value:
        _windows_raise_last_error(ctypes, f"Could not create temporary file: {path}")
    return handle


def _windows_regular_metadata(path: Path):
    try:
        metadata = os.lstat(path)
    except FileNotFoundError:
        return None
    if _is_link_or_reparse(metadata) or not stat.S_ISREG(metadata.st_mode):
        raise SecureMutationError(
            f"Destination target is a link, reparse point, or non-regular file: {path}."
        )
    return metadata


def _windows_require_safe_handle(handle, path: Path, *, directory: bool) -> None:
    ctypes, wintypes, kernel32 = _windows_api()

    class FileInformation(ctypes.Structure):
        _fields_ = [
            ("dwFileAttributes", wintypes.DWORD),
            ("ftCreationTime", wintypes.FILETIME),
            ("ftLastAccessTime", wintypes.FILETIME),
            ("ftLastWriteTime", wintypes.FILETIME),
            ("dwVolumeSerialNumber", wintypes.DWORD),
            ("nFileSizeHigh", wintypes.DWORD),
            ("nFileSizeLow", wintypes.DWORD),
            ("nNumberOfLinks", wintypes.DWORD),
            ("nFileIndexHigh", wintypes.DWORD),
            ("nFileIndexLow", wintypes.DWORD),
        ]

    information = FileInformation()
    if not kernel32.GetFileInformationByHandle(handle, ctypes.byref(information)):
        _windows_close_handle(handle)
        _windows_raise_last_error(ctypes, f"Could not inspect pinned path: {path}")
    attributes = information.dwFileAttributes
    is_directory = bool(attributes & 0x00000010)
    if attributes & 0x00000400 or is_directory != directory:
        _windows_close_handle(handle)
        kind = "directory" if directory else "regular file"
        raise SecureMutationError(f"Pinned path is not a safe {kind}: {path}.")


def _windows_write_all(handle, content: bytes) -> None:
    ctypes, wintypes, kernel32 = _windows_api()
    offset = 0
    while offset < len(content):
        chunk = content[offset : offset + 1024 * 1024]
        buffer = ctypes.create_string_buffer(chunk)
        written = wintypes.DWORD()
        if not kernel32.WriteFile(
            handle,
            buffer,
            len(chunk),
            ctypes.byref(written),
            None,
        ):
            _windows_raise_last_error(ctypes, "Could not write temporary file")
        offset += written.value
    if not kernel32.FlushFileBuffers(handle):
        _windows_raise_last_error(ctypes, "Could not flush temporary file")


def _windows_read_all(handle, *, max_bytes: Optional[int] = None) -> bytes:
    ctypes, wintypes, kernel32 = _windows_api()
    zero = ctypes.c_longlong(0)
    if not kernel32.SetFilePointerEx(handle, zero, None, 0):
        _windows_raise_last_error(ctypes, "Could not rewind file handle")
    chunks = []
    remaining = max_bytes + 1 if max_bytes is not None else None
    while True:
        chunk_size = 1024 * 1024
        if remaining is not None:
            if remaining == 0:
                break
            chunk_size = min(chunk_size, remaining)
        buffer = ctypes.create_string_buffer(chunk_size)
        read = wintypes.DWORD()
        if not kernel32.ReadFile(
            handle,
            buffer,
            len(buffer),
            ctypes.byref(read),
            None,
        ):
            _windows_raise_last_error(ctypes, "Could not read file handle")
        if read.value == 0:
            break
        chunks.append(buffer.raw[: read.value])
        if remaining is not None:
            remaining -= read.value
    return b"".join(chunks)


def _windows_handle_size(handle) -> int:
    ctypes, wintypes, kernel32 = _windows_api()

    class FileInformation(ctypes.Structure):
        _fields_ = [
            ("dwFileAttributes", wintypes.DWORD),
            ("ftCreationTime", wintypes.FILETIME),
            ("ftLastAccessTime", wintypes.FILETIME),
            ("ftLastWriteTime", wintypes.FILETIME),
            ("dwVolumeSerialNumber", wintypes.DWORD),
            ("nFileSizeHigh", wintypes.DWORD),
            ("nFileSizeLow", wintypes.DWORD),
            ("nNumberOfLinks", wintypes.DWORD),
            ("nFileIndexHigh", wintypes.DWORD),
            ("nFileIndexLow", wintypes.DWORD),
        ]

    information = FileInformation()
    if not kernel32.GetFileInformationByHandle(handle, ctypes.byref(information)):
        _windows_raise_last_error(ctypes, "Could not inspect file size")
    return (information.nFileSizeHigh << 32) | information.nFileSizeLow


def _windows_rename_handle(handle, target: Path, *, replace: bool) -> None:
    ctypes, wintypes, kernel32 = _windows_api()

    class RenameInformation(ctypes.Structure):
        _fields_ = [
            ("Flags", wintypes.DWORD),
            ("RootDirectory", wintypes.HANDLE),
            ("FileNameLength", wintypes.DWORD),
            ("FileName", wintypes.WCHAR * 1),
        ]

    encoded_name = str(target).encode("utf-16-le")
    buffer_size = ctypes.sizeof(RenameInformation) + len(encoded_name)
    buffer = ctypes.create_string_buffer(buffer_size)
    information = ctypes.cast(
        buffer,
        ctypes.POINTER(RenameInformation),
    ).contents
    information.Flags = 0x00000001 if replace else 0
    information.RootDirectory = None
    information.FileNameLength = len(encoded_name)
    ctypes.memmove(
        ctypes.addressof(buffer) + RenameInformation.FileName.offset,
        encoded_name,
        len(encoded_name),
    )
    if not kernel32.SetFileInformationByHandle(
        handle,
        3,
        buffer,
        buffer_size,
    ):
        _windows_raise_last_error(ctypes, f"Could not rename file handle to {target!s}")


def _windows_dispose_handle(handle) -> None:
    ctypes, wintypes, kernel32 = _windows_api()

    class DispositionInformation(ctypes.Structure):
        _fields_ = [("DeleteFile", wintypes.BOOLEAN)]

    information = DispositionInformation(True)
    if not kernel32.SetFileInformationByHandle(
        handle,
        4,
        ctypes.byref(information),
        ctypes.sizeof(information),
    ):
        _windows_raise_last_error(ctypes, "Could not dispose quarantined file")


def _windows_close_handle(handle) -> None:
    _ctypes, _wintypes, kernel32 = _windows_api()
    kernel32.CloseHandle(handle)


def _windows_close_handles(handles) -> None:
    for handle in reversed(handles):
        _windows_close_handle(handle)


def _windows_raise_last_error(ctypes, message: str) -> None:
    error = ctypes.get_last_error()
    raise ctypes.WinError(error, message)


def _stat_target(parent_fd: int, name: str):
    try:
        return os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
    except FileNotFoundError:
        return None


def _unlink_posix_if_identity(
    parent_fd: int,
    name: str,
    expected_metadata,
    relative_path: str,
) -> None:
    current = _stat_target(parent_fd, name)
    if _stat_identity(current) != _stat_identity(expected_metadata):
        raise SecureMutationError(
            f"Published destination identity changed during rollback: "
            f"{relative_path}."
        )
    os.unlink(name, dir_fd=parent_fd)


def _verify_expected_existence(
    expected_state: Optional[ExpectedFileState],
    exists: bool,
    relative_path: str,
) -> None:
    if expected_state is not None and expected_state.exists != exists:
        raise SecureMutationError(
            f"Destination changed after authorization: {relative_path}."
        )


def _verify_expected_posix_bytes(
    parent_fd: int,
    name: str,
    expected_state: Optional[ExpectedFileState],
    relative_path: str,
) -> None:
    if expected_state is None or expected_state.sha256 is None:
        return
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    file_fd = os.open(name, flags, dir_fd=parent_fd)
    try:
        actual = _hash_file_descriptor(file_fd)
    finally:
        os.close(file_fd)
    if actual != expected_state.sha256:
        raise SecureMutationError(
            f"Destination changed after authorization: {relative_path}."
        )


def _verify_expected_windows_bytes(
    handle,
    expected_state: Optional[ExpectedFileState],
    relative_path: str,
) -> None:
    if expected_state is None or expected_state.sha256 is None:
        return
    actual = hashlib.sha256(_windows_read_all(handle)).hexdigest()
    if actual != expected_state.sha256:
        raise SecureMutationError(
            f"Destination changed after authorization: {relative_path}."
        )


def _hash_file_descriptor(file_fd: int) -> str:
    digest = hashlib.sha256()
    duplicate_fd = os.dup(file_fd)
    assert duplicate_fd is not None
    with os.fdopen(duplicate_fd, "rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def _supports_posix_rename_noreplace() -> bool:
    if is_windows_host():
        return False
    try:
        import ctypes

        libc = ctypes.CDLL(None, use_errno=True)
    except (ImportError, OSError):
        return False
    if sys.platform.startswith("linux"):
        return hasattr(libc, "renameat2")
    if sys.platform == "darwin":
        return hasattr(libc, "renameatx_np")
    return False


def _posix_fchmod(file_fd: int, mode: int) -> None:
    import ctypes

    libc = ctypes.CDLL(None, use_errno=True)
    operation = getattr(libc, "fchmod", None)
    if operation is None:
        raise SecureMutationError(
            "Secure POSIX replacement requires descriptor-based chmod."
        )
    if operation.__call__(file_fd, mode) != 0:
        error_number = ctypes.get_errno()
        raise OSError(error_number, os.strerror(error_number))


def _posix_rename_noreplace(parent_fd: int, source: str, target: str) -> None:
    """Rename within one pinned parent without replacing the target."""
    import ctypes
    import errno

    libc = ctypes.CDLL(None, use_errno=True)
    source_bytes = os.fsencode(source)
    target_bytes = os.fsencode(target)
    if sys.platform.startswith("linux") and hasattr(libc, "renameat2"):
        operation = libc.renameat2
        operation.argtypes = (
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_uint,
        )
        result = operation(
            parent_fd,
            source_bytes,
            parent_fd,
            target_bytes,
            _RENAME_NOREPLACE,
        )
    elif sys.platform == "darwin" and hasattr(libc, "renameatx_np"):
        operation = libc.renameatx_np
        operation.argtypes = (
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_uint,
        )
        result = operation(
            parent_fd,
            source_bytes,
            parent_fd,
            target_bytes,
            _POSIX_RENAME_EXCL,
        )
    else:
        raise SecureMutationError(
            "This POSIX host has no supported no-replace rename primitive."
        )
    if result == 0:
        return
    error_number = ctypes.get_errno()
    if error_number == errno.EEXIST:
        raise FileExistsError(error_number, os.strerror(error_number), target)
    if error_number == errno.ENOENT:
        raise FileNotFoundError(error_number, os.strerror(error_number), source)
    if sys.platform.startswith("linux") and error_number == errno.EINVAL:
        raise SecureMutationError(
            f"renameat2 RENAME_NOREPLACE is unsupported on this filesystem: "
            f"{os.strerror(error_number)}"
        )
    if sys.platform == "darwin" and error_number in (
        getattr(errno, "ENOTSUP", 0),
        getattr(errno, "ENOSYS", 0),
    ):
        raise SecureMutationError(
            f"renameatx_np RENAME_EXCL is unsupported on this filesystem: "
            f"{os.strerror(error_number)}"
        )
    raise OSError(error_number, os.strerror(error_number), source, target)


def _reject_oversize(
    size: int,
    max_bytes: Optional[int],
    source_path: Path,
) -> None:
    if max_bytes is not None and size > max_bytes:
        raise SecureMutationError(
            f"Source size {size} exceeds secure read limit {max_bytes}: "
            f"{source_path}."
        )


def _read_stream_bounded(
    stream: BinaryIO,
    *,
    max_bytes: Optional[int],
    source_path: Path,
) -> bytes:
    content = stream.read() if max_bytes is None else stream.read(max_bytes + 1)
    if max_bytes is not None and len(content) > max_bytes:
        raise SecureMutationError(
            f"Source grew beyond secure read limit {max_bytes}: {source_path}."
        )
    return content


def _verify_parent_identity(
    root: Path,
    relative_path: str,
    pinned_parent_fd: int,
) -> None:
    reopened_fd: Optional[int] = None
    try:
        reopened_fd, _ = open_relative_parent(root, relative_path, create=False)
        if _stat_identity(os.fstat(reopened_fd)) != _stat_identity(
            os.fstat(pinned_parent_fd)
        ):
            raise SecureMutationError(
                f"Destination parent identity changed at mutation time: "
                f"{root / relative_path}."
            )
    except OSError as error:
        if isinstance(error, SecureMutationError):
            raise
        raise SecureMutationError(
            f"Destination parent became unsafe at mutation time: "
            f"{root / relative_path}."
        ) from error
    finally:
        if reopened_fd is not None:
            os.close(reopened_fd)


def _verify_target_identity(
    parent_fd: int,
    name: str,
    original_target,
    destination: Path,
) -> None:
    current_target = _stat_target(parent_fd, name)
    if current_target is not None and not stat.S_ISREG(current_target.st_mode):
        raise SecureMutationError(
            f"Destination target became non-regular at mutation time: {destination}."
        )
    if _stat_identity(current_target) != _stat_identity(original_target):
        raise SecureMutationError(
            f"Destination target identity changed at mutation time: {destination}."
        )


def _replacement_mode(metadata, executable: Optional[bool]) -> int:
    mode = stat.S_IMODE(metadata.st_mode) if metadata is not None else 0o644
    if executable is True:
        return mode | 0o111 if metadata is not None else 0o755
    if executable is False:
        return mode & ~0o111
    return mode


def _stat_identity(metadata) -> Optional[Tuple[int, int, int]]:
    if metadata is None:
        return None
    return metadata.st_dev, metadata.st_ino, stat.S_IFMT(metadata.st_mode)


def _is_link_or_reparse(metadata) -> bool:
    return stat.S_ISLNK(metadata.st_mode) or bool(
        getattr(metadata, "st_file_attributes", 0) & _REPARSE_POINT_FLAG
    )


def _fsync_directory(path: Path) -> None:
    if is_windows_host():
        return
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    descriptor = os.open(path, flags)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
