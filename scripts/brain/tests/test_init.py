"""Tests for scripts/brain/__init__.py and scripts/brain/utils.py.

Covers:
- Dataclass instantiation (Entity, Topic, Edge, BrainData)
- Entity convenience properties (slug, title, date_str, status, tags)
- Null coercion fix: _coerce("null") / _coerce("~") / _coerce("none") -> None
- Import availability of build_brain and parse_frontmatter

Run from repo root:
    python -m pytest scripts/brain/tests/test_init.py -v
"""
from __future__ import annotations

from pathlib import Path
from unittest import mock

import pytest


# ---------------------------------------------------------------------------
# Import checks
# ---------------------------------------------------------------------------


class TestImports:
    def test_build_brain_importable(self) -> None:
        from brain import build_brain

        assert callable(build_brain)

    def test_parse_frontmatter_importable(self) -> None:
        from brain.utils import parse_frontmatter

        assert callable(parse_frontmatter)

    def test_brain_version(self) -> None:
        import brain

        assert brain.__version__ == "0.2.0"

    def test_cluster_strategy_importable_from_brain(self) -> None:
        """P3.4 re-export: from brain import ClusterStrategy must resolve via __getattr__."""
        from brain import ClusterStrategy
        from brain.clusterer import ClusterStrategy as _Direct

        assert ClusterStrategy is _Direct


class TestInlineListParser:
    def test_inline_list_none_returns_none(self) -> None:
        from brain.utils import _parse_inline_list

        assert _parse_inline_list("None") is None

    def test_inline_list_empty_returns_empty_list(self) -> None:
        from brain.utils import _parse_inline_list

        assert _parse_inline_list("[]") == []

    def test_inline_list_preserves_apostrophes(self) -> None:
        from brain.utils import _parse_inline_list

        assert _parse_inline_list('["children\'s data", testing]') == ["children's data", "testing"]


# ---------------------------------------------------------------------------
# Dataclass instantiation
# ---------------------------------------------------------------------------


class TestEntityDataclass:
    def test_minimal_instantiation(self) -> None:
        from brain import Entity

        e = Entity(
            path=Path(".cg-docs/solutions/bugs/foo.md"),
            entity_type="solution",
            frontmatter={"title": "Test fix", "date": "2026-05-19"},
        )
        assert e.entity_type == "solution"
        assert e.summary == ""
        assert e.text == ""
        assert e.keywords == []

    def test_slug_from_path(self) -> None:
        from brain import Entity

        e = Entity(
            path=Path(".cg-docs/plans/2026-05-19-my-plan.md"),
            entity_type="plan",
            frontmatter={},
        )
        assert e.slug == "2026-05-19-my-plan"

    def test_slug_from_roadmap_virtual_path(self) -> None:
        from brain import Entity

        e = Entity(
            path=Path("roadmap.json#wiki-auto-generation"),
            entity_type="feature",
            frontmatter={},
        )
        assert e.slug == "wiki-auto-generation"

    def test_title_from_frontmatter(self) -> None:
        from brain import Entity

        e = Entity(
            path=Path("foo.md"),
            entity_type="solution",
            frontmatter={"title": "My Title"},
        )
        assert e.title == "My Title"

    def test_title_falls_back_to_slug(self) -> None:
        from brain import Entity

        e = Entity(
            path=Path("2026-05-19-some-fix.md"),
            entity_type="solution",
            frontmatter={},
        )
        assert e.title == "2026-05-19-some-fix"

    def test_date_str_from_frontmatter(self) -> None:
        from brain import Entity

        e = Entity(
            path=Path("f.md"),
            entity_type="plan",
            frontmatter={"date": "2026-05-19"},
        )
        assert e.date_str == "2026-05-19"

    def test_date_str_empty_when_absent(self) -> None:
        from brain import Entity

        e = Entity(path=Path("f.md"), entity_type="plan", frontmatter={})
        assert e.date_str == ""

    def test_status_lowercased(self) -> None:
        from brain import Entity

        e = Entity(
            path=Path("f.md"),
            entity_type="plan",
            frontmatter={"status": "Active"},
        )
        assert e.status == "active"

    def test_tags_list(self) -> None:
        from brain import Entity

        e = Entity(
            path=Path("f.md"),
            entity_type="solution",
            frontmatter={"tags": ["pester", "powershell"]},
        )
        assert e.tags == ["pester", "powershell"]

    def test_tags_empty_when_absent(self) -> None:
        from brain import Entity

        e = Entity(path=Path("f.md"), entity_type="solution", frontmatter={})
        assert e.tags == []


class TestTopicDataclass:
    def test_instantiation(self) -> None:
        from brain import Topic

        t = Topic(
            slug="pester-testing",
            label="Pester Testing",
            keywords=["pester", "testing"],
            entity_paths=[Path("a.md"), Path("b.md")],
        )
        assert t.slug == "pester-testing"
        assert t.label == "Pester Testing"
        assert len(t.keywords) == 2
        assert len(t.entity_paths) == 2


class TestEdgeDataclass:
    def test_instantiation(self) -> None:
        from brain import Edge

        e = Edge(
            source=Path("plan.md"),
            target=Path("brainstorm.md"),
            edge_type="decided_from",
        )
        assert e.edge_type == "decided_from"
        assert e.target_missing is False

    def test_target_missing_flag(self) -> None:
        from brain import Edge

        e = Edge(
            source=Path("a.md"),
            target=Path("missing.md"),
            edge_type="references",
            target_missing=True,
        )
        assert e.target_missing is True


class TestBrainDataDataclass:
    def test_instantiation(self) -> None:
        from brain import BrainData

        bd = BrainData(entities=[], topics=[], edges=[], generated="2026-05-19")
        assert bd.generated == "2026-05-19"
        assert bd.entities == []
        assert bd.topics == []
        assert bd.edges == []


# ---------------------------------------------------------------------------
# Null coercion fix (P1.2)
# ---------------------------------------------------------------------------


class TestNullCoercion:
    """_coerce() must return None for YAML null values, not treat them as paths."""

    def test_null_string_returns_none(self) -> None:
        from brain.utils import _coerce

        assert _coerce("null") is None

    def test_tilde_returns_none(self) -> None:
        from brain.utils import _coerce

        assert _coerce("~") is None

    def test_none_string_returns_none(self) -> None:
        from brain.utils import _coerce

        assert _coerce("none") is None

    def test_null_case_insensitive(self) -> None:
        from brain.utils import _coerce

        assert _coerce("NULL") is None
        assert _coerce("Null") is None
        assert _coerce("None") is None
        assert _coerce("NONE") is None

    def test_true_coerced(self) -> None:
        from brain.utils import _coerce

        assert _coerce("true") is True
        assert _coerce("yes") is True

    def test_false_coerced(self) -> None:
        from brain.utils import _coerce

        assert _coerce("false") is False
        assert _coerce("no") is False

    def test_integer_coerced(self) -> None:
        from brain.utils import _coerce

        assert _coerce("42") == 42
        assert _coerce("-1") == -1

    def test_date_preserved_as_string(self) -> None:
        from brain.utils import _coerce

        assert _coerce("2026-05-19") == "2026-05-19"

    def test_non_null_path_preserved(self) -> None:
        from brain.utils import _coerce

        val = _coerce(".cg-docs/brainstorms/2026-05-19-knowledge-brain-engine.md")
        assert val == ".cg-docs/brainstorms/2026-05-19-knowledge-brain-engine.md"

    def test_non_null_path_is_not_none(self) -> None:
        """Regression guard: real paths must not be coerced to None."""
        from brain.utils import _coerce

        assert _coerce(".cg-docs/plans/2026-05-01-wiki-system.md") is not None


# ---------------------------------------------------------------------------
# parse_frontmatter smoke tests
# ---------------------------------------------------------------------------


class TestParseFrontmatter:
    def test_basic_key_value(self) -> None:
        from brain.utils import parse_frontmatter

        text = "---\ndate: 2026-05-19\ntitle: My Doc\n---\n# Body"
        fm = parse_frontmatter(text)
        assert fm["date"] == "2026-05-19"
        assert fm["title"] == "My Doc"

    def test_empty_without_frontmatter(self) -> None:
        from brain.utils import parse_frontmatter

        fm = parse_frontmatter("# Just a heading\n\nNo frontmatter here.")
        assert fm == {}

    def test_null_value_coerced_to_none(self) -> None:
        """brainstorm: ~ must parse to None, not the string '~'."""
        from brain.utils import parse_frontmatter

        text = "---\nbrainstorm: ~\nplan: null\n---\n"
        fm = parse_frontmatter(text)
        assert fm["brainstorm"] is None
        assert fm["plan"] is None

    def test_inline_list(self) -> None:
        from brain.utils import parse_frontmatter

        text = "---\ntags: [pester, powershell, testing]\n---\n"
        fm = parse_frontmatter(text)
        assert fm["tags"] == ["pester", "powershell", "testing"]

    def test_boolean_values(self) -> None:
        from brain.utils import parse_frontmatter

        text = "---\nactive: true\narchived: false\n---\n"
        fm = parse_frontmatter(text)
        assert fm["active"] is True
        assert fm["archived"] is False


# ---------------------------------------------------------------------------
# _write_atomic tests  (P2.6)
# ---------------------------------------------------------------------------


class TestWriteAtomic:
    def test_creates_file(self, tmp_path: Path) -> None:
        from brain.utils import write_atomic

        p = tmp_path / "out.md"
        write_atomic(p, "hello")
        assert p.read_text(encoding="utf-8") == "hello"

    def test_overwrites_existing(self, tmp_path: Path) -> None:
        from brain.utils import write_atomic

        p = tmp_path / "out.md"
        write_atomic(p, "first")
        write_atomic(p, "second")
        assert p.read_text(encoding="utf-8") == "second"

    def test_utf8_encoding(self, tmp_path: Path) -> None:
        from brain.utils import write_atomic

        p = tmp_path / "out.md"
        content = "# Héllo wörld — résumé"
        write_atomic(p, content)
        assert p.read_text(encoding="utf-8") == content

    def test_raises_after_windows_retry_exhausted(self, tmp_path: Path) -> None:
        from brain.utils import write_atomic

        p = tmp_path / "out.md"
        with (
            mock.patch("brain.utils.os.name", "nt"),
            mock.patch("brain.utils.time.sleep", return_value=None),
            mock.patch("brain.utils.os.replace", side_effect=PermissionError("locked")),
        ):
            with pytest.raises(PermissionError):
                write_atomic(p, "content")


# ---------------------------------------------------------------------------
# extract_summary tests  (P2.7)
# ---------------------------------------------------------------------------


class TestExtractSummary:
    def test_problem_section_preferred(self) -> None:
        from brain.utils import extract_summary

        text = "---\ntitle: X\n---\n## Overview\nOther stuff.\n## Problem\nThis is the fix.\n"
        result = extract_summary(text)
        assert "fix" in result

    def test_falls_back_to_first_paragraph(self) -> None:
        from brain.utils import extract_summary

        text = "---\ntitle: X\n---\n\nFirst real paragraph here.\n"
        result = extract_summary(text)
        assert "paragraph" in result

    def test_truncated_to_max_words(self) -> None:
        from brain.utils import extract_summary

        body = "word " * 200
        text = f"---\ntitle: X\n---\n\n{body}\n"
        result = extract_summary(text, max_words=50)
        assert len(result.split()) <= 51  # up to 50 words + "..."

    def test_skips_fenced_code(self) -> None:
        from brain.utils import extract_summary

        text = "---\ntitle: X\n---\n\n```python\nprint('skip')\n```\n\nReal summary here.\n"
        result = extract_summary(text)
        assert "Real summary" in result
        assert "print" not in result

    def test_empty_when_no_body(self) -> None:
        from brain.utils import extract_summary

        text = "---\ntitle: X\n---\n"
        assert extract_summary(text) == ""


# ---------------------------------------------------------------------------
# build_brain integration tests  (P2.8)
# ---------------------------------------------------------------------------


class TestBuildBrainIntegration:
    def test_returns_brain_data_from_fixture(self, tmp_path: Path) -> None:
        from brain import BrainData, build_brain

        (tmp_path / ".cg-docs" / "solutions" / "bugs").mkdir(parents=True)
        (tmp_path / ".cg-docs" / "solutions" / "bugs" / "fix.md").write_text(
            "---\ntitle: My Fix\ndate: 2026-05-01\nstatus: active\n---\n\nFixed the crash.\n",
            encoding="utf-8",
        )
        data = build_brain(root=tmp_path, generated="2026-05-01")
        assert isinstance(data, BrainData)
        assert len(data.entities) == 1
        assert data.entities[0].entity_type == "solution"
        assert len(data.entities[0].keywords) > 0
        assert data.generated == "2026-05-01"

    def test_empty_project_returns_empty_brain(self, tmp_path: Path) -> None:
        from brain import BrainData, build_brain

        data = build_brain(root=tmp_path)
        assert isinstance(data, BrainData)
        assert data.entities == []
        assert data.topics == []
        assert data.edges == []

    def test_generated_defaults_to_today(self, tmp_path: Path) -> None:
        import re

        from brain import build_brain

        data = build_brain(root=tmp_path)
        assert re.match(r"\d{4}-\d{2}-\d{2}$", data.generated), (
            f"generated should be an ISO date string, got {data.generated!r}"
        )


# ---------------------------------------------------------------------------
# New tests added by cg-review (P2.5, P2.14, P3.10)
# ---------------------------------------------------------------------------


class TestEntityTagsScalar:
    """P2.5 — scalar tag frontmatter value must return single-element list."""

    def test_tags_scalar_string_single_element_list(self) -> None:
        from brain import Entity

        e = Entity(
            path=Path("f.md"),
            entity_type="solution",
            frontmatter={"tags": "pester"},
        )
        assert e.tags == ["pester"]

    def test_tags_scalar_empty_string_returns_empty(self) -> None:
        from brain import Entity

        e = Entity(
            path=Path("f.md"),
            entity_type="solution",
            frontmatter={"tags": "   "},
        )
        assert e.tags == []


class TestBomPrefixHandling:
    """P2.14 — BOM prefix (\ufeff) in file should not break frontmatter parsing."""

    def test_bom_prefix_does_not_break_frontmatter(self, tmp_path: Path) -> None:
        from brain import build_brain

        content = "\ufeff---\ntitle: BOM Test\ndate: 2026-05-01\nstatus: active\n---\n\nBody.\n"
        p = tmp_path / ".cg-docs" / "plans" / "bom.md"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")

        data = build_brain(root=tmp_path)
        assert len(data.entities) == 1
        # BOM should not appear in the title
        assert "\ufeff" not in data.entities[0].title
