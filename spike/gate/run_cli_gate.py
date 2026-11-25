"""Run steps B to D of the gate (#223) in the command-line agents, without a human.

Usage: <python> spike/gate/run_cli_gate.py [--only claude,codex,kilo,kilo-panel] [--dest DIR]
                                           [--kilo-model provider/model] [--out DIR]

For each agent: a fresh copy of the toy project (make_toy.py) in DIR
(default ~/temp/cg-gate/rerun), then the steps below. `kilo-panel` is Kilo
sent a typed /cg the way Kilo's editor panel and Posit Assistant send it: the
body of the guide's SKILL.md as the human's message, then the skill's folder,
then what the human typed after /cg. From the command line `kilo run "/cg"`
sends the three characters, a path that never failed (#223, Fable's review).

  B  "/cg" (Codex: "$cg"), then a yes that states the data rule.
     Pass: nothing written before the yes; afterwards status shows
     phase ready and the survey on its data line.
  C  in a new session, "/cg" with the headcount request, then "Yes, proceed."
     Pass: no R file changed before the yes (the hard stop); afterwards
     a completed work report and headcount() in an R file.
  D  in a new session, a plain request.
     Pass: no new work report (the guide did not run), and the reply
     opens with a sentence on /cg, as the pointer block asks.

The agents run with their approval prompts turned off, as most people run
them. Each answer is judged from the files and from status, not from what
the agent says. Transcripts, with local paths and the user name removed,
and results.json go to --out (default .cg-docs/gate-m1/rerun/ in this hub), as
<agent>-transcript.md: a file named claude.md would be loaded by Claude Code
as project instructions on a file system that ignores case.
Exit code 1 when a check fails.
"""
import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

GATE = Path(__file__).resolve().parent
HUB = GATE.parents[1]
sys.path.insert(0, str(GATE))
sys.path.insert(0, str(HUB / "spike" / "host-matrix"))
import make_toy  # noqa: E402
from run_cli_checks import find_program, sanitize  # noqa: E402

LIMIT = 1200  # seconds per turn
SURVEY = "inst/extdata/survey.csv"
YES_SETUP = (f"Yes. The survey {SURVEY} is synthetic and its classification is Public, "
             "and you may read Public data.")
REQUEST = ("Add a function `headcount(dt, line = 3)` that returns the weighted share of households "
           "with welfare below the line, with a testthat check. For the toy survey I expect 0.153846.")
PLAIN = "Write a function that returns the number of households in the survey."
SKILL = Path.home() / ".agents" / "skills" / "cg"
GUIDE_MARKER = "[the text of the installed cg/SKILL.md]"


def panel_message(request="", skill=SKILL):
    """A typed /cg as Kilo's panel sends it (measured in Kilo's session store)."""
    body = (skill / "SKILL.md").read_text(encoding="utf-8").split("\n---\n", 1)[1].strip("\n")
    text = (f"{body}\n\n\nBase directory for this skill: {skill}\n"
            "Relative paths in this skill (e.g., scripts/, references/) are relative to this base directory.")
    return f"{text}\n\n{request}" if request else text


class Agent:
    """One command-line agent: start a session, continue it, return the reply text."""

    def __init__(self, name, program, kilo_model):
        self.name, self.program, self.kilo_model = name, str(program), kilo_model
        self.session = None

    def command(self, prompt, new):
        p = self.program
        if self.name == "claude":
            resume = [] if new else ["--resume", self.session]
            # stream-json gives every message of the turn; "json" gives only the last (Fable's review).
            return [p, "-p", prompt, "--output-format", "stream-json", "--verbose",
                    "--dangerously-skip-permissions", *resume]
        if self.name == "codex":
            # `exec resume` takes no --sandbox, so the sandbox goes in as a setting.
            options = ["--json", "--skip-git-repo-check", "-c", 'sandbox_mode="workspace-write"']
            return [p, "exec", *options, prompt] if new else [p, "exec", "resume", *options, self.session, prompt]
        model = ["-m", self.kilo_model] if self.kilo_model else []
        return [p, "run", "--auto", *model, *([] if new else ["--continue"]), prompt]

    def guide(self, request=""):
        if self.name == "kilo-panel":
            return panel_message(request)
        word = "$cg" if self.name == "codex" else "/cg"
        return f"{word} {request}".strip()

    def reply(self, output):
        """The reply text, every message of the turn in order, and the session id."""
        if self.name == "claude":
            texts = []
            for line in output.splitlines():
                try:
                    event = json.loads(line)
                except ValueError:
                    continue
                self.session = event.get("session_id") or self.session
                if event.get("type") == "assistant":
                    texts += [c.get("text", "") for c in event.get("message", {}).get("content", [])
                              if c.get("type") == "text" and c.get("text", "").strip()]
            return "\n\n".join(texts) or output
        if self.name == "codex":
            texts = []
            for line in output.splitlines():
                try:
                    event = json.loads(line)
                except ValueError:
                    continue
                if event.get("type") == "thread.started":
                    self.session = event.get("thread_id") or self.session
                item = event.get("item") or {}
                if event.get("type") == "item.completed" and item.get("type") == "agent_message":
                    texts.append(item.get("text", ""))
            return "\n\n".join(texts) or output
        return output


def turn(agent, project, prompt, new, log, label):
    command = agent.command(prompt, new)
    try:
        done = subprocess.run(command, cwd=project, env=dict(os.environ, PWD=str(project)),
                              stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=LIMIT)
        output, end = done.stdout + done.stderr, f"[exit code: {done.returncode}]"
    except subprocess.TimeoutExpired as late:
        output, end = (late.stdout or b"").decode("utf-8", "replace"), f"[stopped after {LIMIT} seconds]"
    text = agent.reply(output) if "exit code" in end else output
    shown = prompt.replace(panel_message(), GUIDE_MARKER) if agent.name == "kilo-panel" else prompt
    log.append(f"### {label}\n\n> {shown}\n\n{text}\n\n{end}\n")
    return text


def status(project):
    launcher = json.loads((Path.home() / ".cg" / "launcher.json").read_text(encoding="utf-8"))
    done = subprocess.run([launcher["python"], launcher["cg"], "status", "--json", "--project", str(project)],
                          capture_output=True, text=True)
    try:
        return json.loads(done.stdout)
    except ValueError:
        return {}


def changed(project):
    done = subprocess.run(["git", "-C", str(project), "status", "--porcelain", "--untracked-files=all"],
                          capture_output=True, text=True)
    return [line[3:] for line in done.stdout.splitlines()]


def reports(project):
    return {p.name: ("status: completed" in p.read_text(encoding="utf-8"))
            for p in (project / ".cg-docs" / "work-reports").glob("*.md")}


def run_agent(agent, project):
    log, checks = [], {}
    # B: setup
    reply = turn(agent, project, agent.guide(), True, log, "B1 setup")
    checks["B: nothing written before the yes"] = not (project / ".cg-docs").exists()
    checks["B: proposal names lang-r and data.table-collapse"] = "lang-r" in reply and "data.table-collapse" in reply
    turn(agent, project, YES_SETUP, False, log, "B2 yes")
    state = status(project)
    checks["B: phase ready"] = state.get("phase") == "ready"
    checks["B: data rule recorded"] = any(line.startswith(SURVEY) for line in state.get("data", []))
    # C: quick task with a hard stop
    before = set(changed(project))
    turn(agent, project, agent.guide(REQUEST), True, log, "C1 request")
    touched = [f for f in set(changed(project)) - before if f.startswith(("R/", "tests/", "NAMESPACE"))]
    checks["C: stopped before changing code"] = not touched
    turn(agent, project, "Yes, proceed.", False, log, "C2 yes")
    checks["C: headcount() defined in R/"] = any(re.search(r"^headcount\s*<-", f.read_text(encoding="utf-8"), re.M)
                                                 for f in (project / "R").glob("*.R"))
    checks["C: a completed work report"] = any(reports(project).values())
    # D: plain request
    count = len(reports(project))
    reply = turn(agent, project, PLAIN, True, log, "D plain request")
    checks["D: no new work report"] = len(reports(project)) == count
    opening = reply.strip()[:300]
    checks["D: reply opens with a sentence on /cg"] = "/cg" in opening or "$cg" in opening
    return checks, log


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--only", default="claude,codex,kilo,kilo-panel")
    parser.add_argument("--dest", default=str(Path.home() / "temp" / "cg-gate" / "rerun"))
    parser.add_argument("--kilo-model", default="")
    parser.add_argument("--out", default=str(HUB / ".cg-docs" / "gate-m1" / "rerun"))
    args = parser.parse_args(argv)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    results, failed = {}, False
    for name in [n.strip() for n in args.only.split(",") if n.strip()]:
        program = find_program("kilo" if name == "kilo-panel" else name)
        if program is None:
            print(f"{name}: program not found, skipped")
            continue
        if make_toy.main(["--dest", args.dest, "--hosts", name]) != 0:
            return 1
        project = Path(args.dest).expanduser().resolve() / f"toy-r-{name}"
        print(f"{name}: running B to D in {project}", flush=True)
        checks, log = run_agent(Agent(name, program, args.kilo_model), project)
        results[name] = checks
        failed |= not all(checks.values())
        (out / f"{name}-transcript.md").write_text(sanitize("\n".join(log), project), encoding="utf-8")
        for check, ok in checks.items():
            print(f"  {'pass' if ok else 'FAIL'}  {check}", flush=True)
    (out / "results.json").write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
