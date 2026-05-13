---
date: 2026-05-12
title: "Source-scanning regression guard for PowerShell scripting anti-patterns"
category: "testing-patterns"
language: "PowerShell"
tags: [powershell, pester, regression-guard, source-scanning, Read-Host, anti-pattern, link]
root-cause: "Anti-patterns in .ps1 scripts can silently re-enter after a fix if there is no static assertion banning the pattern"
severity: "P2"
---

# Source-scanning regression guard for PowerShell scripting anti-patterns

## Problem

A scripting anti-pattern (`Read-Host ""`) was introduced during a feature addition to
`scripts/link.ps1`. The anti-pattern threw `PSArgumentException: name cannot be null or
empty` at runtime — preventing users from answering the interactive prompt entirely.

Because the pattern looked superficially correct (the intent was to read input without
printing a second prompt), it could easily re-enter on the next edit.

## Root Cause

There is no static check preventing `Read-Host ""` from appearing in the source.
Without a Pester assertion, the pattern can reappear after any refactor, copy-paste,
or AI-assisted edit that copies the wrong idiom.

The underlying PowerShell gotcha: `Read-Host` does not accept an empty string as its
`-Prompt` argument. It throws immediately, before any input is read.
The correct idiom for silent input (where the preceding `Write-Host` already shows the
question) is bare `Read-Host` with no argument.

## Solution

Write a **source-scanning regression guard**: a Pester test that opens the `.ps1` file
as raw text and asserts the anti-pattern is absent.

```powershell
# In tests/link.Tests.ps1
Describe "link.ps1 - bootstrap index Read-Host prompt" {
    Context "Read-Host empty-string argument is the root cause of the PSArgumentException" {
        It "Read-Host with empty string prompt throws PSArgumentException [reproduces bug]" {
            # Documents why the fix was needed — fails on the buggy code
            { Read-Host "" } | Should -Throw
        }

        It "link.ps1 bootstrap prompt does not use Read-Host with an empty string [regression guard]" {
            $content = Get-Content (Join-Path $PSScriptRoot "..\scripts\link.ps1") -Raw
            $content | Should -Not -Match 'Read-Host\s+""'
        }
    }
}
```

The first `It` block **demonstrates the crash** — it serves as executable documentation.
The second `It` block **bans the pattern** — it fails the moment the anti-pattern
reappears in source.

## Prevention

### General pattern: source-scanning guard

Whenever you fix a scripting anti-pattern that:
- looks plausible (easy to re-introduce),
- has no compiler/linter to catch it, and
- would cause a runtime failure,

add a source-scanning guard in the relevant test file:

```powershell
It "<script> does not use <anti-pattern> [regression guard]" {
    $content = Get-Content (Join-Path $PSScriptRoot "..\scripts\<script>.ps1") -Raw
    $content | Should -Not -Match '<regex-for-anti-pattern>'
}
```

### `Read-Host` idioms (PowerShell)

| Intent | Correct | Wrong |
|--------|---------|-------|
| Prompt with visible label | `Read-Host "Enter value"` | — |
| Silent read (prior `Write-Host` shows question) | `Read-Host` | `Read-Host ""` ❌ |
| Mask password | `Read-Host -AsSecureString "Password"` | — |

`Read-Host ""` (empty string) throws `PSArgumentException` immediately on PowerShell 5.1
and 7.x. It is not a no-op.

### Where to put source-scanning guards

Add the guard to the test file that already covers the modified script:

| Script | Test file |
|--------|-----------|
| `scripts/link.ps1` | `tests/link.Tests.ps1` |
| `scripts/update.ps1` | `tests/update.Tests.ps1` |
| `scripts/unlink.ps1` | `tests/unlink.Tests.ps1` |
| `scripts/helpers.ps1` | `tests/helpers.Tests.ps1` |

## Related

- `.cg-docs/solutions/bugs/2026-05-12-link-read-host-empty-string-throws-psargumentexception.md` — the bug this pattern was introduced to prevent from recurring
- `.cg-docs/solutions/bugs/2026-05-13-cg-link-bootstrap-index-offer-fails-on-empty-projects.md` — follow-up bug in the same bootstrap block; the source-scanning pattern was extended to assert the entire block is absent from both `link.ps1` and `link.sh`
- `.cg-docs/solutions/testing-patterns/2026-03-13-regression-test-trycatch-guard-clm-environment.md` — related source-simulation regression test pattern
