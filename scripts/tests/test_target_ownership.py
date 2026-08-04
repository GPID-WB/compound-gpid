"""Contract tests for generated-target ownership manifests and stale cleanup."""
from __future__ import annotations

# pylint: disable=protected-access

import hashlib
import json
import os
from pathlib import Path

import pytest

import cg_generate_targets as gen
import secure_fs


MANIFEST_NAME = ".compound-gpid-generated.json"


def _write(path: Path, content: str | bytes, *, executable: bool = False) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(content, bytes):
        path.write_bytes(content)
    else:
        path.write_text(content, encoding="utf-8")
    if executable:
        path.chmod(path.stat().st_mode | 0o111)
    return path


def _fixture_repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    _write(
        root / ".github/prompts/cg-alpha.prompt.md",
        "---\ndescription: Alpha\n---\n\n# Alpha\n",
    )
    _write(
        root / ".github/prompts/cg-beta.prompt.md",
        "---\ndescription: Beta\n---\n\n# Beta\n",
    )
    _write(
        root / ".github/agents/cg-review.agent.md",
        "---\ndescription: Review\ntools: [read]\n---\n\n# Review\n",
    )
    _write(
        root / ".github/skills/cg-skill-brainstorming/SKILL.md",
        "---\nname: cg-skill-brainstorming\ndescription: Test\n---\n\n# Skill\n",
    )
    _write(
        root / ".github/skills/cg-skill-brainstorming/workflows/nested/run.sh",
        b"#!/bin/sh\nexit 0\n",
        executable=True,
    )
    _write(root / ".github/instructions/python.instructions.md", "# Python\n")
    _write(root / ".github/shared/runtime-contract.md", "# Runtime contract\n")
    target = {
        "id": "claude-code",
        "name": "Claude Code",
        "generatedTreePath": ".claude",
        "capabilities": {field: True for field in gen.REQUIRED_CAPABILITY_FIELDS},
        "formats": {
            "commandFormat": "claude-command",
            "skillFormat": "claude-skill",
            "agentFormat": "claude-agent",
        },
        "outputPaths": {
            "commands": ".claude/commands",
            "skills": ".claude/skills",
            "agents": ".claude/agents",
            "instructions": ".claude/instructions",
            "shared": ".claude/shared",
            "rootAdapter": ".claude/CLAUDE.md",
        },
    }
    _write(
        root / gen.TARGET_MAPPING_PATH,
        json.dumps({"schemaVersion": 1, "description": "test", "targets": [target]}),
    )
    return root


def _generate(root: Path) -> int:
    return gen.main(["--root", str(root), "--target", "claude-code"])


def _manifest_path(root: Path) -> Path:
    return root / ".claude" / MANIFEST_NAME


def _manifest(root: Path) -> dict:
    return json.loads(_manifest_path(root).read_bytes())


def _manifest_entry(root: Path, destination: str) -> dict:
    return next(item for item in _manifest(root)["files"] if item["path"] == destination)


def test_manifest_is_deterministic_sorted_schema_v1_and_identifies_policy(tmp_path: Path) -> None:
    root = _fixture_repo(tmp_path)
    assert _generate(root) == 0
    first = _manifest_path(root).read_bytes()
    data = json.loads(first)

    assert data.keys() == {"schemaVersion", "target", "policyVersion", "files"}
    assert data["schemaVersion"] == 1
    assert data["target"] == "claude-code"
    assert data["policyVersion"] == 1
    assert [item["path"] for item in data["files"]] == sorted(
        item["path"] for item in data["files"]
    )
    assert first == (json.dumps(data, indent=2, ensure_ascii=False) + "\n").encode()


def test_manifest_completely_covers_generated_files_without_self_hash(tmp_path: Path) -> None:
    root = _fixture_repo(tmp_path)
    assert _generate(root) == 0
    target_root = root / ".claude"
    actual = {
        path.relative_to(root).as_posix()
        for path in target_root.rglob("*")
        if path.is_file() and path.name != MANIFEST_NAME
    }
    recorded = {item["path"] for item in _manifest(root)["files"]}

    assert recorded == actual
    assert not any(item["path"] == ".claude/" + MANIFEST_NAME for item in _manifest(root)["files"])


def test_manifest_entries_record_destination_source_kind_hash_and_executable(tmp_path: Path) -> None:
    root = _fixture_repo(tmp_path)
    assert _generate(root) == 0

    for item in _manifest(root)["files"]:
        assert item.keys() == {"path", "source", "kind", "sha256", "executable"}
        assert item["path"].startswith(".claude/")
        assert isinstance(item["source"], str) and item["source"]
        assert isinstance(item["kind"], str) and item["kind"]
        assert item["sha256"] == hashlib.sha256((root / item["path"]).read_bytes()).hexdigest()
        assert isinstance(item["executable"], bool)

    script = _manifest_entry(
        root, ".claude/skills/cg-skill-brainstorming/workflows/nested/run.sh"
    )
    assert script["source"].endswith("workflows/nested/run.sh")
    assert script["kind"] == "skill-resource"
    assert script["executable"] is (os.name != "nt")


@pytest.mark.parametrize(
    "mutate",
    [
        pytest.param(lambda data: data.update(schemaVersion=2), id="schema"),
        pytest.param(lambda data: data["files"].append(dict(data["files"][0])), id="duplicate"),
        pytest.param(lambda data: data.update(target="foreign"), id="foreign-target"),
        pytest.param(lambda data: data["files"][0].update(path="../unsafe"), id="unsafe-path"),
        pytest.param(lambda data: data["files"][0].update(sha256="not-a-sha256"), id="invalid-hash"),
    ],
)
def test_manifest_rejects_malformed_schema_duplicate_foreign_unsafe_and_hash(
    tmp_path: Path, mutate
) -> None:
    root = _fixture_repo(tmp_path)
    assert _generate(root) == 0
    data = _manifest(root)
    before = {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in (root / ".claude").rglob("*")
        if path.is_file() and path.name != MANIFEST_NAME
    }
    mutate(data)
    poisoned = (json.dumps(data) + "\n").encode()
    _manifest_path(root).write_bytes(poisoned)

    assert _generate(root) == 1
    assert _manifest_path(root).read_bytes() == poisoned
    assert all((root / path).read_bytes() == content for path, content in before.items())


def test_manifest_second_generation_is_byte_identical(tmp_path: Path) -> None:
    root = _fixture_repo(tmp_path)
    assert _generate(root) == 0
    first = _manifest_path(root).read_bytes()
    assert _generate(root) == 0
    assert _manifest_path(root).read_bytes() == first


def test_generation_repairs_windows_line_endings_without_conflict(
    tmp_path: Path,
) -> None:
    root = _fixture_repo(tmp_path)
    assert _generate(root) == 0
    command = root / ".claude/commands/cg-alpha.md"
    command.write_bytes(command.read_bytes().replace(b"\n", b"\r\n"))

    assert _generate(root) == 0
    assert b"\r\n" not in command.read_bytes()
    assert _manifest_entry(root, ".claude/commands/cg-alpha.md")["sha256"] == hashlib.sha256(
        command.read_bytes()
    ).hexdigest()


def test_cleanup_deletes_unchanged_stale_file_after_source_delete_and_rename(tmp_path: Path) -> None:
    root = _fixture_repo(tmp_path)
    assert _generate(root) == 0
    old = root / ".claude/commands/cg-alpha.md"
    source = root / ".github/prompts/cg-alpha.prompt.md"
    source.rename(source.with_name("cg-renamed.prompt.md"))

    assert _generate(root) == 0
    assert not old.exists()
    assert (root / ".claude/commands/cg-renamed.md").is_file()
    assert ".claude/commands/cg-alpha.md" not in {item["path"] for item in _manifest(root)["files"]}


def test_cleanup_modified_stale_is_preserved_and_fails_before_other_cleanup(tmp_path: Path) -> None:
    root = _fixture_repo(tmp_path)
    assert _generate(root) == 0
    modified = root / ".claude/commands/cg-alpha.md"
    unchanged = root / ".claude/commands/cg-beta.md"
    modified.write_text("user edit\n", encoding="utf-8")
    (root / ".github/prompts/cg-alpha.prompt.md").unlink()
    (root / ".github/prompts/cg-beta.prompt.md").unlink()
    manifest_before = _manifest_path(root).read_bytes()

    assert _generate(root) == 1
    assert modified.read_text(encoding="utf-8") == "user edit\n"
    assert unchanged.is_file()
    assert _manifest_path(root).read_bytes() == manifest_before


def _seed_legacy_model_mapping(root: Path) -> Path:
    legacy = _write(root / ".claude/model-mapping.claude.json", b'{"legacy": true}\n')
    data = _manifest(root)
    data["files"].append({
        "path": ".claude/model-mapping.claude.json",
        "source": ".claude/model-mapping.claude.json",
        "kind": "legacy-model-mapping",
        "sha256": hashlib.sha256(legacy.read_bytes()).hexdigest(),
        "executable": False,
    })
    _manifest_path(root).write_bytes((json.dumps(data, indent=2, ensure_ascii=False) + "\n").encode())
    return legacy


def test_cleanup_removes_unchanged_legacy_model_mapping(tmp_path: Path) -> None:
    root = _fixture_repo(tmp_path)
    assert _generate(root) == 0
    legacy = _seed_legacy_model_mapping(root)

    assert _generate(root) == 0
    assert not legacy.exists()
    assert ".claude/model-mapping.claude.json" not in {
        item["path"] for item in _manifest(root)["files"]
    }


def test_cleanup_preserves_modified_legacy_model_mapping(tmp_path: Path) -> None:
    root = _fixture_repo(tmp_path)
    assert _generate(root) == 0
    legacy = _seed_legacy_model_mapping(root)
    legacy.write_text("user edit\n", encoding="utf-8")

    assert _generate(root) == 1
    assert legacy.read_text(encoding="utf-8") == "user edit\n"


@pytest.mark.backend_posix
@pytest.mark.skipif(not gen._supports_secure_dir_fd(), reason="requires POSIX dir_fd support")
def test_cleanup_rechecks_stale_content_immediately_before_unlink(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _fixture_repo(tmp_path)
    assert _generate(root) == 0
    stale = root / ".claude/commands/cg-alpha.md"
    (root / ".github/prompts/cg-alpha.prompt.md").unlink()
    plan = gen.build_generation_plan(
        root, gen.load_target_mapping(root), gen.scan_canonical_assets(root)
    )
    monkeypatch.setattr(
        gen, "_before_secure_unlink",
        lambda path: path.write_text("new user content\n", encoding="utf-8") if path == stale else None,
    )

    with pytest.raises(ValueError, match="changed before deletion"):
        gen.commit_generation_plan(root, plan, ("claude-code",))
    assert stale.read_text(encoding="utf-8") == "new user content\n"


@pytest.mark.backend_posix
@pytest.mark.skipif(not gen._supports_secure_dir_fd(), reason="requires POSIX dir_fd support")
def test_cleanup_rollback_never_overwrites_post_quarantine_collision(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _fixture_repo(tmp_path)
    assert _generate(root) == 0
    stale = root / ".claude/commands/cg-alpha.md"
    (root / ".github/prompts/cg-alpha.prompt.md").unlink()
    plan = gen.build_generation_plan(
        root, gen.load_target_mapping(root), gen.scan_canonical_assets(root)
    )

    def collide_after_quarantine(original: Path, _quarantine: Path) -> None:
        # Only collide on the stale file's path — the write path also
        # quarantines existing files (e.g. CLAUDE.md) and must not collide.
        if original == stale:
            original.write_text("concurrent-user-content\n", encoding="utf-8")

    monkeypatch.setattr(
        gen,
        "_before_secure_unlink",
        lambda path: path.write_text("changed-owned-content\n", encoding="utf-8"),
    )
    monkeypatch.setattr(secure_fs, "_after_secure_quarantine", collide_after_quarantine)

    with pytest.raises(ValueError, match="quarantine preserved"):
        gen.commit_generation_plan(root, plan, ("claude-code",))

    assert stale.read_text(encoding="utf-8") == "concurrent-user-content\n"
    quarantine_files = list(stale.parent.glob(f".{stale.name}.*.stale"))
    assert len(quarantine_files) == 1
    assert quarantine_files[0].read_text(encoding="utf-8") == "changed-owned-content\n"


@pytest.mark.backend_posix
@pytest.mark.backend_windows
@pytest.mark.skipif(
    os.name != "nt" and not gen._supports_secure_dir_fd(),
    reason="requires Windows handle pinning or POSIX dir_fd support",
)
def test_commit_rechecks_destination_ancestor_immediately_before_write(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _fixture_repo(tmp_path)
    plan = gen.build_generation_plan(
        root, gen.load_target_mapping(root), gen.scan_canonical_assets(root)
    )
    outside = tmp_path / "outside"
    outside.mkdir()
    commands = root / ".claude/commands"
    displaced = root / ".claude/commands-displaced"
    replaced = False

    def replace_at_write_boundary(destination: Path) -> None:
        nonlocal replaced
        if destination.parent == commands and not replaced:
            commands.rename(displaced)
            commands.symlink_to(outside, target_is_directory=True)
            replaced = True

    monkeypatch.setattr(gen, "_before_secure_replace", replace_at_write_boundary)

    with pytest.raises(OSError):
        gen.commit_generation_plan(root, plan, ("claude-code",))
    assert list(outside.iterdir()) == []


@pytest.mark.backend_posix
@pytest.mark.backend_windows
def test_commit_rejects_later_destination_changed_after_preflight(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _fixture_repo(tmp_path)
    assert _generate(root) == 0
    plan = gen.build_generation_plan(
        root,
        gen.load_target_mapping(root),
        gen.scan_canonical_assets(root),
    )
    destinations = [
        root / entry.destination
        for entry in plan.by_target["claude-code"].entries
    ]
    assert len(destinations) >= 2
    later = destinations[1]
    calls = 0

    def change_later_destination(_path: Path) -> None:
        nonlocal calls
        calls += 1
        if calls == 1:
            later.write_bytes(b"late user content")

    monkeypatch.setattr(gen, "_before_secure_replace", change_later_destination)

    with pytest.raises(OSError, match="changed after authorization"):
        gen.commit_generation_plan(root, plan, ("claude-code",))

    assert later.read_bytes() == b"late user content"


@pytest.mark.backend_posix
@pytest.mark.backend_windows
def test_commit_rejects_manifest_changed_after_pinned_preflight(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _fixture_repo(tmp_path)
    assert _generate(root) == 0
    plan = gen.build_generation_plan(
        root,
        gen.load_target_mapping(root),
        gen.scan_canonical_assets(root),
    )
    manifest = _manifest_path(root)
    original_write = gen._secure_write_entry

    def change_manifest_before_write(root_path, entry, expected_state):
        if entry.kind == "manifest":
            manifest.write_bytes(b"late unowned manifest")
        return original_write(root_path, entry, expected_state)

    monkeypatch.setattr(gen, "_secure_write_entry", change_manifest_before_write)

    with pytest.raises(OSError, match="changed after authorization"):
        gen.commit_generation_plan(root, plan, ("claude-code",))

    assert manifest.read_bytes() == b"late unowned manifest"


def test_cleanup_untracked_file_is_preserved(tmp_path: Path) -> None:
    root = _fixture_repo(tmp_path)
    assert _generate(root) == 0
    untracked = _write(root / ".claude/notes/private.txt", "mine\n")

    assert _generate(root) == 0
    assert untracked.read_text(encoding="utf-8") == "mine\n"
    assert untracked.relative_to(root).as_posix() not in {
        item["path"] for item in _manifest(root)["files"]
    }


def test_cleanup_adopts_equal_unowned_expected_destination(tmp_path: Path) -> None:
    root = _fixture_repo(tmp_path)
    plan = gen.build_generation_plan(
        root,
        gen.load_target_mapping(root),
        gen.scan_canonical_assets(root),
    )
    expected = next(
        item for item in plan.by_target["claude-code"].entries
        if item.destination == ".claude/commands/cg-alpha.md"
    )
    _write(root / expected.destination, expected.content)

    assert _generate(root) == 0
    assert _manifest_entry(root, expected.destination)["sha256"] == expected.sha256


def test_cleanup_conflicting_unowned_destination_is_preserved_and_fails(tmp_path: Path) -> None:
    root = _fixture_repo(tmp_path)
    conflict = _write(root / ".claude/commands/cg-alpha.md", "user-owned\n")

    assert _generate(root) == 1
    assert conflict.read_text(encoding="utf-8") == "user-owned\n"
    assert not _manifest_path(root).exists()


def test_cleanup_malformed_manifest_fails_without_tree_mutation(tmp_path: Path) -> None:
    root = _fixture_repo(tmp_path)
    assert _generate(root) == 0
    generated = root / ".claude/commands/cg-alpha.md"
    before = generated.read_bytes()
    _manifest_path(root).write_bytes(b"{ malformed")

    assert _generate(root) == 1
    assert generated.read_bytes() == before
    assert _manifest_path(root).read_bytes() == b"{ malformed"


@pytest.mark.skipif(not gen._supports_secure_dir_fd(), reason="requires POSIX dir_fd support")
def test_cleanup_interrupted_per_file_write_recovers_with_manifest_written_last(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _fixture_repo(tmp_path)
    assert _generate(root) == 0
    old_manifest = _manifest_path(root).read_bytes()
    source = root / ".github/prompts/cg-alpha.prompt.md"
    source.write_text(source.read_text(encoding="utf-8") + "changed\n", encoding="utf-8")
    calls: list[Path] = []

    def interrupt(path: Path) -> None:
        calls.append(path)
        if len(calls) == 2:
            raise OSError("simulated interruption")

    monkeypatch.setattr(gen, "_before_secure_replace", interrupt)
    with pytest.raises(OSError, match="simulated interruption"):
        gen.commit_generation_plan(
            root,
            gen.build_generation_plan(
                root,
                gen.load_target_mapping(root),
                gen.scan_canonical_assets(root),
            ),
            ("claude-code",),
        )
    assert _manifest_path(root).read_bytes() == old_manifest
    assert _manifest_path(root) not in calls

    monkeypatch.setattr(gen, "_before_secure_replace", lambda _path: None)
    assert _generate(root) == 0
    assert _manifest_path(root).read_bytes() != old_manifest
    assert _manifest_entry(root, ".claude/commands/cg-alpha.md")["sha256"] == hashlib.sha256(
        (root / ".claude/commands/cg-alpha.md").read_bytes()
    ).hexdigest()


def test_cleanup_leaves_empty_directories_to_avoid_pathname_pruning(tmp_path: Path) -> None:
    root = _fixture_repo(tmp_path)
    assert _generate(root) == 0
    source = root / ".github/skills/cg-skill-brainstorming/workflows/nested/run.sh"
    generated_parent = root / ".claude/skills/cg-skill-brainstorming/workflows/nested"
    source.unlink()

    assert _generate(root) == 0
    assert generated_parent.is_dir()
    assert (root / ".claude").is_dir()
    assert _manifest_path(root).is_file()
