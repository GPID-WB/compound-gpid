"""Tests for team_brain.distiller.

Covers: DistillResult dataclass, all distillation sources (root-cause
frontmatter, ## Solution section, ## Root Cause section, title fallback,
empty fallback), truncation, and skipping logic for code blocks / headings.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from team_brain.distiller import DistillResult, distill_pattern


class TestDistillResult(unittest.TestCase):
    """Tests for the DistillResult dataclass."""

    def test_fields_exist(self):
        """DistillResult has pattern_text, source, and prompt fields."""
        r = DistillResult(pattern_text="foo", source="root-cause")
        self.assertEqual(r.pattern_text, "foo")
        self.assertEqual(r.source, "root-cause")
        self.assertIsNone(r.prompt)

    def test_prompt_field_accepts_string(self):
        """prompt field accepts a non-None string."""
        r = DistillResult(pattern_text="foo", source="title", prompt="Ask the model.")
        self.assertEqual(r.prompt, "Ask the model.")


class TestDistillPattern(unittest.TestCase):
    """Tests for distill_pattern."""

    # ------------------------------------------------------------------
    # Source: root-cause frontmatter
    # ------------------------------------------------------------------

    def test_root_cause_fm_wins(self):
        """root-cause frontmatter is the highest-priority source."""
        fm = {"root-cause": "Value was read before checking for None."}
        result = distill_pattern(fm, "")
        self.assertEqual(result.pattern_text, "Value was read before checking for None.")
        self.assertEqual(result.source, "root-cause")
        self.assertIsNone(result.prompt)

    def test_root_cause_fm_truncates_long(self):
        """root-cause strings longer than 200 chars are truncated to 200."""
        fm = {"root-cause": "X" * 300}
        result = distill_pattern(fm, "")
        self.assertEqual(len(result.pattern_text), 200)
        self.assertEqual(result.source, "root-cause")

    def test_root_cause_fm_strips_quotes(self):
        """Quoted root-cause values are unquoted before returning."""
        fm = {"root-cause": '"Always guard inputs."'}
        result = distill_pattern(fm, "")
        self.assertEqual(result.pattern_text, "Always guard inputs.")

    def test_root_cause_fm_beats_solution_section(self):
        """root-cause frontmatter wins even when ## Solution section exists."""
        fm = {"root-cause": "Frontmatter wins."}
        body = "## Solution\n\nSection would lose.\n"
        result = distill_pattern(fm, body)
        self.assertEqual(result.pattern_text, "Frontmatter wins.")
        self.assertEqual(result.source, "root-cause")

    # ------------------------------------------------------------------
    # Source: ## Solution section
    # ------------------------------------------------------------------

    def test_solution_section_used_when_no_root_cause(self):
        """First sentence from ## Solution section used when no root-cause field."""
        body = "## Solution\n\nAlways validate inputs at entry points.\n"
        result = distill_pattern({}, body)
        self.assertEqual(result.pattern_text, "Always validate inputs at entry points.")
        self.assertEqual(result.source, "solution-section")
        self.assertIsNone(result.prompt)

    def test_solution_section_wins_over_root_cause_section(self):
        """## Solution section wins over ## Root Cause section."""
        body = "## Solution\n\nAlways validate.\n\n## Root Cause\n\nCaller passed None.\n"
        result = distill_pattern({}, body)
        self.assertEqual(result.source, "solution-section")

    def test_solution_section_skips_short_tokens(self):
        """Short tokens (≤10 chars) in the section body are skipped."""
        body = "## Solution\n\nFix it.\n\nAlways validate inputs at system boundaries.\n"
        result = distill_pattern({}, body)
        self.assertIn("validate", result.pattern_text)
        self.assertEqual(result.source, "solution-section")

    def test_solution_section_skips_code_blocks(self):
        """Lines starting with ``` are not used as patterns."""
        body = (
            "## Solution\n\n"
            "```python\nraise ValueError\n```\n\n"
            "Always guard inputs at the entry point.\n"
        )
        result = distill_pattern({}, body)
        self.assertEqual(result.pattern_text, "Always guard inputs at the entry point.")
        self.assertEqual(result.source, "solution-section")

    def test_solution_section_skips_table_rows(self):
        """Lines starting with | are not used as patterns."""
        body = "## Solution\n\n| col1 | col2 |\n|------|------|\n\nUse explicit checks.\n"
        result = distill_pattern({}, body)
        self.assertEqual(result.pattern_text, "Use explicit checks.")

    def test_solution_section_skips_list_items(self):
        """Lines starting with - are not used as patterns."""
        body = "## Solution\n\n- Do this.\n- Do that.\n\nAlways validate inputs.\n"
        result = distill_pattern({}, body)
        self.assertEqual(result.pattern_text, "Always validate inputs.")

    # ------------------------------------------------------------------
    # Source: ## Root Cause section
    # ------------------------------------------------------------------

    def test_root_cause_section_fallback(self):
        """## Root Cause section used when no root-cause field and no ## Solution."""
        body = "## Root Cause\n\nThe caller passed None instead of an empty list.\n"
        result = distill_pattern({}, body)
        self.assertEqual(result.source, "root-cause-section")
        self.assertIn("None", result.pattern_text)
        self.assertIsNone(result.prompt)

    # ------------------------------------------------------------------
    # Source: title
    # ------------------------------------------------------------------

    def test_title_fallback(self):
        """Title used when no root-cause field and no relevant sections."""
        result = distill_pattern({"title": "Fix missing null check"}, "No sections.")
        self.assertEqual(result.pattern_text, "Fix missing null check")
        self.assertEqual(result.source, "title")
        self.assertIsNotNone(result.prompt)

    def test_title_fallback_provides_llm_prompt(self):
        """LLM prompt string is non-empty when source is 'title'."""
        result = distill_pattern({"title": "My fix"}, "")
        self.assertIsInstance(result.prompt, str)
        self.assertGreater(len(result.prompt), 20)

    def test_title_fallback_truncates_long(self):
        """Title strings longer than 200 chars are truncated."""
        result = distill_pattern({"title": "T" * 300}, "")
        self.assertEqual(len(result.pattern_text), 200)

    # ------------------------------------------------------------------
    # Source: fallback
    # ------------------------------------------------------------------

    def test_fallback_when_empty(self):
        """Returns (no pattern) when no information is available."""
        result = distill_pattern({}, "")
        self.assertEqual(result.pattern_text, "(no pattern)")
        self.assertEqual(result.source, "fallback")

    def test_fallback_when_only_noise(self):
        """Returns fallback when body has only short/blocked lines."""
        body = "## Solution\n\n- ok\n```code```\n| col |\n"
        result = distill_pattern({}, body)
        self.assertEqual(result.source, "fallback")

    # ------------------------------------------------------------------
    # Return type
    # ------------------------------------------------------------------

    def test_returns_distill_result(self):
        """Return type is always DistillResult."""
        for fm, body in [
            ({"root-cause": "x" * 15}, ""),
            ({}, "## Solution\n\nAlways validate inputs properly.\n"),
            ({}, "## Root Cause\n\nCaller did not handle the None case.\n"),
            ({"title": "My solution"}, ""),
            ({}, ""),
        ]:
            with self.subTest(fm=fm):
                result = distill_pattern(fm, body)
                self.assertIsInstance(result, DistillResult)


if __name__ == "__main__":
    unittest.main()


# ---------------------------------------------------------------------------
# P3.6 — Additional coverage tests (review findings)
# ---------------------------------------------------------------------------


class TestDistillerReviewFindings(unittest.TestCase):
    """Tests added during Phase 2 code review to fill coverage gaps."""

    def test_empty_fallback_source(self):
        """Empty frontmatter and body returns fallback source with no prompt."""
        result = distill_pattern({}, "")
        self.assertEqual(result.pattern_text, "(no pattern)")
        self.assertEqual(result.source, "fallback")
        self.assertIsNone(result.prompt)

    def test_root_cause_section_skips_code_blocks(self):
        """Code blocks in ## Root Cause are skipped; prose following them is used."""
        body = (
            "## Root Cause\n\n"
            "```python\nraise ValueError\n```\n\n"
            "Always guard inputs at the entry point.\n"
        )
        result = distill_pattern({}, body)
        self.assertEqual(result.source, "root-cause-section")
        self.assertEqual(result.pattern_text, "Always guard inputs at the entry point.")

    def test_root_cause_section_skips_table_rows(self):
        """Table rows in ## Root Cause are skipped; prose following them is used."""
        body = (
            "## Root Cause\n\n"
            "| col1 | col2 |\n|------|------|\n\n"
            "Use explicit checks.\n"
        )
        result = distill_pattern({}, body)
        self.assertEqual(result.source, "root-cause-section")
        self.assertEqual(result.pattern_text, "Use explicit checks.")

    def test_root_cause_fm_single_quotes_stripped(self):
        """Single-quoted root-cause values are unquoted before returning."""
        result = distill_pattern({"root-cause": "'Guard inputs.'"}, "")
        self.assertEqual(result.pattern_text, "Guard inputs.")
        self.assertEqual(result.source, "root-cause")

    def test_null_root_cause_falls_through(self):
        """root-cause: null does not produce 'None' as a pattern."""
        result = distill_pattern({"root-cause": None}, "")
        self.assertNotEqual(result.pattern_text, "None")
        # Should fall through to fallback since body is empty
        self.assertEqual(result.source, "fallback")

    def test_null_title_falls_through(self):
        """title: null does not produce 'None' as a pattern."""
        result = distill_pattern({"title": None}, "")
        self.assertNotEqual(result.pattern_text, "None")
        self.assertEqual(result.source, "fallback")
