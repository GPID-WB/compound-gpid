---
date: 2026-06-01
title: "Test-correctness assessment for /cg-fixbug and /cg-work"
status: decided
scope: "Standard"
chosen-approach: "Three-change package: red-phase gate, diagnostic fork, mutation verification"
tags: [testing, test-integrity, cg-fixbug, cg-work, red-green-refactor, mutation-testing]
---

# Test-Correctness Assessment for /cg-fixbug and /cg-work

## Context

When an AI agent writes a feature and its tests in the same step, both artifacts
are derived from the same mental model. If that model is wrong, both the code and
the test will be wrong together — and the test passes for the wrong reasons. This
is a correlated failure: the test was never proven to be sensitive to failure
because it was never red.

Two manifestations:
1. During feature development: tests written alongside implementation, never
   confirmed to fail first. A bug in feature logic is silently mirrored in the test.
2. During bug fixing: a bug surfaces but the existing test did not catch it. The
   agent doesn't know whether to look at the test or the feature first.

The charter's "Current Focus" explicitly lists "smarter test-awareness in /cg-fixbug"
and the roadmap tracks this as idea `fixbug-test-correctness-assessment`.

## Requirements

- The agent must confirm tests are sensitive to failure (red phase) before trusting them.
- During bug fixing, the agent must distinguish between "test is incomplete" and
  "test codifies the bug" when an existing test passes on buggy code.
- High-stakes statistical functions (welfare, FGT, weights) need stronger verification.
- All diagnostic output must be readable by non-technical economists.
- No hard stops in `/cg-work` (flow prompt) — only in `/cg-fixbug` (interactive prompt).
- No schema migrations (no `tests:` field in plan structure).
- Must not conflict with existing two-round recovery loop in `/cg-work`.

## Approaches Considered

### Approach 1: Three-change package (chosen)

Implement all three changes as a coordinated set:

**Change 1 — Red-phase gate in `/cg-work`** (preventive):
- Conditional pre-step before implementation, NOT a hard stop.
- Triggers when a step introduces new testable behavior (function creation, return
  value changes, data transformation logic).
- Agent writes test, runs it, confirms failure, logs result, then implements.
- Escape hatch: if agent cannot determine what to test, logs "Could not establish
  failing baseline" and proceeds. Flags for `@cg-testing`.
- Structural/prompt/config steps skip this pre-step entirely.

**Change 2 — Diagnostic fork in `/cg-fixbug` Step 2** (reactive):
- Before writing a reproduction test, search for existing tests covering the function.
- If existing test FAILS on buggy code → trustworthy, use as reproduction test.
- If existing test PASSES on buggy code → sub-diagnostic:
  - Does test exercise the SAME INPUT that triggers the bug?
    - YES → test codifies the bug (asserts wrong expected value). Write new correct
      reproduction test. Defer repair of flawed test to Step 4 (after fix confirmed).
    - NO → test is incomplete (doesn't cover this path). Write new reproduction test.
      Existing test is fine — leave it alone.
- If no existing test → write new failing test (current behavior, unchanged).

**Change 3 — Mutation verification reference** (detective):
- Add `references/test-integrity.md` to `cg-skill-r-testing`.
- Protocol: introduce deliberate error → test must fail → revert → test must pass.
- P2 (recommended) by default; auto-escalates to P1 for welfare/FGT/weights functions.
- Triggered by `/cg-fixbug` completion, not by `@cg-testing` reviews.
- Tautological test detection: passive note for human reviewers, not automated finding.

**Pros:**
- Covers all three lifecycle moments: prevention, reaction, detection.
- No schema migrations, no new agents, no new tools.
- Each change is self-contained (~15-20 lines of prompt text each).
- Aligns with charter constraints (fail loudly, document after confirmation).

**Cons:**
- Three files to modify/create in a single implementation.
- Red-phase gate adds execution time to `/cg-work` steps.
- Mutation verification adds friction for economists (scoped to high-stakes functions to mitigate).

**Effort:** Medium (2-3 days)
**Recommended?** Yes

### Approach 2: Change 2 only (minimal)

Implement only the diagnostic fork in `/cg-fixbug`. Skip the preventive and
detective measures.

**Pros:**
- Smallest scope. Ships in a day.
- Addresses the acute problem (bug-fixing with suspect tests) immediately.
- No changes to `/cg-work` flow.

**Cons:**
- Does nothing to prevent correlated failures during feature development.
- No mechanism to verify test sensitivity after the fact.
- Leaves the "Current Focus" item partially addressed.

**Effort:** Small (1 day)
**Recommended?** No — insufficient for the stated goal.

### Approach 3: Full TDD enforcement

Make red-phase gates hard stops in BOTH `/cg-work` and `/cg-fixbug`. Require
mutation verification for all functions, not just statistical ones.

**Pros:**
- Maximum protection against correlated failures.
- Every test is proven sensitive before implementation proceeds.

**Cons:**
- Hard stops in `/cg-work` break flow (see context.md: "steps after wait are dead code").
- Mutation verification for ALL functions is disproportionate friction.
- Economists would abandon the workflow if every step requires manual confirmation.

**Effort:** Large (5+ days, plus workflow redesign)
**Recommended?** No — over-engineering that conflicts with existing architecture.

## Decision

**Approach 1: Three-change package.** All three changes address different lifecycle
moments and are self-contained. Each is ~15-20 lines of prompt text. No schema
migrations, no new agents, no conflicts with existing infrastructure.

Key design decisions:
- `/cg-work` red-phase is a soft checkpoint with escape hatch, not a hard stop.
- `/cg-fixbug` diagnostic fork distinguishes "incomplete" from "codifies bug."
- Mutation verification is scoped to high-stakes functions and triggered post-fix.
- Flawed test repair happens in Step 4 (after fix confirmed), not Step 2.
- Audit trail: bug documents record `red-phase-confirmed: "yes"` and step summaries
  log "Baseline failure confirmed: [test name] → [error message]."

## Next Steps

1. Modify `/cg-fixbug` Step 2 to add the diagnostic fork (Change 2).
2. Read `/cg-work` to understand current Step 2 structure, then add conditional
   red-phase pre-step (Change 1).
3. Create `references/test-integrity.md` in `cg-skill-r-testing` (Change 3).
4. Add `red-phase-confirmed` field to the bug document schema in `/cg-fixbug` Step 5.
5. Write Pester tests for the new prompt text in Changes 1 and 2.
6. Update roadmap feature `fixbug-test-correctness-assessment` status from `idea` to `in-progress`.
