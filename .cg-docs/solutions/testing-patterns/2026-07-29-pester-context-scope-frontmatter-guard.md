---
date: 2026-07-29
title: "Guard Get-Frontmatter at Context scope to prevent silent test-block crashes"
category: "testing-patterns"
language: "PowerShell"
tags: [pester, frontmatter, context-scope, test-quality, agent-files, yaml]
root-cause: "Get-Content inside Get-Frontmatter throws a terminating error when the file is absent, crashing the entire Context block instead of cleanly failing the existence It"
severity: "P2"
---

# Guard Get-Frontmatter at Context Scope to Prevent Silent Test-Block Crashes

## Problem

In Pester 4 test files that loop over agent/prompt files and parse frontmatter
inside a `Context` block, `Get-Frontmatter` is often called before the
file-existence `It` assertion:

```powershell
Context "$name - existence and frontmatter" {
    $fm = Get-Frontmatter -FilePath $path   # ← crashes here if file absent

    It "[$name] exists" {
        Test-Path $path | Should -Be $true
    }
    It "[$name] has module: research" { ... }
}
```

If the file at `$path` is absent, `Get-Content` inside `Get-Frontmatter`
throws a **terminating exception at Context scope**. In Pester 4, a
Context-scope exception surfaces as a `RuntimeException` and causes all `It`
blocks in that Context to be skipped entirely — they never appear as failures
in the output. The existence check that should have caught the problem is
silently swallowed.

## Root Cause

Pester 4's test discovery model evaluates `Context` and `Describe` body code
at collection time. Code that throws at this level is not wrapped by any
`It`-level error handler, so it bypasses the normal failure reporting path.

## Solution

Wrap every `Get-Frontmatter` call at Context (or Describe) scope with a
`Test-Path` guard so the function is only called when the file exists:

```powershell
Context "$name - existence and frontmatter" {
    $fm = if (Test-Path $path) { Get-Frontmatter -FilePath $path } else { '' }

    It "[$name] exists" {
        Test-Path $path | Should -Be $true
    }
    It "[$name] has module: research" {
        ($fm -match '(?m)^\s*module:\s*research') | Should -Be $true
    }
}
```

With `$fm = ''`:
- `It "exists"` → fails cleanly via `Test-Path $false`
- All other `It` blocks receive `''` and fail with meaningful assertion failures
- No Context-scope crash; all test results are visible

**Note on false-passes**: A negative check like `($fm -notmatch 'write')` will
pass on an empty string. This is pre-existing behaviour identical to when the
old unguarded code reached those assertions on a valid empty file. If this is a
concern, add an explicit `(Test-Path $path) | Should -Be $true` guard inside
each negative `It` block.

## Prevention

- Always guard `Get-Frontmatter` (or any `Get-Content` call) at Context/Describe
  scope with `if (Test-Path $path) { ... } else { '' }`.
- The file-existence `It` block must remain — the guard is not a substitute for
  the existence assertion; it just prevents a crash before that assertion runs.
- Pattern already used in `helpers.ps1` skill files — see the `$fm = if (Test-Path
  $skillFile) { Get-Frontmatter ... } else { "" }` pattern in `model-assignments.Tests.ps1`.

## Related

- `2026-07-29-get-toolslist-over-tools-regex.md` — companion pattern for the
  tools assertion inside the same Context loop
- `model-assignments.Tests.ps1` — reference implementation of safe frontmatter
  reading pattern
