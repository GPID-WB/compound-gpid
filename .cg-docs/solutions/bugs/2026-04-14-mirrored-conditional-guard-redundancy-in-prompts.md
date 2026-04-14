---
date: 2026-04-14
title: "Mirrored conditional guard creates redundant closing clause in prompt steps"
category: "bugs"
type: "anti-pattern"
language: "both"
tags: [prompt-design, cg-work, redundant-guard, step-structure, anti-pattern, review-finding]
root-cause: "Closing 'If X does not exist: skip' guard mirrors the opening 'If X exists:' wrapper — the negative case is already implied and the duplicate creates confusion for future authors"
severity: "P3"
test-written: "no"
fix-confirmed: "yes"
---

# Mirrored Conditional Guard Redundancy in Prompt Steps

## Problem

A prompt step was structured as:

```markdown
If `roadmap.json` exists at the project root:

1. Step A
2. Step B
3. Step C

If `roadmap.json` does not exist, skip this step entirely.
```

The closing guard is logically redundant: the entire body is already wrapped in the
positive condition. The duplication implies the two guards apply different conditions
when they do not — misleading future authors who extend the step.

Caught as **P3.2** in the `2026-04-13-cg-work-roadmap-bug-review.md` thorough review
of the cg-work roadmap bug fix.

## Root Cause

When adding a conditional step to a prompt file, authors write the opening guard
(`If X exists:`) and then reflexively add a closing safety net (`If X does not
exist: skip`) without realizing the closing clause is already implied by the
surrounding `if` block's structure.

The negative case is logically equivalent to "fall out of the `if` block" — no
explicit instruction is needed.

## Solution

Remove the closing guard. The opening `If X exists at the project root:` wrapper
is sufficient. The step is silently skipped when `X` does not exist.

**Before:**
```markdown
If `roadmap.json` exists at the project root:

1. ...
2. ...

If `roadmap.json` does not exist, skip this step entirely.
```

**After:**
```markdown
If `roadmap.json` exists at the project root:

1. ...
2. ...
```

Fix applied in `b2f5ef6..1ccb6c7` to `.github/prompts/cg-work.prompt.md` Step 3.7.

## Prevention

When authoring a conditional prompt step:

- **Use one guard, not two** — write the opening condition only; the negative case
  is implicit.
- **Exception**: Use a closing guard only when the two conditions are *non-exhaustive*
  (e.g., `If X is 'light': ... If X is 'standard': ... otherwise: ...`).
- **Review trigger**: Flag any step where the last non-blank line before the next
  heading is a restatement of the opening condition in negative form.

## Related

- [2026-04-13-cg-work-roadmap-status-never-updated-to-done.md](./2026-04-13-cg-work-roadmap-status-never-updated-to-done.md) — the roadmap bug fix session that produced the review containing this finding
- [2026-04-13-dead-step-after-wait-prompt-session-terminator.md](../testing-patterns/2026-04-13-dead-step-after-wait-prompt-session-terminator.md) — adjacent pattern from the same session: dead steps placed after a user-wait pause
