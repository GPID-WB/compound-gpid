"""Adversarial content-security tests for artifact rendering."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from artifact_views.errors import ArtifactSecurityError
from artifact_views.parser import parse_artifact
from artifact_views.provenance import ArtifactProvenance
from artifact_views.renderer import render_document
from artifact_views.schema import ArtifactKind
from artifact_views.security import render_safe_inline, safe_url, validate_html_security

FIXTURE = Path(__file__).parent / "fixtures/strict_brainstorm.md"


def _render(source: str) -> str:
    source_path = Path(".cg-docs/brainstorms/security.md")
    document = parse_artifact(source, source_path, ArtifactKind.BRAINSTORM)
    provenance = ArtifactProvenance.from_source(
        source_path=source_path,
        source_bytes=source.encode("utf-8"),
        artifact_schema_version=document.identity.schema_version or "legacy",
        renderer_version="0.1.0",
        generated_at=datetime(2026, 7, 31, tzinfo=timezone.utc),
    )
    return render_document(document, provenance).decode("utf-8")


@pytest.mark.parametrize(
    "url",
    (
        "javascript:alert(1)",
        "java%73cript:alert(1)",
        "jav&#x61;script:alert(1)",
        "vbscript:msgbox(1)",
        "data:text/html,<script>alert(1)</script>",
        "//evil.example/payload",
        "#bad anchor",
        "https://good.example/\njavascript:alert(1)",
        "file:///etc/passwd",
    ),
)
def test_unsafe_urls_are_rejected(url: str) -> None:
    with pytest.raises(ArtifactSecurityError):
        safe_url(url)


@pytest.mark.parametrize(
    "url",
    (
        "#decision",
        "../plans/example.md",
        "assets/reference.txt",
        "https://example.org/reference",
        "http://example.org/reference",
        "mailto:team@example.org",
    ),
)
def test_documented_safe_urls_are_allowed(url: str) -> None:
    assert safe_url(url) == url


def test_markdown_links_render_with_safe_href() -> None:
    source = FIXTURE.read_text(encoding="utf-8").replace(
        "Humans and agents need different views of one canonical artifact.",
        "Review the [canonical plan](../plans/example.md).",
    )

    html = _render(source)

    assert '<a href="../plans/example.md">canonical plan</a>' in html


def test_encoded_script_link_aborts_rendering() -> None:
    source = FIXTURE.read_text(encoding="utf-8").replace(
        "Humans and agents need different views of one canonical artifact.",
        "Open [payload](java%73cript:alert(1)).",
    )

    with pytest.raises(ArtifactSecurityError, match="URL scheme"):
        _render(source)


def test_raw_events_styles_scripts_and_json_payloads_remain_inert() -> None:
    source = FIXTURE.read_text(encoding="utf-8").replace(
        "Humans and agents need different views of one canonical artifact.",
        '<img src=x onerror=alert(1)>\n\n<style>body{display:none}</style>\n\n'
        '<script>eval("payload")</script>\n\n</script><script>alert(2)</script>',
    )

    html = _render(source)

    assert "<img src=x" not in html
    assert "<style>body" not in html
    assert '<script>eval("payload")</script>' not in html
    assert "&lt;img src=x onerror=alert(1)&gt;" in html
    assert "&lt;style&gt;body{display:none}&lt;/style&gt;" in html
    assert "&lt;script&gt;eval" in html
    validate_html_security(html)


def test_final_html_has_restrictive_offline_csp_and_no_dynamic_code() -> None:
    html = _render(FIXTURE.read_text(encoding="utf-8"))

    assert "default-src 'none'" in html
    assert "connect-src 'none'" in html
    assert "object-src 'none'" in html
    assert "frame-src 'none'" in html
    assert "media-src 'none'" in html
    assert "innerHTML" not in html
    assert "eval(" not in html
    assert "<script src=" not in html
    validate_html_security(html)


def test_duplicate_ids_and_event_attributes_fail_final_validation() -> None:
    with pytest.raises(ArtifactSecurityError, match="Duplicate HTML id"):
        validate_html_security('<main id="same"><div id="same"></div></main>')
    with pytest.raises(ArtifactSecurityError, match="Event handler"):
        validate_html_security('<button onclick="alert(1)">Run</button>')
    with pytest.raises(ArtifactSecurityError, match="Source-derived style"):
        validate_html_security('<p style="display:none">Hidden</p>')


def test_repeated_and_derived_heading_ids_remain_unique() -> None:
    source = FIXTURE.read_text(encoding="utf-8").replace(
        "## Decision\n",
        "## Approach Index\n\nAdditional bounded section.\n\n## Decision\n",
    )

    html = _render(source)

    validate_html_security(html)
    assert html.count('id="approach-index"') == 1


def test_inline_renderer_work_scales_linearly_across_helpers() -> None:
    class CountingText(str):
        def __new__(cls, value, counter):
            instance = super().__new__(cls, value)
            instance.counter = counter
            return instance

        def __getitem__(self, key):
            self.counter["operations"] += 1
            result = super().__getitem__(key)
            if isinstance(key, slice):
                return type(self)(result, self.counter)
            return result

        def startswith(self, prefix, start=0, end=None):
            self.counter["operations"] += 1
            if end is None:
                return super().startswith(prefix, start)
            return super().startswith(prefix, start, end)

        def find(self, sub, start=0, end=None):
            end_index = len(self) if end is None else end
            self.counter["operations"] += max(1, end_index - start)
            if end is None:
                return super().find(sub, start)
            return super().find(sub, start, end)

    def measured_operations(size: int) -> int:
        counter = {"operations": 0}
        malformed = CountingText("[" * size + "<" * size, counter)
        rendered = render_safe_inline(malformed)
        assert rendered == "[" * size + "&lt;" * size
        return counter["operations"]

    small = measured_operations(2000)
    large = measured_operations(4000)

    assert large <= (2 * small) + 64
