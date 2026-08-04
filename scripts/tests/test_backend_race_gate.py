"""Tests for the CI backend-race JUnit report gate."""
from __future__ import annotations

from pathlib import Path

from assert_backend_race_gate import main


def _write_report(path: Path, body: str) -> None:
    path.write_text(
        f'<testsuite tests="1">{body}</testsuite>',
        encoding="utf-8",
    )


def test_backend_gate_accepts_non_skipped_test(tmp_path: Path, capsys) -> None:
    report = tmp_path / "results.xml"
    _write_report(report, '<testcase classname="race" name="runs" />')

    assert main([str(report), "backend_posix"]) == 0
    assert "backend_posix" in capsys.readouterr().out


def test_backend_gate_rejects_skipped_test(tmp_path: Path, capsys) -> None:
    report = tmp_path / "results.xml"
    _write_report(report, '<testcase classname="race" name="skips"><skipped /></testcase>')

    assert main([str(report), "backend_windows"]) == 1
    assert "skipped" in capsys.readouterr().err


def test_backend_gate_rejects_empty_report(tmp_path: Path, capsys) -> None:
    report = tmp_path / "results.xml"
    report.write_text('<testsuite tests="0" />', encoding="utf-8")

    assert main([str(report), "backend_posix"]) == 1
    assert "No tests" in capsys.readouterr().err