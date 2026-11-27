"""Tests for the runner of the planted cases, evals/planted/run_planted.py (task 2.6, #229).

The runner starts a coding agent on a verifier's kickoff, so CI never runs it in full. These tests
hold what it judges from a reply and from the files, and that a dry run builds the project and the
kickoff of each stage, with the lens in it, and starts no agent.
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

HUB = Path(__file__).resolve().parents[2]
RUNNER = HUB / "evals" / "planted" / "run_planted.py"
CG = HUB / "packs" / "core" / "cg" / "scripts" / "cg.py"
pytestmark = pytest.mark.skipif(shutil.which("git") is None, reason="git is not installed")


def test_a_finding_catches_a_case_at_its_line_or_where_the_case_allows_and_each_proposes_code(tmp_path):
    sys.path.insert(0, str(RUNNER.parent))
    import run_planted
    project = tmp_path / "p"
    shutil.copytree(RUNNER.parent / "determinism" / "project", project)
    cases = [{"flag": "unseeded randomness", "file": "pipeline.py", "text": "random.choices("},
             {"flag": "an unpinned environment", "file": "uv.lock", "or": ["record"]}]
    line = next(n for n, text in enumerate((project / "pipeline.py").read_text().splitlines(), 1)
                if "random.choices(" in text)
    block = ("principle: P3\nverdict: FLAG\nfindings:\n"
             f"  - `pipeline.py:{line + 1}`: the bootstrap draws with no seed (P1; fix: random.seed(7) above it)\n"
             "  - .cg-docs/evidence/x/0003-repro.json: no lockfile (P2; fix: uv lock)\nnote: none\n")
    wanted = {"verdict: FLAG": True, "each finding proposes the code that replaces it": True,
              "unseeded randomness: pipeline.py, at 'random.choices('": True, "an unpinned environment: uv.lock": True}
    assert run_planted.judge(project, cases, "A sentence before the block.\n\n" + block) == wanted
    worse = block.replace(f"pipeline.py:{line + 1}", "pipeline.py:1").replace(" (P2; fix: uv lock)", " (P2)")
    result = run_planted.judge(project, cases, worse)
    assert not result["unseeded randomness: pipeline.py, at 'random.choices('"], result
    assert not result["each finding proposes the code that replaces it"] and result["an unpinned environment: uv.lock"]
    assert not run_planted.judge(project, cases, block.replace("FLAG", "PASS"))["verdict: FLAG"]


def test_review_of_2_6_one_finding_catches_one_case(tmp_path):
    """Review of #229: five findings that named only a file each, over its whole length, caught every case of
    the review stage, and one finding at one slice of the plan caught all three cases of the plan stage, since
    a case was caught by any finding near it. Each case now needs a finding of its own."""
    sys.path.insert(0, str(RUNNER.parent))
    import run_planted
    folder, project = RUNNER.parent / "determinism", tmp_path / "p"
    shutil.copytree(folder / "project", project)
    shutil.copy(folder / "plan.md", project / "plan.md")
    cases = json.loads((folder / "expected.json").read_text(encoding="utf-8"))
    head = "principle: P3\nverdict: FLAG\nfindings:\n"
    vague = head + "".join(f"  - {name}:1-40: this file breaks P3 (P1; fix: rewrite it)\n" for name in
                           ("pipeline.py", "report.qmd", "README.md", "do/robustness.do", ".cg-docs/evidence/x.json"))
    result = run_planted.judge(project, cases["review"], vague)
    assert sum(result.values()) - 2 <= 5, result  # the verdict and the fixes, and one case at most for each finding
    one = head + "  - plan.md:57: the agent types the table (P1; fix: a script that writes it)\n"
    result = run_planted.judge(project, cases["plan"], one, plan="plan.md")
    assert sum(result.values()) - 2 == 1, result


def test_a_dry_run_builds_each_stage_and_prints_the_kickoff_with_the_lens_and_starts_no_agent(tmp_path):
    done = subprocess.run([sys.executable, str(RUNNER), "--dry-run", "--cg", str(CG), "--dest", str(tmp_path / "lens"),
                           "--only", "claude"], capture_output=True, text=True)
    out = done.stdout + done.stderr
    project = tmp_path / "lens" / "toy-poverty-claude"
    assert done.returncode == 0 and out.count("You are the verifier `determinism`") == 2, out
    assert "lenses/determinism.md" in out and "no agent started" in out, out
    assert list((project / ".cg-docs" / "evidence").rglob("*-repro.json")), out
    assert (project / ".cg-docs" / "plans" / "2026-11-27-poverty-brief.md").is_file()
