"""Tests for Codex target generation.

Run from repo root:
    python3 -m pytest scripts/tests/test_target_codex.py -v
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

import cg_generate_targets as gen

REPO_ROOT = Path(__file__).resolve().parents[2]


class TestCodexTreeStructure:
    def test_commands_dir_exists(self) -> None:
        assert (REPO_ROOT / ".agents/commands").is_dir()

    def test_subagents_dir_exists(self) -> None:
        assert (REPO_ROOT / ".agents/subagents").is_dir()

    def test_skills_dir_exists(self) -> None:
        assert (REPO_ROOT / ".agents/skills").is_dir()

    def test_root_adapter_exists(self) -> None:
        assert (REPO_ROOT / ".agents/AGENTS.md").is_file()

    def test_model_mapping_artifact_exists(self) -> None:
        assert (REPO_ROOT / ".agents/model-mapping.codex.json").is_file()

    def test_every_prompt_has_a_command(self) -> None:
        prompts = list((REPO_ROOT / ".github/prompts").glob("*.prompt.md"))
        for prompt in prompts:
            cmd_name = prompt.name.replace(".prompt.md", ".md")
            assert (REPO_ROOT / ".agents/commands" / cmd_name).exists(), f"Missing command: {cmd_name}"

    def test_every_agent_has_toml_subagent(self) -> None:
        agents = list((REPO_ROOT / ".github/agents").glob("*.agent.md"))
        for agent in agents:
            toml_name = agent.name.replace(".agent.md", ".toml")
            assert (REPO_ROOT / ".agents/subagents" / toml_name).exists(), f"Missing TOML: {toml_name}"

    def test_every_agent_has_fallback_skill(self) -> None:
        agents = list((REPO_ROOT / ".github/agents").glob("*.agent.md"))
        for agent in agents:
            skill_name = agent.name.replace(".agent.md", ".md")
            assert (REPO_ROOT / ".agents/skills" / skill_name).exists(), f"Missing fallback: {skill_name}"


class TestCodexTOMLFormat:
    def test_toml_has_subagent_header(self) -> None:
        toml_files = list((REPO_ROOT / ".agents/subagents").glob("*.toml"))
        assert len(toml_files) > 0
        content = toml_files[0].read_text(encoding="utf-8")
        assert "[[subagent]]" in content

    def test_toml_has_name_field(self) -> None:
        toml_files = list((REPO_ROOT / ".agents/subagents").glob("*.toml"))
        content = toml_files[0].read_text(encoding="utf-8")
        assert "name =" in content

    def test_toml_has_description_field(self) -> None:
        toml_files = list((REPO_ROOT / ".agents/subagents").glob("*.toml"))
        content = toml_files[0].read_text(encoding="utf-8")
        assert "description =" in content

    def test_fallback_skill_has_agent_header(self) -> None:
        fallback_files = list((REPO_ROOT / ".agents/skills").glob("*.md"))
        assert len(fallback_files) > 0
        content = fallback_files[0].read_text(encoding="utf-8")
        assert "# Agent:" in content


class TestCodexModelMapping:
    def test_model_mapping_uses_exact_mode(self) -> None:
        data = json.loads((REPO_ROOT / ".agents/model-mapping.codex.json").read_text(encoding="utf-8"))
        assert data["modelMappingMode"] == "exact"

    def test_model_mapping_has_coding_role(self) -> None:
        data = json.loads((REPO_ROOT / ".agents/model-mapping.codex.json").read_text(encoding="utf-8"))
        assert data["mapping"]["coding"] == "GPT-5.3-Codex"

    def test_model_mapping_has_review_role(self) -> None:
        data = json.loads((REPO_ROOT / ".agents/model-mapping.codex.json").read_text(encoding="utf-8"))
        assert data["mapping"]["review"] == "GPT-5.4"

    def test_root_adapter_references_agents_paths(self) -> None:
        content = (REPO_ROOT / ".agents/AGENTS.md").read_text(encoding="utf-8")
        assert ".agents/" in content
