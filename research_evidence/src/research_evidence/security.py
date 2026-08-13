"""Created 2026-08-12. Offline network and subprocess policy guards."""
from __future__ import annotations

from contextlib import AbstractContextManager
import ipaddress
import os
from pathlib import Path
import socket
from typing import Callable, Mapping, Optional, Sequence, TypeVar
from urllib.parse import urlsplit

from .errors import NetworkAccessDenied

_T = TypeVar("_T")

_FORBIDDEN_EXECUTABLES = {
    "bash",
    "curl",
    "cmd",
    "npm",
    "pip",
    "powershell",
    "pwsh",
    "sh",
    "wget",
    "zsh",
}
_PROXY_VARIABLES = ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY")


def _address_host(address: object) -> str:
    """Extract a socket host from common address shapes."""
    if isinstance(address, tuple) and address:
        return str(address[0])
    return str(address)


def _is_loopback_host(host: str) -> bool:
    """Return whether a literal host is loopback; reject DNS names."""
    if host.lower() == "localhost":
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def validate_offline_environment(
    environment: Optional[Mapping[str, str]] = None,
) -> None:
    """Reject proxy settings that could route normal processing remotely.

    Args:
        environment: Optional environment mapping; ``os.environ`` is used by default.

    Returns:
        ``None`` when no outbound proxy is configured.

    Raises:
        NetworkAccessDenied: If an HTTP, HTTPS, or generic proxy is configured.

    Example:
        ``validate_offline_environment({})`` passes the offline check.
    """
    values = environment or os.environ
    configured = [name for name in _PROXY_VARIABLES if values.get(name)]
    if configured:
        raise NetworkAccessDenied(
            "Offline processing rejects configured proxy variables: "
            + ", ".join(configured)
        )


def validate_http_target(target: str) -> str:
    """Reject remote HTTP targets before an HTTP client can issue a request.

    Args:
        target: URL or local target string supplied by an untrusted caller.

    Returns:
        The validated target when it is not a remote URL.

    Raises:
        NetworkAccessDenied: If the target is a non-loopback HTTP(S) URL.

    Example:
        ``validate_http_target("/sources/search")`` returns the local path.
    """
    parsed = urlsplit(target)
    if parsed.scheme in {"http", "https"} and parsed.hostname:
        if not _is_loopback_host(parsed.hostname):
            raise NetworkAccessDenied("remote HTTP targets are disabled in offline mode")
    elif parsed.scheme or parsed.netloc:
        raise NetworkAccessDenied("remote URL targets are disabled in offline mode")
    return target


def validate_browser_target(target: str) -> str:
    """Apply the same-origin browser target policy to a rendered link/request.

    Args:
        target: Browser URL or same-origin path.

    Returns:
        The validated same-origin target.

    Raises:
        NetworkAccessDenied: If the target points to a remote host or scheme.

    Example:
        ``validate_browser_target("/review/history")`` remains local.
    """
    return validate_http_target(target)


def validate_model_loader_kwargs(kwargs: Mapping[str, object]) -> dict[str, object]:
    """Require local-cache-only model loading and reject hidden downloads.

    Args:
        kwargs: Adapter keyword arguments supplied to a local model loader.

    Returns:
        A copied validated mapping.

    Raises:
        NetworkAccessDenied: If downloads or remote cache loading are enabled.

    Example:
        ``validate_model_loader_kwargs({"local_files_only": True})`` passes.
    """
    validated = dict(kwargs)
    if validated.get("local_files_only") is not True:
        raise NetworkAccessDenied("model loading requires local_files_only=True")
    if validated.get("download") is True or validated.get("allow_download") is True:
        raise NetworkAccessDenied("model downloads are disabled during processing")
    return validated


def validate_subprocess_command(
    command: Sequence[str],
    allowed_executables: Optional[set[str]] = None,
) -> str:
    """Validate a local parser/OCR subprocess against an explicit allowlist.

    Args:
        command: Executable and arguments that a local worker proposes to run.
        allowed_executables: Basenames explicitly enabled in the inventory.

    Returns:
        The normalized executable basename when it is allowed.

    Raises:
        ValueError: If the command is empty, forbidden, or not allowlisted.

    Example:
        ``validate_subprocess_command(["pdftotext"], {"pdftotext"})``.
    """
    if not command:
        raise ValueError("Subprocess command cannot be empty.")
    executable = Path(command[0]).name.lower()
    if executable in _FORBIDDEN_EXECUTABLES:
                raise ValueError(f"forbidden subprocess executable: {executable}.")
    allowed = {item.lower() for item in (allowed_executables or set())}
    if executable not in allowed:
        raise ValueError(f"Subprocess executable is not in the local allowlist: {executable}.")
    if any(any(character in argument for character in (";", "|", "&", "`", "\n")) for argument in command):
        raise ValueError("Shell metacharacters are forbidden in subprocess arguments.")
    return executable


class OfflineNetworkGuard(AbstractContextManager["OfflineNetworkGuard"]):
    """Deny non-loopback socket attempts for the current process context.

    Args:
        None.

    Returns:
        A context manager restoring socket functions on exit.

    Example:
        ``with OfflineNetworkGuard():`` protects a local processing operation.
    """

    def __init__(self) -> None:
        """Create an inactive guard with no global patches applied."""
        self._original_connect: Optional[Callable[..., object]] = None
        self._original_connect_ex: Optional[Callable[..., object]] = None
        self._original_create_connection: Optional[Callable[..., object]] = None

    def __enter__(self) -> "OfflineNetworkGuard":
        """Install process-level socket checks and return this guard.

        Args:
            None.

        Returns:
            The active guard.

        Example:
            ``with OfflineNetworkGuard() as guard:`` enters the protected scope.
        """
        if self._original_connect is not None:
            raise RuntimeError("OfflineNetworkGuard cannot be entered twice.")
        validate_offline_environment()
        self._original_connect = socket.socket.connect
        self._original_connect_ex = socket.socket.connect_ex
        self._original_create_connection = socket.create_connection
        original_connect = self._original_connect
        original_connect_ex = self._original_connect_ex
        original_create_connection = self._original_create_connection

        def _guarded_connect(sock: socket.socket, address: object) -> object:
            """Reject remote destinations before delegating to the socket."""
            host = _address_host(address)
            if not _is_loopback_host(host):
                raise NetworkAccessDenied("outbound network is disabled outside loopback.")
            return original_connect(sock, address)

        def _guarded_connect_ex(sock: socket.socket, address: object) -> object:
            """Reject remote connect_ex destinations before delegation."""
            host = _address_host(address)
            if not _is_loopback_host(host):
                raise NetworkAccessDenied("outbound network is disabled outside loopback.")
            return original_connect_ex(sock, address)

        def _guarded_create_connection(*args: object, **kwargs: object) -> object:
            """Reject remote create_connection destinations before delegation."""
            if not args:
                raise NetworkAccessDenied("Socket destination is required and must be loopback.")
            host = _address_host(args[0])
            if isinstance(args[0], tuple) and args[0]:
                host = _address_host(args[0])
            elif isinstance(args[0], str):
                host = args[0]
            if not _is_loopback_host(host):
                raise NetworkAccessDenied("outbound network is disabled outside loopback.")
            return original_create_connection(*args, **kwargs)

        socket.socket.connect = _guarded_connect  # type: ignore[method-assign]
        socket.socket.connect_ex = _guarded_connect_ex  # type: ignore[method-assign]
        socket.create_connection = _guarded_create_connection  # type: ignore[assignment]
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        """Restore the original socket functions after protected processing.

        Args:
            exc_type: Exception type supplied by the context protocol.
            exc: Exception instance supplied by the context protocol.
            traceback: Exception traceback supplied by the context protocol.

        Returns:
            ``None``; exceptions are never suppressed.

        Example:
            Leaving ``with OfflineNetworkGuard():`` restores normal test state.
        """
        if self._original_connect is not None:
            socket.socket.connect = self._original_connect  # type: ignore[method-assign]
        if self._original_connect_ex is not None:
            socket.socket.connect_ex = self._original_connect_ex  # type: ignore[method-assign]
        if self._original_create_connection is not None:
            socket.create_connection = self._original_create_connection  # type: ignore[assignment]
        self._original_connect = None
        self._original_connect_ex = None
        self._original_create_connection = None
        return None
