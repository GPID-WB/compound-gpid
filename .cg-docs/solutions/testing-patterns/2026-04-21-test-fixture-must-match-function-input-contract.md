---
date: 2026-04-21
title: "Test fixtures must match function input contract, not full document format"
category: "testing-patterns"
language: "both"
tags: [powershell, pester, fixtures, input-contract, yaml, frontmatter, get-toolslist, false-positive]
root-cause: "Test fixtures that include delimiters/wrappers not expected by the function under test produce false-positive passes — tests appear to verify behavior but actually test the function's tolerance of unexpected input"
severity: "P2"
---

# Test Fixtures Must Match Function Input Contract, Not Full Document Format

## Problem

`Get-ToolsList` in `tests/helpers.ps1` accepts an extracted frontmatter
**body** — the inner content between `---` delimiters, as returned by
`Get-Frontmatter`. The edge-case tests in `tests/helpers.Tests.ps1` were
passing full YAML blocks including delimiters:

```powershell
# WRONG — includes --- delimiters not expected by Get-ToolsList
$fm = "---`nplan: null`ndate: 2026-01-01`n---"
$result = Get-ToolsList -Frontmatter $fm
@($result).Count | Should Be 0
```

The test passed — but only because `---` does not match `^\s*tools:`, not
because the function correctly handled frontmatter body input. The fixture was
testing the function's tolerance of unexpected delimiters, not its core logic.

## Root Cause

Tests were written with a "full document example" mental model rather than
the function's actual input contract. `Get-Frontmatter` is the document parser
that strips delimiters; `Get-ToolsList` is a post-parse helper that operates
on the extracted body. Passing a full document to `Get-ToolsList` was a layer
violation that happened to produce the right output by coincidence.

## Solution

Strip delimiters from fixture strings so they represent the extracted body:

```powershell
# CORRECT — extracted body, no delimiters
$fm = "plan: null`ndate: 2026-01-01"
$result = Get-ToolsList -Frontmatter $fm
@($result).Count | Should Be 0

# CORRECT — extracted body, no delimiters
$fm = "tools: ['agent', 'read', 'write']"
$result = Get-ToolsList -Frontmatter $fm
($result -contains 'agent') | Should Be $true
```

## Prevention

- **Rule**: Before writing fixtures for a helper function, read the function
  signature and check what format its callers (e.g., `Get-Frontmatter`) produce.
  Match the fixture format to the function's actual input contract, not to the
  "full file" format.
- **Code comment**: Add a comment at the function definition indicating its
  expected input format:
  ```powershell
  # Accepts: frontmatter BODY (inner content between --- delimiters).
  # Use Get-Frontmatter to extract the body before calling this.
  function Get-ToolsList { ... }
  ```

## Related

- [2026-04-21-where-object-returns-array-coercion-trap.md](./2026-04-21-where-object-returns-array-coercion-trap.md) — the coercion bug that fixtures with delimiters partially masked
- [2026-04-07-pester-test-quality-patterns.md](./2026-04-07-pester-test-quality-patterns.md) — general Pester quality patterns
