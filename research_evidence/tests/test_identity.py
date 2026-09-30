"""Created 2026-08-12. Tests for deterministic source identity."""
from __future__ import annotations

from research_evidence.identity import (
    canonical_locator,
    make_source_unit_id,
    make_source_version_id,
    text_fingerprint,
)
from research_evidence.schemas import TypedLocator


def test_source_version_and_unit_ids_are_deterministic() -> None:
    """Reproduce IDs from the same bytes, parser profile, and locator contract."""
    version_a = make_source_version_id(
        "resource-1", "b" * 64, "markdown-v1", "locator-v1"
    )
    version_b = make_source_version_id(
        "resource-1", "b" * 64, "markdown-v1", "locator-v1"
    )
    assert version_a == version_b
    locator = TypedLocator(
        kind="markdown_block",
        block=1,
        line_start=1,
        line_end=2,
        unit_fingerprint="sha256:" + "c" * 64,
    )
    assert make_source_unit_id(version_a, locator, text_fingerprint("A  sentence")) == make_source_unit_id(
        version_b, locator, text_fingerprint("A sentence")
    )


def test_canonical_locator_is_order_independent() -> None:
    """Serialize typed locator fields canonically for stable IDs and audit logs."""
    locator = TypedLocator(
        kind="markdown_block",
        block=1,
        line_start=1,
        line_end=2,
        unit_fingerprint="sha256:" + "c" * 64,
    )
    serialized = canonical_locator(locator)
    assert '"kind":"markdown_block"' in serialized
    assert serialized == canonical_locator(locator)


def test_text_fingerprint_normalizes_whitespace() -> None:
    """Treat equivalent whitespace as the same source-unit text fingerprint."""
    assert text_fingerprint("A  sentence\nwith spacing") == text_fingerprint(
        "A sentence with spacing"
    )
