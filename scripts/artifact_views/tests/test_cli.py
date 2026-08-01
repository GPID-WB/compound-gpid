"""Tests for one-file artifact render, validation, and stale-check CLI modes."""
from __future__ import annotations

from pathlib import Path
import shutil

import pytest

from artifact_views import cli

FIXTURES = Path(__file__).parent / "fixtures"
SOURCE_RELATIVE = Path(".cg-docs/plans/example.md")
VIEW_RELATIVE = Path(".cg-docs/views/plans/example.html")


def _project(tmp_path: Path, *, config: str = "") -> Path:
    root = tmp_path / "repo"
    root.mkdir()
    (root / "compound-gpid.md").write_text("# Project\n", encoding="utf-8")
    (root / "compound-gpid.local.md").write_text(
        f"---\n{config}---\n# Local\n",
        encoding="utf-8",
    )
    source = root / SOURCE_RELATIVE
    source.parent.mkdir(parents=True)
    shutil.copyfile(FIXTURES / "strict_plan.md", source)
    return root


def _charterless_project(tmp_path: Path) -> Path:
    root = tmp_path / "charterless"
    source = root / SOURCE_RELATIVE
    source.parent.mkdir(parents=True)
    shutil.copyfile(FIXTURES / "strict_plan.md", source)
    return root


def _run(
    root: Path,
    arguments: list[str],
    capsys: pytest.CaptureFixture,
) -> tuple[int, str, str]:
    result = cli.main(["--root", str(root), *arguments])
    captured = capsys.readouterr()
    return result, captured.out, captured.err


def test_explicit_render_writes_one_view_and_prints_only_path(
    tmp_path: Path,
    capsys: pytest.CaptureFixture,
) -> None:
    root = _project(tmp_path)

    result, stdout, stderr = _run(root, [str(SOURCE_RELATIVE)], capsys)

    assert result == 0
    assert stdout == f"{VIEW_RELATIVE.as_posix()}\n"
    assert stderr == ""
    assert (root / VIEW_RELATIVE).read_text(encoding="utf-8").startswith(
        "<!doctype html>\n"
    )


def test_find_project_root_accepts_charterless_cg_docs_boundary(tmp_path: Path) -> None:
    root = _charterless_project(tmp_path)

    assert cli.find_project_root(root / SOURCE_RELATIVE) == root


def test_cli_runs_from_charterless_project_without_hidden_root(
    tmp_path: Path,
    capsys: pytest.CaptureFixture,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _charterless_project(tmp_path)
    monkeypatch.chdir(root)

    result = cli.main([str(SOURCE_RELATIVE)])
    captured = capsys.readouterr()

    assert result == 0
    assert captured.out == f"{VIEW_RELATIVE.as_posix()}\n"
    assert (root / VIEW_RELATIVE).is_file()


def test_automatic_enabled_validates_and_writes(
    tmp_path: Path,
    capsys: pytest.CaptureFixture,
) -> None:
    root = _project(tmp_path)

    result, stdout, _ = _run(
        root,
        ["--automatic", str(SOURCE_RELATIVE)],
        capsys,
    )

    assert result == 0
    assert stdout == f"{VIEW_RELATIVE.as_posix()}\n"
    assert (root / VIEW_RELATIVE).is_file()


def test_automatic_opt_out_still_validates_and_does_not_write(
    tmp_path: Path,
    capsys: pytest.CaptureFixture,
) -> None:
    root = _project(tmp_path, config="artifact-html: false\n")

    result, stdout, stderr = _run(
        root,
        ["--automatic", str(SOURCE_RELATIVE)],
        capsys,
    )

    assert result == 0
    assert stdout == f"HTML disabled; validated {SOURCE_RELATIVE.as_posix()}\n"
    assert stderr == ""
    assert not (root / VIEW_RELATIVE).exists()

    source = root / SOURCE_RELATIVE
    source.write_text(source.read_text(encoding="utf-8").replace("## Objective", "## Missing Objective"), encoding="utf-8")
    result, _, stderr = _run(
        root,
        ["--automatic", str(SOURCE_RELATIVE)],
        capsys,
    )
    assert result == 1
    assert "Required section" in stderr
    assert not (root / VIEW_RELATIVE).exists()


def test_explicit_render_ignores_automatic_opt_out(
    tmp_path: Path,
    capsys: pytest.CaptureFixture,
) -> None:
    root = _project(tmp_path, config="artifact-html: false\n")

    result, stdout, _ = _run(root, [str(SOURCE_RELATIVE)], capsys)

    assert result == 0
    assert stdout == f"{VIEW_RELATIVE.as_posix()}\n"
    assert (root / VIEW_RELATIVE).is_file()


def test_validate_only_never_writes(
    tmp_path: Path,
    capsys: pytest.CaptureFixture,
) -> None:
    root = _project(tmp_path)

    result, stdout, stderr = _run(
        root,
        ["--validate-only", str(SOURCE_RELATIVE)],
        capsys,
    )

    assert result == 0
    assert stdout == f"Validated {SOURCE_RELATIVE.as_posix()}\n"
    assert stderr == ""
    assert not (root / VIEW_RELATIVE).exists()


def test_check_reports_missing_current_and_stale_even_under_opt_out(
    tmp_path: Path,
    capsys: pytest.CaptureFixture,
) -> None:
    root = _project(tmp_path, config="artifact-html: false\n")

    result, stdout, _ = _run(root, ["--check", str(SOURCE_RELATIVE)], capsys)
    assert result == 1
    assert stdout == f"missing {VIEW_RELATIVE.as_posix()}\n"

    assert _run(root, [str(SOURCE_RELATIVE)], capsys)[0] == 0
    result, stdout, _ = _run(root, ["--check", str(SOURCE_RELATIVE)], capsys)
    assert result == 0
    assert stdout == f"current {VIEW_RELATIVE.as_posix()}\n"

    source = root / SOURCE_RELATIVE
    source.write_text(source.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    result, stdout, _ = _run(root, ["--check", str(SOURCE_RELATIVE)], capsys)
    assert result == 1
    assert stdout == f"stale {VIEW_RELATIVE.as_posix()}\n"


@pytest.mark.parametrize(
    "mutation",
    (
        lambda text: text.replace("Execution contract", "Forged contract", 1),
        lambda text: text.replace("default-src 'none'", "default-src *", 1),
        lambda text: text.replace('"artifactSchemaVersion":1,', "", 1),
    ),
    ids=("body", "csp", "provenance"),
)
def test_check_reports_tampered_view_stale(
    tmp_path: Path,
    capsys: pytest.CaptureFixture,
    mutation,
) -> None:
    root = _project(tmp_path)
    assert _run(root, [str(SOURCE_RELATIVE)], capsys)[0] == 0
    view = root / VIEW_RELATIVE
    original = view.read_text(encoding="utf-8")
    tampered = mutation(original)
    assert tampered != original
    view.write_text(tampered, encoding="utf-8")

    result, stdout, _ = _run(root, ["--check", str(SOURCE_RELATIVE)], capsys)

    assert result == 1
    assert stdout == f"stale {VIEW_RELATIVE.as_posix()}\n"


def test_invalid_config_warns_and_defaults_automatic_html_enabled(
    tmp_path: Path,
    capsys: pytest.CaptureFixture,
) -> None:
    root = _project(tmp_path, config="artifact-html: sometimes\n")

    result, stdout, stderr = _run(
        root,
        ["--automatic", str(SOURCE_RELATIVE)],
        capsys,
    )

    assert result == 0
    assert stdout == f"{VIEW_RELATIVE.as_posix()}\n"
    assert "invalid artifact-html" in stderr.lower()
    assert (root / VIEW_RELATIVE).is_file()


@pytest.mark.parametrize(
    "arguments",
    (
        ["--automatic", "--check", str(SOURCE_RELATIVE)],
        ["--validate-only", "--check", str(SOURCE_RELATIVE)],
        [str(SOURCE_RELATIVE), str(SOURCE_RELATIVE)],
        [".cg-docs/plans"],
    ),
)
def test_conflicting_multiple_or_directory_inputs_fail(
    tmp_path: Path,
    capsys: pytest.CaptureFixture,
    arguments: list[str],
) -> None:
    root = _project(tmp_path)

    result, _, stderr = _run(root, arguments, capsys)

    assert result == 2
    assert stderr


def test_failure_output_contains_state_expected_path_and_recovery_command(
    tmp_path: Path,
    capsys: pytest.CaptureFixture,
) -> None:
    root = _project(tmp_path)
    source = root / SOURCE_RELATIVE
    source.write_text(source.read_text(encoding="utf-8").replace("## Objective", "## Missing Objective"), encoding="utf-8")

    result, stdout, stderr = _run(root, [str(SOURCE_RELATIVE)], capsys)

    assert result == 1
    assert stdout == ""
    assert f"Source: {SOURCE_RELATIVE.as_posix()}" in stderr
    assert f"Expected view: {VIEW_RELATIVE.as_posix()} (missing)" in stderr
    assert f"Recover: cg-render-artifact {SOURCE_RELATIVE.as_posix()}" in stderr
