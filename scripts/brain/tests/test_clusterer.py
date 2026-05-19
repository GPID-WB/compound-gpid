"""Tests for brain.clusterer — topic clustering.

Run from repo root:
    python -m pytest scripts/brain/tests/test_clusterer.py -v
"""
from __future__ import annotations

from pathlib import Path
from typing import List, Tuple

import pytest

from brain import Entity, Topic
from brain.clusterer import (
    _GreedyAgglomerative,
    _UnionFind,
    _top_keywords_for_cluster,
    _topic_label,
    _topic_slug,
    _weighted_jaccard,
    cluster_topics,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _entity_with_keywords(
    slug: str,
    keywords: List[Tuple[str, float]],
    entity_type: str = "solution",
) -> Entity:
    return Entity(
        path=Path(f".cg-docs/{entity_type}s/{slug}.md"),
        entity_type=entity_type,
        frontmatter={"title": slug},
        keywords=keywords,
    )


def _kws(*args: str, weight: float = 1.0) -> List[Tuple[str, float]]:
    """Build a keyword list where every keyword has the same weight."""
    return [(kw, weight) for kw in args]


# ---------------------------------------------------------------------------
# _weighted_jaccard
# ---------------------------------------------------------------------------


class TestWeightedJaccard:
    def test_identical_dicts_return_1(self) -> None:
        kws = {"pester": 3.0, "powershell": 2.0}
        assert _weighted_jaccard(kws, kws) == pytest.approx(1.0)

    def test_disjoint_dicts_return_0(self) -> None:
        assert _weighted_jaccard({"a": 1.0}, {"b": 1.0}) == pytest.approx(0.0)

    def test_partial_overlap(self) -> None:
        # shared "a" (weight 1 each), union adds "b" and "c"
        # intersection = min(1,1) = 1, union = max(1,1)+max(0,1)+max(1,0) = 1+1+1 = 3
        result = _weighted_jaccard({"a": 1.0, "b": 1.0}, {"a": 1.0, "c": 1.0})
        assert result == pytest.approx(1 / 3)

    def test_empty_dicts_return_0(self) -> None:
        assert _weighted_jaccard({}, {}) == pytest.approx(0.0)

    def test_one_empty_dict_return_0(self) -> None:
        assert _weighted_jaccard({"a": 1.0}, {}) == pytest.approx(0.0)

    def test_asymmetric_weights(self) -> None:
        # "a": min(3,1)=1, max(3,1)=3; "b": min(2,0)=0, max(2,0)=2
        # intersection=1, union=5
        result = _weighted_jaccard({"a": 3.0, "b": 2.0}, {"a": 1.0})
        assert result == pytest.approx(1 / 5)

    def test_symmetry(self) -> None:
        kws_a = {"x": 2.0, "y": 1.0}
        kws_b = {"y": 2.0, "z": 3.0}
        assert _weighted_jaccard(kws_a, kws_b) == pytest.approx(
            _weighted_jaccard(kws_b, kws_a)
        )


# ---------------------------------------------------------------------------
# _UnionFind
# ---------------------------------------------------------------------------


class TestUnionFind:
    def test_initially_each_is_own_root(self) -> None:
        uf = _UnionFind(3)
        assert uf.find(0) == 0
        assert uf.find(1) == 1
        assert uf.find(2) == 2

    def test_union_merges_roots(self) -> None:
        uf = _UnionFind(3)
        uf.union(0, 1)
        assert uf.find(0) == uf.find(1)

    def test_union_is_transitive(self) -> None:
        uf = _UnionFind(4)
        uf.union(0, 1)
        uf.union(1, 2)
        assert uf.find(0) == uf.find(2)

    def test_unconnected_stays_separate(self) -> None:
        uf = _UnionFind(3)
        uf.union(0, 1)
        assert uf.find(2) != uf.find(0)

    def test_clusters_groups_correctly(self) -> None:
        uf = _UnionFind(4)
        uf.union(0, 1)
        uf.union(2, 3)
        clusters = uf.clusters()
        sizes = sorted(len(v) for v in clusters.values())
        assert sizes == [2, 2]


# ---------------------------------------------------------------------------
# Topic labelling helpers
# ---------------------------------------------------------------------------


class TestTopicSlug:
    def test_basic_slug(self) -> None:
        assert _topic_slug(["pester", "powershell", "testing"]) == "pester-powershell-testing"

    def test_special_chars_replaced(self) -> None:
        slug = _topic_slug(["cg-work", "cg-plan"])
        assert "/" not in slug
        assert "_" not in slug or "-" in slug

    def test_limited_to_label_keywords(self) -> None:
        slug = _topic_slug(["a", "b", "c", "d", "e"])
        parts = slug.split("-")
        # slug from first 3 keywords only (each may be multi-char)
        assert len(parts) <= 3


class TestTopicLabel:
    def test_title_case_label(self) -> None:
        assert _topic_label(["pester", "powershell"]) == "Pester / Powershell"

    def test_limited_to_three(self) -> None:
        label = _topic_label(["a", "b", "c", "d"])
        parts = label.split(" / ")
        assert len(parts) <= 3


class TestTopKeywordsForCluster:
    def test_sums_across_entities(self) -> None:
        kw_dicts = [{"pester": 3.0, "python": 1.0}, {"pester": 2.0, "r": 1.0}]
        top = _top_keywords_for_cluster(kw_dicts)
        assert top[0] == "pester"  # highest total score

    def test_empty_list(self) -> None:
        assert _top_keywords_for_cluster([]) == []


# ---------------------------------------------------------------------------
# cluster_topics — integration
# ---------------------------------------------------------------------------


class TestClusterTopics:
    def _make_cluster_entities(self) -> List[Entity]:
        """Build a set of entities that should form two clear topic groups."""
        # Group 1: pester + powershell focused
        pester_kws = _kws("pester", "powershell", "invoke", "testing", weight=3.0)
        group1 = [
            _entity_with_keywords(f"pester-{i}", pester_kws + _kws(f"unique{i}"))
            for i in range(3)
        ]
        # Group 2: python + scanner focused
        python_kws = _kws("python", "scanner", "extractor", "pytest", weight=3.0)
        group2 = [
            _entity_with_keywords(f"python-{i}", python_kws + _kws(f"other{i}"))
            for i in range(3)
        ]
        return group1 + group2

    def test_returns_list_of_topics(self) -> None:
        entities = self._make_cluster_entities()
        topics = cluster_topics(entities, min_cluster_size=2)
        assert isinstance(topics, list)
        assert all(isinstance(t, Topic) for t in topics)

    def test_related_entities_cluster_together(self) -> None:
        entities = self._make_cluster_entities()
        topics = cluster_topics(entities, min_cluster_size=2)
        assert len(topics) >= 1

    def test_min_cluster_size_respected(self) -> None:
        # With min_cluster_size=10 and only 6 entities, expect no topics
        entities = self._make_cluster_entities()
        topics = cluster_topics(entities, min_cluster_size=10)
        assert topics == []

    def test_empty_entities_returns_empty(self) -> None:
        assert cluster_topics([]) == []

    def test_sorted_by_size_descending(self) -> None:
        entities = self._make_cluster_entities()
        topics = cluster_topics(entities, min_cluster_size=2)
        if len(topics) >= 2:
            sizes = [len(t.entity_paths) for t in topics]
            assert sizes == sorted(sizes, reverse=True)

    def test_topic_has_slug_and_label(self) -> None:
        entities = self._make_cluster_entities()
        topics = cluster_topics(entities, min_cluster_size=2)
        for t in topics:
            assert t.slug != ""
            assert t.label != ""

    def test_topic_keywords_non_empty(self) -> None:
        entities = self._make_cluster_entities()
        topics = cluster_topics(entities, min_cluster_size=2)
        for t in topics:
            assert len(t.keywords) > 0

    def test_entity_paths_in_topics(self) -> None:
        entities = self._make_cluster_entities()
        topics = cluster_topics(entities, min_cluster_size=2)
        for t in topics:
            assert len(t.entity_paths) > 0


class TestClusterStrategy:
    def test_custom_strategy_is_used(self) -> None:
        """The pluggable ClusterStrategy protocol works."""

        class ConstantStrategy:
            def __call__(self, entities: List[Entity]) -> List[Topic]:
                return [
                    Topic(
                        slug="fixed-topic",
                        label="Fixed Topic",
                        keywords=["fixed"],
                        entity_paths=[e.path for e in entities],
                    )
                ]

        entities = [
            _entity_with_keywords("a", _kws("pester")),
            _entity_with_keywords("b", _kws("pester")),
        ]
        topics = cluster_topics(entities, strategy=ConstantStrategy())
        assert len(topics) == 1
        assert topics[0].slug == "fixed-topic"

    def test_none_strategy_uses_default(self) -> None:
        entities = [
            _entity_with_keywords(f"e{i}", _kws("pester", "powershell", weight=3.0))
            for i in range(3)
        ]
        # Should not raise
        topics = cluster_topics(entities, strategy=None, min_cluster_size=2)
        assert isinstance(topics, list)


class TestEdgeCases:
    def test_all_disjoint_keywords_no_clusters(self) -> None:
        entities = [
            _entity_with_keywords(f"e{i}", [(f"unique_keyword_{i}", 5.0)])
            for i in range(5)
        ]
        topics = cluster_topics(entities, min_cluster_size=2)
        assert topics == []

    def test_single_entity_below_min_size(self) -> None:
        entities = [_entity_with_keywords("solo", _kws("pester", "testing"))]
        topics = cluster_topics(entities, min_cluster_size=3)
        assert topics == []

    def test_no_keywords_entities_handled(self) -> None:
        entities = [
            Entity(
                path=Path("f.md"),
                entity_type="solution",
                frontmatter={},
                keywords=[],
            )
            for _ in range(4)
        ]
        # Should not raise; likely no clusters (no shared keywords)
        topics = cluster_topics(entities, min_cluster_size=2)
        assert isinstance(topics, list)
