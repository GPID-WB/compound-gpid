"""Tests for team_brain.config — load team brain config from local.md.

Run from repo root:
    python -m pytest scripts/team_brain/tests/test_config.py -v
"""
from __future__ import annotations

from pathlib import Path

import pytest

from team_brain.config import (
    TeamBrainLocalConfig,
    _find_local_config,
    _parse_markdown_body_key_block,
    load_team_brain_local_config,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_MINIMAL_LOCAL_MD = """\
---
language: "both"
project-type: "tool"
---
# Config

## Team Brain

team-brain:
  repo: "GPID-WB/team-brain"
  project-name: "compound-gpid"
  enabled: true
  llm-filter: true
"""

_DISABLED_LOCAL_MD = """\
---
language: "both"
---
team-brain:
  repo: "GPID-WB/team-brain"
  project-name: "compound-gpid"
  enabled: false
"""

_MISSING_REPO_MD = """\
---
language: "both"
---
team-brain:
  project-name: "compound-gpid"
  enabled: true
"""

_NO_TEAM_BRAIN_MD = """\
---
language: "both"
project-type: "tool"
---
# Config
"""


def _write(tmp_path: Path, content: str) -> Path:
    p = tmp_path / "compound-gpid.local.md"
    p.write_text(content, encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# _parse_markdown_body_key_block
# ---------------------------------------------------------------------------


def test_body_block_parsed_correctly():
    result = _parse_markdown_body_key_block(_MINIMAL_LOCAL_MD, "team-brain")
    assert result["repo"] == "GPID-WB/team-brain"
    assert result["project-name"] == "compound-gpid"
    assert result["enabled"] is True
    assert result["llm-filter"] is True


def test_body_block_missing_key_returns_empty():
    result = _parse_markdown_body_key_block("# Some markdown\nNo block here.", "team-brain")
    assert result == {}


# ---------------------------------------------------------------------------
# load_team_brain_local_config — happy path
# ---------------------------------------------------------------------------


def test_load_minimal_config(tmp_path):
    p = _write(tmp_path, _MINIMAL_LOCAL_MD)
    config = load_team_brain_local_config(p)
    assert config is not None
    assert isinstance(config, TeamBrainLocalConfig)
    assert config.repo == "GPID-WB/team-brain"
    assert config.project_name == "compound-gpid"
    assert config.enabled is True
    assert config.llm_filter is True


def test_load_config_llm_filter_false(tmp_path):
    content = _MINIMAL_LOCAL_MD.replace("llm-filter: true", "llm-filter: false")
    p = _write(tmp_path, content)
    config = load_team_brain_local_config(p)
    assert config is not None
    assert config.llm_filter is False


def test_repo_owner_and_name(tmp_path):
    p = _write(tmp_path, _MINIMAL_LOCAL_MD)
    config = load_team_brain_local_config(p)
    assert config.repo_owner() == "GPID-WB"
    assert config.repo_name() == "team-brain"


# ---------------------------------------------------------------------------
# load_team_brain_local_config — disabled / absent
# ---------------------------------------------------------------------------


def test_load_returns_none_when_disabled(tmp_path):
    p = _write(tmp_path, _DISABLED_LOCAL_MD)
    config = load_team_brain_local_config(p)
    assert config is None


def test_load_returns_none_when_section_absent(tmp_path):
    p = _write(tmp_path, _NO_TEAM_BRAIN_MD)
    config = load_team_brain_local_config(p)
    assert config is None


def test_load_returns_none_when_file_missing(tmp_path):
    config = load_team_brain_local_config(tmp_path / "nonexistent.md")
    assert config is None


# ---------------------------------------------------------------------------
# load_team_brain_local_config — error paths
# ---------------------------------------------------------------------------


def test_load_raises_on_missing_repo(tmp_path):
    p = _write(tmp_path, _MISSING_REPO_MD)
    with pytest.raises(ValueError, match="missing required field 'repo'"):
        load_team_brain_local_config(p)


def test_load_raises_on_invalid_repo_format(tmp_path):
    content = _MINIMAL_LOCAL_MD.replace(
        'repo: "GPID-WB/team-brain"', 'repo: "notavalidrepo"'
    )
    p = _write(tmp_path, content)
    with pytest.raises(ValueError, match="owner/repo"):
        load_team_brain_local_config(p)


# ---------------------------------------------------------------------------
# TeamBrainLocalConfig — repo_owner / repo_name error paths
# ---------------------------------------------------------------------------


def test_repo_owner_raises_on_bad_format():
    config = TeamBrainLocalConfig(repo="notavalidrepo", project_name="x")
    with pytest.raises(ValueError, match="owner/repo"):
        config.repo_owner()


def test_repo_name_raises_on_bad_format():
    config = TeamBrainLocalConfig(repo="notavalidrepo", project_name="x")
    with pytest.raises(ValueError, match="owner/repo"):
        config.repo_name()


# ---------------------------------------------------------------------------
# _find_local_config — boundary stop behaviour (P2.4 verify)
# ---------------------------------------------------------------------------


def test_find_local_config_stops_at_git_boundary(tmp_path):
    """_find_local_config must not climb past a directory containing .git/."""
    # Layout:  tmp_path/
    #            compound-gpid.local.md  ← ancestor config (should NOT be found)
    #            project/
    #              .git/                  ← stop boundary
    #              subdir/                ← search starts here
    (tmp_path / "compound-gpid.local.md").write_text(
        _MINIMAL_LOCAL_MD, encoding="utf-8"
    )
    project = tmp_path / "project"
    project.mkdir()
    (project / ".git").mkdir()
    subdir = project / "subdir"
    subdir.mkdir()
    # Walking up from subdir hits project/.git before reaching the ancestor config
    result = _find_local_config(start=subdir)
    assert result is None, "Should stop at .git boundary and not return the ancestor config"


def test_find_local_config_returns_config_below_git_boundary(tmp_path):
    """_find_local_config must return a config that lives BELOW the .git boundary."""
    # Layout:  tmp_path/
    #            .git/                            ← repo root marker
    #            compound-gpid.local.md           ← at the repo root (same level as .git)
    (tmp_path / ".git").mkdir()
    config_path = tmp_path / "compound-gpid.local.md"
    config_path.write_text(_MINIMAL_LOCAL_MD, encoding="utf-8")
    # Starting from tmp_path itself — the candidate is found BEFORE the stop check
    result = _find_local_config(start=tmp_path)
    assert result == config_path
