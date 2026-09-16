"""Created 2026-08-12. Tests for manual atomic claims and quote verification."""
from __future__ import annotations

import pytest

from research_evidence.claims import AtomicClaimError, create_claim, create_evidence
from research_evidence.parsers.markdown import parse_markdown
from research_evidence.verification.basic import verify_evidence


def test_multi_assertion_claim_requires_splitting() -> None:
    """Keep multiple independent assertions out of the atomic claim table."""
    with pytest.raises(AtomicClaimError, match="atomic"):
        create_claim("c1", "The rate fell and employment rose.")


def test_exact_normalized_quote_verifies_against_original_unit() -> None:
    """Accept whitespace-normalized exact text and promote it to high confidence."""
    unit = parse_markdown("A sentence with   spacing.", "source-version:v1")[0]
    claim = create_claim("c1", "The source contains a sentence.")
    evidence = create_evidence("e1", claim, unit, "A sentence with spacing.")
    verified, result = verify_evidence(evidence, unit, original_authority=True)
    assert result.status.value == "verified-high"
    assert verified.confidence == "high"
    assert verified.original_authority_verified is True


def test_fabricated_locator_or_quote_is_rejected() -> None:
    """Reject evidence whose source unit or quotation does not match."""
    units = parse_markdown("A sentence.", "source-version:v1")
    claim = create_claim("c1", "The source contains a sentence.")
    evidence = create_evidence("e1", claim, units[0], "Fabricated text.")
    verified, result = verify_evidence(evidence, units[0], original_authority=True)
    assert result.status.value == "rejected"
    assert verified.confidence == "low"
