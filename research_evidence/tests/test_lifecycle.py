"""Created 2026-08-12. Tests for source lifecycle invalidation propagation."""
from __future__ import annotations

from pathlib import Path

import pytest

from research_evidence.identity import make_source_unit_id, text_fingerprint
from research_evidence.lifecycle import (
    MappingStatus,
    apply_resource_event,
    build_lifecycle_graph,
    invalidate_source_change,
    map_source_units,
    persist_lifecycle_result,
    reverify_stale_evidence,
)
from research_evidence.resources import ResourceEvent, ResourceEventKind
from research_evidence.schemas import (
    AnalysisLink,
    ClaimRecord,
    EvidenceRecord,
    EvidenceRelation,
    ReviewState,
    SourceUnit,
    TypedLocator,
    VerificationStatus,
)
from research_evidence.transactions import ArtifactStore, SimulatedCrash


def _unit(version_id: str, text: str, block: int = 1) -> SourceUnit:
    """Build one deterministic Markdown source unit for lifecycle tests."""
    fingerprint = text_fingerprint(text)
    locator = TypedLocator(
        kind="markdown_block",
        block=block,
        unit_fingerprint=fingerprint,
    )
    return SourceUnit(
        source_unit_id=make_source_unit_id(version_id, locator, fingerprint),
        source_version_id=version_id,
        locator=locator,
        text=text,
    )


def _graph(old_unit: SourceUnit):
    """Build one approved evidence -> claim -> analysis-link graph."""
    evidence = EvidenceRecord(
        evidence_id="e1",
        source_unit_id=old_unit.source_unit_id,
        source_version_id=old_unit.source_version_id,
        locator=old_unit.locator,
        quote=old_unit.text,
        extraction_method="manual",
        verification_status=VerificationStatus.VERIFIED_HIGH,
        confidence="high",
        review_state=ReviewState.APPROVED,
        relation=EvidenceRelation.SUPPORTS,
        original_authority_verified=True,
    )
    claim = ClaimRecord(
        claim_id="c1",
        statement="The source finding is true.",
        claim_type="factual",
        evidence_ids=["e1"],
        review_state=ReviewState.APPROVED,
    )
    link = AnalysisLink(
        link_id="a1",
        claim_id="c1",
        analysis_ref="analysis/model.R",
        active=True,
    )
    return build_lifecycle_graph([old_unit], [evidence], [claim], [link])


def test_unchanged_and_moved_events_do_not_invalidate_records() -> None:
    """Keep approved downstream decisions active for content-preserving events."""
    old_unit = _unit("version-1", "The finding.")
    graph = _graph(old_unit)
    unchanged = ResourceEvent(
        kind=ResourceEventKind.UNCHANGED,
        relative_path="notes.md",
        resource_id="resource-1",
        reason="same hash",
    )
    moved = ResourceEvent(
        kind=ResourceEventKind.MOVED,
        relative_path="new/notes.md",
        previous_path="notes.md",
        resource_id="resource-1",
        reason="same hash",
    )

    assert apply_resource_event(graph, unchanged).evidence["e1"].stale is False
    assert apply_resource_event(graph, moved).evidence["e1"].stale is False


def test_changed_source_stales_entire_downstream_graph() -> None:
    """Stale evidence must make linked claims and analysis links ineligible."""
    old_unit = _unit("version-1", "The finding.")
    graph = _graph(old_unit)
    result = invalidate_source_change(graph, "version-1", "version-2", [_unit("version-2", "Revised finding.")])

    assert result.evidence["e1"].stale is True
    assert result.evidence["e1"].review_state == ReviewState.STALE
    assert result.evidence["e1"].verification_status == VerificationStatus.STALE
    assert result.claims["c1"].stale is True
    assert result.claims["c1"].review_state == ReviewState.STALE
    assert result.analysis_links["a1"].active is False
    assert result.invalidations[0].reason == "source-version-changed"


def test_mapping_uses_exact_fingerprints_and_flags_ambiguity() -> None:
    """Map unique content only; duplicate or missing matches remain review-required."""
    old = [_unit("old", "A"), _unit("old", "B", block=2)]
    new = [_unit("new", "B", block=4), _unit("new", "A", block=9)]
    mapped = map_source_units(old, new)
    assert all(item.status == MappingStatus.MAPPED for item in mapped)

    ambiguous = map_source_units([_unit("old", "A")], [_unit("new", "A"), _unit("new", "A", block=2)])
    assert ambiguous[0].status == MappingStatus.AMBIGUOUS
    missing = map_source_units([_unit("old", "missing")], [_unit("new", "other")])
    assert missing[0].status == MappingStatus.MISSING


def test_reverification_restores_approval_only_after_exact_original_check() -> None:
    """Restore stale approval only when the replacement original unit verifies."""
    old_unit = _unit("version-1", "The finding.")
    graph = _graph(old_unit)
    stale = invalidate_source_change(graph, "version-1", "version-2", [_unit("version-2", "The finding.")])
    replacement = stale.source_units[next(iter(stale.source_units))]

    restored = reverify_stale_evidence(stale, "e1", replacement, original_authority=True)
    assert restored.evidence["e1"].stale is False
    assert restored.evidence["e1"].review_state == ReviewState.APPROVED
    assert restored.claims["c1"].review_state == ReviewState.APPROVED
    assert restored.analysis_links["a1"].active is True

    failed = reverify_stale_evidence(stale, "e1", _unit("version-2", "Fabricated."), original_authority=True)
    assert failed.evidence["e1"].stale is True
    assert failed.claims["c1"].stale is True


def test_invalidation_is_idempotent_and_records_ambiguity() -> None:
    """Repeated invalidation does not compound state and ambiguous maps stay stale."""
    old_unit = _unit("version-1", "The finding.")
    graph = _graph(old_unit)
    new_units = [_unit("version-2", "The finding."), _unit("version-2", "The finding.", block=2)]
    first = invalidate_source_change(graph, "version-1", "version-2", new_units)
    second = invalidate_source_change(first, "version-1", "version-2", new_units)

    assert second.evidence["e1"].stale is True
    assert second.invalidations == first.invalidations
    assert second.mappings[0].status == MappingStatus.AMBIGUOUS


def test_interrupted_invalidation_recovers_canonical_stale_state(tmp_path: Path) -> None:
    """Recover a lifecycle mutation after canonical replacement interruption."""
    old_unit = _unit("version-1", "The finding.")
    graph = invalidate_source_change(
        _graph(old_unit),
        "version-1",
        "version-2",
        [_unit("version-2", "Revised finding.")],
    )
    store = ArtifactStore(tmp_path / "evidence")

    with pytest.raises(SimulatedCrash):
        persist_lifecycle_result(store, graph, expected_revision=0, failure_at="after_replace")

    recovery = store.recover()
    assert recovery[0].status == "committed"
    assert store.current_revision() == 1
