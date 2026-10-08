"""Real-Git acquisition and rollback; no real install, profiles, registry or Kilo.

Windows executes only the EXACT wrapper mutation block from
v1.2.0.9021:install.ps1:248-252, NOT a full installer qualification.
Linux executes the full committed POSIX installer; Git Bash is not POSIX proof.
"""
from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
import io
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import tarfile
import tempfile

import pytest

ROOT = Path(__file__).resolve().parents[2]
OLD, TARGET = "v1.2.0.9021", "v1.2.0.9022"
PIN = b"\xef\xbb\xbf \tlatest\r\n\r\nfixture trailing bytes\x00"
REQUIRED = ("link.ps1 link.sh update.ps1 update.sh helpers.ps1 cg_generate_targets.py "
            "cg_project_manifest.py cg_project_projection.py cg_kilo_preflight.py "
            "cg_kilo_copy.py cg_migrate_research_layout.py research_layout.py "
            "secure_fs.py").split()
POSIX_DIRTY = {f"bin/cg-{name}" for name in (
    "link", "unlink", "update", "index", "brain-init", "token-audit",
    "autopilot-control", "help", "diff-summary", "log-summary",
    "problems-summary", "test-summary", "tree-summary")}
CMD_PROBE_CHANGES = {f"bin/cg-{name}.cmd" for name in (
    "skill", "kilo", "index", "brain-init", "render-artifact", "token-audit")}
POSIX_WRAPPER_CHANGES = {f"bin/cg-{name}" for name in (
    "brain-init", "diff-summary", "index", "kilo", "link", "log-summary",
    "problems-summary", "publish-markdown", "render-artifact", "skill",
    "test-summary", "token-audit", "tree-summary", "unlink", "update")}
WORKER = '''
import os, subprocess, sys
from pathlib import Path
root = Path(__file__).resolve().parents[1]
name = Path(__file__).name
pin = root / '.cg-version'
mode = os.environ.get('RM_MODE', '')
head = subprocess.check_output([os.environ['RM_GIT'], 'rev-parse', 'HEAD'], cwd=root).decode().strip()
assert head == os.environ['RM_TARGET'], head
with open(os.environ['RM_LOG'], 'a', encoding='utf-8') as log:
    log.write(name + '\\n')
if name == 'cg_generate_targets.py':
    assert sys.argv[1:] == ['--root', str(root), '--all', '--dry-run'], sys.argv
    before = pin.read_bytes().hex() if pin.exists() else 'absent'
    assert before == os.environ['RM_PIN'], 'pin written before validation'
    if mode == 'head':
        subprocess.check_call([os.environ['RM_GIT'], 'checkout', '--detach', os.environ['RM_MOVED']], cwd=root)
    if mode in ('generator', 'head'):
        sys.stderr.write('fixture generator failed\\n')
        raise SystemExit(23)
elif mode in ('downstream', 'rollback-after'):
    assert pin.read_bytes().strip().decode() == 'v1.2.0.9022', 'failure must be AFTER pin'
    sys.stderr.write('fixture post-pin retirement failed\\n')
    raise SystemExit(24)
'''


def _write(path: Path, data: str | bytes) -> None:
    """Write disposable bytes, e.g. a synthetic target worker."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data.encode() if isinstance(data, str) else data)


@dataclass
class Runtime:
    """One restricted process environment, e.g. a Windows clone fixture."""

    root: Path
    env: dict[str, str]
    command: list[str]
    git: str
    suffix: str


def _git(rt: Runtime, cwd: Path, *args: str) -> bytes:
    """Run real Git, e.g. checkout ONLY inside a disposable clone."""
    result = subprocess.run([rt.git, *args], cwd=cwd, env=rt.env,
                            capture_output=True, timeout=60, check=False)
    assert result.returncode == 0, result.stderr.decode(errors="replace")
    return result.stdout


@pytest.fixture(params=("ps1", "sh"))
def runtime(request: pytest.FixtureRequest) -> Iterator[Runtime]:
    """Supply fake HOME/profile and file-only Git, e.g. for pinned rollback."""
    windows = request.param == "ps1"
    if windows and os.name != "nt":
        pytest.skip("Windows PowerShell runtime requires Windows")
    if not windows and not sys.platform.startswith("linux"):
        pytest.skip("Bash runtime is Linux-only, not Git Bash or macOS proof")
    shell, git = shutil.which("powershell.exe" if windows else "bash"), shutil.which("git")
    if not shell or not git:
        pytest.skip("Required shell or real Git is unavailable")
    if windows and Path(git).parent.parent.name == "mingw64":
        # Git Bash exposes the internal binary; cmd/git.exe sets its DLL paths.
        git = str(Path(git).parents[2] / "cmd/git.exe")
        assert Path(git).is_file(), git
    with tempfile.TemporaryDirectory(prefix="rm-") as temporary:
        root = Path(temporary).resolve()
        env = {k: v for k, v in os.environ.items()
               if not k.upper().startswith(("CG_", "KILO_", "GIT_", "PYTHON", "RM_"))
               and k.upper() not in ("BASH_ENV", "ENV", "PSMODULEPATH", "PATH")}
        for name in ("HOME", "USERPROFILE", "APPDATA", "LOCALAPPDATA",
                     "XDG_CONFIG_HOME", "XDG_DATA_HOME", "XDG_CACHE_HOME", "XDG_STATE_HOME"):
            path = root / name.lower()
            path.mkdir()
            env[name] = str(path)
        for name in ("bin", "temp", "empty", "consumer"):
            (root / name).mkdir()
        _write(root / "profile.ps1", "# private fixture profile\n")
        _write(root / "empty-config", b"")
        env.update(PROFILE=str(root / "profile.ps1"), TEMP=str(root / "temp"),
                   TMP=str(root / "temp"), TMPDIR=str(root / "temp"), SHELL=shell,
                   GIT_CONFIG_GLOBAL=str(root / "empty-config"),
                   GIT_CONFIG_SYSTEM=str(root / "empty-config"), GIT_CONFIG_NOSYSTEM="1",
                   GIT_TEMPLATE_DIR=str(root / "empty"), GIT_ALLOW_PROTOCOL="file",
                   GIT_TERMINAL_PROMPT="0", CG_INTERNAL_CALL="1", LC_ALL="C",
                   PYTHONDONTWRITEBYTECODE="1", PYTEST_DISABLE_PLUGIN_AUTOLOAD="1",
                   RM_GIT=git, RM_LOG=str(root / "events"))
        configs = {"core.hooksPath": str(root / "empty"), "core.autocrlf": "false",
                   "core.longpaths": "true", "user.name": "Fixture",
                   "user.email": "fixture@example.invalid", "commit.gpgsign": "false",
                   "init.defaultBranch": "main", "protocol.file.allow": "always"}
        env["GIT_CONFIG_COUNT"] = str(len(configs))
        for i, (key, value) in enumerate(configs.items()):
            env[f"GIT_CONFIG_KEY_{i}"], env[f"GIT_CONFIG_VALUE_{i}"] = key, value
        if windows:
            # Only Git's directory is exposed to helper subprocesses, never System32.
            env["PATH"] = str(Path(git).parent)
            python = sys.executable.replace("'", "''")
            _write(root / "invoke.ps1", f'''
param([string]$Script, [string]$Version)
$global:PROFILE = $env:PROFILE
Set-Variable -Name HOME -Scope Global -Value $env:HOME -Force
Set-Alias -Name python3 -Scope Global -Value '{python}'
# Native-failure simulation AFTER real checkout, never an installed Git hook.
function global:git {{
    $ErrorActionPreference = 'Continue'
    if ($args[0] -eq 'fetch' -and $env:RM_MODE -eq 'fetch') {{
        [Console]::Error.WriteLine('fixture Git fetch transport failed')
        $global:LASTEXITCODE = 28; return
    }}
    & $env:RM_GIT @args
    $code = $LASTEXITCODE
    if ($code -eq 0 -and $args -contains 'checkout') {{
        $head = & $env:RM_GIT -C $env:RM_INSTALL rev-parse HEAD
        if (($env:RM_MODE -eq 'checkout-after' -and $head -eq $env:RM_TARGET) -or
            ($env:RM_MODE -eq 'rollback-after' -and $head -eq $env:RM_ORIGINAL)) {{
            [Console]::Error.WriteLine('fixture Git checkout failed AFTER HEAD changed')
            $code = 29
        }}
    }}
    $global:LASTEXITCODE = $code
}}
& $Script $Version
exit $LASTEXITCODE
''')
            command = [shell, "-NoProfile", "-NonInteractive", "-ExecutionPolicy",
                       "Bypass", "-File", str(root / "invoke.ps1")]
        else:
            env["PATH"] = str(root / "bin")
            for name in ("git", "dirname", "basename", "mktemp", "rm", "ln", "mkdir",
                         "cat", "chmod", "cp", "grep", "head", "tr", "xargs", "mv",
                         "sed", "find", "ls", "rmdir", "readlink", "awk", "cmp", "stat"):
                executable = shutil.which(name)
                if not executable:
                    pytest.skip(f"Required utility unavailable: {name}")
                (root / "bin" / name).symlink_to(executable)
            _write(root / "bin/python3", f"#!/bin/sh\nexec {shlex.quote(sys.executable)} \"$@\"\n")
            (root / "bin/python3").chmod(0o755)
            command = [shell]
        assert all(shutil.which(name, path=env["PATH"]) is None
                   for name in ("kilo", "reg", "setx"))
        yield Runtime(root, env, command, git, request.param)


def _archive(rt: Runtime, root: Path, *paths: str) -> list[str]:
    """Unpack committed 9021, e.g. its installer and original wrappers."""
    data = _git(rt, ROOT, "archive", "--format=tar", OLD, *paths)
    executable = []
    with tarfile.open(fileobj=io.BytesIO(data)) as archive:
        for member in archive:
            assert not Path(member.name).is_absolute() and ".." not in Path(member.name).parts
            assert member.isfile() or member.isdir(), member.name
            if member.isfile():
                _write(root / member.name, archive.extractfile(member).read())
                (root / member.name).chmod(member.mode)
                if member.mode & 0o111:
                    executable.append(member.name)
    return executable


def _build(rt: Runtime, *, legacy: bool = False, changed: bool = False,
           missing: bool = False) -> tuple[Path, bytes]:
    """Create REAL local source/clone; e.g. OLD caller plus current candidate."""
    source, install = rt.root / "source", rt.root / "install"
    source.mkdir()
    old_executable = _archive(rt, source, *(() if legacy else ("install.ps1", "scripts/install.sh", "bin")))
    if not legacy:
        for name in (*REQUIRED, "cg_restore_installer_wrappers.py"):
            _write(source / "scripts" / name, (ROOT / "scripts" / name).read_bytes())
        for name in ("cg_generate_targets.py", "cg_retire_native_evidence.py"):
            _write(source / "scripts" / name, WORKER)
        _write(source / ".gitignore", ".cg-version\n.cg-version.tmp\n")
        _write(source / "package.txt", "before\n")
    _git(rt, source, "init")
    _git(rt, source, "add", "-A")
    _git(rt, source, "update-index", "--chmod=+x", "--", *old_executable)
    _git(rt, source, "commit", "-m", "fixture old source")
    old = _git(rt, source, "rev-parse", "HEAD").strip()
    rt.env["RM_ORIGINAL"] = old.decode()
    _git(rt, source, "tag", OLD)
    if legacy:
        executable = []
        for path in source.iterdir():
            if path.name != ".git":
                shutil.rmtree(path) if path.is_dir() else path.unlink()
        for entry in _git(rt, ROOT, "ls-files", "--stage", "-z").split(b"\0"):
            if entry:
                metadata, relative = entry.split(b"\t", 1)
                mode = metadata.split()[0]
                assert mode in (b"100644", b"100755")
                path = Path(os.fsdecode(relative))
                _write(source / path, (ROOT / path).read_bytes())
                (source / path).chmod(0o755 if mode == b"100755" else 0o644)
                if mode == b"100755":
                    executable.append(os.fsdecode(relative))
    else:
        _write(source / "package.txt", "after\n")
        _write(source / "target-only.txt", "target\n")
        if missing:
            (source / "scripts/cg_project_projection.py").unlink()
    _git(rt, source, "add", "-A")
    if legacy:
        _git(rt, source, "update-index", "--chmod=+x", "--", *executable)
        nonexecutable = [path for path in old_executable
                         if path not in executable and (source / path).is_file()]
        if nonexecutable:
            _git(rt, source, "update-index", "--chmod=-x", "--", *nonexecutable)
    if changed and legacy:
        _git(rt, source, "update-index", "--chmod=+x", "bin/cg-brain-init")
    _git(rt, source, "commit", "-m", "fixture candidate")
    _git(rt, source, "tag", TARGET)
    rt.env["RM_TARGET"] = _git(rt, source, "rev-parse", "HEAD").decode().strip()
    if legacy:
        modified = _git(rt, source, "diff", "--diff-filter=M", "--name-only", OLD, TARGET, "--", "bin").decode().splitlines()
        expected = CMD_PROBE_CHANGES | POSIX_WRAPPER_CHANGES
        assert set(modified) == expected
    else:
        _write(source / "package.txt", "independent HEAD\n")
        _git(rt, source, "add", "-A")
        _git(rt, source, "commit", "-m", "fixture independent writer")
        rt.env["RM_MOVED"] = _git(rt, source, "rev-parse", "HEAD").decode().strip()
    _git(rt, rt.root, "clone", "--no-local", source.as_uri(), str(install))
    _git(rt, install, "checkout", "-b", "fixture-start", old.decode())
    return install, old


def _state(rt: Runtime, install: Path) -> tuple[bytes, bytes, bytes | None]:
    """Capture exact package identity/pin, e.g. an absent pin and detached HEAD."""
    pin = install / ".cg-version"
    return (_git(rt, install, "rev-parse", "HEAD"),
            _git(rt, install, "rev-parse", "--abbrev-ref", "HEAD"),
            pin.read_bytes() if pin.exists() else None)


def _run(rt: Runtime, install: Path, version: str = TARGET) -> subprocess.CompletedProcess[str]:
    """Invoke an actual updater; e.g. OLD code with an empty consumer."""
    profile = Path(rt.env["PROFILE"])
    before = profile.read_bytes()
    rt.env["RM_INSTALL"] = str(install)
    rt.env["RM_PIN"] = (install / ".cg-version").read_bytes().hex() if (install / ".cg-version").exists() else "absent"
    result = subprocess.run([*rt.command, str(install / f"scripts/update.{rt.suffix}"), version],
                            cwd=rt.root / "consumer", env=rt.env,
                            capture_output=True, text=True, timeout=60, check=False)
    assert profile.read_bytes() == before
    return result


def _install(rt: Runtime, install: Path) -> dict[str, tuple[bytes, int]]:
    """Execute full OLD POSIX install OR exact OLD PS wrapper mutation only."""
    if rt.suffix == "ps1":
        committed = _git(rt, ROOT, "show", f"{OLD}:install.ps1").decode()
        block = committed[committed.index('$scripts = @("link", "unlink", "update")'):]
        block = block[:block.index('Write-Host "  Created:')]
        assert "[Environment]" not in block and "reg " not in block and "setx" not in block
        _write(rt.root / "wrappers.ps1", 'param([string]$Unused)\n$ErrorActionPreference="Stop"\n'
               + "$binDir='" + str(install / "bin").replace("'", "''") + "'\n" + block)
        script = rt.root / "wrappers.ps1"
    else:
        script = install / "scripts/install.sh"
        assert script.read_bytes() == _git(rt, ROOT, "show", f"{OLD}:scripts/install.sh")
    result = subprocess.run([*rt.command, str(script)], cwd=install, env=rt.env,
                            capture_output=True, text=True, timeout=60, check=False)
    assert result.returncode == 0, result.stdout + result.stderr
    return {path.relative_to(install).as_posix(): (path.read_bytes(), path.stat().st_mode & 0o111)
            for path in (install / "bin").iterdir() if path.is_file()}


def _manual_restore(rt: Runtime, install: Path, output: dict[str, tuple[bytes, int]]) -> None:
    """Documented pre-step: prove exact installer bytes/modes; restore ONLY those."""
    assert not _git(rt, install, "diff", "--cached", "--name-only")
    dirty = _git(rt, install, "diff", "--name-only").decode().splitlines()
    assert set(dirty) <= POSIX_DIRTY | {f"bin/cg-{name}.cmd" for name in ("link", "unlink", "update")}
    assert all(output[name] == ((install / name).read_bytes(),
                               (install / name).stat().st_mode & 0o111) for name in dirty)
    if dirty:
        _git(rt, install, "restore", "--source=HEAD", "--staged", "--worktree", "--", *dirty)
    assert not _git(rt, install, "diff", "HEAD", "--name-only")


@pytest.mark.parametrize("changed", (False, True))
def test_old_committed_installer_and_updater_acquire_current_candidate(runtime: Runtime, changed: bool) -> None:
    """Probe edits avoid installer overlap; deleted/mode-collision paths need proof."""
    rt = runtime
    install, _ = _build(rt, legacy=True, changed=changed)
    _write(install / ".cg-version", PIN)
    assert (install / f"scripts/update.{rt.suffix}").read_bytes() == _git(rt, ROOT, "show", f"{OLD}:scripts/update.{rt.suffix}")
    output = _install(rt, install)
    before = _state(rt, install)
    result = _run(rt, install)
    if rt.suffix == "sh":
        assert result.returncode != 0  # Baseline deletes dirty autopilot/help wrappers.
        assert _state(rt, install) == before
        assert set(_git(rt, install, "diff", "--name-only").decode().splitlines()) == POSIX_DIRTY
        path = install / "bin/cg-brain-init"
        _write(path, b"user launcher\n")
        with pytest.raises(AssertionError):
            _manual_restore(rt, install, output)
        assert path.read_bytes() == b"user launcher\n" and _state(rt, install) == before
        _write(path, output["bin/cg-brain-init"][0])
        path.chmod(0o755)
        _manual_restore(rt, install, output)
        result = _run(rt, install)
    assert result.returncode == 0, result.stdout + result.stderr
    assert _state(rt, install)[:2] == (rt.env["RM_TARGET"].encode() + b"\n", b"HEAD\n")
    assert (install / ".cg-version").read_bytes().strip() == TARGET.encode()
    assert not _git(rt, install, "status", "--porcelain")
    assert not any((rt.root / "consumer").iterdir())


@pytest.mark.parametrize("detached,pin", ((False, PIN), (True, None)))
@pytest.mark.parametrize("failure", ("success", "invalid", "missing-tag", "missing", "generator", "checkout", "downstream", "head", "checkout-after", "rollback-after", "fetch"))
def test_new_pinned_transaction(runtime: Runtime, detached: bool, pin: bytes | None, failure: str) -> None:
    """Execute validation, pin publication and rollback with REAL Git state."""
    rt = runtime
    if failure in ("checkout-after", "rollback-after", "fetch") and rt.suffix != "ps1":
        pytest.skip("Clearly labelled native-failure simulation is PowerShell-only")
    install, old = _build(rt, missing=failure == "missing")
    if detached:
        _git(rt, install, "checkout", "--detach", old.decode())
    if pin is not None:
        _write(install / ".cg-version", pin)
    if failure == "checkout":
        _write(install / "target-only.txt", "user untracked collision\n")
    rt.env["RM_MODE"] = failure
    before = _state(rt, install)
    result = _run(rt, install, {"invalid": "not-a-tag", "missing-tag": "v9.9.9"}.get(failure, TARGET))
    if failure == "success":
        assert result.returncode == 0, result.stdout + result.stderr
        assert _state(rt, install) == (rt.env["RM_TARGET"].encode() + b"\n", b"HEAD\n", TARGET.encode())
    else:
        assert result.returncode != 0, result.stdout + result.stderr
        if failure == "head":
            assert _state(rt, install) == (rt.env["RM_MOVED"].encode() + b"\n", b"HEAD\n", pin)
        else:
            assert _state(rt, install) == before
    if failure == "checkout":
        assert "would be overwritten by checkout" in result.stdout + result.stderr
        assert (install / "target-only.txt").read_text() == "user untracked collision\n"
    if failure in ("success", "generator", "downstream", "head", "rollback-after"):
        events = Path(rt.env["RM_LOG"]).read_text().splitlines()
        assert events == (["cg_generate_targets.py", "cg_retire_native_evidence.py"]
                          if failure in ("success", "downstream", "rollback-after") else ["cg_generate_targets.py"])
    else:
        assert not Path(rt.env["RM_LOG"]).exists()
    if failure in ("checkout-after", "rollback-after", "fetch"):
        assert "fixture Git" in result.stdout + result.stderr


@pytest.mark.parametrize("dirt", ("unknown", "staged", "launcher", "residue", "latest"))
def test_new_updater_preserves_unknown_dirt_and_restores_proven_residue(runtime: Runtime, dirt: str) -> None:
    """Only exact installer output is restored; latest never rewrites the pin."""
    rt = runtime
    install, _ = _build(rt)
    _write(install / ".cg-version", PIN)
    if dirt == "residue":
        _install(rt, install)
    else:
        path = install / ("bin/cg-update.cmd" if rt.suffix == "ps1" else "bin/cg-update") if dirt == "launcher" else install / "package.txt"
        _write(path, "user-owned changes\n")
        if dirt == "staged":
            _git(rt, install, "add", "package.txt")
    before, index = _state(rt, install), _git(rt, install, "diff", "--cached", "--binary")
    result = _run(rt, install, "latest" if dirt == "latest" else TARGET)
    if dirt == "residue":
        assert result.returncode == 0, result.stdout + result.stderr
        assert not _git(rt, install, "status", "--porcelain")
    else:
        assert result.returncode != 0
        assert _state(rt, install) == before and path.read_text() == "user-owned changes\n"
        assert _git(rt, install, "diff", "--cached", "--binary") == index
        assert not Path(rt.env["RM_LOG"]).exists()
