"""Canonical source containment and mirrored artifact-view path mapping."""
from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path, PurePosixPath
import stat
import unicodedata
from typing import Union

from artifact_views.errors import ArtifactPathError
from artifact_views.generic_model import GENERIC_DOCUMENT_TYPE
from artifact_views.schema import ArtifactKind
from artifact_views.writer import ViewDestination, ViewNamespace

_SOURCE_ROOTS = {
    "brainstorms": ArtifactKind.BRAINSTORM,
    "plans": ArtifactKind.PLAN,
}
_REPARSE_POINT_FLAG = 0x400
_DOCUMENT_VIEW_ROOT = PurePosixPath(".cg-docs/views/documents")
_WINDOWS_DEVICE_NAMES = frozenset(
    {"CON", "PRN", "AUX", "NUL", "CONIN$", "CONOUT$"}
    | {f"COM{index}" for index in range(1, 10)}
    | {f"LPT{index}" for index in range(1, 10)}
)


@dataclass(frozen=True)
class ArtifactPaths:
    """Validated canonical source and derived destination paths."""

    project_root: Path
    kind: ArtifactKind
    source_path: Path
    source_relative: Path
    view_path: Path
    view_relative: Path
    destination: ViewDestination


@dataclass(frozen=True)
class GenericPaths:
    """Validated generic source and one owned document-view destination."""

    project_root: Path
    source_path: Path
    source_relative: Path
    output_path: Path
    output_relative: Path
    output_identity: str
    ownership_key: str
    destination: ViewDestination
    document_type: str = GENERIC_DOCUMENT_TYPE


def resolve_generic_paths(
    project_root: Path,
    source_path: Union[str, Path],
    output_relative: Union[str, Path, None] = None,
) -> GenericPaths:
    """Resolve one regular generic Markdown source and portable output.

    Args:
        project_root: Existing non-linked project root.
        source_path: Absolute or project-relative generic Markdown source.
        output_relative: Optional portable path under the documents view root.

    Returns:
        Validated source, destination, and normalized ownership identity.

    Raises:
        ArtifactPathError: If source or output identity is unsafe or reserved.

    Example:
        ``README.md`` maps to ``.cg-docs/views/documents/README.html``.
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
            "Generic source is outside project root.",
            source_path=source,
            corrective_action="Choose one project-contained Markdown source.",
        ) from error
    source_identity = PurePosixPath(*relative.parts)
    if source_identity.suffix != ".md":
        raise ArtifactPathError(
            "Generic source must have the exact .md suffix.",
            source_path=relative,
            corrective_action="Select a regular Markdown source file.",
        )
    source_parts = tuple(part.casefold() for part in source_identity.parts)
    if len(source_parts) >= 2 and source_parts[0] == ".cg-docs" and source_parts[1] in {
        "brainstorms",
        "plans",
        "views",
    }:
        raise ArtifactPathError(
            "Generic publishing cannot accept typed or generated artifact roots.",
            source_path=relative,
            corrective_action=(
                "Use cg-render-artifact for Brainstorms and Plans; never use a "
                "generated view as source."
            ),
        )
    _reject_link_components(root, relative)
    try:
        metadata = os.lstat(source)
    except FileNotFoundError as error:
        raise ArtifactPathError(
            "Generic source is not an existing regular file.",
            source_path=relative,
            corrective_action="Save the Markdown source before publishing.",
        ) from error
    if _is_link_or_reparse(metadata) or not stat.S_ISREG(metadata.st_mode):
        raise ArtifactPathError(
            "Generic source must be a regular file, not a link or reparse point.",
            source_path=relative,
            corrective_action="Use one regular project-contained Markdown file.",
        )
    if metadata.st_nlink != 1:
        raise ArtifactPathError(
            "Generic source has multiple hard links and ambiguous ownership.",
            source_path=relative,
            corrective_action="Publish from a file with exactly one filesystem link.",
        )

    if output_relative is None:
        derived = (_DOCUMENT_VIEW_ROOT / source_identity.with_suffix(".html")).as_posix()
        try:
            output_pure = _portable_output_path(derived)
        except ArtifactPathError as error:
            raise ArtifactPathError(
                "Generic source path is not portable as a mirrored output name.",
                source_path=relative,
                corrective_action=(
                    "Rename the source so no component uses a Windows device "
                    "name, a trailing space or dot, or a control character; or "
                    "pass an explicit --output path."
                ),
            ) from error
    else:
        raw_output = (
            output_relative if isinstance(output_relative, str) else output_relative.as_posix()
        )
        output_pure = _portable_output_path(raw_output)
    output_identity = output_pure.as_posix()
    output_path = root / Path(*output_pure.parts)
    _reject_portable_output_collisions(root, output_pure)
    return GenericPaths(
        project_root=root,
        source_path=source,
        source_relative=relative,
        output_path=output_path,
        output_relative=Path(*output_pure.parts),
        output_identity=output_identity,
        ownership_key=output_identity.casefold(),
        destination=ViewDestination(ViewNamespace.DOCUMENTS, Path(*output_pure.parts)),
    )


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
        destination=ViewDestination(ViewNamespace(category), view_relative),
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


def _portable_output_path(raw_output: str) -> PurePosixPath:
    if not raw_output or "\\" in raw_output or any(
        unicodedata.category(character)[0] == "C"
        for character in raw_output
    ):
        raise _portable_output_error(raw_output)
    raw_parts = raw_output.split("/")
    if any(part in {"", ".", ".."} for part in raw_parts):
        raise _portable_output_error(raw_output)
    output = PurePosixPath(raw_output)
    if output.is_absolute() or output.suffix != ".html":
        raise _portable_output_error(raw_output)
    if output.parts[:3] != (".cg-docs", "views", "documents") or len(output.parts) < 4:
        raise ArtifactPathError(
            "Generic output must stay in the registered documents namespace.",
            source_path=Path(raw_output),
            corrective_action=(
                "Use a portable relative .html path under "
                ".cg-docs/views/documents/."
            ),
        )
    for part in output.parts:
        if part.endswith((" ", ".")) or ":" in part:
            raise _portable_output_error(raw_output)
        base = part.split(".", 1)[0].upper()
        if base in _WINDOWS_DEVICE_NAMES:
            raise _portable_output_error(raw_output)
    return output


def _portable_output_error(raw_output: str) -> ArtifactPathError:
    return ArtifactPathError(
        "Generic output identity must be a portable relative .html path.",
        source_path=Path(raw_output),
        corrective_action=(
            "Avoid traversal, backslashes, alternate streams, trailing spaces or "
            "dots, and Windows device names."
        ),
    )


def _reject_portable_output_collisions(
    root: Path,
    output: PurePosixPath,
) -> None:
    current = Path(root)
    for component in output.parts:
        if not current.is_dir():
            return
        expected_key = _portable_component_key(component)
        for child in current.iterdir():
            if (
                child.name != component
                and _portable_component_key(child.name) == expected_key
            ):
                raise ArtifactPathError(
                    "Generic output has a portable case or Unicode collision.",
                    source_path=Path(output.as_posix()),
                    corrective_action=(
                        "Rename the colliding output path so every portable "
                        "component has one canonical spelling."
                    ),
                )
        current /= component


def _portable_component_key(component: str) -> str:
    return unicodedata.normalize("NFC", component).casefold().rstrip(". ")
