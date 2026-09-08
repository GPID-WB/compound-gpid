"""Tests for cg_generate_targets.py generator core.

Run from repo root:
    python3 -m pytest scripts/tests/test_cg_generate_targets.py -v
"""
from __future__ import annotations

import hashlib
import json
import os
from collections import Counter
from pathlib import Path
from types import SimpleNamespace

import pytest

import cg_generate_targets as gen


REPO_ROOT = Path(__file__).resolve().parents[2]
RENAMED_COMMAND_PATHS = {
    "claude-code": ".claude/commands/cg-compound-gpid-rd.md",
    "codex": ".agents/commands/cg-compound-gpid-rd.md",
    "opencode": ".opencode/commands/cg-compound-gpid-rd.md",
    "kilo": ".kilo/commands/cg-compound-gpid-rd.md",
}
OLD_COMMAND_PATHS = {
    "claude-code": ".claude/commands/cg-review-repos.md",
    "codex": ".agents/commands/cg-review-repos.md",
    "opencode": ".opencode/commands/cg-review-repos.md",
    "kilo": ".kilo/commands/cg-review-repos.md",
}
ARGUMENT_BLOCK_SUFFIXES = {
    "opencode": (
        b"\n## OpenCode Invocation Arguments\n\n"
        b"User-provided slash-command arguments:\n\n"
        b"```text\n$ARGUMENTS\n```\n"
    ),
    "kilo": (
        b"\n## Invocation Arguments\n\n"
        b"User-provided slash-command arguments:\n\n"
        b"```text\n$ARGUMENTS\n```\n"
    ),
}
COMMIT_PUSH_COMMAND_PATHS = {
    "claude-code": ".claude/commands/cg-commit-push-pr.md",
    "codex": ".agents/commands/cg-commit-push-pr.md",
    "opencode": ".opencode/commands/cg-commit-push-pr.md",
    "kilo": ".kilo/commands/cg-commit-push-pr.md",
}
EXPECTED_PLAN_TARGETS = set(COMMIT_PUSH_COMMAND_PATHS) | {"copilot"}
SOURCE_MARKER = ".compound-gpid-source.json"


def _write(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def _generated_command_body(content: bytes) -> bytes:
    """Return exact generated command bytes after YAML frontmatter."""
    prefix, opening, remainder = content.partition(b"---\n")
    assert opening and not prefix, "Generated command must start with YAML frontmatter"
    _frontmatter, closing, body = remainder.partition(b"---\n\n")
    assert closing, "Generated command must close YAML frontmatter"
    return body


def _worktree_output_matches(
    entry: gen.OutputEntry,
    current_bytes: bytes,
    copilot_destinations: set[str],
) -> bool:
    """Compare planned output without treating canonical checkout EOLs as drift."""
    if current_bytes == entry.content:
        return True
    if (
        entry.target_id != "copilot"
        or entry.destination not in copilot_destinations
    ):
        return False
    if entry.destination != entry.source:
        return False
    if not gen.bundle_service.is_normalized_markdown_path(entry.source):
        return False
    if b"\r" in entry.content:
        return False
    return current_bytes == entry.content.replace(b"\n", b"\r\n")


def _worktree_output_mismatches(
    root: Path,
    entries: tuple[gen.OutputEntry, ...],
    copilot_destinations: set[str],
) -> list[str]:
    """Return missing or byte-mismatched outputs from the release parity gate."""
    mismatches = []
    for entry in entries:
        output_path = root / entry.destination
        if not output_path.is_file():
            mismatches.append(f"missing:{entry.destination}")
            continue
        if not _worktree_output_matches(
            entry, output_path.read_bytes(), copilot_destinations
        ):
            mismatches.append(f"content:{entry.destination}")
    return mismatches


def _make_fixture_repo(tmp_path: Path) -> Path:
    """Create a minimal fixture repo with .github/ canonical assets."""
    root = tmp_path / "fixture"

    _write(root / ".github/prompts/cg-test.prompt.md",
           "---\ndescription: Test prompt\n---\n\n# Test Prompt\n\nBody.\n")
    _write(root / ".github/prompts/cg-another.prompt.md",
           "---\ndescription: Another prompt\n---\n\n# Another\n\nBody.\n")

    _write(root / ".github/agents/cg-test-agent.agent.md",
           "---\ndescription: Test agent\ntools: ['read', 'write']\n---\n\n# Test Agent\n\nAgent body.\n")

    _write(root / ".github/skills/cg-skill-test/SKILL.md",
           "---\nname: cg-skill-test\ndescription: Test skill\n---\n\n# Test Skill\n\nSkill body.\n")
    _write(root / ".github/instructions/python.instructions.md", "# Python instructions\n")
    _write(root / ".github/shared/runtime-contract.md", "# Runtime contract\n")

    _write(root / ".github/shared/target-mapping.json", json.dumps({
        "schemaVersion": 1,
        "description": "Test mapping",
        "targets": [
            {
                "id": "copilot",
                "name": "GitHub Copilot",
                "generatedTreePath": None,
                "capabilities": {f: True for f in gen.REQUIRED_CAPABILITY_FIELDS},
                "formats": {f: "github-" + f.replace("Format", "") for f in gen.REQUIRED_FORMAT_FIELDS},
                "outputPaths": {"commands": ".github/prompts", "skills": ".github/skills", "agents": ".github/agents", "instructions": ".github/instructions", "shared": ".github/shared"},
            },
            {
                "id": "claude-code",
                "name": "Claude Code",
                "generatedTreePath": ".claude",
                "capabilities": {f: True for f in gen.REQUIRED_CAPABILITY_FIELDS},
                "formats": {"commandFormat": "claude-command", "skillFormat": "claude-skill", "agentFormat": "claude-agent"},
                "outputPaths": {
                    "commands": ".claude/commands",
                    "skills": ".claude/skills",
                    "agents": ".claude/agents",
                    "instructions": ".claude/instructions",
                    "shared": ".claude/shared",
                    "rootAdapter": ".claude/CLAUDE.md",
                },
            },
            {
                "id": "codex",
                "name": "Codex",
                "generatedTreePath": ".agents",
                "capabilities": {f: True for f in gen.REQUIRED_CAPABILITY_FIELDS},
                "formats": {"commandFormat": "codex-command", "skillFormat": "codex-skill", "agentFormat": "codex-subagent-toml", "fallbackAgentFormat": "codex-skill"},
                "outputPaths": {
                    "commands": ".agents/commands",
                    "skills": ".agents/skills",
                    "agents": ".agents/subagents",
                    "instructions": ".agents/instructions",
                    "shared": ".agents/shared",
                    "rootAdapter": ".agents/AGENTS.md",
                },
            },
            {
                "id": "opencode",
                "name": "OpenCode",
                "generatedTreePath": ".opencode",
                "capabilities": {f: True for f in gen.REQUIRED_CAPABILITY_FIELDS},
                "formats": {"commandFormat": "opencode-command", "skillFormat": "opencode-skill", "agentFormat": "opencode-agent"},
                "outputPaths": {
                    "commands": ".opencode/commands",
                    "skills": ".opencode/skills",
                    "agents": ".opencode/agents",
                    "instructions": ".opencode/instructions",
                    "shared": ".opencode/shared",
                    "rootAdapter": ".opencode/AGENTS.md",
                    "config": ".opencode/opencode.json",
                },
            },
            {
                "id": "kilo",
                "name": "Kilo",
                "generatedTreePath": ".kilo",
                "capabilities": {f: True for f in gen.REQUIRED_CAPABILITY_FIELDS},
                "formats": {"commandFormat": "kilo-command", "skillFormat": "kilo-skill", "agentFormat": "kilo-agent"},
                "outputPaths": {
                    "commands": ".kilo/commands",
                    "skills": ".kilo/skills",
                    "agents": ".kilo/agents",
                    "instructions": ".kilo/instructions",
                    "shared": ".kilo/shared",
                    "rootAdapter": ".kilo/AGENTS.md",
                    "config": ".kilo/kilo.json",
                },
            },
        ],
    }))

    return root


def _install_fixture_registry(root: Path) -> Path:
    """Add a minimal registry that owns the fixture skill bundle."""
    return _write(
        root / gen.MODULE_REGISTRY_PATH,
        json.dumps({
            "schemaVersion": 1,
            "description": "fixture registry",
            "modules": [{
                "id": "kernel",
                "layer": "kernel",
                "displayName": "Kernel",
                "description": "fixture",
                "dependsOn": [],
                "ownedAssets": [".github/skills/cg-skill-test/"],
            }],
        }),
    )


_CANONICAL_SECURITY_CASES = (
    ("prompt", ".github/prompts/cg-test.prompt.md"),
    ("agent", ".github/agents/cg-test-agent.agent.md"),
    ("skill", ".github/skills/cg-skill-test/SKILL.md"),
    ("instruction", ".github/instructions/python.instructions.md"),
    ("module registry", gen.MODULE_REGISTRY_PATH),
    ("target mapping", gen.TARGET_MAPPING_PATH),
)


def _read_security_case(root: Path, case: str) -> str:
    """Read one canonical class through its production generator boundary."""
    if case == "module registry":
        registry = gen._load_module_registry(root)  # pylint: disable=protected-access
        assert registry is not None
        return str(registry["description"])
    if case == "target mapping":
        return str(gen.load_target_mapping(root)["description"])
    if case == "skill":
        files = gen._inventory_skill_bundle(  # pylint: disable=protected-access
            root,
            root / ".github/skills/cg-skill-test",
        )
        skill = next(
            item for item in files if item["bundle_relative_path"] == "SKILL.md"
        )
        return skill["content"].decode("utf-8")
    assets = gen.scan_canonical_assets(root)
    category = {
        "prompt": "prompts",
        "agent": "agents",
        "instruction": "instructions",
    }[case]
    relative_path = dict(_CANONICAL_SECURITY_CASES)[case]
    asset = next(
        item for item in assets[category]
        if item["relative_path"] == relative_path
    )
    return str(asset["body"])


class TestScanCanonicalAssets:
    @pytest.mark.parametrize(
        "value",
        [
            "../escape",
            "/absolute",
            "C:/drive",
            "folder/CON.txt",
            "folder/trailing. ",
            "folder/bad:name",
        ],
    )
    def test_portable_path_policy_rejects_cross_platform_hazards(
        self, value: str
    ) -> None:
        assert gen.validate_repo_relative_path("fixture", value)

    def test_finds_prompts(self, tmp_path: Path) -> None:
        root = _make_fixture_repo(tmp_path)
        assets = gen.scan_canonical_assets(root)
        assert len(assets["prompts"]) == 2
        assert assets["prompts"][0]["filename"] == "cg-another.prompt.md"

    def test_finds_agents(self, tmp_path: Path) -> None:
        root = _make_fixture_repo(tmp_path)
        assets = gen.scan_canonical_assets(root)
        assert len(assets["agents"]) == 1

    def test_finds_skills(self, tmp_path: Path) -> None:
        root = _make_fixture_repo(tmp_path)
        assets = gen.scan_canonical_assets(root)
        assert len(assets["skills"]) == 1

    def test_missing_canonical_roots_fail(self, tmp_path: Path) -> None:
        root = tmp_path / "empty"
        root.mkdir()
        (root / ".github/shared/target-mapping.json").parent.mkdir(parents=True)
        with pytest.raises(ValueError, match="Required canonical prompts root"):
            gen.scan_canonical_assets(root)

    @pytest.mark.parametrize("category", ["prompts", "agents", "skills", "instructions", "shared"])
    def test_empty_required_canonical_inventory_fails(self, tmp_path: Path, category: str) -> None:
        root = _make_fixture_repo(tmp_path)
        path = root / ".github" / category
        for item in sorted(path.rglob("*"), reverse=True):
            if item.is_file():
                item.unlink()
            elif item.is_dir():
                item.rmdir()

        with pytest.raises(ValueError, match=f"canonical {category} inventory is empty"):
            gen.scan_canonical_assets(root)

    def test_regular_pyc_inside_skill_bundle_is_rejected(self, tmp_path: Path) -> None:
        root = _make_fixture_repo(tmp_path)
        cache_file = root / ".github/skills/cg-skill-test/nested/module.pyc"
        cache_file.parent.mkdir(parents=True)
        cache_file.write_bytes(b"bytecode")

        with pytest.raises(ValueError, match=r"cache|\.pyc"):
            gen.scan_canonical_assets(root)

    def test_nested_shared_resources_are_recursive_and_path_preserving(
        self, tmp_path: Path
    ) -> None:
        root = _make_fixture_repo(tmp_path)
        _write(
            root / ".github/shared/skill-management/contracts/common.json",
            '{"kind":"contract"}\n',
        )
        _write(
            root / ".github/shared/skill-management/operations/common.json",
            '{"contract":".github/shared/skill-management/contracts/common.json",'
            '"workflow":".github/skills/cg-skill-test/workflows/common.md"}\n',
        )
        _write(
            root / ".github/skills/cg-skill-test/workflows/common.md",
            "# Common workflow\n",
        )

        assets = gen.scan_canonical_assets(root)
        plan = gen.build_generation_plan(root, gen.load_target_mapping(root), assets)

        for target_id, shared_root in {
            "claude-code": ".claude/shared",
            "codex": ".agents/shared",
            "opencode": ".opencode/shared",
            "kilo": ".kilo/shared",
        }.items():
            entries = {
                entry.destination: entry
                for entry in plan.by_target[target_id].entries
                if entry.kind == "shared"
            }
            contract = f"{shared_root}/skill-management/contracts/common.json"
            operation = f"{shared_root}/skill-management/operations/common.json"
            assert entries[contract].content == b'{"kind":"contract"}\n'
            operation_text = entries[operation].content.decode("utf-8")
            assert f'{shared_root}/skill-management/contracts/common.json' in operation_text
            skill_root = {
                "claude-code": ".claude/skills",
                "codex": ".agents/skills",
                "opencode": ".opencode/skills",
                "kilo": ".kilo/skills",
            }[target_id]
            assert f'{skill_root}/cg-skill-test/workflows/common.md' in operation_text
            assert entries[contract].source.endswith(
                "skill-management/contracts/common.json"
            )

    def test_default_cg_generation_includes_public_management_module(
        self,
    ) -> None:
        repository_root = Path(__file__).resolve().parents[2]
        assets = gen.scan_canonical_assets(repository_root)
        paths = {
            item["relative_path"]
            for category in assets.values()
            for item in category
        }
        assert ".github/skills/cg-skill-management/SKILL.md" in paths
        assert (
            ".github/shared/skill-management/contracts/result-v1.schema.json"
            in paths
        )
        assert ".github/shared/skill-management/operations/help.json" in paths

    @pytest.mark.usefixtures("require_symlink_support")
    def test_shared_leaf_swap_is_rejected_at_the_secure_read_boundary(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        root = _make_fixture_repo(tmp_path)
        target = _write(
            root / ".github/shared/skill-management/contracts/common.json",
            '{"kind":"contract"}\n',
        )
        outside = _write(tmp_path / "outside-secret.json", "secret\n")
        original = gen.secure_fs.secure_read_bytes
        swapped = False

        def swap_then_read(read_root, relative_path, **kwargs):
            nonlocal swapped
            if str(relative_path).replace("\\", "/").endswith(
                "skill-management/contracts/common.json"
            ) and not swapped:
                target.unlink()
                target.symlink_to(outside)
                swapped = True
            return original(read_root, relative_path, **kwargs)

        monkeypatch.setattr(gen.secure_fs, "secure_read_bytes", swap_then_read)
        with pytest.raises((OSError, ValueError), match="link|reparse|safe|regular"):
            gen.scan_canonical_assets(root)

    @pytest.mark.usefixtures("require_symlink_support")
    def test_nested_shared_directory_link_is_rejected_without_following(
        self, tmp_path: Path
    ) -> None:
        root = _make_fixture_repo(tmp_path)
        outside = tmp_path / "outside"
        outside.mkdir()
        _write(outside / "secret.json", "secret\n")
        link = root / ".github/shared/skill-management"
        link.symlink_to(outside, target_is_directory=True)

        with pytest.raises(ValueError, match="link|reparse"):
            gen.scan_canonical_assets(root)

    @pytest.mark.skipif(
        os.name == "nt",
        reason="NTFS maps colon paths to alternate data streams",
    )
    def test_unsafe_nested_shared_path_is_rejected(self, tmp_path: Path) -> None:
        root = _make_fixture_repo(tmp_path)
        unsafe = root / ".github/shared/skill-management/contracts/bad:name.json"
        try:
            _write(unsafe, "{}\n")
        except OSError:
            pytest.skip("host filesystem cannot create the unsafe path fixture")

        with pytest.raises(ValueError, match="forbidden|portable|unsafe"):
            gen.scan_canonical_assets(root)

    def test_nested_hidden_shared_artifact_is_rejected(self, tmp_path: Path) -> None:
        root = _make_fixture_repo(tmp_path)
        _write(
            root / ".github/shared/skill-management/contracts/.local.json",
            "{}\n",
        )
        with pytest.raises(ValueError, match="local artifact"):
            gen.scan_canonical_assets(root)

    def test_inactive_shared_directory_is_not_traversed_or_counted(
        self, tmp_path: Path
    ) -> None:
        root = _make_fixture_repo(tmp_path)
        _write(root / ".github/shared/inactive/.local.json", "{}\n")
        selected = gen.path_policy.inventory_shared_assets(
            root,
            include_globs=(".github/shared/runtime-contract.md",),
            max_files=1,
            max_depth=1,
        )
        assert selected == [".github/shared/runtime-contract.md"]
        with pytest.raises(ValueError, match="local artifact"):
            gen.path_policy.inventory_shared_assets(
                root,
                include_globs=(".github/shared/inactive/",),
            )

    def test_git_index_is_the_portable_executable_source(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        root = tmp_path.resolve()
        calls = []

        def run(arguments, **_kwargs):
            calls.append(arguments)
            if "--show-toplevel" in arguments:
                return SimpleNamespace(returncode=0, stdout=str(root), stderr="")
            return SimpleNamespace(
                returncode=0,
                stdout="100755 abcdef 0\t.github/skills/example/scripts/run.sh\n",
                stderr="",
            )

        monkeypatch.setattr(gen.subprocess, "run", run)
        assert gen._git_executable_paths(root) == {  # pylint: disable=protected-access
            ".github/skills/example/scripts/run.sh"
        }
        assert len(calls) == 2


class TestCanonicalCaptureSecurity:
    def test_captured_text_is_lf_normalized_and_binary_resource_is_exact(
        self,
        tmp_path: Path,
    ) -> None:
        root = _make_fixture_repo(tmp_path)
        _install_fixture_registry(root)
        text_paths = (
            ".github/prompts/cg-test.prompt.md",
            ".github/agents/cg-test-agent.agent.md",
            ".github/skills/cg-skill-test/SKILL.md",
            ".github/instructions/python.instructions.md",
            ".github/shared/runtime-contract.md",
            gen.TARGET_MAPPING_PATH,
        )
        for relative_path in text_paths:
            path = root / relative_path
            content = path.read_bytes().replace(b"\r\n", b"\n")
            path.write_bytes(content.replace(b"\n", b"\r\n") + b"\r\n")
        binary = b"\x00\xff\r\n\xfeopaque\rbytes"
        binary_path = root / ".github/skills/cg-skill-test/assets/blob.bin"
        binary_path.parent.mkdir(parents=True)
        binary_path.write_bytes(binary)

        mapping, assets = gen.load_generation_inputs(root)
        plan = gen.build_generation_plan(root, mapping, assets)
        entries = plan.by_target["kilo"].entries

        for relative_path in text_paths:
            entry = next(item for item in entries if item.source == relative_path)
            assert b"\r" not in entry.content
            assert entry.sha256 == hashlib.sha256(entry.content).hexdigest()
        binary_entry = next(
            item for item in entries
            if item.source == ".github/skills/cg-skill-test/assets/blob.bin"
        )
        assert binary_entry.content == binary
        assert binary_entry.sha256 == hashlib.sha256(binary).hexdigest()

    @pytest.mark.parametrize(("case", "relative_path"), _CANONICAL_SECURITY_CASES)
    def test_leaf_replacement_after_capture_cannot_change_parsed_bytes(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        case: str,
        relative_path: str,
    ) -> None:
        root = _make_fixture_repo(tmp_path)
        _install_fixture_registry(root)
        target = root / relative_path
        marker = f"POST-CAPTURE-{case}"
        original = gen.secure_fs.secure_read_bytes
        swapped = False

        def capture_then_swap(read_root, read_relative, **kwargs):
            nonlocal swapped
            content = original(read_root, read_relative, **kwargs)
            if str(read_relative).replace("\\", "/") == relative_path and not swapped:
                target.write_text(marker, encoding="utf-8")
                swapped = True
            return content

        monkeypatch.setattr(gen.secure_fs, "secure_read_bytes", capture_then_swap)

        captured = _read_security_case(root, case)

        assert swapped is True
        assert marker not in captured

    @pytest.mark.parametrize(("case", "relative_path"), _CANONICAL_SECURITY_CASES)
    @pytest.mark.usefixtures("require_symlink_support")
    def test_leaf_link_swap_is_rejected_at_the_secure_read_boundary(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        case: str,
        relative_path: str,
    ) -> None:
        root = _make_fixture_repo(tmp_path)
        _install_fixture_registry(root)
        target = root / relative_path
        outside = _write(tmp_path / f"outside-{case}.txt", "outside bytes\n")
        original = gen.secure_fs.secure_read_bytes
        swapped = False

        def swap_then_read(read_root, read_relative, **kwargs):
            nonlocal swapped

            def swap(_path: Path) -> None:
                nonlocal swapped
                target.unlink()
                target.symlink_to(outside)
                swapped = True

            if str(read_relative).replace("\\", "/") == relative_path and not swapped:
                return original(
                    read_root,
                    read_relative,
                    before_open=swap,
                    **kwargs,
                )
            return original(read_root, read_relative, **kwargs)

        monkeypatch.setattr(gen.secure_fs, "secure_read_bytes", swap_then_read)

        with pytest.raises((OSError, ValueError), match="link|reparse|safe|regular"):
            _read_security_case(root, case)

        assert swapped is True

    @pytest.mark.backend_posix
    @pytest.mark.skipif(
        not gen.secure_fs.supports_secure_dir_fd(),
        reason="requires POSIX pinned no-follow directory handles",
    )
    @pytest.mark.parametrize(("case", "relative_path"), _CANONICAL_SECURITY_CASES)
    def test_ancestor_swap_reads_only_bytes_from_the_pinned_parent(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        case: str,
        relative_path: str,
    ) -> None:
        root = _make_fixture_repo(tmp_path)
        _install_fixture_registry(root)
        target = root / relative_path
        original_parent = target.parent
        moved_parent = original_parent.with_name(original_parent.name + "-captured")
        outside_parent = tmp_path / f"outside-{case}"
        outside_parent.mkdir()
        outside_marker = f"OUTSIDE-{case}"
        _write(outside_parent / target.name, outside_marker)
        original = gen.secure_fs.secure_read_bytes
        swapped = False

        def swap_then_read(read_root, read_relative, **kwargs):
            nonlocal swapped

            def swap(_path: Path) -> None:
                nonlocal swapped
                original_parent.rename(moved_parent)
                original_parent.symlink_to(outside_parent, target_is_directory=True)
                swapped = True

            if str(read_relative).replace("\\", "/") == relative_path and not swapped:
                return original(
                    read_root,
                    read_relative,
                    before_open=swap,
                    **kwargs,
                )
            return original(read_root, read_relative, **kwargs)

        monkeypatch.setattr(gen.secure_fs, "secure_read_bytes", swap_then_read)

        captured = _read_security_case(root, case)

        assert swapped is True
        assert outside_marker not in captured

    @pytest.mark.parametrize(("case", "relative_path"), _CANONICAL_SECURITY_CASES)
    def test_hard_link_is_rejected_before_parse_or_render(
        self,
        tmp_path: Path,
        case: str,
        relative_path: str,
    ) -> None:
        root = _make_fixture_repo(tmp_path)
        _install_fixture_registry(root)
        target = root / relative_path
        alias = tmp_path / f"hard-link-{case}"
        try:
            os.link(target, alias)
        except OSError as error:
            pytest.skip(f"host does not permit hard links: {error}")

        with pytest.raises((OSError, ValueError), match="multiple hard links"):
            _read_security_case(root, case)

    def test_generation_captures_each_asset_and_control_once(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        root = _make_fixture_repo(tmp_path)
        _install_fixture_registry(root)
        original_mapping = (root / gen.TARGET_MAPPING_PATH).read_bytes()
        original = gen.secure_fs.secure_read_bytes
        calls = Counter()

        def observe(read_root, relative_path, **kwargs):
            normalized = str(relative_path).replace("\\", "/")
            calls[normalized] += 1
            assert kwargs["reject_hardlinks"] is True
            assert 0 < kwargs["max_bytes"] <= gen.MAX_CANONICAL_CONTROL_BYTES
            return original(read_root, relative_path, **kwargs)

        monkeypatch.setattr(gen.secure_fs, "secure_read_bytes", observe)

        mapping, assets = gen.load_generation_inputs(root)
        plan = gen.build_generation_plan(root, mapping, assets)

        for _case, relative_path in _CANONICAL_SECURITY_CASES:
            assert calls[relative_path] == 1
        rendered_mapping = next(
            entry for entry in plan.by_target["kilo"].entries
            if entry.source == gen.TARGET_MAPPING_PATH
        )
        assert rendered_mapping.content == original_mapping


class TestDryRun:
    def test_dry_run_produces_no_files(self, tmp_path: Path) -> None:
        root = _make_fixture_repo(tmp_path)
        exit_code = gen.main(["--root", str(root), "--target", "claude-code", "--dry-run"])
        assert exit_code == 0
        assert not (root / ".claude").exists()

    def test_dry_run_reports_manifest(self, tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
        root = _make_fixture_repo(tmp_path)
        gen.main(["--root", str(root), "--target", "claude-code", "--dry-run"])
        captured = capsys.readouterr()
        assert "claude-code" in captured.out
        assert ".claude/commands" in captured.out

    def test_dry_run_all_targets(self, tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
        root = _make_fixture_repo(tmp_path)
        gen.main(["--root", str(root), "--all", "--dry-run"])
        captured = capsys.readouterr()
        assert "claude-code" in captured.out
        assert "codex" in captured.out
        assert "opencode" in captured.out


class TestGenerationPlan:
    def test_entries_are_sorted_and_contain_final_bytes_and_hashes(self, tmp_path: Path) -> None:
        root = _make_fixture_repo(tmp_path)
        mapping = gen.load_target_mapping(root)
        assets = gen.scan_canonical_assets(root)

        plan = gen.build_generation_plan(root, mapping, assets)

        destinations = [entry.destination for entry in plan.entries]
        assert destinations == sorted(destinations)
        assert all(isinstance(entry.content, bytes) for entry in plan.entries)
        assert all(entry.sha256 == hashlib.sha256(entry.content).hexdigest() for entry in plan.entries)
        assert all(isinstance(entry.executable, bool) for entry in plan.entries)

    def test_identical_inputs_produce_identical_structured_plan(self, tmp_path: Path) -> None:
        root = _make_fixture_repo(tmp_path)
        mapping = gen.load_target_mapping(root)
        assets = gen.scan_canonical_assets(root)

        first = gen.build_generation_plan(root, mapping, assets)
        second = gen.build_generation_plan(root, mapping, assets)

        assert first == second

    def test_plan_exposes_target_results_without_stdout_parsing(self, tmp_path: Path) -> None:
        root = _make_fixture_repo(tmp_path)
        plan = gen.build_generation_plan(
            root,
            gen.load_target_mapping(root),
            gen.scan_canonical_assets(root),
        )

        assert set(plan.by_target) == {"claude-code", "codex", "opencode", "kilo"}
        assert all(result.entries for result in plan.by_target.values())

    def test_all_outputs_render_before_first_write(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        root = _make_fixture_repo(tmp_path)
        mapping = gen.load_target_mapping(root)
        assets = gen.scan_canonical_assets(root)
        original = gen._render_output_entry  # pylint: disable=protected-access

        def fail_on_late_target(*args, **kwargs):
            target = args[0]
            if target["id"] == "opencode":
                raise ValueError("late render failure")
            return original(*args, **kwargs)

        monkeypatch.setattr(gen, "_render_output_entry", fail_on_late_target)

        with pytest.raises(ValueError, match="late render failure"):
            gen.build_generation_plan(root, mapping, assets)

        assert not (root / ".claude").exists()
        assert not (root / ".agents").exists()
        assert not (root / ".opencode").exists()
        assert not (root / ".kilo").exists()

    @pytest.mark.parametrize("target_id", ["claude-code", "codex", "opencode", "kilo"])
    def test_emit_plan_writes_exact_planned_bytes(self, tmp_path: Path, target_id: str) -> None:
        root = _make_fixture_repo(tmp_path)
        plan = gen.build_generation_plan(
            root,
            gen.load_target_mapping(root),
            gen.scan_canonical_assets(root),
        )

        result = gen.commit_generation_plan(root, plan, [target_id])

        assert result.target_ids == (target_id,)
        for entry in plan.by_target[target_id].entries:
            assert (root / entry.destination).read_bytes() == entry.content

    def test_generated_commit_commands_exactly_match_canonical_body(self) -> None:
        plan = gen.build_generation_plan(
            REPO_ROOT,
            gen.load_target_mapping(REPO_ROOT),
            gen.scan_canonical_assets(REPO_ROOT),
        )
        planned_entries = {entry.destination: entry for entry in plan.entries}
        canonical_body = _generated_command_body(
            (REPO_ROOT / ".github/prompts/cg-commit-push-pr.prompt.md").read_bytes()
        )
        forbidden_adapter_mappings = (
            ".claude/shared/target-mapping.json",
            ".agents/shared/target-mapping.json",
            ".opencode/shared/target-mapping.json",
            ".kilo/shared/target-mapping.json",
        )

        assert set(plan.by_target) == EXPECTED_PLAN_TARGETS
        for target_id, command_path in COMMIT_PUSH_COMMAND_PATHS.items():
            body = _generated_command_body(planned_entries[command_path].content)
            expected_argument_blocks = int(target_id in ARGUMENT_BLOCK_SUFFIXES)
            assert body.count(b"$ARGUMENTS") == expected_argument_blocks, target_id
            if expected_argument_blocks:
                suffix = ARGUMENT_BLOCK_SUFFIXES[target_id]
                assert body.endswith(suffix), target_id
                body = body[:-len(suffix)]
            assert body == canonical_body, target_id

            command = body.decode("utf-8")
            assert SOURCE_MARKER in command, target_id
            assert '`".github"`, `"shared"`, and `"target-mapping.json"`' in command, target_id
            assert "Set `$isCompoundGpidSource` exactly once" in command, target_id
            assert "never recompute" in command, target_id
            for adapter_mapping in forbidden_adapter_mappings:
                assert adapter_mapping not in command, (target_id, adapter_mapping)

    def test_source_marker_is_absent_from_generation_plan_and_install_units(self) -> None:
        mapping = gen.load_target_mapping(REPO_ROOT)
        plan = gen.build_generation_plan(
            REPO_ROOT,
            mapping,
            gen.scan_canonical_assets(REPO_ROOT),
        )

        assert all(SOURCE_MARKER not in entry.destination for entry in plan.entries)
        assert all(SOURCE_MARKER not in entry.source for entry in plan.entries)
        for target in mapping["targets"]:
            for unit in target["installUnits"]:
                assert SOURCE_MARKER not in unit["source"], target["id"]
                assert SOURCE_MARKER not in unit["target"], target["id"]

    @pytest.mark.parametrize(
        ("path", "expected"),
        [
            ("SKILL.md", True),
            ("references/GUIDE.MARKDOWN", True),
            ("resources/config.json", False),
            ("resources/opaque.bin", False),
        ],
    )
    def test_markdown_normalization_path_contract(
        self, path: str, expected: bool
    ) -> None:
        assert gen.bundle_service.is_normalized_markdown_path(path) is expected

    def test_bundle_normalization_preserves_opaque_crlf_bytes(self) -> None:
        markdown = gen.bundle_service.BundleFile(
            "skill/guide.md",
            "guide.md",
            b"first\r\nsecond\r\n",
            "a" * 64,
            False,
        )
        opaque = gen.bundle_service.BundleFile(
            "skill/opaque.bin",
            "opaque.bin",
            b"first\r\nsecond\r\n",
            "b" * 64,
            False,
        )

        assert gen.bundle_service.normalized_content(markdown) == b"first\nsecond\n"
        assert gen.bundle_service.normalized_content(opaque) == opaque.content

    def test_release_parity_accepts_only_copilot_self_projection_crlf(
        self, tmp_path: Path
    ) -> None:
        def planned(target: str, destination: str, source: str) -> gen.OutputEntry:
            return gen.OutputEntry(
                target_id=target,
                destination=destination,
                source=source,
                kind="skill-resource",
                content=b"first\nsecond\n",
                sha256="a" * 64,
                executable=False,
            )

        markdown_path = ".github/skills/example/references/guide.md"
        markdown = planned("copilot", markdown_path, markdown_path)
        opaque_path = ".github/skills/example/resources/opaque.bin"
        opaque = planned("copilot", opaque_path, opaque_path)
        relocated = planned(
            "copilot",
            ".github/skills/copy/references/guide.md",
            markdown_path,
        )
        generated = planned(
            "codex",
            ".agents/skills/example/references/guide.md",
            markdown_path,
        )
        entries = (markdown, opaque, relocated, generated)
        copilot_destinations = {
            markdown.destination,
            opaque.destination,
            relocated.destination,
        }
        for entry in entries:
            output = tmp_path / entry.destination
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_bytes(b"first\r\nsecond\r\n")

        assert (tmp_path / markdown.destination).read_bytes() != markdown.content
        assert _worktree_output_mismatches(
            tmp_path, entries, copilot_destinations
        ) == [
            f"content:{opaque.destination}",
            f"content:{relocated.destination}",
            f"content:{generated.destination}",
        ]
        assert not _worktree_output_matches(
            markdown, b"first\r\nsecond\n", copilot_destinations
        )
        assert not _worktree_output_matches(
            markdown, b"first\rsecond\r", copilot_destinations
        )

    def test_real_repository_working_tree_matches_current_plan(self) -> None:
        plan = gen.build_generation_plan(
            REPO_ROOT,
            gen.load_target_mapping(REPO_ROOT),
            gen.scan_canonical_assets(REPO_ROOT),
        )
        planned_entries = {entry.destination: entry for entry in plan.entries}
        copilot_destinations = {
            entry.destination for entry in plan.by_target["copilot"].entries
        }
        assert set(plan.by_target) == EXPECTED_PLAN_TARGETS

        expected_manifest_bytes = {}
        expected_manifest_paths = {}
        for target_id in RENAMED_COMMAND_PATHS:
            result = plan.by_target[target_id]
            manifest_path = f"{result.target_root}/{gen.OWNERSHIP_MANIFEST_NAME}"
            manifest_bytes = gen._ownership_manifest_bytes(  # pylint: disable=protected-access
                result
            )
            manifest = json.loads(manifest_bytes.decode("utf-8"))
            expected_manifest_bytes[target_id] = (manifest_path, manifest_bytes)
            expected_manifest_paths[target_id] = {
                item["path"] for item in manifest["files"]
            }

        normalized_bodies = {}
        for target_id, new_path in RENAMED_COMMAND_PATHS.items():
            old_path = OLD_COMMAND_PATHS[target_id]
            assert new_path in planned_entries, new_path
            assert old_path not in planned_entries, old_path
            assert new_path in expected_manifest_paths[target_id], new_path
            assert old_path not in expected_manifest_paths[target_id], old_path

            command_entry = planned_entries[new_path]
            assert command_entry.kind == "command", new_path
            body = _generated_command_body(command_entry.content)
            expected_argument_blocks = int(target_id in ARGUMENT_BLOCK_SUFFIXES)
            assert body.count(b"$ARGUMENTS") == expected_argument_blocks, target_id
            if expected_argument_blocks:
                suffix = ARGUMENT_BLOCK_SUFFIXES[target_id]
                assert body.endswith(suffix), target_id
                body = body[:-len(suffix)]
            body = body.replace(
                new_path.encode("utf-8"),
                b".github/prompts/cg-compound-gpid-rd.prompt.md",
            )
            normalized_bodies[target_id] = body

        assert len(set(normalized_bodies.values())) == 1
        canonical_body = _generated_command_body(
            (REPO_ROOT / ".github/prompts/cg-compound-gpid-rd.prompt.md").read_bytes()
        )
        assert all(body == canonical_body for body in normalized_bodies.values())

        output_mismatches = _worktree_output_mismatches(
            REPO_ROOT, plan.entries, copilot_destinations
        )

        manifest_mismatches = []
        disk_manifest_paths = {}
        malformed_manifests = []
        for target_id, (manifest_path, expected_bytes) in expected_manifest_bytes.items():
            disk_path = REPO_ROOT / manifest_path
            if not disk_path.is_file():
                manifest_mismatches.append(f"missing:{manifest_path}")
                disk_manifest_paths[target_id] = set()
                continue

            disk_bytes = disk_path.read_bytes()
            if disk_bytes != expected_bytes:
                manifest_mismatches.append(f"content:{manifest_path}")
            try:
                disk_manifest = json.loads(disk_bytes.decode("utf-8"))
                disk_manifest_paths[target_id] = {
                    item["path"] for item in disk_manifest["files"]
                }
            except (KeyError, TypeError, UnicodeDecodeError, json.JSONDecodeError) as exc:
                malformed_manifests.append(f"{manifest_path}:{exc}")
                disk_manifest_paths[target_id] = set()

        missing_new_disk_paths = sorted(
            path for path in RENAMED_COMMAND_PATHS.values()
            if not (REPO_ROOT / path).is_file()
        )
        present_old_disk_paths = sorted(
            path for path in OLD_COMMAND_PATHS.values()
            if (REPO_ROOT / path).exists()
        )
        missing_new_manifest_paths = sorted(
            path for target_id, path in RENAMED_COMMAND_PATHS.items()
            if path not in disk_manifest_paths[target_id]
        )
        present_old_manifest_paths = sorted(
            path for target_id, path in OLD_COMMAND_PATHS.items()
            if path in disk_manifest_paths[target_id]
        )

        drift = []
        if output_mismatches:
            drift.append(
                f"planned output byte mismatches ({len(output_mismatches)}): "
                f"{output_mismatches}"
            )
        if manifest_mismatches:
            drift.append(
                f"ownership manifest byte mismatches ({len(manifest_mismatches)}): "
                f"{manifest_mismatches}"
            )
        if malformed_manifests:
            drift.append(f"malformed ownership manifests: {malformed_manifests}")
        if missing_new_disk_paths:
            drift.append(f"new command paths missing from disk: {missing_new_disk_paths}")
        if present_old_disk_paths:
            drift.append(f"old command paths still on disk: {present_old_disk_paths}")
        if missing_new_manifest_paths:
            drift.append(
                "new command paths missing from disk manifests: "
                f"{missing_new_manifest_paths}"
            )
        if present_old_manifest_paths:
            drift.append(
                "old command paths still in disk manifests: "
                f"{present_old_manifest_paths}"
            )

        assert not drift, (
            "Current generated working tree does not match the current generator plan.\n"
            "Run: python scripts/cg_generate_targets.py --all\n- "
            + "\n- ".join(drift)
        )


class TestMetadataSerialization:
    def test_generated_toml_parses_adversarial_valid_metadata(self, tmp_path: Path) -> None:
        tomllib = pytest.importorskip("tomllib")
        root = _make_fixture_repo(tmp_path)
        _write(
            root / ".github/agents/cg-tricky.agent.md",
            '---\ndescription: A "quoted" path \\ value\ntools: ["read", "odd/tool"]\n---\n\n# Tricky\n\nBody.\n',
        )

        assert gen.main(["--root", str(root), "--target", "codex"]) == 0

        parsed = tomllib.loads((root / ".agents/subagents/cg-tricky.toml").read_text(encoding="utf-8"))
        assert parsed["subagent"][0]["description"] == 'A "quoted" path \\ value'
        assert parsed["subagent"][0]["tools"] == ["read", "odd/tool"]

    def test_generated_frontmatter_quotes_scalar_values(self, tmp_path: Path) -> None:
        root = _make_fixture_repo(tmp_path)
        _write(
            root / ".github/prompts/cg-tricky.prompt.md",
            '---\ndescription: "value: #quoted"\n---\n\n# Tricky\n',
        )

        assert gen.main(["--root", str(root), "--target", "claude-code"]) == 0

        content = (root / ".claude/commands/cg-tricky.md").read_text(encoding="utf-8")
        description_line = next(
            line for line in content.splitlines() if line.startswith("description: ")
        )
        assert json.loads(description_line.split(": ", 1)[1]) == "value: #quoted"


class TestGeneratorWrites:
    def test_claude_code_writes_commands(self, tmp_path: Path) -> None:
        root = _make_fixture_repo(tmp_path)
        gen.main(["--root", str(root), "--target", "claude-code"])
        cmd_files = list((root / ".claude/commands").glob("*.md"))
        assert len(cmd_files) == 2

    def test_claude_code_writes_agents(self, tmp_path: Path) -> None:
        root = _make_fixture_repo(tmp_path)
        gen.main(["--root", str(root), "--target", "claude-code"])
        agent_files = list((root / ".claude/agents").glob("*.md"))
        assert len(agent_files) == 1

    def test_codex_writes_toml_subagents(self, tmp_path: Path) -> None:
        root = _make_fixture_repo(tmp_path)
        gen.main(["--root", str(root), "--target", "codex"])
        toml_files = list((root / ".agents/subagents").glob("*.toml"))
        assert len(toml_files) == 1
        tomllib = pytest.importorskip("tomllib")
        parsed = tomllib.loads(toml_files[0].read_text(encoding="utf-8"))
        agent = parsed["subagent"][0]
        assert agent["name"] == "cg-test-agent"
        assert agent["description"] == "Test agent"
        assert "model" not in agent
        assert agent["tools"] == ["read", "write"]
        assert "instructions" in agent

    def test_codex_writes_fallback_skills(self, tmp_path: Path) -> None:
        root = _make_fixture_repo(tmp_path)
        gen.main(["--root", str(root), "--target", "codex"])
        fallback_files = list((root / ".agents/skills").glob("*.md"))
        assert len(fallback_files) == 1

    def test_opencode_writes_config(self, tmp_path: Path) -> None:
        root = _make_fixture_repo(tmp_path)
        gen.main(["--root", str(root), "--target", "opencode"])
        data = json.loads((root / ".opencode/opencode.json").read_text())
        assert data == {
            "$schema": "https://opencode.ai/config.json",
            "instructions": [".opencode/AGENTS.md"],
            "skills": {"paths": [".opencode/skills"]},
        }

    def test_opencode_commands_use_valid_frontmatter_and_arguments(self, tmp_path: Path) -> None:
        root = _make_fixture_repo(tmp_path)
        gen.main(["--root", str(root), "--target", "opencode"])
        content = (root / ".opencode/commands/cg-test.md").read_text()
        assert 'description: "Test prompt"' in content
        assert "role:" not in content.split("---", 2)[1]
        assert "$ARGUMENTS" in content

    def test_escaped_canonical_description_is_not_double_escaped(self, tmp_path: Path) -> None:
        root = _make_fixture_repo(tmp_path)
        _write(
            root / ".github/prompts/cg-test.prompt.md",
            '---\ndescription: "A \\"quoted\\" prompt"\n---\n\n# Test\n',
        )
        gen.main(["--root", str(root), "--target", "opencode"])
        content = (root / ".opencode/commands/cg-test.md").read_text(encoding="utf-8")
        description_line = next(line for line in content.splitlines() if line.startswith("description:"))
        assert json.loads(description_line.partition(":")[2].strip()) == 'A "quoted" prompt'

    def test_opencode_uses_role_only_no_exact_models(self, tmp_path: Path) -> None:
        root = _make_fixture_repo(tmp_path)
        gen.main(["--root", str(root), "--target", "opencode"])
        agent_files = list((root / ".opencode/agents").glob("*.md"))
        assert len(agent_files) == 1
        content = agent_files[0].read_text()
        assert "mode: subagent" in content
        assert "role:" not in content.split("---", 2)[1]
        assert "GPT-5" not in content

    def test_kilo_writes_config(self, tmp_path: Path) -> None:
        root = _make_fixture_repo(tmp_path)
        gen.main(["--root", str(root), "--target", "kilo"])
        data = json.loads((root / ".kilo/kilo.json").read_text())
        assert data == {
            "$schema": "https://app.kilo.ai/config.json",
            "instructions": [".kilo/AGENTS.md"],
            "skills": {"paths": [".kilo/skills"]},
            "watcher": {"ignore": [".compound-gpid/kilo-compat-skills/**"]},
        }

    def test_kilo_commands_use_valid_frontmatter_and_arguments(self, tmp_path: Path) -> None:
        root = _make_fixture_repo(tmp_path)
        gen.main(["--root", str(root), "--target", "kilo"])
        content = (root / ".kilo/commands/cg-test.md").read_text()
        assert 'description: "Test prompt"' in content
        assert "role:" not in content.split("---", 2)[1]
        assert "$ARGUMENTS" in content

    def test_kilo_uses_role_only_no_exact_models(self, tmp_path: Path) -> None:
        root = _make_fixture_repo(tmp_path)
        gen.main(["--root", str(root), "--target", "kilo"])
        agent_files = list((root / ".kilo/agents").glob("*.md"))
        assert len(agent_files) == 1
        content = agent_files[0].read_text()
        assert "mode: subagent" in content
        assert "role:" not in content.split("---", 2)[1]
        assert "GPT-5" not in content

    def test_generator_does_not_modify_github(self, tmp_path: Path) -> None:
        root = _make_fixture_repo(tmp_path)
        prompt_before = (root / ".github/prompts/cg-test.prompt.md").read_text()
        gen.main(["--root", str(root), "--all"])
        prompt_after = (root / ".github/prompts/cg-test.prompt.md").read_text()
        assert prompt_before == prompt_after

    def test_all_targets_write(self, tmp_path: Path) -> None:
        root = _make_fixture_repo(tmp_path)
        gen.main(["--root", str(root), "--all"])
        assert (root / ".claude").exists()
        assert (root / ".agents").exists()
        assert (root / ".opencode").exists()
        assert (root / ".kilo").exists()

    def test_copilot_target_produces_no_output(self, tmp_path: Path) -> None:
        """Copilot target has generatedTreePath: null and must produce no files."""
        root = _make_fixture_repo(tmp_path)
        exit_code = gen.main(["--root", str(root), "--target", "copilot"])
        assert exit_code == 0
        assert not (root / ".claude").exists()
        assert not (root / ".agents").exists()
        assert not (root / ".opencode").exists()

    def test_invalid_target_errors(self, tmp_path: Path) -> None:
        root = _make_fixture_repo(tmp_path)
        exit_code = gen.main(["--root", str(root), "--target", "nonexistent"])
        assert exit_code == 1

    def test_missing_target_mapping_errors(self, tmp_path: Path) -> None:
        root = tmp_path / "no-mapping"
        root.mkdir()
        exit_code = gen.main(["--root", str(root), "--target", "claude-code"])
        assert exit_code == 1

    def test_model_mapping_artifact_is_not_written(self, tmp_path: Path) -> None:
        root = _make_fixture_repo(tmp_path)
        gen.main(["--root", str(root), "--target", "claude-code"])
        assert not (root / ".claude/model-mapping.claude.json").exists()

    def test_root_adapter_written(self, tmp_path: Path) -> None:
        root = _make_fixture_repo(tmp_path)
        gen.main(["--root", str(root), "--target", "claude-code"])
        assert (root / ".claude/CLAUDE.md").exists()


class TestEdgeCases:
    """Edge case tests for graceful handling of missing/malformed data (P2.4)."""

    def test_prompt_with_no_frontmatter(self, tmp_path: Path) -> None:
        """A prompt file with no frontmatter at all should not crash the generator."""
        root = _make_fixture_repo(tmp_path)
        _write(root / ".github/prompts/cg-no-fm.prompt.md", "# No Frontmatter\n\nJust body text.\n")
        exit_code = gen.main(["--root", str(root), "--target", "claude-code"])
        assert exit_code == 0

    def test_agent_with_no_tools_field(self, tmp_path: Path) -> None:
        """An agent without a tools: field should generate a TOML with empty tools list."""
        root = _make_fixture_repo(tmp_path)
        _write(root / ".github/agents/cg-no-tools.agent.md",
               "---\ndescription: Agent without tools\n---\n\n# Agent\n\nBody.\n")
        exit_code = gen.main(["--root", str(root), "--target", "codex"])
        assert exit_code == 0
        toml = (root / ".agents/subagents/cg-no-tools.toml").read_text()
        assert "tools = []" in toml

    def test_generation_without_execution_catalog(self, tmp_path: Path) -> None:
        """Generation does not require an execution model catalog."""
        root = _make_fixture_repo(tmp_path)
        exit_code = gen.main(["--root", str(root), "--target", "claude-code"])
        assert exit_code == 0

    def test_skill_with_no_frontmatter(self, tmp_path: Path) -> None:
        """A skill with no frontmatter should still be copied as a skill body."""
        root = _make_fixture_repo(tmp_path)
        _write(root / ".github/skills/cg-skill-nofm/SKILL.md", "# Skill without frontmatter\n\nBody.\n")
        exit_code = gen.main(["--root", str(root), "--target", "claude-code"])
        assert exit_code == 0
        assert (root / ".claude/skills/cg-skill-nofm/SKILL.md").exists()

    def test_empty_github_directory(self, tmp_path: Path) -> None:
        """An empty canonical tree must fail before generation."""
        root = tmp_path / "empty"
        (root / ".github/prompts").mkdir(parents=True)
        (root / ".github/agents").mkdir(parents=True)
        (root / ".github/skills").mkdir(parents=True)
        (root / ".github/shared").mkdir(parents=True)
        _write(root / ".github/shared/target-mapping.json", json.dumps({
            "schemaVersion": 1,
            "description": "Empty",
            "targets": [{
                "id": "claude-code", "name": "Claude Code", "generatedTreePath": ".claude",
                "capabilities": {f: True for f in gen.REQUIRED_CAPABILITY_FIELDS},
                "formats": {"commandFormat": "c", "skillFormat": "s", "agentFormat": "a"},
                "outputPaths": {"commands": ".claude/commands", "skills": ".claude/skills", "agents": ".claude/agents", "instructions": ".claude/instructions", "shared": ".claude/shared", "rootAdapter": ".claude/CLAUDE.md"},
            }],
        }))
        exit_code = gen.main(["--root", str(root), "--target", "claude-code"])
        assert exit_code == 1
        assert not (root / ".claude").exists()


class TestNamespaceAgnosticSkills:
    """Namespace-agnostic skill discovery (R3): registry-driven, with fallback."""

    def _registry(self, root: Path, skill_owners: dict) -> None:
        """Write a minimal module registry owning the given skill dir names."""
        modules = [
            {
                "id": "kernel",
                "layer": "kernel",
                "displayName": "Kernel",
                "description": "kernel",
                "dependsOn": [],
                "ownedAssets": [".github/shared/*.contract.md"],
            }
        ]
        for name in skill_owners:
            modules.append({
                "id": skill_owners[name],
                "layer": "capability" if "--" not in name else "suite",
                "displayName": name,
                "description": name,
                "dependsOn": ["kernel"],
                "ownedAssets": [f".github/skills/{name}/"],
            })
        _write(root / ".github/shared/module-registry.json", json.dumps({
            "schemaVersion": 1,
            "description": "test",
            "modules": modules,
        }, indent=2))

    def test_discovery_includes_cr_skill_when_registered(self, tmp_path: Path) -> None:
        root = _make_fixture_repo(tmp_path)
        _write(root / ".github/skills/cr-skill-identification/SKILL.md",
               "---\ndescription: cr skill\n---\n\n# CR Skill\n\nBody.\n")
        self._registry(root, {"cg-skill-test": "cap-test", "cr-skill-identification": "suite-cr"})
        assets = gen.scan_canonical_assets(root)
        names = {Path(a["relative_path"]).parent.name for a in assets["skills"]}
        assert names == {"cg-skill-test", "cr-skill-identification"}

    def test_discovery_rejects_unregistered_skill_dir(self, tmp_path: Path) -> None:
        root = _make_fixture_repo(tmp_path)
        _write(root / ".github/skills/cr-skill-unowned/SKILL.md",
               "---\ndescription: unowned\n---\n\nBody.\n")
        self._registry(root, {"cg-skill-test": "cap-test"})
        with pytest.raises(ValueError, match="unowned|ownership"):
            gen.scan_canonical_assets(root)

    def test_fallback_without_registry_keeps_cg_skill_glob(self, tmp_path: Path, capsys) -> None:
        root = _make_fixture_repo(tmp_path)
        _write(root / ".github/skills/cr-skill-ignored/SKILL.md",
               "---\ndescription: ignored\n---\n\nBody.\n")
        assert not (root / ".github/shared/module-registry.json").exists()
        assets = gen.scan_canonical_assets(root)
        names = {Path(a["relative_path"]).parent.name for a in assets["skills"]}
        assert names == {"cg-skill-test"}
        captured = capsys.readouterr()
        assert "falling back to cg-skill-*" in captured.err

    def test_cr_skill_emitted_to_all_platform_trees(self, tmp_path: Path) -> None:
        root = _make_fixture_repo(tmp_path)
        _write(root / ".github/skills/cr-skill-identification/SKILL.md",
               "---\ndescription: cr skill\n---\n\n# CR Skill\n\nBody.\n")
        self._registry(root, {"cg-skill-test": "cap-test", "cr-skill-identification": "suite-cr"})
        assert gen.main(["--root", str(root), "--all"]) == 0
        for tree in (".claude/skills", ".agents/skills", ".opencode/skills", ".kilo/skills"):
            assert (root / tree / "cr-skill-identification" / "SKILL.md").exists(), tree


class TestContextBudgetFailFast:
    """--active-suites must fail loudly on misconfiguration (P2) instead of
    silently generating an unfiltered or empty tree."""

    def _registry(self, root: Path) -> None:
        _write(root / ".github/shared/module-registry.json", json.dumps({
            "schemaVersion": 1,
            "description": "test",
            "modules": [
                {
                    "id": "kernel",
                    "layer": "kernel",
                    "displayName": "Kernel",
                    "description": "k",
                    "dependsOn": [],
                    "ownedAssets": [".github/shared/*.contract.md", ".github/prompts/cg-*.prompt.md"],
                },
                {
                    "id": "suite-cg",
                    "layer": "suite",
                    "displayName": "CG",
                    "description": "cg",
                    "dependsOn": ["kernel"],
                    "ownedAssets": [".github/prompts/cg-*.prompt.md", ".github/agents/cg-*.agent.md", ".github/skills/cg-skill-r-*/", ".github/instructions/r.instructions.md"],
                },
            ],
        }))

    def test_unknown_suite_fails_and_writes_nothing(self, tmp_path: Path, capsys) -> None:
        root = _make_fixture_repo(tmp_path)
        self._registry(root)
        exit_code = gen.main(["--root", str(root), "--all", "--active-suites", "cgx"])
        assert exit_code == 1
        captured = capsys.readouterr()
        assert "unknown active suite" in captured.err
        assert not (root / ".claude").exists()
        assert not (root / ".kilo").exists()

    def test_missing_registry_with_active_suites_fails(self, tmp_path: Path, capsys) -> None:
        root = _make_fixture_repo(tmp_path)
        assert not (root / ".github/shared/module-registry.json").exists()
        exit_code = gen.main(["--root", str(root), "--all", "--active-suites", "cg"])
        assert exit_code == 1
        captured = capsys.readouterr()
        assert "requires module-registry.json" in captured.err
        assert not (root / ".claude").exists()


class TestOwnershipManifest:
    """Tests for ownership manifest commit/write path (P2.3)."""

    def _make_entry(self, destination: str, sha256: str = "a" * 64) -> gen.OutputEntry:
        return gen.OutputEntry(
            target_id="claude-code", destination=destination, source="src.md",
            kind="command", content=b"", sha256=sha256, executable=False,
        )

    def _make_result(self, entries: tuple[gen.OutputEntry, ...]) -> gen.TargetResult:
        return gen.TargetResult(target_id="claude-code", target_root=".claude", entries=entries)

    def test_ownership_manifest_bytes_structure(self) -> None:
        """_ownership_manifest_bytes produces deterministic JSON with correct fields."""
        entries = (
            self._make_entry(".claude/commands/cg-test.md"),
            self._make_entry(".claude/agents/cg-agent.md"),
        )
        result = self._make_result(entries)
        manifest = gen._ownership_manifest_bytes(result)  # pylint: disable=protected-access
        data = json.loads(manifest.decode("utf-8"))
        assert data["schemaVersion"] == 1
        assert data["target"] == "claude-code"
        assert data["policyVersion"] == gen.OWNERSHIP_POLICY_VERSION
        assert len(data["files"]) == 2
        assert data["files"][0]["path"] == ".claude/commands/cg-test.md"
        assert data["files"][0]["sha256"] == "a" * 64
        assert manifest.endswith(b"\n")

    def test_ownership_manifest_bytes_deterministic(self) -> None:
        """Two calls with the same data produce identical bytes."""
        entries = (self._make_entry(".claude/commands/cg-test.md"),)
        result = self._make_result(entries)
        assert gen._ownership_manifest_bytes(  # pylint: disable=protected-access
            result
        ) == gen._ownership_manifest_bytes(result)  # pylint: disable=protected-access

    def test_read_prior_manifest_returns_empty_when_missing(self, tmp_path: Path) -> None:
        """_read_prior_ownership_manifest returns {} when no manifest exists."""
        entries = (self._make_entry(".claude/commands/cg-test.md"),)
        result = self._make_result(entries)
        root = tmp_path / "fixture"
        assert gen._read_prior_ownership_manifest(  # pylint: disable=protected-access
            root, result
        ) == {}

    def test_read_prior_manifest_parses_valid(self, tmp_path: Path) -> None:
        """_read_prior_ownership_manifest correctly parses a valid manifest."""
        root = tmp_path / "fixture"
        (root / ".claude").mkdir(parents=True)
        entries = (self._make_entry(".claude/commands/cg-test.md", "b" * 64),)
        result = self._make_result(entries)
        manifest_data = {
            "schemaVersion": 1, "target": "claude-code", "policyVersion": 1,
            "files": [{"path": ".claude/commands/cg-test.md", "source": "src.md", "kind": "command",
                       "sha256": "b" * 64, "executable": False}],
        }
        (root / ".claude/.compound-gpid-generated.json").write_text(
            json.dumps(manifest_data), encoding="utf-8"
        )
        owned = gen._read_prior_ownership_manifest(  # pylint: disable=protected-access
            root, result
        )
        assert owned[".claude/commands/cg-test.md"].sha256 == "b" * 64

    def test_read_prior_manifest_uses_bounded_secure_reader(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        root = tmp_path / "fixture"
        (root / ".claude").mkdir(parents=True)
        result = self._make_result(())
        manifest_data = {
            "schemaVersion": 1,
            "target": "claude-code",
            "policyVersion": 1,
            "files": [],
        }
        (root / ".claude/.compound-gpid-generated.json").write_text(
            json.dumps(manifest_data),
            encoding="utf-8",
        )
        observed = {}
        original_read = gen.secure_fs.secure_read_bytes

        def observe(root_path, relative_path, **kwargs):
            observed.update(kwargs)
            return original_read(root_path, relative_path, **kwargs)

        monkeypatch.setattr(gen.secure_fs, "secure_read_bytes", observe)

        gen._read_prior_ownership_manifest(root, result)  # pylint: disable=protected-access

        assert observed["reject_hardlinks"] is True
        assert observed["max_bytes"] > 0

    @pytest.mark.usefixtures("require_symlink_support")
    def test_manifest_final_component_swap_fails_closed(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        root = tmp_path / "fixture"
        (root / ".claude").mkdir(parents=True)
        result = self._make_result(())
        manifest = root / ".claude/.compound-gpid-generated.json"
        manifest.write_bytes(
            gen._ownership_manifest_bytes(result)  # pylint: disable=protected-access
        )
        outside = tmp_path / "outside.json"
        outside.write_text(
            '{"schemaVersion":1,"target":"claude-code","policyVersion":1,"files":[]}',
            encoding="utf-8",
        )
        original_read = gen.secure_fs.secure_read_bytes

        def swap_then_read(root_path, relative_path, **kwargs):
            def swap(_path: Path) -> None:
                manifest.unlink()
                manifest.symlink_to(outside)

            return original_read(root_path, relative_path, before_open=swap, **kwargs)

        monkeypatch.setattr(gen.secure_fs, "secure_read_bytes", swap_then_read)

        with pytest.raises(ValueError, match="unsafe"):
            gen._read_prior_ownership_manifest(root, result)  # pylint: disable=protected-access

    def test_read_prior_manifest_rejects_missing_keys(self, tmp_path: Path) -> None:
        """_read_prior_ownership_manifest rejects manifest with missing schema keys."""
        root = tmp_path / "fixture"
        (root / ".claude").mkdir(parents=True)
        entries = (self._make_entry(".claude/commands/cg-test.md"),)
        result = self._make_result(entries)
        (root / ".claude/.compound-gpid-generated.json").write_text(
            json.dumps({"schemaVersion": 1, "target": "claude-code"}), encoding="utf-8"
        )
        with pytest.raises(ValueError, match="invalid schema"):
            gen._read_prior_ownership_manifest(  # pylint: disable=protected-access
                root, result
            )

    def test_read_prior_manifest_rejects_wrong_target(self, tmp_path: Path) -> None:
        """_read_prior_ownership_manifest rejects manifest for a different target."""
        root = tmp_path / "fixture"
        (root / ".claude").mkdir(parents=True)
        entries = (self._make_entry(".claude/commands/cg-test.md"),)
        result = self._make_result(entries)
        data = {"schemaVersion": 1, "target": "codex", "policyVersion": 1, "files": []}
        (root / ".claude/.compound-gpid-generated.json").write_text(
            json.dumps(data), encoding="utf-8"
        )
        with pytest.raises(ValueError, match="target does not match"):
            gen._read_prior_ownership_manifest(  # pylint: disable=protected-access
                root, result
            )

    def test_read_prior_manifest_rejects_python_cache_path(self, tmp_path: Path) -> None:
        root = tmp_path / "fixture"
        (root / ".claude").mkdir(parents=True)
        result = self._make_result(())
        manifest = {
            "schemaVersion": 1,
            "target": "claude-code",
            "policyVersion": 1,
            "files": [{
                "path": ".claude/skills/cg-skill-test/__pycache__/module.pyc",
                "source": ".github/skills/cg-skill-test/__pycache__/module.pyc",
                "kind": "skill-resource",
                "sha256": "a" * 64,
                "executable": False,
            }],
        }
        (root / ".claude/.compound-gpid-generated.json").write_text(
            json.dumps(manifest), encoding="utf-8"
        )

        with pytest.raises(ValueError, match=r"cache|\.pyc"):
            gen._read_prior_ownership_manifest(  # pylint: disable=protected-access
                root, result
            )

    def test_preflight_target_commit_detects_stale_file_modification(self, tmp_path: Path) -> None:
        """_preflight_target_commit raises on modified stale owned file."""
        root = tmp_path / "fixture"
        (root / ".claude/commands").mkdir(parents=True)
        stale_path = root / ".claude/commands/stale.md"
        stale_path.write_text("original content")
        stale_hash = hashlib.sha256(stale_path.read_bytes()).hexdigest()
        stale_path.write_text("modified content")

        # Write the expected entry
        dest_path = root / ".claude/commands/cg-test.md"
        dest_path.write_text("expected")
        content_hash = hashlib.sha256(dest_path.read_bytes()).hexdigest()

        entries = (self._make_entry(".claude/commands/cg-test.md", content_hash),)
        result = self._make_result(entries)
        prior_data = {
            "schemaVersion": 1, "target": "claude-code", "policyVersion": 1,
            "files": [{"path": ".claude/commands/stale.md", "source": "old.md",
                       "kind": "command", "sha256": stale_hash, "executable": False}],
        }
        (root / ".claude/.compound-gpid-generated.json").write_text(
            json.dumps(prior_data), encoding="utf-8"
        )
        with pytest.raises(ValueError, match="Modified stale"):
            gen._preflight_target_commit(root, result)  # pylint: disable=protected-access

    def test_preflight_target_commit_accepts_unmodified_stale(self, tmp_path: Path) -> None:
        """_preflight_target_commit accepts stale file with matching hash."""
        root = tmp_path / "fixture"
        (root / ".claude/commands").mkdir(parents=True)
        stale_path = root / ".claude/commands/stale.md"
        stale_path.write_text("stale content")
        stale_hash = hashlib.sha256(stale_path.read_bytes()).hexdigest()

        # Write the expected entry and compute its proper hash
        dest_path = root / ".claude/commands/cg-test.md"
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        dest_path.write_text("test")
        content_hash = hashlib.sha256(dest_path.read_bytes()).hexdigest()

        entry = self._make_entry(".claude/commands/cg-test.md", content_hash)
        entries = (entry,)
        result = self._make_result(entries)
        prior_data = {
            "schemaVersion": 1, "target": "claude-code", "policyVersion": 1,
            "files": [{"path": ".claude/commands/stale.md", "source": "old.md",
                       "kind": "command", "sha256": stale_hash, "executable": False}],
        }
        (root / ".claude/.compound-gpid-generated.json").write_text(
            json.dumps(prior_data), encoding="utf-8"
        )
        plan = gen._preflight_target_commit(  # pylint: disable=protected-access
            root, result
        )
        assert isinstance(plan, gen.TargetCommitPlan)

    def test_pathname_parent_pruning_helper_is_absent(self) -> None:
        """Generated cleanup must not mutate parent directories by pathname."""
        assert not hasattr(gen, "_prune_empty_parents")  # pylint: disable=protected-access


class TestHelperFunctions:
    """Parametrized unit tests for YAML scalar, fenced-code, and reference helpers."""

    @pytest.mark.parametrize("value,expected", [
        ("simple", "simple"),
        ("path/to/file", "path/to/file"),
        ("null", '"null"'),
        ("true", '"true"'),
        ("false", '"false"'),
        ("yes", '"yes"'),
        ("no", '"no"'),
        ("on", '"on"'),
        ("off", '"off"'),
        ("has spaces", "has spaces"),
        ("CON", "CON"),
        ("value: #comment", '"value: #comment"'),
        ("trailing ", "trailing "),
        ("123", "123"),
    ])
    def test_yaml_scalar(self, value: str, expected: str) -> None:
        assert gen._yaml_scalar(value) == expected  # pylint: disable=protected-access

    @pytest.mark.parametrize("text,expected", [
        ("plain text", "plain text"),
        ("before\n```\ncode\n```\nafter", "before\nafter"),
        ("before\n~~~\ncode\n~~~\nafter", "before\nafter"),
        ("```\nunterminated\n", ""),
        ("```python\nprint(1)\n```\nbody\n```\nmore", "body\n"),
    ])
    def test_strip_fenced_code(self, text: str, expected: str) -> None:
        assert gen._strip_fenced_code(text) == expected  # pylint: disable=protected-access

    def test_validate_bundle_references_valid(self) -> None:
        bundle = [
            {"bundle_relative_path": "doc.md", "content": b"See [other](other.md)", "relative_path": "doc.md"},
            {"bundle_relative_path": "other.md", "content": b"Other content", "relative_path": "other.md"},
        ]
        gen._validate_bundle_markdown_references(bundle)  # pylint: disable=protected-access

    def test_validate_bundle_references_missing(self) -> None:
        bundle = [
            {"bundle_relative_path": "doc.md", "content": b"See [missing](nope.md)", "relative_path": "doc.md"},
        ]
        with pytest.raises(ValueError, match="missing from skill bundle"):
            gen._validate_bundle_markdown_references(bundle)  # pylint: disable=protected-access

    def test_validate_bundle_references_escapes(self) -> None:
        bundle = [
            {"bundle_relative_path": "doc.md", "content": b"See [/etc/passwd](/etc/passwd)", "relative_path": "doc.md"},
        ]
        with pytest.raises(ValueError, match="escapes skill bundle"):
            gen._validate_bundle_markdown_references(bundle)  # pylint: disable=protected-access

    def test_validate_bundle_references_skips_urls(self) -> None:
        bundle = [
            {"bundle_relative_path": "doc.md", "content": b"See [web](https://example.com)", "relative_path": "doc.md"},
        ]
        gen._validate_bundle_markdown_references(bundle)  # pylint: disable=protected-access

    def test_validate_bundle_references_skips_non_markdown(self) -> None:
        bundle = [
            {"bundle_relative_path": "data.csv", "content": b"a,b,c", "relative_path": "data.csv"},
        ]
        gen._validate_bundle_markdown_references(bundle)  # pylint: disable=protected-access
