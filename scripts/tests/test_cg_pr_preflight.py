"""Contract tests for the CI-impact preflight and native target runner."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

import cg_pr_preflight as preflight

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_canonical_change_selects_native_and_module_gates() -> None:
    selection = preflight.classify_changed_files([".github/prompts/cg-work.prompt.md"])

    assert selection.native_required is True
    assert selection.module_checks == ("dependencies", "cross-suite", "ownership")
    assert "prompt" in selection.reasons


def test_generated_tree_change_selects_committed_drift_gate() -> None:
    selection = preflight.classify_changed_files([".agents/commands/cg-work.md"])

    assert selection.native_required is True
    assert selection.generated_tree_changed is True
    assert selection.drift_required is True


def test_no_impact_change_does_not_select_native_target() -> None:
    selection = preflight.classify_changed_files(["README.md"])

    assert selection.native_required is False
    assert selection.module_checks == ()
    assert selection.drift_required is False


@pytest.mark.parametrize("path", ["compound-gpid.local.md", ".compound-gpid/active-manifest.json"])
def test_project_selection_changes_are_native_and_module_impacting(path: str) -> None:
    selection = preflight.classify_changed_files([path])

    assert selection.native_required is True
    assert selection.module_checks == ("dependencies", "cross-suite", "ownership")
    assert "project-config" in selection.reasons


def test_base_resolution_prefers_existing_pr_base() -> None:
    assert preflight.resolve_base_branch("release", "feature-base", "main") == "release"
    assert preflight.resolve_base_branch(None, "feature-base", "main") == "feature-base"
    assert preflight.resolve_base_branch(None, None, "main") == "main"


def test_missing_history_is_visible_and_uses_explicit_full_gate_fallback(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(
        preflight,
        "_run_git",
        lambda *args, **kwargs: preflight.GitResult(128, "", "shallow history"),
    )

    result = preflight.derive_changed_files(tmp_path, base="origin/main")

    assert result.selection_error is not None
    assert result.full_gate_fallback is False


def test_zero_before_revision_requests_full_gate_fallback(tmp_path: Path) -> None:
    result = preflight.derive_changed_files(tmp_path, base="0" * 40)

    assert result.full_gate_fallback is True
    assert result.selection_error is None


def test_cache_artifacts_distinguish_tracked_manifest_and_local_noise(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    cache = tmp_path / ".github/skills/cg-skill-test/__pycache__/module.pyc"
    cache.parent.mkdir(parents=True)
    cache.write_bytes(b"bytecode")
    monkeypatch.setattr(preflight, "git_tracked_paths", lambda *args, **kwargs: set())

    report = preflight.inspect_cache_artifacts(tmp_path)

    assert report.fatal is False
    assert report.paths == (".github/skills/cg-skill-test/__pycache__/module.pyc",)


def test_git_tracking_failure_is_fatal_for_cache_provenance(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(
        preflight,
        "_run_git",
        lambda *args, **kwargs: preflight.GitResult(128, "", "not a repository"),
    )

    report = preflight.inspect_cache_artifacts(tmp_path)

    assert report.fatal is True
    assert report.git_error is not None


def test_cache_report_bounds_local_path_samples(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(preflight, "git_tracked_paths", lambda *args, **kwargs: set())
    for index in range(preflight.MAX_CACHE_REPORT_PATHS + 5):
        cache = tmp_path / f"scripts/cache-{index}/__pycache__/module.pyc"
        cache.parent.mkdir(parents=True)
        cache.write_bytes(b"bytecode")

    report = preflight.inspect_cache_artifacts(tmp_path)

    assert report.path_count == preflight.MAX_CACHE_REPORT_PATHS + 5
    assert report.truncated is True
    assert len(report.paths) == preflight.MAX_CACHE_REPORT_PATHS


def test_native_command_contains_ordered_pytest_marker_and_all_module_checks() -> None:
    commands = preflight.native_commands(Path("repo"))
    pytest_command = commands[0]

    assert pytest_command[:4] == (preflight.PYTHON, "-m", "pytest", "scripts/tests/test_target_mapping.py")
    assert "-m" in pytest_command
    assert "not integration" in pytest_command
    assert (preflight.PYTHON, "scripts/cg_validate_modules.py", "--check-dependencies") in commands
    assert (preflight.PYTHON, "scripts/cg_validate_modules.py", "--check-cross-suite") in commands
    assert (preflight.PYTHON, "scripts/cg_validate_modules.py", "--check-ownership") in commands
    assert "scripts/tests/test_project_projection.py" in commands[0]


def test_native_command_never_invokes_pester() -> None:
    commands = preflight.native_commands(Path("repo"))

    assert all("pester" not in " ".join(command).casefold() for command in commands)
    assert all("Run-Tests.ps1" not in " ".join(command) for command in commands)


def test_prepare_defers_head_drift_until_committed_phase() -> None:
    prepare = preflight.build_preflight_result(
        Path("repo"),
        phase="prepare",
        changed_files=[".github/prompts/cg-commit-push-pr.prompt.md"],
    )
    committed = preflight.build_preflight_result(
        Path("repo"),
        phase="committed",
        changed_files=[".github/prompts/cg-commit-push-pr.prompt.md"],
    )

    assert all(
        "test_target_drift.py" not in " ".join(command)
        for command in prepare.selected_commands
    )
    assert any(
        "test_target_drift.py" in " ".join(command)
        for command in committed.selected_commands
    )


def test_full_gate_selection_includes_committed_drift_and_all_module_commands() -> None:
    result = preflight.build_preflight_result(
        Path("repo"), phase="committed", changed_files=(), full_gate=True
    )
    command_text = " ".join(" ".join(command) for command in result.selected_commands)

    assert result.full_gate_fallback is True
    assert "test_target_drift.py" in command_text
    assert all(check in command_text for check in ("check-dependencies", "check-cross-suite", "check-ownership"))


def test_cli_consumes_neutral_and_blocking_kilo_results(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
    monkeypatch.setattr(preflight, "inspect_cache_artifacts", lambda _root: preflight.CacheReport())
    neutral_path = tmp_path / "neutral.json"
    neutral_path.write_text(json.dumps({
        "status": "missing-kilo", "exit_code": 3, "inventory": {},
    }), encoding="utf-8")

    neutral_exit = preflight.main([
        "--root", str(tmp_path), "--changed-file", "README.md",
        "--kilo-result-json", str(neutral_path), "--selection-only", "--format", "json",
    ])
    neutral_output = json.loads(capsys.readouterr().out)
    assert neutral_exit == 0
    assert neutral_output["kilo"]["outcome"] == "generic-not-applicable"

    blocking_path = tmp_path / "blocking.json"
    blocking_path.write_text(json.dumps({
        "status": "local-content-invalid", "exit_code": 2, "inventory": {},
    }), encoding="utf-8")
    blocking_exit = preflight.main([
        "--root", str(tmp_path), "--changed-file", "README.md",
        "--kilo-result-json", str(blocking_path), "--selection-only", "--format", "json",
    ])
    assert blocking_exit == 2


def test_kilo_adapter_preserves_authoritative_status_and_evidence() -> None:
    payload = {
        "status": "missing-kilo",
        "exit_code": 3,
        "message": "No supported Kilo executable was found",
        "remediation": "Install Kilo",
        "kilo_version": None,
        "kilo_executable_sha256": None,
        "certified_launch_required": False,
        "inventory": {"records": []},
    }

    outcome = preflight.adapt_kilo_result(payload)

    assert outcome.outcome == "generic-not-applicable"
    assert outcome.source_status == "missing-kilo"
    assert outcome.exit_code == 3
    assert outcome.inventory == {"records": []}


def test_kilo_adapter_rejects_unknown_status() -> None:
    with pytest.raises(preflight.KiloResultError, match="unknown Kilo status"):
        preflight.adapt_kilo_result({"status": "future-status", "exit_code": 0})


@pytest.mark.parametrize(
    ("status", "expected", "exit_code"),
    [
        ("ok", "certified-ready", 0),
        ("ok-no-coexistence", "generic-not-applicable", 0),
        ("missing-kilo", "generic-not-applicable", 3),
        ("unsupported-kilo-version", "generic-not-applicable", 3),
        ("local-projection-missing", "blocking-configuration", 2),
        ("local-projection-invalid", "blocking-configuration", 2),
        ("local-content-invalid", "blocking-content", 2),
        ("host-command-error", "blocking-configuration", 3),
        ("host-schema-error", "blocking-configuration", 5),
        ("local-inventory-missing", "blocking-content", 5),
        ("containment-unhonored", "blocking-containment", 4),
    ],
)
def test_kilo_adapter_maps_every_authoritative_status(
    status: str, expected: str, exit_code: int
) -> None:
    payload = {"status": status, "exit_code": exit_code, "inventory": {}}
    if status == "ok":
        payload.update({
            "kilo_version": "7.4.21",
            "kilo_executable": "/opt/kilo",
            "kilo_executable_sha256": "a" * 64,
        })
    outcome = preflight.adapt_kilo_result(payload)

    assert outcome.outcome == expected
    assert outcome.source_status == status


def test_kilo_adapter_rejects_malformed_result() -> None:
    with pytest.raises(preflight.KiloResultError, match="exit_code"):
        preflight.adapt_kilo_result({"status": "ok"})
    with pytest.raises(preflight.KiloResultError, match="inventory"):
        preflight.adapt_kilo_result({"status": "ok", "exit_code": 0, "inventory": "invalid"})


def test_json_and_text_results_are_bounded() -> None:
    result = preflight.PreflightResult(
        phase="prepare",
        selection=preflight.classify_changed_files(["scripts/cg_generate_targets.py"]),
        changed_files=("scripts/cg_generate_targets.py",),
    )

    rendered = preflight.render_result(result, "json")
    decoded = json.loads(rendered)
    assert decoded["phase"] == "prepare"
    assert "native_commands" in decoded
    assert "full_output" not in decoded
    assert "prepare" in preflight.render_result(result, "text")


def test_text_result_exposes_bounded_failed_command_output() -> None:
    result = preflight.PreflightResult(
        phase="committed",
        selection=preflight.full_gate_selection(),
        changed_files=(),
        command_results=(
            preflight.CommandResult(
                command=("python", "-m", "pytest"),
                returncode=1,
                stdout="assertion failure",
                stderr="pytest error",
            ),
        ),
    )

    rendered = preflight.render_result(result, "text")

    assert "assertion failure" in rendered
    assert "pytest error" in rendered


def test_workflow_delegates_native_selection_and_preserves_context() -> None:
    workflow = (REPO_ROOT / ".github/workflows/tests.yml").read_text(encoding="utf-8")
    native_start = workflow.index("- name: Run authoritative native target preflight")
    publisher_start = workflow.index("- name: Run generic publisher", native_start)
    native_block = workflow[native_start:publisher_start]

    assert "scripts/cg_pr_preflight.py" in native_block
    assert "python -m pytest" not in native_block
    assert "github.event.pull_request.base.sha" in native_block
    assert "github.event.before" in native_block
    assert "--full-gate" in native_block
    assert "0000000000000000000000000000000000000000" in native_block
    assert "fetch-depth: 0" in workflow
    assert "origin/HEAD" not in native_block
    assert "tests/Run-Tests.ps1" in workflow
    assert "E2E smoke test" in workflow


def test_native_target_owns_deterministic_kilo_and_preflight_tests() -> None:
    assert "scripts/tests/test_kilo_coexistence.py" in preflight.NATIVE_PYTEST_FILES
    assert "scripts/tests/test_kilo_copy.py" in preflight.NATIVE_PYTEST_FILES
    assert "scripts/tests/test_link_projection_order.py" in preflight.NATIVE_PYTEST_FILES
    assert "scripts/tests/test_cg_pr_preflight.py" in preflight.NATIVE_PYTEST_FILES
    assert "scripts/tests/test_project_manifest.py" in preflight.NATIVE_PYTEST_FILES
    assert "scripts/tests/test_project_projection.py" in preflight.NATIVE_PYTEST_FILES
    assert "scripts/tests/test_release_policy.py" in preflight.NATIVE_PYTEST_FILES


def test_workflow_reports_neutral_generic_kilo_capability() -> None:
    workflow = (REPO_ROOT / ".github/workflows/tests.yml").read_text(encoding="utf-8")
    start = workflow.index("kilo-capability-report:")
    end = workflow.index("  native-targets:", start)
    block = workflow[start:end]

    assert "CG_KILO_CERTIFIED_RUNNER" in block
    assert "CG_KILO_CERTIFIED_VERSION" in block
    assert "CG_KILO_CERTIFIED_SHA256" in block
    assert "generic-not-applicable" in block
    assert "real-host integration" in block
    assert "upload-artifact" in block


def test_certified_kilo_job_is_protected_and_hash_pinned() -> None:
    workflow = (REPO_ROOT / ".github/workflows/tests.yml").read_text(encoding="utf-8")
    start = workflow.index("kilo-certified-integration:")
    block = workflow[start:]

    assert "github.event_name == 'push'" in block
    assert "github.event_name == 'workflow_dispatch'" in block
    assert "github.ref == format('refs/heads/{0}', github.event.repository.default_branch)" in block
    assert "github.event_name != 'pull_request'" in block
    assert "vars.CG_KILO_CERTIFIED_RUNNER" in block
    assert "vars.CG_KILO_CERTIFIED_VERSION" in block
    assert "vars.CG_KILO_CERTIFIED_SHA256" in block
    assert "environment: cg-kilo-certified" in block
    assert "ref: ${{ github.event.repository.default_branch }}" in block
    assert "kilo_executable_sha256" in block
    assert "CG_KILO_CERTIFIED_SHA256" in block
    assert "CG_KILO_CERTIFIED_VERSION" in block
    assert "certified-host" in block
    assert "cg-kilo" in block
    assert "CG_KILO_CERTIFIED_EXECUTABLE" in block
    assert "-m pytest scripts/tests/test_kilo_coexistence.py -m integration" in block


def test_generic_e2e_consumes_declared_capability_without_host_probe() -> None:
    workflow = (REPO_ROOT / ".github/workflows/tests.yml").read_text(encoding="utf-8")
    start = workflow.index("# Windows E2E smoke test")
    end = workflow.index("# macOS: pwsh", start)
    block = workflow[start:end]

    assert "needs.kilo-capability-report.outputs.outcome" in workflow
    assert "CG_KILO_CAPABILITY" in block
    assert "generic-not-applicable" in block
    assert "kilo debug skill" not in block
