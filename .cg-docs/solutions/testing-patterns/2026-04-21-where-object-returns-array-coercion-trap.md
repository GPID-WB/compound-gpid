---
date: 2026-04-21
title: "Where-Object returns PSObject[] — regex on array coerces to space-joined string"
category: "testing-patterns"
language: "both"
tags: [powershell, pester, where-object, array, coercion, regex, select-object, get-toolslist]
root-cause: "Where-Object always returns a PSObject[] even when only one line matches; calling .NET Matches() on an array triggers implicit ToString() which joins elements with spaces, producing garbled tokens"
severity: "P2"
---

# `Where-Object` Returns `PSObject[]` — Regex on Array Coerces to Space-Joined String

## Problem

`Get-ToolsList` in `tests/helpers.ps1` extracted the `tools:` line from a
frontmatter string and passed it directly to `[regex]::Matches()`:

```powershell
$line = ($Frontmatter -split '\r?\n' | Where-Object { $_ -match '^\s*tools:' })
$tokens = [regex]::Matches($line, "['""](\w+)['""]") | ForEach-Object { $_.Groups[1].Value }
```

When the frontmatter contained two `tools:` keys (e.g., malformed YAML),
`$line` was a `PSObject[]` with two elements. `.NET`'s `[regex]::Matches()`
expects a `[string]`; when given an array it calls `.ToString()`, which joins
elements with spaces:

```
"tools: ['agent']  tools: ['read','write']"
```

The regex then matched across the merged string, returning incorrect merged
tokens rather than raising an error.

## Root Cause

`Where-Object` in PowerShell always returns a collection (`PSObject[]`), even
when exactly one element matches. Scalar coercion only happens when the result
is assigned to a typed `[string]` variable — which does not occur with `var =
(pipeline | Where-Object)` syntax. Any .NET method called on the array object
triggers implicit `.ToString()` (space-joined).

## Solution

Add `| Select-Object -First 1` after `Where-Object` to force a single-element
result before passing to .NET methods:

```powershell
$line = ($Frontmatter -split '\r?\n' |
         Where-Object { $_ -match '^\s*tools:' } |
         Select-Object -First 1)
```

This also silently handles duplicate keys — the first match wins, which is the
correct behavior for a helper that mirrors how YAML parsers handle duplicates.

## Prevention

- **Rule**: Never pass `Where-Object` output directly to a .NET method that
  expects a `[string]`. Always add `| Select-Object -First 1` or cast to
  `[string]` when scalar string input is required.
- **Test coverage**: Add a test for the multi-key dedup case explicitly:
  ```powershell
  It "returns only first tools line when multiple tools: keys present" {
      $fm = "tools: ['agent']`ntools: ['read', 'write']"
      $result = Get-ToolsList -Frontmatter $fm
      @($result).Count | Should Be 1
      ($result -contains 'agent') | Should Be $true
  }
  ```

## Related

- [2026-04-21-test-fixture-must-match-function-input-contract.md](./2026-04-21-test-fixture-must-match-function-input-contract.md) — related: fixtures that included `---` delimiters masked this issue
- [2026-03-19-testing-powershell-switch-parameters.md](./2026-03-19-testing-powershell-switch-parameters.md) — other PowerShell type-coercion traps in tests
