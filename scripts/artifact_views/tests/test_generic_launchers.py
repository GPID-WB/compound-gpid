"""Tests for cross-platform generic publication launchers and installation."""
from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

ROOT = Path(__file__).parents[3]


def test_bash_launcher_is_self_relative_and_forwards_status() -> None:
    content = (ROOT / "bin/cg-publish-markdown").read_text(encoding="utf-8")

    assert "SCRIPT_DIR" in content
    assert "python3 python py" in content
    assert "sys.version_info >= (3, 8)" in content
    assert "../scripts/publish_markdown.py" in content
    assert 'exec "$PYTHON_CMD"' in content
    assert '"$@"' in content


def test_cmd_launcher_uses_guarded_candidates_and_forwards_status() -> None:
    content = (ROOT / "bin/cg-publish-markdown.cmd").read_text(encoding="utf-8")

    for candidate in ("python3", "python", "py"):
        assert f"where {candidate} >nul 2>&1" in content
        assert f"call {candidate} -c" in content
    assert "for /f" in content.lower()
    assert "sys.version_info >= (3, 8)" in content
    assert "..\\scripts\\publish_markdown.py" in content
    assert "%*" in content
    assert "exit /b %ERRORLEVEL%" in content


def test_installers_copy_committed_launchers_and_list_command() -> None:
    powershell = (ROOT / "install.ps1").read_text(encoding="utf-8")
    bash = (ROOT / "scripts/install.sh").read_text(encoding="utf-8")

    assert "cgPublishMarkdownCmdSrc" in powershell
    assert 'bin\\cg-publish-markdown.cmd' in powershell
    assert "Copy-Item -Path $cgPublishMarkdownCmdSrc" in powershell
    assert "cg-publish-markdown" in powershell
    assert 'CG_PUBLISH_MARKDOWN_SRC="$COMPOUND_GPID_DIR/bin/cg-publish-markdown"' in bash
    assert 'cp "$COMPOUND_GPID_DIR/bin/cg-publish-markdown"' in bash
    assert "chmod +x \"$BIN_DIR/cg-publish-markdown\"" in bash
    assert "cg-publish-markdown" in bash


@pytest.mark.skipif(os.name != "nt", reason="executes the Windows installed wrapper")
def test_installed_cmd_runs_render_and_check_from_outside_spaced_layout(
    tmp_path: Path,
) -> None:
    install_root = tmp_path / "installed publisher with spaces"
    shutil.copytree(ROOT / "scripts", install_root / "scripts")
    (install_root / "bin").mkdir()
    shutil.copy2(
        ROOT / "bin/cg-publish-markdown.cmd",
        install_root / "bin/cg-publish-markdown.cmd",
    )
    project = tmp_path / "project with spaces"
    project.mkdir()
    (project / "compound-gpid.md").write_text("# Project\n", encoding="utf-8")
    (project / "guide.md").write_text("# Guide\n", encoding="utf-8")
    outside = tmp_path / "outside"
    outside.mkdir()
    command = install_root / "bin/cg-publish-markdown.cmd"

    rendered = subprocess.run(
        [str(command), "--root", str(project), "guide.md"],
        cwd=outside,
        capture_output=True,
        text=True,
        check=False,
    )
    checked = subprocess.run(
        [str(command), "--root", str(project), "--check", "guide.md"],
        cwd=outside,
        capture_output=True,
        text=True,
        check=False,
    )

    assert rendered.returncode == 0, rendered.stderr
    assert checked.returncode == 0, checked.stderr
    assert "current .cg-docs/views/documents/guide.html" in checked.stdout


@pytest.mark.skipif(os.name == "nt", reason="executes the POSIX installed wrapper")
def test_installed_bash_runs_render_and_check_from_outside_spaced_layout(
    tmp_path: Path,
) -> None:
    install_root = tmp_path / "installed publisher with spaces"
    shutil.copytree(ROOT / "scripts", install_root / "scripts")
    (install_root / "bin").mkdir()
    wrapper = install_root / "bin/cg-publish-markdown"
    shutil.copy2(ROOT / "bin/cg-publish-markdown", wrapper)
    wrapper.chmod(0o755)
    project = tmp_path / "project with spaces"
    project.mkdir()
    (project / "compound-gpid.md").write_text("# Project\n", encoding="utf-8")
    (project / "guide.md").write_text("# Guide\n", encoding="utf-8")
    outside = tmp_path / "outside"
    outside.mkdir()

    rendered = subprocess.run(
        [str(wrapper), "--root", str(project), "guide.md"],
        cwd=outside,
        capture_output=True,
        text=True,
        check=False,
    )
    checked = subprocess.run(
        [str(wrapper), "--root", str(project), "--check", "guide.md"],
        cwd=outside,
        capture_output=True,
        text=True,
        check=False,
    )

    assert rendered.returncode == 0, rendered.stderr
    assert checked.returncode == 0, checked.stderr
    assert "current .cg-docs/views/documents/guide.html" in checked.stdout


def test_entrypoint_propagates_invalid_source_status(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / "compound-gpid.md").write_text("# Project\n", encoding="utf-8")
    (project / "guide.md").write_bytes(b"\xff")

    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/publish_markdown.py"),
            "--root",
            str(project),
            "guide.md",
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 2


@pytest.mark.skipif(os.name == "nt", reason="executes Bash candidate fallback")
def test_bash_wrapper_falls_back_and_propagates_child_failure(tmp_path: Path) -> None:
    install_root = tmp_path / "install"
    shutil.copytree(ROOT / "scripts", install_root / "scripts")
    (install_root / "bin").mkdir()
    wrapper = install_root / "bin/cg-publish-markdown"
    shutil.copy2(ROOT / "bin/cg-publish-markdown", wrapper)
    wrapper.chmod(0o755)
    fake_bin = tmp_path / "fake-bin"
    fake_bin.mkdir()
    log = tmp_path / "python.log"
    (fake_bin / "python3").write_text(
        "#!/bin/sh\n"
        "if [ \"$1\" = \"--version\" ]; then echo 'not python'; exit 0; fi\n"
        "exit 99\n",
        encoding="utf-8",
    )
    (fake_bin / "python3").chmod(0o755)
    (fake_bin / "python").write_text(
        "#!/bin/sh\n"
        "if [ \"$1\" = \"--version\" ]; then echo 'Python 3.11.0'; exit 0; fi\n"
        "if [ \"$1\" = \"-c\" ]; then exit 0; fi\n"
        f"printf '%s\\n' \"$*\" >> '{log}'\n"
        "exit 7\n",
        encoding="utf-8",
    )
    (fake_bin / "python").chmod(0o755)
    environment = os.environ.copy()
    environment["PATH"] = f"{fake_bin}{os.pathsep}{environment.get('PATH', '')}"

    result = subprocess.run(
        [str(wrapper), "--check", "guide with spaces.md"],
        cwd=tmp_path,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 7
    assert "guide with spaces.md" in log.read_text(encoding="utf-8")