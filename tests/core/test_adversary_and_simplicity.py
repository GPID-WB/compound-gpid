"""Tests for the adversary (P5) and the simplicity (P6) verifiers (task 2.8, #231).

A verifier is a model reading a lens, and CI cannot start one. Code holds what it can. A finding of the adversary
stands only when a run of this work reproduced it, its rounds are numbered and bounded, and what it dropped is
listed. `cg.py scope` measures the change and names what a rule can find of P6. The planted cases are in
evals/planted/adversary/ and evals/planted/simplicity/, and run_planted.py gives each lens its project.
"""
import json
import re
import sys

from test_artifacts import CG, HUB, env, load_cg  # noqa: F401  (env is a fixture)
from test_determinism import at
from test_verifiers import give, held
from test_work import PY

sys.path.insert(0, str(HUB / "evals" / "planted"))
import run_planted  # noqa: E402

REPORT = run_planted.REPORT


def build(env, name):
    """The planted project of a verifier as the work leaves it, before its verifiers start."""
    folder, cg = HUB / "evals" / "planted" / name, env["home"] / ".agents" / "skills" / "cg" / "scripts" / "cg.py"
    cases = json.loads((folder / "expected.json").read_text(encoding="utf-8"))
    env["project"].rmdir()
    run_planted.build(folder, env["project"], [sys.executable, str(cg)], cases)
    return env["project"], cases


def probe(env, command):
    """A probe run through the line for a run, with this interpreter: its exit code and the path of its record."""
    code, out = env["cg"]("evidence", "--run", command.replace("python ", f"{PY} ", 1), "--report", REPORT)
    return code, re.search(r"^record: (\S+)", out, re.M).group(1)


def test_a_finding_of_the_adversary_stands_only_when_a_run_reproduced_it_and_the_rest_is_listed_as_dropped(env):
    """Done when (#231): findings reproduced, dropped findings listed. Each planted case has a probe that fails on
    the planted fault, and code keeps a finding that points at its record. A finding at a line, at a run that passed,
    or at a run whose command the record cut, so that nobody can run it again, is listed as dropped, after what the
    adversary dropped itself; a FLAG that keeps none is UNVERIFIED."""
    project, cases = build(env, "adversary")
    kept, given = [], []
    for case in cases["review"]:
        code, record = probe(env, case["probe"])
        assert code == 1 and case["code"] == "run", case
        kept, given = kept + [record], given + ["--finding", f"{record}: {case['flag']} (P1; fix: an error)"]
    (_, passed), (_, cut) = probe(env, cases["decoy"]["probe"]), probe(env, f'python -B -c "assert {"1" * 300} == 0"')
    assert json.loads((project / passed).read_text(encoding="utf-8"))["exit"] == 0
    lost = [f"{passed}: a group with no weight", "pipeline.py:36: the share counts", f"{cut}: a probe cut short"]
    assert give(env, REPORT, "review", "adversary", "FLAG", "independent", *given, *[a for f in lost for a in (
        "--finding", f)], "--dropped", f"{passed}: an empty group stops the run, as R4 asks")[0] == 0
    entry = held(env, REPORT)[-1]
    assert [f["where"] for f in entry["findings"]] == kept and entry["verdict"] == "FLAG" and entry["round"] == 1
    assert entry["dropped"] == [f"{passed}: an empty group stops the run, as R4 asks"] + [
        f"not reproduced: {text}" for text in lost] and entry["unverified"] == [], entry
    listing = env["cg"]("conformance", REPORT, "--stage", "review")[1]
    assert "adversary: FLAG, independent review, round 1 of 3" in listing and f"\n  dropped: {lost[0]}" not in listing
    assert f"\n  dropped: not reproduced: {lost[0]}" in listing, listing
    assert give(env, REPORT, "review", "adversary", "FLAG", "independent", "--finding", lost[1])[0] == 0
    assert held(env, REPORT)[-1]["verdict"] == "UNVERIFIED" and held(env, REPORT)[-1]["round"] == 1
    # Any other verifier keeps a finding at a line, as before, and a run that passed is proof of what it ran.
    assert give(env, REPORT, "review", "verification", "FLAG", "independent", "--finding", lost[1])[0] == 0
    assert held(env, REPORT)[-1]["findings"] and "round" not in held(env, REPORT)[-1]


def test_the_adversary_has_three_rounds_one_for_each_state_of_the_change_and_stops_at_doubt_theater(env):
    """Done when (#231): bounded to three rounds. A round is the adversary's verdict on one state of the change, so a
    second verdict on the same state is the same round. Code numbers each, refuses a fourth, and refuses a third
    after two rounds that gave findings and reproduced none, which P5 calls doubt theater."""
    project, _ = build(env, "adversary")
    quick, line = ".cg-docs/work-reports/2026-11-26-quick.md", "pipeline.py:36: the share counts a household twice"
    assert env["cg"]("new", "work-report", "Quick", "--date", "2026-11-26")[0] == 0
    for report, verdict in ((REPORT, ("PASS",)), (quick, ("FLAG", "--finding", line))):
        for number in (1, 1, 2, 3, 4):
            (project / "README.md").write_text(f"round {number}\n", encoding="utf-8")
            code, out = give(env, report, "review", "adversary", verdict[0], "independent", *verdict[1:])
            if report == REPORT and number < 4 or report == quick and number < 3:
                assert code == 0, (report, number, out)
        assert code == 1 and "refused: " in out, out
    rounds = [(v["artifact"], v["round"], v["verdict"]) for v in held(env, REPORT) + held(env, quick)]
    assert rounds == [(REPORT, 1, "PASS")] * 2 + [(REPORT, 2, "PASS"), (REPORT, 3, "PASS")] + [
        (quick, 1, "UNVERIFIED")] * 2 + [(quick, 2, "UNVERIFIED")], rounds
    assert "has had its 3 rounds" in give(env, REPORT, "review", "adversary", "PASS", "independent")[1]
    assert "doubt theater" in out and "round 2 of 3" in env["cg"]("conformance", quick, "--stage", "review")[1]


def test_scope_measures_the_change_and_finds_the_part_of_each_planted_case_of_p6_that_code_can_find(env):
    """Code's part of P6 (#231): `cg.py scope` gives the size of the change beside the files the slices list, and
    names a change of layout alone, a function the change adds that no line calls or one line calls, and an argument
    its body never reads, each with the change that would replace it. It names nothing the change did not add, and
    a finding at its record is proof. The runner ran it once every slice was done, as the work playbook does."""
    project, cases = build(env, "simplicity")
    code, out = env["cg"]("scope", "--report", REPORT)
    path = re.search(r"^record: (\S+)", out, re.M).group(1)
    record = json.loads((project / path).read_text(encoding="utf-8"))
    assert code == 1 and record["kind"] == "scope" and (record["files"], record["listed"]) == (3, 3), out
    assert record["added"] > record["removed"] > 0 and "change: 3 files, +" in out and "the slices list 3" in out
    for case in cases["review"]:
        found = [f["where"] for f in record["findings"] if f["rule"] == case["code"]]
        name, lines = case["file"], (project / case["file"]).read_text(encoding="utf-8").splitlines()
        spot = (name, next(n for n, text in enumerate(lines, 1) if case["text"] in text) * (case["code"] != "reformat"))
        assert not case["code"] or any(at(where, spot) for where in found), (case, found)
    assert {f["rule"] for f in record["findings"]} == set(load_cg().SCOPE) and all(
        f"FLAG {f['rule']}: {f['where']}; fix: {f['fix']}" in out for f in record["findings"])
    old = {n for n, text in enumerate((project / "pipeline.py").read_text().splitlines(), 1) if "def " in text
           and text.split("def ")[1].split("(")[0] in ("households", "headcount", "main")}
    assert not [f for f in record["findings"] if f["where"].split(":")[0] == "pipeline.py" and int(
        f["where"].split(":")[1]) in old], record["findings"]
    assert give(env, REPORT, "review", "simplicity", "FLAG", "independent", "--finding", f"{path}: x")[0] == 0
    assert held(env, REPORT)[-1]["findings"][0]["where"] == path


def test_the_adversary_and_simplicity_lenses_hold_what_code_does_in_the_shape_of_the_others():
    """Each lens (#231) is in the shape of the determinism lens, within its 60 lines: what code holds or found, with
    the bullet that the verifier accounts for each finding of code, then what is judged and what is left alone. The
    principle files say what code holds, the guide records what was dropped, and the decision is ADR 0011."""
    cg = load_cg()
    for name, principle, words in (
            ("adversary", "P5", ("three rounds", "doubt theater", "dropped:", "reproduced", "300 characters",
                                 "python -B -c", "Rscript -e", "fails again", "rule 6", "rule 7")),
            ("simplicity", "P6", ("`cg.py scope`", "## At the plan stage", "scratch copy", *[f"`{r}`" for r in cg.SCOPE]))):
        text = (CG / "lenses" / f"{name}.md").read_text(encoding="utf-8")
        front, body = text.split("\n---\n", 1)
        assert len(text.splitlines()) <= 60 and f"principle: {principle}" in front and "derived-from:" in front, name
        assert "Account for each" in body and "## Leave alone" in body, name
        assert [w for w in words if w not in body] == [], name
    p5, p6 = (cg.read_frontmatter((CG / "principles" / f"{f}.md").read_text(encoding="utf-8"))[0] for f in (
        "P05-adversarial-by-default", "P06-smallest-change"))
    assert (str(p5.get("rounds")), p5.get("proof"), p6.get("rounds")) == ("3", "run", None)
    assert "`cg.py scope`" in (CG / "principles" / "P06-smallest-change.md").read_text().split("## Deterministic checks")[1]
    assert "`--dropped`" in (CG / "SKILL.md").read_text(encoding="utf-8")
    assert list((HUB / "docs" / "adr").glob("0011-*.md")) and "the adversary and the simplicity verifiers" in (
        HUB / "README.md").read_text(encoding="utf-8")
