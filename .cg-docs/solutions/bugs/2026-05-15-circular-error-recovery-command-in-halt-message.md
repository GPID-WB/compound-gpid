---
date: 2026-05-15
title: "Circular error recovery: halt message suggests a command that itself requires the precondition that caused the halt"
category: "bugs"
language: "both"
tags: [prompt-design, agent-design, error-messages, ux, cg-wiki, pre-flight, bootstrap-trap]
root-cause: "A halt or error message suggests running command X as recovery, but X itself has the same precondition (e.g., _wiki.yml must exist) that caused the original halt. The user follows the advice, hits the identical error, and has no forward path."
severity: "P2"
---

# Circular Error Recovery: Halt Message Suggests a Command That Itself Requires the Same Missing Precondition

## Problem

`@cg-wiki` halts in Pre-Flight when `_wiki.yml` is absent:
```
Wiki manifest not found at wiki/_wiki.yml. Run `/cg-setup` or `/cg-wiki rebuild` to initialize.
```

But `rebuild` mode is dispatched through `@cg-wiki` — which runs the **same
Pre-Flight** and halts on the identical check. Following the suggested recovery:

1. User runs `/cg-wiki rebuild`
2. Pre-Flight: `_wiki.yml` not found → halt with the same message
3. User is stuck in an infinite loop with no forward path

The same pattern appeared in `cg-wiki.prompt.md` Step 2 (fixed as P3.7 in the
original review) and survived undetected in the **agent's own Pre-Flight halt
message** — found only by the subsequent verify pass (P2.1 in verify review).

## Root Cause

When writing recovery suggestions in error messages, the author knows the
context — `_wiki.yml` is missing — and reasons about which command creates the
manifest. `rebuild` sounds correct ("it rebuilds the wiki") but the command
name is misleading; it regenerates wiki pages from an existing manifest, it does
not bootstrap a manifest from scratch. That is `init` mode, triggered via
`/cg-setup`.

The bug recurred across prompt and agent because the check was fixed locally
in the prompt's user-facing error message without searching for the same pattern
in the agent's Pre-Flight message. Since prompt and agent are separate files,
the inconsistency survived code review and only surfaced during the verify pass.

## Solution

### Immediate Fix

```markdown
# Before (circular)
Wiki manifest not found at wiki/_wiki.yml.
Run `/cg-setup` or `/cg-wiki rebuild` to initialize.

# After (correct — current state)
Wiki manifest not found at wiki/_wiki.yml.
Run `/cg-wiki init` to initialize the wiki for this project.
```

> **2026-05-15 update**: The original fix pointed users to `/cg-setup`, which solved the infinite loop but required full re-setup. A follow-on fix (`2026-05-15-cg-wiki-no-user-facing-init-path-for-existing-projects.md`) added `/cg-wiki init` as a direct user-facing subcommand and updated all recovery messages accordingly.

### Design Rule: Verify Recovery Commands Before Writing Them

Before writing a recovery suggestion in any halt or error message:

1. **Can this command succeed without the precondition?** If the precondition
   is `_wiki.yml` must exist, ask: does the suggested command need `_wiki.yml`?
2. **Does the command name accurately describe what it does?** `rebuild` sounds
   like it creates from scratch but it only regenerates from an existing manifest.
3. **Search for sibling messages**: if a prompt and its agent both handle the
   same error condition, audit both when fixing either one.

### Cross-File Audit Rule

When a review finds a circular recovery message in a prompt, immediately search
the dispatched agent's Pre-Flight and error messages for the same pattern. The
prompt and agent often produce the same error under different execution paths.

## Prevention

- Write error messages as: "X failed because Y is missing. To create Y, run Z."
  Then verify Z doesn't also require Y.
- For wiki-class agents: `init` mode (triggered by `/cg-setup` or directly via
  `/cg-wiki init`) creates `_wiki.yml`. All other modes require it. When the
  manifest is absent, suggest `/cg-wiki init` as recovery — never `rebuild`,
  `update`, or `convert`.
- Add a Pester test that checks the Pre-Flight halt message does not contain
  `rebuild` in the "manifest not found" branch.

## Related

- `.cg-docs/solutions/bugs/2026-04-15-self-defeating-guardrail-exception-in-llm-prompts.md` — related pattern: a guard whose exception clause defeats the guard's purpose
- `.cg-docs/solutions/testing-patterns/2026-04-23-verify-mode-suppression-must-be-anchored-to-fixed-finding-scope.md` — verify pass design to catch survivors like this one
