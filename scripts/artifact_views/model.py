"""Immutable source-ledger and semantic models for workflow artifacts."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional, Tuple, Union

from artifact_views.errors import ArtifactModelError
from artifact_views.schema import ArtifactKind, SchemaSupport

CompletionPhase = Optional[Union[int, str]]


@dataclass(frozen=True)
class SourceSpan:
    """One-based line span and half-open UTF-8 byte range."""

    start_line: int
    end_line: int
    start_byte: int
    end_byte: int

    def __post_init__(self) -> None:
        if self.start_line < 1 or self.end_line < self.start_line:
            raise ValueError("Source lines must be one-based and ordered.")
        if self.start_byte < 0 or self.end_byte < self.start_byte:
            raise ValueError("Source byte offsets must be non-negative and ordered.")


@dataclass(frozen=True)
class ArtifactIdentity:
    """Canonical source identity and schema compatibility state."""

    kind: ArtifactKind
    source_path: Path
    title: str
    schema_version: Optional[Union[int, str]]
    schema_support: SchemaSupport

    def __post_init__(self) -> None:
        if not self.title.strip():
            raise ValueError("Artifact title must be non-empty.")
        if not str(self.source_path):
            raise ValueError("Artifact source path must be non-empty.")


@dataclass(frozen=True)
class FrontmatterField:
    """One parsed frontmatter field with its source span."""

    key: str
    value: Any
    span: SourceSpan


@dataclass(frozen=True)
class Frontmatter:
    """Ordered immutable frontmatter fields."""

    fields: Tuple[FrontmatterField, ...]

    def __post_init__(self) -> None:
        keys = [field.key for field in self.fields]
        duplicate = _first_duplicate(keys)
        if duplicate is not None:
            raise ArtifactModelError(
                f"Duplicate frontmatter field {duplicate!r}.",
                span=next(
                    field.span for field in self.fields if field.key == duplicate
                ),
                corrective_action="Keep exactly one value for each field.",
            )

    def get(self, key: str, default: Any = None) -> Any:
        """Return one parsed frontmatter value.

        Args:
            key: Field name to find.
            default: Value returned when the field is absent.

        Returns:
            The stored field value or ``default``.

        Example:
            >>> Frontmatter(()).get("title") is None
            True
        """
        for field in self.fields:
            if field.key == key:
                return field.value
        return default


@dataclass(frozen=True)
class LexicalBlock:
    """One grammar token accounting for an exact source byte range."""

    block_id: str
    kind: str
    span: SourceSpan
    raw: str
    substantive: bool


@dataclass(frozen=True)
class SubstantiveBlock:
    """One source-backed semantic block eligible for rendered ownership."""

    source_id: str
    kind: str
    span: SourceSpan


@dataclass(frozen=True)
class Requirement:
    """A Plan requirement parsed from the requirements table."""

    identifier: str
    text: str
    source_block_id: str


@dataclass(frozen=True)
class Alternative:
    """A Brainstorm alternative and its ordered source blocks."""

    title: str
    source_block_ids: Tuple[str, ...]


@dataclass(frozen=True)
class Phase:
    """A numbered Plan phase heading."""

    number: int
    title: str
    source_block_id: str


@dataclass(frozen=True)
class Step:
    """A globally numbered implementation step and declared mappings."""

    number: int
    title: str
    requirement_ids: Tuple[str, ...]
    source_block_ids: Tuple[str, ...]
    phase_number: Optional[int] = None


@dataclass(frozen=True)
class TestCase:
    """A source-backed test command or test scenario."""

    name: str
    command: str
    source_block_id: str


@dataclass(frozen=True)
class Risk:
    """A parsed risk and mitigation pair."""

    description: str
    mitigation: str
    source_block_id: str


@dataclass(frozen=True)
class CompletionRow:
    """A verification or constraint row from the completion contract."""

    row_type: str
    identifier: str
    values: Tuple[Tuple[str, str], ...]
    source_block_id: str
    phase: CompletionPhase = None
    required: bool = False

    def value_for(self, header: str, default: str = "") -> str:
        """Return a completion-cell value by normalized header.

        Args:
            header: Normalized table header.
            default: Value returned when no cell matches.

        Returns:
            The matching cell text or ``default``.

        Example:
            >>> row = CompletionRow("verification", "V1", (("required", "yes"),), "b")
            >>> row.value_for("required")
            'yes'
        """
        for name, value in self.values:
            if name == header:
                return value
        return default


@dataclass(frozen=True)
class PresentationElement:
    """A source-backed or explicitly derived presentation element."""

    element_id: str
    kind: str
    source_block_ids: Tuple[str, ...] = ()
    derived: bool = False

    def __post_init__(self) -> None:
        if self.derived and self.source_block_ids:
            raise ArtifactModelError(
                f"Derived presentation element {self.element_id!r} cannot claim "
                "source ownership.",
                corrective_action=(
                    "Remove source block IDs or mark the element as source-backed."
                ),
            )
        if not self.derived and not self.source_block_ids:
            raise ArtifactModelError(
                f"Source-backed presentation element {self.element_id!r} has no "
                "source ownership.",
                corrective_action="Assign at least one substantive source block.",
            )


@dataclass(frozen=True)
class ArtifactDocument:
    """Common immutable document state with a complete lexical ledger."""

    identity: ArtifactIdentity
    frontmatter: Frontmatter
    lexical_blocks: Tuple[LexicalBlock, ...]
    substantive_blocks: Tuple[SubstantiveBlock, ...]
    source_length_bytes: int

    def __post_init__(self) -> None:
        _validate_source_ledger(self)


@dataclass(frozen=True)
class BrainstormDocument(ArtifactDocument):
    """Typed Brainstorm source model."""

    alternatives: Tuple[Alternative, ...] = ()

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.identity.kind is not ArtifactKind.BRAINSTORM:
            raise _model_error(
                self,
                "BrainstormDocument requires a brainstorm identity.",
                "Use ArtifactKind.BRAINSTORM for this source.",
            )
        _validate_relation_sources(
            self,
            tuple(
                block_id
                for alternative in self.alternatives
                for block_id in alternative.source_block_ids
            ),
        )


@dataclass(frozen=True)
class PlanDocument(ArtifactDocument):
    """Typed Plan source model and source-derived execution relationships."""

    requirements: Tuple[Requirement, ...] = ()
    phases: Tuple[Phase, ...] = ()
    steps: Tuple[Step, ...] = ()
    tests: Tuple[TestCase, ...] = ()
    risks: Tuple[Risk, ...] = ()
    completion_rows: Tuple[CompletionRow, ...] = ()

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.identity.kind is not ArtifactKind.PLAN:
            raise _model_error(
                self,
                "PlanDocument requires a plan identity.",
                "Use ArtifactKind.PLAN for this source.",
            )
        _validate_unique_relationships(self)
        relation_sources = tuple(
            requirement.source_block_id for requirement in self.requirements
        )
        relation_sources += tuple(phase.source_block_id for phase in self.phases)
        relation_sources += tuple(
            block_id for step in self.steps for block_id in step.source_block_ids
        )
        relation_sources += tuple(test.source_block_id for test in self.tests)
        relation_sources += tuple(risk.source_block_id for risk in self.risks)
        relation_sources += tuple(
            row.source_block_id for row in self.completion_rows
        )
        _validate_relation_sources(self, relation_sources)


def stable_block_id(index: int) -> str:
    """Create the stable document-local ID for a one-based block index.

    Args:
        index: One-based block position in source order.

    Returns:
        A zero-padded stable ID such as ``block-0001``.

    Raises:
        ValueError: If ``index`` is less than one.

    Example:
        >>> stable_block_id(12)
        'block-0012'
    """
    if index < 1:
        raise ValueError("Block index must be at least one.")
    return f"block-{index:04d}"


def _validate_source_ledger(document: ArtifactDocument) -> None:
    if document.source_length_bytes < 0:
        raise _model_error(
            document,
            "Source byte length cannot be negative.",
            "Read the source as strict UTF-8 and pass its exact byte length.",
        )

    lexical_ids = [block.block_id for block in document.lexical_blocks]
    duplicate_lexical = _first_duplicate(lexical_ids)
    if duplicate_lexical is not None:
        raise _model_error(
            document,
            f"Duplicate lexical block ID {duplicate_lexical!r}.",
            "Assign stable IDs once in source order.",
        )

    expected_start = 0
    for block in document.lexical_blocks:
        if block.span.start_byte < expected_start:
            raise _model_error(
                document,
                f"Lexical block {block.block_id!r} overlaps previous block.",
                "Tokenize each source byte exactly once in source order.",
                block.span,
            )
        if block.span.start_byte > expected_start:
            raise _model_error(
                document,
                f"Lexical block {block.block_id!r} leaves a byte gap.",
                "Represent whitespace and metadata in the lexical ledger.",
                block.span,
            )
        expected_start = block.span.end_byte

    if expected_start != document.source_length_bytes:
        raise _model_error(
            document,
            "Lexical ledger does not cover the complete source byte range.",
            "Tokenize through the final source byte, including trailing newlines.",
        )

    for block in document.lexical_blocks:
        raw_length = len(block.raw.encode("utf-8"))
        span_length = block.span.end_byte - block.span.start_byte
        if raw_length != span_length:
            raise _model_error(
                document,
                f"Lexical block {block.block_id!r} raw bytes do not match its span.",
                "Compute byte offsets from the unmodified UTF-8 source.",
                block.span,
            )

    substantive_ids = [block.source_id for block in document.substantive_blocks]
    duplicate_substantive = _first_duplicate(substantive_ids)
    if duplicate_substantive is not None:
        raise _model_error(
            document,
            f"Duplicate substantive block ID {duplicate_substantive!r}.",
            "Create exactly one substantive identity per source block.",
        )

    expected_substantive = {
        block.block_id for block in document.lexical_blocks if block.substantive
    }
    actual_substantive = set(substantive_ids)
    if expected_substantive != actual_substantive:
        missing = sorted(expected_substantive - actual_substantive)
        extra = sorted(actual_substantive - expected_substantive)
        raise _model_error(
            document,
            "Substantive ownership mismatch "
            f"(missing={missing}, extra={extra}).",
            "Map every substantive lexical block exactly once and no metadata blocks.",
        )

    lexical_by_id = {block.block_id: block for block in document.lexical_blocks}
    for block in document.substantive_blocks:
        lexical = lexical_by_id[block.source_id]
        if block.span != lexical.span or block.kind != lexical.kind:
            raise _model_error(
                document,
                f"Substantive block {block.source_id!r} changed source identity.",
                "Reuse the lexical block kind and span without modification.",
                block.span,
            )


def _validate_unique_relationships(document: PlanDocument) -> None:
    groups = (
        ("requirement", [item.identifier for item in document.requirements]),
        ("phase", [str(item.number) for item in document.phases]),
        ("step", [str(item.number) for item in document.steps]),
        (
            "completion",
            [
                f"{item.row_type}:{item.identifier}"
                for item in document.completion_rows
            ],
        ),
    )
    for label, values in groups:
        duplicate = _first_duplicate(values)
        if duplicate is not None:
            display = duplicate.split(":", 1)[-1]
            raise _model_error(
                document,
                f"Duplicate {label} ID {display!r}.",
                f"Use one unique {label} identifier per Plan.",
            )


def _validate_relation_sources(
    document: ArtifactDocument,
    source_block_ids: Tuple[str, ...],
) -> None:
    known = {block.source_id for block in document.substantive_blocks}
    unknown = sorted(set(source_block_ids) - known)
    if unknown:
        raise _model_error(
            document,
            f"Typed relationships reference unknown source blocks: {unknown}.",
            "Reference only substantive block IDs from this document.",
        )


def _first_duplicate(values: list) -> Optional[str]:
    seen = set()
    for value in values:
        if value in seen:
            return str(value)
        seen.add(value)
    return None


def _model_error(
    document: ArtifactDocument,
    message: str,
    corrective_action: str,
    span: Optional[SourceSpan] = None,
) -> ArtifactModelError:
    return ArtifactModelError(
        message,
        source_path=document.identity.source_path,
        span=span,
        corrective_action=corrective_action,
    )
