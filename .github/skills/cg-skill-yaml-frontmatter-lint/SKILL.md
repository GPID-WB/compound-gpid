---
name: cg-skill-yaml-frontmatter-lint
description: "Validates YAML frontmatter in .kilo/agents/*.md and .kilo/skills/*/SKILL.md files. Checks: quoted descriptions, ASCII-only frontmatter, no BOM, valid YAML parse, required fields. Load when creating or editing agent/skill markdown files, or when Kilo reports 'Failed to parse agent' errors."
---

# YAML Frontmatter Lint for Agent & Skill Files

After the 2026-08-06 parsing failure incident (see `.cg-docs/solutions/bugs/2026-08-06-kilo-agent-skill-parsing-failures.md`),
all `.kilo/agents/*.md` and `.kilo/skills/*/SKILL.md` files must pass these checks.

## Validation Rules

### Rule 1: Quoted Descriptions (MANDATORY)

All `description:` values in YAML frontmatter MUST be double-quoted.

```yaml
# ✅ Correct
description: "Reviews code for quality and best practices."
# ❌ Wrong
description: Reviews code for quality and best practices.
```

**Why**: Unquoted values containing colons (`: `), brackets (`[]`), or other
YAML-significant characters cause silent parse failures. One failing file can
cascade — Kilo may report the entire directory as failed.

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
- `description` (required) — double-quoted string
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

Run the PowerShell validation script to check all agent and skill files:

```powershell
.skills/cg-skill-yaml-frontmatter-lint/Invoke-YamlLint.ps1
```

This checks all `.kilo/agents/*.md` and `.kilo/skills/*/SKILL.md` files against
Rules 1–5 and reports violations with file paths and line numbers.

### Options

- `-Path <dir>` — check a specific directory instead of the default `.kilo/`
- `-Fix` — automatically fix Rule 2 (ASCII frontmatter) and Rule 1 (quote
  unquoted descriptions). Other rules require manual fixes.

## When to Load This Skill

- **Creating** a new agent or skill file — validate before committing
- **Editing** an existing agent or skill file — validate after editing
- **"Failed to parse agent"** errors from Kilo — run the linter to find the cause
- **Pre-commit hook** — run `Invoke-YamlLint.ps1` before committing `.kilo/` changes

## Quick Manual Check

To quickly check if a single file's frontmatter parses:

```powershell
$content = Get-Content .kilo/agents/some-agent.md -Raw
$match = [regex]::Match($content, '(?s)^---\r?\n(.+?)\r?\n---')
if ($match.Success) {
    try {
        $yaml = ConvertFrom-Yaml $match.Groups[1].Value
        Write-Output "OK: $($yaml.description)"
    } catch {
        Write-Output "PARSE FAILED: $_"
    }
}
```