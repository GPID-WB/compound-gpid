"""Tests for team_brain.curate — CLI curation bot.

Covers: YAML parsing, gh CLI availability check, issue body formatting,
run_curation() dry-run and live paths (mocked subprocess), missing config,
no contradictions (clean exit), and the main() CLI entry point.

Run from repo root:
    python -m pytest scripts/team_brain/tests/test_curate.py -v
"""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
import warnings
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from team_brain.curate import (
    _create_issue,
    _format_issue_body,
    _gh_available,
    _parse_team_brain_yml,
    main,
    run_curation,
)
from team_brain.dedup import ContradictionReport


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_entry(entry_id: str, project: str, pattern: str, topic: str = "Test", **kw) -> dict:
    return {
        "id": entry_id,
        "date": kw.get("date", "2026-01-01"),
        "source-project": project,
        "topic": topic,
        "tags": kw.get("tags", []),
        "pattern": pattern,
        "entry-path": f"entries/{project}/{entry_id}.md",
        "confidence": kw.get("confidence", 1.0),
        "superseded-by": None,
        "root-cause": kw.get("root_cause", ""),
        "title": kw.get("title", ""),
    }


def _make_report(
    entry_a=None,
    entry_b=None,
    classification="contradiction",
    jaccard_score=0.75,
    shared_tags=None,
    recommended_action="supersede entry_a with entry_b",
) -> ContradictionReport:
    if entry_a is None:
        entry_a = _make_entry("a1", "proj-a", "guard validate inputs boundary null")
    if entry_b is None:
        entry_b = _make_entry("b1", "proj-b", "guard validate inputs boundary null")
    return ContradictionReport(
        entry_a=entry_a,
        entry_b=entry_b,
        classification=classification,
        jaccard_score=jaccard_score,
        shared_tags=shared_tags if shared_tags is not None else ["guard"],
        recommended_action=recommended_action,
    )


def _write_valid_config(path: Path, manager: str = "wb384996", auto_supersede: bool = False) -> None:
    path.write_text(
        f'schema-version: "1.0"\n'
        f'manager: "{manager}"\n'
        f'auto-supersede: {"true" if auto_supersede else "false"}\n'
        f'contributors:\n'
        f'  - org: "GPID-WB"\n',
        encoding="utf-8",
    )


def _write_jsonl(patterns_dir: Path, project: str, entries: list) -> None:
    patterns_dir.mkdir(parents=True, exist_ok=True)
    (patterns_dir / f"{project}.jsonl").write_text(
        "\n".join(json.dumps(e) for e in entries) + "\n", encoding="utf-8"
    )


# ---------------------------------------------------------------------------
# _parse_team_brain_yml
# ---------------------------------------------------------------------------


class TestParseTeamBrainYml(unittest.TestCase):
    def test_valid_config(self):
        """Valid TEAM-BRAIN.yml parses manager and auto-supersede."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yml", delete=False, encoding="utf-8"
        ) as f:
            f.write('schema-version: "1.0"\nmanager: "wb384996"\nauto-supersede: false\n')
            tmp = Path(f.name)
        try:
            cfg = _parse_team_brain_yml(tmp)
            self.assertEqual(cfg["manager"], "wb384996")
            self.assertIs(cfg["auto-supersede"], False)
        finally:
            tmp.unlink()

    def test_missing_manager_warns(self):
        """Missing 'manager' field emits UserWarning and sets manager to None."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yml", delete=False, encoding="utf-8"
        ) as f:
            f.write('schema-version: "1.0"\n')
            tmp = Path(f.name)
        try:
            with self.assertWarns(UserWarning):
                cfg = _parse_team_brain_yml(tmp)
            self.assertIsNone(cfg["manager"])
        finally:
            tmp.unlink()

    def test_missing_file_raises(self):
        """Non-existent config file raises FileNotFoundError."""
        with self.assertRaises(FileNotFoundError):
            _parse_team_brain_yml(Path("/nonexistent/TEAM-BRAIN.yml"))

    def test_auto_supersede_true(self):
        """auto-supersede: true parses as boolean True."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yml", delete=False, encoding="utf-8"
        ) as f:
            f.write('manager: "wb384996"\nauto-supersede: true\n')
            tmp = Path(f.name)
        try:
            cfg = _parse_team_brain_yml(tmp)
            self.assertIs(cfg["auto-supersede"], True)
        finally:
            tmp.unlink()


# ---------------------------------------------------------------------------
# _gh_available
# ---------------------------------------------------------------------------


class TestGhAvailable(unittest.TestCase):
    def test_gh_available_when_returncode_zero(self):
        """Returns True when gh --version exits 0."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        with patch("subprocess.run", return_value=mock_result):
            self.assertTrue(_gh_available())

    def test_gh_not_available_when_not_found(self):
        """Returns False when gh is not on PATH (FileNotFoundError)."""
        with patch("subprocess.run", side_effect=FileNotFoundError):
            self.assertFalse(_gh_available())

    def test_gh_not_available_when_nonzero(self):
        """Returns False when gh --version exits non-zero."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        with patch("subprocess.run", return_value=mock_result):
            self.assertFalse(_gh_available())


# ---------------------------------------------------------------------------
# _format_issue_body
# ---------------------------------------------------------------------------


class TestFormatIssueBody(unittest.TestCase):
    def test_contains_entry_ids(self):
        """Issue body contains both entry IDs."""
        report = _make_report()
        body = _format_issue_body(report)
        self.assertIn("a1", body)
        self.assertIn("b1", body)

    def test_contains_patterns(self):
        """Issue body contains both pattern texts."""
        report = _make_report()
        body = _format_issue_body(report)
        self.assertIn("guard validate inputs boundary null", body)

    def test_contains_jaccard_score(self):
        """Issue body contains the Jaccard score."""
        report = _make_report(jaccard_score=0.732)
        body = _format_issue_body(report)
        self.assertIn("0.732", body)

    def test_contains_recommended_action(self):
        """Issue body contains the recommended action."""
        report = _make_report(recommended_action="supersede entry_a with entry_b")
        body = _format_issue_body(report)
        self.assertIn("supersede entry_a with entry_b", body)

    def test_contextual_variant_label(self):
        """Contextual variant classification gets the yellow label."""
        report = _make_report(classification="contextual_variant")
        body = _format_issue_body(report)
        self.assertIn("Contextual variant", body)

    def test_contradiction_label(self):
        """Contradiction classification gets the red label."""
        report = _make_report(classification="contradiction")
        body = _format_issue_body(report)
        self.assertIn("Contradiction", body)

    def test_shared_tags_shown(self):
        """Shared tags are included in the issue body."""
        report = _make_report(shared_tags=["guard", "validation"])
        body = _format_issue_body(report)
        self.assertIn("guard", body)
        self.assertIn("validation", body)

    def test_no_shared_tags(self):
        """Empty shared_tags shows 'none' in the issue body."""
        report = _make_report(shared_tags=[])
        body = _format_issue_body(report)
        self.assertIn("none", body)


# ---------------------------------------------------------------------------
# _create_issue
# ---------------------------------------------------------------------------


class TestCreateIssue(unittest.TestCase):
    def test_returns_true_on_success(self):
        """Returns True when gh issue create exits 0."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        with patch("subprocess.run", return_value=mock_result):
            result = _create_issue("GPID-WB/team-brain", "Title", "Body", "manager")
        self.assertTrue(result)

    def test_returns_false_and_warns_on_failure(self):
        """Returns False and emits UserWarning when gh exits non-zero."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "error: not authenticated"
        with patch("subprocess.run", return_value=mock_result):
            with self.assertWarns(UserWarning):
                result = _create_issue("GPID-WB/team-brain", "Title", "Body", None)
        self.assertFalse(result)

    def test_returns_false_on_file_not_found(self):
        """Returns False (with warning) when gh is not on PATH."""
        with patch("subprocess.run", side_effect=FileNotFoundError):
            with self.assertWarns(UserWarning):
                result = _create_issue("GPID-WB/team-brain", "Title", "Body", "mgr")
        self.assertFalse(result)

    def test_assignee_included_when_provided(self):
        """--assignee flag is passed to gh when assignee is non-None."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        with patch("subprocess.run", return_value=mock_result) as mock_run:
            _create_issue("GPID-WB/team-brain", "Title", "Body", "wb384996")
        cmd = mock_run.call_args[0][0]
        self.assertIn("--assignee", cmd)
        self.assertIn("wb384996", cmd)

    def test_no_assignee_flag_when_none(self):
        """--assignee is omitted when assignee is None."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        with patch("subprocess.run", return_value=mock_result) as mock_run:
            _create_issue("GPID-WB/team-brain", "Title", "Body", None)
        cmd = mock_run.call_args[0][0]
        self.assertNotIn("--assignee", cmd)


# ---------------------------------------------------------------------------
# run_curation
# ---------------------------------------------------------------------------


class TestRunCuration(unittest.TestCase):
    def test_no_contradictions_returns_zero(self):
        """Returns 0 and prints clean message when no contradictions found."""
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            cfg = p / "TEAM-BRAIN.yml"
            _write_valid_config(cfg)
            # Single entry → no pairs possible
            _write_jsonl(p / "patterns", "proj-a", [
                _make_entry("a1", "proj-a", "Guard inputs validate")
            ])
            with patch("team_brain.curate._gh_available", return_value=True):
                code = run_curation(p / "patterns", cfg, "GPID-WB/test-repo")
        self.assertEqual(code, 0)

    def test_missing_config_returns_one(self):
        """Returns 1 when TEAM-BRAIN.yml is not found."""
        with tempfile.TemporaryDirectory() as tmp:
            code = run_curation(
                Path(tmp) / "patterns",
                Path(tmp) / "TEAM-BRAIN.yml",
                "GPID-WB/test-repo",
            )
        self.assertEqual(code, 1)

    def test_dry_run_does_not_call_gh(self):
        """In dry-run mode, no subprocess calls are made."""
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            cfg = p / "TEAM-BRAIN.yml"
            _write_valid_config(cfg)
            # Write two cross-project entries with high Jaccard
            pattern = "Always validate guard inputs boundary system cache null"
            _write_jsonl(p / "patterns", "proj-a", [
                _make_entry("a1", "proj-a", pattern,
                            root_cause="missing guard", title="null check")
            ])
            _write_jsonl(p / "patterns", "proj-b", [
                _make_entry("b1", "proj-b", pattern,
                            root_cause="missing guard", title="null check")
            ])
            with patch("subprocess.run") as mock_run:
                code = run_curation(p / "patterns", cfg, "GPID-WB/test-repo", dry_run=True)
        # No subprocess calls (no gh CLI calls in dry-run mode)
        mock_run.assert_not_called()
        self.assertEqual(code, 0)

    def test_contradiction_found_creates_issue(self):
        """When contradictions are found, gh issue create is called."""
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            cfg = p / "TEAM-BRAIN.yml"
            _write_valid_config(cfg)
            pattern = "Always validate guard inputs boundary system cache null"
            _write_jsonl(p / "patterns", "proj-a", [
                _make_entry("a1", "proj-a", pattern,
                            root_cause="missing guard", title="null check")
            ])
            _write_jsonl(p / "patterns", "proj-b", [
                _make_entry("b1", "proj-b", pattern,
                            root_cause="missing guard", title="null check")
            ])
            mock_result = MagicMock()
            mock_result.returncode = 0
            with patch("team_brain.curate._gh_available", return_value=True), \
                 patch("subprocess.run", return_value=mock_result) as mock_run:
                code = run_curation(p / "patterns", cfg, "GPID-WB/test-repo")
        self.assertEqual(code, 0)
        mock_run.assert_called()
        # Verify it was a gh issue create call
        first_call_cmd = mock_run.call_args_list[0][0][0]
        self.assertIn("gh", first_call_cmd)
        self.assertIn("issue", first_call_cmd)
        self.assertIn("create", first_call_cmd)

    def test_gh_not_available_returns_one(self):
        """Returns 1 when gh CLI is not installed (non-dry-run)."""
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            cfg = p / "TEAM-BRAIN.yml"
            _write_valid_config(cfg)
            with patch("team_brain.curate._gh_available", return_value=False):
                code = run_curation(p / "patterns", cfg, "GPID-WB/test-repo")
        self.assertEqual(code, 1)

    def test_issue_creation_failure_returns_two(self):
        """Partial failure (issue create fails) returns exit code 2."""
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            cfg = p / "TEAM-BRAIN.yml"
            _write_valid_config(cfg)
            pattern = "Always validate guard inputs boundary system cache null"
            _write_jsonl(p / "patterns", "proj-a", [
                _make_entry("a1", "proj-a", pattern,
                            root_cause="missing guard", title="null check")
            ])
            _write_jsonl(p / "patterns", "proj-b", [
                _make_entry("b1", "proj-b", pattern,
                            root_cause="missing guard", title="null check")
            ])
            mock_result = MagicMock()
            mock_result.returncode = 1
            mock_result.stderr = "error: not authenticated"
            with patch("team_brain.curate._gh_available", return_value=True), \
                 patch("subprocess.run", return_value=mock_result):
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    code = run_curation(p / "patterns", cfg, "GPID-WB/test-repo")
        self.assertEqual(code, 2)

    def test_auto_supersede_enabled_warns(self):
        """auto-supersede: true emits a UserWarning for high-Jaccard pairs."""
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            cfg = p / "TEAM-BRAIN.yml"
            _write_valid_config(cfg, auto_supersede=True)
            pattern = "Always validate guard inputs boundary system cache null"
            _write_jsonl(p / "patterns", "proj-a", [
                _make_entry("a1", "proj-a", pattern,
                            root_cause="missing guard", title="null check")
            ])
            _write_jsonl(p / "patterns", "proj-b", [
                _make_entry("b1", "proj-b", pattern,
                            root_cause="missing guard", title="null check")
            ])
            mock_result = MagicMock()
            mock_result.returncode = 0
            with patch("team_brain.curate._gh_available", return_value=True), \
                 patch("subprocess.run", return_value=mock_result):
                with self.assertWarns(UserWarning):
                    run_curation(p / "patterns", cfg, "GPID-WB/test-repo")


# ---------------------------------------------------------------------------
# main() CLI entry point
# ---------------------------------------------------------------------------


class TestMain(unittest.TestCase):
    def test_help_does_not_crash(self):
        """--help exits with code 0 (argparse SystemExit)."""
        with self.assertRaises(SystemExit) as cm:
            main(["--help", "--repo", "GPID-WB/test"])
        self.assertEqual(cm.exception.code, 0)

    def test_missing_repo_exits_nonzero(self):
        """Missing --repo argument exits with non-zero (argparse error)."""
        with self.assertRaises(SystemExit) as cm:
            main([])
        self.assertNotEqual(cm.exception.code, 0)

    def test_dry_run_flag_forwarded(self):
        """--dry-run flag is forwarded to run_curation."""
        with patch("team_brain.curate.run_curation", return_value=0) as mock_fn:
            main([
                "--repo", "GPID-WB/test",
                "--dry-run",
                "--config", "/nonexistent.yml",
            ])
        mock_fn.assert_called_once()
        _kw = mock_fn.call_args[1]
        self.assertTrue(_kw.get("dry_run") or mock_fn.call_args[0][3])
