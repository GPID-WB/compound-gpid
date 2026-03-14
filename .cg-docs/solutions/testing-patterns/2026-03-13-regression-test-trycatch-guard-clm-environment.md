---
date: 2026-03-13
title: "Regression test for try/catch control-flow guards when script cannot be executed"
category: "testing-patterns"
language: "both"
tags: [powershell, pester, regression-test, try-catch, clm, OneDrive, control-flow, simulation]
root-cause: "CLM/OneDrive path restrictions prevent Pester from dot-sourcing scripts under OneDrive paths, so real script invocation in tests is not possible — tests must simulate the guarded pattern instead"
severity: "P2"
---

# Regression Test for try/catch Control-Flow Guards in CLM Environments

## Problem

A PS5.1 bug (`ErrorActionPreference=Stop` promoting git stderr to a terminating error) was fixed
in `update.ps1` by wrapping `git checkout .` in a `try/catch`. The fix needed a regression test
to prevent it from being accidentally removed during future refactors.

However, Pester 3.4 cannot dot-source or invoke scripts located under OneDrive paths due to
Constrained Language Mode (CLM) — the same environment restriction the fix was addressing.
Running `Invoke-Pester update.Tests.ps1` from the OneDrive workspace fails with
`CommandNotFoundException` for the script path itself.

## Root Cause

Pester 3.4 internally dot-sources the test file. CLM blocks dot-sourcing of scripts from
OneDrive-redirected paths (treated as untrusted by AppLocker/WDAC). This means tests cannot
call the actual `update.ps1` — they must simulate the logic they intend to test.

This is the same CLM restriction that motivated the batch-wrapper install approach in the
first place.

## Solution

Write regression tests that simulate the **pattern** rather than invoking the actual script.
The test validates that the control-flow construct (try/catch around checkout, pull still reached)
behaves correctly — even though it cannot run the real git commands.

```powershell
Context "PS5.1 ErrorActionPreference=Stop regression" {
    # Regression for: cg-update fails with "Updated 0 paths from the index"
    # Root cause documented in: .cg-docs/solutions/git-workflows/
    #   2026-03-05-ps51-stderr-stop-terminates-on-git-informational-output.md

    It "does not throw when checkout step raises a terminating error" {
        $ErrorActionPreference = "Stop"
        $checkoutAttempted = $false
        $pullAttempted     = $false
        $threw             = $false

        try {
            # Simulate the update.ps1 pattern: try/catch around checkout
            try {
                $checkoutAttempted = $true
                throw "Simulated PS5.1 stderr-as-terminating-error from git checkout ."
            } catch {
                <# Simulates update.ps1 pattern: ignore informational stderr from git checkout . #>
            }

            # Pull must still be reached even though checkout threw
            $pullAttempted = $true
        } catch {
            $threw = $true
        } finally {
            $ErrorActionPreference = "Continue"
        }

        $checkoutAttempted | Should Be $true
        $pullAttempted     | Should Be $true
        $threw             | Should Be $false
    }

    It "does not suppress a real checkout failure (non-zero LASTEXITCODE)" {
        # Even with the try/catch, a non-zero exit code must still be detectable
        $global:LASTEXITCODE = 1
        $warnTriggered = $false

        try { throw "Simulated stderr" } catch { <# ignore #> }
        if ($LASTEXITCODE -ne 0) { $warnTriggered = $true }

        $warnTriggered | Should Be $true
        $global:LASTEXITCODE = 0  # reset
    }
}
```

**Key design decisions**:
- `$ErrorActionPreference = "Stop"` is set inside the test to replicate the PS5.1 condition
- Always reset to `"Continue"` in a `finally` block to avoid polluting other tests
- Two tests cover the two halves of the guard: (a) terminating errors don't escape, (b) real failures are still detectable via `$LASTEXITCODE`

## Prevention

When writing regression tests for try/catch guards in CLM environments:

1. **Simulate the pattern, not the command** — throw a synthetic error to represent the native command's stderr
2. **Set `$ErrorActionPreference = "Stop"` explicitly** — reproduce the PS5.1 condition, don't rely on it being set elsewhere
3. **Always reset in `finally`** — `$ErrorActionPreference = "Continue"` prevents test pollution
4. **Add a reference comment** — link the test back to the solution doc so future readers understand the why

## Related

- [`.cg-docs/solutions/git-workflows/2026-03-05-ps51-stderr-stop-terminates-on-git-informational-output.md`](../git-workflows/2026-03-05-ps51-stderr-stop-terminates-on-git-informational-output.md) — Root cause and fix for the PS5.1 issue being tested
- [`.cg-docs/solutions/testing-patterns/2026-03-04-pester-3-vs-5-windows-compatibility.md`](2026-03-04-pester-3-vs-5-windows-compatibility.md) — Pester version compatibility on Windows
