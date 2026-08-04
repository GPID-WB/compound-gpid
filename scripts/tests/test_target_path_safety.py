"""Adversarial path and output-namespace tests for native target generation."""
from __future__ import annotations

import copy
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import zlib

import pytest

import cg_generate_targets as gen
from artifact_views.errors import ArtifactWriteError
from artifact_views.writer import ViewDestination, write_view
from secure_fs import ExpectedFileState


REPO_ROOT = Path(__file__).resolve().parents[2]


def _mapping() -> dict:
    return json.loads(
        (REPO_ROOT / ".github/shared/target-mapping.json").read_text(encoding="utf-8")
    )


def _target(data: dict, target_id: str = "claude-code") -> dict:
    return next(target for target in data["targets"] if target["id"] == target_id)


@pytest.mark.parametrize(
    "value",
    ["", "/absolute", "../escape", "a/../../escape", "C:/drive", "C:\\drive", "//server/share", "\\\\server\\share", "has\x00nul"],
)
def test_unsafe_mapping_paths_fail(value: str) -> None:
    data = _mapping()
    _target(data)["outputPaths"]["commands"] = value

    errors = gen.validate_target_mapping(data)

    assert any("outputPaths.commands" in error for error in errors)


@pytest.mark.parametrize(
    "value",
    [".claude/con", ".claude/NUL.txt", ".claude/trailing. ", ".claude/aux/file"],
)
def test_windows_nonportable_paths_fail(value: str) -> None:
    data = _mapping()
    _target(data)["outputPaths"]["commands"] = value

    errors = gen.validate_target_mapping(data)

    assert any("outputPaths.commands" in error for error in errors)


@pytest.mark.parametrize(
    "value",
    [".claude/bad:name", ".claude/bad<name", ".claude/bad\x1fname", ".claude/file.txt:stream"],
)
def test_windows_forbidden_characters_and_ads_paths_fail(value: str) -> None:
    data = _mapping()
    _target(data)["outputPaths"]["commands"] = value

    errors = gen.validate_target_mapping(data)

    assert any("Windows-forbidden" in error for error in errors)


def test_generated_destination_under_canonical_tree_fails() -> None:
    data = _mapping()
    _target(data)["generatedTreePath"] = ".github/generated"
    for key in _target(data)["outputPaths"]:
        _target(data)["outputPaths"][key] = f".github/generated/{key}"

    errors = gen.validate_target_mapping(data)

    assert any("canonical .github" in error for error in errors)


def test_output_path_must_be_inside_generated_tree() -> None:
    data = _mapping()
    _target(data)["outputPaths"]["commands"] = ".agents/commands"

    errors = gen.validate_target_mapping(data)

    assert any("outside generatedTreePath" in error for error in errors)


def test_install_unit_source_must_be_inside_generated_tree() -> None:
    data = _mapping()
    _target(data)["installUnits"][0]["source"] = ".agents/commands"

    errors = gen.validate_target_mapping(data)

    assert any("installUnits[0].source" in error and "outside generatedTreePath" in error for error in errors)


def test_install_unit_type_and_strategy_must_agree() -> None:
    data = _mapping()
    _target(data)["installUnits"][0]["type"] = "file"

    errors = gen.validate_target_mapping(data)

    assert any("link-directory" in error and "directory" in error for error in errors)


def test_overlapping_generated_roots_fail() -> None:
    data = _mapping()
    _target(data, "opencode")["generatedTreePath"] = ".agents/nested"
    for key, value in _target(data, "opencode")["outputPaths"].items():
        suffix = Path(value).name
        _target(data, "opencode")["outputPaths"][key] = f".agents/nested/{suffix}"

    errors = gen.validate_target_mapping(data)

    assert any("generated tree" in error and "overlap" in error for error in errors)


@pytest.mark.parametrize(
    ("first", "second"),
    [
        (".claude/Commands", ".claude/commands"),
        (".claude/caf\u00e9", ".claude/cafe\u0301"),
        (".claude/name", ".claude/name."),
    ],
)
def test_portable_output_path_collisions_fail(first: str, second: str) -> None:
    data = _mapping()
    target = _target(data)
    target["outputPaths"]["commands"] = first
    target["outputPaths"]["skills"] = second

    errors = gen.validate_target_mapping(data)

    assert any("collision" in error for error in errors)


def test_file_directory_prefix_conflict_fails() -> None:
    data = _mapping()
    target = _target(data)
    target["outputPaths"]["commands"] = ".claude/runtime"
    target["outputPaths"]["skills"] = ".claude/runtime/skills"

    errors = gen.validate_target_mapping(data)

    assert any("file/directory" in error for error in errors)


@pytest.mark.usefixtures("require_symlink_support")
def test_existing_symlink_ancestor_escape_fails(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    outside = tmp_path / "outside"
    root.mkdir()
    outside.mkdir()
    (root / ".claude").symlink_to(outside, target_is_directory=True)
    data = _mapping()

    with pytest.raises(gen.PathSafetyError, match="escapes repository root"):
        gen.validate_mapping_paths(root, data)


def test_invalid_late_target_prevents_all_writes(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    data = _mapping()
    broken = copy.deepcopy(data)
    _target(broken, "opencode")["outputPaths"]["commands"] = "../escape"

    with pytest.raises(gen.MappingValidationError):
        gen.build_generation_plan(root, broken, {"prompts": [], "agents": [], "skills": [], "instructions": []})

    assert list(root.iterdir()) == []


def test_active_backend_preserves_destination_created_after_authorized_absence(
    tmp_path: Path,
) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    destination = ViewDestination.from_path(
        Path(".cg-docs/views/documents/backend-race.html")
    )
    output = root / destination.relative

    def insert_concurrent_owner(_path: Path) -> None:
        output.write_bytes(b"concurrent owner")

    with pytest.raises(ArtifactWriteError):
        write_view(
            root,
            destination,
            b"new publication",
            before_replace=insert_concurrent_owner,
            expected_state=ExpectedFileState.absent(),
        )

    assert output.read_bytes() == b"concurrent owner"


def test_matrix_installed_publisher_renders_bitmap_and_checks_from_outside_cwd(
    tmp_path: Path,
) -> None:
    install_root = tmp_path / "installed publisher with spaces"
    shutil.copytree(REPO_ROOT / "scripts", install_root / "scripts")
    (install_root / "bin").mkdir()
    launcher_name = (
        "cg-publish-markdown.cmd" if os.name == "nt" else "cg-publish-markdown"
    )
    launcher = install_root / "bin" / launcher_name
    shutil.copy2(REPO_ROOT / "bin" / launcher_name, launcher)
    if os.name != "nt":
        launcher.chmod(0o755)
    project = tmp_path / "project with spaces"
    project.mkdir()
    (project / "compound-gpid.md").write_text("# Project\n", encoding="utf-8")
    (project / "guide.md").write_text(
        "# Guide\n\n![Pixel](pixel.png)\n",
        encoding="utf-8",
    )
    def png_chunk(chunk_type: bytes, data: bytes) -> bytes:
        return (
            struct.pack(">I", len(data))
            + chunk_type
            + data
            + struct.pack(">I", zlib.crc32(chunk_type + data) & 0xFFFFFFFF)
        )

    (project / "pixel.png").write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + png_chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 6, 0, 0, 0))
        + png_chunk(b"IDAT", zlib.compress(b"\x00\x00\x00\x00\x00"))
        + png_chunk(b"IEND", b"")
    )
    outside = tmp_path / "outside"
    outside.mkdir()

    rendered = subprocess.run(
        [str(launcher), "--root", str(project), "guide.md"],
        cwd=outside,
        capture_output=True,
        text=True,
        check=False,
    )
    checked = subprocess.run(
        [str(launcher), "--root", str(project), "--check", "guide.md"],
        cwd=outside,
        capture_output=True,
        text=True,
        check=False,
    )

    assert rendered.returncode == 0, rendered.stderr
    assert checked.returncode == 0, checked.stderr
    assert "current .cg-docs/views/documents/guide.html" in checked.stdout
    output = project / ".cg-docs/views/documents/guide.html"
    assert "data:image/png;base64," in output.read_text(encoding="utf-8")


@pytest.mark.skipif(os.name == "nt", reason="executes Bash candidate fallback")
def test_matrix_bash_wrapper_fallback_and_child_failure(tmp_path: Path) -> None:
    install_root = tmp_path / "install"
    shutil.copytree(REPO_ROOT / "scripts", install_root / "scripts")
    (install_root / "bin").mkdir()
    wrapper = install_root / "bin/cg-publish-markdown"
    shutil.copy2(REPO_ROOT / "bin/cg-publish-markdown", wrapper)
    wrapper.chmod(0o755)
    fake_bin = tmp_path / "fake-bin"
    fake_bin.mkdir()
    log = tmp_path / "python.log"
    (fake_bin / "python3").write_text(
        "#!/bin/sh\n"
        "if [ \"$1\" = \"--version\" ]; then echo 'not python'; exit 0; fi\n"
        "exit 99\n",
        encoding="utf-8",
    )
    (fake_bin / "python3").chmod(0o755)
    (fake_bin / "python").write_text(
        "#!/bin/sh\n"
        "if [ \"$1\" = \"--version\" ]; then echo 'Python 3.11.0'; exit 0; fi\n"
        "if [ \"$1\" = \"-c\" ]; then exit 0; fi\n"
        f"printf '%s\\n' \"$*\" >> '{log}'\n"
        "exit 7\n",
        encoding="utf-8",
    )
    (fake_bin / "python").chmod(0o755)
    environment = os.environ.copy()
    environment["PATH"] = f"{fake_bin}{os.pathsep}{environment.get('PATH', '')}"

    result = subprocess.run(
        [str(wrapper), "--check", "guide with spaces.md"],
        cwd=tmp_path,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 7
    assert "guide with spaces.md" in log.read_text(encoding="utf-8")


@pytest.mark.skipif(os.name == "nt", reason="executes repository-local Bash wrapper")
def test_matrix_repository_bash_wrapper_runs_and_falls_back(tmp_path: Path) -> None:
    wrapper = REPO_ROOT / "bin/cg-publish-markdown"
    project = tmp_path / "repo project with spaces"
    project.mkdir()
    (project / "compound-gpid.md").write_text("# Project\n", encoding="utf-8")
    (project / "guide with spaces.md").write_text("# Guide\n", encoding="utf-8")
    outside = tmp_path / "outside"
    outside.mkdir()

    rendered = subprocess.run(
        [str(wrapper), "--root", str(project), "guide with spaces.md"],
        cwd=outside,
        capture_output=True,
        text=True,
        check=False,
    )
    checked = subprocess.run(
        [str(wrapper), "--root", str(project), "--check", "guide with spaces.md"],
        cwd=outside,
        capture_output=True,
        text=True,
        check=False,
    )

    assert rendered.returncode == 0, rendered.stderr
    assert checked.returncode == 0, checked.stderr

    fake_bin = tmp_path / "repo-fake-bin"
    fake_bin.mkdir()
    log = tmp_path / "repo-python.log"
    (fake_bin / "python3").write_text(
        "#!/bin/sh\nif [ \"$1\" = \"--version\" ]; then echo bad; exit 0; fi\nexit 99\n",
        encoding="utf-8",
    )
    (fake_bin / "python3").chmod(0o755)
    (fake_bin / "python").write_text(
        "#!/bin/sh\n"
        "if [ \"$1\" = \"--version\" ]; then echo 'Python 3.11.0'; exit 0; fi\n"
        "if [ \"$1\" = \"-c\" ]; then exit 0; fi\n"
        f"printf '%s\\n' \"$*\" >> '{log}'\nexit 7\n",
        encoding="utf-8",
    )
    (fake_bin / "python").chmod(0o755)
    environment = os.environ.copy()
    environment["PATH"] = f"{fake_bin}{os.pathsep}{environment.get('PATH', '')}"
    failed = subprocess.run(
        [str(wrapper), "--check", "guide with spaces.md"],
        cwd=outside,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )

    assert failed.returncode == 7
    assert "guide with spaces.md" in log.read_text(encoding="utf-8")
