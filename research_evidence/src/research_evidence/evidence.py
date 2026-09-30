"""Created 2026-08-13. Candidate evidence and local claim proposal contracts."""
from __future__ import annotations

from hashlib import sha256
from collections.abc import Mapping
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from .claims import AtomicClaimError, create_claim, create_evidence
from .schemas import ClaimRecord, EvidenceRecord, ReviewState, SourceUnit


class CandidateProposalError(ValueError):
    """Signal malformed, fabricated, duplicate, or non-atomic proposal data.

    Args:
        message: Human-readable proposal validation failure.

    Returns:
        An exception suitable for local candidate handling.

    Example:
        ``raise CandidateProposalError("source unit is not local")``.
    """


class CandidateProposal(BaseModel):
    """Store one source-linked candidate claim/evidence proposal.

    Args:
        candidate_id: Deterministic proposal identifier.
        claim: Atomic candidate claim.
        evidence: Candidate source-linked evidence.
        rationale: Untrusted proposal rationale retained for review.
        run_id: Local run identifier that generated the proposal.
        profile_id: Retrieval/model profile reference.
        inventory_id: Dependency/model inventory reference.

    Returns:
        A validated candidate proposal.

    Example:
        ``proposal.claim.review_state`` remains ``candidate``.
    """

    model_config = ConfigDict(extra="forbid")

    candidate_id: str = Field(min_length=1)
    claim: ClaimRecord
    evidence: EvidenceRecord
    rationale: str = Field(min_length=1)
    run_id: str = Field(min_length=1)
    profile_id: str = Field(min_length=1)
    inventory_id: str = Field(min_length=1)


class CandidateProposalRegistry:
    """Keep deterministic candidate proposals without silently deduplicating them.

    Args:
        proposals: Optional initial candidate records.

    Returns:
        A registry that rejects duplicate candidate IDs.

    Example:
        ``registry = CandidateProposalRegistry(); registry.add(proposal)``.
    """

    def __init__(self, proposals: list[CandidateProposal] | None = None) -> None:
        """Initialize a candidate registry and validate initial uniqueness.

        Args:
            proposals: Optional initial candidate records.

        Returns:
            ``None``; the registry is ready for additions.

        Example:
            ``CandidateProposalRegistry([proposal])``.
        """
        self._proposals: dict[str, CandidateProposal] = {}
        for proposal in proposals or []:
            self.add(proposal)

    def add(self, proposal: CandidateProposal) -> None:
        """Add one candidate or reject a deterministic duplicate.

        Args:
            proposal: Candidate proposal to retain.

        Returns:
            ``None`` after insertion.

        Raises:
            CandidateProposalError: If the candidate ID already exists.

        Example:
            ``registry.add(proposal)`` preserves a review candidate.
        """
        if proposal.candidate_id in self._proposals:
            raise CandidateProposalError(
                f"duplicate candidate proposal: {proposal.candidate_id}"
            )
        self._proposals[proposal.candidate_id] = proposal

    def records(self) -> list[CandidateProposal]:
        """Return candidates in deterministic ID order.

        Args:
            None.

        Returns:
            Candidate proposals sorted by candidate ID.

        Example:
            ``registry.records()`` supplies a stable review queue.
        """
        return [self._proposals[key] for key in sorted(self._proposals)]


def _required_text(raw: Mapping[str, Any], key: str) -> str:
    """Extract one non-empty untrusted string field."""
    value = raw.get(key)
    if not isinstance(value, str) or not value.strip():
        raise CandidateProposalError(f"proposal field {key!r} is required")
    return value.strip()


def create_candidate_proposal(
    raw: Mapping[str, Any],
    source_units: Mapping[str, SourceUnit],
    *,
    run_id: str,
    profile_id: str,
    inventory_id: str,
) -> CandidateProposal:
    """Convert untrusted structured output into a source-linked candidate record.

    Args:
        raw: Untrusted mapping containing statement, quote, relation, and rationale.
        source_units: Current local source units keyed by deterministic ID.
        run_id: Local run identifier.
        profile_id: Retrieval/model profile reference.
        inventory_id: Dependency/model inventory reference.

    Returns:
        Candidate-only claim/evidence proposal with flagged-low evidence.

    Raises:
        CandidateProposalError: If fields, atomicity, source reference, or metadata fail.

    Example:
        ``create_candidate_proposal(raw, units, run_id="r1", profile_id="lexical-baseline", inventory_id="pypdf")``.
    """
    if not isinstance(raw, Mapping):
        raise CandidateProposalError("proposal output must be a mapping")
    run = run_id.strip() if isinstance(run_id, str) else ""
    profile = profile_id.strip() if isinstance(profile_id, str) else ""
    inventory = inventory_id.strip() if isinstance(inventory_id, str) else ""
    if not run or not profile or not inventory:
        raise CandidateProposalError("run, profile, and inventory references are required")
    source_unit_id = _required_text(raw, "source_unit_id")
    source_unit = source_units.get(source_unit_id)
    if source_unit is None:
        raise CandidateProposalError(f"source unit is not local: {source_unit_id}")
    statement = _required_text(raw, "statement")
    claim_type = _required_text(raw, "claim_type")
    quote = _required_text(raw, "quote")
    relation = _required_text(raw, "relation")
    rationale = _required_text(raw, "rationale")
    try:
        claim_id = "claim-candidate:" + sha256(
            "\x1f".join((run, profile, source_unit_id, statement)).encode("utf-8")
        ).hexdigest()
        evidence_id = "evidence-candidate:" + sha256(
            "\x1f".join((run, profile, source_unit_id, quote)).encode("utf-8")
        ).hexdigest()
        claim = create_claim(claim_id, statement, claim_type)
        evidence = create_evidence(
            evidence_id,
            claim,
            source_unit,
            quote,
            relation,
            extraction_method="candidate-proposal",
        )
    except (AtomicClaimError, ValueError) as error:
        message = str(error)
        if "atomic" in message.lower() or "assertion" in message.lower():
            raise CandidateProposalError(f"claim is not atomic: {message}") from error
        raise CandidateProposalError(f"invalid candidate proposal: {message}") from error
    claim.review_state = ReviewState.CANDIDATE
    evidence.review_state = ReviewState.CANDIDATE
    evidence.verification_status = evidence.verification_status
    candidate_id = "candidate:" + sha256(
        "\x1f".join((run, profile, source_unit_id, statement, quote)).encode("utf-8")
    ).hexdigest()
    return CandidateProposal(
        candidate_id=candidate_id,
        claim=claim,
        evidence=evidence,
        rationale=rationale,
        run_id=run,
        profile_id=profile,
        inventory_id=inventory,
    )
