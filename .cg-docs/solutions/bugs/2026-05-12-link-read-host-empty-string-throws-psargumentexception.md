---
date: 2026-05-12
title: "Read-Host empty string throws PSArgumentException in cg-link bootstrap prompt"
category: "bugs"
type: "bug"
language: "PowerShell"
tags: [link, Read-Host, bootstrap, cg-index, PSArgumentException, interactive]
root-cause: "Read-Host does not accept an empty string as its -Prompt argument; PowerShell throws PSArgumentException: name cannot be null or empty"
severity: "P2"
test-written: "yes"
fix-confirmed: "yes"
---

# Read-Host empty string throws PSArgumentException in cg-link bootstrap prompt

## Symptom

Running `cg-link` in an interactive terminal completed the junction setup but then
crashed at the "Would you like to build the initial knowledge index now? (y/N)" prompt:

```
Would you like to build the initial knowledge index now? (y/N)
Read-Host : name cannot be null or empty.
At C:\WBG\.compound-gpid\scripts\link.ps1:281 char:25
+         $indexAnswer = (Read-Host "").Trim().ToLower()
+                         ~~~~~~~~~~~~
    + CategoryInfo          : InvalidArgument: (:) [Read-Host], PSArgumentException
    + FullyQualifiedErrorId : Argument,Microsoft.PowerShell.Commands.ReadHostCommand
```

The user could not answer the prompt because the error fired immediately, before any
input was possible.

## Root Cause

`Read-Host` does not accept an empty string `""` as its `-Prompt` parameter. PowerShell
treats the empty string as `$null` for this parameter and throws
`PSArgumentException: name cannot be null or empty`.

The intent was to read a bare keypress without printing a second prompt line (the
preceding `Write-Host` already displayed the question). The correct idiom is to call
`Read-Host` with **no argument**, which reads stdin silently.

## Reproduction Test

Added to `tests/link.Tests.ps1` — `Describe "link.ps1 - bootstrap index Read-Host prompt"`:

```powershell
It "Read-Host with empty string prompt throws PSArgumentException [reproduces bug]" {
    { Read-Host "" } | Should -Throw
}

It "link.ps1 bootstrap prompt does not use Read-Host with an empty string [regression guard]" {
    $content = Get-Content (Join-Path $PSScriptRoot "..\scripts\link.ps1") -Raw
    $content | Should -Not -Match 'Read-Host\s+""'
}
```

The regression-guard test fails on the buggy code and passes after the fix.

## Fix

**`scripts/link.ps1` line 281** — remove the empty string argument:

```powershell
# Before (buggy)
$indexAnswer = (Read-Host "").Trim().ToLower()

# After (fixed)
$indexAnswer = (Read-Host).Trim().ToLower()
```

The `Write-Host` on the preceding line already displays the question; `Read-Host` with
no argument reads the user's input without printing anything extra.

## Lessons Learned

- `Read-Host ""` is not a valid no-op. PowerShell validates the `-Prompt` parameter
  and rejects empty strings. Always use bare `Read-Host` (no argument) when you want
  to read input without a second prompt.
- When a `Write-Host` line immediately precedes a `Read-Host`, the pattern is:
  ```powershell
  Write-Host "Question text (y/N)" -ForegroundColor Cyan
  $answer = (Read-Host).Trim().ToLower()   # ← no argument
  ```
- Add a regression-guard test (`Should -Not -Match 'Read-Host\s+""'`) to any script
  that uses `Read-Host` to catch this class of bug at CI time.

## Related

- `.cg-docs/solutions/testing-patterns/2026-05-12-source-scanning-regression-guard-for-scripting-anti-patterns.md` — team-wide pattern for banning scripting anti-patterns via Pester source-scanning assertions
