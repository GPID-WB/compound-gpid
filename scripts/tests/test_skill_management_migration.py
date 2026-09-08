"""Public cg-skill migration and old-surface retirement tests."""
from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
OLD_NAMES = ("cg-find-skill", "cg-import-skill")
GENERATED_COMMAND_ROOTS = (
    ".claude/commands",
    ".agents/commands",
    ".opencode/commands",
    ".kilo/commands",
)
MIGRATION_REFERENCES = {
    "docs/skills/management/migration.md",
    "install.ps1",
    "scripts/install.sh",
}


def _active_text_files() -> tuple[Path, ...]:
    files = []
    for relative in (
        ".github",
        ".claude",
        ".agents",
        ".opencode",
        ".kilo",
        "bin",
        "docs",
        "scripts",
    ):
        for path in (REPO_ROOT / relative).rglob("*"):
            if not path.is_file() or "scripts/tests" in path.as_posix():
                continue
            if path.suffix.casefold() in {".md", ".json", ".py", ".ps1", ".sh", ".cmd"}:
                files.append(path)
    files.extend((REPO_ROOT / "install.ps1", REPO_ROOT / "compound-gpid.context.md"))
    return tuple(sorted(set(files)))


def test_public_prompt_and_wrappers_replace_old_surfaces() -> None:
    assert (REPO_ROOT / ".github/prompts/cg-skill.prompt.md").is_file()
    assert (REPO_ROOT / "bin/cg-skill").is_file()
    assert (REPO_ROOT / "bin/cg-skill.cmd").is_file()
    for old_name in OLD_NAMES:
        assert not (REPO_ROOT / f".github/prompts/{old_name}.prompt.md").exists()
        for root in GENERATED_COMMAND_ROOTS:
            assert not (REPO_ROOT / root / f"{old_name}.md").exists()
    assert not (REPO_ROOT / "bin/cg-find-skill").exists()
    assert not (REPO_ROOT / "bin/cg-find-skill.cmd").exists()
    for root in GENERATED_COMMAND_ROOTS:
        assert (REPO_ROOT / root / "cg-skill.md").is_file()


def test_windows_wrapper_uses_guarded_python_detection_and_exact_entrypoint() -> None:
    content = (REPO_ROOT / "bin/cg-skill.cmd").read_text(encoding="utf-8")
    for candidate in ("python3", "python", "py"):
        assert f"where {candidate} >nul 2>&1" in content
        assert f"call {candidate} -c" in content
    assert 'call %PYTHON_CMD% "%~dp0..\\scripts\\cg_skill.py" %*' in content
    assert "exit /b %ERRORLEVEL%" in content


def test_posix_wrapper_resolves_python_and_forwards_arguments() -> None:
    content = (REPO_ROOT / "bin/cg-skill").read_text(encoding="utf-8")
    assert content.startswith("#!/usr/bin/env bash\n")
    assert "for candidate in python3 python py" in content
    assert 'exec "$PYTHON_CMD" "$SCRIPT_DIR/../scripts/cg_skill.py" "$@"' in content


def test_skill_management_is_a_public_cg_suite_capability() -> None:
    registry = json.loads(
        (REPO_ROOT / ".github/shared/module-registry.json").read_text(encoding="utf-8")
    )
    capability = next(
        item for item in registry["capabilities"] if item["id"] == "skill-management"
    )
    suite = next(item for item in registry["modules"] if item["id"] == "suite-cg")
    assert capability["owningModule"] == "cap-skill-management"
    assert capability["supportedSuites"] == ["cg"]
    assert capability["configSelectors"] == []
    assert "/cg-skill" in capability["taskTriggers"]
    assert "cap-skill-management" in suite["dependsOn"]


def test_old_names_remain_only_in_explicit_migration_text() -> None:
    occurrences = {name: [] for name in OLD_NAMES}
    for path in _active_text_files():
        relative = path.relative_to(REPO_ROOT).as_posix()
        content = path.read_text(encoding="utf-8", errors="strict")
        for old_name in OLD_NAMES:
            if old_name in content:
                occurrences[old_name].append(relative)
    for old_name, paths in occurrences.items():
        assert set(paths) <= MIGRATION_REFERENCES, (old_name, paths)
        assert "docs/skills/management/migration.md" in paths


def test_public_navigation_and_benchmark_use_cg_skill() -> None:
    navigation = json.loads((REPO_ROOT / "docs/navigation.json").read_text(encoding="utf-8"))
    groups = [group for group in navigation["groups"] if group["title"] == "Skill Management"]
    assert len(groups) == 1
    assert len(groups[0]["pages"]) == 29
    benchmark = (REPO_ROOT / "scripts/cg_projection_benchmark.py").read_text(
        encoding="utf-8"
    )
    assert '"requestedCommand": "/cg-skill find"' in benchmark
    assert '"expectedRoute": "cg-skill find"' in benchmark
