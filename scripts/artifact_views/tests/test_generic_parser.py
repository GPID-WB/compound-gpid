"""Tests for independent generic Markdown parsing and source ownership."""
from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

# pylint: disable=import-error
from artifact_views.errors import ArtifactModelError, ArtifactParseError
from artifact_views.generic_model import GenericDocument
from artifact_views.generic_parser import parse_generic_markdown
# pylint: enable=import-error


@pytest.mark.parametrize(
    ("frontmatter", "heading", "filename", "expected"),
    (
        ("---\ntitle: Frontmatter title\n---\n", "# Heading title\n", "fallback.md", "Frontmatter title"),
        ("", "# Heading title\n", "fallback.md", "Heading title"),
        ("", "Body only.\n", "fallback.md", "fallback"),
    ),
    ids=("frontmatter", "first-h1", "filename"),
)
def test_generic_title_resolution_is_deterministic(
    frontmatter: str,
    heading: str,
    filename: str,
    expected: str,
) -> None:
    document = parse_generic_markdown(
        f"{frontmatter}{heading}\nBody.\n",
        Path("notes") / filename,
    )

    assert isinstance(document, GenericDocument)
    assert document.identity.title == expected
    assert document.identity.document_type == "generic-markdown"


@pytest.mark.parametrize(
    "marker",
    ("NOTE", "TIP", "IMPORTANT", "WARNING", "CAUTION", "DECISION", "PROS", "CONS"),
)
def test_only_exact_supported_callout_markers_are_classified(marker: str) -> None:
    source = f"# Guide\n\n> [!{marker}]\n> Source-backed detail.\n"

    document = parse_generic_markdown(source, Path("docs/guide.md"))

    assert [(item.kind, item.source_block_id) for item in document.callouts] == [
        (marker, document.lexical_blocks[2].block_id)
    ]
    assert document.lexical_blocks[2].kind == "callout"


def test_similar_callout_text_remains_an_ordinary_blockquote() -> None:
    source = "# Guide\n\n> [!note]\n> Not an exact marker.\n"

    document = parse_generic_markdown(source, Path("docs/guide.md"))

    assert document.callouts == ()
    assert document.lexical_blocks[2].kind == "blockquote"


def test_generic_ledger_reconstructs_unicode_crlf_and_escaped_table_pipes() -> None:
    source = (
        "---\r\ntitle: Café guide\r\n---\r\n"
        "# Ignored title\r\n\r\n"
        "| Item | Detail |\r\n|---|---|\r\n| A | left \\| right |\r\n"
        + "\r\nParagraph.\r\n" * 300
        + "\r\n<div>escaped later</div>\r\n"
    )

    document = parse_generic_markdown(source, Path("docs/café.md"))

    assert "".join(block.raw for block in document.lexical_blocks) == source
    assert document.source_length_bytes == len(source.encode("utf-8"))
    assert any(block.kind == "pipe_table" for block in document.lexical_blocks)
    assert any(block.kind == "raw_html" for block in document.lexical_blocks)


@pytest.mark.parametrize(
    "source_path",
    (
        Path(".cg-docs/brainstorms/example.md"),
        Path(".cg-docs/plans/example.md"),
        Path(".cg-docs/views/documents/example.md"),
    ),
)
def test_generic_parser_rejects_typed_and_generated_roots(source_path: Path) -> None:
    with pytest.raises(ArtifactParseError, match="cg-render-artifact"):
        parse_generic_markdown("# Example\n", source_path)


def test_generic_model_rejects_duplicate_source_ownership() -> None:
    document = parse_generic_markdown("# Guide\n\nBody.\n", Path("docs/guide.md"))
    with pytest.raises(ArtifactModelError, match="Duplicate substantive block ID"):
        replace(
            document,
            substantive_blocks=(
                document.substantive_blocks[0],
                document.substantive_blocks[0],
                *document.substantive_blocks[1:],
            ),
        )


@pytest.mark.parametrize(
    ("source", "message"),
    (
        ("# Guide\n\n```text\nunclosed\n", "Unclosed fenced code block"),
        (
            "# Guide\n\n| A | A |\n|---|---|\n| x | y |\n",
            "duplicate normalized headers",
        ),
    ),
)
def test_generic_parser_fails_on_ambiguous_grammar(source: str, message: str) -> None:
    with pytest.raises(ArtifactParseError, match=message):
        parse_generic_markdown(source, Path("docs/guide.md"))