"""Generic Markdown rendering through the shared semantic reference shell."""
from __future__ import annotations

from pathlib import Path, PurePosixPath
import posixpath

from artifact_views.generic_model import GenericDocument
from artifact_views.provenance import PublicationProvenance
from artifact_views.renderer import (
    heading_ids,
    navigation,
    render_source_blocks,
)
from artifact_views.errors import ArtifactSecurityError
from artifact_views.security import (
    GenericRenderContext,
    render_generic_inline,
    validate_html_security,
)
from artifact_views.templates import render_html_shell
from artifact_views.themes import get_theme


def render_generic_document(
    document: GenericDocument,
    provenance: PublicationProvenance,
    *,
    project_root: Path | None = None,
    max_image_bytes: int = 5 * 1024 * 1024,
    max_total_image_bytes: int = 20 * 1024 * 1024,
    max_image_count: int = 32,
    max_output_bytes: int = 32 * 1024 * 1024,
) -> bytes:
    """Render one generic document with exact source ownership.

    Args:
        document: Independently parsed generic Markdown document.
        provenance: Complete schema-2 source/output/theme identity.

    Returns:
        Complete deterministic self-contained HTML bytes.

    Raises:
        ValueError: If provenance does not identify this document type.

    Example:
        Pass a parsed generic document and schema-2 provenance to receive HTML.
    """
    if provenance.document_type != document.identity.document_type:
        raise ValueError("Generic provenance document type does not match source.")
    reserved = {"main-content", "artifact-provenance", "provenance-heading"}
    ids = heading_ids(document.lexical_blocks, reserved)
    navigation_items = tuple(
        (heading.title, ids[heading.source_block_id])
        for heading in document.headings
    ) + (("Provenance", "provenance-heading"),)
    if project_root is None and any(
        "![" in block.raw for block in document.lexical_blocks
    ):
        raise ArtifactSecurityError(
            "Image rendering requires a validated project root."
        )
    context = GenericRenderContext(
        project_root=project_root or Path("."),
        source_relative=document.identity.source_path,
        output_relative=Path(provenance.output_path),
        max_image_bytes=max_image_bytes,
        max_total_image_bytes=max_total_image_bytes,
        max_image_count=max_image_count,
        max_output_bytes=max_output_bytes,
    )
    rendered = render_html_shell(
        artifact_kind=document.identity.document_type,
        title=document.identity.title,
        eyebrow="Published document",
        deck=(
            "A complete human view of project-contained generic Markdown."
        ),
        canonical_href=_canonical_href(provenance),
        navigation_html=navigation(navigation_items),
        derived_html="",
        body_html=render_source_blocks(
            document,
            ids,
            lambda value: render_generic_inline(value, context=context),
        ),
        provenance=provenance,
        theme=get_theme(provenance.theme_name),
        navigation_label="Document sections",
        article_label="Canonical document content",
    )
    if len(rendered) > max_output_bytes:
        raise ArtifactSecurityError(
            "Generic document exceeds the rendered output budget."
        )
    validate_html_security(rendered.decode("utf-8"))
    return rendered


def _canonical_href(provenance: PublicationProvenance) -> str:
    source = PurePosixPath(provenance.source_path)
    output = PurePosixPath(provenance.output_path)
    return posixpath.relpath(source.as_posix(), output.parent.as_posix())