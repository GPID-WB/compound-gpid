---
date: 2026-06-01
title: "Test-correctness assessment — red-phase gate, diagnostic fork, mutation verification"
status: complete
scope: "Standard"
brainstorm: ".cg-docs/brainstorms/2026-06-01-fixbug-test-correctness-assessment.md"
language: "both"
estimated-effort: "medium"
tags: [testing, test-integrity, cg-fixbug, cg-work, red-green-refactor, mutation-testing]
phases: 2
completed-phases: [1, 2]
---

# Plan: Test-Correctness Assessment

## Objective

Add test-integrity awareness to the `/cg-fixbug` and `/cg-work` prompts so that
the AI agent never blindly trusts tests written from the same flawed mental model
as the code. Three coordinated changes: a diagnostic fork in `/cg-fixbug` (reactive),
a red-phase gate in `/cg-work` (preventive), and a mutation verification reference
in `cg-skill-r-testing` (detective).

## Context

- `/cg-fixbug` currently enforces hard stops at Step 2 (test must fail) and Step 4
  (test must pass) but does not evaluate whether *existing* tests are trustworthy.
- `/cg-work` runs tests after implementation but never confirms tests are sensitive
  to failure (never red before green).
- The charter's "Current Focus" explicitly mentions "smarter test-awareness in /cg-fixbug."
- The roadmap tracks this as feature `fixbug-test-correctness-assessment` (status: idea).

## Requirements

| ID  | Requirement                                                    | Source           |
|-----|----------------------------------------------------------------|------------------|
| R1  | `/cg-fixbug` evaluates existing tests before writing new ones  | brainstorm       |
| R2  | Agent distinguishes "test is incomplete" from "test codifies bug" | brainstorm    |
| R3  | Flawed test repair deferred to Step 4 (after fix confirmed)    | brainstorm       |
| R4  | `/cg-work` confirms new tests fail before implementation       | brainstorm       |
| R5  | Red-phase gate is soft checkpoint, not hard stop               | brainstorm       |
| R6  | Escape hatch when agent cannot determine what to test          | brainstorm       |
| R7  | Structural/prompt/config steps skip the red-phase gate         | brainstorm       |
| R8  | Mutation verification protocol documented as reference         | brainstorm       |
| R9  | P2 default, P1 for welfare/FGT/weights functions              | brainstorm       |
| R10 | Bug document records `red-phase-confirmed` field               | brainstorm       |
| R11 | All diagnostic output readable by non-technical economists     | charter          |
| R12 | No schema migration (no `tests:` field in plan structure)      | brainstorm       |
| R13 | Agent identifies expected behavior source before writing tests | user (Layer 1)   |
| R14 | Test gap classification explains why old tests missed the bug  | user (Layer 2)   |
| R15 | Red-green proof sequence required before bug is declared fixed | user (Layer 3)   |

## Phase 1: Core prompt changes

### 1. Add three-layer test-correctness protocol to `/cg-fixbug`

- **Requirements**: R1, R2, R3, R11, R13, R14, R15
- **Files**: `.github/prompts/cg-fixbug.prompt.md` (MODIFY), `tests/prompt-tools.Tests.ps1` (MODIFY)
- **Details**: Restructure Steps 2–4 of `/cg-fixbug` to incorporate the three layers.
  The existing step numbering and hard stops are preserved — the layers are inserted
  as sub-steps within the existing structure. The resulting sequence is:

  **Step 1 (Intake)** — unchanged.

  **Step 1.5 (NEW — Layer 1: Expected Behavior Source)**:

  Before writing any test, the agent must identify where the *correct* expected behavior
  comes from. The source of truth is the intended behavior — not the current
  implementation and not the existing tests. State explicitly:

  > "The expected behavior for this function/feature is defined by: `[source]`"

  Valid sources (in priority order):
  1. User requirement (the bug reporter stated what should happen)
  2. Documentation (roxygen2/docstrings describe the contract)
  3. Mathematical/statistical definition (e.g., "FGT index averages over entire population")
  4. Hand-computed toy example (known input → known output, verifiable by hand)
  5. Package convention (upstream API guarantees a specific behavior)
  6. External reference (paper, specification document, World Bank methodology note)
  7. Explicit backward-compatibility contract (prior version's documented behavior)

  If the agent cannot identify a source: ask the user.
  > "I cannot determine the expected behavior from code or documentation alone.
  > What should this function return for input X?"

  This step is mandatory — the agent must not proceed to write a test without first
  declaring the expected behavior source. This prevents circular reasoning (deriving
  expected values from the implementation being debugged).

  **Step 2 (Reproduce — HARD STOP)** — enhanced with diagnostic fork:

  1. **Evaluate existing tests** (pre-check before writing new test):
     Search for existing tests covering the buggy function/behavior. Use the same
     discovery conventions as `/cg-work` Step 1.6: file mapping (`tests/test-<module>.R`,
     `tests/<module>.Tests.ps1`, `tests/test_<module>.py`) and function-name grep.

     - If existing test found → run it on current buggy code:
       - If it FAILS → trustworthy. Report: "Existing test `[name]` confirmed failing —
         using it as reproduction test." Skip writing a new test. Proceed to hard stop.
       - If it PASSES → sub-diagnostic:
         - Does the test exercise the same input that triggers the bug?
           - YES → "Existing test `[name]` asserts buggy behavior (passes on broken code
             with the same input). Writing a new correct reproduction test. Will repair
             `[name]` after fix is confirmed in Step 4."
           - NO → "Existing test `[name]` covers a different aspect of this function
             (doesn't exercise the buggy input). Writing a new reproduction test.
             Existing test is fine."
     - If no existing test found → write new failing test.

  2. **Write the failing regression test** using the expected behavior source from
     Step 1.5. The test's expected values must come from the declared source — not
     from running the function and copying its output.

  3. **Hard stop** (unchanged): "Confirm the reproduction test fails on the current code."

  **Step 2.5 (NEW — Layer 2: Test Gap Classification)**:

  After the reproduction test is confirmed failing, classify why the old test suite
  did not catch this bug. State explicitly:

  > "Test gap classification: `[category]` — `[one-line explanation]`"

  Categories:
  | Category | Meaning |
  |----------|---------|
  | **missing-test** | No test existed for this function or behavior |
  | **weak-test** | Test existed but asserted too loosely (e.g., checked type not value) |
  | **circular-test** | Test derived expected values from the implementation itself |
  | **wrong-test** | Test asserted incorrect expected values (codifies the bug) |
  | **ambiguous-spec** | Specification was unclear; test matched one valid interpretation |
  | **fixture-gap** | Test used fixtures that didn't cover the triggering data shape |
  | **edge-case-gap** | Test covered the happy path but not the boundary condition |
  | **integration-gap** | Unit tests passed but the bug emerges from component interaction |

  This classification informs Step 4 (which tests to repair) and Step 5 (Lessons Learned).

  **Step 3 (Diagnose)** — unchanged.

  **Step 4 (Fix — HARD STOP)** — enhanced with Layer 3 (Red-Green Proof):

  After the implementation fix is applied, the agent must demonstrate the full
  red-green proof sequence before the hard stop confirmation:

  1. **Red phase verified**: The regression test from Step 2 failed before the fix
     (already confirmed at Step 2 hard stop). State: "Red phase: confirmed at Step 2."
  2. **Failure matches reported bug**: The test failure message corresponds to the
     symptom described in Step 1 (Intake). State: "Failure corresponds to reported
     symptom: `[brief match]`"
  3. **Implementation changed after test**: The fix was applied only after the failing
     test existed. State: "Implementation modified after failing test was confirmed."
  4. **Green phase**: Run the regression test. It must pass. State:
     "Green phase: `[test name]` now passes."
  5. **Existing valid tests pass**: Run the full relevant test suite. State:
     "Existing tests: N passing, 0 regressions."
  6. **Flawed tests corrected**: If Step 2.5 classified the gap as `wrong-test`,
     `circular-test`, or `weak-test`, repair those tests now — update expected values
     to match the confirmed-correct behavior (from Step 1.5's declared source).
     State: "Repaired: `[test name]` — was `[category]`, now asserts correct behavior."
     If no flawed tests were identified, state: "No flawed tests to repair."

  Only after all six sub-points are satisfied:
  > "Red-green proof complete. Reply 'confirmed fixed' to proceed to documentation."

  **Step 5 (Document)** — enhanced:

  The bug document's `## Lessons Learned` section must reference the test gap
  classification from Step 2.5 and explain what pattern to follow to avoid this
  class of gap in the future.

- **Test Scenarios**:
  - ✅ Happy path: user states expected behavior → new failing test written from that source → gap classified → fix applied → red-green proof passes
  - ✅ Happy path: existing test fails on buggy code → reused as reproduction test → gap is "N/A (test was correct)"
  - 🛑 Edge case: agent cannot identify expected behavior source → asks user
  - 🛑 Edge case: existing test passes with same input → classified as "wrong-test" → repaired in Step 4
  - 🛑 Edge case: gap is "ambiguous-spec" → agent flags that spec needs clarification
  - ❌ Error path: test discovery finds no test files → "missing-test" classification → proceeds to write new test
  - ❌ Error path: red-green proof fails at sub-point 5 (existing tests regress) → fix needs revision
- **Tests**: Write Pester assertions in `prompt-tools.Tests.ps1` (colocated with this step) verifying:
  - The prompt contains "expected behavior" source identification language before Step 2
  - The prompt lists the valid source types (user requirement, documentation, mathematical, etc.)
  - The prompt contains the test gap classification table with all 8 categories
  - The prompt contains "codifies bug" vs "incomplete" distinction in the diagnostic fork
  - The prompt contains red-green proof sequence (all 6 sub-points) in Step 4
  - The prompt mentions flawed test repair in Step 4
  - Step 2 hard stop is preserved (not weakened)
  - The prompt requires the agent to ask the user if expected behavior cannot be determined
- **Acceptance criteria**: `/cg-fixbug` now implements the full three-layer protocol:
  expected behavior source (before test), test gap classification (after test), and
  red-green proof (after fix). All colocated Pester assertions pass.

### 2. Update bug document schema in `/cg-fixbug` Step 5

- **Requirements**: R10, R13, R14, R15
- **Files**: `.github/prompts/cg-fixbug.prompt.md` (MODIFY — Step 5 schema), `tests/prompt-tools.Tests.ps1` (MODIFY)
- **Details**: Extend the YAML frontmatter template in Step 5's bug document schema
  with three new fields (place after `fix-confirmed`):

  ```yaml
  red-phase-confirmed: "yes"
  expected-behavior-source: "<source type from Step 1.5>"
  test-gap: "<classification from Step 2.5>"
  ```

  Add to the Schema Rules section:
  - `red-phase-confirmed` must always be `"yes"` — the reproduction test was verified
    failing before any fix was applied.
  - `expected-behavior-source` must name the source type (one of: user-requirement,
    documentation, mathematical-definition, hand-computed-example, package-convention,
    external-reference, backward-compatibility-contract).
  - `test-gap` must contain one of the 8 classification categories from Step 2.5.

  Also update the document body template:
  - Add a `## Expected Behavior Source` section (between Symptom and Root Cause) where
    the agent records the source and the specific expected value derived from it.
  - Add a `## Test Gap` section (between Reproduction Test and Fix) where the agent
    records the classification and a one-paragraph explanation of why existing tests missed this.
  - The `## Lessons Learned` section must reference the test gap classification.

- **Test Scenarios**:
  - ✅ Happy path: all three new fields present in schema template
  - ✅ Happy path: both new body sections present in document template
  - 🛑 Edge case: all fields are required, not optional
- **Tests**: Write Pester assertions (colocated) that:
  - The schema template contains `red-phase-confirmed`
  - The schema template contains `expected-behavior-source`
  - The schema template contains `test-gap`
  - The document template contains `## Expected Behavior Source`
  - The document template contains `## Test Gap`
- **Acceptance criteria**: Bug document schema includes all three new fields and two new
  body sections; Schema Rules documents their invariants. All colocated assertions pass.

### 3. Add red-phase gate to `/cg-work` Step 2

- **Requirements**: R4, R5, R6, R7, R12
- **Files**: `.github/prompts/cg-work.prompt.md` (MODIFY — Step 2), `tests/prompt-tools.Tests.ps1` (MODIFY)
- **Details**: Insert as **bold inline text** between current sub-step 2 ("Discover existing
  tests") and sub-step 3 ("Implement"). Use the label **"Red-phase verification"** as a
  bold paragraph — NOT a `###` heading (to avoid collision with the existing
  `### Step 2.5: Phase Boundary` section). Do NOT renumber any existing sub-steps — all
  downstream references (e.g., "format from sub-step 4") remain valid.

  The inserted text:

  > **Red-phase verification** (conditional — skip if this step is purely structural:
  > config files, prompt text, documentation, YAML frontmatter, or directory scaffolding):
  >
  > If this plan step introduces new testable behavior (creates a function, modifies
  > return values, changes data transformation logic, or adds a new code path):
  > 1. Write the test(s) now, before touching the implementation.
  > 2. Run the test(s) against the current unmodified code.
  > 3. The test must fail. Report: "Red-phase confirmed: `[test name]` fails with: `[one-line error]`"
  > 4. If the test passes before implementation: the test is wrong — it does not detect
  >    the absence of the feature. Revise (one attempt). If still passing: log "Could not
  >    establish failing baseline — proceeding without red-phase confirmation. Flag for
  >    `@cg-testing` review." Continue to implementation.
  > 5. After red-phase confirmation: proceed to implementation (sub-step 3).
  >
  > This is NOT a hard stop. Do not wait for user confirmation. Log the result and continue.

  Ensure the language makes clear this is separate from and runs before the post-implementation
  Test Failure Recovery loop. No existing sub-step numbers change.

- **Test Scenarios**:
  - ✅ Happy path: new function → test written → test fails → implementation proceeds
  - ✅ Happy path: structural step (prompt edit) → red-phase skipped
  - 🛑 Edge case: test passes before implementation → one revision attempt → still passes → escape hatch
  - ❌ Error path: agent cannot determine what to test → logs and proceeds
- **Tests**: Write Pester assertions in `prompt-tools.Tests.ps1` (colocated with this step) verifying:
  - The prompt contains "Red-phase verification" language in Step 2
  - The prompt contains the escape hatch ("Could not establish failing baseline")
  - The prompt specifies this is NOT a hard stop
  - The prompt distinguishes structural steps from testable behavior
  - The existing `### Step 2.5: Phase Boundary` heading is unchanged
- **Acceptance criteria**: `/cg-work` Step 2 contains the conditional red-phase gate;
  escape hatch is documented; structural steps are explicitly excluded; no existing
  sub-step numbers or Pester assertions are broken. All colocated assertions pass.

## Phase 2: Reference documentation

### 4. Create `references/test-integrity.md` in `cg-skill-r-testing`

- **Requirements**: R8, R9, R13, R14
- **Files**: `.github/skills/cg-skill-r-testing/references/test-integrity.md` (CREATE)
- **Details**: New reference file documenting the three-layer test-integrity protocol
  as it applies to R code. Sections:

  **1. Expected Behavior Sources** — how to derive test expected values from external
  sources rather than implementation output. Priority-ordered list matching Step 1.5
  of `/cg-fixbug`. Include R-specific examples: roxygen2 `@returns` documentation,
  mathematical definitions (weighted mean formula), hand-computed data.table examples.

  **2. Mutation Verification Protocol**:
  1. After a test is written and passing, introduce a deliberate minimal error in the
     function (flip a comparison, swap an argument, change a return value).
  2. Re-run the test. It must fail.
  3. Revert the error. Re-run the test. It must pass again.
  4. If the test passes with the deliberate error: the test is not sensitive to this
     failure mode. Revise it.

  **3. Test Gap Taxonomy** — the 8-category classification from `/cg-fixbug` Step 2.5,
  with R-specific examples for each (e.g., "circular-test: expected value computed by
  calling the same function being tested").

  **4. Detection Signals for Tautological Tests** (passive guidance for human reviewers):
  - Test expected value appears copied from function output rather than derived from spec
  - Test was committed in the same commit as the implementation with no prior red phase
  - Test mirrors implementation logic (same formula, same conditionals)

  **5. When to Apply**:
  - Required (P1) for welfare/FGT/weights/survey functions
  - Recommended (P2) for all other functions where a prior bug was found that tests missed
  - Integration: `/cg-fixbug` references this after Step 4 for high-stakes functions

  All examples use data.table + collapse + testthat.

- **Test Scenarios**:
  - ✅ File exists and is reachable from SKILL.md
  - ✅ Contains mutation verification steps
  - ✅ Contains P1/P2 severity guidance
  - ✅ Contains the 8-category test gap taxonomy
  - ✅ Contains expected behavior source guidance
- **Tests**: Pester assertion verifying the file exists and contains key terms
  ("mutation", "deliberate error", "P1", "welfare", "expected behavior", "test gap").
- **Acceptance criteria**: Reference file exists at the expected path; covers all five
  sections; uses project-standard R examples.

### 5. Update `cg-skill-r-testing` SKILL.md to reference the new file

- **Requirements**: R8
- **Files**: `.github/skills/cg-skill-r-testing/SKILL.md` (MODIFY)
- **Details**: Add a brief mention and link to `references/test-integrity.md` in the
  appropriate section of SKILL.md. Keep it minimal — one line pointing to the reference.
- **Test Scenarios**:
  - ✅ SKILL.md mentions test-integrity
- **Tests**: Pester assertion that SKILL.md contains "test-integrity".
- **Acceptance criteria**: SKILL.md links to the new reference file.

### 6. Write Pester tests for reference documentation

- **Requirements**: R8, R9 (regression coverage for Phase 2 artifacts)
- **Files**: `tests/prompt-tools.Tests.ps1` (MODIFY)
- **Details**: Add a `Describe` block for:
  - `cg-skill-r-testing - test-integrity reference`: file existence, key content terms
    ("mutation", "deliberate error", "P1", "welfare").
  Note: Pester tests for prompt changes (Steps 1–3) are colocated in Phase 1 — NOT
  deferred here. This step covers only the Phase 2 reference file.
- **Test Scenarios**:
  - ✅ All assertions pass after changes are applied
  - 🛑 Edge case: assertions fail if reference file is deleted (regression detection)
- **Tests**: Self-referential — these ARE the tests.
- **Acceptance criteria**: Pester assertion for `test-integrity.md` passes.

## Testing Strategy

All tests are Pester-based content assertions (`-match`, `-like`) on prompt file text.
No functional/runtime tests needed — these are prompt engineering changes, not code.
The test file is `tests/prompt-tools.Tests.ps1`. Follow the existing pattern: `Describe`
block per feature, `It` block per assertion, `$content -match 'pattern'` for text presence.

Key assertion groups:
- **Layer 1 (Expected Behavior Source)**: source type list present, "ask the user" fallback present, placement before Step 2
- **Layer 2 (Test Gap Classification)**: all 8 categories present, placement after Step 2 hard stop
- **Layer 3 (Red-Green Proof)**: all 6 sub-points present, placement in Step 4
- **Diagnostic fork**: existing test evaluation, codifies-bug vs incomplete distinction
- **Schema fields**: `red-phase-confirmed`, `expected-behavior-source`, `test-gap` in template
- **Document sections**: `## Expected Behavior Source`, `## Test Gap` in body template

## Documentation Checklist

- [ ] No function documentation needed (prompt text changes only)
- [ ] No README updates needed (internal workflow improvement)
- [ ] Inline comments in test file explaining what each assertion guards
- [ ] `references/test-integrity.md` is self-documenting (it IS documentation)

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Red-phase gate adds execution time to `/cg-work` | Medium — slower step execution | Conditional: skips structural steps; escape hatch prevents stalling |
| Red-phase doubles `execution_subagent` invocations per testable step | Medium — extends session length and context pressure | Structural-step exclusion and escape hatch bound worst case; non-testable steps pay zero cost |
| Agent over-diagnoses "test codifies bug" | Medium — false positives stall `/cg-fixbug` | Sub-diagnostic requires matching input, not just function coverage |
| Mutation verification adds friction for economists | Low — scoped to high-stakes only | P2 default; P1 only for welfare/FGT/weights; never required for prompt/config work |
| Pester test file grows larger | Low — maintenance burden | Follow existing pattern; one Describe block per feature |

## Out of Scope

- No changes to `@cg-testing` agent (no new automated detection of tautological tests)
- No `tests:` field added to plan step structure
- No changes to `/cg-plan` template
- No changes to the two-round recovery loop mechanics in `/cg-work`
- No Python or Stata testing skill changes (R only for now; patterns are transferable later)
- No changes to `/cg-review` or `/cg-fix-triage` prompts
