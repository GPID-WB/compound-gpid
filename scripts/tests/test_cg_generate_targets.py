"""Tests for cg_generate_targets.py generator core.

Run from repo root:
    python3 -m pytest scripts/tests/test_cg_generate_targets.py -v
"""
from __future__ import annotations

import json
import hashlib
import os
from collections import Counter
from pathlib import Path
from types import SimpleNamespace

import pytest

import cg_generate_targets as gen


def _write(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


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
