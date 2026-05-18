---
date: 2026-05-18
title: "Regex extraction vacuous pass — Groups[1].Value returns empty string on no match"
category: "testing-patterns"
language: "both"
tags: [pester, regex, vacuous-pass, false-positive, drift-detection, parse-guard, -match, comparison-test]
root-cause: "[regex]::Match(...).Groups[1].Value returns empty string \"\" when the pattern does not match, not $null or an exception. A test that extracts two values and compares them ($a | Should -Be $b) passes vacuously when both return \"\" — providing zero real coverage."
severity: "P2"
test-written: true
fix-confirmed: true
---

# Regex Extraction Vacuous Pass — `Groups[1].Value` Returns Empty String on No Match

## Problem

A drift-detection test in `tests/wiki.Tests.ps1` extracted a folder value from
two files using `[regex]::Match(...).Groups[1].Value` and compared them with a
single `Should -Be` assertion:

```powershell
Describe "docs/_wiki.yml - folder matches compound-gpid.context.md declaration" {
    $ctxFile   = Join-Path $repoRoot "compound-gpid.context.md"
    $ymlFile   = Join-Path $repoRoot "docs\_wiki.yml"
    $ctx       = if (Test-Path $ctxFile) { Get-Content $ctxFile -Raw -Encoding UTF8 } else { "" }
    $yml       = if (Test-Path $ymlFile) { Get-Content $ymlFile -Raw -Encoding UTF8 } else { "" }
    $ctxFolder = [regex]::Match($ctx, '<!--\s*folder:\s*(\S+?)\s*-->').Groups[1].Value
    $ymlFolder = [regex]::Match($yml, '(?m)^folder:\s*"?([^"\s]+)"?').Groups[1].Value

    It "folder in _wiki.yml matches folder declared in compound-gpid.context.md" {
        $ymlFolder | Should -Be $ctxFolder   # ← vacuous pass if both extractions fail
    }
}
```

In the verify pass, `@cg-code-quality` and `@cg-testing` both independently
flagged this: if either source file is absent or either regex pattern does not
match, `.Groups[1].Value` returns `""` (not an exception, not `$null`). The test
then evaluates `"" | Should -Be ""` — green, zero coverage.

This is most dangerous exactly when it would matter most: if someone accidentally
removes the `<!-- folder: docs -->` directive from `compound-gpid.context.md`,
the test that was supposed to catch the drift passes silently.

## Root Cause

In .NET, `Regex.Match()` always succeeds — it never throws on no match. The
returned `Match` object has `Success = $false`, but `Groups[1].Value` is still
a valid (empty) string. PowerShell does not surface the failure; it just looks
like both files have an empty folder, which is vacuously equal.

This is distinct from three related patterns:

- **Alternation masking** (`A|B`): one branch always matches, hiding gaps in the
  other. (See `2026-05-01-regex-alternation-masks-coverage.md`)
- **Array parse guards** (`$dirs.Count | Should -BeGreaterThan 0`): catching
  empty arrays from failed collection steps. (See `2026-05-13-cross-script-parity-tests.md`)
- **Common-word false positives**: word appears in unrelated prose. (See
  `2026-05-15-common-word-regex-false-positive-in-security-assertions.md`)

The extraction-vacuous-pass is specifically about **comparison tests**: the test
computes a value A and value B and checks `A | Should -Be B`. If both come from
a regex extraction that can silently return `""`, the guard must be separate and
explicit.

## Solution

Add `Should -Not -BeNullOrEmpty` guards for each extracted value before the
comparison assertion:

```powershell
It "folder in _wiki.yml matches folder declared in compound-gpid.context.md" {
    $ctxFolder | Should -Not -BeNullOrEmpty   # guard: regex must have matched
    $ymlFolder | Should -Not -BeNullOrEmpty   # guard: regex must have matched
    $ymlFolder | Should -Be $ctxFolder
}
```

Now if the `<!-- folder: docs -->` directive is removed from `context.md`,
the test fails with:
```
Expected a value that is not null or empty, but got "".
```
— pointing directly to the real problem.

## Prevention

**Rule**: Whenever a `Describe` block extracts values via `[regex]::Match(...).Groups[n].Value`
and uses those values in `Should -Be` comparisons, add `Should -Not -BeNullOrEmpty`
guards before the comparison. One guard per extracted variable.

**General form**:
```powershell
$extracted = [regex]::Match($content, '(pattern)').Groups[1].Value
$extracted | Should -Not -BeNullOrEmpty   # guard: no match returns ""
$extracted | Should -Be $expectedValue
```

**Scope**: This applies to any extraction-then-compare pattern, including:
- `[regex]::Match(...).Groups[1].Value`
- `[regex]::Matches(...)[0].Groups[1].Value`
- `Select-String -Pattern '...' | ForEach-Object { $_.Matches[0].Groups[1].Value }`

**Does not apply**: Presence-only tests (`($content -match 'pattern') | Should -Be $true`)
do not need this guard — they test the regex match result directly.

## Related

- [`2026-05-01-regex-alternation-masks-coverage-split-into-independent-assertions.md`]
  — alternation masking in `-match` presence tests
- [`2026-05-13-cross-script-parity-tests-ps1-sh.md`]
  — array parse guards (`$dirs.Count | Should -BeGreaterThan 0`) for collection extractions
- [`2026-03-30-derived-invariant-validation-in-schema-tests.md`]
  — validating stored state against derived state (same class of comparison test)
- [`2026-05-15-common-word-regex-false-positive-in-security-assertions.md`]
  — related: overly broad regex patterns that always match
