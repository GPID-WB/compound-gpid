---
name: cg-skill-yaml-frontmatter-lint
description: "Validates YAML frontmatter in .kilo/agents/*.md and .kilo/skills/*/SKILL.md files. Checks: quoted descriptions, ASCII-only frontmatter, no BOM, valid YAML parse, required fields. Load when creating or editing agent/skill markdown files, or when Kilo reports 'Failed to parse agent' errors."
---

# YAML Frontmatter Lint for Agent & Skill Files

After the 2026-08-06 parsing failure incident (see `.cg-docs/solutions/bugs/2026-08-06-kilo-agent-skill-parsing-failures.md`),
all `.kilo/agents/*.md` and `.kilo/skills/*/SKILL.md` files must pass these checks.

## Validation Rules

### Rule 1: Parse-Safe Descriptions (MANDATORY)

A `description:` value must use a form that cannot silently misparse.

**Skill files** (`.kilo/skills/*/SKILL.md`) — the description MUST be a
double-quoted string, per the repository coding guidelines:

```yaml
# Required for skill files
description: "Reviews code for quality and best practices."
```

**Agent files** (`.kilo/agents/*.md`) — double-quoted is preferred; any
parse-safe scalar is accepted:

- double-quoted (`"..."`) -- required when the text contains a colon, `#`, or
  other YAML-significant characters
- single-quoted (`'...'`)
- a block scalar with a valid header (`>`, `|`, `>-`, `|+`, `>2-`, ...)
- a safe unquoted plain scalar: alphanumeric plus spaces, `.`, `/`, `-`, `_`;
  not a YAML reserved word (`true`/`false`/`null`/`yes`/`no`/`on`/`off`)

```yaml
# Agent: preferred
description: "Reviews code for quality and best practices."
# Agent: also valid (safe plain scalar, emitted by the tree generator)
description: Reviews code for quality and best practices
# WRONG (any file): colon-space, or a malformed block-scalar header, breaks parsing
description: Migration mode for /cg-fix-triage. Adds findings: tracking
description: >invalid
```

**Why**: An unquoted value containing a colon followed by a space makes YAML
treat the text after the colon as a new mapping key, silently corrupting or
failing the frontmatter -- this was the direct cause of the original
cg-skill-fix-triage-migrate parse failure. Skill files enforce double quotes
per the repository coding guidelines. Agent files accept any parse-safe scalar
because the platform-tree generator emits unquoted simple scalars for them; the
accepted set mirrors `cg_generate_targets._yaml_scalar`'s policy so generated
trees pass by construction and the linter never false-positives on valid
generated output.

### Rule 2: ASCII-Only Frontmatter (MANDATORY)

Frontmatter between `---` delimiters must contain only ASCII characters (U+0000–U+007F).

Forbidden in frontmatter:
- Em-dash `—` (U+2014) → use `--`
- En-dash `–` (U+2013) → use `-` or `--`
- Curly quotes `""` (U+201C/201D) → use straight `"`
- Arrow `→` (U+2192) → use `->`
- Any character above U+007F

### Rule 3: No BOM (MANDATORY)

Files must not start with a UTF-8 BOM (byte sequence `EF BB BF`). Kilo's YAML
parser may fail on BOM-prefixed files.

### Rule 4: Required Fields

**Agent files** (`.kilo/agents/*.md`):
- `description` (required) — double-quoted or parse-safe scalar (see Rule 1)
- `mode` (required) — one of `subagent`, `primary`, `all`

**Skill files** (`.kilo/skills/*/SKILL.md`):
- `name` (required) — must match the parent directory name
- `description` (required) — double-quoted string

### Rule 5: Body Content Encoding

Body content (after the closing `---`) should prefer ASCII where possible.
Known mojibake patterns to fix:

```
Mojibake bytes          ->  Intended character
C3 A2 E2 82 AC E2 80 9D ->  --  (was em-dash)
C3 A2 E2 80 A0 E2 80 99 ->  ->  (was arrow)
C3 A2 E2 82 AC E2 80 9C ->  -   (was en-dash)
C3 A2 E2 82 AC E2 84 A2 ->  '   (was curly apostrophe)
```

## Validation Script

The validator ships as a matched pair so it runs on every platform with no
extra install (macOS/Linux use the system shell; Windows uses built-in
PowerShell). Both entries run the same five rules and report identical results.

```bash
# macOS / Linux (bash; also works in Git Bash on Windows)
bash Invoke-YamlLint.sh
bash Invoke-YamlLint.sh -Path .kilo -Fix
```
```powershell
# Windows (PowerShell)
.\Invoke-YamlLint.ps1
.\Invoke-YamlLint.ps1 -Path .kilo -Fix
```

`Invoke-YamlLint.sh` runs `validate_yaml_frontmatter.py` (Python 3, stdlib
only; already a Compound GPID dependency on Unix). `Invoke-YamlLint.ps1` is a
self-contained native PowerShell implementation. Run from the repo root so the
default `-Path .kilo` resolves; it scans `.kilo/agents/*.md` and
`.kilo/skills/*/SKILL.md` and reports violations with file paths and line
numbers.

### Options

- `-Path <dir>` -- check a specific platform tree instead of the default `.kilo/`
- `-Fix` -- auto-fix Rule 1 (quote unsafe unquoted agent descriptions) and
  Rule 2 (replace non-ASCII frontmatter) via the Python validator
  (`validate_yaml_frontmatter.py`). The PowerShell entry is validation-only;
  passing `-Fix` there prints a notice and does not modify files.

## When to Load This Skill

- **Creating** a new agent or skill file — validate before committing
- **Editing** an existing agent or skill file — validate after editing
- **"Failed to parse agent"** errors from Kilo — run the linter to find the cause
- **Pre-commit hook** — run `bash Invoke-YamlLint.sh` (macOS/Linux) or
  `.\Invoke-YamlLint.ps1` (Windows) before committing `.kilo/` changes

## Quick Manual Check

To quickly check whether a single file's frontmatter is present and ASCII-clean
(portable, no modules required):

```bash
python3 - <<'PY'
import re, sys
c = open(sys.argv[1], encoding="utf-8-sig").read()
m = re.match(r"---\r?\n(.+?)\r?\n---", c, re.DOTALL)
print("OK" if m and not re.search(r"[^\x00-\x7f]", m.group(1)) else "CHECK")
PY
.kilo/agents/some-agent.md
```