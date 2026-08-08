"""Baseline tests for research-suite (cr-*) structural fidelity.

Extracted fixtures pin the structural baseline of the research branch
(origin/feat/compound-research-v2): prompt sections, agent frontmatter schema,
skill SKILL.md frontmatter, skill bundle closure, and instruction headings.
The ported CR assets in Phase 3 must preserve these structures.

Run from repo root:
    python -m pytest scripts/tests/test_cr_baseline.py -q
"""
from __future__ import annotations

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE = REPO_ROOT / "scripts/tests/fixtures/cr_baseline_from_research_branch.json"


def _frontmatter_keys(text: str) -> list[str]:
    if not text.lstrip("\ufeff\r\n").startswith("---"):
        return []
    try:
        block = text.lstrip("\ufeff\r\n").split("---", 2)[1]
    except IndexError:
        return []
    return sorted(
        line.split(":", 1)[0].strip()
        for line in block.splitlines()
        if ":" in line and not line.startswith((" ", "\t"))
    )


def _headings(text: str) -> list[str]:
    return sorted(line[3:].strip() for line in text.splitlines() if line.startswith("## "))


def _skill_dir_names() -> list[str]:
    return sorted(p.name for p in (REPO_ROOT / ".github/skills").glob("cr-skill-*") if p.is_dir())


def _bundle_relative_paths(skill_dir: Path) -> list[str]:
    return sorted(
        path.relative_to(skill_dir).as_posix()
        for path in skill_dir.rglob("*")
        if path.is_file()
    )


def _load_fixture() -> dict:
    assert FIXTURE.exists(), f"Missing CR baseline fixture: {FIXTURE}"
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


class TestCrBaseline:
    def test_fixture_is_committed(self) -> None:
        assert FIXTURE.exists()

    def test_cr_prompt_required_sections_preserved(self) -> None:
        fixture = _load_fixture()
        for name, expected in fixture["prompts"].items():
            path = REPO_ROOT / ".github/prompts" / f"{name}.prompt.md"
            if not path.exists():
                continue
            headings = _headings(path.read_text(encoding="utf-8"))
            assert set(expected["headings"]) <= set(headings), (
                f"{name}.prompt.md missing baseline sections: {sorted(set(expected['headings']) - set(headings))}"
            )

    def test_cr_agent_frontmatter_schema_preserved(self) -> None:
        fixture = _load_fixture()
        for name, expected_keys in fixture["agents"].items():
            path = REPO_ROOT / ".github/agents" / f"{name}.agent.md"
            if not path.exists():
                continue
            keys = _frontmatter_keys(path.read_text(encoding="utf-8"))
            assert set(expected_keys) <= set(keys), (
                f"{name}.agent.md missing baseline frontmatter keys: {sorted(set(expected_keys) - set(keys))}"
            )

    def test_cr_skill_frontmatter_fidelity(self) -> None:
        fixture = _load_fixture()
        for name, expected_keys in fixture["skills"].items():
            path = REPO_ROOT / ".github/skills" / name / "SKILL.md"
            if not path.exists():
                continue
            keys = _frontmatter_keys(path.read_text(encoding="utf-8"))
            assert set(expected_keys) <= set(keys), (
                f"{name}/SKILL.md missing baseline frontmatter keys: {sorted(set(expected_keys) - set(keys))}"
            )

    def test_cr_skill_bundle_closure_preserved(self) -> None:
        fixture = _load_fixture()
        for name, expected_files in fixture["skill_bundles"].items():
            skill_dir = REPO_ROOT / ".github/skills" / name
            if not skill_dir.is_dir():
                continue
            actual = _bundle_relative_paths(skill_dir)
            assert set(expected_files) <= set(actual), (
                f"{name} bundle missing baseline files: {sorted(set(expected_files) - set(actual))}"
            )

    def test_ported_cr_assets_are_imported_capability_style(self) -> None:
        """When any CR asset exists, its skill may carry a 'module' frontmatter
        aligning it with the research suite, and agents remain declarative."""
        for agent in (REPO_ROOT / ".github/agents").glob("cr-*.agent.md"):
            content = agent.read_text(encoding="utf-8")
            keys = _frontmatter_keys(content)
            assert "description" in keys, agent.name
            assert "tools" in keys, agent.name

    def test_cr_instruction_headings_preserved(self) -> None:
        fixture = _load_fixture()
        for name, expected_headings in fixture.get("instructions", {}).items():
            path = REPO_ROOT / ".github/instructions" / f"{name}.instructions.md"
            if not path.exists():
                continue
            headings = _headings(path.read_text(encoding="utf-8"))
            assert set(expected_headings) <= set(headings), (
                f"{name}.instructions.md missing baseline headings: "
                f"{sorted(set(expected_headings) - set(headings))}"
            )

    def test_cr_asset_count_matches_fixture_when_imported(self) -> None:
        fixture = _load_fixture()
        actual_prompts = len(list((REPO_ROOT / ".github/prompts").glob("cr-*.prompt.md")))
        actual_agents = len(list((REPO_ROOT / ".github/agents").glob("cr-*.agent.md")))
        actual_skills = len(_skill_dir_names())
        # Research instructions are the LaTeX and math files (not cr-* prefixed).
        research_instructions = [
            name for name in ("latex", "math")
            if (REPO_ROOT / ".github/instructions" / f"{name}.instructions.md").exists()
        ]
        if actual_prompts == 0 and actual_agents == 0 and actual_skills == 0:
            return  # CR not yet imported — baseline is a forward pin
        assert actual_prompts >= len(fixture["prompts"]), (
            f"Only {actual_prompts} cr-prompts imported; expected at least {len(fixture['prompts'])}"
        )
        assert actual_agents >= len(fixture["agents"]), (
            f"Only {actual_agents} cr-agents imported; expected at least {len(fixture['agents'])}"
        )
        assert actual_skills >= len(fixture["skills"]), (
            f"Only {actual_skills} cr-skills imported; expected at least {len(fixture['skills'])}"
        )
        assert len(research_instructions) >= len(fixture.get("instructions", {})), (
            f"Only {len(research_instructions)} research instructions present; "
            f"expected at least {len(fixture.get('instructions', {}))}"
        )
