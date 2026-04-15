---
date: 2026-04-07
title: "Four Pester test quality patterns: shared helpers, anchored regex, non-empty value checks, and named-criteria guards"
category: "testing-patterns"
language: "both"
tags: [powershell, pester, helpers, dot-source, dry, regex, frontmatter, named-criteria, prompt-testing]
root-cause: "Four independent quality issues found in model-audit Pester tests: duplicated helper function, over-broad regex matching, missing value validation for frontmatter keys, and missing guards for named prompt criteria"
severity: "P2"
---

# Four Pester Test Quality Patterns

Surfaced during the 2026-04-07 model-audit light review (P1.1, P2.1, P3.1–P3.4).
All four patterns apply broadly to any Pester test suite that validates YAML
frontmatter or Markdown prompt files.

---

## Pattern 1 — Shared helper via dot-source (P2.1)

### Problem

Both `tests/prompt-tools.Tests.ps1` and `tests/model-assignments.Tests.ps1` defined
an identical 7-line `Get-Frontmatter` helper. A future change to frontmatter parsing
(e.g., supporting multi-line values or different delimiter styles) required editing
two files.

```powershell
# ❌ Duplicated in both test files
function Get-Frontmatter {
    param([string]$FilePath)
    $raw = Get-Content $FilePath -Raw -Encoding UTF8
    if ($raw -match '(?s)^---\s*\r?\n(.+?)\r?\n---') { return $Matches[1] }
    return ''
}
```

### Solution

Extract to `tests/helpers.ps1` and dot-source at the top of each test file.

```powershell
# tests/helpers.ps1
function Get-Frontmatter {
    param([string]$FilePath)
    $raw = Get-Content $FilePath -Raw -Encoding UTF8
    if ($raw -match '(?s)^---\s*\r?\n(.+?)\r?\n---') { return $Matches[1] }
    return ''
}
```

```powershell
# At the top of each test file (after $repoRoot assignment)
. "$PSScriptRoot/helpers.ps1"
```

### Prevention

- Create `tests/helpers.ps1` at the start of any project with more than one Pester
  file that reads the same file types.
- Any function used in two or more test files belongs in `helpers.ps1`.
- `$PSScriptRoot` is always correct in Pester 3.4; never hardcode the path.

---

## Pattern 2 — Anchor sync-table regex to file extension (P3.2)

### Problem

Stem-based sync tests — verifying that a guide document references every prompt/agent
file by name — matched the stem anywhere in the document, including prose sentences:

```powershell
# ❌ Matches "use cg-review to inspect..." even if the table row was deleted
($content -match [regex]::Escape($stem)) | Should Be $true
```

A stem like `cg-review` would match the sentence "run `/cg-review` to apply" even
if the reference table entry had been removed.

### Solution

Anchor the search to the file extension so the pattern only matches a real file
reference:

```powershell
# ✅ Only matches "cg-review.prompt.md" or "cg-review.agent.md" in the table
($content -match ([regex]::Escape($stem) + '\.prompt\.md')) | Should Be $true
($content -match ([regex]::Escape($stem) + '\.agent\.md'))  | Should Be $true
```

### Prevention

Whenever writing a test that asserts "this document references file X by stem":
- Always anchor to the full filename (stem + extension).
- Prose mentions of a command (e.g., `` `/cg-review` ``) use the slash prefix, not
  the `.prompt.md` extension — so extension-anchored patterns avoid false positives
  from prose.

---

## Pattern 3 — Check non-empty frontmatter values, not just key presence (P3.3)

### Problem

A test that checks only key presence passes when the value is empty or a placeholder:

```powershell
# ❌ Passes for "model: " (empty) or "model: TODO"
($frontmatter -cmatch '(?m)^\s*model:') | Should Be $true
```

### Solution

Require at least one non-whitespace character after the colon:

```powershell
# ✅ Fails for empty value or placeholder like "TODO"
($frontmatter -cmatch '(?m)^\s*model:\s+\S+') | Should Be $true
```

The `\s+` requires at least one whitespace separator, and `\S+` requires at least
one non-whitespace character in the value. This catches `model: ` (trailing space
only), `model:` (no value), and any single-token placeholder.

### Prevention

Apply this pattern to any required frontmatter key where a blank or placeholder
value would be as wrong as a missing key. Common cases in this project:
`model:`, `description:`, `title:`, `date:`.

---

## Pattern 4 — Named criteria guards in prompt quality tests (P1.1)

### Problem

A Pester test block for a Step 2.5 quality check asserted the **section existed**
but not that the **named criteria** it defined were still present:

```powershell
# ❌ Doesn't catch if "Presence", "Context", or "Volume" headings were renamed
It "includes a Step 2.5 subagent output quality check" {
    ($content -match 'Subagent Output Quality Check') | Should Be $true
}
```

If an editor changed `**Presence**: Contains…` to `**Has findings**: Contains…`,
the section header test still passed, but downstream automation relying on the
criteria names would silently break.

### Solution

Add one `It` block per named criterion:

```powershell
It "documents the Presence criterion by name" {
    ($content -match '\bPresence\b') | Should Be $true
}
It "documents the Context criterion by name" {
    ($content -match '\bContext\b') | Should Be $true
}
It "documents the Volume criterion by name" {
    ($content -match '\bVolume\b') | Should Be $true
}
```

### Prevention

For any prompt that defines an **enumerated list of named criteria** (quality gates,
checklist items, acceptance criteria), add one test per name. Section-level tests
guard structure; criterion-level tests guard terms that downstream code or prompts
may depend on by name.

---

## Bonus: Remove duplicate Describe blocks (P3.1)

If two `Describe` blocks exercise identical files with identical assertions (same
file list, same `It` text, same `Test-Path` body), remove one. Pester does not
deduplicate: both run, both can fail, and two failure messages for the same root
cause double the noise.

In `tests/prompt-tools.Tests.ps1`, `"cg-skill-r-testing - skill file structure"`
and `"cg-skill-r-testing - file structure"` tested the same 6 files. The second
block was removed.

---

## Related

- [prompt-pipeline contract testing](./2026-03-30-prompt-pipeline-contract-testing.md) — the upstream pattern for testing named prompt interfaces
- [Pester 3.4 vs 5 compatibility](./2026-03-04-pester-3-vs-5-windows-compatibility.md) — syntax constraints that apply to all of the above
- [Invoke-Pester full suite + PassThru crashes VS Code](./2026-04-02-invoke-pester-full-suite-passthru-crashes-vscode.md) — safe run patterns
- [2026-04-15-pester-dotall-flag-required-for-multiline-regex.md](./2026-04-15-pester-dotall-flag-required-for-multiline-regex.md) — `(?s)` required when matching text that spans a line break in `Get-Content -Raw` output
- [2026-04-15-new-validation-branch-requires-dedicated-test.md](./2026-04-15-new-validation-branch-requires-dedicated-test.md) — each new conditional path in a validation function requires a dedicated `It` block
