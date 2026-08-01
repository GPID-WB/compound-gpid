"""Structural accessibility, responsive, offline, and print tests."""
from __future__ import annotations

from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

from artifact_views.parser import parse_artifact
from artifact_views.provenance import ArtifactProvenance
from artifact_views.renderer import render_document
from artifact_views.schema import ArtifactKind

FIXTURE = Path(__file__).parent / "fixtures/strict_deep_plan.md"


class _StructureParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.tags = []
        self.ids = set()
        self.hrefs = []
        self.aria_labels = []

    def handle_starttag(self, tag, attrs) -> None:
        attributes = dict(attrs)
        self.tags.append(tag)
        if attributes.get("id"):
            self.ids.add(attributes["id"])
        if attributes.get("href"):
            self.hrefs.append(attributes["href"])
        if attributes.get("aria-label"):
            self.aria_labels.append(attributes["aria-label"])


def _html() -> str:
    source = FIXTURE.read_text(encoding="utf-8")
    source_path = Path(".cg-docs/plans/accessibility.md")
    document = parse_artifact(source, source_path, ArtifactKind.PLAN)
    provenance = ArtifactProvenance.from_source(
        source_path=source_path,
        source_bytes=source.encode("utf-8"),
        artifact_schema_version=1,
        renderer_version="0.1.0",
        generated_at=datetime(2026, 7, 31, tzinfo=timezone.utc),
    )
    return render_document(document, provenance).decode("utf-8")


def test_semantic_landmarks_skip_link_and_navigation_are_present() -> None:
    html = _html()
    parser = _StructureParser()
    parser.feed(html)

    for tag in ("header", "nav", "main", "article", "footer"):
        assert tag in parser.tags
    assert '<a class="skip-link" href="#main-content">' in html
    assert "Artifact sections" in parser.aria_labels
    for href in parser.hrefs:
        if href.startswith("#"):
            assert href[1:] in parser.ids


def test_keyboard_focus_and_table_overflow_guards_are_frozen() -> None:
    html = _html()

    assert ":focus-visible" in html
    assert "outline: 3px solid var(--focus)" in html
    assert 'role="region"' in html
    assert 'tabindex="0"' in html
    assert "overflow-x: auto" in html
    assert "overflow-wrap: anywhere" in html


def test_responsive_zoom_and_reduced_motion_rules_preserve_content() -> None:
    html = _html()

    assert "grid-template-columns: minmax(12rem, 18rem) minmax(0, 1fr)" in html
    assert "@media (max-width: 48rem)" in html
    assert ".layout { grid-template-columns: 1fr; }" in html
    assert "min-width: 20rem" in html
    assert "@media (prefers-reduced-motion: reduce)" in html
    assert "scroll-behavior: auto" in html
    assert "font-size: clamp(" not in html


def test_print_keeps_source_provenance_tables_code_and_links() -> None:
    html = _html()

    assert "@media print" in html
    assert ".sidebar { display: none; }" in html
    assert "thead { display: table-header-group; }" in html
    assert "a[href]::after" in html
    assert 'class="provenance"' in html
    assert 'aria-label="Canonical artifact content"' in html
    assert "article { display: none" not in html
    assert "main { display: none" not in html


def test_status_and_authority_are_not_conveyed_by_color_alone() -> None:
    html = _html()

    assert "Execution contract" in html
    assert "Canonical Markdown remains authoritative" in html
    assert "Derived view provenance" in html
