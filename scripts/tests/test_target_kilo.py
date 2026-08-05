"""Tests for Kilo target generation.

Run from repo root:
    python3 -m pytest scripts/tests/test_target_kilo.py -v
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

import cg_generate_targets as gen

REPO_ROOT = Path(__file__).resolve().parents[2]


def _frontmatter(content: str) -> dict[str, str]:
    """Parse simple key: value frontmatter used by generated Kilo files."""
    assert content.startswith("---\n")
    _, raw_fm, _ = content.split("---", 2)
    fields: dict[str, str] = {}
    for line in raw_fm.splitlines():
        if not line.strip() or ":" not in line:
            continue
        key, value = line.split(":", 1)
        fields[key.strip()] = value.strip()
    return fields


class TestKiloTreeStructure:
    def test_commands_dir_exists(self) -> None:
        assert (REPO_ROOT / ".kilo/commands").is_dir()

    def test_skills_dir_exists(self) -> None:
        assert (REPO_ROOT / ".kilo/skills").is_dir()
        assert not (REPO_ROOT / ".kilo" / "skill").exists()

    def test_agents_dir_exists(self) -> None:
        assert (REPO_ROOT / ".kilo/agents").is_dir()
        assert not (REPO_ROOT / ".kilo" / "agent").exists()

    def test_root_adapter_exists(self) -> None:
        assert (REPO_ROOT / ".kilo/AGENTS.md").is_file()

    def test_config_file_exists(self) -> None:
        assert (REPO_ROOT / ".kilo/kilo.json").is_file()

    def test_every_prompt_has_a_command(self) -> None:
        prompts = list((REPO_ROOT / ".github/prompts").glob("*.prompt.md"))
        for prompt in prompts:
            cmd_name = prompt.name.replace(".prompt.md", ".md")
            assert (REPO_ROOT / ".kilo/commands" / cmd_name).exists(), f"Missing command: {cmd_name}"

    def test_commands_are_kilo_discoverable(self) -> None:
        command_files = list((REPO_ROOT / ".kilo/commands").glob("cg-*.md"))
        assert command_files
        for command_file in command_files:
            content = command_file.read_text(encoding="utf-8")
            fm = _frontmatter(content)
            assert fm.get("description"), f"Missing description: {command_file}"
            assert "role" not in fm, f"Kilo command has invalid role field: {command_file}"
            assert "$ARGUMENTS" in content, f"Command does not receive arguments: {command_file}"
            assert content.split("---", 2)[-1].strip(), f"Missing command template: {command_file}"

    def test_every_agent_has_an_agent_file(self) -> None:
        agents = list((REPO_ROOT / ".github/agents").glob("*.agent.md"))
        for agent in agents:
            agent_name = agent.name.replace(".agent.md", ".md")
            assert (REPO_ROOT / ".kilo/agents" / agent_name).exists(), f"Missing agent: {agent_name}"

    def test_agents_are_kilo_discoverable(self) -> None:
        agent_files = list((REPO_ROOT / ".kilo/agents").glob("*.md"))
        assert agent_files
        for agent_file in agent_files:
            content = agent_file.read_text(encoding="utf-8")
            fm = _frontmatter(content)
            assert fm.get("description"), f"Missing description: {agent_file}"
            assert fm.get("mode") == "subagent", f"Missing subagent mode: {agent_file}"
            assert "role" not in fm, f"Kilo agent has invalid role field: {agent_file}"
            assert content.split("---", 2)[-1].strip(), f"Missing agent prompt: {agent_file}"

    def test_every_skill_has_a_skill_file(self) -> None:
        skills = list((REPO_ROOT / ".github/skills").glob("cg-skill-*/SKILL.md"))
        for skill in skills:
            skill_name = skill.parent.name
            assert (REPO_ROOT / ".kilo/skills" / skill_name / "SKILL.md").exists(), f"Missing skill: {skill_name}"

    def test_skills_are_kilo_discoverable(self) -> None:
        skill_files = list((REPO_ROOT / ".kilo/skills").glob("*/SKILL.md"))
        assert skill_files
        for skill_file in skill_files:
            content = skill_file.read_text(encoding="utf-8")
            fm = _frontmatter(content)
            assert fm.get("name") == skill_file.parent.name, f"Skill name mismatch: {skill_file}"
            assert fm.get("description"), f"Missing skill description: {skill_file}"


class TestKiloModelInheritance:
    def test_commands_and_agent_files_do_not_assign_models(self) -> None:
        files = list((REPO_ROOT / ".kilo/commands").rglob("*.md"))
        files += list((REPO_ROOT / ".kilo/agents").glob("*.md"))
        assert files
        for path in files:
            assert "model:" not in path.read_text(encoding="utf-8"), path

    def test_config_file_uses_valid_kilo_schema_shape(self) -> None:
        data = json.loads((REPO_ROOT / ".kilo/kilo.json").read_text(encoding="utf-8"))
        assert data["$schema"] == "https://app.kilo.ai/config.json"
        assert data["instructions"] == [".kilo/AGENTS.md"]
        assert data["skills"] == {"paths": [".kilo/skills"]}
        assert "platform" not in data
        assert "commands" not in data
        assert "agents" not in data

    def test_root_adapter_references_kilo_paths(self) -> None:
        content = (REPO_ROOT / ".kilo/AGENTS.md").read_text(encoding="utf-8")
        assert ".kilo/commands" in content
