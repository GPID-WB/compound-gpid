"""Real CLI output and confirmation tests; providers are replaced before invocation."""

import json
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import pytest
from test_preview import snapshot

from cg_release import cli


def test_plan_outputs_structured_preview_without_admission(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    monkeypatch.setattr(cli, "acquire_snapshot", lambda *_a, **_k: snapshot())
    assert cli.main(["plan", "--version", "1.0.0", "--json"]) == 0
    event = json.loads(capsys.readouterr().out)
    assert event["kind"] == "preview"
    assert event["proposal"]["version"] == "1.0.0"
    assert event["proposal"]["submission_available"] is False


def test_start_yes_rechecks_but_cannot_submit(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    calls = []

    def acquire(*_a: object, **_k: object):
        calls.append(1)
        return snapshot()

    monkeypatch.setattr(cli, "acquire_snapshot", acquire)
    assert cli.main(["start", "--version", "1.0.0", "--yes", "--json"]) == 2
    events = [json.loads(line) for line in capsys.readouterr().out.splitlines()]
    assert [e["kind"] for e in events] == ["preview", "error"]
    assert events[-1]["code"] == "E_SUBMISSION_UNAVAILABLE"
    assert calls == [1, 1]


def test_noninteractive_start_requires_yes(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    monkeypatch.setattr(cli, "acquire_snapshot", lambda *_a, **_k: snapshot())
    monkeypatch.setattr(sys.stdin, "isatty", lambda: False)
    assert cli.main(["start", "--version", "1.0.0", "--json"]) == 2
    events = [json.loads(line) for line in capsys.readouterr().out.splitlines()]
    assert events[-1]["code"] == "E_CONFIRMATION_REQUIRED"


def test_real_subprocess_preview_json_and_human_output(tmp_path: Path) -> None:
    """Run CLI in a generic directory without GPID; inject only acquisition data."""
    tests = str(Path(__file__).parent)
    for json_output in (True, False):
        code = (
            "import sys; sys.path.insert(0, " + repr(tests) + "); "
            "from test_preview import snapshot; from cg_release import cli; "
            "cli.acquire_snapshot=lambda *a,**k:snapshot(); "
            "raise SystemExit(cli.main("
            + repr(["plan", "--version", "1.0.0"] + (["--json"] if json_output else []))
            + "))"
        )
        result = subprocess.run(
            [sys.executable, "-c", code],
            cwd=tmp_path,
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        )
        assert result.returncode == 0, result.stderr
        assert "Traceback" not in result.stderr
        if json_output:
            assert json.loads(result.stdout)["kind"] == "preview"
        else:
            assert "1.0.0" in result.stdout and "source_sha" in result.stdout


@pytest.mark.parametrize(
    "answer,outcome",
    [
        ("y", "complete"),
        ("n", "complete"),
        (EOFError, "interrupted"),
        (KeyboardInterrupt, "interrupted"),
    ],
)
def test_confirmation_timing_excludes_only_human_wait(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture,
    answer: object,
    outcome: str,
) -> None:
    now, deadlines = [0.0], []
    state = snapshot()
    policy = json.loads(state.policy_raw)
    policy["timeouts"]["start_seconds"] = 10
    state = replace(state, policy_raw=json.dumps(policy).encode())

    def acquire(*_a: object, **kwargs: object):
        deadlines.append(kwargs["deadline"])
        now[0] += 2 if len(deadlines) == 1 else 3
        return state

    def respond():
        now[0] += 500
        if isinstance(answer, type):
            raise answer
        return answer

    monkeypatch.setattr(cli, "acquire_snapshot", acquire)
    monkeypatch.setattr("builtins.input", respond)
    monkeypatch.setattr(cli.sys.stdin, "isatty", lambda: True)
    assert (
        cli.main(["start", "--version", "1.0.0", "--json"], clock=lambda: now[0]) == 2
    )
    events = [json.loads(line) for line in capsys.readouterr().out.splitlines()]
    timing = [e for e in events if e["kind"] == "timing"]
    assert len(timing) == 1 and timing[0]["step"] == "confirmation"
    assert timing[0]["elapsed_seconds"] == 500 and timing[0]["observed"] == outcome
    assert not any(e["step"] == "submission" for e in events)
    if answer == "y":
        assert (
            deadlines == [120, 510] and events[-1]["code"] == "E_SUBMISSION_UNAVAILABLE"
        )
    else:
        assert len(deadlines) == 1 and events[-1]["code"] == "E_DECLINED"


@pytest.mark.parametrize("first,second,limit", [(11, 0, 10), (2, 9, 10), (60, 61, 120)])
def test_acquisition_and_recheck_share_deadline(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture,
    first: int,
    second: int,
    limit: int,
) -> None:
    now, calls = [0.0], []
    state = snapshot()
    policy = json.loads(state.policy_raw)
    policy["timeouts"]["start_seconds"] = limit
    state = replace(state, policy_raw=json.dumps(policy).encode())

    def acquire(*_a: object, **_k: object):
        now[0] += first if not calls else second
        calls.append(1)
        return state

    monkeypatch.setattr(cli, "acquire_snapshot", acquire)
    assert (
        cli.main(
            ["start", "--version", "1.0.0", "--yes", "--json"], clock=lambda: now[0]
        )
        == 2
    )
    events = [json.loads(line) for line in capsys.readouterr().out.splitlines()]
    assert events[-1]["code"] == "E_DEADLINE"
    assert len(calls) == (1 if first >= limit else 2)
