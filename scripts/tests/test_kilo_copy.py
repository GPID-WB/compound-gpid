"""Tests for checksum-owned, no-follow Kilo copy-directory synchronization."""
from __future__ import annotations

import builtins
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

import cg_kilo_copy as kilo_copy


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_sync_writes_marker_and_preserves_modified_files(tmp_path: Path) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    _write(source / "commands/cg-test.md", "source-v1")
    _write(source / "skills/cg-test/SKILL.md", "---\nname: cg-test\ndescription: test\n---\n")

    kilo_copy.sync_directory(source, target, ".kilo/skills")
    assert (target / "commands/cg-test.md").read_text(encoding="utf-8") == "source-v1"
    assert (target / kilo_copy.MARKER_NAME).is_file()

    _write(target / "commands/cg-test.md", "user-edit")
    _write(source / "commands/cg-test.md", "source-v2")
    kilo_copy.sync_directory(source, target, ".kilo/skills")
    assert (target / "commands/cg-test.md").read_text(encoding="utf-8") == "user-edit"


def test_sync_removes_only_unchanged_stale_files(tmp_path: Path) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    _write(source / "old.md", "old")
    kilo_copy.sync_directory(source, target, ".kilo/skills")
    (source / "old.md").unlink()
    kilo_copy.sync_directory(source, target, ".kilo/skills")
    assert not (target / "old.md").exists()

    _write(source / "old.md", "old")
    kilo_copy.sync_directory(source, target, ".kilo/skills")
    _write(target / "old.md", "user-edit")
    (source / "old.md").unlink()
    kilo_copy.sync_directory(source, target, ".kilo/skills")
    assert (target / "old.md").read_text(encoding="utf-8") == "user-edit"


def test_sync_rejects_source_symlink(tmp_path: Path) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.mkdir()
    outside = tmp_path / "outside.md"
    outside.write_text("outside", encoding="utf-8")
    try:
        (source / "linked.md").symlink_to(outside)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks unavailable on this host")

    with pytest.raises(kilo_copy.CopyError, match="link or reparse"):
        kilo_copy.sync_directory(source, target, ".kilo/skills")


def test_import_fallback_precedes_ownership_import(monkeypatch: pytest.MonkeyPatch) -> None:
    """Loading by file path must establish local imports before ownership loads."""
    scripts = Path(kilo_copy.__file__).resolve().parent
    original_import = builtins.__import__
    monkeypatch.setattr(sys, "path", [path for path in sys.path
                                   if Path(path).resolve() != scripts])

    def local_import(name: str, *args, **kwargs):
        """Force the secure_fs fallback and check ownership's local search path."""
        if name == "secure_fs" and str(scripts) not in sys.path:
            raise ImportError("fixture: scripts not on import path")
        if name == "cg_link_ownership":
            assert sys.path[0] == str(scripts)
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", local_import)
    spec = importlib.util.spec_from_file_location("isolated_kilo_copy", scripts / "cg_kilo_copy.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.ReleasedContent is kilo_copy.ReleasedContent


def test_basic_copy_does_not_require_projection(tmp_path: Path) -> None:
    """A copied basic worker needs only secure_fs and ownership, not projection."""
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    for name in ("cg_kilo_copy.py", "secure_fs.py", "cg_link_ownership.py"):
        shutil.copy2(Path(kilo_copy.__file__).parent / name, scripts / name)
    source, project = tmp_path / "source", tmp_path / "project"
    _write(source / ".kilo/kilo.json", '{"fixture":true}\n')
    project.mkdir()
    env = {key: value for key, value in os.environ.items()
           if not key.upper().startswith("PYTHON")}
    result = subprocess.run(
        [sys.executable, "-B", str(scripts / "cg_kilo_copy.py"),
         "--source-root", str(source), "--project-root", str(project),
         "--file", ".kilo/kilo.json", ".kilo/kilo.json", "copy"],
        cwd=tmp_path, env=env, capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert (project / ".kilo/kilo.json").read_bytes() == (source / ".kilo/kilo.json").read_bytes()
    assert kilo_copy.scalar_receipt(project)[".kilo/kilo.json"]["source"] == ".kilo/kilo.json"


def test_scalar_receipt_reads_bom_through_secure_fs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Read BOM receipts with bounded, hard-link-rejecting secure reads."""
    record = {"source": ".kilo/kilo.json", "checksum": "a" * 64}
    data = {"schemaVersion": "compound-gpid-managed-files-v1",
            "files": {".kilo/kilo.json": record}}
    _write(tmp_path / ".compound-gpid/managed-files.json", "\ufeff" + json.dumps(data))
    original_read = kilo_copy.secure_fs.secure_read_bytes
    calls = []

    def read(root: Path, relative: str, **kwargs) -> bytes:
        """Record the security options while using the real filesystem backend."""
        calls.append((root, relative, kwargs))
        return original_read(root, relative, **kwargs)

    monkeypatch.setattr(kilo_copy.secure_fs, "secure_read_bytes", read)
    assert kilo_copy.scalar_receipt(tmp_path) == {".kilo/kilo.json": record}
    assert calls == [(tmp_path, ".compound-gpid/managed-files.json",
                      {"reject_hardlinks": True, "max_bytes": 16 * 1024 * 1024})]


@pytest.mark.parametrize("content", (
    b"", b"{", b"\xff", b"[]", b"null", b"{}",
    b'{"schemaVersion":"compound-gpid-managed-files-v1","files":[]}',
))
def test_invalid_scalar_receipt_warns_and_returns_empty(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], content: bytes,
) -> None:
    """Malformed, empty and wrong-shape receipts cannot supply ownership proof."""
    receipt = tmp_path / ".compound-gpid/managed-files.json"
    receipt.parent.mkdir()
    receipt.write_bytes(content)
    assert kilo_copy.scalar_receipt(tmp_path) == {}
    error = capsys.readouterr().err
    assert "WARNING:" in error and "invalid copy receipt" in error


def test_missing_scalar_receipt_returns_empty_without_warning(
    tmp_path: Path, capsys: pytest.CaptureFixture[str],
) -> None:
    """A first-time consumer has no receipt and needs no warning."""
    assert kilo_copy.scalar_receipt(tmp_path) == {}
    assert capsys.readouterr().err == ""


def test_unsafe_scalar_receipt_raises_copy_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Unsafe secure reads fail closed under the copy worker's error contract."""
    def read(*args, **kwargs) -> bytes:
        """Simulate a rejected receipt without requiring host link privileges."""
        raise kilo_copy.secure_fs.SecureMutationError("unsafe receipt")

    monkeypatch.setattr(kilo_copy.secure_fs, "secure_read_bytes", read)
    with pytest.raises(kilo_copy.CopyError, match="safe copy receipt read failed"):
        kilo_copy.scalar_receipt(tmp_path)


@pytest.mark.parametrize("newline", ("\n", "\r\n"), ids=("lf", "crlf"))
def test_generated_instructions_render_real_frontmatter_fields(
    tmp_path: Path, newline: str,
) -> None:
    """Both platform delimiters supply project and local configuration fields."""
    source, project = tmp_path / "source", tmp_path / "project"
    template = "{{project-name}}|{{project-type}}|{{languages}}|{{review-depth}}\n"
    _write(source / ".github/copilot-instructions.template.md", template)
    (source / ".github/copilot-instructions.template.md").write_bytes(template.encode())
    for relative, fields in (
        ("compound-gpid.md", 'project-name: "Configured Project"'),
        ("compound-gpid.local.md", 'project-type: "research"\nlanguage: "R, Python"\n'
         'r-syntax: "data.table-collapse"\nreview-depth: "thorough"'),
    ):
        path = project / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(("---\n" + fields + "\n---\n").replace("\n", newline).encode())
    result = kilo_copy.generated_instructions(source, project)
    assert result == (b"<!-- compound-gpid:managed -->\nConfigured Project|research|"
                      b"R, Python (R dialect: data.table-collapse)|thorough\n")


@pytest.mark.parametrize("kind", ("directory", "scalar"))
@pytest.mark.parametrize("error", (PermissionError("denied"), OSError("read failed")))
def test_destination_io_error_returns_nonzero(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, kind: str, error: OSError,
) -> None:
    """Operational read failures are not reported as successful keep decisions."""
    source, project = tmp_path / "source", tmp_path / "project"
    relative = ".kilo/commands/cg-test.md"
    _write(source / relative, "desired")
    _write(project / relative, "existing")
    original = kilo_copy.secure_fs.secure_read_bytes

    def read(root: Path, path: str, **kwargs) -> bytes:
        """Fail only the existing consumer file, not its source or receipts."""
        if root / path == project / relative:
            raise error
        return original(root, path, **kwargs)

    monkeypatch.setattr(kilo_copy.secure_fs, "secure_read_bytes", read)
    unit = (["--directory", ".kilo/commands", ".kilo/commands"] if kind == "directory"
            else ["--file", relative, relative, "copy"])
    assert kilo_copy.main(["--source-root", str(source), "--project-root", str(project),
                           *unit]) == 1
    assert (project / relative).read_bytes() == b"existing"
    assert not (project / ".compound-gpid/managed-files.json").exists()
    assert not (project / ".kilo/commands" / kilo_copy.MARKER_NAME).exists()


@pytest.mark.parametrize("kind", ("directory", "scalar"))
def test_secure_destination_rejection_is_a_successful_manual_keep(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, kind: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Secure no-follow rejections are distinct from operational I/O failures."""
    source, project = tmp_path / "source", tmp_path / "project"
    relative = ".kilo/commands/cg-test.md"
    _write(source / relative, "desired")
    _write(project / relative, "existing")
    original = kilo_copy.secure_fs.secure_read_bytes

    def read(root: Path, path: str, **kwargs) -> bytes:
        """Simulate the secure backend rejecting an unsafe destination identity."""
        if root / path == project / relative:
            raise kilo_copy.secure_fs.SecureMutationError("link destination rejected")
        return original(root, path, **kwargs)

    monkeypatch.setattr(kilo_copy.secure_fs, "secure_read_bytes", read)
    unit = (["--directory", ".kilo/commands", ".kilo/commands"] if kind == "directory"
            else ["--file", relative, relative, "copy"])
    assert kilo_copy.main(["--source-root", str(source), "--project-root", str(project),
                           *unit]) == 0
    assert (project / relative).read_bytes() == b"existing"
    output = capsys.readouterr()
    assert "link destination rejected" in output.err
    assert "Manual action required: 1" in output.out
    assert "Kilo validation deferred: 1" in output.out


@pytest.mark.parametrize("kind", ("directory", "scalar"))
def test_link_destination_is_kept_with_success(
    tmp_path: Path, kind: str, capsys: pytest.CaptureFixture[str],
) -> None:
    """Real file links remain untouched and produce a successful manual keep."""
    source, project = tmp_path / "source", tmp_path / "project"
    relative = ".kilo/commands/cg-test.md"
    _write(source / relative, "desired")
    outside = tmp_path / "outside.md"
    _write(outside, "outside sentinel")
    destination = project / relative
    destination.parent.mkdir(parents=True)
    try:
        destination.symlink_to(outside)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks unavailable on this host")
    unit = (["--directory", ".kilo/commands", ".kilo/commands"] if kind == "directory"
            else ["--file", relative, relative, "copy"])
    assert kilo_copy.main(["--source-root", str(source), "--project-root", str(project),
                           *unit]) == 0
    assert destination.is_symlink()
    assert outside.read_bytes() == b"outside sentinel"
    output = capsys.readouterr()
    assert "manual action required" in output.err
    assert "Kilo validation deferred: 1" in output.out


@pytest.mark.parametrize("kind", ("directory", "scalar"))
@pytest.mark.parametrize("side", ("source", "target"))
@pytest.mark.parametrize("invalid", ("..", "safe/../escape", ".", "", "/absolute", "C:/absolute"))
def test_all_unit_paths_rejected_before_any_mutation(
    tmp_path: Path, kind: str, side: str, invalid: str,
) -> None:
    """Reject every unsafe queue input before an earlier valid unit can write."""
    source, project = tmp_path / "source", tmp_path / "project"
    _write(source / "safe/file.md", "desired")
    project.mkdir()
    paths = [invalid, "safe"] if side == "source" else ["safe", invalid]
    arguments = ["--source-root", str(source), "--project-root", str(project),
                 "--directory", "safe", "would-be-created"]
    arguments += (["--directory", *paths] if kind == "directory"
                  else ["--file", *paths, "copy"])
    assert kilo_copy.main(arguments) == 1
    assert list(project.iterdir()) == []
    assert sorted(path.relative_to(source).as_posix() for path in source.rglob("*")) == [
        "safe", "safe/file.md",
    ]


def test_unrecorded_user_file_is_informational_not_manual(
    tmp_path: Path, capsys: pytest.CaptureFixture[str],
) -> None:
    """Unrelated regular leaves are kept without claiming copy ownership."""
    source, project = tmp_path / "source", tmp_path / "project"
    _write(source / ".kilo/commands/cg-test.md", "desired")
    _write(project / ".kilo/commands/user.md", "user content")
    kilo_copy.sync_units(source, project, [(".kilo/commands", ".kilo/commands")], [])
    output = capsys.readouterr()
    assert "user file kept" in output.out
    assert "Manual action required: 0" in output.out
    assert "Kilo validation deferred: 0" in output.out
    assert output.err == ""
    assert (project / ".kilo/commands/user.md").read_bytes() == b"user content"
    assert "user.md" not in kilo_copy._read_marker(project / ".kilo/commands", ".kilo/commands")


@pytest.mark.parametrize("manual,expected", (
    ([".kilo"], 1), ([".kilo/commands", ".kilo/commands/cg-x.md"], 2),
    ([".kilo/skills/x/SKILL.md", ".kilo/skills/x/SKILL.md"], 1),
    ([".kilo/agents/x.md", ".kilo/instructions/x.md", ".kilo/shared/x.json"], 3),
    ([".github/copilot-instructions.md", ".kilo/AGENTS.md", ".kilo/kilo.json"], 0),
    ([".agents", ".claude/skills/x/SKILL.md", ".opencode/skills",
      ".compound-gpid/kilo-compat-skills/codex/x/SKILL.md"], 0),
    ([".kilo/commands-other/x.md"], 0),
))
def test_deferred_validation_counts_only_preflight_roots(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], manual: list[str], expected: int,
) -> None:
    """The count covers unique conflicting descendants and ancestors, not siblings."""
    from cg_kilo_preflight import REQUIRED_LOCAL_ROOTS

    assert kilo_copy.VALIDATED_KILO_ROOTS == REQUIRED_LOCAL_ROOTS
    kilo_copy.sync_units(tmp_path, tmp_path, [], [], manual_paths=manual)
    output = capsys.readouterr().out
    assert f"Manual action required: {len(set(manual))}\n" in output
    assert f"Kilo validation deferred: {expected}\n" in output
