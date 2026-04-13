---
date: 2026-04-13
title: "cg-work roadmap status never updated to done after plan completion"
category: "bugs"
type: "bug"
language: "both"
tags: [cg-work, roadmap, status-drift, step-ordering, dead-code]
root-cause: "Roadmap update step placed after user-wait pause — session ends before it executes"
severity: "P2"
test-written: "yes"
fix-confirmed: "yes"
---

# cg-work roadmap status never updated to done after plan completion

## Symptom

When `/cg-work` completes a feature tracked in `roadmap.json`, it marks the
plan file's status as `completed` (Step 3.5) but never updates the
corresponding feature's status in `roadmap.json`. Features remain as `idea`
or `active` in the roadmap long after they've been built and shipped.

Evidence: Three Quality Loop features (`cg-fix-problems-agent`,
`cg-fix-problems-prompt`, `ce-improvements-integration`) had their plans
marked completed but `roadmap.json` still showed them as `idea` / `active`.
Had to be corrected manually during a `/cg-strategy` session on 2026-04-13.

## Root Cause

In `cg-work.prompt.md`, Step 5 ("Update Roadmap Status") was positioned
**after** Step 4 ("Summary"), which ends with:

> "Wait for the user's response before proceeding."

After that wait, the user always picks a next action (`/cg-review`,
`/cg-compound`, etc.) which starts a new conversation. Step 5 was effectively
dead code — it could never execute.

The plan file update (Step 3.5) worked correctly because it runs **before**
the summary and wait.

## Reproduction Test

File: `tests/prompt-tools.Tests.ps1`, block
`"cg-work.prompt.md - roadmap done update before summary wait"`.

```powershell
It "dispatches roadmap 'status done' update BEFORE the 'Wait for the user' pause (prevents roadmap drift)" {
    $waitPos = $content.IndexOf("Wait for the user's response before proceeding")
    $donePos = $content.IndexOf("status done")
    # Both phrases must be present
    $donePos | Should BeGreaterThan -1
    $waitPos | Should BeGreaterThan -1
    # The roadmap update must precede the user-wait pause
    $donePos | Should BeLessThan $waitPos
}
```

The test verifies that the `"status done"` dispatch instruction appears at a
lower character offset than the `"Wait for the user's response before
proceeding"` line in the prompt file.

## Fix

Two changes:

1. **Moved roadmap update to Step 3.7** (`.github/prompts/cg-work.prompt.md`):
   Inserted the roadmap update logic between Step 3.5 ("Mark Plan Complete")
   and the former Step 4 ("Summary"). This places it in the automatic
   completion sequence that runs before the user-wait pause.

2. **Removed dead Step 5**: The old Step 5 after the wait was deleted entirely
   since its content now lives in Step 3.7.

3. **Tightened test assertion** (`tests/prompt-tools.Tests.ps1`): Changed
   `IndexOf("Wait for the user")` to
   `IndexOf("Wait for the user's response before proceeding")` to avoid a
   false match against a different "Wait for the user's choice" line in the
   mid-step auto-fix error handler (Step 2).

## Lessons Learned

**Anti-pattern: Placing side-effect steps after a user-wait pause.** In
prompt-driven workflows, a "wait for the user" instruction is effectively a
session terminator — the user's next action almost always starts a different
prompt. Any step with side effects (file writes, status updates, agent
dispatches) must execute **before** the final user-wait.

**Pattern to follow:** All automated completion work (marking plans done,
updating roadmap, cleaning up) should be grouped in a contiguous block
(Steps 3.x) that runs before the summary and user-wait. The summary step
should be the last step before the wait.

**Testing pattern:** Position-based assertions (`IndexOf` comparisons) are
a lightweight way to enforce step ordering in prompt files. When using them,
be specific with the search string to avoid matching unrelated occurrences.

## Related

None.
