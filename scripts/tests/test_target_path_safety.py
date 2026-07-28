"""Adversarial path and output-namespace tests for native target generation."""
from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

import cg_generate_targets as gen


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
        gen.build_generation_plan(root, broken, {"prompts": [], "agents": [], "skills": [], "instructions": []}, {})

    assert list(root.iterdir()) == []
