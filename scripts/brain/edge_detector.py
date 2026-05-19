"""brain.edge_detector — Relationship detection for the brain engine.

Detects typed directed relationships between entities and outputs a list of
:class:`~brain.Edge` objects.  Two detection strategies are used:

**Explicit edges** — derived from frontmatter fields:

+-------------------------------+-------------+-------------------+
| Source entity type            | Field       | Edge type         |
+===============================+=============+===================+
| ``plan``                      | ``brainstorm``  | ``decided_from``  |
| ``review``                    | ``plan``        | ``reviews``       |
| ``review``                    | ``parent-review`` | ``verifies``    |
| ``solution``                  | ``plan``        | ``references``    |
| ``solution``                  | ``brainstorm``  | ``references``    |
+-------------------------------+-------------+-------------------+

**Inferred edges** — derived from structural signals:

- **Same slug across directories**: two entities with the same filename stem
  but in different ``.cg-docs/`` sub-directories get a ``references`` edge.
- **Roadmap implements**: a plan whose slug tokens overlap a feature's ID
  tokens with weighted Jaccard ≥ 0.4 gets an ``implements`` edge.

**Null-guard**: any frontmatter field whose value is ``None`` or whose string
value (case-insensitive) is ``""``, ``"null"``, ``"~"``, or ``"none"`` is
silently skipped.  This handles the common ``brainstorm: ~`` pattern in plan
files that have no associated brainstorm yet.
"""
from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, FrozenSet, List, Set, Tuple

from brain import Edge, Entity

# ---------------------------------------------------------------------------
# Null-guard
# ---------------------------------------------------------------------------

_NULL_STRINGS: FrozenSet[str] = frozenset({"", "null", "~", "none"})


def _is_null(val: Any) -> bool:
    """Return ``True`` if ``val`` is a null-like value.

    Handles: ``None``, empty string, and the YAML null strings ``"null"``,
    ``"~"``, ``"none"`` (case-insensitive).

    Args:
        val: The frontmatter field value to test.

    Returns:
        ``True`` if the value should be treated as absent.

    Example:
        >>> _is_null(None)
        True
        >>> _is_null("~")
        True
        >>> _is_null(".cg-docs/brainstorms/foo.md")
        False
    """
    if val is None:
        return True
    if isinstance(val, str):
        return val.strip().lower() in _NULL_STRINGS
    return False


# ---------------------------------------------------------------------------
# Path resolution
# ---------------------------------------------------------------------------


def _resolve_path(val: str, root: Path) -> Path:
    """Resolve a frontmatter path value to an absolute :class:`Path`.

    Frontmatter paths are typically relative to the project root (e.g.
    ``.cg-docs/plans/foo.md``).  This function makes them absolute.

    Args:
        val: Path string from a frontmatter field.
        root: Project root directory.

    Returns:
        Absolute :class:`Path`.

    Example:
        >>> _resolve_path(".cg-docs/plans/foo.md", Path("/repo"))
        PosixPath('/repo/.cg-docs/plans/foo.md')
    """
    p = Path(val)
    if p.is_absolute():
        return p
    return (root / p).resolve()


# ---------------------------------------------------------------------------
# Token Jaccard (for roadmap implements edges)
# ---------------------------------------------------------------------------

#: Stopwords filtered before computing token Jaccard between slug tokens.
_JACCARD_STOPWORDS: FrozenSet[str] = frozenset({"cg", "and", "the", "for", "in", "a", "an"})

_SLUG_SPLIT_RE = re.compile(r"[-_]")


def _slug_tokens(slug: str) -> Set[str]:
    """Split a slug into lowercase tokens, filtering Jaccard stopwords.

    Args:
        slug: Kebab or snake-case identifier string.

    Returns:
        Set of non-empty, non-stopword token strings.

    Example:
        >>> _slug_tokens("auto-generated-project-wiki")
        {'auto', 'generated', 'project', 'wiki'}
    """
    tokens = {t for t in _SLUG_SPLIT_RE.split(slug.lower()) if t}
    return tokens - _JACCARD_STOPWORDS


def _jaccard_tokens(tokens_a: Set[str], tokens_b: Set[str]) -> float:
    """Compute unweighted set Jaccard similarity between two token sets.

    Args:
        tokens_a: Token set for entity A.
        tokens_b: Token set for entity B.

    Returns:
        Jaccard similarity in [0.0, 1.0].

    Example:
        >>> _jaccard_tokens({"auto", "wiki"}, {"wiki", "generation"})
        0.333...
    """
    if not tokens_a or not tokens_b:
        return 0.0
    intersection = len(tokens_a & tokens_b)
    union = len(tokens_a | tokens_b)
    return intersection / union if union > 0 else 0.0


#: Minimum Jaccard similarity for plan→feature ``implements`` edges.
_IMPLEMENTS_THRESHOLD: float = 0.4


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def detect_edges(entities: List[Entity], root: Path) -> List[Edge]:
    """Detect all typed relationships between entities.

    Applies both explicit frontmatter edge rules and structural inference.
    Deduplicates edges by ``(source, target, edge_type)`` key.

    Args:
        entities: All indexed entities (from scanner + extractor).
        root: Project root directory (used to resolve relative paths).

    Returns:
        List of :class:`~brain.Edge` objects.

    Example:
        >>> from pathlib import Path
        >>> from brain.edge_detector import detect_edges
        >>> edges = detect_edges(entities, root=Path("."))
        >>> print(len(edges), "relationships detected")
    """
    # Build a set of known absolute paths for target-missing detection
    known_paths: Set[Path] = set()
    for e in entities:
        if e.entity_type != "feature":  # virtual paths can't be resolved
            known_paths.add(e.path.resolve() if e.path.is_absolute() else (root / e.path).resolve())

    edges: List[Edge] = []
    # Deduplication key: (source_str, target_str, edge_type)
    seen: Set[Tuple[str, str, str]] = set()

    def _add_edge(source: Path, target: Path, edge_type: str, target_missing: bool) -> None:
        key = (str(source), str(target), edge_type)
        if key not in seen:
            seen.add(key)
            edges.append(Edge(source=source, target=target, edge_type=edge_type, target_missing=target_missing))

    # -----------------------------------------------------------------------
    # Pass 1: Explicit frontmatter edges
    # -----------------------------------------------------------------------
    for entity in entities:
        fm = entity.frontmatter
        source = entity.path

        if entity.entity_type == "plan":
            # brainstorm: <path>  →  plan decided_from brainstorm
            bval = fm.get("brainstorm")
            if not _is_null(bval) and isinstance(bval, str):
                target = _resolve_path(bval, root)
                _add_edge(source, target, "decided_from", target not in known_paths)

        elif entity.entity_type == "review":
            # plan: <path>  →  review reviews plan
            pval = fm.get("plan")
            if not _is_null(pval) and isinstance(pval, str):
                target = _resolve_path(pval, root)
                _add_edge(source, target, "reviews", target not in known_paths)

            # parent-review: <path>  →  review verifies parent-review
            prval = fm.get("parent-review")
            if not _is_null(prval) and isinstance(prval, str):
                target = _resolve_path(prval, root)
                _add_edge(source, target, "verifies", target not in known_paths)

        elif entity.entity_type == "brainstorm":
            # plan: <path>  →  brainstorm references plan
            # A brainstorm precedes and informs a plan; it does not "review" one.
            pval = fm.get("plan")
            if not _is_null(pval) and isinstance(pval, str):
                target = _resolve_path(pval, root)
                _add_edge(source, target, "references", target not in known_paths)

        elif entity.entity_type == "solution":
            # plan: or brainstorm: <path>  →  solution references plan/brainstorm
            for field in ("plan", "brainstorm"):
                fval = fm.get(field)
                if not _is_null(fval) and isinstance(fval, str):
                    target = _resolve_path(fval, root)
                    _add_edge(source, target, "references", target not in known_paths)

    # -----------------------------------------------------------------------
    # Pass 2: Inferred edges — same slug across different directories
    # -----------------------------------------------------------------------
    slug_to_entities: Dict[str, List[Entity]] = defaultdict(list)
    for entity in entities:
        if entity.entity_type != "feature":
            slug_to_entities[entity.slug].append(entity)

    for _slug, slug_entities in slug_to_entities.items():
        if len(slug_entities) < 2:
            continue
        # Add a reference edge between each pair sharing the same slug
        for i in range(len(slug_entities)):
            for j in range(i + 1, len(slug_entities)):
                a = slug_entities[i]
                b = slug_entities[j]
                _add_edge(a.path, b.path, "references", False)

    # -----------------------------------------------------------------------
    # Pass 3: Roadmap implements — plan tokens vs feature ID tokens (Jaccard ≥ 0.4)
    # -----------------------------------------------------------------------
    plans = [e for e in entities if e.entity_type == "plan"]
    features = [e for e in entities if e.entity_type == "feature"]

    feature_token_list = [(e, _slug_tokens(e.slug)) for e in features]
    for plan in plans:
        plan_tokens = _slug_tokens(plan.slug)
        if not plan_tokens:
            continue
        for feature, feature_tokens in feature_token_list:
            if not feature_tokens:
                continue
            if _jaccard_tokens(plan_tokens, feature_tokens) >= _IMPLEMENTS_THRESHOLD:
                _add_edge(plan.path, feature.path, "implements", False)

    return edges
