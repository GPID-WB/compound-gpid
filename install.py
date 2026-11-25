"""Install Compound GPID packs from this hub into the user's skill folders.

Usage, where <python> is Python 3.9 or later (py -3 or python on Windows):
  <python> install.py --packs core,lang-r        first install of these packs
  <python> install.py --profile economist        first install of a profile
  <python> install.py --add lang-stata           add packs
  <python> install.py --remove lang-stata        remove packs
  <python> install.py --update                   copy the installed packs again from this hub
  <python> install.py --uninstall                remove everything install.py installed
  <python> install.py --remove-v1 [--project P]  remove what version 1 left that it owned
Add --dry-run to any of them to see what would change.

Where skills go (ADR 0001, design change 4): a real folder in ~/.agents/skills
(Codex, Kilo, Copilot) and a link to it from ~/.claude/skills (Claude Code).
Where a link cannot be made, a second real copy. Nothing goes into projects.

What install.py owns is listed in ~/.cg/installed.json, with a digest of each
folder. It never writes over, or removes, a folder it does not own or one
changed since it was installed. Standard library only; no Node.
"""
import argparse
import hashlib
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
from pathlib import Path

HUB = Path(__file__).resolve().parent
INDEX = HUB / ".claude-plugin" / "marketplace.json"
# Which packs each profile installs. Packs not yet in the hub are skipped with a note.
PROFILES = {
    "economist": ["core", "lang-r", "lang-stata", "research", "writing-wb"],
    "developer": ["core", "lang-r", "lang-python"],
    "everything": None,  # every pack in the index
}
V1_MARKER = ".compound-gpid-managed-copy.json"
V1_PROFILE_START = "# --- Compound GPID ---"


# ---------------------------------------------------------------- places

def home() -> Path:
    return Path.home()


def agents_root() -> Path:
    return home() / ".agents" / "skills"


def claude_root() -> Path:
    return home() / ".claude" / "skills"


def other_roots():
    """User-level folders a host reads; a copy there would be listed twice."""
    return [home() / ".kilo" / "skills", home() / ".copilot" / "skills"]


def record_path() -> Path:
    return home() / ".cg" / "installed.json"


def show(path: Path) -> str:
    try:
        return "~/" + path.relative_to(home()).as_posix()
    except ValueError:
        return str(path)


# ---------------------------------------------------------------- files

def is_link(path: Path) -> bool:
    """A symbolic link, or on Windows a directory junction (any Python version)."""
    if path.is_symlink():
        return True
    if os.name != "nt" or not path.exists():
        return False
    isjunction = getattr(os.path, "isjunction", None)  # Python 3.12 and later
    if isjunction is not None:
        return isjunction(str(path))
    try:
        os.readlink(path)  # reads junctions on Windows since Python 3.8
        return True
    except (OSError, ValueError):
        return False


def make_junction(target: Path, link: Path) -> bool:
    """Windows only: a directory junction needs no special rights (ADR 0001)."""
    if os.name != "nt":
        return False
    done = subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(target)], capture_output=True)
    return done.returncode == 0 and is_link(link)


def remove_link(path: Path) -> None:
    try:
        os.unlink(path)
    except OSError:
        os.rmdir(path)  # a directory link on Windows


def remove_tree(path: Path) -> None:
    def retry(func, name, _):
        os.chmod(name, stat.S_IWRITE)
        func(name)
    shutil.rmtree(path, onerror=retry)


def digest(folder: Path) -> str:
    h = hashlib.sha256()
    for path in sorted(p for p in folder.rglob("*") if p.is_file() and "__pycache__" not in p.parts):
        h.update(path.relative_to(folder).as_posix().encode())
        h.update(path.read_bytes())
    return h.hexdigest()


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(data, indent=2, sort_keys=True) + "\n")
    os.replace(tmp, path)


def place_copy(source: Path, target: Path) -> None:
    """Copy source to target through a temporary folder beside it, then rename."""
    target.parent.mkdir(parents=True, exist_ok=True)
    staging = target.parent / f".cg-new-{target.name}"
    if staging.exists():
        remove_tree(staging)
    try:
        shutil.copytree(source, staging, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    except BaseException:
        if staging.exists():
            remove_tree(staging)  # never leave a half-made copy where hosts read
        raise
    if target.exists() or is_link(target):
        old = target.parent / f".cg-old-{target.name}"
        os.replace(target, old)
        os.replace(staging, target)
        remove_link(old) if is_link(old) else remove_tree(old)
    else:
        os.replace(staging, target)


def place_link(target: Path, link: Path) -> str:
    """Link link -> target: a symbolic link, else on Windows a junction, else a copy.

    Returns 'link' or 'copy'.
    """
    link.parent.mkdir(parents=True, exist_ok=True)
    if is_link(link):
        remove_link(link)
    elif link.exists():
        remove_tree(link)
    try:
        os.symlink(target, link, target_is_directory=True)
        return "link"
    except (OSError, NotImplementedError):
        if make_junction(target, link):
            return "link"
        place_copy(target, link)
        return "copy"


# ---------------------------------------------------------------- hub

def hub_packs():
    """{name: {"version", "skills", "folder"}} for every local pack in the index."""
    index = json.loads(INDEX.read_text(encoding="utf-8"))
    packs = {}
    for entry in index.get("plugins", []):
        source = entry.get("source")
        if not (isinstance(source, str) and source.startswith("./")):
            continue  # packs from other repositories: not yet supported here
        folder = (HUB / source).resolve()
        manifests = sorted(folder.glob("*/pack.json"))
        if len(manifests) != 1:
            continue
        data = json.loads(manifests[0].read_text(encoding="utf-8"))
        packs[data["name"]] = {"version": data["version"], "skills": data["skills"], "folder": folder}
    return packs


def load_record():
    path = record_path()
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def plugin_copies(skill: str):
    """Copies of a skill that Claude Code installed as a plugin, lead skill or not (#220)."""
    base = home() / ".claude" / "plugins" / "cache"
    if not base.is_dir():
        return []
    return sorted(p.parent for p in base.rglob("SKILL.md") if p.parent.name == skill)


def conflicts(skills, record):
    """Every place a skill already exists that install.py does not own."""
    owned = (record or {}).get("skills", {})
    found = []
    for skill in skills:
        for root in (agents_root(), claude_root()):
            path = root / skill
            if (path.exists() or is_link(path)) and skill not in owned:
                found.append(f"{show(path)} exists and was not installed by install.py; "
                             f"move or remove it, then run again")
        for root in other_roots():
            if (root / skill).exists():
                found.append(f"{show(root / skill)}: a host reads that folder too and would list "
                             f"'{skill}' twice; remove that copy")
        for copy in plugin_copies(skill):
            found.append(f"{show(copy)}: '{skill}' is also installed as a Claude Code plugin; "
                         f"uninstall the plugin, or keep it and do not use install.py")
    return found


def not_owned_any_more(skills, record):
    """A recorded link that something else replaced. --force does not override this."""
    found = []
    for skill in skills:
        info = record["skills"].get(skill)
        path = claude_root() / skill
        if not info or info["claude"] != "link" or not (path.exists() or is_link(path)):
            continue
        if not is_link(path):
            found.append(f"{show(path)} is a folder install.py did not make (it made a link there); "
                         f"move it away, then run again")
        elif path.resolve() != (agents_root() / skill).resolve():
            found.append(f"{show(path)} links somewhere install.py did not link it; "
                         f"remove that link, then run again")
    return found


def changed_since_install(skills, record):
    found = []
    for skill in skills:
        info = record["skills"].get(skill)
        if not info:
            continue
        for path in (agents_root() / skill, claude_root() / skill if info["claude"] == "copy" else None):
            if path is None:
                continue
            if not path.is_dir():
                found.append(f"{show(path)} is missing")
            elif digest(path) != info["digest"]:
                found.append(f"{show(path)} was changed since it was installed; move your changes "
                             f"out of it, or pass --force to overwrite them")
    return found


# ---------------------------------------------------------------- actions

def save(record):
    write_json(record_path(), record)


def install_skills(names, packs, record, dry):
    """Install the packs' skills, writing the record after each step.

    Until the last pack is done the record says "unfinished", so a run that
    stops part-way owns what it already placed and can be run again.
    """
    if not dry:
        record["unfinished"] = names
        save(record)
    for name in names:
        pack = packs[name]
        for skill in pack["skills"]:
            target = agents_root() / skill
            print(f"install {name}: {skill} -> {show(target)}, linked from {show(claude_root() / skill)}")
            if dry:
                continue
            place_copy(pack["folder"] / skill, target)
            record["skills"][skill] = {"pack": name, "claude": "missing", "digest": digest(target)}
            save(record)
            how = place_link(target, claude_root() / skill)
            if how == "copy":
                print(f"  links are not allowed here; {show(claude_root() / skill)} is a second copy")
            record["skills"][skill]["claude"] = how
            save(record)
        record["packs"][name] = pack["version"]


def remove_skill(skill, record, dry):
    print(f"remove {record['skills'][skill]['pack']}: {skill} from {show(agents_root())} and {show(claude_root())}")
    if dry:
        return
    link = claude_root() / skill
    if is_link(link):
        remove_link(link)
    elif link.exists():
        remove_tree(link)
    if (agents_root() / skill).exists():
        remove_tree(agents_root() / skill)
    del record["skills"][skill]


def remove_skills(names, record, dry):
    for name in names:
        for skill in sorted(s for s, info in record["skills"].items() if info["pack"] == name):
            remove_skill(skill, record, dry)
        record["packs"].pop(name, None)


def run_doctor() -> int:
    cg = agents_root() / "cg" / "scripts" / "cg.py"
    if not cg.is_file():
        return 0
    print("\ncg.py doctor:", flush=True)  # flush so the lines above print first
    return subprocess.run([sys.executable, str(cg), "doctor"]).returncode


def resolve_names(text, packs):
    names, notes = [], []
    for name in [n.strip() for n in text.split(",") if n.strip()]:
        (names if name in packs else notes).append(name)
    return names, notes


# ---------------------------------------------------------------- version 1

def v1_clones():
    candidates = [home() / ".compound-gpid", Path("C:/WBG/.compound-gpid")]
    for entry in os.environ.get("PATH", "").split(os.pathsep):
        path = Path(entry)
        if path.name == "bin" and path.parent.name == ".compound-gpid":
            candidates.append(path.parent)
    seen, clones = set(), []
    for path in candidates:
        try:
            real = path.resolve()
        except OSError:
            continue
        if real not in seen and ((real / ".compound-gpid-source.json").is_file() or (real / "bin" / "cg-link").is_file()):
            seen.add(real)
            clones.append(real)
    return clones


def inside_any(path: Path, folders) -> bool:
    try:
        real = path.resolve()
    except OSError:
        return False
    return any(real == f or f in real.parents for f in folders)


def find_v1(project):
    """Return (removable paths, notes). Removable means version 1 provably owns it."""
    clones = v1_clones()
    removable, notes = [], []
    places = [agents_root(), claude_root(), *other_roots()]
    if project:
        places += [project / d / sub for d in (".github", ".claude", ".agents", ".kilo", ".opencode")
                   for sub in ("", "skills", "prompts", "agents", "commands", "instructions", "shared")]
    for folder in places:
        if not folder.is_dir() or is_link(folder) and not inside_any(folder, clones):
            continue
        entries = [folder] if is_link(folder) else sorted(folder.iterdir())
        for entry in entries:
            if is_link(entry) and inside_any(entry, clones):
                removable.append(entry)
            elif entry.is_dir() and not is_link(entry) and (entry / V1_MARKER).is_file():
                removable.append(entry)
            elif folder in places[:4] and entry.name.startswith(("cg-", "cr-")):
                notes.append(f"{show(entry)}: named like a version 1 skill but not provably "
                             f"version 1's; left in place, remove it yourself if it is")
    for clone in clones:
        uninstall = (f'& "{clone / "install.ps1"}" -Uninstall' if os.name == "nt"
                     else f"bash {show(clone / 'scripts' / 'install.sh')} --uninstall")
        notes.append(f"version 1 is installed at {show(clone)}. To take its commands off PATH, run: "
                     f"{uninstall}. Then delete {show(clone)} when you no longer need version 1.")
    for name in (".zshrc", ".bashrc", ".zprofile", ".bash_profile"):
        rc = home() / name
        if rc.is_file() and V1_PROFILE_START in rc.read_text(encoding="utf-8", errors="replace"):
            notes.append(f"{show(rc)} holds the version 1 PATH block; the uninstall command above removes it")
    kilo = home() / ".config" / "kilo" / "kilo.jsonc"
    if kilo.is_file() and ".compound-gpid" in kilo.read_text(encoding="utf-8", errors="replace"):
        notes.append(f"{show(kilo)} names the version 1 folder in a permission entry; remove that entry")
    if project and (project / ".gitignore").is_file() and \
            "# Compound GPID managed items" in (project / ".gitignore").read_text(encoding="utf-8", errors="replace"):
        notes.append(f"{project / '.gitignore'} holds the version 1 managed block; remove it when the links are gone")
    unique = sorted(set(removable), key=str)
    return unique, notes


def report_v1(project, remove, dry):
    removable, notes = find_v1(project)
    for path in removable:
        if remove:
            print(f"remove version 1: {show(path)}")
            if not dry:
                remove_link(path) if is_link(path) else remove_tree(path)
        else:
            print(f"version 1 left {show(path)}; install.py --remove-v1 removes it")
    for note in notes:
        print(f"note: {note}")


# ---------------------------------------------------------------- main

def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="install.py", description=__doc__.split("\n\n")[0])
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--packs")
    group.add_argument("--profile", choices=sorted(PROFILES))
    group.add_argument("--add")
    group.add_argument("--remove")
    group.add_argument("--update", action="store_true")
    group.add_argument("--uninstall", action="store_true")
    group.add_argument("--remove-v1", action="store_true")
    parser.add_argument("--project", help="with --remove-v1: also clean this project")
    parser.add_argument("--force", action="store_true", help="overwrite installed folders changed since install")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    dry = args.dry_run
    project = Path(args.project).resolve() if args.project else None

    if args.remove_v1:
        report_v1(project, remove=True, dry=dry)
        return 0

    packs = hub_packs()
    record = load_record()
    fresh = record is None
    record = record or {"hub": str(HUB), "packs": {}, "skills": {}}

    if args.packs or args.profile:
        if not fresh and not record.get("unfinished"):
            print(f"already installed ({', '.join(sorted(record['packs']))}); "
                  f"use --add, --remove, --update or --uninstall")
            return 1
        wanted = PROFILES[args.profile] if args.profile else None
        text = ",".join(wanted if wanted is not None else packs) if args.profile else args.packs
        names, unknown = resolve_names(text, packs)
        if "core" not in names:
            names.insert(0, "core")
        add = names
    elif args.add:
        if fresh:
            print("nothing is installed yet; start with --packs or --profile")
            return 1
        names, unknown = resolve_names(args.add, packs)
        add = [n for n in names if n not in record["packs"]]
        for name in sorted(set(names) - set(add)):
            print(f"note: pack '{name}' is already installed; --update copies it again")
    else:
        add, unknown = [], []

    for name in unknown:
        print(f"note: pack '{name}' is not in this hub; skipped")

    if args.remove or args.uninstall:
        if fresh:
            print("nothing is installed")
            return 1
        names = sorted(record["packs"]) if args.uninstall else [n.strip() for n in args.remove.split(",")]
        absent = [n for n in names if n not in record["packs"]]
        if absent:
            print("\n".join(f"pack '{n}' is not installed; installed: {', '.join(sorted(record['packs']))}"
                             for n in absent))
            return 1
        if "core" in names and not args.uninstall and set(record["packs"]) - set(names):
            print("core is needed by the other packs; remove them too, or use --uninstall")
            return 1
        skills = [s for s, info in record["skills"].items() if info["pack"] in names]
        problems = not_owned_any_more(skills, record) + ([] if args.force else changed_since_install(skills, record))
        if problems:
            print("\n".join(f"refused: {p}" for p in problems))
            return 1
        remove_skills(names, record, dry)
    if args.update:
        if fresh:
            print("nothing is installed")
            return 1
        names = sorted(n for n in record["packs"] if n in packs)
        skills = [s for s, info in record["skills"].items() if info["pack"] in names]
        problems = not_owned_any_more(skills, record) + ([] if args.force else changed_since_install(skills, record))
        if problems:
            print("\n".join(f"refused: {p}" for p in problems))
            return 1
        for skill in sorted(s for s, info in record["skills"].items()
                            if info["pack"] in names and s not in packs[info["pack"]]["skills"]):
            remove_skill(skill, record, dry)  # the pack no longer has this skill
        add = names
    if add:
        skills = [s for n in add for s in packs[n]["skills"] if s not in record["skills"] or not args.update]
        problems = conflicts([s for s in skills if s not in record["skills"]], record)
        if problems:
            print("\n".join(f"refused: {p}" for p in problems))
            return 1
        try:
            install_skills(add, packs, record, dry)
        except OSError as error:
            print(f"stopped: {error}")
            print("What was installed so far is recorded. Fix the cause, then run the same command again.")
            return 1

    if not dry:
        record.pop("unfinished", None)
        if record["packs"]:
            record["hub"] = str(HUB)
            write_json(record_path(), record)
        elif record_path().exists():
            record_path().unlink()
            launcher = home() / ".cg" / "launcher.json"
            if launcher.exists():
                launcher.unlink()
            if (home() / ".cg").is_dir() and not any((home() / ".cg").iterdir()):
                (home() / ".cg").rmdir()
    report_v1(None, remove=False, dry=True)
    if add and not dry and run_doctor() != 0:
        print("The packs are installed, but doctor found a problem above.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
