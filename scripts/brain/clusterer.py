"""brain.clusterer — Topic clustering for the brain engine.

Groups entities into topics using keyword co-occurrence and weighted Jaccard
similarity.  The algorithm is:

1. Build an inverted index: keyword → set of entity indices.
2. For each pair of entities sharing at least one keyword, compute the
   weighted Jaccard similarity of their keyword score vectors.
3. Sort all candidate pairs by Jaccard descending.
4. Greedily merge pairs above :data:`_MERGE_THRESHOLD` using Union-Find.
5. Discard clusters smaller than ``min_cluster_size`` (default 3).
6. For each surviving cluster, derive a topic slug + label from the top
   shared keywords.

The :class:`ClusterStrategy` protocol makes the algorithm swappable for
future NLP-based upgrades (e.g. embedding-based clustering) without changing
the ``cluster_topics()`` call site.

Note: topic deduplication is explicitly out of scope for Batch A (P3.2
deferred) and will be addressed in a future clusterer upgrade.
"""
from __future__ import annotations

import re
import warnings
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Protocol, Tuple

from brain import Entity, Topic

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

#: Weighted Jaccard threshold above which two entities are merged into the
#: same topic cluster.
_MERGE_THRESHOLD: float = 0.10

#: Maximum number of keywords used to label a topic (slug + label).
_LABEL_KEYWORDS: int = 3


# ---------------------------------------------------------------------------
# Pluggable strategy protocol
# ---------------------------------------------------------------------------


class ClusterStrategy(Protocol):
    """Protocol for topic clustering strategies.

    Implement this protocol to replace the default greedy-agglomerative
    algorithm with a custom approach (e.g. NLP embeddings).

    Example::

        class MyStrategy:
            def __call__(self, entities: List[Entity]) -> List[Topic]:
                ...  # custom logic
                return topics

        topics = cluster_topics(entities, strategy=MyStrategy())
    """

    def __call__(self, entities: List[Entity]) -> List[Topic]:
        """Cluster entities into topics.

        Args:
            entities: All entities to cluster (keywords must be populated).

        Returns:
            List of :class:`~brain.Topic` objects.
        """
        ...


# ---------------------------------------------------------------------------
# Internal Union-Find (path-compressed)
# ---------------------------------------------------------------------------


class _UnionFind:
    """Simple Union-Find (disjoint set) with path compression."""

    def __init__(self, n: int) -> None:
        self._parent = list(range(n))

    def find(self, x: int) -> int:
        while self._parent[x] != x:
            self._parent[x] = self._parent[self._parent[x]]  # path compression
            x = self._parent[x]
        return x

    def union(self, x: int, y: int) -> None:
        self._parent[self.find(x)] = self.find(y)

    def clusters(self) -> Dict[int, List[int]]:
        """Return a dict mapping root index → list of member indices."""
        groups: Dict[int, List[int]] = defaultdict(list)
        for i in range(len(self._parent)):
            groups[self.find(i)].append(i)
        return dict(groups)


# ---------------------------------------------------------------------------
# Weighted Jaccard
# ---------------------------------------------------------------------------


def _weighted_jaccard(
    kws_a: Dict[str, float], kws_b: Dict[str, float]
) -> float:
    """Compute weighted Jaccard similarity between two keyword score dicts.

    Weighted Jaccard = Σ min(score_a, score_b) / Σ max(score_a, score_b)
    over all keywords in the union of both sets.  Optimised via the identity
    ``Σ min(a,b) = Σa + Σb - Σ max(a,b)`` to iterate only the intersection,
    which is O(|intersection|) instead of O(|union|).

    Args:
        kws_a: Keyword → score dict for entity A.
        kws_b: Keyword → score dict for entity B.

    Returns:
        Similarity score in [0.0, 1.0].

    Example:
        >>> _weighted_jaccard({"a": 1.0, "b": 2.0}, {"a": 1.0, "c": 1.0})
        0.25
    """
    if not kws_a or not kws_b:
        return 0.0
    sum_a = sum(kws_a.values())
    sum_b = sum(kws_b.values())
    numerator = sum(min(kws_a[k], kws_b[k]) for k in kws_a if k in kws_b)
    denominator = sum_a + sum_b - numerator
    return numerator / denominator if denominator > 0.0 else 0.0


# ---------------------------------------------------------------------------
# Topic labelling
# ---------------------------------------------------------------------------

_NON_ALNUM = re.compile(r"[^a-z0-9]+")


def _topic_slug(keywords: List[str]) -> str:
    """Derive a kebab-case slug from the top keyword list.

    Args:
        keywords: Top keywords for the topic.

    Returns:
        Kebab-case slug, e.g. ``"pester-powershell-testing"``.
    """
    parts = [_NON_ALNUM.sub("-", kw.lower()).strip("-") for kw in keywords[:_LABEL_KEYWORDS]]
    return "-".join(p for p in parts if p)


def _topic_label(keywords: List[str]) -> str:
    """Derive a human-readable label from the top keyword list.

    Args:
        keywords: Top keywords for the topic.

    Returns:
        Title-cased label, e.g. ``"Pester / Powershell / Testing"``.
    """
    return " / ".join(kw.title() for kw in keywords[:_LABEL_KEYWORDS])


def _top_keywords_for_cluster(
    entity_kw_dicts: List[Dict[str, float]],
) -> List[str]:
    """Find the top keywords by total score across all cluster members.

    Args:
        entity_kw_dicts: List of {keyword: score} dicts for each entity in
            the cluster.

    Returns:
        Top :data:`_LABEL_KEYWORDS` keywords sorted by total score descending.
    """
    totals: Dict[str, float] = defaultdict(float)
    for kw_dict in entity_kw_dicts:
        for kw, score in kw_dict.items():
            totals[kw] += score
    sorted_kws = sorted(totals.items(), key=lambda kv: kv[1], reverse=True)
    return [kw for kw, _ in sorted_kws[:_LABEL_KEYWORDS]]


# ---------------------------------------------------------------------------
# Default greedy-agglomerative implementation
# ---------------------------------------------------------------------------


class _GreedyAgglomerative:
    """Default clustering strategy: inverted index + weighted Jaccard + Union-Find.

    This class implements :class:`ClusterStrategy` and is the default used by
    :func:`cluster_topics`.
    """

    def __init__(self, min_cluster_size: int = 3) -> None:
        self._min_size = min_cluster_size

    def __call__(self, entities: List[Entity]) -> List[Topic]:  # noqa: D102
        if not entities:
            return []

        # Build per-entity keyword dicts for fast lookup
        kw_dicts: List[Dict[str, float]] = [dict(e.keywords) for e in entities]

        # Build inverted index: keyword → set of entity indices
        inv_index: Dict[str, List[int]] = defaultdict(list)
        for idx, kw_dict in enumerate(kw_dicts):
            for kw in kw_dict:
                inv_index[kw].append(idx)

        # Collect candidate pairs (entities that share at least one keyword)
        candidate_pairs: Dict[Tuple[int, int], float] = {}
        for indices in inv_index.values():
            for i in range(len(indices)):
                for j in range(i + 1, len(indices)):
                    a, b = indices[i], indices[j]
                    pair: Tuple[int, int] = (a, b) if a < b else (b, a)
                    if pair not in candidate_pairs:
                        candidate_pairs[pair] = _weighted_jaccard(
                            kw_dicts[a], kw_dicts[b]
                        )

        # Sort pairs by Jaccard descending for greedy processing
        sorted_pairs = sorted(
            candidate_pairs.items(), key=lambda kv: kv[1], reverse=True
        )

        # Greedy merge with Union-Find
        uf = _UnionFind(len(entities))
        for pair, similarity in sorted_pairs:
            if similarity < _MERGE_THRESHOLD:
                break  # pairs are sorted; no need to continue
            a, b = pair
            uf.union(a, b)

        # Build clusters; discard those below min_cluster_size
        topics: List[Topic] = []
        for root, member_indices in uf.clusters().items():
            if len(member_indices) < self._min_size:
                continue

            member_entities = [entities[i] for i in member_indices]
            member_kw_dicts = [kw_dicts[i] for i in member_indices]
            top_kws = _top_keywords_for_cluster(member_kw_dicts)

            if not top_kws:
                continue

            topics.append(
                Topic(
                    slug=_topic_slug(top_kws),
                    label=_topic_label(top_kws),
                    keywords=top_kws,
                    entity_paths=[e.path for e in member_entities],
                )
            )

        # Sort topics by size descending (largest first); slug as tie-breaker for stability
        topics.sort(key=lambda t: (-len(t.entity_paths), t.slug))

        # Warn on slug collisions (two topics share identical top keywords)
        seen_slugs: Dict[str, int] = {}
        for t in topics:
            if t.slug in seen_slugs:
                warnings.warn(
                    f"[brain.clusterer] Topic slug collision: '{t.slug}' produced by "
                    f"{seen_slugs[t.slug] + 1} topics. BRAIN.md navigation links may be ambiguous.",
                    stacklevel=2,
                )
            seen_slugs[t.slug] = seen_slugs.get(t.slug, 0) + 1

        return topics


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def cluster_topics(
    entities: List[Entity],
    min_cluster_size: int = 3,
    strategy: ClusterStrategy | None = None,
) -> List[Topic]:
    """Cluster entities into topics by keyword co-occurrence.

    Uses :class:`_GreedyAgglomerative` by default.  Pass a custom ``strategy``
    implementing :class:`ClusterStrategy` to override.

    Args:
        entities: Entities with populated ``keywords`` fields.
        min_cluster_size: Clusters smaller than this are discarded.
        strategy: Optional custom clustering strategy.  If ``None``, uses
            the default greedy-agglomerative algorithm.

    Returns:
        List of :class:`~brain.Topic` objects sorted by size descending.
        Returns ``[]`` if fewer than ``min_cluster_size`` entities exist.

    Example:
        >>> from pathlib import Path
        >>> from brain import Entity
        >>> from brain.clusterer import cluster_topics
        >>> entities = [...]  # entities with keywords populated
        >>> topics = cluster_topics(entities, min_cluster_size=2)
        >>> print(len(topics), "topics found")
    """
    if strategy is not None:
        # min_cluster_size is intentionally not forwarded — the custom strategy
        # is responsible for its own cluster-size filtering.
        return strategy(entities)
    return _GreedyAgglomerative(min_cluster_size=min_cluster_size)(entities)
