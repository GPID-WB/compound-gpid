"""Tests for team_brain.dedup — Contradiction detection.

Covers: Jaccard computation, tokenisation, candidate pairing, intra-project
skipping, contradiction vs contextual-variant classification, empty/missing
patterns directory, and the full detect_contradictions() integration path.

Run from repo root:
    python -m pytest scripts/team_brain/tests/test_dedup.py -v
"""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from team_brain.dedup import (
    ContradictionReport,
    JACCARD_THRESHOLD,
    MAX_JSONL_BYTES,
    _jaccard,
    _load_all_patterns,
    _tokenize,
    detect_contradictions,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_entry(
    entry_id: str,
    project: str,
    pattern: str,
    tags=None,
    date: str = "2026-01-01",
    confidence: float = 1.0,
    root_cause: str = "",
    title: str = "",
    topic: str = "",
) -> dict:
    return {
        "id": entry_id,
        "date": date,
        "source-project": project,
        "topic": topic,
        "tags": tags or [],
        "pattern": pattern,
        "entry-path": f"entries/{project}/{entry_id}.md",
        "confidence": confidence,
        "superseded-by": None,
        "root-cause": root_cause,
        "title": title,
    }


def _write_jsonl(dir_path: Path, filename: str, entries: list) -> None:
    (dir_path / filename).write_text(
        "\n".join(json.dumps(e) for e in entries) + "\n", encoding="utf-8"
    )


# ---------------------------------------------------------------------------
# _tokenize
# ---------------------------------------------------------------------------


class TestTokenize(unittest.TestCase):
    def test_basic_tokenisation(self):
        """Common words are returned as lowercase tokens."""
        result = _tokenize("Always guard inputs at boundaries.")
        self.assertIn("guard", result)
        self.assertIn("inputs", result)
        self.assertIn("boundaries", result)

    def test_stop_words_excluded(self):
        """Stop words like 'the', 'in', 'is' are excluded."""
        result = _tokenize("the guard is in the system")
        self.assertNotIn("the", result)
        self.assertNotIn("in", result)
        self.assertNotIn("is", result)

    def test_single_char_excluded(self):
        """Single-character tokens (len=1) are excluded by the 2+ regex."""
        result = _tokenize("a b c guard")
        self.assertNotIn("a", result)
        self.assertNotIn("b", result)
        self.assertNotIn("c", result)
        self.assertIn("guard", result)

    def test_case_insensitive(self):
        """Tokens are lowercased regardless of input case."""
        result = _tokenize("Always GUARD Inputs")
        self.assertIn("always", result)
        self.assertIn("guard", result)
        self.assertIn("inputs", result)

    def test_empty_string(self):
        """Empty string returns empty set."""
        self.assertEqual(_tokenize(""), set())

    def test_non_alpha_delimiters(self):
        """Non-alphabetic characters act as delimiters."""
        result = _tokenize("null-check: always validate!")
        self.assertIn("null", result)
        self.assertIn("check", result)
        self.assertIn("always", result)
        self.assertIn("validate", result)


# ---------------------------------------------------------------------------
# _jaccard
# ---------------------------------------------------------------------------


class TestJaccard(unittest.TestCase):
    def test_identical_sets(self):
        """Identical sets → Jaccard = 1.0."""
        s = {"guard", "inputs", "boundary"}
        self.assertAlmostEqual(_jaccard(s, s), 1.0)

    def test_disjoint_sets(self):
        """Disjoint sets → Jaccard = 0.0."""
        a = {"guard", "inputs"}
        b = {"cache", "timeout"}
        self.assertAlmostEqual(_jaccard(a, b), 0.0)

    def test_partial_overlap(self):
        """Partial overlap is between 0 and 1."""
        a = {"guard", "inputs", "boundary"}
        b = {"guard", "validate"}
        # intersection: {guard}, union: {guard, inputs, boundary, validate}
        expected = 1 / 4
        self.assertAlmostEqual(_jaccard(a, b), expected)

    def test_empty_a(self):
        """Empty first set → 0.0."""
        self.assertAlmostEqual(_jaccard(set(), {"guard"}), 0.0)

    def test_empty_b(self):
        """Empty second set → 0.0."""
        self.assertAlmostEqual(_jaccard({"guard"}, set()), 0.0)

    def test_both_empty(self):
        """Both empty → 0.0."""
        self.assertAlmostEqual(_jaccard(set(), set()), 0.0)


# ---------------------------------------------------------------------------
# _load_all_patterns
# ---------------------------------------------------------------------------


class TestLoadAllPatterns(unittest.TestCase):
    def test_loads_valid_jsonl(self):
        """Valid JSONL files are loaded and returned."""
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            entry = _make_entry("id1", "proj-a", "Always guard inputs.")
            _write_jsonl(p, "proj-a.jsonl", [entry])
            result = _load_all_patterns(p)
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0]["id"], "id1")

    def test_skips_blank_lines(self):
        """Blank lines in JSONL are silently skipped."""
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            entry = _make_entry("id1", "proj-a", "Guard inputs.")
            (p / "proj-a.jsonl").write_text(
                json.dumps(entry) + "\n\n\n", encoding="utf-8"
            )
            result = _load_all_patterns(p)
            self.assertEqual(len(result), 1)

    def test_malformed_line_warns_and_skips(self):
        """Malformed JSON lines emit a UserWarning and are skipped."""
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            (p / "proj-a.jsonl").write_text(
                "not-valid-json\n", encoding="utf-8"
            )
            with self.assertWarns(UserWarning):
                result = _load_all_patterns(p)
            self.assertEqual(result, [])

    def test_non_existent_directory(self):
        """Non-existent directory returns empty list without error."""
        result = _load_all_patterns(Path("/nonexistent/path/99999"))
        self.assertEqual(result, [])

    def test_oversized_jsonl_skipped_with_warning(self):
        """Oversized JSONL files are skipped before full read_text()."""
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            jsonl_path = p / "proj-a.jsonl"
            jsonl_path.write_text("{}\n", encoding="utf-8")
            original_stat = Path.stat

            def fake_stat(path, *args, **kwargs):
                result = original_stat(path, *args, **kwargs)
                if path == jsonl_path:
                    return type("Stat", (), {"st_size": MAX_JSONL_BYTES + 1})()
                return result

            with patch.object(Path, "stat", fake_stat):
                with self.assertWarns(UserWarning):
                    result = _load_all_patterns(p)
            self.assertEqual(result, [])

    def test_empty_directory(self):
        """Empty patterns directory returns empty list."""
        with tempfile.TemporaryDirectory() as tmp:
            result = _load_all_patterns(Path(tmp))
            self.assertEqual(result, [])

    def test_multiple_files(self):
        """Entries from multiple JSONL files are all returned."""
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            _write_jsonl(p, "proj-a.jsonl", [_make_entry("a1", "proj-a", "Guard inputs.")])
            _write_jsonl(p, "proj-b.jsonl", [_make_entry("b1", "proj-b", "Validate boundary.")])
            result = _load_all_patterns(p)
            ids = {e["id"] for e in result}
            self.assertIn("a1", ids)
            self.assertIn("b1", ids)


# ---------------------------------------------------------------------------
# detect_contradictions — core scenarios
# ---------------------------------------------------------------------------


class TestDetectContradictions(unittest.TestCase):
    """Integration tests for detect_contradictions()."""

    def test_empty_patterns_directory(self):
        """Empty directory returns empty report without error."""
        with tempfile.TemporaryDirectory() as tmp:
            result = detect_contradictions(Path(tmp))
            self.assertEqual(result, [])

    def test_nonexistent_patterns_directory(self):
        """Non-existent directory returns empty report without error."""
        result = detect_contradictions(Path("/nonexistent/patterns/99999"))
        self.assertEqual(result, [])

    def test_single_entry_no_pairs(self):
        """One entry → no pairs possible → empty report."""
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            _write_jsonl(p, "proj-a.jsonl", [
                _make_entry("a1", "proj-a", "Always validate guard inputs boundary.")
            ])
            result = detect_contradictions(p)
            self.assertEqual(result, [])

    def test_intra_project_pair_skipped(self):
        """Two entries from the same project are never compared."""
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            _write_jsonl(p, "proj-a.jsonl", [
                _make_entry("a1", "proj-a", "Always validate guard inputs boundary safely."),
                _make_entry("a2", "proj-a", "Always validate guard inputs boundary safely."),
            ])
            result = detect_contradictions(p)
            self.assertEqual(result, [])

    def test_high_jaccard_same_root_cause_flagged_as_contradiction(self):
        """Two entries with high Jaccard + overlapping root-cause → contradiction."""
        # Patterns that are nearly identical
        pattern = "Always guard null validate inputs system boundary"
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            _write_jsonl(p, "proj-a.jsonl", [
                _make_entry(
                    "a1", "proj-a", pattern,
                    date="2026-01-01", root_cause="null guard validation",
                    title="null check guard"
                )
            ])
            _write_jsonl(p, "proj-b.jsonl", [
                _make_entry(
                    "b1", "proj-b", pattern,
                    date="2026-02-01", root_cause="null guard validation",
                    title="null check guard"
                )
            ])
            result = detect_contradictions(p)
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0].classification, "contradiction")
            # Newer entry (b1) should be the recommended winner
            self.assertIn("b1", result[0].recommended_action)

    def test_high_jaccard_different_root_cause_is_contextual_variant(self):
        """Two entries with high Jaccard + different root-cause → contextual variant."""
        pattern = "Always validate guard inputs boundary system"
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            _write_jsonl(p, "proj-a.jsonl", [
                _make_entry(
                    "a1", "proj-a", pattern,
                    root_cause="concurrent request race",
                    title="race condition prevention"
                )
            ])
            _write_jsonl(p, "proj-b.jsonl", [
                _make_entry(
                    "b1", "proj-b", pattern,
                    root_cause="database schema mismatch type",
                    title="type mismatch database error"
                )
            ])
            result = detect_contradictions(p)
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0].classification, "contextual_variant")
            self.assertIn("context-note", result[0].recommended_action)

    def test_low_jaccard_pair_not_grouped(self):
        """Two entries with Jaccard below threshold are not grouped."""
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            _write_jsonl(p, "proj-a.jsonl", [
                _make_entry("a1", "proj-a", "Guard null validation boundary inputs system")
            ])
            _write_jsonl(p, "proj-b.jsonl", [
                _make_entry("b1", "proj-b", "Configure database timeout retry exponential backoff")
            ])
            result = detect_contradictions(p)
            self.assertEqual(result, [])

    def test_shared_tags_included_in_report(self):
        """Shared tags between two entries are captured in the report."""
        pattern = "Always validate guard inputs boundary system"
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            _write_jsonl(p, "proj-a.jsonl", [
                _make_entry("a1", "proj-a", pattern, tags=["validation", "guard", "null"])
            ])
            _write_jsonl(p, "proj-b.jsonl", [
                _make_entry("b1", "proj-b", pattern, tags=["validation", "guard", "error"])
            ])
            result = detect_contradictions(p)
            self.assertGreater(len(result), 0)
            shared = result[0].shared_tags
            self.assertIn("validation", shared)
            self.assertIn("guard", shared)
            self.assertNotIn("null", shared)
            self.assertNotIn("error", shared)

    def test_report_jaccard_score_is_captured(self):
        """The Jaccard score is recorded in the ContradictionReport."""
        pattern = "Always validate guard inputs boundary"
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            _write_jsonl(p, "proj-a.jsonl", [
                _make_entry("a1", "proj-a", pattern)
            ])
            _write_jsonl(p, "proj-b.jsonl", [
                _make_entry("b1", "proj-b", pattern)
            ])
            result = detect_contradictions(p)
            self.assertGreater(len(result), 0)
            self.assertGreater(result[0].jaccard_score, JACCARD_THRESHOLD)

    def test_too_few_tokens_pair_skipped(self):
        """Entries with fewer than MIN_TOKEN_COUNT tokens are not compared."""
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            # Patterns with only 1-2 meaningful tokens
            _write_jsonl(p, "proj-a.jsonl", [
                _make_entry("a1", "proj-a", "guard")
            ])
            _write_jsonl(p, "proj-b.jsonl", [
                _make_entry("b1", "proj-b", "guard")
            ])
            result = detect_contradictions(p)
            self.assertEqual(result, [])

    def test_contradiction_report_fields_populated(self):
        """ContradictionReport has all expected fields populated."""
        pattern = "Always validate guard inputs boundary system cache"
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            _write_jsonl(p, "proj-a.jsonl", [
                _make_entry("a1", "proj-a", pattern,
                            root_cause="missing guard", title="guard fix")
            ])
            _write_jsonl(p, "proj-b.jsonl", [
                _make_entry("b1", "proj-b", pattern,
                            root_cause="missing guard", title="guard fix")
            ])
            result = detect_contradictions(p)
            self.assertGreater(len(result), 0)
            r = result[0]
            self.assertIsInstance(r, ContradictionReport)
            self.assertIn(r.classification, ("contradiction", "contextual_variant"))
            self.assertGreater(r.jaccard_score, 0)
            self.assertIsInstance(r.recommended_action, str)
            self.assertGreater(len(r.recommended_action), 0)
            self.assertIsInstance(r.entry_a, dict)
            self.assertIsInstance(r.entry_b, dict)
