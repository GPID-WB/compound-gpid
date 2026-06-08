"""Tests for cg_audit_context.

Run from repo root:
    python -m pytest scripts/tests/test_audit_context.py -v
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

import cg_audit_context as audit


def _write(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def _frontmatter(model: str | None = "Claude Sonnet 4.6") -> str:
    if model is None:
        return "---\ndescription: Test\n---\n\nBody\n"
    return f"---\ndescription: Test\nmodel: \"{model}\"\n---\n\nBody\n"


class TestTokenEstimation:
    def test_empty_file_zero_tokens(self) -> None:
        assert audit.estimate_tokens("") == 0

    def test_known_length(self) -> None:
        assert audit.estimate_tokens("a" * 400) == 100

    def test_unicode_chars_counted(self) -> None:
        assert audit.estimate_tokens("é" * 8) == 2


class TestFileScanner:
    def test_finds_prompt_files(self, tmp_path: Path) -> None:
        _write(tmp_path / ".github/prompts/x.prompt.md", _frontmatter())
        files, _ = audit.scan_files(tmp_path)
        assert any(row["path"] == ".github/prompts/x.prompt.md" for row in files)

    def test_finds_agent_files(self, tmp_path: Path) -> None:
        _write(tmp_path / ".github/agents/x.agent.md", _frontmatter())
        files, _ = audit.scan_files(tmp_path)
        assert any(row["path"] == ".github/agents/x.agent.md" for row in files)

    def test_categorizes_correctly(self, tmp_path: Path) -> None:
        _write(tmp_path / ".github/prompts/x.prompt.md", _frontmatter())
        _write(tmp_path / ".github/agents/x.agent.md", _frontmatter())
        _write(tmp_path / ".github/skills/cg-skill-x/SKILL.md", "Skill")
        _write(tmp_path / ".github/instructions/python.instructions.md", "Instruction")
        files, _ = audit.scan_files(tmp_path)
        categories = {row["path"]: row["category"] for row in files}
        assert categories[".github/prompts/x.prompt.md"] == "prompts"
        assert categories[".github/agents/x.agent.md"] == "agents"
        assert categories[".github/skills/cg-skill-x/SKILL.md"] == "skills"
        assert categories[".github/instructions/python.instructions.md"] == "instructions"

    def test_missing_category_dir_no_error(self, tmp_path: Path) -> None:
        files, by_category = audit.scan_files(tmp_path)
        assert files == []
        assert by_category["shared"]["files"] == 0


class TestModelExtraction:
    def test_extracts_model_from_frontmatter(self, tmp_path: Path) -> None:
        _write(tmp_path / ".github/prompts/x.prompt.md", _frontmatter("Claude Sonnet 4.6"))
        files, _ = audit.scan_files(tmp_path)
        declarations = audit.extract_model_declarations(tmp_path, files)
        assert declarations[0]["model"] == "Claude Sonnet 4.6"

    def test_missing_model_field(self, tmp_path: Path) -> None:
        _write(tmp_path / ".github/prompts/x.prompt.md", _frontmatter(None))
        files, _ = audit.scan_files(tmp_path)
        inventory = audit.build_model_inventory(tmp_path, files)
        assert inventory["missing"][0]["path"] == ".github/prompts/x.prompt.md"

    def test_ordinary_prompt_without_model_uses_model_picker_tier(self, tmp_path: Path) -> None:
        _write(tmp_path / ".github/prompts/cg-plan.prompt.md", _frontmatter(None))
        files, _ = audit.scan_files(tmp_path)
        inventory = audit.build_model_inventory(tmp_path, files)
        declaration = inventory["declarations"][0]
        assert declaration["model"] is None
        assert declaration["model_tier"] == "model-picker"
        assert inventory["missing"] == []
        assert inventory["ordinary_model_picker_violations"] == []

    def test_ordinary_prompt_with_standard_model_is_model_picker_violation(self, tmp_path: Path) -> None:
        _write(tmp_path / ".github/prompts/cg-plan.prompt.md", _frontmatter("Claude Sonnet 4.6"))
        files, _ = audit.scan_files(tmp_path)
        inventory = audit.build_model_inventory(tmp_path, files)
        assert inventory["ordinary_model_picker_violations"][0]["path"] == ".github/prompts/cg-plan.prompt.md"

    def test_ordinary_prompt_with_premium_model_is_model_picker_violation(self, tmp_path: Path) -> None:
        _write(tmp_path / ".github/prompts/cg-plan.prompt.md", _frontmatter("Claude Opus 4.6"))
        files, _ = audit.scan_files(tmp_path)
        inventory = audit.build_model_inventory(tmp_path, files)
        assert inventory["ordinary_model_picker_violations"][0]["model"] == "Claude Opus 4.6"

    def test_tier_classification(self) -> None:
        assert audit.classify_model_tier("Claude Opus 4.6") == "premium"
        assert audit.classify_model_tier("Claude Sonnet 4.6") == "standard"
        assert audit.classify_model_tier("Claude Haiku 4.5") == "economy"


class TestReferenceCounting:
    def test_counts_agent_refs(self) -> None:
        assert audit.count_references("x", "Ask @cg-roadmap for help")["agent_refs"] == 1

    def test_counts_skill_refs(self) -> None:
        assert audit.count_references("x", "Load cg-skill-brain-query")["skill_refs"] == 1

    def test_counts_file_refs(self) -> None:
        assert audit.count_references("x", "Read compound-gpid.md")["file_refs"] == 1

    def test_multiple_refs_summed(self) -> None:
        row = audit.count_references(
            "x",
            "Read compound-gpid.md, dispatch @cg-roadmap, load cg-skill-brain-query, then run_in_terminal.",
        )
        assert row["total_refs"] == 6


class TestDispatchBurden:
    def test_detects_conditional_review_routing(self) -> None:
        row = audit.count_dispatch_burden(
            ".github/prompts/cg-review.prompt.md",
            "Resolve mode with deterministic preflight routing. "
            "Light dispatches @cg-code-quality and @cg-testing. "
            "Data-risk dispatches @cg-data-quality and @cg-reproducibility.",
        )
        assert row["dispatch_refs"] == 4
        assert row["conditional_routing"] is True
        assert row["burden_level"] == "conditional"

    def test_detects_broad_unconditional_review_dispatch(self) -> None:
        row = audit.count_dispatch_burden(
            ".github/prompts/cg-review.prompt.md",
            "Dispatch all standard agents by default: @cg-code-quality @cg-testing "
            "@cg-documentation @cg-version-control @cg-reproducibility "
            "@cg-performance @cg-architecture @cg-data-quality.",
        )
        assert row["dispatch_refs"] == 8
        assert row["conditional_routing"] is False
        assert row["burden_level"] == "broad"


class TestContextLoadingRisks:
    def test_unqualified_context_read_is_risk(self) -> None:
        row = audit.classify_context_loading_line(
            ".github/prompts/x.prompt.md",
            "3. Read `compound-gpid.context.md` for project-specific context.",
        )
        assert row is not None
        assert row["level"] == "risk"
        assert row["artifact"] == "compound-gpid.context.md"

    def test_context_expansion_is_justified(self) -> None:
        row = audit.classify_context_loading_line(
            ".github/prompts/cg-resume.prompt.md",
            "Context expansion: reading full roadmap.json because /cg-resume computes global milestone health.",
        )
        assert row is not None
        assert row["level"] == "justified"

    def test_targeted_brain_topic_read_is_not_risk(self) -> None:
        row = audit.classify_context_loading_line(
            ".github/skills/cg-skill-brain-query/SKILL.md",
            "Open matched `BRAIN-NN.md` topic sections only after selecting a topic.",
        )
        assert row is not None
        assert row["level"] == "targeted"

    def test_unqualified_brain_index_read_is_risk(self) -> None:
        row = audit.classify_context_loading_line(
            ".github/prompts/x.prompt.md",
            "Read `brain-index.json` before planning.",
        )
        assert row is not None
        assert row["level"] == "risk"

    def test_read_and_modify_context_line_is_still_classified(self) -> None:
        row = audit.classify_context_loading_line(
            ".github/prompts/x.prompt.md",
            "Read and modify `compound-gpid.context.md` during enrichment.",
        )
        assert row is not None
        assert row["level"] == "risk"
        assert row["artifact"] == "compound-gpid.context.md"

    def test_build_context_loading_risks_includes_line_numbers(self, tmp_path: Path) -> None:
        _write(
            tmp_path / ".github/prompts/x.prompt.md",
            "Read `compound-gpid.context.md`.\n"
            "Search targeted headings in `compound-gpid.context.md` only.\n",
        )
        files, _ = audit.scan_files(tmp_path)
        rows = audit.build_context_loading_risks(tmp_path, files)
        assert rows[0]["level"] == "risk"
        assert rows[0]["line"] == 1
        assert any(row["level"] == "targeted" for row in rows)


class TestDuplicateDetection:
    BLOCK = "one\ntwo\nthree\nfour\n"

    def test_no_duplicates_under_threshold(self, tmp_path: Path) -> None:
        _write(tmp_path / ".github/prompts/a.prompt.md", self.BLOCK)
        _write(tmp_path / ".github/prompts/b.prompt.md", self.BLOCK)
        files, _ = audit.scan_files(tmp_path)
        assert audit.detect_duplicates(tmp_path, files) == []

    def test_duplicates_at_threshold(self, tmp_path: Path) -> None:
        for name in ("a", "b", "c"):
            _write(tmp_path / f".github/prompts/{name}.prompt.md", self.BLOCK)
        files, _ = audit.scan_files(tmp_path)
        duplicates = audit.detect_duplicates(tmp_path, files)
        assert duplicates[0]["file_count"] == 3

    def test_short_blocks_ignored(self, tmp_path: Path) -> None:
        for name in ("a", "b", "c", "d", "e"):
            _write(tmp_path / f".github/prompts/{name}.prompt.md", "one\ntwo\nthree\n")
        files, _ = audit.scan_files(tmp_path)
        assert audit.detect_duplicates(tmp_path, files) == []


class TestThresholdClassification:
    def _classify_one(self, record: dict, refs: int = 0, model: dict | None = None) -> dict:
        matrix = [{"path": record["path"], "total_refs": refs}]
        inventory = {"declarations": [model] if model else [], "missing": [], "drift": [], "premium_usage": []}
        return audit.classify_optimization_candidates([record], matrix, inventory, [])

    def test_large_instruction_immediate(self) -> None:
        result = self._classify_one({
            "path": ".github/instructions/python.instructions.md",
            "category": "instructions",
            "characters": 7000,
            "estimated_tokens": 1750,
        })
        assert result["immediate"]

    def test_medium_prompt_needs_review(self) -> None:
        result = self._classify_one({
            "path": ".github/prompts/x.prompt.md",
            "category": "prompts",
            "characters": 6000,
            "estimated_tokens": 1500,  # at THRESHOLD_PROMPT_REVIEW
        })
        assert result["needs_review"]

    def test_small_file_acceptable(self) -> None:
        result = self._classify_one({
            "path": ".github/prompts/x.prompt.md",
            "category": "prompts",
            "characters": 2000,
            "estimated_tokens": 500,
        })
        assert result["acceptable_count"] == 1

    def test_high_refs_needs_review(self) -> None:
        result = self._classify_one({
            "path": ".github/prompts/x.prompt.md",
            "category": "prompts",
            "characters": 100,
            "estimated_tokens": 25,
        }, refs=6)
        assert result["needs_review"]
        assert result["immediate"] == []

    def test_high_refs_with_large_prompt_immediate(self) -> None:
        result = self._classify_one({
            "path": ".github/prompts/x.prompt.md",
            "category": "prompts",
            "characters": 12000,
            "estimated_tokens": 3000,
        }, refs=6)
        assert result["immediate"]

    def test_premium_no_escalation_immediate(self) -> None:
        model = {
            "path": ".github/prompts/x.prompt.md",
            "category": "prompts",
            "model": "Claude Opus 4.6",
            "model_tier": "premium",
            "has_escalation_condition": False,
        }
        result = self._classify_one({
            "path": ".github/prompts/x.prompt.md",
            "category": "prompts",
            "characters": 100,
            "estimated_tokens": 25,
        }, model=model)
        assert result["immediate"]

    def test_model_picker_prompt_not_flagged_as_missing_model(self) -> None:
        model = {
            "path": ".github/prompts/cg-plan.prompt.md",
            "category": "prompts",
            "model": None,
            "model_tier": "model-picker",
            "has_escalation_condition": False,
        }
        result = self._classify_one({
            "path": ".github/prompts/cg-plan.prompt.md",
            "category": "prompts",
            "characters": 100,
            "estimated_tokens": 25,
        }, refs=6, model=model)
        assert result["immediate"] == []
        assert result["needs_review"][0]["reason"] == "reference count >= 5"

    def test_ordinary_prompt_model_picker_violation_is_immediate(self) -> None:
        model = {
            "path": ".github/prompts/cg-plan.prompt.md",
            "category": "prompts",
            "model": "Claude Sonnet 4.6",
            "model_tier": "standard",
            "has_escalation_condition": False,
        }
        record = {
            "path": ".github/prompts/cg-plan.prompt.md",
            "category": "prompts",
            "characters": 100,
            "estimated_tokens": 25,
        }
        matrix = [{"path": record["path"], "total_refs": 0}]
        inventory = {
            "declarations": [model],
            "missing": [],
            "drift": [],
            "premium_usage": [],
            "ordinary_model_picker_violations": [model],
        }
        result = audit.classify_optimization_candidates([record], matrix, inventory, [])
        assert result["immediate"]
        assert "ordinary prompt hard-codes model" in result["immediate"][0]["reason"]


class TestOutputFormats:
    def test_json_output_valid(self, tmp_path: Path) -> None:
        report = {
            "generated": "2026-06-04T00:00:00",
            "disclaimer": audit.DISCLAIMER,
            "summary": {"total_files": 0, "total_characters": 0, "total_estimated_tokens": 0, "by_category": {}},
            "files": [],
            "reference_matrix": [],
            "model_inventory": {"declarations": [], "missing": [], "drift": [], "premium_usage": []},
            "duplicates": [],
            "optimization_candidates": {"immediate": [], "needs_review": [], "acceptable_count": 0},
        }
        paths = audit.write_outputs(report, tmp_path, "json")
        payload = json.loads(paths[0].read_text(encoding="utf-8"))
        assert {"generated", "summary", "files", "model_inventory"} <= set(payload)

    def test_markdown_output_has_sections(self) -> None:
        markdown = audit.render_markdown({
            "generated": "2026-06-04T00:00:00",
            "disclaimer": audit.DISCLAIMER,
            "summary": {"total_files": 0, "total_characters": 0, "total_estimated_tokens": 0, "by_category": {}},
            "files": [],
            "reference_matrix": [],
            "dispatch_burden": [],
            "model_inventory": {"declarations": [], "missing": [], "drift": [], "premium_usage": []},
            "context_loading_risks": [],
            "duplicates": [],
            "optimization_candidates": {"immediate": [], "needs_review": [], "acceptable_count": 0},
        })
        assert "## Summary" in markdown
        assert "## Prompt Reference Matrix" in markdown
        assert "## Review Dispatch Burden" in markdown
        assert "## Context Loading Risks" in markdown
        assert "## Model Inventory" in markdown

    def test_disclaimer_present(self, tmp_path: Path) -> None:
        report = audit.build_report(Path(__file__).resolve().parents[2])
        paths = audit.write_outputs(report, tmp_path, "both")
        assert audit.DISCLAIMER in paths[0].read_text(encoding="utf-8")
        assert audit.DISCLAIMER in paths[1].read_text(encoding="utf-8")


class TestIntegration:
    @pytest.mark.integration
    def test_full_run_on_real_repo(self, tmp_path: Path) -> None:
        root = Path(__file__).resolve().parents[2]
        assert audit.main(["--root", str(root), "--output-dir", str(tmp_path), "--format", "json"]) == 0
        payload = json.loads((tmp_path / "context-audit.json").read_text(encoding="utf-8"))
        assert payload["summary"]["total_files"] > 0


# ---------------------------------------------------------------------------
# P2.16 — parse_model_guide() tests
# ---------------------------------------------------------------------------

class TestModelGuideParser:
    def test_missing_file_returns_empty(self, tmp_path: Path) -> None:
        result = audit.parse_model_guide(tmp_path / "no-guide.md")
        assert result == {}

    def test_valid_prompts_table_parsed(self, tmp_path: Path) -> None:
        guide_md = (
            "# Model Guide\n\n"
            "### Prompts\n\n"
            "| File | Model |\n"
            "| --- | --- |\n"
            "| cg-review.prompt.md | Claude Sonnet 4.6 (copilot) |\n"
        )
        _write(tmp_path / "docs" / "model-guide.md", guide_md)
        result = audit.parse_model_guide(tmp_path / "docs" / "model-guide.md")
        assert result.get("cg-review.prompt.md") == "Claude Sonnet 4.6 (copilot)"

    def test_separator_rows_ignored(self, tmp_path: Path) -> None:
        guide_md = (
            "### Prompts\n\n"
            "| File | Model |\n"
            "| --- | --- |\n"
            "| :--- | :--- |\n"
            "| ------ | ------ |\n"
            "| cg-plan.prompt.md | Claude Haiku 4.5 |\n"
        )
        _write(tmp_path / "docs" / "model-guide.md", guide_md)
        result = audit.parse_model_guide(tmp_path / "docs" / "model-guide.md")
        assert "---" not in result
        assert ":---" not in result
        assert result.get("cg-plan.prompt.md") == "Claude Haiku 4.5"

    def test_agents_section_also_parsed(self, tmp_path: Path) -> None:
        guide_md = (
            "### Agents\n\n"
            "| File | Model |\n"
            "| --- | --- |\n"
            "| cg-code-quality.agent.md | Claude Haiku 4.5 |\n"
        )
        _write(tmp_path / "docs" / "model-guide.md", guide_md)
        result = audit.parse_model_guide(tmp_path / "docs" / "model-guide.md")
        assert result.get("cg-code-quality.agent.md") == "Claude Haiku 4.5"


# ---------------------------------------------------------------------------
# P2.17 — main() exit codes 1 and 2
# ---------------------------------------------------------------------------

class TestMainCLI:
    def test_invalid_root_exit_code_2(self, tmp_path: Path) -> None:
        # tmp_path has no .github/prompts/ — should return 2
        result = audit.main(["--root", str(tmp_path)])
        assert result == 2

    def test_oserror_exit_code_1(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        root = Path(__file__).resolve().parents[2]
        monkeypatch.setattr(audit, "build_report", lambda r: (_ for _ in ()).throw(OSError("simulated")))
        result = audit.main(["--root", str(root), "--output-dir", str(tmp_path), "--format", "json"])
        assert result == 1


# ---------------------------------------------------------------------------
# P2.18 — normalize_model_name() tests
# ---------------------------------------------------------------------------

class TestNormalizeModelName:
    def test_strips_copilot_suffix(self) -> None:
        assert audit.normalize_model_name("Claude Sonnet 4.6 (copilot)") == "Claude Sonnet 4.6"

    def test_strips_capitalized_copilot(self) -> None:
        assert audit.normalize_model_name("Claude Haiku 4.5 (Copilot)") == "Claude Haiku 4.5"

    def test_none_returns_empty_string(self) -> None:
        assert audit.normalize_model_name(None) == ""

    def test_no_suffix_passthrough(self) -> None:
        assert audit.normalize_model_name("Claude Sonnet 4.6") == "Claude Sonnet 4.6"


# ---------------------------------------------------------------------------
# P2.19 — _has_broad_tools() and broad-tools classification
# ---------------------------------------------------------------------------

class TestBroadTools:
    def test_none_is_false(self) -> None:
        assert audit._has_broad_tools(None) is False

    def test_list_with_edit_is_true(self) -> None:
        assert audit._has_broad_tools(["read", "edit_file"]) is True

    def test_list_without_edit_is_false(self) -> None:
        assert audit._has_broad_tools(["read", "search"]) is False

    def test_wildcard_string_is_true(self) -> None:
        assert audit._has_broad_tools("*") is True

    def test_premium_agent_with_broad_tools_immediate(self) -> None:
        record = {
            "path": ".github/agents/x.agent.md",
            "category": "agents",
            "characters": 100,
            "estimated_tokens": 25,
        }
        model = {
            "path": ".github/agents/x.agent.md",
            "category": "agents",
            "model": "Claude Opus 4.6",
            "model_tier": "premium",
            "has_escalation_condition": False,
            "tools": ["edit_file", "run_in_terminal"],
        }
        matrix = [{"path": record["path"], "total_refs": 0}]
        inventory = {"declarations": [model], "missing": [], "drift": [], "premium_usage": [model]}
        result = audit.classify_optimization_candidates([record], matrix, inventory, [])
        assert result["immediate"]
        reasons = result["immediate"][0]["reason"]
        assert "broad tools" in reasons


# ---------------------------------------------------------------------------
# P2.20 — duplicate-block escalation path
# ---------------------------------------------------------------------------

class TestDuplicateEscalation:
    def test_duplicate_above_threshold_immediate(self) -> None:
        dup = {"file_count": 4, "estimated_tokens": 1200, "files": ["a.md", "b.md", "c.md", "d.md"]}
        result = audit.classify_optimization_candidates([], [], {"declarations": [], "missing": [], "drift": [], "premium_usage": []}, [dup])
        assert any(e["category"] == "duplicates" for e in result["immediate"])

    def test_duplicate_below_token_threshold_not_immediate(self) -> None:
        dup = {"file_count": 4, "estimated_tokens": 500, "files": ["a.md", "b.md", "c.md", "d.md"]}
        result = audit.classify_optimization_candidates([], [], {"declarations": [], "missing": [], "drift": [], "premium_usage": []}, [dup])
        assert not any(e["category"] == "duplicates" for e in result["immediate"])


# ---------------------------------------------------------------------------
# P2.21 — model-guide drift classification path
# ---------------------------------------------------------------------------

class TestDriftClassification:
    def test_drift_path_flagged_as_needs_review(self) -> None:
        record = {
            "path": ".github/prompts/x.prompt.md",
            "category": "prompts",
            "characters": 100,
            "estimated_tokens": 25,
        }
        model_decl = {
            "path": ".github/prompts/x.prompt.md",
            "category": "prompts",
            "model": "Claude Haiku 4.5",
            "model_tier": "economy",
            "has_escalation_condition": False,
        }
        drift_entry = {
            "path": ".github/prompts/x.prompt.md",
            "frontmatter_model": "Claude Haiku 4.5",
            "model_guide_model": "Claude Sonnet 4.6",
        }
        matrix = [{"path": record["path"], "total_refs": 0}]
        inventory = {"declarations": [model_decl], "missing": [], "drift": [drift_entry], "premium_usage": []}
        result = audit.classify_optimization_candidates([record], matrix, inventory, [])
        assert result["needs_review"]
        assert "model guide drift" in result["needs_review"][0]["reason"]


# ---------------------------------------------------------------------------
# P2.22 — count_dispatch_burden "limited" and "none" levels
# ---------------------------------------------------------------------------

class TestDispatchBurdenLevels:
    def test_limited_burden(self) -> None:
        # 3 agent refs, no routing keywords, no broad dispatch keyword
        row = audit.count_dispatch_burden(
            "x.prompt.md",
            "@cg-code-quality @cg-testing @cg-documentation help with the task.",
        )
        assert row["burden_level"] == "limited"
        assert row["dispatch_refs"] == 3

    def test_none_burden(self) -> None:
        row = audit.count_dispatch_burden("x.prompt.md", "No agent references here.")
        assert row["burden_level"] == "none"
        assert row["dispatch_refs"] == 0


# ---------------------------------------------------------------------------
# P2.23 — write_outputs(fmt="md") path
# ---------------------------------------------------------------------------

class TestMdOutput:
    def test_md_output_written(self, tmp_path: Path) -> None:
        report = {
            "generated": "2026-06-06T00:00:00",
            "disclaimer": audit.DISCLAIMER,
            "summary": {"total_files": 0, "total_characters": 0, "total_estimated_tokens": 0, "by_category": {}},
            "files": [],
            "reference_matrix": [],
            "dispatch_burden": [],
            "model_inventory": {"declarations": [], "missing": [], "drift": [], "premium_usage": []},
            "context_loading_risks": [],
            "duplicates": [],
            "optimization_candidates": {"immediate": [], "needs_review": [], "acceptable_count": 0},
        }
        paths = audit.write_outputs(report, tmp_path, "md")
        assert len(paths) == 1
        assert paths[0].name == "context-audit.md"
        assert "## Summary" in paths[0].read_text(encoding="utf-8")
