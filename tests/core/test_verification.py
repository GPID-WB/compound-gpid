"""Tests for the verification verifier (P4) and `cg.py evidence --rerun` (task 2.7, #230).

A verifier is a model reading a lens, and CI cannot start a model. The verifier of P4 reruns every check
of the plan itself, through a line that code prints in its kickoff: code runs each check as the approved
plan declares it, records the run as the verifier's and apart from the evidence of the work, shows and
keeps no line of what a check printed (P12), and compares each check with the work's newest run of it.
It also names what a rule can find of P4. Each violation the issue names is planted in
evals/planted/verification/, and code is held to its part of each. What stays by judgement runs on the
same project through a coding agent: evals/planted/run_planted.py, whose build these tests use.
"""
import json
import re
import shlex
import sys

from test_artifacts import ALL_NO, CG, HUB, env, load_cg  # noqa: F401  (env is a fixture)
from test_determinism import at
from test_verifiers import dispatched, give, held
from test_work import PLAN, PY, REPORT as WORK, SLICE, start, yes

sys.path.insert(0, str(HUB / "evals" / "planted"))
import run_planted  # noqa: E402

PLANTED = HUB / "evals" / "planted" / "verification"
CASES = json.loads((PLANTED / "expected.json").read_text(encoding="utf-8"))
REPORT = run_planted.REPORT


def planted(env):
    """The planted project as the work leaves it: an approved plan, its slices done, each check run as it went."""
    env["project"].rmdir()
    run_planted.build(PLANTED, env["project"], [sys.executable, str(env["home"] / ".agents" / "skills" / "cg" /
                                                                     "scripts" / "cg.py")], CASES)
    return env["project"]


def rerun(env, report=REPORT, *more):
    """What the rerun printed, its exit code, and the newest record of a rerun, with its path."""
    code, out = env["cg"]("evidence", *more, "--rerun", "--report", report)
    folder = env["project"] / ".cg-docs" / "evidence" / report.split("/")[-1][:-3]
    found = sorted(folder.glob("*-rerun.json"))
    return code, out, json.loads(found[-1].read_text(encoding="utf-8")) if found else {}, \
        found[-1].relative_to(env["project"]).as_posix() if found else ""


def where(project, case):
    """Where a planted case shows: the path, and the line that holds its text when it has one."""
    name = run_planted.PLACES.get(case["file"], case["file"])
    lines = (project / name).read_text(encoding="utf-8").splitlines()
    return name, next((n for n, line in enumerate(lines, 1) if case.get("text", "\0") in line), 0)


# ---------------------------------------------------------------- the code

def test_the_verifier_reruns_every_declared_check_itself_and_code_finds_its_part_of_each_planted_violation(env):
    """Done when (#230): it reruns every declared check itself, through the line its kickoff gives; and it flags
    claims with no evidence, proxy evidence, checks that cannot fail and statistics with no independent check.
    Code finds its part of each planted case, each with the change that would replace it. The rerun is the
    verifier's own: the evidence of the work is as it was, and nothing a check printed is shown or kept."""
    project = planted(env)
    folder = project / ".cg-docs" / "evidence" / "2026-11-27-poverty-brief"
    before = sorted(path.name for path in folder.glob("*.json"))
    v = next(v for v in dispatched(env, REPORT, "review") if v["verifier"] == "verification")
    assert v["reads"][-1].endswith("cg/lenses/verification.md")
    line = v["kickoff"].split("Every check of the plan, rerun by code: ")[1].splitlines()[0]
    words = shlex.split(line.replace("\\", "/"))
    assert words[-2:] == ["--project", project.as_posix()] and "<" not in line, line
    code, out = env["cg"](*words[2:-2])
    path = next(name for name in sorted(path.name for path in folder.glob("*.json")) if name not in before)
    path, record = f".cg-docs/evidence/{folder.name}/{path}", json.loads((folder / path).read_text(encoding="utf-8"))
    assert code == 1 and record["kind"] == "rerun" and record["exits"] == [0, 0, 0, 1, 0], out
    assert list(record["checks"]) == ["C1", "C2", "C3", "C4", "C5"] and record["verdict"] == "not verified"
    assert record["checks"]["C4"]["work"]["on"] == "an earlier state of its files" and not record["checks"]["C5"]["work"]
    assert record["checks"]["C3"]["work"]["on"] == "the files as they now are" and "\nC4: exit 1; " in "\n" + out, out
    for case in CASES["review"]:
        found = [f["where"] for f in record["findings"] if f["rule"] == case["code"]]
        assert not case["code"] or any(at(spot, where(project, case)) for spot in found), (case, found)
    assert {f["rule"] for f in record["findings"]} == {r for r in load_cg().VERIFY_RULES}, record["findings"]
    flags = [line for line in out.splitlines() if line.startswith("FLAG ")]
    assert len(flags) == len(record["findings"]) and all(f"; fix: {f['fix']}" in out for f in record["findings"])
    # P12: no line of what a check printed reaches the screen or the record (interval.py prints a sentence).
    assert "the interval has a width" not in out + (project / path).read_text(encoding="utf-8") and "HH-0" not in out
    # The rerun is the verifier's: the work's records are as they were, and the work's verdicts with them.
    assert sorted(p.name for p in folder.glob("*.json") if not p.name.endswith("-rerun.json")) == before
    assert "S2: C2 verified; C4 verified; C5 not run" in env["cg"]("evidence", "--report", REPORT)[1]
    # A finding at the record of the rerun is proof, and so is one at the line of the plan that code named.
    plan_line = next(f["where"] for f in record["findings"] if f["rule"] == "fails")
    assert give(env, REPORT, "review", "verification", "FLAG", "independent", "--finding",
                f"{path}: C4 fails on the files as they now are", "--finding", f"{plan_line}: C4 fails")[0] == 0
    assert [f["where"] for f in held(env, REPORT)[-1]["findings"]] == [path, plan_line]


def test_the_rerun_needs_a_plan_runs_nothing_past_a_stop_and_can_take_one_check(env):
    """The rerun runs only what the human approved with the plan: quick work has no declared check, and the line
    in its kickoff says so; at the plan stage nothing has run. Like every run, it runs nothing while a stop of
    the work waits. One check can be rerun alone, and a check the work ran on the files as they now are is the
    same run."""
    project = start(env)
    assert env["cg"]("tier", *ALL_NO, *SLICE)[0] == 0
    assert "rerun by code: none at this stage" in dispatched(env, PLAN, "plan")[0]["kickoff"]
    code, out, record, _ = rerun(env, WORK)
    rows = [where(project, {"file": PLAN, "text": f"| {cid} |"}) for cid in ("C1", "C2")]
    assert record["exits"] == [0, 3] and [(f["rule"], f["where"]) for f in record["findings"]] == [
        ("not-run", f"{name}:{line}") for name, line in rows], (out, record)
    assert env["cg"]("evidence", "C1", "--report", WORK)[0] == 0
    code, out, record, _ = rerun(env, WORK, "C1")
    assert list(record["checks"]) == ["C1"] and record["checks"]["C1"]["work"]["on"] == "the files as they now are"
    assert record["checks"]["C1"]["work"]["same-output"] and "not-run" not in out, out
    assert env["cg"]("evidence", "--rerun", "--run", f"{PY} check1.py", "--report", WORK)[0] == 2
    assert env["cg"]("tier", *yes("irreversible"), *SLICE)[0] == 0  # on a plan, the one fact that always stops
    code, out, _, _ = rerun(env, WORK)
    assert code == 1 and "refused: this work stops for the human's yes" in out, out
    quick = ".cg-docs/work-reports/2026-11-26-quick.md"
    assert env["cg"]("new", "work-report", "Quick", "--date", "2026-11-26")[0] == 0
    code, out, _, _ = rerun(env, quick)
    assert code == 1 and "names no plan" in out, out
    assert "rerun by code: none: no plan declares a check" in dispatched(env, quick, "review")[0]["kickoff"]
    assert not list((project / ".cg-docs" / "evidence" / "2026-11-26-quick").glob("*-rerun.json"))


def test_the_rules_find_a_check_that_cannot_fail_by_its_shape_and_one_that_rests_on_a_proxy():
    """A command whose exit code is fixed by what follows it, or by a default of the tool, cannot fail: R's
    devtools::test() and rcmdcheck() exit with 0 when a test fails, a pipe ends with its last command, and
    python -O drops every assert. A check that shows only that a file exists, or that code compiles, rests on
    a proxy. Each rule leaves alone the form that can fail."""
    rules = {rule: pattern for rule, part, pattern, fix in load_cg().VERIFY if part == "command"}
    cannot = ['Rscript -e "devtools::test()"', "pytest -q || true", "Rscript tests/run.R | tail -1",
              "make check; echo done", "flake8 --exit-zero .", 'Rscript -e "rcmdcheck::rcmdcheck()"',
              'python -O -c "assert 1"', 'Rscript -e "testthat::test_dir(\'tests\', stop_on_failure = FALSE)"',
              "pytest || echo failed", "true"]
    can = ['Rscript -e "devtools::test(stop_on_failure = TRUE)"', "pytest -q", "python checks/a.py && echo ok",
           'Rscript -e "x <- 1:3 |> head(1); stopifnot(x == 1)"', 'Rscript -e "rcmdcheck::rcmdcheck(error_on = \'warning\')"',
           'python -c "import sys; sys.exit(1)"', "python checks/a.py 2>&1"]
    proxy = ["test -f output/table.csv", "ls output", 'python -c "import os; assert os.path.exists(\'x\')"',
             'Rscript -e "stopifnot(file.exists(\'x\'))"', "python -m py_compile pipeline.py", "R CMD build .",
             "pytest --collect-only"]
    assert [c for c in cannot if not re.search(rules["cannot-fail"], c)] == []
    assert [c for c in can + proxy if re.search(rules["cannot-fail"], c)] == []
    assert [c for c in proxy if not re.search(rules["proxy"], c)] == []
    assert [c for c in cannot[:2] + can if re.search(rules["proxy"], c)] == []


# ---------------------------------------------------------------- the text

def test_the_lens_says_what_code_reruns_what_is_judged_and_asks_what_else_each_number_could_measure():
    """Done when (#230): the lens has the verifier rerun every check through code, names every rule code
    writes, and asks of every reported number what else it could be measuring. It copies the shape of the
    determinism lens, within its 60 lines, and the decision is ADR 0010."""
    text = (CG / "lenses" / "verification.md").read_text(encoding="utf-8")
    front, body = text.split("\n---\n", 1)
    assert len(text.splitlines()) <= 60 and all(f"\n{key}: " in front for key in ("name", "principle", "derived-from"))
    assert "principle: P4" in front and "benchmark-checklist" in front and "principle-explain-the-number" in front
    rules = load_cg().VERIFY_RULES
    assert all(f"`{rule}`" in body for rule in rules), [r for r in rules if f"`{r}`" not in body]
    rows = [line.split("|")[1:-1] for line in body.split("## The flags")[1].split("\n## ")[0].splitlines()
            if line.startswith("| ") and "---" not in line][1:]
    assert len(rows) >= 6 and all(row[3].strip() for row in rows)  # each flag has the change that replaces it
    for words in ("rerun", "no evidence", "proxy", "cannot fail", "independent", "what else it could be measuring",
                  "Every check of the plan, rerun by code", "INCONCLUSIVE", "rule 6", "the line that computes it",
                  "each filter, merge, weight and unit"):  # lens run 1 (#231): trace each number
        assert words in body, words
    assert "{rerun}" in (CG / "templates" / "kickoff.md").read_text(encoding="utf-8")
    p4 = (CG / "principles" / "P04-prove-it-works.md").read_text(encoding="utf-8")
    assert "`cg.py evidence --rerun`" in p4.split("## Deterministic checks")[1]
    assert list((HUB / "docs" / "adr").glob("0010-*.md")) and "the verification verifier" in (HUB / "README.md").read_text()


# ---------------------------------------------------------------- the review of task 2.7

def test_review_of_2_7_a_claim_beside_a_negation_and_r_runs_that_exit_with_0_on_a_failure_are_found():
    """Review of #230. `unrecorded` skipped a line with any word of negation, so "C5 passes, and no share lies
    outside 0 and 1" was no claim. `cannot-fail` missed testthat::test_file() and a test run inside try() or a
    tryCatch() that stops nothing, which exit with 0 when a test fails (testthat 3.3). `proxy` missed a check
    that only loads code or searches a test file, and named one that tests a file exists and then its value."""
    rules = {rule: pattern for rule, part, pattern, fix in load_cg().VERIFY if part in ("command", "report")}
    claims = ["- C5 passes, and no share lies outside 0 and 1.", "- C5 is not yet run, but C2 passes.",
              "- C4 fails; C5 passes.", "- C5 passed without an error."]
    negated = ["- C5 does not pass yet.", "- C5 has not passed.", "- C5 didn't pass.", "- C5 failed to pass.",
               "- C5 never passed.", "- C5 is not verified.", "- No run of C5 passed.", "| C5 | a share outside 0 and 1 |"]
    assert [c for c in claims if not re.search(rules["unrecorded"], c, re.I)] == []
    assert [c for c in negated if re.search(rules["unrecorded"], c, re.I)] == []
    # Lens run 1 (#231): a claim of success or validation that names no check is found too, by the same shape.
    claims = ["- The headcount ratio matches the figure the survey report publishes.", "- The table was validated "
              "against the census.", "- The interval reproduces the published one, and agrees with Stata."]
    assert [c for c in claims if not re.search(rules["unbacked"], c, re.I)] == [] and rules["unbacked"] == rules[
        "unrecorded"] and not re.search(rules["unbacked"], "- The share was not validated against a source.", re.I)
    cannot = ['Rscript -e "testthat::test_file(\'tests/testthat/test-gap.R\')"',
              'Rscript -e "library(testthat); test_file(\'tests/testthat/test-gap.R\')"',
              'Rscript -e "try(testthat::test_dir(\'tests\'))"',
              'Rscript -e "tryCatch(testthat::test_dir(\'tests\'), error = function(e) NULL)"']
    can = ['Rscript -e "testthat::test_file(\'tests/testthat/test-gap.R\', stop_on_failure = TRUE)"',
           'Rscript -e "tryCatch(testthat::test_dir(\'tests\'), error = function(e) stop(\'failed\'))"',
           'Rscript -e "devtools::check()"', 'Rscript -e "testthat::test_dir(\'tests\')"']
    assert [c for c in cannot if not re.search(rules["cannot-fail"], c)] == []
    assert [c for c in can if re.search(rules["cannot-fail"], c)] == []
    proxy = ['python -c "import pipeline"', 'Rscript -e "devtools::load_all()"', "Rscript -e \"library(toy)\"",
             "Rscript -e \"source('R/headcount.R')\"", "grep -q expect_equal tests/testthat/test-headcount.R"]
    sound = ["test -f output/table.csv && python checks/value.py", "[ -s output/ci.csv ] && python checks/interval.py",
             'Rscript -e "devtools::load_all(); stopifnot(abs(headcount(x) - 0.153846) < 1e-6)"',
             'python -c "import sys; sys.exit(1)"', "grep -q North output/table.csv"]
    assert [c for c in proxy if not re.search(rules["proxy"], c)] == []
    assert [c for c in sound if re.search(rules["proxy"], c)] == []


def test_review_of_2_7_each_lens_has_the_verifier_account_for_every_finding_of_code():
    """Item 46 of the handoff: two agents missed a finding that repro had named. Each lens has the verifier
    account for every finding of code: a finding of its own, or a line of its note with the reason."""
    for name, part in (("determinism", "## What code found"), ("verification", "## First, rerun the checks")):
        text = (CG / "lenses" / f"{name}.md").read_text(encoding="utf-8")
        section = text.split(part)[1].split("\n## ")[0]
        assert "Account for each" in section and "set it aside" in section and "your note" in section, name
        assert name == "determinism" or "open no output to read its values (rule 6)" in text  # P12, review of #230
        assert len(text.splitlines()) <= 60, name


def test_review_of_2_7_only_the_verification_verifier_runs_the_rerun_line_of_its_kickoff():
    """V18 of the review of #230: every verifier at the review stage gets the rerun line, and nothing told the other
    eight to leave it. The kickoff says that the verifier `verification` alone runs it, and the others read its record."""
    text = (CG / "templates" / "kickoff.md").read_text(encoding="utf-8")
    rest = text.split("Every check of the plan, rerun by code: {rerun}\n")[1].splitlines()[0]
    assert "Only the verifier `verification` runs the line above" in rest and "reads the record" in rest, rest
