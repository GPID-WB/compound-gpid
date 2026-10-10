"""Real-Git acquisition and rollback; no real install, profiles, registry or Kilo.

Windows executes only the EXACT wrapper mutation block from
v1.2.0.9021:install.ps1:248-252, NOT a full installer qualification.
Linux/macOS execute the full committed POSIX installer; Git Bash is not proof.
"""
from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
import io
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys
import tarfile
import tempfile

import pytest

ROOT = Path(__file__).resolve().parents[2]
OLD, TARGET = "v1.2.0.9021", "v1.2.0.9022"
CANDIDATE = "v1.2.0.9023"
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
    assert pin.read_bytes().strip().decode() == os.environ['RM_TAG'], 'failure must be AFTER pin'
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
    if not windows and not (sys.platform.startswith("linux") or sys.platform == "darwin"):
        pytest.skip("Bash runtime requires Linux or macOS, not Git Bash")
    shell, git = shutil.which("powershell.exe" if windows else "bash"), shutil.which("git")
    if not shell or not git:
        pytest.skip("Required shell or real Git is unavailable")
    if (windows and Path(git).name.casefold() == "git.exe"
            and Path(git).parent.name.casefold() == "bin"
            and Path(git).parent.parent.name.casefold() in
            ("mingw64", "ucrt64", "clang64", "clangarm64")):
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
                   RM_GIT=git, RM_LOG=str(root / "events"), RM_TAG=TARGET)
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
param([string]$Script, [string]$Version, [string]$Operation = 'update')
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
if ($Operation -eq 'link') {{
    & $Script -RawArgs @('--platforms', 'codex,kilo', '--yes')
}} else {{
    & $Script $Version
}}
exit $LASTEXITCODE
''')
            command = [shell, "-NoProfile", "-NonInteractive", "-ExecutionPolicy",
                       "Bypass", "-File", str(root / "invoke.ps1")]
        else:
            env["PATH"] = str(root / "bin")
            for name in ("bash", "echo", "git", "dirname", "basename", "mktemp", "rm", "ln", "mkdir",
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


def _archive(rt: Runtime, root: Path, *paths: str, tag: str = OLD) -> list[str]:
    """Unpack a published tag, e.g. its installer and original wrappers."""
    data = _git(rt, ROOT, "archive", "--format=tar", tag, *paths)
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
           missing: bool = False, old_tag: str = OLD, target_tag: str = TARGET,
           lifecycle: bool = False, host_mode: str | None = None) -> tuple[Path, bytes]:
    """Create REAL local source/clone; e.g. OLD caller plus current candidate."""
    source, install = rt.root / "source", rt.root / "install"
    source.mkdir()
    if host_mode is not None:
        rt.env.update(RM_HOST_MODE=host_mode,
                      RM_HOST_LOG=str(rt.root / "host-commands"))
        if host_mode != "absent":
            host = rt.root / "bin/kilo.py"
            _write(host, '''
import os, sys
from pathlib import Path
with Path(os.environ['RM_HOST_LOG']).open('a', encoding='utf-8') as log:
    log.write(repr(sys.argv[1:]) + '\\n')
if sys.argv[1:] == ['--version']:
    if os.environ['RM_HOST_MODE'] == 'unreadable':
        raise SystemExit(16)
    sys.stdout.write('0.1.0\\n' if os.environ['RM_HOST_MODE'] == 'old' else '7.4.21\\n')
    raise SystemExit(0)
if sys.argv[1:3] == ['debug', 'skill']:
    sys.stderr.write('fixture debug skill failed\\n')
    raise SystemExit(17)
raise SystemExit(18)
''')
            if rt.suffix == "ps1":
                _write(rt.root / "bin/kilo.cmd",
                       f'@echo off\n"{sys.executable}" "{host}" %*\n')
                rt.env["PATH"] = str(rt.root / "bin") + os.pathsep + rt.env["PATH"]
            else:
                _write(rt.root / "bin/kilo", "#!/bin/sh\nexec "
                       f'{shlex.quote(sys.executable)} {shlex.quote(str(host))} "$@"\n')
                (rt.root / "bin/kilo").chmod(0o755)
    old_executable = _archive(
        rt, source,
        *(() if legacy else ("install.ps1", "scripts/install.sh", "bin")),
        tag=old_tag,
    )
    rt.env["RM_TAG"] = target_tag
    if not legacy:
        for name in (*REQUIRED, "cg_restore_installer_wrappers.py"):
            _write(source / "scripts" / name, (ROOT / "scripts" / name).read_bytes())
            if name.endswith(".sh"):
                (source / "scripts" / name).chmod(0o755)
        for name in ("cg_generate_targets.py", "cg_retire_native_evidence.py"):
            _write(source / "scripts" / name, WORKER)
        _write(source / ".gitignore", ".cg-version\n.cg-version.tmp\n")
        _write(source / "package.txt", "before\n")
        if lifecycle:
            mapping_path = ".github/shared/target-mapping.json"
            mapping = json.loads((ROOT / mapping_path).read_text(encoding="utf-8"))
            _write(source / mapping_path, json.dumps(mapping))
            for target in mapping["targets"]:
                if target["id"] not in ("codex", "kilo"):
                    continue
                for unit in target["installUnits"]:
                    path = source / unit["source"]
                    if unit["type"] == "file":
                        _write(path, "{}\n" if path.suffix == ".json" else "# Fixture\n")
                    elif path.name == "skills":
                        _write(path / "cg-fixture/SKILL.md", '---\nname: cg-fixture\n'
                               'description: "Fixture"\n---\n# Fixture\n')
                    elif path.name == "agents" or path.name == "subagents":
                        _write(path / "cg-fixture.md", '---\ndescription: "Fixture"\n'
                               'mode: subagent\n---\n# Fixture\n')
                    elif path.name == "commands":
                        _write(path / "cg-plan.md",
                               '---\ndescription: "Fixture"\n---\n# Fixture\n')
                    else:
                        _write(path / "fixture.txt", "fixture\n")
    _git(rt, source, "init")
    _git(rt, source, "add", "-A")
    _git(rt, source, "update-index", "--chmod=+x", "--", *old_executable)
    _git(rt, source, "commit", "-m", "fixture old source")
    old = _git(rt, source, "rev-parse", "HEAD").strip()
    rt.env["RM_ORIGINAL"] = old.decode()
    _git(rt, source, "tag", old_tag)
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
    _git(rt, source, "tag", target_tag)
    rt.env["RM_TARGET"] = _git(rt, source, "rev-parse", "HEAD").decode().strip()
    if legacy:
        modified = _git(rt, source, "diff", "--diff-filter=M", "--name-only", old_tag, target_tag, "--", "bin").decode().splitlines()
        expected = (CMD_PROBE_CHANGES | POSIX_WRAPPER_CHANGES
                    if old_tag == OLD else set())
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


def _run(rt: Runtime, install: Path, version: str = TARGET,
         project: Path | None = None) -> subprocess.CompletedProcess[str]:
    """Invoke an actual updater; e.g. OLD code with an empty consumer."""
    profile = Path(rt.env["PROFILE"])
    before = profile.read_bytes()
    rt.env["RM_INSTALL"] = str(install)
    rt.env["RM_PIN"] = (install / ".cg-version").read_bytes().hex() if (install / ".cg-version").exists() else "absent"
    result = subprocess.run([*rt.command, str(install / f"scripts/update.{rt.suffix}"), version],
                            cwd=project or rt.root / "consumer", env=rt.env,
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


def test_published_9022_updater_acquires_9023_from_empty_folder(
    runtime: Runtime,
) -> None:
    """The published updater acquires candidate bytes without a consumer or host."""
    rt = runtime
    install, _ = _build(rt, legacy=True, old_tag=TARGET, target_tag=CANDIDATE)
    updater = f"scripts/update.{rt.suffix}"
    assert (install / updater).read_bytes() == _git(
        rt, ROOT, "show", f"{TARGET}:{updater}",
    )
    consumer = rt.root / "consumer"
    assert not any(consumer.iterdir())
    # Exercise the public updater, not the internal-link consumer suppression.
    rt.env.pop("CG_INTERNAL_CALL", None)
    result = _run(rt, install, CANDIDATE)
    assert result.returncode == 0, result.stdout + result.stderr
    assert _state(rt, install) == (
        rt.env["RM_TARGET"].encode() + b"\n", b"HEAD\n", CANDIDATE.encode(),
    )
    assert not _git(rt, install, "status", "--porcelain")
    assert not any(consumer.iterdir())


@pytest.mark.parametrize("host_mode", ("absent", "old", "unreadable", "debug-fail"))
def test_update_and_link_ignore_host_and_print_one_note(
    runtime: Runtime, host_mode: str,
) -> None:
    """Actual fixture update/link succeed without even querying a hostile host."""
    rt = runtime
    install, _ = _build(rt, lifecycle=True, host_mode=host_mode, target_tag=CANDIDATE)
    result = _run(rt, install, CANDIDATE)
    assert result.returncode == 0, result.stdout + result.stderr
    rt.env.pop("CG_INTERNAL_CALL", None)
    rt.env["RM_PIN"] = (install / ".cg-version").read_bytes().hex()
    project = rt.root / "consumer"
    command = [*rt.command, str(install / f"scripts/link.{rt.suffix}")]
    command.extend([CANDIDATE, "link"] if rt.suffix == "ps1" else
                   ["--platforms", "codex,kilo", "--yes"])
    profile = Path(rt.env["PROFILE"])
    before_profile = profile.read_bytes()
    # A second link has coexisting roots before its internal update. That update
    # must leave the single note to link, not print another copy itself.
    for _ in range(2):
        result = subprocess.run(command, cwd=project, env=rt.env, capture_output=True,
                                text=True, timeout=60, check=False)
        output = result.stdout + result.stderr
        assert result.returncode == 0, output
        assert "Kilo preflight" in output
        assert output.count("Note: Kilo and compatibility skills coexist.") == 1
        assert "Linked!" in output
        assert (project / ".kilo/skills/.compound-gpid-managed-copy.json").is_file()
        assert (project / ".agents/skills/cg-fixture/SKILL.md").is_file()
        assert not Path(rt.env["RM_HOST_LOG"]).exists()
    result = _run(rt, install, CANDIDATE)
    output = result.stdout + result.stderr
    assert result.returncode == 0, output
    assert "Kilo preflight" in output
    assert output.count("Note: Kilo and compatibility skills coexist.") == 1
    assert profile.read_bytes() == before_profile
    assert not Path(rt.env["RM_HOST_LOG"]).exists()
    assert not _git(rt, install, "status", "--porcelain")


@pytest.mark.parametrize("compatibility_root", (".claude", ".agents"))
def test_home_update_preserves_user_skills_without_validation_or_host(
    runtime: Runtime, compatibility_root: str,
) -> None:
    """User-level skills are not OUR generated projection, even with state nearby."""
    rt = runtime
    install, _ = _build(rt, host_mode="unreadable", target_tag=CANDIDATE)
    home = Path(rt.env["HOME"])
    user_skills = (
        home / ".kilo/skills/user-skill/SKILL.md",
        home / compatibility_root / "skills/user-skill/SKILL.md",
        home / ".compound-gpid/user-sentinel.txt",
    )
    for path in user_skills:
        # Deliberately invalid generated content; user-level content is not ours.
        _write(path, b"\xffuser bytes\n")
    before = {path: path.read_bytes() for path in user_skills}
    rt.env.pop("CG_INTERNAL_CALL", None)
    result = _run(rt, install, CANDIDATE, project=home)
    output = result.stdout + result.stderr
    assert result.returncode == 0, output
    assert "Kilo preflight" not in output
    assert output.count("Note: Kilo and compatibility skills coexist.") == 1
    assert {path: path.read_bytes() for path in user_skills} == before
    assert not Path(rt.env["RM_HOST_LOG"]).exists()
    assert _state(rt, install)[2] == CANDIDATE.encode()


MIGRATION_TAG = "v1.2.0.9024"


@pytest.fixture
def windows_migration(runtime: Runtime) -> tuple[Runtime, Path, Path]:
    """Use real disposable clones and a synthetic NEW installer, never real HKCU."""
    rt = runtime
    if rt.suffix != "ps1":
        pytest.skip("Windows migration requires Windows PowerShell")
    source, remote, new = (rt.root / name for name in ("seed", "official.git", "new"))
    install = Path(rt.env["USERPROFILE"]) / ".compound-gpid"
    source.mkdir()
    _write(source / ".gitignore", ".cg-version\n")
    _write(source / ".gitattributes", "*.ps1 text eol=lf\nbin/*.cmd text eol=crlf\n")
    _write(source / "package.txt", "old package\n")
    _write(source / "install.ps1", "throw 'OLD CODE MUST NEVER RUN'\n")
    for name in ("link", "unlink", "update"):
        _write(source / f"bin/cg-{name}.cmd", "@echo off\nexit /b 71\n")
        _write(source / f"scripts/{name}.ps1", "throw 'OLD CODE MUST NEVER RUN'\n")
    _git(rt, source, "init")
    _git(rt, source, "add", "-A")
    _git(rt, source, "commit", "-m", "fixture old installation")
    _git(rt, source, "tag", OLD)
    _write(source / "scripts/migrate-install.ps1", (ROOT / "scripts/migrate-install.ps1").read_bytes())
    _write(source / "package.txt", "new package\n")
    _write(source / "install.ps1", '''
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
if ((Get-Content -LiteralPath "$PSScriptRoot/.cg-version" -Raw) -ne 'v1.2.0.9024') {
    throw 'NEW pin must exist BEFORE installer'
}
Set-Content -LiteralPath $env:WIN_LOG -Value $PSScriptRoot -Encoding UTF8
if ($env:WIN_FAILURE -eq 'install') { exit 23 }
Set-Content -LiteralPath $env:WIN_REGISTRY -Value "$PSScriptRoot/bin" -NoNewline -Encoding UTF8
if ($env:WIN_FAILURE -eq 'dirty') { Set-Content -LiteralPath "$PSScriptRoot/package.txt" -Value 'changed' }
exit 0
''')
    _git(rt, source, "add", "-A")
    _git(rt, source, "commit", "-m", "fixture new release")
    _git(rt, source, "tag", MIGRATION_TAG)
    _git(rt, rt.root, "clone", "--bare", source.as_uri(), str(remote))
    for target, tag in ((new, MIGRATION_TAG), (install, OLD)):
        _git(rt, rt.root, "clone", "--no-local", "--branch", tag, remote.as_uri(), str(target))
    assert (new / "scripts/migrate-install.ps1").read_bytes() == (ROOT / "scripts/migrate-install.ps1").read_bytes()
    rt.env.update(WIN_REMOTE=remote.as_uri(), WIN_SOURCE=str(new), WIN_INSTALL=str(install),
                  WIN_LOG=str(rt.root / "new-installer.log"),
                  WIN_REGISTRY=str(rt.root / "fake-hkcu-path"), WIN_FAILURE="")
    _write(Path(rt.env["WIN_REGISTRY"]), b"")
    return rt, new, install


def _migrate(fixture: tuple[Runtime, Path, Path], *args: str) -> subprocess.CompletedProcess[str]:
    """Run exact candidate bytes with fixture-only Git transport/registry mocks."""
    rt, new, _ = fixture
    def quote(value: str | Path) -> str:
        """Quote one fixture path for PowerShell, e.g. a spaced custom path."""
        return "'" + str(value).replace("'", "''") + "'"
    # These mocks only read/write fixture files. They never load installed code.
    command = '''
$global:PROFILE = $env:PROFILE
Set-Variable -Name HOME -Scope Global -Value $env:HOME -Force
function global:git {
    & $env:RM_GIT -c "url.$($env:WIN_REMOTE).insteadOf=https://github.com/GPID-WB/compound-gpid.git" -c protocol.allow=never -c protocol.file.allow=always -c core.autocrlf=false @args
    $global:LASTEXITCODE = $LASTEXITCODE
}
function global:Get-ItemProperty {
    [CmdletBinding()]param([string]$LiteralPath)
    if ($LiteralPath -eq 'HKCU:\\Environment') {
        Add-Content -LiteralPath "$env:WIN_REGISTRY.reads" -Value 'HKCU'
        $path = if ($env:WIN_FAILURE -eq 'path') { $env:WIN_SHADOW } else { Get-Content -LiteralPath $env:WIN_REGISTRY -Raw }
        return [pscustomobject]@{Path=$path}
    }
    if ($LiteralPath -eq 'HKLM:\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Environment') {
        return [pscustomobject]@{Path=(Split-Path $env:RM_GIT -Parent)}
    }
    throw "Unexpected registry access: $LiteralPath"
}
function global:Test-Path {
    [CmdletBinding()]param([string]$LiteralPath, [string]$Path, [string]$PathType)
    if ($LiteralPath -eq 'C:\\WBG\\.compound-gpid') { return $false }
    Microsoft.PowerShell.Management\\Test-Path @PSBoundParameters
}
function global:Get-ChildItem {
    [CmdletBinding()]param([string]$Path, [string]$LiteralPath, [switch]$Force)
    if ($LiteralPath -eq 'C:\\WBG') { return }
    Microsoft.PowerShell.Management\\Get-ChildItem @PSBoundParameters
}
'''
    invocation = " & " + quote(new / "scripts/migrate-install.ps1")
    invocation += " " + " ".join(arg if arg in ("-InstallPath", "-Rollback") else quote(arg) for arg in args)
    before = Path(rt.env["PROFILE"]).read_bytes()
    result = subprocess.run([rt.env["SHELL"], "-NoProfile", "-NonInteractive", "-ExecutionPolicy",
                             "Bypass", "-Command", command + invocation], cwd=rt.root, env=rt.env,
                             capture_output=True, text=True, encoding="utf-8", timeout=90, check=False)
    assert Path(rt.env["PROFILE"]).read_bytes() == before
    return result


@pytest.mark.parametrize("selection", ("default", "path", "custom", "dirty", "explicit-two", "accented"))
def test_windows_migration_preserves_old_clone_and_pins_new(
    windows_migration: tuple[Runtime, Path, Path], selection: str,
) -> None:
    """Discovery/custom selection keeps old bytes and executes only NEW install."""
    rt, new, install = windows_migration
    args = []
    if selection in ("path", "custom", "accented"):
        custom = rt.root / ("ni\u00f1o install" if selection == "accented" else "custom install")
        install.rename(custom)
        install = custom
        if selection == "path":
            rt.env["PATH"] = str(install / "bin") + os.pathsep + rt.env["PATH"]
        else:
            args = ["-InstallPath", str(install)]
        if selection == "accented":
            accented_source = rt.root / "ni\u00f1o new clone"
            new.rename(accented_source)
            new = accented_source
            windows_migration = (rt, new, install)
    if selection == "explicit-two":
        other = rt.root / "other install"
        _git(rt, rt.root, "clone", "--branch", OLD, rt.env["WIN_REMOTE"], str(other))
        rt.env["PATH"] = str(other / "bin") + os.pathsep + rt.env["PATH"]
        args = ["-InstallPath", str(install)]
    _write(install / ".cg-version", PIN)
    if selection == "dirty":
        _write(install / "package.txt", "user tracked changes\n")
        _git(rt, install, "add", "package.txt")
        _write(install / "untracked.txt", b"private\x00bytes")
    before = {p.relative_to(install): p.read_bytes() for p in install.rglob("*") if p.is_file() and ".git" not in p.relative_to(install).parts}
    old_head = _git(rt, install, "rev-parse", "HEAD")
    index = _git(rt, install, "diff", "--cached", "--binary")
    result = _migrate(windows_migration, *args)
    assert result.returncode == 0, result.stdout + result.stderr
    backups = list(install.parent.glob(install.name + ".backup-*"))
    assert len(backups) == 1
    backup = backups[0]
    assert all((backup / path).read_bytes() == data for path, data in before.items())
    assert _git(rt, backup, "rev-parse", "HEAD") == old_head
    assert _git(rt, backup, "diff", "--cached", "--binary") == index
    assert _git(rt, install, "rev-parse", "HEAD") == _git(rt, new, "rev-parse", "HEAD")
    assert (install / ".cg-version").read_bytes() == MIGRATION_TAG.encode()
    assert not _git(rt, install, "status", "--porcelain")
    assert (install / ".git/config").read_text().find("https://github.com/GPID-WB/compound-gpid.git") >= 0
    assert not (install / ".git/objects/info/alternates").exists()
    assert Path(rt.env["WIN_LOG"]).read_text(encoding="utf-8-sig").strip() == str(install)
    assert Path(rt.env["WIN_REGISTRY"] + ".reads").read_text().splitlines() == ["HKCU"] * (1 if args else 2)
    assert "Old HEAD:" in result.stdout and "Old .cg-version:" in result.stdout
    assert "Old status:" not in result.stdout
    assert "manual action required" in result.stdout and "-Rollback" in result.stdout
    assert not _git(rt, new, "status", "--porcelain")
    repeat = _migrate(windows_migration, "-InstallPath", str(install))
    assert repeat.returncode != 0 and "Existing backup found" in repeat.stdout + repeat.stderr
    assert all((backup / path).read_bytes() == data for path, data in before.items())


@pytest.mark.parametrize("failure", ("install", "dirty", "path", "remote-tag"))
def test_windows_migration_failure_restores_old_folder(
    windows_migration: tuple[Runtime, Path, Path], failure: str,
) -> None:
    """Failed NEW install/verification leaves original HEAD, pin and local bytes."""
    rt, _, install = windows_migration
    _write(install / ".cg-version", PIN)
    _write(install / "private.txt", b"unchanged private bytes")
    before = _state(rt, install)
    rt.env["WIN_FAILURE"] = failure
    if failure == "path":
        shadow = rt.root / "shadow"
        _write(shadow / "cg-update.cmd", "@echo off\nexit /b 72\n")
        rt.env["WIN_SHADOW"] = str(shadow)
    if failure == "remote-tag":
        _git(rt, rt.root, "--git-dir", str(rt.root / "official.git"), "update-ref", "refs/tags/" + MIGRATION_TAG,
             _git(rt, install, "rev-parse", "HEAD").decode().strip())
    result = _migrate(windows_migration)
    assert result.returncode != 0
    assert "Old folder restored" in " ".join((result.stdout + result.stderr).split())
    assert _state(rt, install) == before
    assert (install / "private.txt").read_bytes() == b"unchanged private bytes"
    assert not list(install.parent.glob(install.name + ".backup-*"))


@pytest.mark.parametrize("case", ("two", "junction", "worktree", "overlap", "dirty-source", "untagged", "interrupted", "zero"))
def test_windows_migration_refuses_unsafe_or_ambiguous_state(
    windows_migration: tuple[Runtime, Path, Path], case: str,
) -> None:
    """Refusals occur before installer execution or old clone replacement."""
    rt, new, install = windows_migration
    args, junction = [], None
    old = _git(rt, install, "rev-parse", "HEAD")
    if case == "two":
        other = rt.root / "other"
        _git(rt, rt.root, "clone", "--branch", OLD, rt.env["WIN_REMOTE"], str(other))
        rt.env["PATH"] = str(other / "bin") + os.pathsep + rt.env["PATH"]
    elif case == "junction":
        junction = rt.root / "alias"
        result = subprocess.run([rt.env["SHELL"], "-NoProfile", "-Command",
                                 f"New-Item -ItemType Junction -Path '{junction}' -Value '{install}' | Out-Null"],
                                capture_output=True, text=True, check=False)
        assert result.returncode == 0, result.stderr
        args = ["-InstallPath", str(junction)]
    elif case == "worktree":
        worktree = rt.root / "worktree"
        _git(rt, install, "worktree", "add", "--detach", str(worktree), OLD)
        args = ["-InstallPath", str(worktree)]
    elif case == "overlap":
        args = ["-InstallPath", str(new)]
    elif case == "dirty-source":
        _write(new / "untracked.txt", "dirty source\n")
    elif case == "untagged":
        _git(rt, new, "tag", "-d", MIGRATION_TAG)
    elif case in ("interrupted", "zero"):
        aside = install.parent / (install.name + ".backup-v1.2.0.9021-20261010-120000-000" if case == "interrupted" else "not-an-install")
        install.rename(aside)
        if case == "interrupted":
            _write(install / "partial.txt", "interrupted new clone\n")
    try:
        result = _migrate(windows_migration, *args)
        assert result.returncode != 0
        assert not Path(rt.env["WIN_LOG"]).exists()
        expected = {"two": "Multiple installations", "junction": "Link/junction",
                    "worktree": ".git files/worktrees refused", "overlap": "overlap",
                    "dirty-source": "clean fresh clone", "untagged": "Git failed"}
        if case in expected:
            assert expected[case] in result.stdout + result.stderr
        if case not in ("interrupted", "zero"):
            assert _git(rt, install, "rev-parse", "HEAD") == old
        if case == "interrupted":
            assert "Existing backup found" in result.stdout + result.stderr
            assert "-Rollback" in result.stdout + result.stderr
            assert (install / "partial.txt").read_text() == "interrupted new clone\n"
        if case == "zero":
            assert "normal NEW install.ps1" in result.stdout + result.stderr
    finally:
        if junction is not None:
            # Unlink the junction itself before TemporaryDirectory cleanup.
            os.rmdir(junction)


@pytest.mark.parametrize("current", ("migrated", "missing", "partial"))
def test_windows_migration_rollback_keeps_current_folder(
    windows_migration: tuple[Runtime, Path, Path], current: str,
) -> None:
    """Restore exact path, retaining later edits or an interrupted partial clone."""
    rt, _, install = windows_migration
    _write(install / ".cg-version", PIN)
    before = _state(rt, install)
    if current == "migrated":
        result = _migrate(windows_migration)
        assert result.returncode == 0, result.stdout + result.stderr
        backup = next(install.parent.glob(install.name + ".backup-*"))
    else:
        backup = install.parent / (install.name + ".backup-v1.2.0.9021-20261010-120000-000")
        install.rename(backup)
    if current != "missing":
        _write(install / "later-user-edit.txt", b"preserve later edits")
    result = _migrate(windows_migration, "-InstallPath", str(install), "-Rollback", str(backup))
    assert result.returncode == 0, result.stdout + result.stderr
    assert _state(rt, install) == before
    assert not backup.exists()
    asides = list(install.parent.glob(install.name + ".rollback-*"))
    assert len(asides) == (0 if current == "missing" else 1)
    if asides:
        assert (asides[0] / "later-user-edit.txt").read_bytes() == b"preserve later edits"


@pytest.mark.parametrize("current", ("missing", "partial"))
def test_windows_migration_detects_interrupted_custom_hkcu_path(
    windows_migration: tuple[Runtime, Path, Path], current: str,
) -> None:
    """Raw HKCU bin entries find sibling backups even with no current wrappers."""
    rt, new, install = windows_migration
    target = rt.root / "custom interrupted install"
    backup = target.with_name(target.name + ".backup-v1.2.0.9021-20261010-120000-000")
    install.rename(backup)
    _write(Path(rt.env["WIN_REGISTRY"]), str(target / "bin"))
    if current == "partial":
        _write(target / "partial.txt", b"preserve partial clone")
    before = _state(rt, backup)
    result = _migrate(windows_migration)
    output = " ".join((result.stdout + result.stderr).split())
    assert result.returncode != 0 and "Existing backup found" in output
    assert f"& '{new / 'scripts/migrate-install.ps1'}' -InstallPath '{target}' -Rollback '{backup}'" in output
    assert f"& '{new / 'scripts/migrate-install.ps1'}' -InstallPath '{target}'" in output
    assert "To resume: roll back first" in output
    assert _state(rt, backup) == before
    assert not Path(rt.env["WIN_LOG"]).exists()
    assert Path(rt.env["WIN_REGISTRY"]).read_text() == str(target / "bin")
    if current == "partial":
        assert (target / "partial.txt").read_bytes() == b"preserve partial clone"
    else:
        assert not target.exists()


def test_windows_migration_error_keeps_long_unicode_paths(
    windows_migration: tuple[Runtime, Path, Path],
) -> None:
    """Hosted-length paths must not wrap or corrupt the refusal and recovery text."""
    rt, new, install = windows_migration
    long_source = rt.root / ("hosted runner " + "x" * 64) / "ni\u00f1o NEW clone"
    long_source.parent.mkdir()
    new.rename(long_source)
    target = rt.root / "ni\u00f1o old installation"
    backup = target.with_name(target.name + ".backup-v1.2.0.9021-20261010-120000-000")
    install.rename(backup)
    before = _state(rt, backup)

    result = _migrate((rt, long_source, target), "-InstallPath", str(target))

    assert result.returncode == 1
    assert f"Existing backup found: {backup}. Nothing was changed." in result.stderr.splitlines()
    assert f"-InstallPath '{target}' -Rollback '{backup}'" in result.stdout
    assert "To resume: roll back first" in result.stdout
    assert _state(rt, backup) == before and not target.exists()
    assert not Path(rt.env["WIN_LOG"]).exists()
    assert not _git(rt, long_source, "status", "--porcelain")


def test_windows_migration_rollback_requires_install_path(
    windows_migration: tuple[Runtime, Path, Path],
) -> None:
    """An omitted or mismatched explicit target cannot move the preserved backup."""
    rt, _, install = windows_migration
    backup = install.with_name(install.name + ".backup-v1.2.0.9021-20261010-120000-000")
    install.rename(backup)
    before = _state(rt, backup)
    for args, message in (
        (["-Rollback", str(backup)], "-Rollback requires -InstallPath"),
        (["-InstallPath", str(rt.root / "wrong target"), "-Rollback", str(backup)], "exact target and sibling"),
    ):
        result = _migrate(windows_migration, *args)
        assert result.returncode != 0
        assert message in " ".join((result.stdout + result.stderr).split())
        assert _state(rt, backup) == before and not install.exists()
        assert not Path(rt.env["WIN_LOG"]).exists()


def test_windows_migration_sanitizes_unusual_describe_for_backup(
    windows_migration: tuple[Runtime, Path, Path],
) -> None:
    """Unicode, plus signs and a reserved backup delimiter become a safe version."""
    rt, _, install = windows_migration
    unusual = "v1.2.0.9021.pi\u00f1ata+.BaCkUp-r\u00e9sum\u00e9"
    _git(rt, install, "tag", "-d", OLD)
    _git(rt, install, "tag", unusual)
    _write(install / "package.txt", "preserve tracked changes\n")
    before = _state(rt, install)
    result = _migrate(windows_migration)
    assert result.returncode == 0, result.stdout + result.stderr
    assert f"Old describe: {unusual}-dirty" in result.stdout
    backup = next(install.parent.glob(install.name + ".backup-*"))
    suffix = backup.name.removeprefix(install.name + ".backup-")
    match = re.fullmatch(r"([A-Za-z0-9._-]+)-(\d{8}-\d{6}-\d{3})", suffix)
    assert match is not None
    assert "backup" not in match[1].casefold()
    assert _state(rt, backup) == before
    assert (backup / "package.txt").read_text() == "preserve tracked changes\n"
    result = _migrate(windows_migration, "-InstallPath", str(install), "-Rollback", str(backup))
    assert result.returncode == 0, result.stdout + result.stderr
    assert _state(rt, install) == before and not backup.exists()
