"""Tests for cg_audit_context.

Run from repo root:
    python -m pytest scripts/tests/test_audit_context.py -v
"""
from __future__ import annotations

import csv
import io
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
        assert audit.classify_model_tier("Experimental Local Model") == "unknown"

    def test_catalog_enriches_vendor_role_and_preferred_model(self, tmp_path: Path) -> None:
        _write(tmp_path / ".github/prompts/x.prompt.md", _frontmatter("Claude Sonnet 4.6"))
        _write(
            tmp_path / audit.MODEL_CATALOG_PATH,
            json.dumps({
                "models": [
                    {
                        "name": "Claude Sonnet 4.6",
                        "vendor": "anthropic",
                        "family": "Claude",
                        "tier": "standard",
                        "policyStatus": "fallback",
                    },
                    {
                        "name": "GPT-5.3-Codex",
                        "vendor": "openai",
                        "family": "GPT-5-Codex",
                        "tier": "standard",
                        "policyStatus": "preferred",
                    },
                ],
                "frontmatterSupport": [
                    {"model": "Claude Sonnet 4.6", "status": "frontmatter-supported"},
                    {"model": "GPT-5.3-Codex", "status": "not-tested"},
                ],
                "assignments": [
                    {
                        "path": ".github/prompts/x.prompt.md",
                        "role": "coding",
                        "preferredModel": "GPT-5.3-Codex",
                        "frontmatterMode": "explicit",
                        "rationale": "coding test",
                    }
                ],
            }),
        )
        files, _ = audit.scan_files(tmp_path)
        inventory = audit.build_model_inventory(tmp_path, files)
        declaration = inventory["declarations"][0]
        assert declaration["vendor"] == "anthropic"
        assert declaration["role"] == "coding"
        assert declaration["preferred_model"] == "GPT-5.3-Codex"
        assert inventory["openai_first_violations"][0]["path"] == ".github/prompts/x.prompt.md"
        assert inventory["frontmatter_support_gaps"][0]["preferred_model_support"] == "not-tested"

    def test_missing_catalog_assignment_is_reported(self, tmp_path: Path) -> None:
        _write(tmp_path / ".github/prompts/x.prompt.md", _frontmatter("GPT-5.3-Codex"))
        _write(
            tmp_path / audit.MODEL_CATALOG_PATH,
            json.dumps({
                "models": [
                    {
                        "name": "GPT-5.3-Codex",
                        "vendor": "openai",
                        "family": "GPT-5-Codex",
                        "tier": "standard",
                        "policyStatus": "preferred",
                    }
                ],
                "frontmatterSupport": [{"model": "GPT-5.3-Codex", "status": "frontmatter-supported"}],
                "assignments": [],
            }),
        )
        files, _ = audit.scan_files(tmp_path)
        inventory = audit.build_model_inventory(tmp_path, files)
        assert inventory["missing_catalog_assignments"][0]["path"] == ".github/prompts/x.prompt.md"

    def test_haiku_non_mechanical_role_is_violation(self, tmp_path: Path) -> None:
        _write(tmp_path / ".github/agents/x.agent.md", _frontmatter("Claude Haiku 4.5"))
        _write(
            tmp_path / audit.MODEL_CATALOG_PATH,
            json.dumps({
                "models": [
                    {
                        "name": "Claude Haiku 4.5",
                        "vendor": "anthropic",
                        "family": "Claude",
                        "tier": "economy",
                        "policyStatus": "mechanical-only",
                    }
                ],
                "frontmatterSupport": [{"model": "Claude Haiku 4.5", "status": "frontmatter-supported"}],
                "assignments": [
                    {
                        "path": ".github/agents/x.agent.md",
                        "role": "review",
                        "preferredModel": "GPT-5.3-Codex",
                        "frontmatterMode": "explicit",
                    }
                ],
            }),
        )
        files, _ = audit.scan_files(tmp_path)
        inventory = audit.build_model_inventory(tmp_path, files)
        assert inventory["haiku_role_violations"][0]["path"] == ".github/agents/x.agent.md"


class TestReferenceCounting:
    def test_counts_agent_refs(self) -> None:
        assert audit.count_references("x", "Ask @cg-roadmap for help")["agent_refs"] == 1

    def test_counts_skill_refs(self) -> None:
        assert audit.count_references("x", "Load cg-skill-brain-query")["skill_refs"] == 1

    def test_counts_file_refs(self) -> None:
        assert audit.count_references("x", "Read compound-gpid.md")["file_refs"] == 1

    def test_counts_tool_refs(self) -> None:
        assert audit.count_references("x", "Use run_in_terminal for checks")["tool_refs"] == 1

    def test_counts_load_verbs(self) -> None:
        assert audit.count_references("x", "Read the prompt and load the skill")["load_verbs"] == 1

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

    def test_context_expansion_for_docs_directory_is_justified(self) -> None:
        row = audit.classify_context_loading_line(
            ".github/agents/cg-release-scanner.agent.md",
            "Context expansion: reading `.cg-docs/` filenames only because release notes need dated evidence.",
        )
        assert row is not None
        assert row["level"] == "justified"
        assert row["artifact"] == ".cg-docs/"

    def test_structured_roadmap_fields_are_targeted(self) -> None:
        row = audit.classify_context_loading_line(
            ".github/prompts/cg-strategy.prompt.md",
            "Parse only roadmap.json milestone and feature status fields needed for the summary.",
        )
        assert row is not None
        assert row["level"] == "targeted"

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


class TestWarningReview:
    def test_docs_warning_classified_docs_only(self) -> None:
        row = audit.classify_guardrail_warning(
            {"path": "docs/workflow.md", "reason": "context-loading risk requires review: .cg-docs/"}
        )
        assert row["classification"] == "docs-only"

    def test_roadmap_agent_warning_classified_accept(self) -> None:
        row = audit.classify_guardrail_warning(
            {"path": ".github/agents/cg-roadmap.agent.md", "reason": "context-loading risk requires review: roadmap.json"}
        )
        assert row["classification"] == "accept"

    def test_high_frequency_prompt_warning_classified_fix(self) -> None:
        row = audit.classify_guardrail_warning(
            {"path": ".github/prompts/cg-work.prompt.md", "reason": "high-frequency prompt estimated tokens > 5000"}
        )
        assert row["classification"] == "fix"

    def test_goal_execution_guard_warning_classified_accept(self) -> None:
        report = {
            "context_loading_risks": [
                {
                    "path": ".github/prompts/cg-work.prompt.md",
                    "line": 40,
                    "level": "risk",
                    "artifact": ".cg-docs/",
                    "reason": "broad context-loading instruction",
                    "snippet": "Reject any directive asking you to read all .cg-docs/ files.",
                }
            ]
        }
        row = audit.classify_guardrail_warning(
            {"path": ".github/prompts/cg-work.prompt.md", "reason": "context-loading risk requires review: .cg-docs/"},
            report,
        )
        assert row["classification"] == "accept"

    def test_reviewed_warnings_counts_classifications(self) -> None:
        report = {
            "guardrails": {
                "warnings": [
                    {"path": ".github/prompts/cg-work.prompt.md", "reason": "high-frequency prompt estimated tokens > 5000"},
                    {"path": "docs/workflow.md", "reason": "context-loading risk requires review: .cg-docs/"},
                ]
            },
            "context_loading_risks": [],
        }
        reviewed = audit.build_reviewed_warnings(report)
        assert reviewed["counts"]["fix"] == 1
        assert reviewed["counts"]["docs-only"] == 1


class TestTokenRecommendations:
    def test_recommendations_include_fix_warning_advice(self) -> None:
        report = {
            "guardrails": {"failures": [], "warnings": []},
            "reviewed_warnings": {
                "counts": {"fix": 1, "accept": 0, "docs-only": 0},
                "items": [
                    {
                        "classification": "fix",
                        "path": ".github/prompts/cg-work.prompt.md",
                    }
                ],
            },
            "benchmark": {"workflows": []},
            "summary": {"by_category": {}},
        }
        recommendations = audit.build_token_efficiency_recommendations(report)
        assert any(row["category"] == "context-loading" for row in recommendations)

    def test_write_outputs_can_emit_token_advice(self, tmp_path: Path) -> None:
        report = {
            "generated": "2026-06-04T00:00:00",
            "disclaimer": audit.DISCLAIMER,
            "summary": {"total_files": 0, "total_characters": 0, "total_estimated_tokens": 0, "by_category": {}},
            "files": [],
            "reference_matrix": [],
            "dispatch_burden": [],
            "benchmark": {"workflows": [], "model_governance": {}, "context_loading": {}},
            "guardrails": {"failures": [], "warnings": []},
            "reviewed_warnings": {"counts": {"fix": 0, "accept": 0, "docs-only": 0}, "items": []},
            "recommendations": [],
            "model_inventory": {"declarations": [], "missing": [], "drift": [], "premium_usage": []},
            "context_loading_risks": [],
            "duplicates": [],
            "optimization_candidates": {"immediate": [], "needs_review": [], "acceptable_count": 0},
        }
        paths = audit.write_outputs(report, tmp_path, "json", recommendations=True)
        assert tmp_path / "token-advice.md" in paths
        assert (tmp_path / "token-advice.md").exists()


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
        assert audit.main([
            "--root",
            str(root),
            "--output-dir",
            str(tmp_path),
            "--token-output-dir",
            str(tmp_path / "token"),
            "--format",
            "json",
        ]) == 0
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

    def test_assignment_rows_parse_role_and_rationale(self, tmp_path: Path) -> None:
        guide_md = (
            "### Prompts\n\n"
            "| File | Model | Role | Rationale |\n"
            "| --- | --- | --- | --- |\n"
            "| cg-work.prompt.md | GPT-5.3-Codex | coding | Implementation workflow |\n"
        )
        _write(tmp_path / "docs" / "model-guide.md", guide_md)
        result = audit.parse_model_guide_assignments(tmp_path / "docs" / "model-guide.md")
        row = result["cg-work.prompt.md"]
        assert row["model"] == "GPT-5.3-Codex"
        assert row["role"] == "coding"
        assert row["rationale"] == "Implementation workflow"

    def test_inherited_model_picker_guide_row_does_not_drift(self, tmp_path: Path) -> None:
        _write(tmp_path / ".github/prompts/cg-plan.prompt.md", _frontmatter(None))
        _write(
            tmp_path / audit.MODEL_CATALOG_PATH,
            json.dumps({
                "models": [],
                "frontmatterSupport": [],
                "assignments": [
                    {
                        "path": ".github/prompts/cg-plan.prompt.md",
                        "role": "inherited",
                        "preferredModel": None,
                        "frontmatterMode": "inherited",
                    }
                ],
            }),
        )
        guide_md = (
            "### Prompts\n\n"
            "| File | Model | Role | Rationale |\n"
            "| --- | --- | --- | --- |\n"
            "| cg-plan.prompt.md | Copilot model picker | inherited | Planning inherits the user's chosen model. |\n"
        )
        _write(tmp_path / "docs" / "model-guide.md", guide_md)
        files, _ = audit.scan_files(tmp_path)
        inventory = audit.build_model_inventory(tmp_path, files)
        assert inventory["drift"] == []


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

    def test_recommendations_cli_uses_supplied_root(self, tmp_path: Path) -> None:
        project = tmp_path / "consumer-project"
        _write(project / ".github/prompts/x.prompt.md", _frontmatter())
        result = audit.main([
            "--root",
            str(project),
            "--output-dir",
            str(tmp_path / "out"),
            "--format",
            "json",
            "--recommendations",
        ])
        assert result == 0
        payload = json.loads((tmp_path / "out" / "context-audit.json").read_text(encoding="utf-8"))
        assert payload["files"][0]["path"] == ".github/prompts/x.prompt.md"
        assert (tmp_path / "out" / "token-advice.md").exists()


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
        dup = {"file_count": 4, "total_redundant_tokens": 1200, "files": ["a.md", "b.md", "c.md", "d.md"]}
        result = audit.classify_optimization_candidates([], [], {"declarations": [], "missing": [], "drift": [], "premium_usage": []}, [dup])
        assert any(e["category"] == "duplicates" for e in result["immediate"])

    def test_duplicate_below_token_threshold_not_immediate(self) -> None:
        dup = {"file_count": 4, "total_redundant_tokens": 500, "files": ["a.md", "b.md", "c.md", "d.md"]}
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


class TestPhase6Benchmark:
    def test_workflow_registry_covers_phase_1_1_commands(self) -> None:
        commands = [row["workflow"] for row in audit.WORKFLOW_REGISTRY]
        workflow_ids = [row["workflow_id"] for row in audit.WORKFLOW_REGISTRY]
        assert commands == [
            "/cg-brainstorm",
            "/cg-plan",
            "/cg-work",
            "/cg-review",
            "/cg-fix-triage",
            "/cg-compound",
            "/cg-resume",
            "/cg-diagnose",
            "/cg-token-audit",
        ]
        assert len(workflow_ids) == len(set(workflow_ids))

    def test_duplicate_workflow_ids_fail_registry_validation(self) -> None:
        registry = [
            {"workflow_id": "cg-plan", "workflow": "/cg-plan", "path": ".github/prompts/cg-plan.prompt.md"},
            {"workflow_id": "cg-plan", "workflow": "/cg-work", "path": ".github/prompts/cg-work.prompt.md"},
        ]
        with pytest.raises(ValueError, match="Duplicate workflow_id"):
            audit.validate_workflow_registry(registry)

    def test_builds_workflow_benchmark_rows(self, tmp_path: Path) -> None:
        _write(tmp_path / ".github/prompts/cg-plan.prompt.md", _frontmatter(None) + "Context expansion: reading `roadmap.json` because targeted fields.\n")
        _write(tmp_path / ".github/prompts/cg-work.prompt.md", _frontmatter() + "review:auto review:manual review:none route-aware staged mode @cg-code-quality\n")
        _write(tmp_path / ".github/prompts/cg-review.prompt.md", _frontmatter() + "explicit user mode wins. Auto risk-class routing applies only when no explicit mode. full thorough mode:verify light-only @cg-testing\n")
        _write(tmp_path / ".github/prompts/cg-compound.prompt.md", _frontmatter() + "cg-index --brain rebuild BRAIN.md\n")
        _write(tmp_path / ".github/prompts/cg-resume.prompt.md", _frontmatter("Claude Haiku 4.5") + "Context expansion: reading full roadmap.json because /cg-resume computes global milestone health.\n")
        _write(tmp_path / ".github/skills/cg-skill-brain-query/SKILL.md", "query-first matched topic BRAIN.md BRAIN-NN.md brain-index.json tooling may query\n")
        files, _ = audit.scan_files(tmp_path)
        report = {
            "files": files,
            "reference_matrix": audit.build_reference_matrix(tmp_path, files),
            "dispatch_burden": audit.build_dispatch_burden(tmp_path, files),
            "model_inventory": audit.build_model_inventory(tmp_path, files),
            "context_loading_risks": audit.build_context_loading_risks(tmp_path, files),
        }
        benchmark = audit.build_benchmark_summary(tmp_path, report)
        names = {row["workflow"] for row in benchmark["workflows"]}
        assert {
            "/cg-brainstorm",
            "/cg-plan",
            "/cg-work",
            "/cg-review",
            "/cg-fix-triage",
            "/cg-compound",
            "/cg-resume",
            "/cg-diagnose",
            "/cg-token-audit",
            "Knowledge Brain/context lookup",
        } <= names
        cg_plan = next(row for row in benchmark["workflows"] if row["workflow"] == "/cg-plan")
        assert cg_plan["model_tier"] == "model-picker"
        brain = next(row for row in benchmark["workflows"] if row["workflow"] == "Knowledge Brain/context lookup")
        assert brain["query_first"] is True

    def test_workflow_telemetry_marks_missing_prompts_unavailable(self, tmp_path: Path) -> None:
        _write(tmp_path / ".github/prompts/cg-plan.prompt.md", _frontmatter(None))
        report = audit.build_report(tmp_path)
        telemetry = report["workflow_telemetry"]
        missing = next(row for row in telemetry["workflows"] if row["workflow"] == "/cg-token-audit")
        assert missing["available"] is False
        assert missing["characters"] is None
        assert missing["estimated_tokens"] is None
        assert missing["observability"]["estimated_token_pressure"]["status"] == "not_observed"

    def test_workflow_telemetry_observability_statuses_are_explicit(self, tmp_path: Path) -> None:
        _write(
            tmp_path / ".github/prompts/cg-token-audit.prompt.md",
            _frontmatter(None)
            + "Read compound-gpid.md, load cg-skill-brain-query, dispatch @cg-roadmap, then use run_in_terminal.\n",
        )
        report = audit.build_report(tmp_path)
        row = next(item for item in report["workflow_telemetry"]["workflows"] if item["workflow"] == "/cg-token-audit")
        assert row["file_references"] == ["compound-gpid.md"]
        assert row["likely_file_reads"] == ["compound-gpid.md"]
        assert row["skill_references"] == ["cg-skill-brain-query"]
        assert row["likely_skill_loads"] == ["cg-skill-brain-query"]
        assert row["agent_references"] == ["@cg-roadmap"]
        assert row["tool_references"] == ["run_in_terminal"]
        assert row["observability"]["files_read"]["status"] == "partially_observed"
        assert row["observability"]["skills_loaded"]["status"] == "partially_observed"
        assert row["observability"]["agents_dispatched"]["status"] == "partially_observed"
        assert row["observability"]["command_output_size"]["status"] == "not_observed"
        assert row["observability"]["summary_size"]["status"] == "not_observed"

    def test_workflow_telemetry_extracts_shared_paths_and_execution_subagent(self, tmp_path: Path) -> None:
        _write(
            tmp_path / ".github/prompts/cg-work.prompt.md",
            _frontmatter(None)
            + "Load `.github/shared/context-loading.contract.md` before Step 1.\n"
            + "Load `.github/shared/goal-execution.contract.md` for the contract.\n"
            + "Read `.github/shared/review-routing.contract.md` for review routing.\n"
            + "Use execution_subagent to run `. tests\\Run-Tests.ps1` safely.\n",
        )
        report = audit.build_report(tmp_path)
        row = next(item for item in report["workflow_telemetry"]["workflows"] if item["workflow"] == "/cg-work")
        assert ".github/shared/context-loading.contract.md" in row["file_references"]
        assert ".github/shared/goal-execution.contract.md" in row["file_references"]
        assert ".github/shared/review-routing.contract.md" in row["file_references"]
        assert "tests/Run-Tests.ps1" in row["file_references"]
        assert ".github/shared/context-loading.contract.md" in row["likely_file_reads"]
        assert ".github/shared/review-routing.contract.md" in row["likely_file_reads"]
        assert "execution_subagent" in row["tool_references"]
        assert row["tool_refs"] == 1

    def test_workflow_telemetry_tracks_generated_report_reads_without_scanning_outputs(self, tmp_path: Path) -> None:
        _write(
            tmp_path / ".github/prompts/cg-token-audit.prompt.md",
            _frontmatter("Claude Haiku 4.5")
            + "Read `.cg-docs/cost/token-advice.md` and `.cg-docs/token/TOKEN-BUDGET.md`.\n",
        )
        _write(tmp_path / ".cg-docs/cost/token-advice.md", "Generated advice")
        _write(tmp_path / ".cg-docs/token/TOKEN-BUDGET.md", "Generated budget")

        report = audit.build_report(tmp_path)

        row = next(item for item in report["workflow_telemetry"]["workflows"] if item["workflow"] == "/cg-token-audit")
        assert ".cg-docs/cost/token-advice.md" in row["file_references"]
        assert ".cg-docs/token/TOKEN-BUDGET.md" in row["file_references"]
        assert ".cg-docs/cost/token-advice.md" in row["likely_file_reads"]
        assert ".cg-docs/token/TOKEN-BUDGET.md" in row["likely_file_reads"]
        scanned_paths = {item["path"] for item in report["files"]}
        assert ".cg-docs/cost/token-advice.md" not in scanned_paths
        assert ".cg-docs/token/TOKEN-BUDGET.md" not in scanned_paths

    def test_token_artifacts_are_written_with_expected_shapes(self, tmp_path: Path) -> None:
        _write(
            tmp_path / ".github/prompts/cg-token-audit.prompt.md",
            _frontmatter("Claude Haiku 4.5")
            + "Read `.github/shared/context-loading.contract.md` and run_in_terminal.\n",
        )
        report = audit.build_report(tmp_path)
        token_dir = tmp_path / ".cg-docs/token"

        paths = audit.write_token_artifacts(report, token_dir)

        assert {path.name for path in paths} == set(audit.TOKEN_ARTIFACT_FILENAMES)
        token_payload = json.loads((token_dir / "token-audit.json").read_text(encoding="utf-8"))
        assert token_payload["schema_version"] == 1
        assert len(token_payload["workflow_telemetry"]["workflows"]) == 9

        context_payload = json.loads((token_dir / "context-map.json").read_text(encoding="utf-8"))
        assert context_payload["schema_version"] == 1
        assert len(context_payload["workflows"]) == 9
        token_audit_context = next(
            row for row in context_payload["workflows"] if row["workflow"] == "/cg-token-audit"
        )
        assert ".github/shared/context-loading.contract.md" in token_audit_context["file_references"]
        assert "run_in_terminal" in token_audit_context["tool_references"]

        cost_rows = list(csv.DictReader(io.StringIO((token_dir / "workflow-costs.csv").read_text(encoding="utf-8"))))
        assert len(cost_rows) == 9
        token_audit_cost = next(row for row in cost_rows if row["workflow"] == "/cg-token-audit")
        assert token_audit_cost["command_output_status"] == "not_observed"
        assert token_audit_cost["summary_output_status"] == "not_observed"

        budget = (token_dir / "TOKEN-BUDGET.md").read_text(encoding="utf-8")
        assert "not evidence of token savings" in budget
        assert "not_observed" in budget
        warnings = (token_dir / "large-context-warnings.md").read_text(encoding="utf-8")
        assert "Large Context Warnings" in warnings

    def test_main_writes_token_artifacts_by_default(self, tmp_path: Path) -> None:
        root = tmp_path / "project"
        _write(root / ".github/prompts/cg-token-audit.prompt.md", _frontmatter("Claude Haiku 4.5"))
        output_dir = tmp_path / "legacy-cost"

        result = audit.main(["--root", str(root), "--output-dir", str(output_dir), "--format", "json"])

        assert result == 0
        assert (output_dir / "context-audit.json").exists()
        assert (root / ".cg-docs/token/TOKEN-BUDGET.md").exists()
        assert (root / ".cg-docs/token/token-audit.json").exists()

    def test_main_can_disable_token_artifacts_for_legacy_run(self, tmp_path: Path) -> None:
        root = tmp_path / "project"
        _write(root / ".github/prompts/cg-token-audit.prompt.md", _frontmatter("Claude Haiku 4.5"))
        output_dir = tmp_path / "legacy-cost"
        token_dir = root / ".cg-docs/token"

        result = audit.main([
            "--root",
            str(root),
            "--output-dir",
            str(output_dir),
            "--format",
            "json",
            "--no-token-artifacts",
        ])

        assert result == 0
        assert (output_dir / "context-audit.json").exists()
        for filename in audit.TOKEN_ARTIFACT_FILENAMES:
            assert not (token_dir / filename).exists()
        assert not token_dir.exists()

    def test_workflow_observability_schema_requires_status(self) -> None:
        observability = audit.workflow_observability(True)
        del observability["summary_size"]["status"]
        with pytest.raises(ValueError, match="summary_size"):
            audit.validate_observability_matrix(observability)

    def test_baseline_comparison_reports_deltas(self) -> None:
        current = {
            "benchmark": {
                "workflows": [
                    {"workflow": "/cg-plan", "path": ".github/prompts/cg-plan.prompt.md", "estimated_tokens": 100, "total_refs": 4, "context_risk_count": 1, "dispatch_refs": 0, "dispatch_burden": "none"},
                ],
                "model_governance": {"premium_usage_count": 0, "ordinary_model_picker_violations": 0},
            }
        }
        baseline = {
            "benchmark": {
                "workflows": [
                    {"workflow": "/cg-plan", "path": ".github/prompts/cg-plan.prompt.md", "estimated_tokens": 125, "total_refs": 6, "context_risk_count": 3, "dispatch_refs": 0, "dispatch_burden": "none"},
                ],
                "model_governance": {"premium_usage_count": 1, "ordinary_model_picker_violations": 1},
            }
        }
        comparison = audit.compare_benchmark_to_baseline(current, baseline)
        row = comparison["workflows"][0]
        assert row["estimated_tokens_delta"] == -25
        assert row["total_refs_delta"] == -2
        assert row["context_risk_count_delta"] == -2
        assert comparison["model_governance"]["premium_usage_count_delta"] == -1

    def test_malformed_baseline_returns_exit_code_1(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        root = Path(__file__).resolve().parents[2]
        bad = tmp_path / "bad.json"
        bad.write_text("{not-json", encoding="utf-8")
        result = audit.main(["--root", str(root), "--output-dir", str(tmp_path), "--format", "json", "--baseline", str(bad)])
        captured = capsys.readouterr()
        assert result == 1
        assert "baseline" in captured.err.lower()


class TestPhase6Guardrails:
    def test_guardrails_fail_for_ordinary_model_and_broad_prompt_read(self, tmp_path: Path) -> None:
        _write(tmp_path / ".github/prompts/cg-plan.prompt.md", _frontmatter("Claude Opus 4.6") + "Read `brain-index.json` before planning.\n")
        _write(tmp_path / ".github/prompts/cg-work.prompt.md", _frontmatter() + "review:auto review:manual review:none no agent dispatch route-aware review-routing.contract.md\n")
        _write(tmp_path / ".github/prompts/cg-review.prompt.md", _frontmatter() + "explicit user mode wins. Auto risk-class routing applies only when no explicit mode. full thorough mode:verify light-only\n")
        _write(tmp_path / ".github/shared/review-routing.contract.md", "- `light` | `@cg-code-quality`, `@cg-testing`\n- `full` | all `standard` agents plus `@cg-learnings-researcher` and `@cg-adversarial`\n")
        files, _ = audit.scan_files(tmp_path)
        report = audit.build_report(tmp_path)
        guardrails = report["guardrails"]
        reasons = " ".join(row["reason"] for row in guardrails["failures"])
        assert "ordinary prompt hard-codes model" in reasons
        assert "broad context-loading" in reasons

    def test_guardrails_validate_review_route_counts(self, tmp_path: Path) -> None:
        _write(tmp_path / ".github/prompts/cg-plan.prompt.md", _frontmatter(None))
        _write(tmp_path / ".github/prompts/cg-work.prompt.md", _frontmatter() + "review:auto review:manual review:none default and review:manual must never dispatch review agents automatically. review:auto route-aware agent dispatch using review-routing.contract.md\n")
        _write(tmp_path / ".github/prompts/cg-review.prompt.md", _frontmatter() + "explicit user mode wins. Auto risk-class routing applies only when no explicit mode. Users can explicitly request full review. thorough maps to full. mode:verify light-only.\n")
        _write(
            tmp_path / ".github/shared/review-routing.contract.md",
            "| `light` | `@cg-code-quality`, `@cg-testing` |\n"
            "| `standard` | `@cg-code-quality`, `@cg-testing`, `@cg-documentation`, `@cg-version-control`, `@cg-reproducibility`, `@cg-performance`, `@cg-architecture`, `@cg-data-quality` |\n"
            "| `data-risk` | all `standard` agents, with mandatory emphasis on `@cg-data-quality` and `@cg-reproducibility` |\n"
            "| `architecture` | all `standard` agents, with mandatory emphasis on `@cg-architecture` and `@cg-performance` |\n"
            "| `full` | all `standard` agents plus `@cg-learnings-researcher` and `@cg-adversarial` |\n",
        )
        report = audit.build_report(tmp_path)
        failures = [row for row in report["guardrails"]["failures"] if "review route agent counts" in row["reason"]]
        assert failures == []

    def test_markdown_output_includes_phase6_sections(self) -> None:
        markdown = audit.render_markdown({
            "generated": "2026-06-08T00:00:00",
            "disclaimer": audit.DISCLAIMER,
            "summary": {"total_files": 0, "total_characters": 0, "total_estimated_tokens": 0, "by_category": {}},
            "files": [],
            "reference_matrix": [],
            "dispatch_burden": [],
            "benchmark": {"workflows": [], "model_governance": {}, "context_loading": {}, "review_agent_counts": {}, "comparison": None},
            "guardrails": {"failures": [], "warnings": []},
            "model_inventory": {"declarations": [], "missing": [], "drift": [], "premium_usage": [], "ordinary_model_picker_violations": []},
            "context_loading_risks": [],
            "duplicates": [],
            "optimization_candidates": {"immediate": [], "needs_review": [], "acceptable_count": 0},
        })
        assert "## Benchmark Summary" in markdown
        assert "## Guardrails" in markdown
        assert "## Release-Readiness Checklist" in markdown
