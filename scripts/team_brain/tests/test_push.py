"""Tests for team_brain.push.

Covers: token resolution, frontmatter parsing, pattern distillation,
JSONL upsert, dry-run mode, blocked entries, skipped config, and
live-mode API interactions (mocked via unittest.mock).
"""
from __future__ import annotations

import os
import unittest
from pathlib import Path
from typing import Dict
from unittest.mock import MagicMock, patch

# Ensure the scripts/ directory is importable from the test runner
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from team_brain.config import TeamBrainLocalConfig
from team_brain.push import (
    _distill_pattern,
    _parse_frontmatter,
    _upsert_jsonl_line,
    get_token,
    push_entry,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_VALID_FRONTMATTER = """\
---
date: 2026-05-20
title: "Fix missing null check"
category: bugs
language: Python
tags: [null, validation, guard]
root-cause: "Value was read before checking for None."
severity: P1
---
"""

_BODY = """\
## Problem

Function crashed when receiving None input.

## Root Cause

The caller did not guard against None values.

## Solution

Added an explicit `if value is None: raise ValueError(...)` guard at the
entry point before passing to the inner function.

## Prevention

Always validate inputs at system boundaries.
"""

_SOLUTION_CONTENT = _VALID_FRONTMATTER + _BODY

_CONFIG = TeamBrainLocalConfig(
    repo="GPID-WB/team-brain",
    project_name="test-project",
    enabled=True,
    llm_filter=False,
)


def _make_solution_file(tmp_path: Path, content: str = _SOLUTION_CONTENT) -> Path:
    f = tmp_path / "2026-05-20-fix-null-check.md"
    f.write_text(content, encoding="utf-8")
    return f


# ---------------------------------------------------------------------------
# Token resolution
# ---------------------------------------------------------------------------


class TestGetToken(unittest.TestCase):
    def test_explicit_token_returned_directly(self) -> None:
        token = get_token("my-explicit-token")
        self.assertEqual(token, "my-explicit-token")

    def test_github_token_env_var(self) -> None:
        with patch.dict(os.environ, {"GITHUB_TOKEN": "env-token", "GH_TOKEN": ""}):
            token = get_token()
        self.assertEqual(token, "env-token")

    def test_gh_token_env_var_fallback(self) -> None:
        with patch.dict(os.environ, {"GITHUB_TOKEN": "", "GH_TOKEN": "gh-token"}):
            token = get_token()
        self.assertEqual(token, "gh-token")

    def test_no_token_returns_none(self) -> None:
        env_overrides = {"GITHUB_TOKEN": "", "GH_TOKEN": ""}

        def fake_run(cmd, **_kwargs):  # type: ignore[misc]  # mock must accept subprocess kwargs
            if cmd[0] == "gh":
                return MagicMock(stdout="", returncode=1)  # gh not authenticated
            return MagicMock(stdout="username=user\n", returncode=0)  # no password line

        with patch.dict(os.environ, env_overrides):
            with patch("subprocess.run", side_effect=fake_run):
                token = get_token()
        self.assertIsNone(token)

    def test_git_credential_fill_fallback(self) -> None:
        env_overrides = {"GITHUB_TOKEN": "", "GH_TOKEN": ""}

        def fake_run(cmd, **_kwargs):  # type: ignore[misc]  # mock must accept subprocess kwargs
            if cmd[0] == "gh":
                return MagicMock(stdout="", returncode=1)  # gh not available
            return MagicMock(stdout="username=user\npassword=cred-token\n", returncode=0)

        with patch.dict(os.environ, env_overrides):
            with patch("subprocess.run", side_effect=fake_run):
                token = get_token()
        self.assertEqual(token, "cred-token")

    def test_gh_cli_auth_token_fallback(self) -> None:
        env_overrides = {"GITHUB_TOKEN": "", "GH_TOKEN": ""}

        def fake_run(cmd, **_kwargs):  # type: ignore[misc]  # mock must accept subprocess kwargs
            if cmd[0] == "gh":
                return MagicMock(stdout="gh-cli-token\n", returncode=0)
            return MagicMock(stdout="", returncode=0)

        with patch.dict(os.environ, env_overrides):
            with patch("subprocess.run", side_effect=fake_run):
                token = get_token()
        self.assertEqual(token, "gh-cli-token")


# ---------------------------------------------------------------------------
# Frontmatter parsing
# ---------------------------------------------------------------------------


class TestParseFrontmatter(unittest.TestCase):
    def test_parses_standard_solution_file(self) -> None:
        fm, body = _parse_frontmatter(_SOLUTION_CONTENT)
        self.assertEqual(fm["date"], "2026-05-20")
        self.assertEqual(fm["title"], "Fix missing null check")
        self.assertEqual(fm["category"], "bugs")
        self.assertEqual(fm["tags"], ["null", "validation", "guard"])
        self.assertEqual(fm["root-cause"], "Value was read before checking for None.")
        self.assertIn("## Problem", body)

    def test_returns_empty_dict_if_no_frontmatter(self) -> None:
        fm, body = _parse_frontmatter("# Just a heading\n\nNo frontmatter here.")
        self.assertEqual(fm, {})
        self.assertIn("# Just a heading", body)

    def test_handles_unquoted_boolean(self) -> None:
        content = "---\nprivate: true\nenabled: false\n---\n"
        fm, _ = _parse_frontmatter(content)
        self.assertIs(fm["private"], True)
        self.assertIs(fm["enabled"], False)

    def test_strips_inline_comments(self) -> None:
        content = "---\ndate: 2026-05-20 # comment\n---\n"
        fm, _ = _parse_frontmatter(content)
        self.assertEqual(fm["date"], "2026-05-20")


# ---------------------------------------------------------------------------
# Pattern distillation
# ---------------------------------------------------------------------------


class TestDistillPattern(unittest.TestCase):
    def test_prefers_root_cause_frontmatter(self) -> None:
        fm = {"root-cause": "Value was None before check.", "title": "Other title"}
        pattern = _distill_pattern(fm, _BODY)
        self.assertEqual(pattern, "Value was None before check.")

    def test_falls_back_to_solution_section(self) -> None:
        fm = {"title": "My Fix"}
        pattern = _distill_pattern(fm, _BODY)
        # Should pick first substantive sentence from ## Solution (contains "guard")
        self.assertIn("guard", pattern.lower())

    def test_falls_back_to_title(self) -> None:
        fm = {"title": "My Fix"}
        body_no_sections = "## Problem\nSomething broke.\n"
        pattern = _distill_pattern(fm, body_no_sections)
        self.assertEqual(pattern, "My Fix")

    def test_truncates_at_200_chars(self) -> None:
        long_root_cause = "x" * 300
        fm = {"root-cause": long_root_cause}
        pattern = _distill_pattern(fm, "")
        self.assertEqual(len(pattern), 200)

    def test_returns_fallback_when_nothing_available(self) -> None:
        pattern = _distill_pattern({}, "")
        self.assertEqual(pattern, "(no pattern)")

    def test_skips_code_blocks_in_section(self) -> None:
        fm = {}
        body = "## Solution\n\n```python\nx = None\n```\n\nUse explicit guard.\n"
        pattern = _distill_pattern(fm, body)
        self.assertNotIn("```", pattern)


# ---------------------------------------------------------------------------
# JSONL upsert
# ---------------------------------------------------------------------------


class TestUpsertJsonlLine(unittest.TestCase):
    def test_appends_when_id_not_present(self) -> None:
        existing = '{"id": "old-entry", "pattern": "old"}\n'
        new_line = '{"id": "new-entry", "pattern": "new"}'
        result = _upsert_jsonl_line(existing, new_line, "new-entry")
        lines = [l for l in result.strip().splitlines() if l]
        self.assertEqual(len(lines), 2)
        self.assertIn("new-entry", result)

    def test_replaces_existing_id(self) -> None:
        existing = '{"id": "same-entry", "pattern": "old pattern"}\n'
        new_line = '{"id": "same-entry", "pattern": "updated pattern"}'
        result = _upsert_jsonl_line(existing, new_line, "same-entry")
        lines = [l for l in result.strip().splitlines() if l]
        self.assertEqual(len(lines), 1)
        self.assertIn("updated pattern", result)
        self.assertNotIn("old pattern", result)

    def test_preserves_other_entries(self) -> None:
        existing = (
            '{"id": "entry-a", "pattern": "a"}\n'
            '{"id": "entry-b", "pattern": "b"}\n'
        )
        new_line = '{"id": "entry-a", "pattern": "a-updated"}'
        result = _upsert_jsonl_line(existing, new_line, "entry-a")
        self.assertIn("entry-b", result)
        self.assertIn("a-updated", result)

    def test_trailing_newline(self) -> None:
        result = _upsert_jsonl_line("", '{"id": "x"}', "x")
        self.assertTrue(result.endswith("\n"))


# ---------------------------------------------------------------------------
# push_entry — skipped and blocked cases
# ---------------------------------------------------------------------------


class TestPushEntrySkipped(unittest.TestCase):
    def test_skipped_when_config_is_none(self) -> None:
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            solution = Path(td) / "2026-05-20-fix.md"
            solution.write_text(_SOLUTION_CONTENT, encoding="utf-8")
            # Pass a non-existent local_config_path so load returns None
            result = push_entry(
                solution,
                config=None,
                local_config_path=Path(td) / "nonexistent.md",
            )
        self.assertEqual(result.action, "skipped")
        self.assertIn("not configured", result.summary)

    def test_skipped_when_enabled_false(self) -> None:
        import tempfile
        disabled_config = TeamBrainLocalConfig(
            repo="GPID-WB/team-brain",
            project_name="test-project",
            enabled=False,
        )
        with tempfile.TemporaryDirectory() as td:
            solution = Path(td) / "2026-05-20-fix.md"
            solution.write_text(_SOLUTION_CONTENT, encoding="utf-8")
            result = push_entry(solution, config=disabled_config)
        self.assertEqual(result.action, "skipped")


class TestPushEntryBlocked(unittest.TestCase):
    def test_blocked_when_private_true_in_frontmatter(self) -> None:
        import tempfile
        private_content = (
            "---\n"
            "date: 2026-05-20\n"
            "title: Private entry\n"
            "category: bugs\n"
            "language: Python\n"
            "tags: [secret]\n"
            "root-cause: Internal issue\n"
            "severity: P1\n"
            "private: true\n"
            "---\n"
            "## Problem\nInternal details.\n"
        )
        with tempfile.TemporaryDirectory() as td:
            solution = Path(td) / "2026-05-20-private.md"
            solution.write_text(private_content, encoding="utf-8")
            result = push_entry(solution, config=_CONFIG, dry_run=True)
        # Privacy filter should block this
        self.assertEqual(result.action, "blocked")


# ---------------------------------------------------------------------------
# push_entry — dry-run mode
# ---------------------------------------------------------------------------


class TestPushEntryDryRun(unittest.TestCase):
    def test_dry_run_returns_dry_run_action(self) -> None:
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            solution = Path(td) / "2026-05-20-fix-null-check.md"
            solution.write_text(_SOLUTION_CONTENT, encoding="utf-8")
            result = push_entry(solution, config=_CONFIG, dry_run=True)
        self.assertEqual(result.action, "dry-run")
        self.assertIn("entries/test-project/2026-05-20-fix-null-check.md", result.entry_path)
        self.assertIn("patterns/test-project.jsonl", result.jsonl_path)
        self.assertIn("[dry-run]", result.summary)

    def test_dry_run_makes_no_api_calls(self) -> None:
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            solution = Path(td) / "2026-05-20-fix.md"
            solution.write_text(_SOLUTION_CONTENT, encoding="utf-8")
            with patch("team_brain.push._api_request") as mock_api:
                push_entry(solution, config=_CONFIG, dry_run=True)
        mock_api.assert_not_called()


# ---------------------------------------------------------------------------
# push_entry — live mode (mocked API)
# ---------------------------------------------------------------------------


def _make_api_response(status: int, body: Dict) -> tuple:
    return (status, body)


class TestPushEntryLive(unittest.TestCase):
    """Tests with GitHub API calls mocked via patch."""

    def _run_push(self, solution_path: Path, *, existing_entry=None, existing_jsonl=None):
        """Helper: run push_entry with fully mocked GitHub API."""

        def fake_get_remote(_owner_repo, path, _token):
            if "entries/" in path and existing_entry:
                return existing_entry
            if "patterns/" in path and existing_jsonl:
                return existing_jsonl
            return None

        with patch("team_brain.push.get_token", return_value="fake-token"):
            with patch("team_brain.push._get_remote_file", side_effect=fake_get_remote):
                with patch("team_brain.push._put_remote_file") as mock_put:
                    result = push_entry(solution_path, config=_CONFIG)
        return result, mock_put

    def test_creates_new_entry_and_jsonl(self) -> None:
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            solution = Path(td) / "2026-05-20-fix-null-check.md"
            solution.write_text(_SOLUTION_CONTENT, encoding="utf-8")
            result, mock_put = self._run_push(solution)

        self.assertEqual(result.action, "created")
        self.assertEqual(mock_put.call_count, 2)
        # Entry created — sha (6th positional arg) should be None for a new file
        entry_call = mock_put.call_args_list[0]
        self.assertIn("entries/test-project", entry_call.args[1])
        self.assertIsNone(entry_call.args[5])  # sha=None for new file
        # JSONL initialized
        jsonl_call = mock_put.call_args_list[1]
        self.assertIn("patterns/test-project.jsonl", jsonl_call.args[1])

    def test_updates_existing_entry(self) -> None:
        import tempfile
        existing_sha = "abc123"
        existing_entry = (existing_sha, _SOLUTION_CONTENT)
        existing_jsonl_content = (
            '{"id": "2026-05-20-fix-null-check", "pattern": "old"}\n'
        )
        existing_jsonl = ("def456", existing_jsonl_content)

        with tempfile.TemporaryDirectory() as td:
            solution = Path(td) / "2026-05-20-fix-null-check.md"
            solution.write_text(_SOLUTION_CONTENT, encoding="utf-8")
            result, mock_put = self._run_push(
                solution,
                existing_entry=existing_entry,
                existing_jsonl=existing_jsonl,
            )

        self.assertEqual(result.action, "updated")
        # Entry SHA passed as 6th positional arg for update
        entry_call = mock_put.call_args_list[0]
        self.assertEqual(entry_call.args[5], existing_sha)

    def test_raises_when_no_token_in_live_mode(self) -> None:
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            solution = Path(td) / "2026-05-20-fix.md"
            solution.write_text(_SOLUTION_CONTENT, encoding="utf-8")
            with patch("team_brain.push.get_token", return_value=None):
                with self.assertRaises(ValueError, msg="No GitHub token found"):
                    push_entry(solution, config=_CONFIG)

    def test_entry_contains_source_project_field(self) -> None:
        """The pushed markdown content must include source-project in frontmatter."""
        import tempfile
        pushed_content = []

        def capture_put(_owner_repo, path, _token, content, _message, _sha=None):
            if "entries/" in path:
                pushed_content.append(content)

        with tempfile.TemporaryDirectory() as td:
            solution = Path(td) / "2026-05-20-fix-null-check.md"
            solution.write_text(_SOLUTION_CONTENT, encoding="utf-8")
            with patch("team_brain.push.get_token", return_value="fake-token"):
                with patch("team_brain.push._get_remote_file", return_value=None):
                    with patch("team_brain.push._put_remote_file", side_effect=capture_put):
                        push_entry(solution, config=_CONFIG)

        self.assertEqual(len(pushed_content), 1)
        self.assertIn('source-project: "test-project"', pushed_content[0])
        self.assertIn("pushed-date:", pushed_content[0])


if __name__ == "__main__":
    unittest.main()
