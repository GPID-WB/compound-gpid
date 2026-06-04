"""Tests for brain.scanner — entity discovery.

Run from repo root:
    python -m pytest scripts/brain/tests/test_scanner.py -v
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from brain.scanner import _DIR_TO_TYPE, scan_all, scan_roadmap


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write(path: Path, content: str) -> Path:
    """Create a file with content, creating parent directories as needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def _md(title: str = "Test", date: str = "2026-05-19", status: str = "active") -> str:
    return f"---\ntitle: {title}\ndate: {date}\nstatus: {status}\n---\n\nBody text here.\n"


# ---------------------------------------------------------------------------
# scan_all — entity type dispatch
# ---------------------------------------------------------------------------


class TestScanAllEntityTypes:
    def test_solutions_dir_maps_to_solution(self, tmp_path: Path) -> None:
        _write(tmp_path / ".cg-docs/solutions/bugs/foo.md", _md("Foo fix"))
        entities = scan_all(tmp_path)
        assert len(entities) == 1
        assert entities[0].entity_type == "solution"

    def test_plans_dir_maps_to_plan(self, tmp_path: Path) -> None:
        _write(tmp_path / ".cg-docs/plans/2026-05-19-my-plan.md", _md("My plan"))
        entities = scan_all(tmp_path)
        assert len(entities) == 1
        assert entities[0].entity_type == "plan"

    def test_brainstorms_dir_maps_to_brainstorm(self, tmp_path: Path) -> None:
        _write(tmp_path / ".cg-docs/brainstorms/2026-05-19-idea.md", _md("Idea"))
        entities = scan_all(tmp_path)
        assert len(entities) == 1
        assert entities[0].entity_type == "brainstorm"

    def test_reviews_dir_maps_to_review(self, tmp_path: Path) -> None:
        _write(tmp_path / ".cg-docs/reviews/2026-05-19-review.md", _md("Review"))
        entities = scan_all(tmp_path)
        assert len(entities) == 1
        assert entities[0].entity_type == "review"

    def test_competitive_reviews_dir_maps_to_review(self, tmp_path: Path) -> None:
        _write(
            tmp_path / ".cg-docs/competitive-reviews/2026-05-19-comp.md",
            _md("Comp review"),
        )
        entities = scan_all(tmp_path)
        assert len(entities) == 1
        assert entities[0].entity_type == "review"

    def test_strategy_dir_maps_to_strategy(self, tmp_path: Path) -> None:
        _write(tmp_path / ".cg-docs/strategy/2026-05-19-vision.md", _md("Vision"))
        entities = scan_all(tmp_path)
        assert len(entities) == 1
        assert entities[0].entity_type == "strategy"

    def test_archive_dir_is_skipped(self, tmp_path: Path) -> None:
        _write(tmp_path / ".cg-docs/archive/old.md", _md("Old doc"))
        entities = scan_all(tmp_path)
        assert entities == []

    def test_files_directly_in_cg_docs_are_skipped(self, tmp_path: Path) -> None:
        """DIGEST.md at the top level must be skipped (rel_parts length == 1)."""
        _write(tmp_path / ".cg-docs/DIGEST.md", "# Digest\n")
        entities = scan_all(tmp_path)
        assert entities == []

    def test_unknown_top_dir_is_skipped(self, tmp_path: Path) -> None:
        _write(tmp_path / ".cg-docs/misc/foo.md", _md())
        entities = scan_all(tmp_path)
        assert entities == []

    def test_unknown_top_dir_emits_warning(self, tmp_path: Path) -> None:
        import warnings as _w

        _write(tmp_path / ".cg-docs/misc/foo.md", _md())
        with _w.catch_warnings(record=True) as caught:
            _w.simplefilter("always")
            scan_all(tmp_path)
        assert any("Unknown .cg-docs/ subdirectory" in str(w.message) for w in caught)


class TestScanAllContent:
    def test_frontmatter_parsed(self, tmp_path: Path) -> None:
        _write(
            tmp_path / ".cg-docs/solutions/bugs/fix.md",
            "---\ntitle: My Fix\ndate: 2026-05-19\nstatus: active\n---\n\nDetails.\n",
        )
        e = scan_all(tmp_path)[0]
        assert e.frontmatter["title"] == "My Fix"
        assert e.frontmatter["date"] == "2026-05-19"
        assert e.frontmatter["status"] == "active"

    def test_summary_extracted(self, tmp_path: Path) -> None:
        _write(
            tmp_path / ".cg-docs/plans/plan.md",
            "---\ntitle: Plan\n---\n\nThis is the summary paragraph.\n",
        )
        e = scan_all(tmp_path)[0]
        assert "summary" in e.summary.lower() or e.summary != ""

    def test_raw_text_stored(self, tmp_path: Path) -> None:
        content = "---\ntitle: X\n---\n\nSome body.\n"
        _write(tmp_path / ".cg-docs/plans/p.md", content)
        e = scan_all(tmp_path)[0]
        assert e.text == content

    def test_path_is_relative(self, tmp_path: Path) -> None:
        _write(tmp_path / ".cg-docs/plans/p.md", _md())
        e = scan_all(tmp_path)[0]
        assert not e.path.is_absolute()
        assert str(e.path).replace("\\", "/") == ".cg-docs/plans/p.md"

    def test_null_frontmatter_values_coerced(self, tmp_path: Path) -> None:
        """brainstorm: null or ~ must parse to None, not a path string."""
        content = "---\ntitle: Plan\nbrainstorm: ~\nstatus: active\n---\n\nBody.\n"
        _write(tmp_path / ".cg-docs/plans/p.md", content)
        e = scan_all(tmp_path)[0]
        assert e.frontmatter.get("brainstorm") is None


class TestScanAllEdgeCases:
    def test_missing_cg_docs_returns_empty(self, tmp_path: Path) -> None:
        entities = scan_all(tmp_path)
        assert entities == []

    def test_empty_cg_docs_returns_empty(self, tmp_path: Path) -> None:
        (tmp_path / ".cg-docs").mkdir()
        entities = scan_all(tmp_path)
        assert entities == []

    def test_multiple_files_across_dirs(self, tmp_path: Path) -> None:
        _write(tmp_path / ".cg-docs/solutions/bugs/a.md", _md("A"))
        _write(tmp_path / ".cg-docs/plans/b.md", _md("B"))
        _write(tmp_path / ".cg-docs/brainstorms/c.md", _md("C"))
        entities = scan_all(tmp_path)
        assert len(entities) == 3

    def test_sorted_by_path(self, tmp_path: Path) -> None:
        """Results must be sorted (deterministic ordering)."""
        _write(tmp_path / ".cg-docs/plans/z.md", _md("Z"))
        _write(tmp_path / ".cg-docs/plans/a.md", _md("A"))
        entities = scan_all(tmp_path)
        paths = [e.path for e in entities]
        assert paths == sorted(paths)


# ---------------------------------------------------------------------------
# scan_roadmap — feature discovery
# ---------------------------------------------------------------------------

_SIMPLE_ROADMAP = {
    "schemaVersion": "compound-gpid-roadmap-v1",
    "milestones": [
        {
            "id": "test-milestone",
            "title": "Test Milestone",
            "objective": "Achieve something useful.",
            "status": "active",
            "features": [
                {
                    "id": "feature-alpha",
                    "title": "Feature Alpha",
                    "status": "in-progress",
                    "plan": ".cg-docs/plans/alpha.md",
                },
                {
                    "id": "feature-beta",
                    "title": "Feature Beta",
                    "status": "done",
                },
            ],
        }
    ],
}


class TestScanRoadmap:
    def _write_roadmap(self, root: Path, data: dict) -> None:
        (root / "roadmap.json").write_text(
            json.dumps(data), encoding="utf-8"
        )

    def test_returns_empty_when_no_roadmap(self, tmp_path: Path) -> None:
        assert scan_roadmap(tmp_path) == []

    def test_one_entity_per_feature(self, tmp_path: Path) -> None:
        self._write_roadmap(tmp_path, _SIMPLE_ROADMAP)
        entities = scan_roadmap(tmp_path)
        assert len(entities) == 2

    def test_entity_type_is_feature(self, tmp_path: Path) -> None:
        self._write_roadmap(tmp_path, _SIMPLE_ROADMAP)
        for e in scan_roadmap(tmp_path):
            assert e.entity_type == "feature"

    def test_virtual_path_contains_feature_id(self, tmp_path: Path) -> None:
        self._write_roadmap(tmp_path, _SIMPLE_ROADMAP)
        slugs = {e.slug for e in scan_roadmap(tmp_path)}
        assert "feature-alpha" in slugs
        assert "feature-beta" in slugs

    def test_frontmatter_populated(self, tmp_path: Path) -> None:
        self._write_roadmap(tmp_path, _SIMPLE_ROADMAP)
        entities = {e.slug: e for e in scan_roadmap(tmp_path)}

        alpha = entities["feature-alpha"]
        assert alpha.frontmatter["id"] == "feature-alpha"
        assert alpha.frontmatter["title"] == "Feature Alpha"
        assert alpha.frontmatter["status"] == "in-progress"
        assert alpha.frontmatter["milestone"] == "Test Milestone"
        assert alpha.frontmatter["plan"] == ".cg-docs/plans/alpha.md"

    def test_frontmatter_plan_none_when_absent(self, tmp_path: Path) -> None:
        self._write_roadmap(tmp_path, _SIMPLE_ROADMAP)
        entities = {e.slug: e for e in scan_roadmap(tmp_path)}
        beta = entities["feature-beta"]
        assert beta.frontmatter["plan"] is None

    def test_summary_is_feature_title(self, tmp_path: Path) -> None:
        self._write_roadmap(tmp_path, _SIMPLE_ROADMAP)
        entities = {e.slug: e for e in scan_roadmap(tmp_path)}
        assert entities["feature-alpha"].summary == "Feature Alpha"

    def test_text_includes_milestone_and_objective(self, tmp_path: Path) -> None:
        self._write_roadmap(tmp_path, _SIMPLE_ROADMAP)
        entities = {e.slug: e for e in scan_roadmap(tmp_path)}
        text = entities["feature-alpha"].text
        assert "Test Milestone" in text
        assert "Achieve something useful" in text

    def test_malformed_roadmap_returns_empty(self, tmp_path: Path) -> None:
        (tmp_path / "roadmap.json").write_text("not valid json", encoding="utf-8")
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            result = scan_roadmap(tmp_path)
        assert result == []

    def test_feature_without_id_is_skipped(self, tmp_path: Path) -> None:
        data = {
            "milestones": [
                {
                    "id": "m",
                    "title": "M",
                    "features": [
                        {"title": "No ID feature"},  # missing "id"
                        {"id": "valid-feature", "title": "Valid"},
                    ],
                }
            ]
        }
        self._write_roadmap(tmp_path, data)
        entities = scan_roadmap(tmp_path)
        assert len(entities) == 1
        assert entities[0].slug == "valid-feature"


# ---------------------------------------------------------------------------
# _DIR_TO_TYPE coverage check
# ---------------------------------------------------------------------------


class TestDirToTypeMapping:
    def test_archive_maps_to_none(self) -> None:
        assert _DIR_TO_TYPE["archive"] is None

    def test_known_types_present(self) -> None:
        for dir_name in ("solutions", "plans", "brainstorms", "reviews", "strategy"):
            assert dir_name in _DIR_TO_TYPE
            assert _DIR_TO_TYPE[dir_name] is not None


# ---------------------------------------------------------------------------
# New tests added by cg-review (P2.13 — unreadable file emits warning)
# ---------------------------------------------------------------------------


class TestScanAllUnreadable:
    def test_unreadable_file_skipped_with_warning(self, tmp_path: Path) -> None:
        """P2.13 — permission-denied file should warn and continue scanning."""
        import stat
        import sys
        import warnings

        _write(tmp_path / ".cg-docs/plans/good.md", _md("Good"))
        bad = _write(tmp_path / ".cg-docs/plans/bad.md", _md("Bad"))

        if sys.platform == "win32":
            pytest.skip("chmod mode tests not reliable on Windows CI")

        bad.chmod(stat.S_IWUSR)  # write-only: unreadable
        try:
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                entities = scan_all(tmp_path)
            slugs = [e.slug for e in entities]
            assert "good" in slugs
            assert "bad" not in slugs
            assert any("Could not read" in str(w.message) for w in caught)
        finally:
            bad.chmod(stat.S_IRUSR | stat.S_IWUSR)
