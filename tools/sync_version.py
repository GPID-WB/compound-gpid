"""Keep the hub's manifests in step with their sources.

Usage: python tools/sync_version.py [--check] [--root PATH]

Sources:
- each pack's version is the `version` in its lead skill's `pack.json`;
- the hub's version is the core pack's version;
- the hub URL is the `repository` in the root `plugin.json`.

Targets: the root `plugin.json` version, each pack's
`.claude-plugin/plugin.json` (version, repository), and the pack's entry in
`.claude-plugin/marketplace.json` (version, source).

Also checked, never fixed: every hub pack has an index entry and every local
index entry has a pack; outside the manifests, the hub URL appears in at most
one file of what ships (`packs/`, `tools/`, files at the root, and
`docs/install-block.md`), so moving the repository changes one line of text.

Without --check, drifted fields are rewritten. With --check, nothing is
written. Exit code 1 when anything is out of step.
"""
import json
import os
import sys
import tempfile
from pathlib import Path

MARKETPLACE = Path(".claude-plugin/marketplace.json")
ROOT_PLUGIN = Path("plugin.json")
URL_SCOPE_DIRS = ("packs", "tools")
URL_SCOPE_FILES = ("docs/install-block.md",)
URL_ALLOWED_IN = 1


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data) -> None:
    """Write atomically: a temporary file in the same folder, then a rename."""
    text = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
        os.replace(tmp, path)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


def hub_packs(root: Path):
    """Return {pack name: (pack folder relative to root, pack.json data)}."""
    packs = {}
    for manifest in sorted(root.glob("packs/*/*/pack.json")):
        data = read_json(manifest)
        packs[data["name"]] = (manifest.parent.parent.relative_to(root), data)
    return packs


def manifest_files(root: Path):
    files = {root / ROOT_PLUGIN, root / MARKETPLACE}
    files.update(root.glob("packs/*/.claude-plugin/plugin.json"))
    return files


def url_files(root: Path, url: str):
    """Files in the shipped scope, other than manifests, that hold the hub URL."""
    candidates = [p for p in root.iterdir() if p.is_file()]
    for name in URL_SCOPE_DIRS:
        candidates += [p for p in (root / name).rglob("*") if p.is_file()]
    candidates += [root / name for name in URL_SCOPE_FILES if (root / name).is_file()]
    skip = manifest_files(root)
    found = []
    for path in sorted(set(candidates)):
        if path in skip or "__pycache__" in path.parts:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        if url in text:
            found.append(path.relative_to(root).as_posix())
    return found


def sync(root: Path, check: bool):
    """Return a list of (fixable, message). Fix the fixable ones unless check is set."""
    problems = []
    fix = lambda m: problems.append((True, m))
    flag = lambda m: problems.append((False, m))
    packs = hub_packs(root)
    if "core" not in packs:
        return [(False, "no core pack: packs/core/<lead skill>/pack.json is missing")]
    core_version = packs["core"][1]["version"]

    root_plugin = read_json(root / ROOT_PLUGIN)
    url = root_plugin.get("repository", "")
    if not url:
        flag(f"{ROOT_PLUGIN}: no 'repository', so the hub URL has no source")
    if root_plugin.get("version") != core_version:
        fix(f"{ROOT_PLUGIN}: version {root_plugin.get('version')} != core {core_version}")
        root_plugin["version"] = core_version
        if not check:
            write_json(root / ROOT_PLUGIN, root_plugin)

    for name, (folder, data) in packs.items():
        path = root / folder / ".claude-plugin" / "plugin.json"
        if not path.is_file():
            flag(f"{path.relative_to(root).as_posix()}: missing")
            continue
        plugin, changed = read_json(path), False
        for key, want in (("version", data["version"]), ("repository", url)):
            if plugin.get(key) != want:
                fix(f"{path.relative_to(root).as_posix()}: {key} {plugin.get(key)!r} != {want!r}")
                plugin[key], changed = want, True
        if changed and not check:
            write_json(path, plugin)

    index = read_json(root / MARKETPLACE)
    entries = {e.get("name"): e for e in index.get("plugins", [])}
    changed = False
    for name, (folder, data) in packs.items():
        entry = entries.get(name)
        if entry is None:
            flag(f"{MARKETPLACE}: no entry for hub pack '{name}'")
            continue
        for key, want in (("version", data["version"]), ("source", f"./{folder.as_posix()}")):
            if entry.get(key) != want:
                fix(f"{MARKETPLACE}: '{name}' {key} {entry.get(key)!r} != {want!r}")
                entry[key], changed = want, True
    for name, entry in entries.items():
        source = entry.get("source")
        if isinstance(source, str) and source.startswith("./") and name not in packs:
            flag(f"{MARKETPLACE}: entry '{name}' points at {source}, which holds no pack")
    if changed and not check:
        write_json(root / MARKETPLACE, index)

    if url:
        holders = url_files(root, url)
        if len(holders) > URL_ALLOWED_IN:
            flag(f"hub URL appears outside the manifests in {len(holders)} files "
                            f"(at most {URL_ALLOWED_IN}): {', '.join(holders)}")
    return problems


def main(argv):
    check = "--check" in argv
    root = Path(argv[argv.index("--root") + 1]) if "--root" in argv else Path(".")
    problems = sync(root.resolve(), check)
    for fixable, line in problems:
        print(("DRIFT " if check else "fixed ") + line if fixable else "ERROR " + line)
    if not problems:
        print("manifests in step")
    failed = problems if check else [p for p in problems if not p[0]]
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
