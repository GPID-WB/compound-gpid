"""cg.py: the deterministic tooling of the core pack.

Usage, with the interpreter that ~/.cg/launcher.json records as <python>:
  "<python>" cg.py doctor [--project PATH]
  "<python>" cg.py status [--project PATH] [--json] [--guide]
  "<python>" cg.py new TYPE TITLE... [--project PATH] [--date YYYY-MM-DD]
  "<python>" cg.py validate [FILE...] [--strict] [--json] [--project PATH]
  "<python>" cg.py approve PLAN --reply "the human's reply, word for word" [--project PATH]
  "<python>" cg.py approve --reads FILE... --agent NAME --reply "..." [--project PATH]
  "<python>" cg.py tier --fact NAME=yes|no... --touches FILE... --reads FILE|none... [--agent NAME]
                      [--json] [--project PATH]
  "<python>" cg.py packs [--json]
  "<python>" cg.py setup [--packs a,b] [--setting pack.key=value]... [--classification-levels "A;B"]
                       [--approved-tool "agent=level"]... [--data "path=level"]...
                       [--project PATH] [--dry-run]

status names the next playbook only with --guide: the guide asks for it, and an
agent that runs status from the pointer block must not open a playbook (#223).
setup needs --packs the first time; later runs keep the recorded packs.
validate fails on a schema 2 artifact that breaks the schema; --strict, for a
project's CI, fails on a warning too. Version 1 artifacts are read as they are.
tier wants every fact in FACTS declared, and computes the rest.
approve --reads records the human's decision that a coding agent reads a data
file it is not cleared for; tier then names the decision and no longer stops.

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
import posixpath
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

CG_DIR = Path(__file__).resolve().parent.parent  # the cg skill folder
MIN_PYTHON = (3, 9)
PACK_KEYS = ("name", "version", "requires-core", "skills", "lenses", "tracks")

# The artifact schema. An artifact is a Markdown file under .cg-docs/ whose
# frontmatter is flat: one 'key: value' line per key, the value text or a
# one-line list. A file that says `schema: 2` is held to the tables below. A
# file with no `schema` key is version 1 and is read as it is (read_artifact).
SCHEMA = "2"
# Per type: the folder (version 1's, so old and new artifacts sit together),
# each status with what it means for status (waiting on the human, open or
# closed), and the headings the body must hold. The first status is the one
# `new` writes: the artifact is still being written.
ARTIFACTS = {
    "intent": {"folder": "brainstorms",
               "statuses": {"draft": "waiting", "decided": "closed", "dropped": "closed"},
               "sections": ["## Goal", "## Out of scope", "## A wrong result"]},
    "plan": {"folder": "plans",
             "statuses": {"draft": "waiting", "approved": "open", "in-progress": "open",
                          "completed": "closed", "superseded": "closed", "dropped": "closed"},
             "sections": ["## Contract", "### Goal", "### Out of scope", "### Requirements", "### Checks",
                          "### Boundaries", "## Data register", "## Slices"]},
    "work-report": {"folder": "work-reports",
                    "statuses": {"in-progress": "open", "completed": "closed"},
                    "sections": ["## Changed", "## Checks", "## Evidence", "## Not checked"]},
    "review": {"folder": "reviews",
               "statuses": {"open": "waiting", "triaged": "open", "closed": "closed"},
               "sections": ["## Findings", "## Not checked"]},
    "decision": {"folder": "decisions",
                 "statuses": {"proposed": "waiting", "accepted": "closed", "superseded": "closed"},
                 "sections": ["## Decision"]},
    "solution": {"folder": "solutions",
                 "statuses": {"draft": "open", "verified": "closed", "superseded": "closed"},
                 "sections": ["## Lesson", "## Enforced by"]},
}
ARTIFACT_FOLDERS = {kind: spec["folder"] for kind, spec in ARTIFACTS.items()}
COMMON_KEYS = ("type", "schema", "title", "date", "status")
LINK_KEYS = ("intent", "plan", "work-report", "review", "supersedes")  # each a path from the project root
KNOWN_KEYS = COMMON_KEYS + LINK_KEYS + ("size", "decided-by", "tags")
SETTLED = ("dropped", "superseded")  # nobody will finish these, so unfilled text in them is no failure
NEEDS_APPROVAL = ("approved", "in-progress", "completed")  # plan statuses that rest on the human's yes
# Version 1 statuses that are open; `draft` waits on the human. Any other is closed.
V1_STATES = {"draft": "waiting", **dict.fromkeys(
    ("active", "in-progress", "planned", "open", "approved", "blocked", "handoff"), "open")}
# Replies P2 names as not a yes. approve refuses them; whether any other reply is a clear yes is by judgement.
NOT_A_YES = ("sounds good", "whatever you think", "sure, go on")
# What the agent declares about a piece of work, each with what a yes means. tier adds what code
# can work out: whether this coding agent may read each data file, and the number of files.
FACTS = {
    "number": "it computes a number someone will read, or can change one",
    "personal": "it touches personal data, credentials or access rights",
    "irreversible": "it deletes or overwrites data, or does something that cannot be undone",
    "interface": "it adds or upgrades a dependency, or alters something other code or other people rely on",
    "choice": "it needs a choice between real alternatives that the human has not made",
    "no-check": "no check would fail if the change were wrong",
}
MAX_FILES = 5  # a change that touches more files than this is not small
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


def read_value(value: str):
    """One frontmatter value: text, or a list for a one-line list such as [a, "b, c"]."""
    quoted = re.match(r'"((?:[^"\\]|\\.)*)"', value) or re.match(r"'([^']*)'", value)
    if quoted:  # a quoted value ends at its closing quote; a '#' inside it is text
        text = quoted.group(1)
        return re.sub(r'\\(["\\])', r"\1", text) if value[0] == '"' else text
    value = re.sub(r"\s+#.*$", "", value).strip()
    if value.startswith("[") and value.endswith("]"):
        items = re.findall(r'\s*"((?:[^"\\]|\\.)*)"|\s*\'([^\']*)\'|([^,]+)', value[1:-1])
        return [item for item in ((a or b or c).strip() for a, b, c in items) if item]
    return value


def read_frontmatter(text: str):
    """Return (fields, body, problems) for the text of a Markdown file.

    fields maps each top-level key to text, or to a list for a one-line list.
    That is all schema 2 allows. Version 1 files also hold nested blocks: each
    is read as the list of its lines, so nothing is dropped, and is named in
    problems. Only a schema 2 artifact is failed for its problems.
    """
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, text, ["no frontmatter: the first line is not ---"]
    end = next((i for i, line in enumerate(lines[1:], 1) if line.strip() == "---"), None)
    if end is None:
        return {}, "", ["the frontmatter is not closed by a --- line"]
    fields, problems, key, nested = {}, [], None, set()
    for number, line in enumerate(lines[1:end], 2):
        match = re.match(r"([A-Za-z][\w-]*):\s*(.*)$", line)
        if match:
            key, value = match.group(1), match.group(2).strip()
            if key in fields:
                problems.append(f"line {number}: the key '{key}' appears twice")
            if value.startswith("{"):
                problems.append(f"line {number}: '{key}' holds a map; a value is text or a one-line list")
            fields[key] = read_value(value)
        elif key is not None and line.strip() and line[0] in " \t-":
            if key not in nested:
                nested.add(key)
                problems.append(f"line {number}: '{key}' holds a nested block; a value is text or a one-line list")
                held = fields[key]
                fields[key] = held if isinstance(held, list) else [] if held in ("", "|", ">", "|-", ">-") else [held]
            fields[key].append(re.sub(r"^-\s+", "", line.strip()))
        elif line.strip() and not line.lstrip().startswith("#"):
            problems.append(f"line {number}: not a 'key: value' line")
    return fields, "\n".join(lines[end + 1:]), problems


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


def read_artifact(path: Path, kind: str, project: Path) -> dict:
    """One artifact as status and validate see it, whichever schema wrote it.

    This is the version 1 reader too. A file with no `schema` key is version 1:
    its type is its folder's, its status is read through V1_STATES, and nothing
    in it is an error, so a version 1 folder needs no conversion.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        text = ""
    fields, body, problems = read_frontmatter(text)
    schema = str(fields["schema"]) if "schema" in fields else "1"
    status = fields.get("status", "")
    status = status.lower() if isinstance(status, str) else ""
    # A schema 2 status that nobody defined stays in view until validate's message is acted on.
    state = (V1_STATES.get(status, "closed") if schema == "1"
             else ARTIFACTS[kind]["statuses"].get(status, "open"))
    title = fields.get("title", "")
    return {"type": kind, "schema": schema, "path": path.relative_to(project).as_posix(), "name": path.name,
            "status": status, "state": state, "title": title if isinstance(title, str) else "",
            "fields": fields, "body": body, "problems": problems}


def artifacts(project: Path):
    """Every artifact of the project, newest file name first.

    Folders inside an artifact folder are read too: version 1 keeps its solutions by category.
    """
    docs = project / ".cg-docs"
    found = [read_artifact(path, kind, project) for kind, folder in sorted(ARTIFACT_FOLDERS.items())
             for path in sorted((docs / folder).rglob("*.md"))]
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


# The data rules that tier reads (#223, #224), with the shape each must have.
RULE_KEYS = {"data": "map file paths to a classification level",
             "approved-tools": "map coding agent names to a classification level"}


def rule_problems(config):
    """Shape problems in the data rules of a config, worded as stops."""
    problems = []
    for key, shape in RULE_KEYS.items():
        value = (config or {}).get(key, {})
        if not isinstance(value, dict) or not all(isinstance(v, str) for v in value.values()):
            problems.append(f".cg-docs/config.json {key} must {shape}, as text")
    levels = (config or {}).get("classification-levels", [])
    if not isinstance(levels, list) or not all(isinstance(v, str) for v in levels):
        problems.append('.cg-docs/config.json classification-levels must be a list of level names, '
                        'from public to most restricted, such as ["Public", "Internal"]')
    return problems


def rule_lines(config, key):
    """config[key] as sorted 'name=level' lines, or [] when its shape is wrong."""
    value = (config or {}).get(key, {})
    if not isinstance(value, dict):
        return []
    return [f"{name}={level}" for name, level in sorted(value.items()) if isinstance(level, str)]


def compute_status(project: Path, guide: bool = False) -> dict:
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
    stops += rule_problems(config)
    open_ones = [a for a in artifacts(project) if a["state"] != "closed"]
    waiting = [f"{a['path']} (status {a['status']})" for a in open_ones if a["state"] == "waiting"]
    waiting += [f"{a['path']} (status {a['status']}, not approved as it now reads)" for a in open_ones
                if a["schema"] == SCHEMA and a["type"] == "plan" and a["status"] in NEEDS_APPROVAL
                and not is_approved(project, a)]
    phase = "setup" if config is None else "ready"
    if stops:
        step = "stop and show the human the stops"
    elif guide:
        step = f"read {PHASE_PLAYBOOK[phase]}"
    else:
        step = "the human types /cg to run the work through the guide"
    state = {
        "project": str(project),
        "core": core["version"] if core else None,
        "phase": phase,
        "reason": "no .cg-docs/config.json" if config is None else ".cg-docs/config.json found",
        "active": open_ones[0]["path"] if open_ones else None,
        "open-artifacts": len(open_ones),
        "waiting-on-human": waiting,
        "packs-expected": expected,
        "packs-missing": missing,
        "add-command": add_command(missing) if missing else None,
        "settings": settings,
        "data": rule_lines(config, "data"),
        "approved-tools": rule_lines(config, "approved-tools"),
        "data-decisions": [f"{r['reads'] or '.'} ({r['agent']}, {r['name']}, {r['time'][:10]})"
                           for r in data_decisions(project)],
        "stops": stops,
        "next": step,
        **git_facts(project),
    }
    if guide:
        state["playbook"] = str(CG_DIR / PHASE_PLAYBOOK[phase])
    return state


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
    state = compute_status(project, guide=args.guide)
    if args.json:
        print(json.dumps(state, indent=2, sort_keys=True))
        return 1 if state["stops"] else 0
    order = ["project", "core", "phase", "reason", "active", "open-artifacts", "waiting-on-human",
             "packs-expected", "packs-missing", "add-command", "settings", "data", "approved-tools",
             "data-decisions", "git", "branch", "commits", "changed-files",
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
    template = CG_DIR / "templates" / f"{args.type}.md"
    safe_title = title.replace("\\", "\\\\").replace('"', '\\"')
    values = {"type": args.type, "title": safe_title, "heading": title, "date": date}
    # One pass, so a title that itself holds "{date}" is kept as written (#218).
    text = re.sub(r"\{(type|title|heading|date)\}", lambda m: values[m.group(1)],
                  template.read_text(encoding="utf-8"))
    write_atomic(target, text)
    print(f"created {target.relative_to(project).as_posix()}")
    return 0


# ---------------------------------------------------------------- validate

def headings(body: str):
    """The level 2 and 3 headings of a body, outside fenced code."""
    found, fenced = [], False
    for line in body.splitlines():
        if line.lstrip().startswith(("```", "~~~")):
            fenced = not fenced
        elif not fenced and re.match(r"#{2,3} \S", line):
            found.append(" ".join(line.split()))
    return found


def table_rows(body: str, heading: str):
    """The rows of the table under a heading, as lists of cells, without the table's two header lines.

    A | inside backticks or after a backslash belongs to its cell, so a command may hold a pipe.
    """
    rows, inside = [], False
    for line in body.splitlines():
        if re.match(r"#{1,6} ", line):
            inside = " ".join(line.split()) == heading
        elif inside and line.lstrip().startswith("|"):
            cells, cell, code, escaped = [], "", False, False
            for char in line.strip():
                code = code != (char == "`")
                if char == "|" and not code and not escaped:
                    cells.append(cell.strip())
                    cell = ""
                else:
                    cell += char
                escaped = char == "\\" and not escaped
            rows.append(cells[1:] + ([cell.strip()] if cell.strip() else []))
    return rows[2:]


def contract_problems(body: str):
    """What P1 asks of a contract that code can check: requirements and checks carry IDs, every
    requirement has a check that names it, and every check has a command and a failing outcome."""
    problems, ids, covered = [], [], set()
    requirements = [row[0] for row in table_rows(body, "### Requirements") if row]
    checks = [(row + [""] * 4)[:4] for row in table_rows(body, "### Checks") if row]
    problems += [f"'{rid}' is not an ID such as R1" for rid in requirements if not re.fullmatch(r"R\d+", rid)]
    if not requirements or not checks:
        problems.append("the Requirements table and the Checks table each need a row")
    for cid, serves, command, fails in checks:
        if not re.fullmatch(r"C\d+", cid):
            problems.append(f"'{cid}' is not an ID such as C1")
        named = re.findall(r"R\d+", serves)
        unknown = [rid for rid in named if rid not in requirements]
        if not named:
            problems.append(f"check {cid} names no requirement")
        if unknown:
            problems.append(f"check {cid} names {', '.join(unknown)}, which the Requirements table does not hold")
        if not command.strip("` "):
            problems.append(f"check {cid} has no command")
        if not fails:
            problems.append(f"check {cid} does not say which outcome means failure")
        covered.update(named)
        ids.append(cid)
    problems += [f"the ID {i} appears twice" for i in sorted({i for i in ids + requirements
                                                              if (ids + requirements).count(i) > 1})]
    problems += [f"requirement {rid} has no check" for rid in requirements if rid not in covered]
    return problems


def unfilled(kind: str, body: str):
    """The lines of a body that are still the template's own request to fill a part in."""
    try:
        template = (CG_DIR / "templates" / f"{kind}.md").read_text(encoding="utf-8")
    except OSError:
        return []
    asks = {line.strip() for line in template.splitlines() if re.search(r"<[^<>]+>", line)}
    return [line.strip() for line in body.splitlines() if line.strip() in asks]


def artifact_problems(project: Path, a: dict, approving: bool = False):
    """(errors, warnings) for one schema 2 artifact, against ARTIFACTS.

    approving judges a plan the way approve must: its text has to be complete,
    and the approval it is about to get is not yet asked for.
    """
    spec, fields = ARTIFACTS[a["type"]], a["fields"]
    if a["schema"] != SCHEMA:
        return [f"schema is {a['schema']}; this core reads schema {SCHEMA} and version 1, which has no "
                f"schema key, so a higher number needs a newer core"], []
    errors = list(a["problems"])
    errors += [f"the key '{key}' is missing or empty" for key in COMMON_KEYS
               if not isinstance(fields.get(key), str) or not fields[key]]
    if fields.get("type") and fields["type"] != a["type"]:
        errors.append(f"type is {fields['type']}, but {spec['folder']}/ holds {a['type']} artifacts")
    if fields.get("date"):
        try:
            datetime.date.fromisoformat(str(fields["date"]))
        except ValueError:
            errors.append(f"date is not YYYY-MM-DD: {fields['date']}")
    if a["status"] and a["status"] not in spec["statuses"]:
        errors.append(f"status is {a['status']}; a {a['type']} is one of: {', '.join(spec['statuses'])}")
    for key in LINK_KEYS:
        value = fields.get(key) or []
        for target in [value] if isinstance(value, str) else value:
            if os.path.isabs(target) or not (project / target).is_file():
                errors.append(f"{key}: no such file from the project root: {target}")
    held = headings(a["body"])
    missing = [f"the section '{heading}' is missing" for heading in spec["sections"] if heading not in held]
    errors += missing
    if a["type"] == "plan":
        errors += [] if missing else contract_problems(a["body"])
        if a["status"] in NEEDS_APPROVAL and not approving and not is_approved(project, a):
            errors.append(f"its status is {a['status']}, but no approval is recorded for the plan as it now "
                          f"reads; show the human the plan, and record their reply with approve")
    if a["type"] == "decision" and a["status"] == "accepted" and not fields.get("decided-by"):
        errors.append("an accepted decision names the person who decided, in 'decided-by'")
    warnings = [f"the key '{key}' is not part of schema {SCHEMA}" for key in fields if key not in KNOWN_KEYS]
    left = unfilled(a["type"], a["body"])
    if left:
        being_written = a["status"] == next(iter(spec["statuses"])) or a["status"] in SETTLED
        (warnings if being_written and not approving else errors).append(
            f"the template's text is still in it, first: {left[0]}")
    return errors, warnings


def artifact_at(project: Path, arg: str):
    """(path, type) for a file named on the command line, or None when it is in no artifact folder."""
    path = Path(arg)
    if not path.is_absolute():
        path = project / path if (project / path).is_file() else Path.cwd() / path
    path = path.resolve()
    for kind, folder in ARTIFACT_FOLDERS.items():
        if path.is_file() and (project / ".cg-docs" / folder).resolve() in path.parents:
            return path, kind
    return None


def cmd_validate(args) -> int:
    project = project_from(args.project)
    if project is None:
        return 2
    found = artifacts(project)
    if args.paths:
        chosen = [(arg, artifact_at(project, arg)) for arg in args.paths]
        for arg, at in chosen:
            if at is None:
                print(f"not an artifact of this project: {arg}")
                return 2
        found = [read_artifact(path, kind, project) for _, (path, kind) in chosen]
    report = []
    for a in sorted((a for a in found if a["schema"] != "1"), key=lambda a: a["path"]):
        errors, warnings = artifact_problems(project, a)
        report.append({"path": a["path"], "type": a["type"], "status": a["status"],
                       "errors": errors, "warnings": warnings})
    problems = sum(len(r["errors"]) for r in report)
    warnings = sum(len(r["warnings"]) for r in report)
    failed = problems + (warnings if args.strict else 0)
    if args.json:
        print(json.dumps({"artifacts": report, "version-1": len(found) - len(report), "strict": args.strict,
                          "problems": problems, "warnings": warnings}, indent=2, sort_keys=True))
        return 1 if failed else 0
    for r in report:
        for line in r["errors"]:
            print(f"FAIL {r['path']}: {line}")
        for line in r["warnings"]:
            print(f"{'FAIL' if args.strict else 'warn'} {r['path']}: {line}")
    print(f"schema-{SCHEMA}: {len(report)}\nversion-1: {len(found) - len(report)} (read as they are)\n"
          f"problems: {problems}\nwarnings: {warnings}")
    return 1 if failed else 0


# ---------------------------------------------------------------- approve

def text_hash(body: str) -> str:
    """The digest an approval is recorded against.

    It covers the body below the frontmatter, so a status can move on without
    voiding the approval. Line ends, trailing spaces and blank lines at either
    end are left out, so a sync or an editor cannot void it either.
    """
    text = "\n".join(line.rstrip() for line in body.splitlines()).strip("\n")
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def approvals(project: Path, artifact: dict):
    """Every approval record of an artifact. One approval is one file under .cg-docs/approvals/."""
    found, stem = [], Path(artifact["name"]).stem
    for path in sorted((project / ".cg-docs" / "approvals").glob("*.json")):
        if not path.name.startswith(stem + "."):
            continue
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if isinstance(record, dict) and record.get("artifact") == artifact["path"]:
            found.append(record)
    return found


def is_approved(project: Path, artifact: dict) -> bool:
    """True when the human approved the artifact as it now reads."""
    digest = text_hash(artifact["body"])
    return any(record.get("hash") == digest for record in approvals(project, artifact))


def the_yes(project: Path, reply: str):
    """What keeps a reply from being recorded as the human's yes (P2), and who gave it, from git."""
    refused, said = [], reply.strip()
    if not said:
        refused.append("give the human's reply, word for word, with --reply")
    elif said.lower().strip(" .!\"'") in NOT_A_YES:
        refused.append(f'"{said}" is not a clear yes (P2); ask the human what is unclear, '
                       f'and record the reply that settles it')

    def git_config(key):
        done = subprocess.run(["git", "-C", str(project), "config", "--get", key],
                              capture_output=True, text=True) if shutil.which("git") else None
        return done.stdout.strip() if done and done.returncode == 0 else ""
    name, email = git_config("user.name"), git_config("user.email")
    if not name:
        refused.append('git has no user.name here, so the record would name nobody; the human sets it '
                       'with: git config user.name "Their Name"')
    return refused, name, email


def now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def cmd_approve(args) -> int:
    """Record the human's approval of a plan: their reply word for word, who gave it, when, and
    the digest of the text they approved. Run again on the same text, it changes nothing.
    With --reads, record their decision on data instead (approve_reads)."""
    project = project_from(args.project)
    if project is None:
        return 2
    if bool(args.artifact) == bool(args.reads):
        print("give a plan, or --reads with the data the human decided on, and not both")
        return 2
    if args.reads:
        return approve_reads(project, args)
    at = artifact_at(project, args.artifact)
    if at is None or at[1] != "plan":
        print(f"not a plan of this project: {args.artifact}")
        return 2
    plan = read_artifact(at[0], "plan", project)
    refused = []
    if plan["schema"] == "1":
        refused.append("this is a version 1 plan, which holds no contract to approve; write the plan with new")
    else:
        refused += artifact_problems(project, plan, approving=True)[0]
        if plan["status"] not in ("draft", "approved", "in-progress"):
            refused.append(f"its status is {plan['status']}; a plan takes an approval while it is draft, "
                           f"approved or in-progress")
    more, name, email = the_yes(project, args.reply)
    refused += more
    digest = text_hash(plan["body"])
    record_path = project / ".cg-docs" / "approvals" / f"{at[0].stem}.{digest[7:23]}.json"
    known = is_approved(project, plan)
    if record_path.exists() and not known:
        refused.append(f"{record_path.relative_to(project).as_posix()} exists and is not this plan's record")
    if refused:
        for line in refused:
            print(f"refused: {line}")
        return 1
    if known:
        print(f"already approved as it now reads: {plan['path']}")
    else:
        record = {"artifact": plan["path"], "hash": digest, "reply": args.reply, "name": name, "email": email,
                  "time": now()}
        write_atomic(record_path, json.dumps(record, indent=2, ensure_ascii=False) + "\n")
        print(f"approved {plan['path']}\nrecord: {record_path.relative_to(project).as_posix()}\n"
              f"hash: {digest}\nby: {name} <{email}>")
    if plan["status"] == "draft":  # the one line of the plan that code changes
        text = at[0].read_text(encoding="utf-8")
        write_atomic(at[0], re.sub(r"\A(---[ \t]*\n(?:(?!---|status:).*\n)*)status:.*", r"\1status: approved", text, count=1))
    return 0


# ---------------------------------------------------------------- tier

def data_path(project: Path, arg: str) -> str:
    """A path as the data rules write it: from the project root, with forward slashes."""
    path = Path(arg)
    if path.is_absolute():
        try:
            arg = path.resolve().relative_to(project).as_posix()
        except ValueError:
            pass
    arg = posixpath.normpath(arg.replace("\\", "/"))
    return "" if arg == "." else arg


def data_decisions(project: Path):
    """Every decision of the human that a coding agent reads data it is not cleared for (P12).
    One decision is one file, .cg-docs/approvals/data.<digest>.json."""
    found = []
    for path in sorted((project / ".cg-docs" / "approvals").glob("data.*.json")):
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if isinstance(record, dict) and all(isinstance(record.get(key), str)
                                            for key in ("reads", "agent", "name", "time")):
            found.append(record)
    return found


def decision_for(decisions, found: dict, agent: str):
    """The decision that covers one file: for this agent, for the file or a folder
    above it, and for the level the file has now. A new level asks for a new decision."""
    for record in decisions:
        place = record["reads"]
        if (record["agent"].casefold() == agent.casefold() and record.get("level") == found["level"]
                and (place in ("", found["path"]) or found["path"].startswith(place + "/"))):
            return record
    return None


def approve_reads(project: Path, args) -> int:
    """Record that the human lets a coding agent read data it is not cleared for: the place,
    the agent, the level it had, their reply word for word, who gave it and when."""
    config, stops = read_config(project)
    stops = stops + rule_problems(config)
    if stops:
        for line in stops:
            print(f"stop: {line}")
        return 1
    if not args.agent:
        print("give --agent with the name of this coding agent, as tier takes it")
        return 2
    refused, name, email = the_yes(project, args.reply)
    if refused:
        for line in refused:
            print(f"refused: {line}")
        return 1
    for arg in args.reads:
        found = clearance(project, config or {}, data_path(project, arg), args.agent)
        shown = found["path"] or "."
        if found["cleared"]:
            print(f"{shown} is cleared for {args.agent} ({found['why']}); there is nothing to record")
        elif decision_for(data_decisions(project), found, args.agent):
            print(f"already recorded: {args.agent} reads {shown}")
        else:
            key = "\n".join([found["path"], args.agent.casefold(), found["level"] or ""])
            record_path = (project / ".cg-docs" / "approvals"
                           / f"data.{hashlib.sha256(key.encode('utf-8')).hexdigest()[:16]}.json")
            record = {"reads": found["path"], "agent": args.agent, "level": found["level"],
                      "reply": args.reply, "name": name, "email": email, "time": now()}
            write_atomic(record_path, json.dumps(record, indent=2, ensure_ascii=False) + "\n")
            print(f"recorded: {args.agent} reads {shown}, which is not cleared ({found['why']})\n"
                  f"record: {record_path.relative_to(project).as_posix()}\nby: {name} <{email}>")
    return 0


def clearance(project: Path, config: dict, path: str, agent: str) -> dict:
    """Whether the recorded data rules let this coding agent read one file (P12).

    The rule for the file wins, then the rule for the nearest folder above it.
    A file is cleared when its level is Public, or when approved-tools gives
    this agent that level or a more restricted one in classification-levels.
    """
    rules = {data_path(project, key): level for key, level in config.get("data", {}).items()}
    over = [key for key in rules if key in ("", path) or path.startswith(key + "/")]
    if not over:
        return {"path": path, "level": None, "cleared": False, "why": "no classification is recorded for it"}
    level = rules[max(over, key=len)]
    found = {"path": path, "level": level, "cleared": True, "why": f"its level is {level}"}
    if level.casefold() == "public":
        return found
    tools = {name.casefold(): (name, allowed) for name, allowed in config.get("approved-tools", {}).items()}
    if agent.casefold() not in tools:
        return {**found, "cleared": False, "why": f"its level is {level}, and no level is recorded for {agent}"}
    name, allowed = tools[agent.casefold()]
    order = [item.casefold() for item in config.get("classification-levels", [])]
    if level.casefold() == allowed.casefold():
        return {**found, "why": f"{name} may read {allowed}"}
    if level.casefold() not in order or allowed.casefold() not in order:
        return {**found, "cleared": False, "why": f"its level is {level}, and classification-levels does not "
                                                  f"rank it against what {name} may read ({allowed})"}
    if order.index(level.casefold()) < order.index(allowed.casefold()):
        return {**found, "why": f"{name} may read up to {allowed}"}
    return {**found, "cleared": False, "why": f"its level is {level}, above what {name} may read ({allowed})"}


def cmd_tier(args) -> int:
    """The risk level of a piece of work, from declared facts and never from an opinion.

    The agent declares every fact in FACTS as yes or no, the files the change
    touches and the data files it reads. Code adds the data rules and the file
    count. Any yes makes the tier elevated. A data file that is not cleared
    raises it until the human's decision to read it is recorded; after that,
    every run names the decision.
    """
    project = project_from(args.project)
    if project is None:
        return 2
    config, stops = read_config(project)
    stops = stops + rule_problems(config)
    if stops:
        for line in stops:
            print(f"stop: {line}")
        return 1
    facts = pairs(args.fact, "--fact")
    if facts is None:
        return 2
    config, facts = config or {}, {name: value.lower() for name, value in facts.items()}
    reads, usage = args.reads or [], []
    if len(facts) < len(args.fact or []):
        usage.append("a fact is declared more than once; declare each fact once")
    usage += [f"'{name}' is not a fact; the facts are: {', '.join(FACTS)}" for name in facts if name not in FACTS]
    usage += [f"--fact {name} must be yes or no" for name, value in facts.items() if value not in ("yes", "no")]
    usage += [f"declare --fact {name}=yes or --fact {name}=no; a yes means {meaning}"
              for name, meaning in FACTS.items() if name not in facts]
    if not args.touches:
        usage.append("give --touches once for each file the change will create, change or delete")
    if not reads or ("none" in reads and len(reads) > 1):
        usage.append("give --reads once for each data file the work will open or that code it runs will read, "
                     "or --reads none alone when there is none")
    elif reads != ["none"] and not args.agent:
        names = ", ".join(sorted(config.get("approved-tools", {})))
        usage.append("give --agent with the name of this coding agent, as setup recorded it"
                     + (f": {names}" if names else ""))
    if usage:
        for line in usage:
            print(line)
        return 2
    data = [] if reads == ["none"] else [clearance(project, config, data_path(project, r), args.agent) for r in reads]
    decisions = data_decisions(project)
    for d in data:
        made = None if d["cleared"] else decision_for(decisions, d, args.agent)
        d["decision"] = made and {key: made.get(key) for key in ("name", "time", "reply")}
    files = sorted({data_path(project, f) for f in args.touches})
    reasons = [f"{name}: {FACTS[name]}" for name in FACTS if facts[name] == "yes"]
    reasons += [f"data: {d['path']} is not cleared for {args.agent}" for d in data
                if not d["cleared"] and not d["decision"]]
    if len(files) > MAX_FILES:
        reasons.append(f"size: the change touches {len(files)} files, more than {MAX_FILES}")
    state = {"tier": "elevated" if reasons else "low", "reasons": reasons, "data": data, "files": files,
             "facts": {name: facts[name] for name in FACTS}}
    if args.json:
        print(json.dumps(state, indent=2, sort_keys=True))
        return 0
    shown = [f"{d['path']}{'=' + d['level'] if d['level'] else ''}: "
             f"{'cleared' if d['cleared'] else 'not cleared'} ({d['why']})"
             + (f"; read on the decision of {d['decision']['name']}, {d['decision']['time'][:10]}"
                if d["decision"] else "") for d in data]
    print(f"tier: {state['tier']}\nreasons: {'; '.join(reasons) or 'none'}\n"
          f"data: {'; '.join(shown) or 'none'}\nfiles: {len(files)}")
    return 0


# ---------------------------------------------------------------- setup

START, END = "<!-- cg:start", "<!-- cg:end -->"
BLOCK_RE = re.compile(r"^<!-- cg:start.*?^<!-- cg:end -->[ \t]*$", re.M | re.S)
BUILD_IGNORE = ["^\\.cg-docs$", "^AGENTS\\.md$", "^CLAUDE\\.md$"]


def pairs(items, what):
    """'key=value' strings to a dict; None when one is malformed."""
    found = {}
    for item in items or []:
        key, sep, value = item.partition("=")
        if not sep or not key.strip() or not value.strip():
            print(f"{what} must be written key=value: {item!r}")
            return None
        found[key.strip()] = value.strip()
    return found


def planned_setup(project: Path, args):
    """Return (changes, problems): changes are (path, new text) for files that differ."""
    names = [n.strip() for n in (args.packs or "").split(",") if n.strip()]
    if args.packs is not None and (not names or not all(re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", n) for n in names)):
        return None, ["--packs must be pack names joined by commas, such as core,lang-r"]
    settings, tools, data = (pairs(args.setting, "--setting"), pairs(args.approved_tool, "--approved-tool"),
                             pairs(args.data, "--data"))
    if settings is None or tools is None or data is None:
        return None, []
    if any("." not in key for key in settings):
        return None, ["--setting must be written pack.key=value, such as lang-r.r-syntax=tidyverse"]
    problems, changes = [], []
    config_path = project / ".cg-docs" / "config.json"
    config = {}
    if config_path.is_file():
        try:
            config = json.loads(config_path.read_text(encoding="utf-8"))
            if not isinstance(config, dict):
                raise ValueError("not a JSON object")
        except (OSError, ValueError) as error:
            return [], [f".cg-docs/config.json is unreadable ({error}); fix it, then run setup again"]
    shape = rule_problems(config)
    if shape:
        return [], [f"{line}; fix it, then run setup again" for line in shape]
    if not names and not config.get("packs"):
        return None, ["the first setup needs --packs, such as --packs core,lang-r"]
    packs, _ = discover_packs()
    core = next((p["version"] for p in packs if p["name"] == "core"), None)
    config = dict(config)
    if names:
        config["packs"] = names
    if core:
        config["requires-core"] = core
    merged = {k: dict(v) for k, v in (config.get("settings") or {}).items() if isinstance(v, dict)}
    for key, value in sorted(settings.items()):
        pack, _, name = key.partition(".")
        merged.setdefault(pack, {})[name] = value
    if merged:
        config["settings"] = merged
    if args.classification_levels:
        config["classification-levels"] = [x.strip() for x in args.classification_levels.split(";") if x.strip()]
    for key, values in (("approved-tools", tools), ("data", data)):
        if values:
            config[key] = {**(config.get(key) or {}), **values}
    changes.append((config_path, json.dumps(config, indent=2, ensure_ascii=False) + "\n"))
    verification = project / ".cg-docs" / "verification.md"
    if not verification.is_file():
        changes.append((verification, (CG_DIR / "templates" / "verification.md").read_text(encoding="utf-8")))
    block = (CG_DIR / "templates" / "pointer-block.md").read_text(encoding="utf-8").strip()
    agents = project / "AGENTS.md"
    text = agents.read_text(encoding="utf-8") if agents.is_file() else ""
    found = BLOCK_RE.findall(text)
    if len(found) > 1:
        problems.append(f"AGENTS.md holds {len(found)} pointer blocks; keep one, then run setup again")
    elif found:
        changes.append((agents, BLOCK_RE.sub(lambda m: block, text, count=1)))
    else:
        changes.append((agents, (text.rstrip("\n") + "\n\n" if text.strip() else "") + block + "\n"))
    for other in ("CLAUDE.md", ".github/copilot-instructions.md"):
        path = project / other
        if path.is_file() and START in path.read_text(encoding="utf-8"):
            problems.append(f"{other} holds the pointer block; it belongs in AGENTS.md only (ADR 0001), "
                            f"so remove it there, then run setup again")
    claude = project / "CLAUDE.md"
    text = claude.read_text(encoding="utf-8") if claude.is_file() else ""
    if "@AGENTS.md" not in [line.strip() for line in text.splitlines()]:
        changes.append((claude, (text.rstrip("\n") + "\n" if text.strip() else "") + "@AGENTS.md\n"))
    if (project / "DESCRIPTION").is_file():
        ignore = project / ".Rbuildignore"
        lines = ignore.read_text(encoding="utf-8").splitlines() if ignore.is_file() else []
        lines += [line for line in BUILD_IGNORE if line not in lines]
        changes.append((ignore, "\n".join(lines) + "\n"))
    changes = [(path, new) for path, new in changes
               if not path.is_file() or path.read_text(encoding="utf-8") != new]
    return changes, problems


def cmd_setup(args) -> int:
    """Write what the human confirmed in the setup playbook. Run again, it changes only what differs."""
    project = project_from(args.project)
    if project is None:
        return 2
    changes, problems = planned_setup(project, args)
    if changes is None:
        for line in problems:
            print(line)
        return 2
    if problems:
        for line in problems:
            print(f"refused: {line}")
        return 1
    for path, text in changes:
        verb = "change" if path.is_file() else "create"
        rel = path.relative_to(project).as_posix()
        if args.dry_run:
            print(f"would {verb} {rel}")
        else:
            write_atomic(path, text)
            print(f"{verb}d {rel}")
    if not changes:
        print("nothing to change: the project already holds what setup writes")
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
    status.add_argument("--guide", action="store_true", help="also name the playbook the guide opens next")
    new = sub.add_parser("new", help="create an artifact under .cg-docs/")
    new.add_argument("type", choices=sorted(ARTIFACT_FOLDERS))
    new.add_argument("title", nargs="+")
    new.add_argument("--project", default=".")
    new.add_argument("--date")
    packs = sub.add_parser("packs", help="list the installed packs")
    packs.add_argument("--json", action="store_true")
    setup = sub.add_parser("setup", help="write what the human confirmed in the setup playbook")
    setup.add_argument("--packs")
    setup.add_argument("--setting", action="append")
    setup.add_argument("--classification-levels")
    setup.add_argument("--approved-tool", action="append")
    setup.add_argument("--data", action="append", help="path=level: the classification the human gave a data file")
    setup.add_argument("--project", default=".")
    setup.add_argument("--dry-run", action="store_true")
    validate = sub.add_parser("validate", help="check the artifacts under .cg-docs/ against the schema")
    validate.add_argument("paths", nargs="*", help="artifacts to check; all of them when none is given")
    validate.add_argument("--strict", action="store_true", help="for a project's CI: a warning fails too")
    validate.add_argument("--json", action="store_true")
    validate.add_argument("--project", default=".")
    approve = sub.add_parser("approve", help="record the human's approval of a plan, or their decision on data")
    approve.add_argument("artifact", nargs="?", help="the plan the human approved")
    approve.add_argument("--reads", action="append", help="a data file or folder the human lets --agent read "
                                                          "though it is not cleared")
    approve.add_argument("--agent", help="with --reads: this coding agent, as tier takes it")
    approve.add_argument("--reply", required=True, help="the human's reply, word for word")
    approve.add_argument("--project", default=".")
    tier = sub.add_parser("tier", help="compute the risk level of a piece of work from declared facts")
    tier.add_argument("--fact", action="append", help=f"name=yes or name=no, once for each of: {', '.join(FACTS)}")
    tier.add_argument("--touches", action="append", help="a file the change will create, change or delete")
    tier.add_argument("--reads", action="append", help="a data file the work reads, or none")
    tier.add_argument("--agent", help="this coding agent, as setup recorded it under approved-tools")
    tier.add_argument("--json", action="store_true")
    tier.add_argument("--project", default=".")
    args = parser.parse_args(argv)
    commands = {"doctor": cmd_doctor, "status": cmd_status, "new": cmd_new, "packs": cmd_packs, "setup": cmd_setup,
                "validate": cmd_validate, "approve": cmd_approve, "tier": cmd_tier}
    return commands[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
