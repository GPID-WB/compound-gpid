"""Validate packs against the pack contract (docs/adr/0003-packs.md).

Usage: python tools/validate_pack.py [PACK_FOLDER ...]

With no argument, every pack under `packs/` is validated, and skill names
are checked for uniqueness across all of them. A pack from another
repository is validated by passing its folder.

Rules
- Exactly one skill folder of the pack holds `pack.json`: the lead skill.
- `pack.json` has the six keys and no others, with the right types.
- `skills` lists every skill folder of the pack, and each listed folder exists.
- Each lens has `id`, `file`, `principle` and `when`; its file exists inside
  the lead skill; its principle exists among core's principle files; its
  `when` is file patterns as text, or an object with `files` and optionally
  `track` (ADR 0003, 2026-11-27); its `id` is lowercase words joined by
  hyphens, used once in the pack, since it names the verifier `<pack>.<id>`.
- Each track has `track` and `playbook` (and optionally `alias`); the
  playbook exists inside the lead skill.
- Skill names are unique across every pack validated together.
- The pack's skill files pass tools/lint_skills.py and
  tools/check_glossary.py, and its tooling passes tools/check_budgets.py.

Exit code 1 when any rule fails.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
HUB = TOOLS.parent
KEYS = ("name", "version", "requires-core", "skills", "lenses", "tracks")
LENS_KEYS = {"id", "file", "principle", "when"}
TRACK_KEYS = {"track", "playbook", "alias"}
VERSION = re.compile(r"\d+(\.\d+)*")
NAME = re.compile(r"[a-z0-9]+(-[a-z0-9]+)*")


def principle_ids():
    """The principle IDs core defines, read from the `id:` line of each file."""
    ids = set()
    for path in (HUB / "packs" / "core" / "cg" / "principles").glob("P*.md"):
        match = re.search(r"^id:\s*(P\d+)\s*$", path.read_text(encoding="utf-8"), re.M)
        if match:
            ids.add(match.group(1))
    return ids


def inside(base: Path, rel) -> bool:
    if not isinstance(rel, str) or not rel or rel.startswith("/") or "\\" in rel:
        return False
    target = (base / rel).resolve()
    return base.resolve() in target.parents and target.is_file()


def hub_core_version():
    try:
        data = json.loads((HUB / "packs" / "core" / "cg" / "pack.json").read_text(encoding="utf-8"))
        return tuple(int(n) for n in data["version"].split("."))
    except (OSError, ValueError, KeyError):
        return None


def newer(a, b) -> bool:
    width = max(len(a), len(b))
    return a + (0,) * (width - len(a)) > b + (0,) * (width - len(b))


def check_contract(pack: Path, principles):
    """Return (data or None, problems) for one pack folder."""
    problems = []
    leads = sorted(pack.glob("*/pack.json"))
    if len(leads) != 1:
        return None, [f"{pack}: {len(leads)} skill folders hold pack.json; exactly one must"]
    manifest = leads[0]
    lead = manifest.parent
    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
    except ValueError as error:
        return None, [f"{manifest}: not valid JSON ({error})"]
    if not isinstance(data, dict):
        return None, [f"{manifest}: not a JSON object"]
    keys = set(data)
    if keys != set(KEYS):
        missing, extra = sorted(set(KEYS) - keys), sorted(keys - set(KEYS))
        problems.append(f"{manifest}: keys must be exactly {', '.join(KEYS)}"
                        + (f"; missing {', '.join(missing)}" if missing else "")
                        + (f"; not in the contract {', '.join(extra)}" if extra else ""))
    if not isinstance(data.get("name"), str) or not NAME.fullmatch(data.get("name", "")):
        problems.append(f"{manifest}: name must be lowercase words joined by hyphens")
    for key in ("version", "requires-core"):
        if not isinstance(data.get(key), str) or not VERSION.fullmatch(data.get(key, "")):
            problems.append(f"{manifest}: {key} must be numbers joined by dots, such as 2.0.0")
    core = hub_core_version()
    needs = data.get("requires-core")
    if core and isinstance(needs, str) and VERSION.fullmatch(needs) and \
            newer(tuple(int(n) for n in needs.split(".")), core):
        problems.append(f"{manifest}: requires-core {needs} is newer than the hub's core "
                        f"{'.'.join(map(str, core))}; no install could satisfy it (#217)")
    skills = data.get("skills")
    if not isinstance(skills, list) or not all(isinstance(s, str) for s in skills):
        problems.append(f"{manifest}: skills must be a list of folder names")
        skills = []
    folders = sorted(p.name for p in pack.iterdir() if p.is_dir() and not p.name.startswith("."))
    for name in skills:
        if not (pack / name / "SKILL.md").is_file():
            problems.append(f"{manifest}: skill '{name}' has no folder with a SKILL.md in {pack}")
    for name in folders:
        if name not in skills:
            problems.append(f"{manifest}: folder '{name}' is in the pack but not in skills")
    if lead.name not in skills:
        problems.append(f"{manifest}: the lead skill '{lead.name}' is not in skills")
    for key, required, allowed, path_key in (("lenses", LENS_KEYS, LENS_KEYS, "file"),
                                             ("tracks", TRACK_KEYS - {"alias"}, TRACK_KEYS, "playbook")):
        entries = data.get(key)
        if not isinstance(entries, list):
            problems.append(f"{manifest}: {key} must be a list (empty when the pack has none)")
            continue
        for number, entry in enumerate(entries, 1):
            where = f"{manifest}: {key}[{number}]"
            if not isinstance(entry, dict):
                problems.append(f"{where} must be an object")
                continue
            if not required <= set(entry) or not set(entry) <= allowed:
                problems.append(f"{where} keys must be {', '.join(sorted(required))}"
                                + (" and optionally alias" if key == "tracks" else ""))
            if not inside(lead, entry.get(path_key)):
                problems.append(f"{where} {path_key} '{entry.get(path_key)}' is not a file inside {lead.name}/")
            if key != "lenses":
                continue
            ids = [other.get("id") for other in entries if isinstance(other, dict)]
            if not isinstance(entry.get("id"), str) or not NAME.fullmatch(entry["id"]) or ids.count(entry["id"]) > 1:
                problems.append(f"{where} id must be lowercase words joined by hyphens, used once in the pack: it "
                                f"names the verifier <pack>.<id> in a line that code prints to run (review of #228)")
            if entry.get("principle") not in principles:
                problems.append(f"{where} principle '{entry.get('principle')}' is not one of core's principles")
            when = entry.get("when") if isinstance(entry.get("when"), dict) else {"files": entry.get("when")}
            texts = [when.get("files"), when.get("track", "any")]
            if not set(when) <= {"files", "track"} or not all(isinstance(text, str) and text.strip() for text in texts):
                problems.append(f"{where} when must be file patterns as text, such as '*.R, *.Rmd', or an object "
                                f"with files and optionally track")
    return data, problems


def run_tool(script: str, *args):
    done = subprocess.run([sys.executable, str(TOOLS / script), *map(str, args)],
                          capture_output=True, text=True, cwd=HUB)
    return done.returncode, (done.stdout + done.stderr).strip()


def validate(packs):
    principles = principle_ids()
    problems, owners = [], {}
    for pack in packs:
        data, found = check_contract(pack, principles)
        problems += found
        for name in (data or {}).get("skills") or []:
            owners.setdefault(name, []).append(pack.name)
        for script, args in (("lint_skills.py", [pack]), ("check_glossary.py", [pack]),
                             ("check_budgets.py", ["--pack", pack])):
            code, out = run_tool(script, *args)
            if code != 0:
                problems.append(f"{pack}: {script} failed:\n{out}")
    for name, where in sorted(owners.items()):
        if len(where) > 1:
            problems.append(f"skill name '{name}' is used by more than one pack: {', '.join(where)}")
    return problems


def main(argv):
    packs = [Path(a).resolve() for a in argv] or sorted(p for p in (HUB / "packs").iterdir() if p.is_dir())
    problems = validate(packs)
    for line in problems:
        print(f"ERROR {line}")
    print(f"{len(packs)} packs, {len(problems)} problems")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
