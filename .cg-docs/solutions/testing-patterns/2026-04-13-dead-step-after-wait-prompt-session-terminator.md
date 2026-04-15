---
date: 2026-04-13
title: "Dead-step-after-wait: prompt steps after a user-wait pause never execute"
category: "testing-patterns"
language: "both"
tags: [prompt-design, copilot, cg-work, roadmap, dead-code, step-ordering, session-terminator]
root-cause: "Steps placed after a 'Wait for the user's response' pause are dead code — the user's next action starts a new session and the remaining steps never execute"
severity: "P1"
---

# Dead-Step-After-Wait: Prompt Steps After a User-Wait Pause Never Execute

## Problem

`cg-work.prompt.md` had a Step 5 ("Update Roadmap Status") placed **after**
Step 4 ("Summary"), which ended with:

> "Wait for the user's response before proceeding."

After that pause, the user picks a next action — `/cg-review`, `/cg-compound`,
etc. — which starts a new conversation. Step 5 was dead code: it executed in
zero of the sessions where it was supposed to run.

**Observable consequence**: Three `cg-fix-problems` features completed their
plans (plan frontmatter marked `status: completed`) but `roadmap.json` still
showed them as `idea` / `active`. Required manual correction in a `/cg-strategy`
session.

## Root Cause

In prompt-driven AI workflows, `"Wait for the user's response before
proceeding"` is effectively a **session terminator**. The user's next reply
almost always invokes a different prompt — so the current prompt's context
ends. Any step with side effects (file writes, status updates, agent dispatches)
placed after a user-wait pause is unreachable.

This is invisible during development: there is no compiler, no error, no
warning. The prompt "looks correct" — the step is present. It simply never
runs.

## Solution

**Rule**: All automated completion work must execute **before** the
summary/user-wait. The summary step should be the last step before the pause.

In `cg-work.prompt.md`, the fix was to insert the roadmap update as Step 3.7
— in the contiguous automatic completion block (3.5 → 3.7 → 4 Summary → wait):

```
Step 3.5: Mark Plan Complete      ← automatic, no user input
Step 3.7: Update Roadmap Status   ← automatic, no user input  [MOVED HERE]
Step 4:   Summary                 ← automatic, no user input
           Wait for the user's response ...  ← session ends here
```

Old (broken) ordering:
```
Step 4:   Summary
           Wait for the user's response ...  ← session ends here
Step 5:   Update Roadmap Status   ← DEAD CODE, never reached
```

## Prevention

**When adding a new step to any prompt**, ask:
> "Is there a 'Wait for the user's response' pause between this step and the
> step before it?"

If yes — the new step is dead code. Move it before the wait.

**Structural rule for prompt files:**
1. All automatic steps (side effects, writes, dispatches) → grouped before summary
2. Summary presentation → last automatic step
3. "What next?" options → last content before wait
4. `Wait for the user's response before proceeding.` → only appears once per prompt, at the very end

**Check all existing prompts**: run this search after any prompt restructure:

```powershell
# Find prompts that have substantive content after the wait line
$prompts = Get-ChildItem ".github\prompts\*.prompt.md"
foreach ($p in $prompts) {
    $content = Get-Content $p.FullName -Raw
    $waitIdx = $content.IndexOf("Wait for the user's response before proceeding")
    if ($waitIdx -gt 0 -and $content.Length - $waitIdx -gt 100) {
        Write-Warning "$($p.Name): content after wait ($($content.Length - $waitIdx) chars)"
    }
}
```

**Add a regression test** for any step that must precede a wait:

```powershell
It "roadmap dispatch appears before user-wait pause" {
    $waitPos = $content.IndexOf("Wait for the user's response before proceeding")
    $donePos = $content.IndexOf("to status done.")
    $donePos | Should BeGreaterThan -1
    $waitPos | Should BeGreaterThan -1
    $donePos | Should BeLessThan $waitPos
}
```

## Related

- `.cg-docs/solutions/bugs/2026-04-13-cg-work-roadmap-status-never-updated-to-done.md` — the specific bug instance
- `.cg-docs/solutions/testing-patterns/2026-04-13-prompt-interaction-branch-completeness.md` — related: all response branches must be explicitly handled
- `.cg-docs/solutions/testing-patterns/2026-03-30-prompt-pipeline-contract-testing.md` — related: testing interface contracts between chained prompts
- `.cg-docs/solutions/bugs/2026-04-15-self-defeating-guardrail-exception-in-llm-prompts.md` — related: another class of self-nullifying LLM guardrail (exception triggers on same evidence as the rule)
- `.cg-docs/solutions/bugs/2026-04-15-per-batch-retry-counter-unbounded-loop.md` — related: bounded retry logic that resets incorrectly per failure batch
- `.cg-docs/solutions/bugs/2026-04-15-loop-early-exit-skips-per-iteration-cleanup.md` — related: loop early-exit directive skips per-iteration cleanup steps (same root cause, within a loop rather than after a wait)
