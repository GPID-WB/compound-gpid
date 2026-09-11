"""Created 2026-08-13. Tests for the generalized lexical retrieval baseline."""
from __future__ import annotations

from pathlib import Path

from research_evidence.identity import make_source_unit_id, text_fingerprint
from research_evidence.retrieval.lexical import LexicalIndex
from research_evidence.schemas import SourceUnit, TypedLocator


def _unit(version: str, text: str, block: int, unit_type: str = "prose") -> SourceUnit:
    """Build one typed source unit for retrieval tests."""
    fingerprint = text_fingerprint(text)
    locator = TypedLocator(kind="markdown_block", block=block, unit_fingerprint=fingerprint)
    return SourceUnit(
        source_unit_id=make_source_unit_id(version, locator, fingerprint),
        source_version_id=version,
        locator=locator,
        text=text,
        unit_type=unit_type,
        review_required=unit_type != "prose",
        parser_metadata={"source": "fixture"},
    )


def test_index_rebuilds_typed_metadata_and_replaces_removed_units(tmp_path: Path) -> None:
    """Index text, headings, typed markers, and remove replaced source units."""
    old = _unit("v1", "Old finding", 1)
    table = _unit("v1", "Year Rate", 2, unit_type="table")
    index = LexicalIndex(tmp_path / "lexical.sqlite")
    index.rebuild([old, table])

    metadata = index.metadata(table.source_unit_id)
    assert metadata["unit_type"] == "table"
    assert metadata["review_required"] is True
    assert metadata["parser_metadata"] == {"source": "fixture"}

    replacement = _unit("v2", "New finding", 1)
    index.replace_units([old.source_unit_id], [replacement])
    assert index.search("Old finding") == []
    assert [item.text for item in index.search("New finding")] == ["New finding"]
    index.close()


def test_corrupt_derived_index_rebuilds_explicitly(tmp_path: Path) -> None:
    """Rebuild a corrupt derived SQLite file from canonical source units."""
    path = tmp_path / "lexical.sqlite"
    path.write_bytes(b"not sqlite")
    unit = _unit("v1", "Recovery finding", 1)

    index = LexicalIndex.open_or_rebuild(path, [unit])

    assert [item.text for item in index.search("Recovery")] == ["Recovery finding"]
    index.close()


def test_equal_score_order_is_repeatable_and_source_metadata_is_not_logged(tmp_path: Path) -> None:
    """Keep equal-score result order deterministic without raw benchmark logging."""
    units = [_unit("v1", "Same finding", 1), _unit("v1", "Same finding", 2)]
    index = LexicalIndex(tmp_path / "lexical.sqlite")
    index.rebuild(units)
    first = [item.source_unit_id for item in index.search("Same")]
    second = [item.source_unit_id for item in index.search("Same")]
    assert first == second
    assert index.manifest()["raw_text_logging"] is False
    index.close()
