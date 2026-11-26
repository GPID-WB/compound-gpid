"""Tests for the plan playbook and hard stop 1 (task 2.3, #226).

What an agent must not get wrong is held by code: a plan is built on a decided
intent, every check in it can fail and is run by a slice, its data register
agrees with the recorded classifications, only the human's recorded yes
approves it, an approved plan changes only by an amendment, and an unfinished
plan is never written over. The other tests hold the playbook to that code.
"""
import json
import re
import shlex

from test_artifacts import (CG, CLEAN, IDEA, INTENT_BODY, PLAN, PLAN_BODY, env, front,  # noqa: F401  (env is a fixture)
                            load_cg)

GOOD = front("plan", "draft") + PLAN_BODY
SLICE = "| S1 | headcount() | R/headcount.R | C1, C2 | by code: R/headcount.R |"
AMENDED = "\n## Amendments\n\n- 2026-11-26: the expected share is 0.25, from the survey report.\n"


def refused(env, path, text, words):
    """A plan with this text fails validate and is not approved, each time for the reason in words."""
    path.write_text(text, encoding="utf-8")
    code, out = env["cg"]("validate", PLAN)
    assert code == 1 and words in out and "Traceback" not in out, (words, out)
    code, out = env["cg"]("approve", PLAN, "--reply", "Yes.")
    assert code == 1 and "refused" in out and words in out and "status: draft" in path.read_text(), (words, out)


# ---------------------------------------------------------------- the code

def test_every_check_in_a_plan_can_fail(env):
    """Done when (#226): every check in the plan can fail. A check has a command and an outcome
    that means failure, neither is a placeholder, the outcome does not say that the check cannot
    fail, and a slice runs it: a check that no slice ends in never fails."""
    path = env["put"]("plan", GOOD)
    assert SLICE in GOOD and env["cg"]("validate", "--strict", PLAN) == (0, CLEAN)
    for cell in ("TBD", "-", "n/a", "to be decided", "?"):
        refused(env, path, GOOD.replace("| no error is raised |", f"| {cell} |"),
                "check C2 does not say which outcome means failure")
    for cell in ("never", "Never, it is a smoke run", "nothing", "None.", "It cannot fail.", "this check can't fail",
                 "always passes", "N/A - a smoke run", "not applicable"):
        refused(env, path, GOOD.replace("| no error is raised |", f"| {cell} |"), "check C2 cannot fail")
    for cell in ("TBD", "`to be decided`", "..."):
        refused(env, path, GOOD.replace("`Rscript tests/missing-weight.R`", cell), "check C2 has no command")
    for old, new, words in (
            ("| C1, C2 |", "| C1 |", "check C2 is run by no slice"),
            ("| C1, C2 |", "| C1, C2, C9 |", "slice S1 names C9, which the Checks table does not hold"),
            ("| C1, C2 |", "| the tests |", "slice S1 ends in no check"),
            ("| S1 |", "| first |", "'first' is not an ID such as S1"),
            ("| R/headcount.R | C1", "| TBD | C1", "slice S1 names no file"),
            ("| by code: R/headcount.R |", "| quickly |", "slice S1 does not say whether it is done by code or by judgement"),
            ("| by code: R/headcount.R |", "| by code |", "slice S1 is done by code and names no tool"),
            (SLICE, SLICE + "\n" + SLICE.replace("C1, C2", "C1"), "the ID S1 appears twice"),
            (SLICE + "\n", "", "the Slices table needs a row")):
        assert old in GOOD
        refused(env, path, GOOD.replace(old, new), words)
    # An outcome that starts like a placeholder, or that holds the word fail, is still an outcome.
    for cell in ("unknown country codes are left in the output", "the run does not fail on a missing weight",
                 "nothing is returned", "none of the rows has a weight", "open rows remain", "NA is returned"):
        path.write_text(GOOD.replace("| no error is raised |", f"| {cell} |"), encoding="utf-8")
        assert env["cg"]("validate", "--strict", PLAN) == (0, CLEAN), cell
    path.write_text(GOOD.replace("| by code: R/headcount.R |", "| by judgement |"), encoding="utf-8")
    assert env["cg"]("validate", "--strict", PLAN) == (0, CLEAN)


def test_a_plan_is_approved_only_by_the_humans_recorded_yes_which_is_written_into_it(env):
    """Done when (#226): the turn ends at approval, and approval is written to the artifact. Code
    cannot see a turn end. It holds what the stop is for: a plan is `approved` only through
    `approve`, which takes a plain yes and nothing else, and the plan then names its record."""
    path = env["put"]("plan", GOOD)
    assert json.loads(env["cg"]("status", "--json")[1])["waiting-on-human"] == [f"{PLAN} (status draft)"]
    for reply in ("Sounds good.", "Yes, but drop C2.", "Go ahead with S1 first", "Looks fine, start the work"):
        code, out = env["cg"]("approve", PLAN, "--reply", reply)
        assert code == 1 and "refused" in out and "status: draft" in path.read_text(), (reply, out)
    assert env["plan-records"]() == [] and "approval:" not in path.read_text()
    code, out = env["cg"]("approve", PLAN, "--reply", "Yes.")
    assert code == 0 and f"approved {PLAN}" in out, out
    (record,) = env["plan-records"]()
    text = path.read_text()
    assert "\nstatus: approved\n" in text and text.endswith(PLAN_BODY)
    assert f"\napproval: .cg-docs/approvals/{record.name}\n" in text.split("---\n")[1]
    held = json.loads(record.read_text(encoding="utf-8"))
    assert held["reply"] == "Yes." and held["text"] == PLAN_BODY.strip("\n")  # the text they said yes to
    assert env["cg"]("validate", "--strict", PLAN) == (0, CLEAN)
    # The plan names a record that exists: without it, the plan is not approved.
    record.unlink()
    code, out = env["cg"]("validate", PLAN)
    assert code == 1 and "approval: no such file" in out and "no approval is recorded for the plan" in out, out


def test_a_plan_is_built_on_a_decided_intent(env):
    """ADR 0005 left open what links an intent to the work that follows. `new plan` writes the
    link, and makes no plan on an intent that the human has not confirmed as it reads."""
    env["base"]()
    plans = env["project"] / ".cg-docs" / "plans"
    env["put"]("intent", front("intent", "draft") + INTENT_BODY, "2026-11-21-draft.md")
    env["put"]("intent", front("intent", "decided") + INTENT_BODY, "2026-11-22-typed.md")
    env["put"]("review", front("review", "open") + "\n## Findings\n\nNone.\n\n## Not checked\n\nNothing.\n")
    for more in ([], ["--intent", ".cg-docs/brainstorms/2026-11-21-draft.md"],
                 ["--intent", ".cg-docs/brainstorms/2026-11-22-typed.md"],
                 ["--intent", ".cg-docs/reviews/2026-11-25-headcount.md"], ["--intent", "README.md"]):
        code, out = env["cg"]("new", "plan", "Headcount", "--date", "2026-11-25", *more)
        assert code == 1 and "refused: a plan is built on a decided intent" in out and "/cg brainstorm" in out, out
        assert not plans.exists()
    code, out = env["cg"]("new", "plan", "Headcount", "--date", "2026-11-25", "--intent", str(env["project"] / IDEA))
    assert code == 0 and f"\nintent: {IDEA}\n" in (plans / "2026-11-25-headcount.md").read_text(), out
    # At approval the intent must still be decided as it reads, and the plan must still name it.
    path = env["put"]("plan", GOOD)
    path.write_text(GOOD.replace(f"intent: {IDEA}\n", ""), encoding="utf-8")
    code, out = env["cg"]("validate", PLAN)
    assert code == 0 and f"warn {PLAN}: it names no intent" in out, out
    code, out = env["cg"]("approve", PLAN, "--reply", "Yes.")
    assert code == 1 and "it names no intent" in out and "status: draft" in path.read_text(), out
    path.write_text(GOOD, encoding="utf-8")
    intent = env["project"] / IDEA
    intent.write_text(intent.read_text().replace("99th percentile", "95th percentile"), encoding="utf-8")
    code, out = env["cg"]("approve", PLAN, "--reply", "Yes.")
    assert code == 1 and f"the intent {IDEA} is not decided as it now reads" in out, out
    assert env["cg"]("approve", IDEA, "--reply", "Yes.")[0] == 0
    assert env["cg"]("approve", PLAN, "--reply", "Yes.")[0] == 0


def test_the_data_register_is_held_to_the_recorded_classifications(env):
    """ADR 0005 left open how the data register meets the data rules (P12). A dataset in the
    register has the classification the human had recorded, and no other: a level typed into
    the plan is a description, as "public" in a README is."""
    path = env["put"]("plan", GOOD)
    row = "| inst/extdata/survey.csv | Public | synthetic | 1 | the team | any |"
    assert row in GOOD
    cases = [({}, "no classification is recorded for inst/extdata/survey.csv, which the data register lists"),
             ({"inst/extdata": "Official Use Only"}, "the data register gives inst/extdata/survey.csv as Public, and "
                                                     "the recorded classification is Official Use Only"),
             (["survey.csv"], "no classification is recorded for inst/extdata/survey.csv")]  # rules of the wrong shape
    for rules, words in cases:
        env["config"](data=rules)
        code, out = env["cg"]("validate", PLAN)
        assert code == 0 and f"warn {PLAN}: {words}" in out, (rules, out)
        code, out = env["cg"]("approve", PLAN, "--reply", "Yes.")
        assert code == 1 and words in out and "setup --data" in out and "status: draft" in path.read_text(), out
    env["config"](data={"inst/extdata": "PUBLIC"})  # a folder's rule covers the file, in any case
    assert env["cg"]("validate", "--strict", PLAN) == (0, CLEAN)
    path.write_text(GOOD.replace(row, row.replace("| Public |", "| **Public** |").replace("inst/", "`inst/")
                                 .replace(".csv |", ".csv` |")), encoding="utf-8")
    assert env["cg"]("validate", "--strict", PLAN) == (0, CLEAN)
    for cell in ("unknown", "TBD", ""):
        path.write_text(GOOD.replace("| the team |", f"| {cell} |"), encoding="utf-8")
        code, out = env["cg"]("approve", PLAN, "--reply", "Yes.")
        assert code == 1 and "the data register leaves a cell of inst/extdata/survey.csv unfilled" in out, (cell, out)
    # Work that reads and produces no dataset says so, and needs no rule.
    env["config"]()
    path.write_text(GOOD.replace(row, "| none | none | none | none | none | none |"), encoding="utf-8")
    assert env["cg"]("validate", "--strict", PLAN) == (0, CLEAN)
    assert env["cg"]("approve", PLAN, "--reply", "Yes.")[0] == 0


def test_an_unfinished_plan_is_never_overwritten(env):
    """Done when (#226). `new` never writes over a file, and it makes no second plan while one
    is unfinished unless the human said that the new one is other work."""
    env["base"]()
    plans = env["project"] / ".cg-docs" / "plans"
    new = ["new", "plan", "--intent", IDEA, "--date", "2026-11-25"]
    assert env["cg"](*new, "Headcount")[0] == 0
    first = plans / "2026-11-25-headcount.md"
    first.write_text(first.read_text() + "\nHalf written.\n", encoding="utf-8")
    kept = first.read_text()
    code, out = env["cg"](*new, "Headcount")
    assert code == 1 and "exists, not overwritten" in out and first.read_text() == kept, out
    for status in ("draft", "approved", "in-progress", "parked"):
        first.write_text(kept.replace("status: draft", f"status: {status}"), encoding="utf-8")
        code, out = env["cg"](*new, "Poverty gap")
        assert code == 1 and f"refused: a plan is not finished: {PLAN} (status {status})" in out, out
        assert "--other-work" in out and "amendment" in out and [p.name for p in plans.iterdir()] == [first.name]
    code, out = env["cg"](*new, "Poverty gap", "--other-work")
    assert code == 0 and len(list(plans.iterdir())) == 2 and first.read_text() == kept.replace("draft", "parked", 1), out
    # A plan that is finished or set aside is in nobody's way, and neither is a version 1 plan.
    for path, status in zip(sorted(plans.iterdir()), ("completed", "dropped")):
        path.write_text(re.sub(r"status: \S+", f"status: {status}", path.read_text(), count=1), encoding="utf-8")
    (plans / "2026-03-01-old.md").write_text("---\nstatus: active\n---\n", encoding="utf-8")
    assert env["cg"](*new, "Severity")[0] == 0


def test_an_approved_plan_changes_only_by_an_amendment_and_what_was_approved_stays_readable(env):
    """P1: a change to the contract is an amendment the human approves, and the original stays
    readable. The record of each approval keeps the text, and a changed plan is approved again
    only with one more dated line under Amendments than the text in force had."""
    path = env["put"]("plan", GOOD)
    assert env["cg"]("approve", PLAN, "--reply", "Yes.")[0] == 0
    changed = path.read_text().replace("0.153846", "0.25")
    for text in (changed, changed + "\n## Amendments\n\nThe expected share changed.\n",
                 changed + "\n## Notes\n\n- 2026-11-26: the expected share is 0.25.\n"):
        path.write_text(text, encoding="utf-8")
        assert env["cg"]("validate", PLAN)[0] == 1
        code, out = env["cg"]("approve", PLAN, "--reply", "Yes.")
        assert code == 1 and "refused: this plan was approved before" in out and "## Amendments" in out, out
        assert len(env["plan-records"]()) == 1
    path.write_text(changed + AMENDED, encoding="utf-8")
    assert env["cg"]("approve", PLAN, "--reply", "Yes.")[0] == 0 and env["cg"]("validate", PLAN)[0] == 0
    held = [json.loads(p.read_text(encoding="utf-8")) for p in env["plan-records"]()]
    held.sort(key=lambda record: len(record["text"]))
    assert held[0]["text"] == PLAN_BODY.strip("\n") and "0.25" in held[1]["text"]
    newest = next(p.name for p in env["plan-records"]() if "0.25" in p.read_text(encoding="utf-8"))
    assert f"\napproval: .cg-docs/approvals/{newest}\n" in path.read_text()
    # A second change needs a second line: the first one does not cover it.
    path.write_text(path.read_text().replace("0.25", "0.3"), encoding="utf-8")
    assert "this plan was approved before" in env["cg"]("approve", PLAN, "--reply", "Yes.")[1]
    path.write_text(path.read_text() + "- 2026-11-27: the expected share is 0.3.\n", encoding="utf-8")
    assert env["cg"]("approve", PLAN, "--reply", "Yes.")[0] == 0 and len(env["plan-records"]()) == 3


# ---------------------------------------------------------------- the text

PLAYBOOK = CG / "playbooks" / "plan.md"


def lines_run(text):
    """The cg.py lines a playbook prints, without the launcher and the project."""
    return [span.split('"<cg>" ', 1)[1].replace(' --project "<project root>"', "")
            for span in re.findall(r"`([^`\n]+)`", text) if span.startswith('"<python>" "<cg>" ')]


def test_the_plan_playbook_writes_no_code_opens_no_data_and_ends_in_a_hard_stop():
    text = PLAYBOOK.read_text(encoding="utf-8")
    opening = text[:text.index("## 1.")]
    assert "outside `.cg-docs/`" in opening and "no data file" in opening and "hard stop" in opening
    assert "`grilling.md`" in opening and "in full" in opening
    approve = text[text.index("## 7. Approve"):text.index("## 8.")]
    for words in ("This is a hard stop.", "as the file reads", "plain yes", "end your turn", "`refused`"):
        assert words in approve, words
    assert "Do not start" in text[text.index("## 8."):]


def test_the_plan_playbook_holds_what_the_issue_names():
    """#226: thin vertical slices, declared checks, boundaries, deferred scope; an unfinished plan
    is never overwritten; and the plan-stage verifiers, a marked placeholder until task 2.5."""
    text = PLAYBOOK.read_text(encoding="utf-8")
    start = text[text.index("## 1."):text.index("## 2.")]
    assert "`--other-work`" in start and "`exists, not overwritten`" in start and "amendment" in start
    assert "`## Amendments`" in start and "/cg brainstorm" in start
    contract = text[text.index("## 3."):text.index("## 4.")]
    for words in ("Always", "Ask first", "Never", "deferred", "would fail if the requirement were not met",
                  "wrong result", "proxy"):
        assert words in contract, words
    slices = text[text.index("## 4."):text.index("## 5.")]
    assert "thinnest" in slices and "by code" in slices and "by judgement" in slices and "ends in" in slices
    checked = text[text.index("## 6."):text.index("## 7.")]
    assert "PLACEHOLDER: written in task 2.5" in checked and "self-review" in checked
    # An amended plan fails validate until it is approved again, and the playbook says so.
    assert "no approval is recorded for the plan as it now reads" in checked
    for principle in ("P1", "P3", "P6", "P12"):
        assert principle in checked, principle


def test_the_guide_opens_the_plan_through_status(env):
    guide = (CG / "SKILL.md").read_text(encoding="utf-8")
    row = next(line for line in guide.splitlines() if line.startswith("|") and "`plan` after `/cg`" in line)
    assert "`--playbook plan`" in row and "section 3" in row
    env["config"]()
    state = json.loads(env["cg"]("status", "--guide", "--playbook", "plan", "--json")[1])
    assert state["playbook"].endswith("plan.md") and state["next"] == "read playbooks/plan.md"


def test_the_lines_the_plan_playbook_runs_work_as_written(env):
    """The plan is made by `new`, checked by `validate` and approved by `approve`, each as the
    playbook writes it. The lines on data are the ones quick work runs, word for word."""
    env["base"]()
    text = PLAYBOOK.read_text(encoding="utf-8")
    lines = lines_run(text)
    new, validate, approve = (next(line for line in lines if line.startswith(word))
                              for word in ("new plan", "validate", "approve \"<the plan>\""))
    code, out = env["cg"](*shlex.split(new.replace("<the decided intent>", IDEA)), "--date", "2026-11-25")
    assert code == 0 and out.startswith("created .cg-docs/plans/2026-11-25-"), out
    made = out.split()[1]
    assert env["cg"](*shlex.split(validate.replace("<the plan>", made)))[0] == 0
    path = env["project"] / made
    path.write_text(path.read_text().split("\n# ", 1)[0] + PLAN_BODY, encoding="utf-8")
    asked = approve.replace("<the plan>", made)
    assert "holds no plain yes" in env["cg"](*shlex.split(asked))[1]  # the placeholder is no reply
    code, out = env["cg"](*shlex.split(asked.replace("<the human's reply, word for word>", "Yes.")))
    assert code == 0 and "approved" in out and "status: approved" in path.read_text(), out
    quick = lines_run((CG / "playbooks" / "quick.md").read_text(encoding="utf-8"))
    others = [line for line in lines if line not in (new, validate, approve)]
    assert {line.split()[0] for line in others} == {"tier", "setup", "approve"} and len(others) == 3
    assert all(line in quick for line in others), others


def test_the_plan_template_asks_for_what_code_checks_and_new_fills_in_the_intent():
    template = (CG / "templates" / "plan.md").read_text(encoding="utf-8")
    assert "\nintent: {intent}\n" in template.split("---\n")[1]
    assert "no check" in template[template.index("### Checks"):template.index("### Boundaries")]
    assert "recorded" in template[template.index("## Data register"):template.index("## Slices")]


def test_the_other_texts_name_the_plan():
    """What a human types changed: `/cg plan`. Each text that tells them what comes next names it."""
    quick = (CG / "playbooks" / "quick.md").read_text(encoding="utf-8")
    assert "`/cg plan`" in quick[quick.index("**`tier: elevated`.**"):quick.index("**When the human answers")]
    assert "approved plan" in quick[quick.index("## 1. Restate"):quick.index("## 2.")]
    brainstorm = (CG / "playbooks" / "brainstorm.md").read_text(encoding="utf-8")
    assert "`/cg plan`" in brainstorm[brainstorm.index("**Reply:**"):]
    hub = CG.parents[2]
    assert "`/cg plan`" in (hub / "docs" / "install-block.md").read_text(encoding="utf-8")
    assert "`/cg plan`" in (hub / "README.md").read_text(encoding="utf-8")
    cg = load_cg()
    p1 = (CG / "principles" / "P01-specify-before-generating.md").read_text(encoding="utf-8")
    assert "slice" in p1[p1.index("## Deterministic checks"):] and "decided intent" in p1[p1.index("## Deterministic checks"):]
    assert "approval" in cg.LINK_KEYS and "**Amendment**" in (CG / "GLOSSARY.md").read_text(encoding="utf-8")
