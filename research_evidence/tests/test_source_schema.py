"""Created 2026-08-12. Tests for parser metadata on source units."""
from __future__ import annotations

from research_evidence.schemas import LocatorKind, SourceUnit, TypedLocator


def test_source_units_can_mark_lossy_or_non_prose_content_for_review() -> None:
    """Keep table/equation uncertainty explicit in canonical source records."""
    locator = TypedLocator(
        kind=LocatorKind.LATEX_BLOCK,
        block=1,
        unit_fingerprint="sha256:" + "a" * 64,
    )
    unit = SourceUnit(
        source_unit_id="unit-1",
        source_version_id="version-1",
        locator=locator,
        text="x = y",
        unit_type="equation",
        review_required=True,
        parser_metadata={"parser": "latex-stdlib"},
    )
    assert unit.review_required is True
    assert unit.unit_type == "equation"
    assert unit.parser_metadata["parser"] == "latex-stdlib"
