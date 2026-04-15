---
date: 2026-04-15
title: "Per-batch retry counter creates unbounded loop when cascading regressions occur"
category: "bugs"
type: "anti-pattern"
language: "both"
tags: [prompt-design, cg-work, adversarial, retry-logic, bounded-retry, test-failure-recovery, anti-pattern, loop]
root-cause: "Scoping a 'max N attempts' counter to a per-batch failure set instead of the whole logical unit lets cascading regressions chain fresh counters indefinitely"
severity: "P0"
fix-confirmed: "no"
reviewed-in: ".cg-docs/reviews/2026-04-15-per-step-test-failure-handling-review.md"
---

# Per-Batch Retry Counter Creates Unbounded Loop

## Problem

`cg-work.prompt.md`'s Test Failure Recovery block defined a 2-attempt limit
scoped to a specific set of *targeted failures*:

```markdown
If any tests fail:
1. Make a targeted fix and re-run.
2. If still failing, make one more targeted fix and re-run.    ← counter = 2
3. If the targeted failures are resolved, re-run the full test suite.
   If the full suite passes, continue normally.
4. If tests are still failing after 2 fix attempts: emit notification.
```

The problem: rule 3's full-suite re-run can expose a **new** regression that
wasn't in the original targeted set. Because the counter was scoped to
targeted failures (now resolved), the new failure has a **fresh counter of
zero**. The LLM starts another 2-attempt cycle. That fix may again resolve
targeted failures but expose another full-suite regression — and so on
indefinitely.

**Discovered as P0.2** in the cg-adversarial thorough review of the
per-step test failure handling feature (2026-04-15).

## Root Cause

The attempt counter was scoped to a **failure batch** (the initial failing
test set) rather than the **logical unit** (the plan step as a whole).

Cascading regression pattern:
```
Attempt 1: Fix targeted failures (A fails) → A passes, full suite reveals B fails
Attempt 2: Fix targeted failures (B fails) → B passes, full suite reveals C fails  
Attempt 3: Fix targeted failures (C fails) → ...  (counter reset each time)
```

The user never sees a notification because the 2-attempt cap is never
reached *within any single batch*. The LLM modifies code indefinitely.

**The general anti-pattern**: Bounded retry logic is unbounded when the
counter resets at the boundary of each sub-batch, rather than the whole
logical unit.

## Solution

Make the counter global to the **logical unit** (the plan step), not the
failure batch:

```markdown
If any tests fail:
1. Make a targeted fix and re-run. (Attempt 1 of 2 for this plan step)
2. If still failing, make one more targeted fix and re-run. (Attempt 2 of 2)
3. If the targeted failures resolve, re-run the full test suite.
   If the full suite passes, continue normally.
   If the full suite reveals new regressions, emit the standard failure
   notification and continue — the 2-attempt budget is exhausted.
4. If any tests are **still failing after 2 total fix attempts** (targeted or
   regression), emit the notification and continue to Auto-Fix Diagnostics.
```

Key change: **"2 fix attempts total for this plan step, regardless of which
failure batch triggered them."**

## Prevention

When designing bounded retry logic:

1. **Define the logical unit** — what does one complete "work item" represent?
   (Here: one plan step, not one failure batch.)
2. **Scope the counter to the logical unit** — the counter increments once per
   fix attempt, regardless of which failure subset triggered it.
3. **Ask**: "Can the counter reset to zero while still inside the same logical  
   unit?" If yes, the bound is broken.

**Checklist for retry logic**:
- [ ] Is the counter scoped to the full logical unit, not a sub-batch?
- [ ] Can a cascade of sub-batch resolutions keep the counter below the cap?
- [ ] Is there a termination condition that fires regardless of which batch
  triggered the last failure?
- [ ] Does the "continue normally" path guarantee the counter state is
  consumed, not bypassed?

## Related

- `.cg-docs/solutions/bugs/2026-04-15-self-defeating-guardrail-exception-in-llm-prompts.md`
  — companion P0 finding from the same review; both are adversarial prompt
  design anti-patterns discovered in Test Failure Recovery
- `.cg-docs/solutions/testing-patterns/2026-03-30-prompt-pipeline-contract-testing.md`
  — testing patterns for catching prompt logic bugs
