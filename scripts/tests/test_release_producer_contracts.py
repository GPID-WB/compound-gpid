"""Ordinary producer selection, dependency binding and exact historical bytes."""

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import cg_pr_preflight as preflight


def test_pinned_wheel_installs_own_resources_without_cache_aliases():
    files = [
        *(ROOT / "packages/cg-release/templates").glob("*.yml"),
        *(ROOT / ".github/workflows").glob("release-controller*.yml"),
    ]
    installs = [
        line
        for file in files
        for line in file.read_text().splitlines()
        if "uv pip install" in line
    ]
    assert installs
    assert all("--link-mode copy" in line for line in installs)


def test_ordinary_producers_include_reader_and_security_suites():
    assert (
        "scripts/tests/test_release_version_readers.py" in preflight.NATIVE_PYTEST_FILES
    )
    assert (
        "scripts/tests/test_legacy_pages_security.py" in preflight.NATIVE_PYTEST_FILES
    )
    command = json.loads((ROOT / "package.json").read_text())["scripts"][
        "test:docs-automation"
    ]
    for name in (
        "release-version",
        "docs-snapshots",
        "legacy-pages",
        "assemble-docs-site",
    ):
        assert "scripts/tests/" + name + ".test.js" in command
    workflow = yaml.safe_load((ROOT / ".github/workflows/tests.yml").read_text())
    native = workflow["jobs"]["native-targets"]
    assert {row["os"] for row in native["strategy"]["matrix"]["include"]} == {
        "windows-2022",
        "macos-14",
        "ubuntu-24.04",
    }
    assert any(
        step.get("uses", "").startswith("actions/setup-node@")
        for step in native["steps"]
    )


def test_frozen_reader_attributes_and_provenance():
    directory = ROOT / "scripts/tests/fixtures/release-bridge"
    metadata = json.loads((directory / "source.json").read_text())
    for name in ("update.ps1", "update.sh"):
        path = directory / (name + ".fixture")
        assert hashlib.sha256(path.read_bytes()).hexdigest() == metadata["sha256"][name]
        result = subprocess.run(
            ["git", "check-attr", "text", "--", str(path)],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        assert result.stdout.strip().endswith(": text: unset")


@pytest.mark.parametrize(
    "owner,package_count", [("local", 1), ("gpid-native-profile", 0)]
)
def test_executed_gate_counts_keep_package_owner_separate(
    monkeypatch, tmp_path, owner, package_count
):
    calls = []

    def run(argv, **kwargs):
        calls.append(tuple(argv))
        return subprocess.CompletedProcess(
            argv, 0, "uv 0.11.3" if argv == ["uv", "--version"] else "", ""
        )

    monkeypatch.setattr(preflight.subprocess, "run", run)
    result = preflight.run_native_target(
        tmp_path, preflight.full_gate_selection(), gate_owner=owner
    )
    assert result.exit_code == 0
    assert sum("packages/cg-release/tests" in argv for argv in calls) == package_count
    assert sum("ruff" in argv for argv in calls) == package_count
    assert (
        sum("build" in argv and "--no-isolation" in argv for argv in calls)
        == package_count
    )
    assert (
        sum(
            "scripts/tests/test_release_controller_profile.py" in argv for argv in calls
        )
        == 1
    )
    assert (
        sum("scripts/tests/test_release_version_readers.py" in argv for argv in calls)
        == 1
    )
    assert sum("scripts/cg_validate_modules.py" in argv for argv in calls) == 3


def test_source_job_uses_locked_native_interpreter_not_core_environment():
    workflow = yaml.safe_load(
        (ROOT / ".github/workflows/release-controller-build.yml").read_text()
    )
    job = workflow["jobs"]["build"]
    assert "environment" not in job
    text = json.dumps(job)
    assert "RELEASE_CONTROL_APP_PRIVATE_KEY" not in text
    assert "--group gpid-native" in text and "--locked" in text
    assert "CG_RELEASE_NATIVE_PYTHON" in text
    assert "--no-install-project" in text
    policy = json.loads((ROOT / ".release-controller.json").read_text())
    assert "packages/cg-release/pyproject.toml" in policy["build"]["lock_paths"]
    assert any(
        item["name"] == "native-environment.json"
        for item in policy["build"]["artifacts"]
    )


@pytest.mark.parametrize("owner", ["local", "gpid-native-profile"])
def test_full_package_timeout_is_bounded_and_exclusive(monkeypatch, tmp_path, owner):
    calls = []

    def run(argv, **kwargs):
        calls.append((tuple(argv), kwargs["timeout"]))
        return subprocess.CompletedProcess(
            argv, 0, "uv 0.11.3" if argv == ["uv", "--version"] else "", ""
        )

    monkeypatch.setattr(preflight.subprocess, "run", run)
    result = preflight.run_native_target(
        tmp_path, preflight.full_gate_selection(), gate_owner=owner
    )
    assert result.exit_code == 0
    assert len(calls) == (9 if owner == "local" else 5)
    for argv, timeout in calls:
        assert timeout == (1800 if "packages/cg-release/tests" in argv else 600)


def test_filtered_package_command_keeps_default_timeout(monkeypatch, tmp_path):
    command = next(
        argv for argv in preflight.selected_native_commands(
            preflight.full_gate_selection(), tmp_path
        ) if "packages/cg-release/tests" in argv
    ) + ("-k", "module_bounds")

    def run(argv, **kwargs):
        assert kwargs["timeout"] == 600
        raise subprocess.TimeoutExpired(argv, kwargs["timeout"])

    monkeypatch.setattr(preflight.subprocess, "run", run)
    result = preflight.run_native_target(tmp_path, commands=(command, ("never",)))
    assert result.exit_code != 0
    assert len(result.commands) == 1
