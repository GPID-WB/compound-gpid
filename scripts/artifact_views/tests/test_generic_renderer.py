"""Tests for generic Markdown rendering through the shared semantic shell."""
from __future__ import annotations

# pylint: disable=import-error

from datetime import datetime, timezone
from pathlib import Path
import re

import pytest

from artifact_views.errors import ArtifactSecurityError
from artifact_views.generic_parser import parse_generic_markdown
from artifact_views.generic_renderer import render_generic_document
from artifact_views.provenance import PublicationProvenance
from artifact_views.security import validate_html_security
from artifact_views.tests.test_publishing_security import PNG


def _render(
    source: str,
    *,
    project_root: Path | None = None,
    **render_options,
) -> tuple:
    source_path = Path("docs/guide.md")
    output_path = Path(".cg-docs/views/documents/docs/guide.html")
    document = parse_generic_markdown(source, source_path)
    provenance = PublicationProvenance.from_source(
        source_path=source_path,
        source_bytes=source.encode("utf-8"),
        output_path=output_path,
        document_type="generic-markdown",
        renderer_version="0.2.0",
        theme_name="reference",
        theme_version=1,
        generated_at=datetime(2026, 8, 3, 12, 0, tzinfo=timezone.utc),
    )
    return document, render_generic_document(
        document,
        provenance,
        project_root=project_root,
        **render_options,
    ).decode("utf-8")


def test_generic_renderer_uses_heading_navigation_and_unique_ids() -> None:
    _, html = _render("# Guide\n\n## Repeat\n\nFirst.\n\n## Repeat\n\nSecond.\n")

    assert 'data-artifact-kind="generic-markdown"' in html
    assert 'aria-label="Document sections"' in html
    assert 'href="#repeat"' in html
    assert 'href="#repeat-2"' in html
    assert html.count('id="repeat"') == 1
    assert html.count('id="repeat-2"') == 1
    assert 'data-derived="phase-map"' not in html


def test_generic_renderer_preserves_exact_once_source_ownership() -> None:
    source = (
        "# Guide\n\nParagraph with **strong** and [link](https://example.org).\n\n"
        "> [!DECISION]\n> Publish the bounded core.\n\n"
        "| Item | Result |\n|---|---|\n| Parser | Pass |\n\n"
        "- One\n- Two\n\n```python\nvalue = '<safe>'\n```\n\n"
        "<script>alert('source')</script>\n"
    )
    document, html = _render(source)

    rendered_ids = re.findall(r'data-source-block="([^"]+)"', html)
    expected_ids = [block.source_id for block in document.substantive_blocks]
    assert sorted(rendered_ids) == sorted(expected_ids)
    assert len(rendered_ids) == len(set(rendered_ids))
    assert '<aside class="callout callout-decision"' in html
    assert "Decision" in html
    assert "<table" in html
    assert "<ul" in html
    assert "<pre><code class=\"language-python\"" in html
    assert "&lt;script&gt;alert(&#x27;source&#x27;)&lt;/script&gt;" in html
    assert "<script>alert('source')</script>" not in html
    validate_html_security(html)


def test_all_exact_callout_markers_render_without_prose_inference() -> None:
    markers = ("NOTE", "TIP", "IMPORTANT", "WARNING", "CAUTION", "DECISION", "PROS", "CONS")
    source = "# Guide\n\n" + "\n\n".join(
        f"> [!{marker}]\n> {marker.title()} body."
        for marker in markers
    ) + "\n\n> [!note]\n> Ordinary quote.\n"

    _, html = _render(source)

    for marker in markers:
        assert f"callout-{marker.casefold()}" in html
    assert html.count('class="callout ') == len(markers)
    assert "Ordinary quote." in html


def test_fixed_generic_inputs_produce_identical_complete_offline_bytes() -> None:
    source = "# Guide\n\n## Section\n\nText.\n"

    _, first = _render(source)
    _, second = _render(source)

    assert first == second
    assert first.startswith("<!doctype html>\n")
    assert "default-src 'none'" in first
    assert "http://" not in first
    assert "https://example.org" not in first


def test_generic_renderer_embeds_local_bitmap_and_escapes_raw_image_html(
    tmp_path: Path,
) -> None:
    root = tmp_path / "repo"
    image = root / "docs/assets/figure.png"
    image.parent.mkdir(parents=True)
    image.write_bytes(PNG)
    source = (
        "# Guide\n\n![Bounded figure](assets/figure.png)\n\n"
        '<img src="https://example.org/remote.png" onerror="alert(1)">\n'
    )

    _, html = _render(source, project_root=root)

    assert '<img src="data:image/png;base64,' in html
    assert 'alt="Bounded figure"' in html
    assert '<img src="https://example.org/remote.png"' not in html
    assert "&lt;img src=&quot;https://example.org/remote.png&quot;" in html
    validate_html_security(html)


def test_generic_renderer_rejects_image_when_resource_root_is_missing() -> None:
    with pytest.raises(ArtifactSecurityError, match="project root"):
        _render("# Guide\n\n![Figure](assets/figure.png)\n")


def test_generic_renderer_rejects_aggregate_output_over_budget(
    tmp_path: Path,
) -> None:
    root = tmp_path / "repo"
    image = root / "docs/figure.png"
    image.parent.mkdir(parents=True)
    image.write_bytes(PNG)
    source = "# Guide\n\n" + " ".join(
        f"![Figure {index}](figure.png)" for index in range(4)
    ) + "\n"

    with pytest.raises(ArtifactSecurityError, match="output budget"):
        _render(
            source,
            project_root=root,
            max_output_bytes=2_000,
            max_image_count=10,
            max_total_image_bytes=len(PNG) + 1,
        )


def test_generic_renderer_rebases_relative_links_to_output_location() -> None:
    _, html = _render(
        "# Guide\n\n[Sibling](other.md) [Section](#section) "
        "[Web](https://example.org).\n"
    )

    assert 'href="../../../../docs/other.md"' in html
    assert 'href="#section"' in html
    assert 'href="https://example.org"' in html