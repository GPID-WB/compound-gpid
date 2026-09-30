---
date: 2026-05-14
title: "Zero-byte/near-empty files bypass graceful-skip guards and produce false-negative clean results in scan agents"
category: "bugs"
language: "both"
tags: [agent-design, input-validation, graceful-skip, empty-file, false-negative, cr-mathematical-verification, cr-identification-audit, scan-agent, zero-byte]
root-cause: "Graceful-skip logic checks for *absence* of files (no files found → skip). A zero-byte or near-empty file satisfies 'file found' but provides no content for the scan — the agent proceeds through all steps, finds nothing, and returns a false 'no discrepancies' instead of a skip message."
severity: "P0"
---

# Zero-Byte/Near-Empty Files Bypass Graceful-Skip Guards

## Problem

Scan agents in this project use a graceful-skip pattern:

```markdown
If no derivation files exist:
> "No derivation files found. Symbolic verification skipped."
Stop and return this message.
```

The gap: graceful-skip is triggered by **absence** (`no files found`), but a
zero-byte `.tex` or `.md` file satisfies the "file found" condition. The agent:

1. Detects the file in Step 1 → proceeds (no graceful skip)
2. Builds a variable mapping table in Step 2 → table is empty (no content)
3. Runs verification checks in Step 3 → nothing to check
4. Returns "No discrepancies found" or silently passes

This was found in `@cr-mathematical-verification` (P0.4) and similar gaps in
`@cr-identification-audit` (P2.12) and `@cr-econometric-reasoning` (P2.13)
in the 2026-05-14 thorough review.

**Impact**: A researcher can create placeholder `.tex` files with zero bytes
(e.g., as empty scaffolding) and the mathematical verification agent will report
a clean result — even though no verification was actually performed.

## Root Cause

Existence check ≠ content check. The pattern:

```
if (no files) → skip
else → proceed
```

treats existence as sufficient signal that the content is processable. In file
systems, a file exists as soon as it's created — even before any content is
written. Empty scaffolding files (common in early-stage research), accidentally
committed zero-byte files, or git-tracked placeholder files all trigger this gap.

## Solution

Augment graceful-skip to check **content length** in addition to existence:

```markdown
If no derivation files exist:
  → return skip message

If derivation files exist but ALL are zero-byte or contain fewer than
50 non-whitespace characters (empty scaffolds):
  → treat as "no files found" and return the same skip message
  → note: "Derivation files found but contain no parseable content"
```

The 50-character threshold is conservative — a legitimate equation like
`\beta = \frac{Y}{X}` is ~20 characters.

For input-file validation in non-skip contexts (agents that don't have a
graceful-skip, but receive a file to scan):

```markdown
Before beginning: if any file under review is zero-byte or contains only
whitespace/comments (no executable code), report:
"[file] is empty — [review type] skipped for this file."
Do not proceed with Steps 1–N against empty files.
```

## Pattern

**Every scan agent that has a graceful-skip guard must also check content
length, not just file existence:**

```
graceful-skip = absence OR (existence AND content_length < threshold)
```

Apply to:
- Agents checking for derivation files (`@cr-mathematical-verification`)
- Agents scanning code for patterns (`@cr-identification-audit`, `@cr-econometric-reasoning`)
- Any agent whose graceful-skip fires on `no files found`

## Prevention

When writing a scan agent, add this check to every file-existence guard:

```markdown
Step N: Check <X> files
- If no <X> files found → [graceful skip message]
- If <X> files found but all are zero-byte or contain fewer than 50
  non-whitespace characters → treat as absent, return skip message
- Otherwise → proceed
```

Pester test to add:
```powershell
It "graceful skip handles empty/zero-byte files (not just absent files)" {
    ($content -match '(?i)zero.byte|fewer than \d+ non.whitespace|empty scaffold') | Should -Be $true
}
```

## Related

- [`2026-04-15-prompt-step-silent-skip-antipattern-fallback-required.md`](../testing-patterns/2026-04-15-prompt-step-silent-skip-antipattern-fallback-required.md) — related: steps that silently skip when conditions are not met
- [`2026-04-29-two-phase-injection-guard-for-agent-file-reads.md`](../testing-patterns/2026-04-29-two-phase-injection-guard-for-agent-file-reads.md) — related: input file validation for AI agents
