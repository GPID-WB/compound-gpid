"""cg.py: the deterministic tooling of the core pack.

Usage, with the interpreter that ~/.cg/launcher.json records as <python>:
  "<python>" cg.py doctor [--project PATH]
  "<python>" cg.py status [--project PATH] [--json] [--guide [--playbook NAME]]
  "<python>" cg.py new TYPE TITLE... [--project PATH] [--date YYYY-MM-DD]
  "<python>" cg.py new plan TITLE... --intent INTENT [--other-work] [--project PATH] [--date YYYY-MM-DD]
  "<python>" cg.py new work-report TITLE... [--plan PLAN] [--project PATH] [--date YYYY-MM-DD]
  "<python>" cg.py validate [FILE...] [--strict] [--json] [--project PATH]
  "<python>" cg.py approve PLAN|INTENT --reply "the human's reply, word for word" [--project PATH]
  "<python>" cg.py approve --reads FILE... --agent NAME --reply "..." [--project PATH]
  "<python>" cg.py approve REPORT --reply "..." [--project PATH]
  "<python>" cg.py tier --fact NAME=yes|no... --touches FILE...|--slice ID --reads FILE|none... [--agent NAME]
                      [--report REPORT] [--json] [--project PATH]
  "<python>" cg.py evidence [CHECK-ID | --run COMMAND] [--verdict not-verified|inconclusive] --report REPORT
                      [--project PATH]
  "<python>" cg.py guard [--report REPORT] [--base COMMIT] [--project PATH]
  "<python>" cg.py verifiers PLAN|REPORT|SOLUTION --stage STAGE [--json] [--project PATH]
  "<python>" cg.py conformance PLAN|REPORT|SOLUTION [--stage STAGE] [--verifier NAME --verdict VERDICT
                      --review independent|self-review [--finding "POINTER: WHAT"]... [--note TEXT]] [--json]
  "<python>" cg.py packs [--json]
  "<python>" cg.py setup [--packs a,b] [--setting pack.key=value]... [--classification-levels "A;B"]
                       [--approved-tool "agent=level"]... [--data "path=level"]...
                       [--project PATH] [--dry-run]

What each command does and why is in docs/adr/0005-artifacts.md, 0006-evidence.md, 0008-verifiers.md
and in its --help.
PATH may be any folder inside the project: the commands use the nearest folder
above it that holds .cg-docs/, else the root of its git repository.

Standard library only, Python 3.9 or later, one implementation for every
operating system. Every write is atomic and each record is its own file.
"""
import argparse
import datetime
import fnmatch
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
                          "### Boundaries", "## Data register", "## Slices", "## Open questions"]},
    "work-report": {"folder": "work-reports",
                    "statuses": {"in-progress": "open", "completed": "closed", "dropped": "closed"},
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
# Each a path from the project root. `approval` is the record of the human's yes, written by approve.
LINK_KEYS = ("intent", "plan", "work-report", "review", "supersedes", "approval")
KNOWN_KEYS = COMMON_KEYS + LINK_KEYS + ("size", "decided-by", "tags", "track")
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
# A "Fails when" cell that says its check cannot fail: a bare word, or a claim about the check.
# "never converges" and "N/A values appear" are outcomes (review of #226). The rest is by judgement.
CANNOT_FAIL = (r"(there is )?((it|this|this check|the check)( will| would| can| does)? )?((never|n/a|not applicable|"
               r"none|nothing)(\W*$|\s*[,;:(]|\s+[-–—]\s)|(never|cannot|can ?not|can'?t|will not|won'?t|no)\s+"
               r"fail|always (passes|succeeds)\b|(passes|succeeds)\W*$|no (failing )?outcome\b)")
# A mark of something still open, inside other text. Capitals only, so "pending households" is prose.
# (Q1) stands where the answer to a question of the plan goes, until the answer is written there.
OPEN_MARK = (r"(?<![\"'])\b[A-Z0-9_-]*(TBD|TODO|FIXME|XXX|PENDING|PLACEHOLDER)[A-Z0-9_-]*\b(?![\"'])|\?\?\?|"
             r"<[A-Za-z][a-z]*( [A-Za-z][a-z]*)+>|\(Q\d+\)")
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
# A yes to one of these facts stops the work each time, on a plan too: no earlier approval covers it (#227).
ALWAYS_STOP = ("irreversible",)
# What guard looks for in a change (P4): per rule a pattern, whether only test files are searched,
# and whether more of it (True) or less of it (False) than the commit holds is the problem.
TEST_FILE = r"(^|/)(tests?|testthat|spec)/|(^|/)test[-_.][^/]*$|[-_.](test|spec)s?\.[^/.]+$"
GUARD = (
    ("test-removed", r"\btest_that\s*\(|^\s*(async\s+)?def test_\w+|^\s*(it|test|describe)\s*\(|^\s*func Test\w+|"
                     r"\btest_(check|dir|file)\s*\(|\bunittest\.main\s*\(", True, False),
    ("assertion-removed", r"\bexpect(_\w+)?\s*\(|\bassert\w*\b|\bstopifnot\s*\(", True, False),
    ("test-skipped", r"\b(skip(_\w+|If|Unless|Test)?|importorskip)\s*\(|\.skip\b|\bmark\.(skip|xfail)|\bx(it|describe)\s*\(|"
                     r"\bt\.Skip\(|\bif\s*\(\s*(FALSE|F|0)\s*\)|^\s*if\s+(False|0)\s*:", True, True),
    ("test-excluded", r"--(ignore|deselect)(-glob)?[=\s]|\bcollect_ignore(_glob)?\b", False, True),
    # A message is no warning and no error, so suppressMessages() is not here (review of #227).
    ("suppression-added", r"\bsuppress(Warnings)?\s*\(|#\s*(nolint|noqa|type:\s*ignore|pragma:\s*no cover)|pylint:\s*disable|"
                          r"\b(filterwarnings|simplefilter)\s*\(|\bwarn\s*=\s*-\s*\d|\bsilent\s*=\s*T(RUE)?\b|"
                          r"@ts-(ignore|nocheck|expect-error)|eslint-disable|\|\|\s*(true\b|:)|\bset\s+\+e\b|"
                          r"\bexcept\b[^:\n]*:\s*(pass|\.\.\.)\s*$|\berror\s*=\s*function\s*\([^)]*\)\s*(NULL|NA\b|\{\s*\})|"
                          r"\bcap(t|tu|tur|ture)?\s+(noi(sily)?\s+)?(assert|confirm)\b", False, True),
)
# A line that is only a comment holds no test, assertion or skip: # in R, Python and the shell, * and // in Stata.
COMMENT = r"^[ \t]*(#|//|\*).*$"
# What git compares with before a repository's first commit: the empty tree.
EMPTY_TREE = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"
# The stages a principle file may name under `stages`, each with the type of artifact its verifiers
# look at. Which verifiers run at a stage is the principle files' to say, and no list here (#228).
STAGES = {"plan": "plan", "review": "work-report", "sign-off": "work-report", "compound": "solution"}
VERDICTS = ("PASS", "FLAG", "INCONCLUSIVE", "NOT-APPLICABLE")
REVIEWS = {"independent": "independent review", "self-review": "self-review"}
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


def say(lines, word="refused") -> int:
    """Print each line behind the word that says what it is. Returns the exit code of a refusal."""
    for line in lines:
        print(f"{word}: {line}")
    return 1


def write_record(project: Path, path: Path, record: dict) -> str:
    """Write one record as its own file. Returns its path from the project root."""
    write_atomic(path, json.dumps(record, indent=2, ensure_ascii=False) + "\n")
    return path.relative_to(project).as_posix()


def git(project: Path, *args):
    """What a git command prints in a folder, or None when it fails or git is not installed.
    These commands only read, so none takes the index lock."""
    if shutil.which("git") is None:
        return None
    done = subprocess.run(["git", "--no-optional-locks", "-c", "core.quotepath=off", "-C", str(project), *args],
                          capture_output=True, text=True, encoding="utf-8", errors="replace")
    return done.stdout.strip() if done.returncode == 0 else None


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
    if git(project, "rev-parse", "--is-inside-work-tree") != "true":
        return {"git": "not a repository"}
    # symbolic-ref names the branch before the first commit too; detached HEAD has none.
    branch = git(project, "symbolic-ref", "--short", "-q", "HEAD") or "HEAD (detached)"
    facts = {"git": "repository", "branch": branch}
    if git(project, "rev-parse", "--verify", "-q", "HEAD") is None:
        facts["commits"] = "none"
    changed = git(project, "status", "--porcelain")
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
    planned = {a["fields"].get("intent") for a in found if a["type"] == "plan" and a["status"] != "dropped"}
    waiting = [f"{a['path']} (status {a['status']})" for a in open_ones if a["state"] == "waiting"]
    waiting += [f"{a['path']} (status {a['status']}, not approved as it now reads)" for a in found
                if a["schema"] == SCHEMA and a["status"] in APPROVED.get(a["type"], ((), "", ()))[2]
                and not is_approved(project, a)]
    for a in (a for a in open_ones if a["type"] == "work-report" and a["schema"] == SCHEMA):
        held = tier_of(project, a)
        if held and held[1].get("stop") and not held[3]:
            waiting.append(f"{a['path']} (stops for the human's yes: {'; '.join(held[1]['stop'])})")
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
        # A decided intent is closed, so nothing above shows it: name each one no plan is built on yet.
        "ready-to-plan": [a["path"] for a in found if a["schema"] == SCHEMA and a["type"] == "intent"
                          and a["status"] == "decided" and is_approved(project, a) and a["path"] not in planned],
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
    top = git(folder, "rev-parse", "--show-toplevel")
    return Path(top).resolve() if top else folder


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
    order = ["project", "core", "phase", "reason", "active", "open-artifacts", "waiting-on-human", "ready-to-plan",
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
    intent = decided_intent(project, args.intent) if args.type == "plan" and args.intent else None
    if args.type == "plan":  # what a plan is built on, and what it must not push aside (#226)
        unfinished = [f"{a['path']} (status {a['status']})" for a in artifacts(project)
                      if a["type"] == "plan" and a["schema"] == SCHEMA and a["state"] != "closed"]
        if intent is None:
            print("refused: a plan is built on a decided intent; give its path with --intent. An intent is "
                  "decided by the human's recorded yes to its text. When no decided intent covers this work, "
                  "the human starts one with /cg brainstorm")
            return 1
        if unfinished and not args.other_work:
            print(f"refused: a plan is not finished: {'; '.join(unfinished)}\nThe same work goes on in that file: "
                  "a draft is edited, and an approved plan takes an amendment. When this is other work, ask the "
                  "human whether the new plan stands beside it, and after their yes add --other-work")
            return 1
    plan = None
    if args.type == "work-report" and args.plan:  # what holds the work to the plan (#227)
        plan = plan_of(project, {"fields": {"plan": args.plan}}, True)
        going = [a["path"] for a in artifacts(project) if a["type"] == "work-report" and a["state"] != "closed"
                 and plan and a["fields"].get("plan") == plan["path"]]
        if plan is None or going:
            print(f"refused: the work on this plan has a work report that is not finished: {going[0]}; continue in "
                  f"that file" if going else
                  "refused: work starts on a plan the human approved as it now reads; show them the plan, and "
                  "record their reply with approve. A change to an approved plan is an amendment")
            return 1
    template = CG_DIR / "templates" / f"{args.type}.md"
    safe_title = title.replace("\\", "\\\\").replace('"', '\\"')
    values = {"type": args.type, "title": safe_title, "heading": title, "date": date,
              "intent": intent["path"] if intent else "", "plan": plan["path"] if plan else "",
              "size": "standard" if plan else "quick"}
    # One pass, so a title that itself holds "{date}" is kept as written (#218).
    text = re.sub(r"\{(type|title|heading|date|intent|plan|size)\}", lambda m: values[m.group(1)],
                  template.read_text(encoding="utf-8"))
    if plan:  # on a plan the verdicts are in the conformance record, which says who gave each (#228)
        text = re.sub(r"^## Self-review\n.*?(?=^## )", "", text, flags=re.M | re.S)
    write_atomic(target, text)
    if plan and plan["status"] == "approved":
        set_front(project / plan["path"], {"status": "in-progress"})
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


def rows_of(body: str, heading: str, width: int, problems: list):
    """The rows of the table under a heading, each `width` cells wide. A row with more cells is
    named: a | outside backticks split a cell, and what followed it is out of view (review of #226)."""
    rows = [row for row in table_rows(body, heading) if row]
    problems += [f"the row {row[0]} under '{heading}' has {len(row)} cells and the table {width}; a | inside a "
                 f"cell goes in backticks" for row in rows if len(row) > width]
    return [(row + [""] * width)[:width] for row in rows]


def id_problems(ids, letter: str):
    """What is wrong with the IDs of one table: each is the letter and a number, and none appears twice."""
    return ([f"'{i}' is not an ID such as {letter}1" for i in ids if not re.fullmatch(letter + r"\d+", i)]
            + [f"the ID {i} appears twice" for i in sorted({i for i in ids if ids.count(i) > 1})])


def command_of(cell: str):
    """What a Command cell declares: its one text in backticks, with a \\| read as the table shows
    it. None when it holds no such text or more than one: code would run a file name or prose
    (gate rerun 17, review of #227)."""
    spans = [span.strip() for span in re.findall(r"`([^`]+)`", cell)]
    return spans[0].replace("\\|", "|") if len(spans) == 1 and spans[0] else None


def sha_of(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def contract_problems(body: str):
    """What P1 asks of a contract that code can check: requirements and checks carry IDs, every
    requirement has a check that names it, and every check has a command and a failing outcome."""
    problems, ids, covered = [], [], set()
    rows = rows_of(body, "### Requirements", 2, problems)
    requirements, checks = [rid for rid, _ in rows], rows_of(body, "### Checks", 4, problems)
    problems += [f"requirement {rid} says nothing" for rid, text in rows if nothing(text)]
    if not requirements or not checks:
        problems.append("the Requirements table and the Checks table each need a row")
    for cid, serves, command, fails in checks:
        named = re.findall(r"R\d+", serves)
        unknown = [rid for rid in named if rid not in requirements]
        if not named:
            problems.append(f"check {cid} names no requirement")
        if unknown:
            problems.append(f"check {cid} names {', '.join(unknown)}, which the Requirements table does not hold")
        if nothing(command):
            problems.append(f"check {cid} has no command")
        elif command_of(command) is None and not re.match(r"<[^<>]+>$", command.strip()):  # a request: unfilled()
            problems.append(f"check {cid}: its command is not one text in backticks; code runs what stands between "
                            f"them, so write the command as it is run in one pair of backticks")
        if nothing(fails):
            problems.append(f"check {cid} does not say which outcome means failure")
        elif re.match(CANNOT_FAIL, bare(fails)):
            problems.append(f"check {cid} cannot fail: '{fails}' names no outcome that means failure")
        covered.update(named)
        ids.append(cid)
    # A slice ends in a check, and a check that no slice ends in is never run (P4). Each slice says
    # which files it may touch (P6) and whether it is done by code, with the tool, or by judgement (P3).
    slices, run = rows_of(body, "## Slices", 5, problems), set()
    problems += [] if slices else ["the Slices table needs a row"]
    for sid, _, files, checked, how in slices:
        named = re.findall(r"C\d+", checked)
        if not named:
            problems.append(f"slice {sid} ends in no check")
        if set(named) - set(ids):
            problems.append(f"slice {sid} names {', '.join(sorted(set(named) - set(ids)))}, which the Checks "
                            f"table does not hold")
        if nothing(files):
            problems.append(f"slice {sid} names no file")
        if not re.search(r"\bby (code|judgement)\b", bare(how)):
            problems.append(f"slice {sid} does not say whether it is done by code or by judgement")
        elif "by judgement" not in bare(how) and nothing(bare(how).replace("by code", "")):
            problems.append(f"slice {sid} is done by code and names no tool")
        run.update(named)
    problems += [f"check {cid} is run by no slice" for cid in ids if slices and cid not in run]
    problems += id_problems(requirements, "R") + id_problems(ids, "C") + id_problems([s[0] for s in slices], "S")
    problems += [f"requirement {rid} has no check" for rid in requirements if rid not in covered]
    return problems


def plan_inputs(project: Path, a: dict):
    """What a plan rests on that code can check before the human's yes: a decided intent (P1), for
    each dataset in its register the classification the human had recorded (P12), and their answer
    to each open question (P2). A level typed into the plan is a description; only a recorded rule
    is a classification."""
    named = a["fields"].get("intent") or []
    named = [named] if isinstance(named, str) else named
    problems = [] if named else ["it names no intent; a plan is built on a decided intent, linked under 'intent'"]
    problems += [f"the intent {target} is not decided as it now reads; the human confirms it first, in a brainstorm"
                 for target in named if (project / target).is_file() and not decided_intent(project, target)]
    config = read_config(project)[0]
    config = {} if rule_problems(config) else config or {}
    # A row of the template is skipped: unfilled() names it. Any other row is a dataset (review of #226).
    rows = [[cell.strip("`\"'*~<> ") for cell in row] for row in rows_of(a["body"], "## Data register", 6, problems)
            if not unfilled("plan", "| " + " | ".join(row) + " |")]
    rules, listed = rule_paths(project, config), {data_path(project, row[0]) for row in rows}
    for name, level, *cells in rows:
        if name.lower() == "none":  # no dataset
            continue
        place = data_path(project, name)
        recorded = None if nothing(name) else clearance(project, config, place, "")["level"]
        # A folder is read with every file in it, as tier reads it (#224): a file at another level needs a row.
        hidden = [f"{key} in it is recorded as {rules[key]}" for key in sorted(rules) if key != place
                  and within(key, place) and key not in listed and not same_level(rules[key], level)]
        if any(nothing(cell) for cell in [name, level, *cells]):
            problems.append(f"the data register leaves a cell of {name or 'a row'} unfilled")
        elif recorded is None:
            problems.append(f"no classification is recorded for {name}, which the data register lists; ask the "
                            f"human for its level, and record it with setup --data")
        elif not same_level(recorded, level):
            problems.append(f"the data register gives {name} as {level}, and the recorded classification is "
                            f"{recorded}; write the recorded one, or record the human's with setup --data")
        elif hidden:
            problems.append(f"the data register gives {name} as {level}, and {'; '.join(hidden)}; give it a row "
                            f"of its own")
    asked = rows_of(a["body"], "## Open questions", 5, problems)
    problems += [] if asked else ['the Open questions table needs a row: a question, or "none" in each cell']
    return problems + asked_problems([q for q in asked if any(bare(c).strip(".") != "none" for c in q)], "question")


def decided_intent(project: Path, target: str):
    """The intent a path names, when it is decided on the human's yes to its text; else None."""
    at = artifact_at(project, target)
    intent = read_artifact(at[0], "intent", project) if at and at[1] == "intent" else None
    return intent if intent and intent["status"] == "decided" and is_approved(project, intent) else None


def bare(text: str) -> str:
    """A cell or a line without marks of emphasis, HTML comments, one-word tags such as <br> or
    <open>, entities, and the list mark or bracket before its first word, in lower case."""
    text = re.sub(r"<!--.*?-->|</?\w+\s*/?>|&#?\w+;", "", text)  # a template's request of several words stays
    text = re.sub(r"[`*_~()\[\]{}]", "", text).strip().lower()
    return re.sub(r"^(\d+[.)]\s+|[^\w\"'“‘«])+", "", text)


def nothing(cell: str, opens: bool = False, source: bool = False) -> bool:
    """True when a cell says nothing: no word, or only a placeholder such as `open`, pending, TBD
    or ?. A cell that only starts with such a word is content: "unknown codes are left in the
    output" names an outcome. With opens, for an answer or a source, it is nothing too, and the
    human's own words go in quotes. With source, "none" or "a guess" is nothing as well."""
    text = bare(cell)
    return (not re.search(r"\w", text) or bool(re.match(NOT_FILLED + ("" if opens else r"[\W_]*\Z"), text))
            or (source and bool(re.match(NO_SOURCE, text))))


def filler(line: str) -> bool:
    """True when a line under a heading says nothing. In a table row, every cell must say nothing."""
    cells = line.strip().strip("|").split("|") if line.lstrip().startswith("|") else [line]
    return all(nothing(cell) for cell in cells)


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


def asked_problems(rows, word: str):
    """What is wrong with rows that were put to the human (P2), an intent's decisions or a plan's open
    questions: the last two cells are the recommended answer and the human's answer, and a cell that
    only stands for "not yet" is neither. The IDs are the word's first letter and a number."""
    problems = []
    for rid, *_, recommended, answer in rows:
        if nothing(recommended, opens=True):
            problems.append(f"{word} {rid} has no recommended answer")
        if nothing(answer, opens=True):
            problems.append(f"{word} {rid} has no answer from the human yet"
                            + (f"; when '{answer}' is what they said, put it in quotes" if answer else ""))
    return problems + id_problems([row[0] for row in rows], word[0].upper())


def intent_problems(body: str):
    """What grilling must leave settled that code can check (P2): each fact names its source, and
    each decision was put to the human with a recommended answer and has their answer."""
    facts = [(row + [""] * 2)[:2] for row in table_rows(body, "## Facts") if row]
    decisions = [(row + [""] * 4)[:4] for row in table_rows(body, "## Decisions") if row]
    problems = [] if facts and decisions else ["the Facts table and the Decisions table each need a row"]
    problems += [f"the fact '{fact}' names no source" for fact, source in facts if nothing(source, True, True)]
    return problems + asked_problems(decisions, "decision")


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


def open_marks(body: str):
    """The lines of a body, outside fenced code and comments, that mark something as still open
    inside other text: a word in capitals such as TBD or VALUE-PENDING, ???, a request such as
    <the expected value>, or the ID of an open question, (Q1). A value in quotes is data (gate rerun 16, #226)."""
    lines, fenced = [], False
    for line in re.sub(r"<!--.*?-->", "", body, flags=re.S).splitlines():
        fenced = fenced != line.lstrip().startswith(("```", "~~~"))
        if not fenced and re.search(OPEN_MARK, line):
            lines.append(line.strip())
    return lines


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
            elif key == "approval":  # the artifact names its own record, and the record holds its text (#226)
                held = record_at(project / target)
                if held.get("artifact") != a["path"]:
                    errors.append(f"approval: {target} is not a record of this {a['type']}")
                elif "text" in held and text_hash(str(held["text"])) != held.get("hash"):
                    errors.append(f"approval: {target} does not hold the text it was approved for")
                elif held.get("hash") != text_hash(a["body"]) and is_approved(project, a):
                    errors.append(f"approval: {target} names the record of an earlier text; the newest one is in force")
    held = headings(a["body"])
    missing = [f"the section '{heading}' is missing" for heading in spec["sections"] if heading not in held]
    errors += missing
    warnings = [f"the key '{key}' is not part of schema {SCHEMA}" for key in fields if key not in KNOWN_KEYS]
    rests_on_yes = a["status"] in APPROVED.get(a["type"], ((), "", ()))[2]
    if a["type"] == "plan" and not missing:  # a plan set aside half written is left as it is (review of #226)
        (warnings if a["status"] in SETTLED else errors).extend(contract_problems(a["body"]))
        if approving or a["status"] == "draft":  # a draft's inputs may still be open; a yes needs them settled
            (errors if approving else warnings).extend(plan_inputs(project, a))
    if a["type"] == "intent" and not missing:  # an open decision is a draft's normal state
        (errors if approving or rests_on_yes else warnings).extend(intent_problems(a["body"]))
    if rests_on_yes and not approving and not is_approved(project, a):
        errors.append(f"its status is {a['status']}, but no approval is recorded for the {a['type']} as it now "
                      f"reads; show the human the {a['type']}, and record their reply with approve")
    if a["type"] == "work-report" and a["status"] == "completed":
        errors += unproven(project, a)
    if a["type"] == "decision" and a["status"] == "accepted" and not fields.get("decided-by"):
        errors.append("an accepted decision names the person who decided, in 'decided-by'")
    # What is unfinished is a warning while the artifact is being written, and an error after.
    being_written = (a["status"] == next(iter(spec["statuses"])) or a["status"] in SETTLED) and not approving
    unfinished = [f"nothing is written under '{heading}'" for heading in empty_sections(a["body"], spec["sections"])]
    left = unfilled(a["type"], a["body"])
    if left:
        unfinished.append(f"the template's text is still in it, first: {left[0]}")
    marked = [line for line in open_marks(a["body"]) if line not in left] if a["type"] == "plan" else []
    unfinished += [f"it still marks something as open, first: {marked[0]}"] if marked else []
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
    return "sha256:" + hashlib.sha256(approved_text(body).encode("utf-8")).hexdigest()


def approved_text(body: str) -> str:
    """A body as an approval holds it: without trailing spaces and without blank lines at either end."""
    return "\n".join(line.rstrip() for line in body.splitlines()).strip("\n")


def amendments(body: str):
    """The dated lines under `## Amendments`, such as `- 2026-11-26: what changes and why`. A date
    alone says nothing, so it is no amendment (review of #226)."""
    return [line.rstrip() for line in re.findall(r"^[-*] \d{4}-\d\d-\d\d:[ \t]*\S.*$",
                                                 section(body, "## Amendments"), re.M)]


def section(body: str, heading: str) -> str:
    """What stands under a level 2 heading, up to the next one; nothing when the heading is not there."""
    found = re.search(rf"^{re.escape(heading)}[ \t]*$(.*?)(?=^## |\Z)", body, re.M | re.S)
    return found.group(1).strip("\n") if found else ""


def record_at(path: Path) -> dict:
    """A record under .cg-docs/approvals/, or {} when the file is no record."""
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return record if isinstance(record, dict) else {}


def approvals(project: Path, artifact: dict):
    """Every approval record of an artifact. One approval is one file under .cg-docs/approvals/."""
    found, stem = [], Path(artifact["name"]).stem
    for path in sorted((project / ".cg-docs" / "approvals").glob("*.json")):
        record = record_at(path) if path.name.startswith(stem + ".") else {}
        if record.get("artifact") == artifact["path"]:
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
    name, email = (git(project, "config", "--get", key) or "" for key in ("user.name", "user.email"))
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
    if at and at[1] == "work-report":
        return approve_stop(project, read_artifact(at[0], "work-report", project), args.reply)
    if at is None or at[1] not in APPROVED:
        print(f"not a plan, an intent or a work report of this project: {args.artifact}")
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
    known, stamp, earlier = is_approved(project, plan), now(), approvals(project, plan)
    # The name holds the number of the approval, so a text approved a second time gets a record of its own.
    record_path = project / ".cg-docs" / "approvals" / f"{at[0].stem}.{digest[7:23]}.{len(earlier) + 1}.json"
    dated, before = amendments(plan["body"]), amendments(str(earlier[-1].get("text", "")) if earlier else "")
    if kind == "plan" and earlier and not known and (len(dated) <= len(before) or not set(before) <= set(dated)):
        refused.append("this plan was approved before, and a change to an approved plan is an amendment (P1); add "
                       "a line under a heading '## Amendments' at its end, such as '- 2026-11-26: what changes, "
                       "and why', keep the earlier lines, and show the human what changed")
    if refused:
        return say(refused)
    if known:
        print(f"already approved as it now reads: {plan['path']}")
    else:
        # The record keeps the text the human said yes to, so what was approved stays readable (P1).
        record = {"artifact": plan["path"], "hash": digest, "reply": args.reply, "name": name, "email": email,
                  "time": stamp, "text": approved_text(plan["body"])}
        print(f"approved {plan['path']}\nrecord: {write_record(project, record_path, record)}\n"
              f"hash: {digest}\nby: {name} <{email}>")
    # The two lines of the file that code changes: its status, and the record of the yes just written.
    set_front(at[0], {**({} if known else {"approval": record_path.relative_to(project).as_posix()}),
                      **({"status": written} if plan["status"] == "draft" else {})})
    return 0


def set_front(path: Path, keys: dict) -> None:
    """Set keys in the frontmatter of an artifact, and change nothing else in the file."""
    lines = path.read_text(encoding="utf-8-sig").split("\n")
    end = next(i for i, line in enumerate(lines[1:], 1) if line.strip() == "---")
    for key, value in keys.items():
        spot = next((i for i in range(1, end) if lines[i].startswith(f"{key}:")), end)
        lines[spot:spot + (spot < end)] = [f"{key}: {value}"]
        end += spot == end
    if keys:
        write_atomic(path, "\n".join(lines))


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
    found = [record_at(path) for path in sorted((project / ".cg-docs" / "approvals").glob("data.*.json"))]
    return [record for record in found if all(isinstance(record.get(key), str)
                                              for key in ("reads", "agent", "name", "time"))]


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
        return say(stops, "stop")
    if not args.agent:
        print("give --agent with the name of this coding agent, as tier takes it")
        return 2
    refused, name, email = the_yes(project, args.reply)
    if refused:
        return say(refused)
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
            print(f"recorded: {args.agent} reads {shown}, which is not cleared ({found['why']})\n"
                  f"record: {write_record(project, record_path, record)}\nby: {name} <{email}>")
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
    every run names the decision. With --report, code writes these lines as a
    record of the work report and names the reasons that stop the work until
    the human's yes is recorded: every reason in quick work, and on an approved
    plan those of ALWAYS_STOP, which no earlier approval covers.
    """
    project = project_from(args.project)
    if project is None:
        return 2
    config, stops = read_config(project)
    stops = stops + rule_problems(config)
    if stops:
        return say(stops, "stop")
    facts = pairs(args.fact, "--fact")
    if facts is None:
        return 2
    config, facts = config or {}, {name: value.lower() for name, value in facts.items()}
    reads, usage, touches = args.reads or [], [], args.touches or []
    report = report_at(project, args.report) if args.report else None
    if args.report and report is None:
        return 2
    plan = plan_of(project, report, True) if report else None  # a plan that is not approved covers nothing
    if plan or args.slice:  # the files of a slice are the plan's to say (P6)
        files = {row[0]: row[2] for row in rows_of(plan["body"], "## Slices", 5, [])} if plan else {}
        if args.slice not in files:
            usage.append(f"give --slice with the slice this work is on, and not --touches: '{args.slice or ''}' is "
                         f"no slice of the plan the work report names; its slices are: {', '.join(files) or 'none'}")
        touches = listed(project, files.get(args.slice, ""))
    if len(facts) < len(args.fact or []):
        usage.append("a fact is declared more than once; declare each fact once")
    usage += [f"'{name}' is not a fact; the facts are: {', '.join(FACTS)}" for name in facts if name not in FACTS]
    usage += [f"--fact {name} must be yes or no" for name, value in facts.items() if value not in ("yes", "no")]
    usage += [f"declare --fact {name}=yes or --fact {name}=no; a yes means {meaning}"
              for name, meaning in FACTS.items() if name not in facts]
    if not touches and not args.slice:
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
    files = sorted({data_path(project, f) for f in touches})
    reasons = [f"{name}: {FACTS[name]}" for name in FACTS if facts[name] == "yes"]
    reasons += [f"data: {d['path']} is not cleared for {args.agent}" for d in data
                if not d["cleared"] and not d["decision"]]
    if len(files) > MAX_FILES:
        reasons.append(f"size: the change touches {len(files)} files, more than {MAX_FILES}")
    state = {"tier": "elevated" if reasons else "low", "reasons": reasons, "data": data, "files": files,
             "facts": {name: facts[name] for name in FACTS}}
    if report:  # the start of a slice, or of quick work: what was declared, and what had changed before it
        # The plan's approval covers a data file its register lists; one it does not list stops (review of #227).
        register = [data_path(project, row[0].strip("`\"'*~<> ")) for row in rows_of(plan["body"], "## Data register",
                                                                                    6, [])] if plan else []
        unlisted = {f"data: {d['path']} is not cleared for {args.agent}" for d in data if not covers(register, d["path"])}
        state["stop"] = [r for r in reasons if plan is None or r.split(":")[0] in ALWAYS_STOP or r in unlisted]
        kept = {key: state[key] for key in ("tier", "reasons", "stop", "files", "facts")}
        commit = git(project, "rev-parse", "--verify", "-q", "HEAD")
        state["record"] = add_record(project, report, "tier", {
            "kind": "tier", "slice": args.slice, **kept, "commit": commit, "before": {
                name_key(name): held for name, held in digests(project, changed_files(project, commit or EMPTY_TREE)
                                                                or []).items()},
            "data": [{key: d[key] for key in ("path", "level", "cleared")} for d in data]})
    if args.json:
        print(json.dumps(state, indent=2, sort_keys=True))
        return 0
    shown = [f"{d['path']}{'=' + d['level'] if d['level'] else ''}: "
             f"{'cleared' if d['cleared'] else 'not cleared'} ({d['why']})"
             + (f"; read on the decision of {d['decision']['name']}, {d['decision']['time'][:10]}"
                if d["decision"] else "") for d in data]
    print(f"tier: {state['tier']}\nreasons: {'; '.join(reasons) or 'none'}\n"
          f"data: {'; '.join(shown) or 'none'}\nfiles: {len(files)}")
    if report:
        print(f"stop: {'; '.join(state['stop']) or 'none'}\nrecord: {state['record']}")
    return 0


# ---------------------------------------------------------------- evidence and guard

def report_at(project: Path, arg: str):
    """The work report a path names, as read_artifact reads it. When it names none, a line says so."""
    at = artifact_at(project, arg)
    if at and at[1] == "work-report":
        return read_artifact(at[0], "work-report", project)
    print(f"not a work report of this project: {arg}")


def plan_of(project: Path, report: dict, in_force: bool = False):
    """The plan a work report names under `plan`, or None. With in_force, only a plan that work may
    go on under: the human approved it as it now reads, and it is not finished."""
    at = artifact_at(project, str(report["fields"].get("plan") or ""))
    plan = read_artifact(at[0], "plan", project) if at and at[1] == "plan" else None
    live = plan and plan["status"] in ("approved", "in-progress") and is_approved(project, plan)
    return plan if live or not in_force else None


def listed(project: Path, cell: str):
    """The files a slice lists in its Files cell: paths, folders or patterns, apart by commas or spaces."""
    parts = (part.strip("`\"'") for part in re.split(r"[\s,;]+|<br\s*/?>", cell))
    return [data_path(project, part) for part in parts if part]


def covers(names, path: str) -> bool:
    """True when a path is one of the names, is under one that is a folder, or fits one that is a pattern."""
    return any(within(path, name) or fnmatch.fnmatchcase(path, name) for name in names)


def changed_files(project: Path, base: str = "HEAD"):
    """Every file that differs from a commit, new files too, outside .cg-docs/; None when git cannot say."""
    known = git(project, "diff", "--name-only", "--no-renames", "--relative", "-z", base, "--")
    new = git(project, "ls-files", "-z", "--others", "--exclude-standard")
    if known is None or new is None:
        return None
    return sorted({name for name in (known + "\0" + new).split("\0") if name and not name.startswith(".cg-docs/")})


def digests(project: Path, names) -> dict:
    """A digest of each named file as it now is, so that code can tell later whether it changed.
    A data file can be large, so it is read a block at a time."""
    found = {}
    for name in names:
        held = hashlib.sha256()
        try:
            with open(project / name, "rb") as handle:
                for block in iter(lambda: handle.read(1 << 20), b""):
                    held.update(block)
            found[name] = held.hexdigest()[:16]
        except OSError:
            found[name] = "gone"
    return found


def name_key(name: str) -> str:
    """How the tier record names a file it did not declare: by a digest, so no name of a file the work
    does not touch, a data file named after a person among them, is written down (review of #227)."""
    return sha_of(name)[7:23]


def base_of(project: Path, report: dict, whole: bool = False) -> str:
    """The commit the work began on: the one the first tier record of this slice holds, so that a commit
    in the slice hides nothing from guard (review of #227); before a first commit, the empty tree.
    With whole, the commit the first slice began on: what a verifier compares the whole change with."""
    tiers = [r for _, r in records(project, report, "tier")][:1 if whole else None]
    while len(tiers) > 1 and tiers[-2].get("slice") == tiers[-1].get("slice"):  # back to the start of this slice
        tiers.pop()
    return (tiers[-1].get("commit") if tiers else None) or git(project, "rev-parse", "--verify", "-q", "HEAD") \
        or EMPTY_TREE


def work_state(project: Path, declared, base: str = "HEAD") -> str:
    """One digest of the declared files that differ from the commit the work began on. Evidence holds for this
    state of them."""
    held = digests(project, [name for name in changed_files(project, base) or [] if covers(declared, name)])
    return "sha256:" + hashlib.sha256(json.dumps(held, sort_keys=True).encode("utf-8")).hexdigest()


def records(project: Path, report: dict, kind: str):
    """The records of one kind that code wrote for a work report, oldest first, as (path, record). A
    record is one file under .cg-docs/evidence/<the work report's name>/, named by its number."""
    folder = project / ".cg-docs" / "evidence" / Path(report["name"]).stem
    found = [(path, record_at(path)) for path in sorted(folder.glob("*.json"))]
    return [(path, record) for path, record in found if kind in ("any", record.get("kind"))]


def add_record(project: Path, report: dict, label: str, record: dict) -> str:
    """Write one more record for a work report, and never over another. Returns its path."""
    record = {"report": report["path"], **record, "time": now()}
    name = f"{len(records(project, report, 'any')) + 1:04d}-{re.sub(r'[-:]', '', record['time'])}-{label}.json"
    return write_record(project, project / ".cg-docs" / "evidence" / Path(report["name"]).stem / name, record)


def runs(project: Path, report: dict) -> dict:
    """The newest record of each check that ran: under its ID when the plan declares it, else under its command."""
    return {r.get("check") if r.get("label") == "declared" else r.get("command-digest"): r
            for _, r in records(project, report, "check")}


def tier_of(project: Path, report: dict):
    """The newest tier record of a work report as (path, record, digest, yes), or None. yes says
    whether the human's yes to that record is on file: to that file and to what it holds, since
    two records of one second hold the same text."""
    found = records(project, report, "tier")
    if not found:
        return None
    name, digest = found[-1][0].relative_to(project).as_posix(), text_hash(found[-1][0].read_text(encoding="utf-8"))
    return (*found[-1], digest, any(a.get("hash") == digest and a.get("tier") == name
                                    for a in approvals(project, report)))


def open_stop(project: Path, report: dict):
    """What keeps a piece of work from going on, or None: no risk computed for it yet, or a stop
    of its newest tier record that the human has not said yes to. No check is recorded past it."""
    held = tier_of(project, report)
    if held is None:
        return "no risk is computed for this work yet; run tier with --report first"
    if held[1].get("stop") and not held[3]:
        return (f"this work stops for the human's yes ({'; '.join(held[1]['stop'])}). Write under '## Risk' in the "
                f"work report what will be done, show it, ask, and end your turn. Record their reply with: approve "
                f"{report['path']} --reply")
    return None


def approve_stop(project: Path, report: dict, reply: str) -> int:
    """Record the human's yes to go on past a stop of tier: their reply word for word, who gave it,
    when, the tier record it answers, and what the work report said under Risk. The yes holds for
    that record alone: the next stop asks again."""
    held = tier_of(project, report)
    if held is None or not held[1].get("stop") or held[3]:
        print("already recorded: the human's yes to this stop" if held and held[3] else
              "nothing stops this work: its newest tier record names no reason that needs the human's yes, so "
              "there is nothing to record")
        return 0
    path, tier, digest, _ = held
    refused, name, email = the_yes(project, reply)
    if any(reason.startswith("data: ") for reason in tier["stop"]):  # a yes to the contract opens no file (P12)
        refused.append("a data file that is not cleared stops this work, and a yes to the contract does not open it; "
                       "record the human's decision to read it with approve --reads, or leave the file out, and run "
                       "tier again")
    asked = section(report["body"], "## Risk")
    if not asked.strip() or unfilled("work-report", asked):
        refused.append("the work report does not say under '## Risk' what the human is asked to say yes to; write "
                       "it there, show it to them, and ask again")
    if refused:
        return say(refused)
    record = {"artifact": report["path"], "tier": path.relative_to(project).as_posix(), "hash": digest, "reply": reply,
              "name": name, "email": email, "time": now(), "text": asked}
    target = (project / ".cg-docs" / "approvals"
              / f"{Path(report['name']).stem}.{digest[7:23]}.{len(approvals(project, report)) + 1}.json")
    print(f"recorded: the human's yes to {'; '.join(tier['stop'])}\nrecord: {write_record(project, target, record)}\n"
          f"by: {name} <{email}>")
    return 0


def unproven(project: Path, report: dict):
    """What keeps a work report from being completed: completion follows from evidence, never from
    a status typed into the file (P4). Every check of its plan is verified; in quick work, one is."""
    stop, plan = open_stop(project, report), plan_of(project, report)
    declared = {row[0]: command_of(row[2]) or "" for row in rows_of(plan["body"], "### Checks", 4, [])} if plan else {}
    # A declared run counts under its own plan, for the command that plan now declares (review of #227).
    verified = {key for key, run in runs(project, report).items() if run.get("verdict") == "verified" and (
        run.get("label") != "declared" or plan and run.get("plan") == plan["path"]
        and run.get("command-digest") == sha_of(declared.get(key, "")))}
    wanted = list(declared)
    problems = [stop] * bool(stop) + [f"check {cid} of the plan has no verified evidence; run it with evidence {cid}"
                                      for cid in wanted if cid not in verified]
    if not plan and not verified:
        problems.append("no check is verified in the evidence of this work; run each check through evidence, and "
                        "with no verified check leave the status in-progress")
    return problems


def cmd_evidence(args) -> int:
    """Run a check and record that it ran: the command, the exit code, the verdict, a digest and
    two counts of what it printed, and the commit. What it printed is shown and never stored.

    A check ID runs the command the approved plan declares for it. Any other command is given
    with --run and labelled ad hoc. With neither, the records of the work report are listed.
    """
    project = project_from(args.project)
    report = report_at(project, args.report) if project else None
    if report and args.check and args.run:
        print("give a check ID of the plan, or --run with another command, and not both")
    if report is None or (args.check and args.run):
        return 2
    plan = plan_of(project, report)
    checks = {row[0]: row[2] for row in rows_of(plan["body"], "### Checks", 4, [])} if plan else {}
    if not args.check and not args.run:
        held = runs(project, report)
        for path, r in records(project, report, "any"):
            print(f"{path.name}: " + (f"tier {r.get('tier')}; stop: {'; '.join(r.get('stop') or []) or 'none'}"
                                      if r.get("kind") == "tier" else
                                      f"{r.get('check')} ({r.get('label')}), exit {r.get('exit')}, {r.get('verdict')}: "
                                      f"{r.get('command')}"))
        for row in rows_of(plan["body"], "## Slices", 5, []) if plan else []:
            print(f"{row[0]}: " + "; ".join(f"{cid} {held[cid]['verdict'] if cid in held else 'not run'}"
                                            for cid in re.findall(r"C\d+", row[3])))
        return 0
    refused = [open_stop(project, report)]
    if args.check and plan is None:
        refused.append("this work report names no plan, so no check is declared for it; give the command with "
                       "--run, and it is recorded as ad hoc")
    elif args.check and not plan_of(project, report, True):
        refused.append(f"the plan {plan['path']} is not approved as it now reads; a change to an approved plan is "
                       f"an amendment, which the human approves before a check of it runs")
    elif args.check and args.check not in checks:
        refused.append(f"{args.check} is not a check of the approved plan, whose checks are {', '.join(checks)}; any "
                       f"other command is given with --run and recorded as ad hoc")
    elif args.check and command_of(checks[args.check]) is None:
        refused.append(f"the Command cell of {args.check} is not one text in backticks, so what it runs is not "
                       f"clear; that is a change to the plan, an amendment the human approves")
    if any(refused):
        return say(filter(None, refused))
    command = args.run or command_of(checks[args.check])  # the command is what the plan holds in backticks
    done = subprocess.run(command, shell=True, cwd=project, capture_output=True, stdin=subprocess.DEVNULL)
    printed = done.stdout + done.stderr
    sys.stdout.buffer.write(printed + b"\n" * (printed[-1:] not in (b"", b"\n")))
    sys.stdout.buffer.flush()
    verdict = (args.verdict or ("verified" if done.returncode == 0 else "not verified")).replace("-", " ")
    sha = "sha256:" + hashlib.sha256(printed).hexdigest()
    record = {"kind": "check", "check": args.check or "ad hoc", "label": "declared" if args.check else "ad hoc",
              **({"plan": plan["path"], "plan-hash": text_hash(plan["body"])} if args.check else {}),
              "command": command[:300], "command-digest": sha_of(command),
              "exit": done.returncode, "verdict": verdict,
              "output": {"digest": sha, "lines": printed.count(b"\n"), "bytes": len(printed)},
              "commit": git(project, "rev-parse", "--short", "HEAD") or "none",
              "state": work_state(project, tier_of(project, report)[1].get("files") or [], base_of(project, report))}
    print(f"check: {record['check']} ({record['label']})\nexit: {done.returncode}\nverdict: {verdict}\n"
          f"output: {record['output']['lines']} lines, {len(printed)} bytes, {sha}\n"
          f"record: {add_record(project, report, args.check or 'ad-hoc', record)}")
    return 0 if verdict == "verified" else 1


def cmd_guard(args) -> int:
    """Fail when a change lowers the bar or leaves what was declared (P4, P6).

    In the diff against a commit, new files included: a test file deleted, tests or assertions
    taken out, a test skipped, a checker silenced (GUARD). With --report, also: a stop the human
    has not answered, a file changed since the slice started that the slice does not list (in
    quick work, that tier was not given), and a check with no verified evidence on the files as
    they now are. It names the rule and the file, never a line. Exit code 2: guard could not run.
    """
    project = project_from(args.project)
    report = report_at(project, args.report) if project and args.report else None
    base = args.base  # with --report, the commit the slice began on (review of #227); before any commit, none
    if project and base == "HEAD":
        base = base_of(project, report) if report else "HEAD" if git(project, "rev-parse", "--verify", "-q", "HEAD") \
            else EMPTY_TREE
    files = changed_files(project, base) if project else None
    if files is None or (args.report and report is None):
        print(f"guard cannot run: git cannot compare the files of this project with {args.base}")
        return 2
    found, shown = [], "the first commit" if base == EMPTY_TREE else args.base if base == args.base else base[:12]
    for name in files:
        file, test = project / name, bool(re.search(TEST_FILE, name, re.I))
        if not file.is_file():
            found += [f"test-deleted: {name}"] * test
        elif file.suffix.lower() not in (".md", ".txt", ".rst") and file.stat().st_size < 1_000_000:
            new, old = file.read_text(encoding="utf-8", errors="replace"), git(project, "show", f"{base}:./{name}") or ""
            # A test, an assertion or a skip in a comment is not run (review of #227); a suppression is a comment.
            run = [re.sub(COMMENT, "", text, flags=re.M) for text in (new, old)]
            for rule, pattern, tests_only, more in GUARD:
                now, then = run if tests_only else (new, old)
                was = len(re.findall(pattern, then, re.M))
                lines = [str(now.count("\n", 0, m.start()) + 1) for m in re.finditer(pattern, now, re.M)]
                if (test or not tests_only) and (len(lines) > was if more else len(lines) < was):
                    found.append(f"{rule}: {name} holds {len(lines)} where {shown} holds {was}"
                                 + f"; see lines {', '.join(lines)}" * more)
    held = tier_of(project, report) if report else None
    stop = open_stop(project, report) if report else None
    found += [f"stop: {stop}"] * bool(stop)
    if held:
        tier, plan, tiers = held[1], plan_of(project, report), [r for _, r in records(project, report, "tier")]
        while len(tiers) > 1 and tiers[-2].get("slice") == tier.get("slice"):  # back to the start of this slice
            tiers.pop()
        before, declared = tiers[-1].get("before") or {}, tier.get("files") or []
        where = f"slice {tier['slice']} does not list it" if tier.get("slice") else "tier was not given it"
        now = digests(project, files)
        mine = [name for name in files if now[name] not in (before.get(name_key(name)), before.get(name))]
        found += [f"outside: {name} changed and {where}; undo it, or run tier again with it, which may stop the work"
                  for name in mine if not covers(declared, name)]
        rows = {row[0]: row[3] for row in rows_of(plan["body"], "## Slices", 5, [])} if plan else {}
        state, text = work_state(project, declared, base), text_hash(plan["body"]) if plan else None
        fresh = {key for key, run in runs(project, report).items() if run.get("verdict") == "verified"
                 and run.get("state") == state and run.get("plan-hash") in (None, text)}
        wanted = re.findall(r"C\d+", rows.get(tier.get("slice"), ""))
        found += [f"no-evidence: check {cid} is not verified on the files as they now are; run it with evidence {cid}"
                  for cid in wanted if cid not in fresh]
        if not wanted and not fresh:
            found.append("no-evidence: no check is verified on the files as they now are; run each through evidence")
    for line in found:
        print(f"FAIL {line}")
    print(f"guard: {len(found)} problem{'s' * (len(found) > 1)}" if found else "guard: clean")
    return 1 if found else 0


# ---------------------------------------------------------------- verifiers and conformance

def principles():
    """Each principle as the frontmatter of its file says it: its ID, its name, its verifier and the
    stages that verifier runs at. Dispatch is computed from these files (plan, section 4.2)."""
    found = []
    for path in sorted((CG_DIR / "principles").glob("P*.md")):
        fields = read_frontmatter(path.read_text(encoding="utf-8"))[0]
        found.append({**{key: str(fields.get(key, "")) for key in ("id", "name", "verifier")}, "path": path,
                      "stages": [stage.strip() for stage in str(fields.get("stages", "")).split(",") if stage.strip()]})
    return found


def work_files(project: Path, a: dict):
    """The files a lens of a pack is matched against: for a plan the files its slices list, for a work
    report the files that differ from the commit the work began on. None when code cannot tell, and
    then no lens is ruled out: git cannot say, or a slice lists a folder or a pattern."""
    if a["type"] == "plan":
        names = [name for row in rows_of(a["body"], "## Slices", 5, []) for name in listed(project, row[2])]
        return None if any("*" in name or "." not in posixpath.basename(name) for name in names) else names
    return changed_files(project, base_of(project, a, True)) if a["type"] == "work-report" else []


def dispatch(project: Path, a: dict, stage: str):
    """The verifiers that check an artifact at a stage, computed and never remembered: one for each
    principle whose `stages` names the stage, and one for each lens of an installed pack that serves
    such a principle and whose `when` fits the files and the track of the work (ADR 0003, rule 2).
    Each reads its principle file, and its lens when there is one: lenses/<verifier>.md in core."""
    files, track, found = work_files(project, a), a["fields"].get("track"), []
    lenses = [(pack, lens) for pack in discover_packs()[0]
              for lens in (read_pack(Path(pack["path"]) / "pack.json")[0] or {}).get("lenses") or []
              if isinstance(lens, dict)]
    for p in (p for p in principles() if stage in p["stages"]):
        own = CG_DIR / "lenses" / f"{p['verifier']}.md"
        found.append({"verifier": p["verifier"], "principle": p["id"], "name": p["name"],
                      "reads": [p["path"]] + [own] * own.is_file()})
        for pack, lens in lenses:
            when = lens.get("when") if isinstance(lens.get("when"), dict) else {"files": lens.get("when")}
            patterns = listed(project, when["files"]) if isinstance(when.get("files"), str) else []
            # A trigger that code cannot read rules nothing out, and a track narrows once the artifact names one.
            if lens.get("principle") == p["id"] and (not track or when.get("track") in (None, track)) and (
                    files is None or not patterns or any(covers(patterns, name) for name in files)):
                found.append({"verifier": f"{pack['name']}.{lens.get('id')}", "principle": p["id"], "name": p["name"],
                              "reads": [p["path"], Path(pack["path"]) / str(lens.get("file"))]})
    return found


def cg_line(project: Path, *words) -> str:
    """A line of cg.py as the agent runs it, with the interpreter, this file and the project filled in."""
    return " ".join([f'"{sys.executable}"', f'"{Path(__file__).resolve()}"', *words, f'--project "{project.as_posix()}"'])


def kickoff(project: Path, a: dict, stage: str, v: dict) -> str:
    """The text that starts one verifier: templates/kickoff.md, with nothing filled in but paths and
    IDs that code computes. No line of an artifact and no word of the agent that did the work goes
    into it, and the command takes none, so no kickoff holds the author's explanation (P5)."""
    def link(artifact, key):  # a link of the frontmatter is passed on only when it names a file
        value = artifact["fields"].get(key)
        return value if isinstance(value, str) and (project / value).is_file() else "a file that is not there"
    values = {"cg": CG_DIR.as_posix(), "verifier": v["verifier"], "principle": f"{v['principle']} {v['name']}",
              "stage": stage, "project": project.as_posix(), "artifact": a["path"], "contract": "none",
              "evidence": "none", "run": "none at this stage, so point at a file and a line",
              "reads": "\n".join(f"{number}. {Path(path).as_posix()}"
                                 for number, path in enumerate([CG_DIR / "verifier.md", *v["reads"]], 1))}
    if a["type"] == "plan":
        values["contract"] = f"in the plan itself; the human decided the intent it is built on, {link(a, 'intent')}"
    elif a["type"] == "work-report":
        base, plan = base_of(project, a, True), plan_of(project, a)
        values.update(
            artifact=f"every file that differs from commit {base} (`git diff {base}`), each file that no commit holds "
                     f"(`git status --short`), and the work report {a['path']}",
            contract='no plan: this is quick work, and what the human asked is under "Asked" in the work report',
            evidence=f".cg-docs/evidence/{Path(a['name']).stem}/ and .cg-docs/approvals/",
            run=cg_line(project, "evidence", "--run", '"<the command>"', "--report", f'"{a["path"]}"'))
        if plan:
            values["contract"] = f"the plan {plan['path']}, " + (
                f"which the human approved as the record {link(plan, 'approval')} holds it"
                if is_approved(project, plan) else "which the human has not approved as it now reads")
    template = (CG_DIR / "templates" / "kickoff.md").read_text(encoding="utf-8")
    return re.sub(r"\{([a-z]+)\}", lambda m: values.get(m.group(1), m.group(0)), template).strip()


def staged(project: Path, arg: str, stage):
    """The artifact that the verifiers of a stage look at, or of any stage when none is given, as
    read_artifact reads it. When the file is none, a line says so."""
    at = artifact_at(project, arg)
    if at and (at[1] == STAGES[stage] if stage else at[1] in STAGES.values()):
        return read_artifact(*at, project)
    print(f"at the {stage} stage the verifiers check {article(STAGES[stage])} of this project, and this is none: {arg}"
          if stage else f"not a plan, a work report or a solution of this project: {arg}")


def cmd_verifiers(args) -> int:
    """Print the verifiers that check an artifact at a stage: each with the kickoff that starts it,
    and the line that records its verdict. Then the line that lists the verdicts."""
    project = project_from(args.project)
    a = staged(project, args.artifact, args.stage) if project else None
    if a is None:
        return 2
    target = ["conformance", f'"{a["path"]}"', "--stage", args.stage]
    found = [{**v, "reads": [Path(path).as_posix() for path in v["reads"]],
              "kickoff": kickoff(project, a, args.stage, v),
              "record": cg_line(project, *target, "--verifier", v["verifier"], "--verdict",
                                f"<{', '.join(VERDICTS[:-1])} or {VERDICTS[-1]}>", "--review",
                                "<independent or self-review>")} for v in dispatch(project, a, args.stage)]
    if args.json:
        print(json.dumps(found, indent=2, sort_keys=True))
        return 0
    print(f"stage: {args.stage}\nartifact: {a['path']}\n"
          f"verifiers: {'; '.join(v['verifier'] + ' (' + v['principle'] + ')' for v in found) or 'none'}")
    for v in found:
        print(f"\n== {v['verifier']} ({v['principle']} {v['name']})\nkickoff:\n{v['kickoff']}\nrecord: {v['record']}")
    print(f"\nthen: {cg_line(project, *target)}")
    return 0


def verdicts(project: Path, a: dict):
    """(path, verdicts): the conformance record of an artifact, one file under .cg-docs/conformance/
    in a folder named as the artifact's, and every verdict code wrote into it, oldest first."""
    path = project / ".cg-docs" / "conformance" / ARTIFACT_FOLDERS[a["type"]] / f"{Path(a['name']).stem}.json"
    return path, [v for v in record_at(path).get("verdicts") or [] if isinstance(v, dict)]


def standing(project: Path, a: dict, stage: str):
    """Where an artifact stands at a stage: (stage, verifier, verdict) for each verifier that dispatch()
    names, with its newest verdict on record, or None. A verdict says under `earlier` whether the text
    it was given on has changed since. What applies is computed again each time, as the work now is."""
    newest = {v.get("verifier"): {**v, "earlier": v.get("on") not in (None, text_hash(a["body"]))}
              for v in verdicts(project, a)[1] if v.get("stage") == stage}
    return [(stage, v, newest.get(v["verifier"])) for v in dispatch(project, a, stage)]


def proven(project: Path, finding: str):
    """(pointer, sentence) when a finding opens with proof that code can open: a file of the project
    with a line it holds, as path:line, or the record of a run under .cg-docs/evidence/. Else None.
    Whether the pointer shows what the sentence says is for the reader to judge."""
    found = re.match(r"(.{1,400}?)(?::(\d+))?:\s+(\S.*)$", finding)
    name = data_path(project, found.group(1).strip("`\"' ")) if found else ".."
    try:
        if project not in (project / name).resolve().parents:  # a link that leaves the project is no file of it
            return None
        with open(project / name, "rb") as handle:  # its lines are counted, and nothing of it is kept
            lines = sum(1 for _ in handle)
    except (OSError, ValueError):
        return None
    held = (1 <= int(found.group(2)) <= lines if found.group(2) else
            name.startswith(".cg-docs/evidence/") and record_at(project / name).get("kind") == "check")
    return (name + (":" + found.group(2) if found.group(2) else ""), found.group(3)) if held else None


def cmd_conformance(args) -> int:
    """Record the verdict of one verifier on an artifact, or list its conformance record.

    A verdict is recorded only for a verifier that dispatch() names, and only with the kind of
    review that gave it. Code opens the proof of each finding: a finding with none goes under
    `unverified`, and a FLAG whose findings all lack it is recorded as UNVERIFIED. A record holds
    pointers and short sentences, and names no person. With no --verifier, the newest verdict of
    each verifier is listed, for work on a plan the plan's too. Exit code 1 while a verifier has
    given none: that is what keeps sign-off from being offered.
    """
    project = project_from(args.project)
    a = staged(project, args.artifact, args.stage) if project else None
    if a is None:
        return 2
    path, held = verdicts(project, a)
    if args.verifier:
        if not (args.stage and args.verdict and args.review):
            print("to record a verdict give --stage, --verifier, --verdict and --review: independent when another agent "
                  "in a fresh context gave the verdict on the kickoff alone, self-review when the agent that did the "
                  "work gave it")
            return 2
        named = {v["verifier"]: v for v in dispatch(project, a, args.stage)}
        findings, refused = [" ".join(text.split()) for text in args.finding or [] if text.strip()], []
        note = " ".join((args.note or "").split())
        if args.verifier not in named:
            refused.append(f"{args.verifier} is no verifier of the {args.stage} stage for {a['path']}; code says which "
                           f"ones run: {', '.join(named) or 'none'}")
        if (args.verdict == "FLAG") != bool(findings):
            refused.append("a FLAG comes with each finding, given once each with --finding, and any other verdict "
                           "comes with none: one finding makes the verdict a FLAG")
        if args.verdict in VERDICTS[2:] and not note:
            refused.append(f"{args.verdict} needs --note: what kept the verifier from checking, or why the principle "
                           f"does not apply to this work")
        if path.is_file() and not record_at(path):
            refused.append(f"{path.relative_to(project).as_posix()} cannot be read as a conformance record; put it "
                           f"right or move it away first, so that no verdict in it is written over")
        if refused:
            return say(refused)
        opened = [(text, proven(project, text)) for text in findings]
        entry = {"stage": args.stage, "verifier": args.verifier, "principle": named[args.verifier]["principle"],
                 "verdict": args.verdict.replace("-", " ") if any(p for _, p in opened) or not findings else "UNVERIFIED",
                 "review": args.review, "findings": [{"where": p[0], "what": p[1][:300]} for _, p in opened if p],
                 "unverified": [text[:300] for text, p in opened if not p], "note": note[:300],
                 # A verdict is on the text it was given on. A work report changes as it is filled in, so it has none.
                 "on": None if a["type"] == "work-report" else text_hash(a["body"]), "time": now()}
        print(f"recorded: {args.verifier} ({entry['principle']}) at the {args.stage} stage: {entry['verdict']}, "
              f"{REVIEWS[args.review]}" + "".join(f"\nunverified: {text}" for text in entry["unverified"]))
        if entry["unverified"]:
            print("  code found no proof it can open at the start of an unverified finding: a file of the project "
                  "with a line it holds, written path:line, or the record of a run under .cg-docs/evidence/")
        print(f"record: {write_record(project, path, {'artifact': a['path'], 'verdicts': held + [entry]})}")
        return 0
    plan = plan_of(project, a) if a["type"] == "work-report" and not args.stage else None
    rows = standing(project, plan, "plan") if plan else []
    for stage in [args.stage] if args.stage else [s for s, kind in STAGES.items() if kind == a["type"]]:
        rows += standing(project, a, stage)
    missing = [f"{stage} {v['verifier']}" for stage, v, given in rows if not given]
    shown = [given for *_, given in rows if given]
    if args.json:
        print(json.dumps({"artifact": a["path"], "verdicts": shown, "missing": missing}, indent=2, sort_keys=True))
        return 1 if missing else 0
    for stage, v, g in rows:
        print(f"{stage} {v['principle']} {v['verifier']}: " + ("no verdict" if not g else (
            f"{g.get('verdict')}, {REVIEWS.get(g.get('review'))}" + ", on an earlier text" * g["earlier"]
            + "".join(f"\n  finding: {f.get('where')}: {f.get('what')}" for f in g.get("findings") or [])
            + "".join(f"\n  unverified: {text}" for text in g.get("unverified") or [])
            + f"\n  note: {g.get('note')}" * bool(g.get("note")))))
    kinds = [g.get("review") for g in shown]
    print(f"missing: {'; '.join(missing) or 'none'}\nindependent review: {kinds.count('independent')}; "
          f"self-review: {kinds.count('self-review')}")
    if a["type"] == "work-report" and not args.stage:
        print("sign-off: " + ("blocked until each verifier under missing has given a verdict" if missing
                              else "every verifier has given a verdict"))
    return 1 if missing else 0


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
        return say(problems)
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
    new.add_argument("--intent", help="for a plan: the decided intent it is built on")
    new.add_argument("--other-work", action="store_true",
                     help="for a plan: the human said it stands beside the unfinished plan")
    new.add_argument("--plan", help="for a work report: the approved plan the work is held to")
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
    approve.add_argument("artifact", nargs="?", help="the plan or the intent the human said yes to, or the work "
                                                     "report whose stop they said yes to")
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
    tier.add_argument("--slice", help="on a plan: the slice that starts; its files are the plan's to say")
    tier.add_argument("--report", help="the work report: code writes what it prints as a record of it")
    tier.add_argument("--json", action="store_true")
    tier.add_argument("--project", default=".")
    evidence = sub.add_parser("evidence", help="run a check and record that it ran, or list the records")
    evidence.add_argument("check", nargs="?", help="the ID of a check the approved plan declares")
    evidence.add_argument("--run", help="any other command: it is recorded as ad hoc")
    evidence.add_argument("--verdict", choices=("not-verified", "inconclusive"),
                          help="what the exit code cannot see: the check exits with 0 and its outcome means failure")
    evidence.add_argument("--report", required=True, help="the work report the check belongs to")
    evidence.add_argument("--project", default=".")
    guard = sub.add_parser("guard", help="fail when a change removes or skips tests, silences a checker, or leaves "
                                         "what was declared")
    guard.add_argument("--report", help="the work report: also hold the change to its slice and its evidence")
    guard.add_argument("--base", default="HEAD", help="the commit the change is compared with")
    guard.add_argument("--project", default=".")
    verifiers = sub.add_parser("verifiers", help="print the verifiers that check an artifact at a stage, each with "
                                                 "its kickoff")
    conformance = sub.add_parser("conformance", help="record the verdict of a verifier, or list the verdicts on an "
                                                     "artifact")
    for command in (verifiers, conformance):
        command.add_argument("artifact", help="the plan, the work report or the solution that is checked")
        command.add_argument("--stage", choices=sorted(STAGES), required=command is verifiers)
        command.add_argument("--json", action="store_true")
        command.add_argument("--project", default=".")
    conformance.add_argument("--verifier", help="the verifier whose verdict is recorded, as verifiers names it")
    conformance.add_argument("--verdict", choices=VERDICTS, type=lambda text: text.upper().replace(" ", "-"))
    conformance.add_argument("--review", choices=sorted(REVIEWS), help="who gave the verdict: another agent in a "
                                                                       "fresh context, or the agent that did the work")
    conformance.add_argument("--finding", action="append", help="once for each finding: its pointer, a colon, and "
                                                                "what is wrong in one sentence")
    conformance.add_argument("--note", help="what the verifier could not check, or why the principle does not apply")
    args = parser.parse_args(argv)
    commands = {"doctor": cmd_doctor, "status": cmd_status, "new": cmd_new, "packs": cmd_packs, "setup": cmd_setup,
                "validate": cmd_validate, "approve": cmd_approve, "tier": cmd_tier, "evidence": cmd_evidence,
                "guard": cmd_guard, "verifiers": cmd_verifiers, "conformance": cmd_conformance}
    return commands[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
