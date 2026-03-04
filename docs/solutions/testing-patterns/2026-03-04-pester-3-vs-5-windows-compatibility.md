---
date: 2026-03-04
title: "Pester 3.4 vs Pester 5 syntax — Windows built-in compatibility"
category: "testing-patterns"
language: "both"
tags: [powershell, pester, testing, windows, compatibility, pester3, pester5]
root-cause: "Windows ships with Pester 3.4.0; tests written with Pester 5 syntax fail silently or with confusing parse errors on any machine that has not explicitly upgraded Pester"
severity: "P2"
---

# Pester 3.4 vs Pester 5 Syntax — Windows Built-In Compatibility

## Problem

Tests were written using Pester 5 syntax and ran fine in CI but failed on team
Windows machines with errors such as:

```
A parameter cannot be found that matches parameter name 'Output'
BeforeAll is not valid in the current context
UnexpectedToken '-Be'
```

Root session example:

```powershell
# Pester 5 syntax — will NOT work on Windows built-in Pester 3.4
Invoke-Pester tests/ -Output Detailed          # -Output flag doesn't exist in 3
BeforeAll { $installDir = "..." }              # top-level BeforeAll: Pester 5 only
It "works" { $x | Should -Be $true }          # -Be switch: Pester 5 only
It "works" { $x | Should -Not -BeNullOrEmpty }
```

## Root Cause

Windows ships with **Pester 3.4.0** in `C:\Windows\System32\WindowsPowerShell\`.
Unless a team member explicitly runs `Install-Module Pester -Force -SkipPublisherCheck`,
they have 3.4.0. The module is signed by Microsoft and the built-in version takes
precedence unless imported explicitly.

Key breaking differences between the two versions:

| Pester 3.4 | Pester 5 |
|-----------|---------|
| `Should Be $value` | `Should -Be $value` |
| `Should Not Be $value` | `Should -Not -Be $value` |
| `Should BeNullOrEmpty` | `Should -BeNullOrEmpty` |
| `Should Not BeNullOrEmpty` | `Should -Not -BeNullOrEmpty` |
| `Should Match 'regex'` | `Should -Match 'regex'` |
| `BeforeAll` only inside `Describe` | `BeforeAll` anywhere (script scope) |
| No `-Output` param on `Invoke-Pester` | `-Output Detailed\|Minimal\|None` |

A further breaking issue: em dashes (`—`) in strings cause PowerShell 5.1 lexer
errors when the file is saved as UTF-8 without BOM and then read back. Avoid them.

## Solution

Write tests using Pester 3.4-compatible syntax. All tests will then work on both
3.4 and 5.x without changes:

```powershell
# Works on Pester 3.4 AND 5.x
Describe "my feature" {
    Context "happy path" {
        BeforeEach {
            # setup goes here, inside Describe
            $target = Join-Path $TestDrive "test-dir"
            New-Item -ItemType Directory -Path $target -Force | Out-Null
        }

        It "creates the directory" {
            Test-Path $target | Should Be $true
        }

        It "result is not null" {
            $result = Get-Something
            $result | Should Not BeNullOrEmpty
        }

        It "string matches pattern" {
            $value | Should Match '^prefix-[a-z]+'
        }
    }
}
```

Run tests:

```powershell
Invoke-Pester tests/              # Pester 3 — no flags needed
Invoke-Pester tests/ -Verbose     # equivalent of Detailed output in 3.x
```

Use `$TestDrive` for temp files — it is supported in both versions and is cleaned
up automatically after each test.

## Prevention

- **Write all new Pester tests using 3.4 syntax** (the table above) to ensure
  compatibility across the team without requiring an update step.
- If upgrading to Pester 5 is desired, make it an explicit, documented team
  decision and update `install.ps1` to install the new version.
- Add a Pester version comment at the top of each test file:
  ```powershell
  # Compatible with Pester 3.4+ (ships built-in on Windows)
  ```
- Avoid Unicode punctuation (em dashes, curly quotes) in `.ps1` files saved
  without BOM — they cause lexer errors.

## Related

- [Prompt file permission guardrails](2026-03-02-prompt-file-permission-guardrails.md) — another testing-patterns entry from this project
- Pester documentation: <https://pester.dev/docs/v3/quick-start> (v3 docs)
- Microsoft blog: [Pester 5 upgrade guide](https://pester.dev/docs/migrations/v3-to-v4)
