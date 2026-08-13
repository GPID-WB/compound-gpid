"""Created 2026-08-12. Tests for the local SQLite FTS lexical baseline."""
from __future__ import annotations

from pathlib import Path

from research_evidence.index.lexical import LexicalIndex
from research_evidence.parsers.markdown import parse_markdown


def test_lexical_index_search_is_local_and_deterministic(tmp_path: Path) -> None:
    """Index source units and return stable ranked results without external calls."""
    units = parse_markdown(
        "# Findings\n\nWeighted poverty fell.\n\nUnrelated note.",
        "source-version:v1",
    )
    index = LexicalIndex(tmp_path / "index.sqlite")
    index.rebuild(units)
    assert [unit.text for unit in index.search("weighted poverty")] == ["Weighted poverty fell."]
    assert index.search("does-not-exist") == []
    assert index.get(units[1].source_unit_id) == units[1]
    index.close()


def test_equal_lexical_results_use_source_unit_id_tie_breaking(tmp_path: Path) -> None:
    """Make equal-score ordering reproducible across repeated queries."""
    units = parse_markdown(
        "Alpha finding.\n\nAlpha finding.",
        "source-version:v1",
    )
    index = LexicalIndex(tmp_path / "index.sqlite")
    index.rebuild(units)
    first = [unit.source_unit_id for unit in index.search("Alpha")]
    second = [unit.source_unit_id for unit in index.search("Alpha")]
    assert first == second == sorted(first)
    index.close()
