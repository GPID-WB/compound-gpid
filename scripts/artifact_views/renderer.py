"""Deterministic semantic renderer for Brainstorm and Plan documents."""
from __future__ import annotations

from html import escape
from pathlib import Path, PurePosixPath
import posixpath
import re
from typing import Dict, List, Sequence, Tuple

from artifact_views.coverage import CoverageLedger, RenderedOwner
from artifact_views.model import (
    ArtifactDocument,
    BrainstormDocument,
    LexicalBlock,
    PlanDocument,
)
from artifact_views.parser import parse_pipe_table
from artifact_views.provenance import ArtifactProvenance
from artifact_views.security import render_safe_inline, validate_html_security
from artifact_views.templates import render_html_shell

_HEADING_RE = re.compile(r"^ {0,3}(#{1,6})(?:[ \t]+(.*?))?[ \t]*$")
_FENCE_RE = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")
_LIST_RE = re.compile(r"^\s*(?:[-+*]|\d+[.)])\s+(.*)$")
_TASK_RE = re.compile(r"^\s*[-+*]\s+\[([ xX])\]\s+(.*)$")


def render_document(
    document: ArtifactDocument,
    provenance: ArtifactProvenance,
) -> bytes:
    """Render a validated typed document to deterministic self-contained HTML.

    Args:
        document: Parsed and semantically validated Brainstorm or Plan.
        provenance: Complete explicit source and generation identity.

    Returns:
        Complete UTF-8 HTML bytes.

    Raises:
        ArtifactCoverageError: If exact-once ownership cannot be proven before
            final serialization.

    Example:
        Pass a validated document and explicit ``ArtifactProvenance``; the
        returned bytes begin with the HTML doctype.
    """
    canonical_href = _canonical_href(Path(provenance.source_path))
    if isinstance(document, BrainstormDocument):
        reserved_ids = {
            "main-content",
            "artifact-provenance",
            "provenance-heading",
            "approach-index",
        }
        heading_ids = _heading_ids(document.lexical_blocks, reserved_ids)
        navigation = _navigation(
            (
                ("Context", _heading_anchor(document.lexical_blocks, heading_ids, "Context")),
                ("Requirements", _heading_anchor(document.lexical_blocks, heading_ids, "Requirements")),
                ("Approaches", _heading_anchor(document.lexical_blocks, heading_ids, "Approaches Considered")),
                ("Decision", _heading_anchor(document.lexical_blocks, heading_ids, "Decision")),
                ("Next steps", _heading_anchor(document.lexical_blocks, heading_ids, "Next Steps")),
                ("Provenance", "provenance-heading"),
            )
        )
        eyebrow = "Decision record"
        deck = (
            "A complete human view of the canonical Brainstorm, organized around "
            "alternatives and the chosen direction."
        )
        derived = _brainstorm_overview(document)
    elif isinstance(document, PlanDocument):
        reserved_ids = {
            "main-content",
            "artifact-provenance",
            "provenance-heading",
            "phase-map",
            "requirement-coverage",
        }
        heading_ids = _heading_ids(document.lexical_blocks, reserved_ids)
        step_anchor = _heading_anchor(
            document.lexical_blocks,
            heading_ids,
            "Implementation Steps",
        )
        if not step_anchor and document.steps:
            step_anchor = heading_ids.get(document.steps[0].source_block_ids[0], "")
        navigation = _navigation(
            (
                ("Outcome", _heading_anchor(document.lexical_blocks, heading_ids, "Objective")),
                ("Phase map", "phase-map"),
                ("Steps", step_anchor),
                ("Requirement coverage", "requirement-coverage"),
                ("Verification", _heading_anchor(document.lexical_blocks, heading_ids, "Verification Surface")),
                ("Risks", _heading_anchor(document.lexical_blocks, heading_ids, "Risks & Mitigations")),
                ("Boundaries", _heading_anchor(document.lexical_blocks, heading_ids, "Out of Scope")),
                ("Provenance", "provenance-heading"),
            )
        )
        eyebrow = "Execution contract"
        deck = (
            "A complete human view of the canonical Plan, including phases, "
            "requirements, verification, risks, and boundaries."
        )
        derived = _plan_overview(document)
    else:
        raise TypeError(f"Unsupported artifact document: {type(document)!r}")

    owners: List[RenderedOwner] = []
    rendered_blocks: List[str] = []
    for index, block in enumerate(document.lexical_blocks, start=1):
        if not block.substantive:
            continue
        owner_id = f"render-owner-{index:04d}"
        owners.append(RenderedOwner(owner_id, block.block_id))
        rendered_blocks.append(_render_block(block, owner_id, heading_ids))
    CoverageLedger(document).validate(tuple(owners))

    rendered = render_html_shell(
        artifact_kind=document.identity.kind.value,
        title=document.identity.title,
        eyebrow=eyebrow,
        deck=deck,
        canonical_href=canonical_href,
        navigation_html=navigation,
        derived_html=derived,
        body_html="\n".join(rendered_blocks),
        provenance=provenance,
    )
    validate_html_security(rendered.decode("utf-8"))
    return rendered


def _render_block(
    block: LexicalBlock,
    owner_id: str,
    heading_ids: Dict[str, str],
) -> str:
    attributes = (
        f'id="{escape(owner_id, quote=True)}" '
        f'data-source-block="{escape(block.block_id, quote=True)}" '
        f'data-source-lines="{block.span.start_line}-{block.span.end_line}"'
    )
    content = _render_block_content(block, heading_ids)
    class_name = "source-block"
    if block.kind == "atx_heading":
        class_name += " source-heading"
    return f'<div class="{class_name}" {attributes}>{content}</div>'


def _render_block_content(
    block: LexicalBlock,
    heading_ids: Dict[str, str],
) -> str:
    raw = block.raw.rstrip("\r\n")
    if block.kind == "atx_heading":
        match = _HEADING_RE.match(raw)
        if match is None:
            return _raw_source(block)
        level = len(match.group(1))
        title = re.sub(r"\s+#+\s*$", "", (match.group(2) or "").strip())
        heading_id = heading_ids[block.block_id]
        return f'<h{level} id="{escape(heading_id, quote=True)}">{_inline(title)}</h{level}>'
    if block.kind == "paragraph":
        lines = raw.splitlines()
        rendered = []
        for line in lines:
            hard_break = line.endswith("  ")
            rendered.append(_inline(line.rstrip()))
            if hard_break:
                rendered.append("<br>")
            else:
                rendered.append(" ")
        return f"<p>{''.join(rendered).strip()}</p>"
    if block.kind in {"ordered_list", "unordered_list", "task_list"}:
        return _render_list(block)
    if block.kind == "pipe_table":
        return _render_table(block)
    if block.kind == "fenced_code":
        return _render_fence(block)
    if block.kind == "blockquote":
        text = "\n".join(
            re.sub(r"^\s*>\s?", "", line)
            for line in raw.splitlines()
        )
        return f"<blockquote><p>{_inline(text)}</p></blockquote>"
    if block.kind == "thematic_break":
        return "<hr>"
    if block.kind == "raw_html":
        return _raw_source(block)
    return _raw_source(block)


def _render_list(block: LexicalBlock) -> str:
    lines = block.raw.rstrip("\r\n").splitlines()
    if any(
        re.match(r"^\s+(?:[-+*]|\d+[.)])\s+", line)
        for line in lines
    ):
        return _raw_source(block)
    tag = "ol" if block.kind == "ordered_list" else "ul"
    items = []
    for line in lines:
        task = _TASK_RE.match(line)
        if task:
            checked = " checked" if task.group(1).lower() == "x" else ""
            items.append(
                f'<li><input type="checkbox" disabled{checked}> '
                f"{_inline(task.group(2))}</li>"
            )
            continue
        match = _LIST_RE.match(line)
        if match:
            items.append(f"<li>{_inline(match.group(1))}</li>")
        elif items:
            items[-1] = items[-1][:-5] + f" {_inline(line.strip())}</li>"
    return f"<{tag}>{''.join(items)}</{tag}>"


def _render_table(block: LexicalBlock) -> str:
    headers, rows = parse_pipe_table(block.raw)
    if not headers:
        return _raw_source(block)
    head = "".join(f"<th scope=\"col\">{escape(_display_header(item))}</th>" for item in headers)
    body_rows = []
    for row in rows:
        cells = "".join(f"<td>{_inline(row.get(header, ''))}</td>" for header in headers)
        body_rows.append(f"<tr>{cells}</tr>")
    return (
        '<div class="table-scroll" role="region" aria-label="Source table" tabindex="0">'
        f"<table><thead><tr>{head}</tr></thead><tbody>{''.join(body_rows)}</tbody></table>"
        "</div>"
    )


def _render_fence(block: LexicalBlock) -> str:
    lines = block.raw.rstrip("\r\n").splitlines()
    opening = _FENCE_RE.match(lines[0]) if lines else None
    language = (opening.group(2).strip().split()[0] if opening and opening.group(2).strip() else "")
    code = "\n".join(lines[1:-1])
    class_attribute = f' class="language-{escape(language, quote=True)}"' if language else ""
    return f"<pre><code{class_attribute}>{escape(code)}</code></pre>"


def _raw_source(block: LexicalBlock) -> str:
    return (
        '<figure class="raw-source">'
        f"<figcaption>Raw source · {escape(block.kind)} · lines "
        f"{block.span.start_line}–{block.span.end_line}</figcaption>"
        f"<pre><code>{escape(block.raw.rstrip(chr(10) + chr(13)))}</code></pre>"
        "</figure>"
    )


def _inline(value: str) -> str:
    return render_safe_inline(value)


def _heading_ids(
    blocks: Sequence[LexicalBlock],
    reserved_ids: Sequence[str],
) -> Dict[str, str]:
    used: Dict[str, int] = {item: 1 for item in reserved_ids}
    result: Dict[str, str] = {}
    for block in blocks:
        if block.kind != "atx_heading":
            continue
        match = _HEADING_RE.match(block.raw.rstrip("\r\n"))
        title = (match.group(2) or "") if match else block.block_id
        base = _slug(title) or block.block_id
        count = used.get(base, 0) + 1
        used[base] = count
        result[block.block_id] = base if count == 1 else f"{base}-{count}"
    return result


def _heading_anchor(
    blocks: Sequence[LexicalBlock],
    heading_ids: Dict[str, str],
    title: str,
) -> str:
    for block in blocks:
        if block.kind != "atx_heading":
            continue
        match = _HEADING_RE.match(block.raw.rstrip("\r\n"))
        if match and (match.group(2) or "").strip() == title:
            return heading_ids.get(block.block_id, "")
    return ""


def _slug(value: str) -> str:
    lowered = value.casefold()
    slug = re.sub(r"[^a-z0-9]+", "-", lowered).strip("-")
    return slug


def _navigation(items: Sequence[Tuple[str, str]]) -> str:
    links = "".join(
        f'<li><a href="#{escape(anchor, quote=True)}">{escape(label)}</a></li>'
        for label, anchor in items
        if anchor
    )
    return f"<ul>{links}</ul>"


def _brainstorm_overview(document: BrainstormDocument) -> str:
    alternatives = "".join(
        f"<li>{escape(alternative.title)}</li>"
        for alternative in document.alternatives
    ) or "<li>No structured alternatives declared.</li>"
    return (
        '<section class="derived-panel" data-derived="approach-index" '
        'aria-labelledby="approach-index">'
        '<h2 id="approach-index">Approach index</h2>'
        f"<ol>{alternatives}</ol></section>"
    )


def _plan_overview(document: PlanDocument) -> str:
    if document.phases:
        phases = "".join(
            f"<li><strong>Phase {phase.number}</strong> · {escape(phase.title)}</li>"
            for phase in document.phases
        )
    else:
        phases = "<li>Non-phased execution plan</li>"
    coverage = []
    for requirement in document.requirements:
        step_numbers = [
            str(step.number)
            for step in document.steps
            if requirement.identifier in step.requirement_ids
        ]
        coverage.append(
            f"<li><strong>{escape(requirement.identifier)}</strong> → steps "
            f"{escape(', '.join(step_numbers) or 'none')}</li>"
        )
    return (
        '<section class="derived-panel" data-derived="phase-map" '
        'aria-labelledby="phase-map">'
        '<h2 id="phase-map">Phase map</h2>'
        f'<ol class="phase-list">{phases}</ol></section>'
        '<section class="derived-panel" data-derived="requirement-coverage" '
        'aria-labelledby="requirement-coverage">'
        '<h2 id="requirement-coverage">Requirement coverage</h2>'
        f'<ul class="coverage-list">{"".join(coverage)}</ul></section>'
    )


def _canonical_href(source_path: Path) -> str:
    source = PurePosixPath(source_path.as_posix())
    parts = source.parts
    if len(parts) >= 3 and parts[0] == ".cg-docs":
        view = PurePosixPath(".cg-docs", "views", parts[1], *parts[2:]).with_suffix(
            ".html"
        )
        return posixpath.relpath(source.as_posix(), view.parent.as_posix())
    return source.as_posix()


def _display_header(value: str) -> str:
    return value.title().replace("Id", "ID")
