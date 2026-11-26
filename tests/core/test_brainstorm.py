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
    path.write_text(good.replace("status: draft", "status: dropped"), encoding="utf-8")
    code, out = env["cg"]("approve", INTENT, "--reply", "Yes, that is what I want.")
    assert code == 1 and "an intent takes an approval while it is draft or decided" in out, out
    path.write_text(good.replace("status: draft", "status: parked"), encoding="utf-8")
    assert "status is parked; an intent is one of: draft, decided, dropped" in env["cg"]("validate")[1]


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
    asked = approve.replace("<the intent>", made)
    # The line as written holds no reply yet, and code does not take its placeholder for a yes.
    assert "holds no plain yes" in env["cg"](*shlex.split(asked))[1]
    code, out = env["cg"](*shlex.split(asked.replace("<the human's reply, word for word>", "Yes, that is it.")))
    assert code == 0 and "approved" in out and "status: decided" in path.read_text(), out


def test_the_intent_template_holds_what_grilling_settles(env):
    template = (CG / "templates" / "intent.md").read_text(encoding="utf-8")
    cg = load_cg()
    for heading in ("## Goal", "## Out of scope", "## A wrong result", "## Facts", "## Decisions", "## Assumptions"):
        assert heading in template and heading in cg.ARTIFACTS["intent"]["sections"], heading
    assert '"open"' in template[template.index("## Decisions"):template.index("## Assumptions")]


# ---------------------------------------------------------------- review of 2.2 before Opus (#225)

def test_only_a_reply_that_holds_a_plain_yes_is_recorded(env):
    """The maintainer's decision of 2026-11-26 (#225): code records a reply only when it holds a
    plain yes word. Before, it refused a list and recorded the rest, "I'd rather not" included."""
    path = env["put"]("intent", front("intent", "draft") + INTENT_BODY)
    refused = [("I don't approve", "holds no plain yes"), ("I do not agree", "holds no plain yes"),
               ("I'd rather not", "holds no plain yes"), ("Absolutely not", "holds no plain yes"),
               ("Maybe", "holds no plain yes"), ("Let me think about it", "holds no plain yes"),
               ("Sure", "holds no plain yes"), ("Is D1 really the Pareto tail?", "holds no plain yes"),
               ("Change D1 to the 95th percentile", "holds no plain yes"), ("Si quieres", "holds no plain yes"),
               ("That is not ok", "says no"), ("It isn't approved", "says no"), ("I can't say yes yet", "says no"),
               ("No estoy de acuerdo", "says no"), ("Todavía no estoy de acuerdo", "says no"),
               ("Yes, and also add the poverty gap", "a condition or a correction"),
               ("Yes, though drop D1", "a condition or a correction"),
               ("Sí, pero solo la ola de 2019", "a condition or a correction")]
    for said, words in refused:
        code, out = env["cg"]("approve", INTENT, "--reply", said)
        assert code == 1 and words in out and "status: draft" in path.read_text(), (said, out)
    assert not (env["project"] / ".cg-docs" / "approvals").exists()
    for number, said in enumerate(("ok", "OK.", "Okay, do it", "Sí", "Sí.", "si, de acuerdo", "De acuerdo.", "Go ahead.",
                                   "I agree", "Approved", "Confirmed.", "Yes. No other change.", "Sounds good. Yes.")):
        path = env["put"]("intent", front("intent", "draft") + INTENT_BODY, name=f"2026-11-25-reply-{number}.md")
        code, out = env["cg"]("approve", str(path), "--reply", said)
        assert code == 0 and "status: decided" in path.read_text(), (said, out)
    text = GRILLING.read_text(encoding="utf-8")
    plain = text[text.index("## Replies that are not a yes"):]
    for word in ("yes", "ok", "approved", "confirmed", "agreed", "go ahead", "sí", "de acuerdo"):
        assert f'"{word}"' in plain, word


def test_a_cell_that_only_stands_for_not_yet_is_no_answer_no_source_and_no_recommendation(env):
    """Before, only the word open counted as no answer: "pending", "TBD", "?" and `open` in
    backticks, which is how the playbook prints the word, each let an intent be decided."""
    answered = "| Yes, the Pareto tail. |"
    for cell in ("`open`", "*open*", "(open)", "still open", "pending", "Pending.", "TBD", "?", "-", "n/a",
                 "to be decided", "not yet decided", "waiting for the survey team"):
        path = env["put"]("intent", front("intent", "draft") + INTENT_BODY.replace(answered, f"| {cell} |"))
        code, out = env["cg"]("approve", INTENT, "--reply", "Yes.")
        assert code == 1 and "decision D1 has no answer from the human yet" in out, (cell, out)
        assert "status: draft" in path.read_text()
    # The human's own words stand when they are in quotes.
    env["put"]("intent", front("intent", "draft") + INTENT_BODY.replace(answered, '| "Pending the tail, yes." |'))
    assert env["cg"]("approve", INTENT, "--reply", "Yes.")[0] == 0
    for old, new, words in (("`R/welfare.R:41`", "unknown", "names no source"), ("`R/welfare.R:41`", "?", "names no source"),
                            ("A Pareto tail above the 99th percentile; it adds a threshold to choose", "-",
                             "decision D1 has no recommended answer")):
        env["put"]("intent", front("intent", "draft") + INTENT_BODY.replace(old, new), name="2026-11-25-cells.md")
        code, out = env["cg"]("approve", ".cg-docs/brainstorms/2026-11-25-cells.md", "--reply", "Yes.")
        assert code == 1 and words in out, (new, out)


def test_a_section_with_nothing_written_under_it_is_not_confirmed(env):
    """Before, a heading with nothing under it passed: an intent was decided with no goal, no
    out of scope, no wrong result or no assumptions, once the template's own text was deleted."""
    for heading, text in (("## Goal", INTENT_BODY.split("## Goal")[1].split("##")[0]),
                          ("## Out of scope", "\nThe 2016 wave is not estimated again.\n"),
                          ("## A wrong result", INTENT_BODY.split("## A wrong result")[1].split("##")[0]),
                          ("## Assumptions", INTENT_BODY.split("## Assumptions")[1].split("##")[0])):
        assert text.strip() and INTENT_BODY.count(text) == 1
        path = env["put"]("intent", front("intent", "draft") + INTENT_BODY.replace(text, "\n\n"))
        code, out = env["cg"]("validate", INTENT)
        assert code == 0 and f"warn {INTENT}: nothing is written under '{heading}'" in out, (heading, out)
        code, out = env["cg"]("approve", INTENT, "--reply", "Yes.")
        assert code == 1 and f"nothing is written under '{heading}'" in out and "status: draft" in path.read_text()
    # A table with its two header lines and no row holds nothing either.
    env["cg"]("new", "work-report", "Fix the label", "--date", "2026-11-25")
    report = env["project"] / ".cg-docs" / "work-reports" / "2026-11-25-fix-the-label.md"
    done = re.sub(r"<[^<>]+>", "filled", report.read_text(encoding="utf-8")).replace("status: in-progress", "status: completed")
    report.write_text(done, encoding="utf-8")
    assert env["cg"]("validate", str(report))[0] == 0
    report.write_text(done.replace("| filled | filled |\n\n## Checks", "\n## Checks"), encoding="utf-8")
    code, out = env["cg"]("validate", str(report))
    assert code == 1 and "nothing is written under '## Changed'" in out, out


# ---------------------------------------------------------------- review of 2.2 by Opus 5.5 (#225)

def test_a_reply_that_holds_a_yes_word_and_is_not_a_yes_is_refused(env):
    """Review finding 1: a yes word was enough. A question that holds one, a stop after it, a
    condition with "if", a correction with no marker word, a negation the list missed, and a
    condition or a negation in Spanish were each recorded."""
    path = env["put"]("intent", front("intent", "draft") + INTENT_BODY)
    refused = {
        "is a question": ["Is this ok?", "Who approved this?", "Ok?", "¿De acuerdo?"],
        "says no, or not yet": ["OK, wait.", "Ok, stop.", "Okay, hold on.", "OK, let me think about it.",
                                "Yes, no wait.", '"Wait, ok"', "I haven't approved this", "It hasn't been approved",
                                "I shouldn't say yes", "Nothing here is ok", "None of this is ok",
                                "Nobody approved this", "Nunca dije que sí", "Jamás estaré de acuerdo",
                                "Tampoco estoy de acuerdo", "Para nada de acuerdo"],
        "a condition or a correction": ["Yes if you drop D2", "Yes, assuming D2 uses the 2019 file",
                                        "Yes, on condition that D2 changes", "Yes, and add the poverty gap too",
                                        "Yes. Change D2 to the 2019 file.", "Yes, drop D2.",
                                        "Sí, aunque cambia D2", "Sí, excepto D2", "Sí, salvo D2",
                                        "Sí, siempre que uses 2019", "Sí, a menos que D2 cambie", "Sí, si quitas D2",
                                        "Sí, sin embargo cambia D2", "Sí, también añade la brecha"],
    }
    for words, replies in refused.items():
        for said in replies:
            code, out = env["cg"]("approve", INTENT, "--reply", said)
            assert code == 1 and words in out and "status: draft" in path.read_text(), (said, out)
    assert not (env["project"] / ".cg-docs" / "approvals").exists()
    for number, said in enumerate(("Yes.", "Yes, nothing to add.", "Nothing to change; yes.", "Sí, adelante",
                                   "Yes, I confirm D1 and D2 as written.")):
        path = env["put"]("intent", front("intent", "draft") + INTENT_BODY, name=f"2026-11-25-yes-{number}.md")
        code, out = env["cg"]("approve", str(path), "--reply", said)
        assert code == 0 and "status: decided" in path.read_text(), (said, out)


def test_what_sits_under_a_subheading_of_facts_or_decisions_is_checked(env):
    """Review finding 2: table_rows read only the table right under the heading, so a second round
    of decisions under `### Round 2`, or facts under a subheading, were never checked."""
    good = front("intent", "draft") + INTENT_BODY
    round_two = ("\n### Round 2\n\n| ID | Decision | Recommended answer, with its trade-off | The human's answer |\n"
                 "|---|---|---|---|\n| D3 | Which survey year | 2019, the latest | open |\n")
    more_facts = "\n### From the codebook\n\n| Fact | Source |\n|---|---|\n| Weights are household weights | |\n"
    second_table = ("\nAsked later:\n\n| ID | Decision | Recommended answer, with its trade-off | The human's answer |\n"
                    "|---|---|---|---|\n| D3 | Which survey year | 2019, the latest | pending |\n")
    for text, words in ((good.replace("\n## Assumptions", round_two + "\n## Assumptions"), "decision D3 has no answer"),
                        (good.replace("\n## Decisions", more_facts + "\n## Decisions"), "names no source"),
                        (good.replace("\n## Assumptions", second_table + "\n## Assumptions"), "decision D3 has no answer")):
        path = env["put"]("intent", text)
        code, out = env["cg"]("approve", INTENT, "--reply", "Yes.")
        assert code == 1 and words in out and "status: draft" in path.read_text(), (words, out)


def test_the_assumptions_block_from_grilling_is_not_filled_while_its_requests_are_in_it(env):
    """Review finding 3: grilling.md's block, pasted with its requests left in, passed."""
    text = GRILLING.read_text(encoding="utf-8")
    block = text[text.index("```\nAssumptions"):text.index("Correct me now.\n```") + len("Correct me now.\n```")]
    assumptions = INTENT_BODY.split("## Assumptions")[1].split("##")[0]
    path = env["put"]("intent", front("intent", "draft") + INTENT_BODY.replace(assumptions, f"\n\n{block}\n\n"))
    code, out = env["cg"]("approve", INTENT, "--reply", "Yes.")
    assert code == 1 and "the template's text is still in it" in out and "status: draft" in path.read_text(), out


def test_a_placeholder_behind_a_mark_or_off_the_list_is_no_answer_and_none_is_no_source(env):
    """Review finding 4: a list mark or a bracket before a placeholder hid it, the list missed
    common ones and Spanish ones, and "none" or "guess" counted as a source."""
    answered = "| Yes, the Pareto tail. |"
    for cell in ("- pending", "— TBD", "<open>", "{open}", "> open", "~~open~~", "1. TBD", "TBC", "t.b.d.", "n.a.",
                 "XXX", "FIXME", "to decide", "to confirm", "not asked yet", "no answer yet", "ask the human",
                 "unclear", "not sure", "don't know", "pendiente", "por decidir", "sin respuesta"):
        path = env["put"]("intent", front("intent", "draft") + INTENT_BODY.replace(answered, f"| {cell} |"))
        code, out = env["cg"]("approve", INTENT, "--reply", "Yes.")
        assert code == 1 and "decision D1 has no answer from the human yet" in out, (cell, out)
        assert "status: draft" in path.read_text()
    for source in ("none", "no source", "not found", "not checked", "guess", "my guess", "assumed", "from memory",
                   "general knowledge", "I think so"):
        env["put"]("intent", front("intent", "draft") + INTENT_BODY.replace("`R/welfare.R:41`", source),
                   name="2026-11-25-source.md")
        code, out = env["cg"]("approve", ".cg-docs/brainstorms/2026-11-25-source.md", "--reply", "Yes.")
        assert code == 1 and "names no source" in out, (source, out)
    # "None" stays a human's answer, and "the human" stays a source.
    env["put"]("intent", front("intent", "draft") + INTENT_BODY.replace(answered, "| None. |")
               .replace("`R/welfare.R:41`", "the human"), name="2026-11-25-none.md")
    assert env["cg"]("approve", ".cg-docs/brainstorms/2026-11-25-none.md", "--reply", "Yes.")[0] == 0


def test_a_section_that_holds_only_filler_is_empty(env):
    """Review finding 5: one line of filler under a heading passed."""
    goal = INTENT_BODY.split("## Goal")[1].split("##")[0]
    for filler in ("TBD", "- TBD", "...", "***", "<!-- to fill -->", "<!--\nto fill\n-->", "&nbsp;", "<br>", "n/a",
                   "```\nTBD\n```"):
        path = env["put"]("intent", front("intent", "draft") + INTENT_BODY.replace(goal, f"\n\n{filler}\n\n"))
        code, out = env["cg"]("approve", INTENT, "--reply", "Yes.")
        assert code == 1 and "nothing is written under '## Goal'" in out, (filler, out)
        assert "status: draft" in path.read_text()
    # "none" is what grilling.md asks for when nothing is assumed.
    assumptions = INTENT_BODY.split("## Assumptions")[1].split("##")[0]
    env["put"]("intent", front("intent", "draft") + INTENT_BODY.replace(assumptions, "\n\nnone\n\n"))
    assert env["cg"]("approve", INTENT, "--reply", "Yes.")[0] == 0


def test_a_playbook_asked_for_before_setup_is_named_as_waiting(env):
    """Review finding 7: in a project that is not set up, --playbook brainstorm opened setup and
    said nothing of the brainstorm, so the guide had no line to tell the human."""
    state = json.loads(env["cg"]("status", "--guide", "--playbook", "brainstorm", "--json")[1])
    assert state["playbook"].endswith("setup.md")
    assert state["next"] == "read playbooks/setup.md; brainstorm, which the human asked for, opens once setup is done"
