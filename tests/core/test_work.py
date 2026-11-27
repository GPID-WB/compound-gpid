"""Tests for the work playbook, `cg.py evidence` and `cg.py guard` (task 2.4, #227).

What an agent must not get wrong is held by code: a check that counts is one the approved plan
declares, run as the plan writes it; a record of a run holds a digest and counts, never what the
check printed; a change that removes or skips a test or silences a checker fails `guard`; an
action that cannot be undone stops the work each time, whatever was approved before; and a work
report is completed on evidence, not on a status typed into it. The last tests hold the texts to
that code, and run each line a playbook prints.
"""
import hashlib
import json
import re
import shlex
import subprocess
import sys

from test_artifacts import ALL_NO, CG, CLEAN, PLAN, PLAN_BODY, env, front, load_cg  # noqa: F401  (env is a fixture)
from test_plan import lines_run

PY = f'"{sys.executable}"'
BODY = (PLAN_BODY.replace('`Rscript -e "devtools::test()" | tail -1`', f"`{PY} check1.py`")
        .replace("`Rscript tests/missing-weight.R`", f"`{PY} check2.py`"))
REPORT = ".cg-docs/work-reports/2026-11-26-headcount.md"
CODE, TEST = "R/headcount.R", "tests/testthat/test-headcount.R"
FIXED = 'headcount <- function(dt) if (anyNA(dt$w)) stop("no weight") else 1\n'
# check2 fails until the code stops on a missing weight, so a slice can see its check fail first.
FILES = {"check1.py": "print('share 0.153846')\n", CODE: "headcount <- function(dt) 1\n",
         "check2.py": "import sys\nsys.exit(0 if 'stop(' in open('R/headcount.R').read() else 3)\n",
         TEST: 'test_that("it is weighted", {\n  expect_equal(headcount(dt), 0.153846)\n})\n'
               'test_that("it stops", {\n  expect_error(headcount(bad))\n})\n'}
SLICE = ["--slice", "S1", "--reads", "none", "--report", REPORT]
QUICK = ["--touches", CODE, "--reads", "none", "--report", REPORT]
STOPS = "this work stops for the human's yes"


def yes(fact):
    return [arg.replace(f"{fact}=no", f"{fact}=yes") for arg in ALL_NO]


def git(project, *args):
    subprocess.run(["git", "-C", str(project), "-c", "user.name=T", "-c", "user.email=t@example.org",
                    "-c", "commit.gpgsign=false", *args], check=True, capture_output=True)


def start(env, plan=True, report=True):
    """A project under git with one commit and two small checks; then an approved plan whose
    checks they are, and the work report of the work on it, or the work report of quick work."""
    project = env["project"]
    for name, text in FILES.items():
        (project / name).parent.mkdir(parents=True, exist_ok=True)
        (project / name).write_text(text, encoding="utf-8")
    env["config"](data={"inst/extdata/survey.csv": "Public"})
    git(project, "init", "-q")
    git(project, "add", "-A")
    git(project, "commit", "-q", "-m", "base")
    if plan:
        env["put"]("plan", front("plan", "draft") + BODY)
        assert env["cg"]("approve", PLAN, "--reply", "Yes.")[0] == 0
    if report:
        code, out = env["cg"]("new", "work-report", "Headcount", "--date", "2026-11-26", *(["--plan", PLAN] * plan))
        assert code == 0, out
    return project


def held(env, kind=None):
    """The records code wrote for the work report, oldest first."""
    folder = env["project"] / ".cg-docs" / "evidence" / "2026-11-26-headcount"
    found = [json.loads(path.read_text(encoding="utf-8")) for path in sorted(folder.glob("*.json"))]
    return [record for record in found if kind in (None, record["kind"])]


def fill(path, status="in-progress", risk="filled"):
    """A work report with every request of its template answered."""
    text = re.sub(r"(## Risk\n\n)<[^<>]+>", lambda m: m.group(1) + risk, path.read_text(encoding="utf-8"))
    path.write_text(re.sub(r"<[^<>]+>", "filled", text).replace("status: in-progress", f"status: {status}"),
                    encoding="utf-8")


# ---------------------------------------------------------------- the code

def test_evidence_runs_only_the_checks_the_approved_plan_declares_and_labels_anything_else_ad_hoc(env):
    """Done when (#227). A check ID runs the command the approved plan holds for it, and no
    other. Any other command is run only as what it is, ad hoc, and never under a check's name."""
    project = start(env)
    code, out = env["cg"]("evidence", "C1", "--report", REPORT)
    assert code == 1 and "refused: no risk is computed for this work yet" in out and not held(env), out
    assert env["cg"]("tier", *ALL_NO, *SLICE)[0] == 0
    code, out = env["cg"]("evidence", "C1", "--report", REPORT)
    assert code == 0 and "share 0.153846" in out and "check: C1 (declared)" in out and "verdict: verified" in out, out
    (run,) = held(env, "check")
    assert [run[key] for key in ("check", "label", "command", "exit", "verdict")] == [
        "C1", "declared", f"{PY} check1.py", 0, "verified"]
    assert run["plan"] == PLAN and run["plan-hash"] == load_cg().text_hash(BODY)
    # A check that fails is recorded as failing. The agent may lower a verdict, and never raise one.
    code, out = env["cg"]("evidence", "C2", "--report", REPORT)
    assert code == 1 and "exit: 3" in out and "verdict: not verified" in out and held(env)[-1]["exit"] == 3, out
    code, out = env["cg"]("evidence", "C1", "--verdict", "inconclusive", "--report", REPORT)
    assert code == 1 and held(env)[-1]["verdict"] == "inconclusive" and held(env)[-1]["exit"] == 0, out
    assert env["cg"]("evidence", "C2", "--verdict", "verified", "--report", REPORT)[0] == 2
    count = len(held(env))
    for name in ("C9", "c1", "C1 --easy"):
        code, out = env["cg"]("evidence", name, "--report", REPORT)
        assert code == 1 and f"refused: {name} is not a check of the approved plan" in out and "--run" in out, out
    assert env["cg"]("evidence", "C1", "--run", f"{PY} check1.py", "--report", REPORT)[0] == 2
    assert len(held(env)) == count
    code, out = env["cg"]("evidence", "--run", f"{PY} check1.py", "--report", REPORT)
    assert code == 0 and "(ad hoc)" in out and held(env)[-1]["label"] == "ad hoc" and "plan" not in held(env)[-1], out
    assert "S1: C1 inconclusive; C2 not verified" in env["cg"]("evidence", "--report", REPORT)[1]  # ad hoc is no C1
    # The command is the plan's. A plan changed since its approval runs nothing under a check's name.
    plan = project / PLAN
    plan.write_text(plan.read_text().replace("check2.py", "check1.py"), encoding="utf-8")
    code, out = env["cg"]("evidence", "C2", "--report", REPORT)
    assert code == 1 and "is not approved as it now reads" in out and "amendment" in out, out
    assert len(held(env)) == count + 1


def test_evidence_stores_a_bounded_digest_and_never_what_a_check_printed(env):
    """Done when (#227), and P12. The agent sees what a check prints. The record holds a digest
    and two counts of it, whatever its size, and a long command is cut and kept as a digest."""
    project = start(env, plan=False)
    (project / "rows.py").write_text("for i in range(20000):\n    print('hh-%05d,2.75,Jane Roe' % i)\n")
    assert env["cg"]("tier", *ALL_NO, *QUICK)[0] == 0
    code, out = env["cg"]("evidence", "--run", f"{PY} rows.py", "--report", REPORT)
    assert code == 0 and "hh-19999,2.75,Jane Roe" in out, out[-300:]
    printed = subprocess.run(f"{PY} rows.py", shell=True, cwd=project, capture_output=True).stdout
    (run,) = held(env, "check")
    assert run["output"] == {"digest": "sha256:" + hashlib.sha256(printed).hexdigest(), "lines": 20000,
                             "bytes": len(printed)}
    assert set(run) == {"kind", "report", "check", "label", "command", "command-digest", "exit", "verdict",
                        "output", "commit", "state", "time"}
    long = f"{PY} -c \"x = '{'4.25,' * 1000}'\""
    assert env["cg"]("evidence", "--run", long, "--report", REPORT)[0] == 0
    last = held(env)[-1]
    assert len(last["command"]) <= 300 and last["command-digest"] == "sha256:" + hashlib.sha256(long.encode()).hexdigest()
    for path in (project / ".cg-docs" / "evidence").rglob("*.json"):
        text = path.read_text(encoding="utf-8")
        assert len(text) < 3000 and not re.search(r"Jane Roe|hh-0|Test Human|example\.org", text), path


LOWERED = [  # the file, what goes, what comes in its place, and the rule that names it
    (TEST, None, None, "test-deleted"),
    (TEST, 'test_that("it stops", {\n  expect_error(headcount(bad))\n})\n', "", "test-removed"),
    (TEST, "  expect_error(headcount(bad))\n", "", "assertion-removed"),
    (TEST, 'test_that("it stops", {\n', 'test_that("it stops", {\n  skip("later")\n', "test-skipped"),
    ("tests/test_gap.py", "", "import pytest\n\n@pytest.mark.skip\ndef test_gap():\n    assert gap() == 1\n", "test-skipped"),
    (CODE, "function(dt) 1", 'function(dt) suppressWarnings(as.numeric("SECRET-42"))', "suppression-added"),
    ("R/gap.R", "", "gap <- function(dt) try(log(-1), silent = TRUE)\n", "suppression-added"),
    ("scripts/run.py", "", "import os  # noqa: F401\n", "suppression-added"),
]


def test_guard_fails_when_the_diff_deletes_or_skips_tests_or_adds_suppressions(env):
    """Done when (#227). The cheapest way past a failing check is to take the check away. guard
    names the rule and the file, never the line, which may hold a value."""
    code, out = env["cg"]("guard")
    assert code == 2 and "guard cannot run" in out, out  # no git repository: never read as clean
    project = start(env, plan=False)
    assert env["cg"]("guard") == (0, "guard: clean\n")
    (project / CODE).write_text(FIXED)
    (project / TEST).write_text(FILES[TEST] + 'test_that("it is a share", {\n  expect_lte(headcount(dt), 1)\n})\n')
    assert env["cg"]("guard") == (0, "guard: clean\n")  # a change that adds a test lowers nothing
    for name, old, new, rule in LOWERED:
        git(project, "checkout", "-q", "--", ".")
        git(project, "clean", "-fdq", "-e", ".cg-docs")
        path = project / name
        text = path.read_text() if path.exists() else ""
        assert old is None or old in text
        if new is None:
            path.unlink()
        else:
            path.parent.mkdir(exist_ok=True)
            path.write_text(text.replace(old, new) if old else text + new)
        code, out = env["cg"]("guard")
        assert code == 1 and f"FAIL {rule}: {name}" in out and "SECRET-42" not in out, (rule, out)
        assert re.search(r"guard: \d problems?\n$", out), out


def test_guard_holds_a_slice_to_its_files_and_to_evidence_on_the_files_as_they_now_are(env):
    """Plan, section 4.3, the end of each slice: the files touched match the slice, and evidence
    exists for the slice's checks. Evidence holds for the files as they were when the check ran."""
    project = start(env)
    (project / "notes.txt").write_text("changed before the slice started\n")
    assert env["cg"]("tier", *ALL_NO, *SLICE)[0] == 0 and held(env, "tier")[0]["files"] == [CODE]
    assert env["cg"]("evidence", "C2", "--report", REPORT)[0] == 1  # the check is seen to fail first
    (project / CODE).write_text(FIXED)
    (project / "R" / "other.R").write_text("other <- 1\n")
    code, out = env["cg"]("guard", "--report", REPORT)
    assert code == 1 and "FAIL outside: R/other.R" in out and "S1" in out and "notes.txt" not in out, out
    assert "FAIL no-evidence: check C1" in out and "FAIL no-evidence: check C2" in out, out
    (project / "R" / "other.R").unlink()
    for check in ("C1", "C2"):
        assert env["cg"]("evidence", check, "--report", REPORT)[0] == 0
    assert env["cg"]("guard", "--report", REPORT) == (0, "guard: clean\n")
    assert "S1: C1 verified; C2 verified" in env["cg"]("evidence", "--report", REPORT)[1]
    (project / CODE).write_text(FIXED + "# one more change\n")
    code, out = env["cg"]("guard", "--report", REPORT)
    assert code == 1 and "FAIL no-evidence: check C1" in out and "as they now are" in out, out
    assert env["cg"]("evidence", "--run", f"{PY} check1.py", "--report", REPORT)[0] == 0
    assert "FAIL no-evidence: check C1" in env["cg"]("guard", "--report", REPORT)[1]  # ad hoc is no C1
    # Run again in the middle of a slice, tier does not take the agent's own change for what was there before.
    (project / "R" / "other.R").write_text("other <- 1\n")
    assert env["cg"]("tier", *ALL_NO, *SLICE)[0] == 0
    assert "FAIL outside: R/other.R" in env["cg"]("guard", "--report", REPORT)[1]
    for args, words in ((["--slice", "S9"], "'S9' is no slice of the plan"), (["--touches", CODE], "give --slice")):
        code, out = env["cg"]("tier", *ALL_NO, *args, "--reads", "none", "--report", REPORT)
        assert code == 2 and words in out, out


def test_an_irreversible_action_always_stops_and_goes_on_only_on_the_humans_recorded_yes(env):
    """Done when (#227): irreversible actions always stop. The plan's approval covers what the plan
    says, a number or an interface. It never covers an action that cannot be undone: code names the
    stop, records nothing past it, and takes only a plain yes to that one action."""
    project = start(env)
    code, out = env["cg"]("tier", *yes("number"), *SLICE)
    assert code == 0 and out.startswith("tier: elevated\nreasons: number: ") and "\nstop: none\n" in out, out
    code, out = env["cg"]("tier", *yes("irreversible"), *SLICE)
    assert code == 0 and "\nstop: irreversible: " in out, out
    waits = json.loads(env["cg"]("status", "--json")[1])["waiting-on-human"]
    assert any(REPORT in item and "irreversible" in item for item in waits), waits
    for command in (["evidence", "C1"], ["evidence", "--run", f"{PY} check1.py"], ["guard"]):
        code, out = env["cg"](*command, "--report", REPORT)
        assert code == 1 and STOPS in out and "irreversible" in out and "end your turn" in out, out
    assert not held(env, "check")
    code, out = env["cg"]("approve", REPORT, "--reply", "Yes.")
    assert code == 1 and "refused" in out and "'## Risk'" in out, out  # the report does not say what is asked
    fill(project / REPORT, risk="Delete data/old.csv, which no commit holds.")
    for reply in ("Sounds good.", "Yes, but keep a copy.", "ok?", "No."):
        code, out = env["cg"]("approve", REPORT, "--reply", reply)
        assert code == 1 and "refused" in out, (reply, out)
    records = project / ".cg-docs" / "approvals"
    assert not list(records.glob("2026-11-26-headcount.*"))
    code, out = env["cg"]("approve", REPORT, "--reply", "Yes.")
    assert code == 0 and "recorded: the human's yes" in out and "Test Human" in out, out
    (path,) = records.glob("2026-11-26-headcount.*.json")
    record = json.loads(path.read_text(encoding="utf-8"))
    assert record["reply"] == "Yes." and record["artifact"] == REPORT and "Delete data/old.csv" in record["text"]
    assert (project / record["tier"]).is_file() and held(env, "tier")[-1]["stop"][0].startswith("irreversible")
    assert env["cg"]("evidence", "C1", "--report", REPORT)[0] == 0
    assert "already recorded" in env["cg"]("approve", REPORT, "--reply", "Yes.")[1]
    # The yes was to that action. The next one stops again, and a report typed as completed fails.
    assert env["cg"]("tier", *yes("irreversible"), *SLICE)[0] == 0
    code, out = env["cg"]("evidence", "C1", "--report", REPORT)
    assert code == 1 and STOPS in out, out
    fill(project / REPORT, status="completed")
    code, out = env["cg"]("validate", REPORT)
    assert code == 1 and STOPS in out, out


def test_a_yes_to_one_stop_never_covers_the_next_one_even_within_the_same_second(env, monkeypatch):
    """CI on 7162a8b7 (#227): two runs of tier within one second wrote two records with the same
    text, and the yes to the first one covered the second. The clock is held still here."""
    project = start(env)
    cg = load_cg()
    monkeypatch.setattr(cg, "now", lambda: "2026-11-26T10:00:00Z")
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(env["home"] / ".gitconfig"))
    here = ["--project", str(project)]
    fill(project / REPORT, risk="Delete data/old.csv, which no commit holds.")
    assert cg.main(["tier", *yes("irreversible"), *SLICE, *here]) == 0
    assert cg.main(["approve", REPORT, "--reply", "Yes.", *here]) == 0
    assert cg.main(["evidence", "C1", "--report", REPORT, *here]) == 0
    assert cg.main(["tier", *yes("irreversible"), *SLICE, *here]) == 0
    assert cg.main(["evidence", "C1", "--report", REPORT, *here]) == 1  # the second stop is not answered
    assert cg.main(["approve", REPORT, "--reply", "Yes.", *here]) == 0
    assert len(list((project / ".cg-docs" / "approvals").glob("2026-11-26-headcount.*.json"))) == 2


def test_work_starts_on_a_plan_approved_as_it_now_reads_and_is_completed_only_on_evidence(env):
    """ADR 0005 left open what holds the work to the plan. The work report names the plan, and
    it is completed when every check of the plan has verified evidence (version 1 issue #98)."""
    project = start(env, report=False)
    plan = project / PLAN
    approved = plan.read_text()
    for text in (approved.replace("status: approved", "status: draft"), approved.replace("0.153846", "0.2")):
        plan.write_text(text, encoding="utf-8")
        code, out = env["cg"]("new", "work-report", "Headcount", "--date", "2026-11-26", "--plan", PLAN)
        assert code == 1 and "refused: work starts on a plan the human approved as it now reads" in out, out
    plan.write_text(approved, encoding="utf-8")
    assert env["cg"]("new", "work-report", "Headcount", "--date", "2026-11-26", "--plan", PLAN)[0] == 0
    report = project / REPORT
    assert f"\nplan: {PLAN}\n" in report.read_text() and "\nsize: standard\n" in report.read_text()
    assert "\nstatus: in-progress\n" in plan.read_text() and env["cg"]("validate", PLAN)[0] == 0
    code, out = env["cg"]("new", "work-report", "Headcount again", "--plan", PLAN)
    assert code == 1 and f"not finished: {REPORT}" in out and "continue in that file" in out, out
    fill(report, status="completed")
    code, out = env["cg"]("validate", REPORT)
    assert code == 1 and "no risk is computed for this work yet" in out, out
    assert "check C1 of the plan has no verified evidence" in out and "check C2 of the plan" in out, out
    assert env["cg"]("tier", *ALL_NO, *SLICE)[0] == 0
    assert env["cg"]("evidence", "C1", "--report", REPORT)[0] == 0 and env["cg"]("evidence", "C2", "--report", REPORT)[0] == 1
    code, out = env["cg"]("validate", REPORT)
    assert code == 1 and "check C2 of the plan has no verified evidence" in out and "check C1" not in out, out
    (project / CODE).write_text(FIXED)
    assert env["cg"]("evidence", "C2", "--report", REPORT)[0] == 0
    assert env["cg"]("validate", REPORT) == (0, CLEAN)


def test_quick_work_stops_at_any_reason_and_its_record_is_the_evidence(env):
    """ADR 0005 left open whether code records the lines of tier and the yes at an elevated tier
    in quick work. It does: tier writes its lines, approve the reply, and evidence the checks."""
    project = start(env, plan=False)
    report = project / REPORT
    assert "\nsize: quick\n" in report.read_text() and "\nplan: \n" in report.read_text()
    code, out = env["cg"]("tier", *yes("number"), *QUICK)
    assert code == 0 and "\nstop: number: " in out and "\nrecord: .cg-docs/evidence/2026-11-26-headcount/" in out, out
    tier = held(env, "tier")[-1]
    assert tier["tier"] == "elevated" and tier["files"] == [CODE] and tier["facts"]["number"] == "yes"
    assert STOPS in env["cg"]("evidence", "--run", f"{PY} check1.py", "--report", REPORT)[1]
    fill(report, risk="Goal: a weighted share. Check: the share is 0.153846.")
    code, out = env["cg"]("approve", REPORT, "--reply", "Yes, proceed.")
    assert code == 0 and "recorded: the human's yes" in out, out
    code, out = env["cg"]("evidence", "C1", "--report", REPORT)
    assert code == 1 and "names no plan" in out and "--run" in out, out
    (project / CODE).write_text(FIXED)
    (project / "R" / "gap.R").write_text("gap <- 1\n")
    code, out = env["cg"]("guard", "--report", REPORT)
    assert code == 1 and "FAIL outside: R/gap.R" in out and "tier" in out and "FAIL no-evidence: no check" in out, out
    (project / "R" / "gap.R").unlink()
    report.write_text(report.read_text().replace("status: in-progress", "status: completed"))
    code, out = env["cg"]("validate", REPORT)
    assert code == 1 and "no check is verified" in out, out
    assert env["cg"]("evidence", "--run", f"{PY} check2.py", "--report", REPORT)[0] == 0
    assert env["cg"]("guard", "--report", REPORT) == (0, "guard: clean\n")
    assert env["cg"]("validate", REPORT) == (0, CLEAN)
    # A tier that is low stops nothing, and there is nothing to say yes to.
    assert "\nstop: none\n" in env["cg"]("tier", *ALL_NO, *QUICK)[1]
    code, out = env["cg"]("approve", REPORT, "--reply", "Yes.")
    assert code == 0 and "nothing stops this work" in out and len(list((project / ".cg-docs" / "approvals").glob("2026-11-26-*"))) == 1


# ---------------------------------------------------------------- the review of task 2.4

def test_completion_counts_a_run_only_under_its_own_plan_and_the_command_it_declares(env):
    """Review of #227, finding 1. With the work report pointed at another approved plan for one
    run, a check that never passed under its own plan counted for completion."""
    project = start(env)
    other = ".cg-docs/plans/2026-11-25-other.md"
    env["put"]("plan", front("plan", "draft") + BODY.replace("check2.py", "check1.py"), "2026-11-25-other.md")
    assert env["cg"]("approve", other, "--reply", "Yes.")[0] == 0
    assert env["cg"]("tier", *ALL_NO, *SLICE)[0] == 0
    report = project / REPORT
    text = report.read_text()
    report.write_text(text.replace(f"plan: {PLAN}", f"plan: {other}"))
    assert env["cg"]("evidence", "C2", "--report", REPORT)[0] == 0  # check1.py, the other plan's C2
    report.write_text(text)
    assert env["cg"]("evidence", "C1", "--report", REPORT)[0] == 0
    fill(report, status="completed")
    code, out = env["cg"]("validate", REPORT)
    assert code == 1 and "check C2 of the plan has no verified evidence" in out, out


def test_a_check_runs_only_a_command_cell_that_holds_one_text_in_backticks(env):
    """Review of #227, finding 2. Code ran the first text in backticks, `cd tests` or a file name
    in gate rerun 17's plans, or a whole cell of prose; and a \\| that the table shows as | was
    run with its backslash."""
    project = start(env, report=False)
    plan, cg = project / PLAN, load_cg()
    approved = plan.read_text()
    for cell in (f"Run `cd tests`, then `{PY} check2.py`", f"{PY} check2.py, then compare the share"):
        plan.write_text(approved.replace(f"`{PY} check2.py`", cell).replace("status: approved", "status: draft"))
        code, out = env["cg"]("validate", PLAN)
        assert code == 1 and "check C2: its command is not one text in backticks" in out, out
    assert cg.command_of("`a \\| b` (the table shows a | b)") == "a | b" and cg.command_of("`a` and `b`") is None
    assert cg.command_of("`Rscript tests/run.R`, from the root") == "Rscript tests/run.R"


def test_a_data_file_that_is_not_cleared_is_read_only_on_the_humans_decision_on_data(env):
    """Review of #227, finding 3. In quick work a yes to the contract answered a stop whose reason
    was a data file that is not cleared, and no decision on data was recorded. On a plan, such a
    file stopped nothing, also when the plan's data register does not list it."""
    project = start(env)
    env["config"](data={"inst/extdata/survey.csv": "Confidential", "data/secret.csv": "Confidential"})
    reads = ["--agent", "Claude Code", "--report", REPORT]
    out = env["cg"]("tier", *ALL_NO, "--slice", "S1", "--reads", "inst/extdata/survey.csv", *reads)[1]
    assert "reasons: data: inst/extdata/survey.csv" in out and "\nstop: none\n" in out, out  # the register lists it
    out = env["cg"]("tier", *ALL_NO, "--slice", "S1", "--reads", "data/secret.csv", *reads)[1]
    assert "\nstop: data: data/secret.csv" in out, out  # the register does not
    quick = ".cg-docs/work-reports/2026-11-27-label.md"
    assert env["cg"]("new", "work-report", "Label", "--date", "2026-11-27")[0] == 0
    out = env["cg"]("tier", *ALL_NO, "--touches", CODE, "--reads", "data/secret.csv", *reads[:2], "--report", quick)[1]
    fill(project / quick, risk="Goal: a weighted share. Check: the share is 0.153846.")
    code, out = env["cg"]("approve", quick, "--reply", "Yes.")
    assert code == 1 and "approve --reads" in out and not held(env, "x"), out
    assert env["cg"]("approve", "--reads", "data/secret.csv", "--agent", "Claude Code", "--reply", "Yes.")[0] == 0
    out = env["cg"]("tier", *ALL_NO, "--touches", CODE, "--reads", "data/secret.csv", *reads[:2], "--report", quick)[1]
    assert "\nstop: none\n" in out, out


def test_guard_holds_a_slice_to_the_commit_it_began_on_and_runs_before_the_first_commit(env):
    """Review of #227, finding 4. A commit in the slice hid a deleted test and a file outside the
    slice from guard, and in a repository with no commit guard could never print clean."""
    project = start(env)
    assert env["cg"]("tier", *ALL_NO, *SLICE)[0] == 0
    (project / CODE).write_text(FIXED)
    (project / "R" / "other.R").write_text("other <- 1\n")
    (project / TEST).unlink()
    git(project, "add", "-A")
    git(project, "commit", "-q", "-m", "the slice")
    for check in ("C1", "C2"):
        assert env["cg"]("evidence", check, "--report", REPORT)[0] == 0
    code, out = env["cg"]("guard", "--report", REPORT)
    assert code == 1 and f"FAIL test-deleted: {TEST}" in out and "FAIL outside: R/other.R" in out, out
    assert "no-evidence" not in out, out
    git(project, "update-ref", "-d", "HEAD")  # a repository with no commit yet
    assert env["cg"]("guard") == (0, "guard: clean\n")


MISSED = [  # the file, what it held, what it holds now: each lowers the bar, and guard missed it
    ("tests/testthat/test-a.R", 'test_that("w", {\n  expect_equal(f(1), 2)\n})\n',
     '# test_that("w", {\n#   expect_equal(f(1), 2)\n# })\n'),
    ("tests/testthat/test-a.R", 'test_that("w", {\n  expect_equal(f(1), 2)\n})\n',
     'if (FALSE) test_that("w", {\n  expect_equal(f(1), 2)\n})\n'),
    ("tests/testthat.R", 'library(testthat)\ntest_check("pkg")\n', "library(testthat)\n"),
    ("tests/test_a.py", "def test_a():\n    assert f(1) == 2\n", "def test_a():\n    # assert f(1) == 2\n    pass\n"),
    ("tests/test_a.py", "def test_a(self):\n    assert f(1) == 2\n", "def test_a(self):\n    self.skipTest('x')\n    assert f(1) == 2\n"),
    ("tests/test_a.py", "def test_a():\n    assert f(1) == 2\n", "@unittest.skipIf(True, 'x')\ndef test_a():\n    assert f(1) == 2\n"),
    ("tests/test_a.py", "def test_a():\n    assert f(1) == 2\n", "np = pytest.importorskip('np')\ndef test_a():\n    assert f(1) == 2\n"),
    ("src/a.py", "def f(x):\n    check(x)\n", "def f(x):\n    try:\n        check(x)\n    except Exception:\n        pass\n"),
    ("src/a.py", "x = 1\n", "x = 1  # pylint: disable=all\n"),
    ("src/a.py", "def f():\n    g()\n", "def f():\n    with contextlib.suppress(Exception):\n        g()\n"),
    ("pyproject.toml", "[tool.pytest.ini_options]\n", '[tool.pytest.ini_options]\naddopts = "--ignore=tests/test_a.py"\n'),
    ("R/a.R", "f <- function(x) stopifnot(x > 0)\n", "f <- function(x) tryCatch(stopifnot(x > 0), error = function(e) NULL)\n"),
    ("tests/test_a.do", "assert w > 0\n", "capture assert w > 0\n"),
    ("do/clean.do", "assert w > 0\n", "cap noi assert w > 0\n"),
    ("tests/test_a.do", "assert w > 0\nassert y > 0\n", "assert w > 0\n* assert y > 0\n"),
    ("tests/run.sh", "set -e\nRscript t.R\n", "set +e\nRscript t.R\n"),
    ("src/a.ts", "let x = 1\n", "// @ts-expect-error\nlet x = 1\n"),
]


def test_guard_sees_a_test_commented_out_a_skip_by_condition_and_a_silenced_error(env):
    """Review of #227, finding 5: each change in MISSED lowers the bar in R, Python, Stata or the
    shell, and guard printed clean. suppressMessages() around library() silences no warning or
    error, and guard failed it."""
    project = env["project"]
    git(project, "init", "-q")
    for name, old, new in MISSED + [("R/load.R", "f <- 1\n", "suppressMessages(library(data.table))\nf <- 1\n")]:
        (project / name).parent.mkdir(parents=True, exist_ok=True)
        (project / name).write_text(old)
        git(project, "add", "-A")
        git(project, "commit", "-q", "--allow-empty", "-m", "base")
        (project / name).write_text(new)
        code, out = env["cg"]("guard")
        assert (code == 1) == (name != "R/load.R"), (name, new, out)
        (project / name).write_text(old)


def test_the_tier_record_names_no_file_the_work_does_not_declare(env):
    """Review of #227, finding 6. The tier record kept the name of every file that had changed or
    that no commit holds, a data file named after a person among them, and is committed."""
    project = start(env)
    (project / "data" / "interviews").mkdir(parents=True)
    (project / "data" / "interviews" / "jane_roe.csv").write_text("id,answer\n1,42\n")
    assert env["cg"]("tier", *ALL_NO, *SLICE)[0] == 0
    assert "jane_roe" not in json.dumps(held(env, "tier"))
    (project / "data" / "interviews" / "jane_roe.csv").write_text("id,answer\n1,43\n")
    assert "FAIL outside: data/interviews/jane_roe.csv" in env["cg"]("guard", "--report", REPORT)[1]


def test_a_work_report_that_will_not_be_finished_is_dropped_and_then_blocks_nothing(env):
    """Gate rerun 18 (#227): an open work report held back the next piece of work for two agents,
    and no status closed a work report unfinished. A dropped one keeps its text, needs no evidence,
    and is no longer open, active or waiting, also with a stop the human never said yes to."""
    project = start(env)
    report = project / REPORT
    assert env["cg"]("tier", *yes("irreversible"), *SLICE)[0] == 0
    state = json.loads(env["cg"]("status", "--json")[1])
    assert state["active"] == REPORT and any(REPORT in item for item in state["waiting-on-human"]), state
    kept = report.read_text().replace("status: in-progress", "status: dropped")
    report.write_text(kept)
    state = json.loads(env["cg"]("status", "--json")[1])
    assert state["active"] == PLAN and state["open-artifacts"] == 1 and state["waiting-on-human"] == [], state
    code, out = env["cg"]("validate", REPORT)
    assert code == 0 and "problems: 0" in out and "evidence" not in out and report.read_text() == kept, out
    # The work of the plan can start again, in a work report of its own.
    code, out = env["cg"]("new", "work-report", "Headcount again", "--date", "2026-11-27", "--plan", PLAN)
    assert code == 0 and "created" in out, out
    cg = load_cg()
    assert cg.ARTIFACTS["work-report"]["statuses"]["dropped"] == "closed" and "dropped" in cg.SETTLED
    for text in (WORK.read_text(encoding="utf-8"), QUICK_TEXT.read_text(encoding="utf-8")):  # when the agent sets it
        assert "`status: dropped`" in text and "not to be finished" in text and "Never set it" in text


# ---------------------------------------------------------------- the texts

WORK, WORKER, QUICK_TEXT = (CG / "playbooks" / "work.md", CG / "worker.md", CG / "playbooks" / "quick.md")
STOP_LIST = ("delet", "overwrit", "push", "release", "publish", "message", "credentials")


def run_line(env, line, **values):
    """Run one line of a playbook as it is written, with each request in angle brackets answered.
    A fact is answered before the line is split, and the rest after, so a command keeps its quotes."""
    return env["cg"](*[re.sub(r"<([^<>]+)>", lambda m: values.get(m.group(1), m.group(0)), part)
                       for part in shlex.split(line.replace("<yes or no>", "no"))])


def test_the_lines_the_work_playbook_and_quick_work_run_work_as_written(env):
    project = start(env, report=False)
    values = {"short title": "Headcount", "the plan": PLAN, "the work report": REPORT, "slice ID": "S1", "check ID": "C1", "the check's command": f"{PY} check1.py", "data file": "none",
              "the human's reply, word for word": "Yes.", "file": CODE}
    work = lines_run(WORK.read_text(encoding="utf-8"))
    assert [line.split()[0] for line in work] == ["evidence", "new", "tier", "evidence", "guard", "approve", "validate"]
    listing, new, tier, check, guard, approve, validate = work
    assert "--plan" in new and "--slice" in tier and "--touches" not in tier and check.startswith('evidence "<check ID>"')
    assert run_line(env, new + " --date 2026-11-26", **values)[0] == 0
    no_agent = tier.replace(' --agent "<this coding agent>"', "")
    assert tier != no_agent and "\nstop: none\n" in run_line(env, no_agent, **values)[1]
    assert "verdict: verified" in run_line(env, check, **values)[1]
    assert "S1: C1 verified; C2 not run" in run_line(env, listing, **values)[1]
    assert "FAIL no-evidence: check C2" in run_line(env, guard, **values)[1]
    assert "nothing stops this work" in run_line(env, approve, **values)[1]
    assert "schema-2: 1" in run_line(env, validate, **values)[1]
    # Quick work runs the same lines, with the files given to tier and the check's command given to evidence.
    quick = lines_run(QUICK_TEXT.read_text(encoding="utf-8"))
    assert [line.split()[0] for line in quick] == ["new", "tier", "approve", "setup", "approve", "packs", "evidence",
                                                   "guard", "validate"]
    assert quick[2] == approve and quick[8] == validate and quick[7] == guard and "--plan" not in quick[0]
    assert quick[1] == tier.replace('--slice "<slice ID>"', '--touches "<file>"')
    values["the work report"] = ".cg-docs/work-reports/2026-11-27-label.md"
    assert run_line(env, quick[0] + " --date 2026-11-27", **{**values, "short title": "Label"})[0] == 0
    assert "\nstop: none\n" in run_line(env, quick[1].replace(' --agent "<this coding agent>"', ""), **values)[1]
    code, out = run_line(env, quick[6], **values)
    assert code == 0 and "(ad hoc)" in out and "--run" in quick[6], out
    assert run_line(env, guard, **values) == (0, "guard: clean\n")
    assert (project / values["the work report"]).is_file()


def test_the_work_playbook_takes_one_slice_at_a_time_and_names_the_stops():
    """#227: build in slices, with evidence recorded by code, and stop rules. No stop relies on
    the coding agent's approval prompt: a hard stop is a question, and then the turn ends."""
    text = WORK.read_text(encoding="utf-8")
    opening = text[:text.index("## 1.")]
    assert "one slice at a time" in opening and "cannot be undone" in opening
    stops = text[text.index("## 5. Stop"):text.index("## 6.")]
    for words in ("This is a hard stop", "end your turn", "approval settings", "plain yes", "each time", "`refused`",
                  "`irreversible=yes`", "two attempts", "amendment", "Ask first", *STOP_LIST):
        assert words in stops, words
    slices = text[text.index("## 2."):text.index("## 5. Stop")]
    for words in ("fail", "before the change", "lead skill", "worked example", "`--verdict", "`FAIL`"):
        assert words in slices, words
    assert "Never" in slices and "expected value" in slices  # a check is never made easier
    close = text[text.index("## 6."):]
    assert "PLACEHOLDER: written in task 2.5" in close and "self-review" in close and "`worker.md`" in text
    for principle in ("P3", "P4", "P6"):
        assert principle in close, principle
    assert "Commit" in close and "only when" in close


def test_the_texts_hold_what_the_review_of_task_2_4_found_in_their_wording():
    """Review of #227, W1 to W10. In gate rerun 18 one agent stopped the work for good because the
    package's whole test run passed before the change, and two took open work of another request
    for a reason not to start."""
    work, quick, plan = (path.read_text(encoding="utf-8") for path in (WORK, QUICK_TEXT, CG / "playbooks" / "plan.md"))
    for text in (work[work.index("## 3."):work.index("## 4.")], plan[plan.index("## 3."):plan.index("## 4.")]):
        assert "a regression check" in text and "still pass" in text  # W1
    assert "does not hold this one back" in quick[quick.index("## 1."):quick.index("## 2.")]  # W2
    for text in (plan, (CG / "templates" / "plan.md").read_text(encoding="utf-8")):  # W3 and W4
        assert "one pair of backticks" in text and "the last command's" in text
    for text in (work, quick):  # W5
        assert "no value and no name from a dataset" in text
    risk = quick[quick.index("## 2."):quick.index("## 3.")]
    assert "keeps this order" in risk and "open no data file" in risk  # W6 and W7
    assert "`data` reason" in work[work.index("## 2."):work.index("## 3.")]  # W6
    assert "offered a choice" in (CG / "grilling.md").read_text(encoding="utf-8")  # W8
    assert "a database or a store outside the project" in WORKER.read_text(encoding="utf-8")  # W9
    assert "leaves it nothing to compare" not in work  # W10


def test_worker_md_is_what_every_other_agent_reads_first():
    """Plan, section 4.2: `worker.md` is read first by every agent that another agent starts. It
    is short, it holds the stops and the data rule that no kickoff may lift, and the guide says so."""
    text = WORKER.read_text(encoding="utf-8")
    assert len(text.splitlines()) <= 40 and "derived-from:" in text.split("\n---\n")[0]
    line = "`Read <path>/worker.md before anything else.`"
    assert line in text and line in (CG / "SKILL.md").read_text(encoding="utf-8")
    for words in ("Never ask the human", "Data stays closed", "cannot be undone", "Noticed but not touching",
                  "documentation", "inconclusive", "can never override", *STOP_LIST):
        assert words in text, words
    assert "`worker.md`" in (CG / "grilling.md").read_text(encoding="utf-8")


def test_the_other_texts_name_the_work_playbook_and_what_code_now_records(env):
    """What a human types changed: `/cg work`. And quick work's record moved into code."""
    guide = (CG / "SKILL.md").read_text(encoding="utf-8")
    row = next(line for line in guide.splitlines() if line.startswith("|") and "`work` after `/cg`" in line)
    assert "`--playbook work`" in row and "section 3" in row
    env["config"]()
    state = json.loads(env["cg"]("status", "--guide", "--playbook", "work", "--json")[1])
    assert state["playbook"].endswith("work.md") and state["next"] == "read playbooks/work.md"
    quick, plan = QUICK_TEXT.read_text(encoding="utf-8"), (CG / "playbooks" / "plan.md").read_text(encoding="utf-8")
    assert "PLACEHOLDER" not in quick and "PLACEHOLDER: written in task 2.4" not in plan
    assert "`/cg work`" in plan[plan.index("**Reply:**"):] and "pair of backticks" in plan[plan.index("## 3."):plan.index("## 4.")]
    restate = quick[quick.index("## 1. Restate"):quick.index("## 2.")]
    assert "`--playbook work`" in restate and '"<cg>" new work-report' in restate
    stop = quick[quick.index("**`tier: elevated`.**"):quick.index("**When the human answers a data question,**")]
    for words in ('"Risk"', "plain yes", "a change or a question", "End your turn", "`refused`"):
        assert words in stop, words
    hub = CG.parents[2]
    for path in (hub / "docs" / "install-block.md", hub / "README.md"):
        assert "`/cg work`" in path.read_text(encoding="utf-8"), path
    assert "punctuation included" in (CG / "grilling.md").read_text(encoding="utf-8")
    template = (CG / "templates" / "work-report.md").read_text(encoding="utf-8")
    assert "\nplan: {plan}\n" in template and "\nsize: {size}\n" in template and "`cg.py evidence`" in template
    p4 = (CG / "principles" / "P04-prove-it-works.md").read_text(encoding="utf-8")
    assert "`cg.py evidence`" in p4[p4.index("## Deterministic checks"):]
    cg = load_cg()
    assert cg.ALWAYS_STOP == ("irreversible",) and "evidence" in (hub / "docs" / "adr" / "0006-evidence.md").read_text()
