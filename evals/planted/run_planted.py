"""Run a verifier's lens on its planted project through a coding agent, and judge what it returns (#229).

Usage: <python> evals/planted/run_planted.py [--verifier determinism] [--only claude,codex,kilo]
                                             [--stages review,plan] [--dest DIR] [--out DIR]
                                             [--kilo-model provider/model] [--cg PATH] [--dry-run]

CI holds what code finds of each planted violation (tests/core/test_determinism.py and
test_verification.py). The rest is by judgement: a model reads the lens, and CI cannot start a model,
so this script gives that part a run.
For each agent it builds a copy of the planted project in DIR (default ~/temp/cg-lens): the files of
<verifier>/project/, its verification profile, the rule for its data file, and git with no commit, so
that every file is the change. For the review stage it adds a work report, the risk of the work and,
as the cases ask, the record of `cg.py repro`, or an approved plan and each slice with the checks the
work ran (#230), as the work playbook leaves them; for the plan stage, <verifier>/plan.md as a draft
plan. The stages are those the cases hold. `cg.py verifiers` prints the kickoff, and the agent gets it,
in a new session, with no word added (the guide's rule "Verifiers").

It judges each reply from its verdict block and from the files: the verdict is FLAG; each finding
proposes the code that would replace it (`fix:`); each case of <verifier>/expected.json is caught by a
finding of its own; the verifier changed no file of the project but the records of a run; and, where
the cases ask it, the verifier reran every check of the plan itself. The agents run with approval
prompts off, as in the gate. --dry-run builds every copy, prints each kickoff and the line that would
start the agent, and starts nothing. Transcripts and results.json go to --out (default DIR/out).
Exit code 1 when a check fails.
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "spike" / "gate"))
import run_cli_gate as gate  # noqa: E402  (its Agent and its turn, and the tools of the host kit)

REPORT = ".cg-docs/work-reports/2026-11-27-poverty-brief.md"
PLAN = ".cg-docs/plans/2026-11-27-poverty-brief.md"
INTENT = ".cg-docs/brainstorms/2026-11-27-poverty-brief.md"
PLACES = {"@plan": PLAN, "@report": REPORT, "@profile": ".cg-docs/verification.md"}  # where a case may show
RISK = "repro runs the pipeline twice and writes over the outputs, which no commit holds."
ASKED = "Add the bootstrap interval of the headcount ratio and the table by region to the poverty brief."
NO = [arg for fact in ("number", "personal", "irreversible", "interface", "choice", "no-check")
      for arg in ("--fact", f"{fact}=no")]
FINDING = re.compile(r"^\s*-\s+[`*\"']*(?:\./)?([^\s`*\"':]+)(?::(\d+)(?:-(\d+))?(?::\d+)?)?[`*\"']*:\s+(\S.*)$")


def run_cg(cg, project, *args):
    done = subprocess.run([*cg, *args, "--project", str(project)], capture_output=True, text=True)
    return done.returncode, done.stdout + done.stderr


def build(folder: Path, project: Path, cg, cases):
    """The planted project as the work leaves it, before its verifiers start. With "intent" in the cases, the work
    is on a plan the human approved: its intent and the plan are approved, and each step of "work" starts its slice,
    puts back what "earlier" says the files held then, runs the Run command and records the slice's checks. With
    "report", that file is the body of the work report. With "repro", the human's yes to writing over the outputs
    that no commit holds is on record (stop rule 1 of the work playbook), and `cg.py repro` runs. With "before", that
    folder is the project at the commit the work began on, and with "scope", `cg.py scope` runs at the end (#231)."""
    def cg_ok(*args):
        code, out = run_cg(cg, project, *args)
        if code and args[0] != "evidence":  # a check may fail, as the work left it
            raise SystemExit(f"cg.py {args[0]} failed on {project}:\n{out}")
        return out
    python = "python" if os.name == "nt" else "python3"  # a path to the interpreter would be a finding of its own
    shutil.copytree(folder / "project", project)
    (project / ".cg-docs" / "plans").mkdir(parents=True)
    for name, place in (("verification.md", PLACES["@profile"]), ("plan.md", PLAN), (cases.get("intent"), INTENT)):
        if name:  # each command of the profile and of the plan runs with the interpreter this machine has
            text = (folder / name).read_text(encoding="utf-8").replace("python ", f"{python} ")
            text = text.replace("status: draft\n", f"status: draft\nintent: {INTENT}\n") if place == PLAN and \
                cases.get("intent") else text
            (project / place).parent.mkdir(parents=True, exist_ok=True)
            (project / place).write_text(text, encoding="utf-8")
    (project / ".cg-docs" / "config.json").write_text(json.dumps({"packs": ["core"], "data": cases.get("data", {})}))
    for args in (["init", "-q"], ["config", "user.name", "Planted case"], ["config", "user.email", "planted@example.org"]):
        subprocess.run(["git", "-C", str(project), *args], check=True, capture_output=True)
    if cases.get("before"):  # the project as it was, committed, and then the files as the work leaves them
        for source in (folder / cases["before"], folder / "project"):
            for path in [path for path in project.rglob("*") if path.is_file() and not {".git", ".cg-docs"} & set(path.parts)]:
                path.unlink()
            shutil.copytree(source, project, dirs_exist_ok=True)
            for args in [["add", "-A", "--", ".", ":!.cg-docs"], ["commit", "-q", "-m", "before the work"]] * (source.name != "project"):
                subprocess.run(["git", "-C", str(project), *args], check=True, capture_output=True)
    if cases.get("intent"):
        cg_ok("approve", INTENT, "--reply", "Yes.")
        cg_ok("approve", PLAN, "--reply", "Yes.")
    cg_ok("new", "work-report", "Poverty brief", "--date", "2026-11-27", *(["--plan", PLAN] * bool(cases.get("intent"))))
    report, run = project / REPORT, re.search(r"^```\n(.+)\n```", (project / PLACES["@profile"]).read_text(
        encoding="utf-8"), re.M).group(1)
    text = report.read_text(encoding="utf-8")
    report.write_text(text[:text.index("\n---\n", 4) + 5] + "\n" + (folder / cases["report"]).read_text(encoding="utf-8")
                      if cases.get("report") else re.sub(r"(## Asked\n\n)<[^<>]+>", lambda m: m.group(1) + ASKED, text),
                      encoding="utf-8")
    if not cases.get("work"):
        cg_ok("tier", *NO, "--touches", "pipeline.py", "--reads", "none", "--report", REPORT)
    for step in cases.get("work", []):  # each slice as the work did it, on the files as they were then
        kept = {name: (project / name).read_text(encoding="utf-8") for name in step.get("earlier", {})}
        for name, (now, then) in step.get("earlier", {}).items():
            (project / name).write_text(kept[name].replace(now, then), encoding="utf-8")
        cg_ok("tier", *NO, "--slice", step["slice"], "--reads", "none", "--report", REPORT)
        subprocess.run(run, shell=True, cwd=project, capture_output=True)
        for check in step["checks"]:
            cg_ok("evidence", check, "--report", REPORT)
        for name, text in kept.items():
            (project / name).write_text(text, encoding="utf-8")
    if cases.get("repro"):  # the runs write over typed outputs that no commit holds: the human's yes first
        cg_ok("tier", *[arg.replace("irreversible=no", "irreversible=yes") for arg in NO], "--touches", "pipeline.py",
              "--reads", "none", "--report", REPORT)
        text = report.read_text(encoding="utf-8")
        report.write_text(re.sub(r"(## Risk\n\n)<[^<>]+>", lambda m: m.group(1) + RISK, text), encoding="utf-8")
        cg_ok("approve", REPORT, "--reply", "Yes.")
        print(run_cg(cg, project, "repro", "--report", REPORT)[1].splitlines()[-1])  # the line that names its record
    if cases.get("scope"):  # as the work playbook runs it once every slice is done (#231)
        print(run_cg(cg, project, "scope", "--report", REPORT)[1].splitlines()[-1])


def records(project: Path):
    """The names of the records code wrote for the work report so far."""
    return {path.name for path in (project / ".cg-docs" / "evidence" / Path(REPORT).stem).glob("*.json")}


def reran(project: Path, known) -> bool:
    """True when a record of a rerun that is not among known holds every check of the plan: the verifier reran
    each declared check itself (#230)."""
    wanted = set(re.findall(r"^\|\s*(C\d+)\s*\|", (project / PLAN).read_text(encoding="utf-8"), re.M))
    for name in records(project) - set(known):
        record = json.loads((project / ".cg-docs" / "evidence" / Path(REPORT).stem / name).read_text(encoding="utf-8"))
        if record.get("kind") == "rerun" and wanted and wanted <= set(record.get("checks") or {}):
            return True
    return False


def failed(project: Path, known):
    """The records, by their path, of the runs of a command that are not among known and that failed: what the
    adversary ran in its turn to reproduce a fault (#231)."""
    folder, found = project / ".cg-docs" / "evidence" / Path(REPORT).stem, set()
    for name in records(project) - set(known):
        record = json.loads((folder / name).read_text(encoding="utf-8"))
        if record.get("kind") == "check" and record.get("exit"):
            found.add((folder / name).relative_to(project).as_posix())
    return found


def dropped(block: str) -> bool:
    """True when a verdict block lists what the verifier dropped, as the adversary lens asks (#231)."""
    return bool(re.search(r"^\s*dropped:", block, re.M))


def kickoff(cg, project, artifact, stage, verifier):
    """The kickoff that code prints for one verifier, or None when code dispatches no such verifier."""
    code, out = run_cg(cg, project, "verifiers", artifact, "--stage", stage, "--json")
    found = [v["kickoff"] for v in (json.loads(out) if code == 0 else []) if v["verifier"] == verifier]
    return found[0] if found else None


def judge(project: Path, cases, reply: str, plan=PLAN, probes=()):
    """What a reply shows, from its last verdict block and from the files: its verdict, whether each
    finding proposes the code that would replace it, and whether each case is caught. A case is caught
    by a finding whose pointer is its file, at the line that holds its text, three lines either way,
    or is one of the places under "or", where "record" is a record under .cg-docs/evidence/. One
    finding catches one case: five findings that each named a whole file caught every case (review).
    A pointer names ten lines at most, and a record that is there: as many findings that each named
    a whole file as it has cases, or a record that no run wrote, still did (review of #230). Where a case
    allows "run", the pointer is one of probes, a run of the verifier's turn that failed, and the sentence
    names the case's line, or a line of "also" (#231). A line listed under `dropped:` is no finding."""
    block = reply[reply.rfind("principle:"):] if "principle:" in reply else reply
    verdict = re.search(r"^\s*verdict:\s*(\S+)", block, re.M)
    found = [m.groups() for m in map(FINDING.match, re.split(r"\n\s*(?:dropped|note):", block)[0].splitlines()) if m]
    result = {"verdict: FLAG": bool(verdict) and verdict.group(1).strip("`*") == "FLAG",
              "each finding proposes the code that replaces it": bool(found) and all("fix:" in f[3] for f in found)}
    options, owner = {}, {}
    for case in cases:
        name, line, near = {**PLACES, "@plan": plan}.get(case["file"], case["file"]), 0, []
        if "text" in case:
            lines = (project / name).read_text(encoding="utf-8").splitlines()
            near = [next(n for n, text in enumerate(lines, 1) if want in text) for want in [case["text"], *case.get("also", [])]]
            line = near[0]
        allowed = case.get("or", [])
        key = f"{case['flag']}: {case['file']}" + (f", at '{case['text']}'" if "text" in case else "")
        options[key] = [n for n, (path, first, last, what) in enumerate(found) if (
            ("record" in allowed and (project / path).is_file() or "run" in allowed and path in probes and any(
                int(a) - 3 <= at <= int(b or a) + 3 for a, b in re.findall(rf"{re.escape(name)}:(\d+)(?:-(\d+))?", what)
                for at in near)) if path.startswith(".cg-docs/evidence/") else
            path in allowed or path == name and (not line or bool(first) and int(last or first) - int(first) <= 10
                                                 and int(first) - 3 <= line <= int(last or first) + 3))]

    def place(key, seen):  # give the case a finding of its own, moving another case to another finding if it must
        for n in options[key]:
            if n not in seen:
                seen.add(n)
                if n not in owner or place(owner[n], seen):
                    owner[n] = key
                    return True
        return False
    result.update({key: place(key, set()) for key in options})
    return result


def state(project: Path) -> str:
    """One digest of the files of the project, git's and the records of a run left out, and the byte code that
    Python writes when a check imports a module, as a rerun of the checks does (review of #230)."""
    found = hashlib.sha256()
    for path in sorted(project.rglob("*")):
        name = path.relative_to(project).as_posix()
        if path.is_file() and not name.startswith((".git/", ".cg-docs/evidence/")) and "__pycache__" not in path.parts:
            found.update(name.encode() + b"\0" + path.read_bytes())
    return found.hexdigest()


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--verifier", default="determinism", help="a folder beside this script")
    parser.add_argument("--only", default="claude,codex,kilo")
    parser.add_argument("--stages", default="", help="by default the stages that <verifier>/expected.json holds")
    parser.add_argument("--dest", default=str(Path.home() / "temp" / "cg-lens"))
    parser.add_argument("--out", default="")
    parser.add_argument("--kilo-model", default="")
    parser.add_argument("--cg", default="", help="the cg.py to run; by default the one ~/.cg/launcher.json names")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    folder, dest = HERE / args.verifier, Path(args.dest).expanduser().resolve()
    cases = json.loads((folder / "expected.json").read_text(encoding="utf-8"))
    if args.cg:
        cg = [sys.executable, str(Path(args.cg).resolve())]
    else:
        launcher = json.loads((Path.home() / ".cg" / "launcher.json").read_text(encoding="utf-8"))
        cg = [launcher["python"], launcher["cg"]]
    out, results = Path(args.out).expanduser() if args.out else dest / "out", {}
    for name in [n.strip() for n in args.only.split(",") if n.strip()]:
        program = name if args.dry_run else gate.find_program(name)
        project = dest / f"toy-poverty-{name}"
        if program is None or project.exists():
            print(f"{name}: skipped, " + ("program not found" if program is None else f"{project} exists already"))
            continue
        build(folder, project, cg, cases)
        log, results[name] = [], {}
        for stage in [s.strip() for s in args.stages.split(",") if s.strip()] or [s for s in ("review", "plan") if s in cases]:
            text, agent = kickoff(cg, project, PLAN if stage == "plan" else REPORT, stage, cases["verifier"]), \
                gate.Agent(name, program, args.kilo_model)
            if text is None or args.dry_run:
                print(f"== {name}, {stage} stage: no agent started\n{text}\n\nwould run: "
                      f"{agent.command('<the kickoff above>', True)}\n")
                results[name][f"{stage}: code dispatches {cases['verifier']}"] = text is not None
                continue
            before, known = state(project), records(project)
            reply = gate.turn(agent, project, text, True, log, f"{stage} stage")
            checks = judge(project, cases[stage], reply, probes=failed(project, known))
            checks["the verifier changed no file of the project"] = state(project) == before
            if cases.get("dropped"):
                checks["the verifier listed what it dropped"] = dropped(reply[reply.rfind("principle:"):])
            if cases.get("reruns") and stage == "review":
                checks["the verifier reran every check of the plan itself"] = reran(project, known)
            results[name].update({f"{stage}: {key}": ok for key, ok in checks.items()})
        out.mkdir(parents=True, exist_ok=True)
        (out / f"{name}-transcript.md").write_text(gate.sanitize("\n".join(log), project), encoding="utf-8")
        for check, ok in results[name].items():
            print(f"  {'pass' if ok else 'FAIL'}  {check}", flush=True)
    out.mkdir(parents=True, exist_ok=True)
    (out / "results.json").write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    return 1 if any(not ok for checks in results.values() for ok in checks.values()) else 0


if __name__ == "__main__":
    sys.exit(main())
