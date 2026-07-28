"""Tests for cg-update platform tree regeneration wiring.

Verifies that update.ps1 and update.sh contain the generator invocation
that refreshes .claude/, .agents/, and .opencode/ after a git pull, and
that Python resolution is consistent across the plugin.

Run from repo root:
    python3 -m pytest scripts/tests/test_update_generates_targets.py -v
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
DIRECT_PYTHON3_COMMAND = re.compile(r"(?m)^\s*(?:exec\s+|command\s+)?python3\s")


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

    @pytest.mark.parametrize(
        "failure",
        ["generator unavailable", "invalid mapping", "generation validation failure", "Python unavailable"],
    )
    def test_generation_failure_is_blocking(self, content: str, failure: str) -> None:
        assert "throw" in content.lower(), f"{failure} must terminate update.ps1"
        assert "platform trees not regenerated" not in content.lower()
        assert "existing trees remain linked" not in content.lower()

    def test_failure_stops_before_consumer_refresh(self, content: str) -> None:
        generation = content.index("cg_generate_targets.py")
        refresh = content.index("Update-CgManagedPlatformFiles")
        assert "throw" in content[generation:refresh].lower()

    def test_success_still_reports_regenerated_tree(self, content: str) -> None:
        assert "Platform trees regenerated." in content

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

    @pytest.mark.parametrize(
        "failure",
        ["generator unavailable", "invalid mapping", "generation validation failure", "Python unavailable"],
    )
    def test_generation_failure_is_blocking(self, content: str, failure: str) -> None:
        assert 'print_error "Platform tree generation' in content, failure
        assert "existing trees remain linked" not in content.lower()

    def test_failure_stops_before_managed_file_refresh(self, content: str) -> None:
        generation = content.index("cg_generate_targets.py")
        refresh = content.index("managed-files.json")
        assert "exit 1" in content[generation:refresh]

    def test_success_still_reports_regenerated_tree(self, content: str) -> None:
        assert "Platform trees regenerated." in content

    def test_uses_resolved_python_command_for_generator(self, content: str) -> None:
        assert "resolve_python" in content
        assert "PYTHON_CMD" in content
        assert 'python3 "$GENERATOR_SCRIPT"' not in content

    def test_refreshes_manifest_managed_files(self, content: str) -> None:
        assert "managed-files.json" in content
        assert "Refreshed managed platform file" in content


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

    def test_bash_wrappers_resolve_python_candidates(self) -> None:
        for path in [
            REPO_ROOT / "bin/cg-index",
            REPO_ROOT / "bin/cg-token-audit",
            REPO_ROOT / "bin/cg-brain-init",
            REPO_ROOT / "bin/cg-diff-summary",
            REPO_ROOT / "bin/cg-log-summary",
            REPO_ROOT / "bin/cg-problems-summary",
            REPO_ROOT / "bin/cg-test-summary",
            REPO_ROOT / "bin/cg-tree-summary",
        ]:
            content = path.read_text(encoding="utf-8")
            assert "resolve_python" in content, path
            assert "python3 python py" in content, path

    def test_bash_wrappers_do_not_call_python3_directly(self) -> None:
        for path in [
            REPO_ROOT / "bin/cg-index",
            REPO_ROOT / "bin/cg-token-audit",
            REPO_ROOT / "bin/cg-brain-init",
            REPO_ROOT / "bin/cg-diff-summary",
            REPO_ROOT / "bin/cg-log-summary",
            REPO_ROOT / "bin/cg-problems-summary",
            REPO_ROOT / "bin/cg-test-summary",
            REPO_ROOT / "bin/cg-tree-summary",
        ]:
            content = path.read_text(encoding="utf-8")
            assert not DIRECT_PYTHON3_COMMAND.search(content), path

    def test_install_sh_generated_python_wrappers_do_not_call_python3_directly(self) -> None:
        content = (REPO_ROOT / "scripts/install.sh").read_text(encoding="utf-8")
        assert "resolve_python" in content
        assert not DIRECT_PYTHON3_COMMAND.search(content)


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

    def test_generation_failure_halts_before_staging(self, content: str) -> None:
        failure = content.index("If generation fails")
        staging = content.index("### Step 2")
        failure_contract = content[failure:staging].lower()
        assert "halt" in failure_contract
        assert "do not halt" not in failure_contract
        assert "continue to step 2" not in failure_contract

    def test_missing_generator_is_not_treated_as_consumer_repo(self, content: str) -> None:
        assert "If either is missing, skip this step" not in content

    def test_has_generated_targets_file_group(self, content: str) -> None:
        assert "Generated Targets" in content
        assert ".claude/" in content
        assert ".agents/" in content
        assert ".opencode/" in content
