"""Tests for fence-aware artifact parsing and exact source accounting."""
from __future__ import annotations

from pathlib import Path

import pytest

from artifact_views.errors import ArtifactParseError
from artifact_views.model import BrainstormDocument, PlanDocument
from artifact_views.parser import parse_artifact
from artifact_views.schema import ArtifactKind, SchemaSupport

FIXTURES = Path(__file__).parent / "fixtures"


def _fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def test_parse_strict_brainstorm_preserves_ledger_and_alternatives() -> None:
    source = _fixture("strict_brainstorm.md")
    document = parse_artifact(
        source,
        Path(".cg-docs/brainstorms/strict.md"),
        ArtifactKind.BRAINSTORM,
    )
    assert isinstance(document, BrainstormDocument)
    assert document.source_length_bytes == len(source.encode("utf-8"))
    assert [alternative.title for alternative in document.alternatives] == [
        "Approach 1: Deterministic parser",
        "Approach 2: Generic conversion",
    ]
    assert document.identity.schema_support is SchemaSupport.STRICT
    assert [block.block_id for block in document.lexical_blocks] == [
        f"block-{index:04d}"
        for index in range(1, len(document.lexical_blocks) + 1)
    ]


def test_parse_strict_plan_builds_source_derived_relationships() -> None:
    document = parse_artifact(
        _fixture("strict_plan.md"),
        Path(".cg-docs/plans/strict.md"),
        ArtifactKind.PLAN,
    )
    assert isinstance(document, PlanDocument)
    assert [requirement.identifier for requirement in document.requirements] == [
        "R1",
        "R2",
    ]
    assert document.phases == ()
    assert [step.number for step in document.steps] == [1]
    assert document.steps[0].requirement_ids == ("R1", "R2")
    assert [row.identifier for row in document.completion_rows] == ["V1", "C1"]


def test_parse_phased_plan_assigns_each_step_to_its_phase() -> None:
    document = parse_artifact(
        _fixture("strict_deep_plan.md"),
        Path(".cg-docs/plans/deep.md"),
        ArtifactKind.PLAN,
    )
    assert isinstance(document, PlanDocument)
    assert [(phase.number, phase.title) for phase in document.phases] == [
        (1, "Contract"),
        (2, "Validation"),
    ]
    assert [step.phase_number for step in document.steps] == [1, 2]
    assert [row.phase for row in document.completion_rows] == [1, 2, 1, 2]


def test_headings_and_pipes_inside_fences_are_not_structure() -> None:
    source = _fixture("strict_plan.md").replace(
        "The validator must operate without renderer dependencies.",
        "```markdown\n## Fake Phase\n| ID | Fake |\n|---|---|\n```\n\n"
        "The validator must operate without renderer dependencies.",
    )
    document = parse_artifact(
        source,
        Path(".cg-docs/plans/fenced.md"),
        ArtifactKind.PLAN,
    )
    assert isinstance(document, PlanDocument)
    assert document.phases == ()
    assert sum(block.kind == "fenced_code" for block in document.lexical_blocks) == 1
    assert [requirement.identifier for requirement in document.requirements] == [
        "R1",
        "R2",
    ]


def test_tilde_fences_and_crlf_preserve_exact_bytes() -> None:
    source = _fixture("strict_brainstorm.md").replace(
        "Humans and agents need different views of one canonical artifact.",
        "~~~text\n## Not a section\n~~~",
    )
    source = source.replace("\n", "\r\n")
    document = parse_artifact(
        source,
        Path(".cg-docs/brainstorms/crlf.md"),
        ArtifactKind.BRAINSTORM,
    )
    assert document.source_length_bytes == len(source.encode("utf-8"))
    fenced = [block for block in document.lexical_blocks if block.kind == "fenced_code"]
    assert len(fenced) == 1
    assert fenced[0].raw.startswith("~~~text\r\n")


@pytest.mark.parametrize(
    "transform",
    (
        lambda source: source,
        lambda source: "\ufeff" + source.replace("Strict Brainstorm", "Café Brainstorm"),
        lambda source: source.replace("\n", "\r\n"),
        lambda source: source.rstrip("\n"),
    ),
    ids=("ordinary", "bom-unicode", "crlf", "no-final-newline"),
)
def test_lexical_ledger_reconstructs_exact_source_bytes(transform) -> None:
    source = transform(_fixture("strict_brainstorm.md"))

    document = parse_artifact(
        source,
        Path(".cg-docs/brainstorms/reconstruction.md"),
        ArtifactKind.BRAINSTORM,
    )

    reconstructed = "".join(block.raw for block in document.lexical_blocks)
    assert reconstructed == source
    assert reconstructed.encode("utf-8") == source.encode("utf-8")


def test_pipe_inside_code_span_does_not_split_table_cell() -> None:
    source = _fixture("strict_plan.md").replace(
        "Parse the supported grammar.",
        "Parse the `left | right` code span.",
    )
    document = parse_artifact(
        source,
        Path(".cg-docs/plans/code-span-pipe.md"),
        ArtifactKind.PLAN,
    )
    assert isinstance(document, PlanDocument)
    assert document.requirements[0].text == "Parse the `left | right` code span."


def test_exact_status_comment_is_lexical_but_not_substantive() -> None:
    source = _fixture("strict_brainstorm.md")
    document = parse_artifact(
        source,
        Path(".cg-docs/brainstorms/status.md"),
        ArtifactKind.BRAINSTORM,
    )
    status_blocks = [
        block
        for block in document.lexical_blocks
        if "Valid status values" in block.raw
    ]
    assert len(status_blocks) == 1
    assert status_blocks[0].kind == "raw_html"
    assert status_blocks[0].substantive is False

    similar = source.replace("abandoned -->", "abandoned, archived -->")
    similar_document = parse_artifact(
        similar,
        Path(".cg-docs/brainstorms/similar-status.md"),
        ArtifactKind.BRAINSTORM,
    )
    similar_block = next(
        block
        for block in similar_document.lexical_blocks
        if "Valid status values" in block.raw
    )
    assert similar_block.substantive is True


def test_missing_schema_version_is_classified_as_compatible_legacy() -> None:
    source = _fixture("strict_plan.md").replace(
        "artifact-schema-version: 1\n",
        "",
        1,
    )
    document = parse_artifact(
        source,
        Path(".cg-docs/plans/legacy.md"),
        ArtifactKind.PLAN,
    )
    assert document.identity.schema_support is SchemaSupport.COMPATIBLE_LEGACY
    assert document.identity.schema_version is None


def test_kind_can_be_inferred_from_canonical_parent_directory() -> None:
    document = parse_artifact(
        _fixture("strict_plan.md"),
        Path(".cg-docs/plans/inferred.md"),
    )
    assert isinstance(document, PlanDocument)


def test_unclosed_fence_fails_with_source_lines() -> None:
    with pytest.raises(ArtifactParseError, match="Unclosed fenced code block") as caught:
        parse_artifact(
            _fixture("unclosed_fence.md"),
            Path(".cg-docs/brainstorms/unclosed.md"),
            ArtifactKind.BRAINSTORM,
        )
    assert caught.value.span is not None
    assert caught.value.span.start_line == 13


def test_completion_tables_are_parsed_by_header_name_not_position() -> None:
    source = _fixture("strict_plan.md").replace(
        "| ID | Evidence Required | Command/Artifact | Required |\n"
        "|----|-------------------|------------------|----------|\n"
        "| V1 | Parser tests pass. | `pytest -q scripts/artifact_views/tests/test_parser.py` | yes |",
        "| Required | Command/Artifact | ID | Evidence Required |\n"
        "|----------|------------------|----|-------------------|\n"
        "| yes | `pytest -q scripts/artifact_views/tests/test_parser.py` | V1 | Parser tests pass. |",
    )
    document = parse_artifact(
        source,
        Path(".cg-docs/plans/reordered.md"),
        ArtifactKind.PLAN,
    )
    verification = document.completion_rows[0]
    assert verification.identifier == "V1"
    assert verification.required is True
    assert verification.value_for("command/artifact").startswith("`pytest")


@pytest.mark.parametrize(
    "replacement",
    (
        "| ID | **ID** | Source |\n|----|--------|--------|\n| R1 | Duplicate | Test |",
        "| ID | Requirement | Source |\n|----|-------------|--------|\n| R1 | Text | Test | Extra |",
        "| ID |  | Source |\n|----|---|--------|\n| R1 | Text | Test |",
    ),
    ids=("duplicate-header", "extra-cell", "empty-header"),
)
def test_lossy_pipe_tables_fail_before_model_construction(replacement: str) -> None:
    source = _fixture("strict_plan.md")
    original = (
        "| ID | Requirement | Source |\n"
        "|----|-------------|--------|\n"
        "| R1 | Parse the supported grammar. | Contract |\n"
        "| R2 | Validate complete requirement coverage. | Contract |"
    )
    source = source.replace(original, replacement)

    with pytest.raises(ArtifactParseError, match="table|header|cells"):
        parse_artifact(
            source,
            Path(".cg-docs/plans/lossy-table.md"),
            ArtifactKind.PLAN,
        )
