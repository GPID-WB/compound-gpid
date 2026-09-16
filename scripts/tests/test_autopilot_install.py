"""Installed helper launchers, identity and explicit consumer root (Phase 5, Step 13).

Covers the wrapper-relative Windows/POSIX launchers with version-verified
Python detection and Windows Store-stub rejection, the parity rule across all
Python-resolving ``bin/*.cmd`` launchers, the explicit validated consumer
``--root`` contract (no working-directory change, no installed source test
selection), and the installed helper identity: bounded helper version,
contract digest, and an allowlisted code-path layout with no hardlink
aliases.

Run: python -B -m pytest scripts/tests/test_autopilot_install.py -q
"""
from __future__ import annotations

import os
import re
from pathlib import Path

import cg_autopilot
from autopilot.arguments import parse_invocation
from autopilot.install import (
    CODE_PATH_PREFIXES,
    resolve_install_root,
    validate_installed_layout,
)
from tests.autopilot_plan_fixture import plan_source_valid

REPO_ROOT = Path(__file__).resolve().parents[2]


# ---------------------------------------------------------------------------
# Windows launcher pattern
# ---------------------------------------------------------------------------


class TestWindowsLauncher:
    def _cmd(self) -> str:
        return (REPO_ROOT / "bin" / "cg-autopilot-control.cmd").read_text(
            encoding="utf-8"
        )

    def test_launcher_exists_in_committed_bin(self) -> None:
        assert (REPO_ROOT / "bin" / "cg-autopilot-control.cmd").is_file()

    def test_every_python_probe_has_where_precheck(self) -> None:
        content = self._cmd()
        assert "where python3 >nul 2>&1" in content
        assert "where python >nul 2>&1" in content
        assert "where py >nul 2>&1" in content

    def test_version_verification_rejects_store_stubs(self) -> None:
        content = self._cmd()
        assert "for /f" in content
        assert content.count('findstr /i "^Python [0-9]"') == 3
        assert "sys.version_info >= (3, 8)" in content

    def test_calls_python_and_propagates_exit_code(self) -> None:
        content = self._cmd()
        assert "call %PYTHON_CMD% " in content
        assert "exit /b %ERRORLEVEL%" in content

    def test_resolves_entrypoint_wrapper_relative(self) -> None:
        content = self._cmd()
        assert "%~dp0..\\scripts\\cg_autopilot.py" in content

    def test_never_changes_consumer_working_directory(self) -> None:
        content = self._cmd().lower()
        assert "cd /d" not in content
        assert "pushd" not in content
        assert "chdir" not in content


# ---------------------------------------------------------------------------
# POSIX launcher pattern
# ---------------------------------------------------------------------------


class TestPosixLauncher:
    def _sh(self) -> str:
        return (REPO_ROOT / "bin" / "cg-autopilot-control").read_text(
            encoding="utf-8"
        )

    def test_posix_launcher_exists_in_committed_bin(self) -> None:
        assert (REPO_ROOT / "bin" / "cg-autopilot-control").is_file()

    def test_resolves_python_with_version_verification(self) -> None:
        content = self._sh()
        assert "resolve_python" in content
        assert "Python\\ [0-9]" in content
        assert "sys.version_info >= (3, 8)" in content

    def test_execs_entrypoint_wrapper_relative(self) -> None:
        content = self._sh()
        assert 'exec "$PYTHON_CMD" "$SCRIPT_DIR/../scripts/cg_autopilot.py" "$@"' in content


# ---------------------------------------------------------------------------
# Parity rule: every Python-resolving bin/*.cmd follows the same pattern
# ---------------------------------------------------------------------------


class TestLauncherParity:
    def _python_cmds(self):
        for path in sorted((REPO_ROOT / "bin").glob("*.cmd")):
            content = path.read_text(encoding="utf-8")
            if "for /f" in content:
                yield path.name, content

    def test_every_python_cmd_uses_where_guard_and_store_stub_check(self) -> None:
        stub_check = re.compile(r'findstr /i(?: /R /C:)? *"\^Python \[0-9\]"')
        problems = []
        for name, content in self._python_cmds():
            for candidate in ("python3", "python", "py"):
                if f"where {candidate} >nul" not in content:
                    problems.append(f"{name}: missing where guard for {candidate}")
            if not stub_check.search(content):
                problems.append(f"{name}: missing Store-stub version check")
            if "exit /b %ERRORLEVEL%" not in content:
                problems.append(f"{name}: exit code not propagated")
            if "sys.version_info >= (3, 8)" not in content:
                problems.append(f"{name}: missing Python 3.8+ version gate")
        assert problems == []

    def test_every_python_cmd_resolves_entrypoint_wrapper_relative(self) -> None:
        problems = [
            f"{name}: entrypoint is not wrapper-relative"
            for name, content in self._python_cmds()
            if "%~dp0..\\scripts\\" not in content
        ]
        assert problems == []


# ---------------------------------------------------------------------------
# Explicit validated consumer root
# ---------------------------------------------------------------------------


class TestExplicitConsumerRoot:
    def test_helper_requires_explicit_root_flag(self) -> None:
        assert cg_autopilot.main(["inspect"]) == 1

    def test_root_flag_must_name_an_existing_directory(self) -> None:
        missing = REPO_ROOT / "does-not-exist-helper-root"
        assert cg_autopilot.main(["inspect", "--root", str(missing)]) == 1

    def test_entrypoint_never_changes_working_directory(self) -> None:
        source = (REPO_ROOT / "scripts" / "cg_autopilot.py").read_text(encoding="utf-8")
        assert "os.chdir" not in source
        assert "chdir(" not in source

    def test_helper_never_selects_installed_source_test_inventory(self) -> None:
        entrypoint = (REPO_ROOT / "scripts" / "cg_autopilot.py").read_text(encoding="utf-8")
        install = (REPO_ROOT / "scripts" / "autopilot" / "install.py").read_text(
            encoding="utf-8"
        )
        for source in (entrypoint, install):
            assert "cg_pr_preflight" not in source
            assert "NATIVE_PYTEST" not in source
            assert "scripts/tests" not in source


# ---------------------------------------------------------------------------
# Installed helper identity
# ---------------------------------------------------------------------------


def _fake_install(tmp_path: Path) -> Path:
    root = tmp_path / "install"
    (root / "scripts" / "autopilot").mkdir(parents=True)
    (root / "scripts" / "artifact_views").mkdir(parents=True)
    (root / ".github" / "shared").mkdir(parents=True)
    (root / "bin").mkdir()
    for rel, content in (
        ("SCHEMA_VERSION", "1.0.0"),
        ("scripts/cg_autopilot.py", "pass\n"),
        ("scripts/autopilot/__init__.py", "pass\n"),
        ("scripts/secure_fs.py", "pass\n"),
        (".github/shared/autopilot-stage.contract.md", "# contract\n"),
        ("bin/cg-autopilot-control.cmd", "@echo off\n"),
    ):
        (root / rel).write_text(content, encoding="utf-8")
    return root


class TestInstalledIdentity:
    def test_resolve_install_root_is_repo_root(self) -> None:
        assert resolve_install_root() == REPO_ROOT

    def test_source_checkout_layout_validates_without_problems(self) -> None:
        result = validate_installed_layout()
        assert result["problems"] == []
        assert result["helper-version"]
        assert len(result["contract-digest"]) == 64
        assert len(result["entrypoint-digest"]) == 64
        assert result["launchers"]

    def test_missing_launchers_reported(self, tmp_path: Path) -> None:
        root = _fake_install(tmp_path)
        (root / "bin" / "cg-autopilot-control.cmd").unlink()
        result = validate_installed_layout(root)
        assert any("launcher" in problem for problem in result["problems"])
        assert result["helper-version"] == "1.0.0"

    def test_missing_contract_reported(self, tmp_path: Path) -> None:
        root = _fake_install(tmp_path)
        (root / ".github" / "shared" / "autopilot-stage.contract.md").unlink()
        result = validate_installed_layout(root)
        assert any("contract-missing" in problem for problem in result["problems"])

    def test_missing_entrypoint_reported(self, tmp_path: Path) -> None:
        root = _fake_install(tmp_path)
        (root / "scripts" / "cg_autopilot.py").unlink()
        result = validate_installed_layout(root)
        assert any("entrypoint-missing" in problem for problem in result["problems"])

    def test_hardlinked_entrypoint_is_rejected(self, tmp_path: Path) -> None:
        root = _fake_install(tmp_path)
        entrypoint = root / "scripts" / "cg_autopilot.py"
        try:
            os.link(str(entrypoint), str(root / "alias.py"))
        except (OSError, NotImplementedError):
            import pytest
            pytest.skip("hard links unavailable on this host")
        result = validate_installed_layout(root)
        assert any("entrypoint-unsafe" in problem for problem in result["problems"])

    def test_invalid_or_oversized_version_reported(self, tmp_path: Path) -> None:
        root = _fake_install(tmp_path)
        (root / "SCHEMA_VERSION").write_text("line one\nline two\n", encoding="utf-8")
        result = validate_installed_layout(root)
        assert any("helper-version-invalid" in problem for problem in result["problems"])

    def test_code_path_prefixes_are_contained_under_scripts(self) -> None:
        assert CODE_PATH_PREFIXES
        for prefix in CODE_PATH_PREFIXES:
            assert ".." not in prefix
            assert prefix.startswith("scripts/")

    def test_code_path_directories_must_be_real_directories(self, tmp_path: Path) -> None:
        import shutil
        root = _fake_install(tmp_path)
        shutil.rmtree(root / "scripts" / "autopilot")
        (root / "scripts" / "autopilot").write_text("not a dir", encoding="utf-8")
        result = validate_installed_layout(root)
        assert any("package" in problem and "unsafe" in problem for problem in result["problems"])


# ---------------------------------------------------------------------------
# Inspect integration
# ---------------------------------------------------------------------------


class TestInspectReportsInstalledIdentity:
    def test_run_inspect_includes_helper_identity(self, tmp_path: Path) -> None:
        root = tmp_path / "consumer"
        plan_rel = ".cg-docs/plans/test.md"
        plan_path = root / plan_rel
        plan_path.parent.mkdir(parents=True)
        plan_path.write_text(plan_source_valid(), encoding="utf-8")
        invocation = parse_invocation(
            ["--plan", plan_rel, "--batches", "1", "--base", "origin/dev"]
        )
        report = cg_autopilot.run_inspect(root, invocation)
        helper = report["installed-helper"]
        assert helper["install-root"]
        assert "helper-version" in helper
        assert "contract-digest" in helper
        assert "entrypoint-digest" in helper
        assert "launchers" in helper
        # The helper identity comes from the real source checkout layout.
        assert helper["problems"] == []
