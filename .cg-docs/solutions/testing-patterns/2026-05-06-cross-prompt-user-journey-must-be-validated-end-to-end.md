---
date: 2026-05-06
title: "Cross-prompt user journey must be validated end-to-end, not just per-prompt"
category: "testing-patterns"
language: "both"
tags: [powershell, pester, prompt-pipeline, cg-resume, cg-work, user-journey, contract-testing, phased-execution]
root-cause: "cg-resume told users to 'Run /cg-work' after all phases completed, but cg-work halts in that condition — a broken user journey undetectable by single-prompt tests"
severity: "P2"
---

# Cross-Prompt User Journey Must Be Validated End-to-End, Not Just Per-Prompt

## Problem

During the phased execution verify review, a **P2** finding emerged that all individual-prompt tests had missed:

- `cg-resume` Step 2a (all-phases-complete branch) instructed: *"All M phases completed. Run `/cg-work` to proceed to final quality checks."*
- `cg-work` Step 1.2 dispatch table (Phased | none row) explicitly **halts** when `completed-phases` contains all phases: *"display 'All N phases are already complete. Nothing to run.' and halt."*

A user following cg-resume's instruction would run `/cg-work` with no argument, hit the halt immediately, and never reach Step 3 quality checks. The prompts individually passed all their tests, but the **user journey** was broken.

This is different from the data/format contract issue documented in `2026-03-30-prompt-pipeline-contract-testing.md`. Format contracts verify that prompt A emits data in the format prompt B parses. Journey contracts verify that when prompt A says **"do X next"**, doing X in the state implied by prompt A actually works.

## Root Cause

Journey breakage occurs when:
1. Prompt A advises the user to invoke prompt B with arguments/state S.
2. Prompt B has a guard that halts or errors when entered with state S.
3. The guard and the advice were written at different times, by different fixes, without cross-checking.

In this case, the all-phases-complete halt in `cg-work` (added as P2.1 fix) and the "run `/cg-work`" suggestion in `cg-resume` (the original text) were never reconciled. Each looked correct in isolation.

## Solution

### 1. Fix the broken advice

When a prompt's handler halts or redirects for a given state, any upstream prompt that advises the user to enter that state must either:
- (a) Reflect what actually happens: *"Final quality checks ran at the end of the last phase."*
- (b) Give a valid invocation: *"To re-run the final phase and its quality checks: `/cg-work phaseM`."*

Never advise a bare invocation that a prompt will immediately halt.

### 2. Add end-to-end journey contract tests

Beyond per-prompt format tests (see `2026-03-30-prompt-pipeline-contract-testing.md`), add Pester tests that verify the behavioral contract — when prompt A says "run X", X's handlers must accommodate the state implied.

Pattern: extract the advice from prompt A, extract the handler from prompt B, assert they are compatible.

```powershell
Describe "phased execution journey: cg-resume all-phases-complete advice is valid for cg-work" {
    $resumeFile = Join-Path $repoRoot ".github\prompts\cg-resume.prompt.md"
    $workFile   = Join-Path $repoRoot ".github\prompts\cg-work.prompt.md"
    $resumeStep2a = # ... extract step 2a block
    $workDispatch = # ... extract dispatch table section

    It "cg-resume all-phases-complete branch does not advise bare /cg-work (which halts)" {
        # The bare '/cg-work' suggestion was the broken journey — this ensures it stays fixed
        ($resumeStep2a -match 'Run `/cg-work` to proceed') | Should Be $false
    }

    It "cg-work halts when all phases are complete (Phased | none row)" {
        ($workDispatch -match 'All M phases are already complete.*halt') | Should Be $true
    }
}
```

The first assertion is a **negative** test — it guards against re-introducing the broken advice. The second asserts the halt behavior exists, so if the halt is ever removed the journey advice also needs revisiting (a reminder to cross-check).

### 3. Review rule: cross-check "next step" suggestions against target prompt guards

When writing or reviewing any prompt step that ends with "Run `/cg-X`" or "Next: `/cg-X argY`":
1. Find the handler in `/cg-X` that matches the implied state.
2. Verify that handler does NOT halt before completing the intended action.
3. If it does halt, either (a) fix the advice to reflect reality or (b) add a code path in `/cg-X` that handles the implied state correctly.

## Prevention

- **Review checklist**: When adding any "run `/cg-X`" suggestion to a prompt, always cross-check the target prompt's dispatch table for the state being implied.
- **Co-author negative test**: Any "do NOT suggest X in state S" behavior should have a `($content -match 'broken pattern') | Should Be $false` test, not just positive coverage.
- **Verify pass catches these**: The verify review mode (`/cg-review mode:verify`) caught P2.v1 because agents re-examine behavioral consistency. Run a verify pass after any multi-prompt feature.

## Related

- `2026-03-30-prompt-pipeline-contract-testing.md` — Data/format contract testing between chained prompts (complementary, not identical)
- `2026-04-13-prompt-interaction-branch-completeness.md` — All branches of a prompt interaction must be handled
- `2026-05-05-phased-plan-and-execution-thorough-verify-review.md` — The review where this was caught (P2.v1)
