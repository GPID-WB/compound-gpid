"""One-file CLI modes for artifact validation, rendering, and stale checks."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
import re
import sys
from typing import Optional, Sequence, TextIO

from artifact_views import __version__
from artifact_views.config import load_artifact_view_config
from artifact_views.errors import ArtifactPathError, ArtifactReadError, ArtifactViewError
from artifact_views.paths import ArtifactPaths, resolve_artifact_paths
from artifact_views.provenance import (
    PublicationProvenance,
    parse_provenance,
    source_sha256,
)
from artifact_views.publishing import PublishMode, resolve_publication
from artifact_views.renderer import render_document
from artifact_views.themes import resolve_theme
from artifact_views.validator import validate_source
from artifact_views.writer import write_view
from secure_fs import ExpectedFileState, secure_read_bytes

_PROVENANCE_RE = re.compile(
    r'<script id="artifact-provenance" type="application/json">(.*?)</script>',
    re.DOTALL,
)


class ViewState(str, Enum):
    """Derived view freshness relative to one canonical source."""

    MISSING = "missing"
    STALE = "stale"
    CURRENT = "current"


def build_parser() -> argparse.ArgumentParser:
    """Build the one-source artifact CLI parser.

    Args:
        None.

    Returns:
        Configured argument parser for all supported one-file modes.

    Example:
        >>> build_parser().prog
        'cg-render-artifact'
    """
    parser = argparse.ArgumentParser(prog="cg-render-artifact")
    parser.add_argument("--root", type=Path, help=argparse.SUPPRESS)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--automatic", action="store_true")
    modes.add_argument("--validate-only", action="store_true")
    modes.add_argument("--check", action="store_true")
    parser.add_argument("--theme")
    parser.add_argument("source", type=Path)
    return parser


def find_project_root(start: Path) -> Path:
    """Find the nearest project root from a file or directory path.

    Args:
        start: Existing or lexical path within a Compound GPID project.

    Returns:
        Nearest canonical ``.cg-docs`` boundary or ancestor containing a
        Compound GPID config, charter, or Git root.

    Raises:
        ArtifactPathError: If no project boundary is found.

    Example:
        ``find_project_root(Path('.cg-docs/plans/example.md'))`` resolves the
        directory containing the canonical ``.cg-docs`` tree.
    """
    candidate = Path(start).expanduser()
    if not candidate.is_absolute():
        candidate = Path.cwd() / candidate
    candidate = candidate.resolve(strict=False)
    if candidate.is_file() or candidate.suffix:
        candidate = candidate.parent
    for parent in (candidate, *candidate.parents):
        if parent.name == ".cg-docs" and parent.is_dir():
            return parent.parent
        if (
            (parent / "compound-gpid.md").is_file()
            or (parent / "compound-gpid.local.md").is_file()
            or (parent / ".git").exists()
            or (parent / ".cg-docs").is_dir()
        ):
            return parent
    raise ArtifactPathError(
        "Could not locate a Compound GPID project boundary.",
        source_path=Path(start),
        corrective_action="Run the command from the project or pass a project source path.",
    )


def view_state(
    paths: ArtifactPaths,
    source_bytes: bytes,
    *,
    renderer_version: str = __version__,
    explicit_theme: Optional[str] = None,
) -> ViewState:
    """Classify a derived view as missing, stale, or current.

    Args:
        paths: Validated canonical and mirrored view paths.
        source_bytes: Exact canonical source bytes.
        renderer_version: Renderer version required for current status.

    Returns:
        Missing, stale, or current state. Unsafe/corrupt views are stale.

    Example:
        A freshly rendered exact-byte view returns ``ViewState.CURRENT``.
    """
    view = paths.view_path
    if not view.exists() and not view.is_symlink():
        return ViewState.MISSING
    if view.is_symlink() or not view.is_file():
        return ViewState.STALE
    try:
        view_bytes = secure_read_bytes(paths.project_root, paths.view_relative)
        text = view_bytes.decode("utf-8", errors="strict")
        matches = _PROVENANCE_RE.findall(text)
        if len(matches) != 1:
            return ViewState.STALE
        provenance = parse_provenance(matches[0])
        if not isinstance(provenance, PublicationProvenance):
            return ViewState.STALE
        source_text = source_bytes.decode("utf-8", errors="strict")
        document = validate_source(source_text, paths.source_relative, paths.kind)
    except (OSError, UnicodeDecodeError, ValueError):
        return ViewState.STALE
    try:
        decision = resolve_publication(
            mode=PublishMode.CHECK,
            source_path=paths.source_relative,
            output_path=paths.view_relative,
            document_type=paths.kind.value,
            explicit_theme=explicit_theme,
            output_exists=True,
            existing_provenance=provenance,
        )
        if provenance.source_sha256 != source_sha256(source_bytes):
            return ViewState.STALE
        if provenance.renderer_version != renderer_version or decision.stale:
            return ViewState.STALE
        expected_provenance = PublicationProvenance.from_source(
            source_path=paths.source_relative,
            source_bytes=source_bytes,
            output_path=paths.view_relative,
            document_type=paths.kind.value,
            renderer_version=renderer_version,
            theme_name=decision.theme.name,
            theme_version=decision.theme.contract_version,
            generated_at=provenance.generated_datetime(),
        )
        if provenance != expected_provenance:
            return ViewState.STALE
        expected_bytes = render_document(document, expected_provenance)
    except (
        ArtifactViewError,
        OSError,
        RuntimeError,
        TypeError,
        UnicodeError,
        ValueError,
    ):
        return ViewState.STALE
    return ViewState.CURRENT if expected_bytes == view_bytes else ViewState.STALE


def main(
    argv: Optional[Sequence[str]] = None,
    *,
    stdout: Optional[TextIO] = None,
    stderr: Optional[TextIO] = None,
    now: Optional[datetime] = None,
) -> int:
    """Execute one explicit, automatic, validation-only, or check operation.

    Args:
        argv: Optional CLI arguments excluding the executable name.
        stdout: Optional destination for normal output.
        stderr: Optional destination for diagnostics.
        now: Optional explicit UTC generation time for deterministic callers.

    Returns:
        Process exit code: 0 for success/current, 1 for failures or stale/missing
        checks, and 2 for input or usage errors.

    Example:
        ``main(['--check', '.cg-docs/plans/example.md'])`` checks one view.
    """
    output = stdout or sys.stdout
    errors = stderr or sys.stderr
    try:
        arguments = build_parser().parse_args(argv)
    except SystemExit as error:
        return int(error.code)

    source_argument = arguments.source
    try:
        root = (
            arguments.root.expanduser().resolve()
            if arguments.root is not None
            else find_project_root(source_argument)
        )
        paths = resolve_artifact_paths(root, source_argument)
        resolve_theme(paths.kind.value, arguments.theme)
    except (ArtifactPathError, ValueError) as error:
        errors.write(f"Artifact input invalid: {error}\n")
        return 2

    source_bytes: Optional[bytes] = None
    state = ViewState.MISSING
    try:
        try:
            source_bytes = secure_read_bytes(root, paths.source_relative)
            source_text = source_bytes.decode("utf-8", errors="strict")
        except (OSError, UnicodeDecodeError) as error:
            raise ArtifactReadError(
                f"Artifact source could not be read as strict UTF-8: {error}",
                source_path=paths.source_relative,
                corrective_action="Save a readable UTF-8 Markdown source and retry.",
            ) from error
        document = validate_source(source_text, paths.source_relative, paths.kind)

        if arguments.validate_only:
            output.write(f"Validated {paths.source_relative.as_posix()}\n")
            return 0
        if arguments.check:
            state = view_state(
                paths,
                source_bytes,
                explicit_theme=arguments.theme,
            )
            output.write(f"{state.value} {paths.view_relative.as_posix()}\n")
            return 0 if state is ViewState.CURRENT else 1
        if arguments.automatic:
            config = load_artifact_view_config(root)
            if config.warning:
                errors.write(f"Warning: {config.warning}\n")
            if not config.automatic_html:
                output.write(
                    f"HTML disabled; validated {paths.source_relative.as_posix()}\n"
                )
                return 0

        output_exists = paths.view_path.exists() or paths.view_path.is_symlink()
        view_bytes: Optional[bytes] = None
        existing_provenance = None
        if output_exists:
            try:
                view_bytes = secure_read_bytes(paths.project_root, paths.view_relative)
                view_text = view_bytes.decode("utf-8", errors="strict")
                matches = _PROVENANCE_RE.findall(view_text)
                if len(matches) == 1:
                    existing_provenance = parse_provenance(matches[0])
            except (OSError, UnicodeDecodeError, ValueError):
                existing_provenance = None
        decision = resolve_publication(
            mode=(PublishMode.AUTOMATIC if arguments.automatic else PublishMode.RENDER),
            source_path=paths.source_relative,
            output_path=paths.view_relative,
            document_type=paths.kind.value,
            explicit_theme=arguments.theme,
            output_exists=output_exists,
            existing_provenance=existing_provenance,
        )

        timestamp = now or datetime.now(timezone.utc)
        provenance = PublicationProvenance.from_source(
            source_path=paths.source_relative,
            source_bytes=source_bytes,
            output_path=paths.view_relative,
            document_type=paths.kind.value,
            renderer_version=__version__,
            theme_name=decision.theme.name,
            theme_version=decision.theme.contract_version,
            generated_at=timestamp,
        )
        content = render_document(document, provenance)
        expected_state = (
            ExpectedFileState.from_bytes(view_bytes)
            if view_bytes is not None
            else ExpectedFileState.absent()
        )
        write_view(
            root,
            paths.destination,
            content,
            expected_state=expected_state,
        )
        output.write(f"{paths.view_relative.as_posix()}\n")
        return 0
    except (
        ArtifactViewError,
        OSError,
        RuntimeError,
        TypeError,
        UnicodeError,
        ValueError,
    ) as error:
        try:
            if source_bytes is not None:
                state = view_state(
                    paths,
                    source_bytes,
                    explicit_theme=arguments.theme,
                )
            else:
                state = (
                    ViewState.STALE if paths.view_path.exists() else ViewState.MISSING
                )
        except (
            ArtifactViewError,
            OSError,
            RuntimeError,
            TypeError,
            UnicodeError,
            ValueError,
        ):
            state = ViewState.STALE if paths.view_path.exists() else ViewState.MISSING
        errors.write(f"Artifact render failed: {error}\n")
        errors.write(f"Source: {paths.source_relative.as_posix()}\n")
        errors.write(
            f"Expected view: {paths.view_relative.as_posix()} ({state.value})\n"
        )
        errors.write(
            f"Recover: cg-render-artifact {paths.source_relative.as_posix()}\n"
        )
        return 1
