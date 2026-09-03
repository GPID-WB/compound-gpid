"""Tests for hybrid Copilot per-bundle project projection."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

import cg_project_manifest as manifest_module
import cg_project_projection as projection
from scripts.tests.test_project_skill_registry import (
    add_project_skill,
    write_project_overlay,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


def _consumer(
    tmp_path: Path, *, platforms: list[str], second_skill: bool = False
) -> tuple[Path, dict]:
    project = tmp_path / "consumer"
    project.mkdir()
    record = add_project_skill(project, "local-copilot")
    records = [record]
    if second_skill:
        records.append(add_project_skill(project, "local-sibling"))
    write_project_overlay(project, records)
    (project / "compound-gpid.local.md").write_text(
        '---\nlanguage: "python"\nsuites: [cg]\n'
        'capabilities: [project-skill-local-copilot]\n---\n# Consumer\n',
        encoding="utf-8",
    )
    manifest = manifest_module.resolve_active_manifest(
        project,
        source_root=REPO_ROOT,
        platforms=platforms,
    )
    state = project / ".compound-gpid"
    state.mkdir(exist_ok=True)
    (state / "active-manifest.json").write_text(
        manifest_module.canonical_manifest_bytes(manifest),
        encoding="utf-8",
    )
    return project, manifest


def test_copilot_mapping_projects_only_skill_bundles() -> None:
    mapping = json.loads(
        (REPO_ROOT / ".github/shared/target-mapping.json").read_text(encoding="utf-8")
    )
    copilot = next(item for item in mapping["targets"] if item["id"] == "copilot")

    assert copilot["projectedCategories"] == ["skills"]
    assert copilot["projectRoots"]["managed"] == [".github/skills"]
    assert not any(
        item["target"] == ".github/skills" for item in copilot["installUnits"]
    )


def test_copilot_only_plan_contains_skills_and_no_other_category(tmp_path: Path) -> None:
    project, manifest = _consumer(tmp_path, platforms=["copilot"])

    plan = projection.build_projection_plan(
        REPO_ROOT,
        manifest,
        project_root=project,
    )

    assert plan.platforms == ("copilot",)
    assert plan.entries
    assert all(item.destination.startswith(".github/skills/") for item in plan.entries)
    assert all(item.kind in ("skill", "skill-resource") for item in plan.entries)
    assert not any("/prompts/" in item.destination for item in plan.entries)
    assert not any("/agents/" in item.destination for item in plan.entries)
    assert not any("/instructions/" in item.destination for item in plan.entries)
    assert not any("/shared/" in item.destination for item in plan.entries)


def test_selected_project_bundle_reaches_all_five_platforms(tmp_path: Path) -> None:
    platforms = ["copilot", "claude-code", "codex", "opencode", "kilo"]
    project, manifest = _consumer(tmp_path, platforms=platforms)
    plan = projection.build_projection_plan(
        REPO_ROOT,
        manifest,
        project_root=project,
    )

    destinations = {item.destination for item in plan.entries}
    for root in (
        ".github/skills",
        ".claude/skills",
        ".agents/skills",
        ".opencode/skills",
        ".kilo/skills",
    ):
        assert f"{root}/local-copilot/SKILL.md" in destinations


def test_two_project_bundles_project_only_the_explicit_selection(tmp_path: Path) -> None:
    platforms = ["copilot", "claude-code", "codex", "opencode", "kilo"]
    project, manifest = _consumer(
        tmp_path, platforms=platforms, second_skill=True
    )

    plan = projection.build_projection_plan(
        REPO_ROOT, manifest, project_root=project
    )

    assert any("/local-copilot/" in item.destination for item in plan.entries)
    assert not any("/local-sibling/" in item.destination for item in plan.entries)
    project_entries = [
        item for item in plan.entries if "/local-copilot/" in item.destination
    ]
    assert {item.origin for item in project_entries} == {"project-imported"}
    assert all("example/project-skills@" in item.provenance_identity for item in project_entries)
    assert all(str(project) not in item.provenance_identity for item in project_entries)


def test_real_copilot_parent_preserves_unrelated_user_bundle(tmp_path: Path) -> None:
    project, manifest = _consumer(tmp_path, platforms=["copilot"])
    user = project / ".github/skills/user-owned/SKILL.md"
    user.parent.mkdir(parents=True)
    user.write_text("# User owned\n", encoding="utf-8")
    plan = projection.build_projection_plan(
        REPO_ROOT,
        manifest,
        project_root=project,
    )

    ownership = projection.publish_projection(project, plan, source_root=REPO_ROOT)

    assert user.read_text(encoding="utf-8") == "# User owned\n"
    assert (project / ".github/skills/local-copilot/SKILL.md").is_file()
    assert projection.verify_projection(project, plan) == []
    assert ".github/skills/user-owned/SKILL.md" not in ownership["entries"]


def test_collision_inside_selected_bundle_blocks_without_partial_write(tmp_path: Path) -> None:
    project, manifest = _consumer(tmp_path, platforms=["copilot"])
    collision = project / ".github/skills/local-copilot/SKILL.md"
    collision.parent.mkdir(parents=True)
    collision.write_text("user collision\n", encoding="utf-8")
    plan = projection.build_projection_plan(
        REPO_ROOT,
        manifest,
        project_root=project,
    )

    with pytest.raises(projection.ProjectionError, match="collision|modified|user-owned"):
        projection.publish_projection(project, plan, source_root=REPO_ROOT)

    assert collision.read_text(encoding="utf-8") == "user collision\n"
    assert not (project / ".github/skills/local-copilot/references/guide.md").exists()


def test_unexpected_file_inside_managed_bundle_fails_exact_verification(
    tmp_path: Path,
) -> None:
    project, manifest = _consumer(tmp_path, platforms=["copilot"])
    plan = projection.build_projection_plan(
        REPO_ROOT,
        manifest,
        project_root=project,
    )
    projection.publish_projection(project, plan, source_root=REPO_ROOT)
    unexpected = project / ".github/skills/local-copilot/unexpected.txt"
    unexpected.write_text("unexpected\n", encoding="utf-8")

    problems = projection.verify_projection(project, plan)

    assert any("unexpected" in problem for problem in problems)


@pytest.mark.usefixtures("require_symlink_support")
def test_existing_managed_copilot_skill_link_migrates_to_real_parent(
    tmp_path: Path,
) -> None:
    project, manifest = _consumer(tmp_path, platforms=["copilot"])
    github = project / ".github"
    github.mkdir()
    skills = github / "skills"
    skills.symlink_to(REPO_ROOT / ".github/skills", target_is_directory=True)
    plan = projection.build_projection_plan(
        REPO_ROOT,
        manifest,
        project_root=project,
    )

    projection.publish_projection(project, plan, source_root=REPO_ROOT)

    assert skills.is_dir()
    assert not skills.is_symlink()
    assert (skills / "local-copilot/SKILL.md").is_file()


@pytest.mark.usefixtures("require_symlink_support")
def test_user_owned_copilot_skill_link_is_rejected_without_removal(
    tmp_path: Path,
) -> None:
    project, manifest = _consumer(tmp_path, platforms=["copilot"])
    outside = tmp_path / "user-skills"
    outside.mkdir()
    github = project / ".github"
    github.mkdir()
    skills = github / "skills"
    skills.symlink_to(outside, target_is_directory=True)
    plan = projection.build_projection_plan(
        REPO_ROOT,
        manifest,
        project_root=project,
    )

    with pytest.raises(projection.ProjectionError, match="user-owned|unmanaged|link"):
        projection.publish_projection(project, plan, source_root=REPO_ROOT)

    assert skills.is_symlink()
