"""Created 2026-08-12. Exact normalized quote and locator verification."""
from __future__ import annotations

from dataclasses import dataclass
import unicodedata

from ..schemas import EvidenceRecord, SourceUnit, VerificationStatus


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
    normalized_quote = normalize_quote(evidence.quote)
    if (
        evidence.source_unit_id != source_unit.source_unit_id
        or evidence.source_version_id != source_unit.source_version_id
        or evidence.locator != source_unit.locator
    ):
        result = VerificationResult(
            VerificationStatus.REJECTED,
            "source-identity-or-locator-mismatch",
            normalized_quote,
        )
        return evidence.model_copy(
            update={
                "verification_status": VerificationStatus.REJECTED,
                "confidence": "low",
                "original_authority_verified": False,
            }
        ), result
    normalized_source = normalize_quote(source_unit.text)
    if normalized_quote not in normalized_source:
        result = VerificationResult(
            VerificationStatus.REJECTED,
            "quote-not-found",
            normalized_quote,
        )
        return evidence.model_copy(
            update={
                "verification_status": VerificationStatus.REJECTED,
                "confidence": "low",
                "original_authority_verified": original_authority,
            }
        ), result
    if not original_authority:
        result = VerificationResult(
            VerificationStatus.FLAGGED_MEDIUM,
            "original-authority-unverified",
            normalized_quote,
        )
        return evidence.model_copy(
            update={
                "verification_status": VerificationStatus.FLAGGED_MEDIUM,
                "confidence": "medium",
                "original_authority_verified": False,
            }
        ), result
    result = VerificationResult(
        VerificationStatus.VERIFIED_HIGH,
        "exact-normalized-quote-and-locator-match",
        normalized_quote,
    )
    return evidence.model_copy(
        update={
            "verification_status": VerificationStatus.VERIFIED_HIGH,
            "confidence": "high",
            "original_authority_verified": True,
        }
    ), result
