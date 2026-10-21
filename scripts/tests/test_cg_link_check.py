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
from parsing_utils import LEGACY_CONFIG_NOTE
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
        root, config_text=CONFIG,
        platforms=["kilo", "codex", "claude-code", "opencode"], source_root=root,
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
    "legacy-config", "bom-config", "bom-legacy-config",
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
    elif scenario in ("legacy-config", "bom-legacy-config", "bom-config"):
        text = CONFIG if scenario == "bom-config" else "# Compound GPID - Local Configuration\r\nKeep this file.\r\n"
        if scenario.startswith("bom-"):
            text = "\ufeff" + text
        _write(project / "compound-gpid.local.md", text)
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
    assert output.count(LEGACY_CONFIG_NOTE) == int(scenario in ("legacy-config", "bom-legacy-config"))
    if scenario == "invalid-config":
        assert "compound-gpid.local.md line 2:" in output
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


@pytest.mark.parametrize("content", [
    b"# Compound GPID - Local Configuration\r\nKeep this file.\r\n",
    b"\xef\xbb\xbf# Old configuration\r\n",
    ("\ufeff" + CONFIG).encode("utf-8"),
    CONFIG.encode("utf-8"),
])
@pytest.mark.parametrize("empty_instructions", [False, True])
def test_link_prints_one_legacy_note_and_preserves_config(
    runtime: tuple, content: bytes, empty_instructions: bool, tmp_path: Path,
) -> None:
    """Both native wrappers accept old/BOM files without repairing source bytes."""
    project, home, env, command, source = runtime
    if empty_instructions:
        isolated_source = tmp_path / "empty-instructions-source"
        shutil.copytree(source, isolated_source)
        (isolated_source / ".github/instructions/r.instructions.md").unlink()
        command = [*command[:-1], str(isolated_source / "scripts" / Path(command[-1]).name)]
    config = project / "compound-gpid.local.md"
    config.write_bytes(content)
    env["CG_SKIP_UPDATE"] = "1"
    result = subprocess.run([*command, "--yes", "--platforms=kilo"],
                            cwd=project, env=env, capture_output=True, text=True,
                            timeout=90, check=False)
    output = result.stdout + result.stderr
    assert result.returncode == 0, output
    assert output.count(LEGACY_CONFIG_NOTE) == int(b"---" not in content)
    assert config.read_bytes() == content
    assert (project / ".kilo/instructions").is_dir()
    if empty_instructions:
        assert not list((project / ".kilo/instructions").iterdir())
    assert "UPDATE WAS CALLED" not in output


@pytest.mark.skipif(os.name == "nt", reason="POSIX ancestor symlinks")
@pytest.mark.parametrize("ancestor", ("tmp", "var", "user-folder"))
def test_path_check_allows_linked_ancestors_but_not_inside_project(
    tmp_path: Path, ancestor: str,
) -> None:
    """Resolve the project boundary before no-follow checks below that boundary."""
    from cg_link_check_paths import inspect_path, inventory, link_component, mirror_receipt

    physical = tmp_path / "physical"
    project = physical / "project"
    _write(project / ".kilo/commands/command.md", "managed content\n")
    alias = tmp_path / ancestor
    alias.symlink_to(physical, target_is_directory=True)
    lexical = alias / "project"
    checksum = hashlib.sha256(b"managed content\n").hexdigest()
    assert link_component(lexical, ".kilo/commands/command.md") == ""
    assert inspect_path(lexical, ".kilo/commands/command.md") == ("file", checksum, "")
    assert inventory(lexical, ".kilo/commands") == [".kilo/commands/command.md"]
    _write(project / ".kilo/commands/.compound-gpid-managed-copy.json", json.dumps(dict(
        schemaVersion=1, source=".kilo/commands", files={"command.md": checksum},
    )))
    assert mirror_receipt(lexical, ".kilo/commands", ".kilo/commands") == {
        "command.md": checksum,
    }
    (project / ".kilo/foreign").symlink_to(physical, target_is_directory=True)
    assert link_component(lexical, ".kilo/foreign/project") == ".kilo/foreign"
    state, current, error = inspect_path(lexical, ".kilo/foreign/project")
    assert state == "link/reparse"
    assert current == ""
    assert ".kilo/foreign" in error


@pytest.mark.parametrize("tag,expected", (
    (0, ""), (0x9000001A, ""), (0x80000017, ""),
    (0xA000000C, ".kilo"), (0xA0000003, ".kilo"),
))
def test_path_check_uses_link_reparse_tags_not_reparse_attribute(
    tmp_path: Path, tag: int, expected: str,
) -> None:
    """Cloud/non-link reparse directories are not classified as junctions."""
    from types import SimpleNamespace
    from unittest.mock import patch
    from cg_link_check_paths import inventory, link_component

    _write(tmp_path / ".kilo/commands/command.md", "managed content\n")
    original = Path.lstat
    metadata = SimpleNamespace(st_mode=stat.S_IFDIR | 0o755,
                               st_file_attributes=0x400, st_reparse_tag=tag)
    with patch.object(Path, "lstat", autospec=True, side_effect=lambda path, *args, **kwargs:
                      metadata if path == tmp_path / ".kilo"
                      else original(path, *args, **kwargs)):
        assert link_component(tmp_path, ".kilo/commands/command.md") == expected
        assert inventory(tmp_path, ".kilo") == ([] if expected else [
            ".kilo/commands/command.md",
        ])


@pytest.mark.parametrize("error", (OSError("denied"), ValueError("unsafe"),
                                    RuntimeError("link loop")))
def test_copy_receipt_read_errors_return_no_proof(
    tmp_path: Path, error: Exception,
) -> None:
    """Receipt probes fail closed without leaking a traceback to shell callers."""
    from unittest.mock import patch
    from cg_link_check_paths import mirror_receipt

    _write(tmp_path / ".kilo/commands/.compound-gpid-managed-copy.json", "{}")
    with patch("cg_link_check_paths.kilo_copy._read_marker", side_effect=error):
        assert mirror_receipt(tmp_path, ".kilo/commands", ".kilo/commands") is None


def test_release_proof_does_not_use_parent_repository_tags(tmp_path: Path) -> None:
    """An unpacked installation inside a tagged repository has no release proof."""
    from cg_link_ownership import ReleasedContent
    from scripts.tests.test_install_sh import _git

    parent = tmp_path / "parent-repository"
    relative = ".kilo/commands/command.md"
    content = b"user bytes from the parent repository\n"
    _write(parent / relative, content)
    _git(parent, "init")
    _git(parent, "add", ".")
    _git(parent, "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
         "-c", "commit.gpgsign=false", "-c", "core.hooksPath=" + os.devnull,
         "commit", "-m", "test: parent release tag")
    _git(parent, "tag", "v1.0.0")
    installation = parent / "unpacked-installation"
    installation.mkdir()
    before = _snapshot(parent)
    assert ReleasedContent(parent).matches(relative, content)
    released = ReleasedContent(installation)
    assert not released.matches(relative, content)
    assert not released.matches(relative, content)
    assert _snapshot(parent) == before


def test_release_proof_rejects_mismatched_git_top_level(tmp_path: Path) -> None:
    """Exact repository identity is required even if discovery returns a parent."""
    from unittest.mock import patch
    from cg_link_ownership import ReleasedContent

    installation = tmp_path / "installation"
    installation.mkdir()
    released = ReleasedContent(installation)
    with patch.object(released, "_git", return_value=str(tmp_path).encode("utf-8")) as git:
        assert not released.matches(".kilo/commands/command.md", b"user bytes")
        git.assert_called_once_with("rev-parse", "--show-toplevel")


def test_release_git_uses_installation_cwd_and_preserves_normal_config(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Repository routing is isolated without disabling normal Git configuration."""
    from unittest.mock import patch
    from cg_link_ownership import ReleasedContent

    monkeypatch.setenv("GIT_DIR", "foreign/.git")
    monkeypatch.setenv("GIT_WORK_TREE", "foreign")
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", "foreign")
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", "normal-config")
    monkeypatch.setenv("GIT_CONFIG_COUNT", "1")
    monkeypatch.setenv("GIT_CONFIG_KEY_0", "filter.fixture.clean")
    monkeypatch.setenv("GIT_CONFIG_VALUE_0", "normal-filter")
    with patch("cg_link_ownership.subprocess.run") as run:
        run.return_value.stdout = b"git output"
        assert ReleasedContent(tmp_path)._git("tag", "--list") == b"git output"
        arguments = run.call_args.kwargs
        assert arguments["cwd"] == tmp_path.resolve()
        assert arguments["env"]["GIT_CEILING_DIRECTORIES"] == str(tmp_path.resolve().parent)
        assert "GIT_DIR" not in arguments["env"]
        assert "GIT_WORK_TREE" not in arguments["env"]
        assert arguments["env"]["GIT_CONFIG_GLOBAL"] == "normal-config"
        assert arguments["env"]["GIT_CONFIG_KEY_0"] == "filter.fixture.clean"
        assert arguments["env"]["GIT_CONFIG_VALUE_0"] == "normal-filter"


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


def test_report_preserves_marked_edit_without_content_proof(tmp_path: Path) -> None:
    """A management marker cannot authorize replacement of modified bytes."""
    project, source = tmp_path / "project", tmp_path / "source"
    relative = ".github/copilot-instructions.md"
    _write(project / relative, "<!-- compound-gpid:managed -->\nuser edit\n")
    _write(source / ".github/copilot-instructions.template.md", "# {{project-name}}\n")
    units = [dict(installUnits=[dict(type="file", target=relative,
                                    source=".github/copilot-instructions.template.md",
                                    strategy="generated-copy")])]
    before = _snapshot(project)
    rows = legacy_rows(project, source, units, {relative: {
        "source": ".github/copilot-instructions.template.md", "checksum": "a" * 64,
    }}, False, False)
    assert rows[0]["owner"] == "modified-owned"
    assert rows[0]["action"] == "preserve/block"
    assert rows[0]["manual"] is True
    assert _snapshot(project) == before


@pytest.mark.parametrize("mirror", (False, True), ids=("copy-directory", "mirror"))
def test_check_user_added_regular_file_is_nonmanual_keep(tmp_path: Path, mirror: bool) -> None:
    """Copied directory extras have the worker's informational keep classification."""
    from cg_link_check_paths import mirror_rows

    project, source = tmp_path / "project", tmp_path / "source"
    source_relative = ".agents/skills" if mirror else ".kilo/commands"
    relative = ".compound-gpid/kilo-compat-skills/codex" if mirror else source_relative
    _write(source / source_relative / "managed.md", "desired\n")
    _write(project / relative / "user.md", "user content\n")
    unit = dict(type="directory", source=source_relative, target=source_relative,
                strategy="copy-directory")
    target = dict(id="codex", installUnits=[unit], outputPaths={"skills": source_relative})
    before = _snapshot(project)
    rows = (mirror_rows(project, source, [target]) if mirror else
            legacy_rows(project, source, [target], {}, False, False))
    row = next(row for row in rows if row["path"] == relative + "/user.md")
    assert row["action"] == "keep/adopt"
    assert row["manual"] is False
    assert row["owner"] == "unowned"
    assert "user file kept" in row["reason"]
    assert _snapshot(project) == before


def test_generated_check_never_queries_release_proof(tmp_path: Path) -> None:
    """No generic file-row or generated decision may request release ownership."""
    from unittest.mock import Mock

    project, source = tmp_path / "project", tmp_path / "source"
    relative = ".github/copilot-instructions.md"
    _write(project / relative, "# unmarked installation instructions\n")
    _write(source / ".github/copilot-instructions.template.md", "# {{project-name}}\n")
    released = Mock()
    released.matches.side_effect = AssertionError("generated copies cannot use release proof")
    units = [dict(installUnits=[dict(type="file", target=relative,
                                    source=".github/copilot-instructions.template.md",
                                    strategy="generated-copy")])]
    rows = legacy_rows(project, source, units, {}, False, False, released)
    assert rows[0]["action"] == "preserve/block"
    assert rows[0]["manual"] is True
    released.matches.assert_not_called()


@pytest.mark.parametrize("scenario", ("managed", "changed", "foreign"))
@pytest.mark.parametrize("configured", (False, True), ids=("legacy", "manifest"))
def test_check_reports_compatibility_mirrors_without_writes(
    runtime: tuple, scenario: str, configured: bool,
) -> None:
    """Recognize receipts/links, preserve edits and refuse foreign mirror links."""
    project, home, env, command, source = runtime
    if configured:
        _write(project / "compound-gpid.local.md", CONFIG)
    mirror_relative = ".compound-gpid/kilo-compat-skills/codex"
    mirror = project / mirror_relative
    original = source / ".agents/skills"
    files = {p.relative_to(original).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
             for p in original.rglob("*") if p.is_file()}
    shutil.copytree(original, mirror)
    _write(mirror / ".compound-gpid-managed-copy.json", json.dumps(dict(
        schemaVersion=1, source=".agents/skills", files=files,
    )))
    leaf = next(iter(files))
    if scenario == "changed":
        _write(mirror / leaf, "user mirror edit\n")
    if scenario == "foreign":
        mirror.rename(project / "foreign-skills")
        destination, target = mirror, project / "foreign-skills"
    else:
        destination, target = project / ".agents/skills", mirror
    destination.parent.mkdir(parents=True, exist_ok=True)
    if os.name == "nt":
        linked = subprocess.run(
            ["cmd.exe", "/c", "mklink", "/J", str(destination), str(target)],
            capture_output=True, text=True, check=False,
        )
        assert linked.returncode == 0, linked.stdout + linked.stderr
    else:
        destination.symlink_to(target, target_is_directory=True)
    before = (_snapshot(project), _snapshot(home), _snapshot(source))
    result = subprocess.run([*command, "--check", "--platforms=codex"],
                            cwd=project, env=env, capture_output=True, text=True,
                            timeout=45, check=False)
    output = result.stdout + result.stderr
    assert (_snapshot(project), _snapshot(home), _snapshot(source)) == before
    assert "UPDATE WAS CALLED" not in output
    assert result.returncode == int(scenario != "managed"), output
    if scenario != "foreign":
        assert ".agents/skills | managed | link/reparse | keep | recognized managed" in output
        assert f"{mirror_relative} | managed | directory | sync" in output
    if scenario == "managed":
        assert "Manual action required:\n  none" in output
        assert f"{mirror_relative}/{leaf} | managed | file sha256=" in output
    elif scenario == "changed":
        assert f"{mirror_relative}/{leaf} | modified-owned | file sha256=" in output
        assert "preserve/block" in output
    else:
        assert f"{mirror_relative} | unowned | link/reparse | preserve/block" in output


@pytest.mark.parametrize("scenario", (
    "related", "jsonc", "custom-path", "missing", "invalid", "wrong-shape",
))
def test_global_kilo_settings_are_information_only_and_never_written(
    runtime: tuple, scenario: str,
) -> None:
    """Global grants/plugins, even malformed settings, cannot block project check."""
    project, home, env, command, source = runtime
    config = home / ".config/kilo/kilo.jsonc"
    key = (source.as_posix() if scenario == "custom-path" else "/old/compound-gpid") + "/.kilo/commands/*"
    content = json.dumps(dict(
        permission={"markdown_source": {key: "deny", "/unrelated/*": "allow"}},
        plugin=["file:///old/compound-gpid/.kilo/plugins/cg-native-evidence.js", "unrelated-plugin"],
    ))
    if scenario == "jsonc":
        content = "// retained comment\n" + content[:-1] + ", /* retained */ }\n"
    elif scenario == "invalid":
        content = "not valid JSONC\n"
    elif scenario == "wrong-shape":
        content = '{"permission":[],"plugin":{}}\n'
    _write(config, content)
    if scenario == "missing":
        config.unlink()
    before = (_snapshot(project), _snapshot(home), _snapshot(source))
    result = subprocess.run([*command, "--check", "--platforms=kilo"],
                            cwd=project, env=env, capture_output=True, text=True,
                            timeout=45, check=False)
    output = result.stdout + result.stderr
    assert result.returncode == 0, output
    assert "Global Kilo settings (INFORMATION ONLY; never block or write)" in output
    assert "Manual action required:\n  none" in output
    assert "UPDATE WAS CALLED" not in output
    if scenario in ("related", "jsonc", "custom-path"):
        assert key in output
        assert ' = "deny"' in output
        assert "cg-native-evidence.js" in output
        assert "unrelated-plugin" not in output
        assert "/unrelated/*" not in output
    elif scenario == "missing":
        assert "kilo.jsonc: absent" in output
    elif scenario == "invalid":
        assert "not assessed" in output
    else:
        assert "permission: not an object; preserved" in output
        assert "plugin: not an array; preserved" in output
    assert (_snapshot(project), _snapshot(home), _snapshot(source)) == before
