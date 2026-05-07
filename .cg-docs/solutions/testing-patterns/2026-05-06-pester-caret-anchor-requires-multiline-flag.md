---
date: 2026-05-06
title: "Pester write-guard regex with ^ always false without (?m) — silent false-positive"
category: "testing-patterns"
language: "both"
tags: [pester, regex, powershell, multiline, caret-anchor, write-guard, prompt-testing, silent-failure, false-positive]
root-cause: "In .NET regex, ^ anchors to the start of the entire string by default. A write-guard pattern like (?i)^\\s*(write|modify) never matches because the file starts with frontmatter, not the target word — so the test always passes regardless of what the agent body contains."
severity: "P2"
fix-confirmed: "yes"
reviewed-in: ".cg-docs/reviews/2026-05-06-roadmap-visualization-review.md"
---

# Pester `^` Anchor Requires `(?m)` Multiline Flag — Silent False-Positive

## Problem

A write-guard test for `cg-roadmap-view.agent.md` was written as:

```powershell
It "write-guard: agent does not instruct writing to files" {
    ($content -match '(?i)^\s*(write|modify|create)\s+the\s+(file|roadmap|plan)') |
        Should Be $false
}
```

This test **always passes** — not because the agent is safe, but because the
pattern can never match. The agent file begins with `---` YAML frontmatter,
not a write instruction. In .NET regex, `^` without `(?m)` anchors to the start
of the entire string, so the pattern is evaluated exactly once at position 0
and immediately fails.

**The test gives a green checkmark whether or not the agent contains dangerous
write instructions anywhere in the body.**

Discovered as **P2.3** in the thorough review of the roadmap-visualization
feature (`2026-05-06-roadmap-visualization-review.md`).

## Root Cause

.NET regex has two distinct behaviors for `^` and `$`:

| Flag | `^` matches | `$` matches |
|------|------------|------------|
| (default) | Start of **string** only | End of **string** only |
| `(?m)` (Multiline) | Start of **each line** | End of **each line** |
| `(?s)` (Singleline / Dotall) | Start of string only | End of string only |

`(?m)` and `(?s)` are independent flags. `(?s)` only affects `.` — it does
not enable line-anchored `^`/`$`. They can be combined: `(?im)`.

The write-guard relied on `^` to prevent false positives (matching "write"
mid-sentence), but `^` without `(?m)` silently reduces the test to a noop
on any file that doesn't begin with the target word.

> **Companion trap**: see `2026-04-15-pester-dotall-flag-required-for-multiline-regex.md`
> for the `(?s)` case — `.*` silently failing to cross line breaks.

## Solution

Add `(?m)` to any regex pattern that uses `^` or `$` to anchor to a line
boundary rather than the string boundary:

```powershell
# BROKEN — ^ only matches start of entire string
($content -match '(?i)^\s*(write|modify|create)\s+the\s+(file|roadmap|plan)') |
    Should Be $false

# FIXED — (?m) makes ^ match start of each line
($content -match '(?im)^\s*(write|modify|create)\s+the\s+(file|roadmap|plan)') |
    Should Be $false
```

When both `^` anchoring and `.`-across-newlines are needed, combine both flags:

```powershell
($content -match '(?ims)^\s*(write|modify).*file') | Should Be $false
```

## Prevention

- **Any regex with `^` or `$`**: Ask "am I anchoring to the string boundary or
  a line boundary?" If the file has multiple lines (all prompt/agent files do),
  you almost certainly want `(?m)`.
- **Write-guard tests**: The canonical safe pattern is `(?im)^\s*<verb>`.
- **Code review check**: In PR review, flag every `-match '...'` containing
  `^` or `$` without `(?m)`.

## Related

- [`2026-04-15-pester-dotall-flag-required-for-multiline-regex.md`](2026-04-15-pester-dotall-flag-required-for-multiline-regex.md) — `(?s)` for `.` crossing line breaks (distinct issue, often confused)
- [`2026-03-02-prompt-file-permission-guardrails.md`](2026-03-02-prompt-file-permission-guardrails.md) — write-guard patterns for prompt files
