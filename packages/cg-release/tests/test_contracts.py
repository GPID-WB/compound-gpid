"""Offline boundary contracts; these do not authorize release operations."""

import hashlib
import json
import subprocess
from pathlib import Path

import pytest
from pydantic import ValidationError

import cg_release.process as process
from cg_release.cli import main, parse_args
from cg_release.events import ControllerError, emit_event, redact
from cg_release.models import (
    Event,
    Policy,
    Provenance,
    Request,
    canonical_bytes,
    load_record,
)
from cg_release.process import run_process

FIXTURES = Path(__file__).parent / "fixtures"


def test_semver_corpus_uses_library_syntax_and_numeric_precedence() -> None:
    """Validate reusable fixtures without implementing release selection."""
    from semver import Version

    corpus = json.loads((FIXTURES / "versions.json").read_text())
    for value in corpus["valid"]:
        assert str(Version.parse(value)) == value
    for value in corpus["invalid"]:
        payload = json.loads((FIXTURES / "request.json").read_text())
        payload["version"] = value
        with pytest.raises(ValueError):
            load_record(Request, json.dumps(payload).encode())
        with pytest.raises(ControllerError):
            parse_args(["plan", "--version", value])
    versions = [Version.parse(value) for value in corpus["ascending"]]
    assert versions == sorted(set(versions))
    assert Version.parse("1.5.0-rc.9") < Version.parse("1.5.0-rc.10")
    for left, right in corpus["equivalent"]:
        assert Version.parse(left) == Version.parse(right)


def test_provenance_separates_source_and_controller_and_requires_jobs() -> None:
    """A source SHA is not substituted for a trusted dispatch workflow SHA."""
    record = load_record(Provenance, (FIXTURES / "provenance.json").read_bytes())
    assert record.release_source_sha != record.controller_workflow_sha
    assert record.run_attempt == 1
    payload = record.model_dump(mode="json")
    payload["jobs"] = []
    with pytest.raises(ValueError):
        load_record(Provenance, json.dumps(payload).encode())


def test_fixture_invariants_keep_phase_one_disabled() -> None:
    corpus = json.loads((FIXTURES / "invariants.json").read_text())
    assert set(corpus["invariants"]) == {f"C{number}" for number in range(1, 7)}
    assert corpus["required_requirement_ids"] == [f"R{i}" for i in range(1, 20)]
    assert corpus["phase1_remote_operations_enabled"] is False
    assert corpus["phase1_release_mode_ci_available"] is False


def test_canonical_digest_has_fixed_bytes() -> None:
    """Canonical JSON is stable across dictionary insertion order."""
    value = {"b": 2, "a": 1}
    assert canonical_bytes(value) == b'{"a":1,"b":2}'
    assert hashlib.sha256(canonical_bytes(value)).hexdigest() == (
        "43258cff783fe7036d8a43033f830adfc60ec037382473548ac742b888292777"
    )


@pytest.mark.parametrize("value", [float("nan"), float("inf")])
def test_canonical_json_rejects_nonfinite_numbers(value: float) -> None:
    with pytest.raises(ValueError):
        canonical_bytes({"value": value})


@pytest.mark.parametrize("model,name", [(Policy, "policy"), (Request, "request")])
def test_valid_fixtures_roundtrip(model: type, name: str) -> None:
    record = load_record(model, (FIXTURES / f"{name}.json").read_bytes())
    assert record.schema_version == 1
    assert load_record(model, canonical_bytes(record)) == record


@pytest.mark.parametrize(
    "mutation",
    [
        {"schema_version": 2},
        {"schema_version": True},
        {"schema_version": "1"},
        {"unknown": "ignored?"},
        {"repository_id": "123"},
        {"repository_id": 0},
    ],
)
def test_request_rejects_unknown_or_coerced_contracts(mutation: dict) -> None:
    payload = json.loads((FIXTURES / "request.json").read_text())
    payload.update(mutation)
    with pytest.raises((ValidationError, ValueError)):
        load_record(Request, json.dumps(payload).encode())


@pytest.mark.parametrize(
    "raw",
    [
        b'{"schema_version":1,"schema_version":1}',
        b"[]",
        b'{"schema_version":NaN}',
        b"\xff",
        b" " * 65537,
    ],
    ids=["duplicate", "array", "nonfinite", "encoding", "oversized"],
)
def test_invalid_json_is_rejected_without_echoing_input(raw: bytes) -> None:
    with pytest.raises(ValueError):
        load_record(Request, raw)


def test_policy_requires_all_controls_and_rejects_unknown_nested_fields() -> None:
    payload = json.loads((FIXTURES / "policy.json").read_text())
    for field in ("controller", "apps", "environments", "timeouts", "required_checks"):
        incomplete = dict(payload)
        del incomplete[field]
        with pytest.raises(ValueError):
            load_record(Policy, json.dumps(incomplete).encode())
    payload["apps"]["untrusted"] = True
    with pytest.raises(ValueError):
        load_record(Policy, json.dumps(payload).encode())


@pytest.mark.parametrize(
    "args",
    [
        ["plan", "--bump", "patch", "--version", "1.0.0"],
        ["start", "--version", "1.0.0", "--channel", "rc"],
        ["plan"],
        ["start", "--bump", "unknown"],
        ["plan", "--version", "01.2.3"],
        ["plan", "--bump", "patch", "--channel", "123"],
        ["plan", "--bump", "patch", "--channel", "rc.1"],
        ["start", "--bump", "patch", "--allow-non-deployment-branch"],
        ["plan", "--bump", "patch", "--reason", "not an override"],
        ["status", "request", "--timeout", "0s"],
        ["status", "request", "--watch", "--timeout", "infinite"],
        ["status", "request", "--ver", "1.0.0"],
        ["plan", "--version", ""],
        ["plan", "--version", "1.0.0", "--channel", ""],
        ["start", "--version", "", "--channel", "rc"],
        ["start", "--bump", "patch", "--channel", ""],
    ],
)
def test_cli_rejects_invalid_options(
    args: list[str],
    capsys: pytest.CaptureFixture,
) -> None:
    with pytest.raises(ControllerError) as error:
        parse_args(args)
    assert error.value.code == "E_ARGUMENT"
    assert main([*args, "--json"]) == 2
    assert json.loads(capsys.readouterr().out)["code"] == "E_ARGUMENT"


@pytest.mark.parametrize(
    "args",
    [
        ["status", "request", "--watch", "--timeout", "10m", "--json"],
        ["resume", "request"],
    ],
)
def test_invalid_observation_locators_fail_closed_without_processes(
    args: list[str],
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture,
) -> None:
    def forbidden(*_args: object, **_kwargs: object) -> None:
        pytest.fail("invalid locators must not execute subprocesses")

    monkeypatch.setattr(subprocess, "Popen", forbidden)
    assert main(args) == 2
    output = capsys.readouterr()
    assert "E_LOCATOR" in output.out
    assert "Traceback" not in output.err
    if "--json" in args:
        event = json.loads(output.out)
        assert event["kind"] == "error"
        assert event["code"] == "E_LOCATOR"


def test_secret_bearing_parse_error_is_not_echoed(
    capsys: pytest.CaptureFixture,
) -> None:
    secret = "ghp_" + "x" * 36
    assert main(["plan", "--version", secret, "--json"]) == 2
    output = capsys.readouterr()
    assert secret not in output.out + output.err
    assert json.loads(output.out)["code"] == "E_ARGUMENT"


@pytest.mark.parametrize(
    "secret",
    [
        "ghp_" + "x" * 36,
        "github_pat_" + "x" * 50,
        "https://person:pass@example.com/x",
        "Authorization: Bearer abcdef",
        "password=hidden",
        "token=hidden",
        "api_key=hidden",
    ],
)
def test_redaction_covers_common_secret_shapes(secret: str) -> None:
    assert secret not in redact(secret)
    assert "[REDACTED]" in redact(secret)


def test_event_stdout_is_one_json_line(capsys: pytest.CaptureFixture) -> None:
    emit_event(
        Event(kind="error", code="E_TEST", message="token=hidden"), json_output=True
    )
    output = capsys.readouterr()
    assert len(output.out.splitlines()) == 1
    assert "hidden" not in output.out
    assert json.loads(output.out)["schema_version"] == 1


def test_process_boundary_passes_argv_without_shell(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    calls = []

    def capture(argv: list[str], **kwargs: object) -> subprocess.CompletedProcess:
        calls.append((argv, kwargs))
        return subprocess.CompletedProcess(argv, 0, "ok", "")

    monkeypatch.setattr(process, "_capture", capture)
    result = run_process("git", ["show", "--", "x; touch injected"], cwd=tmp_path)
    assert result.stdout == "ok"
    argv, kwargs = calls[0]
    assert argv == ["git", "show", "--", "x; touch injected"]
    assert kwargs["timeout"] == 20
    assert kwargs["max_output_bytes"] == process.MAX_OUTPUT_BYTES
    assert Path(kwargs["cwd"]) == tmp_path


@pytest.mark.parametrize(
    "failure,code",
    [
        (subprocess.TimeoutExpired("secret", 20, stderr="token=hidden"), "E_TIMEOUT"),
        (FileNotFoundError("token=hidden"), "E_TOOL_MISSING"),
        (OSError("token=hidden"), "E_PROCESS"),
    ],
)
def test_process_failure_is_typed_and_redacted(
    failure: Exception,
    code: str,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    def fail(*_args: object, **_kwargs: object) -> None:
        raise failure

    monkeypatch.setattr(process, "_capture", fail)
    with pytest.raises(ControllerError) as error:
        run_process("git", ["status"], cwd=tmp_path)
    assert error.value.code == code
    assert "hidden" not in str(error.value)


@pytest.mark.parametrize(
    "tool,args,timeout",
    [
        ("cmd", ["/c", "echo hello"], 20),
        ("git", ["x\x00y"], 20),
        ("gh", ["api", "-H", "Authorization: Bearer secret"], 20),
        ("git", ["status"], 0),
        ("git", ["status"], float("nan")),
    ],
)
def test_process_rejects_unsafe_contracts(
    tool: str, args: list, timeout: float, tmp_path: Path
) -> None:
    with pytest.raises(ControllerError):
        run_process(tool, args, cwd=tmp_path, timeout=timeout)
