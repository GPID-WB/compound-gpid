"""Tests for team_brain.schema — schema validation and JSONL parsing.

Run from repo root:
    python -m pytest scripts/team_brain/tests/test_schema.py -v
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from team_brain.schema import (
    PatternEntry,
    TeamBrainConfig,
    _parse_team_brain_yml,
    load_patterns_from_jsonl,
    parse_pattern_jsonl_line,
    validate_team_brain_yml,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _minimal_yml_data() -> dict:
    return {
        "schema-version": "1.0",
        "manager": "wb384996",
        "contributors": [{"org": "GPID-WB"}],
    }


def _minimal_jsonl_line() -> str:
    return json.dumps(
        {
            "id": "2026-05-20-pester-safety",
            "date": "2026-05-20",
            "source-project": "compound-gpid",
            "topic": "PowerShell testing",
            "tags": ["pester", "powershell"],
            "pattern": "Use -Quiet with Pester 4.",
            "entry-path": "entries/compound-gpid/2026-05-20-pester-safety.md",
            "confidence": 1.0,
            "superseded-by": None,
        }
    )


# ---------------------------------------------------------------------------
# validate_team_brain_yml — happy path
# ---------------------------------------------------------------------------


def test_validate_minimal_yml():
    config = validate_team_brain_yml(_minimal_yml_data())
    assert isinstance(config, TeamBrainConfig)
    assert config.manager == "wb384996"
    assert config.contributors == [{"org": "GPID-WB"}]
    assert config.curation_schedule == "weekly"
    assert config.auto_supersede is False


def test_validate_yml_with_team_contributor():
    data = _minimal_yml_data()
    data["contributors"] = [{"team": "GPID-WB/core-devs"}]
    config = validate_team_brain_yml(data)
    assert config.contributors == [{"team": "GPID-WB/core-devs"}]


def test_validate_yml_auto_supersede_true():
    data = _minimal_yml_data()
    data["curation"] = {"schedule": "daily", "auto-supersede": "true"}
    config = validate_team_brain_yml(data)
    assert config.auto_supersede is True
    assert config.curation_schedule == "daily"


def test_validate_yml_internal_url_patterns():
    data = _minimal_yml_data()
    data["internal-url-patterns"] = ["*.worldbank.org", "internal.wb.lan"]
    config = validate_team_brain_yml(data)
    assert "*.worldbank.org" in config.internal_url_patterns


# ---------------------------------------------------------------------------
# validate_team_brain_yml — error paths
# ---------------------------------------------------------------------------


def test_validate_yml_missing_manager():
    data = _minimal_yml_data()
    del data["manager"]
    with pytest.raises(ValueError, match="missing required field.*manager"):
        validate_team_brain_yml(data)


def test_validate_yml_missing_contributors():
    data = _minimal_yml_data()
    del data["contributors"]
    with pytest.raises(ValueError, match="missing required field.*contributors"):
        validate_team_brain_yml(data)


def test_validate_yml_empty_contributors():
    data = _minimal_yml_data()
    data["contributors"] = []
    with pytest.raises(ValueError, match="non-empty list"):
        validate_team_brain_yml(data)


def test_validate_yml_missing_schema_version():
    data = _minimal_yml_data()
    del data["schema-version"]
    with pytest.raises(ValueError, match="missing required field.*schema-version"):
        validate_team_brain_yml(data)


def test_validate_yml_empty_manager():
    data = _minimal_yml_data()
    data["manager"] = ""
    with pytest.raises(ValueError, match="non-empty GitHub username"):
        validate_team_brain_yml(data)


# ---------------------------------------------------------------------------
# parse_pattern_jsonl_line — happy path
# ---------------------------------------------------------------------------


def test_parse_jsonl_line_minimal():
    entry = parse_pattern_jsonl_line(_minimal_jsonl_line())
    assert entry.id == "2026-05-20-pester-safety"
    assert entry.source_project == "compound-gpid"
    assert entry.confidence == 1.0
    assert entry.superseded_by is None


def test_parse_jsonl_line_superseded():
    data = json.loads(_minimal_jsonl_line())
    data["superseded-by"] = "2026-06-01-pester-safety-v2"
    entry = parse_pattern_jsonl_line(json.dumps(data))
    assert entry.superseded_by == "2026-06-01-pester-safety-v2"


def test_pattern_entry_roundtrip():
    line = _minimal_jsonl_line()
    entry = parse_pattern_jsonl_line(line)
    re_serialized = entry.to_jsonl_line()
    re_parsed = parse_pattern_jsonl_line(re_serialized)
    assert re_parsed.id == entry.id
    assert re_parsed.pattern == entry.pattern


# ---------------------------------------------------------------------------
# parse_pattern_jsonl_line — error paths
# ---------------------------------------------------------------------------


def test_parse_jsonl_invalid_json():
    with pytest.raises(ValueError, match="not valid JSON"):
        parse_pattern_jsonl_line("{ not json }")


def test_parse_jsonl_missing_required_field():
    data = json.loads(_minimal_jsonl_line())
    del data["pattern"]
    with pytest.raises(ValueError, match="missing required fields.*pattern"):
        parse_pattern_jsonl_line(json.dumps(data))


# ---------------------------------------------------------------------------
# load_patterns_from_jsonl
# ---------------------------------------------------------------------------


def test_load_patterns_from_jsonl(tmp_path):
    jsonl_file = tmp_path / "compound-gpid.jsonl"
    jsonl_file.write_text(
        _minimal_jsonl_line() + "\n# comment\n\n",
        encoding="utf-8",
    )
    entries = load_patterns_from_jsonl(jsonl_file)
    assert len(entries) == 1
    assert entries[0].source_project == "compound-gpid"


def test_load_patterns_skips_malformed_with_warning(tmp_path):
    jsonl_file = tmp_path / "compound-gpid.jsonl"
    jsonl_file.write_text(
        _minimal_jsonl_line() + "\n{bad json}\n",
        encoding="utf-8",
    )
    with pytest.warns(UserWarning, match="malformed"):
        entries = load_patterns_from_jsonl(jsonl_file)
    assert len(entries) == 1  # malformed line skipped


def test_load_patterns_file_not_found(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_patterns_from_jsonl(tmp_path / "nonexistent.jsonl")


# ---------------------------------------------------------------------------
# New tests added by cg-review findings
# ---------------------------------------------------------------------------


def test_parse_jsonl_tags_string_raises():
    """P0.2 — tags as string (not array) must raise, not silently explode."""
    data = json.loads(_minimal_jsonl_line())
    data["tags"] = "pester"  # string instead of list
    with pytest.raises(ValueError, match="tags.*JSON array"):
        parse_pattern_jsonl_line(json.dumps(data))


def test_parse_jsonl_confidence_negative_raises():
    """P1.1 — negative confidence must raise ValueError."""
    data = json.loads(_minimal_jsonl_line())
    data["confidence"] = -0.5
    with pytest.raises(ValueError, match="confidence"):
        parse_pattern_jsonl_line(json.dumps(data))


def test_parse_jsonl_confidence_above_max_raises():
    """P2.2 verify — confidence above 2.0 must raise ValueError."""
    data = json.loads(_minimal_jsonl_line())
    data["confidence"] = 2.5
    with pytest.raises(ValueError, match="confidence"):
        parse_pattern_jsonl_line(json.dumps(data))


def test_parse_jsonl_date_non_iso_raises():
    """P1.2 — non-ISO date must raise ValueError."""
    data = json.loads(_minimal_jsonl_line())
    data["date"] = "May 2026"
    with pytest.raises(ValueError, match="date.*YYYY-MM-DD"):
        parse_pattern_jsonl_line(json.dumps(data))


def test_parse_jsonl_entry_path_traversal_raises():
    """P1.9 — path traversal in entry-path must raise ValueError."""
    data = json.loads(_minimal_jsonl_line())
    data["entry-path"] = "../../etc/shadow"
    with pytest.raises(ValueError, match="relative path"):
        parse_pattern_jsonl_line(json.dumps(data))


def test_parse_jsonl_empty_id_raises():
    """P2.7 — empty id must raise ValueError."""
    data = json.loads(_minimal_jsonl_line())
    data["id"] = ""
    with pytest.raises(ValueError, match="id.*non-empty"):
        parse_pattern_jsonl_line(json.dumps(data))


def test_pattern_entry_roundtrip_with_superseded_by():
    """P3.9 — superseded-by field name mapping must survive roundtrip."""
    data = json.loads(_minimal_jsonl_line())
    data["superseded-by"] = "2026-06-01-pester-safety-v2"
    entry = parse_pattern_jsonl_line(json.dumps(data))
    re_parsed = parse_pattern_jsonl_line(entry.to_jsonl_line())
    assert re_parsed.superseded_by == "2026-06-01-pester-safety-v2"


def test_validate_yml_invalid_schedule_raises():
    """P1.8 — invalid curation schedule must raise ValueError."""
    data = _minimal_yml_data()
    data["curation"] = {"schedule": "biweekly", "auto-supersede": "false"}
    with pytest.raises(ValueError, match="curation.schedule"):
        validate_team_brain_yml(data)


def test_load_patterns_comment_only_file(tmp_path):
    """P3.4 — comment-only file should return empty list with no warnings."""
    f = tmp_path / "x.jsonl"
    f.write_text("# just comments\n# nothing here\n", encoding="utf-8")
    entries = load_patterns_from_jsonl(f)
    assert entries == []
