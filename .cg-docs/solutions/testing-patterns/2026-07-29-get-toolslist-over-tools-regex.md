---
date: 2026-07-29
title: "Use Get-ToolsList helper over regex for YAML tools-array assertions"
category: "testing-patterns"
language: "PowerShell"
tags: [pester, yaml, tools-array, frontmatter, regex, helper]
root-cause: "A regex like tools:.*'read' fails silently on multi-line YAML array blocks and can produce false positives on other frontmatter fields"
severity: "P2"
---

# Use Get-ToolsList Helper Over Regex for YAML Tools-Array Assertions

## Problem

Agent frontmatter files declare a `tools:` array. Tests often assert the
presence or absence of specific tools using a line-regex:

```powershell
It "[$name] has tools including 'read'" {
    ($fm -match "tools:.*'read'") | Should -Be $true
}
It "[$name] does not have 'write' tool" {
    ($fm -notmatch "'write'") | Should -Be $true
}
```

Two failure modes:

1. **Multi-line YAML fails silently**: If any agent is reformatted to
   multi-line YAML:
   ```yaml
   tools:
     - 'read'
     - 'search'
   ```
   then `tools:.*'read'` produces a false negative — the test fails even
   though the tool is present.

2. **Over-broad notmatch**: `($fm -notmatch "'write'")` matches on the
   literal string `'write'` anywhere in the frontmatter — including in the
   `description:` field or a comment. Could produce false negatives if a
   description happens to mention "overwrite" or similar text.

## Root Cause

Single-line regex cannot reliably parse multi-line YAML. The `tools:` field
can be inlined (`tools: ['read', 'search']`) or expanded (multi-line array),
and both are valid. Tests that only handle the inline form are fragile.

## Solution

Use the `Get-ToolsList` helper (defined in `tests/helpers.ps1`) which
tokenizes the tools list correctly for both single-line and multi-line YAML:

```powershell
It "[$name] has tools including 'read'" {
    $tools = Get-ToolsList -Frontmatter $fm
    ($tools -contains 'read') | Should -Be $true
}
It "[$name] does not have 'write' tool" {
    $tools = Get-ToolsList -Frontmatter $fm
    ($tools -contains 'write') | Should -Be $false
}
```

`Get-ToolsList` uses `['""](\w+)['""]` to extract quoted tool names from
the raw frontmatter string, then returns an array — works correctly for
both `tools: ['read']` and multi-line array blocks.

**Performance note**: Calling `Get-ToolsList` twice (once per `It` block)
is redundant but harmless in Pester 4. If micro-optimisation matters,
assign `$tools` at Context scope: `$tools = Get-ToolsList -Frontmatter $fm`.

## Prevention

- Replace all `$fm -match "tools:.*'<name>'"` patterns with `Get-ToolsList`.
- Replace all `$fm -notmatch "'<name>'"` with `($tools -contains '<name>') | Should -Be $false`.
- When writing new agent tests, always use `Get-ToolsList` for tool assertions.

## Related

- `2026-07-29-pester-context-scope-frontmatter-guard.md` — companion pattern
  for safe Context-scope frontmatter reading
- `tests/helpers.ps1` — `Get-ToolsList` function definition (line 18)
