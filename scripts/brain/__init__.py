"""brain — Knowledge Brain engine for Compound GPID.

Orchestrates the full brain pipeline: scan all ``.cg-docs/`` entities, extract
content keywords, cluster into topics, detect typed relationships, and render
the multi-file BRAIN output (``BRAIN.md``, ``BRAIN-log.md``, ``brain-index.json``).

This module replaces the legacy ``DIGEST.md`` + ``search-index.json`` system.

Usage::

    from pathlib import Path
    from brain import build_brain
    from brain.renderer import render_brain

    data = build_brain(root=Path("."))
    render_brain(data, out_dir=Path(".cg-docs"))

Architecture (modular single-pass)::

    cg_index.py --brain
        ├── build_brain(root)              # this module
        │   ├── scanner.scan_all()         # entity discovery
        │   ├── extractor.extract_keywords()  # content extraction
        │   ├── clusterer.cluster_topics()    # topic clustering
        │   └── edge_detector.detect_edges()  # relationship detection
        └── renderer.render_brain(data)    # output generation (separate step)
"""
from __future__ import annotations

__version__ = "0.2.0"

__all__ = ["Entity", "Topic", "Edge", "BrainData", "build_brain", "__version__", "ClusterStrategy"]

from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Tuple


# ---------------------------------------------------------------------------
# Core data structures
# ---------------------------------------------------------------------------


@dataclass
class Entity:
    """A single indexed artifact from ``.cg-docs/`` or ``roadmap.json``.

    Attributes:
        path: Path relative to the repo root (or virtual path for features,
            e.g. ``roadmap.json#feature-id``).
        entity_type: One of ``solution``, ``plan``, ``brainstorm``, ``review``,
            ``strategy``, ``feature``.
        frontmatter: Parsed YAML frontmatter key/value pairs.
        summary: Short plain-text summary (~100 words) extracted from the body.
        text: Raw body text (used by the extractor; not serialised to output).
        keywords: Weighted keywords extracted from the entity content.
            Each item is a ``(keyword, weight)`` tuple; higher weight = more
            significant. Populated by ``extractor.extract_keywords()``.
    """

    path: Path
    entity_type: str
    frontmatter: Dict[str, Any]
    summary: str = ""
    text: str = ""
    keywords: List[Tuple[str, float]] = field(default_factory=list)

    @property
    def slug(self) -> str:
        """Unique identifier: filename stem, or feature ID for roadmap features."""
        path_str = str(self.path)
        if "#" in path_str:
            return path_str.split("#", 1)[-1]
        return self.path.stem

    @property
    def title(self) -> str:
        """Frontmatter ``title`` field, falling back to the slug."""
        return str(self.frontmatter.get("title", self.slug))

    @property
    def date_str(self) -> str:
        """ISO date string from frontmatter; empty string if absent."""
        return str(self.frontmatter.get("date", ""))

    @property
    def status(self) -> str:
        """Frontmatter ``status`` lowercased; empty string if absent."""
        return str(self.frontmatter.get("status", "")).lower()

    @property
    def tags(self) -> List[str]:
        """List of tag strings from frontmatter; empty list if absent.

        Handles both list-form (``tags: [a, b]``) and scalar-form (``tags: pester``)
        frontmatter values. A bare scalar tag is returned as a single-element list.
        """
        raw = self.frontmatter.get("tags", [])
        if isinstance(raw, list):
            return [str(t) for t in raw]
        if isinstance(raw, str) and raw.strip():
            return [raw.strip()]  # scalar tag → single-element list
        return []


@dataclass
class Topic:
    """A cluster of related entities grouped by keyword co-occurrence.

    Attributes:
        slug: Kebab-case identifier derived from top keywords, e.g.
            ``pester-powershell-testing``.
        label: Human-readable topic label, e.g. ``"Pester / PowerShell Testing"``.
        keywords: Top keywords shared across constituent entities.
        entity_paths: Paths of all entities assigned to this topic.
    """

    slug: str
    label: str
    keywords: List[str]
    entity_paths: List[Path]


@dataclass
class Edge:
    """A typed directed relationship between two artifacts.

    Attributes:
        source: Path of the source artifact.
        target: Path of the target artifact.
        edge_type: One of ``decided_from``, ``reviews``, ``verifies``,
            ``implements``, ``resolves``, ``supersedes``, ``references``.
        target_missing: ``True`` if ``target`` did not resolve to a known entity.
    """

    source: Path
    target: Path
    edge_type: str
    target_missing: bool = False


@dataclass
class BrainData:
    """Full in-memory representation of the project brain.

    Attributes:
        entities: All indexed artifacts (solutions, plans, brainstorms, etc.).
        topics: Auto-detected topic clusters.
        edges: Typed relationships between artifacts.
        generated: ISO date string when this data was produced.
    """

    entities: List[Entity]
    topics: List[Topic]
    edges: List[Edge]
    generated: str


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------


def build_brain(root: Path, generated: str = "") -> BrainData:
    """Orchestrate the full brain pipeline.

    Scans all ``.cg-docs/`` artifacts and ``roadmap.json`` features, extracts
    content keywords, clusters into topics, detects typed relationships, and
    returns a :class:`BrainData` ready for rendering.

    Uses lazy imports from sub-modules so that individual modules can be
    developed and tested incrementally without requiring all siblings to exist.

    Args:
        root: Project root directory (must contain ``.cg-docs/``).
        generated: ISO date string to stamp on the output.  Defaults to
            ``date.today().isoformat()`` when empty.

    Returns:
        :class:`BrainData` with ``entities``, ``topics``, and ``edges`` populated.

    Raises:
        ImportError: If a required brain sub-module has not been implemented yet.

    Example:
        >>> from pathlib import Path
        >>> from brain import build_brain
        >>> data = build_brain(root=Path("."))
        >>> print(len(data.entities), "entities indexed")
    """
    # Lazy imports allow incremental step-by-step module development.
    # Each sub-module is implemented in a separate plan step.
    from brain.scanner import scan_all, scan_roadmap  # Step 2
    from brain.extractor import extract_keywords       # Step 3
    from brain.clusterer import cluster_topics         # Step 4
    from brain.edge_detector import detect_edges       # Step 5

    # 1. Scan all entities
    entities: List[Entity] = scan_all(root)
    entities.extend(scan_roadmap(root))

    # 2. Extract keywords for each entity
    for entity in entities:
        entity.keywords = extract_keywords(entity, entity.text)
    # Free raw text — not used downstream by clusterer, edge detector, or renderer
    for entity in entities:
        entity.text = ""

    # 3. Cluster into topics
    topics: List[Topic] = cluster_topics(entities)

    # 4. Detect typed relationships
    edges: List[Edge] = detect_edges(entities, root)

    return BrainData(
        entities=entities,
        topics=topics,
        edges=edges,
        generated=generated or date.today().isoformat(),
    )


# ---------------------------------------------------------------------------
# Protocol re-export
# ---------------------------------------------------------------------------


def __getattr__(name: str) -> object:
    """Lazy re-export of ClusterStrategy from brain.clusterer.

    Avoids a circular import at module load time while still making
    ``from brain import ClusterStrategy`` work (architecture P3.4 fix).
    """
    if name == "ClusterStrategy":
        from brain.clusterer import ClusterStrategy  # noqa: PLC0415
        return ClusterStrategy
    raise AttributeError(f"module 'brain' has no attribute {name!r}")
