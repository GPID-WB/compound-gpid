"""Public cg-skill migration and old-surface retirement tests."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest


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


def _active_text_files(root: Path) -> tuple[Path, ...]:
    """Scan source-owned files, not ignored or independent nested worktrees."""
    roots = (
        ".github",
        ".claude",
        ".agents",
        ".opencode",
        ".kilo",
        "bin",
        "docs",
        "scripts",
    )
    result = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z",
         "--", *roots],
        cwd=root, capture_output=True, text=True, encoding="utf-8",
        timeout=30, check=True,
    )
    files = []
    for relative in result.stdout.split("\0"):
        path = root / relative
        if not relative or not path.is_file() or Path(relative).parts[:2] == ("scripts", "tests"):
            continue
        if path.suffix.casefold() in {".md", ".json", ".py", ".ps1", ".sh", ".cmd"}:
            files.append(path)
    files.extend((root / "install.ps1", root / "compound-gpid.context.md"))
    return tuple(sorted(set(files)))


@pytest.mark.parametrize("ignored", [False, True])
@pytest.mark.parametrize("git_file", [False, True])
def test_migration_scan_respects_repository_ownership(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, ignored: bool, git_file: bool
) -> None:
    """Nested Git boundaries cannot hide source-owned native release content."""
    root = tmp_path / "source"
    root.mkdir()
    subprocess.run(["git", "init", str(root)], capture_output=True, check=True)
    owned = {
        ".kilo/commands/current.md": "cg-find-skill",
        ".kilo/worktrees/owned/record.md": "source-owned content",
        "docs/skills/management/migration.md": " ".join(OLD_NAMES),
        "install.ps1": "",
        "compound-gpid.context.md": "",
    }
    for relative, content in owned.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=root, capture_output=True, check=True)
    if ignored:
        (root / ".gitignore").write_text(".kilo/worktrees/\n", encoding="utf-8")
    nested = root / ".kilo/worktrees/independent"
    command = ["git", "init"]
    if git_file:
        command.extend(["--separate-git-dir", str(tmp_path / "nested-git")])
    subprocess.run([*command, str(nested)], capture_output=True, check=True)
    (nested / "retired.md").write_text(" ".join(OLD_NAMES), encoding="utf-8")
    untracked = root / ".kilo/commands/new command.md"
    untracked.write_text("new native command", encoding="utf-8")

    assert set(_active_text_files(root)) == {root / path for path in owned} | {untracked}
    monkeypatch.setitem(globals(), "REPO_ROOT", root)
    with pytest.raises(AssertionError, match="current.md"):
        test_old_names_remain_only_in_explicit_migration_text()
    (root / ".kilo/commands/current.md").write_text("cg-skill", encoding="utf-8")
    test_old_names_remain_only_in_explicit_migration_text()


def test_migration_scan_fails_closed_without_git_ownership(tmp_path: Path) -> None:
    """A failed Git query must not silently produce an empty scan."""
    with pytest.raises(subprocess.CalledProcessError):
        _active_text_files(tmp_path)


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
    for path in _active_text_files(REPO_ROOT):
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
