"""Release gate tests — verify generated trees are current before release.

Run from repo root:
    python3 -m pytest scripts/tests/test_release_gate_targets.py -v
"""
from __future__ import annotations

import subprocess
import sys
import os
import shutil
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


def _write_executable(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")
    path.chmod(0o755)


def _run_release_fixture(
    tmp_path: Path, *, tag_commit: str = "abc123", head_commit: str = "abc123",
    dirty: bool = False, python_exit: int = 1, cwd: Path | None = None,
) -> tuple[subprocess.CompletedProcess[str], Path, Path, Path]:
    if os.name == "nt":
        pytest.skip("POSIX command shims are covered here; Windows release behavior is covered by Pester")
    pwsh = shutil.which("pwsh")
    if pwsh is None:
        pytest.skip("pwsh is required for release-script integration tests")
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    git_log = tmp_path / "git.log"
    python_log = tmp_path / "python.log"
    api_log = tmp_path / "api.log"
    _write_executable(
        bin_dir / "git",
        "#!/bin/sh\n"
        "printf '%s\\n' \"$*\" >> \"$CG_GIT_LOG\"\n"
        "case \"$1 $3\" in\n"
        "  '-C rev-parse') case \"$5\" in HEAD*) printf '%s\\n' \"$CG_HEAD_COMMIT\" ;; *) printf '%s\\n' \"$CG_TAG_COMMIT\" ;; esac ;;\n"
        "  '-C tag') printf '%s\\n' 'v1.2.0.9006' ;;\n"
        "  '-C ls-remote') case \"$4\" in --heads) printf '%s\\t%s\\n' \"$CG_HEAD_COMMIT\" 'refs/heads/dev' ;; --tags) printf '%s\\t%s\\n' \"$CG_TAG_COMMIT\" 'refs/tags/v1.2.0.9006' ;; esac ;;\n"
        "  '-C status') [ \"$CG_DIRTY\" = 1 ] && printf '%s\\n' ' M changed.txt' ;;\n"
        "  'credential fill') printf '%s\\n' 'password=fake-token' ;;\n"
        "esac\nexit 0\n",
    )
    _write_executable(
        bin_dir / "python3",
        "#!/bin/sh\nprintf '%s\\n' \"$*\" >> \"$CG_PYTHON_LOG\"\n"
        "[ \"$1\" = '--version' ] && { printf '%s\\n' 'Python 3.11.0'; exit 0; }\n"
        "exit \"$CG_PYTHON_EXIT\"\n",
    )
    notes = tmp_path / "notes.md"
    notes.write_text("release notes\n", encoding="utf-8")
    script = REPO_ROOT / "create-release.ps1"
    escaped_script = str(script).replace("'", "''")
    escaped_notes = str(notes).replace("'", "''")
    escaped_api_log = str(api_log).replace("'", "''")
    command = (
        "$global:LASTEXITCODE = 0; "
        f"function global:Invoke-RestMethod {{ Add-Content -Path '{escaped_api_log}' -Value 'called'; "
        "return [pscustomobject]@{ id = 1; html_url = 'https://example.invalid' } }; "
        f"& '{escaped_script}' -Tag v1.2.0.9006 -Name 'v1.2.0.9006 - Manifest-driven skill loading, certified contained launcher, and quarantined skill importing' -NotesFile '{escaped_notes}'"
    )
    env = os.environ.copy()
    env.update({
        "PATH": f"{bin_dir}{os.pathsep}{env.get('PATH', '')}",
        "CG_GIT_LOG": str(git_log),
        "CG_PYTHON_LOG": str(python_log),
        "CG_TAG_COMMIT": tag_commit,
        "CG_HEAD_COMMIT": head_commit,
        "CG_DIRTY": "1" if dirty else "0",
        "CG_PYTHON_EXIT": str(python_exit),
    })
    result = subprocess.run(  # pylint: disable=subprocess-run-check
        [pwsh, "-NoProfile", "-Command", command], capture_output=True, text=True,
        cwd=str(cwd or tmp_path), env=env, timeout=30, check=False,
    )
    return result, git_log, python_log, api_log


class TestReleaseGateTargets:
    def test_workflow_has_required_python_gate_on_supported_operating_systems(self) -> None:
        workflow = (REPO_ROOT / ".github/workflows/tests.yml").read_text(encoding="utf-8")
        assert "setup-python" in workflow
        assert "windows-2022" in workflow
        assert "macos-14" in workflow
        assert "cg_pr_preflight.py" in workflow
        assert "--run-native-target" in workflow
        preflight = (REPO_ROOT / "scripts/cg_pr_preflight.py").read_text(encoding="utf-8")
        assert "test_release_policy.py" in preflight

    def test_workflow_runs_publisher_security_and_backend_race_gates(self) -> None:
        workflow = (REPO_ROOT / ".github/workflows/tests.yml").read_text(encoding="utf-8")
        for test_file in (
            "test_secure_fs.py",
            "test_writer.py",
            "test_generic_cli.py",
            "test_generic_parser.py",
            "test_generic_renderer.py",
            "test_generic_launchers.py",
            "test_publishing.py",
            "test_publishing_paths.py",
            "test_publishing_provenance.py",
            "test_publishing_security.py",
        ):
            assert test_file in workflow
        assert "backend_windows" in workflow
        assert "backend_posix" in workflow
        assert "assert_backend_race_gate.py" in workflow
        assert "upload-artifact" in workflow

    def test_create_release_invokes_preflight_before_github_api(self) -> None:
        content = (REPO_ROOT / "create-release.ps1").read_text(encoding="utf-8")
        preflight = content.lower().find("preflight")
        api = content.find("Invoke-RestMethod")
        assert preflight >= 0
        assert preflight < api
        assert "LASTEXITCODE" in content[preflight:api]

    def test_release_rejects_checkout_not_matching_tag_before_preflight(self, tmp_path: Path) -> None:
        result, git_log, python_log, api_log = _run_release_fixture(
            tmp_path, tag_commit="tag-commit", head_commit="head-commit"
        )

        assert result.returncode != 0
        assert "checkout mismatch" in (result.stdout + result.stderr).lower()
        assert git_log.exists()
        assert not python_log.exists()
        assert not api_log.exists()

    def test_release_rejects_dirty_checkout_before_preflight(self, tmp_path: Path) -> None:
        result, _, python_log, api_log = _run_release_fixture(tmp_path, dirty=True)

        assert result.returncode != 0
        assert "must be clean" in (result.stdout + result.stderr).lower()
        assert not python_log.exists()
        assert not api_log.exists()

    def test_failing_preflight_never_reads_credentials_or_calls_api(self, tmp_path: Path) -> None:
        caller = tmp_path / "unrelated-cwd"
        caller.mkdir()
        result, git_log, python_log, api_log = _run_release_fixture(
            tmp_path, python_exit=7, cwd=caller
        )

        assert result.returncode != 0
        assert "preflight failed with exit code 7" in (result.stdout + result.stderr).lower()
        assert "credential fill" not in git_log.read_text(encoding="utf-8")
        assert f"-C {REPO_ROOT}" in git_log.read_text(encoding="utf-8")
        assert not api_log.exists()
        pytest_args = python_log.read_text(encoding="utf-8")
        assert "scripts/cg_pr_preflight.py" in pytest_args
        assert "--phase committed --full-gate --run-native-target" in pytest_args

    def test_release_prompt_requires_gate_before_execute(self) -> None:
        content = (REPO_ROOT / ".github/prompts/cg-release.prompt.md").read_text(encoding="utf-8")
        execute = content.index("### Step 5: Create and publish the durable release source")
        before_execute = content[:execute].lower()
        assert "authoritative complete native preflight" in before_execute
        assert "release gate" in before_execute or "preflight" in before_execute
        assert "halt" in before_execute

    def test_generator_runs_clean_against_repo(self) -> None:
        """Generator must run without error against the real repo."""
        result = subprocess.run(  # pylint: disable=subprocess-run-check
            [sys.executable, str(REPO_ROOT / "scripts/cg_generate_targets.py"), "--root", str(REPO_ROOT), "--all", "--dry-run"],
            capture_output=True, text=True, cwd=str(REPO_ROOT), timeout=60, check=False,
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
        result = subprocess.run(  # pylint: disable=subprocess-run-check
            [sys.executable, "-m", "pytest", "scripts/tests/test_target_drift.py", "-q"],
            capture_output=True, text=True, cwd=str(REPO_ROOT), timeout=600, check=False,
        )
        assert result.returncode == 0, f"Drift test failed — generated trees are stale:\n{result.stdout}\n{result.stderr}"

    def test_all_platform_tests_pass(self) -> None:
        """All per-platform tests must pass at release time."""
        result = subprocess.run(  # pylint: disable=subprocess-run-check
            [sys.executable, "-m", "pytest",
             "scripts/tests/test_target_claude.py",
             "scripts/tests/test_target_codex.py",
             "scripts/tests/test_target_opencode.py",
             "scripts/tests/test_target_kilo.py",
             "scripts/tests/test_target_documentation.py",
             "scripts/tests/test_model_advisory.py",
             "scripts/tests/test_audit_context.py", "-q"],
            capture_output=True, text=True, cwd=str(REPO_ROOT), timeout=60, check=False,
        )
        assert result.returncode == 0, f"Platform tests failed:\n{result.stdout}\n{result.stderr}"
