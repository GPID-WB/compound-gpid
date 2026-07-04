"""Tests for cg_generate_targets.py generator core.

Run from repo root:
    python3 -m pytest scripts/tests/test_cg_generate_targets.py -v
"""
from __future__ import annotations

import json
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
           "---\ndescription: Test prompt\nmodel: GPT-5.3-Codex\n---\n\n# Test Prompt\n\nBody.\n")
    _write(root / ".github/prompts/cg-another.prompt.md",
           "---\ndescription: Another prompt\n---\n\n# Another\n\nBody.\n")

    _write(root / ".github/agents/cg-test-agent.agent.md",
           "---\ndescription: Test agent\nmodel: GPT-5.4\ntools: ['read', 'write']\n---\n\n# Test Agent\n\nAgent body.\n")

    _write(root / ".github/skills/cg-skill-test/SKILL.md",
           "---\nname: cg-skill-test\ndescription: Test skill\n---\n\n# Test Skill\n\nSkill body.\n")

    _write(root / ".github/shared/target-mapping.json", json.dumps({
        "schemaVersion": 1,
        "description": "Test mapping",
        "targets": [
            {
                "id": "copilot",
                "name": "GitHub Copilot",
                "generatedTreePath": None,
                "modelMappingMode": "role-only",
                "capabilities": {f: True for f in gen.REQUIRED_CAPABILITY_FIELDS},
                "formats": {f: "github-" + f.replace("Format", "") for f in gen.REQUIRED_FORMAT_FIELDS},
                "outputPaths": {"commands": ".github/prompts", "skills": ".github/skills", "agents": ".github/agents"},
            },
            {
                "id": "claude-code",
                "name": "Claude Code",
                "generatedTreePath": ".claude",
                "modelMappingMode": "tier",
                "capabilities": {f: True for f in gen.REQUIRED_CAPABILITY_FIELDS},
                "formats": {"commandFormat": "claude-command", "skillFormat": "claude-skill", "agentFormat": "claude-agent"},
                "outputPaths": {
                    "commands": ".claude/commands",
                    "skills": ".claude/skills",
                    "agents": ".claude/agents",
                    "rootAdapter": ".claude/CLAUDE.md",
                    "modelMapping": ".claude/model-mapping.claude.json",
                },
                "modelMapping": {"coding": "sonnet", "review": "sonnet", "reasoning": "opus", "mechanical": "haiku", "inherited": None},
            },
            {
                "id": "codex",
                "name": "Codex",
                "generatedTreePath": ".agents",
                "modelMappingMode": "exact",
                "capabilities": {f: True for f in gen.REQUIRED_CAPABILITY_FIELDS},
                "formats": {"commandFormat": "codex-command", "skillFormat": "codex-skill", "agentFormat": "codex-subagent-toml", "fallbackAgentFormat": "codex-skill"},
                "outputPaths": {
                    "commands": ".agents/commands",
                    "skills": ".agents/skills",
                    "agents": ".agents/subagents",
                    "rootAdapter": ".agents/AGENTS.md",
                    "modelMapping": ".agents/model-mapping.codex.json",
                },
                "modelMapping": {"coding": "GPT-5.3-Codex", "review": "GPT-5.4", "reasoning": "GPT-5.4", "mechanical": "GPT-5.4 mini", "inherited": None},
            },
            {
                "id": "opencode",
                "name": "OpenCode",
                "generatedTreePath": ".opencode",
                "modelMappingMode": "role-only",
                "capabilities": {f: True for f in gen.REQUIRED_CAPABILITY_FIELDS},
                "formats": {"commandFormat": "opencode-command", "skillFormat": "opencode-skill", "agentFormat": "opencode-agent"},
                "outputPaths": {
                    "commands": ".opencode/commands",
                    "skills": ".opencode/skills",
                    "agents": ".opencode/agents",
                    "rootAdapter": ".opencode/AGENTS.md",
                    "config": ".opencode/opencode.json",
                    "modelMapping": ".opencode/model-mapping.opencode.json",
                },
            },
        ],
    }))

    _write(root / ".github/shared/model-catalog.json", json.dumps({
        "models": [{"name": "GPT-5.3-Codex", "vendor": "openai", "family": "GPT-5-Codex", "roles": ["coding", "review"], "tier": "standard", "policyStatus": "preferred"}],
        "frontmatterSupport": [{"model": "GPT-5.3-Codex", "status": "frontmatter-supported"}],
        "assignments": [
            {"path": ".github/prompts/cg-test.prompt.md", "role": "coding", "preferredModel": "GPT-5.3-Codex", "frontmatterMode": "explicit", "rationale": "test"},
            {"path": ".github/agents/cg-test-agent.agent.md", "role": "review", "preferredModel": "GPT-5.4", "frontmatterMode": "explicit", "rationale": "test"},
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

    def test_empty_repo_no_error(self, tmp_path: Path) -> None:
        root = tmp_path / "empty"
        root.mkdir()
        (root / ".github/shared/target-mapping.json").parent.mkdir(parents=True)
        assets = gen.scan_canonical_assets(root)
        assert assets["prompts"] == []
        assert assets["agents"] == []


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

    def test_codex_writes_fallback_skills(self, tmp_path: Path) -> None:
        root = _make_fixture_repo(tmp_path)
        gen.main(["--root", str(root), "--target", "codex"])
        fallback_files = list((root / ".agents/skills").glob("*.md"))
        assert len(fallback_files) == 1

    def test_opencode_writes_config(self, tmp_path: Path) -> None:
        root = _make_fixture_repo(tmp_path)
        gen.main(["--root", str(root), "--target", "opencode"])
        assert (root / ".opencode/opencode.json").exists()

    def test_opencode_uses_role_only_no_exact_models(self, tmp_path: Path) -> None:
        root = _make_fixture_repo(tmp_path)
        gen.main(["--root", str(root), "--target", "opencode"])
        agent_files = list((root / ".opencode/agents").glob("*.md"))
        assert len(agent_files) == 1
        content = agent_files[0].read_text()
        assert "role:" in content
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

    def test_model_mapping_artifact_written(self, tmp_path: Path) -> None:
        root = _make_fixture_repo(tmp_path)
        gen.main(["--root", str(root), "--target", "claude-code"])
        assert (root / ".claude/model-mapping.claude.json").exists()
        data = json.loads((root / ".claude/model-mapping.claude.json").read_text())
        assert data["platform"] == "claude-code"
        assert data["modelMappingMode"] == "tier"

    def test_root_adapter_written(self, tmp_path: Path) -> None:
        root = _make_fixture_repo(tmp_path)
        gen.main(["--root", str(root), "--target", "claude-code"])
        assert (root / ".claude/CLAUDE.md").exists()


class TestModelResolution:
    def test_exact_mode_returns_model_name(self) -> None:
        target = {"modelMappingMode": "exact", "modelMapping": {"coding": "GPT-5.3-Codex"}}
        assert gen.resolve_model(target, "coding") == "GPT-5.3-Codex"

    def test_role_only_mode_returns_none(self) -> None:
        target = {"modelMappingMode": "role-only", "modelMapping": {}}
        assert gen.resolve_model(target, "coding") is None

    def test_tier_mode_returns_tier(self) -> None:
        target = {"modelMappingMode": "tier", "modelMapping": {"coding": "sonnet"}}
        assert gen.resolve_model(target, "coding") == "sonnet"

    def test_inherited_role_returns_none(self) -> None:
        target = {"modelMappingMode": "exact", "modelMapping": {"inherited": None}}
        assert gen.resolve_model(target, "inherited") is None

    def test_unknown_role_returns_none(self) -> None:
        target = {"modelMappingMode": "exact", "modelMapping": {"coding": "GPT-5.3-Codex"}}
        assert gen.resolve_model(target, "unknown-role") is None


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
               "---\ndescription: Agent without tools\nmodel: GPT-5.4\n---\n\n# Agent\n\nBody.\n")
        exit_code = gen.main(["--root", str(root), "--target", "codex"])
        assert exit_code == 0
        toml = (root / ".agents/subagents/cg-no-tools.toml").read_text()
        assert "tools = []" in toml

    def test_model_catalog_with_no_assignments(self, tmp_path: Path) -> None:
        """A catalog with no assignments array should not crash — roles resolve to None."""
        root = _make_fixture_repo(tmp_path)
        _write(root / ".github/shared/model-catalog.json", json.dumps({
            "models": [{"name": "GPT-5.3-Codex", "vendor": "openai", "family": "GPT-5", "roles": ["coding"], "tier": "standard", "policyStatus": "preferred"}],
            "frontmatterSupport": [],
            "assignments": [],
        }))
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
        """An empty .github/ directory should produce only root-adapter + model-mapping artifacts."""
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
                "modelMappingMode": "tier",
                "capabilities": {f: True for f in gen.REQUIRED_CAPABILITY_FIELDS},
                "formats": {"commandFormat": "c", "skillFormat": "s", "agentFormat": "a"},
                "outputPaths": {"commands": ".claude/commands", "skills": ".claude/skills", "agents": ".claude/agents", "rootAdapter": ".claude/CLAUDE.md", "modelMapping": ".claude/mm.json"},
                "modelMapping": {"coding": "sonnet"},
            }],
        }))
        exit_code = gen.main(["--root", str(root), "--target", "claude-code"])
        assert exit_code == 0
        assert (root / ".claude/CLAUDE.md").exists()
        assert (root / ".claude/mm.json").exists()
