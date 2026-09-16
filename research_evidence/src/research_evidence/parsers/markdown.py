"""Created 2026-08-12. Deterministic Markdown block parser."""
from __future__ import annotations

from typing import Optional
import re

from ..identity import make_source_unit_id, text_fingerprint
from ..schemas import LocatorKind, SourceUnit, TypedLocator

_HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.+?)\s*$")


def parse_markdown(text: str, source_version_id: str) -> list[SourceUnit]:
    """Parse non-empty Markdown blocks into typed source units.

    Args:
        text: UTF-8 Markdown source text.
        source_version_id: Immutable source-version identifier.

    Returns:
        Source units with stable block, line, heading, and text-fingerprint metadata.

    Raises:
        ValueError: If ``source_version_id`` is empty or ``text`` is not a string.

    Example:
        ``parse_markdown("# Heading\\n\\nA paragraph.", "version-1")``.
    """
    if not source_version_id:
        raise ValueError("A source version is required for Markdown parsing.")
    if not isinstance(text, str):
        raise ValueError("Markdown parser input must be text.")
    lines = text.replace("\r\n", "\n").replace("\r", "\n").splitlines()
    blocks: list[tuple[int, int, list[str]]] = []
    block_start: Optional[int] = None
    block_lines: list[str] = []
    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            if block_start is not None:
                blocks.append((block_start, line_number - 1, block_lines))
                block_start = None
                block_lines = []
            continue
        if block_start is None:
            block_start = line_number
        block_lines.append(line)
    if block_start is not None:
        blocks.append((block_start, len(lines), block_lines))

    heading_path: list[str] = []
    units: list[SourceUnit] = []
    for block_number, (line_start, line_end, block_lines) in enumerate(blocks, start=1):
        for line in block_lines:
            match = _HEADING_PATTERN.match(line)
            if match:
                level = len(match.group(1))
                heading_path = heading_path[: level - 1]
                heading_path.append(match.group(2).strip())
        unit_text = "\n".join(block_lines).strip()
        fingerprint = text_fingerprint(unit_text)
        locator = TypedLocator(
            kind=LocatorKind.MARKDOWN_BLOCK,
            block=block_number,
            line_start=line_start,
            line_end=line_end,
            anchor=heading_path[-1] if heading_path else None,
            unit_fingerprint=fingerprint,
        )
        units.append(
            SourceUnit(
                source_unit_id=make_source_unit_id(
                    source_version_id,
                    locator,
                    fingerprint,
                ),
                source_version_id=source_version_id,
                locator=locator,
                text=unit_text,
                heading_path=list(heading_path),
            )
        )
    return units
