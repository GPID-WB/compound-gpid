---
date: 2026-04-15
title: "cg-work Step 3.7 silently skips plan:null features — no fallback"
category: "bugs"
type: "bug"
language: "both"
tags: [cg-work, roadmap, step-3-7, plan-null, silent-skip, fallback]
root-cause: "Step 3.7 only matched features by plan path; when plan:null, it warned and exited with no title-search fallback"
severity: "P2"
test-written: "yes"
fix-confirmed: "yes"
---

# cg-work Step 3.7 silently skips plan:null features — no fallback

## Symptom

When `/cg-work` implements a plan that covers roadmap features where `plan: null`
(either because the features were never linked, or because the plan itself
adds new features not yet in the roadmap), Step 3.7 emits a single soft warning:

> "No matching feature found in `roadmap.json`. Verify the plan path is linked
> with `@cg-roadmap`."

…and then exits without updating any feature statuses. The features remain
at their pre-implementation status indefinitely. This is silent data drift —
no error, no prompt, no recovery path.

## Root Cause

Step 3.7's matching logic was:

1. Find features where `plan == <plan-path>` (path normalization applied).
2. If none found → emit soft warning → **stop**.

Step 2 had no fallback. Any feature with `plan: null` was structurally
unreachable by Step 3.7, regardless of whether the plan's content clearly
described that feature. The warning was easy to miss because Step 3.7 runs
inside the automated completion sequence and the user sees it buried between
other status messages.

## Reproduction Test

File: `tests/prompt-tools.Tests.ps1`, Describe block `P1.37`:

```powershell
Describe "cg-work.prompt.md - Step 3.7 title-search fallback for plan:null features" {
    It "Step 3.7 searches feature titles in the plan content when no path match found" {
        ($content -match 'title.*plan content|feature.*title.*appear|scan.*plan.*title|title.*match.*plan') | Should Be $true
    }
    It "Step 3.7 prompts the user to confirm which unlinked features were completed" {
        ($content -match 'confirm.*which features|which.*features.*complet|ask.*user.*confirm') | Should Be $true
    }
    It "Step 3.7 still dispatches @cg-roadmap for confirmed matches from the fallback" {
        $step37Block = $content.Substring($step37Start, $step4Start - $step37Start)
        ($step37Block -match '@cg-roadmap') | Should Be $true
    }
}
```

All three assertions failed on current code before the fix.

## Fix

`.github/prompts/cg-work.prompt.md`, Step 3.7 — replaced the soft-warning
stop with a title-search fallback (step 2a):

> **2a. Title-search fallback for unlinked features:**
> Read the plan document. Scan all features in `roadmap.json` whose `plan`
> is null. For each such feature whose title appears in the plan's requirement
> list or step titles, collect it as a candidate. Ask the user to confirm
> which features were completed. For confirmed features: dispatch `@cg-roadmap`
> to set status done and link the plan. Only if no candidates are found from
> the title scan, emit the soft warning.

The fallback is interactive (user confirms candidates) to prevent false
positives — title matching is fuzzy and the LLM should not auto-update
without confirmation.

## Lessons Learned

A silent skip with a soft warning is functionally equivalent to no warning at
all in a multi-step workflow. When Step 3.7 could not proceed, it should have
**escalated to the user with actionable candidates**, not silently moved on.

**Pattern to follow**: When an automated step cannot find its target by the
primary key (plan path), attempt a secondary search (title match) and surface
candidates for confirmation rather than failing silently. This is especially
important for steps that update shared state (roadmap.json).

**Anti-pattern that caused it**: The warning message said "Verify the plan
path is linked with `@cg-roadmap`" — but the user only sees this after the
session is over, when the context is lost and the motivation to fix it is low.
Always offer an inline recovery path.

## Related

- [2026-04-15: Roadmap out of sync after plan:null features completed](./../2026-04-15-roadmap-out-of-sync-after-plan-null-features-completed.md) — Bug 1: data consequence of this mechanism.
- [2026-04-13: cg-work roadmap status never updated to done after plan completion](./../2026-04-13-cg-work-roadmap-status-never-updated-to-done.md) — earlier Step ordering bug; this is the next layer of the same failure class.
