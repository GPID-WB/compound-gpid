"""Tests for cg_audit_context.

Run from repo root:
    python -m pytest scripts/tests/test_audit_context.py -v
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import pytest

import cg_audit_context as audit


def _write(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def _frontmatter(model: Optional[str] = "Claude Sonnet 4.6") -> str:
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
            "characters": 4000,
            "estimated_tokens": 1000,
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

    def test_high_refs_immediate(self) -> None:
        result = self._classify_one({
            "path": ".github/prompts/x.prompt.md",
            "category": "prompts",
            "characters": 100,
            "estimated_tokens": 25,
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
            "model_inventory": {"declarations": [], "missing": [], "drift": [], "premium_usage": []},
            "duplicates": [],
            "optimization_candidates": {"immediate": [], "needs_review": [], "acceptable_count": 0},
        })
        assert "## Summary" in markdown
        assert "## Prompt Reference Matrix" in markdown
        assert "## Model Inventory" in markdown

    def test_disclaimer_present(self, tmp_path: Path) -> None:
        report = audit.build_report(Path.cwd())
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
