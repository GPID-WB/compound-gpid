"""Created 2026-08-13. Tests for candidate evidence and claim proposals."""
from __future__ import annotations

import pytest

from research_evidence.evidence import (
    CandidateProposalError,
    CandidateProposalRegistry,
    create_candidate_proposal,
)
from research_evidence.identity import make_source_unit_id, text_fingerprint
from research_evidence.schemas import ReviewState, SourceUnit, TypedLocator, is_approved_evidence


def _unit() -> SourceUnit:
    """Build one source unit used by proposal tests."""
    text = "The weighted rate fell."
    fingerprint = text_fingerprint(text)
    locator = TypedLocator(kind="markdown_block", block=1, unit_fingerprint=fingerprint)
    return SourceUnit(
        source_unit_id=make_source_unit_id("version-1", locator, fingerprint),
        source_version_id="version-1",
        locator=locator,
        text=text,
    )


def _raw(unit: SourceUnit, **overrides: object) -> dict[str, object]:
    """Build untrusted structured proposal data."""
    values: dict[str, object] = {
        "statement": "The weighted rate fell.",
        "claim_type": "factual",
        "source_unit_id": unit.source_unit_id,
        "quote": unit.text,
        "relation": "supports",
        "rationale": "The retrieved passage directly states the change.",
    }
    values.update(overrides)
    return values


def test_candidate_proposal_is_source_linked_but_never_approved() -> None:
    """Keep a valid local proposal candidate-only until independent review."""
    unit = _unit()
    proposal = create_candidate_proposal(
        _raw(unit),
        {unit.source_unit_id: unit},
        run_id="run-1",
        profile_id="lexical-baseline",
        inventory_id="pypdf",
    )

    assert proposal.claim.review_state == ReviewState.CANDIDATE
    assert proposal.evidence.review_state == ReviewState.CANDIDATE
    assert proposal.evidence.source_version_id == unit.source_version_id
    assert proposal.profile_id == "lexical-baseline"
    assert is_approved_evidence(proposal.evidence) is False


def test_fabricated_source_id_is_rejected() -> None:
    """Reject proposals that cite a source unit absent from the local corpus."""
    unit = _unit()
    with pytest.raises(CandidateProposalError, match="source unit"):
        create_candidate_proposal(
            _raw(unit, source_unit_id="source-unit:fabricated"),
            {unit.source_unit_id: unit},
            run_id="run-1",
            profile_id="lexical-baseline",
            inventory_id="pypdf",
        )


def test_multi_assertion_and_missing_quote_are_rejected() -> None:
    """Require atomic statements and a verbatim quote field in proposals."""
    unit = _unit()
    with pytest.raises(CandidateProposalError, match="atomic"):
        create_candidate_proposal(
            _raw(unit, statement="The rate fell and employment rose."),
            {unit.source_unit_id: unit},
            run_id="run-1",
            profile_id="lexical-baseline",
            inventory_id="pypdf",
        )
    with pytest.raises(CandidateProposalError, match="quote"):
        create_candidate_proposal(
            _raw(unit, quote=""),
            {unit.source_unit_id: unit},
            run_id="run-1",
            profile_id="lexical-baseline",
            inventory_id="pypdf",
        )


def test_paraphrase_stays_flagged_and_duplicate_proposals_are_rejected() -> None:
    """Keep unverbatim paraphrases unapproved and prevent duplicate candidates."""
    unit = _unit()
    proposal = create_candidate_proposal(
        _raw(unit, quote="The weighted measure declined."),
        {unit.source_unit_id: unit},
        run_id="run-1",
        profile_id="lexical-baseline",
        inventory_id="pypdf",
    )
    assert proposal.evidence.review_state == ReviewState.CANDIDATE
    assert proposal.evidence.verification_status.value == "flagged-low"
    registry = CandidateProposalRegistry()
    registry.add(proposal)
    with pytest.raises(CandidateProposalError, match="duplicate"):
        registry.add(proposal)
