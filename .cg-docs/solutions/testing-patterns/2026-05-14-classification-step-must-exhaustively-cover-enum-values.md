---
date: 2026-05-14
title: "Classification steps must exhaustively cover all enum values with terminal actions"
category: "testing-patterns"
language: "both"
tags: [prompt-design, classification, enum-exhaustion, guard-conditions, edge-cases, cg-verify-pr]
root-cause: "A classification step lacked a terminal action for an all-CANCELLED scenario, causing silent fall-through into a fix loop with zero failing checks"
severity: "P2"
---

# Classification steps must exhaustively cover all enum values with terminal actions

## Problem

A prompt step that classifies input into one of N categories must provide a
terminal action (halt or proceed) for every possible combination of input values.
When a value or combination is missing, control falls through to the next step
with invalid state.

**Example from this session**: `cg-verify-pr` Step 2 classified CI check conclusions
into: All passing (SUCCESS/NEUTRAL/SKIPPED) | Pending | Manual action required
(ACTION_REQUIRED/STALE) | Cancelled (non-blocking) | Failing (FAILURE/TIMED_OUT).

The "Cancelled" rule said "treat as non-blocking, note in classification" — but had
no terminal action. The "Failing" rule fired only when `FAILURE`/`TIMED_OUT` was
present. If every check returned `CANCELLED`, no rule produced a clean exit: the
prompt fell through to Step 3 ("Fetch and classify failure logs") with zero failing
checks to diagnose.

Discovered as P2.1 in the verify pass.

## Root Cause

Classification tables are built incrementally. Initial cases cover the happy path
(success, failure) and obvious guards (pending, manual-action). Edge-case
combinations — all-CANCELLED, all-SKIPPED, mixed-CANCELLED-and-NEUTRAL — are
added as afterthoughts or not at all.

The "all non-failing" combinations are particularly prone to this gap because they
are neither clean successes nor actionable failures.

## Solution

### Design rule

For every classification step, enumerate the complete set of conclusion/status
values and verify each one maps to exactly one terminal action:

```
SUCCESS  → All passing (halt with "✅")
NEUTRAL  → All passing
SKIPPED  → All passing (treat as non-blocking pass)
PENDING  → Pending (halt with "⏳")
CANCELLED → Non-blocking (exclude from fix) → if remaining are non-failing: "✅ Nothing to fix"
ACTION_REQUIRED → Manual action (halt)
STALE    → Manual action (halt)
FAILURE  → Failing (proceed to fix)
TIMED_OUT → Failing (proceed to fix)
```

Add an explicit "all non-failing" case that merges non-standard non-failures
(CANCELLED, SKIPPED, NEUTRAL, SUCCESS) into a clean halt:

```markdown
- **All non-failing** (all checks are `CANCELLED`, `SKIPPED`, `NEUTRAL`, or `SUCCESS`
  after excluding `FAILURE`/`TIMED_OUT`):
  > "✅ No failing checks. Nothing to fix."
  Halt.
- **Failing**: at least one check has `conclusion: FAILURE` or `conclusion: TIMED_OUT`.
  Proceed to Step 3.
```

### Ordering rule

Place the "all non-failing" case *after* the per-value non-blocking rules and
*before* the Failing case. This ensures: (1) non-standard values are explicitly
acknowledged, (2) the failing case is a clean default for actionable items only.

### Test signal

```powershell
# Verify each non-standard conclusion value appears in the prompt
foreach ($val in @('SKIPPED', 'CANCELLED', 'ACTION_REQUIRED', 'STALE')) {
    It "handles $val conclusion explicitly (P1.7)" {
        ($content -match $val) | Should -Be $true
    }
}
```

## Prevention

- After implementing any classification step: draw an exhaustive enum table and
  verify each value appears in the prompt text.
- For CI-status classification steps specifically, include all GitHub Check
  conclusion values: `SUCCESS`, `FAILURE`, `NEUTRAL`, `CANCELLED`, `SKIPPED`,
  `TIMED_OUT`, `ACTION_REQUIRED`, `STALE`, and the special `null` (pending).
- Prefer "all non-failing" as a catch-all terminal case over individual per-value
  halts — it is future-proof if GitHub adds new conclusion values.

## Related

- `.cg-docs/solutions/testing-patterns/2026-04-13-prompt-interaction-branch-completeness.md`
- `.cg-docs/solutions/testing-patterns/2026-04-15-new-validation-branch-requires-dedicated-test.md`
- `.cg-docs/solutions/testing-patterns/2026-04-15-prompt-step-silent-skip-antipattern-fallback-required.md`
