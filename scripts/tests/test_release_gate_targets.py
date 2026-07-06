"""Release gate tests — verify generated trees are current before release.

Run from repo root:
    python3 -m pytest scripts/tests/test_release_gate_targets.py -v
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


class TestReleaseGateTargets:
    def test_generator_runs_clean_against_repo(self) -> None:
        """Generator must run without error against the real repo."""
        result = subprocess.run(
            [sys.executable, str(REPO_ROOT / "scripts/cg_generate_targets.py"), "--root", str(REPO_ROOT), "--all", "--dry-run"],
            capture_output=True, text=True, cwd=str(REPO_ROOT), timeout=60,
        )
        assert result.returncode == 0, f"Generator failed: {result.stderr}"

    def test_target_mapping_validates(self) -> None:
        """target-mapping.json must validate at release time."""
        import cg_generate_targets as gen
        import json
        data = json.loads((REPO_ROOT / ".github/shared/target-mapping.json").read_text())
        errors = gen.validate_target_mapping(data)
        assert errors == [], f"Validation errors: {errors}"

    def test_drift_test_would_pass(self) -> None:
        """Drift check must pass — generated trees must be current."""
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "scripts/tests/test_target_drift.py", "-q"],
            capture_output=True, text=True, cwd=str(REPO_ROOT), timeout=60,
        )
        assert result.returncode == 0, f"Drift test failed — generated trees are stale:\n{result.stdout}\n{result.stderr}"

    def test_all_platform_tests_pass(self) -> None:
        """All per-platform tests must pass at release time."""
        result = subprocess.run(
            [sys.executable, "-m", "pytest",
             "scripts/tests/test_target_claude.py",
             "scripts/tests/test_target_codex.py",
             "scripts/tests/test_target_opencode.py", "-q"],
            capture_output=True, text=True, cwd=str(REPO_ROOT), timeout=60,
        )
        assert result.returncode == 0, f"Platform tests failed:\n{result.stdout}\n{result.stderr}"
