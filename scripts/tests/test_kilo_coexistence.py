"""Tests for the contained Kilo/Codex coexistence boundary."""
from __future__ import annotations

import json
import os
from pathlib import Path
import stat
import shutil
import subprocess
import sys

import pytest

import cg_kilo_preflight as preflight


REPO_ROOT = Path(__file__).resolve().parents[2]
EVIDENCE_PATH = REPO_ROOT / "scripts/tests/fixtures/kilo_coexistence_host.json"


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _projection(root: Path, *, codex: bool = True, claude: bool = False) -> None:
    for relative in preflight.REQUIRED_LOCAL_ROOTS:
        (root / relative).mkdir(parents=True, exist_ok=True)
    _write(
        root / ".kilo/skills/cg-local-sentinel/SKILL.md",
        "---\nname: cg-local-sentinel\ndescription: local sentinel\n---\n\n# Local\n",
    )
    _write(
        root / ".kilo/agents/cg-local-agent.md",
        "---\ndescription: local agent\nmode: subagent\n---\n\n# Agent\n",
    )
    if codex:
        _write(
            root / ".agents/skills/cg-codex-sentinel/SKILL.md",
            "---\nname: cg-codex-sentinel\ndescription: codex sentinel\n---\n",
        )
    if claude:
        _write(
            root / ".claude/skills/cg-claude-sentinel/SKILL.md",
            "---\nname: cg-claude-sentinel\ndescription: claude sentinel\n---\n",
        )


def _fake_kilo(
    path: Path,
    inventory_log: Path,
    *,
    ignore_containment: bool = False,
    version: str = "7.4.21",
    version_returncode: int = 0,
) -> Path:
    """Create a host fixture that honors the containment variable."""
    script = path.with_suffix(".py")
    ignore_containment_literal = "True" if ignore_containment else "False"
    host_script = """#!/usr/bin/env python3
import json, os, pathlib, sys
args = sys.argv[1:]
if args == ['--version']:
    print(__VERSION__)
    raise SystemExit(__VERSION_RETURNCODE__)
if args[:2] == ['debug', 'skill']:
    root = pathlib.Path.cwd()
    records = [{'name': 'cg-local-sentinel', 'location': str(root / '.kilo/skills/cg-local-sentinel/SKILL.md')}]
    if (root / '.agents/skills').is_dir() and (os.environ.get('KILO_DISABLE_EXTERNAL_SKILLS') != '1' or __IGNORE_CONTAINMENT__):
        records.append({'name': 'cg-codex-sentinel', 'location': str(root / '.agents/skills/cg-codex-sentinel/SKILL.md')})
    if (root / '.claude/skills').is_dir() and (os.environ.get('KILO_DISABLE_EXTERNAL_SKILLS') != '1' or __IGNORE_CONTAINMENT__):
        records.append({'name': 'cg-claude-sentinel', 'location': str(root / '.claude/skills/cg-claude-sentinel/SKILL.md')})
    print(json.dumps(records))
    raise SystemExit(0)
pathlib.Path(os.environ['CG_KILO_TEST_LOG']).write_text(json.dumps({'args': args, 'containment': os.environ.get('KILO_DISABLE_EXTERNAL_SKILLS')}), encoding='utf-8')
raise SystemExit(23)
""".replace("__IGNORE_CONTAINMENT__", ignore_containment_literal).replace("__VERSION__", repr(version)).replace("__VERSION_RETURNCODE__", str(version_returncode))
    script.write_text(
        host_script,
        encoding="utf-8",
    )
    if os.name != "nt":
        script.chmod(script.stat().st_mode | stat.S_IXUSR)
        return script
    wrapper = path.with_suffix(".cmd")
    wrapper.write_text(f'@echo off\n"{sys.executable}" "{script}" %*\n', encoding="ascii")
    return wrapper


def test_inventory_summary_preserves_names_and_separates_external_roots() -> None:
    summary = preflight.summarise_inventory(
        [
            {"name": "local", "location": "C:/project/.kilo/skills/local/SKILL.md"},
            {"name": "codex", "location": "C:/project/.agents/skills/codex/SKILL.md"},
        ]
    )
    assert summary.names == ("codex", "local")
    assert summary.external_compatibility_locations == (
        "C:/project/.agents/skills/codex/SKILL.md",
    )


def test_preflight_blocks_missing_local_projection(tmp_path: Path) -> None:
    result = preflight.run_preflight(tmp_path, require_host_inventory=False)
    assert result.status == preflight.PreflightStatus.LOCAL_PROJECTION_MISSING
    assert result.exit_code == preflight.EXIT_CONFIGURATION


def test_preflight_distinguishes_local_content_failure_from_host_failure(tmp_path: Path) -> None:
    _projection(tmp_path, codex=False)
    (tmp_path / ".kilo/skills/cg-local-sentinel/SKILL.md").write_bytes(b"\xff\xfe")
    result = preflight.run_preflight(tmp_path, require_host_inventory=False)
    assert result.status == preflight.PreflightStatus.LOCAL_CONTENT_INVALID
    assert "UTF-8" in result.message


@pytest.mark.parametrize(
    "version,version_returncode,warning",
    [
        ("7.4.21", 0, False),
        ("7.4.19", 0, True),
        ("6.99.99", 0, True),
        ("unreadable", 0, True),
        ("7.4.21", 1, True),
    ],
)
def test_contained_launch_preserves_caller_environment_and_relays_child_status(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    version: str,
    version_returncode: int,
    warning: bool,
) -> None:
    _projection(tmp_path, codex=True)
    log_path = tmp_path / "child-args.json"
    fake = _fake_kilo(
        tmp_path / "fake-kilo", log_path,
        version=version, version_returncode=version_returncode,
    )
    monkeypatch.setenv("CG_KILO_TEST_LOG", str(log_path))
    monkeypatch.delenv(preflight.CONTAINMENT_ENVIRONMENT, raising=False)

    result = preflight.main(
        [
            "--root",
            str(tmp_path),
            "--kilo-executable",
            str(fake),
            "--launch",
            "--",
            "--test-argument",
        ]
    )

    assert result == 23
    assert os.environ.get(preflight.CONTAINMENT_ENVIRONMENT) is None
    child = json.loads(log_path.read_text(encoding="utf-8"))
    assert child["args"] == ["--test-argument"]
    assert child["containment"] == "1"
    output = capsys.readouterr().out
    assert ("WARNING:" in output) is warning
    assert "BLOCKED" not in output


def test_certified_preflight_blocks_uncontained_inventory(tmp_path: Path) -> None:
    _projection(tmp_path, codex=True)
    fake = _fake_kilo(
        tmp_path / "fake-kilo", tmp_path / "child-args.json", ignore_containment=True
    )
    result = preflight.run_preflight(tmp_path, kilo_executable=str(fake))
    assert result.exit_code == preflight.EXIT_CONTAINMENT
    assert result.status == preflight.PreflightStatus.CONTAINMENT_UNHONORED
    assert result.certified_launch_required is True
    assert result.direct_launch_supported is False
    assert result.containment_environment == preflight.CONTAINMENT_ENVIRONMENT


@pytest.mark.parametrize("roots", [(False, True), (True, True)])
def test_claude_and_mixed_compatibility_roots_are_contained(
    tmp_path: Path, roots: tuple[bool, bool]
) -> None:
    codex, claude = roots
    _projection(tmp_path, codex=codex, claude=claude)
    fake = _fake_kilo(tmp_path / "fake-kilo", tmp_path / "child-args.json")
    result = preflight.run_preflight(tmp_path, kilo_executable=str(fake))
    assert result.exit_code == preflight.EXIT_OK
    assert result.status == preflight.PreflightStatus.OK
    assert result.inventory.external_compatibility_locations == ()


def test_no_codex_root_does_not_require_certified_coexistence(tmp_path: Path) -> None:
    _projection(tmp_path, codex=False)
    fake = _fake_kilo(tmp_path / "fake-kilo", tmp_path / "child-args.json")
    result = preflight.run_preflight(tmp_path, kilo_executable=str(fake))
    assert result.status == preflight.PreflightStatus.NO_COEXISTENCE
    assert result.certified_launch_required is False
    assert result.direct_launch_supported is True


def test_host_evidence_fixture_is_machine_readable() -> None:
    data = json.loads(EVIDENCE_PATH.read_text(encoding="utf-8"))
    assert data["schemaVersion"] == "compound-gpid-kilo-coexistence-v1"
    assert data["containment"]["environment"] == "KILO_DISABLE_EXTERNAL_SKILLS"
    assert data["containment"]["scope"] == "child-process-only"
    assert data["hosts"]
    for host in data["hosts"]:
        assert preflight.VERSION_PATTERN.fullmatch(host["version"])
        assert host["invocation"] == ["kilo", "debug", "skill"]
        assert host["contained"]["localSkill"] is True
        assert host["contained"]["codexSkill"] is False
        assert host["contained"]["claudeSkill"] is False


@pytest.mark.integration
def test_current_embedded_kilo_hosts_match_containment_contract(tmp_path: Path) -> None:
    """Check containment when an embedded editor host is installed."""
    configured = os.environ.get("CG_KILO_CERTIFIED_EXECUTABLE")
    if configured:
        executables = [Path(configured)]
        if not executables[0].is_file():
            pytest.fail(f"Configured certified Kilo executable does not exist: {configured}")
    else:
        executables = []
        for root in (
            Path.home() / ".vscode/extensions",
            Path.home() / ".positron/extensions",
        ):
            if root.is_dir():
                executables.extend(root.glob("kilocode.kilo-code-*/bin/kilo.exe" if os.name == "nt" else "kilocode.kilo-code-*/bin/kilo"))
    if not executables:
        pytest.skip("No embedded Kilo host is installed on this machine")

    _projection(tmp_path, codex=True)
    for executable in executables:
        result = preflight.run_preflight(tmp_path, kilo_executable=str(executable))
        assert result.exit_code == preflight.EXIT_OK
        assert result.inventory.external_compatibility_locations == ()


@pytest.mark.parametrize("version", ["6.99.99", "7.4.19", "7.4.20", "7.5.16", "7.10.0", "8.0.0", "10.0.0", "unreadable"])
@pytest.mark.parametrize("ignore_containment", [False, True])
def test_all_host_versions_require_live_containment(tmp_path: Path, version: str, ignore_containment: bool) -> None:
    _projection(tmp_path)
    fake = _fake_kilo(tmp_path / "fake-kilo", tmp_path / "log", version=version, ignore_containment=ignore_containment)
    result = preflight.run_preflight(tmp_path, kilo_executable=str(fake))
    assert result.kilo_version == (None if version == "unreadable" else version)
    assert result.exit_code == (preflight.EXIT_CONTAINMENT if ignore_containment else preflight.EXIT_OK)


@pytest.mark.parametrize("version", ["7.4.19", "6.99.99", "7.5", "7.5.16.1", "7.5.16-bad", "garbage7.5.16", "07.5.16", "7.5.16\n8.0.0", ""])
def test_old_or_unreadable_host_version_warns_without_blocking(tmp_path: Path, version: str, monkeypatch: pytest.MonkeyPatch) -> None:
    _projection(tmp_path)
    fake = _fake_kilo(tmp_path / "fake-kilo", tmp_path / "log", version=version)
    monkeypatch.setattr(preflight, "_candidate_kilo_executables", lambda explicit: [fake])
    result = preflight.run_preflight(tmp_path, kilo_executable=str(fake))
    assert result.status == preflight.PreflightStatus.OK
    assert result.exit_code == preflight.EXIT_OK
    assert result.host_evidence == "verified-contained"
    assert len(result.warnings) == 1
    assert result.inventory.external_compatibility_locations == ()
    assert result.containment_environment == preflight.CONTAINMENT_ENVIRONMENT
    assert result.kilo_version == (version if version in {"7.4.19", "6.99.99"} else None)
    assert result.as_json()["warnings"] == list(result.warnings)


@pytest.mark.parametrize(
    "reason,status,exit_code",
    [
        ("command", preflight.PreflightStatus.HOST_COMMAND_ERROR, preflight.EXIT_HOST_UNAVAILABLE),
        ("syntax", preflight.PreflightStatus.HOST_SCHEMA_ERROR, preflight.EXIT_HOST_SCHEMA),
        ("schema", preflight.PreflightStatus.HOST_SCHEMA_ERROR, preflight.EXIT_HOST_SCHEMA),
        ("output", preflight.PreflightStatus.HOST_SCHEMA_ERROR, preflight.EXIT_HOST_SCHEMA),
    ],
)
def test_version_warning_does_not_override_host_inventory_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    reason: str,
    status: str,
    exit_code: int,
) -> None:
    _projection(tmp_path)
    fake = _fake_kilo(tmp_path / "fake-kilo", tmp_path / "log", version="unreadable")
    monkeypatch.setattr(
        preflight, "_inventory",
        lambda *args, **kwargs: (None, reason, "inventory failed"),
    )
    result = preflight.run_preflight(tmp_path, kilo_executable=str(fake))
    assert result.status == status
    assert result.exit_code == exit_code
    assert result.message == "inventory failed"
    assert result.warnings


def test_local_only_preflight_does_not_resolve_or_query_kilo(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _projection(tmp_path)
    monkeypatch.setattr(
        preflight, "resolve_kilo_executable",
        lambda *args: pytest.fail("local-only validation must not resolve Kilo"),
    )
    result = preflight.run_preflight(tmp_path, require_host_inventory=False)
    assert result.exit_code == preflight.EXIT_OK
    assert result.host_evidence == "not-run"
    assert result.kilo_version is None
    assert result.warnings == ()


@pytest.mark.parametrize("version", ["7.5.16", "8.0.0", "7.4.19", "7.5.16.1"])
def test_updater_input_validation_is_independent_of_host_version(tmp_path: Path, version: str) -> None:
    """Exercise the actual updater, stopping at invalid input before any Git write."""
    shell = shutil.which("powershell" if os.name == "nt" else "bash")
    if not shell:
        pytest.skip("Native updater shell is unavailable")
    install = tmp_path / "install/scripts"
    install.mkdir(parents=True)
    extension = "ps1" if os.name == "nt" else "sh"
    for name in (f"update.{extension}", "helpers.ps1", "cg_kilo_preflight.py"):
        shutil.copyfile(REPO_ROOT / "scripts" / name, install / name)
    consumer = tmp_path / "consumer"
    _projection(consumer)
    host_dir = tmp_path / "host"
    host_dir.mkdir()
    fake = _fake_kilo(host_dir / "kilo", tmp_path / "log", version=version)
    if os.name != "nt":
        fake.rename(host_dir / "kilo")
    home = tmp_path / "home"
    home.mkdir()
    environment = os.environ.copy()
    environment.update(HOME=str(home), USERPROFILE=str(home), PATH=str(host_dir) + os.pathsep + os.environ["PATH"])
    environment.pop("CG_INTERNAL_CALL", None)
    if os.name == "nt":
        script_path = str(install / "update.ps1").replace("'", "''")
        profile = str(home / "profile.ps1").replace("'", "''")
        command = [shell, "-NoProfile", "-NonInteractive", "-Command", f"$PROFILE = '{profile}'; & '{script_path}' -Version invalid-test-version"]
    else:
        command = [shell, str(install / "update.sh"), "invalid-test-version"]
    result = subprocess.run(command, cwd=consumer, env=environment, capture_output=True, text=True, timeout=90)
    output = result.stdout + result.stderr
    assert result.returncode != 0
    assert "Invalid version:" in output
    assert "unsupported-kilo-version" not in output
    assert not (install.parent / ".cg-version").exists()


@pytest.mark.parametrize("version", ["7.4.19", "unreadable"])
def test_host_selection_does_not_discard_old_or_unreadable_candidate(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, version: str
) -> None:
    older, newer = tmp_path / "old", tmp_path / "new"
    monkeypatch.setattr(preflight, "_candidate_kilo_executables", lambda explicit: [older, newer])
    monkeypatch.setattr(preflight, "_read_version", lambda path, root: (version if path == older else "7.5.16", None))
    assert preflight.resolve_kilo_executable() == older


def test_unreadable_version_warning_is_machine_readable(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _projection(tmp_path)
    fake = _fake_kilo(tmp_path / "fake-kilo", tmp_path / "log", version="unreadable")
    result = preflight.main(["--root", str(tmp_path), "--kilo-executable", str(fake), "--json"])
    assert result == preflight.EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == preflight.PreflightStatus.OK
    assert payload["kilo_version"] is None
    assert "not recognized" in payload["warnings"][0]
    assert payload["host_evidence"] == "verified-contained"
