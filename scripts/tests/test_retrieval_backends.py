"""Tests for optional retrieval backend evaluation registry."""
from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = REPO_ROOT / ".github/shared/retrieval-backends.json"
DOC_PATH = REPO_ROOT / "docs/retrieval-backends.md"

REQUIRED_GATES = {
    "explicit_opt_in",
    "privacy_review",
    "offline_behavior",
    "dependency_review",
    "token_budget_comparison",
    "deterministic_validation",
    "rollback_plan",
}


def _registry() -> dict:
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


def test_registry_shape_and_current_backend() -> None:
    registry = _registry()

    assert registry["schema_version"] == 1
    assert registry["current_backend"] == "native-brain-query"
    assert registry["policy"]["default_runtime"] == "native-brain-query"
    assert registry["policy"]["optional_backends_default_enabled"] is False
    assert registry["policy"]["evaluation_only"] is True
    assert REQUIRED_GATES.issubset(set(registry["required_gates"]))


def test_only_native_brain_query_is_current_and_enabled() -> None:
    registry = _registry()
    current = [backend for backend in registry["backends"] if backend["status"] == "current"]
    enabled = [backend for backend in registry["backends"] if backend["default_enabled"]]

    assert [backend["id"] for backend in current] == ["native-brain-query"]
    assert [backend["id"] for backend in enabled] == ["native-brain-query"]
    assert current[0]["network_required"] is False
    assert current[0]["dependencies"] == "stdlib-only"


def test_optional_backends_are_opt_in_and_default_disabled() -> None:
    registry = _registry()

    for backend in registry["backends"]:
        if backend["id"] == registry["current_backend"]:
            continue
        assert backend["status"] in {"evaluate-only", "deferred"}
        assert backend["default_enabled"] is False
        assert backend["requires_explicit_opt_in"] is True
        assert set(backend["gates"]).issubset(REQUIRED_GATES)
        assert "token_budget_comparison" in backend["gates"]
        assert "deterministic_validation" in backend["gates"]


def test_external_backend_is_deferred_and_not_enabled() -> None:
    registry = _registry()
    external = [backend for backend in registry["backends"] if backend["kind"] == "external"]

    assert external, "expected at least one external candidate for explicit deferral"
    for backend in external:
        assert backend["status"] == "deferred"
        assert backend["network_required"] is True
        assert backend["default_enabled"] is False
        assert "privacy_review" in backend["gates"]
        assert "offline_behavior" in backend["gates"]


def test_docs_explain_evaluation_not_runtime_configuration() -> None:
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "evaluation artifact, not runtime configuration" in content
    assert "Phase 2.2 does not enable a new backend" in content
    assert "default_enabled: false" in content
    assert "requires_explicit_opt_in: true" in content
    assert "No external retrieval backend is approved" in content
