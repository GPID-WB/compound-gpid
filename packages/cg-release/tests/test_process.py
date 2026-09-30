"""Authorization-key regression coverage for argv and diagnostic boundaries."""

import json
import subprocess
from pathlib import Path

import pytest

import cg_release.process as process
from cg_release.events import ControllerError, emit_event, redact
from cg_release.models import Event

HEADERS = [
    "Authorization: token OPAQUE_TEST_VALUE",
    "aUtHoRiZaTiOn: unknown-scheme OPAQUE_TEST_VALUE",
    "AUTHORIZATION = OPAQUE_TEST_VALUE",
    "Authorization: Digest value=OPAQUE_TEST_VALUE, another=OPAQUE_SECOND_VALUE",
    "http.extraHeader=Authorization: token OPAQUE_TEST_VALUE",
    "Proxy-Authorization: arbitrary OPAQUE_TEST_VALUE",
    "Authorization:\r\n token OPAQUE_TEST_VALUE",
]


@pytest.mark.parametrize("header", HEADERS)
def test_authorization_key_blocks_argv_before_any_process(
    header: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = []

    def observe(argv: list[str], **_kwargs: object) -> subprocess.CompletedProcess:
        calls.append(argv)
        return subprocess.CompletedProcess(argv, 0, "", "")

    monkeypatch.setattr(subprocess, "Popen", observe)
    # Rejection must use the authorization key, not rely on display redaction.
    monkeypatch.setattr(process, "redact", lambda value: value)
    with pytest.raises(ControllerError) as error:
        process.run_process("gh", ["api", "-H", header, "user"], cwd=tmp_path)
    assert error.value.code == "E_PROCESS_ARGUMENT"
    assert not calls


@pytest.mark.parametrize("header", HEADERS)
@pytest.mark.parametrize("json_output", [False, True])
def test_authorization_value_is_removed_from_errors_and_events(
    header: str,
    json_output: bool,
    capsys: pytest.CaptureFixture,
) -> None:
    error = ControllerError("E_TEST", header)
    assert "OPAQUE_" not in str(error)
    assert "OPAQUE_" not in redact(header)
    emit_event(Event(kind="error", message=header), json_output=json_output)
    output = capsys.readouterr()
    assert "OPAQUE_" not in output.out + output.err
    assert "[REDACTED]" in output.out
    if json_output:
        assert json.loads(output.out)["kind"] == "error"
