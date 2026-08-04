"""Secure atomic writer for validated self-contained artifact views."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Callable, Optional

from artifact_views.errors import ArtifactWriteError
from secure_fs import ExpectedFileState, secure_write_bytes

BeforeReplace = Optional[Callable[[Path], None]]


class ViewNamespace(str, Enum):
    """Registered derived-view destination namespaces."""

    BRAINSTORMS = "brainstorms"
    PLANS = "plans"
    DOCUMENTS = "documents"


@dataclass(frozen=True)
class ViewDestination:
    """One typed registered root-relative HTML destination."""

    namespace: ViewNamespace
    relative: Path

    def __post_init__(self) -> None:
        path = Path(self.relative)
        expected_root = Path(".cg-docs/views") / self.namespace.value
        try:
            tail = path.relative_to(expected_root)
        except ValueError as error:
            raise ArtifactWriteError(
                "View destination does not match its registered namespace.",
                source_path=path,
                corrective_action="Use a destination produced by the path resolver.",
            ) from error
        if path.is_absolute() or path.suffix != ".html" or not tail.parts:
            raise ArtifactWriteError(
                "View destination must be a relative registered .html path.",
                source_path=path,
                corrective_action="Use a destination produced by the path resolver.",
            )

    @classmethod
    def from_path(cls, relative: Path) -> "ViewDestination":
        """Create a typed destination from one resolver-produced path.

        Args:
            relative: Registered root-relative HTML destination.

        Returns:
            Typed namespace and destination identity.

        Example:
            A documents view resolves to ``ViewNamespace.DOCUMENTS``.
        """
        path = Path(relative)
        parts = path.parts
        if len(parts) < 4 or parts[:2] != (".cg-docs", "views"):
            raise ArtifactWriteError(
                "View destination must be relative and inside a registered namespace.",
                source_path=path,
                corrective_action="Use a destination produced by the path resolver.",
            )
        try:
            namespace = ViewNamespace(parts[2])
        except ValueError as error:
            raise ArtifactWriteError(
                "View destination namespace is not registered.",
                source_path=path,
                corrective_action="Use brainstorms, plans, or documents views.",
            ) from error
        return cls(namespace, path)


def write_view(
    project_root: Path,
    destination: ViewDestination,
    content: bytes,
    *,
    before_replace: BeforeReplace = None,
    expected_state: Optional[ExpectedFileState] = None,
) -> Path:
    """Securely replace one validated derived HTML view.

    Args:
        project_root: Existing project root directory.
        destination: Typed registered root-relative view destination.
        content: Complete in-memory HTML bytes.
        before_replace: Optional mutation-boundary test hook.
        expected_state: Authorized absence or exact prior output bytes.

    Returns:
        The lexical absolute destination path.

    Raises:
        ArtifactWriteError: If secure containment or atomic replacement fails.

    Example:
        Callers render complete bytes first, then pass only a validated
        ``.cg-docs/views/...`` destination to this function.
    """
    if not isinstance(destination, ViewDestination):
        raise TypeError("write_view requires a resolved ViewDestination.")
    relative = destination.relative
    try:
        return secure_write_bytes(
            Path(project_root),
            relative,
            content,
            executable=None,
            before_replace=before_replace,
            expected_state=expected_state,
        )
    except (OSError, ValueError) as error:
        raise ArtifactWriteError(
            f"Secure view replacement failed: {error}",
            source_path=relative,
            corrective_action=(
                "Repair the destination identity and retry through the owning CLI."
            ),
        ) from error
