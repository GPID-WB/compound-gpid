"""brain.renderer — Output generation for the brain engine.

Renders a :class:`~brain.BrainData` object into four output files:

``BRAIN.md``
    Navigation meta-index.  Always a single file containing the topic table,
    entity-type summary, and edge summary.

``BRAIN-01.md``, ``BRAIN-02.md``, …
    Full topic-partitioned content files.  Each file stays at or below
    ``token_cap`` (estimated as ``word_count × 1.6``).  An oversized single
    topic is split at entity boundaries with a continuation header; it is
    never split mid-entity.

``BRAIN-log.md``
    Chronological listing of all entities, newest first.  Always a single
    file regardless of size (designed for append-only reads).

``brain-index.json``
    Machine-readable full index (JSON).  Contains the complete entity list,
    topic list, and edge list with all metadata fields.

The renderer does **not** delete legacy files (``DIGEST.md``,
``search-index.json``).  Legacy deletion is the caller's responsibility
(performed in ``cg_index.py::main()`` after ``render_brain()`` returns).

Token overflow warning: if any single output file exceeds ``token_cap × 1.1``
the renderer emits a ``UserWarning`` with the file name and token estimate.
"""
from __future__ import annotations

import json
import re
import warnings
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import quote

from brain import BrainData, Entity, Topic, __version__ as _BRAIN_VERSION
from brain.utils import write_atomic

# ---------------------------------------------------------------------------
# Token estimation
# ---------------------------------------------------------------------------

#: ~1.6 words per GPT-4 token (empirical for English prose; P3.1 named constant).
_WORDS_PER_TOKEN: float = 1.6

#: Maximum characters for inline entity summaries in topic files.
_SUMMARY_MAX_CHARS: int = 120


def _estimate_tokens(text: str) -> int:
    """Estimate token count from word count using :data:`_WORDS_PER_TOKEN`.

    Args:
        text: Markdown or JSON text to estimate.

    Returns:
        Estimated token count (rounded up).

    Example:
        >>> _estimate_tokens("Hello world")  # 2 words × 1.6 ≈ 3
        3
    """
    # O(n) scan with no word-list allocation; handle empty string correctly
    if not text:
        return 1
    word_count = text.count(" ") + text.count("\n") + 1  # O(n) scan, no allocation
    return int(word_count * _WORDS_PER_TOKEN) + 1


# ---------------------------------------------------------------------------
# Entity and section rendering helpers
# ---------------------------------------------------------------------------

_SLUG_UNSAFE = re.compile(r"[^a-z0-9-]+")


def _sanitize_inline(text: str) -> str:
    """Escape characters that corrupt markdown inline elements.

    Strips newlines and escapes ``]``, ``(`` and ``)`` so that titles and
    other inline values cannot break link syntax or inject title attributes.

    Args:
        text: Raw string from an entity field.

    Returns:
        Sanitized string safe for use inside ``[text](url)`` markdown links.
    """
    return (
        text.replace("\n", " ")
        .replace("[", "\\[")
        .replace("(", "\\(")
        .replace(")", "\\)")
        .replace("]", "\\]")
    )


def _anchor(text: str) -> str:
    """Convert text to a GitHub-style markdown anchor.

    Args:
        text: Section heading text.

    Returns:
        Lowercase, hyphen-delimited anchor string.
    """
    return _SLUG_UNSAFE.sub("-", text.lower()).strip("-")


def _entity_line(entity: Entity) -> str:
    """Render a single entity as a compact markdown list item.

    Format::

        - **[Title](rel/path)** · `type` · *status* · `date`
          > summary (truncated to 120 chars)

    Args:
        entity: Entity to render.

    Returns:
        Markdown string (2 lines if summary exists, 1 line otherwise).
    """
    title = _sanitize_inline(entity.title or entity.slug)
    path_str = quote(str(entity.path).replace("\\", "/"), safe="/#-_.")
    status = entity.status or "—"
    date = entity.date_str or "—"
    etype = entity.entity_type

    line = f"- **[{title}]({path_str})** · `{etype}` · _{status}_ · `{date}`"

    summary = entity.summary.strip()
    if summary:
        # Truncate long summaries to keep token cost low in topic files
        if len(summary) > _SUMMARY_MAX_CHARS:
            summary = summary[:_SUMMARY_MAX_CHARS - 3] + "…"
        line += f"\n  > {summary}"

    return line


def _render_entity_section_for_topic(
    topic: Topic,
    entity_map: Dict[Path, Entity],
    entities_slice: Optional[List[Path]] = None,
    continued_from: Optional[int] = None,
    continues_in: Optional[int] = None,
) -> str:
    """Render a topic section (for use in BRAIN-NN.md files).

    Args:
        topic: The topic to render.
        entity_map: Mapping from path → Entity for all entities.
        entities_slice: If ``None``, uses all of ``topic.entity_paths``.
            Otherwise, a subset of paths for multi-page splits.
        continued_from: If set, adds a *(continued from Part N)* note.
        continues_in: If set, adds a *(continues in Part N)* note.

    Returns:
        Markdown string for the topic section.
    """
    paths = entities_slice if entities_slice is not None else topic.entity_paths
    heading = f"## {topic.label}"
    if continued_from is not None:
        heading += f" _(continued from Part {continued_from})_"

    kw_str = " · ".join(f"`{k}`" for k in topic.keywords[:5])
    lines = [
        heading,
        "",
        f"_Keywords: {kw_str}_ · {len(paths)} entities",
        "",
    ]
    for p in paths:
        entity = entity_map.get(p)
        if entity is not None:
            lines.append(_entity_line(entity))

    if continues_in is not None:
        lines.append("")
        lines.append(f"_…continues in [BRAIN-{continues_in:02d}.md](BRAIN-{continues_in:02d}.md)_")

    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# BRAIN-NN.md: topic-partitioned content files
# ---------------------------------------------------------------------------


def _split_oversized_topic(
    topic: Topic,
    entity_map: Dict[Path, Entity],
    token_cap: int,
) -> List[List[Path]]:
    """Split an oversized topic into entity-boundary chunks fitting within token_cap.

    Each returned chunk is a list of entity paths intended for one BRAIN-NN.md
    page.  Splitting is greedy: entities are accumulated until adding the next
    would exceed ``token_cap``, then a new chunk is started.

    Args:
        topic: Topic whose full content exceeds ``token_cap``.
        entity_map: Path → Entity lookup.
        token_cap: Target maximum token count per chunk.

    Returns:
        List of chunks (each chunk is a list of entity paths).  Always returns
        at least one chunk; returns ``[[]]`` only if ``entity_paths`` is empty.
    """
    chunks: List[List[Path]] = []
    chunk: List[Path] = []
    chunk_tokens = 0

    for path in topic.entity_paths:
        entity = entity_map.get(path)
        if entity is None:
            continue
        line = _entity_line(entity)
        line_tokens = _estimate_tokens(line)

        if chunk and chunk_tokens + line_tokens > token_cap:
            chunks.append(chunk)
            chunk = [path]
            chunk_tokens = line_tokens
        else:
            chunk.append(path)
            chunk_tokens += line_tokens

    if chunk:
        chunks.append(chunk)

    return chunks or [[]]


def _flush_pages_to_files(
    pages: List[List[str]],
    out_dir: Path,
    data: BrainData,
    token_cap: int,
) -> List[Path]:
    """Write pre-packed page sections to ``BRAIN-NN.md`` files.

    Each non-empty page in ``pages`` becomes one ``BRAIN-NN.md`` file.
    Empty pages (no sections accumulated) are skipped.

    Args:
        pages: Packed pages — each entry is a list of pre-rendered section strings.
        out_dir: Output directory.
        data: Full brain data (provides the ``generated`` date for file headers).
        token_cap: Cap used for overflow ``UserWarning`` emission.

    Returns:
        List of written file paths in page order.
    """
    written: List[Path] = []
    for i, sections in enumerate(pages):
        if not sections:
            continue
        page_num = i + 1
        out_path = out_dir / f"BRAIN-{page_num:02d}.md"

        lines = [
            f"# 🧠 Project Brain — Part {page_num}",
            "",
            f"_Generated {data.generated}_",
            "",
        ]
        lines.extend(sections)

        content = "\n".join(lines)
        tokens = _estimate_tokens(content)
        if tokens > token_cap * 1.1:
            warnings.warn(
                f"[brain.renderer] {out_path.name} is {tokens} estimated tokens "
                f"(>{token_cap * 1.1:.0f} cap × 1.1 overflow threshold).",
                UserWarning,
                stacklevel=3,
            )

        write_atomic(out_path, content)
        written.append(out_path)

    return written


def _partition_and_write_topic_files(
    data: BrainData,
    entity_map: Dict[Path, Entity],
    out_dir: Path,
    token_cap: int,
) -> Tuple[List[Path], Dict[str, str]]:
    """Partition topics into numbered content files and write them.

    Algorithm:

    1. For each topic, render its full section and estimate tokens.
    2. If it fits, accumulate into the current page; start a new page on overflow.
    3. If it exceeds ``token_cap``, split at entity boundaries via
       :func:`_split_oversized_topic`, emitting continuation headers per chunk.
    4. Flush all pages to disk via :func:`_flush_pages_to_files`.

    The ``slug_to_file`` map is built during packing (not approximated after the
    fact), so BRAIN.md navigation links are always accurate.

    Args:
        data: Full brain data.
        entity_map: Path → Entity lookup.
        out_dir: Output directory.
        token_cap: Target token cap per file.

    Returns:
        Tuple of ``(written_paths, slug_to_file_map)`` where
        ``slug_to_file_map`` maps each topic slug to its ``BRAIN-NN.md`` filename.
    """
    pages: List[List[str]] = [[]]  # each entry = list of section strings for one page
    page_tokens: List[int] = [0]
    slug_to_file: Dict[str, str] = {}

    for topic in data.topics:
        full_section = _render_entity_section_for_topic(topic, entity_map)
        full_tokens = _estimate_tokens(full_section)

        if full_tokens <= token_cap:
            # Topic fits in a single page
            current_idx = len(pages) - 1
            if page_tokens[current_idx] + full_tokens > token_cap and pages[current_idx]:
                # Would overflow the current page — start a fresh one
                pages.append([])
                page_tokens.append(0)
                current_idx += 1
            pages[current_idx].append(full_section)
            page_tokens[current_idx] += full_tokens
            slug_to_file[topic.slug] = f"BRAIN-{current_idx + 1:02d}.md"
        else:
            # Topic exceeds token_cap — split at entity boundaries
            if pages[-1]:
                # Current page already has content; isolate the oversized topic
                # on its own fresh page so it is not interleaved with prior topics.
                pages.append([])
                page_tokens.append(0)

            # Record the topic to the first page it will occupy (accurate).
            slug_to_file[topic.slug] = f"BRAIN-{len(pages):02d}.md"

            chunks = _split_oversized_topic(topic, entity_map, token_cap)
            n_chunks = len(chunks)

            for chunk_idx, chunk in enumerate(chunks):
                # At the start of each iteration the last page is the current one.
                # len(pages) is its 1-indexed file number.
                prev_1indexed = (len(pages) - 1) if chunk_idx > 0 else None
                next_1indexed = (len(pages) + 1) if chunk_idx < n_chunks - 1 else None

                chunk_section = _render_entity_section_for_topic(
                    topic,
                    entity_map,
                    entities_slice=chunk,
                    continued_from=prev_1indexed,
                    continues_in=next_1indexed,
                )
                current_idx = len(pages) - 1
                pages[current_idx].append(chunk_section)
                page_tokens[current_idx] += _estimate_tokens(chunk_section)

                if next_1indexed is not None:
                    pages.append([])
                    page_tokens.append(0)

    written = _flush_pages_to_files(pages, out_dir, data, token_cap)
    return written, slug_to_file


# ---------------------------------------------------------------------------
# BRAIN.md: navigation meta-index
# ---------------------------------------------------------------------------


def _write_brain_index_md(
    data: BrainData,
    topic_file_map: Dict[str, str],
    out_dir: Path,
) -> Path:
    """Write the ``BRAIN.md`` meta-index navigation file.

    Args:
        data: Full brain data.
        topic_file_map: Mapping from topic slug → ``BRAIN-NN.md`` filename.
        out_dir: Output directory.

    Returns:
        Path of written file.
    """
    # Entity type counts
    type_counts: Dict[str, int] = defaultdict(int)
    for e in data.entities:
        type_counts[e.entity_type] += 1

    # Edge type counts
    edge_counts: Dict[str, int] = defaultdict(int)
    for edge in data.edges:
        edge_counts[edge.edge_type] += 1

    lines = [
        "# 🧠 Project Brain",
        "",
        f"_Generated {data.generated} · "
        f"{len(data.entities)} entities · "
        f"{len(data.topics)} topics · "
        f"{len(data.edges)} edges_",
        "",
        "## How to Use",
        "",
        "1. Find the relevant **topic** in the Topic Index below.",
        "2. Open the linked `BRAIN-NN.md` for full entity details and summaries.",
        "3. For a date-ordered view: [BRAIN-log.md](BRAIN-log.md)",
        "4. For programmatic access: [brain-index.json](brain-index.json)",
        "",
        "## Topic Index",
        "",
        "| # | Topic | Entities | File |",
        "|---|-------|----------|------|",
    ]

    for i, topic in enumerate(data.topics, 1):
        file_name = topic_file_map.get(topic.slug, "BRAIN-01.md")
        anchor = _anchor(topic.label)
        lines.append(
            f"| {i} | [{topic.label}]({file_name}#{anchor}) "
            f"| {len(topic.entity_paths)} | {file_name} |"
        )

    # Entities not in any topic
    all_topic_paths = {p for t in data.topics for p in t.entity_paths}
    unclustered = [e for e in data.entities if e.path not in all_topic_paths]

    lines += [
        "",
        "## Entity Summary",
        "",
        "| Type | Count |",
        "|------|-------|",
    ]
    for etype, count in sorted(type_counts.items()):
        lines.append(f"| {etype} | {count} |")

    if unclustered:
        lines += [
            "",
            f"_{len(unclustered)} entities not assigned to any topic_",
        ]

    if data.edges:
        lines += [
            "",
            "## Relationship Summary",
            "",
            "| Edge Type | Count |",
            "|-----------|-------|",
        ]
        for etype, count in sorted(edge_counts.items()):
            lines += [f"| {etype} | {count} |"]

    lines.append("")
    content = "\n".join(lines)
    out_path = out_dir / "BRAIN.md"
    write_atomic(out_path, content)
    return out_path


# ---------------------------------------------------------------------------
# BRAIN-log.md: chronological log
# ---------------------------------------------------------------------------


def _write_brain_log(data: BrainData, out_dir: Path) -> Path:
    """Write the ``BRAIN-log.md`` chronological entity listing.

    Entities are sorted newest-first by date, then alphabetically by title.
    Feature entities (virtual roadmap paths) are grouped at the end.

    Args:
        data: Full brain data.
        out_dir: Output directory.

    Returns:
        Path of written file.
    """

    non_features = [e for e in data.entities if e.entity_type != "feature"]
    features = [e for e in data.entities if e.entity_type == "feature"]

    # Two-pass stable sort: A→Z title first, then newest-first date.
    # A single-pass reverse=True on a (date, title) tuple would reverse both
    # components, producing Z→A titles within the same date.
    sorted_entities = sorted(non_features, key=lambda e: e.title.lower())
    sorted_entities.sort(key=lambda e: e.date_str or "0000-00-00", reverse=True)
    # Group by date
    by_date: Dict[str, List[Entity]] = defaultdict(list)
    for e in sorted_entities:
        by_date[e.date_str or "undated"].append(e)

    lines = [
        "# 🧠 Project Brain — Chronological Log",
        "",
        f"_Generated {data.generated} · "
        f"{len(non_features)} artifacts (newest first) + "
        f"{len(features)} roadmap features_",
        "",
    ]

    for date_str in sorted(by_date.keys(), reverse=True):
        lines.append(f"## {date_str}")
        lines.append("")
        for entity in by_date[date_str]:
            lines.append(_entity_line(entity))
        lines.append("")

    if features:
        lines += [
            "## Roadmap Features",
            "",
        ]
        for entity in sorted(features, key=lambda e: e.slug):
            lines.append(_entity_line(entity))
        lines.append("")

    content = "\n".join(lines)
    out_path = out_dir / "BRAIN-log.md"
    write_atomic(out_path, content)
    return out_path


# ---------------------------------------------------------------------------
# brain-index.json: machine-readable index
# ---------------------------------------------------------------------------


def _write_brain_json(data: BrainData, out_dir: Path) -> Path:
    """Write the ``brain-index.json`` machine-readable full index.

    Args:
        data: Full brain data.
        out_dir: Output directory.

    Returns:
        Path of written file.
    """
    payload = {
        "generated": data.generated,
        "schema_version": _BRAIN_VERSION,
        "entity_count": len(data.entities),
        "topic_count": len(data.topics),
        "edge_count": len(data.edges),
        "topics": [
            {
                "slug": t.slug,
                "label": t.label,
                "keywords": t.keywords,
                "entity_count": len(t.entity_paths),
                "entity_paths": [str(p).replace("\\", "/") for p in t.entity_paths],
            }
            for t in data.topics
        ],
        "entities": [
            {
                "path": str(e.path).replace("\\", "/"),
                "entity_type": e.entity_type,
                "slug": e.slug,
                "title": e.title,
                "date": e.date_str,
                "status": e.status,
                "tags": e.tags,
                "summary": e.summary,
                "top_keywords": [kw for kw, _ in e.keywords[:10]],
            }
            for e in data.entities
        ],
        "edges": [
            {
                "source": str(edge.source).replace("\\", "/"),
                "target": str(edge.target).replace("\\", "/"),
                "edge_type": edge.edge_type,
                "target_missing": edge.target_missing,
            }
            for edge in data.edges
        ],
    }
    out_path = out_dir / "brain-index.json"
    write_atomic(out_path, json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n")
    return out_path


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def render_brain(
    data: BrainData,
    out_dir: Path,
    token_cap: int = 20_000,
) -> List[Path]:
    """Render a :class:`~brain.BrainData` to the four brain output files.

    Writes all output files atomically (temp file + os.replace).  Does **not**
    delete legacy files — the caller (``cg_index.py::main()``) is responsible
    for cleaning up ``DIGEST.md`` and ``search-index.json`` after this returns.

    Args:
        data: Populated :class:`~brain.BrainData` (from :func:`~brain.build_brain`).
        out_dir: Directory to write output files into.  Created if absent.
        token_cap: Target maximum tokens per ``BRAIN-NN.md`` file.  Default
            20 000.  Files may slightly exceed this if a single entity line
            pushes past the boundary.  A warning is emitted if any file is
            more than 10 % over cap.

    Returns:
        List of :class:`Path` objects for every file written (always includes
        ``BRAIN.md``, ``BRAIN-log.md``, ``brain-index.json``, and at least
        one ``BRAIN-NN.md`` if any topics exist).

    Example:
        >>> from pathlib import Path
        >>> from brain import build_brain
        >>> from brain.renderer import render_brain
        >>> data = build_brain(root=Path("."))
        >>> written = render_brain(data, out_dir=Path(".cg-docs"))
        >>> print("\\n".join(str(p) for p in written))
    """
    out_dir.mkdir(parents=True, exist_ok=True)

    # Build entity path → Entity lookup for fast access
    entity_map: Dict[Path, Entity] = {e.path: e for e in data.entities}

    written: List[Path] = []

    # 1. Write topic content files (BRAIN-NN.md) and get accurate topic→file map.
    # Write-first: new files are fully written before any stale file is removed
    # so readers never see an empty directory (adversarial P1.4 fix).
    topic_files, topic_file_map = _partition_and_write_topic_files(data, entity_map, out_dir, token_cap)
    written.extend(topic_files)

    # Remove stale partition files from previous runs (only after new files are written)
    new_brain_stems = {f.stem for f in topic_files}
    for _stale in out_dir.glob("BRAIN-[0-9][0-9].md"):
        if _stale.stem not in new_brain_stems:
            try:
                _stale.unlink()
            except OSError:
                pass

    # 2. Write BRAIN.md meta-index
    brain_md = _write_brain_index_md(data, topic_file_map, out_dir)
    written.append(brain_md)

    # 3. Write BRAIN-log.md chronological log
    brain_log = _write_brain_log(data, out_dir)
    written.append(brain_log)

    # 4. Write brain-index.json machine-readable index
    brain_json = _write_brain_json(data, out_dir)
    written.append(brain_json)

    return written



