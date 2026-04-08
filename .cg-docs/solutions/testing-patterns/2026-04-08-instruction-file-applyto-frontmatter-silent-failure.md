---
date: 2026-04-08
title: "Test instruction file applyTo frontmatter to prevent silent dialect routing failure"
category: "testing-patterns"
language: "both"
tags: [powershell, pester, instruction-files, applyTo, frontmatter, dialect-routing, r-instructions, copilot, silent-failure]
root-cause: "r.instructions.md applyTo field had no test; a careless edit could silently break dialect routing for all .R files with no visible error"
severity: "P2"
---

# Test Instruction File `applyTo` Frontmatter to Prevent Silent Dialect Routing Failure

Surfaced as P2.4 during the 2026-04-08 R dialect skills postfix light review.

## Problem

`.github/instructions/r.instructions.md` contains an `applyTo:` field in its
YAML frontmatter that controls which file types automatically trigger the
instruction:

```yaml
---
applyTo: "**/*.R,**/*.r,**/*.Rmd"
---
```

If this field is accidentally deleted, misspelled, or set to the wrong pattern,
VS Code Copilot silently stops applying the R dialect router to `.R` files.
No error is raised. The agent simply never loads the dialect skill for R files.
From the user's perspective, "AI seems wrong about R style" — an ambiguous,
hard-to-diagnose symptom.

There was no test asserting:
- The `applyTo:` key exists
- It includes `**/*.R` (uppercase)
- It includes `**/*.r` (lowercase)
- It includes `**/*.Rmd`

Without tests, a single careless edit to the frontmatter silently breaks dialect
routing for the entire team.

## Root Cause

The `applyTo:` key in instruction file frontmatter is an invisible contract
between the file and the VS Code Copilot runtime. Unlike Python import errors or
missing function signatures, there is no runtime check — the instruction just
never fires. This class of silent failure requires explicit test coverage because
there is no other feedback mechanism.

Distinction from `tools:` in prompt files: prompt files use `tools:` to restrict
which tools an agent may call (see
`testing-patterns/2026-03-30-test-prompt-frontmatter-tools-list.md`).
Instruction files use `applyTo:` to declare which files they apply to. Both fail
silently when misconfigured, but they are different frontmatter keys in different
file types.

## Solution

Add `It` blocks to the existing `Describe "r.instructions.md"` block in
`tests/prompt-tools.Tests.ps1`:

```powershell
# P2.4: applyTo field presence — if this field is missing/wrong, dialect routing
# silently stops working for ALL .R files with no error.
It "has applyTo frontmatter field (required for auto-apply to .R files)" {
    ($content -match '(?m)^applyTo:') | Should Be $true
}

It "applyTo covers .R files" {
    ($content -match 'applyTo.*\*\*/\*\.R') | Should Be $true
}

It "applyTo covers .r files (lowercase)" {
    ($content -match 'applyTo.*\*\*/\*\.r') | Should Be $true
}

It "applyTo covers .Rmd files" {
    ($content -match 'applyTo.*\*\*/\*\.Rmd') | Should Be $true
}
```

Key regex notes:
- `(?m)^applyTo:` — multiline anchor ensures the key is at the start of a line
  (not inside a value)
- `applyTo.*\*\*/\*\.R` — checks the `applyTo` line contains the glob (uses
  `\*` to escape the literal asterisk inside the regex pattern)
- Test `.R` (uppercase) and `.r` (lowercase) separately — R on Windows is
  case-insensitive but other platforms are not, and both extensions are used in
  the wild

## Prevention

For every `.github/instructions/*.instructions.md` file added to the project:

1. **Add at least one test** in `tests/prompt-tools.Tests.ps1` asserting:
   - `applyTo:` key exists
   - The expected file extension patterns are present

2. **Template for new instruction file tests**:
   ```powershell
   Describe "<name>.instructions.md - applyTo validation" {
       $path = Join-Path $repoRoot ".github\instructions\<name>.instructions.md"
       $content = if (Test-Path $path) { Get-Content $path -Raw -Encoding UTF8 } else { "" }

       It "has applyTo frontmatter field" {
           ($content -match '(?m)^applyTo:') | Should Be $true
       }

       It "applyTo covers .<ext> files" {
           ($content -match 'applyTo.*\*\*/\*\.<ext>') | Should Be $true
       }
   }
   ```

3. **When adding a new extension** to `applyTo:` (e.g., `.qmd`), add a corresponding
   test case at the same time.

## Related

- [`testing-patterns/2026-03-30-test-prompt-frontmatter-tools-list.md`](./2026-03-30-test-prompt-frontmatter-tools-list.md) — same pattern of "silent failure from missing frontmatter key", but for `tools:` in `.prompt.md` files (different mechanism, different file type)
- [`testing-patterns/2026-04-07-pester-test-quality-patterns.md`](./2026-04-07-pester-test-quality-patterns.md) — general Pester quality patterns including anchored regex and shared helpers
- Review: `.cg-docs/reviews/2026-04-08-r-dialect-skills-postfix-light-review.md` (finding P2.4)
