"""Created 2026-08-12. Local resource and source-version ingestion."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path
from typing import Optional

from .config import RuntimeSettings
from .identity import make_source_version_id, sha256_file
from .parsers.document import ParsedDocument, parse_document
from .schemas import ResourceRecord, SourceOrigin, SourceUnit, SourceVersion


@dataclass(frozen=True)
class ParsedResource:
    """Bundle one local resource, source version, and parsed document.

    Args:
        resource: Logical local resource record.
        source_version: Immutable bytes/parser/locator record.
        document: Format-specific parsed document and warnings.

    Returns:
        An immutable parsed-resource bundle.

    Example:
        ``parsed.units`` supplies typed units for indexing.
    """

    resource: ResourceRecord
    source_version: SourceVersion
    document: ParsedDocument

    @property
    def units(self) -> list[SourceUnit]:
        """Return parsed source units from the format-specific document.

        Args:
            None.

        Returns:
            Typed source units ready for canonical records or indexing.

        Example:
            ``len(parsed.units)`` counts units from a local resource.
        """
        return self.document.units


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


def _parser_profile_for_suffix(suffix: str) -> str:
    """Return the stable parser profile for one supported extension."""
    profiles = {
        ".pdf": "pdf-pypdf-v1",
        ".docx": "docx-stdlib-xml-v1",
        ".md": "markdown-v1",
        ".markdown": "markdown-v1",
        ".tex": "latex-stdlib-v1",
        ".latex": "latex-stdlib-v1",
        ".html": "html-stdlib-v1",
        ".htm": "html-stdlib-v1",
    }
    try:
        return profiles[suffix]
    except KeyError as error:
        raise ValueError(f"Unsupported resource extension: {suffix or '<none>'}") from error


def _parser_version_for_profile(profile: str) -> str:
    """Return the exact parser/runtime version used by one profile."""
    if profile == "pdf-pypdf-v1":
        try:
            import pypdf
        except ImportError as error:
            raise ValueError("PDF parser capability pypdf is unavailable") from error
        return str(getattr(pypdf, "__version__", "unknown"))
    return "stdlib"


def ingest_resource(
    settings: RuntimeSettings,
    relative_path: str,
    *,
    parser_profile: Optional[str] = None,
    locator_schema_version: str = "locator-v1",
) -> ParsedResource:
    """Read one confined supported resource into a versioned parsed record.

    Args:
        settings: Validated local runtime settings.
        relative_path: POSIX resource path below the configured root.
        parser_profile: Optional explicit parser profile override.
        locator_schema_version: Typed locator contract recorded in identity.

    Returns:
        Resource, source-version, and format-specific parsed document bundle.

    Raises:
        ValueError: If the extension or parser capability is unsupported.
        OSError: If the local source cannot be read.

    Example:
        ``ingest_resource(settings, "paper.html")``.
    """
    path = settings.validate_resource_path(relative_path)
    normalized_path = path.relative_to(settings.resources_root).as_posix()
    profile = parser_profile or _parser_profile_for_suffix(path.suffix.lower())
    parser_version = _parser_version_for_profile(profile)
    source_hash = sha256_file(path)
    resource_id = make_resource_id(normalized_path)
    source_version_id = make_source_version_id(
        resource_id,
        source_hash,
        profile,
        locator_schema_version,
        parser_version,
    )
    document = parse_document(path, source_version_id)
    source_version = SourceVersion(
        source_version_id=source_version_id,
        resource_id=resource_id,
        sha256=source_hash,
        parser_profile=profile,
        parser_version=parser_version,
        locator_schema_version=locator_schema_version,
        original_authority=True,
    )
    resource = ResourceRecord(
        resource_id=resource_id,
        origin=SourceOrigin.REPO_LOCAL,
        relative_path=normalized_path,
        sha256=source_hash,
    )
    return ParsedResource(resource, source_version, document)


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
    parsed = ingest_resource(
        settings,
        relative_path,
        parser_profile=parser_profile,
        locator_schema_version=locator_schema_version,
    )
    if parsed.document.format != "markdown":
        raise ValueError("The Phase 1 parser accepts Markdown resources only.")
    return ParsedMarkdownResource(parsed.resource, parsed.source_version, parsed.units)
