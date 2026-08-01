"""Tests for deterministic type-specific semantic HTML rendering."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import re
from typing import Optional

from artifact_views.parser import parse_artifact
from artifact_views.provenance import ArtifactProvenance
from artifact_views.renderer import render_document
from artifact_views.schema import ArtifactKind

FIXTURES = Path(__file__).parent / "fixtures"
FIXED_TIME = datetime(2026, 7, 31, 12, 30, tzinfo=timezone.utc)


def _render(
    fixture: str,
    kind: ArtifactKind,
    source: Optional[str] = None,
) -> tuple:
    source_text = source or (FIXTURES / fixture).read_text(encoding="utf-8")
    source_path = Path(f".cg-docs/{kind.value}s/{fixture}")
    document = parse_artifact(source_text, source_path, kind)
    provenance = ArtifactProvenance.from_source(
        source_path=source_path,
        source_bytes=source_text.encode("utf-8"),
        artifact_schema_version=document.identity.schema_version or "legacy",
        renderer_version="0.1.0",
        generated_at=FIXED_TIME,
    )
    return document, render_document(document, provenance).decode("utf-8")


def test_brainstorm_has_type_specific_information_architecture() -> None:
    _, html = _render("strict_brainstorm.md", ArtifactKind.BRAINSTORM)

    assert 'data-artifact-kind="brainstorm"' in html
    assert "Decision record" in html
    assert "Approaches" in html
    assert "Decision" in html
    assert "Next steps" in html
    assert 'data-derived="navigation"' in html


def test_plan_has_type_specific_information_architecture_and_maps() -> None:
    _, html = _render("strict_deep_plan.md", ArtifactKind.PLAN)

    assert 'data-artifact-kind="plan"' in html
    assert "Execution contract" in html
    assert "Phase map" in html
    assert "Requirement coverage" in html
    assert "Verification" in html
    assert "Risks" in html
    assert "Boundaries" in html
    assert 'data-derived="phase-map"' in html
    assert 'data-derived="requirement-coverage"' in html


def test_every_substantive_block_has_exactly_one_rendered_owner() -> None:
    document, html = _render("strict_deep_plan.md", ArtifactKind.PLAN)

    rendered_ids = re.findall(r'data-source-block="([^"]+)"', html)
    expected_ids = [block.source_id for block in document.substantive_blocks]

    assert sorted(rendered_ids) == sorted(expected_ids)
    assert len(rendered_ids) == len(set(rendered_ids))


def test_non_substantive_status_metadata_is_not_in_human_body() -> None:
    _, html = _render("strict_brainstorm.md", ArtifactKind.BRAINSTORM)

    assert "Valid status values" not in html


def test_raw_html_is_visible_escaped_once() -> None:
    source = (FIXTURES / "strict_brainstorm.md").read_text(encoding="utf-8")
    source = source.replace(
        "Humans and agents need different views of one canonical artifact.",
        "<script>alert('source')</script>",
    )
    document, html = _render(
        "strict_brainstorm.md",
        ArtifactKind.BRAINSTORM,
        source,
    )

    assert "<script>alert('source')</script>" not in html
    assert "&lt;script&gt;alert(&#x27;source&#x27;)&lt;/script&gt;" in html
    raw_block = next(
        block
        for block in document.lexical_blocks
        if block.kind == "raw_html" and block.substantive
    )
    assert html.count(f'data-source-block="{raw_block.block_id}"') == 1
    assert "Raw source" in html


def test_tables_lists_code_and_long_paths_render_without_source_loss() -> None:
    source = (FIXTURES / "strict_plan.md").read_text(encoding="utf-8")
    source = source.replace(
        "Use focused pytest fixtures.",
        "Use focused pytest fixtures.\n\n"
        "```python\npath = 'a/very/long/path/that/must/wrap/output.html'\n```",
    )
    _, html = _render("strict_plan.md", ArtifactKind.PLAN, source)

    assert "<table" in html
    assert "<ul" in html
    assert "<pre" in html and "<code" in html
    assert "a/very/long/path/that/must/wrap/output.html" in html


def test_nested_list_is_rendered_as_visible_raw_source_not_flattened() -> None:
    source = (FIXTURES / "strict_plan.md").read_text(encoding="utf-8")
    source = source.replace(
        "- Rendering HTML.",
        "- Parent boundary\n  - Nested boundary",
    )

    _, html = _render("strict_plan.md", ArtifactKind.PLAN, source)

    assert "Raw source · unordered_list" in html
    assert "- Parent boundary\n  - Nested boundary" in html
    assert "<li>Nested boundary</li>" not in html


def test_provenance_is_machine_readable_and_visible() -> None:
    _, html = _render("strict_plan.md", ArtifactKind.PLAN)

    assert 'id="artifact-provenance"' in html
    assert 'type="application/json"' in html
    assert '"sourcePath":".cg-docs/plans/strict_plan.md"' in html
    assert "Source SHA-256" in html
    assert "2026-07-31T12:30:00Z" in html


def test_canonical_link_uses_project_relative_provenance() -> None:
    source = (FIXTURES / "strict_plan.md").read_text(encoding="utf-8")
    absolute_source = Path.cwd() / ".cg-docs/plans/strict_plan.md"
    document = parse_artifact(source, absolute_source, ArtifactKind.PLAN)
    provenance = ArtifactProvenance.from_source(
        source_path=Path(".cg-docs/plans/strict_plan.md"),
        source_bytes=source.encode("utf-8"),
        artifact_schema_version=1,
        renderer_version="0.1.0",
        generated_at=FIXED_TIME,
    )

    html = render_document(document, provenance).decode("utf-8")

    assert 'href="../../plans/strict_plan.md"' in html
    assert str(Path.cwd()) not in html


def test_fixed_complete_inputs_produce_identical_bytes() -> None:
    source = (FIXTURES / "strict_plan.md").read_text(encoding="utf-8")
    _, first = _render("strict_plan.md", ArtifactKind.PLAN, source)
    _, second = _render("strict_plan.md", ArtifactKind.PLAN, source)

    assert first == second
    assert first.startswith("<!doctype html>\n")


def test_renderer_contains_no_remote_assets() -> None:
    _, html = _render("strict_plan.md", ArtifactKind.PLAN)

    assert "http://" not in html
    assert "https://" not in html
    assert "<link " not in html
    assert "<script src=" not in html
