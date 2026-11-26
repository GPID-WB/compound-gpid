"""Tests for grilling, the restatement, the assumptions and the brainstorm playbook (task 2.2, #225).

What an agent must not get wrong is held by code: an intent is decided only by
the human's recorded yes to its text, nothing in it may still be open, and the
replies that are not a yes are one list in cg.py. The other tests hold the
text of the playbook and of grilling.md to that code.
"""
import json
import re
import shlex

from test_artifacts import CG, env, front, load_cg  # noqa: F401  (env is a fixture)

INTENT = ".cg-docs/brainstorms/2026-11-25-headcount.md"
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


def records(project):
    return [json.loads(p.read_text(encoding="utf-8"))
            for p in sorted((project / ".cg-docs" / "approvals").glob("*.json"))]


# ---------------------------------------------------------------- the code

def test_an_intent_is_decided_only_by_the_humans_recorded_yes(env):
    """Done when (#225): the session ends only when the human confirms."""
    path = env["put"]("intent", front("intent", "draft") + INTENT_BODY)
    assert env["cg"]("validate", "--strict")[0] == 0
    assert json.loads(env["cg"]("status", "--json")[1])["waiting-on-human"] == [f"{INTENT} (status draft)"]
    code, out = env["cg"]("approve", INTENT, "--reply", "Yes, that is what I want.")
    assert code == 0 and f"approved {INTENT}" in out and "by: Test Human" in out, out
    assert "status: decided" in path.read_text() and path.read_text().endswith(INTENT_BODY)
    (record,) = records(env["project"])
    assert record["reply"] == "Yes, that is what I want." and record["artifact"] == INTENT
    assert record["hash"] == load_cg().text_hash(INTENT_BODY)
    assert env["cg"]("validate", "--strict")[0] == 0
    assert json.loads(env["cg"]("status", "--json")[1])["waiting-on-human"] == []


def test_a_status_typed_into_an_intent_is_not_the_humans_yes(env):
    env["put"]("intent", front("intent", "decided") + INTENT_BODY)
    code, out = env["cg"]("validate")
    assert code == 1 and "no approval is recorded for the intent as it now reads" in out, out
    waiting = json.loads(env["cg"]("status", "--json")[1])["waiting-on-human"]
    assert waiting == [f"{INTENT} (status decided, not approved as it now reads)"]


def test_a_decided_intent_that_changes_needs_a_new_yes(env):
    path = env["put"]("intent", front("intent", "draft") + INTENT_BODY)
    env["cg"]("approve", INTENT, "--reply", "Yes, that is what I want.")
    path.write_text(path.read_text().replace("99th percentile", "95th percentile"))
    assert env["cg"]("validate")[0] == 1
    code, out = env["cg"]("approve", INTENT, "--reply", "Yes, the 95th percentile.")
    assert code == 0 and "status: decided" in path.read_text(), out
    assert len(records(env["project"])) == 2 and env["cg"]("validate")[0] == 0


def test_an_intent_with_something_still_open_is_not_confirmed(env):
    """Done when (#225): nothing is silently assumed. Each fact has a source, each
    decision was put to the human with a recommended answer and has their answer,
    and the assumptions are written down."""
    good = front("intent", "draft") + INTENT_BODY
    ask = re.findall(r"<[^<>]+>", (CG / "templates" / "intent.md").read_text(encoding="utf-8"))[0]
    breaks = [
        (good.replace("| Yes, the Pareto tail. |", "| open |"), "decision D1 has no answer from the human yet"),
        (good.replace("| Yes, the Pareto tail. |", "| Open: the survey team knows |"), "decision D1 has no answer"),
        (good.replace("| The new function. |", "| |"), "decision D2 has no answer from the human yet"),
        (good.replace("| The Pareto tail as one new function; the other approach changes nothing |", "| |"),
         "decision D2 has no recommended answer"),
        (good.replace("| `R/welfare.R:41` |", "| |"), "names no source"),
        (good.replace("| D2 |", "| D1 |"), "the ID D1 appears twice"),
        (good.replace("| D2 |", "| second |"), "'second' is not an ID such as D1"),
        (re.sub(r"\| D\d \|.*\n", "", good), "the Facts table and the Decisions table each need a row"),
        (good.replace("## Assumptions", "## Notes"), "the section '## Assumptions' is missing"),
        (good.replace("- The 2016 wave was not adjusted.", f"- {ask}"), "the template's text is still in it"),
    ]
    path = env["put"]("intent", good)
    for text, words in breaks:
        path.write_text(text, encoding="utf-8")
        code, out = env["cg"]("approve", INTENT, "--reply", "Yes, that is what I want.")
        assert code == 1 and "refused" in out and words in out, (words, out)
        assert "status: draft" in path.read_text() and not (env["project"] / ".cg-docs" / "approvals").exists()
    # While the intent is a draft, an open decision is its normal state: a warning, which --strict fails.
    path.write_text(breaks[0][0], encoding="utf-8")
    code, out = env["cg"]("validate")
    assert code == 0 and f"warn {INTENT}: decision D1 has no answer from the human yet" in out, out
    assert env["cg"]("validate", "--strict")[0] == 1
    path.write_text(breaks[0][0].replace("status: draft", "status: decided"), encoding="utf-8")
    assert "FAIL" in env["cg"]("validate")[1]


def test_replies_that_are_not_a_yes_are_refused_with_what_to_ask_next(env):
    """Done when (#225): a list of replies that do not count as a yes."""
    path = env["put"]("intent", front("intent", "draft") + INTENT_BODY)
    cg = load_cg()
    for reply, kind in cg.NOT_A_YES.items():
        for said in (reply, reply.capitalize() + ".", f"  {reply} to me!"):
            code, out = env["cg"]("approve", INTENT, "--reply", said)
            assert code == 1 and f'refused: "{said.strip()}" {cg.KINDS[kind]}' in out, (said, out)
    cases = [("Whatever you think is best.", "hands the decision back"), ("Sure go on", "agrees without deciding"),
             ("Yes, but use the 95th percentile.", "a condition or a correction"),
             ("Go ahead, unless the survey team objects", "a condition or a correction"),
             ("Not yet.", "says no, or not yet")]
    for said, words in cases:
        code, out = env["cg"]("approve", INTENT, "--reply", said)
        assert code == 1 and words in out and "status: draft" in path.read_text(), (said, out)
    assert not (env["project"] / ".cg-docs" / "approvals").exists()
    # A reply that opens the same way and then says a plain yes is a yes.
    assert env["cg"]("approve", INTENT, "--reply", "Sounds good. Yes.")[0] == 0


def test_status_opens_the_playbook_the_human_asked_for_once_the_project_is_set_up(env):
    code, out = env["cg"]("status", "--guide", "--playbook", "brainstorm", "--json")
    state = json.loads(out)
    assert code == 0 and state["phase"] == "setup" and state["playbook"].endswith("setup.md"), out
    env["config"]()
    state = json.loads(env["cg"]("status", "--guide", "--playbook", "brainstorm", "--json")[1])
    assert state["phase"] == "ready" and state["playbook"].endswith("brainstorm.md")
    assert state["next"] == "read playbooks/brainstorm.md"
    assert json.loads(env["cg"]("status", "--guide", "--json")[1])["playbook"].endswith("quick.md")
    code, out = env["cg"]("status", "--guide", "--playbook", "ideate")
    assert code == 2 and "no playbook named 'ideate'" in out and "brainstorm, quick, setup" in out, out
    code, out = env["cg"]("status", "--playbook", "brainstorm")
    assert code == 2 and "--guide" in out


# ---------------------------------------------------------------- the text

GRILLING = CG / "grilling.md"
PLAYBOOK = CG / "playbooks" / "brainstorm.md"


def test_grilling_names_every_reply_that_code_refuses_and_so_do_p2_and_setup():
    cg = load_cg()
    text = GRILLING.read_text(encoding="utf-8").lower()
    for reply in cg.NOT_A_YES:
        assert f'"{reply}"' in text, reply
    assert len(set(cg.NOT_A_YES.values())) == 2 and set(cg.NOT_A_YES.values()) <= set(cg.KINDS)
    # The replies P2 and the setup playbook name are examples from the one list.
    principle = (CG / "principles" / "P02-human-decides.md").read_text(encoding="utf-8")
    hard_stops = principle[principle.index("### Hard stops"):principle.index("### Sign-off")]
    confirm = (CG / "playbooks" / "setup.md").read_text(encoding="utf-8")
    confirm = confirm[confirm.index("## 3. Confirm"):confirm.index("## 4. Write")]
    named = re.findall(r'"([^"]+)"', hard_stops + confirm)
    assert len(named) == 5 and all(reply.lower() in cg.NOT_A_YES for reply in named), named


def test_grilling_holds_the_three_parts_the_issue_names_and_stays_short():
    text = GRILLING.read_text(encoding="utf-8")
    for heading in ("## Facts and decisions", "## Restate", "## Assumptions", "## Replies that are not a yes"):
        assert heading in text, heading
    restate = text[text.index("## Restate"):text.index("## Assumptions")]
    assert "goal" in restate.lower() and "out of scope" in restate.lower() and "wrong result" in restate.lower()
    assert "recommend" in text[text.index("## Facts and decisions"):text.index("## Restate")]
    assert len(text.splitlines()) <= 120, "grilling.md is held to a playbook's budget"
    # The guide points every playbook at it, and the brainstorm playbook has it read in full.
    guide = (CG / "SKILL.md").read_text(encoding="utf-8")
    assert "`grilling.md`" in guide[guide.index("## What holds in every playbook"):]
    assert "`grilling.md` in full" in PLAYBOOK.read_text(encoding="utf-8")


def test_the_guide_opens_the_brainstorm_through_status():
    guide = (CG / "SKILL.md").read_text(encoding="utf-8")
    row = next(line for line in guide.splitlines() if line.startswith("|") and "brainstorm" in line)
    assert "`--playbook brainstorm`" in row and "section 3" in row


def test_the_brainstorm_changes_no_code_opens_no_data_and_ends_in_a_hard_stop():
    text = PLAYBOOK.read_text(encoding="utf-8")
    opening = text[:text.index("## 1.")]
    assert "outside `.cg-docs/`" in opening and "no data file" in opening and "hard stop" in opening
    confirm = text[text.index("## 6. Confirm"):]
    assert "end your turn" in confirm and "`refused`" in confirm and "as the file reads" in confirm


def test_the_lines_the_brainstorm_runs_work_as_written(env):
    """The intent is made by `new`, checked by `validate` and confirmed by `approve`,
    each as the playbook writes it."""
    text = PLAYBOOK.read_text(encoding="utf-8")
    lines = [span.split('"<cg>" ', 1)[1].replace(' --project "<project root>"', "")
             for span in re.findall(r"`([^`\n]+)`", text) if span.startswith('"<python>" "<cg>" ')]
    new, validate, approve = (next(line for line in lines if line.startswith(word))
                              for word in ("new intent", "validate", "approve"))
    code, out = env["cg"](*shlex.split(new), "--date", "2026-11-25")
    assert code == 0 and out.startswith("created .cg-docs/brainstorms/2026-11-25-"), out
    made = out.split()[1]
    assert env["cg"](*shlex.split(validate.replace("<the intent>", made)))[0] == 0
    path = env["project"] / made
    path.write_text(path.read_text().split("\n# ", 1)[0] + INTENT_BODY, encoding="utf-8")
    code, out = env["cg"](*shlex.split(approve.replace("<the intent>", made)))
    assert code == 0 and "approved" in out and "status: decided" in path.read_text(), out


def test_the_intent_template_holds_what_grilling_settles(env):
    template = (CG / "templates" / "intent.md").read_text(encoding="utf-8")
    cg = load_cg()
    for heading in ("## Goal", "## Out of scope", "## A wrong result", "## Facts", "## Decisions", "## Assumptions"):
        assert heading in template and heading in cg.ARTIFACTS["intent"]["sections"], heading
    assert '"open"' in template[template.index("## Decisions"):template.index("## Assumptions")]
