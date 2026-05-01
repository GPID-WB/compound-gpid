---
date: 2026-05-01
title: "Fix-triage changes to prompt text need co-authored Pester assertions"
category: "testing-patterns"
language: "both"
tags: [pester, powershell, prompt-testing, fix-triage, regression, coverage, verify-mode, co-authoring, cg-setup]
root-cause: "21 fix-triage changes were applied to cg-setup.prompt.md and setup-templates.md without co-authored tests; a verify pass found that 10 of those changes had zero regression coverage — behavioral changes that could silently regress without any test failure"
severity: "P1"
fix-confirmed: "yes"
reviewed-in: ".cg-docs/reviews/2026-05-01-smart-setup-phase2-revised-verify-review.md"
---

# Fix-Triage Changes to Prompt Text Need Co-Authored Pester Assertions

## Problem

A thorough review of the smart-setup Phase 2 changes produced 21 findings (P0–P3).
Fix-triage was applied across four priority batches (P0 → P1 → P2 → P3).

After all findings were marked `fixed`, a verify pass (`/cg-review mode:verify`) surfaced
**10 new findings** — all of them test coverage gaps. Nearly half of the 21 fixed
behaviors had no regression anchor:

| Fixed behavior (original review) | Had a test? |
|---|---|
| Duplicate Mode B content truncated (P0.1) | ✓ (line count test) |
| Unescaped `\|` in regex (P1.1) | ✓ (the fix itself was a test) |
| `roadmap.json` existence guard (P1.2) | ✗ — no test |
| Mode B B0.5 pre-load step (P1.3) | ✗ — no test |
| `cg-schema-version` carry-forward in B4 (P1.4) | ✗ — weak test (trivially passing) |
| Scanner injection sanitization block (P1.5) | ✗ — no test |
| Mode B B3 quality gate test (P1.6) | ✓ (the fix itself was a test) |
| B3→B4.5 state handoff (P1.7) | ✗ — no test |
| Fallback charter write ordering (P2.1) | ✗ — no test |
| Q3 `full fallback only` guard (P2.2) | ✗ — no test |
| `## Current Focus` in field mapping (P2.3) | ✗ — no test |
| Exact `<!-- TODO` blocker strings (P2.4) | ✗ — weak (broad `<!-- TODO` match) |
| Phantom cross-reference fix (P2.5) | ✗ — no test |
| Absent-table fallback (P2.6) | ✗ — no test |
| YAML quoting rule (P2.7) | ✗ — no test |
| JSON string escaping rule (P2.8) | ✗ — no test |
| Step numbering gap (P3.1) | implicitly via structure |
| `-ForegroundColor` fix (P3.2) | ✓ (linked to link.ps1 test) |
| Q4 language-config note (P3.3) | ✗ — no test |
| `cg-link` failure message expansion (P3.4) | ✗ — no test |
| `r-syntax` dialect prompt (P3.5) | ✗ — no test |

The verify pass's P1.1 finding (missing sanitization test) was the most serious:
the prompt injection mitigation — the primary security control — had zero regression
coverage. Deleting the sanitization block would not fail any test.

## Root Cause

When fix-triage applies a behavioral fix to a prompt file, the mental model is
"correcting instructions for the AI." Unlike code `if`-statements where missing
coverage is tool-detectable, prompt text guards and behavioral rules are plain text.
Nothing flags them as untested.

The habit of "add fix → add test" that applies naturally in code is easily broken
in prompt files because:
1. The fix looks like editorial work, not a code change.
2. The test for a prompt fix (`$content -match 'text-present'`) is boilerplate —
   it's easy to defer as "obvious."
3. Fix-triage sessions are long; test writing feels like extra friction.

Result: behaviors that must not silently regress have no regression anchor.

## Solution

**Rule**: Every fix-triage change that adds, modifies, or removes text from a
prompt file (`.prompt.md`, `.agent.md`, `SKILL.md`) must be accompanied by a
`($content -match '...') | Should Be $true` assertion in the corresponding
`tests/prompt-tools.Tests.ps1` Describe block.

**Pattern**:
```powershell
# Fix adds "If `roadmap.json` already exists, skip creation entirely" to A5.7
# → co-author this assertion in the same fix-triage step:
It "has roadmap.json existence guard (skip if already exists)" {
    ($content -match 'roadmap\.json.*already exists.*skip|already exists.*roadmap') | Should Be $true
}
```

**Placement**: Add to the existing Describe block that covers the changed section
(e.g., Mode A findings → "cg-setup.prompt.md - Mode A scanner integration").
If no block exists for the section, add one.

**For weak/trivially-passing tests**: If an existing assertion matches the changed
text incidentally (e.g., `cg-schema-version` appears in 5 places), add a more
specific assertion that targets the exact new behavior:
```powershell
# ✗ Weak — passes on any mention of cg-schema-version:
($content -match 'cg-schema-version') | Should Be $true

# ✓ Specific — fails if B4 carry-forward instruction is removed:
($content -match 'carry forward.*cg-schema-version|cg-schema-version.*unchanged') | Should Be $true
```

## Prevention

**In fix-triage sessions**: After applying each fix to a `.md` file, immediately
add the Pester assertion before moving to the next finding. Do not batch test
authoring to the end of the session.

**Self-check at end of fix-triage**: Before running the regression gate, review
each fixed finding and confirm a corresponding test exists. If any is missing,
add it before the gate run.

**In cg-review dispatches**: `@cg-testing` agents should explicitly check whether
fix-triage changes are covered — not just whether the changed prompt behavior
works, but whether a regression would fail a test.

## Related

- `.cg-docs/solutions/testing-patterns/2026-04-28-prompt-guard-conditions-need-immediate-pester-coverage.md` — same pattern, scoped to guard conditions in cg-release; this document generalizes it to all prompt text changes
- `.cg-docs/solutions/testing-patterns/2026-04-15-new-validation-branch-requires-dedicated-test.md` — same root cause in code: new branch added without new test
- `.cg-docs/solutions/testing-patterns/2026-04-07-pester-test-quality-patterns.md` — anchored regex and other quality patterns for prompt assertions
- `.cg-docs/reviews/2026-05-01-smart-setup-phase2-revised-review.md` — original thorough review (21 findings)
- `.cg-docs/reviews/2026-05-01-smart-setup-phase2-revised-verify-review.md` — first verify pass (10 coverage gaps found)
