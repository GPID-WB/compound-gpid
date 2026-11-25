"""cg.py: the deterministic tooling of the core pack.

Usage, with the interpreter that ~/.cg/launcher.json records as <python>:
  "<python>" cg.py doctor [--project PATH]
  "<python>" cg.py status [--project PATH] [--json]
  "<python>" cg.py new TYPE TITLE... [--project PATH] [--date YYYY-MM-DD]
  "<python>" cg.py packs [--json]

PATH may be any folder inside the project: the commands use the nearest
folder above it that holds .cg-docs/, else the root of its git repository.

Standard library only, Python 3.9 or later, one implementation for every
operating system. Every write is atomic and each record is its own file.
Output depends only on the files read, so a rerun on unchanged files prints
the same thing.
"""
import argparse
import datetime
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

CG_DIR = Path(__file__).resolve().parent.parent  # the cg skill folder
MIN_PYTHON = (3, 9)
PACK_KEYS = ("name", "version", "requires-core", "skills", "lenses", "tracks")

# Artifact types and the folder each lives in under .cg-docs/.
# PLACEHOLDER: the artifact schema is set in task 2.1; the folders match version 1.
ARTIFACT_FOLDERS = {
    "intent": "brainstorms",
    "plan": "plans",
    "work-report": "work-reports",
    "review": "reviews",
    "decision": "decisions",
    "solution": "solutions",
}
# Statuses that mean the artifact is still open, and those that wait on the human.
# PLACEHOLDER: set with the artifact schema in task 2.1.
OPEN_STATUSES = {"draft", "active", "in-progress", "planned", "open", "approved", "blocked", "handoff"}
WAITING_STATUSES = {"draft"}
# Which playbook each phase opens.
# PLACEHOLDER: extended in task 2.14; task 1.3 delivers setup and quick only.
PHASE_PLAYBOOK = {"setup": "playbooks/setup.md", "ready": "playbooks/quick.md"}


# ---------------------------------------------------------------- helpers

def write_atomic(path: Path, text: str) -> None:
    """Write text to path through a temporary file in the same folder."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
        os.replace(tmp, path)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


def parse_version(text):
    """'2.0.0.9000' -> (2, 0, 0, 9000). Raises ValueError on anything else."""
    if not isinstance(text, str) or not re.fullmatch(r"\d+(\.\d+)*", text):
        raise ValueError(f"not a version: {text!r}")
    return tuple(int(part) for part in text.split("."))


def version_lt(a: str, b: str) -> bool:
    va, vb = parse_version(a), parse_version(b)
    width = max(len(va), len(vb))
    return va + (0,) * (width - len(va)) < vb + (0,) * (width - len(vb))


def flat_frontmatter(path: Path) -> dict:
    """Read the top-level 'key: value' lines of a Markdown file's frontmatter.

    Nested values are skipped; version 1 files hold some, and reading them is
    task 2.1's reader.
    """
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return {}
    if not lines or lines[0].strip() != "---":
        return {}
    fields = {}
    for line in lines[1:]:
        if line.strip() == "---":
            break
        match = re.match(r"([A-Za-z][\w-]*):\s*(.*)$", line)
        if not match:
            continue
        value = match.group(2).strip()
        quoted = re.match(r'"((?:[^"\\]|\\.)*)"', value) or re.match(r"'([^']*)'", value)
        if quoted:  # a quoted value ends at its closing quote; a '#' inside it is text
            text = quoted.group(1)
            fields[match.group(1)] = re.sub(r'\\(["\\])', r"\1", text) if value[0] == '"' else text
        else:
            fields[match.group(1)] = re.sub(r"\s+#.*$", "", value).strip()
    return fields


def tree_digest(folder: Path) -> str:
    """A digest of every file name and content under folder, in sorted order."""
    digest = hashlib.sha256()
    for path in sorted(p for p in folder.rglob("*") if p.is_file() and "__pycache__" not in p.parts):
        digest.update(path.relative_to(folder).as_posix().encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


def home() -> Path:
    return Path.home()


# ---------------------------------------------------------------- packs

def pack_roots():
    """Folders to look in for pack lead skills, per ADR 0003.

    Installed: the folders beside the cg skill. In the hub: every pack folder.
    """
    parent = CG_DIR.parent
    if parent.name == "core" and parent.parent.name == "packs":
        return sorted(p for p in parent.parent.iterdir() if p.is_dir())
    return [parent]


def read_pack(manifest: Path):
    """Return (data, problems) for one pack.json."""
    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        return None, [f"{manifest}: unreadable ({error})"]
    if not isinstance(data, dict):
        return None, [f"{manifest}: not a JSON object"]
    problems = []
    missing = [k for k in PACK_KEYS if k not in data]
    extra = sorted(set(data) - set(PACK_KEYS))
    if missing:
        problems.append(f"{manifest}: missing keys {', '.join(missing)}")
    if extra:
        problems.append(f"{manifest}: keys outside the contract {', '.join(extra)}")
    for key in ("version", "requires-core"):
        try:
            parse_version(data.get(key))
        except ValueError as error:
            problems.append(f"{manifest}: {key}: {error}")
    return data, problems


def discover_packs():
    """Return (packs, problems). packs: list of dicts sorted by name."""
    packs, problems = [], []
    for root in pack_roots():
        for manifest in sorted(root.glob("*/pack.json")):
            data, found = read_pack(manifest)
            problems += found
            if data is None:
                continue
            packs.append({
                "name": data.get("name"),
                "version": data.get("version"),
                "requires-core": data.get("requires-core"),
                "skills": list(data.get("skills") or []),
                "lenses": len(data.get("lenses") or []),
                "tracks": [t.get("track") for t in data.get("tracks") or [] if isinstance(t, dict)],
                "lead": manifest.parent.name,
                "path": str(manifest.parent),
            })
    packs.sort(key=lambda p: str(p["name"]))
    names = [p["name"] for p in packs]
    for name in sorted({n for n in names if names.count(n) > 1}):
        problems.append(f"pack '{name}' is installed more than once")
    core = next((p for p in packs if p["name"] == "core"), None)
    if core is None:
        problems.append("the core pack was not found beside the cg skill")
    else:
        for pack in packs:
            try:
                if version_lt(core["version"], pack["requires-core"]):
                    problems.append(f"pack '{pack['name']}' needs core {pack['requires-core']}, "
                                    f"installed core is {core['version']}")
            except ValueError:
                pass
    return packs, problems


def cmd_packs(args) -> int:
    packs, problems = discover_packs()
    if args.json:
        print(json.dumps({"packs": packs, "problems": problems}, indent=2, sort_keys=True))
        return 1 if problems else 0
    for p in packs:
        print(f"{p['name']} {p['version']} (needs core {p['requires-core']}): "
              f"skills {', '.join(p['skills']) or '-'}; lenses {p['lenses']}; "
              f"tracks {', '.join(map(str, p['tracks'])) or '-'}")
    for line in problems:
        print(f"PROBLEM {line}")
    return 1 if problems else 0


# ---------------------------------------------------------------- status

def git_facts(project: Path) -> dict:
    if shutil.which("git") is None:
        return {"git": "not found"}
    def git(*args):
        # --no-optional-locks: status only reads, so it never takes the index lock.
        done = subprocess.run(["git", "--no-optional-locks", "-C", str(project), *args],
                              capture_output=True, text=True)
        return done.stdout.strip() if done.returncode == 0 else None
    if git("rev-parse", "--is-inside-work-tree") != "true":
        return {"git": "not a repository"}
    # symbolic-ref names the branch before the first commit too; detached HEAD has none.
    branch = git("symbolic-ref", "--short", "-q", "HEAD") or "HEAD (detached)"
    facts = {"git": "repository", "branch": branch}
    if git("rev-parse", "--verify", "-q", "HEAD") is None:
        facts["commits"] = "none"
    changed = git("status", "--porcelain")
    facts["changed-files"] = len(changed.splitlines()) if changed else 0
    return facts


def artifacts(project: Path):
    """Every artifact with its flat frontmatter, newest file name first."""
    docs = project / ".cg-docs"
    found = []
    for kind, folder in sorted(ARTIFACT_FOLDERS.items()):
        for path in sorted((docs / folder).glob("*.md")):
            fields = flat_frontmatter(path)
            found.append({"type": kind, "path": path.relative_to(project).as_posix(),
                          "name": path.name, "status": fields.get("status", "").lower(),
                          "title": fields.get("title", "")})
    # Dated names (YYYY-MM-DD-...) first, newest first; undated names after them.
    found.sort(key=lambda a: (bool(re.match(r"\d{4}-\d{2}-\d{2}-", a["name"])), a["name"], a["path"]),
               reverse=True)
    return found


def read_config(project: Path):
    """Return (config or None, problems). A key of the wrong shape is dropped and named."""
    path = project / ".cg-docs" / "config.json"
    if not path.is_file():
        return None, []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("not a JSON object")
    except (OSError, ValueError) as error:
        return {}, [f".cg-docs/config.json is unreadable ({error})"]
    problems = []
    packs = data.get("packs", [])
    if not isinstance(packs, list) or not all(isinstance(n, str) for n in packs):
        problems.append('.cg-docs/config.json packs must be a list of pack names, such as ["core", "lang-r"]')
        data = {**data, "packs": []}
    if "requires-core" in data and not isinstance(data["requires-core"], str):
        problems.append('.cg-docs/config.json requires-core must be a version in quotes, such as "2.0.0"')
        data = {k: v for k, v in data.items() if k != "requires-core"}
    return data, problems


def read_settings(config):
    """Flatten config['settings'] to sorted 'pack.key=value' lines (ADR 0003, rule 7)."""
    settings = (config or {}).get("settings", {})
    lines, problems = [], []
    if not isinstance(settings, dict):
        return [], [".cg-docs/config.json settings must be an object keyed by pack name"]
    for pack, values in sorted(settings.items()):
        if not isinstance(values, dict) or not all(isinstance(v, str) for v in values.values()):
            problems.append(f".cg-docs/config.json settings.{pack} must map names to text values")
            continue
        lines += [f"{pack}.{key}={value}" for key, value in sorted(values.items())]
    return lines, problems


def compute_status(project: Path) -> dict:
    packs, pack_problems = discover_packs()
    core = next((p for p in packs if p["name"] == "core"), None)
    config, stops = read_config(project)
    stops = list(stops) + pack_problems
    installed = {p["name"] for p in packs}
    expected = sorted(set((config or {}).get("packs") or []))
    missing = [name for name in expected if name not in installed]
    needs = (config or {}).get("requires-core")
    if needs and core:
        try:
            if version_lt(core["version"], needs):
                stops.append(f"this project needs core {needs}, installed core is {core['version']}")
        except ValueError as error:
            stops.append(f".cg-docs/config.json requires-core: {error}")
    settings, problems = read_settings(config)
    stops += problems
    found = artifacts(project)
    open_ones = [a for a in found if a["status"] in OPEN_STATUSES]
    phase = "setup" if config is None else "ready"
    playbook = CG_DIR / PHASE_PLAYBOOK[phase]
    return {
        "project": str(project),
        "core": core["version"] if core else None,
        "phase": phase,
        "reason": "no .cg-docs/config.json" if config is None else ".cg-docs/config.json found",
        "active": open_ones[0]["path"] if open_ones else None,
        "open-artifacts": len(open_ones),
        "waiting-on-human": [f"{a['path']} (status {a['status']})"
                             for a in open_ones if a["status"] in WAITING_STATUSES],
        "packs-expected": expected,
        "packs-missing": missing,
        "add-command": add_command(missing) if missing else None,
        "settings": settings,
        "stops": stops,
        "next": "stop and show the human the stops" if stops else f"read {PHASE_PLAYBOOK[phase]}",
        "playbook": str(playbook),
        **git_facts(project),
    }


def add_command(missing, windows=None) -> str:
    """The install.py line that adds the missing packs, from the install record if there is one.

    In PowerShell a line that starts with a quoted path needs '&' to run it.
    """
    try:
        hub = json.loads((home() / ".cg" / "installed.json").read_text(encoding="utf-8"))["hub"]
        script = f'"{Path(hub) / "install.py"}"'
    except (OSError, ValueError, KeyError, TypeError):
        script = "install.py"
    # The interpreter running this script, not a fixed command name, which Windows may lack (ADR 0001).
    packs = ",".join(missing)
    call = "& " if (os.name == "nt" if windows is None else windows) else ""
    return f'{call}"{sys.executable}" {script} --add {packs}'


def find_root(folder: Path) -> Path:
    """The nearest folder at or above folder that holds .cg-docs/, else its git root (#218)."""
    for candidate in (folder, *folder.parents):
        if (candidate / ".cg-docs").is_dir():
            return candidate
    if shutil.which("git"):
        done = subprocess.run(["git", "--no-optional-locks", "-C", str(folder), "rev-parse", "--show-toplevel"],
                              capture_output=True, text=True)
        if done.returncode == 0 and done.stdout.strip():
            return Path(done.stdout.strip()).resolve()
    return folder


def project_from(arg):
    """The project root for --project, or None when the folder does not exist."""
    folder = Path(arg).resolve()
    if not folder.is_dir():
        print(f"no such folder: {folder}")
        return None
    return find_root(folder)


def cmd_status(args) -> int:
    project = project_from(args.project)
    if project is None:
        return 2
    state = compute_status(project)
    if args.json:
        print(json.dumps(state, indent=2, sort_keys=True))
        return 1 if state["stops"] else 0
    order = ["project", "core", "phase", "reason", "active", "open-artifacts", "waiting-on-human",
             "packs-expected", "packs-missing", "add-command", "settings", "git", "branch", "commits", "changed-files",
             "stops", "next", "playbook"]
    for key in order:
        if key not in state:
            continue
        value = state[key]
        if isinstance(value, list):
            value = "; ".join(value) if value else "none"
        print(f"{key}: {'none' if value is None else value}")
    return 1 if state["stops"] else 0


# ---------------------------------------------------------------- new

def slugify(title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return slug[:60].rstrip("-") or "untitled"


def cmd_new(args) -> int:
    project = project_from(args.project)
    if project is None:
        return 2
    title = " ".join(args.title).strip()
    if not title:
        print("give a title: cg.py new TYPE TITLE...")
        return 2
    date = args.date or datetime.date.today().isoformat()
    try:
        datetime.date.fromisoformat(date)
    except ValueError:
        print(f"not a date: {date} (use YYYY-MM-DD)")
        return 2
    target = project / ".cg-docs" / ARTIFACT_FOLDERS[args.type] / f"{date}-{slugify(title)}.md"
    if target.exists():
        print(f"exists, not overwritten: {target.relative_to(project).as_posix()}")
        return 1
    template_dir = CG_DIR / "templates"
    template = template_dir / f"{args.type}.md"
    if not template.is_file():
        template = template_dir / "artifact.md"
    safe_title = title.replace("\\", "\\\\").replace('"', '\\"')
    values = {"type": args.type, "title": safe_title, "heading": title, "date": date}
    # One pass, so a title that itself holds "{date}" is kept as written (#218).
    text = re.sub(r"\{(type|title|heading|date)\}", lambda m: values[m.group(1)],
                  template.read_text(encoding="utf-8"))
    write_atomic(target, text)
    print(f"created {target.relative_to(project).as_posix()}")
    return 0


# ---------------------------------------------------------------- doctor

def skill_roots(project: Path):
    """(label, folder) for every place a supported host reads skills from."""
    h = home()
    return [
        ("user ~/.agents/skills", h / ".agents" / "skills"),
        ("user ~/.claude/skills", h / ".claude" / "skills"),
        ("user ~/.kilo/skills", h / ".kilo" / "skills"),
        ("user ~/.copilot/skills", h / ".copilot" / "skills"),
        ("project .agents/skills", project / ".agents" / "skills"),
        ("project .claude/skills", project / ".claude" / "skills"),
        ("project .github/skills", project / ".github" / "skills"),
        ("project .kilo/skills", project / ".kilo" / "skills"),
    ]


def is_v1_name(name: str) -> bool:
    """Version 1 skill and command folders all start with 'cg-' or 'cr-'."""
    return name.startswith(("cg-", "cr-"))


def check_copies(project: Path, packs):
    """Lines about where each pack skill is found, and about v1 leftovers."""
    lines = []
    roots = [(label, folder) for label, folder in skill_roots(project) if folder.is_dir()]
    agents_root = home() / ".agents" / "skills"
    claude_root = home() / ".claude" / "skills"
    for pack in packs:
        for skill in pack["skills"]:
            places = [(label, folder / skill) for label, folder in roots if (folder / skill).exists()]
            real = {}
            for label, path in places:
                real.setdefault(str(path.resolve()), []).append(label)
            pair = {str((agents_root / skill).resolve()), str((claude_root / skill).resolve())}
            extra = [labels for target, labels in real.items() if target not in pair]
            both = (agents_root / skill).is_dir() and (claude_root / skill).is_dir()
            if both and not (claude_root / skill).is_symlink() and \
                    tree_digest(agents_root / skill) != tree_digest(claude_root / skill):
                lines.append(("FAIL", f"{skill}: the copy in ~/.claude/skills differs from "
                                      f"~/.agents/skills; one of them is stale"))
            for labels in extra:
                lines.append(("FAIL", f"{skill}: also found in {', '.join(labels)}; "
                                      f"a host may list it twice, remove that copy"))
            if not extra and places:
                lines.append(("ok", f"{skill}: {', '.join(label for label, _ in places)}"))
    for label, folder in roots:
        leftovers = sorted(p.name for p in folder.iterdir() if is_v1_name(p.name))
        if leftovers:
            # A name alone does not prove version 1 made a folder, so this is a warning, and
            # install.py --remove-v1 removes only what version 1 provably owns (#218).
            lines.append(("warn", f"{label}: {len(leftovers)} folders named like version 1 skills "
                                  f"({', '.join(leftovers[:5])}{', ...' if len(leftovers) > 5 else ''}); "
                                  f"install.py --remove-v1 removes the ones version 1 provably left, "
                                  f"and any others are yours to keep or remove"))
    return lines


def base_interpreter():
    """This Python, or the one a virtual environment was made from (#218).

    A project's environment can be deleted, and every guide on the machine
    starts cg.py through the launcher, so the launcher never records one.
    """
    if sys.prefix == sys.base_prefix:
        return sys.executable
    # Judge a path as written, not resolved: an environment's python is a link to the
    # base one, and a resolved Homebrew path changes with every upgrade.
    venv = {Path(os.path.abspath(sys.prefix)), Path(sys.prefix).resolve()}
    version = f"{sys.version_info[0]}.{sys.version_info[1]}"
    base = Path(sys.base_prefix)
    candidates = [getattr(sys, "_base_executable", ""), base / "python.exe",
                  base / "bin" / f"python{version}", base / "bin" / f"python{sys.version_info[0]}"]
    for candidate in candidates:
        if not candidate:
            continue
        path = Path(os.path.abspath(candidate))
        if path.is_file() and not any(v == path or v in path.parents for v in venv):
            return str(path)
    return None


def write_launcher(core_version) -> tuple:
    """Record how this machine runs cg.py, for playbooks and pack scripts.

    Only an installed copy writes it: a launcher pointing at a hub checkout
    would make every guide run the hub's cg.py and playbooks (#219 review).
    """
    path = home() / ".cg" / "launcher.json"
    place = install_place()
    if place not in ("~/.agents/skills", "~/.claude/skills"):
        return "warn", (f"launcher not written: cg.py runs from {place}; "
                        f"run doctor from the installed cg skill")
    python = base_interpreter()
    if python is None:
        return "FAIL", ("launcher not written: this Python is in a virtual environment and the "
                        "Python it was made from was not found; run doctor with the machine's Python")
    record = {"python": python, "cg": str(Path(__file__).resolve()), "core": core_version}
    text = json.dumps(record, indent=2, sort_keys=True) + "\n"
    try:
        if path.is_file() and path.read_text(encoding="utf-8") == text:
            return "ok", f"launcher up to date: {path}"
        write_atomic(path, text)
        return "ok", f"launcher written: {path}"
    except OSError as error:
        return "FAIL", f"could not write the launcher {path}: {error}"


def install_place() -> str:
    h = home()
    for label, folder in (("~/.agents/skills", h / ".agents" / "skills"),
                          ("~/.claude/skills", h / ".claude" / "skills")):
        if CG_DIR.parent == folder.resolve():
            return label
    if CG_DIR.parent.name == "core" and CG_DIR.parent.parent.name == "packs":
        return "the hub checkout (not installed)"
    return "a folder no supported host reads"


def cmd_doctor(args) -> int:
    project = project_from(args.project)
    if project is None:
        return 2
    lines = []
    py = sys.version_info[:3]
    lines.append(("ok" if py >= MIN_PYTHON else "FAIL",
                  f"python {'.'.join(map(str, py))} at {sys.executable}"
                  + ("" if py >= MIN_PYTHON else f"; needs {'.'.join(map(str, MIN_PYTHON))} or later")))
    for tool, needed in (("git", True), ("gh", False)):
        found = shutil.which(tool)
        if found:
            done = subprocess.run([found, "--version"], capture_output=True, text=True)
            first = (done.stdout.splitlines() or ["version unknown"])[0]
            lines.append(("ok", f"{tool}: {first}"))
        else:
            lines.append(("FAIL" if needed else "warn",
                          f"{tool} not found" + ("" if needed else "; only the issues pack needs it")))
    lines.append(("ok", f"core runs from {install_place()}: {CG_DIR}"))
    packs, problems = discover_packs()
    lines += [("FAIL", p) for p in problems]
    lines += check_copies(project, packs)
    core = next((p for p in packs if p["name"] == "core"), None)
    lines.append(write_launcher(core["version"] if core else None))
    for level, text in lines:
        print(f"{level:<5}{text}")
    return 1 if any(level == "FAIL" for level, _ in lines) else 0


# ---------------------------------------------------------------- main

def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="cg.py", description="Compound GPID core tooling.")
    sub = parser.add_subparsers(dest="command", required=True)
    doctor = sub.add_parser("doctor", help="check this machine and write the launcher file")
    doctor.add_argument("--project", default=".")
    status = sub.add_parser("status", help="print the state of the work in a project")
    status.add_argument("--project", default=".")
    status.add_argument("--json", action="store_true")
    new = sub.add_parser("new", help="create an artifact under .cg-docs/")
    new.add_argument("type", choices=sorted(ARTIFACT_FOLDERS))
    new.add_argument("title", nargs="+")
    new.add_argument("--project", default=".")
    new.add_argument("--date")
    packs = sub.add_parser("packs", help="list the installed packs")
    packs.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    return {"doctor": cmd_doctor, "status": cmd_status, "new": cmd_new, "packs": cmd_packs}[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
