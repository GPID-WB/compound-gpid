"""One-file CLI for secure generic Markdown publication and freshness checks."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
import re
import shlex
import sys
from typing import Optional, Sequence, TextIO

from artifact_views import __version__
from artifact_views.cli import find_project_root
from artifact_views.config import load_artifact_view_config
from artifact_views.errors import ArtifactPathError, ArtifactReadError, ArtifactViewError
from artifact_views.generic_parser import parse_generic_markdown
from artifact_views.generic_renderer import render_generic_document
from artifact_views.paths import GenericPaths, resolve_generic_paths
from artifact_views.provenance import (
    PublicationProvenance,
    parse_provenance,
)
from artifact_views.publishing import PublishMode, resolve_publication
from artifact_views.themes import resolve_theme
from artifact_views.writer import write_view
from secure_fs import ExpectedFileState, secure_read_bytes

_PROVENANCE_RE = re.compile(
    r'<script id="artifact-provenance" type="application/json">(.*?)</script>',
    re.DOTALL,
)
_MAX_SOURCE_BYTES = 10 * 1024 * 1024
_MAX_VIEW_BYTES = 32 * 1024 * 1024


def build_parser() -> argparse.ArgumentParser:
    """Build the generic one-source publication CLI parser.

    Args:
        None.

    Returns:
        Configured parser for render, automatic, validation, and check modes.

    Example:
        ``build_parser().prog`` is ``cg-publish-markdown``.
    """
    parser = argparse.ArgumentParser(
        prog="cg-publish-markdown",
        description=(
            "Publish one project-contained generic Markdown file. The default "
            "destination mirrors the source under .cg-docs/views/documents/."
        ),
        epilog=(
            "Existing output requires matching provenance ownership. Exit code 0 "
            "means success/current; exit code 1 means missing/stale or mutation "
            "failure; exit code 2 means invalid input, source, resource, path, or "
            "theme."
        ),
    )
    parser.add_argument("--root", type=Path, help=argparse.SUPPRESS)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument(
        "--automatic",
        action="store_true",
        help="Validate, then publish only when artifact-html is enabled.",
    )
    modes.add_argument(
        "--validate-only",
        action="store_true",
        help="Validate source, resources, paths, and theme without output I/O.",
    )
    modes.add_argument(
        "--check",
        action="store_true",
        help="Report the expected output as missing, stale, or current.",
    )
    parser.add_argument(
        "--theme",
        help="Registered theme name (reference or editorial).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Portable relative .html path under .cg-docs/views/documents/.",
    )
    parser.add_argument("source", type=Path, help="Project-relative generic Markdown source.")
    return parser


def main(
    argv: Optional[Sequence[str]] = None,
    *,
    stdout: Optional[TextIO] = None,
    stderr: Optional[TextIO] = None,
    now: Optional[datetime] = None,
) -> int:
    """Execute one generic render, automatic, validation, or check operation.

    Args:
        argv: Optional command arguments excluding the executable name.
        stdout: Optional normal-output stream.
        stderr: Optional diagnostic-output stream.
        now: Optional explicit UTC timestamp for deterministic callers.

    Returns:
        Exit code 0 for success/current, 1 for failure/stale/missing, or 2 for
        invalid input and usage.

    Example:
        ``main(['--check', 'README.md'])`` checks one generic document view.
    """
    output_stream = stdout or sys.stdout
    error_stream = stderr or sys.stderr
    try:
        arguments = build_parser().parse_args(argv)
    except SystemExit as error:
        return int(error.code)
    try:
        root = (
            arguments.root.expanduser().resolve()
            if arguments.root is not None
            else find_project_root(arguments.source)
        )
        paths = resolve_generic_paths(root, arguments.source, arguments.output)
        resolve_theme(paths.document_type, arguments.theme)
    except (ArtifactPathError, ValueError) as error:
        error_stream.write(f"Document input invalid: {error}\n")
        return 2

    try:
        source_bytes = secure_read_bytes(
            root,
            paths.source_relative,
            max_bytes=_MAX_SOURCE_BYTES,
            reject_hardlinks=True,
        )
        source_text = source_bytes.decode("utf-8", errors="strict")
    except (OSError, UnicodeDecodeError) as error:
        read_error = ArtifactReadError(
            f"Document source could not be read as strict UTF-8: {error}",
            source_path=paths.source_relative,
            corrective_action="Save one readable bounded UTF-8 Markdown source.",
        )
        return _render_failure(error_stream, paths, read_error, arguments, exit_code=2)

    try:
        document = parse_generic_markdown(source_text, paths.source_relative)
        automatic_enabled = True
        if arguments.automatic:
            config = load_artifact_view_config(root)
            automatic_enabled = config.automatic_html
            if config.warning:
                error_stream.write(f"Warning: {config.warning}\n")
        mode = _publish_mode(arguments)
        if arguments.validate_only or (
            arguments.automatic and not automatic_enabled
        ):
            decision = resolve_publication(
                mode=mode,
                source_path=paths.source_relative,
                output_path=paths.output_relative,
                document_type=paths.document_type,
                explicit_theme=arguments.theme,
                output_exists=False,
                automatic_enabled=automatic_enabled,
            )
            validation_provenance = _provenance(
                paths,
                source_bytes,
                decision.theme.name,
                decision.theme.contract_version,
                now or datetime.now(timezone.utc),
            )
            try:
                render_generic_document(
                    document,
                    validation_provenance,
                    project_root=root,
                )
            except (ArtifactViewError, OSError, UnicodeError, ValueError) as error:
                return _render_failure(
                    error_stream,
                    paths,
                    error,
                    arguments,
                    exit_code=2,
                )
            if arguments.automatic:
                output_stream.write(
                    f"HTML disabled; validated {paths.source_relative.as_posix()}\n"
                )
            else:
                output_stream.write(f"Validated {paths.source_relative.as_posix()}\n")
            return 0

        output_exists = paths.output_path.exists() or paths.output_path.is_symlink()
        existing_bytes: Optional[bytes] = None
        existing_provenance = None
        if output_exists:
            try:
                existing_bytes = secure_read_bytes(
                    root,
                    paths.output_relative,
                    max_bytes=_MAX_VIEW_BYTES,
                    reject_hardlinks=True,
                )
                existing_provenance = _extract_provenance(existing_bytes)
            except (OSError, UnicodeDecodeError, ValueError):
                existing_provenance = None

        if arguments.check and not output_exists:
            output_stream.write(f"missing {paths.output_identity}\n")
            return 1

        if arguments.check and existing_provenance is None:
            output_stream.write(f"stale {paths.output_identity}\n")
            return 1

        try:
            decision = resolve_publication(
                mode=mode,
                source_path=paths.source_relative,
                output_path=paths.output_relative,
                document_type=paths.document_type,
                explicit_theme=arguments.theme,
                output_exists=output_exists,
                existing_provenance=existing_provenance,
                automatic_enabled=automatic_enabled,
            )
        except ValueError:
            if arguments.check:
                output_stream.write(f"stale {paths.output_identity}\n")
                return 1
            return _render_failure(
                error_stream,
                paths,
                sys.exc_info()[1] or ValueError("Publication ownership failed."),
                arguments,
                exit_code=1,
            )

        if arguments.check:
            if not isinstance(existing_provenance, PublicationProvenance):
                output_stream.write(f"stale {paths.output_identity}\n")
                return 1
            if decision.stale:
                output_stream.write(f"stale {paths.output_identity}\n")
                return 1
            expected_provenance = _provenance(
                paths,
                source_bytes,
                decision.theme.name,
                decision.theme.contract_version,
                existing_provenance.generated_datetime(),
            )
            expected_bytes = render_generic_document(
                document,
                expected_provenance,
                project_root=root,
            )
            current = expected_bytes == existing_bytes
            output_stream.write(
                f"{'current' if current else 'stale'} {paths.output_identity}\n"
            )
            return 0 if current else 1

        provenance = _provenance(
            paths,
            source_bytes,
            decision.theme.name,
            decision.theme.contract_version,
            now or datetime.now(timezone.utc),
        )
        try:
            content = render_generic_document(document, provenance, project_root=root)
        except (ArtifactViewError, OSError, UnicodeError, ValueError) as error:
            return _render_failure(
                error_stream,
                paths,
                error,
                arguments,
                exit_code=2,
            )
        expected_state = (
            ExpectedFileState.from_bytes(existing_bytes)
            if existing_bytes is not None
            else ExpectedFileState.absent()
        )
        try:
            write_view(
                root,
                paths.destination,
                content,
                expected_state=expected_state,
            )
        except (ArtifactViewError, OSError, ValueError) as error:
            return _render_failure(
                error_stream,
                paths,
                error,
                arguments,
                exit_code=1,
            )
        output_stream.write(f"{paths.output_identity}\n")
        return 0
    except (
        ArtifactViewError,
        OSError,
        RuntimeError,
        TypeError,
        UnicodeError,
        ValueError,
    ) as error:
        return _render_failure(
            error_stream,
            paths,
            error,
            arguments,
            exit_code=2,
        )


def _publish_mode(arguments: argparse.Namespace) -> PublishMode:
    if arguments.validate_only:
        return PublishMode.VALIDATE_ONLY
    if arguments.check:
        return PublishMode.CHECK
    if arguments.automatic:
        return PublishMode.AUTOMATIC
    return PublishMode.RENDER


def _provenance(
    paths: GenericPaths,
    source_bytes: bytes,
    theme_name: str,
    theme_version: int,
    generated_at: datetime,
) -> PublicationProvenance:
    return PublicationProvenance.from_source(
        source_path=paths.source_relative,
        source_bytes=source_bytes,
        output_path=paths.output_relative,
        document_type=paths.document_type,
        renderer_version=__version__,
        theme_name=theme_name,
        theme_version=theme_version,
        generated_at=generated_at,
    )


def _extract_provenance(content: bytes):
    text = content.decode("utf-8", errors="strict")
    matches = _PROVENANCE_RE.findall(text)
    if len(matches) != 1:
        raise ValueError("Existing output has no unique provenance payload.")
    return parse_provenance(matches[0])


def _render_failure(
    error_stream: TextIO,
    paths: GenericPaths,
    error: Exception,
    arguments: argparse.Namespace,
    *,
    exit_code: int,
) -> int:
    state = "stale" if paths.output_path.exists() else "missing"
    error_stream.write(f"Document publication failed: {error}\n")
    error_stream.write(f"Source: {paths.source_relative.as_posix()}\n")
    error_stream.write(f"Expected output: {paths.output_identity} ({state})\n")
    recovery = ["cg-publish-markdown"]
    if arguments.theme is not None:
        recovery.extend(("--theme", arguments.theme))
    if arguments.output is not None:
        recovery.extend(("--output", paths.output_identity))
    recovery.append(paths.source_relative.as_posix())
    error_stream.write(
        "Recover: " + " ".join(shlex.quote(item) for item in recovery) + "\n"
    )
    return exit_code