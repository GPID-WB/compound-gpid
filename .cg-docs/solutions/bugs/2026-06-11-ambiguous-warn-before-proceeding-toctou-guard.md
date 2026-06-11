---
date: 2026-06-11
title: "Ambiguous 'warn before proceeding' in TOCTOU guard allows duplicate creation without user choice"
category: "bugs"
language: "both"
tags: [prompt-authoring, toctou, race-condition, duplicate-prevention, user-confirmation, cg-issues]
root-cause: "A prompt step that says 'warn the user before proceeding' is interpreted by the LLM as warn-then-continue, not warn-then-stop — the agent dispatches the write operation after displaying the warning without waiting for a user decision"
severity: "P2"
---

# Ambiguous "Warn Before Proceeding" in TOCTOU Guard Allows Duplicate Creation Without User Choice

## Problem

A `cg-issues.prompt.md` step included this TOCTOU guard:

> "If a second match is found, warn the user before proceeding. Dispatch `@cg-roadmap`
> with the **Attach GitHub Issue to Feature** operation using the captured data."

When a duplicate is detected (another collaborator created an issue between the
initial duplicate check and the `gh issue create` call), the LLM:

1. Displays: "Warning: a duplicate issue #42 was found for this feature."
2. Immediately proceeds to dispatch `@cg-roadmap Attach` — linking the NEW issue.
3. The project now has two GitHub issues linked to the same roadmap feature.

**"Warn before proceeding" is parsed as a sequence: warn, then proceed.** The guard
provides no actual protection — it just adds a status message before doing the
potentially corrupting action.

## Root Cause

"Warn before proceeding" is ambiguous in a sequential prompt execution context:
- The human author's intent: "warn AND STOP until the user makes an explicit choice"
- The LLM's execution: "emit warning text, then continue to the next instruction"

There is no syntactic difference between "warn and continue" and "warn then wait for
input" in prose. LLMs default to the sequential interpretation (continue), not the
interactive one (block).

This is a specific instance of the general "ambiguous confirmation" pattern: any
instruction where the agent should pause and wait for user input must explicitly
name the pause, enumerate the options, and explicitly forbid proceeding without
a response.

## Solution

Replace "warn before proceeding" with an explicit stop + enumerated choices:

**Before (ambiguous)**:
```
If a second match is found, warn the user before proceeding.
```

**After (unambiguous)**:
```
If a second match is found, stop immediately and present the user with three choices:
  (a) Delete the newly-created issue and link the existing one instead.
  (b) Proceed acknowledging the duplicate (two issues will be linked).
  (c) Abort — do nothing, leave roadmap.json unchanged.
Do NOT dispatch @cg-roadmap until the user responds.
```

Key elements of the fix:
- **"stop immediately"** — explicit halt, not implicit
- **Enumerated choices (a/b/c)** — forces the LLM to surface a decision tree
- **"Do NOT ... until the user responds"** — explicit prohibition on proceeding
- **Named the forbidden action** — "Do NOT dispatch @cg-roadmap" is more specific
  than "stop" alone

Applied in `.github/prompts/cg-issues.prompt.md` step 9 as part of the
2026-06-11 review cycle.

## Prevention

**Rule**: Any prompt step that should pause for user input at a risky decision point must:

1. Use "stop immediately" or "halt — do not proceed"
2. Enumerate the choices explicitly: (a) ..., (b) ..., (c) ...
3. Include a negative instruction naming the forbidden action:
   "Do NOT <dispatch/write/create/delete> until the user chooses"
4. Handle each choice with a concrete follow-on action

**Anti-pattern list**:
- "warn the user before proceeding" → **ambiguous** (warn + continue)
- "ask the user if they want to continue" → **ambiguous** (LLM may answer for the user)
- "confirm with the user" → **ambiguous** (LLM may auto-confirm)
- "present the options" → **ambiguous without** an explicit stop instruction

**Safe patterns**:
- "Stop. Present the user with three choices: ..."
- "Do NOT proceed until the user explicitly selects one of: ..."
- "Halt. Ask: [choice A / choice B / choice C]. Do not dispatch X until response received."

**Note**: This issue is distinct from confirmation at *creation time* (already requiring
"always ask for explicit confirmation before creating"). TOCTOU guards come *after*
creation — the issue already exists — so the user needs to decide what to do with
a potentially-duplicate artifact, not whether to create one.

## Related

- `.cg-docs/solutions/bugs/2026-03-19-persistent-state-written-before-validation-causes-corruption.md` — related: write-after-validate principle; this solution covers the detection/decision side when a race is actually detected
- `.cg-docs/solutions/bugs/2026-04-15-self-defeating-guardrail-exception-in-llm-prompts.md` — related: guardrail exceptions that can be invoked by the evidence they guard against
- `.cg-docs/solutions/bugs/2026-06-11-cli-injection-in-llm-driven-gh-prompts.md` — broader context; TOCTOU fix was P2.1 finding
- `.github/prompts/cg-issues.prompt.md` — fixed prompt (backfill step 9)
