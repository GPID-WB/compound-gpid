"""Tests for OpenCode target generation.

Run from repo root:
    python3 -m pytest scripts/tests/test_target_opencode.py -v
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

import cg_generate_targets as gen

REPO_ROOT = Path(__file__).resolve().parents[2]


class TestOpenCodeTreeStructure:
    def test_commands_dir_exists(self) -> None:
        assert (REPO_ROOT / ".opencode/commands").is_dir()

    def test_skills_dir_exists(self) -> None:
        assert (REPO_ROOT / ".opencode/skills").is_dir()

    def test_agents_dir_exists(self) -> None:
        assert (REPO_ROOT / ".opencode/agents").is_dir()

    def test_root_adapter_exists(self) -> None:
        assert (REPO_ROOT / ".opencode/AGENTS.md").is_file()

    def test_config_file_exists(self) -> None:
        assert (REPO_ROOT / ".opencode/opencode.json").is_file()

    def test_model_mapping_artifact_exists(self) -> None:
        assert (REPO_ROOT / ".opencode/model-mapping.opencode.json").is_file()

    def test_every_prompt_has_a_command(self) -> None:
        prompts = list((REPO_ROOT / ".github/prompts").glob("*.prompt.md"))
        for prompt in prompts:
            cmd_name = prompt.name.replace(".prompt.md", ".md")
            assert (REPO_ROOT / ".opencode/commands" / cmd_name).exists(), f"Missing command: {cmd_name}"

    def test_every_agent_has_an_agent_file(self) -> None:
        agents = list((REPO_ROOT / ".github/agents").glob("*.agent.md"))
        for agent in agents:
            agent_name = agent.name.replace(".agent.md", ".md")
            assert (REPO_ROOT / ".opencode/agents" / agent_name).exists(), f"Missing agent: {agent_name}"

    def test_every_skill_has_a_skill_file(self) -> None:
        skills = list((REPO_ROOT / ".github/skills").glob("cg-skill-*/SKILL.md"))
        for skill in skills:
            skill_name = skill.parent.name
            assert (REPO_ROOT / ".opencode/skills" / skill_name / "SKILL.md").exists(), f"Missing skill: {skill_name}"


class TestOpenCodeModelMapping:
    def test_model_mapping_uses_role_only_mode(self) -> None:
        data = json.loads((REPO_ROOT / ".opencode/model-mapping.opencode.json").read_text())
        assert data["modelMappingMode"] == "role-only"

    def test_agent_files_use_role_not_exact_models(self) -> None:
        agent_files = list((REPO_ROOT / ".opencode/agents").glob("*.md"))
        assert len(agent_files) > 0
        for agent_file in agent_files:
            content = agent_file.read_text()
            assert "GPT-5" not in content
            assert "Claude" not in content

    def test_config_file_has_platform(self) -> None:
        data = json.loads((REPO_ROOT / ".opencode/opencode.json").read_text())
        assert data["platform"] == "opencode"

    def test_root_adapter_references_opencode_paths(self) -> None:
        content = (REPO_ROOT / ".opencode/AGENTS.md").read_text()
        assert ".opencode/" in content
