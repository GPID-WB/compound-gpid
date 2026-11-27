"""Tests for the runner of the planted cases, evals/planted/run_planted.py (task 2.6, #229).

The runner starts a coding agent on a verifier's kickoff, so CI never runs it in full. These tests
hold what it judges from a reply and from the files, and that a dry run builds the project and the
kickoff of each stage, with the lens in it, and starts no agent.
"""
import json
import os
import shlex
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
    (project / ".cg-docs" / "evidence" / "x").mkdir(parents=True)  # a pointer at a record names one that is there
    (project / ".cg-docs" / "evidence" / "x" / "0003-repro.json").write_text("{}", encoding="utf-8")
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


def test_the_verification_folder_builds_the_work_as_it_went_and_the_runner_asks_that_every_check_was_rerun(tmp_path):
    """Task 2.7 (#230): the planted work of P4 is a plan the human approved, its slices done with the checks run on
    the files as they were then, and a work report with its claims. Its verifier runs at the review stage only.
    The runner asks that the verifier reran every check of the plan itself: a record of a rerun, made during its
    turn, that holds each check. A case may point at the plan, the work report or the verification profile."""
    sys.path.insert(0, str(RUNNER.parent))
    import run_planted
    done = subprocess.run([sys.executable, str(RUNNER), "--dry-run", "--cg", str(CG), "--dest", str(tmp_path / "lens"),
                           "--only", "codex", "--verifier", "verification"], capture_output=True, text=True)
    out, project = done.stdout + done.stderr, tmp_path / "lens" / "toy-poverty-codex"
    assert done.returncode == 0 and out.count("You are the verifier `verification`") == 1, out
    assert "lenses/verification.md" in out and "Every check of the plan, rerun by code: " in out, out
    folder = project / ".cg-docs" / "evidence" / "2026-11-27-poverty-brief"
    found = [json.loads(path.read_text(encoding="utf-8")) for path in sorted(folder.glob("*.json"))]
    assert [(r["kind"], r.get("slice") or r.get("check")) for r in found] == [
        ("tier", "S1"), ("check", "C1"), ("tier", "S2"), ("check", "C2"), ("check", "C4"), ("tier", "S3"),
        ("check", "C3")], found
    assert [r["verdict"] for r in found if r["kind"] == "check"] == ["verified"] * 4
    known = run_planted.records(project)
    assert not run_planted.reran(project, known)
    code = subprocess.run([sys.executable, str(CG), "evidence", "--rerun", "--report", run_planted.REPORT,
                           "--project", str(project)], capture_output=True, text=True).returncode
    assert code == 1 and run_planted.reran(project, known) and not run_planted.reran(project, run_planted.records(project))
    cases = json.loads((RUNNER.parent / "verification" / "expected.json").read_text(encoding="utf-8"))["review"]
    head = "principle: P4\nverdict: FLAG\nfindings:\n"
    report = next(n for n, line in enumerate((project / run_planted.REPORT).read_text().splitlines(), 1) if "C5 passes" in line)
    reply = head + f"  - {run_planted.REPORT}:{report}: C5 never ran (P1; fix: run it)\nnote: none\n"
    result = run_planted.judge(project, cases, reply)
    assert result["a claim with no evidence: @report, at 'C5 passes'"] and sum(result.values()) == 3, result


def test_review_of_2_7_the_rerun_leaves_the_files_the_runner_counts_and_a_lazy_reply_catches_no_case(tmp_path):
    """Review of #230. The kickoff's rerun line, run as the lens asks, made Python write the byte code of the module
    a check imports into the project, so the runner said that a verifier which did right changed a file. And a
    reply whose findings each named a whole file, as many as the file has cases, caught every case, and so did
    findings that point at a record of a run that is not there. A finding catches a case at its line when it
    names ten lines at most, and a record only when it is one."""
    sys.path.insert(0, str(RUNNER.parent))
    import run_planted
    environ = {key: value for key, value in os.environ.items() if key != "PYTHONDONTWRITEBYTECODE"}
    done = subprocess.run([sys.executable, str(RUNNER), "--dry-run", "--cg", str(CG), "--dest", str(tmp_path / "lens"),
                           "--only", "codex", "--verifier", "verification"], capture_output=True, text=True, env=environ)
    project = tmp_path / "lens" / "toy-poverty-codex"
    assert done.returncode == 0, done.stdout + done.stderr
    before = run_planted.state(project)
    kickoff = run_planted.kickoff([sys.executable, str(CG)], project, run_planted.REPORT, "review", "verification")
    line = kickoff.split("Every check of the plan, rerun by code: ")[1].splitlines()[0]
    assert subprocess.run(shlex.split(line.replace("\\", "/")), capture_output=True, env=environ).returncode == 1, line
    assert run_planted.state(project) == before
    cases = json.loads((RUNNER.parent / "verification" / "expected.json").read_text(encoding="utf-8"))["review"]
    def size(name):
        return len((project / run_planted.PLACES.get(name, name)).read_text(encoding="utf-8").splitlines())
    head, many = "principle: P4\nverdict: FLAG\nfindings:\n", []
    for name, count in (("@plan", 4), ("@report", 2), ("@profile", 1), ("pipeline.py", 2), ("checks/headcount.py", 1)):
        many += [f"  - {run_planted.PLACES.get(name, name)}:1-{size(name)}: this file breaks P4 (P1; fix: rewrite it)"] * count
    result = run_planted.judge(project, cases, head + "\n".join(many) + "\nnote: none\n")
    caught = {key.split(':')[0] for key, ok in list(result.items())[2:] if ok}  # a failing check allows any line
    assert caught <= {'a check that fails on the work as it now is', 'an expected value derived the same way as '
                      'the output'}, result  # of pipeline.py, and checks/headcount.py has 11 lines in all
    fake = head + "  - .cg-docs/evidence/2026-11-27-poverty-brief/0099-rerun.json: a check fails (P1; fix: fix it)\n" * 6
    assert sum(run_planted.judge(project, cases, fake + "note: none\n").values()) - 2 == 0
    record = sorted((project / ".cg-docs" / "evidence" / "2026-11-27-poverty-brief").glob("*-rerun.json"))[-1]
    real = fake.replace("0099-rerun.json", record.name)
    assert sum(run_planted.judge(project, cases, real + "note: none\n").values()) - 2 == 6


def test_the_adversary_folder_builds_its_work_and_a_case_is_caught_only_by_a_run_of_the_turn_that_failed(tmp_path):
    """Task 2.8 (#231): the planted work of P5 is a plan the human approved and its slices done, with faults that no
    check of the plan catches. A finding catches a case only when it points at the record of a run that failed and
    that the verifier made in its turn, and its sentence names the line of the fault; the block lists what it dropped.
    What the adversary drops is no finding, and the runner reads no line under `dropped:` as one."""
    sys.path.insert(0, str(RUNNER.parent))
    import run_planted
    done = subprocess.run([sys.executable, str(RUNNER), "--dry-run", "--cg", str(CG), "--dest", str(tmp_path / "lens"),
                           "--only", "kilo", "--verifier", "adversary"], capture_output=True, text=True)
    out, project = done.stdout + done.stderr, tmp_path / "lens" / "toy-poverty-kilo"
    assert done.returncode == 0 and out.count("You are the verifier `adversary`") == 1 and "lenses/adversary.md" in out
    cases = json.loads((RUNNER.parent / "adversary" / "expected.json").read_text(encoding="utf-8"))["review"]
    known = run_planted.records(project)
    command = cases[0]["probe"].replace("python ", f'"{sys.executable}" ', 1)
    assert subprocess.run([sys.executable, str(CG), "evidence", "--run", command, "--report", run_planted.REPORT,
                           "--project", str(project)], capture_output=True).returncode == 1
    probes = run_planted.failed(project, known)
    line = next(n for n, text in enumerate((project / "pipeline.py").read_text().splitlines(), 1) if cases[0]["text"] in text)
    block = (f"principle: P5\nverdict: FLAG\nfindings:\n  - {sorted(probes)[0]}: `pipeline.py:{line}` counts a household "
             f"at the line (R1) (P1; fix: <)\ndropped:\n  - pipeline.py:{line}: none (P1; fix: x)\nnote: none\n")
    result = run_planted.judge(project, cases, block, probes=probes)
    assert len(probes) == 1 and result[f"{cases[0]['flag']}: pipeline.py, at '{cases[0]['text']}'"], result
    assert sum(result.values()) == 3, result  # the verdict, the fixes and the one case: a dropped line catches none
    assert sum(run_planted.judge(project, cases, block).values()) == 2  # a run that is not of the verifier's turn
    assert sum(run_planted.judge(project, cases, block.replace(f":{line}`", ":1`"), probes=probes).values()) == 2
    assert run_planted.dropped(block) and not run_planted.dropped(block.replace("dropped:", "kept:"))


def test_the_simplicity_folder_builds_the_change_on_the_commit_it_began_on_and_runs_scope(tmp_path):
    """Task 2.8 (#231): the planted change of P6 needs the project as it was, so before/ is committed first and the
    work then leaves project/ as it is. The plan stage and the review stage each get a kickoff, and the runner runs
    cg.py scope once every slice is done, as the work playbook does."""
    done = subprocess.run([sys.executable, str(RUNNER), "--dry-run", "--cg", str(CG), "--dest", str(tmp_path / "lens"),
                           "--only", "codex", "--verifier", "simplicity"], capture_output=True, text=True)
    out, project = done.stdout + done.stderr, tmp_path / "lens" / "toy-poverty-codex"
    assert done.returncode == 0 and out.count("You are the verifier `simplicity`") == 2, out
    log = subprocess.run(["git", "-C", str(project), "log", "--oneline"], capture_output=True, text=True).stdout
    changed = subprocess.run(["git", "-C", str(project), "status", "--short"], capture_output=True, text=True).stdout
    assert len(log.splitlines()) == 1 and " M pipeline.py" in changed and "?? checks/table.py" in changed, changed
    assert list((project / ".cg-docs" / "evidence").rglob("*-scope.json")), out
