---
date: 2026-05-20
title: "Hoist Get-Content/Get-Frontmatter to Context scope — not inside It blocks"
category: "testing-patterns"
language: "both"
tags: [pester, performance, file-reads, context-scope, hoisting, test-organization, Get-Content, Get-Frontmatter]
root-cause: "Get-Content and Get-Frontmatter called once per It block instead of once per Context, causing N disk reads for N tests on the same file and scattering read logic throughout the test body."
severity: "P2"
---

# Hoist File Reads to Context Scope in Pester 4 Tests

## Problem

Tests for a single file repeated the file read inside every `It` block:

```powershell
It "loads cr-skill-research-workflow" {
    $content = Get-Content $path -Raw
    ($content -match 'cr-skill-research-workflow') | Should Be $true
}

It "contains P0 deferral policy" {
    $content = Get-Content $path -Raw
    ($content -match 'P0 deferral') | Should Be $true
}

It "has correct description in frontmatter" {
    $content = Get-Content $path -Raw
    $fm = Get-Frontmatter $content
    $fm.description | Should Not BeNullOrEmpty
}
```

A Context block with 10 `It` tests performs 10 file reads for the same file. In
`cr-prompts.Tests.ps1`, this anti-pattern appeared across 7–8 Context blocks — meaning
~70 redundant disk reads per test run.

## Root Cause

In Pester 4, `Context` blocks execute their body during discovery, so variables assigned
in the `Context` body (outside `It`/`BeforeAll`) are available to all `It` blocks within.
When tests are written inline without awareness of this scoping, `Get-Content` drifts into
every `It` block naturally — there's no compile-time error to catch it.

## Solution

Assign `$content` and `$fm` once at the top of the `Context` block:

```powershell
Context "cr-econometric-reasoning.agent.md" {
    $path    = "$agentsRoot/cr-econometric-reasoning.agent.md"
    $content = Get-Content $path -Raw      # read once
    $fm      = Get-Frontmatter $content    # parse once

    It "loads cr-skill-research-workflow" {
        ($content -match 'cr-skill-research-workflow') | Should Be $true
    }

    It "contains P0 deferral policy" {
        ($content -match 'P0 deferral') | Should Be $true
    }

    It "has correct description in frontmatter" {
        $fm.description | Should Not BeNullOrEmpty
    }
}
```

Both `$content` and `$fm` are hoisted together — they are always created as a pair.

## Prevention

- Every Pester `Context` block that tests a single file must read that file **exactly once**
  at the top of the Context block.
- `Get-Frontmatter` is always paired with `Get-Content` — hoist both in the same line group.
- Use this command to find the anti-pattern across test files:
  ```bash
  grep -n 'Get-Content\|Get-Frontmatter' tests/*.Tests.ps1 | grep -v '^\s*\$[a-z].*= Get'
  ```
  Any `Get-Content` or `Get-Frontmatter` call inside an `It { }` block is a hoist candidate.
- When reviewing a new test file, scan the `It` blocks first and move all file reads up.

## Related

- `tests/cr-prompts.Tests.ps1` — hoisting applied to CR prompts and agents loops (2026-05-20)
- `.cg-docs/solutions/testing-patterns/2026-04-28-prompt-guard-conditions-need-immediate-pester-coverage.md`
- `.cg-docs/solutions/testing-patterns/2026-05-22-pester-hoist-expensive-computation-to-outer-scope.md` — extends this rule to computed values (`[regex]::Match()`) and `foreach`-body scope
