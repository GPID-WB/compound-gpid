"""Host matrix, command-line part (issue #211). One script for macOS and Windows.

Run from the repository root, in a terminal:

    macOS     python3 spike/host-matrix/run_cli_checks.py
    Windows   py -3 spike\\host-matrix\\run_cli_checks.py

It starts the Claude Code, Codex and Kilo command-line programs that the editor
extensions bundle, sends each the same prompts, and saves what they answer. It
installs two test skills for the run and removes them at the end. It changes
nothing else. Expect a few minutes and a small token cost on each account.

Options (each also reads the environment variable in brackets):

    --only claude,codex,kilo    which programs to run                [ONLY]
    --kilo-model provider/model model for Kilo; its default may not call tools.
                                The provider decides who pays: kilo/... needs
                                credits on the Kilo account, openai/... uses the
                                account signed in with OpenAI.       [KILO_MODEL]
    --layout link               where the test skills go             [LAYOUT]
                                  link         real folder in ~/.agents/skills,
                                               link from ~/.claude/skills
                                  copy         a real copy in both folders
                                  agents-only  only ~/.agents/skills
                                  claude-only  only ~/.claude/skills
    --project-parent DIR        create the throwaway project inside DIR, for
                                example a OneDrive folder with spaces in its name
    --report                    also write a copy with local paths, the user
                                name and email addresses removed, to
                                spike/host-matrix/reports/ (tracked by git)

    --manual                    prepare the test for hosts that only run inside
                                the editor (Copilot, Kilo's panel): install the
                                test skills, make a test project and an answer
                                sheet in the home folder, print what to do
    --manual-done               collect the answer sheet and remove all of it

Raw answers land in spike/host-matrix/results/<time>/, ignored by git because
they contain local paths. Standard library only.
"""
import argparse
import getpass
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import time
import unicodedata
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILLS = ("cg-spike-hello", "cg-spike-auto")
WINDOWS = os.name == "nt"
LIMIT = 240  # seconds per prompt

P1 = ("Do not run any tool. Answer only from what is already in your context. "
      "(a) List every skill you can see whose name starts with cg-spike. If one appears more "
      "than once, list it once per appearance. (b) For each, say whether you may invoke it "
      "yourself or only the human may. (c) Which of these markers appear in your instructions: "
      "CG-SPIKE-POINTER-AGENTS, CG-SPIKE-POINTER-CLAUDE? (d) Name your todo tool and your "
      "subagent tool, or say none.")
P2 = "/cg-spike-hello"
P3 = "I saw a purple heron today."
P4 = "Please run the host probe."

HOSTS = {  # name: (extension folder prefix, known path inside it, override variable)
    "claude": ("anthropic.claude-code-", "resources/native-binary/claude", "CLAUDE_BIN"),
    "codex": ("openai.chatgpt-", "bin/*/codex", "CODEX_BIN"),
    "kilo": ("kilocode.kilo-code-", "bin/kilo", "KILO_BIN"),
}


def version_key(path):
    return [int(n) for n in re.findall(r"\d+", path.name)]


def find_program(name):
    """Newest bundled copy of a host's command-line program, or None."""
    prefix, known, variable = HOSTS[name]
    if os.environ.get(variable):
        return Path(os.environ[variable])
    endings = (".exe", ".cmd") if WINDOWS else ("",)
    for editor in (".vscode", ".vscode-insiders", ".positron"):
        root = Path.home() / editor / "extensions"
        for ext in sorted(root.glob(prefix + "*"), key=version_key, reverse=True):
            for ending in endings:
                found = sorted(ext.glob(known + ending)) or sorted(ext.rglob(name + ending))
                found = [f for f in found if f.is_file() and (WINDOWS or os.access(f, os.X_OK))]
                if found:
                    return found[0]
    on_path = shutil.which(name)
    return Path(on_path) if on_path else None


def remove(path):
    """Remove a link, a Windows junction or a folder, without following links."""
    for attempt in (os.unlink, os.rmdir, shutil.rmtree):
        if not os.path.lexists(path):
            return
        try:
            attempt(path)
        except OSError:
            continue


def link(target, at):
    """Link `at` to `target`. Returns the kind made, or None if no link is allowed."""
    try:
        os.symlink(target, at, target_is_directory=True)
        return "symlink"
    except OSError:
        pass
    if WINDOWS:
        made = subprocess.run(["cmd", "/c", "mklink", "/J", str(at), str(target)],
                              capture_output=True)
        if made.returncode == 0:
            return "junction"
    return None


def install_skills(layout):
    """Put the test skills in place. Returns a sentence saying what was done."""
    agents, claude = Path.home() / ".agents" / "skills", Path.home() / ".claude" / "skills"
    remove_skills()
    done = layout
    for skill in SKILLS:
        source = HERE / "skills" / skill
        if layout != "claude-only":
            agents.mkdir(parents=True, exist_ok=True)
            shutil.copytree(source, agents / skill)
        if layout in ("claude-only", "copy"):
            claude.mkdir(parents=True, exist_ok=True)
            shutil.copytree(source, claude / skill)
        if layout == "link":
            claude.mkdir(parents=True, exist_ok=True)
            kind = link(agents / skill, claude / skill)
            if kind is None:
                shutil.copytree(source, claude / skill)
                kind = "copy, because this machine did not allow a link"
            done = f"link ({kind})"
    return done


def remove_skills():
    for folder in (".agents", ".claude"):
        for skill in SKILLS:
            remove(Path.home() / folder / "skills" / skill)


def run(out, project, label, command):
    print(">>", label, flush=True)
    if WINDOWS and str(command[0]).lower().endswith((".cmd", ".bat")):
        command = ["cmd", "/c", *command]
    shown = " ".join(str(part) for part in command)
    try:
        # PWD too: a program that reads it would otherwise take the folder the
        # script was started from as its project, and load that folder's files.
        done = subprocess.run([str(part) for part in command], cwd=project,
                              env=dict(os.environ, PWD=str(project)),
                              stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT, timeout=LIMIT)
        text, end = done.stdout, f"[exit code: {done.returncode}]"
    except subprocess.TimeoutExpired as late:
        text, end = late.stdout or b"", f"[stopped after {LIMIT} seconds]"
    except OSError as failed:
        text, end = b"", f"[could not start: {failed}]"
    body = text.decode("utf-8", errors="replace").replace("\r\n", "\n")
    (out / f"{label}.txt").write_text(f"$ {shown}\n\n{body}\n{end}\n", encoding="utf-8")


def sanitize(text, project, names=None):
    """Remove terminal colors, local paths, email addresses, the user name, the name git
    records for the person, and session IDs. names defaults to the user.name git gives in the project, which is the one `cg.py approve` prints."""
    text = re.sub(r"\x1b\[[0-9;?]*[A-Za-z]", "", text)
    places = [(project, "<project>"), (Path(tempfile.gettempdir()), "<tmp>"),
              (Path.home(), "~")]
    for place, word in places:
        for form in {str(place), str(place.resolve())}:
            for spelled in {form, form.replace("\\", "/"), form.replace("\\", "\\\\")}:
                text = re.sub(re.escape(spelled), lambda _: word, text, flags=re.IGNORECASE)
    # A home folder typed another way by the agent: its name goes whole (lens run adversary-2, #231).
    text = re.sub(r"(?i)(/Users/|/home/|[A-Z]:(?:\\){1,2}Users(?:\\){1,2})[^/\\\s\"'`<>]+",
                  lambda found: found.group(1) + "<user>", text)
    # Addresses go first: once the user name is replaced inside one, it is no longer read as an address.
    # A domain ends in letters, so "python@3.14" in a Homebrew path is not an address.
    text = re.sub(r"[A-Za-z0-9._%+-]+(?:@|%40)(?:[A-Za-z0-9-]+\.)+[A-Za-z]{2,}\b", "<email>", text)
    if names is None:
        asked = subprocess.run(["git", "-C", str(project), "config", "--get", "user.name"],
                               capture_output=True, text=True) \
            if shutil.which("git") else None
        names = [asked.stdout.strip()] if asked and asked.returncode == 0 else []
    for name in names:
        # Each spelling a transcript can hold: as typed, composed or decomposed, JSON-escaped, and
        # without its accents (review of #225: a name with letters outside ASCII stayed).
        forms = {unicodedata.normalize(norm, name) for norm in ("NFC", "NFD")}
        forms |= {json.dumps(form)[1:-1] for form in set(forms)}
        forms.add("".join(c for c in unicodedata.normalize("NFD", name) if not unicodedata.combining(c)))
        for form in sorted(forms, key=len, reverse=True):
            if len(form) >= 3:
                text = re.sub(re.escape(form), "<name>", text, flags=re.IGNORECASE)
    user = getpass.getuser()
    if len(user) >= 3:
        text = re.sub(re.escape(user), "<user>", text, flags=re.IGNORECASE)
    return re.sub(r"(?im)^(session id:\s*)\S+", r"\1<removed>", text)


def write_report(out, project, stamp):
    reports = HERE / "reports"
    reports.mkdir(exist_ok=True)
    report = reports / f"{platform.system().lower()}-{stamp}.txt"
    parts = []
    for answer in sorted(out.glob("*.txt")):
        if answer.stem.endswith(("-help", "-models")):
            continue  # long, and the model list shows what the account can use
        parts.append(f"===== {answer.stem}\n{answer.read_text(encoding='utf-8')}")
    report.write_text(sanitize("\n".join(parts), project), encoding="utf-8")
    return report


MANUAL_PROJECT = Path.home() / "cg-spike-project"
MANUAL_SHEET = Path.home() / "cg-spike-answers.txt"
MANUAL_MARKERS = {"AGENTS.md": "AGENTS", "CLAUDE.md": "CLAUDE",
                  ".github/copilot-instructions.md": "COPILOT"}
MANUAL_P1 = P1.replace("CG-SPIKE-POINTER-CLAUDE?",
                       "CG-SPIKE-POINTER-CLAUDE, CG-SPIKE-POINTER-COPILOT?")


def manual_start(layout):
    """Install the test skills, make the test project and the answer sheet."""
    layout = install_skills(layout)
    for name, marker in MANUAL_MARKERS.items():
        target = MANUAL_PROJECT / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(f"Marker for the host test: CG-SPIKE-POINTER-{marker}\n",
                          encoding="utf-8")
    steps = [("1", "Paste this prompt", MANUAL_P1), ("2", "Type this", P2),
             ("3", "Paste this prompt", P3), ("4", "Paste this prompt", P4)]
    sheet = [
        "HOST TEST INSIDE THE EDITOR (about 10 minutes). Skill layout: " + layout,
        "",
        "You need two windows:",
        "  - the editor (VS Code or Positron) with the folder cg-spike-project open.",
        "    You chat there. Nothing has to be run in a terminal.",
        "  - this file, open in a plain text program (TextEdit, Notepad).",
        "    You paste the replies here.",
        "Do NOT open this file inside the editor: the editor can show an open file",
        "to the agent, and this file holds the words the test looks for.",
        "",
        "Do this twice: first in the Copilot chat panel (pick the mode 'Agent'),",
        "then in the Kilo chat panel.",
        "  1. Start a NEW chat.",
        "  2. Copy the line under 'Step 1' below, paste it in the chat, send it.",
        "  3. When the reply is complete, copy all of it and paste it here under",
        "     'Reply to step 1'. If the agent asks permission to run something,",
        "     allow it, and count how many times it asked.",
        "  4. Start a NEW chat for step 2, then step 3, then step 4, the same way.",
        "  5. Answer the three short questions at the end of that host's block.",
        "If something does not work, write what you saw. That is a result too.",
        "Save this file when you are done.",
        "",
    ]
    for host in ("COPILOT (agent mode)", "KILO"):
        sheet += ["#" * 70, f"HOST: {host}", "Version and model used: ", ""]
        for number, verb, prompt in steps:
            sheet += [f"--- Step {number}. {verb}:", prompt, "",
                      f"Reply to step {number}:", "", ""]
        sheet += ["--- Three questions, from what you saw:",
                  "a. Type / in the chat box. Is cg-spike-hello offered? Once or twice? ",
                  "b. Is cg-spike-auto also offered after / ? ",
                  "c. How many approval prompts did step 2 show you? ", ""]
    MANUAL_SHEET.write_text("\n".join(sheet), encoding="utf-8")
    print("Ready.\n  Test project:", MANUAL_PROJECT, "\n  Answer sheet:", MANUAL_SHEET)
    print("Open the test project in the editor and the answer sheet in a plain text "
          "program (not in the editor), then follow the sheet.\nRestart the editor "
          "first if the skills do not appear.\nWhen you are done, run this script "
          "with --manual-done.")


def manual_done(report):
    """Keep the answer sheet with the results, then remove everything."""
    stamp = time.strftime("%Y%m%d-%H%M%S")
    out = HERE / "results" / stamp
    if MANUAL_SHEET.exists():
        out.mkdir(parents=True)
        shutil.copy(MANUAL_SHEET, out / "manual-answers.txt")
        print("Answers saved in:\n ", out)
        if report:
            print("Report without local paths, for git:\n ",
                  write_report(out, MANUAL_PROJECT, stamp + "-manual"))
    else:
        print("No answer sheet found at", MANUAL_SHEET)
    remove_skills()
    shutil.rmtree(MANUAL_PROJECT, ignore_errors=True)
    remove(MANUAL_SHEET)
    print("Test skills, test project and answer sheet removed.")


def main():
    parser = argparse.ArgumentParser(description="Host matrix, command-line part.")
    parser.add_argument("--manual", action="store_true")
    parser.add_argument("--manual-done", action="store_true")
    parser.add_argument("--only", default=os.environ.get("ONLY", ""))
    parser.add_argument("--kilo-model", default=os.environ.get("KILO_MODEL", ""))
    parser.add_argument("--layout", default=os.environ.get("LAYOUT", "link"),
                        choices=("link", "copy", "agents-only", "claude-only"))
    parser.add_argument("--project-parent", default=None)
    parser.add_argument("--report", action="store_true")
    args = parser.parse_args()
    if args.manual:
        return manual_start(args.layout)
    if args.manual_done:
        return manual_done(args.report)
    wanted = [h for h in args.only.split(",") if h] or list(HOSTS)
    unknown = sorted(set(wanted) - set(HOSTS))
    if unknown:
        parser.error(f"unknown program: {', '.join(unknown)}")

    stamp = time.strftime("%Y%m%d-%H%M%S")
    out = HERE / "results" / stamp
    out.mkdir(parents=True)
    project = Path(tempfile.mkdtemp(prefix="cg-spike-", dir=args.project_parent))
    try:
        layout = install_skills(args.layout)
        if shutil.which("git"):
            subprocess.run(["git", "init", "-q"], cwd=project)
        agents_md, claude_md = project / "AGENTS.md", project / "CLAUDE.md"
        agents_md.write_text("Marker for the host test: CG-SPIKE-POINTER-AGENTS\n", encoding="utf-8")
        claude_marker = "Marker for the host test: CG-SPIKE-POINTER-CLAUDE\n"
        claude_md.write_text(claude_marker, encoding="utf-8")
        programs = {name: find_program(name) for name in wanted}
        (out / "run-info.txt").write_text("\n".join([
            f"platform: {platform.system()} {platform.release()}",
            f"python: {sys.version.split()[0]}",
            f"skill layout: {layout}",
            f"project: {project}",
            f"project path has spaces: {' ' in str(project)}",
            f"project under OneDrive: {'onedrive' in str(project).lower()}",
            f"kilo model: {args.kilo_model or 'the default'}",
            *[f"{name}: {path or 'not found'}" for name, path in programs.items()],
        ]) + "\n", encoding="utf-8")

        claude, codex, kilo = (programs.get(name) for name in ("claude", "codex", "kilo"))
        if claude:
            allow = ["--allowedTools", "Skill", "Read",
                     "Bash(python3:*)", "Bash(python:*)", "Bash(py:*)"]
            run(out, project, "claude-0-version", [claude, "--version"])
            run(out, project, "claude-1-inventory", [claude, "-p", P1])
            run(out, project, "claude-2-invoke", [claude, "-p", P2, *allow])
            run(out, project, "claude-3-auto", [claude, "-p", P3, *allow])
            run(out, project, "claude-4-no-auto", [claude, "-p", P4, *allow])
            # Same project, but CLAUDE.md only imports AGENTS.md.
            claude_md.write_text("@AGENTS.md\n", encoding="utf-8")
            run(out, project, "claude-5-import", [claude, "-p", P1])
            claude_md.write_text(claude_marker, encoding="utf-8")
        if codex:
            base = [codex, "exec", "--skip-git-repo-check"]
            run(out, project, "codex-0-version", [codex, "--version"])
            run(out, project, "codex-0-help", [codex, "exec", "--help"])
            run(out, project, "codex-1-inventory", [*base, P1])
            run(out, project, "codex-2-invoke", [*base, "$cg-spike-hello"])
            run(out, project, "codex-2b-invoke-slash", [*base, P2])
            run(out, project, "codex-3-auto", [*base, P3])
            run(out, project, "codex-4-no-auto", [*base, P4])
        if kilo:
            base = [kilo, "run", *(["-m", args.kilo_model] if args.kilo_model else [])]
            run(out, project, "kilo-0-version", [kilo, "--version"])
            run(out, project, "kilo-0-help", [kilo, "run", "--help"])
            run(out, project, "kilo-0-models", [kilo, "models"])
            run(out, project, "kilo-1-inventory", [*base, P1])
            run(out, project, "kilo-2-invoke", [*base, P2])
            run(out, project, "kilo-3-auto", [*base, P3])
            run(out, project, "kilo-4-no-auto", [*base, P4])
        report = write_report(out, project, stamp) if args.report else None
    finally:
        remove_skills()
        shutil.rmtree(project, ignore_errors=True)

    print("\nDone. Raw results are in:\n ", out)
    if report:
        print("Report without local paths, for git:\n ", report)
    missing = [name for name, path in programs.items() if not path]
    if missing:
        print("Not found on this machine:", ", ".join(missing))


if __name__ == "__main__":
    main()
