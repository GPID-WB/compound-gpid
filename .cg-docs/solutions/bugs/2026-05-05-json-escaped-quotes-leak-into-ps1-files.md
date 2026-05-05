---
date: 2026-05-05
title: "JSON-escaped quotes leak literal backslash-quote into PowerShell files"
category: "bugs"
language: "both"
tags: [powershell, pester, json, escaping, multi-replace, tool-bug, string-literals]
root-cause: "multi_replace_string_in_file newString parameter uses JSON encoding; \\\" is written literally to the file"
severity: "P1"
---

# JSON-Escaped Quotes Leak Literal `\"` Into PowerShell Files

## Problem

After using `multi_replace_string_in_file` (or a second sequential `replace_string_in_file`)
to insert PowerShell code containing double-quoted strings into a `.ps1` file, the
file on disk contained literal `\"` escape sequences — producing malformed PowerShell:

```powershell
# What appeared on disk (wrong):
It \"result-verification.md stores spec coefficient before reldif (P0.3 guard)\" {
    $rv = Get-Content (Join-Path $skillRoot \"references\\result-verification.md\") -Raw -Encoding UTF8
```

This caused Pester 3.4 to fail to parse the `It` block, resulting in test failures
with confusing messages ("file not found" or `{True}` expected but got `{}`).

## Root Cause

The `multi_replace_string_in_file` tool takes its `newString` parameter as a JSON
string. When the agent writes a PowerShell `It` block into the JSON `"newString"` field,
double quotes inside the PowerShell code must be JSON-escaped as `\"`. The tool is
supposed to unescape them on write — but in a second-pass `replace_string_in_file` call
targeting those same lines, the `oldString` must match the **file on disk** (with real
`"` chars). If the agent uses `\"` in `oldString` instead, the match fails, and
any subsequent write can introduce `\"` literals.

The failure mode here was: the first batch write (via `multi_replace_string_in_file`)
succeeded and wrote proper `"` characters. A second `replace_string_in_file` call then
wrote a `newString` that had literal `\"` sequences, either because the JSON encoding
was not properly handled or because the agent generated the content using `\"` in
the newString body.

## Solution

After every `replace_string_in_file` or `multi_replace_string_in_file` call that
inserts multi-line PowerShell code, **immediately read back the modified block** with
`read_file` to verify the written content. Catch any `\"` literals before running tests:

```powershell
# Correct on disk:
It "result-verification.md stores spec coefficient..." {
    $rv = Get-Content (Join-Path $skillRoot "references\result-verification.md") ...
```

```powershell
# Wrong — JSON escaping leaked:
It \"result-verification.md stores spec coefficient...\" {
    $rv = Get-Content (Join-Path $skillRoot \"references\\result-verification.md\") ...
```

If `\"` literals are found, apply a corrective `replace_string_in_file` using the
exact escaped-quote content as `oldString`.

## Prevention

1. **Always read back** any `.ps1` file section immediately after writing PowerShell
   `It` blocks, especially those with `Get-Content` paths using backslashes.
2. **Prefer single-pass batch writes** for multi-`It` additions — one
   `multi_replace_string_in_file` call is safer than chaining two separate calls
   where the second patches the first's output.
3. **Verify with tests before marking fixed**: run the targeted test file via
   `execution_subagent` before updating frontmatter to `fixed`. Escaped-quote bugs
   produce parse failures that tests immediately expose.

## Related

- `.cg-docs/solutions/testing-patterns/2026-04-15-pester-dotall-flag-required-for-multiline-regex.md` — another category of regex-in-Pester subtleties
- `tests/prompt-tools.Tests.ps1` — the affected file; P0.3 and P2.1 guard blocks were affected
