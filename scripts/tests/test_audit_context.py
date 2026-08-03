"""Tests for cg_audit_context.

Run from repo root:
    python -m pytest scripts/tests/test_audit_context.py -v
"""
from __future__ import annotations

import csv
import io
import json
import os
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

    def test_generated_views_are_excluded_even_from_broad_category_glob(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        sentinel = "VIEW_ONLY_SENTINEL_7E5C9A"
        _write(tmp_path / ".cg-docs/views/plans/view.html", f"<p>{sentinel}</p>")
        _write(tmp_path / ".cg-docs/plans/canonical.md", "# Canonical\n")
        monkeypatch.setattr(audit, "SCAN_CATEGORIES", {"all": ".cg-docs/**/*"})

        files, totals = audit.scan_files(tmp_path)
        duplicates = audit.detect_duplicates(tmp_path, files)

        assert [row["path"] for row in files] == [".cg-docs/plans/canonical.md"]
        assert totals["all"]["files"] == 1
        assert sentinel not in json.dumps(files)
        assert sentinel not in json.dumps(duplicates)

    def test_generic_document_views_are_excluded_from_broad_context_glob(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        sentinel = "GENERIC_VIEW_ONLY_SENTINEL_3A9D"
        _write(
            tmp_path / ".cg-docs/views/documents/docs/guide.html",
            f"<p>{sentinel}</p>",
        )
        monkeypatch.setattr(audit, "SCAN_CATEGORIES", {"all": ".cg-docs/**/*"})

        files, _ = audit.scan_files(tmp_path)
        duplicates = audit.detect_duplicates(tmp_path, files)

        assert sentinel not in json.dumps(files)
        assert sentinel not in json.dumps(duplicates)

    def test_view_path_exclusion_is_component_scoped(self) -> None:
        assert audit.is_model_context_excluded(".cg-docs/views/plans/a.html") is True
        assert audit.is_model_context_excluded(".cg-docs/views-archive/a.md") is False

    @pytest.mark.usefixtures("require_symlink_support")
    def test_symlink_alias_to_view_is_excluded_from_broad_glob(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        sentinel = "VIEW_ALIAS_SENTINEL_A91D"
        view = _write(
            tmp_path / ".cg-docs/views/plans/view.html",
            f"<p>{sentinel}</p>",
        )
        alias = tmp_path / ".cg-docs/plans/leak.md"
        alias.parent.mkdir(parents=True)
        alias.symlink_to(view)
        monkeypatch.setattr(audit, "SCAN_CATEGORIES", {"all": ".cg-docs/**/*"})

        files, _ = audit.scan_files(tmp_path)

        assert files == []
        assert sentinel not in json.dumps(files)

    def test_hardlink_alias_to_view_is_excluded_from_broad_glob(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        view = _write(tmp_path / ".cg-docs/views/plans/view.html", "view-secret")
        alias = tmp_path / ".cg-docs/plans/leak.md"
        alias.parent.mkdir(parents=True)
        os.link(view, alias)
        monkeypatch.setattr(audit, "SCAN_CATEGORIES", {"all": ".cg-docs/**/*"})

        files, _ = audit.scan_files(tmp_path)

        assert files == []


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
        assert inventory["declarations"][0]["model"] is None
        assert inventory["declarations"][0]["execution_metadata"] is False
        assert inventory["forbidden_execution_metadata"] == []

    def test_ordinary_prompt_without_model_inherits_platform_selection(self, tmp_path: Path) -> None:
        _write(tmp_path / ".github/prompts/cg-plan.prompt.md", _frontmatter(None))
        files, _ = audit.scan_files(tmp_path)
        inventory = audit.build_model_inventory(tmp_path, files)
        declaration = inventory["declarations"][0]
        assert declaration["model"] is None
        assert declaration["execution_metadata"] is False
        assert inventory["forbidden_execution_metadata"] == []

    def test_ordinary_prompt_with_standard_model_is_model_picker_violation(self, tmp_path: Path) -> None:
        _write(tmp_path / ".github/prompts/cg-plan.prompt.md", _frontmatter("Claude Sonnet 4.6"))
        files, _ = audit.scan_files(tmp_path)
        inventory = audit.build_model_inventory(tmp_path, files)
        assert inventory["forbidden_execution_metadata"][0]["path"] == ".github/prompts/cg-plan.prompt.md"

    def test_ordinary_prompt_with_premium_model_is_forbidden_metadata(self, tmp_path: Path) -> None:
        _write(tmp_path / ".github/prompts/cg-plan.prompt.md", _frontmatter("Claude Opus 4.6"))
        files, _ = audit.scan_files(tmp_path)
        inventory = audit.build_model_inventory(tmp_path, files)
        assert inventory["forbidden_execution_metadata"][0]["model"] == "Claude Opus 4.6"

    def test_explicit_null_model_is_forbidden_metadata(self, tmp_path: Path) -> None:
        _write(tmp_path / ".github/prompts/cg-plan.prompt.md", "---\ndescription: Test\nmodel: null\n---\n\nBody\n")
        files, _ = audit.scan_files(tmp_path)
        inventory = audit.build_model_inventory(tmp_path, files)
        declaration = inventory["declarations"][0]
        assert declaration["model"] is None
        assert declaration["execution_metadata"] is True
        assert inventory["forbidden_execution_metadata"]

class TestAdvisoryValidation:
    def test_production_advisory_contract_is_valid(self) -> None:
        result = audit.validate_advisory_examples(Path(__file__).resolve().parents[2])
        assert result["valid"] is True
        assert result["stage_count"] == 5
        assert result["example_count"] >= 5

    def test_executable_advisory_key_is_rejected(self, tmp_path: Path) -> None:
        _write(tmp_path / ".github/shared/model-advisory.contract.md", "user makes the final selection\navailability can differ by platform and date\nRuntime catalog introspection is intentionally deferred\nmust never be translated into prompt or agent frontmatter\n")
        _write(tmp_path / ".github/shared/model-advisory-examples.json", json.dumps({
            "schemaVersion": 1,
            "effortLabels": ["low", "medium", "high", "xhigh", "max"],
            "source": {"observedDate": "2026-07-31", "availabilityStatus": "availability-unverified"},
            "stages": {"planning": {"capabilityProfile": ["planning"], "rationale": "r", "strongOption": {"effort": "high", "exampleRefs": []}, "userControl": "user chooses"}},
            "examples": [{"id": "x", "name": "Example", "vendor": "x", "family": "x", "capabilityTags": ["x"], "platforms": ["x"], "observedDate": "2026-07-31", "availabilityStatus": "availability-unverified", "verificationStatus": "not verified", "model": "must not be executable"}],
        }))
        result = audit.validate_advisory_examples(tmp_path)
        assert result["valid"] is False
        assert any("executable advisory metadata" in error for error in result["errors"])

    def test_local_advisory_block_falls_back_when_malformed(self, tmp_path: Path) -> None:
        _write(tmp_path / "compound-gpid.local.md", "model-advisory:\n  enabled: true\n  model: forbidden\n")
        errors = audit.validate_local_advisory_config(tmp_path)
        assert any("executable advisory key" in error for error in errors)

    def test_empty_advisory_bundle_is_invalid(self, tmp_path: Path) -> None:
        _write(tmp_path / ".github/shared/model-advisory.contract.md", "user makes the final selection\navailability can differ by platform and date\nRuntime catalog introspection is intentionally deferred\nmust never be translated into prompt or agent frontmatter\n")
        _write(tmp_path / ".github/shared/model-advisory-examples.json", "{}\n")
        result = audit.validate_advisory_examples(tmp_path)
        assert result["valid"] is False
        assert any("missing schemaVersion" in error for error in result["errors"])

    def test_malformed_advisory_source_is_invalid_not_an_exception(self, tmp_path: Path) -> None:
        _write(tmp_path / ".github/shared/model-advisory.contract.md", "user makes the final selection\navailability can differ by platform and date\nRuntime catalog introspection is intentionally deferred\nmust never be translated into prompt or agent frontmatter\n")
        _write(tmp_path / ".github/shared/model-advisory-examples.json", json.dumps({
            "schemaVersion": 1,
            "source": [],
            "effortLabels": ["low", "medium", "high", "xhigh", "max"],
            "stages": {},
            "examples": [],
        }))
        result = audit.validate_advisory_examples(tmp_path)
        assert result["valid"] is False
        assert any("source must be an object" in error for error in result["errors"])

    def test_local_advisory_invalid_effort_and_example_are_reported(self, tmp_path: Path) -> None:
        _write(tmp_path / "compound-gpid.local.md", "model-advisory:\n  enabled: true\n  examples:\n    strong: unknown-example\n    effort: turbo\n")
        _write(tmp_path / ".github/shared/model-advisory-examples.json", json.dumps({
            "examples": [{"id": "known-example"}],
        }))
        errors = audit.validate_local_advisory_config(tmp_path)
        assert any("unsupported advisory effort" in error for error in errors)
        assert any("unknown advisory example" in error for error in errors)


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
    def test_malformed_local_advisory_is_a_warning_with_fallback(self, tmp_path: Path) -> None:
        report = {
            "model_inventory": {
                "advisory": {
                    "errors": ["compound-gpid.local.md line 3 uses unsupported advisory effort: turbo"],
                    "examples_path": ".github/shared/model-advisory-examples.json",
                }
            }
        }
        guardrails = audit.build_guardrails(tmp_path, report)
        local_failures = [item for item in guardrails["failures"] if item["path"] == "compound-gpid.local.md"]
        local_warnings = [item for item in guardrails["warnings"] if item["path"] == "compound-gpid.local.md"]
        assert local_failures == []
        assert len(local_warnings) == 1

    def test_local_executable_advisory_key_remains_a_failure(self, tmp_path: Path) -> None:
        report = {
            "model_inventory": {
                "advisory": {
                    "errors": ["compound-gpid.local.md line 3 contains executable advisory key"],
                    "examples_path": ".github/shared/model-advisory-examples.json",
                }
            }
        }
        guardrails = audit.build_guardrails(tmp_path, report)
        local_warnings = [item for item in guardrails["warnings"] if item["path"] == "compound-gpid.local.md"]
        local_failures = [item for item in guardrails["failures"] if item["path"] == "compound-gpid.local.md"]
        assert local_warnings == []
        assert len(local_failures) == 1

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
        assert "## Model Inheritance And Advisory Contract" in markdown

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
# P2.18 — duplicate-block escalation path
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
# P2.19 — count_dispatch_burden "limited" and "none" levels
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
        assert cg_plan["execution_metadata"] is False
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
        dashboard = (token_dir / "TOKEN-DASHBOARD.md").read_text(encoding="utf-8")
        assert "Token Dashboard" in dashboard
        assert "Regression Status" in dashboard
        regression = json.loads((token_dir / "regression-check.json").read_text(encoding="utf-8"))
        assert regression["schema_version"] == 1
        assert f"Status: `{regression['status']}`" in dashboard
        assert regression["comparison"]["status"] in {"not_supplied", "available"}

    def test_main_writes_token_artifacts_by_default(self, tmp_path: Path) -> None:
        root = tmp_path / "project"
        _write(root / ".github/prompts/cg-token-audit.prompt.md", _frontmatter("Claude Haiku 4.5"))
        output_dir = tmp_path / "legacy-cost"

        result = audit.main(["--root", str(root), "--output-dir", str(output_dir), "--format", "json"])

        assert result == 0
        assert (output_dir / "context-audit.json").exists()
        assert (root / ".cg-docs/token/TOKEN-BUDGET.md").exists()
        assert (root / ".cg-docs/token/TOKEN-DASHBOARD.md").exists()
        assert (root / ".cg-docs/token/token-audit.json").exists()
        assert (root / ".cg-docs/token/regression-check.json").exists()

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
                "model_governance": {"forbidden_execution_metadata_count": 0, "advisory_error_count": 0},
            }
        }
        baseline = {
            "benchmark": {
                "workflows": [
                    {"workflow": "/cg-plan", "path": ".github/prompts/cg-plan.prompt.md", "estimated_tokens": 125, "total_refs": 6, "context_risk_count": 3, "dispatch_refs": 0, "dispatch_burden": "none"},
                ],
                "model_governance": {"forbidden_execution_metadata_count": 1, "advisory_error_count": 1},
            }
        }
        comparison = audit.compare_benchmark_to_baseline(current, baseline)
        row = comparison["workflows"][0]
        assert row["estimated_tokens_delta"] == -25
        assert row["total_refs_delta"] == -2
        assert row["context_risk_count_delta"] == -2
        assert comparison["model_governance"]["forbidden_execution_metadata_count_delta"] == -1
        assert comparison["model_governance"]["advisory_error_count_delta"] == -1

    def test_token_regression_check_status_baseline_without_comparison(self) -> None:
        report = {
            "generated": "2026-06-23T00:00:00",
            "guardrails": {"failures": [], "warnings": []},
            "benchmark": {"workflows": []},
        }

        regression = audit.build_token_regression_check(report)

        assert regression["status"] == "baseline"
        assert regression["comparison"]["status"] == "not_supplied"
        assert "No baseline comparison" in regression["status_reason"]

    def test_token_regression_check_status_pass_with_comparison(self) -> None:
        report = {
            "generated": "2026-06-23T00:00:00",
            "guardrails": {"failures": [], "warnings": []},
            "benchmark": {
                "workflows": [],
                "comparison": {
                    "workflows": [{"workflow": "/cg-plan", "estimated_tokens_delta": 0}],
                    "model_governance": {},
                },
            },
        }

        regression = audit.build_token_regression_check(report)

        assert regression["status"] == "pass"
        assert regression["comparison"]["status"] == "available"

    def test_token_regression_check_status_fail_for_guardrail_failure(self) -> None:
        report = {
            "generated": "2026-06-23T00:00:00",
            "guardrails": {
                "failures": [{"path": ".github/prompts/cg-work.prompt.md", "reason": "high-frequency prompt estimated tokens > 6000"}],
                "warnings": [],
            },
            "benchmark": {
                "workflows": [
                    {
                        "workflow": "/cg-work",
                        "path": ".github/prompts/cg-work.prompt.md",
                        "estimated_tokens": audit.THRESHOLD_HIGH_FREQ_PROMPT_FAIL + 1,
                    }
                ],
                "comparison": {"workflows": [{"workflow": "/cg-work"}]},
            },
        }

        regression = audit.build_token_regression_check(report)

        assert regression["status"] == "fail"
        assert regression["workflow_budget"][0]["status"] == "fail"
        assert regression["failures"][0]["path"] == ".github/prompts/cg-work.prompt.md"

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
        audit.scan_files(tmp_path)
        report = audit.build_report(tmp_path)
        guardrails = report["guardrails"]
        reasons = " ".join(row["reason"] for row in guardrails["failures"])
        assert "executable model metadata" in reasons
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
