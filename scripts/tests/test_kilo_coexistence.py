"""Tests for the certified Kilo/Codex coexistence boundary."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import stat
import shutil
import subprocess
import sys
from datetime import datetime, timezone

import pytest

import cg_kilo_preflight as preflight


REPO_ROOT = Path(__file__).resolve().parents[2]
EVIDENCE_PATH = REPO_ROOT / "scripts/tests/fixtures/kilo_coexistence_host.json"


@pytest.mark.parametrize("version", [
    "7.4.20", "7.4.23", "7.5.0", "8.0.0", "99.0.0",
    "7.4.20-beta.1", "7.4.23-rc.2", "7.5.0-alpha.1+build.5",
])
def test_step7_minimum_only_host_compatibility(version, tmp_path, monkeypatch):
    _projection(tmp_path, codex=True)
    fake = _fake_kilo(tmp_path / "fake-kilo", tmp_path / "args.json")
    monkeypatch.setattr(preflight, "_read_version", lambda *_: (version, None))
    result = preflight.run_preflight(tmp_path, kilo_executable=str(fake))
    assert result.exit_code == 0, result.message


@pytest.mark.parametrize("version", ["7.4.19", "7.4.19-rc.1", "6.99.99", "6.99.99-alpha.2", None])
def test_step7_minimum_and_missing_version_fail_closed(version, tmp_path, monkeypatch):
    _projection(tmp_path, codex=True)
    fake = _fake_kilo(tmp_path / "fake-kilo", tmp_path / "args.json")
    monkeypatch.setattr(preflight, "_read_version", lambda *_: (version, None))
    assert preflight.run_preflight(tmp_path, kilo_executable=str(fake)).exit_code == preflight.EXIT_HOST_UNAVAILABLE


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


def _fake_kilo(path: Path, inventory_log: Path, *, ignore_containment: bool = False, version: str = "7.4.21") -> Path:
    """Create a host fixture that honors the containment variable."""
    script = path.with_suffix(".py")
    ignore_containment_literal = "True" if ignore_containment else "False"
    host_script = """#!/usr/bin/env python3
import json, os, pathlib, sys
args = sys.argv[1:]
if args == ['--version']:
    print(__VERSION__)
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
""".replace("__IGNORE_CONTAINMENT__", ignore_containment_literal).replace("__VERSION__", repr(version))
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


def _fake_kilo_version_output(path: Path, printed: str) -> Path:
    """Create a host fixture printing a fixed ``--version`` output."""
    script = path.with_suffix(".py")
    script.write_text(
        "import sys\n"
        "if sys.argv[1:] == ['--version']:\n"
        + "    print(" + repr(printed) + ")\n"
        + "    raise SystemExit(0)\n"
        + "raise SystemExit(23)\n",
        encoding="utf-8",
    )
    if os.name != "nt":
        script.chmod(script.stat().st_mode | stat.S_IXUSR)
        return script
    wrapper = path.with_suffix(".cmd")
    wrapper.write_text(f'@echo off\n"{sys.executable}" "{script}" %*\n', encoding="ascii")
    return wrapper


@pytest.mark.parametrize("printed", ["v7.4.20", "7.4.20.1", "Kilo 7.4.20", "version: 7.4.20"])
def test_read_version_rejects_embedded_prefixed_suffixed_output(tmp_path: Path, printed: str) -> None:
    fake = _fake_kilo_version_output(tmp_path / "fake-kilo", printed)
    version, error = preflight._read_version(fake, tmp_path)
    assert version is None
    assert error == "Kilo version output was not recognized"


def test_read_version_parses_only_the_first_non_empty_line(tmp_path: Path) -> None:
    fake = _fake_kilo_version_output(tmp_path / "fake-kilo", "7.4.21\nunrelated trailing banner\n")
    version, error = preflight._read_version(fake, tmp_path)
    assert version == "7.4.21"
    assert error is None


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
        assert preflight.supported_kilo_version(host["version"])
        assert host["invocation"] == ["kilo", "debug", "skill"]
        assert host["contained"]["localSkill"] is True
        assert host["contained"]["codexSkill"] is False
        assert host["contained"]["claudeSkill"] is False


@pytest.mark.integration
def test_current_embedded_kilo_hosts_match_containment_contract(tmp_path: Path) -> None:
    """Run the supported-host proof when an embedded editor host is installed."""
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
        version, error = preflight._read_version(executable, tmp_path)
        if error or not preflight.supported_kilo_version(version):
            pytest.fail(f"Unsupported embedded Kilo host: {executable} ({version or error})")
        result = preflight.run_preflight(tmp_path, kilo_executable=str(executable))
        assert result.exit_code == preflight.EXIT_OK
        assert result.inventory.external_compatibility_locations == ()


@pytest.mark.integration
def test_certified_kilo_help_observed_flows(tmp_path: Path) -> None:
    """Run only an explicitly configured exact-subject host, never auto-discover one."""
    from help import catalog, support
    from scripts.tests.test_cg_help import project
    configured = os.environ.get("CG_KILO_CERTIFIED_EXECUTABLE")
    if not configured:
        pytest.skip("No explicitly configured certified Kilo host")
    subject = os.environ.get("CG_HELP_SUBJECT_COMMIT", "")
    support._commit(REPO_ROOT, subject)
    assert support._git(REPO_ROOT, "rev-parse", "HEAD").decode().strip() == subject
    assert subprocess.run(["git", "symbolic-ref", "-q", "HEAD"], cwd=REPO_ROOT,
                          capture_output=True).returncode == 1
    catalog.check_catalog(REPO_ROOT)
    bindings = support.subject_bindings(REPO_ROOT, subject)
    assert bindings == support.subject_bindings(REPO_ROOT, subject)
    version = os.environ["CG_KILO_CERTIFIED_VERSION"]
    executable_hash = os.environ["CG_KILO_CERTIFIED_SHA256"].lower()
    executable = Path(configured).resolve(strict=True)
    assert preflight._file_sha256(executable) == executable_hash
    assert preflight._read_version(executable, REPO_ROOT) == (version, None)
    outcomes = []
    for name, text in support.PROBE_CASES.items():
        root = tmp_path / name
        for relative in preflight.REQUIRED_LOCAL_ROOTS:
            shutil.copytree(REPO_ROOT / relative, root / relative)
        project(REPO_ROOT, root, "cg, cr", "kilo")
        shutil.copyfile(REPO_ROOT / ".kilo/kilo.json", root / "kilo.json")
        bin_dir, receipts = root / "probe-bin", tmp_path / (name + "-receipts")
        bin_dir.mkdir()
        receipts.mkdir()
        observer = bin_dir / "observer.py"
        observer.write_bytes((
            "import hashlib,io,json,sys,uuid\nfrom pathlib import Path\n"
            + "sys.path.insert(0," + repr(str(REPO_ROOT / "scripts")) + ")\n"
            + "import cg_help\noriginal=cg_help.query_service\nseen=[]\n"
            + "def observe(text,**kwargs):\n seen.append(hashlib.sha256(text.encode('utf-8')).hexdigest())\n return original(text,**kwargs)\n"
            + "cg_help.query_service=observe\nstream=sys.stdout\nsys.stdout=io.StringIO()\n"
            + "status=cg_help.main(sys.argv[1:])\noutput=sys.stdout.getvalue()\nsys.stdout=stream\n"
            + "payload=dict(argv=sys.argv[1:],exitCode=status,envelope=json.loads(output),queryFingerprints=seen)\n"
            + "destination=Path(" + repr(str(receipts)) + ")/(str(uuid.uuid4())+'.json')\n"
            + "destination.write_bytes(json.dumps(payload).encode('utf-8'))\nstream.write(output)\nraise SystemExit(status)\n"
        ).encode("utf-8"))
        if os.name == "nt":
            _write(bin_dir / "cg-help.cmd", '@echo off\n"{}" "{}" %*\n'.format(sys.executable, observer))
        else:
            import shlex
            wrapper = bin_dir / "cg-help"
            _write(wrapper, "#!/bin/sh\nexec {} {} \"$@\"\n".format(shlex.quote(sys.executable), shlex.quote(str(observer))))
            wrapper.chmod(0o700)
        host = preflight.run_preflight(root, kilo_executable=str(executable), force_certified_launch=True)
        assert host.exit_code == 0
        assert host.kilo_version == version and host.kilo_executable_sha256 == executable_hash
        environment = os.environ.copy()
        environment[preflight.CONTAINMENT_ENVIRONMENT] = "1"
        environment["PATH"] = str(bin_dir) + os.pathsep + environment.get("PATH", "")
        # Native host argv carries public fixture input as data, never shell text.
        result = subprocess.run([str(executable), *support.PROBE_ARGUMENTS, text],
                                cwd=root, env=environment, capture_output=True, timeout=180, check=False)
        assert result.returncode == 0, "Certified host command failed"
        assert len(result.stdout) <= preflight.MAX_HOST_OUTPUT_BYTES
        events = [catalog.load_strict_json_bytes(line, source="host event") for line in result.stdout.splitlines() if line.strip()]
        final = "".join(event["part"]["text"] for event in events if event.get("type") == "text")
        commands = [event["part"]["state"]["input"]["command"] for event in events
                    if event.get("type") == "tool_use" and event.get("part", {}).get("tool") == "bash"]
        order = {"request-prepared": 0, "query-completed": 1, "selection-prepared": 1, "selection-rendered": 2}
        records = [catalog.load_strict_json(path) for path in receipts.glob("*.json")]
        records.sort(key=lambda record: order.get(record["envelope"].get("operation"), 99))
        outcomes.append(support.validate_host_flow(name, records, final, commands))
    # A bounded probe fragment is not the canonical combined support artifact.
    fragment = dict(subjectCommit=subject, probeCommit=subject,
                    probeTree=support._git(REPO_ROOT, "rev-parse", "HEAD^{tree}").decode().strip(),
                    host={"pinnedVersion": version, "observedVersion": version,
                          "pinnedSha256": executable_hash, "observedSha256": executable_hash},
                    probes=outcomes, runAt=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), **bindings)
    assert preflight._file_sha256(executable) == executable_hash
    (REPO_ROOT / "kilo-help-probes.json").write_bytes(json.dumps(fragment, sort_keys=True).encode("utf-8"))


@pytest.mark.parametrize("version", ["7.4.20", "7.5.16", "7.10.0", "8.0.0", "10.0.0"])
@pytest.mark.parametrize("ignore_containment", [False, True])
def test_newer_hosts_require_live_containment(tmp_path: Path, version: str, ignore_containment: bool) -> None:
    _projection(tmp_path)
    fake = _fake_kilo(tmp_path / "fake-kilo", tmp_path / "log", version=version, ignore_containment=ignore_containment)
    result = preflight.run_preflight(tmp_path, kilo_executable=str(fake))
    assert result.kilo_version == version
    assert result.exit_code == (preflight.EXIT_CONTAINMENT if ignore_containment else preflight.EXIT_OK)


@pytest.mark.parametrize("version", ["7.4.19", "6.99.99", "7.5", "7.5.16.1", "garbage7.5.16", "7.5.16\n8.0.0", ""])
def test_unsupported_or_malformed_host_version(tmp_path: Path, version: str, monkeypatch: pytest.MonkeyPatch) -> None:
    _projection(tmp_path)
    fake = _fake_kilo(tmp_path / "fake-kilo", tmp_path / "log", version=version)
    monkeypatch.setattr(preflight, "_candidate_kilo_executables", lambda explicit: [fake])
    result = preflight.run_preflight(tmp_path, kilo_executable=str(fake))
    assert result.status == preflight.PreflightStatus.UNSUPPORTED_VERSION
    assert result.exit_code == preflight.EXIT_HOST_UNAVAILABLE
    assert result.host_evidence == "unavailable"


@pytest.mark.parametrize("version,blocked", [("7.5.16", False), ("8.0.0", False), ("7.4.19", True), ("7.5.16.1", True)])
def test_updater_early_guard_uses_minimum_policy(tmp_path: Path, version: str, blocked: bool) -> None:
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
    if blocked:
        assert "unsupported-kilo-version" in output
        assert "Invalid version:" not in output
    else:
        assert "Invalid version:" in output
        assert "unsupported-kilo-version" not in output
    assert not (install.parent / ".cg-version").exists()


def test_host_selection_accepts_newer_candidate(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    older, newer = tmp_path / "old", tmp_path / "new"
    monkeypatch.setattr(preflight, "_candidate_kilo_executables", lambda explicit: [older, newer])
    monkeypatch.setattr(preflight, "_read_version", lambda path, root: ("7.4.19" if path == older else "7.5.16", None))
    assert preflight.resolve_kilo_executable() == newer
