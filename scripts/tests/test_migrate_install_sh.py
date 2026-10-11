"""POSIX migration with disposable Git clones and fake HOME, never old code."""
from __future__ import annotations

import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys

import pytest

from scripts.tests.test_rebuild_migration import MIGRATION_TAG, OLD, PIN, ROOT, Runtime, _git, _state, _write

pytestmark = pytest.mark.skipif(
    not (sys.platform.startswith("linux") or sys.platform == "darwin"),
    reason="POSIX migration requires native macOS or Linux; Windows/Git Bash is not proof",
)


@pytest.fixture
def posix_migration(tmp_path: Path) -> tuple[Runtime, Path, Path]:
    """Build a fake old install and exact NEW tag, e.g. for failure restoration."""
    root = tmp_path.resolve()
    home = root / "home"
    home.mkdir()
    env = {key: value for key, value in os.environ.items()
           if not key.upper().startswith(("CG_", "KILO_", "GIT_", "PYTHON", "RM_"))
           and key not in ("BASH_ENV", "ENV", "ZDOTDIR")}
    env.update(HOME=str(home), USERPROFILE=str(home), ZDOTDIR=str(home),
               SHELL="/bin/bash", PATH="/usr/bin:/bin:/usr/sbin:/sbin",
               GIT_CONFIG_GLOBAL=str(root / "gitconfig"), GIT_CONFIG_NOSYSTEM="1",
               GIT_ALLOW_PROTOCOL="file", GIT_TERMINAL_PROMPT="0",
               PYTHONDONTWRITEBYTECODE="1", POSIX_FAILURE="",
               POSIX_LOG=str(root / "installer.log"))
    _write(root / "gitconfig", b"")
    git = shutil.which("git")
    assert git is not None
    rt = Runtime(root, env, ["/bin/bash"], git, "sh")
    seed, remote, new = (root / name for name in ("seed", "official.git", "new"))
    install = home / ".compound-gpid"
    seed.mkdir()
    _git(rt, seed, "init")
    for key, value in (("user.name", "Fixture"), ("user.email", "fixture@example.invalid"),
                       ("commit.gpgsign", "false"), ("core.autocrlf", "false")):
        _git(rt, seed, "config", key, value)
    _write(seed / ".gitignore", ".cg-version\n")
    _write(seed / "package.txt", "old package\n")
    for name in ("install", "link", "unlink", "update"):
        _write(seed / f"scripts/{name}.sh", "echo 'OLD CODE MUST NEVER RUN' >&2; exit 71\n")
    for name in ("link", "unlink", "update"):
        _write(seed / f"bin/cg-{name}", "#!/bin/bash\necho 'OLD CODE MUST NEVER RUN' >&2\nexit 71\n")
        (seed / f"bin/cg-{name}").chmod(0o755)
    _git(rt, seed, "add", "-A")
    _git(rt, seed, "update-index", "--chmod=+x", "bin/cg-link", "bin/cg-unlink", "bin/cg-update")
    _git(rt, seed, "commit", "-m", "fixture old install")
    _git(rt, seed, "tag", OLD)
    _write(seed / "scripts/migrate-install.sh", (ROOT / "scripts/migrate-install.sh").read_bytes())
    (seed / "scripts/migrate-install.sh").chmod(0o755)
    _write(seed / "package.txt", "new package\n")
    _write(seed / "scripts/install.sh", '''#!/bin/bash
set -eu
root=$(cd "$(dirname "$0")/.." && pwd -P)
test "$(cat "$root/.cg-version")" = v1.2.0.9024
printf '%s' "$root" > "$POSIX_LOG"
test "$POSIX_FAILURE" != install || exit 23
rc="$HOME/.${SHELL##*/}rc"
printf '\\n# --- Compound GPID ---\\nexport PATH="%s/bin:$PATH"\\n# --- End Compound GPID ---\\n' "$root" >> "$rc"
case "$POSIX_FAILURE" in
    dirty) printf 'changed' > "$root/package.txt" ;;
    wrapper) chmod -x "$root/bin/cg-update" ;;
    path) printf 'export PATH="%s:$PATH"\\n' "$POSIX_SHADOW" >> "$rc" ;;
esac
''')
    _git(rt, seed, "add", "-A")
    _git(rt, seed, "update-index", "--chmod=+x", "scripts/migrate-install.sh")
    _git(rt, seed, "commit", "-m", "fixture new release")
    _git(rt, seed, "tag", MIGRATION_TAG)
    _git(rt, root, "clone", "--bare", seed.as_uri(), str(remote))
    # The official URL is redirected only inside this disposable Git environment.
    env.update(GIT_CONFIG_COUNT="2", GIT_CONFIG_KEY_0=f"url.{remote.as_uri()}.insteadOf",
               GIT_CONFIG_VALUE_0="https://github.com/GPID-WB/compound-gpid.git",
               GIT_CONFIG_KEY_1="core.autocrlf", GIT_CONFIG_VALUE_1="false")
    for target, tag in ((new, MIGRATION_TAG), (install, OLD)):
        _git(rt, root, "clone", "--no-local", "--branch", tag, remote.as_uri(), str(target))
    _write(home / ".bash_profile", f'export PATH={shlex.quote(env["PATH"])}\n. "$HOME/.bashrc"\n')
    for rc in (".bashrc", ".zshrc"):
        _write(home / rc, "# private fixture rc\n")
    assert (new / "scripts/migrate-install.sh").read_bytes() == (ROOT / "scripts/migrate-install.sh").read_bytes()
    return rt, new, install


def migrate(fixture: tuple[Runtime, Path, Path], *args: str) -> subprocess.CompletedProcess[str]:
    """Run exact NEW bytes, e.g. with a custom target and synthetic installer."""
    rt, new, _ = fixture
    result = subprocess.run(["/bin/bash", str(new / "scripts/migrate-install.sh"), *args],
                            cwd=rt.root, env=rt.env, capture_output=True, text=True,
                            encoding="utf-8", timeout=90, check=False)
    assert "OLD CODE MUST NEVER RUN" not in result.stdout + result.stderr
    return result


@pytest.mark.parametrize("selection", ("default", "path", "custom", "accented", "dirty", "explicit-two", "zsh", "bashrc", "zshrc"))
def test_posix_migration_preserves_old_clone_and_pins_new(posix_migration, selection: str) -> None:
    """Discovery preserves tracked/index/untracked bytes and executes only NEW install."""
    rt, new, install = posix_migration
    args = []
    if selection in ("path", "custom", "accented", "bashrc", "zshrc"):
        target = rt.root / ("ni\u00f1o install" if selection == "accented" else "custom install")
        install.rename(target)
        install = target
        if selection == "path":
            rt.env["PATH"] = str(install / "bin") + ":" + rt.env["PATH"]
        elif selection.endswith("rc"):
            _write(Path(rt.env["HOME"]) / ("." + selection),
                   f'# --- Compound GPID ---\nexport PATH="{install}/bin:$PATH"\n# --- End Compound GPID ---\n')
        else:
            args = ["--install-path", str(install)]
        if selection == "accented":
            accented = rt.root / "ni\u00f1o new clone"
            new.rename(accented)
            new = accented
    if selection == "zsh":
        shell = shutil.which("zsh")
        if shell is None:
            pytest.skip("Native zsh is unavailable; Bash cases still run")
        rt.env["SHELL"] = shell
    if selection == "explicit-two":
        other = rt.root / "other install"
        _git(rt, rt.root, "clone", "--branch", OLD, str(rt.root / "official.git"), str(other))
        rt.env["PATH"] = str(other / "bin") + ":" + rt.env["PATH"]
        args = ["--install-path", str(install)]
    _write(install / ".cg-version", PIN)
    if selection == "dirty":
        _write(install / "package.txt", "user staged changes\n")
        _git(rt, install, "add", "package.txt")
        _write(install / "bin/cg-update", "user dirty tracked wrapper\n")
        _write(install / "untracked.txt", b"private\x00bytes")
    before = {p.relative_to(install): p.read_bytes() for p in install.rglob("*")
              if p.is_file() and ".git" not in p.relative_to(install).parts}
    state, index = _state(rt, install), _git(rt, install, "diff", "--cached", "--binary")
    result = migrate((rt, new, install), *args)
    assert result.returncode == 0, result.stdout + result.stderr
    backup = next(install.parent.glob(install.name + ".backup-*"))
    assert all((backup / path).read_bytes() == data for path, data in before.items())
    assert _state(rt, backup) == state and _git(rt, backup, "diff", "--cached", "--binary") == index
    assert _git(rt, install, "rev-parse", "HEAD") == _git(rt, new, "rev-parse", "HEAD")
    assert (install / ".cg-version").read_bytes() == MIGRATION_TAG.encode()
    assert not _git(rt, install, "status", "--porcelain")
    assert not _git(rt, new, "status", "--porcelain")
    assert _git(rt, install, "remote", "get-url", "origin").decode().strip() == (rt.root / "official.git").as_uri()
    assert "https://github.com/GPID-WB/compound-gpid.git" in (install / ".git/config").read_text()
    assert not (install / ".git/objects/info/alternates").exists()
    assert Path(rt.env["POSIX_LOG"]).read_text() == str(install)
    assert "Old HEAD:" in result.stdout and "Old .cg-version:" in result.stdout
    assert "manual action required" in result.stdout and "--rollback" in result.stdout
    repeat = migrate((rt, new, install), "--install-path", str(install))
    assert repeat.returncode != 0 and "Existing backup found" in repeat.stderr


@pytest.mark.parametrize("failure", ("install", "dirty", "wrapper", "path", "remote-tag", "login-profile"))
def test_posix_migration_failure_restores_old_folder(posix_migration, failure: str) -> None:
    """Installer/tag/wrapper/login failures restore old HEAD, pin and private bytes."""
    rt, _, install = posix_migration
    _write(install / ".cg-version", PIN)
    _write(install / "private.txt", b"preserved private bytes")
    before = _state(rt, install)
    rt.env["POSIX_FAILURE"] = failure
    if failure == "path":
        shadow = rt.root / "shadow"
        _write(shadow / "cg-update", "#!/bin/bash\nexit 72\n")
        (shadow / "cg-update").chmod(0o755)
        rt.env["POSIX_SHADOW"] = str(shadow)
    if failure == "remote-tag":
        _git(rt, rt.root, "--git-dir", str(rt.root / "official.git"), "update-ref",
             "refs/tags/" + MIGRATION_TAG, before[0].decode().strip())
    if failure == "login-profile":
        _write(Path(rt.env["HOME"]) / ".bash_profile", 'export PATH="/usr/bin:/bin"\n')
    result = migrate(posix_migration)
    assert result.returncode != 0 and "Old folder restored" in result.stderr
    assert _state(rt, install) == before
    assert (install / "private.txt").read_bytes() == b"preserved private bytes"
    assert not list(install.parent.glob(install.name + ".backup-*"))


@pytest.mark.parametrize("case", ("two", "symlink", "worktree", "non-clone", "overlap", "nested", "dirty-source", "untagged", "nonnumeric", "zero", "unknown-option"))
def test_posix_migration_refuses_unsafe_or_ambiguous_state(posix_migration, case: str) -> None:
    """Unsafe targets and sources stop before installer execution or any old move."""
    rt, new, install = posix_migration
    args = []
    before = _state(rt, install)
    if case == "two":
        other = rt.root / "other install"
        _git(rt, rt.root, "clone", "--branch", OLD, str(rt.root / "official.git"), str(other))
        rt.env["PATH"] = str(other / "bin") + ":" + rt.env["PATH"]
    elif case in ("symlink", "worktree", "non-clone"):
        target = rt.root / case
        if case == "symlink":
            target.symlink_to(install, target_is_directory=True)
        elif case == "worktree":
            _git(rt, install, "worktree", "add", "--detach", str(target), OLD)
        else:
            target.mkdir()
        args = ["--install-path", str(target)]
    elif case in ("overlap", "nested"):
        args = ["--install-path", str(new if case == "overlap" else new / "bin")]
    elif case == "dirty-source":
        _write(new / "private.txt", "dirty source\n")
    elif case in ("untagged", "nonnumeric"):
        _git(rt, new, "tag", "-d", MIGRATION_TAG)
        if case == "nonnumeric":
            _git(rt, new, "tag", "v1.2.0-beta")
    elif case == "zero":
        install.rename(rt.root / "not-an-install")
    elif case == "unknown-option":
        args = ["--unknown"]
    rc_before = {rc: (Path(rt.env["HOME"]) / rc).read_bytes() for rc in (".bashrc", ".zshrc")}
    result = migrate(posix_migration, *args)
    assert result.returncode != 0 and result.stderr
    assert not Path(rt.env["POSIX_LOG"]).exists()
    assert rc_before == {rc: (Path(rt.env["HOME"]) / rc).read_bytes() for rc in rc_before}
    if case != "zero":
        assert _state(rt, install) == before
    assert not list(install.parent.glob(install.name + ".backup-*"))
    if case == "two":
        assert "Multiple installations" in result.stderr
    if case == "zero":
        assert "normal NEW scripts/install.sh" in result.stderr


@pytest.mark.parametrize("registration", ("path", "bashrc", "zshrc"))
@pytest.mark.parametrize("current", ("missing", "partial"))
def test_posix_migration_interruption_prints_exact_recovery(posix_migration, registration: str, current: str) -> None:
    """Raw PATH and owned rc text find backups even when wrappers are missing."""
    rt, new, install = posix_migration
    target = rt.root / "ni\u00f1o interrupted install"
    backup = target.with_name(target.name + ".backup-v1.2.0.9021-20261010-120000")
    install.rename(backup)
    if registration == "path":
        rt.env["PATH"] = str(target / "bin") + ":" + rt.env["PATH"]
    else:
        _write(Path(rt.env["HOME"]) / ("." + registration),
               f'# --- Compound GPID ---\nexport PATH="{target}/bin:$PATH"\n# --- End Compound GPID ---\n')
    if current == "partial":
        _write(target / "partial.txt", b"preserve partial clone")
    before = _state(rt, backup)
    result = migrate(posix_migration)
    assert result.returncode != 0 and "Existing backup found" in result.stderr
    # Bash 3.2 can use ANSI-C UTF-8 quoting, which Python shlex cannot decode.
    quoted = subprocess.run(
        ["/bin/bash", "-c", "printf '  bash %q --install-path %q --rollback %q\\n' \"$1\" \"$2\" \"$3\"; "
         "printf '  bash %q --install-path %q\\n' \"$1\" \"$2\"", "fixture",
         str(new / "scripts/migrate-install.sh"), str(target), str(backup)],
        env=rt.env, capture_output=True, text=True, encoding="utf-8", timeout=10, check=True,
    )
    assert all(command in result.stdout.splitlines() for command in quoted.stdout.splitlines())
    assert "To resume: roll back first" in result.stdout and _state(rt, backup) == before
    assert not Path(rt.env["POSIX_LOG"]).exists()
    if current == "partial":
        assert (target / "partial.txt").read_bytes() == b"preserve partial clone"
    else:
        assert not target.exists()


@pytest.mark.parametrize("current", ("migrated", "missing", "partial"))
def test_posix_migration_rollback_keeps_current_folder(posix_migration, current: str) -> None:
    """Explicit rollback restores the exact target and retains later edits aside."""
    rt, _, install = posix_migration
    _write(install / ".cg-version", PIN)
    before = _state(rt, install)
    if current == "migrated":
        result = migrate(posix_migration)
        assert result.returncode == 0, result.stdout + result.stderr
        backup = next(install.parent.glob(install.name + ".backup-*"))
    else:
        backup = install.with_name(install.name + ".backup-v1.2.0.9021-20261010-120000")
        install.rename(backup)
    if current != "missing":
        _write(install / "later.txt", b"preserve later edits")
    result = migrate(posix_migration, "--install-path", str(install), "--rollback", str(backup))
    assert result.returncode == 0, result.stdout + result.stderr
    assert _state(rt, install) == before and not backup.exists()
    asides = list(install.parent.glob(install.name + ".rollback-*"))
    assert len(asides) == (0 if current == "missing" else 1)
    if asides:
        assert (asides[0] / "later.txt").read_bytes() == b"preserve later edits"


def test_posix_migration_rollback_requires_install_path_and_safe_version(posix_migration) -> None:
    """Unusual describe text makes a safe backup; omitted/mismatched targets refuse."""
    rt, _, install = posix_migration
    unusual = "v1.2.0.pi\u00f1ata+.BaCkUp-r\u00e9sum\u00e9"
    _git(rt, install, "tag", "-d", OLD)
    _git(rt, install, "tag", unusual)
    _write(install / "package.txt", "preserve tracked changes\n")
    before = _state(rt, install)
    result = migrate(posix_migration)
    assert result.returncode == 0, result.stdout + result.stderr
    assert f"Old describe: {unusual}-dirty" in result.stdout
    backup = next(install.parent.glob(install.name + ".backup-*"))
    suffix = backup.name.removeprefix(install.name + ".backup-")
    match = re.fullmatch(r"([A-Za-z0-9._-]+)-(\d{8}-\d{6})", suffix)
    assert match is not None and "backup" not in match[1].casefold()
    for args, message in ((["--rollback", str(backup)], "--rollback requires --install-path"),
                          (["--install-path", str(rt.root / "wrong"), "--rollback", str(backup)], "exact target and sibling")):
        result = migrate(posix_migration, *args)
        assert result.returncode != 0 and message in result.stderr
        assert _state(rt, backup) == before
    result = migrate(posix_migration, "--install-path", str(install), "--rollback", str(backup))
    assert result.returncode == 0, result.stdout + result.stderr
    assert _state(rt, install) == before
