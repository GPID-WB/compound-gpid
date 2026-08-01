"""Canonical source containment and mirrored artifact-view path mapping."""
from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path, PurePosixPath
import stat
from typing import Tuple

from artifact_views.errors import ArtifactPathError
from artifact_views.schema import ArtifactKind

_SOURCE_ROOTS = {
    "brainstorms": ArtifactKind.BRAINSTORM,
    "plans": ArtifactKind.PLAN,
}
_REPARSE_POINT_FLAG = 0x400


@dataclass(frozen=True)
class ArtifactPaths:
    """Validated canonical source and derived destination paths."""

    project_root: Path
    kind: ArtifactKind
    source_path: Path
    source_relative: Path
    view_path: Path
    view_relative: Path


def resolve_artifact_paths(project_root: Path, source_path: Path) -> ArtifactPaths:
    """Validate one canonical source and derive its mirrored HTML path.

    Args:
        project_root: Existing project root directory.
        source_path: Absolute source path or path relative to ``project_root``.

    Returns:
        Validated canonical and derived path identities.

    Raises:
        ArtifactPathError: If containment, type, suffix, or link checks fail.

    Example:
        Given ``.cg-docs/plans/a.md``, the view path is
        ``.cg-docs/views/plans/a.html``.
    """
    root_input = Path(project_root)
    if root_input.is_symlink() or not root_input.is_dir():
        raise ArtifactPathError(
            "Project root must be an existing regular directory.",
            source_path=root_input,
            corrective_action="Use the real project directory, not a link.",
        )
    root = Path(os.path.abspath(root_input))
    source_input = Path(source_path)
    candidate = source_input if source_input.is_absolute() else root / source_input
    source = Path(os.path.abspath(candidate))
    try:
        relative = source.relative_to(root)
    except ValueError as error:
        raise ArtifactPathError(
            "Artifact source is outside project root.",
            source_path=source,
            corrective_action=(
                "Choose one .md source under .cg-docs/brainstorms or .cg-docs/plans."
            ),
        ) from error

    parts = relative.parts
    if len(parts) < 3 or parts[0] != ".cg-docs" or parts[1] not in _SOURCE_ROOTS:
        raise ArtifactPathError(
            "Artifact source must be under .cg-docs/brainstorms or .cg-docs/plans.",
            source_path=relative,
            corrective_action="Move or select a supported canonical artifact.",
        )
    if source.suffix != ".md":
        raise ArtifactPathError(
            "Artifact source must have the exact .md suffix.",
            source_path=relative,
            corrective_action="Select a regular Markdown source file.",
        )
    _reject_link_components(root, relative)
    try:
        metadata = os.lstat(source)
    except FileNotFoundError as error:
        raise ArtifactPathError(
            "Artifact source is not an existing regular file.",
            source_path=relative,
            corrective_action="Save the canonical Markdown source before rendering.",
        ) from error
    if _is_link_or_reparse(metadata) or not stat.S_ISREG(metadata.st_mode):
        raise ArtifactPathError(
            "Artifact source must be a regular file, not a link or reparse point.",
            source_path=relative,
            corrective_action="Use a regular canonical Markdown file.",
        )

    category = parts[1]
    source_tail = PurePosixPath(*parts[2:])
    view_tail = source_tail.with_suffix(".html")
    view_relative = Path(PurePosixPath(".cg-docs", "views", category) / view_tail)
    return ArtifactPaths(
        project_root=root,
        kind=_SOURCE_ROOTS[category],
        source_path=source,
        source_relative=relative,
        view_path=root / view_relative,
        view_relative=view_relative,
    )


def _reject_link_components(root: Path, relative: Path) -> None:
    current = root
    for part in relative.parts:
        current = current / part
        if not current.exists() and not current.is_symlink():
            continue
        metadata = os.lstat(current)
        if _is_link_or_reparse(metadata):
            raise ArtifactPathError(
                "Artifact source path contains a symlink or reparse point.",
                source_path=relative,
                corrective_action="Use only regular directories and a regular source file.",
            )
        if current != root / relative and not stat.S_ISDIR(metadata.st_mode):
            raise ArtifactPathError(
                "Artifact source path contains a non-directory ancestor.",
                source_path=relative,
                corrective_action="Repair the canonical artifact directory tree.",
            )


def _is_link_or_reparse(metadata) -> bool:
    return stat.S_ISLNK(metadata.st_mode) or bool(
        getattr(metadata, "st_file_attributes", 0) & _REPARSE_POINT_FLAG
    )
