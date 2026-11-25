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

Raw answers land in spike/host-matrix/results/<time>/, ignored by git because
they contain local paths. Standard library only.
"""
import argparse
import getpass
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import time
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
        done = subprocess.run([str(part) for part in command], cwd=project,
                              stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT, timeout=LIMIT)
        text, end = done.stdout, f"[exit code: {done.returncode}]"
    except subprocess.TimeoutExpired as late:
        text, end = late.stdout or b"", f"[stopped after {LIMIT} seconds]"
    except OSError as failed:
        text, end = b"", f"[could not start: {failed}]"
    body = text.decode("utf-8", errors="replace").replace("\r\n", "\n")
    (out / f"{label}.txt").write_text(f"$ {shown}\n\n{body}\n{end}\n", encoding="utf-8")


def sanitize(text, project):
    """Remove terminal colors, local paths, the user name and email addresses."""
    text = re.sub(r"\x1b\[[0-9;?]*[A-Za-z]", "", text)
    places = [(project, "<project>"), (Path(tempfile.gettempdir()), "<tmp>"),
              (Path.home(), "~")]
    for place, word in places:
        for form in {str(place), str(place.resolve())}:
            for spelled in {form, form.replace("\\", "/"), form.replace("\\", "\\\\")}:
                text = re.sub(re.escape(spelled), lambda _: word, text, flags=re.IGNORECASE)
    user = getpass.getuser()
    if len(user) >= 3:
        text = re.sub(re.escape(user), "<user>", text, flags=re.IGNORECASE)
    return re.sub(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+\.[A-Za-z0-9.-]+", "<email>", text)


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


def main():
    parser = argparse.ArgumentParser(description="Host matrix, command-line part.")
    parser.add_argument("--only", default=os.environ.get("ONLY", ""))
    parser.add_argument("--kilo-model", default=os.environ.get("KILO_MODEL", ""))
    parser.add_argument("--layout", default=os.environ.get("LAYOUT", "link"),
                        choices=("link", "copy", "agents-only", "claude-only"))
    parser.add_argument("--project-parent", default=None)
    parser.add_argument("--report", action="store_true")
    args = parser.parse_args()
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
