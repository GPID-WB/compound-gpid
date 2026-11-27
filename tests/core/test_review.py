"""Tests for the review (task 2.9, #232): `cg.py route`, and the priority that `cg.py conformance` keeps.

The review playbook has the verifiers of the review stage check the work, shows the human every finding, those
against the contract apart from those against the standards, and records what the human decides on each. One record
holds the findings: the conformance record. `route` lists them by priority, P0 first, in two parts, and records each
decision as an approval is recorded, on the human's words, refusing a reply that is not a plain answer.
"""
import json
import re

from test_artifacts import CG, HUB, env, load_cg  # noqa: F401  (env is a fixture)
from test_plan import lines_run
from test_verifiers import REVIEW_STAGE, dispatched, give, held, working
from test_work import CODE, REPORT, fill, run_line

FOUND = [("contract", f"{CODE}:1: the line is 3.65 where the contract says 3.0 (P1; fix: 3.0)"),
         ("governance", f"{CODE}:1: a token stands in the code (P0; fix: an environment variable)"),
         ("determinism", f"{CODE}:1: the share is typed in (P2; fix: compute it)"),
         ("claims", "the work report names no record for its share (P3; fix: name the record)")]


def review(env, found=FOUND):
    """Every verifier of the review stage gives its verdict on the work: PASS, or FLAG with its findings."""
    for name in REVIEW_STAGE:
        mine = [text for verifier, text in found if verifier == name]
        assert give(env, REPORT, "review", name, "FLAG" if mine else "PASS", "independent",
                    *[x for text in mine for x in ("--finding", text)])[0] == 0, name


def route(env, *more):
    code, out = env["cg"]("route", REPORT, "--json", *more)
    return code, json.loads(out)


def answered(env):
    return [json.loads(p.read_text(encoding="utf-8")) for p in sorted(
        (env["project"] / ".cg-docs" / "approvals").glob("2026-11-26-headcount.route.*.json"))]


# ---------------------------------------------------------------- the code

def test_findings_keep_the_priority_their_verifier_gave_them_p0_to_p3(env):
    """Done when (#232): findings keep P0 to P3. In gate reruns 21 to 23 the agents recorded each finding without the
    priority the verdict block gives it, so nothing on record said what blocks a merge. Code now reads it from the
    finding, `(P1; fix: ...)`, keeps it beside the finding, the unverified ones too, and refuses a finding with none."""
    working(env)
    for loose in (f"{CODE}:1: the share is typed in", f"{CODE}:1: the share is typed in (P7 asks; fix: x)", "(P4) gone"):
        code, out = give(env, REPORT, "review", "determinism", "FLAG", "independent", "--finding", loose)
        assert code == 1 and "P0 to P3" in out and not held(env, REPORT), (loose, out)
    review(env)
    record = {v["verifier"]: v for v in held(env, REPORT)}
    assert record["determinism"]["findings"] == [{"where": CODE + ":1", "what": FOUND[2][1].split(": ", 1)[1],
                                                  "priority": "P2"}]
    assert record["claims"]["unverified"] == [{"what": FOUND[3][1], "priority": "P3"}] and not record["claims"]["findings"]
    code, listed = route(env)
    assert code == 1 and [(f["id"], f["priority"], f["verifier"]) for f in listed["findings"]] == [
        ("F1", "P1", "contract"), ("F2", "P0", "governance"), ("F3", "P2", "determinism"), ("F4", "P3", "claims")]
    assert [f["proven"] for f in listed["findings"]] == [True, True, True, False] and listed["missing"] == []


def test_findings_against_the_contract_and_against_the_standards_are_reported_apart(env):
    """Done when (#232): standards findings and spec findings are reported separately. The contract is the spec the
    human approved: the findings of P1's verifier are one part, and those of every other principle, the standards the
    work is held to, the other. Neither is merged into or ranked against the other: the contract's P1 comes before
    the standards' P0. Which principle is the contract's is a key of its file, as P5's rounds are."""
    working(env)
    review(env)
    code, out = env["cg"]("route", REPORT)
    contract, standards = out.index("\ncontract findings: 1\n"), out.index("\nstandards findings: 3\n")
    assert code == 1 and contract < standards and out.index("F1 P1 contract (P1)") < standards, out
    assert out.index("F2 P0 governance (P12)") > standards and "F4 P3 claims (P7): no proof:" in out, out
    assert [f["part"] for f in route(env)[1]["findings"]] == ["contract"] + ["standards"] * 3
    assert {p["id"] for p in load_cg().principles() if p["axis"] == "contract"} == {"P1"}
    assert {p["axis"] for p in load_cg().principles()} == {"contract", "standards"}


def test_the_human_triages_each_finding_and_zero_findings_is_a_valid_result(env):
    """Done when (#232): the human triages; zero findings is a valid result. No decision is the agent's: `route`
    records the human's reply word for word, under their name, and only when it names findings and one decision for
    each, fix, accept with the reason, or drop, as `approve` records only a plain yes. A fix sends the work back, and
    it waits again when a verifier finds it once more on a later state of the change. With no finding nothing waits."""
    project = working(env)
    code, listed = route(env)
    assert code == 1 and listed["missing"] == [f"review {name}" for name in REVIEW_STAGE] and not listed["findings"]
    assert env["cg"]("route", REPORT, "--reply", "all drop")[0] == 1 and not answered(env)  # the review is not done
    review(env)
    fill(project / REPORT, "completed")
    assert any(REPORT in item and "route" in item for item in json.loads(env["cg"]("status", "--json")[1])[
        "waiting-on-human"])
    for reply in ("Yes.", "Sounds good.", "F1 fix?", "F1 fix if it is quick", "F9 fix", "F2 accept", "F1 fix; F1 drop",
                  "Wait, F1 fix", "fix", "F1 fix and F2", "accept all: ok", "F1 F2 fix the line"):
        code, out = env["cg"]("route", REPORT, "--reply", reply)
        assert code == 1 and "refused" in out and not answered(env), (reply, out)
    code, out = env["cg"]("route", REPORT, "--reply", "F1 fix")
    assert code == 0 and "F1 fix" in out and "in-progress" in out, out
    assert "status: in-progress" in (project / REPORT).read_text(encoding="utf-8")  # the work goes on, on a plan
    reply = "OK. F2 accept: the token is a dummy the tests use, and the survey team holds the real one;\nall drop"
    code, out = env["cg"]("route", REPORT, "--reply", reply)
    assert code == 0 and route(env)[0] == 0 and route(env)[1]["waiting"] == [], out
    last = answered(env)[-1]
    assert (last["reply"], last["name"], last["email"], last["artifact"]) == (reply, "Test Human", "human@example.org", REPORT)
    assert [(d["id"], d["decision"], d["priority"]) for d in last["decisions"]] == [
        ("F2", "accept", "P0"), ("F3", "drop", "P2"), ("F4", "drop", "P3")]
    assert last["decisions"][0]["reason"].startswith("the token is a dummy") and "what" not in last["decisions"][0]
    decided = {f["id"]: (f["decision"], f["next"]) for f in route(env)[1]["findings"]}
    assert decided["F1"][0] == "fix" and "/cg plan" in decided["F1"][1] and decided["F2"][0] == "accept"
    # The change moves, and the contract's verifier finds the same fault again: the fix did not take, and it waits.
    (project / CODE).write_text("headcount <- function(dt) 0.25\n", encoding="utf-8")
    assert give(env, REPORT, "review", "contract", "FLAG", "independent", "--finding", FOUND[0][1])[0] == 0
    code, listed = route(env)
    assert code == 1 and listed["waiting"] == ["F1"] and listed["findings"][1]["decision"] == "accept", listed
    # Every verifier passes on the change as it now is: no finding, nothing to decide, and nothing waits.
    review(env, found=())
    code, out = env["cg"]("route", REPORT)
    assert code == 0 and "\nfindings: none\n" in out and "\nwaiting: none\n" in out, out
    assert "nothing to decide" in env["cg"]("route", REPORT, "--reply", "F1 fix")[1]
    assert not any(REPORT in item for item in json.loads(env["cg"]("status", "--json")[1])["waiting-on-human"])


def test_review_of_2_9_a_priority_is_the_one_its_fix_follows_and_a_reply_decides_only_what_it_settles(env):
    """Review of task 2.9 (#232). A fix that cites a principle in brackets, "(P1; fix: compute it with code (P3))", gave
    the finding P3, the last bracket, in place of the P1 its verifier wrote. A reason that is a condition, a no or a
    decision on another finding was recorded as an accept, and the review was done. A dropped work report, which
    the human ended, still waited on them in status, and a fix on it said the work went back."""
    project = working(env)
    for text, level in ((f"{CODE}:1: typed in (P1; fix: compute it with code (P3))", "P1"),
                        (f"{CODE}:1: typed in (P2; fix: see (P0) in the README)", "P2"),
                        (f"{CODE}:1: breaks (P3) here (P1; fix: compute it)", "P1"),
                        (f"{CODE}:1: typed in (P1 - fix: compute it)", "P1")):
        assert give(env, REPORT, "review", "determinism", "FLAG", "independent", "--finding", text)[0] == 0, text
        assert held(env, REPORT)[-1]["findings"][0]["priority"] == level, text
    review(env)
    for reply in ("F2 accept: if the team agrees", "F2 accept: unless the team objects", "F2 aceptar: si el equipo lo "
                  "aprueba", "F2 accept: only when the team agrees", "F2 accept: not now", "F2 accept: no",
                  "F2 accept: later", "F2 accept: F3 drop is fine", "F1 fix; F2 accept: F4 drop"):
        code, out = env["cg"]("route", REPORT, "--reply", reply)
        assert code == 1 and "refused" in out and not answered(env), (reply, out)
    code, out = env["cg"]("route", REPORT, "--reply", "F2 accept: not used by any output the team reads")
    assert code == 0 and answered(env)[-1]["decisions"][0]["reason"].startswith("not used"), out
    fill(project / REPORT, "dropped")
    assert not any(REPORT in item for item in json.loads(env["cg"]("status", "--json")[1])["waiting-on-human"])
    code, out = env["cg"]("route", REPORT, "--reply", "F1 fix")
    assert code == 1 and "dropped" in out and len(answered(env)) == 1, out


# ---------------------------------------------------------------- the text

def test_the_review_playbook_dispatches_the_review_shows_both_parts_and_ends_in_the_humans_decision(env):
    """#232: one review step in place of version 1's /cg-review, /cg-fix-triage and /cg-verify-pr. It takes the
    dispatch of the review stage from the close of the work, shows every finding in its part and by priority, and
    stops for the human's decision, a question in the reply and never an approval prompt. Its lines run as written."""
    text, work = ((CG / "playbooks" / name).read_text(encoding="utf-8") for name in ("review.md", "work.md"))
    lines = lines_run(text)
    assert [line.split()[0] for line in lines] == ["route", "verifiers", "route"], lines
    for words in ("You own the review", "hard stop", "end your turn", "approval settings", "against the contract",
                  "against the standards", "P0", "No finding is a valid result", "fix", "accept", "drop", "plain answer",
                  "`gh pr checks`", "/cg plan", "`missing: none`", "given on an earlier text", '"Verifiers"'):
        assert words in text, words
    assert "PLACEHOLDER" not in text + work and "--playbook review" in work[work.index("## 6."):]
    assert "verifiers" not in " ".join(lines_run(work)) and "--stage review" not in work
    guide = (CG / "SKILL.md").read_text(encoding="utf-8")
    assert "| The human, with `review` after `/cg`" in guide and "--playbook review" in guide
    assert "P0 to P3" in (CG / "verifier.md").read_text(encoding="utf-8")
    project = working(env)
    review(env)
    values = {"the work report": REPORT, "the human's reply, word for word": "all drop"}
    assert run_line(env, lines[0], **values)[0] == 1 and "\nwaiting: F1, F2, F3, F4\n" in run_line(env, lines[0], **values)[1]
    assert "\nverifiers: contract (P1); " in run_line(env, lines[1], **values)[1]
    assert run_line(env, lines[2], **values)[0] == 0 and run_line(env, lines[0], **values)[0] == 0
    assert project.is_dir()


def test_the_general_lenses_port_the_v1_review_agents_to_the_verifiers_that_had_none(env):
    """#232: general lenses ported from the 17 review agents of version 1. Each agent's part that a principle holds went
    to that principle's lens: the three verifiers of the review stage that had none get one, in the shape of the others,
    and the ledger says where each of the 17 went, or why it stays out of core."""
    working(env)
    reads = {v["verifier"]: v["reads"] for v in dispatched(env, REPORT, "review")}
    for name, principle, agents, words in (
            ("domain-lenses", "P10", ("cg-data-quality",), ("## At the plan stage", "weights", "denominator", "merge",
                                                           "vintage", "missing", "rule 6", "python -B -c")),
            ("language", "P11", ("cg-code-quality", "cg-documentation"), ("glossary", "avoid", "two meanings",
                                                                          "help page", "linter")),
            ("governance", "P12", ("cg-version-control",), ("## At the plan stage", "data register", "credential",
                                                             "personal data", "approve --reads`", "lineage", "P0"))):
        text = (CG / "lenses" / f"{name}.md").read_text(encoding="utf-8")
        front, body = text.split("\n---\n", 1)
        assert len(text.splitlines()) <= 60 and f"principle: {principle}" in front, name
        assert all(f"v1:.agents/skills/{agent}.md" in front for agent in agents), name
        assert "## The flags" in body and "## Leave alone" in body and [w for w in words if w not in body] == [], name
        assert reads[name][1].endswith(f"lenses/{name}.md"), reads[name]
    assert "security-and-hardening" in (CG / "lenses" / "governance.md").read_text(encoding="utf-8").split("\n---\n")[0]
    ledger = (HUB / "docs" / "adoption-ledger.md").read_text(encoding="utf-8")
    agents = re.findall(r"^\| `(cg-[a-z-]+)` \|", ledger.split("## Version 1")[1], re.M)
    assert sorted(agents) == sorted(
        ["cg-adversarial", "cg-architecture", "cg-code-quality", "cg-data-quality", "cg-documentation", "cg-fix-problems",
         "cg-learnings-researcher", "cg-performance", "cg-plan-critic", "cg-project-scanner", "cg-release-scanner",
         "cg-reproducibility", "cg-roadmap-view", "cg-roadmap", "cg-testing", "cg-version-control", "cg-wiki"]), agents
    assert list((HUB / "docs" / "adr").glob("0013-*.md")) and "`cg.py route`" in (HUB / "README.md").read_text(
        encoding="utf-8")
