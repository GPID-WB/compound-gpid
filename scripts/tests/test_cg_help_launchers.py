"""Packaged help smoke: real wrappers, isolated installation, docs-free consumers."""
from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def packaged(tmp_path: Path) -> tuple[Path, Path]:
    """Copy current installation sources, never register a real consumer."""
    install = tmp_path / "installed package with spaces"
    consumer = tmp_path / "consumer with spaces"
    consumer.mkdir()
    (consumer / "compound-gpid.local.md").write_text(
        '---\nsuites: [cg, cr]\n---\n', encoding="utf-8")
    for name in (".github", "docs", "scripts", "bin"):
        shutil.copytree(ROOT / name, install / name,
                        ignore=shutil.ignore_patterns("__pycache__", "tests"))
    return install, consumer


def snapshot(root: Path) -> dict[str, bytes]:
    """Capture all fixture files so query mutation cannot hide in Git ignores."""
    return {p.relative_to(root).as_posix(): p.read_bytes()
            for p in root.rglob("*") if p.is_file()}


def invoke(install: Path, consumer: Path, *args: str,
           env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    """Run the actual packaged wrapper from a consumer without docs or scripts."""
    if os.name == "nt":
        wrapper = install / "bin/cg-help.cmd"
        command = (f'"{os.environ["COMSPEC"]}" /d /s /c "'
                   + subprocess.list2cmdline([str(wrapper), *args]) + '"')
    else:
        wrapper = install / "bin/cg-help"
        command = [str(wrapper), *args]
    return subprocess.run(command, cwd=consumer, env=env, capture_output=True,
                          text=True, timeout=60, check=False)


def test_packaged_help_registration_and_preflight() -> None:
    """Installers register committed wrappers and the existing gate runs help."""
    import cg_pr_preflight

    for name in ("bin/cg-help", "bin/cg-help.cmd"):
        assert (ROOT / name).is_file(), name
    windows = (ROOT / "install.ps1").read_text(encoding="utf-8")
    assert '"bin\\cg-help.cmd"' in windows
    assert "Copy-Item -Path $cgHelpCmdSrc -Destination $cgHelpCmdDst" in windows
    posix = (ROOT / "scripts/install.sh").read_text(encoding="utf-8")
    assert "for cmd in link unlink update kilo skill index" in posix
    assert "test-summary tree-summary help; do" in posix
    assert "scripts/tests/test_cg_help.py" in cg_pr_preflight.NATIVE_PYTEST_FILES
    assert "scripts/tests/test_cg_help_review.py" in cg_pr_preflight.NATIVE_PYTEST_FILES
    assert "scripts/tests/test_cg_help_launchers.py" in cg_pr_preflight.NATIVE_PYTEST_FILES


def test_packaged_catalog_matches_current_sources() -> None:
    """Documentation/source changes must ship a normally refreshed catalog."""
    import help_catalog

    assert json.loads((ROOT / "scripts/help_catalog.json").read_text(
        encoding="utf-8")) == help_catalog.build_catalog(ROOT)


@pytest.mark.skipif(os.name != "nt", reason="Windows installer block fixture")
def test_help_installer_registration_block(tmp_path: Path) -> None:
    """Execute only the committed-copy block; never PATH/profile/registry setup."""
    source = tmp_path / "source installation"
    destination = tmp_path / "destination bin"
    (source / "bin").mkdir(parents=True)
    destination.mkdir()
    expected = (ROOT / "bin/cg-help.cmd").read_bytes()
    (source / "bin/cg-help.cmd").write_bytes(expected)
    script = (ROOT / "install.ps1").read_text(encoding="utf-8")
    block = script.split("# Copy the committed help wrapper,", 1)[1].split(
        "# Copy cg-index.cmd", 1)[0]
    block = block[block.index("$cgHelpCmdSrc"):]
    shell = shutil.which("powershell")
    assert shell is not None
    for bin_dir in (destination, source / "bin"):
        command = ("$ErrorActionPreference='Stop'; "
                   f"$CompoundGpidDir='{source}'; $binDir='{bin_dir}'; " + block)
        result = subprocess.run(
            [shell, "-NoProfile", "-NonInteractive", "-Command", command],
            capture_output=True, text=True, check=False, timeout=30)
        assert result.returncode == 0, result.stdout + result.stderr
        assert (bin_dir / "cg-help.cmd").read_bytes() == expected


@pytest.mark.parametrize("suites", [("cg",), ("cr",), ("cg", "cr")])
def test_shared_help_native_generation(suites: tuple[str, ...]) -> None:
    """Every selection retains shared help across all five mapped adapters."""
    import cg_generate_targets as gen

    assets = gen.scan_canonical_assets(ROOT, active_suites=suites)
    # Copilot uses the canonical prompt directly, not a generated output entry.
    assert any(a["relative_path"] == ".github/prompts/cg-help.prompt.md"
               for a in assets["prompts"])
    assert (ROOT / ".github/prompts/cg-help.prompt.md").is_file()
    plan = gen.build_generation_plan(ROOT, gen.load_target_mapping(ROOT), assets)
    help_entries = [e for e in plan.entries if e.source == ".github/prompts/cg-help.prompt.md"]
    assert {e.target_id for e in help_entries} == {
        "claude-code", "codex", "opencode", "kilo"}
    assert not any("help_catalog" in e.destination for e in plan.entries)
    if len(suites) == 2:
        for entry in help_entries:
            assert (ROOT / entry.destination).read_bytes() == entry.content


def test_packaged_query_citations_and_nonmutation(packaged: tuple[Path, Path]) -> None:
    """A multiword request forwards root/format and cites installation sources."""
    install, consumer = packaged
    before = snapshot(install), snapshot(consumer)
    result = invoke(install, consumer, "query", "compare planning and work",
                    "--root", str(consumer), "--format", "json")
    assert result.returncode == 0, result.stdout + result.stderr
    data = json.loads(result.stdout)
    assert data["state"] == "active"
    assert data["evidence"]
    for row in data["evidence"]:
        lines = (install / row["source"]).read_text(encoding="utf-8").splitlines()
        assert row["body"] == "\n".join(lines[row["start_line"] - 1:row["end_line"]])
    assert not (consumer / "docs").exists()
    assert not (consumer / "scripts").exists()
    assert before == (snapshot(install), snapshot(consumer))


def test_packaged_missing_catalog_and_argument_status(packaged: tuple[Path, Path]) -> None:
    """Forward argparse status 2 and catalog status 1 without wrapper masking."""
    install, consumer = packaged
    invalid = invoke(install, consumer, "query", "install help", "--invalid")
    assert invalid.returncode == 2, invalid.stdout + invalid.stderr
    (install / "scripts/help_catalog.json").unlink()
    before = snapshot(install), snapshot(consumer)
    missing = invoke(install, consumer, "query", "install help", "--root", str(consumer),
                     "--format", "json")
    assert missing.returncode == 1, missing.stdout + missing.stderr
    assert json.loads(missing.stdout)["status"] == "error"
    assert "catalog missing" in json.loads(missing.stdout)["limitation"]
    assert before == (snapshot(install), snapshot(consumer))


@pytest.mark.skipif(os.name != "nt", reason="Windows CMD missing-Python path")
def test_packaged_windows_missing_python(packaged: tuple[Path, Path]) -> None:
    """An empty interpreter PATH fails clearly, not with leaked probe errors."""
    install, consumer = packaged
    env = dict(os.environ, PATH=str(Path(os.environ["SYSTEMROOT"]) / "System32"))
    result = invoke(install, consumer, "query", "install help", env=env)
    assert result.returncode == 1
    assert "Python is not available" in result.stderr
    assert "not recognized" not in result.stderr


@pytest.mark.skipif(os.name != "posix", reason="POSIX launcher missing-Python path")
def test_packaged_posix_missing_python(packaged: tuple[Path, Path]) -> None:
    """Leave dirname available but hide Python from the packaged launcher."""
    install, consumer = packaged
    dirname = shutil.which("dirname")
    assert dirname is not None
    tools = consumer.parent / "tools"
    tools.mkdir()
    (tools / "dirname").symlink_to(dirname)
    result = invoke(install, consumer, "query", "install help", "--root", str(consumer),
                    "--format", "json", env={"PATH": str(tools)})
    assert result.returncode == 1, result.stdout + result.stderr
    assert not result.stdout
    assert "Python is not available" in result.stderr


@pytest.mark.skipif(os.name != "nt", reason="Windows CALL argument expansion")
def test_windows_call_preserves_literal_percent_arguments(packaged: tuple[Path, Path]) -> None:
    """After the caller supplies literal arguments, CALL must not expand them again."""
    install, consumer = packaged
    install = install.rename(install.with_name("installed %CG_HELP_LITERAL% spaces"))
    consumer = consumer.rename(consumer.with_name("consumer %CG_HELP_LITERAL% spaces"))
    args = ["query", "install %CG_HELP_LITERAL%", "--root", str(consumer), "--format", "json"]
    env = dict(os.environ, CG_HELP_LITERAL="/cr-work")
    direct = subprocess.run(
        [sys.executable, "-B", str(install / "scripts/cg_help.py"), *args],
        cwd=consumer, env=env, capture_output=True, text=True, timeout=60, check=False)
    assert direct.returncode == 0 and json.loads(direct.stdout)["state"] == "active"
    caller = install.parent / "literal-caller.cmd"
    # In a batch caller %% supplies a literal %, unlike unescaped cmd /c input.
    caller.write_text("@echo off\n" + subprocess.list2cmdline(
        [str(install / "bin/cg-help.cmd"), *args]).replace("%", "%%") + "\n",
        encoding="utf-8")
    result = subprocess.run(
        [os.environ["COMSPEC"], "/d", "/c", str(caller)], cwd=consumer, env=env,
        capture_output=True, text=True, timeout=60, check=False)
    assert result.returncode == direct.returncode, result.stdout + result.stderr
    assert result.stdout == direct.stdout


@pytest.mark.skipif(os.name != "nt", reason="Windows interpreter CMD shim")
def test_windows_deferred_call_keeps_interpreter_shim_support(
    packaged: tuple[Path, Path],
) -> None:
    """A real-Python CMD shim returns to the launcher with the exact child status."""
    install, consumer = packaged
    fake_bin = install.parent / "interpreter shim"
    fake_bin.mkdir()
    (fake_bin / "python3.cmd").write_text(
        '@echo off\nif "%~1"=="--version" (echo Python 3.12.0& exit /b 0)\n'
        'if "%~1"=="-c" exit /b 0\n'
        f'"{sys.executable}" %*\nexit /b %ERRORLEVEL%\n', encoding="utf-8")
    env = dict(os.environ, PATH=str(fake_bin) + ";" + str(
        Path(os.environ["SYSTEMROOT"]) / "System32"))
    result = invoke(install, consumer, "query", "install help", "--invalid", env=env)
    assert result.returncode == 2, result.stdout + result.stderr
