---
date: 2026-05-19
title: "Pester YAML-entry regex: negative lookahead blocks sub-entries; heading backticks break plain-text match"
category: "testing-patterns"
language: "n/a"
tags: [pester, regex, yaml, negative-lookahead, dotall, markdown-heading, backtick, wiki-tests]
root-cause: "The (?:(?!-\\s+id:).)*? guard that prevents YAML cross-entry matching also blocks traversal of sub-entries that share the same key pattern (- id:); separately, a ## heading containing inline code (backtick-wrapped word) does not match its plain-text equivalent in regex"
severity: "P2"
test-written: "yes"
fix-confirmed: "yes"
---

# Pester YAML-entry regex: negative lookahead blocks sub-entries; heading backticks break plain-text match

## Problem

### Gotcha 1 — YAML sub-entry blocked by entry-boundary guard

When writing Pester assertions that must match a specific field within one
YAML entry (without falsely matching a field of the same name in a later
entry), the canonical guard is:

```powershell
($yml -match '(?s)id:\s*"reference"(?:(?!-\s+id:).)*?sections:') | Should -Be $true
```

The `(?:(?!-\s+id:).)*?` construct says: advance one character at a time,
but stop if the next characters are `- id:` (the start of another entry).
This correctly prevents crossing from the `reference` entry into
`context-files`, `model-guide`, etc.

**But it also blocks sub-entries.** YAML sub-entries under `sections:` are
formatted as:

```yaml
    sections:
      - id: "commands"
        managed: true
```

The `- id: "commands"` sub-entry also matches `-\s+id:`. So the negative
lookahead fires at the `- id:` sub-entry and the regex cannot advance past
it — meaning `managed: true` on the line *after* the sub-entry is
unreachable by the same anchored pattern.

**Symptom**: Test for `managed:\s*true` returns `$false` even though
`managed: true` is clearly present in the YAML.

### Gotcha 2 — Markdown heading with inline code doesn't match plain text

A section heading that contains an inline-code word:

```markdown
## Post-`init` Checklist
```

does **not** match the regex `^##\s+Post-init Checklist` — the backtick
characters sit between `Post-` and `init`. `grep_search` with query
`"Post-init Checklist"` also returns no results.

**Symptom**: Tests and searches for the heading text return no matches even
though the section clearly exists in the file.

## Root Cause

### Gotcha 1

The entry-boundary guard `(?!-\s+id:)` uses the same YAML key pattern (`- id:`)
that YAML uses for nested list items. It was designed to detect *top-level*
entry boundaries but cannot distinguish those from sub-entries at deeper
indentation.

### Gotcha 2

Backtick characters are literal characters in the file — they are not stripped
by any regex flag or `Get-Content` option. The heading in the file is the
literal string `## Post-` + backtick + `init` + backtick + ` Checklist`, which
contains 2 extra characters compared to `Post-init Checklist`.

## Solution

### Fix for Gotcha 1 — Split into two separate assertions

For fields **inside sub-entries**, do not try to anchor to the parent entry.
Instead, rely on domain uniqueness: if the field value only occurs in pages
with the right type, an unanchored match is safe.

```powershell
# ✅ Anchored match for the field that comes BEFORE any sub-entry
($yml -match '(?s)id:\s*"reference"(?:(?!-\s+id:).)*?sections:') | Should -Be $true

# ✅ Unanchored match for the field INSIDE the sub-entry
# Safe: only auto-ownership pages ever have managed: true
($yml -match 'managed:\s*true') | Should -Be $true
```

Alternatively, refactor the YAML to move the simple flag up into the page-level
entry — but that may conflict with the schema.

### Fix for Gotcha 2 — Use flexible regex patterns

Replace literal heading text with a flexible pattern that tolerates inline code:

```powershell
# ❌ Fails when heading is '## Post-`init` Checklist'
($content -match '(?m)^##\s+Post-init Checklist') | Should -Be $true

# ✅ Tolerates backtick-wrapped words in the heading
($content -match '(?m)^##\s+Post-.*Checklist') | Should -Be $true
```

For content assertions that reference the section (not just the heading), the
same principle applies — use `.*` between words that might be separated by
inline-code punctuation:

```powershell
# ❌ Fails if the section heading or body uses backtick formatting
($content -match '(?is)Post-init Checklist.*ownership.*auto') | Should -Be $true

# ✅ Handles both plain and backtick-formatted headings
($content -match '(?is)Post-.*Checklist.*ownership.*auto') | Should -Be $true
```

## Prevention

### For YAML entry assertions

Use a two-assertion pattern:

1. **Anchor the parent entry → field-before-sub-entries** using the boundary guard.
2. **Assert sub-entry fields with an unanchored match** that relies on domain uniqueness.

```powershell
# Pattern: check YAML block structure (anchored) + leaf field (unanchored)
($yml -match '(?s)id:\s*"reference"(?:(?!-\s+id:).)*?sections:') | Should -Be $true
($yml -match 'managed:\s*true') | Should -Be $true
```

Document why the unanchored match is safe (comment the "only occurs in X" reason).

### For Markdown heading assertions

When the heading text might contain inline code (especially in headings that
are user-configurable or contain command names):

- Use `.*` or `[^#]*` instead of expecting exact literal text.
- If the heading is known-exact at write time, use the exact backtick-escaped form:

```powershell
# Exact match for known heading format
($content -match '(?m)^##\s+Post-`init`\s+Checklist') | Should -Be $true
```

but prefer the flexible form so tests don't break if the heading is reformatted.

### For `grep_search` / plain-text search

If searching for a heading that contains inline code, use only the invariant
parts as search query (omit backtick-surrounded words or use partial queries).

## Related

- [2026-05-19-cg-compound-wiki-update-silently-skipped-all-manual-pages.md](../bugs/2026-05-19-cg-compound-wiki-update-silently-skipped-all-manual-pages.md) — the wiki fix that produced the YAML tests where both gotchas surfaced
- [2026-05-06-pester-caret-anchor-requires-multiline-flag.md](./2026-05-06-pester-caret-anchor-requires-multiline-flag.md) — sibling Pester regex gotcha: `^` without `(?m)` is always false in multi-line files
