---
date: 2026-06-03
title: "Three-layer test-correctness protocol prevents circular tests in /cg-fixbug"
category: "testing-patterns"
language: "both"
tags: [fixbug, red-green-proof, expected-behavior-source, test-gap-taxonomy, circular-test, tautological-test, cg-fixbug, test-correctness]
root-cause: "No mechanism existed to declare where correct behavior comes from, classify why a test missed a bug, or prove both red-phase and green-phase — allowing tests to be derived from the buggy implementation itself"
severity: "P1"
---

# Three-Layer Test-Correctness Protocol Prevents Circular Tests in /cg-fixbug

## Problem

A `/cg-fixbug` session could produce a "passing" test that provides zero regression protection.
The test was written after the bug was understood, so the agent could:

1. **Derive the expected value from the implementation being fixed** ("circular test") — run the
   buggy code, observe its output, hard-code that output as the expected value. Test goes green
   immediately with no fix required.
2. **Use an existing test that never failed** — the agent verifies a test "passes after the fix"
   without first confirming it failed against the buggy code. The test was always passing; it
   detects nothing.
3. **Classify the test gap incorrectly** — write a new test targeting the wrong layer
   (e.g., unit test for a bug that only appears under component interaction → fixture-gap, not
   logic-gap), producing a test that passes vacuously.

None of these cases triggered the hard-stop gates in Steps 2 or 4, because there was no required
declaration of the correctness source and no taxonomy for why the existing test missed the bug.

## Root Cause

The workflow had two hard stops (Step 2: reproduce → HARD STOP; Step 4: fix → HARD STOP) but no
mechanism to validate the quality of the test before entering the hard stops:

- **No source declaration**: The agent could infer "expected behavior" from any source, including
  the buggy implementation itself.
- **No gap classification**: When an existing test failed to detect the bug, the agent had no
  taxonomy to classify *why*, leading to tests that targeted the wrong failure mode.
- **Red-phase was underdefined**: "The test must fail" did not require that the failure *matches
  the bug symptom* — a test failing for an unrelated reason could satisfy the gate.
- **Missing response branch**: The hard stop awaited `'confirmed failing'` but had no handler for
  `'test passed / did not fail'`, leaving the agent without instructions when the user reported
  the test wasn't actually catching the bug.

## Solution

Three new protocol layers were inserted into `/cg-fixbug`:

### Layer 1 — Step 1.5: Expected Behavior Source (MANDATORY)

Before writing any test, the agent must declare where the expected value comes from.
Seven source types in priority order:

| Priority | Source |
|---|---|
| 1 | User requirement |
| 2 | Documentation |
| 3 | Mathematical/statistical definition |
| 4 | External reference (methodology note, paper, specification) |
| 5 | Package convention (upstream API guarantee) |
| 6 | Hand-computed example (known input → known output) |
| 7 | Backward-compatibility contract |

The implementation cannot appear as a source. If no source can be identified, the agent must ask
the user before proceeding.

MANDATORY = agent-enforced gate (no user confirmation needed). HARD STOP = user-confirmed gate.
This step is MANDATORY, not a HARD STOP.

### Layer 2 — Step 2.5: Test Gap Classification

When an existing test exists but failed to detect the bug, the agent classifies *why* using an
8-category taxonomy:

| Category | Meaning |
|---|---|
| `missing-test` | No test covered this path |
| `wrong-test` | Test existed but expected values were wrong |
| `circular-test` | Expected value derived from the implementation being tested |
| `fixture-gap` | Test data lacked the case that triggers the bug |
| `edge-case-gap` | Boundary/corner case not represented in fixtures |
| `wrong-layer` | Test at wrong level (unit vs integration) |
| `ambiguous-spec` | Expected behavior was genuinely unclear |
| `integration-gap` | Bug only appears under component interaction |

> `circular-test` is a subcategory of `wrong-test`. Prefer `circular-test` when the root cause
> is the derivation method. Use `wrong-test` when expected values are wrong for other reasons.

For detection signals for each category, see
`cg-skill-r-testing/references/test-integrity.md — Test Gap Taxonomy`.

### Layer 3 — Step 4: Red-Green Proof (6-step)

The existing Step 4 gate was expanded from an underdefined "test must fail" to a 6-step proof:

1. Write the failing test (from the Layer 1 source)
2. Confirm red phase — test fails against buggy code
3. Confirm failure matches symptom — the failure message matches the bug description (not an
   unrelated error)
4. Implement the fix
5. Confirm green phase — test passes after fix
6. Confirm no regressions — full suite still passes

Sub-points 1–5 of Step 4 correspond to steps 2–6 of the Red-Green Verification Protocol in
`test-integrity.md` (step 1 — write the test first — happens at Step 2, before Step 4).

### Supporting Infrastructure

- **`test-integrity.md`** — reference file at
  `cg-skill-r-testing/references/test-integrity.md` covering all three layers with detection
  signals, examples, and cross-references back to `/cg-fixbug` steps. Language-neutral (R,
  Python, Stata examples).
- **Missing branch handler**: Step 2 HARD STOP now has an explicit handler for "test is NOT
  failing" — directs the agent to return to the pre-check, revise the test, and re-confirm.
- **Test runner escape hatch**: If the test runner is unavailable (CLM restriction, locked
  environment), the agent logs the unavailability and proceeds to write a new test from the
  Step 1.5 source.

### Red-Phase Gate in /cg-work

A companion gate was added to `/cg-work` Step 2's implementation phase:

```
Red-phase verification (conditional — skip if this step is purely structural with **no Pester
test file asserting against the modified content**: config files, markdown documentation, or
YAML frontmatter — or directory scaffolding)
```

The qualifier "no Pester test file asserting against the modified content" applies to **all**
exempt categories (not just YAML frontmatter). See V-P2.1 in the verify review for the grammar
precision lesson.

## Prevention

**Always apply in this order:**

1. Declare the source (Layer 1) before touching any test code
2. Classify the gap (Layer 2) before writing a new test — this tells you what kind of test to
   write
3. Execute the 6-step proof (Layer 3) — never accept "it passes" without first seeing it fail,
   and never accept "it fails" without verifying the failure message matches the bug

**Anti-patterns to avoid:**

- Running the buggy implementation to obtain the expected value → this is `circular-test`
- Using an existing test without first running it against the buggy code → may never have been failing
- Treating "test fails" as sufficient — always check the failure message matches the symptom
- Writing a unit test for a bug that only appears under component interaction → `integration-gap`,
  needs an integration test

**Grammar precision in skip-condition lists:**

When a qualifier ("with no X") is meant to apply to multiple items in a list, place it in a
single clause before or around the list — do not trail it after the last item. Trailing qualifiers
attach only to the nearest noun. Bad: "A, B, or C with no X". Good: "only when no X: A, B, or C."

## Related

- `cg-skill-r-testing/references/test-integrity.md` — full reference for all three layers
- `2026-04-13-prompt-interaction-branch-completeness.md` — every interaction gate needs handlers for all response branches (motivated P1.4)
- `2026-05-01-fix-triage-prompt-changes-need-co-authored-tests.md` — co-author test rule applied throughout this feature
- `2026-04-23-verify-mode-suppression-must-be-anchored-to-fixed-finding-scope.md` — verify-mode suppression policy governing the verify pass
- `2026-04-07-pester-test-quality-patterns.md` — general Pester quality patterns
