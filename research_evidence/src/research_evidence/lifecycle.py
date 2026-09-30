"""Created 2026-08-12. Source-version lifecycle and stale-state propagation."""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from enum import Enum
import hashlib
from typing import Optional

from .schemas import (
    AnalysisLink,
    ClaimRecord,
    EvidenceRecord,
    ReviewState,
    SourceUnit,
    VerificationStatus,
    is_approved_evidence,
)
from .resources import ResourceEvent, ResourceEventKind
from .verification.basic import verify_evidence
from .transactions import ArtifactStore, TransactionResult


class MappingStatus(str, Enum):
    """Classify exact source-unit mapping across compatible source versions.

    Args:
        value: Serialized mapping status.

    Returns:
        A validated mapping status.

    Example:
        ``MappingStatus.AMBIGUOUS`` blocks silent source continuity.
    """

    MAPPED = "mapped"
    AMBIGUOUS = "ambiguous"
    MISSING = "missing"


@dataclass(frozen=True)
class UnitMapping:
    """Describe one old source unit's exact-fingerprint mapping decision.

    Args:
        old_source_unit_id: Prior source-unit identifier.
        new_source_unit_ids: Candidate replacement identifiers.
        status: Mapped, ambiguous, or missing status.
        reason: Stable explanation for review.

    Returns:
        An immutable mapping result.

    Example:
        ``UnitMapping("old", ["new"], MappingStatus.MAPPED, "unique fingerprint")``.
    """

    old_source_unit_id: str
    new_source_unit_ids: list[str]
    status: MappingStatus
    reason: str


@dataclass(frozen=True)
class InvalidationRecord:
    """Record one source change and its affected downstream graph IDs.

    Args:
        event_id: Deterministic invalidation event identifier.
        old_source_version_id: Source version that became stale.
        new_source_version_id: Replacement version, when available.
        affected_source_unit_ids: Prior units requiring review.
        affected_evidence_ids: Evidence records marked stale.
        affected_claim_ids: Claims marked stale.
        affected_analysis_link_ids: Analysis links disabled.
        reason: Stable invalidation reason.
        mappings: Exact fingerprint mapping decisions.

    Returns:
        An immutable audit record.

    Example:
        ``record.reason`` explains why an approval was withdrawn.
    """

    event_id: str
    old_source_version_id: str
    new_source_version_id: Optional[str]
    affected_source_unit_ids: list[str]
    affected_evidence_ids: list[str]
    affected_claim_ids: list[str]
    affected_analysis_link_ids: list[str]
    reason: str
    mappings: list[UnitMapping]


@dataclass
class LifecycleGraph:
    """Hold source units and downstream decisions for lifecycle transitions.

    Args:
        source_units: Source units keyed by deterministic ID.
        evidence: Evidence records keyed by ID.
        claims: Claim records keyed by ID.
        analysis_links: Analysis links keyed by ID.
        invalidations: Append-only invalidation records.

    Returns:
        A mutable graph whose operations return independent updated graphs.

    Example:
        ``graph = build_lifecycle_graph(units, evidence, claims, links)``.
    """

    source_units: dict[str, SourceUnit]
    evidence: dict[str, EvidenceRecord]
    claims: dict[str, ClaimRecord]
    analysis_links: dict[str, AnalysisLink]
    invalidations: list[InvalidationRecord] = field(default_factory=list)
    mappings: list[UnitMapping] = field(default_factory=list)


def build_lifecycle_graph(
    source_units: list[SourceUnit],
    evidence: list[EvidenceRecord],
    claims: list[ClaimRecord],
    analysis_links: list[AnalysisLink],
) -> LifecycleGraph:
    """Build a validated source-to-analysis lifecycle graph.

    Args:
        source_units: Parsed source units across known versions.
        evidence: Source-linked evidence records.
        claims: Claims linked to evidence IDs.
        analysis_links: Downstream analysis links linked to claim IDs.

    Returns:
        A graph with unique IDs and independent model copies.

    Raises:
        ValueError: If any input collection contains duplicate IDs.

    Example:
        ``build_lifecycle_graph([unit], [evidence], [claim], [link])``.
    """
    source_map = {unit.source_unit_id: deepcopy(unit) for unit in source_units}
    evidence_map = {item.evidence_id: deepcopy(item) for item in evidence}
    claim_map = {item.claim_id: deepcopy(item) for item in claims}
    link_map = {item.link_id: deepcopy(item) for item in analysis_links}
    if len(source_map) != len(source_units):
        raise ValueError("Source-unit IDs must be unique in the lifecycle graph")
    if len(evidence_map) != len(evidence):
        raise ValueError("Evidence IDs must be unique in the lifecycle graph")
    if len(claim_map) != len(claims):
        raise ValueError("Claim IDs must be unique in the lifecycle graph")
    if len(link_map) != len(analysis_links):
        raise ValueError("Analysis-link IDs must be unique in the lifecycle graph")
    return LifecycleGraph(source_map, evidence_map, claim_map, link_map)


def map_source_units(old_units: list[SourceUnit], new_units: list[SourceUnit]) -> list[UnitMapping]:
    """Map source units by exact normalized text fingerprint only.

    Args:
        old_units: Units from the prior source version.
        new_units: Units from the replacement source version.

    Returns:
        Deterministically ordered mapping decisions; ambiguity is never resolved silently.

    Example:
        ``map_source_units(old_units, new_units)`` proposes unique content mappings.
    """
    candidates: dict[str, list[SourceUnit]] = {}
    for unit in new_units:
        candidates.setdefault(unit.locator.unit_fingerprint, []).append(unit)
    mappings: list[UnitMapping] = []
    for old_unit in sorted(old_units, key=lambda item: item.source_unit_id):
        matches = sorted(
            candidates.get(old_unit.locator.unit_fingerprint, []),
            key=lambda item: item.source_unit_id,
        )
        if len(matches) == 1:
            status = MappingStatus.MAPPED
            reason = "unique exact unit fingerprint"
        elif matches:
            status = MappingStatus.AMBIGUOUS
            reason = "multiple new units share the exact fingerprint"
        else:
            status = MappingStatus.MISSING
            reason = "no new unit has the exact fingerprint"
        mappings.append(
            UnitMapping(
                old_source_unit_id=old_unit.source_unit_id,
                new_source_unit_ids=[item.source_unit_id for item in matches],
                status=status,
                reason=reason,
            )
        )
    return mappings


def _copy_graph(graph: LifecycleGraph) -> LifecycleGraph:
    """Deep-copy graph state before applying one transition."""
    return deepcopy(graph)


def _invalidation_id(old_version_id: str, new_version_id: Optional[str], mappings: list[UnitMapping]) -> str:
    """Derive an idempotent invalidation event ID."""
    mapping_text = "|".join(
        f"{item.old_source_unit_id}:{item.status.value}:{','.join(item.new_source_unit_ids)}"
        for item in mappings
    )
    payload = "\x1f".join((old_version_id, new_version_id or "", mapping_text))
    return "invalidation:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()


def invalidate_source_change(
    graph: LifecycleGraph,
    old_source_version_id: str,
    new_source_version_id: str,
    new_units: list[SourceUnit],
) -> LifecycleGraph:
    """Stale all downstream decisions affected by one source-version change.

    Args:
        graph: Existing lifecycle graph.
        old_source_version_id: Version whose approvals are no longer current.
        new_source_version_id: Replacement source version.
        new_units: Parsed units from the replacement version.

    Returns:
        An independent graph with stale evidence, claims, links, mappings, and history.

    Example:
        ``invalidate_source_change(graph, "v1", "v2", new_units)``.
    """
    updated = _copy_graph(graph)
    old_units = [
        unit for unit in updated.source_units.values()
        if unit.source_version_id == old_source_version_id
    ]
    mappings = map_source_units(old_units, new_units)
    updated.mappings = mappings
    for unit in sorted(new_units, key=lambda item: item.source_unit_id):
        updated.source_units[unit.source_unit_id] = deepcopy(unit)
    affected_units = {unit.source_unit_id for unit in old_units}
    affected_evidence = {
        evidence_id: evidence
        for evidence_id, evidence in updated.evidence.items()
        if evidence.source_version_id == old_source_version_id
        or evidence.source_unit_id in affected_units
    }
    for evidence in affected_evidence.values():
        evidence.stale = True
        evidence.review_state = ReviewState.STALE
        evidence.verification_status = VerificationStatus.STALE
        evidence.original_authority_verified = False
    affected_evidence_ids = set(affected_evidence)
    affected_claims = {
        claim_id: claim
        for claim_id, claim in updated.claims.items()
        if any(evidence_id in affected_evidence_ids for evidence_id in claim.evidence_ids)
    }
    for claim in affected_claims.values():
        claim.stale = True
        claim.review_state = ReviewState.STALE
    affected_claim_ids = set(affected_claims)
    affected_links = {
        link_id: link
        for link_id, link in updated.analysis_links.items()
        if link.claim_id in affected_claim_ids
    }
    for link in affected_links.values():
        link.active = False
    record = InvalidationRecord(
        event_id=_invalidation_id(old_source_version_id, new_source_version_id, mappings),
        old_source_version_id=old_source_version_id,
        new_source_version_id=new_source_version_id,
        affected_source_unit_ids=sorted(affected_units),
        affected_evidence_ids=sorted(affected_evidence_ids),
        affected_claim_ids=sorted(affected_claim_ids),
        affected_analysis_link_ids=sorted(affected_links),
        reason="source-version-changed",
        mappings=mappings,
    )
    if not any(item.event_id == record.event_id for item in updated.invalidations):
        updated.invalidations.append(record)
    return updated


def apply_resource_event(graph: LifecycleGraph, event: ResourceEvent) -> LifecycleGraph:
    """Apply a resource event while blocking implicit source-version assumptions.

    Args:
        graph: Existing lifecycle graph.
        event: Hash/path discovery event.

    Returns:
        An independent graph for content-preserving unchanged or moved events.

    Raises:
        ValueError: If a content-changing event lacks explicit old/new source versions.

    Example:
        ``apply_resource_event(graph, moved_event)`` preserves approvals for a move.
    """
    if event.kind in {ResourceEventKind.UNCHANGED, ResourceEventKind.MOVED}:
        return _copy_graph(graph)
    raise ValueError(
        f"{event.kind.value} requires explicit source-version invalidation; "
        "automatic downstream mutation is blocked"
    )


def reverify_stale_evidence(
    graph: LifecycleGraph,
    evidence_id: str,
    replacement_unit: SourceUnit,
    *,
    original_authority: bool,
) -> LifecycleGraph:
    """Re-verify one stale evidence record and restore approval only on success.

    Args:
        graph: Lifecycle graph containing stale evidence.
        evidence_id: Evidence identifier to re-verify.
        replacement_unit: Current source unit resolved from original bytes.
        original_authority: Whether the original resource was checked.

    Returns:
        An independent graph with downstream approval restored only after success.

    Raises:
        KeyError: If the evidence ID is unknown.

    Example:
        ``reverify_stale_evidence(graph, "e1", replacement, original_authority=True)``.
    """
    if evidence_id not in graph.evidence:
        raise KeyError(f"Evidence record is not in lifecycle graph: {evidence_id}")
    updated = _copy_graph(graph)
    evidence = updated.evidence[evidence_id]
    candidate = evidence.model_copy(
        update={
            "source_unit_id": replacement_unit.source_unit_id,
            "source_version_id": replacement_unit.source_version_id,
            "locator": replacement_unit.locator,
            "stale": False,
        }
    )
    verified, result = verify_evidence(candidate, replacement_unit, original_authority=original_authority)
    if result.status == VerificationStatus.VERIFIED_HIGH:
        verified.stale = False
        verified.review_state = ReviewState.APPROVED
        updated.evidence[evidence_id] = verified
    else:
        verified.stale = True
        verified.review_state = ReviewState.STALE
        verified.verification_status = VerificationStatus.STALE
        updated.evidence[evidence_id] = verified
    for claim in updated.claims.values():
        if evidence_id not in claim.evidence_ids:
            continue
        linked = [updated.evidence[item] for item in claim.evidence_ids if item in updated.evidence]
        if linked and all(is_approved_evidence(item) for item in linked):
            claim.stale = False
            claim.review_state = ReviewState.APPROVED
            for link in updated.analysis_links.values():
                if link.claim_id == claim.claim_id:
                    link.active = True
        else:
            claim.stale = True
            claim.review_state = ReviewState.STALE
            for link in updated.analysis_links.values():
                if link.claim_id == claim.claim_id:
                    link.active = False
    return updated


def persist_lifecycle_result(
    store: ArtifactStore,
    graph: LifecycleGraph,
    *,
    expected_revision: int,
    failure_at: Optional[str] = None,
) -> TransactionResult:
    """Persist lifecycle state and invalidation history as one journaled mutation.

    Args:
        store: Canonical evidence artifact store.
        graph: Lifecycle graph after invalidation or re-verification.
        expected_revision: Aggregate revision read by the caller.
        failure_at: Optional transaction test boundary.

    Returns:
        Transaction result after all canonical files commit.

    Raises:
        SimulatedCrash: If a requested recovery boundary is injected.
        RevisionConflictError: If the expected revision is stale.

    Example:
        ``persist_lifecycle_result(store, graph, expected_revision=0)``.
    """
    evidence_payload = {
        "schema_version": "research-evidence-records-v1",
        "records": [
            item.model_dump(mode="json", exclude_none=True)
            for item in sorted(graph.evidence.values(), key=lambda value: value.evidence_id)
        ],
    }
    claims_payload = {
        "schema_version": "research-evidence-matrix-v1",
        "claims": [
            item.model_dump(mode="json", exclude_none=True)
            for item in sorted(graph.claims.values(), key=lambda value: value.claim_id)
        ],
    }
    links_payload = {
        "schema_version": "research-evidence-analysis-links-v1",
        "analysis_links": [
            item.model_dump(mode="json", exclude_none=True)
            for item in sorted(graph.analysis_links.values(), key=lambda value: value.link_id)
        ],
    }
    history_payload = {
        "schema_version": "research-evidence-invalidation-history-v1",
        "events": [
            {
                "event_id": record.event_id,
                "old_source_version_id": record.old_source_version_id,
                "new_source_version_id": record.new_source_version_id,
                "affected_source_unit_ids": record.affected_source_unit_ids,
                "affected_evidence_ids": record.affected_evidence_ids,
                "affected_claim_ids": record.affected_claim_ids,
                "affected_analysis_link_ids": record.affected_analysis_link_ids,
                "reason": record.reason,
                "mappings": [
                    {
                        "old_source_unit_id": mapping.old_source_unit_id,
                        "new_source_unit_ids": mapping.new_source_unit_ids,
                        "status": mapping.status.value,
                        "reason": mapping.reason,
                    }
                    for mapping in record.mappings
                ],
            }
            for record in graph.invalidations
        ],
    }
    with store.transaction(
        expected_revision=expected_revision,
        actor="lifecycle",
        action="invalidate-source",
    ) as transaction:
        transaction.stage_yaml("evidence-records.yaml", evidence_payload)
        transaction.stage_yaml("claim-evidence-matrix.yaml", claims_payload)
        transaction.stage_yaml("analysis-links.yaml", links_payload)
        transaction.stage_yaml("invalidation-history.yaml", history_payload)
        transaction.mark_derived_stale(
            "index/lexical.sqlite",
            "source lifecycle mutation requires derived-index rebuild",
        )
        return transaction.commit(failure_at=failure_at)
