---
date: 2026-05-18
title: "PS 5.1 Set-StrictMode crashes on bare $IsWindows access (variable not set)"
category: "bugs"
type: "bug"
language: "both"
tags: [powershell, ps51, strict-mode, IsWindows, automatic-variables, platform-detection, Test-Path, variable-provider, link, unlink]
root-cause: "$IsWindows is a PS 6+ automatic variable; under Set-StrictMode -Version Latest on PS 5.1 it is undefined, causing 'variable not set' VariableIsUndefined exception before -or short-circuit can save it"
severity: "P1"
test-written: "yes"
fix-confirmed: "yes"
---

# PS 5.1 `Set-StrictMode` Crashes on Bare `$IsWindows` Access

## Symptom

Running `cg-link` on a project using Windows PowerShell 5.1 produced:

```
The variable '$IsWindows' cannot be retrieved because it has not been set.
At C:\Users\wb384996\.compound-gpid\scripts\link.ps1:38 char:15
+ $onWindows = ($IsWindows -eq $true -or $env:OS -eq "Windows_NT")
+               ~~~~~~~~~~
    + CategoryInfo          : InvalidOperation: (IsWindows:String) [],
      ParentContainsErrorRecordException
    + FullyQualifiedErrorId : VariableIsUndefined
```

Same crash in `scripts/unlink.ps1`. The scripts are unusable on PS 5.1 despite
the `$env:OS -eq "Windows_NT"` fallback being present. `cg-unlink` fails identically.

## Root Cause

`$IsWindows` is a **PS 6+ (PowerShell Core) automatic variable**. It does not
exist in Windows PowerShell 5.1. The expression:

```powershell
$onWindows = ($IsWindows -eq $true -or $env:OS -eq "Windows_NT")
```

relies on `-or` short-circuit to skip the right operand when the left is `$true`.
But in PS 5.1, **`$IsWindows` is never defined at all** — it is not `$false` or
`$null`, it is simply absent. `Set-StrictMode -Version Latest` (set at the top
of both scripts) converts any access to an undefined variable into a hard
`VariableIsUndefined` exception, thrown *before* the `-or` short-circuit has
any chance to save execution.

The bug was introduced when cross-platform support added the `$env:OS` fallback
without accounting for the strict-mode interaction. The code was logically
correct under PS 6+, and the fallback was correct in intent, but the two were
incompatible on PS 5.1 strict mode.

## Reproduction Test

A scanner added to `tests/ps51-compat.Tests.ps1` walks all production scripts
and flags any line where `$IsWindows` (or `${IsWindows}`) appears in non-comment
code without a `Test-Path variable:IsWindows` guard on the same line. This test
failed before the fix and passes after:

```powershell
Describe "PS 5.1 compat - no bare IsWindows in production scripts" {
    foreach ($rel in $productionScripts) {
        $filePath = Join-Path $repoRoot $rel
        Context $rel {
            It 'does not access IsWindows without a Test-Path variable: guard' {
                $filePath | Should -Exist
                $lines = Get-Content -Path $filePath
                $violations = @()
                for ($i = 0; $i -lt $lines.Count; $i++) {
                    $line = $lines[$i]
                    if ($line -match '^\s*#') { continue }
                    # Strip trailing inline comment before matching the guard phrase.
                    # Limitation: does not handle '#' inside string literals.
                    $codePart = ($line -replace '#.*$', '').Trim()
                    # Detect both $IsWindows and ${IsWindows} (valid equivalent brace syntax)
                    if (($codePart -match '\$IsWindows|\$\{IsWindows\}') -and
                        $codePart -notmatch 'Test-Path\s+variable:IsWindows') {
                        $violations += "L$($i+1): $($line.Trim())"
                    }
                }
                $violations.Count | Should -Be 0
            }
        }
    }
}
```

Per-script regression guards were also added to `tests/link.Tests.ps1` and
`tests/unlink.Tests.ps1`.

## Fix

Use `Test-Path variable:IsWindows` to probe the PowerShell `Variable:` PSDrive
before accessing the variable. This is a cmdlet invocation with a string
argument — it never dereferences the variable and is safe under any strict mode:

```powershell
# Note: $IsWindows is PS6+ only; Test-Path guard is required for PS 5.1 strict mode.
$onWindows = (((Test-Path variable:IsWindows) -and $IsWindows) -or ($env:OS -eq "Windows_NT"))
```

Evaluation path on each runtime:

| Runtime | `Test-Path variable:IsWindows` | `$IsWindows` accessed? | `$env:OS` | `$onWindows` |
|---|---|---|---|---|
| PS 5.1 Windows | `$false` | No (short-circuit) | `"Windows_NT"` | `$true` |
| PS 7+ Windows | `$true` | Yes → `$true` | — | `$true` |
| PS 7+ macOS | `$true` | Yes → `$false` | `$null` | `$false` |
| PS 7+ Linux | `$true` | Yes → `$false` | `$null` | `$false` |

Key: `Test-Path variable:IsWindows` queries the `Variable:` provider with a
string literal — it does not read `$IsWindows`, so strict mode cannot throw.

Applied to `scripts/link.ps1` line 39 and `scripts/unlink.ps1` line 24.

## Lessons Learned

### Pattern to Follow (production scripts with `Set-StrictMode -Version Latest`)

```powershell
# Safe: probes Variable: provider without dereferencing $IsWindows
$onWindows = (((Test-Path variable:IsWindows) -and $IsWindows) -or ($env:OS -eq "Windows_NT"))
```

Use explicit inner parentheses to make operator precedence self-documenting
(`-and` binds tighter than `-or` by default, but parentheses prevent future
mis-grouping).

### Pattern for test files (no `Set-StrictMode`)

In test files where `Set-StrictMode` is never set, `$IsWindows` returns `$null`
on PS 5.1 rather than throwing. The bare form is safe here, but add a comment:

```powershell
# PS 5.1 compatible: no Set-StrictMode here, so $IsWindows returns $null rather than throwing.
# Production scripts MUST use the Test-Path guarded form.
$script:OnWindows = ($IsWindows -eq $true -or $env:OS -eq "Windows_NT")
```

### Anti-patterns to Avoid

| Anti-pattern | Why it breaks |
|---|---|
| `$IsWindows -eq $true` under `Set-StrictMode -Version Latest` | Throws `VariableIsUndefined` on PS 5.1 |
| `($IsWindows -or $env:OS -eq "Windows_NT")` | Same: `$IsWindows` is evaluated first before `-or` can short-circuit |
| `${IsWindows}` (brace form) | Same crash — `${IsWindows}` is syntactically equivalent to `$IsWindows` |
| `if ($null -eq $IsWindows) { ... }` | Also crashes: accessing `$IsWindows` in the condition throws first |

The only safe approaches are:
1. `Test-Path variable:IsWindows` (recommended — idiomatic)
2. `Get-Variable IsWindows -ErrorAction SilentlyContinue` (verbose alternative)
3. `$null -eq (Get-Variable IsWindows -ValueOnly -ErrorAction SilentlyContinue)` (more verbose)

### Compiler for Companion Variables

The same fix applies to `$IsLinux`, `$IsMacOS`, and `$IsCoreCLR` — all PS 6+
automatic variables. If any of these are used in a production script with
`Set-StrictMode`, apply the same guard:

```powershell
$onMacOS = ((Test-Path variable:IsMacOS) -and $IsMacOS)
$onLinux = ((Test-Path variable:IsLinux) -and $IsLinux)
```

## Related

- [`.cg-docs/solutions/bugs/2026-05-13-link-ps1-runs-on-macos-verification-fails.md`](2026-05-13-link-ps1-runs-on-macos-verification-fails.md) — introduced the `$onWindows` guard pattern (without the PS 5.1 strict-mode fix)
- [`.cg-docs/solutions/environment-issues/2026-05-13-join-path-backslash-not-cross-platform.md`](../environment-issues/2026-05-13-join-path-backslash-not-cross-platform.md) — cross-platform companion rule; code sample was updated to safe form
- [`.cg-docs/solutions/bugs/2026-04-17-ps51-get-content-default-encoding-breaks-equality-check.md`](2026-04-17-ps51-get-content-default-encoding-breaks-equality-check.md) — same PS 5.1 family; covers encoding-related strict-mode failures
- [`.cg-docs/solutions/bugs/2026-03-23-ps51-utf8-bom-em-dash-corrupts-ast-silently.md`](2026-03-23-ps51-utf8-bom-em-dash-corrupts-ast-silently.md) — PS 5.1 family; UTF-8 BOM/em-dash AST corruption
- [`.cg-docs/solutions/bugs/2026-03-30-ps51-convertfrom-json-single-element-array-coercion.md`](2026-03-30-ps51-convertfrom-json-single-element-array-coercion.md) — PS 5.1 family; JSON array coercion
