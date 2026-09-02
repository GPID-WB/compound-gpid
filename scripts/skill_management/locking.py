"""Cross-platform held-handle project lifecycle locking."""
from __future__ import annotations

import errno
import os
from contextlib import contextmanager
from pathlib import Path
import stat
import time
from typing import Callable, Iterator, Optional

import secure_fs


LOCK_PATH = ".compound-gpid/skill-transaction.lock"
_REPARSE_POINT_FLAG = 0x400


class LockError(OSError):
    """Base lifecycle lock failure."""


class LockSecurityError(LockError):
    """Raised when the lock route is not a real no-follow path."""


class LockTimeoutError(LockError):
    """Raised when another process holds the lifecycle lock past timeout."""


def _is_link_or_reparse(metadata: os.stat_result) -> bool:
    return stat.S_ISLNK(metadata.st_mode) or bool(
        getattr(metadata, "st_file_attributes", 0) & _REPARSE_POINT_FLAG
    )


def _validate_project_root(project_root: Path) -> Path:
    root = Path(project_root)
    try:
        metadata = os.lstat(str(root))
    except OSError as error:
        raise LockSecurityError(f"Project root cannot be inspected safely: {root}") from error
    if _is_link_or_reparse(metadata) or not stat.S_ISDIR(metadata.st_mode):
        raise LockSecurityError(
            f"Project root must be one real directory: {root}"
        )
    return root.resolve(strict=True)


def _ensure_state_directory(root: Path) -> None:
    state = root / ".compound-gpid"
    try:
        os.mkdir(str(state))
    except FileExistsError:
        pass
    except OSError as error:
        raise LockSecurityError(
            f"Cannot create lifecycle state directory safely: {state}"
        ) from error
    try:
        metadata = os.lstat(str(state))
    except OSError as error:
        raise LockSecurityError(
            f"Lifecycle state directory cannot be inspected safely: {state}"
        ) from error
    if _is_link_or_reparse(metadata) or not stat.S_ISDIR(metadata.st_mode):
        raise LockSecurityError(
            ".compound-gpid must be one real directory, not a link or reparse point"
        )


def _open_posix_lock(root: Path) -> int:
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
    root_fd = os.open(str(root), flags)
    state_fd: Optional[int] = None
    try:
        state_fd = os.open(".compound-gpid", flags, dir_fd=root_fd)
        file_flags = os.O_RDWR | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0)
        file_fd = os.open(
            "skill-transaction.lock", file_flags, 0o600, dir_fd=state_fd
        )
        metadata = os.fstat(file_fd)
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
            os.close(file_fd)
            raise LockSecurityError("Lifecycle lock must be one regular file")
        return file_fd
    except OSError as error:
        if isinstance(error, LockSecurityError):
            raise
        raise LockSecurityError("Lifecycle lock path is unsafe") from error
    finally:
        if state_fd is not None:
            os.close(state_fd)
        os.close(root_fd)


def _open_windows_lock(root: Path) -> int:
    import ctypes
    import msvcrt
    from ctypes import wintypes

    try:
        ancestor_handles, parent, _parent_handle, name = (
            secure_fs._windows_pin_parent_chain(  # pylint: disable=protected-access
                root, LOCK_PATH, create=False
            )
        )
    except OSError as error:
        raise LockSecurityError("Lifecycle lock ancestors are unsafe") from error
    path = parent / name
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
    handle = None
    try:
        handle = kernel32.CreateFileW(
            secure_fs._windows_long_path(path),  # pylint: disable=protected-access
            0x80000000 | 0x40000000,
            0x00000001 | 0x00000002,
            None,
            4,
            0x00200000 | 0x08000000,
            None,
        )
        if handle == wintypes.HANDLE(-1).value:
            error = ctypes.get_last_error()
            handle = None
            raise LockSecurityError(
                f"Cannot open lifecycle lock safely: {ctypes.WinError(error)}"
            )
        attributes = secure_fs._windows_handle_attributes(  # pylint: disable=protected-access
            handle
        )
        if attributes & (0x00000400 | 0x00000010):
            raise LockSecurityError(
                "Lifecycle lock is a reparse point or directory"
            )
        if secure_fs._windows_handle_link_count(  # pylint: disable=protected-access
            handle
        ) != 1:
            raise LockSecurityError("Lifecycle lock must not have hard links")
        file_fd = msvcrt.open_osfhandle(handle, os.O_RDWR)
        handle = None
        metadata = os.fstat(file_fd)
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
            os.close(file_fd)
            raise LockSecurityError("Lifecycle lock must be one regular file")
        return file_fd
    finally:
        if handle is not None:
            kernel32.CloseHandle(handle)
        secure_fs._windows_close_handles(  # pylint: disable=protected-access
            ancestor_handles
        )


def _open_lock_file(project_root: Path) -> int:
    root = _validate_project_root(project_root)
    _ensure_state_directory(root)
    if os.name == "nt":
        return _open_windows_lock(root)
    return _open_posix_lock(root)


def _try_lock(file_fd: int) -> bool:
    if os.name == "nt":
        import msvcrt

        if os.fstat(file_fd).st_size == 0:
            os.lseek(file_fd, 0, os.SEEK_SET)
            os.write(file_fd, b"\0")
            os.fsync(file_fd)
        os.lseek(file_fd, 0, os.SEEK_SET)
        try:
            msvcrt.locking(file_fd, msvcrt.LK_NBLCK, 1)
        except OSError as error:
            if error.errno in (errno.EACCES, errno.EAGAIN, errno.EDEADLK):
                return False
            raise
        return True

    import fcntl

    try:
        fcntl.flock(file_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError as error:
        if error.errno in (errno.EACCES, errno.EAGAIN):
            return False
        raise
    return True


def _unlock(file_fd: int) -> None:
    if os.name == "nt":
        import msvcrt

        os.lseek(file_fd, 0, os.SEEK_SET)
        msvcrt.locking(file_fd, msvcrt.LK_UNLCK, 1)
        return
    import fcntl

    fcntl.flock(file_fd, fcntl.LOCK_UN)


@contextmanager
def project_lifecycle_lock(
    project_root: Path,
    *,
    timeout: float = 30.0,
    monotonic: Callable[[], float] = time.monotonic,
    sleeper: Callable[[float], None] = time.sleep,
) -> Iterator[None]:
    """Hold the project lifecycle lock for one complete critical section.

    Args:
        project_root: Real project directory that owns lifecycle state.
        timeout: Maximum advisory-lock wait in seconds.
        monotonic: Injectable monotonic clock for deterministic timeout tests.
        sleeper: Injectable bounded wait function.

    Yields:
        ``None`` while the operating-system lock remains held by one file handle.

    Raises:
        LockSecurityError: If the lock path contains an unsafe filesystem object.
        LockTimeoutError: If another writer holds the lock past ``timeout``.

    Example:
        ``with project_lifecycle_lock(root): publish()``
    """
    if timeout < 0:
        raise ValueError("Lifecycle lock timeout must be non-negative")
    file_fd = _open_lock_file(Path(project_root))
    acquired = False
    started = monotonic()
    try:
        while True:
            if _try_lock(file_fd):
                acquired = True
                break
            if monotonic() - started >= timeout:
                raise LockTimeoutError(
                    f"Timed out after {timeout:g}s waiting for {LOCK_PATH}"
                )
            sleeper(min(0.05, timeout))
        yield
    finally:
        if acquired:
            _unlock(file_fd)
        os.close(file_fd)
