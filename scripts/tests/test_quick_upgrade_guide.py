"""Execute the upgrade page against GitHub releases, only on disposable CI hosts.

Local pytest checks extraction without running installers or touching User PATH.
Example: python -m pytest scripts/tests/test_quick_upgrade_guide.py -v
"""

from collections.abc import Iterator
import os
from pathlib import Path
import re
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[2]
REPO = "https://github.com/GPID-WB/compound-gpid.git"
HOSTED = (
    os.environ.get("GITHUB_ACTIONS") == "true"
    and os.environ.get("CG_QUICK_GUIDE_RELEASE_TEST") == "1"
)


def _blocks(language: str) -> dict[str, str]:
    """Read each numbered step's native block, e.g. step 4's shared text block."""
    page = (ROOT / "docs/upgrade.md").read_text(encoding="utf-8")
    blocks = {}
    for step in ("1", "2", "3A", "3B", "4", "5", "6"):
        section = re.search(
            rf"^## {step}\. .*?\n(.*?)(?=^## |\Z)", page, re.M | re.S
        )
        assert section, f"Missing guide step {step}"
        fence = "text" if step == "4" else language
        matches = re.findall(
            rf"^```{fence}\n(.*?)^```$", section[1], re.M | re.S
        )
        assert len(matches) == 1, f"Expected one {fence} block in step {step}"
        blocks[step] = matches[0]
    return blocks


@pytest.mark.parametrize("language", ("powershell", "bash"))
def test_numbered_page_blocks_are_extractable(language: str) -> None:
    """Check both published command sets without installs, e.g. in local pytest."""
    blocks = _blocks(language)
    assert blocks["4"].splitlines() == ["cg-link --check", "cg-link"]
    for block in blocks.values():
        executable = "\n".join(
            line.split("#", 1)[0] for line in block.splitlines()
        )
        assert not re.search(r"\bv\d+\.\d+\.\d+", executable)


def _run(args: list[str], env: dict[str, str], cwd: Path) -> str:
    """Run a fixture command and expose its output on failure, e.g. git clone."""
    result = subprocess.run(
        args, env=env, cwd=cwd, text=True, encoding="utf-8", errors="replace",
        capture_output=True, timeout=600, check=False,
    )
    assert result.returncode == 0, (
        f"{args[0]} exited {result.returncode}\n{result.stdout}\n{result.stderr}"
    )
    return result.stdout


def _shell(code: str, env: dict[str, str], cwd: Path, fresh: bool = False) -> str:
    """Use the documented native shell; fresh=True loads installer registration."""
    if sys.platform == "win32":
        preamble = """
$ErrorActionPreference = 'Stop'
$LASTEXITCODE = 0
Set-Variable HOME $env:HOME -Scope Global -Force
$global:PROFILE = Join-Path $env:HOME 'profile.ps1'
"""
        if fresh:
            # A new terminal loads User PATH; preserve setup-python's process PATH.
            preamble += """
$env:PATH = [Environment]::GetEnvironmentVariable('Path', 'Machine') + ';' +
    [Environment]::GetEnvironmentVariable('Path', 'User') + ';' + $env:PATH
"""
        # The one allowed command substitution: the default installation path.
        code = code.replace(r"C:\WBG\.compound-gpid", r"$HOME\.compound-gpid")
        return _run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-ExecutionPolicy",
             "Bypass", "-Command", preamble + code + "\nexit $LASTEXITCODE"],
            env, cwd,
        )
    preamble = 'set -e\n'
    if fresh:
        preamble += 'source "$HOME/.bashrc"\n'
    return _run(["bash", "-c", preamble + code], env, cwd)


@pytest.fixture(scope="module")
def published_tag() -> str:
    """Choose independently from actual GitHub releases, e.g. v1.2.0.9025 today."""
    if not HOSTED:
        pytest.skip("Published-release installs require the disposable hosted job")
    assert sys.platform in ("win32", "darwin")
    tags = _run(
        ["gh", "api", "--paginate", "repos/GPID-WB/compound-gpid/releases",
         "--jq", ".[] | select(.draft == false) | .tag_name"],
        dict(os.environ), ROOT,
    ).splitlines()
    versions = {
        tag: tuple(map(int, tag[1:].split("."))) for tag in tags
        if re.fullmatch(r"v\d+\.\d+\.\d+(?:\.\d+)?", tag)
    }
    assert versions, "No published numeric releases found"
    newest = max(versions, key=versions.get)
    stable = ".".join(newest.split(".")[:3])
    return stable if stable in versions else newest


@pytest.fixture
def home(tmp_path: Path, published_tag: str) -> Iterator[dict[str, str]]:
    """Isolate profiles, Git and caches; never qualify installs on a local account."""
    env = {
        key: value for key, value in os.environ.items()
        if not key.upper().startswith(("CG_", "KILO_", "GIT_"))
    }
    env.update(HOME=str(tmp_path), USERPROFILE=str(tmp_path), SHELL="/bin/bash")
    for key in ("APPDATA", "LOCALAPPDATA", "XDG_CONFIG_HOME", "XDG_CACHE_HOME",
                "XDG_DATA_HOME", "XDG_STATE_HOME", "ZDOTDIR", "TEMP", "TMP",
                "TMPDIR"):
        path = tmp_path / key.lower()
        path.mkdir()
        env[key] = str(path)
    env.update(
        GIT_CONFIG_GLOBAL=str(tmp_path / "gitconfig"), GIT_CONFIG_NOSYSTEM="1",
        GIT_TERMINAL_PROMPT="0", PYTHONDONTWRITEBYTECODE="1",
    )
    (tmp_path / ".bash_profile").write_text(
        '[ -f "$HOME/.bashrc" ] && source "$HOME/.bashrc"\n', encoding="utf-8"
    )
    if sys.platform != "win32":
        yield env
        return

    # Children recompute $PROFILE from Documents, not from USERPROFILE alone.
    # This fixture is gated on disposable hosted CI before any registry writes.
    import winreg

    documents = tmp_path / "Documents"
    documents.mkdir()
    saved = []
    try:
        for folder in ("User Shell Folders", "Shell Folders"):
            key_path = rf"Software\Microsoft\Windows\CurrentVersion\Explorer\{folder}"
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER, key_path, 0,
                winreg.KEY_READ | winreg.KEY_SET_VALUE,
            ) as key:
                try:
                    original = winreg.QueryValueEx(key, "Personal")
                except FileNotFoundError:
                    original = None
                saved.append((key_path, original))
                winreg.SetValueEx(key, "Personal", 0, winreg.REG_SZ, str(documents))
        resolved = _shell(
            "[Environment]::GetFolderPath('MyDocuments')", env, tmp_path
        ).strip()
        assert Path(resolved) == documents
        yield env
    finally:
        for key_path, original in reversed(saved):
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE
            ) as key:
                if original is None:
                    winreg.DeleteValue(key, "Personal")
                else:
                    value, kind = original
                    winreg.SetValueEx(key, "Personal", 0, kind, value)


def _assert_pin(install: Path, tag: str, env: dict[str, str]) -> None:
    """Check the chosen tag and on-disk pin, e.g. after step 3B."""
    assert (install / ".cg-version").read_text(encoding="utf-8-sig").strip() == tag
    assert _run(
        ["git", "describe", "--tags", "--exact-match"], env, install
    ).strip() == tag


def _link_and_remove(blocks: dict[str, str], env: dict[str, str]) -> None:
    """Run page steps 4 and 6, checking project output and complete removal."""
    home = Path(env["HOME"])
    install = home / ".compound-gpid"
    project = home / "project"
    project.mkdir()
    _run(["git", "init", str(project)], env, home)
    # Blank fixture accepts the defaults, without invoking an editor or Kilo.
    for command in blocks["4"].splitlines():
        _shell(command, env, project, fresh=True)
    assert (project / ".github/prompts/cg-review.prompt.md").is_file()
    assert (project / ".kilo/commands/cg-review.md").is_file()
    if sys.platform == "win32":
        registered = _shell(
            "[Environment]::GetEnvironmentVariable('Path', 'User')", env, home
        )
        assert str(install / "bin").lower() in registered.lower()
    else:
        assert "# --- Compound GPID ---" in (home / ".bashrc").read_text()
    _shell(blocks["6"], env, home, fresh=True)
    assert not install.exists()
    assert not list(home.glob(".compound-gpid.backup-*"))
    if sys.platform == "win32":
        registered = _shell(
            "[Environment]::GetEnvironmentVariable('Path', 'User')", env, home
        )
        assert str(install / "bin").lower() not in registered.lower()
    else:
        assert "Compound GPID" not in (home / ".bashrc").read_text()


@pytest.mark.parametrize("old_tag,step", (("v1.1.11", "3A"), ("v1.2.0.9024", "3B")))
def test_published_upgrade(
    old_tag: str, step: str, home: dict[str, str], published_tag: str,
) -> None:
    """Install a real old release, then execute its documented upgrade path."""
    root = Path(home["HOME"])
    install = root / ".compound-gpid"
    _run(["git", "clone", "--branch", old_tag, REPO, str(install)], home, root)
    (install / ".cg-version").write_text(old_tag + "\n", encoding="ascii")
    windows = sys.platform == "win32"
    _shell(
        '& "$HOME/.compound-gpid/install.ps1"' if windows else
        'bash "$HOME/.compound-gpid/scripts/install.sh"', home, root,
    )
    blocks = _blocks("powershell" if windows else "bash")
    checked = _shell(blocks["2"], home, root)
    assert old_tag in checked
    output = _shell(blocks["1"] + blocks[step], home, root, fresh=True)
    if step == "3A":
        assert "Migrated:" in output
        assert list(root.glob(".compound-gpid.backup-*"))
    _assert_pin(install, published_tag, home)
    _link_and_remove(blocks, home)


def test_published_fresh_install_then_remove(
    home: dict[str, str], published_tag: str,
) -> None:
    """Execute steps 1, 5, 4 and 6, including removal of a fixture backup."""
    root = Path(home["HOME"])
    blocks = _blocks("powershell" if sys.platform == "win32" else "bash")
    _shell(blocks["1"] + blocks["5"], home, root)
    install = root / ".compound-gpid"
    assert install.is_dir()
    _assert_pin(install, published_tag, home)
    backup = root / ".compound-gpid.backup-fixture"
    backup.mkdir()
    (backup / "sentinel").write_text("backup to remove\n", encoding="ascii")
    _link_and_remove(blocks, home)
