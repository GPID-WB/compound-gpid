"""Injected-clock timing and non-publishing benchmark contracts."""

import importlib.util
import json
import socket
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest

from cg_release.timing import STAGES, TimingRecorder


@pytest.fixture
def benchmark_module() -> ModuleType:
    """Load the repository benchmark without running its CLI."""
    script = Path(__file__).resolve().parents[3] / "scripts/benchmark_release.py"
    spec = importlib.util.spec_from_file_location("benchmark_release_test", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("extra_call", [False, True])
def test_benchmark_observes_real_process_boundary_and_forbids_network(
    benchmark_module: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    extra_call: bool,
) -> None:
    """An injected extra Git call must trip the observed resource budget."""
    observed = []
    original_popen = subprocess.Popen
    allowed = {
        ("git", "init", "--quiet"),
        ("git", "rev-parse", "--is-inside-work-tree"),
        ("git", "status", "--porcelain"),
    }

    def observe(argv: list[str], **kwargs: object) -> subprocess.Popen:
        assert tuple(argv) in allowed, "Forbidden offline process"
        observed.append(tuple(argv))
        assert len(observed) <= 3, "Observed Git process budget exceeded"
        return original_popen(argv, **kwargs)

    def forbidden(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("Network is forbidden in the offline benchmark")

    monkeypatch.setattr(subprocess, "Popen", observe)
    monkeypatch.setattr(socket, "create_connection", forbidden)
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket.socket, "connect_ex", forbidden)
    if extra_call:
        original_run = benchmark_module.run_process

        def duplicate(*args: object, **kwargs: object) -> subprocess.CompletedProcess:
            original_run(*args, **kwargs)
            return original_run(*args, **kwargs)

        monkeypatch.setattr(benchmark_module, "run_process", duplicate)
        with pytest.raises(AssertionError, match="Observed Git process budget"):
            benchmark_module.benchmark_offline()
    else:
        report = benchmark_module.benchmark_offline()
        assert report["git_subprocess_count"] == len(observed) == 3
        assert set(observed) == allowed
        assert report["remote_writes"] == 0


@pytest.mark.parametrize(
    "args", [["fetch", "origin"], ["push"], ["-c", "x=y", "status"]]
)
def test_offline_boundary_rejects_unlisted_git_operations(
    benchmark_module: ModuleType,
    args: list[str],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def forbidden(*_args: object, **_kwargs: object) -> None:
        pytest.fail("An unlisted operation reached the process boundary")

    monkeypatch.setattr(benchmark_module, "run_process", forbidden)
    with pytest.raises(ValueError, match="Offline"):
        benchmark_module.OfflineGit().run(args, cwd=tmp_path)


def test_offline_boundary_stops_before_a_fourth_call(
    benchmark_module: ModuleType,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = []

    def observe(
        tool: str, args: list[str], **_kwargs: object
    ) -> subprocess.CompletedProcess:
        calls.append([tool, *args])
        return subprocess.CompletedProcess(calls[-1], 0, "", "")

    monkeypatch.setattr(benchmark_module, "run_process", observe)
    gate = benchmark_module.OfflineGit()
    for _ in range(3):
        gate.run(["status", "--porcelain"], cwd=tmp_path)
    with pytest.raises(ValueError, match="budget exceeded"):
        gate.run(["status", "--porcelain"], cwd=tmp_path)
    assert gate.count == len(calls) == 3


def test_monotonic_elapsed_ignores_wall_clock_skew() -> None:
    ticks = iter([10.0, 12.5])
    wall = iter([100.0, 50.0])
    recorder = TimingRecorder(
        enabled=True, clock=lambda: next(ticks), wall_clock=lambda: next(wall)
    )
    with recorder.span("preparation"):
        pass
    record = recorder.records[0]
    assert record["elapsed_seconds"] == 2.5
    assert record["outcome"] == "complete"
    assert record["wall_started"] == 100.0
    assert record["wall_finished"] == 50.0


def test_disabled_recorder_does_not_call_clocks() -> None:
    def forbidden() -> float:
        pytest.fail("disabled timing must not inspect clocks")

    recorder = TimingRecorder(enabled=False, clock=forbidden, wall_clock=forbidden)
    with recorder.span("gates"):
        pass
    assert recorder.records == []


@pytest.mark.parametrize("failure", [ValueError("token=hidden"), KeyboardInterrupt()])
def test_interrupted_spans_preserve_exception_without_secret_logging(
    failure: BaseException,
) -> None:
    ticks = iter([10.0, 11.0])
    recorder = TimingRecorder(enabled=True, clock=lambda: next(ticks))
    with pytest.raises(type(failure)):
        with recorder.span("publication"):
            raise failure
    assert recorder.records[0]["outcome"] == "interrupted"
    assert recorder.records[0]["elapsed_seconds"] == 1.0
    assert "hidden" not in json.dumps(recorder.records)


def test_repeat_gates_have_distinct_sequence_numbers() -> None:
    ticks = iter([0.0, 1.0, 1.0, 3.0])
    recorder = TimingRecorder(enabled=True, clock=lambda: next(ticks))
    for _ in range(2):
        with recorder.span("gates"):
            pass
    assert [row["sequence"] for row in recorder.records] == [1, 2]
    assert [row["elapsed_seconds"] for row in recorder.records] == [1.0, 2.0]


def test_confirmation_is_a_separate_named_stage() -> None:
    assert "confirmation" in STAGES
    assert {
        "preparation",
        "gates",
        "subprocess",
        "submission",
        "queue",
        "review",
        "build",
        "approval",
        "publication",
        "recovery",
    }.issubset(STAGES)


def test_unknown_stage_cannot_inject_secret_into_records() -> None:
    recorder = TimingRecorder(enabled=True)
    with pytest.raises(ValueError, match="Unknown timing stage"):
        with recorder.span("token=hidden"):
            pass
    assert recorder.records == []


def test_missing_remote_timestamps_remain_missing() -> None:
    recorder = TimingRecorder(enabled=True)
    recorder.remote_interval("queue", started=None, finished=None)
    assert recorder.records[0]["elapsed_seconds"] is None
    assert recorder.records[0]["outcome"] == "missing"


def test_remote_clock_reversal_is_not_reported_as_zero() -> None:
    recorder = TimingRecorder(enabled=True)
    with pytest.raises(ValueError):
        recorder.remote_interval("queue", started=3.0, finished=2.0)


def test_offline_benchmark_is_default_and_bounds_git_calls() -> None:
    root = Path(__file__).resolve().parents[3]
    script = root / "scripts/benchmark_release.py"
    result = subprocess.run(
        [sys.executable, str(script)],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr[-2000:]
    report = json.loads(result.stdout)
    assert report["mode"] == "offline"
    assert report["remote_writes"] == 0
    assert report["git_subprocess_count"] <= 3
    assert report["legacy_baseline"]["status"] == "missing"
    assert report["live_speedup"] is None
    assert report["environment"]["python"]
    assert set(STAGES) == set(report["stage_definitions"])
    assert report["stage_totals_seconds"]["approval"] is None


def test_benchmark_import_does_not_start_work(monkeypatch: pytest.MonkeyPatch) -> None:
    def forbidden(*_args: object, **_kwargs: object) -> None:
        pytest.fail("benchmark import must not spawn subprocesses")

    monkeypatch.setattr(subprocess, "run", forbidden)
    script = Path(__file__).resolve().parents[3] / "scripts/benchmark_release.py"
    spec = importlib.util.spec_from_file_location("benchmark_release_test", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
