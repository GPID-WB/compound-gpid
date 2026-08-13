"""Created 2026-08-13. Tests for offline optional retrieval profile governance."""
from __future__ import annotations

from pathlib import Path

import pytest

from research_evidence.retrieval.dense import rank_dense
from research_evidence.retrieval.profiles import (
    ProfileUnavailableError,
    RetrievalProfile,
    RetrievalProfileRegistry,
    evaluate_profile_budget,
    load_local_profile,
)
from research_evidence.retrieval.rerank import rerank_candidates
from research_evidence.retrieval.sparse import rank_sparse
from research_evidence.identity import make_source_unit_id, text_fingerprint
from research_evidence.schemas import SourceUnit, TypedLocator


def _profile(**overrides: object) -> RetrievalProfile:
    """Build a complete candidate local retrieval profile for tests."""
    values: dict[str, object] = {
        "id": "local-dense-candidate",
        "kind": "dense",
        "model_id": "local/example-model",
        "model_revision": "rev-1",
        "package_version": "mock-runtime-1.0",
        "distribution_source": "https://example.org/model",
        "model_cache_path": "models/example",
        "sha256": "a" * 64,
        "license_or_access_terms": "Apache-2.0",
        "restriction": "",
        "setup_network_required": True,
        "runtime_network_required": False,
        "telemetry_notes": "No telemetry known.",
        "platform_support": ["macos", "windows", "linux"],
        "hardware_support": ["cpu"],
        "deterministic": True,
        "query_p95_budget_ms": 5_000.0,
        "memory_budget_bytes": 4_000_000_000,
        "enterprise_review_status": "unreviewed",
        "selection_rationale": "Optional local semantic retrieval evaluation.",
        "caveat_disclaimer": "Candidate only; lexical retrieval remains the default.",
        "activation_status": "candidate",
        "activation_acknowledged": False,
    }
    values.update(overrides)
    return RetrievalProfile.model_validate(values)


def _units() -> list[SourceUnit]:
    """Build deterministic units for ranking tests."""
    units: list[SourceUnit] = []
    for block, text in enumerate(["alpha", "beta", "gamma"], start=1):
        fingerprint = text_fingerprint(text)
        locator = TypedLocator(kind="markdown_block", block=block, unit_fingerprint=fingerprint)
        units.append(
            SourceUnit(
                source_unit_id=make_source_unit_id("v1", locator, fingerprint),
                source_version_id="v1",
                locator=locator,
                text=text,
            )
        )
    return units


def test_candidate_profile_is_not_selectable() -> None:
    """Keep optional profiles inventory-visible but inactive by default."""
    registry = RetrievalProfileRegistry(entries=[_profile()])
    with pytest.raises(ProfileUnavailableError, match="candidate"):
        registry.selectable("local-dense-candidate", Path("."))


def test_enabled_profile_requires_existing_local_cache(tmp_path: Path) -> None:
    """Fail clearly when a selected local model cache is absent."""
    profile = _profile(activation_status="enabled-local")
    registry = RetrievalProfileRegistry(entries=[profile])
    with pytest.raises(ProfileUnavailableError, match="cache"):
        registry.selectable("local-dense-candidate", tmp_path)


def test_local_loader_forces_cache_only_and_never_downloads(tmp_path: Path) -> None:
    """Pass local cache settings to an adapter without exposing network fallback."""
    cache = tmp_path / "models" / "example"
    cache.mkdir(parents=True)
    profile = _profile(activation_status="enabled-local")
    registry = RetrievalProfileRegistry(entries=[profile])
    calls: list[dict[str, object]] = []

    def loader(**kwargs: object) -> object:
        """Capture loader kwargs without loading a model."""
        calls.append(kwargs)
        return object()

    loaded = load_local_profile(registry, "local-dense-candidate", tmp_path, loader)

    assert loaded is not None
    assert calls[0]["local_files_only"] is True
    assert calls[0]["revision"] == "rev-1"
    assert "download" not in calls[0]


def test_profile_budget_failure_keeps_profile_candidate() -> None:
    """Do not promote an optional profile when declared latency/memory budgets fail."""
    profile = _profile(activation_status="enabled-with-caveat", activation_acknowledged=True)
    evaluation = evaluate_profile_budget(
        profile,
        {"p95_query_ms": 6_000.0, "memory_bytes": 4_000_000_001},
    )
    assert evaluation.passed is False
    assert evaluation.resulting_activation_status == "candidate"


def test_dense_sparse_and_rerank_ordering_is_deterministic() -> None:
    """Sort equal-score optional results by source-unit ID for repeatability."""
    units = _units()
    scores = {unit.source_unit_id: 0.5 for unit in units}
    dense = rank_dense(units, scores)
    sparse = rank_sparse(units, scores)
    reranked = rerank_candidates(units, scores)
    assert [item.source_unit_id for item in dense] == sorted(scores)
    assert [item.source_unit_id for item in sparse] == sorted(scores)
    assert [item.source_unit_id for item in reranked] == sorted(scores)
