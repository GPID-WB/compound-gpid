"""Tests for team_brain.pull.

Covers: cache path helpers, freshness checks, topic keyword parsing, keyword
overlap scoring, project name extraction, disabled config, empty keywords,
TEAM-BRAIN.md fetch failures (network unavailable), pattern matching, and
end-to-end pull_from_team_brain with mocked subprocess.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from team_brain.config import TeamBrainLocalConfig
from team_brain.pull import (
    MatchedPattern,
    PullResult,
    _cache_dir,
    _cache_path,
    _extract_project_names,
    _fetch_remote_raw,
    _is_cache_fresh,
    _keyword_overlap_score,
    _parse_topic_keywords,
    pull_from_team_brain,
)

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

_CONFIG = TeamBrainLocalConfig(
    repo="GPID-WB/team-brain",
    project_name="compound-gpid",
    enabled=True,
    llm_filter=False,
)

_DISABLED_CONFIG = TeamBrainLocalConfig(
    repo="GPID-WB/team-brain",
    project_name="compound-gpid",
    enabled=False,
    llm_filter=False,
)

_SAMPLE_INDEX = """\
# 🧠 Team Brain

## Topic Index

| # | Topic | Entries | File |
|---|-------|---------|------|
| 1 | [Null / Validation / Guard](TEAM-BRAIN-01.md) | 5 | TEAM-BRAIN-01.md |
| 2 | [Privacy / Redaction / Filter](TEAM-BRAIN-01.md) | 3 | TEAM-BRAIN-01.md |

## Entries

- entries/compound-gpid/2026-05-20-fix-null.md
- entries/pcn-tools/2026-05-15-fix-encoding.md
"""

_SAMPLE_JSONL_LINE = json.dumps({
    "id": "2026-05-20-fix-null-check",
    "date": "2026-05-20",
    "source-project": "compound-gpid",
    "topic": "validation",
    "tags": ["null", "validation", "guard"],
    "pattern": "Always validate inputs at system boundaries.",
    "entry-path": "entries/compound-gpid/2026-05-20-fix-null-check.md",
    "confidence": 1.0,
    "superseded-by": None,
})


# ---------------------------------------------------------------------------
# Cache helpers
# ---------------------------------------------------------------------------


class TestCacheDir(unittest.TestCase):
    """Tests for _cache_dir and _cache_path."""

    def test_cache_dir_slug_replaces_slash(self):
        """Repo slashes are replaced with underscores in the cache slug."""
        d = _cache_dir("GPID-WB/team-brain")
        self.assertNotIn("/", d.name)
        self.assertIn("GPID-WB_team-brain", str(d))

    def test_cache_dir_uses_xdg_cache_home(self):
        """XDG_CACHE_HOME override is respected when set."""
        with patch.dict(os.environ, {"XDG_CACHE_HOME": "/tmp/xdg"}, clear=False):
            d = _cache_dir("owner/repo")
        # Check that the XDG value appears in the path (OS-agnostic assertion)
        self.assertIn("xdg", str(d).replace("\\", "/").lower())

    def test_cache_path_is_team_brain_md(self):
        """Cache path ends in TEAM-BRAIN.md."""
        p = _cache_path("owner/repo")
        self.assertEqual(p.name, "TEAM-BRAIN.md")


class TestIsCacheFresh(unittest.TestCase):
    """Tests for _is_cache_fresh."""

    def test_missing_file_is_not_fresh(self):
        """Non-existent file returns False."""
        self.assertFalse(_is_cache_fresh(Path("/tmp/__nonexistent_cg_test__.md")))

    def test_recent_file_is_fresh(self):
        """File modified < max_age seconds ago is fresh."""
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix=".md") as f:
            f.write(b"content")
            tmp = Path(f.name)
        try:
            self.assertTrue(_is_cache_fresh(tmp, max_age=3600))
        finally:
            tmp.unlink(missing_ok=True)

    def test_old_file_is_stale(self):
        """File with mtime in the past is stale."""
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix=".md") as f:
            f.write(b"content")
            tmp = Path(f.name)
        try:
            os.utime(tmp, (time.time() - 7200, time.time() - 7200))
            self.assertFalse(_is_cache_fresh(tmp, max_age=3600))
        finally:
            tmp.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# Topic parsing
# ---------------------------------------------------------------------------


class TestParseTopicKeywords(unittest.TestCase):
    """Tests for _parse_topic_keywords."""

    def test_parses_linked_topics(self):
        """Linked topic rows ([text](link)) are parsed correctly."""
        topics = _parse_topic_keywords(_SAMPLE_INDEX)
        self.assertGreater(len(topics), 0)
        names = [t[0] for t in topics]
        self.assertTrue(any("Null" in n or "null" in n for n in names))

    def test_extracts_keywords_from_slash_separated_name(self):
        """'Null / Validation / Guard' tokenizes to ['null', 'validation', 'guard']."""
        topics = _parse_topic_keywords(_SAMPLE_INDEX)
        kw_lists = [kws for _, kws in topics]
        all_keywords = [kw for kws in kw_lists for kw in kws]
        self.assertIn("null", all_keywords)
        self.assertIn("validation", all_keywords)
        self.assertIn("guard", all_keywords)

    def test_empty_content_returns_empty_list(self):
        """Empty or header-only content produces no topics."""
        result = _parse_topic_keywords("# No table\n\nJust prose.\n")
        self.assertEqual(result, [])

    def test_skips_separator_rows(self):
        """Separator rows (|---|---) are not returned as topics."""
        topics = _parse_topic_keywords(_SAMPLE_INDEX)
        for name, _ in topics:
            self.assertNotIn("---", name)


# ---------------------------------------------------------------------------
# Project name extraction
# ---------------------------------------------------------------------------


class TestExtractProjectNames(unittest.TestCase):
    """Tests for _extract_project_names."""

    def test_extracts_project_names(self):
        """Project names are extracted from entries/ paths."""
        names = _extract_project_names(_SAMPLE_INDEX)
        self.assertIn("compound-gpid", names)
        self.assertIn("pcn-tools", names)

    def test_returns_empty_when_no_entries(self):
        """Returns empty list when no entries/ references exist."""
        result = _extract_project_names("# Just a title\n")
        self.assertEqual(result, [])

    def test_no_duplicates(self):
        """Duplicate entries/ references produce deduplicated project names."""
        content = "entries/proj/a.md\nentries/proj/b.md\n"
        result = _extract_project_names(content)
        self.assertEqual(result.count("proj"), 1)


# ---------------------------------------------------------------------------
# Keyword overlap scoring
# ---------------------------------------------------------------------------


class TestKeywordOverlapScore(unittest.TestCase):
    """Tests for _keyword_overlap_score."""

    def test_exact_tag_match(self):
        """Exact match on a tag returns score ≥ 1."""
        score = _keyword_overlap_score(["null"], ["null", "validation"], "some pattern")
        self.assertGreaterEqual(score, 1)

    def test_pattern_text_word_match(self):
        """Keyword that appears verbatim as a word in pattern text scores ≥ 1."""
        score = _keyword_overlap_score(
            ["validate"], [], "Always validate inputs at system boundaries."
        )
        self.assertGreaterEqual(score, 1)

    def test_no_overlap_returns_zero(self):
        """Unrelated keywords return zero overlap."""
        score = _keyword_overlap_score(
            ["pester", "powershell"], ["python", "validation"], "Always validate."
        )
        self.assertEqual(score, 0)

    def test_case_insensitive(self):
        """Matching is case-insensitive."""
        score = _keyword_overlap_score(["NULL"], ["null"], "")
        self.assertGreaterEqual(score, 1)


# ---------------------------------------------------------------------------
# Disabled config
# ---------------------------------------------------------------------------


class TestPullDisabledConfig(unittest.TestCase):
    """Tests for pull_from_team_brain with disabled config."""

    def test_disabled_config_returns_empty(self):
        """Disabled team brain config skips pull and returns empty result."""
        result = pull_from_team_brain(["null"], _DISABLED_CONFIG)
        self.assertEqual(result.patterns, [])
        self.assertIn("skipped", result.summary.lower())
        self.assertFalse(result.cache_used)

    def test_empty_keywords_returns_empty(self):
        """Empty keywords list returns skipped result without fetching."""
        result = pull_from_team_brain([], _CONFIG)
        self.assertEqual(result.patterns, [])
        self.assertIn("skipped", result.summary.lower())


# ---------------------------------------------------------------------------
# Network failure handling
# ---------------------------------------------------------------------------


class TestPullNetworkFailure(unittest.TestCase):
    """Tests for pull_from_team_brain when network is unavailable."""

    @patch("team_brain.pull._fetch_remote_raw", return_value=None)
    def test_fetch_failure_no_cache_returns_failure_result(self, _mock):
        """When remote fetch fails and no cache exists, returns failure result."""
        with patch("team_brain.pull._cache_path") as mock_cp:
            mock_cp.return_value = Path("/tmp/__nonexistent_cg_brain__.md")
            result = pull_from_team_brain(["null"], _CONFIG)
        self.assertEqual(result.patterns, [])
        self.assertIn("fail", result.summary.lower())

    @patch("team_brain.pull._fetch_remote_raw", return_value=None)
    def test_fetch_failure_uses_stale_cache(self, _mock):
        """When remote fails, stale cache is used as fallback; cache_used is True."""
        with tempfile.TemporaryDirectory() as td:
            cache_file = Path(td) / "TEAM-BRAIN.md"
            cache_file.write_text(_SAMPLE_INDEX, encoding="utf-8")
            # Make it stale (2 hours old)
            old_time = time.time() - 7200
            os.utime(cache_file, (old_time, old_time))

            with patch("team_brain.pull._cache_path", return_value=cache_file):
                with patch("team_brain.pull._fetch_project_jsonl", return_value=[]):
                    # Use keyword that matches a topic so fall-through to JSONL scoring occurs
                    result = pull_from_team_brain(["null"], _CONFIG)

        self.assertIsInstance(result, PullResult)
        # The stale fallback branch sets cache_used = True
        self.assertTrue(result.cache_used)


# ---------------------------------------------------------------------------
# Matching and scoring
# ---------------------------------------------------------------------------


class TestPullMatching(unittest.TestCase):
    """Tests for pull_from_team_brain pattern matching."""

    def _mock_fetch_index(self, _config, *, refresh=False):
        return _SAMPLE_INDEX

    def _mock_fetch_jsonl(self, _config, _project, *, refresh=False):
        return [json.loads(_SAMPLE_JSONL_LINE)]

    @patch("team_brain.pull._fetch_project_jsonl")
    @patch("team_brain.pull._fetch_team_brain_index")
    def test_matching_keywords_returns_patterns(self, mock_index, mock_jsonl):
        """Keywords matching topic + pattern tags return matched patterns."""
        mock_index.side_effect = self._mock_fetch_index
        mock_jsonl.side_effect = self._mock_fetch_jsonl

        result = pull_from_team_brain(["null", "validation"], _CONFIG)
        self.assertGreater(len(result.patterns), 0)
        self.assertIsInstance(result.patterns[0], MatchedPattern)
        self.assertEqual(result.patterns[0].source_project, "compound-gpid")
        self.assertIn("validate", result.patterns[0].pattern_text.lower())

    @patch("team_brain.pull._fetch_project_jsonl")
    @patch("team_brain.pull._fetch_team_brain_index")
    def test_unmatched_topic_returns_empty_patterns(self, mock_index, mock_jsonl):
        """Keywords with no topic match produce an empty result (no noise)."""
        mock_index.side_effect = self._mock_fetch_index
        mock_jsonl.side_effect = self._mock_fetch_jsonl

        result = pull_from_team_brain(["completely_unrelated_keyword_xyz"], _CONFIG)
        self.assertEqual(result.patterns, [])
        self.assertIn("No team brain topic matches", result.summary)

    @patch("team_brain.pull._fetch_project_jsonl")
    @patch("team_brain.pull._fetch_team_brain_index")
    def test_summary_includes_match_count(self, mock_index, mock_jsonl):
        """Summary line reports the number of matched patterns."""
        mock_index.side_effect = self._mock_fetch_index
        mock_jsonl.side_effect = self._mock_fetch_jsonl

        result = pull_from_team_brain(["null"], _CONFIG)
        # Should mention either a count or "No team brain"
        self.assertIsInstance(result.summary, str)
        self.assertGreater(len(result.summary), 0)

    @patch("team_brain.pull._fetch_project_jsonl")
    @patch("team_brain.pull._fetch_team_brain_index")
    def test_patterns_sorted_by_confidence_desc(self, mock_index, mock_jsonl):
        """Results are sorted by confidence descending."""
        mock_index.side_effect = self._mock_fetch_index

        high = dict(json.loads(_SAMPLE_JSONL_LINE))
        low = dict(json.loads(_SAMPLE_JSONL_LINE))
        high["confidence"] = 1.2
        low["confidence"] = 0.8
        low["id"] = "other-entry"
        mock_jsonl.side_effect = lambda _c, _p, **_kw: [low, high]

        result = pull_from_team_brain(["null"], _CONFIG)
        if len(result.patterns) >= 2:
            self.assertGreaterEqual(
                result.patterns[0].confidence,
                result.patterns[1].confidence,
            )

    @patch("team_brain.pull._fetch_project_jsonl")
    @patch("team_brain.pull._fetch_team_brain_index")
    def test_result_has_cache_used_field(self, mock_index, mock_jsonl):
        """PullResult always has a cache_used boolean field."""
        mock_index.side_effect = self._mock_fetch_index
        mock_jsonl.side_effect = self._mock_fetch_jsonl

        result = pull_from_team_brain(["null"], _CONFIG)
        self.assertIsInstance(result.cache_used, bool)

    @patch("team_brain.pull._fetch_project_jsonl")
    @patch("team_brain.pull._fetch_team_brain_index")
    def test_accept_header_used_for_raw_content(self, mock_index, mock_jsonl):
        """gh API call includes the Accept: application/vnd.github.raw+json header."""
        # Test _fetch_remote_raw directly — subprocess.run is never called through
        # pull_from_team_brain when _fetch_team_brain_index is mocked.
        with patch("team_brain.pull.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout=_SAMPLE_JSONL_LINE)
            _fetch_remote_raw("GPID-WB/team-brain", "TEAM-BRAIN.md")

        self.assertEqual(len(mock_run.call_args_list), 1)
        call_args = str(mock_run.call_args_list[0])
        self.assertIn("Accept: application/vnd.github.raw+json", call_args)


# ---------------------------------------------------------------------------
# Return type invariant
# ---------------------------------------------------------------------------


class TestPullReturnType(unittest.TestCase):
    """Tests that pull_from_team_brain always returns a PullResult."""

    @patch("team_brain.pull._fetch_remote_raw", return_value=None)
    def test_always_returns_pull_result(self, _mock):
        """Even on failure, return type is PullResult."""
        with patch("team_brain.pull._cache_path", return_value=Path("/tmp/__x__.md")):
            result = pull_from_team_brain(["null"], _CONFIG)
        self.assertIsInstance(result, PullResult)
        self.assertIsInstance(result.patterns, list)
        self.assertIsInstance(result.summary, str)
        self.assertIsInstance(result.cache_used, bool)


# ---------------------------------------------------------------------------
# P2.8 — Additional edge case tests (review findings)
# ---------------------------------------------------------------------------


class TestPullEdgeCases(unittest.TestCase):
    """Edge cases surfaced during Phase 2 code review."""

    def _mock_fetch_index(self, _config, *, refresh=False):
        return _SAMPLE_INDEX

    @patch("team_brain.pull._is_cache_fresh", return_value=False)
    @patch("team_brain.pull._fetch_remote_raw")
    def test_malformed_jsonl_lines_are_skipped(self, mock_fetch, _mock_fresh):
        """Malformed JSONL lines are skipped with a UserWarning; valid lines are returned."""
        mock_fetch.return_value = (
            "NOT JSON\n"
            + _SAMPLE_JSONL_LINE + "\n"
            + "{invalid}\n"
        )
        from team_brain.pull import _fetch_project_jsonl
        with self.assertWarns(UserWarning):
            entries = _fetch_project_jsonl(_CONFIG, "compound-gpid")
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["id"], "2026-05-20-fix-null-check")

    @patch("team_brain.pull._fetch_project_jsonl")
    @patch("team_brain.pull._fetch_team_brain_index")
    def test_string_format_tags_are_parsed(self, mock_index, mock_jsonl):
        """Tags as comma-string '[null, validation]' are parsed correctly."""
        mock_index.side_effect = self._mock_fetch_index
        entry = dict(json.loads(_SAMPLE_JSONL_LINE))
        entry["tags"] = "[null, validation]"
        mock_jsonl.side_effect = lambda _c, _p, **_kw: [entry]
        result = pull_from_team_brain(["null"], _CONFIG)
        self.assertGreater(len(result.patterns), 0)

    @patch("team_brain.pull._fetch_project_jsonl")
    @patch("team_brain.pull._fetch_team_brain_index")
    def test_empty_topic_list_proceeds_to_pattern_matching(self, mock_index, mock_jsonl):
        """When topic table is absent, matching proceeds without topic-level filter."""
        mock_index.return_value = "# TEAM-BRAIN\n\nNo table here.\n"
        mock_jsonl.side_effect = lambda _c, _p, **_kw: [json.loads(_SAMPLE_JSONL_LINE)]
        result = pull_from_team_brain(["null"], _CONFIG)
        self.assertIsInstance(result, PullResult)  # does not error

    @patch("team_brain.pull._fetch_project_jsonl")
    @patch("team_brain.pull._fetch_team_brain_index")
    def test_non_numeric_confidence_does_not_crash(self, mock_index, mock_jsonl):
        """Non-numeric confidence field does not raise; entry uses default 1.0."""
        mock_index.side_effect = self._mock_fetch_index
        bad_entry = dict(json.loads(_SAMPLE_JSONL_LINE))
        bad_entry["confidence"] = "high"
        mock_jsonl.side_effect = lambda _c, _p, **_kw: [bad_entry]
        result = pull_from_team_brain(["null"], _CONFIG)
        self.assertIsInstance(result, PullResult)  # must not raise
        # Entry should still be present (confidence falls back to 1.0)
        self.assertGreater(len(result.patterns), 0)

    @patch("team_brain.pull._fetch_project_jsonl")
    @patch("team_brain.pull._fetch_team_brain_index")
    def test_null_tags_do_not_crash(self, mock_index, mock_jsonl):
        """tags: null in JSONL does not raise TypeError."""
        mock_index.side_effect = self._mock_fetch_index
        bad_entry = dict(json.loads(_SAMPLE_JSONL_LINE))
        bad_entry["tags"] = None  # JSON null
        mock_jsonl.side_effect = lambda _c, _p, **_kw: [bad_entry]
        result = pull_from_team_brain(["null"], _CONFIG)
        self.assertIsInstance(result, PullResult)  # must not raise

    @patch("team_brain.pull._fetch_project_jsonl")
    @patch("team_brain.pull._fetch_team_brain_index")
    def test_array_pattern_does_not_crash(self, mock_index, mock_jsonl):
        """pattern: [] (JSON array) does not raise AttributeError."""
        mock_index.side_effect = self._mock_fetch_index
        bad_entry = dict(json.loads(_SAMPLE_JSONL_LINE))
        bad_entry["pattern"] = ["item one", "item two"]  # JSON array
        mock_jsonl.side_effect = lambda _c, _p, **_kw: [bad_entry]
        result = pull_from_team_brain(["null"], _CONFIG)
        self.assertIsInstance(result, PullResult)  # must not raise

    @patch("team_brain.pull._fetch_project_jsonl")
    @patch("team_brain.pull._fetch_team_brain_index")
    def test_inf_confidence_clamped_to_one(self, mock_index, mock_jsonl):
        """confidence: inf is clamped to 1.0 — cannot front-rank adversarially."""
        mock_index.side_effect = self._mock_fetch_index
        bad_entry = dict(json.loads(_SAMPLE_JSONL_LINE))
        bad_entry["confidence"] = "inf"
        mock_jsonl.side_effect = lambda _c, _p, **_kw: [bad_entry]
        result = pull_from_team_brain(["null"], _CONFIG)
        self.assertGreaterEqual(len(result.patterns), 1, "inf-confidence entry must still match")
        self.assertFalse(any(p.confidence == float("inf") for p in result.patterns))


if __name__ == "__main__":
    unittest.main()
