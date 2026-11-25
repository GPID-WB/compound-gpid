"""Lint skill folders: frontmatter, names, line budgets, sections and links.

Usage: python tools/lint_skills.py [PATH ...]

PATH is the hub's `packs/` folder (the default), one pack folder, or one
skill folder. Every rule is an error; there are no warnings. Exit code 1
when any error is found.

Rules
- Every folder of a pack holds a SKILL.md (folders starting with "." are
  host manifests and are skipped).
- Frontmatter: present, ASCII only, top-level keys from PORTABLE_KEYS only,
  and free of the YAML shapes a strict host parser rejects (tab indentation,
  an unclosed quote, an unquoted value that starts with a YAML indicator or
  holds ": ").
- `name` equals the folder name, lowercase words joined by hyphens, at most
  64 characters. `description` is present and at most 1024 characters.
- Line budgets from SCOPE.md (LINE_BUDGETS below).
- Principle files hold their four headed parts (REQUIRED_SECTIONS).
- Links in every Markdown file of a skill resolve, and stay inside that skill
  folder (ADR 0003, rule 4). Web, mail and in-page links are not followed.

Pattern from addyosmani/agent-skills@e997ac5:scripts/lib/skill-lint.js
(spec-only top-level keys, the narrow YAML rules, name equals folder); the
code is our own.
"""
import re
import sys
from pathlib import Path

# The Agent Skills specification's top-level keys, plus one host key.
# disable-model-invocation is honored by Claude Code and Copilot and ignored
# without error by Codex and Kilo (ADR 0001), so it is safe in every host.
PORTABLE_KEYS = {"name", "description", "license", "compatibility", "metadata",
                 "allowed-tools", "disable-model-invocation"}
NAME = re.compile(r"[a-z0-9]+(-[a-z0-9]+)*")
MAX_NAME, MAX_DESCRIPTION = 64, 1024

# (test on the path relative to the pack folder, budget, what it is). First match wins.
LINE_BUDGETS = [
    (lambda rel, pack: pack == "core" and rel == "cg/SKILL.md", 100, "the guide's SKILL.md"),
    (lambda rel, pack: rel.split("/")[1:2] == ["playbooks"] and rel.endswith(".md"), 120, "a playbook"),
    (lambda rel, pack: rel.split("/")[1:2] == ["principles"] and re.search(r"/P\d+-[^/]*\.md$", rel),
     120, "a principle file"),
    (lambda rel, pack: rel.split("/")[1:2] == ["lenses"] and rel.endswith(".md"), 60, "a lens"),
    (lambda rel, pack: rel.count("/") == 1 and rel.endswith("/SKILL.md"), 500, "a SKILL.md"),
]
REQUIRED_SECTIONS = {
    "principle": ["## In production", "## Evidence it leaves", "## Verifier", "## Deterministic checks"],
}
LINK = re.compile(r"!?\[[^\]]*\]\(\s*<?([^)\s>]+)>?(?:\s+\"[^\"]*\")?\s*\)")
REF_LINK = re.compile(r"^\s{0,3}\[[^\]]+\]:\s*<?(\S+?)>?(?:\s|$)")


def split_frontmatter(text):
    """Return (frontmatter lines or None, body start line index)."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None, 0
    for i, line in enumerate(lines[1:], 1):
        if line.strip() == "---":
            return lines[1:i], i + 1
    return None, 0


def yaml_problems(lines):
    """Shapes a strict YAML parser rejects that a line reader would accept."""
    found = []
    for number, line in enumerate(lines, 2):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if re.match(r"^ *\t", line):
            found.append((number, "indents with a tab; YAML forbids tabs in indentation"))
            continue
        if ":" not in line:
            continue
        value = line.split(":", 1)[1].strip()
        if not value:
            continue
        if value[0] in "\"'":
            if len(value) < 2 or not value.endswith(value[0]):
                found.append((number, f"opens a {value[0]} quote that never closes"))
        elif re.match(r"[`@%*,]", value):
            found.append((number, f"unquoted value starts with '{value[0]}'; wrap it in quotes"))
        elif re.match(r"[|>]\S", value) or re.match(r"[-?&](\s|$)", value):
            found.append((number, f"unquoted value starts with '{value[0]}'; wrap it in quotes"))
        elif re.search(r":(\s|$)", value) and not re.match(r"[\[{]", value):
            found.append((number, "unquoted value holds ': '; wrap it in quotes"))
    return found


def read_text(path: Path, errors):
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError as error:
        errors.append((path, 0, f"not UTF-8 ({error.reason} at byte {error.start})"))
        return None


def lint_frontmatter(skill: Path, errors):
    path = skill / "SKILL.md"
    text = read_text(path, errors)
    if text is None:
        return
    front, _ = split_frontmatter(text)
    if front is None:
        errors.append((path, 1, "no frontmatter block (--- at the top, closed by ---)"))
        return
    for number, line in enumerate(front, 2):
        if any(ord(ch) > 127 for ch in line):
            errors.append((path, number, "frontmatter is not ASCII; some hosts fail to parse it"))
    for number, message in yaml_problems(front):
        errors.append((path, number, message))
    fields = {}
    for number, line in enumerate(front, 2):
        match = re.match(r"([A-Za-z0-9_-]+)\s*:\s*(.*)$", line)
        if not match:
            continue
        key, value = match.group(1), match.group(2).strip()
        fields[key] = value[1:-1] if len(value) > 1 and value[0] == value[-1] and value[0] in "\"'" else value
        if key not in PORTABLE_KEYS:
            errors.append((path, number, f"frontmatter key '{key}' is not portable; allowed at the top "
                                         f"level: {', '.join(sorted(PORTABLE_KEYS))}; "
                                         f"put anything else under 'metadata'"))
    name, description = fields.get("name", ""), fields.get("description", "")
    if not name:
        errors.append((path, 1, "frontmatter has no 'name'"))
    elif name != skill.name:
        errors.append((path, 1, f"name '{name}' does not match the folder '{skill.name}'"))
    if not NAME.fullmatch(skill.name) or len(skill.name) > MAX_NAME:
        errors.append((path, 1, f"folder name '{skill.name}' is not lowercase words joined by "
                                f"hyphens, at most {MAX_NAME} characters"))
    if not description:
        errors.append((path, 1, "frontmatter has no 'description'"))
    elif len(description) > MAX_DESCRIPTION:
        errors.append((path, 1, f"description is {len(description)} characters, over {MAX_DESCRIPTION}"))


def prose(lines):
    """Yield (line number, text) outside fenced code blocks."""
    fence = None
    for number, line in enumerate(lines, 1):
        match = re.match(r"^ {0,3}(`{3,}|~{3,})", line)
        if match:
            if fence is None:
                fence = match.group(1)
            elif match.group(1)[0] == fence[0] and len(match.group(1)) >= len(fence):
                fence = None
            continue
        if fence is None:
            yield number, line


def lint_file(path: Path, skill: Path, pack: Path, errors):
    rel = path.relative_to(pack).as_posix()
    text = read_text(path, errors) if path.name != "SKILL.md" else path.read_text(encoding="utf-8", errors="replace")
    if text is None:
        return
    lines = text.splitlines()
    for test, budget, what in LINE_BUDGETS:
        if test(rel, pack.name):
            if len(lines) > budget:
                errors.append((path, budget + 1, f"{what} is {len(lines)} lines, over its budget of {budget}"))
            break
    if re.search(r"/principles/P\d+-[^/]*\.md$", "/" + rel):
        headings = [line.strip() for _, line in prose(lines) if line.startswith("## ")]
        for section in REQUIRED_SECTIONS["principle"]:
            if not any(h == section or h.startswith(section + ":") for h in headings):
                errors.append((path, 1, f"principle file has no '{section}' section"))
    for number, line in prose(lines):
        line = re.sub(r"`[^`]*`", "", line)
        targets = LINK.findall(line) + REF_LINK.findall(line)
        for target in targets:
            if re.match(r"[a-z][a-z0-9+.-]*:", target, re.I) or target.startswith("#"):
                continue
            target = target.split("#", 1)[0].split("?", 1)[0]
            if not target:
                continue
            if target.startswith("/"):
                errors.append((path, number, f"link '{target}' is an absolute path"))
                continue
            resolved = (path.parent / target).resolve()
            if not resolved.exists():
                errors.append((path, number, f"link '{target}' points at nothing"))
            elif skill.resolve() not in (resolved, *resolved.parents):
                errors.append((path, number, f"link '{target}' leaves the skill folder '{skill.name}'"))


def skill_folders(arg: Path):
    """Return (pack folder, skill folder) pairs for a hub, pack or skill path."""
    if (arg / "SKILL.md").is_file():
        return [(arg.parent, arg)]
    # A pack folder has skill folders as children; the hub's packs/ folder has pack folders.
    is_pack = any(arg.glob("*/SKILL.md")) or any(arg.glob("*/pack.json"))
    packs = [arg] if is_pack else sorted(p for p in arg.iterdir() if p.is_dir())
    pairs = []
    for pack in packs:
        pairs += [(pack, s) for s in sorted(pack.iterdir()) if s.is_dir() and not s.name.startswith(".")]
    return pairs


def lint(paths):
    errors = []
    for arg in paths:
        for pack, skill in skill_folders(arg):
            if not (skill / "SKILL.md").is_file():
                errors.append((skill, 0, "folder in a pack without a SKILL.md"))
                continue
            lint_frontmatter(skill, errors)
            for path in sorted(skill.rglob("*.md")):
                lint_file(path, skill, pack, errors)
    return errors


def main(argv):
    paths = [Path(a) for a in argv] or [Path("packs")]
    errors = lint(paths)
    for path, line, message in errors:
        print(f"ERROR {path}:{line}: {message}")
    count = sum(len(skill_folders(p)) for p in paths)
    print(f"{count} skill folders, {len(errors)} errors")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
