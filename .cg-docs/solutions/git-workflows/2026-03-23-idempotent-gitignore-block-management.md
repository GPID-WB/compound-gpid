---
date: 2026-03-23
title: "Idempotent .gitignore block management with remove-then-rewrite"
category: "git-workflows"
language: "PowerShell"
tags: [gitignore, idempotent, block-management, powershell, regex, vendor-section]
root-cause: "Naive append-if-missing leaves orphaned entries when the managed block evolves across versions"
severity: "P2"
---

# Idempotent .gitignore Block Management

## Problem

A tool (Compound GPID's `cg-link`) maintains a named section in the project's
`.gitignore`. When the set of managed entries changes between versions (e.g. an
entry is renamed or removed), a simple "append if the header is absent" approach
leaves orphaned lines from the old block in the file.

Symptoms:
- Running `cg-link` multiple times produces duplicate sections.
- After a version upgrade that renames an entry, the old entry stays in
  `.gitignore` and keeps blocking commits of a file the user now wants tracked.
- The file grows unboundedly on repeated tool invocations.

## Root Cause

Append-if-missing checks only for the section header (`# Compound GPID managed
items`). If the header is present it does nothing. If the header is absent it
appends. Neither branch handles the case where the body of the block has changed.

## Solution

Use a **remove-then-rewrite** strategy: unconditionally strip any existing block
matching the header, then append the canonical block.

```powershell
# Define the section to manage
$cgGitignoreMarker  = "# Compound GPID managed items (junctions + copied file - do not commit)"
$cgGitignoreEntries = @(
    ".github/prompts/",
    ".github/skills/",
    ".github/agents/",
    ".github/instructions/",
    ".github/copilot-instructions.md"
)
$cgGitignoreBlock = $cgGitignoreMarker + "`n" + ($cgGitignoreEntries -join "`n") + "`n"

if (Test-Path $gitignorePath) {
    $giContent = Get-Content $gitignorePath -Raw -ErrorAction SilentlyContinue
    if (-not $giContent) { $giContent = "" }

    # Normalize: ensure trailing newline so the regex anchors correctly even
    # when a text editor has stripped the final line ending.
    if ($giContent -and $giContent -notmatch '\r?\n$') { $giContent = $giContent + "`n" }

    # Remove any existing CG block before rewriting.
    # Pattern greedily consumes the header line + all following non-empty body lines.
    # This handles renamed/removed entries without leaving orphans.
    $giUpdated = ($giContent -replace "(?m)^# Compound GPID managed items.*\r?\n([^\r\n]+\r?\n)*", "").TrimEnd()

    # Separate from existing content with a blank line, or write clean if the
    # file was empty (or the block was the entire file).
    $separator = if ($giUpdated.Length -gt 0) { "`n`n" } else { "" }
    Set-Content -Path $gitignorePath -Value ($giUpdated + $separator + $cgGitignoreBlock)
} else {
    Set-Content -Path $gitignorePath -Value $cgGitignoreBlock
}
```

### Regex anatomy

```
(?m)^# Compound GPID managed items.*\r?\n([^\r\n]+\r?\n)*
```

| Part | Meaning |
|------|---------|
| `(?m)` | Multiline mode — `^` matches start of each line |
| `^# Compound GPID managed items.*\r?\n` | Matches the header line (any suffix) + its line ending |
| `([^\r\n]+\r?\n)*` | Matches zero or more non-empty body lines — stops at the first blank line or EOF |

The pattern does **not** require body lines to start with a specific prefix (e.g.
`.github/`), so entries like `.cg-docs/` from older versions are also removed.

## Prevention

- Always use remove-then-rewrite for vendor-managed `.gitignore` sections.
- The managed block should end at the first blank line — never put a blank line
  inside the block, or the regex will stop early and leave a tail.
- Keep a distinctive, version-stable header string. Changing the header string
  between releases will cause the old block to survive, defeating the pattern.
- Test with: (a) fresh file (no block), (b) block present with matching entries,
  (c) block present with stale/extra entries, (d) block is the only content.

## Separate concern: removing a stale entry type

When a previously managed item (e.g. `.cg-docs/`) needs to be permanently
*un-ignored*, it is not enough to remove it from `$cgGitignoreEntries`. If users
ran older versions of the tool, that entry may live in a *different* block with a
*different* header comment. Handle it explicitly:

```powershell
if ($giAfterCg -match '(?i)# Compound GPID knowledge base') {
    $giCleaned = $giAfterCg -replace '(?m)^# Compound GPID knowledge base[^\r\n]*\r?\n\.cg-docs/\r?\n?', ''
    Set-Content -Path $gitignorePath -Value ($giCleaned.TrimEnd() + "`n")
    Write-Host "  Removed stale .cg-docs/ entry from .gitignore" -ForegroundColor DarkGray
}
```

## Related

- [2026-03-23-cg-docs-must-not-be-gitignored.md](2026-03-23-cg-docs-must-not-be-gitignored.md) — the triggering requirement that `.cg-docs/` must be committed, not ignored
- `scripts/link.ps1` — full implementation (Step 5 and Step 5b)
