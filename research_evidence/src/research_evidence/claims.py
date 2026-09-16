"""Created 2026-08-12. Manual atomic claim and evidence constructors."""
from __future__ import annotations

from typing import Optional

from .schemas import (
    ClaimRecord,
    ClaimType,
    EvidenceRecord,
    EvidenceRelation,
    ReviewState,
    SourceUnit,
    VerificationStatus,
)


class AtomicClaimError(ValueError):
    """Signal that a proposed statement contains multiple assertions.

    Args:
        message: Human-readable atomicity failure.

    Returns:
        An exception suitable for researcher-facing validation.

    Example:
        ``raise AtomicClaimError("split the assertions")``.
    """


def create_claim(
    claim_id: str,
    statement: str,
    claim_type: ClaimType | str = ClaimType.FACTUAL,
) -> ClaimRecord:
    """Create one candidate claim after a lightweight atomicity check.

    Args:
        claim_id: Stable claim identifier.
        statement: Single factual, methodological, interpretive, or normative statement.
        claim_type: Claim classification.

    Returns:
        A candidate atomic claim.

    Raises:
        AtomicClaimError: If obvious independent assertions are joined by ``and`` or ``;``.

    Example:
        ``create_claim("c1", "The rate fell.")``.
    """
    normalized = " ".join(statement.split())
    lowered = normalized.casefold()
    if " and " in lowered or ";" in normalized:
        raise AtomicClaimError("Claim contains multiple assertions; split it into atomic claims.")
    if not normalized:
        raise AtomicClaimError("Claim must contain one non-empty assertion.")
    return ClaimRecord(
        claim_id=claim_id,
        statement=normalized,
        claim_type=claim_type,
        review_state=ReviewState.CANDIDATE,
        atomic=True,
    )


def create_evidence(
    evidence_id: str,
    claim: ClaimRecord,
    source_unit: SourceUnit,
    quote: str,
    relation: EvidenceRelation | str = EvidenceRelation.SUPPORTS,
    extraction_method: str = "manual",
) -> EvidenceRecord:
    """Create candidate evidence linked to one claim and source unit.

    Args:
        evidence_id: Stable evidence identifier.
        claim: Atomic claim receiving the evidence link.
        source_unit: Parsed source unit selected by the researcher.
        quote: Verbatim quote to verify.
        relation: Supports, contradicts, or contextualizes relation.
        extraction_method: Method used to supply the quote.

    Returns:
        Candidate low-confidence evidence awaiting verification.

    Example:
        ``create_evidence("e1", claim, unit, "Verbatim text.")``.
    """
    if not quote.strip():
        raise ValueError("Evidence quote cannot be empty.")
    claim.evidence_ids = [*claim.evidence_ids, evidence_id]
    return EvidenceRecord(
        evidence_id=evidence_id,
        source_unit_id=source_unit.source_unit_id,
        source_version_id=source_unit.source_version_id,
        locator=source_unit.locator,
        quote=quote,
        extraction_method=extraction_method,
        verification_status=VerificationStatus.FLAGGED_LOW,
        confidence="low",
        review_state=ReviewState.CANDIDATE,
        relation=relation,
        original_authority_verified=False,
    )
