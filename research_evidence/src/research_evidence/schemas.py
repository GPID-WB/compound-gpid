"""Created 2026-08-12. Strict canonical records for evidence decisions."""
from __future__ import annotations

from enum import Enum
from typing import Any, Literal, Optional

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator


class SourceOrigin(str, Enum):
    """Identify whether a source is local, external, or unresolved.

    Args:
        value: Serialized source origin.

    Returns:
        A validated source origin.

    Example:
        ``SourceOrigin.REPO_LOCAL`` is the only active v1 origin.
    """

    REPO_LOCAL = "repo-local"
    EXTERNAL_OPT_IN = "external-opt-in"
    UNKNOWN = "unknown"


class LocatorKind(str, Enum):
    """Enumerate typed source locator formats.

    Args:
        value: Serialized locator kind.

    Returns:
        A validated locator kind.

    Example:
        ``LocatorKind.MARKDOWN_BLOCK`` identifies a Markdown block.
    """

    PDF_TEXT = "pdf_text"
    PDF_IMAGE = "pdf_image"
    DOCX_PARAGRAPH = "docx_paragraph"
    DOCX_TABLE_ROW = "docx_table_row"
    MARKDOWN_BLOCK = "markdown_block"
    LATEX_BLOCK = "latex_block"
    HTML_BLOCK = "html_block"
    LEGACY_LOCATOR = "legacy_locator"


class VerificationStatus(str, Enum):
    """Record the machine-readable quotation verification outcome.

    Args:
        value: Serialized verification status.

    Returns:
        A validated verification status.

    Example:
        ``VerificationStatus.VERIFIED_HIGH`` marks a successful exact check.
    """

    VERIFIED_HIGH = "verified-high"
    FLAGGED_MEDIUM = "flagged-medium"
    FLAGGED_LOW = "flagged-low"
    STALE = "stale"
    ABSTAINED = "abstained"
    REJECTED = "rejected"


class ReviewState(str, Enum):
    """Record the researcher's review state for a canonical record.

    Args:
        value: Serialized review state.

    Returns:
        A validated review state.

    Example:
        ``ReviewState.CANDIDATE`` keeps a new record out of approval.
    """

    CANDIDATE = "candidate"
    IN_REVIEW = "in-review"
    APPROVED = "approved"
    FLAGGED = "flagged"
    REJECTED = "rejected"
    STALE = "stale"


class EvidenceRelation(str, Enum):
    """Describe how evidence relates to a claim.

    Args:
        value: Serialized relation.

    Returns:
        A validated evidence relation.

    Example:
        ``EvidenceRelation.SUPPORTS`` links supporting source text.
    """

    SUPPORTS = "supports"
    CONTRADICTS = "contradicts"
    CONTEXTUALIZES = "contextualizes"


class ClaimType(str, Enum):
    """Classify the content of an atomic research claim.

    Args:
        value: Serialized claim type.

    Returns:
        A validated claim type.

    Example:
        ``ClaimType.FACTUAL`` represents an empirical statement.
    """

    FACTUAL = "factual"
    METHODOLOGICAL = "methodological"
    INTERPRETIVE = "interpretive"
    NORMATIVE = "normative"


class TypedLocator(BaseModel):
    """Represent a deterministic, format-specific source locator.

    Args:
        kind: Format-specific locator kind.
        page: One-based page for PDF locators.
        block: One-based block/paragraph number where applicable.
        line_start: One-based start line where available.
        line_end: One-based end line where available.
        anchor: Optional heading or HTML anchor.
        unit_fingerprint: SHA-256 fingerprint of normalized unit text.

    Returns:
        A locator whose fields are valid for its selected format.

    Raises:
        ValueError: If fields do not match the selected locator kind.

    Example:
        ``TypedLocator(kind="markdown_block", block=1, unit_fingerprint="sha256:" + "a" * 64)``.
    """

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    kind: LocatorKind
    page: Optional[int] = Field(default=None, gt=0)
    block: Optional[int] = Field(default=None, gt=0)
    line_start: Optional[int] = Field(default=None, gt=0)
    line_end: Optional[int] = Field(default=None, gt=0)
    anchor: Optional[str] = None
    unit_fingerprint: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_fields(self) -> "TypedLocator":
        """Reject locator fields that are not valid for the selected kind.

        Args:
            self: Locator being validated.

        Returns:
            The validated locator.

        Raises:
            ValueError: If required or forbidden fields are present.

        Example:
            ``locator.validate_fields()`` returns a valid typed locator.
        """
        if self.line_start is not None and self.line_end is not None:
            if self.line_end < self.line_start:
                raise ValueError("line_end cannot precede line_start.")
        if self.kind == LocatorKind.MARKDOWN_BLOCK:
            if self.block is None:
                raise ValueError("markdown_block locators require block.")
            if self.page is not None:
                raise ValueError("markdown_block locators cannot contain page.")
        elif self.kind == LocatorKind.PDF_TEXT:
            if self.page is None:
                raise ValueError("pdf_text locators require page.")
            if self.block is not None:
                raise ValueError("pdf_text locators cannot contain block.")
        elif self.kind == LocatorKind.PDF_IMAGE:
            if self.page is None:
                raise ValueError("pdf_image locators require page.")
        elif self.kind in {LocatorKind.DOCX_PARAGRAPH, LocatorKind.DOCX_TABLE_ROW}:
            if self.block is None:
                raise ValueError(f"{self.kind.value} locators require block.")
        elif self.kind in {LocatorKind.LATEX_BLOCK, LocatorKind.HTML_BLOCK}:
            if self.block is None and self.anchor is None:
                raise ValueError(f"{self.kind.value} locators require block or anchor.")
        elif self.kind == LocatorKind.LEGACY_LOCATOR:
            if not self.anchor:
                raise ValueError("legacy_locator locators require anchor text.")
        return self


class ResourceRecord(BaseModel):
    """Identify one logical local or legacy research resource.

    Args:
        resource_id: Stable logical resource identifier.
        origin: Local, external-quarantine, or unresolved origin.
        relative_path: Project-relative path when locally available.
        sha256: Current resource byte hash, when known.

    Returns:
        A validated resource record.

    Example:
        ``ResourceRecord(resource_id="r1", origin="repo-local")``.
    """

    model_config = ConfigDict(extra="allow")

    resource_id: str = Field(min_length=1)
    origin: SourceOrigin
    relative_path: Optional[str] = None
    sha256: Optional[str] = Field(default=None, pattern=r"^[0-9a-f]{64}$")


class SourceVersion(BaseModel):
    """Identify immutable resource bytes and parser/locator contracts.

    Args:
        source_version_id: Deterministic immutable version identifier.
        resource_id: Logical resource identifier.
        sha256: Original resource byte hash.
        parser_profile: Exact parser and configuration profile.
        parser_version: Exact parser package or runtime version.
        locator_schema_version: Typed locator contract version.
        original_authority: Whether original bytes remain available.

    Returns:
        A validated source-version record.

    Example:
        ``SourceVersion(source_version_id="v1", resource_id="r1", sha256="a" * 64, parser_profile="markdown-v1", locator_schema_version="locator-v1")``.
    """

    model_config = ConfigDict(extra="forbid")

    source_version_id: str = Field(min_length=1)
    resource_id: str = Field(min_length=1)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    parser_profile: str = Field(min_length=1)
    parser_version: str = "unknown"
    locator_schema_version: str = Field(min_length=1)
    original_authority: bool = True


class SourceUnit(BaseModel):
    """Store one parsed unit tied to a source version and typed locator.

    Args:
        source_unit_id: Deterministic unit identifier.
        source_version_id: Immutable source-version identifier.
        locator: Typed locator for the unit.
        text: Extracted text used for review and indexing.
        heading_path: Heading context retained for inspection.
        unit_type: Prose, table, equation, figure, or other semantic unit type.
        review_required: Whether the unit requires special researcher review.
        parser_metadata: Parser and format metadata retained for provenance.

    Returns:
        A validated source unit.

    Example:
        ``SourceUnit(source_unit_id="u1", source_version_id="v1", locator=locator, text="Sentence")``.
    """

    model_config = ConfigDict(extra="forbid")

    source_unit_id: str = Field(min_length=1)
    source_version_id: str = Field(min_length=1)
    locator: TypedLocator
    text: str = Field(min_length=1)
    heading_path: list[str] = Field(default_factory=list)
    unit_type: Literal[
        "prose",
        "table",
        "figure",
        "equation",
        "caption",
        "footnote",
        "image",
        "unknown",
    ] = "prose"
    review_required: bool = False
    parser_metadata: dict[str, str] = Field(default_factory=dict)


class EvidenceRecord(BaseModel):
    """Store a verbatim, source-linked evidence record.

    Args:
        evidence_id: Stable evidence identifier.
        source_unit_id: Source unit containing the quotation.
        source_version_id: Source version verified by the record.
        locator: Typed locator resolved during verification.
        quote: Verbatim quotation supplied for checking.
        extraction_method: Manual or parser method that produced the quote.
        verification_status: Machine-readable verification outcome.
        confidence: High, medium, or low confidence label.
        review_state: Researcher review state.
        relation: Claim relation represented by this evidence.
        original_authority_verified: Whether the original bytes were checked.
        stale: Whether a source lifecycle event invalidated the decision.

    Returns:
        A validated evidence record.

    Example:
        ``EvidenceRecord(evidence_id="e1", source_unit_id="u1", source_version_id="v1", locator=locator, quote="Text", extraction_method="manual", verification_status="flagged-low", confidence="low", review_state="candidate", relation="supports")``.
    """

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    evidence_id: str = Field(min_length=1)
    source_unit_id: str = Field(min_length=1)
    source_version_id: str = Field(min_length=1)
    locator: TypedLocator
    quote: str = Field(min_length=1)
    extraction_method: str = Field(min_length=1)
    verification_status: VerificationStatus
    confidence: Literal["high", "medium", "low"]
    review_state: ReviewState
    relation: EvidenceRelation
    original_authority_verified: bool = False
    stale: bool = False


class ClaimRecord(BaseModel):
    """Store one atomic claim and its evidence references.

    Args:
        claim_id: Stable claim identifier.
        statement: One factual, methodological, interpretive, or normative statement.
        claim_type: Claim classification.
        evidence_ids: Evidence records linked to the statement.
        review_state: Researcher review state.
        atomic: Whether the statement passed atomicity review.
        stale: Whether linked source changes require re-verification.

    Returns:
        A validated claim record.

    Example:
        ``ClaimRecord(claim_id="c1", statement="The rate fell.", claim_type="factual")``.
    """

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    claim_id: str = Field(min_length=1)
    statement: str = Field(min_length=1)
    claim_type: ClaimType
    evidence_ids: list[str] = Field(default_factory=list)
    review_state: ReviewState
    atomic: bool = True
    stale: bool = False


class AnalysisLink(BaseModel):
    """Link a claim to a downstream analysis artifact without composing prose.

    Args:
        link_id: Stable analysis-link identifier.
        claim_id: Claim supplied to the analysis.
        analysis_ref: Repository-relative analysis reference.
        active: Whether the link is eligible for downstream use.

    Returns:
        A validated analysis link.

    Example:
        ``AnalysisLink(link_id="a1", claim_id="c1", analysis_ref="analysis/model.R")``.
    """

    model_config = ConfigDict(extra="forbid")

    link_id: str = Field(min_length=1)
    claim_id: str = Field(min_length=1)
    analysis_ref: str = Field(min_length=1)
    active: bool = True


class ReviewEvent(BaseModel):
    """Record one append-only researcher decision event.

    Args:
        event_id: Stable event identifier.
        operation_id: Transaction operation that persisted the event.
        target_type: Evidence, claim, or analysis-link target type.
        target_id: Target record identifier.
        action: Human-readable state-changing action.
        actor: Local actor label.
        revision: Aggregate revision after the action.

    Returns:
        A validated review event.

    Example:
        ``ReviewEvent(event_id="r1", operation_id="op1", target_type="evidence", target_id="e1", action="approve", actor="researcher", revision=1)``.
    """

    model_config = ConfigDict(extra="forbid")

    event_id: str = Field(min_length=1)
    operation_id: str = Field(min_length=1)
    target_type: str = Field(min_length=1)
    target_id: str = Field(min_length=1)
    action: str = Field(min_length=1)
    actor: str = Field(min_length=1)
    revision: int = Field(ge=0)


class TransactionJournalEntry(BaseModel):
    """Describe a prepared, committed, or aborted canonical transaction.

    Args:
        operation_id: Unique operation identifier.
        phase: Journal phase.
        expected_revision: Revision supplied by the caller.
        actual_revision: Revision observed before mutation.
        affected_files: Root-relative canonical files.
        previous_hashes: Hashes before staging.
        new_hashes: Hashes in staged content.
        payload_hash: Hash of the transaction payload.
        actor: Local actor label.
        action: State-changing action.

    Returns:
        A validated transaction journal record.

    Example:
        ``TransactionJournalEntry(operation_id="op1", phase="prepare", expected_revision=0, actual_revision=0, affected_files=[], previous_hashes={}, new_hashes={}, payload_hash="a" * 64, actor="researcher", action="write")``.
    """

    model_config = ConfigDict(extra="forbid")

    operation_id: str = Field(min_length=1)
    phase: Literal["prepare", "commit", "abort"]
    expected_revision: int = Field(ge=0)
    actual_revision: int = Field(ge=0)
    affected_files: list[str] = Field(default_factory=list)
    previous_hashes: dict[str, Optional[str]] = Field(default_factory=dict)
    new_hashes: dict[str, str] = Field(default_factory=dict)
    payload_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    actor: str = Field(min_length=1)
    action: str = Field(min_length=1)


def is_approved_evidence(evidence: EvidenceRecord) -> bool:
    """Return whether evidence is eligible for approved downstream use.

    Args:
        evidence: Evidence record to evaluate.

    Returns:
        ``True`` only for high-confidence, original-verified, approved, non-stale evidence.

    Example:
        ``is_approved_evidence(evidence)`` gates a claim import.
    """
    return (
        evidence.verification_status == VerificationStatus.VERIFIED_HIGH
        and evidence.confidence == "high"
        and evidence.review_state == ReviewState.APPROVED
        and evidence.original_authority_verified
        and not evidence.stale
        and evidence.locator.kind != LocatorKind.LEGACY_LOCATOR
    )


def canonical_yaml(payload: Any) -> str:
    """Serialize a mapping or model as deterministic, readable YAML.

    Args:
        payload: Pydantic model or YAML-compatible mapping/list.

    Returns:
        Sorted-key YAML text ending with a newline.

    Example:
        ``canonical_yaml({"b": 2, "a": 1})`` orders keys deterministically.
    """
    if isinstance(payload, BaseModel):
        payload = payload.model_dump(mode="json", exclude_none=True)
    return yaml.safe_dump(payload, sort_keys=True, allow_unicode=False)


def load_yaml_mapping(text: str) -> dict[str, Any]:
    """Parse one canonical YAML mapping and reject non-mapping documents.

    Args:
        text: YAML document text.

    Returns:
        Parsed mapping.

    Raises:
        ValueError: If the YAML is malformed or not a mapping.

    Example:
        ``load_yaml_mapping("records: []")`` returns ``{"records": []}``.
    """
    try:
        payload = yaml.safe_load(text)
    except yaml.YAMLError as error:
        raise ValueError(f"Invalid canonical YAML: {error}") from error
    if not isinstance(payload, dict):
        raise ValueError("Canonical YAML document must be a mapping.")
    return payload
