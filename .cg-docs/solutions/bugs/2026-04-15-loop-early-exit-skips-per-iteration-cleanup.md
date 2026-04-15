---
date: 2026-04-15
title: "Loop early-exit directive skips per-iteration cleanup steps"
category: "bugs"
type: "anti-pattern"
language: "both"
tags: [prompt-design, cg-work, loop, early-exit, cleanup, validate, commit, step-ordering, anti-pattern]
root-cause: "An early-exit directive inside a for-each loop body ('continue to the next plan step') jumps the outer loop, silently skipping the rest of the current iteration — including Validate, Commit, and Report"
severity: "P1"
fix-confirmed: "yes"
reviewed-in: ".cg-docs/reviews/2026-04-15-per-step-test-failure-handling-standard-review.md"
---

# Loop Early-Exit Directive Skips Per-Iteration Cleanup Steps

## Problem

`cg-work.prompt.md` has a `For each step in the plan` outer loop. Inside
that loop, the Test Failure Recovery (TFR) block for two-attempt exhaustion
instructed:

```markdown
4. If tests are still failing after 2 fix attempts:
   > "N test(s) still failing after 2 fix attempts — ..."
   Continue to the next plan step.
```

"Continue to the next plan step" means the **outer loop's `continue`** —
jump to iteration N+1. This silently skipped every remaining sub-step of
the *current* iteration:

- `get_errors` (Auto-Fix Diagnostics)
- `@cg-fix-problems` dispatch
- **Validate** (step 5) — acceptance criteria never checked
- **Commit checkpoint** (step 6) — no conventional commit suggested
- **Report** (step 7) — no step summary written

Code with live diagnostic errors could advance to the next plan step
unexamined. If auto-fix diagnostics would have caught a type error, it
was silently dropped.

**Discovered as P1.1** in the standard review of the per-step test failure
handling feature (2026-04-15).

## Root Cause

The TFR author intended "move on from test retries and continue the current
step's remaining sub-sequence." But the phrase "continue to the next plan
step" is unambiguous to an LLM: it means the outer loop's **next
iteration**, not a forward jump within the current iteration.

The cleanup sub-steps (Validate, Commit, Report) come *after* TFR and
Auto-Fix Diagnostics in the loop body. Any directive that sounds like "move
on" is interpreted as outer-loop `continue` unless it explicitly names the
next *inner* target.

**The general anti-pattern**: An early-exit directive inside a for-each
loop is ambiguous when:
- The outer-loop unit and an inner sequence share the word "step", AND
- The directive uses a vague phrase ("next step", "move on", "continue")
  without naming the specific target sub-step.

## Solution

Replace the vague outer-loop directive with an explicit forward reference
to the **next inner sub-step**:

```markdown
# Before (broken):
Continue to the next plan step.

# After (fixed):
Continue to **Auto-Fix Diagnostics** (below).
```

This makes the target unambiguous: fall through to the next block in the
current iteration, not start the next iteration.

## Prevention

**Rule**: Inside a for-each loop body, use explicit named targets for
forward jumps — never relative phrases like "next step", "move on", or
"continue".

**Audit pattern for prompt files**: After adding any early-exit
instruction inside a loop body, ask:
1. What is the *outer* loop's unit? (plan step, review finding, etc.)
2. What sub-steps still need to run in this iteration after the early exit?
3. Does the directive skip any of them?

**If cleanup sub-steps remain**: use `Continue to <Named Block> (below)`,
not `continue to the next <outer-unit>`.

**Contrast with intentional outer-loop exit**: If you genuinely want to
skip remaining sub-steps and start the next outer iteration (e.g., "this
step produced no output, nothing to do"), be explicit:
```markdown
Skip the remaining sub-steps for this plan step and continue to
plan step N+1.
```

## Related

- `.cg-docs/solutions/testing-patterns/2026-04-13-dead-step-after-wait-prompt-session-terminator.md`
  — related: steps placed *after* a user-wait are also unreachable, but
  across session boundaries rather than within a loop
- `.cg-docs/solutions/bugs/2026-04-15-self-defeating-guardrail-exception-in-llm-prompts.md`
  — from the same review; another class of silent prompt logic failure
- `.cg-docs/solutions/bugs/2026-04-15-per-batch-retry-counter-unbounded-loop.md`
  — from the same review; retry counter that resets unintentionally
