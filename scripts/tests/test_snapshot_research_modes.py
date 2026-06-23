"""Tests for snapshot and external-research mode registry."""
from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = REPO_ROOT / ".github/shared/snapshot-research-modes.json"
DOC_PATH = REPO_ROOT / "docs/snapshot-external-research.md"

REQUIRED_GATES = {
    "explicit_opt_in",
    "source_attribution",
    "privacy_review",
    "copyright_safe_summary",
    "reproducibility_note",
    "token_budget_review",
    "rollback_plan",
}


def _registry() -> dict:
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


def test_registry_shape_and_current_mode() -> None:
    registry = _registry()

    assert registry["schema_version"] == 1
    assert registry["current_mode"] == "local-workflow"
    assert registry["policy"]["default_mode"] == "local-workflow"
    assert registry["policy"]["evaluation_only"] is True
    assert registry["policy"]["non_local_modes_default_enabled"] is False
    assert registry["policy"]["no_external_action_without_explicit_user_request"] is True
    assert REQUIRED_GATES.issubset(set(registry["required_gates"]))


def test_only_local_workflow_is_current_and_enabled() -> None:
    registry = _registry()
    current = [mode for mode in registry["modes"] if mode["status"] == "current"]
    enabled = [mode for mode in registry["modes"] if mode["default_enabled"]]

    assert [mode["id"] for mode in current] == ["local-workflow"]
    assert [mode["id"] for mode in enabled] == ["local-workflow"]
    assert current[0]["network_required"] is False


def test_snapshot_and_external_modes_are_opt_in_and_disabled() -> None:
    registry = _registry()

    for mode in registry["modes"]:
        if mode["id"] == registry["current_mode"]:
            continue
        assert mode["status"] in {"evaluate-only", "deferred"}
        assert mode["default_enabled"] is False
        assert mode["requires_explicit_opt_in"] is True
        assert set(mode["gates"]).issubset(REQUIRED_GATES)
        assert "token_budget_review" in mode["gates"]
        assert "rollback_plan" in mode["gates"]


def test_external_research_mode_is_deferred_and_gated() -> None:
    registry = _registry()
    external = [mode for mode in registry["modes"] if mode["kind"] == "external"]

    assert external, "expected explicit external research candidate"
    for mode in external:
        assert mode["status"] == "deferred"
        assert mode["network_required"] is True
        assert mode["default_enabled"] is False
        assert "source_attribution" in mode["gates"]
        assert "copyright_safe_summary" in mode["gates"]
        assert "privacy_review" in mode["gates"]


def test_docs_explain_no_runtime_implementation() -> None:
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "evaluation artifact, not runtime configuration" in content
    assert "Phase 2.3 does not implement snapshot capture" in content
    assert "web search execution" in content
    assert "external source fetching" in content
    assert "runtime mode switching" in content
