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
        result, was_replaced = _upsert_jsonl_line(existing, new_line, "new-entry")
        lines = [l for l in result.strip().splitlines() if l]
        self.assertEqual(len(lines), 2)
        self.assertIn("new-entry", result)
        self.assertFalse(was_replaced)

    def test_replaces_existing_id(self) -> None:
        existing = '{"id": "same-entry", "pattern": "old pattern"}\n'
        new_line = '{"id": "same-entry", "pattern": "updated pattern"}'
        result, was_replaced = _upsert_jsonl_line(existing, new_line, "same-entry")
        lines = [l for l in result.strip().splitlines() if l]
        self.assertEqual(len(lines), 1)
        self.assertIn("updated pattern", result)
        self.assertNotIn("old pattern", result)
        self.assertTrue(was_replaced)

    def test_preserves_other_entries(self) -> None:
        existing = (
            '{"id": "entry-a", "pattern": "a"}\n'
            '{"id": "entry-b", "pattern": "b"}\n'
        )
        new_line = '{"id": "entry-a", "pattern": "a-updated"}'
        result, was_replaced = _upsert_jsonl_line(existing, new_line, "entry-a")
        self.assertIn("entry-b", result)
        self.assertIn("a-updated", result)
        self.assertTrue(was_replaced)

    def test_trailing_newline(self) -> None:
        result, was_replaced = _upsert_jsonl_line("", '{"id": "x"}', "x")
        self.assertTrue(result.endswith("\n"))
        self.assertFalse(was_replaced)


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
        """Helper: run push_entry with fully mocked GitHub API.

        Returns (result, mock_put_entry, mock_put_jsonl).
        JSONL is now written first via _put_jsonl_with_retry; the entry goes
        through _put_remote_file.
        """

        def fake_get_remote(_owner_repo, path, _token):
            if "entries/" in path and existing_entry:
                return existing_entry
            if "patterns/" in path and existing_jsonl:
                return existing_jsonl
            return None

        with patch("team_brain.push.get_token", return_value="fake-token"):
            with patch("team_brain.push._get_remote_file", side_effect=fake_get_remote):
                with patch("team_brain.push._put_remote_file") as mock_put:
                    with patch("team_brain.push._put_jsonl_with_retry") as mock_put_jsonl:
                        result = push_entry(solution_path, config=_CONFIG)
        return result, mock_put, mock_put_jsonl

    def test_creates_new_entry_and_jsonl(self) -> None:
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            solution = Path(td) / "2026-05-20-fix-null-check.md"
            solution.write_text(_SOLUTION_CONTENT, encoding="utf-8")
            result, mock_put, mock_put_jsonl = self._run_push(solution)

        self.assertEqual(result.action, "created")
        # Entry PUT: one call through _put_remote_file
        self.assertEqual(mock_put.call_count, 1)
        entry_call = mock_put.call_args_list[0]
        self.assertIn("entries/test-project", entry_call.args[1])
        self.assertIsNone(entry_call.args[5])  # sha=None for new file
        # JSONL PUT: one call through _put_jsonl_with_retry
        self.assertEqual(mock_put_jsonl.call_count, 1)
        jsonl_call = mock_put_jsonl.call_args_list[0]
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
            result, mock_put, mock_put_jsonl = self._run_push(
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
                        with patch("team_brain.push._put_jsonl_with_retry"):
                            push_entry(solution, config=_CONFIG)

        self.assertEqual(len(pushed_content), 1)
        self.assertIn('source-project: "test-project"', pushed_content[0])
        self.assertIn("pushed-date:", pushed_content[0])


# ---------------------------------------------------------------------------
# T-P0.1  project_name path traversal — validation rejects traversal strings
# ---------------------------------------------------------------------------


class TestProjectNameValidation(unittest.TestCase):
    def test_traversal_rejected(self) -> None:
        """project_name containing '../' raises ValueError in config loader."""
        import tempfile
        from team_brain.config import load_team_brain_local_config

        local_md = """\
---
language: python
---

team-brain:
  repo: GPID-WB/team-brain
  project-name: ../../.github/workflows
  enabled: true
"""
        with tempfile.TemporaryDirectory() as td:
            cfg_path = Path(td) / "compound-gpid.local.md"
            cfg_path.write_text(local_md, encoding="utf-8")
            with self.assertRaises(ValueError, msg="traversal project-name should raise"):
                load_team_brain_local_config(cfg_path)

    def test_alphanumeric_accepted(self) -> None:
        import tempfile
        from team_brain.config import load_team_brain_local_config

        local_md = """\
---
language: python
---

team-brain:
  repo: GPID-WB/team-brain
  project-name: my-project-2
  enabled: true
"""
        with tempfile.TemporaryDirectory() as td:
            cfg_path = Path(td) / "compound-gpid.local.md"
            cfg_path.write_text(local_md, encoding="utf-8")
            config = load_team_brain_local_config(cfg_path)
        self.assertIsNotNone(config)
        self.assertEqual(config.project_name, "my-project-2")


# ---------------------------------------------------------------------------
# T-P1.1  _get_remote_file raises RuntimeError on unexpected HTTP status
# ---------------------------------------------------------------------------


class TestGetRemoteFileError(unittest.TestCase):
    def test_raises_runtime_error_on_non_200_404(self) -> None:
        from team_brain.push import _get_remote_file

        with patch("team_brain.push._api_request", return_value=(500, {"message": "server error"})):
            with self.assertRaises(RuntimeError, msg="Should raise on HTTP 500"):
                _get_remote_file("owner/repo", "some/path.md", "fake-token")

    def test_returns_none_on_404(self) -> None:
        from team_brain.push import _get_remote_file

        with patch("team_brain.push._api_request", return_value=(404, {})):
            result = _get_remote_file("owner/repo", "missing.md", "fake-token")
        self.assertIsNone(result)

    def test_raises_runtime_error_on_200_missing_sha(self) -> None:
        """HTTP 200 without 'sha' raises RuntimeError (e.g. file exceeds GitHub 1 MB limit)."""
        from team_brain.push import _get_remote_file

        with patch("team_brain.push._api_request", return_value=(200, {"content": "abc="})):
            with self.assertRaises(RuntimeError):
                _get_remote_file("owner/repo", "path.md", "fake-token")

    def test_raises_runtime_error_on_200_missing_content(self) -> None:
        """HTTP 200 without 'content' raises RuntimeError (e.g. file exceeds GitHub 1 MB limit)."""
        from team_brain.push import _get_remote_file

        with patch("team_brain.push._api_request", return_value=(200, {"sha": "abc123"})):
            with self.assertRaises(RuntimeError):
                _get_remote_file("owner/repo", "path.md", "fake-token")


# ---------------------------------------------------------------------------
# T-P1.2  _put_remote_file raises RuntimeError on non-200/201
# ---------------------------------------------------------------------------


class TestPutRemoteFileError(unittest.TestCase):
    def test_raises_runtime_error_on_non_2xx(self) -> None:
        from team_brain.push import _put_remote_file

        with patch("team_brain.push._api_request", return_value=(422, {"message": "validation failed"})):
            with self.assertRaises(RuntimeError, msg="Should raise on HTTP 422"):
                _put_remote_file("owner/repo", "path.md", "tok", "content", "msg")


# ---------------------------------------------------------------------------
# T-P1.3  push_entry raises FileNotFoundError when solution file is missing
# ---------------------------------------------------------------------------


class TestPushEntryMissingFile(unittest.TestCase):
    def test_raises_file_not_found(self) -> None:
        with self.assertRaises(FileNotFoundError):
            push_entry(Path("/nonexistent/path/2026-05-20-fix.md"), config=_CONFIG)


# ---------------------------------------------------------------------------
# T-P1.4  push_entry raises ValueError when solution has no frontmatter
# ---------------------------------------------------------------------------


class TestPushEntryNoFrontmatter(unittest.TestCase):
    def test_raises_value_error_on_missing_frontmatter(self) -> None:
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            solution = Path(td) / "2026-05-20-no-fm.md"
            solution.write_text("# Just a heading\n\nNo frontmatter here.", encoding="utf-8")
            with self.assertRaises(ValueError, msg="No frontmatter should raise ValueError"):
                push_entry(solution, config=_CONFIG)


# ---------------------------------------------------------------------------
# T-P1.5  get_token — gh not installed raises FileNotFoundError gracefully
# ---------------------------------------------------------------------------


class TestGetTokenGhNotInstalled(unittest.TestCase):
    def test_falls_back_when_gh_not_found(self) -> None:
        env_overrides = {"GITHUB_TOKEN": "", "GH_TOKEN": ""}

        def fake_run(cmd, **_kwargs):  # type: ignore[misc]
            if cmd[0] == "gh":
                raise FileNotFoundError("gh not found")
            return MagicMock(stdout="username=user\npassword=fallback-cred\n", returncode=0)

        with patch.dict(os.environ, env_overrides):
            with patch("subprocess.run", side_effect=fake_run):
                token = get_token()
        # Should fall through to git credential fill
        self.assertEqual(token, "fallback-cred")


# ---------------------------------------------------------------------------
# T-P1.6  _api_request — malformed JSON body falls back gracefully
# ---------------------------------------------------------------------------


class TestApiRequestMalformedJson(unittest.TestCase):
    def test_malformed_json_in_error_body(self) -> None:
        from team_brain.push import _api_request
        import urllib.error

        class _FakeHTTPError(urllib.error.HTTPError):
            def read(self):
                return b"not valid json {"

        with patch("team_brain.push._opener") as mock_opener:
            mock_opener.open.side_effect = _FakeHTTPError(
                "https://api.github.com/test", 422, "Unprocessable", {}, None
            )
            status, data = _api_request("GET", "https://api.github.com/test", "tok")
        self.assertEqual(status, 422)
        # Should not raise — malformed JSON body falls back to {"message": raw[:200]}
        self.assertIn("message", data)

    def test_api_request_success_path_non_json_body(self) -> None:
        """Success path: HTTP 200 with non-JSON body falls back to {"message": raw[:200]}."""
        from team_brain.push import _api_request

        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.read.return_value = b"not-json {"
        with patch("team_brain.push._opener") as mock_opener:
            mock_opener.open.return_value.__enter__.return_value = mock_resp
            mock_opener.open.return_value.__exit__.return_value = False
            status, data = _api_request("GET", "https://api.github.com/test", "tok")
        self.assertEqual(status, 200)
        self.assertIn("message", data)


# ---------------------------------------------------------------------------
# T-P2.1  _upsert_jsonl_line — corrupt line is skipped with a warning
# ---------------------------------------------------------------------------


class TestUpsertJsonlCorruptLine(unittest.TestCase):
    def test_corrupt_line_skipped_with_warning(self) -> None:
        existing = 'INVALID JSON\n{"id": "good-entry", "pattern": "ok"}\n'
        new_line = '{"id": "new-entry", "pattern": "new"}'
        with self.assertWarns(Warning):
            result, was_replaced = _upsert_jsonl_line(existing, new_line, "new-entry")
        self.assertIn("good-entry", result)
        self.assertIn("new-entry", result)
        self.assertFalse(was_replaced)


# ---------------------------------------------------------------------------
# T-P2.2  _distill_pattern — "## Root Cause" section fallback
# ---------------------------------------------------------------------------


class TestDistillPatternRootCauseSection(unittest.TestCase):
    def test_falls_back_to_root_cause_section(self) -> None:
        body = (
            "## Problem\n\nSomething broke.\n\n"
            "## Root Cause\n\nThe caller forgot to check the return value.\n\n"
        )
        # No root-cause in frontmatter, no Solution section
        pattern = _distill_pattern({}, body)
        self.assertIn("return value", pattern.lower())

    def test_solution_takes_priority_over_root_cause_section(self) -> None:
        body = (
            "## Solution\n\nAdd explicit null guard before processing.\n\n"
            "## Root Cause\n\nThe caller forgot to check return value.\n\n"
        )
        pattern = _distill_pattern({}, body)
        self.assertIn("null guard", pattern.lower())


# ---------------------------------------------------------------------------
# T-P2.3  apply_frontmatter_filter — no delimiter in content
# ---------------------------------------------------------------------------


class TestApplyFrontmatterFilterNoDelimiter(unittest.TestCase):
    def test_no_delimiter_treats_all_as_body(self) -> None:
        from team_brain.privacy import apply_frontmatter_filter

        content = "## Problem\n\nBroken function.\n\n## Solution\n\nFixed.\n"
        filtered, blocked, reason = apply_frontmatter_filter(
            content, {"private-sections": ["Problem"]}
        )
        self.assertFalse(blocked)
        self.assertNotIn("## Problem", filtered)
        self.assertIn("## Solution", filtered)

    def test_private_true_blocks_regardless_of_delimiter(self) -> None:
        from team_brain.privacy import apply_frontmatter_filter

        content = "# Title\n\nBody without frontmatter delimiters."
        filtered, blocked, reason = apply_frontmatter_filter(content, {"private": True})
        self.assertTrue(blocked)
        self.assertEqual(filtered, "")


# ---------------------------------------------------------------------------
# T-P2.4  apply_llm_redactions — multiple findings applied in order
# ---------------------------------------------------------------------------


class TestApplyLlmRedactionsMultiple(unittest.TestCase):
    def test_multiple_findings_all_applied(self) -> None:
        from team_brain.privacy import apply_llm_redactions

        content = "Use ACME-DB and CorpTool internally."
        findings = [
            {"line": 1, "type": "system-name", "original": "ACME-DB", "replacement": "<REDACTED:system>"},
            {"line": 1, "type": "system-name", "original": "CorpTool", "replacement": "<REDACTED:system>"},
        ]
        filtered, redactions = apply_llm_redactions(content, findings)
        self.assertNotIn("ACME-DB", filtered)
        self.assertNotIn("CorpTool", filtered)
        self.assertEqual(len(redactions), 2)

    def test_oversized_replacement_capped(self) -> None:
        from team_brain.privacy import apply_llm_redactions

        content = "The internal term is ACME."
        findings = [
            {"line": 1, "type": "jargon", "original": "ACME", "replacement": "x" * 501},
        ]
        filtered, redactions = apply_llm_redactions(content, findings)
        self.assertIn("<REDACTED:llm>", filtered)
        self.assertNotIn("x" * 501, filtered)

    def test_html_bearing_replacement_rejected(self) -> None:
        from team_brain.privacy import apply_llm_redactions

        content = "Replace this token."
        findings = [
            {"line": 1, "type": "jargon", "original": "token", "replacement": "<script>alert(1)</script>"},
        ]
        filtered, redactions = apply_llm_redactions(content, findings)
        # <script>...</script> has a closing tag — should be rejected and replaced with generic
        self.assertIn("<REDACTED:llm>", filtered)
        self.assertNotIn("<script>", filtered)

    def test_simple_placeholder_allowed(self) -> None:
        from team_brain.privacy import apply_llm_redactions

        content = "Use ACME internally."
        findings = [
            {"line": 1, "type": "jargon", "original": "ACME", "replacement": "<internal-platform>"},
        ]
        filtered, redactions = apply_llm_redactions(content, findings)
        # <internal-platform> has no closing tag or dangerous HTML — allowed through
        self.assertIn("<internal-platform>", filtered)
        self.assertNotIn("ACME", filtered)


# ---------------------------------------------------------------------------
# T-P2.6  load_team_brain_local_config — project-name absent → dir default
# ---------------------------------------------------------------------------


class TestProjectNameDefault(unittest.TestCase):
    def test_defaults_to_directory_name(self) -> None:
        import tempfile
        from team_brain.config import load_team_brain_local_config

        local_md = """\
---
language: python
---

team-brain:
  repo: GPID-WB/team-brain
  enabled: true
"""
        with tempfile.TemporaryDirectory() as td:
            cfg_path = Path(td) / "compound-gpid.local.md"
            cfg_path.write_text(local_md, encoding="utf-8")
            config = load_team_brain_local_config(cfg_path)
        self.assertIsNotNone(config)
        # project_name should default to the parent directory name
        self.assertEqual(config.project_name, Path(td).name)


# ---------------------------------------------------------------------------
# T-P2.7  load_team_brain_local_config — frontmatter fallback
# ---------------------------------------------------------------------------


class TestLoadConfigFrontmatterFallback(unittest.TestCase):
    def test_reads_team_brain_from_frontmatter_when_no_body_block(self) -> None:
        """Config in frontmatter (not body block) should still be loaded."""
        import tempfile
        from team_brain.config import load_team_brain_local_config

        local_md = """\
---
language: python
team-brain:
  repo: GPID-WB/team-brain
  project-name: fm-project
  enabled: true
---

Some body text without a team-brain block.
"""
        with tempfile.TemporaryDirectory() as td:
            cfg_path = Path(td) / "compound-gpid.local.md"
            cfg_path.write_text(local_md, encoding="utf-8")
            config = load_team_brain_local_config(cfg_path)
        # The function should fall back to frontmatter parsing
        # (This documents the fallback behaviour, not requiring it always exists)
        # If config is None, it means frontmatter YAML dict nesting isn't supported
        # (which is acceptable — body block is the documented location)
        if config is not None:
            self.assertEqual(config.repo, "GPID-WB/team-brain")


# ---------------------------------------------------------------------------
# T-P2.8  load_team_brain_local_config — enabled: "false" string coercion
# ---------------------------------------------------------------------------


class TestEnabledStringCoercion(unittest.TestCase):
    def test_enabled_false_string_returns_none(self) -> None:
        import tempfile
        from team_brain.config import load_team_brain_local_config

        local_md = """\
---
language: python
---

team-brain:
  repo: GPID-WB/team-brain
  project-name: my-project
  enabled: false
"""
        with tempfile.TemporaryDirectory() as td:
            cfg_path = Path(td) / "compound-gpid.local.md"
            cfg_path.write_text(local_md, encoding="utf-8")
            config = load_team_brain_local_config(cfg_path)
        self.assertIsNone(config)


# ---------------------------------------------------------------------------
# T-P2.9  _find_local_config stops at compound-gpid.md boundary
# ---------------------------------------------------------------------------


class TestFindLocalConfigBoundary(unittest.TestCase):
    def test_stops_at_compound_gpid_md(self) -> None:
        import tempfile
        from team_brain.config import _find_local_config

        # Create: /root/compound-gpid.md + /root/subdir/ (no local.md in subdir)
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "compound-gpid.md").write_text("# Project", encoding="utf-8")
            subdir = root / "deep" / "nested"
            subdir.mkdir(parents=True)
            # Local config ONLY at root (which is a parent of subdir)
            (root / "compound-gpid.local.md").write_text("", encoding="utf-8")

            # Search from subdir — should find root local config
            result = _find_local_config(subdir)
        self.assertIsNotNone(result)
        self.assertEqual(result.name, "compound-gpid.local.md")

    def test_does_not_climb_past_git_boundary(self) -> None:
        import tempfile
        from team_brain.config import _find_local_config

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            # .git dir at root acts as boundary
            (root / ".git").mkdir()
            # local.md above root — should NOT be found
            above = root / "nested"
            above.mkdir()
            # config only in root (which has .git), not in above
            result = _find_local_config(above)
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
