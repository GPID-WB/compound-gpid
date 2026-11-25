"""Tests for the gate kit in spike/gate/ (task 1.7, #223)."""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

HUB = Path(__file__).resolve().parents[2]
GATE = HUB / "spike" / "gate"
CG = HUB / "packs" / "core" / "cg" / "scripts" / "cg.py"

pytestmark = pytest.mark.skipif(shutil.which("git") is None, reason="git is not installed")


def run(script, *args):
    done = subprocess.run([sys.executable, str(GATE / script), *map(str, args)],
                          capture_output=True, text=True)
    return done.returncode, done.stdout + done.stderr


def test_make_toy_makes_one_committed_copy_per_agent_and_prints_the_value(tmp_path):
    dest = tmp_path.resolve() / "cg gate"
    code, out = run("make_toy.py", "--dest", dest)
    assert code == 0, out
    for host in ("claude", "codex", "kilo", "copilot"):
        copy = dest / f"toy-r-{host}"
        log = subprocess.run(["git", "-C", str(copy), "log", "--oneline"], capture_output=True, text=True)
        assert len(log.stdout.splitlines()) == 1
        assert (copy / "inst" / "extdata" / "survey.csv").is_file()
    assert "weighted headcount ratio at 3.00 is 0.153846" in out
    assert "an unweighted share would give 0.200000" in out
    code, out = run("make_toy.py", "--dest", dest)
    assert code == 1 and "exist already" in out


def test_make_toy_refuses_a_folder_inside_a_project(tmp_path):
    (tmp_path / ".cg-docs").mkdir()
    code, out = run("make_toy.py", "--dest", tmp_path / "inside")
    assert code == 1 and "holds .cg-docs/" in out


def setup_copy(copy: Path, settings, report_status="completed"):
    docs = copy / ".cg-docs"
    (docs / "work-reports").mkdir(parents=True)
    (docs / "config.json").write_text(json.dumps({"packs": ["core"], "settings": settings}))
    if report_status:
        (docs / "work-reports" / "2026-11-25-headcount.md").write_text(f"---\nstatus: {report_status}\n---\n")


def test_compare_status_finds_a_difference_and_a_missing_work_report(tmp_path):
    dest = tmp_path.resolve() / "gate"
    run("make_toy.py", "--dest", dest, "--hosts", "claude,codex")
    launcher = tmp_path / "launcher.json"
    launcher.write_text(json.dumps({"python": sys.executable, "cg": str(CG)}))
    setting = {"lang-r": {"r-syntax": "data.table-collapse"}}
    setup_copy(dest / "toy-r-claude", setting)
    setup_copy(dest / "toy-r-codex", setting)
    code, out = run("compare_status.py", "--dest", dest, "--launcher", launcher,
                    "--collect", "--into", tmp_path / "collected")
    assert code == 0, out
    assert (tmp_path / "collected" / "toy-r-codex" / "config.json").is_file()
    (dest / "toy-r-codex" / ".cg-docs" / "config.json").write_text(
        json.dumps({"packs": ["core"], "settings": {"lang-r": {"r-syntax": "tidyverse"}}}))
    (dest / "toy-r-claude" / ".cg-docs" / "work-reports" / "2026-11-25-headcount.md").write_text(
        "---\nstatus: in-progress\n---\n")
    code, out = run("compare_status.py", "--dest", dest, "--launcher", launcher)
    assert code == 1
    assert "DIFF  settings" in out and "MISS  toy-r-claude" in out


def test_the_readme_gives_the_agent_the_value_make_toy_computes():
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "spike" / "gate"))
    import make_toy
    weighted, _ = make_toy.headcounts(make_toy.TOY / "inst" / "extdata" / "survey.csv")
    readme = (make_toy.TOY.parent / "README.md").read_text(encoding="utf-8")
    assert f"For the toy survey I expect {weighted:.6f}." in readme
    assert "VALUE" not in readme
