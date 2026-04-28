---
date: 2026-04-28
title: "Guard test passes vacuously when the checked variable includes a static member"
category: "testing-patterns"
language: "PowerShell"
tags: [pester, testing, guard-test, vacuous-pass, regex-extraction, refactoring, mixed-array, silent-failure]
root-cause: "Guard test checked the count of a mixed array (dynamic + static element) rather than the dynamic portion alone; the static element kept the count above zero even when extraction returned empty."
severity: "P1"
---

# Guard Test Passes Vacuously When the Checked Variable Includes a Static Member

## Problem

A Pester guard test was written to catch empty extraction from `link.ps1`:

```powershell
$managedDirs = $block -split '\r?\n' | ...  # extracted dynamically via regex
$entries = @($managedDirs | ForEach-Object { ".github/$_/" }) +
           @(".github/copilot-instructions.md")  # always present

It "extracted at least one entry from link.ps1 (guard against empty extraction)" {
    ($entries | Measure-Object).Count | Should BeGreaterThan 0
}
```

After a refactor that moved the literal array from `link.ps1` to `helpers.ps1`,
the regex no longer matched anything. `$managedDirs` was empty. `$entries`
collapsed to `@(".github/copilot-instructions.md")` — count = 1.

The guard passed. All three sync-validation tests built from `$entries` also
passed — vacuously, against a list containing only the hardcoded entry and
no managed-directory items. The protection the guard was designed to provide
was silently gone.

## Root Cause

The guard checked `$entries.Count` rather than `$managedDirs.Count`.
`$entries` was constructed as a **mixed array**: the dynamically extracted
part plus a hardcoded static element. Whenever extraction fails, the static
element keeps `Count ≥ 1`, so `Should BeGreaterThan 0` always passes.

The check was semantically wrong from the start — but was only exposed when
a refactor made the regex return empty rather than a populated list.

## Solution

**Rule**: Guard tests that validate extraction success must check the
**extracted variable**, never a downstream composite that includes static members.

Before fix:
```powershell
$entries = @($managedDirs | ForEach-Object { ".github/$_/" }) +
           @(".github/copilot-instructions.md")

It "extracted at least one entry (guard)" {
    ($entries | Measure-Object).Count | Should BeGreaterThan 0  # ❌ checks composite
}
```

After fix:
```powershell
$entries = @($managedDirs | ForEach-Object { ".github/$_/" }) +
           @(".github/copilot-instructions.md")

It "extracted at least one managed dir from helpers.ps1 (guard against empty extraction)" {
    ($managedDirs | Measure-Object).Count | Should BeGreaterThan 0  # ✅ checks extracted var
}
```

Additionally: after a constant is moved to a canonical source file, update
the extraction target too — the guard will now catch regressions:

```powershell
# Before: scraped from link.ps1 (had a literal array)
$block = [regex]::Match($linkContent, '(?s)\$ManagedDirs\s*=\s*@\((.+?)\)').Groups[1].Value

# After: scrape from helpers.ps1 (new canonical location)
$helpersContent = Get-Content (Join-Path $PSScriptRoot "..\scripts\helpers.ps1") -Raw
$block = [regex]::Match($helpersContent, '(?s)\$CG_MANAGED_DIRS\s*=\s*@\((.+?)\)').Groups[1].Value
```

## Prevention

1. **Never mix extracted and static elements in the same array before the guard check.**
   Build `$entries` after the guard, or keep the static element separate.

2. **When a constant moves to a new canonical location, immediately grep for
   tests that scrape the old location** — they will silently return empty rather
   than fail.

3. **Descriptor test names**: name the `It` block after what it is actually guarding:
   `"extracted at least one managed dir from helpers.ps1"` — not the composite
   `$entries` variable. The name doubles as documentation of what would break.

4. **Consider asserting an exact value** when the extracted list is stable:
   ```powershell
   $managedDirs.Count | Should Be 4  # fails if extraction returns empty OR adds unexpected entries
   ```

## Related

- [2026-04-22-schema-constant-coupling-value-equality-test-and-maintenance-anchor.md](2026-04-22-schema-constant-coupling-value-equality-test-and-maintenance-anchor.md) — related pattern: constants that exist in multiple files need value-equality tests to catch drift; presence-only tests are not sufficient
