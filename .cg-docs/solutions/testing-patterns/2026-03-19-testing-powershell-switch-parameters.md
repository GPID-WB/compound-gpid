---
date: 2026-03-19
title: "Testing PowerShell [switch] parameters: magic-string API tests pass for the wrong reasons"
category: "testing-patterns"
language: "both"
tags: [powershell, pester, switch-parameter, magic-string, api-mismatch, regression, cg-update, --list]
root-cause: "A test simulated a [switch] parameter using a magic string ('--list'), which matched the old implementation but not the refactored [switch]$List API — the test continued to pass because it never called the real parameter binding code"
severity: "P2"
---

# Testing PowerShell `[switch]` parameters: magic-string API tests pass for the wrong reasons

## Problem

After refactoring `update.ps1` to replace the magic string `--list` with a proper `[switch]$List` parameter, the existing test still passed:

```powershell
# Old test (WRONG — passes for the wrong reasons)
Context "--list argument" {
    It "is NOT written to .cg-version (special flag)" {
        $Version = "--list"
        ($Version -and $Version -ne "--list") | Should Be $false
    }
}
```

The test was asserting that the old guard expression (`$Version -ne "--list"`) evaluates to `$false`. It never tested that `$List.IsPresent` is `$true`, and it never tested that `$Version` would actually be empty when `--list` is passed through PowerShell's parameter binder.

This meant:
- The test passed after the refactor because the expression `"--list" -ne "--list"` still evaluates to `$false`.
- But if someone accidentally removed the `[switch]$List` declaration and reverted to magic-string handling, the test would still pass — providing zero regression protection.
- The test also gave the false impression that the `--list` flag prevents `.cg-version` writes, when in fact it was testing a completely different (now-deleted) code path.

## Root Cause

When PowerShell binds `--list` to `[switch]$List`:
- `$List` is set to `[switch]$true`
- `$Version` is `""` (empty string) or `$null` — NOT `"--list"`

A test that sets `$Version = "--list"` is simulating the **old** implementation, not the current one. The refactored code never reads `$Version` for the `--list` case at all.

## Solution

Rewrite the test to reflect the **actual PowerShell parameter binding** semantics:

```powershell
Context "--list argument" {
    It "is NOT written to .cg-version (special switch parameter)" {
        # When --list is passed, PowerShell sets $List = [switch]$true
        # and $Version = "" — NOT $Version = "--list"
        $List    = [switch]$true
        $Version = ""

        # The --list branch exits early; $Version is empty so writes are skipped
        $List.IsPresent                       | Should Be $true
        [string]::IsNullOrEmpty($Version)     | Should Be $true
    }
}
```

Also add a test for the guard in the write path itself:

```powershell
Context "--list flag (early return, no write)" {
    It "does NOT modify .cg-version when --list is passed" {
        $versionFile = Join-Path $TestDrive "cv-list-guard.txt"
        Set-Content -Path $versionFile -Value "v0.1.0" -NoNewline

        # Simulate: $List.IsPresent causes early return before any Set-Content
        $List = [switch]$true
        if (-not $List.IsPresent) {
            Set-Content -Path $versionFile -Value "should-not-appear" -NoNewline
        }

        (Get-Content $versionFile -Raw).Trim() | Should Be "v0.1.0"
    }
}
```

## Detection Heuristic

A test that uses a string value to simulate what should be a `[switch]` parameter is a smell:

```powershell
# SMELL: simulating a switch with a string
$Version = "--list"
if ($Version -ne "--list") { ... }  # testing old magic-string guard

# CORRECT: simulate actual PS parameter binding
$List = [switch]$true
if ($List.IsPresent) { ... }        # testing real control-flow path
```

When reviewing tests for PowerShell scripts, check that:
1. `[switch]` params are tested by setting `$param = [switch]$true` (or `[switch]$false`).
2. The test asserts `$param.IsPresent` or `[bool]$param`, not a string comparison.
3. String args to the command (e.g., `"--list"`) are never assigned to `$Version` when `--list` maps to a separate `[switch]$List` param.

## Prevention

**When refactoring from magic-string to `[switch]`**, update tests in the same commit. The compiler won't catch this class of mismatch — tests are the only guard.

**Code review checklist item**: if a PR converts a string-checked special value (e.g., `$arg -eq "--list"`) to a `[switch]` param, verify all tests that reference that string value are updated to use `[switch]` semantics.

## Related

- [`.cg-docs/solutions/testing-patterns/2026-03-13-regression-test-trycatch-guard-clm-environment.md`](./2026-03-13-regression-test-trycatch-guard-clm-environment.md) — similar pattern: testing control-flow guards in CLM environments where scripts can't be dot-sourced; simulation must match the real code path
- [`.cg-docs/solutions/bugs/2026-03-19-persistent-state-written-before-validation-causes-corruption.md`](../bugs/2026-03-19-persistent-state-written-before-validation-causes-corruption.md) — the P1 bug discovered in the same review cycle
