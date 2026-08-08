#!/usr/bin/env python3
"""Validate YAML frontmatter in agent and skill markdown files.

Cross-platform companion to Invoke-YamlLint.ps1. Implements the same five
rules as the PowerShell validator so both entries report identical results:

  R1  description values must be double-quoted
  R2  frontmatter must be ASCII-only (U+0000-U+007F)
  R3  no UTF-8 BOM (EF BB BF)
  R4  required fields present (agents: description, mode; skills: name, description)
  R5  body content has no mojibake (UTF-8/Windows-1252 round-trip artifacts)

The bash entry (Invoke-YamlLint.sh) shells out to this module. The PowerShell
entry (Invoke-YamlLint.ps1) is a self-contained native implementation for
Windows; both accept the same flags and produce the same output.

Usage:
  python3 validate_yaml_frontmatter.py [-Path <dir>] [-Fix]
  python3 validate_yaml_frontmatter.py --Path .kilo --Fix

Exit codes: 0 = clean, 1 = violations or error.
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

FRONTMATTER_RE = re.compile(r"---\r?\n(.+?)\r?\n---", re.DOTALL)
DESCRIPTION_RE = re.compile(r"(?m)^description:\s*(.+)$")
FIELD_DESC_RE = re.compile(r"(?m)^description:")
FIELD_MODE_RE = re.compile(r"(?m)^mode:")
FIELD_NAME_RE = re.compile(r"(?m)^name:")
QUOTED_RE = re.compile(r'^".*"$')
SINGLE_QUOTED_RE = re.compile(r"^'.*'$")
# Valid YAML block-scalar headers: '>' or '|' plus optional indentation
# indicator ([1-9]) and/or chomping indicator (-/+) in either order, e.g. '>',
# '|-', '>2', '>2-', '>+2'. Rejects malformed forms such as '>invalid'.
BLOCK_SCALAR_RE = re.compile(r"^[>|](?:[1-9][-+]?|[-+][1-9]?)?$")
# Mirrors cg_generate_targets._yaml_scalar's unquoted-emit policy so the
# linter accepts exactly the valid YAML the generator emits unquoted (agent
# files) and only flags genuinely parse-breaking values (e.g. unquoted
# colon-space). Skill files require a double-quoted description (Rule 1).
SAFE_PLAIN_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._ /-]*$")
RESERVED_WORDS = {"null", "true", "false", "yes", "no", "on", "off"}
NON_ASCII_RE = re.compile(r"[^\x00-\x7f]")
MOJIBAKE_RE = re.compile(r"[\u00e2][\u20ac\u2020]")

# Non-ASCII -> ASCII replacements applied by -Fix inside frontmatter (Rule 2).
ASCII_FIXES = {
    "\u2014": "--",  # em-dash
    "\u2013": "-",   # en-dash
    "\u201c": '"',   # left double quote
    "\u201d": '"',   # right double quote
    "\u2018": "'",   # left single quote
    "\u2019": "'",   # right single quote / curly apostrophe
    "\u2192": "->",  # rightwards arrow
    "\u2026": "...", # ellipsis
}

COLOR = {
    "cyan": "\033[0;36m",
    "green": "\033[0;32m",
    "red": "\033[0;31m",
    "yellow": "\033[0;33m",
    "darkyellow": "\033[0;33m",
    "gray": "\033[0;90m",
    "white": "\033[0;37m",
    "reset": "\033[0m",
}
RULE_COLOR = {"R1": "yellow", "R2": "yellow", "R3": "red", "R4": "red", "R5": "darkyellow"}
_USE_COLOR = sys.stdout.isatty()


def paint(name: str, text: str) -> str:
    if not _USE_COLOR:
        return text
    return f"{COLOR[name]}{text}{COLOR['reset']}"


class Violation:
    __slots__ = ("file", "line", "rule", "message")

    def __init__(self, file: str, line: int, rule: str, message: str) -> None:
        self.file = file
        self.line = line
        self.rule = rule
        self.message = message


def _rel(file_path: str, root: str) -> str:
    try:
        return os.path.relpath(file_path, root).replace(os.sep, "/")
    except ValueError:
        return file_path


def _detect_line_ending(raw: bytes) -> str:
    if b"\r\n" in raw:
        return "\r\n"
    return "\n"


def _write_preserve_lf(file_path: str, text: str) -> None:
    # open(..., newline="") prevents \n -> os.linesep translation so -Fix
    # preserves LF on Windows/macOS. Unlike Path.write_text(data, newline=),
    # this open() form works on Python 3.8+ (newline was not added to
    # write_text until 3.10).
    with open(file_path, "w", encoding="utf-8", newline="") as handle:
        handle.write(text)


def _quote_description(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def _ascii_fix(line: str) -> str:
    for char, repl in ASCII_FIXES.items():
        if char in line:
            line = line.replace(char, repl)
    return line


def _description_ok(value: str) -> bool:
    """Rule 1 (agent files): accept any description form that is valid YAML.

    Accepts double-quoted, single-quoted, a valid block-scalar header (>/|),
    and safe plain scalars (the unquoted forms the generator emits). Rejects
    empty values and unquoted values containing YAML-significant characters
    that break parsing (colon-space, leading indicators, reserved words).
    Skill files ('.kilo/skills/*/SKILL.md') instead require a double-quoted
    description per the repository coding guidelines.
    """
    if not value:
        return False
    if QUOTED_RE.match(value) or SINGLE_QUOTED_RE.match(value):
        return True
    if BLOCK_SCALAR_RE.match(value):
        return True
    if SAFE_PLAIN_RE.match(value) and value.lower() not in RESERVED_WORDS:
        return True
    return False


def _check_file(file_path: str, root: str, is_agent: bool, fix: bool) -> tuple[list[Violation], str | None]:
    """Return (violations, new_text_if_fixed_else_None) for one file."""
    violations: list[Violation] = []
    rel = _rel(file_path, root)

    with open(file_path, "rb") as handle:
        raw = handle.read()

    # Rule 3: no BOM
    if len(raw) >= 3 and raw[0] == 0xEF and raw[1] == 0xBB and raw[2] == 0xBF:
        violations.append(Violation(rel, 1, "R3-no-bom",
                                   "File starts with UTF-8 BOM (EF BB BF). Remove the BOM."))

    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        violations.append(Violation(rel, 1, "R4-missing-frontmatter",
                                   "File is not valid UTF-8 and cannot be parsed."))
        return violations, None

    fm_match = FRONTMATTER_RE.match(text)
    if not fm_match:
        violations.append(Violation(rel, 1, "R4-missing-frontmatter",
                                   "No YAML frontmatter found (missing --- delimiters)."))
        return violations, None

    frontmatter = fm_match.group(1)
    fm_lines = re.split(r"\r?\n", frontmatter)
    fm_start = 1  # mirrors the PowerShell fmStart offset

    fixed_lines = list(fm_lines)
    was_fixed = False

    # Rule 2: ASCII-only frontmatter
    for i, line in enumerate(fm_lines):
        non_ascii = NON_ASCII_RE.findall(line)
        if non_ascii:
            chars = ", ".join(f"U+{ord(c):04X}" for c in non_ascii)
            violations.append(Violation(rel, fm_start + i, "R2-ascii-frontmatter",
                                        f"Non-ASCII characters in frontmatter: {chars}"))
            if fix:
                replaced = _ascii_fix(line)
                if replaced != line:
                    fixed_lines[i] = replaced
                    was_fixed = True

    # Rule 1: skill files must be double-quoted (repo guideline); agent files
    # accept any parse-safe scalar (matching the tree generator's output).
    desc_match = DESCRIPTION_RE.search(frontmatter)
    if desc_match:
        value = desc_match.group(1).strip()
        if is_agent:
            ok = _description_ok(value)
        else:
            ok = QUOTED_RE.match(value) is not None
        if not ok:
            line_num = len(frontmatter[:desc_match.start(1)].split("\n"))
            preview = value[:60]
            violations.append(Violation(rel, line_num, "R1-quoted-description",
                                        f"description value is not double-quoted: {preview}..."))
            if fix and is_agent and not BLOCK_SCALAR_RE.match(value):
                fm_index = _frontmatter_line_index(fm_lines, "description")
                if fm_index is not None:
                    fixed_lines[fm_index] = _quote_unquoted_line(fm_lines[fm_index])
                    was_fixed = True

    # Rule 4: required fields
    if not FIELD_DESC_RE.search(frontmatter):
        violations.append(Violation(rel, 2, "R4-required-field", "Missing required field: description"))
    if is_agent and not FIELD_MODE_RE.search(frontmatter):
        violations.append(Violation(rel, 2, "R4-required-field", "Missing required field: mode"))
    if not is_agent and not FIELD_NAME_RE.search(frontmatter):
        violations.append(Violation(rel, 2, "R4-required-field", "Missing required field: name"))

    # Rule 5: mojibake in body
    body_start = fm_match.end()
    if body_start < len(text):
        body = text[body_start:]
        body_lines = re.split(r"\r?\n", body)
        body_offset = len(text[:body_start].split("\n"))
        for i, line in enumerate(body_lines):
            if MOJIBAKE_RE.search(line):
                violations.append(Violation(rel, body_offset + i + 1, "R5-mojibake",
                                            "Mojibake detected (UTF-8/Windows-1252 round-trip artifact)."))

    new_text = None
    if fix and was_fixed:
        new_frontmatter = "\n".join(fixed_lines)
        body_text = text[fm_match.end():]
        eol = _detect_line_ending(raw)
        # Reconstruct without the stripped BOM; preserve detected line endings.
        rebuilt = f"---{eol}{new_frontmatter.replace(chr(13), '')}{eol}---{body_text}"
        if eol == "\r\n":
            rebuilt = rebuilt.replace("\r\n", "\n").replace("\n", "\r\n")
        if rebuilt != text:
            new_text = rebuilt

    return violations, new_text


def _frontmatter_line_index(fm_lines: list[str], key: str) -> int | None:
    prefix = f"{key}:"
    for i, line in enumerate(fm_lines):
        if line.lstrip().startswith(prefix):
            return i
    return None


def _quote_unquoted_line(line: str) -> str:
    idx = line.find(":")
    if idx == -1:
        return line
    key_part = line[: idx + 1]
    value_part = line[idx + 1:].strip()
    return f"{key_part} {_quote_description(value_part)}"


def _collect(root: str) -> tuple[list[str], list[str]]:
    agents = sorted(str(p) for p in Path(root, "agents").glob("*.md") if p.is_file())
    skills = sorted(str(p) for p in Path(root, "skills").rglob("SKILL.md") if p.is_file())
    return agents, skills


def _parse_args(argv: list[str]) -> tuple[str, bool]:
    path = ".kilo"
    fix = False
    i = 0
    while i < len(argv):
        arg = argv[i]
        low = arg.lower()
        if low in ("-path", "--path"):
            i += 1
            if i >= len(argv):
                print(paint("red", f"ERROR: Missing value after {arg}"), file=sys.stderr)
                sys.exit(1)
            path = argv[i]
        elif low.startswith("-path=") or low.startswith("/path="):
            path = arg.split("=", 1)[1]
        elif low in ("-fix", "--fix"):
            fix = True
        elif low.startswith("-fix=") or low.startswith("/fix="):
            val = arg.split("=", 1)[1].lower()
            fix = val in ("true", "1", "$true", "yes")
        else:
            print(paint("yellow", f"WARNING: Unrecognized argument {arg} -- ignoring"), file=sys.stderr)
        i += 1
    return path, fix


def main(argv: list[str] | None = None) -> int:
    path, fix = _parse_args(list(sys.argv[1:] if argv is None else argv))
    if not os.path.isdir(path):
        print(paint("red", f"ERROR: Path not found: {path}"), file=sys.stderr)
        return 1

    agents, skills = _collect(path)
    total = len(agents) + len(skills)
    if total == 0:
        print(paint("yellow", f"No agent or skill files found in {os.path.abspath(path)}"))
        return 0

    print(paint("cyan", f"Checking {total} files ({len(agents)} agents, {len(skills)} skills)..."))

    all_violations: list[Violation] = []
    for file_path in agents:
        violations, new_text = _check_file(file_path, path, is_agent=True, fix=fix)
        all_violations.extend(violations)
        if new_text is not None:
            _write_preserve_lf(file_path, new_text)
    for file_path in skills:
        violations, new_text = _check_file(file_path, path, is_agent=False, fix=fix)
        all_violations.extend(violations)
        if new_text is not None:
            _write_preserve_lf(file_path, new_text)

    if not all_violations:
        print(paint("green", f"All {total} files passed validation."))
        return 0

    print(paint("red", f"\nFound {len(all_violations)} violation(s):"))
    for v in all_violations:
        color = RULE_COLOR.get(v.rule[:2], "white")
        print(paint(color, f"  [{v.rule}] {v.file}:{v.line} - {v.message}"))

    summary: list[str] = []
    for rule in sorted({v.rule for v in all_violations}):
        count = sum(1 for v in all_violations if v.rule == rule)
        summary.append(f"{rule}: {count}")
    print(paint("cyan", f"\nSummary: {', '.join(summary)}"))
    return 1


if __name__ == "__main__":
    sys.exit(main())