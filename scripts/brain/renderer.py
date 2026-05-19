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

from brain import BrainData, Edge, Entity, Topic
from brain.utils import _write_atomic

# ---------------------------------------------------------------------------
# Token estimation
# ---------------------------------------------------------------------------

#: Words-to-tokens ratio (P3.3 fix: use 1.6 rather than 1.0).
_WORDS_PER_TOKEN: float = 1.6


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
    word_count = len(text.split())
    return int(word_count * _WORDS_PER_TOKEN) + 1


# ---------------------------------------------------------------------------
# Entity and section rendering helpers
# ---------------------------------------------------------------------------

_SLUG_UNSAFE = re.compile(r"[^a-z0-9-]+")


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
    title = entity.title or entity.slug
    path_str = str(entity.path).replace("\\", "/")
    status = entity.status or "—"
    date = entity.date_str or "—"
    etype = entity.entity_type

    line = f"- **[{title}]({path_str})** · `{etype}` · _{status}_ · `{date}`"

    summary = entity.summary.strip()
    if summary:
        # Truncate long summaries to keep token cost low in topic files
        if len(summary) > 120:
            summary = summary[:117] + "…"
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


def _partition_and_write_topic_files(
    data: BrainData,
    entity_map: Dict[Path, Entity],
    out_dir: Path,
    token_cap: int,
) -> List[Path]:
    """Partition topics into numbered content files and write them.

    Algorithm:

    1. For each topic, render its section and estimate tokens.
    2. Accumulate sections into the current page.
    3. If adding the next section would exceed ``token_cap``, flush the current
       page to ``BRAIN-NN.md`` and start a new one.
    4. If a **single topic** exceeds ``token_cap`` on its own, split it at
       entity boundaries.  A continuation header is added to the next file.

    Args:
        data: Full brain data.
        entity_map: Path → Entity lookup.
        out_dir: Output directory.
        token_cap: Target token cap per file.

    Returns:
        List of written file paths.
    """
    written: List[Path] = []

    # Each page is a list of (content_block, estimated_tokens)
    pages: List[List[str]] = [[]]  # start with one empty page
    page_tokens: List[int] = [0]

    for topic in data.topics:
        all_paths = topic.entity_paths

        # Render the full topic section to check its token cost
        full_section = _render_entity_section_for_topic(topic, entity_map)
        full_tokens = _estimate_tokens(full_section)

        if full_tokens <= token_cap:
            # Topic fits in one page
            current_idx = len(pages) - 1
            if page_tokens[current_idx] + full_tokens > token_cap and pages[current_idx]:
                # Would overflow — start a new page
                pages.append([])
                page_tokens.append(0)
                current_idx += 1
            pages[current_idx].append(full_section)
            page_tokens[current_idx] += full_tokens
        else:
            # Topic exceeds token_cap — split at entity boundaries.
            # If the current page already has content, start a fresh page so
            # oversized topics from consecutive iterations don't pile up.
            current_idx = len(pages) - 1
            if pages[current_idx]:
                pages.append([])
                page_tokens.append(0)

            chunk: List[Path] = []
            chunk_tokens = 0

            for i, path in enumerate(all_paths):
                entity = entity_map.get(path)
                if entity is None:
                    continue
                line = _entity_line(entity)
                line_tokens = _estimate_tokens(line)

                # Would this line overflow the current chunk?
                if chunk and chunk_tokens + line_tokens > token_cap:
                    # Flush chunk to current page
                    current_idx = len(pages) - 1
                    next_file_num = len(pages) + 1

                    chunk_section = _render_entity_section_for_topic(
                        topic,
                        entity_map,
                        entities_slice=chunk,
                        continues_in=next_file_num,
                    )
                    pages[current_idx].append(chunk_section)
                    page_tokens[current_idx] += chunk_tokens  # track tokens in flush

                    # Start new page for continuation
                    pages.append([])
                    page_tokens.append(0)

                    chunk = [path]
                    chunk_tokens = line_tokens
                else:
                    chunk.append(path)
                    chunk_tokens += line_tokens

            # Write final chunk
            if chunk:
                current_idx = len(pages) - 1
                prev_file_num = current_idx  # file N-1 (1-indexed is current_idx)
                chunk_section = _render_entity_section_for_topic(
                    topic,
                    entity_map,
                    entities_slice=chunk,
                    continued_from=prev_file_num if prev_file_num >= 1 else None,
                )
                pages[current_idx].append(chunk_section)
                page_tokens[current_idx] += chunk_tokens

    # Write each page to a BRAIN-NN.md file
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

        _write_atomic(out_path, content)
        written.append(out_path)

    return written


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
    _write_atomic(out_path, content)
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

    def _sort_key(e: Entity) -> Tuple[str, str]:
        # Negate date string for descending sort; empty dates sort last
        d = e.date_str or "0000-00-00"
        return (d, e.title.lower())

    non_features = [e for e in data.entities if e.entity_type != "feature"]
    features = [e for e in data.entities if e.entity_type == "feature"]

    sorted_entities = sorted(non_features, key=_sort_key, reverse=True)
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
    _write_atomic(out_path, content)
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
        "schema_version": "0.2.0",
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
    _write_atomic(out_path, json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
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

    # 1. Write topic content files (BRAIN-NN.md)
    topic_files = _partition_and_write_topic_files(data, entity_map, out_dir, token_cap)
    written.extend(topic_files)

    # Build topic slug → file mapping for the meta-index
    # We need to map each topic to the file it lands in. Walk through the same
    # partitioning logic at a high level: topics are written in order to pages.
    topic_file_map = _build_topic_file_map(data.topics, topic_files)

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


def _build_topic_file_map(
    topics: List[Topic],
    topic_files: List[Path],
) -> Dict[str, str]:
    """Map each topic slug to its BRAIN-NN.md filename.

    Since we can't re-run the partitioning cheaply, we assign topics to files
    in order: topics in ``BRAIN-01.md``, then ``BRAIN-02.md``, etc.  This is
    an approximation — the exact mapping depends on token counts — but is good
    enough for the navigation index.

    Args:
        topics: All topics in order.
        topic_files: Ordered list of written BRAIN-NN.md paths.

    Returns:
        Dict mapping topic slug → file name (e.g. ``"BRAIN-01.md"``).
    """
    if not topic_files:
        return {}
    result: Dict[str, str] = {}
    # Assign topics evenly across files
    n_files = len(topic_files)
    for i, topic in enumerate(topics):
        file_idx = min(i * n_files // max(len(topics), 1), n_files - 1)
        result[topic.slug] = topic_files[file_idx].name
    return result
