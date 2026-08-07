"""Tests for cg_generate_targets.py generator core.

Run from repo root:
    python3 -m pytest scripts/tests/test_cg_generate_targets.py -v
"""
from __future__ import annotations

import json
import hashlib
from pathlib import Path

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


class TestScanCanonicalAssets:
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
        assert "description: Test prompt" in content
        assert "role:" not in content.split("---", 2)[1]
        assert "$ARGUMENTS" in content

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
        }

    def test_kilo_commands_use_valid_frontmatter_and_arguments(self, tmp_path: Path) -> None:
        root = _make_fixture_repo(tmp_path)
        gen.main(["--root", str(root), "--target", "kilo"])
        content = (root / ".kilo/commands/cg-test.md").read_text()
        assert "description: Test prompt" in content
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

    def test_discovery_skips_unregistered_skill_dir(self, tmp_path: Path) -> None:
        root = _make_fixture_repo(tmp_path)
        _write(root / ".github/skills/cr-skill-unowned/SKILL.md",
               "---\ndescription: unowned\n---\n\nBody.\n")
        self._registry(root, {"cg-skill-test": "cap-test"})
        assets = gen.scan_canonical_assets(root)
        names = {Path(a["relative_path"]).parent.name for a in assets["skills"]}
        assert "cr-skill-unowned" not in names
        assert names == {"cg-skill-test"}

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
