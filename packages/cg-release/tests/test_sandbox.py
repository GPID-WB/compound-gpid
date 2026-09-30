"""Offline rollout planning cannot authorize or perform a remote trial."""

import json
import socket
import subprocess
import sys
from pathlib import Path

import pytest
from test_timing import benchmark_module as benchmark_module


def config(profile: str = "generic") -> dict:
    """Return synthetic explicit identity data, never a discovered origin."""
    return {
        "schema_version": 1,
        "repository_id": 123,
        "repository_url": "https://github.com/example/release-sandbox",
        "profile": profile,
        "authorization_reference": "fixture-only-not-live-approval",
    }


@pytest.mark.parametrize("profile", ["generic", "gpid"])
def test_trial_plan_is_offline_and_keeps_every_live_case_deferred(
    benchmark_module, monkeypatch, profile
) -> None:
    def forbidden(*_args, **_kwargs):
        pytest.fail("Offline trial planning reached a process or network boundary")

    monkeypatch.setattr(subprocess, "Popen", forbidden)
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    result = benchmark_module.plan_sandbox(config(profile), repository_id=123)
    assert result["mode"] == "offline-trial-plan"
    assert result["remote_writes"] == 0
    assert result["live_evidence"] == "deferred-not-passed"
    assert result["authorization_verified"] is False
    cases = result["cases"]
    assert all(row["status"] == "deferred-not-passed" for row in cases)
    assert {"approval-role-denials", "portable-locator-recovery", "timing"} <= {
        row["id"] for row in cases
    }
    assert ("bridge-clean-clients" in {r["id"] for r in cases}) == (profile == "gpid")


@pytest.mark.parametrize(
    "change",
    [
        {"schema_version": 2},
        {"repository_id": True},
        {"repository_id": 456},
        {"repository_url": "https://github.com/example/repo?token=private"},
        {"repository_url": "https://evil.test/example/repo"},
        {"repository_url": "https://user:secret@github.com/example/repo"},
        {"profile": "production"},
        {"authorization_reference": ""},
        {"enabled": True},
    ],
)
def test_invalid_or_mismatched_target_is_rejected(benchmark_module, change) -> None:
    with pytest.raises(ValueError):
        benchmark_module.plan_sandbox(config() | change, repository_id=123)


def test_cli_requires_explicit_matching_id_before_planning(
    benchmark_module, monkeypatch, tmp_path, capsys
) -> None:
    path = tmp_path / "sandbox.json"
    path.write_text(json.dumps(config()), encoding="utf-8")
    monkeypatch.setattr("sys.argv", ["benchmark", "--sandbox-config", str(path)])
    assert benchmark_module.main() == 2
    assert json.loads(capsys.readouterr().out)["code"] == "E_BENCHMARK_INPUT"


def test_template_fixture_is_a_plan_not_a_runtime_policy(benchmark_module) -> None:
    path = Path(__file__).parent / "fixtures/sandbox.example.json"
    result = benchmark_module.plan_sandbox(
        json.loads(path.read_text(encoding="utf-8")), repository_id=123
    )
    assert result["authorization_verified"] is False
    assert result["live_evidence"] == "deferred-not-passed"


def test_duplicate_keys_and_oversized_input_fail(benchmark_module, tmp_path) -> None:
    path = tmp_path / "input.json"
    for content in ('{"repository_id":123,"repository_id":456}', " " * 65537):
        path.write_text(content, encoding="utf-8")
        with pytest.raises(ValueError):
            benchmark_module.read_input(path)


@pytest.mark.parametrize("obstruction", ["existing-file", "parent-file", "directory"])
def test_cli_output_errors_are_structured_and_preserve_existing_bytes(
    benchmark_module, tmp_path, obstruction
) -> None:
    protected = tmp_path / "private-evidence.json"
    output = protected
    if obstruction == "directory":
        protected.mkdir()
        protected = protected / "retained.json"
    elif obstruction == "parent-file":
        output = protected / "new.json"
    original = b"existing evidence\x00\xff\n"
    protected.write_bytes(original)
    fixture = Path(__file__).parent / "fixtures/sandbox.example.json"
    result = subprocess.run(
        [
            sys.executable,
            "-I",
            "-B",
            benchmark_module.__file__,
            "--sandbox-config",
            str(fixture),
            "--repository-id",
            "123",
            "--output",
            str(output),
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
    )
    assert protected.read_bytes() == original
    assert result.returncode == 2
    error = json.loads(result.stdout)
    assert error["code"] == "E_BENCHMARK_OUTPUT"
    assert "new writable output path" in error["message"]
    assert result.stderr == ""
    assert "private-evidence" not in result.stdout


def test_cli_large_finite_measurements_write_valid_exclusive_report(
    benchmark_module, tmp_path
) -> None:
    from test_performance import measurements

    data = measurements()
    for sample in data["samples"]:
        sample.update(total_seconds=1e308, confirmation_seconds=0.0)
    path = tmp_path / "measurements.json"
    path.write_text(json.dumps(data, allow_nan=False), encoding="utf-8")
    fixture = Path(__file__).parent / "fixtures/sandbox.example.json"
    output = tmp_path / "new-directory" / "report.json"
    result = subprocess.run(
        [
            sys.executable,
            "-I",
            "-B",
            benchmark_module.__file__,
            "--sandbox-config",
            str(fixture),
            "--repository-id",
            "123",
            "--measurements",
            str(path),
            "--output",
            str(output),
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == result.stderr == ""
    report = json.loads(output.read_text(encoding="utf-8"))
    assert report["measurements"]["median_seconds"] == 1e308
    assert report["measurements"]["live_handoff_passed"] is False
    assert report["live_evidence"] == "deferred-not-passed"


def test_cli_serialization_failure_uses_output_error_before_creating_file(
    benchmark_module, monkeypatch, tmp_path, capsys
) -> None:
    output = tmp_path / "not-created.json"
    monkeypatch.setattr(
        benchmark_module, "benchmark_offline", lambda: {"x": float("inf")}
    )
    monkeypatch.setattr("sys.argv", ["benchmark", "--output", str(output)])
    assert benchmark_module.main() == 2
    captured = capsys.readouterr()
    assert json.loads(captured.out)["code"] == "E_BENCHMARK_OUTPUT"
    assert captured.err == ""
    assert not output.exists()
