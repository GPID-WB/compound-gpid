"""Fence-aware parser for versioned Brainstorm and Plan Markdown."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Dict, List, Optional, Sequence, Tuple, Union

from artifact_views.errors import ArtifactParseError
from artifact_views.model import (
    Alternative,
    ArtifactIdentity,
    BrainstormDocument,
    CompletionRow,
    Frontmatter,
    FrontmatterField,
    LexicalBlock,
    Phase,
    PlanDocument,
    Requirement,
    Risk,
    SourceSpan,
    Step,
    SubstantiveBlock,
    TestCase,
    stable_block_id,
)
from artifact_views.schema import (
    ArtifactKind,
    is_non_substantive_metadata,
    schema_support,
)
from parsing_utils import parse_frontmatter_with_body

_HEADING_RE = re.compile(r"^ {0,3}(#{1,6})(?:[ \t]+(.*?))?[ \t]*$")
_FENCE_RE = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")
_ORDERED_LIST_RE = re.compile(r"^ {0,3}\d+[.)][ \t]+")
_UNORDERED_LIST_RE = re.compile(r"^ {0,3}[-+*][ \t]+")
_TASK_LIST_RE = re.compile(r"^ {0,3}[-+*][ \t]+\[[ xX]\][ \t]+")
_BLOCKQUOTE_RE = re.compile(r"^ {0,3}>")
_THEMATIC_RE = re.compile(
    r"^ {0,3}(?:(?:\*[ \t]*){3,}|(?:-[ \t]*){3,}|(?:_[ \t]*){3,})$"
)
_PHASE_RE = re.compile(r"^Phase[ \t]+([0-9]+):[ \t]*(.+)$", re.IGNORECASE)
_STEP_RE = re.compile(r"^([0-9]+)\.[ \t]+(.+)$")
_HTML_TAG_RE = re.compile(
    r"^</?[A-Za-z][A-Za-z0-9-]*(?:[ \t][^>]*)?/?>$",
    re.DOTALL,
)
_MULTILINE_HTML_RE = re.compile(
    r"^<(?P<tag>script|style|pre|div|table|section|details|article|aside)\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class _Line:
    raw: str
    number: int
    start_char: int
    end_char: int
    start_byte: int
    end_byte: int


ParsedDocument = Union[BrainstormDocument, PlanDocument]
TableRows = Tuple[Dict[str, str], ...]


def parse_artifact(
    source: str,
    source_path: Path,
    kind: Optional[ArtifactKind] = None,
) -> ParsedDocument:
    """Parse one canonical workflow artifact without rendering dependencies.

    Args:
        source: Unmodified Unicode Markdown source decoded as strict UTF-8.
        source_path: Canonical source path used in diagnostics.
        kind: Explicit artifact kind. When omitted, infer it from a canonical
            ``brainstorms`` or ``plans`` parent directory.

    Returns:
        An immutable typed Brainstorm or Plan document.

    Raises:
        ArtifactParseError: If block ownership is ambiguous, a fence is
            unclosed, or the artifact kind cannot be determined.

    Example:
        >>> text = "---\ntitle: Example\n---\n# Example\n"
        >>> parse_artifact(text, Path(".cg-docs/plans/example.md")).identity.title
        'Example'
    """
    source_path = Path(source_path)
    artifact_kind = _normalize_kind(kind, source_path)
    frontmatter_values, body = parse_frontmatter_with_body(source)
    body_start_char = len(source) - len(body)
    lines = _line_records(source)
    body_line_index = _line_index_at_char(lines, body_start_char, source_path)

    lexical: List[LexicalBlock] = []
    if body_start_char:
        frontmatter_lines = lines[:body_line_index]
        if not frontmatter_lines:
            raise _parse_error(
                source_path,
                "Frontmatter boundary does not align with source lines.",
                None,
                "Place the opening and closing delimiters on separate lines.",
            )
        frontmatter_span = _records_span(frontmatter_lines)
        lexical.append(
            LexicalBlock(
                stable_block_id(1),
                "frontmatter",
                frontmatter_span,
                source[:body_start_char],
                False,
            )
        )

    lexical.extend(
        _tokenize_body(
            lines[body_line_index:],
            source_path,
            starting_index=len(lexical) + 1,
        )
    )
    _validate_pipe_tables(lexical, source_path)
    substantive = tuple(
        SubstantiveBlock(block.block_id, block.kind, block.span)
        for block in lexical
        if block.substantive
    )
    frontmatter = Frontmatter(
        _frontmatter_fields(
            lines[:body_line_index],
            frontmatter_values,
        )
    )
    title = str(frontmatter_values.get("title") or "").strip()
    if not title:
        title = _first_h1_title(lexical) or ""
    if not title:
        raise _parse_error(
            source_path,
            "Artifact identity has no title.",
            None,
            "Add a non-empty title frontmatter field or level-one heading.",
        )

    version = frontmatter_values.get("artifact-schema-version")
    identity = ArtifactIdentity(
        kind=artifact_kind,
        source_path=source_path,
        title=title,
        schema_version=version,
        schema_support=schema_support(version),
    )
    source_length = len(source.encode("utf-8"))
    lexical_tuple = tuple(lexical)

    if artifact_kind is ArtifactKind.BRAINSTORM:
        return BrainstormDocument(
            identity=identity,
            frontmatter=frontmatter,
            lexical_blocks=lexical_tuple,
            substantive_blocks=substantive,
            source_length_bytes=source_length,
            alternatives=_parse_alternatives(lexical_tuple),
        )

    requirements = _parse_requirements(lexical_tuple)
    phases = _parse_phases(lexical_tuple)
    steps, tests = _parse_steps(lexical_tuple)
    return PlanDocument(
        identity=identity,
        frontmatter=frontmatter,
        lexical_blocks=lexical_tuple,
        substantive_blocks=substantive,
        source_length_bytes=source_length,
        requirements=requirements,
        phases=phases,
        steps=steps,
        tests=tests,
        risks=_parse_risks(lexical_tuple),
        completion_rows=_parse_completion_rows(lexical_tuple),
    )


def parse_pipe_table(raw: str) -> Tuple[Tuple[str, ...], TableRows]:
    """Parse one pipe table by normalized header name.

    Pipes inside code spans and escaped pipes remain part of their cells.

    Args:
        raw: Exact raw text for one lexical pipe-table block.

    Returns:
        A tuple containing normalized headers and ordered row dictionaries.

    Raises:
        ValueError: If headers are empty/duplicated or row widths differ.

    Example:
        >>> headers, rows = parse_pipe_table("| ID | Text |\n|---|---|\n| R1 | A |\n")
        >>> headers
        ('id', 'text')
        >>> rows[0]['id']
        'R1'
    """
    lines = raw.splitlines()
    if len(lines) < 2:
        return (), ()
    header_cells = _split_pipe_row(lines[0])
    separator_cells = _split_pipe_row(lines[1])
    if not header_cells or not _is_separator_row(separator_cells):
        return (), ()
    headers = tuple(_normalize_header(cell) for cell in header_cells)
    if any(not header for header in headers):
        raise ValueError("Pipe table contains an empty normalized header.")
    if len(set(headers)) != len(headers):
        raise ValueError("Pipe table contains duplicate normalized headers.")
    rows: List[Dict[str, str]] = []
    for line in lines[2:]:
        cells = _split_pipe_row(line)
        if not cells:
            continue
        if len(cells) != len(headers):
            raise ValueError(
                f"Pipe table row has {len(cells)} cells for {len(headers)} headers."
            )
        row = {
            header: cells[index].strip()
            for index, header in enumerate(headers)
        }
        rows.append(row)
    return headers, tuple(rows)


def _validate_pipe_tables(
    blocks: Sequence[LexicalBlock],
    source_path: Path,
) -> None:
    for block in blocks:
        if block.kind != "pipe_table":
            continue
        try:
            parse_pipe_table(block.raw)
        except ValueError as error:
            raise _parse_error(
                source_path,
                f"Invalid pipe table: {error}",
                block.span,
                "Use unique non-empty headers and the same cell count in every row.",
            ) from error


def _normalize_kind(
    kind: Optional[ArtifactKind],
    source_path: Path,
) -> ArtifactKind:
    if kind is not None:
        try:
            return ArtifactKind(kind)
        except (TypeError, ValueError) as error:
            raise _parse_error(
                source_path,
                f"Unsupported artifact kind: {kind!r}.",
                None,
                "Use ArtifactKind.BRAINSTORM or ArtifactKind.PLAN.",
            ) from error
    parent_names = {parent.name for parent in source_path.parents}
    if "brainstorms" in parent_names:
        return ArtifactKind.BRAINSTORM
    if "plans" in parent_names:
        return ArtifactKind.PLAN
    raise _parse_error(
        source_path,
        "Artifact kind cannot be inferred from the source path.",
        None,
        "Pass an explicit Brainstorm or Plan artifact kind.",
    )


def _line_records(source: str) -> Tuple[_Line, ...]:
    records: List[_Line] = []
    char_offset = 0
    byte_offset = 0
    for number, raw in enumerate(source.splitlines(keepends=True), start=1):
        next_char = char_offset + len(raw)
        next_byte = byte_offset + len(raw.encode("utf-8"))
        records.append(
            _Line(
                raw=raw,
                number=number,
                start_char=char_offset,
                end_char=next_char,
                start_byte=byte_offset,
                end_byte=next_byte,
            )
        )
        char_offset = next_char
        byte_offset = next_byte
    return tuple(records)


def _line_index_at_char(
    lines: Sequence[_Line],
    char_offset: int,
    source_path: Path,
) -> int:
    for index, line in enumerate(lines):
        if line.start_char == char_offset:
            return index
        if line.start_char < char_offset < line.end_char:
            raise _parse_error(
                source_path,
                "Frontmatter boundary splits a source line.",
                _records_span((line,)),
                "Put the closing frontmatter delimiter on its own line.",
            )
    if not lines and char_offset == 0:
        return 0
    if lines and char_offset == lines[-1].end_char:
        return len(lines)
    raise _parse_error(
        source_path,
        "Frontmatter boundary is outside the source.",
        None,
        "Use a complete opening and closing frontmatter delimiter.",
    )


def _frontmatter_fields(
    lines: Sequence[_Line],
    values: Dict[str, object],
) -> Tuple[FrontmatterField, ...]:
    fields: List[FrontmatterField] = []
    for line in lines:
        text = _strip_eol(line.raw).strip()
        if not text or text in {"---", "\ufeff---"} or text.startswith("#"):
            continue
        if text.startswith("- ") or ":" not in text:
            continue
        key = text.partition(":")[0].strip()
        if not key:
            continue
        fields.append(
            FrontmatterField(
                key,
                values.get(key),
                _records_span((line,)),
            )
        )
    return tuple(fields)


def _tokenize_body(
    lines: Sequence[_Line],
    source_path: Path,
    starting_index: int,
) -> Tuple[LexicalBlock, ...]:
    blocks: List[LexicalBlock] = []
    index = 0
    block_index = starting_index
    while index < len(lines):
        text = _strip_eol(lines[index].raw)
        stripped = text.strip()
        end = index + 1
        kind = "paragraph"

        if not stripped:
            kind = "blank_line"
            while end < len(lines) and not _strip_eol(lines[end].raw).strip():
                end += 1
        else:
            fence = _FENCE_RE.match(text)
            if fence:
                kind = "fenced_code"
                end = _consume_fence(lines, index, fence.group(1), source_path)
            elif _HEADING_RE.match(text):
                kind = "atx_heading"
            elif _is_table_at(lines, index):
                kind = "pipe_table"
                end = _consume_table(lines, index)
            elif _is_raw_html_start(stripped):
                kind = "raw_html"
                end = _consume_raw_html(lines, index, source_path)
            elif _THEMATIC_RE.match(text):
                kind = "thematic_break"
            elif _TASK_LIST_RE.match(text):
                kind = "task_list"
                end = _consume_list(lines, index)
            elif _ORDERED_LIST_RE.match(text):
                kind = "ordered_list"
                end = _consume_list(lines, index)
            elif _UNORDERED_LIST_RE.match(text):
                kind = "unordered_list"
                end = _consume_list(lines, index)
            elif _BLOCKQUOTE_RE.match(text):
                kind = "blockquote"
                while end < len(lines) and _BLOCKQUOTE_RE.match(
                    _strip_eol(lines[end].raw)
                ):
                    end += 1
            else:
                while end < len(lines) and not _starts_new_block(lines, end):
                    end += 1

        block_lines = lines[index:end]
        raw = "".join(line.raw for line in block_lines)
        substantive = kind != "blank_line"
        if kind == "raw_html" and is_non_substantive_metadata(
            _strip_eol(raw)
        ):
            substantive = False
        blocks.append(
            LexicalBlock(
                stable_block_id(block_index),
                kind,
                _records_span(block_lines),
                raw,
                substantive,
            )
        )
        block_index += 1
        index = end
    return tuple(blocks)


def _consume_fence(
    lines: Sequence[_Line],
    start: int,
    marker: str,
    source_path: Path,
) -> int:
    marker_char = marker[0]
    minimum = len(marker)
    closing = re.compile(
        rf"^ {{0,3}}{re.escape(marker_char)}{{{minimum},}}[ \t]*$"
    )
    for index in range(start + 1, len(lines)):
        if closing.match(_strip_eol(lines[index].raw)):
            return index + 1
    raise _parse_error(
        source_path,
        "Unclosed fenced code block.",
        SourceSpan(
            lines[start].number,
            lines[-1].number,
            lines[start].start_byte,
            lines[-1].end_byte,
        ),
        f"Close the {marker_char * minimum} fence opened on line "
        f"{lines[start].number}.",
    )


def _consume_raw_html(
    lines: Sequence[_Line],
    start: int,
    source_path: Path,
) -> int:
    stripped = _strip_eol(lines[start].raw).strip()
    if stripped.startswith("<!--"):
        for index in range(start, len(lines)):
            if "-->" in lines[index].raw:
                return index + 1
        raise _parse_error(
            source_path,
            "Unclosed raw HTML comment.",
            SourceSpan(
                lines[start].number,
                lines[-1].number,
                lines[start].start_byte,
                lines[-1].end_byte,
            ),
            "Close the HTML comment with -->.",
        )

    multiline = _MULTILINE_HTML_RE.match(stripped)
    if multiline and f"</{multiline.group('tag')}>" not in stripped.lower():
        closing = re.compile(
            rf"</{re.escape(multiline.group('tag'))}>\s*$",
            re.IGNORECASE,
        )
        for index in range(start + 1, len(lines)):
            if closing.search(_strip_eol(lines[index].raw).strip()):
                return index + 1
        raise _parse_error(
            source_path,
            f"Unclosed raw HTML <{multiline.group('tag')}> block.",
            SourceSpan(
                lines[start].number,
                lines[-1].number,
                lines[start].start_byte,
                lines[-1].end_byte,
            ),
            f"Close the raw HTML block with </{multiline.group('tag')}>.",
        )
    return start + 1


def _consume_table(lines: Sequence[_Line], start: int) -> int:
    end = start + 2
    expected_columns = len(_split_pipe_row(_strip_eol(lines[start].raw)))
    while end < len(lines):
        text = _strip_eol(lines[end].raw)
        if not text.strip():
            break
        cells = _split_pipe_row(text)
        if not cells or (expected_columns > 1 and len(cells) < 1):
            break
        end += 1
    return end


def _consume_list(lines: Sequence[_Line], start: int) -> int:
    end = start + 1
    while end < len(lines):
        text = _strip_eol(lines[end].raw)
        if not text.strip():
            break
        if (
            _TASK_LIST_RE.match(text)
            or _ORDERED_LIST_RE.match(text)
            or _UNORDERED_LIST_RE.match(text)
            or text.startswith(("  ", "\t"))
        ):
            end += 1
            continue
        break
    return end


def _starts_new_block(lines: Sequence[_Line], index: int) -> bool:
    text = _strip_eol(lines[index].raw)
    stripped = text.strip()
    if not stripped:
        return True
    return bool(
        _FENCE_RE.match(text)
        or _HEADING_RE.match(text)
        or _is_table_at(lines, index)
        or _is_raw_html_start(stripped)
        or _THEMATIC_RE.match(text)
        or _TASK_LIST_RE.match(text)
        or _ORDERED_LIST_RE.match(text)
        or _UNORDERED_LIST_RE.match(text)
        or _BLOCKQUOTE_RE.match(text)
    )


def _is_table_at(lines: Sequence[_Line], index: int) -> bool:
    if index + 1 >= len(lines):
        return False
    header = _split_pipe_row(_strip_eol(lines[index].raw))
    separator = _split_pipe_row(_strip_eol(lines[index + 1].raw))
    return bool(
        len(header) >= 2
        and len(separator) == len(header)
        and _is_separator_row(separator)
    )


def _is_separator_row(cells: Sequence[str]) -> bool:
    return bool(cells) and all(
        re.fullmatch(r":?-{3,}:?", cell.strip()) is not None for cell in cells
    )


def _split_pipe_row(line: str) -> Tuple[str, ...]:
    text = line.strip()
    if "|" not in text:
        return ()
    cells: List[str] = []
    current: List[str] = []
    code_delimiter = 0
    index = 0
    while index < len(text):
        character = text[index]
        if character == "\\" and index + 1 < len(text):
            current.extend((character, text[index + 1]))
            index += 2
            continue
        if character == "`":
            end = index
            while end < len(text) and text[end] == "`":
                end += 1
            run = end - index
            if code_delimiter == 0:
                code_delimiter = run
            elif code_delimiter == run:
                code_delimiter = 0
            current.append(text[index:end])
            index = end
            continue
        if character == "|" and code_delimiter == 0:
            cells.append("".join(current).strip())
            current = []
        else:
            current.append(character)
        index += 1
    cells.append("".join(current).strip())
    if text.startswith("|") and cells and not cells[0]:
        cells.pop(0)
    if text.endswith("|") and cells and not cells[-1]:
        cells.pop()
    return tuple(cells)


def _is_raw_html_start(stripped: str) -> bool:
    if stripped.startswith("<!--"):
        return True
    first_line = stripped.splitlines()[0]
    return _HTML_TAG_RE.fullmatch(first_line) is not None or bool(
        _MULTILINE_HTML_RE.match(first_line)
    )


def _records_span(lines: Sequence[_Line]) -> SourceSpan:
    first = lines[0]
    last = lines[-1]
    return SourceSpan(
        first.number,
        last.number,
        first.start_byte,
        last.end_byte,
    )


def _heading(block: LexicalBlock) -> Optional[Tuple[int, str]]:
    if block.kind != "atx_heading":
        return None
    match = _HEADING_RE.match(_strip_eol(block.raw))
    if not match:
        return None
    title = (match.group(2) or "").strip()
    title = re.sub(r"[ \t]+#+[ \t]*$", "", title).strip()
    return len(match.group(1)), title


def _first_h1_title(blocks: Sequence[LexicalBlock]) -> Optional[str]:
    for block in blocks:
        heading = _heading(block)
        if heading and heading[0] == 1:
            return heading[1]
    return None


def _section_body(
    blocks: Sequence[LexicalBlock],
    level: int,
    title: str,
) -> Tuple[LexicalBlock, ...]:
    start: Optional[int] = None
    for index, block in enumerate(blocks):
        heading = _heading(block)
        if heading == (level, title):
            start = index + 1
            break
    if start is None:
        return ()
    end = len(blocks)
    for index in range(start, len(blocks)):
        heading = _heading(blocks[index])
        if heading and heading[0] <= level:
            end = index
            break
    return tuple(blocks[start:end])


def _parse_requirements(
    blocks: Sequence[LexicalBlock],
) -> Tuple[Requirement, ...]:
    section = _section_body(blocks, 2, "Requirements")
    table = next((block for block in section if block.kind == "pipe_table"), None)
    if table is None:
        return ()
    _, rows = parse_pipe_table(table.raw)
    requirements: List[Requirement] = []
    for row in rows:
        identifier = row.get("id", "").strip()
        text = row.get("requirement", "").strip()
        if identifier or text:
            requirements.append(Requirement(identifier, text, table.block_id))
    return tuple(requirements)


def _parse_alternatives(
    blocks: Sequence[LexicalBlock],
) -> Tuple[Alternative, ...]:
    section = _section_body(blocks, 2, "Approaches Considered")
    alternatives: List[Alternative] = []
    for index, block in enumerate(section):
        heading = _heading(block)
        if not heading or heading[0] != 3 or not heading[1].startswith("Approach "):
            continue
        end = len(section)
        for next_index in range(index + 1, len(section)):
            next_heading = _heading(section[next_index])
            if next_heading and next_heading[0] <= 3:
                end = next_index
                break
        source_ids = tuple(
            item.block_id for item in section[index:end] if item.substantive
        )
        alternatives.append(Alternative(heading[1], source_ids))
    return tuple(alternatives)


def _parse_phases(blocks: Sequence[LexicalBlock]) -> Tuple[Phase, ...]:
    phases: List[Phase] = []
    for block in blocks:
        heading = _heading(block)
        if not heading or heading[0] != 2:
            continue
        match = _PHASE_RE.match(heading[1])
        if match:
            phases.append(Phase(int(match.group(1)), match.group(2), block.block_id))
    return tuple(phases)


def _parse_steps(
    blocks: Sequence[LexicalBlock],
) -> Tuple[Tuple[Step, ...], Tuple[TestCase, ...]]:
    steps: List[Step] = []
    tests: List[TestCase] = []
    current_phase: Optional[int] = None
    for index, block in enumerate(blocks):
        heading = _heading(block)
        if heading and heading[0] == 2:
            phase_match = _PHASE_RE.match(heading[1])
            current_phase = int(phase_match.group(1)) if phase_match else None
            continue
        if not heading or heading[0] != 3:
            continue
        step_match = _STEP_RE.match(heading[1])
        if not step_match:
            continue
        end = len(blocks)
        for next_index in range(index + 1, len(blocks)):
            next_heading = _heading(blocks[next_index])
            if next_heading and (
                next_heading[0] <= 2
                or (next_heading[0] == 3 and _STEP_RE.match(next_heading[1]))
            ):
                end = next_index
                break
        step_blocks = tuple(blocks[index:end])
        requirements_raw, _requirements_source_id = _extract_label(
            step_blocks,
            "Requirements",
        )
        requirement_ids = tuple(
            value.strip().strip("`")
            for value in requirements_raw.split(",")
            if value.strip()
        )
        source_ids = tuple(
            item.block_id for item in step_blocks if item.substantive
        )
        number = int(step_match.group(1))
        steps.append(
            Step(
                number,
                step_match.group(2).strip(),
                requirement_ids,
                source_ids,
                current_phase,
            )
        )
        test_command, test_source_id = _extract_label(step_blocks, "Tests")
        if test_command and test_source_id is not None:
            tests.append(TestCase(f"step-{number}", test_command, test_source_id))
    return tuple(steps), tuple(tests)


def _extract_label(
    blocks: Sequence[LexicalBlock],
    label: str,
) -> Tuple[str, Optional[str]]:
    for block in blocks:
        if block.kind not in {"ordered_list", "unordered_list", "task_list"}:
            continue
        lines = block.raw.splitlines()
        if not lines:
            continue
        first_item = re.match(r"^(?P<indent> {0,3})(?:[-+*]|\d+[.)])[ \t]+", lines[0])
        if first_item is None:
            continue
        base_indent = first_item.group("indent")
        item_pattern = re.compile(
            rf"^{re.escape(base_indent)}(?:[-+*]|\d+[.)])[ \t]+"
            rf"(?:\[[ xX]\][ \t]+)?\*\*{re.escape(label)}\*\*:[ \t]*(.*)$",
            re.IGNORECASE,
        )
        any_base_item = re.compile(
            rf"^{re.escape(base_indent)}(?:[-+*]|\d+[.)])[ \t]+"
        )
        for index, line in enumerate(lines):
            match = item_pattern.match(line)
            if match is None:
                continue
            inline_value = match.group(1).strip()
            if inline_value:
                return inline_value, block.block_id
            for continuation in lines[index + 1:]:
                if any_base_item.match(continuation):
                    break
                stripped = continuation.strip()
                if stripped.startswith(("```", "~~~")):
                    break
                if stripped:
                    return stripped, block.block_id
    return "", None


def _parse_risks(blocks: Sequence[LexicalBlock]) -> Tuple[Risk, ...]:
    section = _section_body(blocks, 2, "Risks & Mitigations")
    table = next((block for block in section if block.kind == "pipe_table"), None)
    if table is None:
        return ()
    _, rows = parse_pipe_table(table.raw)
    return tuple(
        Risk(
            row.get("risk", "").strip(),
            row.get("mitigation", "").strip(),
            table.block_id,
        )
        for row in rows
        if row.get("risk", "").strip() or row.get("mitigation", "").strip()
    )


def _parse_completion_rows(
    blocks: Sequence[LexicalBlock],
) -> Tuple[CompletionRow, ...]:
    completion = _section_body(blocks, 2, "Completion Contract")
    rows: List[CompletionRow] = []
    for title, row_type in (
        ("Verification Surface", "verification"),
        ("Constraints", "constraint"),
    ):
        section = _section_body(completion, 3, title)
        table = next(
            (block for block in section if block.kind == "pipe_table"),
            None,
        )
        if table is None:
            continue
        _, table_rows = parse_pipe_table(table.raw)
        for row in table_rows:
            identifier = row.get("id", "").strip()
            phase_raw = row.get("phase", "").strip()
            phase: Optional[Union[int, str]] = None
            if phase_raw:
                phase = int(phase_raw) if phase_raw.isdigit() else phase_raw.lower()
            rows.append(
                CompletionRow(
                    row_type=row_type,
                    identifier=identifier,
                    values=tuple(row.items()),
                    source_block_id=table.block_id,
                    phase=phase,
                    required=row.get("required", "").strip().lower() == "yes",
                )
            )
    return tuple(rows)


def _normalize_header(header: str) -> str:
    normalized = re.sub(r"[`*_]", "", header).strip().lower()
    return re.sub(r"\s+", " ", normalized)


def _strip_eol(text: str) -> str:
    return text.rstrip("\r\n")


def _parse_error(
    source_path: Path,
    message: str,
    span: Optional[SourceSpan],
    corrective_action: str,
) -> ArtifactParseError:
    return ArtifactParseError(
        message,
        source_path=source_path,
        span=span,
        corrective_action=corrective_action,
    )
