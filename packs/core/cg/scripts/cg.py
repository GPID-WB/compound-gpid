"""cg.py: the deterministic tooling of the core pack.

Usage, with the interpreter that ~/.cg/launcher.json records as <python>:
  "<python>" cg.py doctor [--project PATH]
  "<python>" cg.py status [--project PATH] [--json] [--guide [--playbook NAME]]
  "<python>" cg.py new TYPE TITLE... [--project PATH] [--date YYYY-MM-DD]
  "<python>" cg.py validate [FILE...] [--strict] [--json] [--project PATH]
  "<python>" cg.py approve PLAN|INTENT --reply "the human's reply, word for word" [--project PATH]
  "<python>" cg.py approve --reads FILE... --agent NAME --reply "..." [--project PATH]
  "<python>" cg.py tier --fact NAME=yes|no... --touches FILE... --reads FILE|none... [--agent NAME]
                      [--json] [--project PATH]
  "<python>" cg.py packs [--json]
  "<python>" cg.py setup [--packs a,b] [--setting pack.key=value]... [--classification-levels "A;B"]
                       [--approved-tool "agent=level"]... [--data "path=level"]...
                       [--project PATH] [--dry-run]

status names the next playbook only with --guide: the guide asks for it, and an
agent that runs status from the pointer block must not open a playbook (#223).
--playbook is the playbook the human asked for by name; a project that is not
set up gets setup first.
approve records the human's yes to a plan or to an intent, as the file reads.
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
import ntpath
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
               "sections": ["## Goal", "## Out of scope", "## A wrong result", "## Facts", "## Decisions",
                            "## Assumptions", "## Approaches considered"]},
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
# The artifacts that rest on the human's yes. Per type: the statuses a file may have when approve
# records a yes, the status code then writes over `draft`, and the statuses that need a yes on record.
APPROVED = {"plan": (("draft", "approved", "in-progress"), "approved", ("approved", "in-progress", "completed")),
            "intent": (("draft", "decided"), "decided", ("decided",))}
# Version 1 statuses that are open; `draft` waits on the human. Any other is closed.
V1_STATES = {"draft": "waiting", **dict.fromkeys(
    ("active", "in-progress", "planned", "open", "approved", "blocked", "handoff"), "open")}
# approve records a reply only when it is a plain yes and nothing else (the maintainer's decisions
# of 2026-11-26, #225): at least one of YES, and beside it only words of FILLER. Lists of what makes a
# reply not a yes kept missing cases, so the rule names what a yes is. grilling.md names each of YES,
# and each reply below, which only choose what the refusal says to ask next: a test holds them together.
YES = ("yes", "ok", "okay", "approved", "confirmed", "agreed", "i approve", "i confirm", "i agree", "go ahead",
       "sí", "si", "de acuerdo", "adelante")
FILLER = ("please", "thanks", "thank you", "gracias", "por favor", "it", "this", "that", "the", "intent", "plan",
          "as written", "as it is", "as it reads", "as shown", "proceed", "do it", "read it")
NOT_A_YES = {"sounds good": "vague", "looks good": "vague", "sure, go on": "vague", "sure, let's go": "vague",
             "i guess": "vague", "if you say so": "vague",
             "whatever you think": "handed-back", "up to you": "handed-back", "your call": "handed-back",
             "you decide": "handed-back"}
# What approve says of each kind of reply it refuses, with the question that comes next.
KINDS = {
    "vague": "agrees without deciding (P2); ask what they would change or what is unclear, and record "
             "the reply that settles it",
    "handed-back": "hands the decision back, and it stays the human's (P2); offer two concrete options as "
                   "a choice, say which you recommend, and record the reply that settles it",
    "no": "says no, or not yet; nothing is recorded, and nothing goes ahead on it",
    "no-yes": "holds no plain yes, so it is not recorded; ask whether it is a yes or what should change, "
              "and record the reply that settles it",
    "more": "says more than a plain yes, so it is not recorded; when it asks, corrects or adds something, "
            "deal with that and show what changed, then ask for a plain yes and record that reply",
}
# A reply that opens with one of these words is a no, or a not yet (#224).
SAYS_NO = r"(no|nope|not|don['’]?t|do not|stop|wait|hold on|cancel|never)\b"
# What stands in a table cell that nobody has filled in yet. The human's own words go in quotes.
NOT_FILLED = (r"(still |not yet |remains )?(open|pending|t\.?b\.?[dac]\.?|todo|fixme|xxx+|placeholder|unknown|"
              r"undecided|unanswered|unclear|unsure|unconfirmed|waiting|awaiting|later(?=\W*$)|n\.?/?a\.?|to be \w+|"
              r"to (decide|confirm|check|ask|answer|fill|follow)|ask( the human)?|fill( in)?(?=\W*$)|"
              r"not (yet )?(decided|answered|known|asked|given|sure|checked|confirmed)|not yet|"
              r"no (answer|reply|decision)( yet)?|none yet|nothing yet|don'?t know|no idea|"
              r"pendiente|por (decidir|confirmar|definir|ver|responder)|sin (respuesta|decidir|definir)|"
              r"abiert[oa]|desconocid[oa]|no s[eé])(?!\w)")
# What stands in a Source cell that names no source. "the human" is a source (grilling.md).
NO_SOURCE = (r"(none|no source|nowhere|not (found|checked|looked up|verified)|guess(ed)?|my guess|"
             r"assum(ed|ption)|(from )?memory|(general|common) knowledge|i think|i believe|presumably|"
             r"ninguna|ninguno|sin fuente)(?!\w)")
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


def article(kind: str) -> str:
    """'a plan', 'an intent': a type with its article, for a message."""
    return f"{'an' if kind[0] in 'aeiou' else 'a'} {kind}"


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

    A byte order mark is no part of the text. A frontmatter that is never
    closed is read up to its first blank line, so a file that says `schema: 2`
    is still held to schema 2 (#224, review finding 4).
    """
    lines = text.removeprefix("﻿").splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, text, ["no frontmatter: the first line is not ---"]
    end = next((i for i, line in enumerate(lines[1:], 1) if line.strip() == "---"), None)
    fields, problems, key, nested = {}, [], None, set()
    if end is None:
        problems.append("the frontmatter is not closed by a --- line")
        end = next((i for i, line in enumerate(lines[1:], 1) if not line.strip()), len(lines))
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
        raw = path.read_bytes()
    except OSError:
        raw = b""
    try:
        text, encoding = raw.decode("utf-8"), []
    except UnicodeDecodeError:  # read it all the same, so a schema 2 file is still checked (#224)
        text, encoding = raw.decode("utf-8", errors="replace"), ["the file is not UTF-8; save it as UTF-8"]
    fields, body, problems = read_frontmatter(text)
    problems = encoding + problems
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


def playbooks():
    """The names of the installed playbooks."""
    return sorted(path.stem for path in (CG_DIR / "playbooks").glob("*.md"))


def compute_status(project: Path, guide: bool = False, asked=None) -> dict:
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
    found = artifacts(project)
    open_ones = [a for a in found if a["state"] != "closed"]
    waiting = [f"{a['path']} (status {a['status']})" for a in open_ones if a["state"] == "waiting"]
    waiting += [f"{a['path']} (status {a['status']}, not approved as it now reads)" for a in found
                if a["schema"] == SCHEMA and a["status"] in APPROVED.get(a["type"], ((), "", ()))[2]
                and not is_approved(project, a)]
    phase = "setup" if config is None else "ready"
    # The playbook the human asked for by name, once the project is set up; else the phase's.
    playbook = f"playbooks/{asked}.md" if asked and phase != "setup" else PHASE_PLAYBOOK[phase]
    if stops:
        step = "stop and show the human the stops"
    elif guide and asked and phase == "setup" and asked != "setup":
        step = f"read {playbook}; {asked}, which the human asked for, opens once setup is done"
    elif guide:
        step = f"read {playbook}"
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
        state["playbook"] = str(CG_DIR / playbook)
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
    if args.playbook and not args.guide:
        print("--playbook goes with --guide: only the guide opens a playbook")
        return 2
    if args.playbook and args.playbook not in playbooks():
        print(f"no playbook named '{args.playbook}'; the installed playbooks are: {', '.join(playbooks())}")
        return 2
    state = compute_status(project, guide=args.guide, asked=args.playbook)
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
    Every table under the heading counts, a table under a deeper heading too, and each one
    drops its own two header lines (review of #225: a second round under `### Round 2`).
    """
    rows, table, level = [], [], 0
    for line in body.splitlines() + [""]:
        mark = re.match(r"(#{1,6}) ", line)
        if not (level and mark is None and line.lstrip().startswith("|")):
            rows, table = rows + table[2:], []
        if mark and not (level and len(mark.group(1)) > level):
            level = len(mark.group(1)) if " ".join(line.split()) == heading else 0
        elif level and mark is None and line.lstrip().startswith("|"):
            cells, cell, code, escaped = [], "", False, False
            for char in line.strip():
                code = code != (char == "`")
                if char == "|" and not code and not escaped:
                    cells.append(cell.strip())
                    cell = ""
                else:
                    cell += char
                escaped = char == "\\" and not escaped
            table.append(cells[1:] + ([cell.strip()] if cell.strip() else []))
    return rows


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


def blank(cell: str, source: bool = False) -> bool:
    """True when a table cell holds nothing: no word, or one that only stands for 'not yet', such
    as `open`, pending, TBD or ?. Marks of emphasis, and a list mark or a bracket before the word,
    are left out; a text in quotes is content. With source, "none" or "a guess" is nothing too."""
    text = bare(cell)
    return (not re.search(r"\w", text) or bool(re.match(NOT_FILLED, text))
            or (source and bool(re.match(NO_SOURCE, text))))


def bare(text: str) -> str:
    """A cell or a line without marks of emphasis, HTML comments, one-word tags such as <br> or
    <open>, entities, and the list mark or bracket before its first word, in lower case."""
    text = re.sub(r"<!--.*?-->|</?\w+\s*/?>|&#?\w+;", "", text)  # a template's request of several words stays
    text = re.sub(r"[`*_~()\[\]{}]", "", text).strip().lower()
    return re.sub(r"^(\d+[.)]\s+|[^\w\"'“‘«])+", "", text)


def filler(line: str) -> bool:
    """True when a line under a heading says nothing: no word, or only a placeholder such as TBD.
    In a table row, every cell must be so. A line that only starts with such a word is content."""
    cells = line.strip().strip("|").split("|") if line.lstrip().startswith("|") else [line]
    return all(not re.search(r"\w", bare(cell)) or re.fullmatch(NOT_FILLED + r"[\W_]*", bare(cell))
               for cell in cells)


def empty_sections(body: str, wanted):
    """The wanted headings with nothing written under them: no line of text, and no table row
    below a table's two header lines. What is under a deeper heading counts for the one above.
    A line of filler, such as TBD, an HTML comment or a bare mark, is nothing (review of #225)."""
    lines, found, fenced = re.sub(r"<!--.*?-->", "", body, flags=re.S).splitlines(), [], False
    rule = re.compile(r"\|?[\s:|-]*-[\s:|-]*\|?")
    level, name, holds = 0, None, False
    for number, line in enumerate(lines + ["# end"]):
        if line.lstrip().startswith(("```", "~~~")):
            fenced = not fenced
            continue
        mark = None if fenced else re.match(r"(#{1,6}) ", line)
        if mark and name and len(mark.group(1)) <= level:
            found += [] if holds else [name]
            name = None
        if mark and not name and " ".join(line.split()) in wanted:
            level, name, holds = len(mark.group(1)), " ".join(line.split()), False
        elif name and not mark and not filler(line) and not rule.fullmatch(line.strip()):
            after = lines[number + 1].strip() if number + 1 < len(lines) else ""
            holds = holds or not (line.lstrip().startswith("|") and rule.fullmatch(after))
    return found


def intent_problems(body: str):
    """What grilling must leave settled that code can check (P2): each fact names its source, and
    each decision was put to the human with a recommended answer and has their answer."""
    facts = [(row + [""] * 2)[:2] for row in table_rows(body, "## Facts") if row]
    decisions = [(row + [""] * 4)[:4] for row in table_rows(body, "## Decisions") if row]
    problems = [] if facts and decisions else ["the Facts table and the Decisions table each need a row"]
    problems += [f"the fact '{fact}' names no source" for fact, source in facts if blank(source, source=True)]
    ids = [did for did, *_ in decisions]
    for did, _, recommended, answer in decisions:
        if not re.fullmatch(r"D\d+", did):
            problems.append(f"'{did}' is not an ID such as D1")
        if blank(recommended):
            problems.append(f"decision {did} has no recommended answer")
        if blank(answer):
            problems.append(f"decision {did} has no answer from the human yet"
                            + (f"; when '{answer}' is what they said, put it in quotes" if answer else ""))
    return problems + [f"the ID {i} appears twice" for i in sorted({i for i in ids if ids.count(i) > 1})]


def unfilled(kind: str, body: str):
    """The lines of a body that still hold one of the template's requests to fill a part in.

    One request left in a line counts, so a table row is not filled until each of its cells is
    (#224, review finding 7). A test holds every template to a request in each cell."""
    try:
        template = (CG_DIR / "templates" / f"{kind}.md").read_text(encoding="utf-8")
    except OSError:
        return []
    asks = set(re.findall(r"<[^<>]+>", template))
    if kind == "intent":  # the assumptions block of grilling.md holds requests too (review of #225)
        try:
            asks |= set(re.findall(r"<[^<>]+>", (CG_DIR / "grilling.md").read_text(encoding="utf-8")))
        except OSError:
            pass
    return [line.strip() for line in body.splitlines() if any(ask in line for ask in asks)]


def artifact_problems(project: Path, a: dict, approving: bool = False):
    """(errors, warnings) for one schema 2 artifact, against ARTIFACTS.

    approving judges a plan or an intent the way approve must: its text has to
    be complete, and the approval it is about to get is not yet asked for.
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
        errors.append(f"status is {a['status']}; {article(a['type'])} is one of: {', '.join(spec['statuses'])}")
    for key in LINK_KEYS:
        value = fields.get(key) or []
        for target in [value] if isinstance(value, str) else value:
            if os.path.isabs(target) or not (project / target).is_file():
                errors.append(f"{key}: no such file from the project root: {target}")
    held = headings(a["body"])
    missing = [f"the section '{heading}' is missing" for heading in spec["sections"] if heading not in held]
    errors += missing
    warnings = [f"the key '{key}' is not part of schema {SCHEMA}" for key in fields if key not in KNOWN_KEYS]
    rests_on_yes = a["status"] in APPROVED.get(a["type"], ((), "", ()))[2]
    if a["type"] == "plan":
        errors += [] if missing else contract_problems(a["body"])
    if a["type"] == "intent" and not missing:  # an open decision is a draft's normal state
        (errors if approving or rests_on_yes else warnings).extend(intent_problems(a["body"]))
    if rests_on_yes and not approving and not is_approved(project, a):
        errors.append(f"its status is {a['status']}, but no approval is recorded for the {a['type']} as it now "
                      f"reads; show the human the {a['type']}, and record their reply with approve")
    if a["type"] == "decision" and a["status"] == "accepted" and not fields.get("decided-by"):
        errors.append("an accepted decision names the person who decided, in 'decided-by'")
    # What is unfinished is a warning while the artifact is being written, and an error after.
    being_written = (a["status"] == next(iter(spec["statuses"])) or a["status"] in SETTLED) and not approving
    unfinished = [f"nothing is written under '{heading}'" for heading in empty_sections(a["body"], spec["sections"])]
    left = unfilled(a["type"], a["body"])
    if left:
        unfinished.append(f"the template's text is still in it, first: {left[0]}")
    (warnings if being_written else errors).extend(unfinished)
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
            found.append((str(record.get("time", "")), path.stat().st_mtime_ns, path.name, record))
    # Oldest first. The time is to the second; within one second the file written last is the newer.
    return [record for *_, record in sorted(found, key=lambda item: item[:3])]


def is_approved(project: Path, artifact: dict) -> bool:
    """True when the human's newest approval is for the artifact as it now reads.

    An amendment replaces the text approved before it. Putting that text back is
    a change the human has not approved (#224, review finding 5).
    """
    found = approvals(project, artifact)
    return bool(found) and found[-1].get("hash") == text_hash(artifact["body"])


def the_yes(project: Path, reply: str):
    """What keeps a reply from being recorded as the human's yes (P2), and who gave it, from git.

    A reply is recorded only when it is a plain yes and nothing else: it holds
    one of YES, and every other word in it is of FILLER. Everything else is
    refused, with what to ask next."""
    refused, said = [], reply.strip()

    def plain(text):  # lower case, without punctuation, so "Sure go on!" is "sure, go on"; "sí" keeps its accent
        return " ".join(re.sub(r"[^\w ]+", " ", re.sub(r"['’]", "", text.lower())).split())

    def any_of(phrases):
        return r"\b(?:" + "|".join(re.escape(plain(p)) for p in sorted(phrases, key=len, reverse=True)) + r")\b"
    words = plain(said)
    opens = next((kind for phrase, kind in NOT_A_YES.items() if f"{words} ".startswith(plain(phrase) + " ")), None)
    yes = re.search(any_of(YES), words)
    if not said:
        refused.append("give the human's reply, word for word, with --reply")
    elif re.match(SAYS_NO, said.lower()):
        refused.append(f'"{said}" {KINDS["no"]}')
    elif not yes:
        refused.append(f'"{said}" {KINDS[opens or "no-yes"]}')
    elif re.sub(any_of(YES + FILLER), " ", words).strip() or re.search(r"[?¿]", said):  # "Ok?" asks
        refused.append(f'"{said}" {KINDS["more"]}')

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
    """Record the human's yes to a plan or to an intent: their reply word for word, who gave it,
    when, and the digest of the text they said yes to. Run again on the same text, it changes
    nothing. With --reads, record their decision on data instead (approve_reads)."""
    project = project_from(args.project)
    if project is None:
        return 2
    if bool(args.artifact) == bool(args.reads):
        print("give a plan or an intent, or --reads with the data the human decided on, and not both")
        return 2
    if args.reads:
        return approve_reads(project, args)
    at = artifact_at(project, args.artifact)
    if at is None or at[1] not in APPROVED:
        print(f"not a plan or an intent of this project: {args.artifact}")
        return 2
    kind = at[1]
    takes, written, _ = APPROVED[kind]
    plan = read_artifact(at[0], kind, project)
    refused = []
    if plan["schema"] == "1":
        refused.append(f"this is a version 1 {kind}, which holds nothing code can check before a yes; "
                       f"write the {kind} with new")
    else:
        refused += artifact_problems(project, plan, approving=True)[0]
        if plan["status"] not in takes:
            refused.append(f"its status is {plan['status']}; {article(kind)} takes an approval while it is "
                           f"{', '.join(takes[:-1])} or {takes[-1]}")
    more, name, email = the_yes(project, args.reply)
    refused += more
    digest = text_hash(plan["body"])
    record_path = project / ".cg-docs" / "approvals" / f"{at[0].stem}.{digest[7:23]}.json"
    known, stamp = is_approved(project, plan), now()
    if record_path.exists() and not known:
        try:
            held = json.loads(record_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            held = None
        if isinstance(held, dict) and held.get("artifact") == plan["path"] and held.get("hash") == digest:
            # This text was approved before an amendment replaced it: a new yes gets a record of its own.
            record_path = record_path.with_name(f"{record_path.stem}.{re.sub(r'[-:]', '', stamp)}.json")
        else:
            refused.append(f"{record_path.relative_to(project).as_posix()} exists and is not this {kind}'s record")
    if refused:
        for line in refused:
            print(f"refused: {line}")
        return 1
    if known:
        print(f"already approved as it now reads: {plan['path']}")
    else:
        record = {"artifact": plan["path"], "hash": digest, "reply": args.reply, "name": name, "email": email,
                  "time": stamp}
        write_atomic(record_path, json.dumps(record, indent=2, ensure_ascii=False) + "\n")
        print(f"approved {plan['path']}\nrecord: {record_path.relative_to(project).as_posix()}\n"
              f"hash: {digest}\nby: {name} <{email}>")
    if plan["status"] == "draft":  # the one line of the file that code changes
        text = at[0].read_text(encoding="utf-8-sig")
        write_atomic(at[0], re.sub(r"\A(---[ \t]*\n(?:(?!---|status:).*\n)*)status:.*", rf"\1status: {written}",
                                   text, count=1))
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


def within(path: str, place: str) -> bool:
    """True when a path, as data_path writes it, is place or is under it.

    The place "" is the project root, so it covers no path outside the project:
    none that starts with ../ and none that is absolute (#224, review finding 1).
    """
    if place == "":
        return not (path == ".." or path.startswith("../") or posixpath.isabs(path) or ntpath.isabs(path))
    return path == place or path.startswith(place + "/")


def same_level(a, b) -> bool:
    """Levels are compared without regard to case; no level (None) is a level of its own."""
    return a is None and b is None or a is not None and b is not None and a.casefold() == b.casefold()


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
        if (record["agent"].casefold() == agent.casefold() and same_level(record.get("level"), found["level"])
                and within(found["path"], record["reads"])):
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


def rule_paths(project: Path, config: dict) -> dict:
    """The data rules, each path as data_path writes it."""
    return {data_path(project, key): level for key, level in config.get("data", {}).items()}


def clearance(project: Path, config: dict, path: str, agent: str) -> dict:
    """Whether the recorded data rules let this coding agent read one file (P12).

    The rule for the file wins, then the rule for the nearest folder above it.
    A file is cleared when its level is Public, or when approved-tools gives
    this agent that level or a more restricted one in classification-levels.
    """
    rules = rule_paths(project, config)
    over = [key for key in rules if within(path, key)]
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
    # A folder that is read is read with every file in it, so each rule below it is checked too (#224).
    places, rules = [] if reads == ["none"] else [data_path(project, r) for r in reads], rule_paths(project, config)
    places += sorted({key for place in places for key in rules if key != place and within(key, place)} - set(places))
    data = [clearance(project, config, place, args.agent) for place in places]
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
    status.add_argument("--playbook", help="with --guide: the playbook the human asked for by name")
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
    approve = sub.add_parser("approve", help="record the human's yes to a plan or an intent, or their decision "
                                             "on data")
    approve.add_argument("artifact", nargs="?", help="the plan or the intent the human said yes to")
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
