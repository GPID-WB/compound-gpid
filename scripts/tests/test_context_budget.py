"""Tests for context-budget enforcement (R10).

Covers generator-level filtering: an active-suite configuration determines which
modules (and therefore which canonical assets) are loadable. CG-only projects
must not load CR instructions/skills; mixed projects load both; capability-pack
assets shared by both suites load regardless of suite selection.

Run from repo root:
    python -m pytest scripts/tests/test_context_budget.py -q
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

import cg_context_budget as budget

REPO_ROOT = Path(__file__).resolve().parents[2]


def _minimal_registry(extra_suite: dict | None = None) -> dict:
    modules = [
        {
            "id": "kernel",
            "layer": "kernel",
            "displayName": "Kernel",
            "description": "kernel",
            "dependsOn": [],
            "ownedAssets": [".github/shared/*.contract.md", ".github/skills/cg-skill-brain-query/"],
        },
        {
            "id": "cap-language-r",
            "layer": "capability",
            "displayName": "R",
            "description": "R",
            "dependsOn": ["kernel"],
            "ownedAssets": [".github/skills/cg-skill-r-*/", ".github/instructions/r.instructions.md"],
        },
        {
            "id": "cap-research-output",
            "layer": "capability",
            "displayName": "Research output",
            "description": "output",
            "dependsOn": ["kernel"],
            "ownedAssets": [".github/skills/cr-skill-publication-output/"],
        },
        {
            "id": "suite-cg",
            "layer": "suite",
            "displayName": "CG",
            "description": "cg",
            "dependsOn": ["kernel", "cap-language-r"],
            "ownedAssets": [".github/prompts/cg-*.prompt.md", ".github/agents/cg-*.agent.md"],
        },
    ]
    if extra_suite:
        modules.append(extra_suite)
    return {"schemaVersion": 1, "description": "test", "modules": modules}


CR_SUITE = {
    "id": "suite-cr",
    "layer": "suite",
    "displayName": "CR",
    "description": "cr",
    "dependsOn": ["kernel", "cap-language-r", "cap-research-output"],
    "ownedAssets": [
        ".github/prompts/cr-*.prompt.md",
        ".github/agents/cr-*.agent.md",
        ".github/skills/cr-skill-academic-writing/",
    ],
}


def _local_config(suites: list[str] | None) -> str:
    field = f"suites: [{', '.join(suites)}]\n" if suites else ""
    return f"---\nlanguage: both\n{field}review-depth: thorough\n---\n# config\n"


class TestActiveSuites:
    def test_read_active_suites_defaults_to_cg(self) -> None:
        assert budget.read_active_suites(_local_config(None)) == ["cg"]

    def test_read_active_suites_explicit(self) -> None:
        assert budget.read_active_suites(_local_config(["cg", "cr"])) == ["cg", "cr"]

    def test_read_active_suites_quoted_yaml_list(self) -> None:
        text = "---\nlanguage: both\nsuites: [\"cg\", \"cr\"]\nreview-depth: thorough\n---\n# config\n"
        assert budget.read_active_suites(text) == ["cg", "cr"]

    def test_read_active_suites_block_style(self) -> None:
        text = "---\nlanguage: both\nsuites:\n  - cg\n  - cr\nreview-depth: thorough\n---\n# config\n"
        assert budget.read_active_suites(text) == ["cg", "cr"]

    def test_unresolved_suite_name_fails_loudly(self, tmp_path: Path) -> None:
        registry = budget.load_registry(tmp_path, _minimal_registry())
        with pytest.raises(ValueError, match="unknown active suite"):
            budget.loadable_modules(registry, ["cgx"])

    def test_capability_id_suffix_is_not_treated_as_suite(self, tmp_path: Path) -> None:
        """P1: capability id suffixes (r, research, output, docs) must fail
        loudly, not silently produce a kernel-only tree."""
        registry = budget.load_registry(tmp_path, _minimal_registry(CR_SUITE))
        for bogus in ("r", "research", "output", "docs"):
            with pytest.raises(ValueError, match="unknown active suite"):
                budget.loadable_modules(registry, [bogus])

    def test_block_style_suite_list_with_comment(self) -> None:
        text = "---\nlanguage: both\nsuites:\n# note\n  - cg\n  - cr\nreview-depth: thorough\n---\n# config\n"
        assert budget.read_active_suites(text) == ["cg", "cr"]

    def test_inline_suite_list_with_trailing_comment(self) -> None:
        text = "---\nlanguage: both\nsuites: [cg, cr]  # both\nreview-depth: thorough\n---\n# config\n"
        assert budget.read_active_suites(text) == ["cg", "cr"]

    def test_filtered_manifest_wires_modules_and_globs(self, tmp_path: Path) -> None:
        registry = budget.load_registry(tmp_path, _minimal_registry(CR_SUITE))
        manifest = budget.filtered_manifest(registry, ["cg"])
        assert manifest["activeSuites"] == ["cg"]
        assert "suite-cg" in manifest["loadableModules"]
        assert "suite-cr" not in manifest["loadableModules"]
        assert any("cg-*.prompt.md" in glob for glob in manifest["loadableAssetGlobs"])

    def test_loadable_modules_cg_only(self, tmp_path: Path) -> None:
        registry = budget.load_registry(tmp_path, _minimal_registry())
        loadable = budget.loadable_modules(registry, ["cg"])
        ids = {module["id"] for module in loadable}
        assert "kernel" in ids and "cap-language-r" in ids and "suite-cg" in ids
        assert "suite-cr" not in ids
        assert "cap-research-output" not in ids

    def test_loadable_modules_mixed(self, tmp_path: Path) -> None:
        registry = budget.load_registry(tmp_path, _minimal_registry(CR_SUITE))
        loadable = budget.loadable_modules(registry, ["cg", "cr"])
        ids = {module["id"] for module in loadable}
        assert {"suite-cg", "suite-cr", "cap-research-output", "kernel"} <= ids

    def test_capability_used_by_both_suites_loads(self, tmp_path: Path) -> None:
        registry = budget.load_registry(tmp_path, _minimal_registry(CR_SUITE))
        loadable = budget.loadable_modules(registry, ["cg", "cr"])
        ids = {module["id"] for module in loadable}
        assert "cap-language-r" in ids  # shared capability

    def test_asset_of_inactive_suite_excluded(self, tmp_path: Path) -> None:
        registry = budget.load_registry(tmp_path, _minimal_registry(CR_SUITE))
        loadable = {module["id"] for module in budget.loadable_modules(registry, ["cg"])}
        assets = budget.loadable_asset_globs(registry, loadable)
        cr_prompt = any(glob.lower().startswith(".github/prompts/cr-") for glob in assets)
        assert not cr_prompt


class TestRealRepo:
    def test_real_registry_cg_minus_cr_detects_cr_excluded(self) -> None:
        # With the real registry but only the cg suite active, cr-* assets are
        # excluded from the loadable set while cg assets remain.
        registry_path = REPO_ROOT / ".github/shared/module-registry.json"
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
        loadable = budget.loadable_modules(registry, ["cg"])
        ids = {module["id"] for module in loadable}
        assert "suite-cg" in ids
        assert "suite-cr" not in ids

    def test_generator_cg_only_omits_cr_assets(self, tmp_path: Path) -> None:
        """Generator-level enforcement: CG-only generation excludes CR assets."""
        import cg_generate_targets as gen

        fixture = tmp_path / "fixture"
        for item in [".github", "scripts"]:
            src = REPO_ROOT / item
            dst = fixture / item
            if src.exists():
                import shutil
                shutil.copytree(src, dst, dirs_exist_ok=True)

        # Force CG-only by scanning with active-suites filter.
        assets = gen.scan_canonical_assets(fixture, active_suites=["cg"])
        cr_prompts = [a for a in assets["prompts"] if a["relative_path"].startswith(".github/prompts/cr-")]
        cr_agents = [a for a in assets["agents"] if a["relative_path"].startswith(".github/agents/cr-")]
        cr_skills = [a for a in assets["skills"] if a["relative_path"].startswith(".github/skills/cr-")]
        assert not cr_prompts and not cr_agents and not cr_skills

        # CG assets remain.
        assert any(a["relative_path"].startswith(".github/prompts/cg-") for a in assets["prompts"])
        assert any(a["relative_path"].startswith(".github/skills/cg-skill-r-") for a in assets["skills"])

    def test_generator_mixed_includes_cr_assets(self, tmp_path: Path) -> None:
        """Generator-level enforcement: mixed generation includes CR assets."""
        import cg_generate_targets as gen

        fixture = tmp_path / "fixture"
        for item in [".github", "scripts"]:
            src = REPO_ROOT / item
            dst = fixture / item
            if src.exists():
                import shutil
                shutil.copytree(src, dst, dirs_exist_ok=True)

        assets = gen.scan_canonical_assets(fixture, active_suites=["cg", "cr"])
        assert any(a["relative_path"].startswith(".github/prompts/cr-") for a in assets["prompts"])
        assert any(a["relative_path"].startswith(".github/skills/cr-skill-") for a in assets["skills"])
