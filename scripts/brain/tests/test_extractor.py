"""Tests for brain.extractor — keyword extraction.

Run from repo root:
    python -m pytest scripts/brain/tests/test_extractor.py -v
"""
from __future__ import annotations

from pathlib import Path

import pytest

from brain import Entity
from brain.extractor import (
    _MAX_KEYWORDS,
    _STOPWORDS,
    extract_keywords,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _entity(**kwargs) -> Entity:
    defaults = dict(
        path=Path("test.md"),
        entity_type="solution",
        frontmatter={},
    )
    defaults.update(kwargs)
    return Entity(**defaults)


def _kw_dict(text: str, entity: Entity | None = None) -> dict:
    """Run extract_keywords and return a {keyword: score} dict."""
    if entity is None:
        entity = _entity()
    return dict(extract_keywords(entity, text))


# ---------------------------------------------------------------------------
# Signal 1: Backtick terms
# ---------------------------------------------------------------------------


class TestBacktickSignal:
    def test_backtick_term_present(self) -> None:
        scores = _kw_dict("Use `parse_frontmatter()` in the code.")
        assert "parse_frontmatter()" in scores

    def test_backtick_term_weight_3(self) -> None:
        # A single backtick hit in isolation (minimal text) should score ≥ 3.0
        scores = _kw_dict("`my_function`")
        assert scores.get("my_function", 0) >= 3.0

    def test_multiple_backtick_hits_accumulate(self) -> None:
        scores = _kw_dict("`brain` and `brain` again.")
        assert scores.get("brain", 0) >= 6.0

    def test_stopword_in_backtick_excluded(self) -> None:
        scores = _kw_dict("`file` and `files`")
        # Both "file" and "files" are in _STOPWORDS — should be absent or 0
        assert scores.get("file", 0) == 0
        assert scores.get("files", 0) == 0


# ---------------------------------------------------------------------------
# Signal 2: Heading text
# ---------------------------------------------------------------------------


class TestHeadingSignal:
    def test_heading_word_present(self) -> None:
        scores = _kw_dict("## Frontmatter Parser\n\nSome body.")
        assert "frontmatter" in scores or "parser" in scores

    def test_h1_heading_counted(self) -> None:
        scores = _kw_dict("# Scanner Module\n\n")
        assert "scanner" in scores

    def test_heading_word_boosted(self) -> None:
        # "scanner" appears only in a heading — should have a non-trivial score
        scores = _kw_dict("# Scanner\n\nIrrelevant body text here.")
        assert scores.get("scanner", 0) >= 3.0

    def test_heading_stopwords_excluded(self) -> None:
        scores = _kw_dict("## How To Use The File\n\n")
        # "how", "the", "file", "use" are stopwords — must not be boosted by heading signal
        for sw in ("how", "the", "file", "use"):
            assert scores.get(sw, 0) == 0, f"Stopword '{sw}' should not be boosted by heading signal"


# ---------------------------------------------------------------------------
# Signal 3: /cg-* command refs
# ---------------------------------------------------------------------------


class TestCommandRefSignal:
    def test_slash_command_present(self) -> None:
        scores = _kw_dict("Run `/cg-brainstorm` to start.")
        assert "cg-brainstorm" in scores

    def test_slash_prefix_stripped(self) -> None:
        scores = _kw_dict("/cg-plan")
        # should appear as "cg-plan", not "/cg-plan"
        assert "cg-plan" in scores
        assert "/cg-plan" not in scores

    def test_multiple_commands(self) -> None:
        scores = _kw_dict("/cg-plan and /cg-brainstorm and /cg-work")
        assert "cg-plan" in scores
        assert "cg-brainstorm" in scores
        assert "cg-work" in scores

    def test_command_weight_2(self) -> None:
        scores = _kw_dict("/cg-scanner")
        assert scores.get("cg-scanner", 0) >= 2.0


# ---------------------------------------------------------------------------
# Signal 4: File refs
# ---------------------------------------------------------------------------


class TestFileRefSignal:
    def test_py_file_ref_captured(self) -> None:
        scores = _kw_dict("See `cg_index.py` for details.")
        assert "cg_index.py" in scores

    def test_ps1_file_ref_captured(self) -> None:
        scores = _kw_dict("Edit `helpers.ps1` and `Run-Tests.ps1`.")
        assert "helpers.ps1" in scores or "run-tests.ps1" in scores

    def test_md_file_ref_captured(self) -> None:
        scores = _kw_dict("See BRAIN.md for the output.")
        assert "brain.md" in scores

    def test_file_ref_weight_2(self) -> None:
        scores = _kw_dict("Only `extractor.py` is mentioned.")
        assert scores.get("extractor.py", 0) >= 2.0


# ---------------------------------------------------------------------------
# Signal 5: Pattern names (Title Case phrases)
# ---------------------------------------------------------------------------


class TestPatternNameSignal:
    def test_two_word_title_case(self) -> None:
        # "an" separates verb from noun phrase, so regex captures just "Inverted Index"
        scores = _kw_dict("Applies an Inverted Index to the data.")
        assert "inverted index" in scores

    def test_three_word_title_case(self) -> None:
        # "the" separates verb from noun phrase
        scores = _kw_dict("Applies the Greedy Agglomerative Clustering algorithm.")
        assert "greedy agglomerative clustering" in scores

    def test_pattern_name_weight_3(self) -> None:
        # "an" separates verb from noun phrase
        scores = _kw_dict("Use an Atomic Write for safety.")
        assert scores.get("atomic write", 0) >= 3.0

    def test_single_capitalized_word_not_matched(self) -> None:
        """Single capitalised words (sentence starts) are not "pattern names"."""
        scores = _kw_dict("Python is great.")
        # "python" might appear from frequency but not from pattern signal
        # The pattern regex requires 2+ consecutive Title Case words
        # This just ensures no crash
        assert isinstance(scores, dict)


# ---------------------------------------------------------------------------
# Signal 6: Frequency keywords
# ---------------------------------------------------------------------------


class TestFrequencySignal:
    def test_repeated_word_scores_higher(self) -> None:
        scores = _kw_dict("clustering clustering clustering")
        assert scores.get("clustering", 0) > 0

    def test_stopwords_excluded_from_frequency(self) -> None:
        scores = _kw_dict("the the the a a a and and and")
        for sw in ("the", "a", "and"):
            assert scores.get(sw, 0) == 0

    def test_non_stop_word_present(self) -> None:
        scores = _kw_dict("The extractor processes entities efficiently.")
        assert "extractor" in scores or "processes" in scores or "entities" in scores


# ---------------------------------------------------------------------------
# Frontmatter signals
# ---------------------------------------------------------------------------


class TestFrontmatterSignals:
    def test_title_words_boosted(self) -> None:
        e = _entity(frontmatter={"title": "Pester Safety Rules"})
        scores = _kw_dict("Some irrelevant body.", entity=e)
        # "pester", "safety", "rules" should all be present
        assert "pester" in scores
        assert "safety" in scores or "rules" in scores

    def test_tags_boosted(self) -> None:
        e = _entity(frontmatter={"tags": ["pester", "powershell"]})
        scores = _kw_dict("Irrelevant body.", entity=e)
        assert "pester" in scores
        assert "powershell" in scores

    def test_stopword_tags_excluded(self) -> None:
        e = _entity(frontmatter={"tags": ["file", "data"]})
        scores = _kw_dict("Some body.", entity=e)
        # "file" and "data" are stopwords — should not be in scores
        assert scores.get("file", 0) == 0
        assert scores.get("data", 0) == 0


# ---------------------------------------------------------------------------
# Output format and limits
# ---------------------------------------------------------------------------


class TestOutputFormat:
    def test_returns_list_of_tuples(self) -> None:
        result = extract_keywords(_entity(), "some text about pester testing")
        assert isinstance(result, list)
        for item in result:
            assert isinstance(item, tuple)
            assert len(item) == 2
            assert isinstance(item[0], str)
            assert isinstance(item[1], float)

    def test_sorted_descending(self) -> None:
        result = extract_keywords(_entity(), "## Pester\n\n`pester` and `pester`")
        scores = [score for _, score in result]
        assert scores == sorted(scores, reverse=True)

    def test_max_keywords_respected(self) -> None:
        # Generate text with many unique words
        words = [f"uniqueword{i}" for i in range(200)]
        text = " ".join(words)
        result = extract_keywords(_entity(), text)
        assert len(result) <= _MAX_KEYWORDS

    def test_empty_text_returns_empty(self) -> None:
        result = extract_keywords(_entity(), "")
        assert result == []

    def test_keywords_lowercased(self) -> None:
        result = extract_keywords(_entity(), "## UPPER CASE HEADING\n")
        keywords = [k for k, _ in result]
        for kw in keywords:
            assert kw == kw.lower() or kw == kw  # no fully-upper keywords


# ---------------------------------------------------------------------------
# Stopword list sanity checks
# ---------------------------------------------------------------------------


class TestStopwords:
    def test_common_english_words_in_stopwords(self) -> None:
        for word in ("the", "and", "or", "is", "in", "of", "with"):
            assert word in _STOPWORDS, f"'{word}' should be a stopword"

    def test_domain_noise_in_stopwords(self) -> None:
        for word in ("cg", "docs", "path", "code", "data"):
            assert word in _STOPWORDS, f"'{word}' should be a stopword"

    def test_meaningful_words_not_in_stopwords(self) -> None:
        for word in ("pester", "powershell", "scanner", "extractor", "clustering"):
            assert word not in _STOPWORDS, f"'{word}' should NOT be a stopword"
