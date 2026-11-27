"""Tests for the contract (P1) and the claims (P7) verifiers (task 2.8, #231).

A verifier is a model reading a lens, and CI cannot start one. Code holds what it can. At the plan stage `cg.py validate`
holds the contract, as it did. At the review stage `cg.py claims` holds what the plan and the work report name to the
project and its records: of P1, each file the plan names is there; of P7, each file and record the work report names is
there, each file its Changed table names was changed, a claim labelled measured has a pointer, a function it names is
defined, and a number on a line that names an output is one that output holds. The planted cases are in
evals/planted/contract/ and evals/planted/claims/, and run_planted.py gives each lens its project.
"""
import json
import re

from test_adversary_and_simplicity import REPORT, build
from test_artifacts import CG, HUB, env, load_cg  # noqa: F401  (env is a fixture)
from test_determinism import at
from test_verification import where
from test_verifiers import dispatched, give, held


def claims(env, cases, principle):
    """What cg.py claims printed and recorded, after each finding was held to a planted case of its principle: each
    case with a rule is found at its line, and nothing else is found, so a claim the work report makes rightly is
    no finding. A finding at its record is proof, and so is one at the line code named."""
    code, out = env["cg"]("claims", "--report", REPORT)
    path = re.search(r"^record: (\S+)", out, re.M).group(1)
    record = json.loads((env["project"] / path).read_text(encoding="utf-8"))
    places = [(case, where(env["project"], case)) for case in cases if case["code"]]
    assert code == 1 and record["kind"] == "claims" and out.startswith("claims: "), out
    for case, spot in places:
        assert any(at(f["where"], spot) for f in record["findings"] if f["rule"] == case["code"]), (case, record)
    assert all(any(at(f["where"], spot) for case, spot in places if case["code"] == f["rule"])
               for f in record["findings"]), record["findings"]
    assert {f["rule"] for f in record["findings"]} == {r for r, (p, _) in load_cg().CLAIMS.items() if p == principle}
    assert all(f"FLAG {f['rule']}: {f['where']}; fix: {f['fix']}" in out for f in record["findings"])
    line = record["findings"][0]["where"]
    assert give(env, REPORT, "review", {"P1": "contract", "P7": "claims"}[principle], "FLAG", "independent",
                "--finding", f"{path}: code found it (P2; fix: x)", "--finding", f"{line}: code found it (P2; fix: x)")[0] == 0
    assert [f["where"] for f in held(env, REPORT)[-1]["findings"]] == [path, line]
    return out + (env["project"] / path).read_text(encoding="utf-8")


def test_claims_finds_the_part_of_each_planted_case_of_p7_that_code_can_find_and_keeps_no_number(env):
    """Done when (#231): the claims verifier catches its planted violations. Code finds a record the report points at
    that is not there, a number its output does not hold, a claim labelled measured with no pointer, a function the
    project does not define, and a file the Changed table names that the change left as it was. It shows and keeps
    no number, of the report or of the output (P12). The verifier reads its lens at the review stage."""
    project, cases = build(env, "claims")
    shown = claims(env, cases["review"], "P7")
    assert not [value for value in ("0.52", "0.472727", "0.55", "regional_shares") if value in shown]
    assert next(v for v in dispatched(env, REPORT, "review") if v["verifier"] == "claims")["reads"][-1].endswith(
        "cg/lenses/claims.md")


def test_claims_finds_a_file_the_plan_names_that_the_work_did_not_build_and_validate_holds_the_planted_plan(env):
    """Done when (#231): the contract verifier catches its planted violations. At the review stage code finds a file
    the plan names in its contract, its data register or its slices that the project does not hold. At the plan stage
    code's part is validate, which the planted plan passes: what is planted in it is for judgement alone."""
    project, cases = build(env, "contract")
    claims(env, cases["review"], "P1")
    assert env["cg"]("validate", ".cg-docs/plans/2026-11-27-poverty-brief.md", "--strict")[0] == 0
    for stage in ("plan", "review"):
        artifact = REPORT if stage == "review" else ".cg-docs/plans/2026-11-27-poverty-brief.md"
        assert dispatched(env, artifact, stage)[0]["reads"][-1].endswith("cg/lenses/contract.md")


def test_the_contract_and_claims_lenses_hold_what_code_does_in_the_shape_of_the_others():
    """Each lens (#231) is in the shape of the determinism lens, within its 60 lines: what code holds or found, with
    the bullet that the verifier accounts for each finding of code, then what is judged and what is left alone. It
    names each rule of its principle. The principle files say what code holds, and the decision is ADR 0012."""
    rules = load_cg().CLAIMS
    for name, principle, words in (
            ("contract", "P1", ("## At the plan stage", "`cg.py validate`", "`cg.py claims`", "amendment", "intent")),
            ("claims", "P7", ("`cg.py claims`", "measured", "inferred", "guess", "`unbacked`", "rule 6"))):
        text = (CG / "lenses" / f"{name}.md").read_text(encoding="utf-8")
        front, body = text.split("\n---\n", 1)
        assert len(text.splitlines()) <= 60 and f"principle: {principle}" in front and "derived-from:" in front, name
        assert "Account for each" in body and "## Leave alone" in body, name
        assert [w for w in words + tuple(f"`{r}`" for r, (p, _) in rules.items() if p == principle) if w not in body] == []
    for name in ("P01-specify-before-generating", "P07-honest-claims"):
        text = (CG / "principles" / f"{name}.md").read_text(encoding="utf-8")
        assert "`cg.py claims`" in text.split("## Deterministic checks")[1], name
    assert list((HUB / "docs" / "adr").glob("0012-*.md")) and "the contract and the claims verifiers" in (
        HUB / "README.md").read_text(encoding="utf-8")


def test_review_of_2_8_a_file_the_plan_names_in_backticks_is_held_and_a_line_past_the_end_of_a_file_is_none(env):
    """Review of #231. `not-built` read the names of the plan only outside backticks, and plans name the files of their
    slices in backticks (8 of the 9 plans of gate reruns 20 to 23), so it found the planted file only as the planted
    plan wrote it. A command is still no file it builds. And a line one past the end of a file was a line of it."""
    project, _ = build(env, "contract")
    plan, report = project / ".cg-docs/plans/2026-11-27-poverty-brief.md", project / REPORT
    text = plan.read_text(encoding="utf-8").replace("written to output/notes.md", "written to `output/notes.md`")
    plan.write_bytes(text.replace("checks/layout.py`", "checks/later.py`").encode("utf-8"))
    end = len((project / "pipeline.py").read_bytes().splitlines())
    report.write_bytes(report.read_bytes() + "".join(f"- Measured: `pipeline.py:{n}`.\n" for n in (end, end + 1)).encode())
    found, last = re.findall(r"^FLAG (\S+): ([^:\s]+):(\d+);", env["cg"]("claims", "--report", REPORT)[1], re.M), \
        len(report.read_text(encoding="utf-8").splitlines())
    notes = 1 + next(n for n, line in enumerate(text.splitlines()) if "`output/notes.md`" in line)
    assert [f for f in found if f[0] == "not-built"] == [("not-built", plan.relative_to(project).as_posix(), str(notes))]
    assert ("no-such-file", REPORT, str(last)) in found and ("no-such-file", REPORT, str(last - 1)) not in found, found


def test_review_of_2_8_each_lens_says_what_its_planted_cases_hold_and_reruns_no_command_of_the_working_agent():
    """Review of #231 and the lens runs. The determinism lens had a finding of `differs` point at the record alone, where
    the fix needs the line, and judged an order or a clock only in an output that is compared; the claims lens wrote
    the column of two rules to judge as when to leave them, and Kilo opened no output to judge `unmatched`, which code
    had compared; the adversary lens had the verifier run again any failed command of the work, the working agent's."""
    lens = {name: (CG / "lenses" / f"{name}.md").read_text(encoding="utf-8") for name in ("determinism", "claims",
                                                                                              "adversary")}
    assert "`differs` names an output: point at the line of code" in lens["determinism"] and "mapped or not" in (
        lens["determinism"]) and "fetches the address" in lens["determinism"]
    row = next(line for line in lens["claims"].splitlines() if line.startswith("| A function named"))
    assert ": leave it" in row and "open no output" in lens["claims"]
    assert "Run no other command of the record" in lens["adversary"] and "rules 3 and 4 of `worker.md`" in lens["adversary"]
