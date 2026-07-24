"""Tests for Claude Code target generation.

Run from repo root:
    python3 -m pytest scripts/tests/test_target_claude.py -v
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

import cg_generate_targets as gen

REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_repo_mapping() -> dict:
    return json.loads((REPO_ROOT / ".github/shared/target-mapping.json").read_text(encoding="utf-8"))


class TestClaudeCodeTreeStructure:
    def test_commands_dir_exists(self) -> None:
        assert (REPO_ROOT / ".claude/commands").is_dir()

    def test_skills_dir_exists(self) -> None:
        assert (REPO_ROOT / ".claude/skills").is_dir()

    def test_agents_dir_exists(self) -> None:
        assert (REPO_ROOT / ".claude/agents").is_dir()

    def test_root_adapter_exists(self) -> None:
        assert (REPO_ROOT / ".claude/CLAUDE.md").is_file()

    def test_model_mapping_artifact_exists(self) -> None:
        assert (REPO_ROOT / ".claude/model-mapping.claude.json").is_file()

    def test_every_prompt_has_a_command(self) -> None:
        prompts = list((REPO_ROOT / ".github/prompts").glob("*.prompt.md"))
        for prompt in prompts:
            cmd_name = prompt.name.replace(".prompt.md", ".md")
            assert (REPO_ROOT / ".claude/commands" / cmd_name).exists(), f"Missing command: {cmd_name}"

    def test_every_agent_has_a_subagent_file(self) -> None:
        agents = list((REPO_ROOT / ".github/agents").glob("*.agent.md"))
        for agent in agents:
            agent_name = agent.name.replace(".agent.md", ".md")
            assert (REPO_ROOT / ".claude/agents" / agent_name).exists(), f"Missing agent: {agent_name}"

    def test_every_skill_has_a_skill_file(self) -> None:
        skills = list((REPO_ROOT / ".github/skills").glob("cg-skill-*/SKILL.md"))
        for skill in skills:
            skill_name = skill.parent.name
            assert (REPO_ROOT / ".claude/skills" / skill_name / "SKILL.md").exists(), f"Missing skill: {skill_name}"


class TestClaudeCodeModelMapping:
    def test_model_mapping_uses_tier_mode(self) -> None:
        data = json.loads((REPO_ROOT / ".claude/model-mapping.claude.json").read_text(encoding="utf-8"))
        assert data["modelMappingMode"] == "tier"

    def test_model_mapping_has_coding_role(self) -> None:
        data = json.loads((REPO_ROOT / ".claude/model-mapping.claude.json").read_text(encoding="utf-8"))
        assert "coding" in data["mapping"]
        assert data["mapping"]["coding"] == "sonnet"

    def test_model_mapping_has_reasoning_role(self) -> None:
        data = json.loads((REPO_ROOT / ".claude/model-mapping.claude.json").read_text(encoding="utf-8"))
        assert data["mapping"]["reasoning"] == "opus"

    def test_model_mapping_has_mechanical_role(self) -> None:
        data = json.loads((REPO_ROOT / ".claude/model-mapping.claude.json").read_text(encoding="utf-8"))
        assert data["mapping"]["mechanical"] == "haiku"

    def test_command_has_model_frontmatter_for_coding_role(self) -> None:
        cmd = (REPO_ROOT / ".claude/commands/cg-work.md")
        if cmd.exists():
            content = cmd.read_text(encoding="utf-8")
            assert "model:" in content

    def test_root_adapter_references_claude_paths(self) -> None:
        content = (REPO_ROOT / ".claude/CLAUDE.md").read_text(encoding="utf-8")
        assert ".claude/" in content
