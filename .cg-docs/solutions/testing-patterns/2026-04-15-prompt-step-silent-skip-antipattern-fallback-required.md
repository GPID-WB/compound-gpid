---
date: 2026-04-15
title: "Prompt step silent-skip anti-pattern: always provide fallback with candidates when primary key lookup fails"
category: "testing-patterns"
language: "both"
tags: [prompt-design, cg-work, step-3-7, silent-skip, fallback, recovery-path, roadmap, workflow]
root-cause: "A prompt step that emits only a soft warning and exits when its primary lookup fails provides no recovery path — the failure is invisible and the user has no actionable information"
severity: "P2"
---

# Prompt Step Silent-Skip Anti-Pattern

## Problem

`/cg-work` Step 3.7 ("Update Roadmap Status") matched features by `plan` path.
When no features matched (because they had `plan: null`), it printed:

> "No matching feature found in `roadmap.json`. Verify the plan path is linked
> with `@cg-roadmap`."

…and silently exited. The user saw this message buried in a long completion
sequence and moved on. The roadmap was never updated. The same plan could fail
to update the roadmap every time it was re-run with the same setup.

**The warning message was technically correct but completely useless.** It told
the user *what to do* (`@cg-roadmap`) but not *which features to update*, in what
*milestone*, or *why* the link was missing. And it provided no inline recovery path.

## Root Cause

The step was designed around the happy path (linked features) and treated the
no-match case as an exceptional edge to warn about and skip. This is the
**silent-skip anti-pattern**:

1. Primary lookup fails
2. Emit one-line warning
3. Exit step
4. User moves on without fixing anything

The warning requires the user to:
- Remember the warning after the session ends
- Open `roadmap.json` manually
- Find the right feature IDs
- Run `@cg-roadmap` with the correct arguments

That's four context-switches after a long session. In practice it never happens.

## Solution

When a prompt step's primary lookup (by key, path, or ID) fails, it should:

1. **Attempt a secondary search** — scan by title, keyword, or content similarity
2. **Surface candidates** — present the user with a ranked list of probable matches
3. **Ask for confirmation** — let the user confirm which candidates are correct
4. **Execute the action** — proceed with the confirmed matches
5. **Only then** emit the soft warning if zero candidates were found

The fix to Step 3.7:

```
2a. Title-search fallback:
    - Read the plan document
    - Scan all features in roadmap.json with plan: null
    - For each feature whose title appears in the plan's requirement list: collect as candidate
    - Present candidates and ask the user to confirm
    - Dispatch @cg-roadmap for confirmed features
    - Only emit soft warning if no candidates found
```

This turns an invisible failure into an interactive recovery step that completes
in ~10 seconds.

## Prevention

### Design rule for prompt steps that search for a target

Before writing any prompt step that uses a lookup (by path, ID, name, etc.):

- **Ask**: "What happens when the lookup returns zero results?"
- **If the step must do something** (update state, dispatch an agent, write a file):
  a fallback search + confirmation is **required**
- **If the step is advisory-only** (generating a suggestion, summarizing): a soft
  warning may be acceptable
- **Never combine**: "must do something" + "soft warning + exit" — this is the anti-pattern

### Test pattern: assert fallback behavior exists

```powershell
It "Step X searches by title when primary key lookup returns nothing" {
    ($content -match 'title.*plan content|scan.*title|feature.*title.*appear') | Should Be $true
}
It "Step X prompts user to confirm fallback candidates" {
    ($content -match 'confirm.*which|ask.*user.*confirm') | Should Be $true
}
```

These tests guard against regression — if someone removes the fallback, the
tests catch it immediately.

### Checklist for prompt steps with a lookup

- [ ] Primary lookup defined (e.g., match by plan path)
- [ ] Secondary/fallback defined (e.g., scan by feature title in plan content)
- [ ] Fallback surfaces candidates to the user (not just a warning)
- [ ] User confirmation before writing any state changes
- [ ] Soft warning only fires when fallback also returns zero candidates
- [ ] Tests assert both the fallback search behavior and the confirmation prompt

## Related

- [2026-04-15 — cg-work Step 3.7 silently skips plan:null features](../bugs/2026-04-15-cg-work-step-3-7-silent-skip-plan-null-features.md)
- [2026-04-15 — Roadmap plan linkage must be audited at completion](./2026-04-15-roadmap-plan-linkage-must-be-audited-at-completion.md)
- [2026-04-13 — Dead step after user-wait is a session terminator](./2026-04-13-dead-step-after-wait-prompt-session-terminator.md)
