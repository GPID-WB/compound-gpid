---
date: 2026-04-15
title: "Per-step test failure handling in /cg-work"
status: completed
completed-date: 2026-04-15
scope: Lightweight
language: "both"
estimated-effort: small
tags: [quality-loop, cg-work, testing, prompt-engineering]
---

# Plan: Per-step test failure handling in /cg-work

## Objective

Add a structured failure path to `/cg-work` Step 2.4 so that when functional tests (testthat, pytest, Pester) fail after a plan step, the agent makes up to 2 targeted fix attempts before notifying the user and moving on — mirroring the 2-round pattern already established by Step 4.1's diagnostic layer.

## Context

Today, Step 2.4 says "run tests after each step" but has no defined behavior when tests fail. The agent improvises — sometimes looping endlessly, sometimes silently skipping. Step 4.1 already has a clean pattern for diagnostic failures: dispatch `@cg-fix-problems` with a 2-round budget, then surface remaining errors. We want the same bounded-retry + notify-and-continue pattern for test failures, but **inline** (no agent dispatch — the `/cg-work` agent fixes the code itself).

The two failure paths must remain separate:
- **Diagnostic failures** (Step 4.1): `get_errors` errors → `@cg-fix-problems` agent → 2 rounds
- **Test failures** (Step 2.4): functional test runner fails → inline fix attempts → 2 rounds

Step 4.1 already contains a guard for the intersection case: "If `get_errors` returns clean but tests still fail — the failure is semantic, not diagnostic." That guard needs a small tweak: if the Test Failure Recovery block already notified the user about exhausted attempts, Step 4.1 sub-item 5 should skip its own notification to avoid double-surfacing the same failure.

## Requirements

| ID  | Requirement                          | Source           |
|-----|--------------------------------------|------------------|
| R1  | After running tests in Step 2.4, if any fail, make up to 2 inline fix attempts targeting the failing tests | user |
| R2  | If tests still failing after 2 attempts, notify the user with count and continue to next step | user |
| R3  | If tests pass at any point (original run or after a fix attempt), continue normally | user |
| R4  | Scope is functional tests only (testthat, pytest, Pester) — not diagnostic errors | user |
| R5  | The diagnostic failure path in Step 4.1 remains separate; only add a skip-guard to sub-item 5 to avoid double-notification | user |
| R6  | After a fix attempt resolves targeted failures, run the full test suite before declaring success (catch regressions) | review |
| R7  | Notification template must include failing test names and last error excerpt, not just a count | review |

## Implementation Steps

### 1. Add test failure sub-step to Step 2.4 in cg-work.prompt.md

- **Requirements**: R1, R2, R3, R4, R5, R6, R7
- **Files**: `.github/prompts/cg-work.prompt.md`
- **Details**:
  Expand item 4 of Step 2 in-place. After the current text "Run both the discovered existing tests AND the new tests to verify nothing regressed," add a **Test Failure Recovery** block (no separate step number — it stays inline within Step 2 item 4):

  ```
  **Test Failure Recovery** (functional tests only — not the `get_errors` diagnostic layer):
  If any tests fail:
  1. Analyse the failure output. Make a targeted fix to the code under test — do not
     weaken or remove test assertions. (Exception: if this plan step explicitly changed
     a function's interface or return type, updating tests to match the new interface
     is correct.) Re-run the tests.
  2. If tests still fail, make one more targeted fix attempt and re-run.
  3. If the targeted failures are resolved, re-run the **full test suite** for all
     modules touched by this step to catch regressions introduced by the fix.
     If the full suite passes, continue normally.
  4. If tests are still failing after 2 fix attempts:
     > "**N test(s) still failing after 2 fix attempts** — continuing to next step.
     > Review before merging.
     > Failing tests:
     > • `<test-file>::<test-name>` — `<last error message>`
     > • ..."
     Continue to the next plan step.

  Do NOT dispatch `@cg-fix-problems` for test failures — that agent handles
  diagnostic errors only (Step 4.1).
  ```

  Additionally, add a skip-guard to Auto-Fix Diagnostics sub-item 5: if the Test Failure Recovery block already notified the user about exhausted test fix attempts in this step, skip the "Tests are still failing but no diagnostic errors" surface to avoid double-notification.

  Key phrasing decisions:
  - "do not weaken or remove test assertions" + interface-change exception — prevents weakening while allowing legitimate test updates.
  - Full-suite re-run after targeted fixes pass — catches regressions from fix attempts.
  - Notification includes test names and error excerpts — gives the user a starting point.
  - No separate step number — avoids structural inconsistency with Step 2 / Step 4.1 numbering.
  - Explicit separation from Step 4.1 + double-notification guard.

- **Test Scenarios**:
  - ✅ Happy path: tests pass on first run → no recovery needed
  - ✅ Fix on first attempt: tests fail, fix #1 works, full suite passes → continue normally
  - ✅ Fix on second attempt: tests fail, fix #1 fails, fix #2 works, full suite passes → continue normally
  - 🛑 Edge case: tests still failing after 2 attempts → notify with names/errors and move on
  - 🛑 Edge case: fix attempt resolves targeted failures but introduces new regressions → caught by full-suite re-run
  - ❌ Error path: agent must not weaken test assertions instead of fixing code (unless plan step changed the interface)
  - ❌ Error path: Step 4.1 sub-item 5 must not double-notify when test recovery already exhausted
- **Tests**: Add Pester tests in `prompt-tools.Tests.ps1` verifying:
  1. The "2 fix attempts" phrase exists in cg-work.prompt.md
  2. The user notification template ("still failing after 2 fix attempts") exists
  3. The separation from `@cg-fix-problems` is explicitly stated
  4. Anti-weakening guard phrasing exists ("not weaken" or "not the test")
  5. Full-suite regression check after targeted fixes phrasing exists
  6. Double-notification skip-guard for Step 4.1 sub-item 5 exists
- **Acceptance criteria**: Step 2.4 contains a bounded retry block with explicit user notification on exhaustion, and it is clearly scoped to functional tests only.

### 2. Add Pester tests for the new sub-step

- **Requirements**: R1, R2, R3, R4
- **Files**: `tests/prompt-tools.Tests.ps1`
- **Details**: Add a new `Describe "cg-work.prompt.md - test failure recovery"` block with named `It` assertions, following the existing convention in the file (e.g., `Describe "cg-work.prompt.md - auto-dispatch @cg-fix-problems"`).
- **Tests**: The test block itself.
- **Acceptance criteria**: Tests pass when run with `Invoke-Pester tests\prompt-tools.Tests.ps1 -Quiet`.

## Testing Strategy

Structural Pester tests only — we verify the prompt file contains the required phrases. No runtime behavioral testing is possible for prompt files.

## Documentation Checklist

- [x] Function documentation — N/A (prompt file, not code)
- [ ] README updates — not needed
- [ ] Inline comments for complex logic — the prompt text is self-documenting
- [ ] Usage examples — the notification template serves as the example

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Agent weakens test assertions instead of fixing code | "Do not weaken or remove test assertions" instruction with interface-change exception |
| Agent loops beyond 2 attempts | Explicit "2 fix attempts" hard cap with move-on instruction |
| Fix attempt resolves targeted failures but introduces regressions | Full-suite re-run required before declaring success |
| Double-notification for same failure (test recovery + Step 4.1 sub-item 5) | Skip-guard in Step 4.1: if test recovery already notified, skip semantic-failure surface |

## Out of Scope

- Changes to the `@cg-fix-problems` agent definition (the skip-guard is in the prompt, not the agent)
- Changes to test runners or test infrastructure
- Retry logic for non-functional concerns (linting, formatting)
- Any prompt file other than `cg-work.prompt.md`
