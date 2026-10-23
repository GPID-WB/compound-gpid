"""Committed POSIX modes and fixture-only clean-clone installation checks."""
from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


def _git(root: Path, *args: str, env: dict[str, str] | None = None) -> str:
    """Run bounded Git in a fixture or read the source index, e.g. ls-files."""
    return subprocess.run(
        ["git", "-C", str(root), *args], env=env, check=True,
        capture_output=True, text=True, timeout=120,
    ).stdout


def test_posix_entrypoints_have_executable_git_modes() -> None:
    """All tracked bin/cg-* POSIX wrappers and scripts/*.sh use mode 100755."""
    entries = _git(REPO_ROOT, "ls-files", "-s", "-z", "bin/", "scripts/")
    checked = []
    for entry in entries.split("\0"):
        if not entry:
            continue
        metadata, name = entry.split("\t", 1)
        path = Path(name)
        if (path.parent == Path("bin") and path.name.startswith("cg-")
                and not path.suffix) or (
                path.parent == Path("scripts") and path.suffix == ".sh"):
            assert metadata.split()[0] == "100755", entry
            checked.append(name)
    assert "bin/cg-brain-init" in checked
    assert "scripts/install.sh" in checked


@pytest.mark.skipif(os.name == "nt", reason="POSIX install requires macOS or Linux")
@pytest.mark.parametrize("profile", ("bash", "zsh"))
def test_install_keeps_clone_clean_and_wrappers_work_elsewhere(
    tmp_path: Path, profile: str,
) -> None:
    """Install twice in a disposable clone and run help through PATH and links."""
    bash = shutil.which("bash")
    assert bash is not None, "POSIX installation requires Bash"
    home, other, links = (tmp_path / name for name in ("home", "other", "links"))
    for directory in (home, other, links):
        directory.mkdir()
    rc_files = {name: home / f".{name}rc" for name in ("bash", "zsh")}
    for rc in rc_files.values():
        rc.write_text("# fixture shell configuration\n", encoding="utf-8")
    env = {key: value for key, value in os.environ.items()
           if not key.upper().startswith(("CG_", "KILO_", "GIT_", "PYTHON"))
           and key.upper() not in ("BASH_ENV", "ENV")}
    for name in ("HOME", "USERPROFILE", "APPDATA", "LOCALAPPDATA", "XDG_CONFIG_HOME"):
        env[name] = str(home)
    env.update(
        SHELL=f"/bin/{profile}", TMPDIR=str(tmp_path),
        GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1",
        GIT_TERMINAL_PROMPT="0", PYTHONDONTWRITEBYTECODE="1",
    )
    clone = tmp_path / "installation"
    _git(tmp_path, "clone", "--no-local", str(REPO_ROOT), str(clone), env=env)
    alias = tmp_path / "installation alias"
    alias.symlink_to(clone, target_is_directory=True)
    wrappers = [name for name in _git(clone, "ls-files", "bin/", env=env).splitlines()
                if not Path(name).suffix]
    before = {name: (clone / name).read_bytes() for name in wrappers}
    # Old or local wrapper names alone do not grant the installer ownership.
    unowned = ("cg-find-skill", "cg-find-skill.cmd", "cg-local-custom")
    exclude = clone / ".git/info/exclude"
    with exclude.open("a", encoding="utf-8") as handle:
        handle.write("\n" + "\n".join(f"/bin/{name}" for name in unowned) + "\n")
    for name in unowned:
        wrapper = clone / "bin" / name
        wrapper.write_bytes(b"fixture user wrapper\n")
        wrapper.chmod(0o640)
    assert _git(clone, "status", "--porcelain", env=env) == ""

    for _ in range(2):
        result = subprocess.run(
            [bash, str(alias / "scripts/install.sh")], cwd=other, env=env,
            capture_output=True, text=True, timeout=60, check=False,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        assert _git(clone, "status", "--porcelain", env=env) == ""
        assert {name: (clone / name).read_bytes() for name in wrappers} == before
        assert all(os.access(clone / name, os.X_OK) for name in wrappers)
        for name in unowned:
            wrapper = clone / "bin" / name
            assert wrapper.read_bytes() == b"fixture user wrapper\n"
            assert wrapper.stat().st_mode & 0o777 == 0o640
    rc = rc_files[profile]
    assert rc.read_text(encoding="utf-8").count("# --- Compound GPID ---") == 1
    assert rc_files["zsh" if profile == "bash" else "bash"].read_text(
        encoding="utf-8") == "# fixture shell configuration\n"
    relative_link = links / "cg-index-relative"
    relative_link.symlink_to("../installation alias/bin/cg-index")
    absolute_link = links / "cg-index-absolute"
    absolute_link.symlink_to(relative_link)
    for command in (
        [bash, "--noprofile", "--norc", "-c", '. "$1"; cg-index --help', "fixture", str(rc)],
        [str(relative_link), "--help"],
        [str(absolute_link), "--help"],
        [str(alias / "bin/cg-brain-init"), "--help"],
    ):
        result = subprocess.run(
            command, cwd=other, env=env, capture_output=True, text=True,
            timeout=30, check=False,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        assert "usage:" in result.stdout.lower()
    assert _git(clone, "status", "--porcelain", env=env) == ""
