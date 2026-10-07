"""Slice 1 runtime boundaries, using copied scripts and temporary state only."""
from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import tempfile

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
NATIVE_PATHS = (
    ".kilo/plugins/cg-native-evidence.js",
    *(
        f".kilo/plugin-support/cg-native-evidence/{name}.mjs"
        for name in ("evidence", "records", "transport", "wire")
    ),
)
OLD_CONFIG = b'{"managed":"before"}\n'
NEW_CONFIG = b'{"managed":"after"}\n'

# Only retirement and inline shell Python execute real workers. Mocked writers
# reject residue BEFORE replacing evidence, so reversing the order fails.
DISPATCH = r'''
import json, os, subprocess, sys
from pathlib import Path
args = sys.argv[1:]
if args[0] in ("--version", "-c", "-"):
    raise SystemExit(subprocess.run([sys.executable, *args]).returncode)
worker = Path(args[0]).name
if worker == "cg_restore_installer_wrappers.py":
    raise SystemExit(0)  # This ordering fixture uses fake Git, not a clone.
if worker == "cg_kilo_preflight.py":
    sys.stdout.write('{"status":"ok","exit_code":0,"certified_launch_required":false}\n')
    raise SystemExit(0)
names = {"cg_retire_native_evidence.py": "retire",
         "cg_generate_targets.py": "generate",
         "cg_project_manifest.py": "manifest",
         "cg_project_projection.py": "projection"}
name = names[worker]
if name == "generate" and "--dry-run" in args:
    root = Path(args[args.index("--root") + 1])
    with open(os.environ["NR_LOG"], "a", encoding="utf-8") as handle:
        handle.write(json.dumps(["validate", str(root)]) + "\n")
    raise SystemExit(0)
flag = "--project-root" if name == "projection" else "--root"
root = Path(args[args.index(flag) + 1])
with open(os.environ["NR_LOG"], "a", encoding="utf-8") as handle:
    handle.write(json.dumps([name, str(root)]) + "\n")
if name == "retire":
    raise SystemExit(subprocess.run([sys.executable, *args]).returncode)
if name == "manifest":
    if os.environ.get("NR_FAIL_MANIFEST") == "1":
        sys.stderr.write("fixture manifest validation failed\n")
        raise SystemExit(9)
    sys.stdout.write("manifest fixture complete\n")
    raise SystemExit(0)
assert not any((root / path).exists()
               for path in json.loads(os.environ["NR_NATIVE_PATHS"])), name
if name == "generate":
    receipt = root / ".kilo/.compound-gpid-generated.json"
    data = {"schemaVersion": 1, "target": "kilo", "policyVersion": 1, "files": []}
else:
    receipt = root / ".compound-gpid/projection-ownership.json"
    data = {"schemaVersion": 1, "entries": {}}
receipt.write_text(json.dumps(data) + "\n", encoding="utf-8")
sys.stdout.write(name + " fixture complete\n")
'''


@dataclass
class Runtime:
    """Paths and a restricted environment for one copied entrypoint runtime."""

    install: Path
    consumer: Path
    env: dict[str, str]
    command: list[str]
    suffix: str


def _write(path: Path, content: str | bytes) -> None:
    """Write fixture bytes, for example a synthetic receipt under its root."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content.encode("utf-8") if isinstance(content, str) else content)


@pytest.fixture(params=("powershell", "bash"))
def runtime(request: pytest.FixtureRequest) -> Iterator[Runtime]:
    """Build isolated copies, e.g. for link with CG_SKIP_UPDATE=1."""
    windows = request.param == "powershell"
    if windows and os.name != "nt":
        pytest.skip("Windows PowerShell entrypoints require Windows")
    if not windows and not sys.platform.startswith("linux"):
        pytest.skip("Bash runtime fixture is Linux-only; no macOS qualification")
    shell = shutil.which("powershell.exe" if windows else "bash")
    if shell is None:
        pytest.skip("Required entrypoint shell is unavailable")
    # Keep secure_fs paths short even when pytest's own temporary path is long.
    with tempfile.TemporaryDirectory(prefix="nr-") as temporary:
        root = Path(temporary).resolve()
        install, consumer, home = root / "install", root / "consumer", root / "home"
        suffix = "ps1" if windows else "sh"
        for name in (f"link.{suffix}", f"update.{suffix}", "helpers.ps1",
                     "cg_retire_native_evidence.py", "secure_fs.py"):
            destination = install / "scripts" / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(REPO_ROOT / "scripts" / name, destination)
        for name in ("generate_targets", "project_manifest", "project_projection",
                      "kilo_preflight"):
            _write(install / f"scripts/cg_{name}.py", "# mocked by dispatch\n")
        for name in ("link.ps1", "link.sh", "update.ps1", "update.sh",
                     "cg_kilo_copy.py", "cg_migrate_research_layout.py",
                     "research_layout.py", "cg_restore_installer_wrappers.py"):
            path = install / "scripts" / name
            if not path.exists():
                _write(path, "# fixture required target script\n")
        mapping_path = ".github/shared/target-mapping.json"
        mapping = json.loads((REPO_ROOT / mapping_path).read_text(encoding="utf-8"))
        kilo = next(target for target in mapping["targets"] if target["id"] == "kilo")
        for unit in kilo["installUnits"]:
            path = install / unit["source"]
            if unit["type"] == "directory":
                path /= "fixture.txt"
            _write(path, NEW_CONFIG if unit["source"] == ".kilo/kilo.json"
                   else "fixture\n")
        _write(install / mapping_path, json.dumps(mapping))
        _write(install / ".cg-version", "latest")
        _write(consumer / "compound-gpid.local.md", "---\nsuites: [cg]\n---\n")
        _write(consumer / ".compound-gpid/active-manifest.json", "{}\n")
        _write(consumer / ".kilo/kilo.json", OLD_CONFIG)
        _write(consumer / ".compound-gpid/managed-files.json", json.dumps({
            "schemaVersion": "compound-gpid-managed-files-v1", "files": {
                ".kilo/kilo.json": {"source": ".kilo/kilo.json",
                                    "checksum": hashlib.sha256(
                                        OLD_CONFIG).hexdigest()}}}))
        _write(home / ".config/kilo/kilo.jsonc", '{"fixture":"preserve"}\n')
        _write(home / "profile.ps1", "# fixture profile\n")
        env = {key: value for key, value in os.environ.items()
               if not key.upper().startswith(("CG_", "KILO_", "GIT_", "PYTHON", "NR_"))
               and key.upper() not in ("BASH_ENV", "ENV", "PSMODULEPATH")}
        for name in ("HOME", "USERPROFILE", "APPDATA", "LOCALAPPDATA",
                     "XDG_CONFIG_HOME"):
            env[name] = str(home)
        (root / "t").mkdir()
        env.update(TEMP=str(root / "t"), TMP=str(root / "t"), TMPDIR=str(root / "t"),
                   PROFILE=str(home / "profile.ps1"), CG_SKIP_UPDATE="1",
                   NR_LOG=str(root / "events.jsonl"),
                   NR_NATIVE_PATHS=json.dumps(NATIVE_PATHS))
        fake_bin = root / "bin"
        fake_bin.mkdir()
        env["PATH"] = str(fake_bin)
        dispatch = root / "dispatch.py"
        _write(dispatch, DISPATCH)
        if windows:
            # Functions cannot fall through to a real Git/Python/Kilo on PATH.
            launcher = root / "invoke.ps1"
            python = "'" + sys.executable.replace("'", "''") + "'"
            dispatcher = "'" + str(dispatch).replace("'", "''") + "'"
            _write(launcher, f'''
param([string]$Script)
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$global:LASTEXITCODE = 0
$PROFILE = $env:PROFILE
Set-Variable -Name HOME -Value $env:HOME -Force
function global:git {{
    $global:LASTEXITCODE = 0
    if ($args[0] -eq "tag") {{ return "v1.2.0.9022" }}
    if ($args[0] -eq "symbolic-ref") {{ return "refs/heads/main" }}
    if ($args[0] -eq "rev-parse") {{
        if ($args[1] -eq "--abbrev-ref") {{ return "main" }}
        return "abc123"
    }}
    if ($args[0] -notin @("checkout", "pull", "diff", "fetch")) {{
        throw "Unexpected fake Git call"
    }}
}}
function global:python3 {{
    $ErrorActionPreference = "Continue"
    & {python} {dispatcher} @args
    $global:LASTEXITCODE = $LASTEXITCODE
}}
if ($Script -like "*link.ps1") {{ & $Script "--platforms=kilo" "--yes" }}
else {{ & $Script }}
exit $LASTEXITCODE
''')
            command = [shell, "-NoProfile", "-NonInteractive",
                       "-ExecutionPolicy", "Bypass", "-File", str(launcher)]
        else:
            # Expose only required OS utilities, never the inherited Kilo PATH.
            for name in ("dirname", "tr", "xargs", "mktemp", "rm", "grep", "head",
                          "mv", "cp", "sed", "mkdir", "readlink", "ln", "basename"):
                utility = shutil.which(name)
                if utility is None:
                    pytest.skip(f"Required fixture utility unavailable: {name}")
                (fake_bin / name).symlink_to(utility)
            _write(fake_bin / "git", "#!/bin/sh\ncase \"$1 $2\" in\n"
                   "'rev-parse --abbrev-ref') echo main ;;\n"
                     "'rev-parse --short') echo abc123 ;;\n"
                     "'rev-parse --verify') echo abc123 ;;\n"
                     "'symbolic-ref --quiet') echo refs/heads/main ;;\n"
                    "'tag --list') echo v1.2.0.9022 ;;\n"
                    "'fetch --tags') ;;\n"
                    "'checkout .'|'checkout v1.2.0.9022'|'checkout --detach'|'checkout main'|'pull --ff-only'|'diff --quiet'|'diff --cached') ;;\n"
                   "*) exit 99 ;;\nesac\n")
            _write(fake_bin / "python3",
                   f"#!/bin/sh\nexec {shlex.quote(sys.executable)} "
                   f"{shlex.quote(str(dispatch))} \"$@\"\n")
            for name in ("git", "python3"):
                (fake_bin / name).chmod(0o755)
            command = [shell]
        yield Runtime(install, consumer, env, command, suffix)


def _seed(root: Path, state: str, source: bool) -> Path:
    """Seed all five paths and one receipt, e.g. a modified consumer projection."""
    records = {}
    for relative in NATIVE_PATHS:
        content = (relative + "\n").encode("ascii")
        _write(root / relative, content)
        records[relative] = dict(source=relative.replace(".kilo/", ".github/", 1),
                                 sha256=hashlib.sha256(content).hexdigest(),
                                 kind="native-plugin", executable=False,
                                 platform="kilo",
                                 preserved=False, origin="plugin-canonical",
                                 provenanceIdentity="canonical/.github")
    if source:
        receipt = root / ".kilo/.compound-gpid-generated.json"
        data = dict(schemaVersion=1, target="kilo", policyVersion=1,
                    files=[dict(path=key, **value) for key, value in records.items()])
        if state == "unowned":
            data["files"] = []
    else:
        receipt = root / ".compound-gpid/projection-ownership.json"
        data = dict(schemaVersion=1, entries={} if state == "unowned" else records)
    _write(receipt, '{"schemaVersion":1,' if state == "malformed" else json.dumps(data))
    if state == "modified":
        _write(root / NATIVE_PATHS[0], b"user-modified loader\n")
    return receipt


def _run(runtime: Runtime, operation: str, *,
         internal: bool = False) -> subprocess.CompletedProcess[str]:
    """Run a copied entrypoint, e.g. update-source with fake Git."""
    name = "link" if operation == "link" else "update"
    args = [str(runtime.install / f"scripts/{name}.{runtime.suffix}")]
    if name == "link" and runtime.suffix == "sh":
        args += ["--platforms=kilo", "--yes"]
    env = dict(runtime.env, CG_INTERNAL_CALL="1" if internal else "")
    cwd = runtime.install if operation.endswith("source") else runtime.consumer
    return subprocess.run([*runtime.command, *args], cwd=cwd, env=env,
                          capture_output=True, text=True, timeout=30, check=False)


def _events(runtime: Runtime) -> list[list[str]]:
    """Read fixture worker events, for example [retire, consumer-root]."""
    return [json.loads(line) for line in Path(runtime.env["NR_LOG"]).read_text(
        encoding="utf-8").splitlines()]


@pytest.mark.parametrize("operation", (
    "link", "update-source", "update-consumer", "update-pinned-source",
))
@pytest.mark.parametrize("state", ("owned", "modified", "unowned", "malformed"))
def test_retirement_precedes_refresh_and_preserved_residue_blocks(
    runtime: Runtime, operation: str, state: str,
) -> None:
    """Proven residue is retired; blockers preserve bytes and stop refresh."""
    source = operation.endswith("source")
    if operation == "update-pinned-source":
        _write(runtime.install / ".cg-version", "v1.2.0.9022")
    root = runtime.install if source else runtime.consumer
    receipt = _seed(root, state, source)
    paths = [root / path for path in NATIVE_PATHS] + [
        receipt, root / ".kilo/kilo.json",
        runtime.consumer / ".compound-gpid/managed-files.json",
        runtime.consumer / ".compound-gpid/active-manifest.json",
        runtime.consumer / "compound-gpid.local.md",
        Path(runtime.env["PROFILE"]),
        Path(runtime.env["HOME"]) / ".config/kilo/kilo.jsonc",
    ]
    before = {path: path.read_bytes() for path in paths}
    result = _run(runtime, operation)
    assert Path(runtime.env["NR_LOG"]).is_file(), result.stdout + result.stderr
    events = _events(runtime)
    assert events.count(["retire", str(root)]) == 1
    if operation == "link":
        assert "CG_SKIP_UPDATE=1" in result.stdout
    if state != "owned":
        assert result.returncode != 0
        assert "Preserved native-evidence file" in result.stdout + result.stderr
        reason = {"modified": "differs from its ownership checksum",
                  "unowned": "no valid ownership receipt",
                  "malformed": "invalid or unsafe ownership receipt"}[state]
        assert reason in result.stdout + result.stderr
        assert {path: path.read_bytes() for path in paths} == before
        assert events[-1] == ["retire", str(root)]
        assert not any(event[0] == "projection" for event in events)
        assert not source or not any(event[0] == "generate" for event in events)
        return
    assert result.returncode == 0, result.stdout + result.stderr
    assert all(not (root / path).exists() for path in NATIVE_PATHS)
    if operation == "update-pinned-source":
        assert receipt.read_bytes() == before[receipt]
    else:
        assert receipt.read_bytes() != before[receipt]
    expected = {"link": ["manifest", "retire", "projection"],
                 "update-source": ["retire", "generate"],
                 "update-pinned-source": ["validate", "retire"],
                "update-consumer": ["retire", "generate", "retire", "projection"]}
    assert [event[0] for event in events] == expected[operation]
    if not source:
        assert (root / ".kilo/kilo.json").read_bytes() == NEW_CONFIG
        managed = json.loads((root / ".compound-gpid/managed-files.json").read_text(
            encoding="utf-8-sig"))
        assert managed["files"][".kilo/kilo.json"]["checksum"] == hashlib.sha256(
            NEW_CONFIG).hexdigest()


def test_manifest_failure_prevents_retirement_and_refresh(runtime: Runtime) -> None:
    """Failed selection validation preserves owned residue and project state."""
    _seed(runtime.consumer, "owned", False)
    before = {path: path.read_bytes() for path in runtime.consumer.rglob("*")
              if path.is_file()}
    global_config = Path(runtime.env["HOME"]) / ".config/kilo/kilo.jsonc"
    config_before = global_config.read_bytes()
    runtime.env["NR_FAIL_MANIFEST"] = "1"
    result = _run(runtime, "link")
    assert result.returncode != 0
    assert "manifest resolution failure" in result.stdout + result.stderr
    assert {path: path.read_bytes() for path in before} == before
    assert global_config.read_bytes() == config_before
    assert _events(runtime) == [["manifest", str(runtime.consumer)]]


@pytest.mark.parametrize("mode", ("internal", "older-package"))
def test_update_preserves_internal_and_older_package_boundaries(
    runtime: Runtime, mode: str,
) -> None:
    """Internal calls leave consumer work to link; older helpers are optional."""
    internal = mode == "internal"
    if internal:
        receipt = _seed(runtime.consumer, "modified", False)
        paths = [receipt, runtime.consumer / NATIVE_PATHS[0],
                 runtime.consumer / ".kilo/kilo.json"]
        before = {path: path.read_bytes() for path in paths}
    else:
        (runtime.install / "scripts/cg_retire_native_evidence.py").unlink()
    result = _run(runtime, "update-consumer", internal=internal)
    assert result.returncode == 0, result.stdout + result.stderr
    if internal:
        assert {path: path.read_bytes() for path in paths} == before
        assert _events(runtime) == [
            ["retire", str(runtime.install)], ["generate", str(runtime.install)]]
    else:
        assert (runtime.consumer / ".kilo/kilo.json").read_bytes() == NEW_CONFIG
        assert _events(runtime) == [
            ["generate", str(runtime.install)], ["projection", str(runtime.consumer)]]
