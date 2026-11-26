"""Tests for the artifact schema, the version 1 reader, and `cg.py validate`,
`approve` and `tier` (task 2.1, #224).

Each test runs the installed copy of cg.py against a project in a temporary
folder. git reads its identity from a file in the temporary home, so the
machine's own identity is never read.
"""
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

HUB = Path(__file__).resolve().parents[2]
CG = HUB / "packs" / "core" / "cg"
TYPES = {"intent": "brainstorms", "plan": "plans", "work-report": "work-reports",
         "review": "reviews", "decision": "decisions", "solution": "solutions"}
CLEAN = "schema-2: 1\nversion-1: 0 (read as they are)\nproblems: 0\nwarnings: 0\n"
FACTS = ["number", "personal", "irreversible", "interface", "choice", "no-check"]
ALL_NO = [arg for name in FACTS for arg in ("--fact", f"{name}=no")]
RULES = {"data": {"inst/extdata/survey.csv": "Public", "data": "Official Use Only",
                  "data/raw": "Confidential", "data/raw/codebook.csv": "public"},
         "approved-tools": {"Claude Code": "Official Use Only"},
         "classification-levels": ["Public", "Official Use Only", "Confidential"]}
PLAN_BODY = """
# Headcount

## Contract

### Goal

headcount() returns the weighted share of households below the line.

### Out of scope

Other poverty measures.

### Requirements

| ID | Requirement |
|---|---|
| R1 | headcount() uses the household weights |
| R2 | headcount() stops on a missing weight |

### Checks

| ID | Requirement | Command | Fails when |
|---|---|---|---|
| C1 | R1 | `Rscript -e "devtools::test()" | tail -1` | the share differs from 0.153846 |
| C2 | R2 | `Rscript tests/missing-weight.R` | no error is raised |

### Boundaries

- Always: run both checks.
- Ask first: a new dependency.
- Never: print rows of the survey.

## Data register

| Dataset | Classification | Source | Version | Owner | Permitted use |
|---|---|---|---|---|---|
| inst/extdata/survey.csv | Public | synthetic | 1 | the team | any |

## Slices

| Slice | What it delivers | Files | Checks | By code or by judgement |
|---|---|---|---|---|
| S1 | headcount() | R/headcount.R | C1, C2 | by code: R/headcount.R |
"""
# The decided intent every plan in these tests is built on, and the one data rule its register needs.
IDEA = ".cg-docs/brainstorms/2026-11-20-headcount.md"
INTENT_BODY = """
# Top-coded incomes in the welfare aggregate

## Goal

Decide how the welfare aggregate treats top-coded incomes, so that the Gini of the 2019 wave can be compared with 2016.

## Out of scope

The 2016 wave is not estimated again.

## A wrong result

A Gini that moves by more than its standard error when only the threshold of the rule moves.

## Facts

| Fact | Source |
|---|---|
| Households with a missing weight are dropped | `R/welfare.R:41` |
| The survey report gives a Gini of 0.41 for 2019 | the survey report, table 3.2 |

## Decisions

| ID | Decision | Recommended answer, with its trade-off | The human's answer |
|---|---|---|---|
| D1 | Which rule replaces the top-coded values | A Pareto tail above the 99th percentile; it adds a threshold to choose | Yes, the Pareto tail. |
| D2 | Which approach goes to the plan | The Pareto tail as one new function; the other approach changes nothing | The new function. |

## Assumptions

- The 2016 wave was not adjusted. If it was, no rule here makes the two waves comparable.

## Approaches considered

| Approach | What it costs | What it risks |
|---|---|---|
| Leave the values as they are | nothing | a Gini that is biased down |
| A Pareto tail above the 99th percentile | one new function and its check | a result that depends on the threshold |
"""


def front(kind, status, extra=""):
    extra = (f"intent: {IDEA}\n" if kind == "plan" else "") + extra
    return f'---\ntype: {kind}\nschema: 2\ntitle: "Headcount"\ndate: 2026-11-25\nstatus: {status}\n{extra}---\n'


@pytest.fixture
def env(tmp_path):
    home, project = tmp_path.resolve() / "home", tmp_path.resolve() / "project"
    shutil.copytree(CG, home / ".agents" / "skills" / "cg", ignore=shutil.ignore_patterns("__pycache__"))
    project.mkdir()
    (home / ".gitconfig").write_text("[user]\n\tname = Test Human\n\temail = human@example.org\n")
    environ = dict(os.environ, HOME=str(home), USERPROFILE=str(home),
                   GIT_CONFIG_GLOBAL=str(home / ".gitconfig"), GIT_CONFIG_NOSYSTEM="1")

    def cg(*args):
        done = subprocess.run([sys.executable, str(home / ".agents" / "skills" / "cg" / "scripts" / "cg.py"),
                               *args, "--project", str(project)], capture_output=True, text=True, env=environ)
        return done.returncode, done.stdout + done.stderr

    def base():
        """What a plan is built on (#226): a decided intent, and a recorded rule for its dataset."""
        if not (project / IDEA).exists():
            put("intent", front("intent", "draft") + INTENT_BODY, Path(IDEA).name)
            assert cg("approve", IDEA, "--reply", "Yes.")[0] == 0
            if not (project / ".cg-docs" / "config.json").exists():
                config(data={"inst/extdata/survey.csv": "Public"})

    def put(kind, text, name="2026-11-25-headcount.md"):
        if kind == "plan":
            base()
        path = project / ".cg-docs" / TYPES[kind] / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def config(**keys):
        (project / ".cg-docs").mkdir(exist_ok=True)
        (project / ".cg-docs" / "config.json").write_text(json.dumps({"packs": ["core"], **keys}))

    def plan_records():
        return sorted((project / ".cg-docs" / "approvals").glob("2026-11-25-headcount.*.json"))

    def proved(report):
        """What a completed work report rests on since task 2.4 (#227): the risk code computed, and a verified check."""
        assert cg("tier", *ALL_NO, "--touches", "R/a.R", "--reads", "none", "--report", str(report))[0] == 0
        assert cg("evidence", "--run", f'"{sys.executable}" -c "print(1)"', "--report", str(report))[0] == 0

    return {"home": home, "project": project, "cg": cg, "put": put, "config": config, "base": base,
            "plan-records": plan_records, "proved": proved}


def load_cg():
    sys.path.insert(0, str(CG / "scripts"))
    import cg
    return cg


def digest(folder: Path) -> str:
    found = hashlib.sha256()
    for path in sorted(p for p in folder.rglob("*") if p.is_file()):
        found.update(path.relative_to(folder).as_posix().encode() + path.read_bytes())
    return found.hexdigest()


# ---------------------------------------------------------------- the reader

def test_frontmatter_is_text_and_one_line_lists_and_names_what_is_nested():
    fields, body, problems = load_cg().read_frontmatter(
        '---\ntitle: "A: b #1"\nstatus: draft   # note\ntags: [poverty, "a, b"]\nempty:\n---\n\n# Body\n')
    assert fields == {"title": "A: b #1", "status": "draft", "tags": ["poverty", "a, b"], "empty": ""}
    assert body.strip() == "# Body" and problems == []
    fields, _, problems = load_cg().read_frontmatter(
        "---\nphases:\n  - one\n  - two\nfindings:\n  p0: 1\nmap: {a: 1}\nstatus: done\nstatus: open\nstray\n---\n")
    assert fields["phases"] == ["one", "two"] and fields["findings"] == ["p0: 1"]
    for words in ("'phases' holds a nested block", "'findings' holds a nested block", "'map' holds a map",
                  "'status' appears twice", "line 10: not a 'key: value' line"):
        assert any(words in line for line in problems), (words, problems)
    assert load_cg().read_frontmatter("# No block\n")[2] and load_cg().read_frontmatter("---\na: b\n")[2]


def test_a_version_1_folder_is_read_without_conversion(env):
    """Done when (#224): an existing version 1 folder is read as it is. These are
    the shapes found in a real one: one-line lists, nested findings, a quoted
    status, a status the reader does not know, a file with no frontmatter, and
    solutions kept in a folder per category."""
    env["put"]("plan", '---\ntitle: "Old"\nstatus: "active"\ntags: [a, b]\nphases:\n  - one\n---\n', "2026-03-01-old.md")
    env["put"]("plan", "---\nstatus: completed\\ncompleted-date: 2026-06-01\n---\n", "2026-03-02-odd.md")
    env["put"]("intent", "---\nstatus: decided\nchosen-approach: b\n---\n", "2026-02-01-idea.md")
    env["put"]("review", "---\ntype: review\nfindings:\n  p0: 0\n  p1: 2\n---\n", "2026-03-03-review.md")
    env["put"]("work-report", "# Notes with no frontmatter\n", "notes.md")
    env["put"]("solution", '---\ntype: "bug"\ncategory: weights\n---\n', "data-quality/2026-01-01-fix.md")
    before = digest(env["project"])
    for flags in ((), ("--strict",)):
        code, out = env["cg"]("validate", *flags)
        assert code == 0 and "version-1: 6 (read as they are)" in out and "FAIL" not in out, out
    state = json.loads(env["cg"]("status", "--json")[1])
    assert state["active"] == ".cg-docs/plans/2026-03-01-old.md" and state["open-artifacts"] == 1
    assert digest(env["project"]) == before


def test_the_version_1_artifacts_of_this_repository_are_read():
    folder = HUB / ".cg-docs"
    before = digest(folder / "plans")
    done = subprocess.run([sys.executable, str(CG / "scripts" / "cg.py"), "validate", "--json", "--project", str(HUB)],
                          capture_output=True, text=True)
    found = json.loads(done.stdout)
    assert done.returncode == 0 and found["problems"] == 0, done.stdout[-2000:]
    assert found["version-1"] > 600 and digest(folder / "plans") == before


def test_status_reads_both_schemas(env):
    env["put"]("plan", front("plan", "draft") + PLAN_BODY)
    env["put"]("review", front("review", "open") + "\n## Findings\n\nNone.\n\n## Not checked\n\nNothing.\n")
    env["put"]("work-report", front("work-report", "wrong"), "2026-11-24-typo.md")
    env["put"]("plan", "---\nstatus: draft\n---\n", "2026-01-01-old.md")
    env["put"]("intent", front("intent", "decided"))
    state = json.loads(env["cg"]("status", "--json")[1])
    assert state["open-artifacts"] == 4  # the decided intent is closed; a status nobody defined stays in view
    # A status typed into an intent is not the human's yes (#225), so it waits on them all the same.
    assert state["waiting-on-human"] == [".cg-docs/reviews/2026-11-25-headcount.md (status open)",
                                         ".cg-docs/plans/2026-11-25-headcount.md (status draft)",
                                         ".cg-docs/plans/2026-01-01-old.md (status draft)",
                                         ".cg-docs/brainstorms/2026-11-25-headcount.md "
                                         "(status decided, not approved as it now reads)"]


# ---------------------------------------------------------------- the schema and validate

def test_every_type_has_a_template_that_meets_the_schema_and_still_asks_to_be_filled(env):
    env["base"]()  # a plan is made on a decided intent (#226), which is the seventh artifact below
    for kind in TYPES:
        more = ["--intent", IDEA] if kind == "plan" else []
        assert env["cg"]("new", kind, "Headcount", "--date", "2026-11-25", *more)[0] == 0
    code, out = env["cg"]("validate")
    assert code == 0 and "schema-2: 7\nversion-1: 0 (read as they are)\nproblems: 0\nwarnings: 6\n" in out, out
    assert out.count("the template's text is still in it") == 6 and "PLACEHOLDER" not in out
    code, out = env["cg"]("validate", "--strict")
    assert code == 1 and out.count("FAIL") == 6, out


def test_validate_passes_a_filled_plan_and_names_each_break_of_the_schema(env):
    good = front("plan", "draft") + PLAN_BODY
    path = env["put"]("plan", good)
    assert env["cg"]("validate", "--strict", PLAN) == (0, CLEAN)
    breaks = [
        (good.replace("status: draft", "status: done"), "status is done; a plan is one of: draft, approved"),
        (good.replace("type: plan", "type: review"), "type is review, but plans/ holds plan artifacts"),
        (good.replace("date: 2026-11-25", "date: 25 Nov"), "date is not YYYY-MM-DD"),
        (good.replace('title: "Headcount"\n', ""), "the key 'title' is missing or empty"),
        (good.replace("schema: 2", "schema: 3"), "a higher number needs a newer core"),
        (good.replace("status: draft\n", "status: draft\nsteps:\n  - one\n"), "'steps' holds a nested block"),
        (good.replace(IDEA, ".cg-docs/brainstorms/none.md"), "intent: no such file"),
        (good.replace("### Boundaries", "### Limits"), "the section '### Boundaries' is missing"),
        (good.replace("## Data register", "## Data"), "the section '## Data register' is missing"),
        (good.replace("| C2 | R2 |", "| C2 | R1 |"), "requirement R2 has no check"),
        (good.replace("| C2 | R2 |", "| C2 | R7 |"), "check C2 names R7, which the Requirements table does not hold"),
        (good.replace("`Rscript tests/missing-weight.R`", ""), "check C2 has no command"),
        (good.replace("| no error is raised |", "| |"), "check C2 does not say which outcome means failure"),
        (good.replace("| C2 |", "| C1 |"), "the ID C1 appears twice"),
        (good.replace("| R2 | headcount", "| second | headcount"), "'second' is not an ID such as R1"),
    ]
    for text, words in breaks:
        path.write_text(text, encoding="utf-8")
        code, out = env["cg"]("validate")
        assert code == 1 and words in out and "Traceback" not in out, (words, out)
    path.write_text(good.replace("status: draft\n", "status: draft\nestimated-effort: 2h\n"), encoding="utf-8")
    code, out = env["cg"]("validate")
    assert code == 0 and "warn .cg-docs/plans/2026-11-25-headcount.md: the key 'estimated-effort' is not part of schema 2" in out
    assert env["cg"]("validate", "--strict", PLAN)[0] == 1


def test_template_text_left_in_a_record_is_a_warning_while_open_and_a_failure_once_completed(env):
    """Quick work marks a work report completed (step 5); code refuses that while a
    part of the template is still unfilled."""
    env["cg"]("new", "work-report", "Fix the label", "--date", "2026-11-25")
    path = env["project"] / ".cg-docs" / "work-reports" / "2026-11-25-fix-the-label.md"
    assert env["cg"]("validate", ".cg-docs/work-reports/2026-11-25-fix-the-label.md")[0] == 0
    path.write_text(path.read_text().replace("status: in-progress", "status: completed"))
    code, out = env["cg"]("validate", str(path))
    assert code == 1 and "the template's text is still in it, first: <the request" in out, out
    filled = "\n".join("filled in" if "<" in line else line for line in path.read_text().splitlines())
    path.write_text(filled)
    env["proved"](path)
    assert env["cg"]("validate", str(path)) == (0, CLEAN)


def test_validate_refuses_a_file_that_is_no_artifact_and_an_accepted_decision_naming_nobody(env):
    (env["project"] / "README.md").write_text("# Project\n")
    code, out = env["cg"]("validate", "README.md")
    assert code == 2 and "not an artifact of this project: README.md" in out
    body = "\n## Decision\n\nWeights are household weights, not person weights, because the survey samples households.\n"
    path = env["put"]("decision", front("decision", "accepted", "decided-by:\n") + body)
    code, out = env["cg"]("validate")
    assert code == 1 and "an accepted decision names the person who decided" in out
    path.write_text(front("decision", "accepted", "decided-by: Test Human\n") + body)
    assert env["cg"]("validate")[0] == 0


# ---------------------------------------------------------------- approve

PLAN = ".cg-docs/plans/2026-11-25-headcount.md"


def test_approve_stores_the_reply_the_identity_the_time_and_the_hash(env):
    """Done when (#224)."""
    path = env["put"]("plan", front("plan", "draft") + PLAN_BODY)
    reply = 'Yes,  "approved".\nThank you.'  # stored as written, marks and line end included
    code, out = env["cg"]("approve", PLAN, "--reply", reply)
    assert code == 0 and f"approved {PLAN}" in out and "by: Test Human <human@example.org>" in out, out
    records = env["plan-records"]()
    assert len(records) == 1
    record = json.loads(records[0].read_text(encoding="utf-8"))
    assert record["reply"] == reply and record["artifact"] == PLAN
    assert (record["name"], record["email"]) == ("Test Human", "human@example.org")
    assert re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ", record["time"])
    assert record["hash"] == load_cg().text_hash(PLAN_BODY) and re.fullmatch(r"sha256:[0-9a-f]{64}", record["hash"])
    assert "status: approved" in path.read_text() and path.read_text().endswith(PLAN_BODY)
    assert env["cg"]("validate", "--strict")[0] == 0
    state = json.loads(env["cg"]("status", "--json")[1])
    assert state["active"] == PLAN and state["waiting-on-human"] == []
    before = digest(env["project"])
    code, out = env["cg"]("approve", PLAN, "--reply", reply)
    assert code == 0 and "already approved" in out and digest(env["project"]) == before


def test_approve_refuses_what_is_not_a_clear_yes_and_what_cannot_be_approved(env):
    path = env["put"]("plan", front("plan", "draft") + PLAN_BODY)
    for reply in ("Sounds good.", "whatever you think", "Sure, go on!", "  "):
        code, out = env["cg"]("approve", PLAN, "--reply", reply)
        assert code == 1 and "refused" in out and "status: draft" in path.read_text(), (reply, out)
    path.write_text(front("plan", "draft") + PLAN_BODY.replace("| C2 | R2 |", "| C2 | R1 |"))
    code, out = env["cg"]("approve", PLAN, "--reply", "Yes, approved.")
    assert code == 1 and "requirement R2 has no check" in out
    env["cg"]("new", "plan", "Unfilled", "--date", "2026-11-25", "--intent", IDEA, "--other-work")
    code, out = env["cg"]("approve", ".cg-docs/plans/2026-11-25-unfilled.md", "--reply", "Yes, approved.")
    assert code == 1 and "the template's text is still in it" in out
    path.write_text(front("plan", "completed") + PLAN_BODY)
    code, out = env["cg"]("approve", PLAN, "--reply", "Yes, approved.")
    assert code == 1 and "its status is completed" in out
    path.write_text("---\nstatus: draft\n---\n" + PLAN_BODY)
    assert "a version 1 plan" in env["cg"]("approve", PLAN, "--reply", "Yes, approved.")[1]
    env["put"]("review", front("review", "open"))
    code, out = env["cg"]("approve", ".cg-docs/reviews/2026-11-25-headcount.md", "--reply", "Yes.")
    assert code == 2 and "not a plan or an intent of this project" in out
    path.write_text(front("plan", "draft") + PLAN_BODY)
    (env["home"] / ".gitconfig").write_text("")
    code, out = env["cg"]("approve", PLAN, "--reply", "Yes, approved.")
    assert code == 1 and "git has no user.name" in out
    assert env["plan-records"]() == [] and len(list((env["project"] / ".cg-docs" / "approvals").iterdir())) == 1


def test_a_change_to_an_approved_plan_needs_a_new_approval_and_the_first_one_stays(env):
    """P1: a change to the contract is an amendment the human approves."""
    path = env["put"]("plan", front("plan", "draft") + PLAN_BODY)
    env["cg"]("approve", PLAN, "--reply", "Yes, approved.")
    approved = path.read_text()
    # A sync or an editor that changes line ends or trailing spaces does not void the approval.
    path.write_bytes(approved.replace("\n", "  \r\n").encode() + b"\r\n\r\n")
    assert env["cg"]("validate")[0] == 0
    path.write_text(approved.replace("status: approved", "status: in-progress").replace("0.153846", "0.25"))
    code, out = env["cg"]("validate")
    assert code == 1 and "no approval is recorded for the plan as it now reads" in out
    state = json.loads(env["cg"]("status", "--json")[1])
    assert state["waiting-on-human"] == [f"{PLAN} (status in-progress, not approved as it now reads)"]
    with path.open("a") as plan:  # a change to an approved plan is an amendment, and says so (#226)
        plan.write("\n## Amendments\n\n- 2026-11-26: the expected share is 0.25, from the survey report.\n")
    code, out = env["cg"]("approve", PLAN, "--reply", "OK, approved.")
    assert code == 0 and "status: in-progress" in path.read_text(), out
    records = [json.loads(p.read_text()) for p in env["plan-records"]()]
    assert sorted(r["reply"] for r in records) == ["OK, approved.", "Yes, approved."]
    assert env["cg"]("validate")[0] == 0


def test_a_status_typed_into_a_plan_is_not_an_approval(env):
    env["put"]("plan", front("plan", "approved") + PLAN_BODY)
    code, out = env["cg"]("validate")
    assert code == 1 and "no approval is recorded" in out
    assert json.loads(env["cg"]("status", "--json")[1])["waiting-on-human"]


# ---------------------------------------------------------------- tier

def test_tier_is_low_when_every_fact_is_no_and_no_data_is_read(env):
    env["config"]()
    out = env["cg"]("tier", *ALL_NO, "--touches", "R/plot.R", "--reads", "none")
    assert out == (0, "tier: low\nreasons: none\ndata: none\nfiles: 1\n")
    assert out == env["cg"]("tier", *ALL_NO, "--touches", "R/plot.R", "--reads", "none")


def test_each_declared_yes_raises_the_tier(env):
    """Done when (#224): the tier comes from declared facts. `number` covers an
    estimate, a weight and a published output; `interface` a schema; `irreversible` a deletion."""
    env["config"]()
    for name in FACTS:
        facts = [arg for other in FACTS for arg in ("--fact", f"{other}={'yes' if other == name else 'no'}")]
        code, out = env["cg"]("tier", *facts, "--touches", "R/plot.R", "--reads", "none")
        assert code == 0 and out.startswith(f"tier: elevated\nreasons: {name}: "), (name, out)
    state = json.loads(env["cg"]("tier", *ALL_NO, "--touches", "a.R", "--reads", "none", "--json")[1])
    assert state["tier"] == "low" and state["facts"] == {name: "no" for name in FACTS}


def test_tier_takes_no_opinion_every_fact_is_declared(env):
    code, out = env["cg"]("tier", "--fact", "number=no", "--touches", "a.R", "--reads", "none")
    assert code == 2 and all(f"--fact {name}=" in out for name in FACTS[1:]) and "tier:" not in out
    for args, words in ((ALL_NO + ["--fact", "size=no"], "'size' is not a fact"),
                        (ALL_NO[:-1] + ["no-check=maybe"], "no-check must be yes or no"),
                        (ALL_NO + ["--fact", "number=yes", "--touches", "a.R", "--reads", "none"], "more than once"),
                        (ALL_NO + ["--reads", "none"], "--touches"),
                        (ALL_NO + ["--touches", "a.R"], "--reads"),
                        (ALL_NO + ["--touches", "a.R", "--reads", "none", "--reads", "d.csv"], "--reads none"),
                        (ALL_NO + ["--touches", "a.R", "--reads", "d.csv"], "--agent")):
        code, out = env["cg"]("tier", *args)
        assert code == 2 and words in out and "tier:" not in out and "Traceback" not in out, (args, out)
    # A project with no config has no data rule, so no data file is cleared in it.
    code, out = env["cg"]("tier", *ALL_NO, "--touches", "a.R", "--reads", "d.csv", "--agent", "Codex")
    assert code == 0 and out.startswith("tier: elevated\nreasons: data: d.csv is not cleared for Codex\n"), out


def test_tier_counts_the_files(env):
    env["config"]()
    files = [arg for n in range(6) for arg in ("--touches", f"R/f{n}.R")]
    code, out = env["cg"]("tier", *ALL_NO, *files, "--reads", "none")
    assert "tier: elevated\nreasons: size: the change touches 6 files, more than 5\n" in out and "files: 6" in out
    assert env["cg"]("tier", *ALL_NO, *files[:10], "--reads", "none")[1].startswith("tier: low")


def test_tier_clears_a_data_file_only_from_the_recorded_rules(env):
    """Gate M1 (#223): two agents read the data line of the risk table differently.
    Code decides it now, and a rule may name a folder (decision 3 of the gate)."""
    env["config"](**RULES)

    def data(path, agent="Claude Code"):
        code, out = env["cg"]("tier", *ALL_NO, "--touches", "R/a.R", "--reads", path, "--agent", agent, "--json")
        state = json.loads(out)
        assert code == 0 and (state["tier"] == "low") == state["data"][0]["cleared"], out
        return state["data"][0]["cleared"], state["data"][0]["why"]

    assert data("inst/extdata/survey.csv") == (True, "its level is Public")
    assert data("./inst/extdata/survey.csv", agent="Some Agent")[0] is True
    assert data("inst/extdata/other.csv") == (False, "no classification is recorded for it")
    assert data("data/clean/pov.dta") == (True, "Claude Code may read Official Use Only")
    assert data("data\\clean\\pov.dta", agent="claude code")[0] is True
    assert data("data/raw/hh.dta") == (False, "its level is Confidential, above what Claude Code may read (Official Use Only)")
    assert data("data/raw/codebook.csv")[0] is True  # the rule for the file wins over its folder's
    assert data("data/clean/pov.dta", agent="Codex") == (False, "its level is Official Use Only, and no level is recorded for Codex")
    assert data(str(env["project"] / "data" / "clean" / "pov.dta"))[0] is True
    assert data("../elsewhere/survey.csv")[0] is False
    env["config"](**{"data": {"d.csv": "Internal"}, "approved-tools": {"Codex": "Restricted"}})
    assert data("d.csv", agent="Codex") == (False, "its level is Internal, and classification-levels does not rank it "
                                                   "against what Codex may read (Restricted)")
    code, out = env["cg"]("tier", *ALL_NO, "--touches", "a.R", "--reads", "d.csv", "--reads", "x.csv", "--agent", "Codex")
    assert "reasons: data: d.csv is not cleared for Codex; data: x.csv is not cleared for Codex\n" in out
    assert "data: d.csv=Internal: not cleared (" in out and "; x.csv: not cleared (no classification" in out


def test_tier_stops_on_data_rules_of_the_wrong_shape(env):
    env["config"](**{"data": ["survey.csv"]})
    code, out = env["cg"]("tier", *ALL_NO, "--touches", "a.R", "--reads", "none")
    assert code == 1 and "data must map file paths to a classification level" in out and "tier:" not in out


# ---------------------------------------------------------------- the human's decision on data

def test_the_human_may_decide_that_an_agent_reads_a_file_that_is_not_cleared(env):
    """The maintainer's rule of 2026-11-25 (#224): the human answers for the data.
    A file that is not cleared stops the work once, for their decision. Once code
    holds that decision, tier names it on every run and no longer stops."""
    env["config"](**RULES)
    reads = ["--touches", "R/a.R", "--reads", "data/raw/hh.dta", "--agent", "Claude Code"]
    why = "its level is Confidential, above what Claude Code may read (Official Use Only)"
    assert env["cg"]("tier", *ALL_NO, *reads)[1].startswith("tier: elevated\nreasons: data: data/raw/hh.dta is not cleared")
    reply = "Yes, read it."
    code, out = env["cg"]("approve", "--reads", "data/raw/hh.dta", "--agent", "Claude Code", "--reply", reply)
    assert code == 0 and "Test Human <human@example.org>" in out and why in out, out
    files = sorted((env["project"] / ".cg-docs" / "approvals").glob("*.json"))
    assert len(files) == 1 and files[0].name.startswith("data.")
    record = json.loads(files[0].read_text(encoding="utf-8"))
    assert re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ", record.pop("time"))
    assert record == {"reads": "data/raw/hh.dta", "agent": "Claude Code", "level": "Confidential",
                      "reply": reply, "name": "Test Human", "email": "human@example.org"}
    code, out = env["cg"]("tier", *ALL_NO, *reads)
    assert code == 0 and out.startswith(f"tier: low\nreasons: none\ndata: data/raw/hh.dta=Confidential: not cleared "
                                        f"({why}); read on the decision of Test Human, 2"), out
    item = json.loads(env["cg"]("tier", *ALL_NO, *reads, "--json")[1])["data"][0]
    assert item["cleared"] is False and item["decision"]["reply"] == reply
    assert "data/raw/hh.dta (Claude Code, Test Human, 2" in env["cg"]("status")[1].split("data-decisions: ")[1]
    # Recorded again, it changes nothing.
    before = digest(env["project"])
    code, out = env["cg"]("approve", "--reads", "data/raw/hh.dta", "--agent", "claude code", "--reply", "Yes.")
    assert code == 0 and "already recorded" in out and digest(env["project"]) == before


def test_a_decision_on_data_holds_for_one_agent_one_place_and_one_level(env):
    env["config"](**RULES)

    def tier(path, agent="Claude Code"):
        return env["cg"]("tier", *ALL_NO, "--touches", "R/a.R", "--reads", path, "--agent", agent)[1].split("\n")[0]

    env["cg"]("approve", "--reads", "data/raw", "--agent", "Claude Code", "--reply", "Yes.")
    assert tier("data/raw/hh.dta") == tier("data/raw/2024/hh.dta") == "tier: low"  # a folder covers what is under it
    assert tier("data/raw/hh.dta", agent="Codex") == "tier: elevated"
    assert tier("data/rawer/hh.dta", agent="Codex") == tier("inst/extdata/other.csv") == "tier: elevated"
    # The decision was for Confidential data. A new level asks for a new decision.
    env["config"](**{**RULES, "data": {**RULES["data"], "data/raw": "Strictly Confidential"}})
    assert tier("data/raw/hh.dta") == "tier: elevated"
    # A file with no classification can be decided on too, and stays covered only while it has none.
    env["cg"]("approve", "--reads", "inst/extdata/other.csv", "--agent", "Codex", "--reply", "Yes.")
    assert tier("inst/extdata/other.csv", agent="Codex") == "tier: low"
    assert tier("inst/extdata/other.csv") == "tier: elevated"


def test_a_decision_on_data_is_refused_without_a_clear_yes_and_not_needed_for_a_cleared_file(env):
    env["config"](**RULES)
    records = env["project"] / ".cg-docs" / "approvals"
    ask = ["approve", "--reads", "data/raw/hh.dta", "--agent", "Claude Code", "--reply"]
    for reply in ("Sounds good.", "whatever you think", "Sure, go on!", "  "):
        code, out = env["cg"](*ask, reply)
        assert code == 1 and "refused" in out and not records.exists(), (reply, out)
    code, out = env["cg"]("approve", "--reads", "data/clean/pov.dta", "--agent", "Claude Code", "--reply", "Yes.")
    assert code == 0 and "nothing to record" in out and not records.exists(), out
    for args, words in ((["approve", "--reads", "data/raw/hh.dta", "--reply", "Yes."], "--agent"),
                        (["approve", "--reply", "Yes."], "or --reads with the data"),
                        (["approve", PLAN, "--reads", "data/raw/hh.dta", "--agent", "Codex", "--reply", "Yes."],
                         "or --reads with the data")):
        code, out = env["cg"](*args)
        assert code == 2 and words in out and "Traceback" not in out and not records.exists(), (args, out)
    (env["home"] / ".gitconfig").write_text("")
    code, out = env["cg"](*ask, "Yes, read it.")
    assert code == 1 and "git has no user.name" in out and not records.exists()
    env["config"](**{"data": ["survey.csv"]})
    code, out = env["cg"](*ask, "Yes, read it.")
    assert code == 1 and "data must map file paths" in out


# ---------------------------------------------------------------- review of task 2.1 by Opus 5.5 (#224)

def test_a_rule_or_a_decision_for_the_project_root_covers_nothing_outside_the_project(env):
    """Finding 1: "." is the project. A file reached with ../ or an absolute path is not in it."""
    outside = ["../other/salaries.csv", str(env["project"].parent / "hr.csv")]

    def tier(*paths):
        reads = [arg for path in paths for arg in ("--reads", path)]
        return json.loads(env["cg"]("tier", *ALL_NO, "--touches", "R/a.R", *reads, "--agent", "Kilo", "--json")[1])

    env["config"](data={".": "Public"})
    state = tier("data/x.csv", *outside)
    assert [d["cleared"] for d in state["data"]] == [True, False, False] and state["tier"] == "elevated", state
    env["config"]()
    assert env["cg"]("approve", "--reads", ".", "--agent", "Kilo", "--reply", "Yes.")[0] == 0
    state = tier("data/x.csv", *outside)
    assert [bool(d["decision"]) for d in state["data"]] == [True, False, False] and state["tier"] == "elevated", state


def test_a_folder_that_is_read_is_held_to_each_rule_below_it(env):
    """Finding 2: reading a folder reads the files in it, so a file with its own,
    stricter rule is not cleared, or covered by a decision, because its folder is."""
    env["config"](data={"data": "Public", "data/hr.csv": "Confidential"})

    def tier(path):
        return json.loads(env["cg"]("tier", *ALL_NO, "--touches", "R/a.R", "--reads", path, "--agent", "Kilo",
                                    "--json")[1])

    state = tier("data")
    assert state["tier"] == "elevated" and "data: data/hr.csv is not cleared for Kilo" in state["reasons"], state
    assert tier(".")["tier"] == "elevated"
    env["config"](data={"data": "Internal", "data/hr.csv": "Confidential"})
    env["cg"]("approve", "--reads", "data", "--agent", "Kilo", "--reply", "Yes.")
    assert tier("data/x.csv")["tier"] == "low"
    assert tier("data")["tier"] == "elevated"  # the decision was for Internal; hr.csv is Confidential


def test_a_reply_that_says_no_is_never_recorded_as_a_yes(env):
    """Finding 3: "a reply that is not a clear yes writes nothing" (HANDOFF, task 2.1)."""
    env["config"](**RULES)
    path = env["put"]("plan", front("plan", "draft") + PLAN_BODY)
    for reply in ("No.", "no, not yet", "Not yet", "Don't read it", "do not", "Wait", "Stop.", "Cancel that", "nope"):
        code, out = env["cg"]("approve", "--reads", "data/raw/hh.dta", "--agent", "Claude Code", "--reply", reply)
        assert code == 1 and "refused" in out, (reply, out)
        code, out = env["cg"]("approve", PLAN, "--reply", reply)
        assert code == 1 and "refused" in out and "status: draft" in path.read_text(), (reply, out)
    assert env["plan-records"]() == [] and not list((env["project"] / ".cg-docs" / "approvals").glob("data.*"))
    # Since the maintainer's second decision of 2026-11-26 (#225), a yes that goes on is refused too.
    assert env["cg"]("approve", PLAN, "--reply", "Yes. No other change.")[0] == 1
    assert env["cg"]("approve", PLAN, "--reply", "Yes.")[0] == 0


def test_a_schema_2_file_the_reader_cannot_parse_is_still_checked(env):
    """Finding 4: only a file with no schema key is version 1. A byte order mark,
    a frontmatter that is never closed, or a file that is not UTF-8 does not make one."""
    plan = front("plan", "draft") + PLAN_BODY
    path = env["put"]("plan", plan)
    path.write_bytes(b"\xef\xbb\xbf" + plan.encode())
    assert env["cg"]("validate", "--strict", PLAN) == (0, CLEAN)
    assert env["cg"]("approve", PLAN, "--reply", "Yes, approved.")[0] == 0
    assert "status: approved" in path.read_text(encoding="utf-8-sig")
    typed = front("plan", "approved") + PLAN_BODY.replace("0.153846", "0.2")
    for raw in (b"\xef\xbb\xbf" + typed.encode(), typed.replace("approved\n---\n", "approved\n", 1).encode(),
                typed.replace("Other poverty", "Other povérty").encode("cp1252")):
        path.write_bytes(raw)
        code, out = env["cg"]("validate", PLAN)
        assert code == 1 and "schema-2: 1" in out, out
        assert json.loads(env["cg"]("status", "--json")[1])["waiting-on-human"], out


def test_a_plan_put_back_to_the_text_an_amendment_replaced_needs_a_new_approval(env):
    """Finding 5: the newest approval is the one in force. Restoring the text it
    replaced (git checkout, an undo) is a change the human has not approved."""
    path = env["put"]("plan", front("plan", "draft") + PLAN_BODY)
    env["cg"]("approve", PLAN, "--reply", "Yes, approved.")
    first = path.read_text()
    amended = "\n## Amendments\n\n- 2026-11-26: the expected share is 0.25.\n"
    path.write_text(first.replace("0.153846", "0.25") + amended)
    assert env["cg"]("approve", PLAN, "--reply", "Yes, approved.")[0] == 0
    path.write_text(first)
    code, out = env["cg"]("validate")
    assert code == 1 and "no approval is recorded for the plan as it now reads" in out, out
    # Since task 2.3 (#226) the way back is an amendment too: one more dated line than the text in force.
    code, out = env["cg"]("approve", PLAN, "--reply", "Yes, I approve it as written.")
    assert code == 1 and "amendment" in out, out
    path.write_text(first + amended + "- 2026-11-27: back to 0.153846; the report was misread.\n")
    code, out = env["cg"]("approve", PLAN, "--reply", "Yes, I approve it as written.")
    assert code == 0 and "refused" not in out, out
    assert env["cg"]("validate")[0] == 0 and len(env["plan-records"]()) == 3
    # An intent has no amendments. Put back to a text it was decided on before, it takes a new yes,
    # and the record of that yes stands beside the first one for the same text.
    intent = env["project"] / IDEA
    decided = intent.read_text()
    intent.write_text(decided.replace("99th percentile", "95th percentile"))
    assert env["cg"]("approve", IDEA, "--reply", "Yes.")[0] == 0
    intent.write_text(decided)
    assert env["cg"]("validate", IDEA)[0] == 1 and env["cg"]("approve", IDEA, "--reply", "Yes.")[0] == 0
    assert len(list((env["project"] / ".cg-docs" / "approvals").glob("2026-11-20-headcount.*.json"))) == 3


def test_a_text_approved_twice_within_one_second_keeps_both_records(env, monkeypatch):
    """CI on 08925e26 (#227): once the name of a record held the time in place of a branch of its
    own, an intent put back to an earlier text in the second of its first yes wrote over that
    record. The clock is held still here, so the test does not depend on the machine's speed."""
    cg = load_cg()
    monkeypatch.setattr(cg, "now", lambda: "2026-11-26T10:00:00Z")
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(env["home"] / ".gitconfig"))
    intent = env["put"]("intent", front("intent", "draft") + INTENT_BODY, Path(IDEA).name)
    first = intent.read_text()
    for text in (first, first.replace("99th percentile", "95th percentile"), first):
        intent.write_text(re.sub(r"status: \w+", "status: draft", text, count=1))
        assert cg.main(["approve", str(intent), "--reply", "Yes.", "--project", str(env["project"])]) == 0
    assert len(list((env["project"] / ".cg-docs" / "approvals").glob("2026-11-20-headcount.*.json"))) == 3


def test_a_decision_on_data_holds_when_its_level_changes_only_in_case(env):
    """Finding 6: levels are compared without regard to case (ADR 0005), so the
    same level written in other case is no new level."""
    env["config"](**RULES)
    env["cg"]("approve", "--reads", "data/raw", "--agent", "Claude Code", "--reply", "Yes.")
    env["config"](**{**RULES, "data": {**RULES["data"], "data/raw": "CONFIDENTIAL"}})
    out = env["cg"]("tier", *ALL_NO, "--touches", "R/a.R", "--reads", "data/raw/hh.dta", "--agent", "Claude Code")[1]
    assert out.startswith("tier: low"), out


# ---------------------------------------------------------------- review of 2.1, findings left for wording

def test_every_cell_a_template_leaves_to_fill_asks_for_its_content_and_counts_as_unfilled(env):
    """Review finding 7 (#224): a completed work report passed with no changed file and no
    verdict for P4 or P6, because those cells were empty in the template and asked for nothing.
    Now each cell asks, and one request left anywhere in a line is unfilled text."""
    for kind in TYPES:
        template = (CG / "templates" / f"{kind}.md").read_text(encoding="utf-8")
        assert not re.search(r"\|[ \t]*\|", template), f"{kind}: a table cell is left empty"
        assert all(" " in ask for ask in re.findall(r"<[^<>]+>", template)), f"{kind}: a request of one word"
    env["cg"]("new", "work-report", "Fix the label", "--date", "2026-11-25")
    path = env["project"] / ".cg-docs" / "work-reports" / "2026-11-25-fix-the-label.md"
    text = path.read_text(encoding="utf-8").replace("status: in-progress", "status: completed")
    asks = re.findall(r"<[^<>]+>", text)
    path.write_text(re.sub(r"<[^<>]+>", "filled", text), encoding="utf-8")
    env["proved"](path)
    assert env["cg"]("validate", str(path)) == (0, CLEAN)
    # One request left in a line that is otherwise filled: the second cell of the first
    # row under Changed, and the finding of P4 (the fourth request under Self-review).
    for heading, nth in (("## Changed", 1), ("## Self-review", 3)):
        spots = [m.start() for m in re.finditer(r"<[^<>]+>", text)]
        kept = [at for at in spots if at > text.index(heading)][nth]
        half = re.sub(r"<[^<>]+>", lambda m: m.group(0) if m.start() == kept else "filled", text)
        assert any(line.startswith("| ") and "filled" in line and "<" in line for line in half.splitlines())
        path.write_text(half, encoding="utf-8")
        code, out = env["cg"]("validate", str(path))
        assert code == 1 and "the template's text is still in it" in out, (heading, out)
