"""Created 2026-08-12. Tests for canonical evidence schemas."""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from research_evidence.schemas import (
    ClaimRecord,
    EvidenceRecord,
    EvidenceRelation,
    ReviewState,
    TypedLocator,
    VerificationStatus,
    is_approved_evidence,
)


@pytest.fixture
def markdown_locator() -> TypedLocator:
    """Return a valid typed Markdown locator for schema tests."""
    return TypedLocator(
        kind="markdown_block",
        block=2,
        line_start=4,
        line_end=6,
        unit_fingerprint="sha256:" + "a" * 64,
    )


def test_typed_locator_rejects_invalid_format_fields() -> None:
    """Reject locator fields that do not belong to the selected format kind."""
    with pytest.raises(ValidationError, match="block"):
        TypedLocator(
            kind="pdf_text",
            block=2,
            page=4,
            unit_fingerprint="sha256:" + "a" * 64,
        )


def test_evidence_approval_requires_original_verification(markdown_locator: TypedLocator) -> None:
    """Require exact original-authority checks before downstream approval."""
    evidence = EvidenceRecord(
        evidence_id="evidence-1",
        source_unit_id="unit-1",
        source_version_id="version-1",
        locator=markdown_locator,
        quote="A verified sentence.",
        extraction_method="manual",
        verification_status=VerificationStatus.VERIFIED_HIGH,
        confidence="high",
        review_state=ReviewState.APPROVED,
        relation=EvidenceRelation.SUPPORTS,
        original_authority_verified=False,
    )
    assert is_approved_evidence(evidence) is False
    evidence.original_authority_verified = True
    assert is_approved_evidence(evidence) is True


def test_stale_evidence_is_never_approved(markdown_locator: TypedLocator) -> None:
    """Keep invalidated evidence in history but remove downstream eligibility."""
    evidence = EvidenceRecord(
        evidence_id="evidence-2",
        source_unit_id="unit-1",
        source_version_id="version-1",
        locator=markdown_locator,
        quote="A verified sentence.",
        extraction_method="manual",
        verification_status=VerificationStatus.VERIFIED_HIGH,
        confidence="high",
        review_state=ReviewState.APPROVED,
        relation=EvidenceRelation.SUPPORTS,
        original_authority_verified=True,
        stale=True,
    )
    assert is_approved_evidence(evidence) is False


def test_claim_records_atomicity_and_relations(markdown_locator: TypedLocator) -> None:
    """Represent one atomic claim linked to a typed evidence relation."""
    claim = ClaimRecord(
        claim_id="claim-1",
        statement="The intervention reduced poverty.",
        claim_type="factual",
        evidence_ids=["evidence-1"],
        review_state=ReviewState.CANDIDATE,
        atomic=True,
    )
    assert claim.evidence_ids == ["evidence-1"]
    assert markdown_locator.kind == "markdown_block"
