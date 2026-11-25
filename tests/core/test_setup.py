"""Tests for `cg.py setup`, which makes setup's file edits by code (#219, finding 2)."""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

HUB = Path(__file__).resolve().parents[2]
CG = HUB / "packs" / "core" / "cg"
BLOCK = (CG / "templates" / "pointer-block.md").read_text(encoding="utf-8").strip()
ARGS = ["--packs", "core,lang-r", "--setting", "lang-r.r-syntax=data.table-collapse",
        "--classification-levels", "Public;Official Use Only;Confidential;Strictly Confidential",
        "--approved-tool", "Claude Code=Official Use Only"]


@pytest.fixture
def env(tmp_path):
    home, project = tmp_path.resolve() / "home", tmp_path.resolve() / "project"
    shutil.copytree(CG, home / ".agents" / "skills" / "cg", ignore=shutil.ignore_patterns("__pycache__"))
    project.mkdir()
    environ = dict(os.environ, HOME=str(home), USERPROFILE=str(home))

    def cg(*args):
        done = subprocess.run([sys.executable, str(home / ".agents" / "skills" / "cg" / "scripts" / "cg.py"),
                               *args, "--project", str(project)], capture_output=True, text=True, env=environ)
        return done.returncode, done.stdout + done.stderr

    return {"project": project, "cg": cg}


def files(project: Path):
    return {p.relative_to(project).as_posix(): p.read_bytes() for p in sorted(project.rglob("*")) if p.is_file()}


def test_setup_writes_what_status_needs_and_a_second_run_changes_nothing(env):
    code, out = env["cg"]("setup", *ARGS)
    assert code == 0, out
    project = env["project"]
    config = json.loads((project / ".cg-docs" / "config.json").read_text())
    assert config["packs"] == ["core", "lang-r"]
    assert config["settings"] == {"lang-r": {"r-syntax": "data.table-collapse"}}
    assert config["classification-levels"][0] == "Public" and len(config["classification-levels"]) == 4
    assert config["approved-tools"] == {"Claude Code": "Official Use Only"}
    assert "contacts" not in config
    assert (project / "AGENTS.md").read_text().count("cg:start") == 1
    assert (project / "CLAUDE.md").read_text() == "@AGENTS.md\n"
    assert (project / ".cg-docs" / "verification.md").is_file()
    assert not (project / ".Rbuildignore").exists()
    before = files(project)
    code, out = env["cg"]("setup", *ARGS)
    assert code == 0 and files(project) == before
    assert "changed" not in out and "created" not in out
    state = json.loads(env["cg"]("status", "--json")[1])
    assert state["phase"] == "ready" and state["stops"] == []


def test_setup_keeps_existing_keys_and_the_humans_text(env):
    project = env["project"]
    (project / ".cg-docs").mkdir()
    (project / ".cg-docs" / "config.json").write_text(json.dumps(
        {"mine": 1, "settings": {"lang-r": {"other": "x"}}}))
    (project / "AGENTS.md").write_text("# My project\n\nOur rules.\n\n<!-- cg:start old -->\nold block\n<!-- cg:end -->\n\nMore rules.\n")
    (project / "CLAUDE.md").write_text("# Claude notes\n")
    assert env["cg"]("setup", *ARGS)[0] == 0
    config = json.loads((project / ".cg-docs" / "config.json").read_text())
    assert config["mine"] == 1
    assert config["settings"]["lang-r"] == {"other": "x", "r-syntax": "data.table-collapse"}
    agents = (project / "AGENTS.md").read_text()
    assert agents.startswith("# My project\n\nOur rules.\n\n") and agents.endswith("\n\nMore rules.\n")
    assert "old block" not in agents and BLOCK in agents
    assert (project / "CLAUDE.md").read_text() == "# Claude notes\n@AGENTS.md\n"


def test_setup_refuses_two_blocks_or_a_block_elsewhere_and_writes_nothing(env):
    project = env["project"]
    (project / "AGENTS.md").write_text(BLOCK + "\n\n" + BLOCK + "\n")
    before = files(project)
    code, out = env["cg"]("setup", *ARGS)
    assert code == 1 and "AGENTS.md holds 2 pointer blocks" in out
    assert files(project) == before
    (project / "AGENTS.md").write_text("# Mine\n")
    (project / "CLAUDE.md").write_text("@AGENTS.md\n" + BLOCK + "\n")
    before = files(project)
    code, out = env["cg"]("setup", *ARGS)
    assert code == 1 and "CLAUDE.md holds the pointer block" in out
    assert files(project) == before


def test_setup_in_an_r_package_adds_the_build_ignore_lines_once(env):
    project = env["project"]
    (project / "DESCRIPTION").write_text("Package: toy\n")
    (project / ".Rbuildignore").write_text("^.*\\.Rproj$\n^\\.cg-docs$\n")
    env["cg"]("setup", *ARGS)
    env["cg"]("setup", *ARGS)
    lines = (project / ".Rbuildignore").read_text().splitlines()
    assert lines == ["^.*\\.Rproj$", "^\\.cg-docs$", "^AGENTS\\.md$", "^CLAUDE\\.md$"]


def test_setup_dry_run_and_bad_input_write_nothing(env):
    project = env["project"]
    code, out = env["cg"]("setup", *ARGS, "--dry-run")
    assert code == 0 and "would create .cg-docs/config.json" in out and files(project) == {}
    for bad in (["--packs", "core", "--setting", "r-syntax"], ["--packs", "Core R"],
                ["--packs", "core", "--approved-tool", "Claude Code"]):
        code, out = env["cg"]("setup", *bad)
        assert code == 2, (bad, out)
    (project / ".cg-docs").mkdir()
    (project / ".cg-docs" / "config.json").write_text("{not json")
    code, out = env["cg"]("setup", *ARGS)
    assert code == 1 and "config.json is unreadable" in out
    assert (project / ".cg-docs" / "config.json").read_text() == "{not json"


def test_setup_records_data_rules_later_without_naming_the_packs_again(env):
    """Gate M1 (#223): "the data are synthetic and public", said during the work,
    reached the config in no agent. A second run records it and keeps the rest."""
    project = env["project"]
    code, out = env["cg"]("setup", "--packs", "core")
    assert code == 0, out
    code, out = env["cg"]("setup", "--data", "inst/extdata/survey.csv=Public", "--approved-tool", "Codex=Public")
    assert code == 0, out
    config = json.loads((project / ".cg-docs" / "config.json").read_text())
    assert config["packs"] == ["core"]
    assert config["data"] == {"inst/extdata/survey.csv": "Public"}
    assert config["approved-tools"] == {"Codex": "Public"}
    state = json.loads(env["cg"]("status", "--json")[1])
    assert state["data"] == ["inst/extdata/survey.csv=Public"]


def test_first_setup_needs_the_packs(env):
    code, out = env["cg"]("setup", "--data", "survey.csv=Public")
    assert code == 2 and "--packs" in out
    assert files(env["project"]) == {}


def test_status_prints_approved_tools_and_stops_on_a_wrong_shape(env):
    """Fable's review of the gate (#223, item 4): quick work's risk line 2 reads
    approved-tools and classification-levels, so status checks their shape and
    prints approved-tools, and line 2 can be answered from status alone."""
    project = env["project"]
    assert env["cg"]("setup", *ARGS)[0] == 0
    state = json.loads(env["cg"]("status", "--json")[1])
    assert state["approved-tools"] == ["Claude Code=Official Use Only"] and state["stops"] == []
    config_path = project / ".cg-docs" / "config.json"
    for key, bad in (("approved-tools", ["Claude Code"]), ("classification-levels", "Public;Internal"),
                     ("approved-tools", {"Claude Code": 3})):
        config = json.loads(config_path.read_text())
        config[key] = bad
        config_path.write_text(json.dumps(config))
        code, out = env["cg"]("status", "--json")
        assert code == 1 and any(key in stop for stop in json.loads(out)["stops"]), (key, out)
    assert env["cg"]("setup", *ARGS)[0] == 1  # setup refuses to merge into a wrong shape


def test_setup_takes_no_contacts(env):
    """The maintainer removed contacts from setup (#223, decision 2)."""
    code, out = env["cg"]("setup", "--packs", "core", "--contact", "ai-use=someone")
    assert code == 2 and files(env["project"]) == {}
