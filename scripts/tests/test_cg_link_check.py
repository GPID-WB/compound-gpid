"""Read-only link checks in isolated Windows and POSIX HOME fixtures."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys

import pytest

import cg_link_check as checker
from cg_link_check_paths import legacy_rows
import cg_project_manifest as manifest_module
import cg_project_projection as projection
from scripts.tests.test_project_projection import _canonical_assets, _real_registry

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG = '---\nlanguage: "r"\nsuites: [cg]\n---\n'
NATIVE = ".kilo/plugins/cg-native-evidence.js"


def _write(path: Path, data: str | bytes) -> None:
    """Seed fixture content, never through a real lifecycle operation."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data.encode("utf-8") if isinstance(data, str) else data)


def _snapshot(root: Path) -> dict[str, tuple]:
    """Snapshot every file hash and directory, without following links."""
    result = {".": ("directory",)}
    pending = [root]
    while pending:
        directory = pending.pop()
        for path in sorted(directory.iterdir()):
            relative = path.relative_to(root).as_posix()
            metadata = path.lstat()
            if stat.S_ISLNK(metadata.st_mode) or getattr(metadata, "st_file_attributes", 0) & 0x400:
                result[relative] = ("link", str(path.resolve()))
            elif path.is_dir():
                result[relative] = ("directory",)
                pending.append(path)
            else:
                result[relative] = ("file", hashlib.sha256(path.read_bytes()).hexdigest())
    return result


@pytest.fixture(scope="module")
def source(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Copy worker code and seed a small canonical source, not an installation."""
    root = tmp_path_factory.mktemp("link-check-source")
    shutil.copytree(REPO_ROOT / "scripts", root / "scripts",
                    ignore=shutil.ignore_patterns("tests", "__pycache__", "*.pyc"))
    _real_registry(root)
    _canonical_assets(root)
    contracts = ".github/shared/skill-management/contracts"
    shutil.copytree(REPO_ROOT / contracts, root / contracts)
    mapping = ".github/shared/target-mapping.json"
    shutil.copy2(REPO_ROOT / mapping, root / mapping)
    _write(root / ".github/copilot-instructions.template.md", "# {{project-name}}\n")
    desired = manifest_module.resolve_active_manifest(
        root, config_text=CONFIG, platforms=["kilo"], source_root=root,
    )
    plan = projection.build_projection_plan(
        root, desired, project_root=root, config_text=CONFIG,
    )
    for entry in plan.entries:
        _write(root / entry.destination, entry.content)
    for directory in ("commands", "skills", "agents", "instructions", "shared"):
        (root / ".kilo" / directory).mkdir(exist_ok=True)
    # If a check ever falls through, update stops visibly before any mutation.
    _write(root / "scripts/update.ps1", 'Write-Host "UPDATE WAS CALLED"; exit 97\n')
    _write(root / "scripts/update.sh", '#!/bin/sh\nprintf "UPDATE WAS CALLED\\n"\nexit 97\n')
    return root


@pytest.fixture(params=("windows", "posix"))
def runtime(request: pytest.FixtureRequest, tmp_path: Path, source: Path) -> tuple:
    """Provide a platform shell and fake HOME with config/cache sentinels."""
    windows = request.param == "windows"
    if windows != (os.name == "nt"):
        pytest.skip("Fixture requires its native Windows or POSIX host")
    shell = shutil.which("powershell.exe" if windows else "bash")
    if shell is None:
        pytest.skip("Native fixture shell is unavailable")
    project, home = tmp_path / "project", tmp_path / "home"
    project.mkdir()
    home.mkdir()
    if windows:
        # PowerShell creates this standard profile directory before script entry.
        (home / "AppData/Roaming").mkdir(parents=True)
    _write(project / "user-file.txt", "project sentinel\n")
    _write(project / ".gitignore", "user-content/\n")
    _write(home / ".config/kilo/kilo.jsonc", '{"permission":{"existing":"deny"}}\n')
    _write(home / ".cache/keep.txt", "cache sentinel\n")
    _write(home / "profile.ps1", "# profile sentinel\n")
    (home / "empty-directory").mkdir()
    environment = {key: value for key, value in os.environ.items()
                   if not key.upper().startswith(("CG_", "KILO_", "GIT_", "PYTHON"))
                   and key.upper() not in ("BASH_ENV", "ENV")}
    for key in ("HOME", "USERPROFILE", "APPDATA", "LOCALAPPDATA",
                "XDG_CONFIG_HOME", "XDG_CACHE_HOME", "PYTHONPYCACHEPREFIX",
                "TEMP", "TMP", "TMPDIR"):
        environment[key] = str(home)
    environment["PATH"] = str(Path(sys.executable).parent) + os.pathsep + environment.get("PATH", "")
    command = ([shell, "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
                "-File", str(source / "scripts/link.ps1")] if windows
               else [shell, str(source / "scripts/link.sh")])
    return project, home, environment, command, source


@pytest.mark.parametrize("scenario", (
    "empty", "new-config", "linked-current", "old-manifest", "no-manifest",
    "modified-owned", "unowned-managed-path", "old-owned-leftover",
    "old-modified-leftover", "old-no-manifest-leftover",
    "9020-owned", "9021-owned", "9021-modified", "9021-unowned",
    "unchanged-old-owned", "unowned-identical", "pending-journal", "invalid-config",
))
def test_check_is_read_only_and_classifies_actions(runtime: tuple, scenario: str) -> None:
    """Check all project/HOME files and directory sets before and after CLI use."""
    project, home, env, command, source = runtime
    if scenario != "empty":
        _write(project / "compound-gpid.local.md", CONFIG)
    desired = manifest_module.resolve_active_manifest(
        project, config_text=CONFIG if scenario != "empty" else checker.DEFAULT_CONFIG,
        platforms=["kilo"], source_root=source,
    )
    plan = projection.build_projection_plan(
        source, desired, project_root=project,
        config_text=CONFIG if scenario != "empty" else checker.DEFAULT_CONFIG,
    )
    entries = {}
    planned = next(entry for entry in plan.entries if entry.kind == "command")
    if scenario == "linked-current":
        for entry in plan.entries:
            _write(project / entry.destination, entry.content)
            entries[entry.destination] = dict(
                sha256=entry.sha256, source=entry.source, kind=entry.kind,
                platform=entry.platform, origin=entry.origin,
                provenanceIdentity=entry.provenance_identity,
            )
        _write(project / manifest_module.ACTIVE_MANIFEST_PATH,
               manifest_module.canonical_manifest_bytes(desired))
    elif scenario == "old-manifest":
        _write(project / manifest_module.ACTIVE_MANIFEST_PATH,
               '{"schemaVersion":0,"installedVersion":"1.2.0.9021"}\n')
    elif scenario in ("unchanged-old-owned", "unowned-identical"):
        content = b"previous managed version\n" if scenario == "unchanged-old-owned" else planned.content
        _write(project / planned.destination, content)
        if scenario == "unchanged-old-owned":
            entries[planned.destination] = dict(sha256=hashlib.sha256(content).hexdigest())
    elif scenario in ("modified-owned", "unowned-managed-path"):
        _write(project / planned.destination, "user modification\n")
        if scenario == "modified-owned":
            entries[planned.destination] = dict(sha256=planned.sha256)
    elif "leftover" in scenario:
        stale = ".kilo/commands/old-command.md"
        _write(project / stale, "old command\n")
        if scenario != "old-no-manifest-leftover":
            entries[stale] = dict(sha256=hashlib.sha256(b"old command\n").hexdigest())
        if scenario == "old-modified-leftover":
            _write(project / stale, "modified old command\n")
    elif scenario.startswith("902"):
        _write(project / NATIVE, "old native loader\n")
        checksum = hashlib.sha256(b"old native loader\n").hexdigest()
        if scenario == "9020-owned":
            _write(project / ".kilo/.compound-gpid-generated.json", json.dumps(dict(
                schemaVersion=1, target="kilo", policyVersion=1,
                files=[dict(path=NATIVE, source=NATIVE.replace(".kilo/", ".github/", 1),
                            sha256=checksum, kind="native-plugin", executable=False)],
            )))
        elif scenario != "9021-unowned":
            _write(project / ".kilo/plugins/.compound-gpid-managed-copy.json",
                   json.dumps(dict(schemaVersion=1, source=".kilo/plugins",
                                   files={"cg-native-evidence.js": checksum})))
        if scenario == "9021-modified":
            _write(project / NATIVE, "modified native loader\n")
    elif scenario == "pending-journal":
        _write(project / manifest_module.TRANSACTION_JOURNAL_PATH,
               json.dumps(dict(schemaVersion=1, transactionId="old", state="prepared")))
    elif scenario == "invalid-config":
        _write(project / "compound-gpid.local.md", "---\nunknown-setting: invalid\n---\n")
    if entries:
        _write(project / manifest_module.OWNERSHIP_STATE_PATH,
               json.dumps(dict(schemaVersion=1, entries=entries,
                               activeAdapters={"kilo": ".kilo/AGENTS.md"})))
    before = (_snapshot(project), _snapshot(home), _snapshot(source))
    result = subprocess.run([*command, "--check", "--platforms=kilo"],
                            cwd=project, env=env, capture_output=True, text=True,
                            timeout=45, check=False)
    output = result.stdout + result.stderr
    assert (_snapshot(project), _snapshot(home), _snapshot(source)) == before
    assert "UPDATE WAS CALLED" not in output
    blocking = scenario in ("modified-owned", "unowned-managed-path",
                            "old-modified-leftover", "old-no-manifest-leftover",
                            "9021-modified", "9021-unowned", "pending-journal",
                            "invalid-config")
    assert result.returncode == int(blocking), output
    assert "Link Check (read-only)" in output
    if scenario != "invalid-config":
        assert "PATH | OWNER | CURRENT STATE | cg-link WOULD | REASON" in output
    assert "Manual action required:" in output
    if scenario == "modified-owned":
        assert f"{planned.destination} | modified-owned | file sha256=" in output
        assert "preserve/block" in output
    if scenario == "unowned-managed-path":
        assert f"{planned.destination} | unowned | file sha256=" in output
    if scenario.startswith("902"):
        assert "9020/9021 native-plugin residue:" in output
        assert f"{NATIVE} |" in output
        assert "remove" in output if not blocking else "retirement is all-or-nothing" in output
    if scenario == "old-owned-leftover":
        assert "old-version leftover" in output
    if scenario == "linked-current":
        assert "Current projection verification: 0 finding(s)" in output
    if scenario == "old-manifest":
        assert "old/invalid manifest" in output
    if scenario == "unchanged-old-owned":
        assert f"{planned.destination} | managed | file sha256=" in output
        assert " | update | matches the recorded ownership checksum" in output
    if scenario == "unowned-identical":
        assert " | keep/adopt | bytes already match the desired plan" in output


@pytest.mark.parametrize("arguments", (
    ["--unknown"], ["--check", "--unknown"], ["--help", "--unknown"],
    ["--platforms=kilo", "--yes", "--unknown=value"], ["typo"],
    ["--platforms"], ["--platforms="], ["--platforms", "--check"],
    ["--platforms=kilo,unknown"],
))
def test_invalid_usage_stops_before_update_or_writes(runtime: tuple, arguments: list[str]) -> None:
    """Unknown options/invalid values cannot start workers or the update path."""
    project, home, env, command, source = runtime
    before = (_snapshot(project), _snapshot(home), _snapshot(source))
    result = subprocess.run([*command, *arguments], cwd=project, env=env,
                            capture_output=True, text=True, timeout=30, check=False)
    output = result.stdout + result.stderr
    assert result.returncode == 2, output
    assert "Usage: cg-link" in output
    assert "UPDATE WAS CALLED" not in output
    assert "Link Check" not in output
    assert (_snapshot(project), _snapshot(home), _snapshot(source)) == before


def test_unknown_option_needs_no_mapping_helpers_or_python(runtime: tuple, tmp_path: Path) -> None:
    """Parse usage before loading installation metadata or resolving Python."""
    project, home, env, command, _ = runtime
    missing = tmp_path / "missing-source"
    missing.mkdir()
    script = missing / Path(command[-1]).name
    shutil.copy2(command[-1], script)
    restricted = dict(env, PATH="")
    before = (_snapshot(project), _snapshot(home), _snapshot(missing))
    result = subprocess.run([*command[:-1], str(script), "--unknown"],
                            cwd=project, env=restricted, capture_output=True,
                            text=True, timeout=30, check=False)
    assert result.returncode == 2, result.stdout + result.stderr
    assert "Usage: cg-link" in result.stdout + result.stderr
    assert (_snapshot(project), _snapshot(home), _snapshot(missing)) == before


def test_read_only_python_invocations_disable_bytecode() -> None:
    """Both entrypoints and Python discovery probes explicitly use -B."""
    powershell = (REPO_ROOT / "scripts/link.ps1").read_text(encoding="utf-8")
    shell = (REPO_ROOT / "scripts/link.sh").read_text(encoding="utf-8")
    helpers = (REPO_ROOT / "scripts/helpers.ps1").read_text(encoding="utf-8")
    assert "Resolve-PythonCommand -NoBytecode" in powershell
    assert '& $checkPython -B' in powershell
    assert 'exec "$PYTHON_CMD" -B "$SCRIPT_DIR/cg_link_check.py"' in shell
    assert "probe_args=(-B)" in shell
    assert '$probeArgs = @("-B")' in helpers


def test_report_retains_marker_only_overwrite_policy(tmp_path: Path) -> None:
    """Reporting a marker-owned edit must not implement the Step3b fix."""
    project, source = tmp_path / "project", tmp_path / "source"
    relative = ".github/copilot-instructions.md"
    _write(project / relative, "<!-- compound-gpid:managed -->\nuser edit\n")
    _write(source / "template.md", "desired template\n")
    units = [dict(installUnits=[dict(type="file", target=relative,
                                   source="template.md", strategy="generated-copy")])]
    before = _snapshot(project)
    rows = legacy_rows(project, source, units, {relative: {"checksum": "a" * 64}}, False, False)
    assert rows[0]["owner"] == "modified-owned"
    assert rows[0]["action"] == "regenerate"
    assert "Step3b" in rows[0]["reason"]
    assert _snapshot(project) == before
