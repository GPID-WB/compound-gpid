"""Created 2026-08-13. Confidence transitions for original-authority evidence."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Optional

from ..schemas import LocatorKind, VerificationStatus


ConfidenceLabel = Literal["high", "medium", "low"]


@dataclass(frozen=True)
class ConfidenceDecision:
    """Represent one machine-readable verification confidence transition.

    Args:
        status: Verification outcome status.
        confidence: Conservative high, medium, or low label.
        reason: Stable reason code shown at the review decision point.
        review_required: Whether a researcher must inspect the result.
        original_authority_verified: Whether original bytes were independently checked.

    Returns:
        An immutable confidence decision.

    Example:
        ``ConfidenceDecision(VerificationStatus.VERIFIED_HIGH, "high", "exact-match", False, True)``.
    """

    status: VerificationStatus
    confidence: ConfidenceLabel
    reason: str
    review_required: bool
    original_authority_verified: bool


def decide_confidence(
    *,
    match_kind: str,
    original_authority_available: bool,
    source_hash_matches: Optional[bool],
    source_available: bool,
    typed_review_required: bool,
    stale: bool,
    legacy_locator: bool,
) -> ConfidenceDecision:
    """Apply the fail-closed confidence policy to verification facts.

    Args:
        match_kind: ``exact``, ``cross-unit``, ``fuzzy``, or ``none`` diagnostic.
        original_authority_available: Whether original bytes were checked in this run.
        source_hash_matches: Current/original hash comparison, or ``None`` if unavailable.
        source_available: Whether the original source can be inspected.
        typed_review_required: Whether the unit is table/equation/OCR/etc.
        stale: Whether lifecycle state already invalidated the record.
        legacy_locator: Whether the locator is an unverified legacy free-text locator.

    Returns:
        A conservative decision; only exact unchanged prose may be high confidence.

    Example:
        ``decide_confidence(match_kind="exact", original_authority_available=True, source_hash_matches=True, source_available=True, typed_review_required=False, stale=False, legacy_locator=False)``.
    """
    if stale or source_hash_matches is False:
        return ConfidenceDecision(
            VerificationStatus.STALE,
            "low",
            "source-hash-mismatch",
            True,
            False,
        )
    if not source_available:
        return ConfidenceDecision(
            VerificationStatus.ABSTAINED,
            "low",
            "original-source-inaccessible",
            True,
            False,
        )
    if legacy_locator:
        return ConfidenceDecision(
            VerificationStatus.REJECTED,
            "low",
            "legacy-locator-requires-review",
            True,
            False,
        )
    if match_kind == "none":
        return ConfidenceDecision(
            VerificationStatus.REJECTED,
            "low",
            "quote-not-found",
            True,
            False,
        )
    if match_kind == "fuzzy":
        return ConfidenceDecision(
            VerificationStatus.FLAGGED_LOW,
            "low",
            "fuzzy-only-match",
            True,
            False,
        )
    if match_kind == "cross-unit":
        return ConfidenceDecision(
            VerificationStatus.FLAGGED_MEDIUM,
            "medium",
            "cross-unit-quote-requires-review",
            True,
            False,
        )
    if typed_review_required:
        return ConfidenceDecision(
            VerificationStatus.FLAGGED_MEDIUM,
            "medium",
            "typed-review-required",
            True,
            False,
        )
    if not original_authority_available:
        return ConfidenceDecision(
            VerificationStatus.FLAGGED_MEDIUM,
            "medium",
            "original-authority-unverified",
            True,
            False,
        )
    return ConfidenceDecision(
        VerificationStatus.VERIFIED_HIGH,
        "high",
        "exact-normalized-quote-and-locator-match",
        False,
        True,
    )


def fuzzy_token_overlap(quote: str, source: str) -> float:
    """Compute a simple diagnostic token-overlap score without approval semantics.

    Args:
        quote: Candidate quote text.
        source: Source-unit text.

    Returns:
        Fraction of quote tokens found in source tokens, from 0 to 1.

    Example:
        ``fuzzy_token_overlap("rate fell", "the rate declined")`` returns ``0.5``.
    """
    quote_tokens = set(quote.casefold().split())
    source_tokens = set(source.casefold().split())
    if not quote_tokens:
        return 0.0
    return len(quote_tokens & source_tokens) / len(quote_tokens)
