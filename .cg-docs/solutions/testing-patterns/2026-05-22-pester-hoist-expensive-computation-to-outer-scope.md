---
date: 2026-05-22
title: "Hoist all expensive computation (regex, transforms) to outer scope — not just file reads"
category: "testing-patterns"
language: "both"
tags: [pester, performance, hoisting, regex, section-extraction, foreach-scope, context-scope, describe-scope, Get-Frontmatter, regex-match]
root-cause: "[regex]::Match() section-extraction and other computed values were assigned inside It blocks, repeating expensive computations once per test rather than once per Describe/foreach body. File-read hoisting was already established but the principle was not applied to derived computed values."
severity: "P2"
related: ".cg-docs/solutions/testing-patterns/2026-05-20-pester-hoist-file-reads-to-context-scope.md"
---

# Hoist All Expensive Computation to Outer Scope in Pester 4 Tests

## Problem

The 2026-05-20 solution established that `Get-Content`/`Get-Frontmatter` should be
hoisted to `Context`/`Describe` scope — not inside `It` blocks. However, the principle
was not applied to **derived values computed from the content**: `[regex]::Match()` section
extractions and similar string operations still appeared inside `It` blocks.

### Anti-pattern 1 — regex section extraction inside `It`

```powershell
Describe "cr-skill-publication-output - existence and content" {
    $path    = Join-Path $skillsDir "cr-skill-publication-output\SKILL.md"
    $content = Get-Content $path -Raw -Encoding UTF8
    $fm      = Get-Frontmatter -FilePath $path

    It "ggsave() criterion appears in figure-caption section (Section 5)" {
        # ❌ Regex runs fresh for every test execution
        $sec5Match = [regex]::Match($content, '(?si)## 5\..*?(?=## 6\.)')
        ($sec5Match.Value -match 'ggsave') | Should -Be $true
    }

    It "ggsave() criterion does NOT appear in table-note section (Section 6)" {
        # ❌ Regex runs again for every test execution
        $sec6Match = [regex]::Match($content, '(?si)## 6\..*?(?=## 7\.|$)')
        ($sec6Match.Value -match 'ggsave') | Should -Be $false
    }
}
```

### Anti-pattern 2 — `Get-Frontmatter` inside `foreach` `It` blocks

```powershell
foreach ($file in $promptFiles) {
    $filePath = $file.FullName

    It "$relPath has a model: frontmatter key" {
        # ❌ File read and parse inside It — deferred to test-execution time
        $frontmatter = Get-Frontmatter -FilePath $filePath
        ($frontmatter -cmatch '(?m)^\s*model:\s+\S+') | Should -Be $true
    }
}
```

### Anti-pattern 3 — `Get-Content` + line-split pipeline inside `It`

```powershell
foreach ($file in $allFiles) {
    It "$relPath has frontmatter delimiters" {
        # ❌ Read + split pipeline runs per test; no early exit
        $content = Get-Content $file.FullName -Raw -Encoding UTF8
        ($content -split '\r?\n' | Where-Object { $_ -match '^---\s*$' }).Count |
            Should -BeGreaterThan 1
    }
}
```

## Root Cause

The 2026-05-20 solution established the I/O hoisting rule for `Context` blocks but
two variants remained unaddressed:

1. **Computed/derived values** (regex extractions, string transforms) are also expensive
   and repeated if placed inside `It` blocks. The rule "only reads" was silently
   interpreted as excluding computed values.

2. **`foreach`-body scope** was not mentioned alongside `Context`/`Describe` scope.
   In Pester 4, the `foreach` body also runs at discovery time — variables assigned
   in the loop body (outside `It`) are visible to all `It` blocks in that iteration.

## Solution

### Fix 1 — Hoist `[regex]::Match()` to `Describe` scope

```powershell
Describe "cr-skill-publication-output - existence and content" {
    $path     = Join-Path $skillsDir "cr-skill-publication-output\SKILL.md"
    $content  = Get-Content $path -Raw -Encoding UTF8
    $fm       = Get-Frontmatter -FilePath $path
    # Pre-compute section text once at Describe scope (avoids re-scanning in each It)
    $sec5Text = [regex]::Match($content, '(?si)## 5\..*?(?=## 6\.)').Value
    $sec6Text = [regex]::Match($content, '(?si)## 6\..*?(?=## 7\.|$)').Value

    It "ggsave() criterion appears in figure-caption section (Section 5)" {
        ($sec5Text -match 'ggsave') | Should -Be $true
    }

    It "ggsave() criterion does NOT appear in table-note section (Section 6)" {
        ($sec6Text -match 'ggsave') | Should -Be $false
    }
}
```

Note: assign `.Value` at hoist time so `$sec5Text`/`$sec6Text` are plain strings,
not `Match` objects. This keeps `It` bodies simple.

### Fix 2 — Hoist `Get-Frontmatter` to `foreach` body with `if (Test-Path)` guard

```powershell
foreach ($file in $promptFiles) {
    $filePath    = $file.FullName
    $relPath     = $filePath.Replace($repoRoot + "\\", "")
    # ✅ Read once at loop/discovery scope; guard prevents exception on missing file
    $frontmatter = if (Test-Path $filePath) { Get-Frontmatter -FilePath $filePath } else { "" }

    It "$relPath exists" {
        Test-Path $filePath | Should -Be $true
    }

    It "$relPath has a model: frontmatter key" {
        ($frontmatter -cmatch '(?m)^\s*model:\s+\S+') | Should -Be $true
    }
}
```

The `if (Test-Path)` guard is critical: without it, a missing file throws at
discovery time (not test-execution time), producing a cryptic scope-level exception
instead of a clean failing `It "... exists"` test.

### Fix 3 — Replace line-split pipeline with a single `-match` on raw content

```powershell
foreach ($file in $allFiles) {
    $relPath    = $file.FullName.Replace($repoRoot + "\\", "")
    # ✅ Read once; raw content enables cheap single-pass regex
    $rawContent = if (Test-Path $file.FullName) { Get-Content $file.FullName -Raw -Encoding UTF8 } else { "" }

    It "$relPath has both opening and closing --- frontmatter delimiters" {
        # (?ms) matches opening --- ... closing --- across lines; no line-split needed
        ($rawContent -match '(?ms)^---\s*$.*?^---\s*$') | Should -Be $true
    }
}
```

The `(?ms)` flag makes `^`/`$` match line boundaries (`m`) and `.` cross newlines (`s`),
eliminating the `Where-Object` scan.

## Prevention

**Rule: Hoist ALL expensive operations to the outermost available scope.**

Scope hierarchy in Pester 4 (outermost first):
1. Script scope (before any `Describe`) — for values shared across all `Describe` blocks
2. `Describe`/`Context` body — for values shared across all `It` blocks in one Describe
3. `foreach` body — for values shared across all `It` blocks in one loop iteration
4. `It` body — for values that are genuinely per-test (the result being asserted)

**Expensive operations that must NOT appear in `It` bodies:**
- `Get-Content` / `Get-FileContent`
- `Get-Frontmatter`
- `[regex]::Match()` (or any regex with significant compiled cost)
- Multi-step string pipelines (`-split` + `Where-Object`)
- `ConvertFrom-Json` / `ConvertFrom-Yaml`

**Detection pattern** — find hoisting violations:
```powershell
# Find Get-Content inside It blocks
Select-String -Path tests/*.Tests.ps1 -Pattern '^\s+\$\w+\s*=\s*Get-Content' |
    Where-Object { $_.Line -notmatch '^\s*#' }
```

**Naming convention**: Always use `$fm` for frontmatter (not `$frontmatter`) — shorter,
consistent with the majority of tests in `cr-prompts.Tests.ps1`.

## Related

- `.cg-docs/solutions/testing-patterns/2026-05-20-pester-hoist-file-reads-to-context-scope.md` — original I/O hoisting rule for `Context` blocks (this solution extends it to computed values and `foreach`-body scope)
- `.cg-docs/solutions/testing-patterns/2026-04-07-pester-test-quality-patterns.md` — general Pester quality patterns
