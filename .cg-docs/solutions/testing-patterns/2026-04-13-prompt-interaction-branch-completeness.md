---
date: 2026-04-13
title: "Prompt interaction guards: all response branches must be explicitly handled"
category: "testing-patterns"
language: "both"
tags: [prompt-design, copilot, interaction, guard, branch-handling, cg-fix-triage, response-length]
root-cause: "A prompt's [yes/batch] interaction guard omitted the 'batch' branch handler — a rule-following model would ignore the unspecified branch and proceed, defeating the guard's purpose"
severity: "P2"
---

# Prompt Interaction Guards: All Response Branches Must Be Explicitly Handled

## Problem

`cg-fix-triage.prompt.md` gained a large-report guard: when more than 15 findings
are open, the prompt warns the user and waits for `[yes/batch]` before continuing.
The guard instruction ended with:

> "Proceed with all N anyway? [yes/batch]"
> Wait for the user's response before continuing.

The instruction documented the wait but not what to do when the user responds
`batch`. A rule-following model that receives `batch` has no instruction to follow,
so it may:
- Proceed as if the user said `yes` (ignore the unspecified branch)
- Display the batch commands but then continue triage anyway
- Stall with no further output

In all three cases, the guard fails silently — the very crash scenario (response
length overflow) that the guard was designed to prevent can still happen.

## Root Cause

Incomplete branch handling in prompt interaction guards. The prompt specified the
trigger condition and the wait, but left the `batch` response path implicit. Implicit
behavior is undefined behavior for a language model — it will fill in the gap, often
incorrectly.

General form of the bug:

```
# INCOMPLETE — only the wait is specified
> "Proceed? [yes/no]"
> Wait for the user's response before continuing.

# COMPLETE — both branches are explicitly handled
> "Proceed? [yes/no]"
> Wait for the user's response before continuing.
> If the user responds `no`: [explicit no-path action].
> If the user responds `yes`: [explicit yes-path action].
```

## Solution

Add an explicit handler for every non-default response branch immediately after
the wait instruction:

```markdown
**Large report notice**: If there are more than 15 open findings in scope and no
arguments were provided, warn the user before proceeding:
> "This report has N open findings. Fixing all at once may hit response length limits.
> Recommended: use priority batches — run `/cg-fix-triage P0 P1` first, then
> `/cg-fix-triage P2`, then `/cg-fix-triage P3`. Proceed with all N anyway? [yes/batch]"
> Wait for the user's response before continuing.
> If the user responds `batch`: display the three recommended commands
> (`/cg-fix-triage P0 P1`, `/cg-fix-triage P2`, `/cg-fix-triage P3`) and stop —
> do not proceed with triage.
```

The `batch` branch is now a hard stop with explicit output — the model has no ambiguity.

## Prevention

**Rule**: Every `[choice/choice]` interaction guard in a prompt must enumerate what
to do for **each** non-default choice, immediately after the wait line. Never leave
a response branch implicit.

**Design checklist for interaction guards**:
1. State the trigger condition clearly.
2. State the wait instruction.
3. For each non-default response option, add: "If the user responds `X`: [action]."
4. If a branch should STOP processing, say so explicitly: "stop — do not proceed."

**Test coverage rule**: Every guard clause in a prompt that can affect execution flow
should have at least one Pester test asserting its key text exists. This prevents
silent regression when the guard is edited or moved:

```powershell
It "warns the user when there are more than 15 open findings (large report guard)" {
    ($content -match '15 open|more than 15') | Should Be $true
}

It "recommends priority batches (P0 P1, P2, P3) in the large report warning" {
    ($content -match 'P0 P1.*P2.*P3|priority batch') | Should Be $true
}
```

## Related

- [prompt-pipeline-contract-testing.md](2026-03-30-prompt-pipeline-contract-testing.md) — Testing the interface contract between chained prompts
- [do-not-delegate-file-write-guardrail.md](../testing-patterns/2026-03-30-do-not-delegate-file-write-guardrail.md) — Another pattern where implicit behavior in prompt instructions causes silent failures
- [2026-06-03-three-layer-test-correctness-protocol-prevents-circular-tests-in-fixbug.md](2026-06-03-three-layer-test-correctness-protocol-prevents-circular-tests-in-fixbug.md) — Applied this rule to add the "test NOT failing" handler in /cg-fixbug Step 2 (P1.4)
