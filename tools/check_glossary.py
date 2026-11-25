"""Check text files against the avoided words in a glossary.

Usage: python tools/check_glossary.py [--glossary PATH] [--notes] [FILE_OR_DIR ...]

With no FILE_OR_DIR, the hub's own text is checked (DEFAULT_PATHS), from
whatever folder the command runs in. CI, CONTRIBUTING.md and the handoff
call it that way, so this list is the one place a new document is added.

An avoided word with no condition is an error. An avoided word with a
condition in brackets, such as "test (when it is not a unit test)", needs
judgement, so it is only counted, and listed when --notes is given. It never
fails the run.

Skipped: YAML frontmatter, fenced code blocks, inline code, and the
glossary file itself. Exit code 1 when any error is found.
"""
import re
import sys
from pathlib import Path

HUB = Path(__file__).resolve().parent.parent
DEFAULT_GLOSSARY = HUB / "packs" / "core" / "cg" / "GLOSSARY.md"
DEFAULT_PATHS = ["packs", "docs/adr", "docs/v2", "docs/adoption-ledger.md", "docs/install-block.md",
                 "SCOPE.md", ".out-of-scope", "spike", "README.md", "CONTRIBUTING.md", "AGENTS.md"]


def read_avoided(glossary: Path):
    """Return (errors, notes): lists of (avoided word, preferred term, condition)."""
    errors, notes, term, terms = [], [], None, set()
    for line in glossary.read_text(encoding="utf-8").splitlines():
        heading = re.match(r"\*\*(.+?)\*\*:\s*$", line)
        if heading:
            term = heading.group(1)
            terms.add(term.lower())
        elif line.startswith("_Avoid_:") and term:
            for item in line[len("_Avoid_:"):].split(","):
                item = item.strip()
                cond = re.match(r"(.+?)\s*\((.+)\)$", item)
                if cond:
                    notes.append((cond.group(1).lower(), term, cond.group(2)))
                elif item:
                    errors.append((item.lower(), term, ""))
    # A conditional avoided word that is itself a defined term would be noted on
    # every correct use, so leave those to the verifier.
    notes = [n for n in notes if n[0] not in terms]
    return errors, notes


def prose_lines(path: Path):
    """Yield (line number, text) for prose only."""
    in_front = in_fence = False
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if number == 1 and line.strip() == "---":
            in_front = True
            continue
        if in_front:
            in_front = line.strip() != "---"
            continue
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if not in_fence:
            yield number, re.sub(r"`[^`]*`", "", line)


def main(argv):
    glossary = DEFAULT_GLOSSARY
    if argv[:1] == ["--glossary"]:
        glossary, argv = Path(argv[1]), argv[2:]
    show_notes = "--notes" in argv
    argv = [a for a in argv if a != "--notes"]
    if not argv:
        argv = [str(HUB / p) for p in DEFAULT_PATHS]
    errors, notes = read_avoided(glossary)
    files = []
    for arg in argv:
        p = Path(arg)
        files += sorted(p.rglob("*.md")) if p.is_dir() else [p]
    found_errors = found_notes = 0
    for path in files:
        if path.resolve() == glossary.resolve():
            continue
        for number, text in prose_lines(path):
            low = text.lower()
            for word, term, _ in errors:
                if re.search(rf"(?<![\w-]){re.escape(word)}(?![\w-])", low):
                    found_errors += 1
                    print(f"ERROR {path}:{number}: '{word}' -> use '{term}'")
            for word, term, cond in notes:
                if re.search(rf"(?<![\w-]){re.escape(word)}s?(?![\w-])", low):
                    found_notes += 1
                    if show_notes:
                        print(f"note  {path}:{number}: '{word}' is avoided {cond} -> '{term}'")
    print(f"{len(files)} files, {found_errors} errors, {found_notes} notes for a reviewer")
    return 1 if found_errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
