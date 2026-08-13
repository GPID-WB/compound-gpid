"""Created 2026-08-12. Tests for deterministic Markdown source units."""
from __future__ import annotations

import pytest

from research_evidence.parsers.markdown import parse_markdown


def test_markdown_blocks_have_typed_deterministic_locators() -> None:
    """Parse paragraphs into stable source units with line and heading context."""
    units = parse_markdown(
        "# Findings\n\nThe weighted rate fell.\n\nA second paragraph.",
        "source-version:v1",
    )
    assert len(units) == 3
    assert units[1].locator.kind.value == "markdown_block"
    assert units[1].locator.block == 2
    assert units[1].locator.line_start == 3
    assert units[1].locator.line_end == 3
    assert units[1].heading_path == ["Findings"]
    assert units == parse_markdown(
        "# Findings\n\nThe weighted rate fell.\n\nA second paragraph.",
        "source-version:v1",
    )


def test_empty_markdown_has_no_units() -> None:
    """Return no source units for an empty resource rather than inventing text."""
    assert parse_markdown("\n\n", "source-version:v1") == []


def test_markdown_requires_text_and_version() -> None:
    """Reject non-text or missing source-version inputs clearly."""
    with pytest.raises(ValueError, match="source version"):
        parse_markdown("Text", "")
