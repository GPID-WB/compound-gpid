"""Secure atomic writer for validated self-contained artifact views."""
from __future__ import annotations

from pathlib import Path
from typing import Callable, Optional

from artifact_views.errors import ArtifactWriteError
from secure_fs import secure_write_bytes

BeforeReplace = Optional[Callable[[Path], None]]


def write_view(
    project_root: Path,
    view_relative: Path,
    content: bytes,
    *,
    before_replace: BeforeReplace = None,
) -> Path:
    """Securely replace one validated derived HTML view.

    Args:
        project_root: Existing project root directory.
        view_relative: Expected root-relative view destination.
        content: Complete in-memory HTML bytes.
        before_replace: Optional mutation-boundary test hook.

    Returns:
        The lexical absolute destination path.

    Raises:
        ArtifactWriteError: If secure containment or atomic replacement fails.

    Example:
        Callers render complete bytes first, then pass only a validated
        ``.cg-docs/views/...`` destination to this function.
    """
    relative = Path(view_relative)
    normalized = relative.as_posix()
    if not (
        normalized.startswith(".cg-docs/views/brainstorms/")
        or normalized.startswith(".cg-docs/views/plans/")
    ) or relative.suffix != ".html":
        raise ArtifactWriteError(
            "View destination must be a relative .html path under "
            ".cg-docs/views/brainstorms or .cg-docs/views/plans.",
            source_path=relative,
            corrective_action="Use resolve_artifact_paths() to derive the destination.",
        )
    try:
        return secure_write_bytes(
            Path(project_root),
            relative,
            content,
            executable=None,
            before_replace=before_replace,
        )
    except (OSError, ValueError) as error:
        raise ArtifactWriteError(
            f"Secure view replacement failed: {error}",
            source_path=relative,
            corrective_action=(
                "Repair the destination path and rerun cg-render-artifact for this source."
            ),
        ) from error
