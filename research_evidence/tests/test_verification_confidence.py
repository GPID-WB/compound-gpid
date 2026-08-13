"""Created 2026-08-13. Tests for original-authority verification and confidence policy."""
from __future__ import annotations

import pytest

from research_evidence.identity import make_source_unit_id, text_fingerprint
from research_evidence.schemas import (
    EvidenceRecord,
    EvidenceRelation,
    LocatorKind,
    ReviewState,
    SourceUnit,
    TypedLocator,
    VerificationStatus,
)
from research_evidence.verification.basic import verify_evidence_context


def _unit(
    version: str,
    text: str,
    *,
    block: int = 1,
    unit_type: str = "prose",
    review_required: bool = False,
    parser: str = "markdown",
) -> SourceUnit:
    """Build one typed source unit for verification tests."""
    fingerprint = text_fingerprint(text)
    locator = TypedLocator(
        kind="markdown_block",
        block=block,
        unit_fingerprint=fingerprint,
    )
    return SourceUnit(
        source_unit_id=make_source_unit_id(version, locator, fingerprint),
        source_version_id=version,
        locator=locator,
        text=text,
        unit_type=unit_type,
        review_required=review_required,
        parser_metadata={"parser": parser},
    )


def _evidence(unit: SourceUnit, quote: str, *, status: str = "flagged-low") -> EvidenceRecord:
    """Build candidate evidence tied to one source unit."""
    return EvidenceRecord(
        evidence_id="evidence-1",
        source_unit_id=unit.source_unit_id,
        source_version_id=unit.source_version_id,
        locator=unit.locator,
        quote=quote,
        extraction_method="manual",
        verification_status=status,
        confidence="low",
        review_state=ReviewState.CANDIDATE,
        relation=EvidenceRelation.SUPPORTS,
    )


def test_exact_quote_and_whitespace_normalization_can_verify_high() -> None:
    """Promote only an exact normalized quote from an unchanged prose unit."""
    unit = _unit("v1", "The weighted rate fell.")
    evidence = _evidence(unit, "The   weighted\nrate fell.")

    verified, result = verify_evidence_context(
        evidence,
        [unit],
        original_authority_available=True,
        source_hash_matches=True,
    )

    assert result.status == VerificationStatus.VERIFIED_HIGH
    assert result.confidence == "high"
    assert verified.original_authority_verified is True


def test_cross_unit_quote_is_flagged_medium_not_high() -> None:
    """Keep a quote spanning units review-required even when originals are available."""
    first = _unit("v1", "The weighted rate", block=1)
    second = _unit("v1", "fell sharply.", block=2)
    evidence = _evidence(first, "The weighted rate fell sharply.")

    verified, result = verify_evidence_context(
        evidence,
        [first, second],
        original_authority_available=True,
        source_hash_matches=True,
    )

    assert result.status == VerificationStatus.FLAGGED_MEDIUM
    assert result.reason == "cross-unit-quote-requires-review"
    assert verified.confidence == "medium"


def test_fuzzy_only_match_is_diagnostic_and_cannot_promote() -> None:
    """Expose fuzzy similarity as low-confidence diagnostic output only."""
    unit = _unit("v1", "The weighted poverty rate declined substantially.")
    evidence = _evidence(unit, "The weighted poverty rate fell substantially.")

    verified, result = verify_evidence_context(
        evidence,
        [unit],
        original_authority_available=True,
        source_hash_matches=True,
        allow_fuzzy_diagnostic=True,
    )

    assert result.status == VerificationStatus.FLAGGED_LOW
    assert result.reason == "fuzzy-only-match"
    assert verified.confidence == "low"
    assert verified.original_authority_verified is False


def test_source_mismatch_and_fabricated_locator_are_rejected() -> None:
    """Reject evidence whose source version or typed locator cannot resolve."""
    unit = _unit("v1", "The finding.")
    other = _unit("v2", "The finding.")
    mismatched = _evidence(unit, unit.text).model_copy(
        update={"source_version_id": "v2"}
    )

    rejected, result = verify_evidence_context(
        mismatched,
        [other],
        original_authority_available=True,
        source_hash_matches=True,
    )

    assert result.status == VerificationStatus.REJECTED
    assert result.reason == "source-identity-or-locator-mismatch"
    assert rejected.confidence == "low"


def test_stale_hash_and_stale_record_cannot_verify() -> None:
    """Return stale status before quote matching when source bytes changed."""
    unit = _unit("v1", "The finding.")
    stale = _evidence(unit, unit.text).model_copy(update={"stale": True})

    verified, result = verify_evidence_context(
        stale,
        [unit],
        original_authority_available=True,
        source_hash_matches=False,
    )

    assert result.status == VerificationStatus.STALE
    assert result.reason == "source-hash-mismatch"
    assert verified.verification_status == VerificationStatus.STALE
    assert verified.review_state == ReviewState.STALE


def test_typed_review_required_units_and_ocr_cannot_receive_high_confidence() -> None:
    """Cap tables, equations, and OCR-derived units at explicit review-required status."""
    table = _unit("v1", "Year Rate", unit_type="table", review_required=True)
    equation = _unit("v1", "x = y", unit_type="equation", review_required=True)
    ocr = _unit("v1", "OCR text", unit_type="image", review_required=True, parser="ocr")

    for unit in (table, equation, ocr):
        verified, result = verify_evidence_context(
            _evidence(unit, unit.text),
            [unit],
            original_authority_available=True,
            source_hash_matches=True,
        )
        assert result.status == VerificationStatus.FLAGGED_MEDIUM
        assert result.reason == "typed-review-required"
        assert verified.confidence == "medium"


def test_inaccessible_original_abstains_and_legacy_locator_rejects() -> None:
    """Abstain when originals are inaccessible and reject legacy free-text locators."""
    unit = _unit("v1", "The finding.")
    evidence = _evidence(unit, unit.text)
    _, abstained = verify_evidence_context(
        evidence,
        [unit],
        original_authority_available=False,
        source_hash_matches=None,
        source_available=False,
    )
    assert abstained.status == VerificationStatus.ABSTAINED
    assert abstained.reason == "original-source-inaccessible"

    legacy_locator = TypedLocator(
        kind=LocatorKind.LEGACY_LOCATOR,
        anchor="free text locator",
        unit_fingerprint=text_fingerprint(unit.text),
    )
    legacy = evidence.model_copy(update={"locator": legacy_locator})
    _, rejected = verify_evidence_context(
        legacy,
        [unit],
        original_authority_available=True,
        source_hash_matches=True,
    )
    assert rejected.status == VerificationStatus.REJECTED
    assert rejected.reason == "legacy-locator-requires-review"
