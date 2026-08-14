"""Tests for the certified Kilo/Codex coexistence boundary."""
from __future__ import annotations

import json
import os
from pathlib import Path
import stat
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


def _fake_kilo(path: Path, inventory_log: Path, *, ignore_containment: bool = False) -> Path:
    """Create a host fixture that honors the containment variable."""
    script = path.with_suffix(".py")
    ignore_containment_literal = "True" if ignore_containment else "False"
    host_script = """import json, os, pathlib, sys
args = sys.argv[1:]
if args == ['--version']:
    print('7.4.21')
    raise SystemExit(0)
if args[:2] == ['debug', 'skill']:
    root = pathlib.Path.cwd()
    records = [{'name': 'cg-local-sentinel', 'location': str(root / '.kilo/skills/cg-local-sentinel/SKILL.md')}]
    if (root / '.agents/skills').is_dir() and (os.environ.get('KILO_DISABLE_EXTERNAL_SKILLS') != '1' or __IGNORE_CONTAINMENT__):
        records.append({'name': 'cg-codex-sentinel', 'location': str(root / '.agents/skills/cg-codex-sentinel/SKILL.md')})
    if (root / '.claude/skills').is_dir() and (os.environ.get('KILO_DISABLE_EXTERNAL_SKILLS') != '1' or __IGNORE_CONTAINMENT__):
        records.append({'name': 'cg-claude-sentinel', 'location': str(root / '.claude/skills/cg-claude-sentinel/SKILL.md')})
    print(json.dumps(records))
    raise SystemExit(0)
pathlib.Path(os.environ['CG_KILO_TEST_LOG']).write_text(json.dumps(args), encoding='utf-8')
raise SystemExit(23)
""".replace("__IGNORE_CONTAINMENT__", ignore_containment_literal)
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


def test_certified_launch_preserves_caller_environment_and_relays_child_status(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _projection(tmp_path, codex=True)
    log_path = tmp_path / "child-args.json"
    fake = _fake_kilo(tmp_path / "fake-kilo", log_path)
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
    assert json.loads(log_path.read_text(encoding="utf-8")) == ["--test-argument"]


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
        assert host["version"] in preflight.SUPPORTED_KILO_VERSIONS
        assert host["invocation"] == ["kilo", "debug", "skill"]
        assert host["contained"]["localSkill"] is True
        assert host["contained"]["codexSkill"] is False
        assert host["contained"]["claudeSkill"] is False


@pytest.mark.integration
def test_current_embedded_kilo_hosts_match_containment_contract(tmp_path: Path) -> None:
    """Run the supported-host proof when an embedded editor host is installed."""
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
        version, error = preflight._read_version(executable, tmp_path)
        if error or version not in preflight.SUPPORTED_KILO_VERSIONS:
            pytest.fail(f"Unsupported embedded Kilo host: {executable} ({version or error})")
        result = preflight.run_preflight(tmp_path, kilo_executable=str(executable))
        assert result.exit_code == preflight.EXIT_OK
        assert result.inventory.external_compatibility_locations == ()
