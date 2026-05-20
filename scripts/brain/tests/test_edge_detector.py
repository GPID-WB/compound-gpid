"""Tests for brain.edge_detector — relationship detection.

Run from repo root:
    python -m pytest scripts/brain/tests/test_edge_detector.py -v
"""
from __future__ import annotations

from pathlib import Path
from typing import List

import pytest

from brain import Edge, Entity
from brain.edge_detector import (
    _IMPLEMENTS_THRESHOLD,
    _is_null,
    _jaccard_tokens,
    _resolve_path,
    _slug_tokens,
    detect_edges,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_ROOT = Path("/repo")


def _entity(
    slug: str,
    entity_type: str = "solution",
    frontmatter: dict | None = None,
    root_dir: str = ".cg-docs/solutions",
) -> Entity:
    return Entity(
        path=_ROOT / root_dir / f"{slug}.md",
        entity_type=entity_type,
        frontmatter=frontmatter or {},
    )


def _edges_of_type(edges: List[Edge], edge_type: str) -> List[Edge]:
    return [e for e in edges if e.edge_type == edge_type]


# ---------------------------------------------------------------------------
# _is_null
# ---------------------------------------------------------------------------


class TestIsNull:
    def test_none_is_null(self) -> None:
        assert _is_null(None) is True

    def test_empty_string_is_null(self) -> None:
        assert _is_null("") is True

    def test_tilde_is_null(self) -> None:
        assert _is_null("~") is True

    def test_null_string_is_null(self) -> None:
        assert _is_null("null") is True

    def test_none_string_is_null(self) -> None:
        assert _is_null("none") is True

    def test_case_insensitive(self) -> None:
        assert _is_null("NULL") is True
        assert _is_null("None") is True
        assert _is_null("NONE") is True

    def test_real_path_is_not_null(self) -> None:
        assert _is_null(".cg-docs/brainstorms/foo.md") is False

    def test_integer_is_not_null(self) -> None:
        assert _is_null(42) is False

    def test_false_is_not_null(self) -> None:
        assert _is_null(False) is False


# ---------------------------------------------------------------------------
# _slug_tokens
# ---------------------------------------------------------------------------


class TestSlugTokens:
    def test_basic_split(self) -> None:
        tokens = _slug_tokens("auto-generated-project-wiki")
        assert tokens == {"auto", "generated", "project", "wiki"}

    def test_stopwords_filtered(self) -> None:
        tokens = _slug_tokens("cg-plan-for-the-wiki")
        assert "cg" not in tokens
        assert "the" not in tokens
        assert "for" not in tokens

    def test_underscore_split(self) -> None:
        tokens = _slug_tokens("wiki_auto_generation")
        assert "wiki" in tokens
        assert "auto" in tokens

    def test_empty_slug(self) -> None:
        assert _slug_tokens("") == set()


# ---------------------------------------------------------------------------
# _jaccard_tokens
# ---------------------------------------------------------------------------


class TestJaccardTokens:
    def test_identical_sets(self) -> None:
        t = {"auto", "wiki"}
        assert _jaccard_tokens(t, t) == pytest.approx(1.0)

    def test_disjoint_sets(self) -> None:
        assert _jaccard_tokens({"a"}, {"b"}) == pytest.approx(0.0)

    def test_plan_review_from_plan(self) -> None:
        """Benchmark case from the plan review: Jaccard = 2/5 = 0.4."""
        plan = _slug_tokens("auto-generated-project-wiki")   # {auto, generated, project, wiki}
        feat = _slug_tokens("wiki-auto-generation")          # {wiki, auto, generation}
        result = _jaccard_tokens(plan, feat)
        # intersection={auto, wiki}=2, union={auto,generated,project,wiki,generation}=5
        assert result == pytest.approx(0.4)

    def test_empty_sets_return_0(self) -> None:
        assert _jaccard_tokens(set(), {"a"}) == pytest.approx(0.0)
        assert _jaccard_tokens({"a"}, set()) == pytest.approx(0.0)

    def test_symmetry(self) -> None:
        a = {"pester", "powershell"}
        b = {"pester", "python"}
        assert _jaccard_tokens(a, b) == pytest.approx(_jaccard_tokens(b, a))


# ---------------------------------------------------------------------------
# Explicit edges — plan → brainstorm (decided_from)
# ---------------------------------------------------------------------------


class TestDecidedFromEdges:
    def test_plan_brainstorm_field_produces_edge(self, tmp_path: Path) -> None:
        brainstorm_path = tmp_path / ".cg-docs/brainstorms/2026-05-19-idea.md"
        brainstorm_path.parent.mkdir(parents=True, exist_ok=True)
        brainstorm_path.write_text("---\ntitle: Idea\n---\n", encoding="utf-8")

        brainstorm = Entity(
            path=brainstorm_path,
            entity_type="brainstorm",
            frontmatter={"title": "Idea"},
        )
        plan = Entity(
            path=tmp_path / ".cg-docs/plans/2026-05-19-plan.md",
            entity_type="plan",
            frontmatter={"brainstorm": str(brainstorm_path)},
        )
        edges = detect_edges([plan, brainstorm], root=tmp_path)
        decided = _edges_of_type(edges, "decided_from")
        assert len(decided) == 1
        assert decided[0].source == plan.path

    def test_null_brainstorm_skipped(self, tmp_path: Path) -> None:
        plan = Entity(
            path=tmp_path / ".cg-docs/plans/plan.md",
            entity_type="plan",
            frontmatter={"brainstorm": None},
        )
        edges = detect_edges([plan], root=tmp_path)
        assert _edges_of_type(edges, "decided_from") == []

    def test_tilde_brainstorm_skipped(self, tmp_path: Path) -> None:
        plan = Entity(
            path=tmp_path / ".cg-docs/plans/plan.md",
            entity_type="plan",
            frontmatter={"brainstorm": "~"},
        )
        edges = detect_edges([plan], root=tmp_path)
        assert _edges_of_type(edges, "decided_from") == []

    def test_null_string_brainstorm_skipped(self, tmp_path: Path) -> None:
        plan = Entity(
            path=tmp_path / ".cg-docs/plans/plan.md",
            entity_type="plan",
            frontmatter={"brainstorm": "null"},
        )
        edges = detect_edges([plan], root=tmp_path)
        assert _edges_of_type(edges, "decided_from") == []


# ---------------------------------------------------------------------------
# Explicit edges — review → plan (reviews)
# ---------------------------------------------------------------------------


class TestReviewsEdges:
    def test_review_plan_field_produces_edge(self, tmp_path: Path) -> None:
        plan = Entity(
            path=tmp_path / ".cg-docs/plans/plan.md",
            entity_type="plan",
            frontmatter={"title": "Plan"},
        )
        review = Entity(
            path=tmp_path / ".cg-docs/reviews/review.md",
            entity_type="review",
            frontmatter={"plan": str(tmp_path / ".cg-docs/plans/plan.md")},
        )
        edges = detect_edges([plan, review], root=tmp_path)
        reviews = _edges_of_type(edges, "reviews")
        assert len(reviews) == 1
        assert reviews[0].source == review.path

    def test_null_plan_field_skipped(self, tmp_path: Path) -> None:
        review = Entity(
            path=tmp_path / ".cg-docs/reviews/r.md",
            entity_type="review",
            frontmatter={"plan": None},
        )
        edges = detect_edges([review], root=tmp_path)
        assert _edges_of_type(edges, "reviews") == []


# ---------------------------------------------------------------------------
# Explicit edges — review → parent-review (verifies)
# ---------------------------------------------------------------------------


class TestVerifiesEdges:
    def test_parent_review_field_produces_edge(self, tmp_path: Path) -> None:
        parent = Entity(
            path=tmp_path / ".cg-docs/reviews/parent.md",
            entity_type="review",
            frontmatter={"title": "Parent Review"},
        )
        child = Entity(
            path=tmp_path / ".cg-docs/reviews/child.md",
            entity_type="review",
            frontmatter={
                "parent-review": str(tmp_path / ".cg-docs/reviews/parent.md")
            },
        )
        edges = detect_edges([parent, child], root=tmp_path)
        verifies = _edges_of_type(edges, "verifies")
        assert len(verifies) == 1
        assert verifies[0].source == child.path


# ---------------------------------------------------------------------------
# Explicit edges — solution → plan/brainstorm (references)
# ---------------------------------------------------------------------------


class TestReferencesEdges:
    def test_solution_plan_field_produces_edge(self, tmp_path: Path) -> None:
        plan = Entity(
            path=tmp_path / ".cg-docs/plans/plan.md",
            entity_type="plan",
            frontmatter={},
        )
        solution = Entity(
            path=tmp_path / ".cg-docs/solutions/bugs/fix.md",
            entity_type="solution",
            frontmatter={"plan": str(tmp_path / ".cg-docs/plans/plan.md")},
        )
        edges = detect_edges([plan, solution], root=tmp_path)
        refs = _edges_of_type(edges, "references")
        assert any(e.source == solution.path for e in refs)

    def test_solution_brainstorm_field_produces_edge(self, tmp_path: Path) -> None:
        brainstorm = Entity(
            path=tmp_path / ".cg-docs/brainstorms/idea.md",
            entity_type="brainstorm",
            frontmatter={},
        )
        solution = Entity(
            path=tmp_path / ".cg-docs/solutions/bugs/fix.md",
            entity_type="solution",
            frontmatter={
                "brainstorm": str(tmp_path / ".cg-docs/brainstorms/idea.md")
            },
        )
        edges = detect_edges([brainstorm, solution], root=tmp_path)
        refs = _edges_of_type(edges, "references")
        assert any(e.source == solution.path for e in refs)


# ---------------------------------------------------------------------------
# target_missing flag
# ---------------------------------------------------------------------------


class TestTargetMissing:
    def test_known_target_not_missing(self, tmp_path: Path) -> None:
        brainstorm_path = tmp_path / ".cg-docs/brainstorms/idea.md"
        brainstorm_path.parent.mkdir(parents=True, exist_ok=True)
        brainstorm_path.write_text("---\ntitle: Idea\n---\n", encoding="utf-8")

        brainstorm = Entity(
            path=brainstorm_path,
            entity_type="brainstorm",
            frontmatter={},
        )
        plan = Entity(
            path=tmp_path / ".cg-docs/plans/plan.md",
            entity_type="plan",
            frontmatter={"brainstorm": str(brainstorm_path)},
        )
        edges = detect_edges([plan, brainstorm], root=tmp_path)
        decided = _edges_of_type(edges, "decided_from")
        assert len(decided) == 1
        assert decided[0].target_missing is False

    def test_unknown_target_marked_missing(self, tmp_path: Path) -> None:
        plan = Entity(
            path=tmp_path / ".cg-docs/plans/plan.md",
            entity_type="plan",
            frontmatter={
                "brainstorm": str(tmp_path / ".cg-docs/brainstorms/missing.md")
            },
        )
        edges = detect_edges([plan], root=tmp_path)
        decided = _edges_of_type(edges, "decided_from")
        assert len(decided) == 1
        assert decided[0].target_missing is True


# ---------------------------------------------------------------------------
# Inferred edges — same slug across directories
# ---------------------------------------------------------------------------


class TestSameSlugInferredEdges:
    def test_same_slug_different_types_get_reference(self, tmp_path: Path) -> None:
        slug = "2026-05-19-feature-x"
        plan = Entity(
            path=tmp_path / ".cg-docs/plans" / f"{slug}.md",
            entity_type="plan",
            frontmatter={},
        )
        brainstorm = Entity(
            path=tmp_path / ".cg-docs/brainstorms" / f"{slug}.md",
            entity_type="brainstorm",
            frontmatter={},
        )
        edges = detect_edges([plan, brainstorm], root=tmp_path)
        refs = _edges_of_type(edges, "references")
        # The same slug pair should produce a reference edge
        assert len(refs) >= 1

    def test_different_slugs_no_inferred_edge(self, tmp_path: Path) -> None:
        plan = Entity(
            path=tmp_path / ".cg-docs/plans/alpha.md",
            entity_type="plan",
            frontmatter={},
        )
        brainstorm = Entity(
            path=tmp_path / ".cg-docs/brainstorms/beta.md",
            entity_type="brainstorm",
            frontmatter={},
        )
        edges = detect_edges([plan, brainstorm], root=tmp_path)
        refs = _edges_of_type(edges, "references")
        # No inferred edge for different slugs and no frontmatter reference
        assert refs == []


# ---------------------------------------------------------------------------
# Roadmap implements edges
# ---------------------------------------------------------------------------


class TestImplementsEdges:
    def test_high_jaccard_produces_implements_edge(self, tmp_path: Path) -> None:
        """Plan slug with ≥40% token overlap with feature ID → implements edge."""
        plan = Entity(
            path=tmp_path / ".cg-docs/plans/auto-generated-project-wiki.md",
            entity_type="plan",
            frontmatter={},
        )
        feature = Entity(
            path=Path("roadmap.json#wiki-auto-generation"),
            entity_type="feature",
            frontmatter={"id": "wiki-auto-generation", "title": "Wiki Auto Generation"},
        )
        edges = detect_edges([plan, feature], root=tmp_path)
        implements = _edges_of_type(edges, "implements")
        assert len(implements) == 1
        assert implements[0].source == plan.path

    def test_low_jaccard_no_implements_edge(self, tmp_path: Path) -> None:
        plan = Entity(
            path=tmp_path / ".cg-docs/plans/pester-testing-improvements.md",
            entity_type="plan",
            frontmatter={},
        )
        feature = Entity(
            path=Path("roadmap.json#wiki-auto-generation"),
            entity_type="feature",
            frontmatter={"id": "wiki-auto-generation", "title": "Wiki Auto"},
        )
        edges = detect_edges([plan, feature], root=tmp_path)
        assert _edges_of_type(edges, "implements") == []


# ---------------------------------------------------------------------------
# Deduplication
# ---------------------------------------------------------------------------


class TestDeduplication:
    def test_no_duplicate_edges(self, tmp_path: Path) -> None:
        """Same slug inferred + explicit frontmatter shouldn't double-add."""
        slug = "2026-05-19-shared"
        brainstorm = Entity(
            path=tmp_path / ".cg-docs/brainstorms" / f"{slug}.md",
            entity_type="brainstorm",
            frontmatter={},
        )
        plan = Entity(
            path=tmp_path / ".cg-docs/plans" / f"{slug}.md",
            entity_type="plan",
            frontmatter={
                "brainstorm": str(tmp_path / ".cg-docs/brainstorms" / f"{slug}.md")
            },
        )
        edges = detect_edges([plan, brainstorm], root=tmp_path)
        # Count all edges
        keys = [(str(e.source), str(e.target), e.edge_type) for e in edges]
        assert len(keys) == len(set(keys)), "Duplicate edges detected"


# ---------------------------------------------------------------------------
# Empty / edge cases
# ---------------------------------------------------------------------------


class TestEdgeCases:
    def test_empty_entities_returns_empty(self, tmp_path: Path) -> None:
        assert detect_edges([], root=tmp_path) == []

    def test_no_frontmatter_fields_no_explicit_edges(self, tmp_path: Path) -> None:
        entities = [
            Entity(
                path=tmp_path / ".cg-docs/solutions/bugs/a.md",
                entity_type="solution",
                frontmatter={},
            ),
            Entity(
                path=tmp_path / ".cg-docs/plans/b.md",
                entity_type="plan",
                frontmatter={},
            ),
        ]
        edges = detect_edges(entities, root=tmp_path)
        # No explicit edges; only potential inferred if same slug (they're not)
        explicit_types = {"decided_from", "reviews", "verifies"}
        assert all(e.edge_type not in explicit_types for e in edges)


# ---------------------------------------------------------------------------
# Regression: brainstorm → plan edge type must be "references" not "reviews"
# ---------------------------------------------------------------------------


class TestBrainstormPlanEdge:
    """Regression guard for P2.9: brainstorm with plan: field should emit
    a ``references`` edge, not a ``reviews`` edge."""

    def test_brainstorm_plan_field_produces_references_not_reviews(
        self, tmp_path: Path
    ) -> None:
        plan = Entity(
            path=tmp_path / ".cg-docs/plans/plan.md",
            entity_type="plan",
            frontmatter={},
        )
        brainstorm = Entity(
            path=tmp_path / ".cg-docs/brainstorms/idea.md",
            entity_type="brainstorm",
            frontmatter={"plan": str(tmp_path / ".cg-docs/plans/plan.md")},
        )
        edges = detect_edges([plan, brainstorm], root=tmp_path)
        edge_types = {e.edge_type for e in edges if e.source == brainstorm.path}
        # Brainstorm precedes a plan — it references it, not reviews it
        assert "references" in edge_types, "brainstorm→plan should emit 'references'"
        assert "reviews" not in edge_types, "brainstorm→plan must NOT emit 'reviews'"

    def test_review_plan_field_still_produces_reviews(
        self, tmp_path: Path
    ) -> None:
        plan = Entity(
            path=tmp_path / ".cg-docs/plans/plan.md",
            entity_type="plan",
            frontmatter={},
        )
        review = Entity(
            path=tmp_path / ".cg-docs/reviews/review.md",
            entity_type="review",
            frontmatter={"plan": str(tmp_path / ".cg-docs/plans/plan.md")},
        )
        edges = detect_edges([plan, review], root=tmp_path)
        edge_types = {e.edge_type for e in edges if e.source == review.path}
        # Review entities still use "reviews" edge type
        assert "reviews" in edge_types
        assert "references" not in edge_types

    def test_null_plan_field_produces_no_edge(self, tmp_path: Path) -> None:
        brainstorm = Entity(
            path=tmp_path / ".cg-docs/brainstorms/idea.md",
            entity_type="brainstorm",
            frontmatter={"plan": None},
        )
        assert _edges_of_type(detect_edges([brainstorm], root=tmp_path), "references") == []

    def test_tilde_plan_field_produces_no_edge(self, tmp_path: Path) -> None:
        brainstorm = Entity(
            path=tmp_path / ".cg-docs/brainstorms/idea.md",
            entity_type="brainstorm",
            frontmatter={"plan": "~"},
        )
        assert _edges_of_type(detect_edges([brainstorm], root=tmp_path), "references") == []
