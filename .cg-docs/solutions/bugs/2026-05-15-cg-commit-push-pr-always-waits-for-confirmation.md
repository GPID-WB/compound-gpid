---
date: 2026-05-15
title: "cg-commit-push-pr always paused for user confirmation — no auto-proceed mode"
category: "bugs"
language: "both"
tags: [cg-commit-push-pr, ux, confirmation, interactive, flag, default-behavior, prompts]
root-cause: "Steps 2.3 and 3.3 contained unconditional 'wait for user' instructions with no bypass mechanism"
severity: "P3"
test-written: yes
fix-confirmed: yes
---

# cg-commit-push-pr always paused for user confirmation — no auto-proceed mode

## Problem

`/cg-commit-push-pr` always halted twice mid-execution:

1. **Step 2.3** — after proposing the commit grouping: "Wait for user confirmation or adjustments before continuing."
2. **Step 3.3** — after generating commit messages: "Present all messages together for review before any `git commit` is run."

There was no way to run the command non-interactively. Even routine, unambiguous commits required two interactive round-trips before any `git commit` was issued.

## Root Cause

Both pause points were unconditional prose instructions — they had no flag guard or condition. The prompt had no flag mechanism at all.

## Solution

Added a `--ask` flag (aliased `--wait`) with a `## Flags` section documenting it:

```markdown
## Flags

- **`--ask`** (or **`--wait`**): Enable interactive confirmation mode. When set, pause after
  proposing the commit structure (Step 2) and after generating commit messages (Step 3) to wait
  for user approval before proceeding. **Default (no flag): auto-proceed without confirmation** —
  classify, generate messages, commit, push, and open the PR in one uninterrupted pass.
```

Step 2.3 changed to:

```markdown
- **If `--ask` (or `--wait`) was passed**: wait for user confirmation or adjustments before
  continuing. **Otherwise (default): auto-proceed** to Step 3 with the proposed grouping.
```

Step 3.3 changed to:

```markdown
3. **If `--ask` (or `--wait`) was passed**: present all messages together and wait for user
   approval before any `git commit` is run. **Otherwise (default): auto-proceed** to Step 4
   immediately after generating the messages.
```

## Tests

Two regression tests added to `tests/prompt-tools.Tests.ps1` in the `cg-commit-push-pr.prompt.md - structure` Describe block:

```powershell
It "supports --ask flag to enable interactive confirmation mode (default is auto-proceed)" {
    ($content -match '--ask|--wait') | Should -Be $true
}

It "states default mode proceeds without confirmation unless --ask is set" {
    ($content -match 'auto.proceed|without.*confirm|unless.*--ask|by default.*proceed|--ask.*confirm') | Should -Be $true
}
```

Both tests confirmed failing before fix, passing (963/963) after fix.

## Prevention

- Default behaviour of agent-driven prompts should be **non-interactive** (auto-proceed).
- Interactive confirmation should be opt-in via an explicit flag.
- Any prompt with a "wait for user" step should expose a `--ask`/`--no-ask` flag pattern.
- Write Pester tests asserting the flag's presence whenever adding a new confirmation step.

## Related

- [cg-brainstorm branch offer asked too late](./../bugs/2026-05-01-cg-brainstorm-branch-offer-asked-too-late.md) — related UX theme: unnecessary interactive pauses in workflow prompts
