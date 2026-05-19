"""Tests for brain.renderer module."""
from __future__ import annotations

import json
import warnings
from pathlib import Path

import pytest

from brain import BrainData, Edge, Entity, Topic
from brain.renderer import (
    _anchor,
    _build_topic_file_map,
    _entity_line,
    _estimate_tokens,
    render_brain,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_entity(
    path: str = ".cg-docs/solutions/2026-01-15-fix-thing.md",
    entity_type: str = "solution",
    title: str = "Fix Thing",
    summary: str = "Short summary.",
    date: str = "2026-01-15",
    status: str = "active",
    tags: list | None = None,
    keywords: list | None = None,
) -> Entity:
    return Entity(
        path=Path(path),
        entity_type=entity_type,
        frontmatter={
            "title": title,
            "date": date,
            "status": status,
            "tags": tags or [],
        },
        summary=summary,
        text="",
        keywords=keywords or [("fix", 2.0), ("thing", 1.5)],
    )


def _make_topic(
    slug: str = "fix-repair",
    label: str = "Fix / Repair",
    keywords: list | None = None,
    paths: list | None = None,
) -> Topic:
    return Topic(
        slug=slug,
        label=label,
        keywords=keywords or ["fix", "repair"],
        entity_paths=[Path(p) for p in (paths or [".cg-docs/solutions/2026-01-15-fix-thing.md"])],
    )


def _make_minimal_brain(
    n_entities: int = 1,
    n_topics: int = 1,
    n_edges: int = 0,
) -> BrainData:
    entity_path = ".cg-docs/solutions/2026-01-15-fix-thing.md"
    entities = [_make_entity(path=entity_path)]
    for i in range(1, n_entities):
        entities.append(_make_entity(
            path=f".cg-docs/solutions/2026-01-{15 + i:02d}-fix-{i}.md",
            title=f"Fix Thing {i}",
            date=f"2026-01-{15 + i:02d}",
        ))

    topics = []
    for j in range(n_topics):
        topics.append(Topic(
            slug=f"topic-{j}",
            label=f"Topic {j}",
            keywords=["key", str(j)],
            entity_paths=[entities[j % len(entities)].path],
        ))

    edges = []
    for k in range(n_edges):
        edges.append(Edge(
            source=entities[0].path,
            target=entities[k % len(entities)].path,
            edge_type="references",
        ))

    return BrainData(entities=entities, topics=topics, edges=edges, generated="2026-01-15")


# ---------------------------------------------------------------------------
# _estimate_tokens
# ---------------------------------------------------------------------------


class TestEstimateTokens:
    def test_empty_string_returns_one(self):
        # Empty string: 0 words * 1.6 + 1 = 1
        assert _estimate_tokens("") == 1

    def test_single_word(self):
        # 1 word * 1.6 = 1.6, int() = 1, +1 = 2
        assert _estimate_tokens("hello") == 2

    def test_ten_words(self):
        text = "one two three four five six seven eight nine ten"
        # 10 * 1.6 = 16, +1 = 17
        assert _estimate_tokens(text) == 17

    def test_scales_with_word_count(self):
        short = "hello world"          # 2 words
        long_text = ("hello world " * 10).strip()  # 20 words
        assert _estimate_tokens(long_text) > _estimate_tokens(short) * 4

    def test_returns_int(self):
        result = _estimate_tokens("some text here")
        assert isinstance(result, int)


# ---------------------------------------------------------------------------
# _anchor
# ---------------------------------------------------------------------------


class TestAnchor:
    def test_lowercase(self):
        assert _anchor("Topic Label") == "topic-label"

    def test_special_chars_replaced(self):
        # The regex collapses runs of non-alnum chars into a single "-"
        # so " / " (space-slash-space) becomes a single "-"
        result = _anchor("Fix / Repair")
        assert result.startswith("fix")
        assert result.endswith("repair")
        assert "fix" in result and "repair" in result

    def test_numbers_preserved(self):
        assert _anchor("Phase 2") == "phase-2"

    def test_consecutive_separators_stripped(self):
        result = _anchor("A / B")
        assert "a" in result
        assert "b" in result

    def test_already_slug(self):
        assert _anchor("my-topic") == "my-topic"


# ---------------------------------------------------------------------------
# _entity_line
# ---------------------------------------------------------------------------


class TestEntityLine:
    def test_contains_title(self):
        entity = _make_entity(title="My Fix")
        line = _entity_line(entity)
        assert "My Fix" in line

    def test_contains_entity_type(self):
        entity = _make_entity(entity_type="plan")
        line = _entity_line(entity)
        assert "`plan`" in line

    def test_contains_status(self):
        entity = _make_entity(status="done")
        line = _entity_line(entity)
        assert "_done_" in line

    def test_contains_date(self):
        entity = _make_entity(date="2026-05-01")
        line = _entity_line(entity)
        assert "2026-05-01" in line

    def test_contains_summary(self):
        entity = _make_entity(summary="Quick fix for crash bug.")
        line = _entity_line(entity)
        assert "Quick fix for crash bug." in line

    def test_long_summary_truncated(self):
        entity = _make_entity(summary="A" * 200)
        line = _entity_line(entity)
        # Should be truncated to ~120 chars + ellipsis
        assert "…" in line

    def test_no_summary_no_blockquote(self):
        entity = _make_entity(summary="")
        line = _entity_line(entity)
        assert ">" not in line

    def test_path_uses_forward_slashes(self):
        entity = _make_entity(path=r".cg-docs\solutions\fix.md")
        line = _entity_line(entity)
        # Forward slashes in markdown links
        assert "\\" not in line

    def test_starts_with_list_marker(self):
        entity = _make_entity()
        line = _entity_line(entity)
        assert line.startswith("- ")

    def test_missing_date_shows_dash(self):
        entity = Entity(
            path=Path(".cg-docs/solutions/nodate.md"),
            entity_type="solution",
            frontmatter={"title": "No Date"},
            summary="",
        )
        line = _entity_line(entity)
        assert "—" in line


# ---------------------------------------------------------------------------
# render_brain: output file creation
# ---------------------------------------------------------------------------


class TestRenderBrainOutputFiles:
    def test_always_creates_brain_md(self, tmp_path):
        data = _make_minimal_brain()
        written = render_brain(data, out_dir=tmp_path)
        names = {p.name for p in written}
        assert "BRAIN.md" in names

    def test_always_creates_brain_log(self, tmp_path):
        data = _make_minimal_brain()
        written = render_brain(data, out_dir=tmp_path)
        names = {p.name for p in written}
        assert "BRAIN-log.md" in names

    def test_always_creates_brain_json(self, tmp_path):
        data = _make_minimal_brain()
        written = render_brain(data, out_dir=tmp_path)
        names = {p.name for p in written}
        assert "brain-index.json" in names

    def test_creates_brain_01_md_when_topics_exist(self, tmp_path):
        data = _make_minimal_brain(n_topics=1)
        written = render_brain(data, out_dir=tmp_path)
        names = {p.name for p in written}
        assert "BRAIN-01.md" in names

    def test_no_topic_files_when_no_topics(self, tmp_path):
        data = BrainData(
            entities=[_make_entity()],
            topics=[],
            edges=[],
            generated="2026-01-15",
        )
        written = render_brain(data, out_dir=tmp_path)
        names = {p.name for p in written}
        brain_nn = [n for n in names if n.startswith("BRAIN-") and n.endswith(".md") and n != "BRAIN-log.md"]
        assert brain_nn == []

    def test_returns_list_of_paths(self, tmp_path):
        data = _make_minimal_brain()
        result = render_brain(data, out_dir=tmp_path)
        assert isinstance(result, list)
        assert all(isinstance(p, Path) for p in result)

    def test_all_returned_files_exist(self, tmp_path):
        data = _make_minimal_brain(n_entities=3, n_topics=2)
        written = render_brain(data, out_dir=tmp_path)
        for p in written:
            assert p.exists(), f"Expected file not found: {p}"

    def test_creates_out_dir_if_missing(self, tmp_path):
        nested = tmp_path / "deep" / "nested"
        data = _make_minimal_brain()
        render_brain(data, out_dir=nested)
        assert nested.exists()

    def test_does_not_delete_legacy_digest(self, tmp_path):
        legacy = tmp_path / "DIGEST.md"
        legacy.write_text("# Old Digest")
        data = _make_minimal_brain()
        render_brain(data, out_dir=tmp_path)
        assert legacy.exists(), "renderer must not delete DIGEST.md"

    def test_does_not_delete_legacy_search_index(self, tmp_path):
        legacy = tmp_path / "search-index.json"
        legacy.write_text("{}")
        data = _make_minimal_brain()
        render_brain(data, out_dir=tmp_path)
        assert legacy.exists(), "renderer must not delete search-index.json"


# ---------------------------------------------------------------------------
# render_brain: BRAIN.md content
# ---------------------------------------------------------------------------


class TestBrainMdContent:
    def test_contains_generated_date(self, tmp_path):
        data = _make_minimal_brain()
        render_brain(data, out_dir=tmp_path)
        content = (tmp_path / "BRAIN.md").read_text(encoding="utf-8")
        assert "2026-01-15" in content

    def test_contains_entity_count(self, tmp_path):
        data = _make_minimal_brain(n_entities=3)
        render_brain(data, out_dir=tmp_path)
        content = (tmp_path / "BRAIN.md").read_text(encoding="utf-8")
        assert "3 entities" in content

    def test_contains_topic_label(self, tmp_path):
        data = _make_minimal_brain(n_topics=1)
        render_brain(data, out_dir=tmp_path)
        content = (tmp_path / "BRAIN.md").read_text(encoding="utf-8")
        assert "Topic 0" in content

    def test_contains_edge_section_when_edges_exist(self, tmp_path):
        data = _make_minimal_brain(n_entities=2, n_edges=1)
        render_brain(data, out_dir=tmp_path)
        content = (tmp_path / "BRAIN.md").read_text(encoding="utf-8")
        assert "Relationship Summary" in content

    def test_no_edge_section_when_no_edges(self, tmp_path):
        data = _make_minimal_brain(n_edges=0)
        render_brain(data, out_dir=tmp_path)
        content = (tmp_path / "BRAIN.md").read_text(encoding="utf-8")
        assert "Relationship Summary" not in content

    def test_links_to_brain_log(self, tmp_path):
        data = _make_minimal_brain()
        render_brain(data, out_dir=tmp_path)
        content = (tmp_path / "BRAIN.md").read_text(encoding="utf-8")
        assert "BRAIN-log.md" in content

    def test_links_to_brain_index_json(self, tmp_path):
        data = _make_minimal_brain()
        render_brain(data, out_dir=tmp_path)
        content = (tmp_path / "BRAIN.md").read_text(encoding="utf-8")
        assert "brain-index.json" in content


# ---------------------------------------------------------------------------
# render_brain: brain-index.json content
# ---------------------------------------------------------------------------


class TestBrainJsonContent:
    def _load_json(self, tmp_path: Path) -> dict:
        return json.loads((tmp_path / "brain-index.json").read_text(encoding="utf-8"))

    def test_valid_json(self, tmp_path):
        data = _make_minimal_brain()
        render_brain(data, out_dir=tmp_path)
        payload = self._load_json(tmp_path)
        assert isinstance(payload, dict)

    def test_has_schema_version(self, tmp_path):
        data = _make_minimal_brain()
        render_brain(data, out_dir=tmp_path)
        payload = self._load_json(tmp_path)
        assert payload["schema_version"] == "0.2.0"

    def test_entity_count_matches(self, tmp_path):
        data = _make_minimal_brain(n_entities=3)
        render_brain(data, out_dir=tmp_path)
        payload = self._load_json(tmp_path)
        assert payload["entity_count"] == 3
        assert len(payload["entities"]) == 3

    def test_topic_count_matches(self, tmp_path):
        data = _make_minimal_brain(n_topics=2)
        render_brain(data, out_dir=tmp_path)
        payload = self._load_json(tmp_path)
        assert payload["topic_count"] == 2
        assert len(payload["topics"]) == 2

    def test_edge_count_matches(self, tmp_path):
        data = _make_minimal_brain(n_entities=2, n_edges=1)
        render_brain(data, out_dir=tmp_path)
        payload = self._load_json(tmp_path)
        assert payload["edge_count"] == 1
        assert len(payload["edges"]) == 1

    def test_entity_has_required_fields(self, tmp_path):
        data = _make_minimal_brain()
        render_brain(data, out_dir=tmp_path)
        payload = self._load_json(tmp_path)
        entity = payload["entities"][0]
        for field in ("path", "entity_type", "slug", "title", "date", "status", "tags", "summary", "top_keywords"):
            assert field in entity, f"Missing field: {field}"

    def test_entity_path_uses_forward_slashes(self, tmp_path):
        data = _make_minimal_brain()
        render_brain(data, out_dir=tmp_path)
        payload = self._load_json(tmp_path)
        for entity in payload["entities"]:
            assert "\\" not in entity["path"]

    def test_edge_has_required_fields(self, tmp_path):
        data = _make_minimal_brain(n_entities=2, n_edges=1)
        render_brain(data, out_dir=tmp_path)
        payload = self._load_json(tmp_path)
        edge = payload["edges"][0]
        for field in ("source", "target", "edge_type", "target_missing"):
            assert field in edge, f"Missing edge field: {field}"

    def test_generated_field_present(self, tmp_path):
        data = _make_minimal_brain()
        render_brain(data, out_dir=tmp_path)
        payload = self._load_json(tmp_path)
        assert payload["generated"] == "2026-01-15"


# ---------------------------------------------------------------------------
# render_brain: BRAIN-log.md content
# ---------------------------------------------------------------------------


class TestBrainLogContent:
    def test_contains_entity_title(self, tmp_path):
        data = _make_minimal_brain()
        render_brain(data, out_dir=tmp_path)
        content = (tmp_path / "BRAIN-log.md").read_text(encoding="utf-8")
        assert "Fix Thing" in content

    def test_contains_generated_date(self, tmp_path):
        data = _make_minimal_brain()
        render_brain(data, out_dir=tmp_path)
        content = (tmp_path / "BRAIN-log.md").read_text(encoding="utf-8")
        assert "2026-01-15" in content

    def test_features_grouped_at_end(self, tmp_path):
        feature = Entity(
            path=Path("roadmap.json#my-feature"),
            entity_type="feature",
            frontmatter={"title": "My Feature", "status": "active"},
            summary="A roadmap feature.",
        )
        non_feature = _make_entity(title="Normal Entity")
        data = BrainData(
            entities=[non_feature, feature],
            topics=[],
            edges=[],
            generated="2026-01-15",
        )
        render_brain(data, out_dir=tmp_path)
        content = (tmp_path / "BRAIN-log.md").read_text(encoding="utf-8")
        # Roadmap Features section should appear after the date-sorted section
        normal_pos = content.index("Normal Entity")
        feature_section_pos = content.index("Roadmap Features")
        assert feature_section_pos > normal_pos

    def test_entities_sorted_newest_first(self, tmp_path):
        older = _make_entity(
            path=".cg-docs/solutions/2025-01-01-old.md",
            title="Old Entity",
            date="2025-01-01",
        )
        newer = _make_entity(
            path=".cg-docs/solutions/2026-01-15-new.md",
            title="New Entity",
            date="2026-01-15",
        )
        data = BrainData(
            entities=[older, newer],
            topics=[],
            edges=[],
            generated="2026-01-15",
        )
        render_brain(data, out_dir=tmp_path)
        content = (tmp_path / "BRAIN-log.md").read_text(encoding="utf-8")
        old_pos = content.index("Old Entity")
        new_pos = content.index("New Entity")
        assert new_pos < old_pos


# ---------------------------------------------------------------------------
# render_brain: token cap + multi-file splitting
# ---------------------------------------------------------------------------


class TestTokenCapSplitting:
    def test_single_file_when_under_cap(self, tmp_path):
        data = _make_minimal_brain(n_topics=2)
        written = render_brain(data, out_dir=tmp_path, token_cap=20_000)
        brain_nn = [p for p in written if p.name.startswith("BRAIN-") and p.name.endswith(".md") and p.name != "BRAIN-log.md"]
        assert len(brain_nn) == 1

    def test_multiple_files_when_over_cap(self, tmp_path):
        # Create many topics with many entities to force splitting
        entities = [
            _make_entity(
                path=f".cg-docs/solutions/2026-01-{i+1:02d}-entity-{i}.md",
                title=f"Entity {i} " + "word " * 50,  # inflate word count
                summary="summary word " * 30,
                date=f"2026-01-{i+1:02d}",
            )
            for i in range(20)
        ]
        topics = [
            Topic(
                slug=f"topic-{j}",
                label=f"Topic {j} " + "label word " * 5,
                keywords=[f"key{j}", f"word{j}"],
                entity_paths=[entities[j].path],
            )
            for j in range(10)
        ]
        data = BrainData(
            entities=entities, topics=topics, edges=[], generated="2026-01-15"
        )
        # Very small cap to force splitting
        written = render_brain(data, out_dir=tmp_path, token_cap=50)
        brain_nn = [p for p in written if p.name.startswith("BRAIN-") and p.name.endswith(".md") and p.name != "BRAIN-log.md"]
        assert len(brain_nn) > 1

    def test_overflow_warning_emitted(self, tmp_path):
        # Summaries are truncated to 120 chars in entity lines, so use a very
        # long title (not truncated) to produce a large entity line.
        long_title = "word " * 60  # ~60 words in the title alone
        entity = _make_entity(title=long_title, summary="")
        topic = Topic(
            slug="big-topic",
            label="Big Topic",
            keywords=["word"],
            entity_paths=[entity.path],
        )
        data = BrainData(entities=[entity], topics=[topic], edges=[], generated="2026-01-15")
        # Entity line: ~65 words → ~104 tokens; topic section: ~80 words → ~128 tokens
        # token_cap=50 → file exceeds 50 × 1.1 = 55 → warning fires
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            render_brain(data, out_dir=tmp_path, token_cap=50)
        overflow_warnings = [w for w in caught if "estimated tokens" in str(w.message)]
        assert len(overflow_warnings) > 0


# ---------------------------------------------------------------------------
# _build_topic_file_map
# ---------------------------------------------------------------------------


class TestBuildTopicFileMap:
    def test_empty_topics_returns_empty(self):
        result = _build_topic_file_map([], [])
        assert result == {}

    def test_single_topic_maps_to_first_file(self):
        topic = _make_topic(slug="my-topic")
        files = [Path("out/BRAIN-01.md")]
        result = _build_topic_file_map([topic], files)
        assert result["my-topic"] == "BRAIN-01.md"

    def test_all_topics_assigned(self):
        topics = [_make_topic(slug=f"topic-{i}") for i in range(4)]
        files = [Path(f"out/BRAIN-0{i+1}.md") for i in range(2)]
        result = _build_topic_file_map(topics, files)
        assert len(result) == 4
        for slug in result:
            assert result[slug] in {"BRAIN-01.md", "BRAIN-02.md"}

    def test_no_files_returns_empty(self):
        topics = [_make_topic()]
        result = _build_topic_file_map(topics, [])
        assert result == {}
