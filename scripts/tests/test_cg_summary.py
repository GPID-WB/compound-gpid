from __future__ import annotations

import json
import os
import stat
import subprocess
from pathlib import Path

import pytest

import cg_summary

# Pytest fixtures are injected through same-named test parameters.
# pylint: disable=redefined-outer-name


def write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=repo, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)


@pytest.fixture()
def git_repo(tmp_path: Path) -> Path:
    git(tmp_path, "init")
    git(tmp_path, "config", "user.email", "test@example.invalid")
    git(tmp_path, "config", "user.name", "Test User")
    write(tmp_path / "README.md", "# Test\n")
    git(tmp_path, "add", "README.md")
    git(tmp_path, "commit", "-m", "initial")
    return tmp_path


def test_redact_secret_like_values() -> None:
    raw = "TOKEN=abc password=hunter2 api_key=xyz secret: nope"
    redacted = cg_summary.redact(raw)
    assert "abc" not in redacted
    assert "hunter2" not in redacted
    assert "xyz" not in redacted
    assert "nope" not in redacted
    assert redacted.count("<redacted>") == 4


def test_runtime_avoids_python_39_only_path_api() -> None:
    source = Path(cg_summary.__file__).read_text(encoding="utf-8")
    assert ".is_relative_to(" not in source


def test_test_summary_reads_last_run_and_writes_redacted_artifact(tmp_path: Path) -> None:
    payload = {
        "totalCount": 3,
        "passedCount": 2,
        "failedCount": 1,
        "filteredFiles": None,
        "ranAt": "2026-06-23T00:00:00Z",
        "failedTests": [{"name": "fails", "message": "TOKEN=abc", "file": "tests/example.Tests.ps1"}],
    }
    write(tmp_path / "tests/last-run.json", json.dumps(payload))

    summary = cg_summary.test_summary(tmp_path, run_id="20260623-000000")

    assert summary["available"] is True
    assert summary["total"] == 3
    assert summary["failed"] == 1
    assert summary["failure_summaries"][0]["name"] == "fails"
    artifact = tmp_path / summary["raw_artifact"]
    assert artifact.exists()
    assert "TOKEN=<redacted>" in artifact.read_text(encoding="utf-8")
    assert "TOKEN=abc" not in artifact.read_text(encoding="utf-8")


def test_test_summary_missing_last_run_is_unavailable(tmp_path: Path) -> None:
    summary = cg_summary.test_summary(tmp_path)
    assert summary["available"] is False
    assert "reads existing results" in summary["note"]


def test_diff_summary_reports_files_hunks_risks_and_artifacts(git_repo: Path) -> None:
    write(git_repo / "README.md", "# Test\n\nchanged token\n")
    write(git_repo / "scripts/token_summary.py", "print('token')\n")

    summary = cg_summary.diff_summary(git_repo, run_id="20260623-000001")

    assert summary["changed_file_count"] == 2
    assert summary["tracked_files"] == ["README.md"]
    assert summary["untracked_files"] == ["scripts/token_summary.py"]
    assert summary["hunks_by_file"]["README.md"] == 1
    assert "python" in summary["risk_tags"]
    assert "token" in summary["risk_tags"]
    assert (git_repo / summary["raw_artifact"]).exists()
    assert (git_repo / summary["stat_artifact"]).exists()


def test_diff_summary_lists_view_path_without_storing_html_body(git_repo: Path) -> None:
    view = write(
        git_repo / ".cg-docs/views/plans/example.html",
        "<!doctype html><p>original</p>\n",
    )
    git(git_repo, "add", ".cg-docs/views/plans/example.html")
    git(git_repo, "commit", "-m", "add generated view")
    sentinel = "VIEW_ONLY_SENTINEL_7E5C9A"
    view.write_text(f"<!doctype html><p>{sentinel}</p>\n", encoding="utf-8")

    summary = cg_summary.diff_summary(git_repo, run_id="20260623-000001-views")
    raw_patch = (git_repo / summary["raw_artifact"]).read_text(encoding="utf-8")

    assert ".cg-docs/views/plans/example.html" in summary["changed_files"]
    assert summary["excluded_body_paths"] == [
        ".cg-docs/views/plans/example.html"
    ]
    assert sentinel not in raw_patch


def test_diff_summary_excludes_generic_document_view_body(git_repo: Path) -> None:
    view = write(
        git_repo / ".cg-docs/views/documents/docs/guide.html",
        "<!doctype html><p>original</p>\n",
    )
    git(git_repo, "add", ".cg-docs/views/documents/docs/guide.html")
    git(git_repo, "commit", "-m", "add generic view")
    sentinel = "GENERIC_VIEW_ONLY_SENTINEL_3A9D"
    view.write_text(f"<!doctype html><p>{sentinel}</p>\n", encoding="utf-8")

    summary = cg_summary.diff_summary(git_repo, run_id="20260803-generic-views")
    raw_patch = (git_repo / summary["raw_artifact"]).read_text(encoding="utf-8")

    assert view.relative_to(git_repo).as_posix() in summary["excluded_body_paths"]
    assert sentinel not in raw_patch


def test_log_summary_reports_branch_commits_and_notable_files(git_repo: Path) -> None:
    write(git_repo / "src.py", "print('hi')\n")
    git(git_repo, "add", "src.py")
    git(git_repo, "commit", "-m", "add src")
    base = git(git_repo, "rev-parse", "HEAD~1").stdout.strip()

    summary = cg_summary.log_summary(git_repo, base=base, run_id="20260623-000002")

    assert summary["available"] is True
    assert summary["first_parent_commit_count"] == 1
    assert summary["commits"][0]["subject"] == "add src"
    assert summary["notable_files"] == ["src.py"]
    assert "python" in summary["risk_tags"]
    assert (git_repo / summary["raw_artifact"]).exists()


def test_tree_summary_excludes_noisy_directories_and_respects_limit(tmp_path: Path) -> None:
    write(tmp_path / ".git/HEAD", "ref: main\n")
    write(tmp_path / ".cg-docs/token/outputs/run/raw.txt", "large\n")
    write(tmp_path / "node_modules/pkg/index.js", "large\n")
    write(tmp_path / "a.txt", "a\n")
    write(tmp_path / "b.txt", "b\n")

    summary = cg_summary.tree_summary(tmp_path, max_entries=1)

    assert summary["entries"] == ["a.txt"]
    assert summary["truncated"] is True
    assert ".git/HEAD" not in summary["entries"]
    assert not any(entry.startswith(".cg-docs/token/outputs/") for entry in summary["entries"])


def test_problems_summary_without_input_degrades_gracefully(tmp_path: Path) -> None:
    summary = cg_summary.problems_summary(tmp_path)
    assert summary["available"] is False
    assert "No diagnostics file" in summary["reason"]


def test_problems_summary_json_counts_severities(tmp_path: Path) -> None:
    source = write(
        tmp_path / "problems.json",
        json.dumps({"diagnostics": [{"severity": "error", "message": "bad", "file": "a.py"}, {"level": "warn", "message": "check"}]}),
    )

    summary = cg_summary.problems_summary(tmp_path, source, run_id="20260623-000003")

    assert summary["available"] is True
    assert summary["parser"] == "json"
    assert summary["severity_counts"] == {"error": 1, "warning": 1}
    assert (tmp_path / summary["raw_artifact"]).exists()


def test_problems_summary_text_counts_severities(tmp_path: Path) -> None:
    source = write(tmp_path / "problems.txt", "INFO ok\nWARN watch\nERROR broken\n")

    summary = cg_summary.problems_summary(tmp_path, source, run_id="20260623-000004")

    assert summary["parser"] == "text"
    assert summary["severity_counts"] == {"error": 1, "info": 1, "warning": 1}


def test_markdown_output_is_bounded_and_contains_artifact(tmp_path: Path) -> None:
    write(tmp_path / "tests/last-run.json", json.dumps({"totalCount": 1, "passedCount": 1, "failedCount": 0}))
    summary = cg_summary.test_summary(tmp_path, run_id="20260623-000005")
    rendered = cg_summary.to_markdown(summary)

    assert "# Test Summary" in rendered
    assert "raw_artifact" in rendered
    assert cg_summary.estimate_tokens(rendered) < 300


def test_cli_emits_valid_json(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    write(tmp_path / "tests/last-run.json", json.dumps({"totalCount": 1, "passedCount": 1, "failedCount": 0}))

    assert cg_summary.main(["--root", str(tmp_path), "--format", "json", "--run-id", "20260623-000006", "test"]) == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["kind"] == "test"
    assert payload["available"] is True


def test_cli_accepts_common_options_after_subcommand(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    write(tmp_path / "tests/last-run.json", json.dumps({"totalCount": 1, "passedCount": 1, "failedCount": 0}))

    assert cg_summary.main(["test", "--root", str(tmp_path), "--format", "json", "--run-id", "20260623-000007"]) == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["source"] == "tests/last-run.json"


def test_invalid_tree_limit_errors(tmp_path: Path) -> None:
    with pytest.raises(SystemExit):
        cg_summary.main(["--root", str(tmp_path), "tree", "--max-entries", "0"])


def test_shell_wrappers_exist_and_reference_expected_subcommands() -> None:
    repo = Path(__file__).resolve().parents[2]
    expected = {
        "bin/cg-test-summary": "test",
        "bin/cg-diff-summary": "diff",
        "bin/cg-log-summary": "log",
        "bin/cg-tree-summary": "tree",
        "bin/cg-problems-summary": "problems",
    }
    for rel_path, subcommand in expected.items():
        path = repo / rel_path
        assert path.exists()
        content = path.read_text(encoding="utf-8")
        assert content.startswith("#!/bin/bash")
        assert f"cg_summary.py\" {subcommand}" in content
        if os.name != "nt":
            assert os.stat(path).st_mode & stat.S_IXUSR
