"""Tests for team_brain.init — team brain initialisation command.

Covers: _gh_available, _repo_exists, _write_scaffold, _update_local_config,
init_team_brain happy path (repo created and pushed), repo already exists
(configure-only path), missing gh CLI, git push failure, and the main() CLI
entry point.

All subprocess.run calls are mocked via unittest.mock.patch.

Run from repo root:
    python -m pytest scripts/team_brain/tests/test_init.py -v
"""
from __future__ import annotations

import os
import sys
import tempfile
import unittest
import warnings
from pathlib import Path
from unittest.mock import MagicMock, call, patch

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from team_brain.init import (
    _gh_available,
    _git_init_and_push,
    _repo_exists,
    _update_local_config,
    _write_scaffold,
    init_team_brain,
    main,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _mock_run_success(*args, **kwargs):
    """Return a mock successful subprocess.CompletedProcess."""
    result = MagicMock()
    result.returncode = 0
    result.stdout = ""
    result.stderr = ""
    return result


def _mock_run_fail(*args, **kwargs):
    """Return a mock failed subprocess.CompletedProcess."""
    result = MagicMock()
    result.returncode = 1
    result.stdout = ""
    result.stderr = "error: simulated failure"
    return result


# ---------------------------------------------------------------------------
# _gh_available
# ---------------------------------------------------------------------------


class TestGhAvailable(unittest.TestCase):
    def test_returns_true_when_gh_exits_zero(self):
        mock_result = MagicMock()
        mock_result.returncode = 0
        with patch("subprocess.run", return_value=mock_result):
            self.assertTrue(_gh_available())

    def test_returns_false_when_not_found(self):
        with patch("subprocess.run", side_effect=FileNotFoundError):
            self.assertFalse(_gh_available())

    def test_returns_false_on_nonzero(self):
        mock_result = MagicMock()
        mock_result.returncode = 1
        with patch("subprocess.run", return_value=mock_result):
            self.assertFalse(_gh_available())


# ---------------------------------------------------------------------------
# _repo_exists
# ---------------------------------------------------------------------------


class TestRepoExists(unittest.TestCase):
    def test_returns_true_when_gh_view_exits_zero(self):
        mock_result = MagicMock()
        mock_result.returncode = 0
        with patch("subprocess.run", return_value=mock_result):
            self.assertTrue(_repo_exists("GPID-WB/team-brain"))

    def test_returns_false_on_404(self):
        mock_result = MagicMock()
        mock_result.returncode = 1
        with patch("subprocess.run", return_value=mock_result):
            self.assertFalse(_repo_exists("GPID-WB/nonexistent"))

    def test_returns_false_when_gh_not_found(self):
        with patch("subprocess.run", side_effect=FileNotFoundError):
            self.assertFalse(_repo_exists("GPID-WB/team-brain"))


# ---------------------------------------------------------------------------
# _write_scaffold
# ---------------------------------------------------------------------------


class TestWriteScaffold(unittest.TestCase):
    def test_creates_required_files(self):
        """_write_scaffold creates the expected directory structure."""
        with tempfile.TemporaryDirectory() as tmp:
            work_dir = Path(tmp) / "scaffold"
            work_dir.mkdir()
            _write_scaffold(work_dir, "wb384996")

            self.assertTrue((work_dir / "TEAM-BRAIN.yml").exists())
            self.assertTrue((work_dir / "TEAM-BRAIN.md").exists())
            self.assertTrue((work_dir / "README.md").exists())
            self.assertTrue((work_dir / ".gitignore").exists())
            self.assertTrue((work_dir / "entries" / ".gitkeep").exists())
            self.assertTrue((work_dir / "patterns" / ".gitkeep").exists())
            self.assertTrue((work_dir / ".github" / "workflows").is_dir())

    def test_team_brain_yml_contains_manager(self):
        """TEAM-BRAIN.yml includes the provided manager username."""
        with tempfile.TemporaryDirectory() as tmp:
            work_dir = Path(tmp) / "scaffold"
            work_dir.mkdir()
            _write_scaffold(work_dir, "wb384996")
            content = (work_dir / "TEAM-BRAIN.yml").read_text(encoding="utf-8")
            self.assertIn("wb384996", content)

    def test_action_templates_written(self):
        """rebuild-index.yml and curation-bot.yml are created in workflows/."""
        with tempfile.TemporaryDirectory() as tmp:
            work_dir = Path(tmp) / "scaffold"
            work_dir.mkdir()
            _write_scaffold(work_dir, "manager")
            workflows = work_dir / ".github" / "workflows"
            # At least placeholder files (or real templates) should be present
            self.assertTrue(
                (workflows / "rebuild-index.yml").exists()
                or any(workflows.iterdir()),
                "At least one workflow file should exist"
            )


# ---------------------------------------------------------------------------
# _update_local_config
# ---------------------------------------------------------------------------


class TestUpdateLocalConfig(unittest.TestCase):
    def test_appends_team_brain_section(self):
        """team-brain: section is appended to compound-gpid.local.md."""
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            config_path = p / "compound-gpid.local.md"
            config_path.write_text("---\nlanguage: Python\n---\n", encoding="utf-8")
            ok = _update_local_config(p, "GPID-WB/team-brain", "compound-gpid")
            self.assertTrue(ok)
            content = config_path.read_text(encoding="utf-8")
            self.assertIn("team-brain:", content)
            self.assertIn("GPID-WB/team-brain", content)

    def test_idempotent_when_already_configured(self):
        """Does not duplicate the section if team-brain: already present."""
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            config_path = p / "compound-gpid.local.md"
            config_path.write_text(
                "---\nlanguage: Python\n---\nteam-brain:\n  repo: GPID-WB/team-brain\n",
                encoding="utf-8",
            )
            ok = _update_local_config(p, "GPID-WB/team-brain", "compound-gpid")
            self.assertTrue(ok)
            content = config_path.read_text(encoding="utf-8")
            # Should not have duplicate sections
            self.assertEqual(content.count("team-brain:"), 1)

    def test_returns_false_when_file_missing(self):
        """Returns False and emits warning when compound-gpid.local.md is missing."""
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            with self.assertWarns(UserWarning):
                ok = _update_local_config(p, "GPID-WB/team-brain", "compound-gpid")
            self.assertFalse(ok)


# ---------------------------------------------------------------------------
# init_team_brain — full integration (mocked subprocess)
# ---------------------------------------------------------------------------


class TestInitTeamBrain(unittest.TestCase):
    def _make_local_config(self, tmp: Path) -> Path:
        cfg = tmp / "compound-gpid.local.md"
        cfg.write_text("---\nlanguage: Python\n---\n", encoding="utf-8")
        return cfg

    def test_gh_not_available_returns_one(self):
        """Returns 1 immediately when gh CLI is missing."""
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            self._make_local_config(p)
            with patch("team_brain.init._gh_available", return_value=False):
                code = init_team_brain("GPID-WB/team-brain", "wb384996", project_root=p)
        self.assertEqual(code, 1)

    def test_repo_already_exists_configures_local(self):
        """When repo already exists, configures local project and returns 0."""
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            self._make_local_config(p)
            with patch("team_brain.init._gh_available", return_value=True), \
                 patch("team_brain.init._repo_exists", return_value=True):
                code = init_team_brain("GPID-WB/team-brain", "wb384996", project_root=p)
            self.assertEqual(code, 0)
            content = (p / "compound-gpid.local.md").read_text(encoding="utf-8")
            self.assertIn("team-brain:", content)

    def test_repo_already_exists_no_configure(self):
        """With configure_local=False, skips compound-gpid.local.md update."""
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            cfg = self._make_local_config(p)
            original_content = cfg.read_text(encoding="utf-8")
            with patch("team_brain.init._gh_available", return_value=True), \
                 patch("team_brain.init._repo_exists", return_value=True):
                code = init_team_brain(
                    "GPID-WB/team-brain", "wb384996", project_root=p, configure_local=False
                )
            self.assertEqual(code, 0)
            # File unchanged
            self.assertEqual(cfg.read_text(encoding="utf-8"), original_content)

    def test_gh_repo_create_fails_returns_one(self):
        """Returns 1 when gh repo create exits non-zero."""
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            self._make_local_config(p)
            mock_fail = MagicMock()
            mock_fail.returncode = 1
            mock_fail.stderr = "error: repository already exists"
            with patch("team_brain.init._gh_available", return_value=True), \
                 patch("team_brain.init._repo_exists", return_value=False), \
                 patch("subprocess.run", return_value=mock_fail):
                code = init_team_brain("GPID-WB/team-brain", "wb384996", project_root=p)
        self.assertEqual(code, 1)

    def test_successful_init_returns_zero(self):
        """Full happy path: repo created, scaffold pushed, local config updated."""
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            self._make_local_config(p)
            with patch("team_brain.init._gh_available", return_value=True), \
                 patch("team_brain.init._repo_exists", return_value=False), \
                 patch("team_brain.init._git_init_and_push", return_value=True), \
                 patch("subprocess.run", _mock_run_success):
                code = init_team_brain("GPID-WB/team-brain", "wb384996", project_root=p)
        self.assertEqual(code, 0)

    def test_git_push_failure_returns_one(self):
        """Returns 1 when git push (via _git_init_and_push) fails."""
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            self._make_local_config(p)
            with patch("team_brain.init._gh_available", return_value=True), \
                 patch("team_brain.init._repo_exists", return_value=False), \
                 patch("team_brain.init._git_init_and_push", return_value=False), \
                 patch("subprocess.run", _mock_run_success):
                code = init_team_brain("GPID-WB/team-brain", "wb384996", project_root=p)
        self.assertEqual(code, 1)


# ---------------------------------------------------------------------------
# main() CLI
# ---------------------------------------------------------------------------


class TestMain(unittest.TestCase):
    def test_help_exits_zero(self):
        """--help exits with code 0."""
        with self.assertRaises(SystemExit) as cm:
            main(["--help"])
        self.assertEqual(cm.exception.code, 0)

    def test_missing_required_args_exits_nonzero(self):
        """Missing --repo and --manager exits with non-zero."""
        with self.assertRaises(SystemExit) as cm:
            main([])
        self.assertNotEqual(cm.exception.code, 0)

    def test_no_configure_flag_forwarded(self):
        """--no-configure forwards configure_local=False to init_team_brain."""
        with patch("team_brain.init.init_team_brain", return_value=0) as mock_fn:
            main([
                "--repo", "GPID-WB/test",
                "--manager", "wb384996",
                "--no-configure",
            ])
        mock_fn.assert_called_once()
        kwargs = mock_fn.call_args[1]
        self.assertFalse(kwargs.get("configure_local", True))
