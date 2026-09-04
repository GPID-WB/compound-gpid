"""Created 2026-08-12. Exact normalized quote and locator verification."""
from __future__ import annotations

from dataclasses import dataclass
import unicodedata
from collections.abc import Sequence
from typing import Optional

from ..schemas import EvidenceRecord, LocatorKind, SourceUnit, VerificationStatus
from .confidence import decide_confidence, fuzzy_token_overlap


@dataclass(frozen=True)
class VerificationResult:
    """Explain one deterministic evidence verification outcome.

    Args:
        status: Machine-readable verification status.
        reason: Stable reason code for review.
        normalized_quote: Normalized quote used by the matcher.

    Returns:
        An immutable verification result.

    Example:
        ``VerificationResult(VerificationStatus.REJECTED, "quote-not-found", "text")``.
    """

    status: VerificationStatus
    reason: str
    normalized_quote: str
    confidence: str = "low"
    review_required: bool = True
    match_kind: str = "none"


def normalize_quote(text: str) -> str:
    """Normalize Unicode and whitespace without rewriting substantive words.

    Args:
        text: Quote or source text.

    Returns:
        NFKC-normalized text with collapsed whitespace.

    Example:
        ``normalize_quote("A  sentence")`` returns ``"A sentence"``.
    """
    return " ".join(unicodedata.normalize("NFKC", text).split())


def verify_evidence(
    evidence: EvidenceRecord,
    source_unit: SourceUnit,
    *,
    original_authority: bool,
) -> tuple[EvidenceRecord, VerificationResult]:
    """Verify source identity, locator equality, and exact normalized quotation.

    Args:
        evidence: Candidate evidence record to verify.
        source_unit: Current source unit resolved from the original resource.
        original_authority: Whether the original bytes were checked in this run.

    Returns:
        Updated evidence and an explainable verification result.

    Example:
        ``verify_evidence(evidence, unit, original_authority=True)``.
    """
    return verify_evidence_context(
        evidence,
        [source_unit],
        original_authority_available=original_authority,
        source_hash_matches=True,
    )


def verify_evidence_context(
    evidence: EvidenceRecord,
    source_units: Sequence[SourceUnit],
    *,
    original_authority_available: bool,
    source_hash_matches: Optional[bool],
    source_available: bool = True,
    allow_fuzzy_diagnostic: bool = False,
) -> tuple[EvidenceRecord, VerificationResult]:
    """Verify evidence against current typed source context and authority facts.

    Args:
        evidence: Evidence record to verify.
        source_units: Current source units for one source version, ordered by locator.
        original_authority_available: Whether original bytes were independently checked.
        source_hash_matches: Current source hash comparison, or ``None`` if unknown.
        source_available: Whether the original source can be inspected.
        allow_fuzzy_diagnostic: Permit low-confidence token-overlap diagnostics.

    Returns:
        Updated evidence and a machine-readable verification result.

    Example:
        ``verify_evidence_context(evidence, [unit], original_authority_available=True, source_hash_matches=True)``.
    """
    normalized_quote = normalize_quote(evidence.quote)
    matching_units = [
        unit for unit in source_units if unit.source_unit_id == evidence.source_unit_id
    ]
    identity_matches = [
        unit
        for unit in matching_units
        if unit.source_version_id == evidence.source_version_id
        and unit.locator == evidence.locator
    ]
    legacy_locator = evidence.locator.kind == LocatorKind.LEGACY_LOCATOR
    if not identity_matches and not legacy_locator:
        result = VerificationResult(
            VerificationStatus.REJECTED,
            "source-identity-or-locator-mismatch",
            normalized_quote,
        )
        return evidence.model_copy(
            update={
                "verification_status": result.status,
                "confidence": result.confidence,
                "original_authority_verified": False,
            }
        ), result
    unit = identity_matches[0] if identity_matches else None
    match_kind = "none"
    if unit is not None and normalized_quote in normalize_quote(unit.text):
        match_kind = "exact"
    if match_kind == "none" and unit is not None and len(source_units) > 1:
        ordered_units = list(source_units)
        for index, candidate in enumerate(ordered_units[:-1]):
            if candidate.source_unit_id != unit.source_unit_id:
                continue
            following = ordered_units[index + 1]
            if candidate.source_version_id == following.source_version_id:
                joined = normalize_quote(f"{candidate.text} {following.text}")
                if normalized_quote in joined:
                    match_kind = "cross-unit"
                    break
    if (
        match_kind == "none"
        and allow_fuzzy_diagnostic
        and unit is not None
        and fuzzy_token_overlap(normalized_quote, normalize_quote(unit.text)) >= 0.6
    ):
        match_kind = "fuzzy"
    decision = decide_confidence(
        match_kind=match_kind,
        original_authority_available=original_authority_available,
        source_hash_matches=source_hash_matches,
        source_available=source_available,
        typed_review_required=bool(unit and unit.review_required),
        stale=evidence.stale,
        legacy_locator=legacy_locator,
    )
    result = VerificationResult(
        decision.status,
        decision.reason,
        normalized_quote,
        decision.confidence,
        decision.review_required,
        match_kind,
    )
    return evidence.model_copy(
        update={
            "verification_status": decision.status,
            "confidence": decision.confidence,
            "review_state": "stale" if decision.status == VerificationStatus.STALE else evidence.review_state,
            "original_authority_verified": decision.original_authority_verified,
            "stale": decision.status == VerificationStatus.STALE,
        }
    ), result
