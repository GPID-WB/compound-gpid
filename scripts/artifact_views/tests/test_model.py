"""Tests for immutable artifact source and relationship models."""
from __future__ import annotations

from pathlib import Path
from typing import Tuple

import pytest

from artifact_views.errors import ArtifactModelError, ArtifactParseError
from artifact_views.model import (
    Alternative,
    ArtifactIdentity,
    BrainstormDocument,
    CompletionRow,
    Frontmatter,
    LexicalBlock,
    Phase,
    PlanDocument,
    PresentationElement,
    Requirement,
    SourceSpan,
    Step,
    SubstantiveBlock,
    stable_block_id,
)
from artifact_views.schema import ArtifactKind, SchemaSupport


def _source_blocks() -> Tuple[Tuple[LexicalBlock, ...], Tuple[SubstantiveBlock, ...]]:
    parts = ("# Title\n", "\n", "Body\n")
    lines = ((1, 1), (2, 2), (3, 3))
    kinds = ("atx_heading", "blank_line", "paragraph")
    substantive_flags = (True, False, True)
    lexical = []
    substantive = []
    byte_offset = 0
    for index, (raw, line_span, kind, is_substantive) in enumerate(
        zip(parts, lines, kinds, substantive_flags),
        start=1,
    ):
        next_offset = byte_offset + len(raw.encode("utf-8"))
        span = SourceSpan(
            start_line=line_span[0],
            end_line=line_span[1],
            start_byte=byte_offset,
            end_byte=next_offset,
        )
        block_id = stable_block_id(index)
        lexical.append(
            LexicalBlock(block_id, kind, span, raw, is_substantive)
        )
        if is_substantive:
            substantive.append(SubstantiveBlock(block_id, kind, span))
        byte_offset = next_offset
    return tuple(lexical), tuple(substantive)


def _identity(kind: ArtifactKind) -> ArtifactIdentity:
    return ArtifactIdentity(
        kind=kind,
        source_path=Path(".cg-docs/plans/example.md"),
        title="Example",
        schema_version=1,
        schema_support=SchemaSupport.STRICT,
    )


def _brainstorm() -> BrainstormDocument:
    lexical, substantive = _source_blocks()
    return BrainstormDocument(
        identity=_identity(ArtifactKind.BRAINSTORM),
        frontmatter=Frontmatter(()),
        lexical_blocks=lexical,
        substantive_blocks=substantive,
        source_length_bytes=lexical[-1].span.end_byte,
    )


def test_models_preserve_source_order_identity_and_spans() -> None:
    document = _brainstorm()
    assert document.identity.kind is ArtifactKind.BRAINSTORM
    assert [block.block_id for block in document.lexical_blocks] == [
        "block-0001",
        "block-0002",
        "block-0003",
    ]
    assert document.substantive_blocks[1].span == SourceSpan(3, 3, 9, 14)
    assert document.alternatives == ()


def test_multiline_block_and_empty_optional_relationships_are_stable() -> None:
    raw = "| A |\n|---|\n| B |\n"
    span = SourceSpan(1, 3, 0, len(raw.encode("utf-8")))
    block = LexicalBlock("block-0001", "pipe_table", span, raw, True)
    document = PlanDocument(
        identity=_identity(ArtifactKind.PLAN),
        frontmatter=Frontmatter(()),
        lexical_blocks=(block,),
        substantive_blocks=(
            SubstantiveBlock("block-0001", "pipe_table", span),
        ),
        source_length_bytes=span.end_byte,
    )
    assert document.requirements == ()
    assert document.phases == ()
    assert document.steps == ()
    assert document.completion_rows == ()
    assert document.lexical_blocks[0].span.end_line == 3


def test_source_ledger_rejects_duplicate_block_ids() -> None:
    lexical, substantive = _source_blocks()
    duplicate = LexicalBlock(
        lexical[0].block_id,
        lexical[1].kind,
        lexical[1].span,
        lexical[1].raw,
        lexical[1].substantive,
    )
    with pytest.raises(ArtifactModelError, match="Duplicate lexical block ID"):
        BrainstormDocument(
            identity=_identity(ArtifactKind.BRAINSTORM),
            frontmatter=Frontmatter(()),
            lexical_blocks=(lexical[0], duplicate, lexical[2]),
            substantive_blocks=substantive,
            source_length_bytes=lexical[-1].span.end_byte,
        )


def test_source_ledger_rejects_overlaps_and_gaps() -> None:
    lexical, substantive = _source_blocks()
    overlap_span = SourceSpan(2, 2, 7, 9)
    overlapping = LexicalBlock(
        lexical[1].block_id,
        lexical[1].kind,
        overlap_span,
        lexical[1].raw,
        False,
    )
    with pytest.raises(ArtifactModelError, match="overlaps previous block"):
        BrainstormDocument(
            identity=_identity(ArtifactKind.BRAINSTORM),
            frontmatter=Frontmatter(()),
            lexical_blocks=(lexical[0], overlapping, lexical[2]),
            substantive_blocks=substantive,
            source_length_bytes=lexical[-1].span.end_byte,
        )

    gap_span = SourceSpan(2, 2, 9, 10)
    gap = LexicalBlock(
        lexical[1].block_id,
        lexical[1].kind,
        gap_span,
        lexical[1].raw,
        False,
    )
    with pytest.raises(ArtifactModelError, match="leaves a byte gap"):
        BrainstormDocument(
            identity=_identity(ArtifactKind.BRAINSTORM),
            frontmatter=Frontmatter(()),
            lexical_blocks=(lexical[0], gap, lexical[2]),
            substantive_blocks=substantive,
            source_length_bytes=lexical[-1].span.end_byte,
        )


def test_every_substantive_lexical_block_requires_one_source_identity() -> None:
    lexical, substantive = _source_blocks()
    with pytest.raises(ArtifactModelError, match="Substantive ownership mismatch"):
        BrainstormDocument(
            identity=_identity(ArtifactKind.BRAINSTORM),
            frontmatter=Frontmatter(()),
            lexical_blocks=lexical,
            substantive_blocks=(substantive[0],),
            source_length_bytes=lexical[-1].span.end_byte,
        )


def test_derived_presentation_elements_cannot_claim_source_ownership() -> None:
    with pytest.raises(ArtifactModelError, match="Derived presentation element"):
        PresentationElement(
            element_id="coverage-map",
            kind="coverage",
            source_block_ids=("block-0001",),
            derived=True,
        )
    source_element = PresentationElement(
        element_id="source-heading",
        kind="heading",
        source_block_ids=("block-0001",),
        derived=False,
    )
    assert source_element.source_block_ids == ("block-0001",)


def test_plan_relationship_ids_must_be_unique() -> None:
    lexical, substantive = _source_blocks()
    with pytest.raises(ArtifactModelError, match="Duplicate requirement ID 'R1'"):
        PlanDocument(
            identity=_identity(ArtifactKind.PLAN),
            frontmatter=Frontmatter(()),
            lexical_blocks=lexical,
            substantive_blocks=substantive,
            source_length_bytes=lexical[-1].span.end_byte,
            requirements=(
                Requirement("R1", "First", "block-0003"),
                Requirement("R1", "Second", "block-0003"),
            ),
        )


def test_typed_plan_relationships_retain_source_identity() -> None:
    lexical, substantive = _source_blocks()
    document = PlanDocument(
        identity=_identity(ArtifactKind.PLAN),
        frontmatter=Frontmatter(()),
        lexical_blocks=lexical,
        substantive_blocks=substantive,
        source_length_bytes=lexical[-1].span.end_byte,
        requirements=(Requirement("R1", "Requirement", "block-0003"),),
        phases=(Phase(1, "Contract", "block-0001"),),
        steps=(Step(1, "Build", ("R1",), ("block-0003",), 1),),
        completion_rows=(
            CompletionRow(
                "verification",
                "V1",
                (("Required", "yes"),),
                "block-0003",
                1,
                True,
            ),
        ),
    )
    assert document.steps[0].requirement_ids == ("R1",)
    assert document.steps[0].phase_number == 1
    assert document.completion_rows[0].required is True


def test_typed_errors_include_path_span_and_corrective_action() -> None:
    error = ArtifactParseError(
        message="Unclosed fenced code block.",
        source_path=Path(".cg-docs/plans/example.md"),
        span=SourceSpan(8, 12, 40, 90),
        corrective_action="Close the fence opened on line 8.",
    )
    rendered = str(error)
    assert ".cg-docs/plans/example.md:8-12" in rendered
    assert "Unclosed fenced code block." in rendered
    assert "Close the fence opened on line 8." in rendered
