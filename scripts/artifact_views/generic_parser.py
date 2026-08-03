"""Independent parser for project-contained generic Markdown."""
from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import re
from typing import Optional

from artifact_views.errors import ArtifactParseError
from artifact_views.generic_model import (
    GenericCallout,
    GenericDocument,
    GenericHeading,
    GenericIdentity,
    SUPPORTED_CALLOUTS,
)
from artifact_views.model import LexicalBlock, SubstantiveBlock
from artifact_views.parser import heading_from_block, parse_lexical_source

_CALLOUT_RE = re.compile(
    r"^ {0,3}>[ \t]+\[!(?P<kind>" + "|".join(sorted(SUPPORTED_CALLOUTS))
    + r")\][ \t]*(?:\r?\n|$)"
)
_REJECTED_ROOTS = frozenset({"brainstorms", "plans", "views"})


def parse_generic_markdown(source: str, source_path: Path) -> GenericDocument:
    """Parse generic Markdown without invoking typed artifact validation.

    Args:
        source: Unmodified Unicode Markdown decoded as strict UTF-8.
        source_path: Project-relative source identity used in diagnostics.

    Returns:
        An immutable generic document with exact source ownership.

    Raises:
        ArtifactParseError: If the path is typed/generated or grammar is
            ambiguous.

    Example:
        >>> parse_generic_markdown("# Guide\n", Path("docs/guide.md")).identity.title
        'Guide'
    """
    source_path = Path(source_path)
    _reject_reserved_source_root(source_path)
    parsed = parse_lexical_source(source, source_path)
    lexical = tuple(_classify_callout(block) for block in parsed.lexical_blocks)
    substantive = tuple(
        SubstantiveBlock(block.block_id, block.kind, block.span)
        for block in lexical
        if block.substantive
    )
    title = str(parsed.frontmatter_values.get("title") or "").strip()
    if not title:
        title = _first_h1(lexical) or source_path.stem.strip()
    if not title:
        raise ArtifactParseError(
            "Generic document identity has no title.",
            source_path=source_path,
            corrective_action=(
                "Add a title field, level-one heading, or non-empty filename."
            ),
        )
    headings = tuple(
        GenericHeading(level, heading_title, block.block_id)
        for block in lexical
        if (heading := heading_from_block(block)) is not None
        for level, heading_title in (heading,)
        if heading_title
    )
    callouts = tuple(
        GenericCallout(match.group("kind"), block.block_id)
        for block in lexical
        if block.kind == "callout"
        if (match := _CALLOUT_RE.match(block.raw)) is not None
    )
    return GenericDocument(
        identity=GenericIdentity(source_path=source_path, title=title),
        frontmatter=parsed.frontmatter,
        lexical_blocks=lexical,
        substantive_blocks=substantive,
        source_length_bytes=parsed.source_length_bytes,
        headings=headings,
        callouts=callouts,
    )


def _classify_callout(block: LexicalBlock) -> LexicalBlock:
    if block.kind == "blockquote" and _CALLOUT_RE.match(block.raw):
        return replace(block, kind="callout")
    return block


def _first_h1(blocks: tuple[LexicalBlock, ...]) -> Optional[str]:
    for block in blocks:
        heading = heading_from_block(block)
        if heading and heading[0] == 1 and heading[1]:
            return heading[1]
    return None


def _reject_reserved_source_root(source_path: Path) -> None:
    parts = tuple(part.casefold() for part in source_path.parts)
    for index, part in enumerate(parts[:-1]):
        if part == ".cg-docs" and parts[index + 1] in _REJECTED_ROOTS:
            raise ArtifactParseError(
                "Generic publishing cannot accept typed or generated artifact roots.",
                source_path=source_path,
                corrective_action=(
                    "Use cg-render-artifact for Brainstorms and Plans, and never "
                    "publish generated views as source."
                ),
            )