"""Tests for budgeted Knowledge Brain query."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

import cg_index
from brain.query import (
    QueryOptions,
    query_brain,
    query_from_args,
    render_query_json,
    render_query_markdown,
)


def _write(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def _solution(title: str, body: str, *, status: str = "active", tags: str = "testing") -> str:
    return f"---\ntitle: \"{title}\"\ndate: 2026-06-01\nstatus: {status}\ntags: [{tags}]\n---\n\n{body}\n"


def _plan(title: str, body: str, *, status: str = "completed") -> str:
    return f"---\ntitle: \"{title}\"\ndate: 2026-06-02\nstatus: {status}\ntags: [token-efficiency, plan]\n---\n\n{body}\n"


def _fixture_root(tmp_path: Path) -> Path:
    _write(
        tmp_path / ".cg-docs/solutions/testing-patterns/pester-safe-runner.md",
        _solution(
            "Canonical safe runner for Pester",
            "Use tests/Run-Tests.ps1 and tests/last-run.json for Pester validation. "
            "Avoid direct Invoke-Pester pipelines and keep output bounded.",
            tags="pester, powershell, testing",
        ),
    )
    _write(
        tmp_path / ".cg-docs/plans/workflow-token-baseline.md",
        _plan(
            "Workflow Token Baseline",
            "The token baseline plan extends scripts/cg_audit_context.py and creates .cg-docs/token/workflow-costs.csv.",
        ),
    )
    _write(
        tmp_path / ".cg-docs/brainstorms/old-token-idea.md",
        _solution(
            "Abandoned token idea",
            "Deprecated token idea that conflicts with the current workflow token baseline approach.",
            status="abandoned",
            tags="token, obsolete",
        ),
    )
    _write(
        tmp_path / "roadmap.json",
        json.dumps({
            "schemaVersion": "compound-gpid-roadmap-v1",
            "milestones": [
                {
                    "id": "token-efficiency-core-system",
                    "title": "Token Efficiency Core System",
                    "objective": "Make context loading budgeted.",
                    "status": "planned",
                    "features": [
                        {
                            "id": "phase-1-2-knowledge-brain-query",
                            "title": "Knowledge Brain query and budgeted retrieval",
                            "status": "planned",
                            "plan": ".cg-docs/plans/workflow-token-baseline.md",
                        }
                    ],
                }
            ],
        }),
    )
    return tmp_path


class TestQueryBrain:
    def test_selects_relevant_artifacts_for_query(self, tmp_path: Path) -> None:
        root = _fixture_root(tmp_path)

        payload = query_brain(root, QueryOptions(intent="review", query="Pester safe runner", budget_tokens=600))

        assert payload["schema_version"] == 1
        assert payload["selected"]
        assert payload["selected"][0]["path"] == ".cg-docs/solutions/testing-patterns/pester-safe-runner.md"
        assert "Pester" in payload["selected"][0]["title"]
        assert payload["estimated_tokens"] <= payload["budget_tokens"]

    def test_changed_file_hints_boost_related_artifacts(self, tmp_path: Path) -> None:
        root = _fixture_root(tmp_path)

        payload = query_brain(
            root,
            QueryOptions(
                intent="work",
                query="token baseline",
                changed_files=("scripts/cg_audit_context.py",),
                budget_tokens=600,
            ),
        )

        top = payload["selected"][0]
        assert top["path"] == ".cg-docs/plans/workflow-token-baseline.md"
        assert any("changed-file" in reason for reason in top["why_selected"])

    def test_low_budget_still_returns_bounded_path_context(self, tmp_path: Path) -> None:
        root = _fixture_root(tmp_path)

        payload = query_brain(root, QueryOptions(intent="plan", query="token", budget_tokens=300))

        assert payload["selected"]
        assert payload["estimated_tokens"] <= payload["budget_tokens"]
        assert all(len(item["snippet"]) <= 360 for item in payload["selected"])

    def test_stale_candidates_are_flagged(self, tmp_path: Path) -> None:
        root = _fixture_root(tmp_path)

        payload = query_brain(root, QueryOptions(intent="brainstorm", query="abandoned deprecated token", budget_tokens=600))

        assert any(item["stale"] for item in payload["selected"])
        assert any("stale" in warning.lower() for warning in payload["warnings"])

    def test_missing_cg_docs_errors(self, tmp_path: Path) -> None:
        with pytest.raises(ValueError, match=".cg-docs"):
            query_brain(tmp_path, QueryOptions(intent="plan", query="anything"))

    def test_invalid_intent_errors(self, tmp_path: Path) -> None:
        root = _fixture_root(tmp_path)
        with pytest.raises(ValueError, match="invalid intent"):
            query_brain(root, QueryOptions(intent="invalid", query="anything"))

    def test_too_small_budget_errors(self, tmp_path: Path) -> None:
        root = _fixture_root(tmp_path)
        with pytest.raises(ValueError, match="budget"):
            query_brain(root, QueryOptions(intent="plan", query="anything", budget_tokens=10))


class TestQueryRendering:
    def test_json_renderer_is_stable_and_parseable(self, tmp_path: Path) -> None:
        payload = query_brain(_fixture_root(tmp_path), QueryOptions(intent="plan", query="token baseline"))

        rendered = render_query_json(payload)
        parsed = json.loads(rendered)

        assert parsed["schema_version"] == 1
        assert parsed["selected"]

    def test_markdown_renderer_contains_paths_without_full_bodies(self, tmp_path: Path) -> None:
        payload = query_brain(_fixture_root(tmp_path), QueryOptions(intent="review", query="Pester safe runner"))

        rendered = render_query_markdown(payload)

        assert "# Knowledge Brain Query" in rendered
        assert ".cg-docs/solutions/testing-patterns/pester-safe-runner.md" in rendered
        assert "Avoid direct Invoke-Pester pipelines" in rendered
        assert len(rendered) < 3000

    def test_query_from_args_renders_json_and_markdown(self, tmp_path: Path) -> None:
        root = _fixture_root(tmp_path)

        as_json = query_from_args(root, intent="plan", query="token baseline", output_format="json")
        as_md = query_from_args(root, intent="plan", query="token baseline", output_format="md")

        assert json.loads(as_json)["intent"] == "plan"
        assert as_md.startswith("# Knowledge Brain Query")

    def test_query_from_args_rejects_unknown_format(self, tmp_path: Path) -> None:
        root = _fixture_root(tmp_path)
        with pytest.raises(ValueError, match="format"):
            query_from_args(root, intent="plan", query="token baseline", output_format="yaml")


class TestCgIndexQueryCli:
    def test_query_cli_outputs_json(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        root = _fixture_root(tmp_path)

        result = cg_index.main([
            "query",
            "--root",
            str(root),
            "--intent",
            "plan",
            "--query",
            "token baseline",
            "--budget",
            "600",
            "--format",
            "json",
        ])

        captured = capsys.readouterr()
        assert result == 0
        payload = json.loads(captured.out)
        assert payload["intent"] == "plan"
        assert payload["selected"]
        assert captured.err == ""

    def test_query_cli_rejects_invalid_budget(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        root = _fixture_root(tmp_path)

        result = cg_index.main([
            "query",
            "--root",
            str(root),
            "--intent",
            "plan",
            "--query",
            "token baseline",
            "--budget",
            "10",
        ])

        captured = capsys.readouterr()
        assert result == 1
        assert "budget" in captured.err.lower()

    def test_existing_version_mode_still_works(self, capsys: pytest.CaptureFixture[str]) -> None:
        with pytest.raises(SystemExit) as exc:
            cg_index.main(["--version"])

        captured = capsys.readouterr()
        assert exc.value.code == 0
        assert "cg-index" in captured.out
