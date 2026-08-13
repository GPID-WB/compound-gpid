"""Created 2026-08-12. Local Markdown resource and source-version ingestion."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path

from .config import RuntimeSettings
from .identity import make_source_version_id, sha256_file
from .parsers.markdown import parse_markdown
from .schemas import ResourceRecord, SourceOrigin, SourceUnit, SourceVersion


@dataclass(frozen=True)
class ParsedMarkdownResource:
    """Bundle a local resource, immutable version, and parsed units.

    Args:
        resource: Logical resource record.
        source_version: Immutable bytes/parser/locator record.
        units: Parsed Markdown source units.

    Returns:
        An immutable parsed-resource bundle.

    Example:
        ``parsed.units`` supplies the units for lexical indexing.
    """

    resource: ResourceRecord
    source_version: SourceVersion
    units: list[SourceUnit]


def make_resource_id(relative_path: str) -> str:
    """Derive a stable logical resource ID from a normalized relative path.

    Args:
        relative_path: POSIX path relative to the configured resources root.

    Returns:
        A deterministic ``resource:`` identifier.

    Example:
        ``make_resource_id("notes.md")`` reproduces the same ID on every run.
    """
    return "resource:" + hashlib.sha256(relative_path.encode("utf-8")).hexdigest()


def ingest_markdown_resource(
    settings: RuntimeSettings,
    relative_path: str,
    *,
    parser_profile: str = "markdown-v1",
    locator_schema_version: str = "locator-v1",
) -> ParsedMarkdownResource:
    """Read one confined Markdown resource and derive its source units.

    Args:
        settings: Validated local runtime settings.
        relative_path: POSIX resource path below the configured root.
        parser_profile: Exact parser profile recorded in source identity.
        locator_schema_version: Typed locator contract recorded in source identity.

    Returns:
        Resource, source-version, and parsed-unit bundle.

    Raises:
        ValueError: If the selected path is not a Markdown file.
        OSError: If the local source cannot be read.

    Example:
        ``ingest_markdown_resource(settings, "findings.md")``.
    """
    path = settings.validate_resource_path(relative_path)
    if path.suffix.lower() not in {".md", ".markdown"}:
        raise ValueError("The Phase 1 parser accepts Markdown resources only.")
    source_hash = sha256_file(path)
    normalized_path = path.relative_to(settings.resources_root).as_posix()
    resource_id = make_resource_id(normalized_path)
    source_version_id = make_source_version_id(
        resource_id,
        source_hash,
        parser_profile,
        locator_schema_version,
    )
    source_version = SourceVersion(
        source_version_id=source_version_id,
        resource_id=resource_id,
        sha256=source_hash,
        parser_profile=parser_profile,
        locator_schema_version=locator_schema_version,
        original_authority=True,
    )
    text = path.read_text(encoding="utf-8")
    units = parse_markdown(text, source_version_id)
    resource = ResourceRecord(
        resource_id=resource_id,
        origin=SourceOrigin.REPO_LOCAL,
        relative_path=normalized_path,
        sha256=source_hash,
    )
    return ParsedMarkdownResource(resource, source_version, units)
