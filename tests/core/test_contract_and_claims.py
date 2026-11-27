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
                "--finding", f"{path}: code found it", "--finding", f"{line}: code found it")[0] == 0
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
