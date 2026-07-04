"""Tests for cg-update platform tree regeneration wiring.

Verifies that update.ps1 and update.sh contain the generator invocation
that refreshes .claude/, .agents/, and .opencode/ after a git pull, and
that Python resolution is consistent across the plugin.

Run from repo root:
    python3 -m pytest scripts/tests/test_update_generates_targets.py -v
"""
from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


class TestUpdatePs1RegeneratesTargets:
    @pytest.fixture
    def content(self) -> str:
        return (REPO_ROOT / "scripts/update.ps1").read_text(encoding="utf-8")

    def test_checks_for_target_mapping_json(self, content: str) -> None:
        assert "target-mapping.json" in content

    def test_checks_for_generator_script(self, content: str) -> None:
        assert "cg_generate_targets.py" in content

    def test_calls_generator_with_all_flag(self, content: str) -> None:
        assert "--all" in content

    def test_warns_on_generation_failure(self, content: str) -> None:
        assert "Platform tree generation" in content

    def test_does_not_halt_on_failure(self, content: str) -> None:
        assert "Write-Warning" in content

    def test_uses_resolve_python_command_not_bare_python3(self, content: str) -> None:
        assert "Resolve-PythonCommand" in content
        assert "python3 $generatorScript" not in content


class TestUpdateShRegeneratesTargets:
    @pytest.fixture
    def content(self) -> str:
        return (REPO_ROOT / "scripts/update.sh").read_text(encoding="utf-8")

    def test_checks_for_target_mapping_json(self, content: str) -> None:
        assert "target-mapping.json" in content

    def test_checks_for_generator_script(self, content: str) -> None:
        assert "cg_generate_targets.py" in content

    def test_calls_generator_with_all_flag(self, content: str) -> None:
        assert "--all" in content

    def test_warns_on_generation_failure(self, content: str) -> None:
        assert "Platform tree generation failed" in content


class TestResolvePythonCommandConsistency:
    """Verify Resolve-PythonCommand is present in helpers.ps1 and matches
    the install.ps1 / bin/*.cmd detection pattern (python3 -> python -> py
    with Windows Store stub rejection)."""

    def test_helpers_ps1_has_resolve_python_command(self) -> None:
        content = (REPO_ROOT / "scripts/helpers.ps1").read_text(encoding="utf-8")
        assert "function Resolve-PythonCommand" in content

    def test_probes_python3_python_py_in_order(self) -> None:
        content = (REPO_ROOT / "scripts/helpers.ps1").read_text(encoding="utf-8")
        assert "python3" in content
        assert '"python"' in content
        assert '"py"' in content

    def test_rejects_windows_store_stubs(self) -> None:
        content = (REPO_ROOT / "scripts/helpers.ps1").read_text(encoding="utf-8")
        assert "^Python\\s+\\d" in content

    def test_update_ps1_uses_resolve_python_command(self) -> None:
        content = (REPO_ROOT / "scripts/update.ps1").read_text(encoding="utf-8")
        assert "Resolve-PythonCommand" in content

    def test_no_bare_python3_in_update_ps1_generator_call(self) -> None:
        content = (REPO_ROOT / "scripts/update.ps1").read_text(encoding="utf-8")
        assert "python3 $generatorScript" not in content


class TestCommitPushPrRegeneratesTargets:
    @pytest.fixture
    def content(self) -> str:
        return (REPO_ROOT / ".github/prompts/cg-commit-push-pr.prompt.md").read_text(encoding="utf-8")

    def test_has_step_1_5_for_regeneration(self, content: str) -> None:
        assert "Step 1.5" in content
        assert "Regenerate Platform Trees" in content

    def test_checks_for_target_mapping_and_generator(self, content: str) -> None:
        assert "target-mapping.json" in content
        assert "cg_generate_targets.py" in content

    def test_checks_github_diff_before_regenerating(self, content: str) -> None:
        assert "git diff HEAD" in content
        assert ".github/" in content

    def test_warns_on_failure_does_not_halt(self, content: str) -> None:
        assert "Do not halt" in content

    def test_has_generated_targets_file_group(self, content: str) -> None:
        assert "Generated Targets" in content
        assert ".claude/" in content
        assert ".agents/" in content
        assert ".opencode/" in content
