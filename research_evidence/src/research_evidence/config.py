"""Created 2026-08-12. Runtime, path, and local-only settings."""
from __future__ import annotations

from dataclasses import dataclass
import ipaddress
from pathlib import Path, PurePath
from typing import Optional, Union
from urllib.parse import urlsplit

from .errors import PathPolicyError

SUPPORTED_MINIMUM = (3, 11)
SUPPORTED_EXCLUSIVE_MAXIMUM = (3, 14)


def ensure_supported_runtime(version: Optional[tuple[int, int, int]] = None) -> None:
    """Require a Python interpreter in the supported package range.

    Args:
        version: Optional ``(major, minor, micro)`` tuple for deterministic tests;
            the active interpreter is used when omitted.

    Returns:
        ``None`` when the version is supported.

    Raises:
        RuntimeError: If the version is below 3.11 or at least 3.14.

    Example:
        ``ensure_supported_runtime((3, 11, 0))`` validates the lower boundary.
    """
    import sys

    candidate = version or sys.version_info[:3]
    major_minor = candidate[:2]
    if not (
        SUPPORTED_MINIMUM <= major_minor < SUPPORTED_EXCLUSIVE_MAXIMUM
    ):
        raise RuntimeError(
            "Research Evidence requires Python >=3.11 and <3.14; "
            f"received {candidate[0]}.{candidate[1]}.{candidate[2]}."
        )


def validate_loopback_host(host: str) -> str:
    """Validate and return a loopback-only bind host.

    Args:
        host: IPv4 or IPv6 address to validate.

    Returns:
        The original host string when it identifies a loopback address.

    Raises:
        ValueError: If ``host`` is not a literal loopback address.

    Example:
        ``validate_loopback_host("127.0.0.1")`` returns ``"127.0.0.1"``.
    """
    try:
        address = ipaddress.ip_address(host)
    except ValueError as error:
        raise ValueError("Service bind host must be a literal loopback address.") from error
    if not address.is_loopback:
        raise ValueError("Service bind host must be loopback-only.")
    return host


def _validate_directory(path: Path, label: str) -> Path:
    """Validate one non-symlink directory for internal settings use."""
    candidate = Path(path).expanduser()
    if candidate.is_symlink() or not candidate.exists() or not candidate.is_dir():
        raise PathPolicyError(f"{label} must be an existing regular directory: {candidate}.")
    return candidate.resolve()


def _reject_url(value: str) -> None:
    """Reject URL-like input before filesystem resolution."""
    parsed = urlsplit(value)
    if parsed.scheme or parsed.netloc or value.startswith("//"):
        raise PathPolicyError("URL and remote-host resources are not allowed.")


@dataclass(frozen=True)
class RuntimeSettings:
    """Describe the confined, offline runtime boundary.

    Args:
        project_root: Existing repository root containing the resources folder.
        resources_root: Existing local directory containing active resources.
        evidence_root: Canonical evidence directory below ``project_root``.
        bind_host: Literal loopback address used by a future local service.
        offline: Whether normal processing must remain offline.
        model_cache_only: Whether model loaders must use local cache only.

    Returns:
        An immutable runtime settings object.

    Example:
        ``RuntimeSettings.from_paths(repo, repo / "resources")`` creates settings.
    """

    project_root: Path
    resources_root: Path
    evidence_root: Path
    bind_host: str = "127.0.0.1"
    offline: bool = True
    model_cache_only: bool = True

    @classmethod
    def from_paths(
        cls,
        project_root: Path,
        resources_root: Union[str, PurePath],
        *,
        bind_host: str = "127.0.0.1",
    ) -> "RuntimeSettings":
        """Construct settings after validating project and resource confinement.

        Args:
            project_root: Existing repository root.
            resources_root: Existing resource directory, absolute or project-relative.
            bind_host: Literal loopback address for the local service boundary.

        Returns:
            Validated runtime settings.

        Raises:
            PathPolicyError: If a root is missing, linked, or outside the project.
            ValueError: If ``bind_host`` is not loopback-only.

        Example:
            ``RuntimeSettings.from_paths(Path.cwd(), Path("resources"))``.
        """
        ensure_supported_runtime()
        project = _validate_directory(Path(project_root), "Project root")
        validate_loopback_host(bind_host)
        raw_resources = Path(resources_root).expanduser()
        resources = raw_resources if raw_resources.is_absolute() else project / raw_resources
        resources = _validate_directory(resources, "Resources root")
        if not resources.is_relative_to(project):
            raise PathPolicyError("Resources root must be inside the project root.")
        evidence = project / ".cg-docs" / "research" / "evidence"
        if evidence.exists() and evidence.is_symlink():
            raise PathPolicyError("Evidence root cannot be a symbolic link.")
        return cls(project, resources, evidence, bind_host)

    def validate_resource_path(self, relative_path: Union[str, PurePath]) -> Path:
        """Resolve one project-relative resource without escaping the corpus.

        Args:
            relative_path: POSIX-style path relative to ``resources_root``.

        Returns:
            The resolved resource path below ``resources_root``.

        Raises:
            PathPolicyError: If the input is a URL, absolute path, directory, or
                path that escapes the configured resources root.

        Example:
            ``settings.validate_resource_path("papers/intro.md")``.
        """
        text = str(relative_path)
        _reject_url(text)
        candidate_input = Path(relative_path)
        if candidate_input.is_absolute() or "\\" in text or "\x00" in text:
            raise PathPolicyError("Resource paths must be relative POSIX paths.")
        candidate = (self.resources_root / candidate_input).resolve(strict=False)
        if not candidate.is_relative_to(self.resources_root):
            raise PathPolicyError("Resource path must stay inside the configured resources root.")
        if candidate.exists() and not candidate.is_file():
            raise PathPolicyError("Resource path must identify a regular file.")
        return candidate

    def model_loader_kwargs(self) -> dict[str, bool]:
        """Return mandatory local-cache-only model loader settings.

        Args:
            None.

        Returns:
            A mapping disabling model downloads during normal processing.

        Raises:
            RuntimeError: If the settings are not offline/cache-only.

        Example:
            ``settings.model_loader_kwargs()["local_files_only"]`` is ``True``.
        """
        if not self.offline or not self.model_cache_only:
            raise RuntimeError("Normal processing requires offline local-cache-only settings.")
        return {"local_files_only": True}
