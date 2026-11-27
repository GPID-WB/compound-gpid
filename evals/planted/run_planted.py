"""Run a verifier's lens on its planted project through a coding agent, and judge what it returns (#229).

Usage: <python> evals/planted/run_planted.py [--verifier determinism] [--only claude,codex,kilo]
                                             [--stages review,plan] [--dest DIR] [--out DIR]
                                             [--kilo-model provider/model] [--cg PATH] [--dry-run]

CI holds what code finds of each planted violation (tests/core/test_determinism.py). The rest is by
judgement: a model reads the lens, and CI cannot start a model, so this script gives that part a run.
For each agent it builds a copy of the planted project in DIR (default ~/temp/cg-lens): the files of
<verifier>/project/, its verification profile, the rule for its data file, and git with no commit, so
that every file is the change. For the review stage it adds a work report, the risk of the work and
the record of `cg.py repro`, as the work playbook leaves them; for the plan stage, <verifier>/plan.md
as a draft plan. `cg.py verifiers` prints the kickoff, and the agent gets it, in a new session, with
no word added (the guide's rule "Verifiers").

It judges each reply from its verdict block and from the files: the verdict is FLAG; each finding
proposes the code that would replace it (`fix:`); each case of <verifier>/expected.json is caught; and
the verifier changed no file of the project but the records of a run. The agents run with approval
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
ASKED = "Add the bootstrap interval of the headcount ratio and the table by region to the poverty brief."
NO = [arg for fact in ("number", "personal", "irreversible", "interface", "choice", "no-check")
      for arg in ("--fact", f"{fact}=no")]
FINDING = re.compile(r"^\s*-\s+[`*\"']*(?:\./)?([^\s`*\"':]+)(?::(\d+)(?:-(\d+))?(?::\d+)?)?[`*\"']*:\s+(\S.*)$")


def run_cg(cg, project, *args):
    done = subprocess.run([*cg, *args, "--project", str(project)], capture_output=True, text=True)
    return done.returncode, done.stdout + done.stderr


def build(folder: Path, project: Path, cg, cases):
    """The planted project as the work leaves it, before its verifiers start."""
    shutil.copytree(folder / "project", project)
    (project / ".cg-docs" / "plans").mkdir(parents=True)
    python = "python" if os.name == "nt" else "python3"  # a path to the interpreter would be a finding of its own
    profile = (folder / "verification.md").read_text(encoding="utf-8").replace("\npython ", f"\n{python} ")
    (project / ".cg-docs" / "verification.md").write_text(profile, encoding="utf-8")
    (project / ".cg-docs" / "config.json").write_text(json.dumps({"packs": ["core"], "data": cases.get("data", {})}))
    shutil.copy(folder / "plan.md", project / PLAN)
    subprocess.run(["git", "init", "-q", str(project)], check=True, capture_output=True)
    for args in (("new", "work-report", "Poverty brief", "--date", "2026-11-27"),
                 ("tier", *NO, "--touches", "pipeline.py", "--reads", "none", "--report", REPORT)):
        code, out = run_cg(cg, project, *args)
        if code:
            raise SystemExit(f"cg.py {args[0]} failed on {project}:\n{out}")
    report = project / REPORT
    report.write_text(re.sub(r"(## Asked\n\n)<[^<>]+>", lambda m: m.group(1) + ASKED, report.read_text(encoding="utf-8")),
                      encoding="utf-8")
    print(run_cg(cg, project, "repro", "--report", REPORT)[1].splitlines()[-1])  # the line that names its record


def kickoff(cg, project, artifact, stage, verifier):
    """The kickoff that code prints for one verifier, or None when code dispatches no such verifier."""
    code, out = run_cg(cg, project, "verifiers", artifact, "--stage", stage, "--json")
    found = [v["kickoff"] for v in (json.loads(out) if code == 0 else []) if v["verifier"] == verifier]
    return found[0] if found else None


def judge(project: Path, cases, reply: str, plan=PLAN):
    """What a reply shows, from its last verdict block and from the files: its verdict, whether each
    finding proposes the code that would replace it, and whether each case is caught. A case is caught
    by a finding whose pointer is its file, at the line that holds its text, three lines either way,
    or is one of the places under "or", where "record" is a record under .cg-docs/evidence/. One
    finding catches one case: five findings that each named a whole file caught every case (review)."""
    block = reply[reply.rfind("principle:"):] if "principle:" in reply else reply
    verdict = re.search(r"^\s*verdict:\s*(\S+)", block, re.M)
    found = [m.groups() for m in map(FINDING.match, block.split("\nnote:")[0].splitlines()) if m]
    result = {"verdict: FLAG": bool(verdict) and verdict.group(1).strip("`*") == "FLAG",
              "each finding proposes the code that replaces it": bool(found) and all("fix:" in f[3] for f in found)}
    options, owner = {}, {}
    for case in cases:
        name, line = plan if case["file"] == "@plan" else case["file"], 0
        if "text" in case:
            lines = (project / name).read_text(encoding="utf-8").splitlines()
            line = next(number for number, text in enumerate(lines, 1) if case["text"] in text)
        allowed = case.get("or", [])
        key = f"{case['flag']}: {case['file']}" + (f", at '{case['text']}'" if "text" in case else "")
        options[key] = [n for n, (path, first, last, _) in enumerate(found) if (
            ("record" in allowed) if path.startswith(".cg-docs/evidence/") else path in allowed or path == name and (
                not line or bool(first) and int(first) - 3 <= line <= int(last or first) + 3))]

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
    """One digest of the files of the project, git's and the records of a run left out."""
    found = hashlib.sha256()
    for path in sorted(project.rglob("*")):
        name = path.relative_to(project).as_posix()
        if path.is_file() and not name.startswith((".git/", ".cg-docs/evidence/")):
            found.update(name.encode() + b"\0" + path.read_bytes())
    return found.hexdigest()


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--verifier", default="determinism", help="a folder beside this script")
    parser.add_argument("--only", default="claude,codex,kilo")
    parser.add_argument("--stages", default="review,plan")
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
        for stage in [s.strip() for s in args.stages.split(",") if s.strip()]:
            text, agent = kickoff(cg, project, PLAN if stage == "plan" else REPORT, stage, cases["verifier"]), \
                gate.Agent(name, program, args.kilo_model)
            if text is None or args.dry_run:
                print(f"== {name}, {stage} stage: no agent started\n{text}\n\nwould run: "
                      f"{agent.command('<the kickoff above>', True)}\n")
                results[name][f"{stage}: code dispatches {cases['verifier']}"] = text is not None
                continue
            before = state(project)
            checks = judge(project, cases[stage], gate.turn(agent, project, text, True, log, f"{stage} stage"))
            checks["the verifier changed no file of the project"] = state(project) == before
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
