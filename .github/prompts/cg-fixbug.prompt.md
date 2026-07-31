---
description: "Structured bug-fix workflow: reproduce, diagnose, fix, verify, document."
---

# Fix Bug

You are a senior developer guiding a structured bug-fix arc: Intake → Reproduce → Diagnose → Fix → Document.

## File Permissions

- **READ**: Any file in the workspace.
- **CREATE**: Only under `.cg-docs/solutions/bugs/` and test files.
- **MODIFY**: Only source files directly related to the confirmed fix.
- **NEVER**: Modify `.cg-docs/` documentation files other than creating the new bug document.

## Process

### Step 0: Get Bearings

1. Read `compound-gpid.md` in the project root for project context (objective,
   constraints, current focus).
2. Read `compound-gpid.local.md` for user config (language, project type,
   review depth).
3. Load `.github/shared/context-loading.contract.md`. Search targeted headings
   or snippets in `compound-gpid.context.md` only if bug diagnosis needs
   project-specific context or workspace notes. If it does not exist, skip silently.
4. If `compound-gpid.md` does not exist, warn the user:
   "No project charter found. Run `/cg-setup` to create one. Proceeding
   without project context."

### Step 1: Intake

1. Ask the user to describe the bug:
   - What is the symptom?
   - Where was it found (file, function, test)?
   - What was the expected behavior vs. actual behavior?

2. Search `.cg-docs/solutions/bugs/` for similar past bugs. Match on:
   - File name keywords
   - YAML frontmatter `title` and `tags` fields
   - `root-cause` field

3. If similar bugs are found, surface them:
   > "I found a similar past bug: [link]. Is this the same issue, or a different one?"

   Wait for the user's answer before continuing.

---

### Step 1.5: Expected Behavior Source — MANDATORY

<!-- MANDATORY = agent-enforced gate (no user confirmation required). HARD STOP = user-confirmed gate. -->
Before writing any test, identify where the *correct* expected behavior comes from.
The source of truth is the intended behavior — not the current implementation and
not the existing tests.

State explicitly:
> "The expected behavior for `[function/feature]` is defined by: `[source type]`"
> "Specifically: `[what the correct behavior should be]`"

Valid sources (in priority order):
1. **User requirement** — the bug reporter stated what should happen
2. **Documentation** — roxygen2 `@returns`, docstrings, or README describes the contract
3. **Mathematical/statistical definition** (slug: `mathematical-definition`) — e.g., "FGT₀ = fraction of population below poverty line"
4. **External reference** — a methodology note, paper, or specification document
5. **Package convention** — upstream API guarantees a specific return shape or value
6. **Hand-computed example** — known input → known output, verifiable without running the code
7. **Backward-compatibility contract** — prior version's documented behavior

R projects: load `cg-skill-r-testing` and its `references/test-integrity.md` for detection signals when classifying test gaps in Step 2.5.

> See also `cg-skill-r-testing/references/test-integrity.md — Expected Behavior Sources` for source examples.

If no source can be identified, ask:
> "I cannot determine the expected behavior from the code or documentation alone.
> What should `[function]` return when given `[the triggering input]`?"

**Do NOT proceed to Step 2 until the expected behavior source is declared.** This prevents
the agent from writing a test that derives its expected value from the same implementation
being debugged.

---

### Step 2: Reproduce — HARD STOP

**Pre-check: Evaluate existing tests** before writing any new test.
Search for existing tests covering the buggy function/behavior using the standard conventions:
file mapping (`tests/test-<module>.R`, `tests/<module>.Tests.ps1`, `tests/test_<module>.py`)
and function-name grep.

- **If an existing test is found** → run it on the current buggy code:
  - If it **FAILS** → trustworthy. Report: "Existing test `[name]` confirmed failing — using it as reproduction test." Skip to the hard stop below.
  - If it **PASSES** on buggy code → sub-diagnostic:
    - Does the test exercise the **same input** that triggers the bug?
      - **YES** → "Existing test `[name]` asserts buggy behavior (passes on broken code with the same input). Writing a new correct reproduction test. Will repair `[name]` after fix is confirmed in Step 4."
      - **NO** → "Existing test `[name]` covers a different aspect — it doesn't exercise the buggy input. Writing a new reproduction test. Existing test is fine."
- **If no existing test is found** → write a new failing test.

**If tests cannot be run** (CLM restriction, missing test runner, locked environment): log
*"Test runner unavailable — skipping existing-test pre-check. Writing new failing test from the
expected behavior source declared in Step 1.5."* and proceed to writing the test.

1. Write the failing regression test using the expected behavior declared in Step 1.5.
   The test's expected values must come from the declared source — not from running the
   function and copying its output.
   - R: use `testthat`. Python: use `pytest`. Stata: use `assert` statements in a validation do-file. PowerShell: use Pester.
   - Place the test in the appropriate test file or create a new one.

2. **STOP. Tell the user exactly this:**

   > "The reproduction test is written. Run this test now and confirm it fails on the current code before we continue.
   >
   > **Reply 'confirmed failing' to proceed to diagnosis.**"

3. **Do NOT proceed to Step 2.5 until the user replies 'confirmed failing' (or equivalent confirmation).**

   **If the user indicates the test is NOT failing**: the test does not detect the bug. Return to the pre-check, revise the test (new input, tighter assertion, or different function call), and request confirmation again. Do not advance to Step 2.5 until a genuinely failing test is confirmed.

---

### Step 2.5: Test Gap Classification

After the reproduction test is confirmed failing, classify why the old test suite did
not catch this bug. State explicitly:
> "Test gap classification: `[category]` — `[one-line explanation]`"

| Category | Meaning |
|----------|----------|
| **missing-test** | No test existed for this function or behavior |
| **weak-test** | Test existed but asserted too loosely (e.g., checked type not value) |
| **circular-test** | Test derived expected values from the same implementation being tested |
| **wrong-test** | Test asserted incorrect expected values (codifies the bug) |
| **ambiguous-spec** | Specification was unclear; test matched one valid interpretation |
| **fixture-gap** | Fixtures didn't cover the triggering data shape |
| **edge-case-gap** | Test covered the happy path but not the boundary condition |
| **integration-gap** | Unit tests passed but the bug emerges from component interaction |

> **Classification note**: `circular-test` is a subcategory of `wrong-test`. Prefer `circular-test` when the root cause is the derivation method (expected value was computed by running the implementation). Use `wrong-test` when expected values are incorrect for other reasons.

> For typical signals distinguishing each category, see [`cg-skill-r-testing/references/test-integrity.md — Test Gap Taxonomy`](./../skills/cg-skill-r-testing/references/test-integrity.md).

This classification informs which tests to repair in Step 4 and the Lessons Learned in Step 5.

---

### Step 3: Diagnose

1. Analyze the failing test and the relevant source code.

2. State your root-cause hypothesis explicitly:
   > "The root cause appears to be **X** because **Y**."

3. Ask the user:
   > "Does this diagnosis look correct, or do you want to investigate further?"

4. If more investigation is needed, ask clarifying questions **one at a time** — never all at once. Wait for each answer before asking the next.

---

### Step 4: Fix — HARD STOP

1. Implement the fix based on the confirmed diagnosis. Follow project conventions:
   - R: follow `.github/instructions/r.instructions.md` style.
   - Python: follow `.github/instructions/python.instructions.md` style.
   - Stata: follow `.github/instructions/stata.instructions.md` style and load `cg-skill-stata-best-practices`.

2. **Demonstrate red-green proof** (run these checks in order, report each result):

   1. **Red phase confirmed**: State: "Red phase: confirmed at Step 2 — `[test name]` was failing before the fix."
   2. **Failure matches symptom**: Confirm the Step 2 test failure message corresponded to the bug described in Step 1. State: "Failure corresponds to reported symptom: `[brief match]`"
   3. **Fix applied after test**: The implementation was changed only after the failing test existed. State: "Implementation modified after failing test was established."
   4. **Green phase**: Run the reproduction test now. State: "Green phase: `[test name]` now passes." If it fails: the fix is incomplete — return to diagnosis.
   5. **Existing tests pass**: Run the full relevant test suite. State: "Existing tests: N passing, 0 regressions." If regressions appear: the fix introduced a new problem — investigate before continuing.
   6. **Flawed tests repaired**: If Step 2.5 classified the gap as `wrong-test`, `circular-test`, or `weak-test`, repair those tests now — update only the specific expected values that were wrong; preserve all other assertions that remain valid. State: "Repaired: `[test name]` — was `[category]`, now asserts correct behavior." For `fixture-gap` and `edge-case-gap`: add the triggering data shape or boundary input to the fixture/test rather than replacing existing assertions. If no flawed tests: state "No flawed tests to repair."

3. **STOP. Only after all six sub-points are confirmed. Tell the user exactly this:**

   > "Red-green proof complete:
   > - ✅ Red phase confirmed at Step 2
   > - ✅ Failure matched reported symptom
   > - ✅ Fix applied after failing test
   > - ✅ `[test name]` now passes (green)
   > - ✅ N existing tests passing, 0 regressions
   > - ✅ `[flawed test status]`
   >
   > **Reply 'confirmed fixed' to proceed to documentation.**"

4. **Do NOT proceed to Step 5 until the user replies 'confirmed fixed' (or equivalent confirmation).**

---

### Step 5: Document

Only write the bug document **after** receiving Step 4 confirmation.

1. Create `.cg-docs/solutions/bugs/YYYY-MM-DD-<brief-title>.md` using this schema:

```markdown
---
date: YYYY-MM-DD
title: "<descriptive title>"
category: "bugs"
type: "bug"
language: "<R|Python|Stata|both>"
tags: [<searchable tags>]
root-cause: "<one-line root cause>"
severity: "<P1|P2|P3>"
test-written: "yes"
fix-confirmed: "yes"
red-phase-confirmed: "yes"
expected-behavior-source: "<source type from Step 1.5>"
test-gap: "<classification from Step 2.5>"
---

# <Title>

## Symptom
<What was the observable wrong behavior?>

## Expected Behavior Source
<The source type declared in Step 1.5 and the specific expected value derived from it.
Example: "Mathematical definition — FGT₀ is the headcount ratio; for a population of
3 where 1 is below the line, the correct value is 0.333, not 1.0.">

## Root Cause
<Why did it happen? What was the underlying issue?>

## Reproduction Test
<The test written in Step 2. Include the file path where it was saved.>

## Test Gap
<The classification from Step 2.5 and a one-paragraph explanation of why existing
tests missed this bug. Example: "circular-test — the expected value in the existing
test was computed by calling the same function, so any systematic error was invisible.">

## Fix
<What changed and why. Include code snippets.>

## Lessons Learned
<What does this bug teach us? Reference the test gap classification: what pattern
should be followed to avoid this class of gap in the future? What anti-pattern caused it?>

## Related
<Links to similar bugs or solutions in .cg-docs/ if any were found in Step 1.
If none were found, write "None.">
```

2. After writing the document, tell the user:
   > "Bug documented at `.cg-docs/solutions/bugs/<filename>`.
   >
   > If this bug reveals a pattern the whole team should avoid, run `/cg-compound` to capture it as a team-wide lesson."

## Schema Rules

- `test-written` and `fix-confirmed` **must always be `"yes"`** by the time the document is written. Never write a bug document where either field is `"no"` or missing.
- `red-phase-confirmed` **must always be `"yes"`** — the reproduction test was verified failing before any fix was applied.
- `expected-behavior-source` must name the source type declared in Step 1.5 (one of: user-requirement, documentation, mathematical-definition, hand-computed-example, package-convention, external-reference, backward-compatibility-contract).
- `test-gap` must contain the classification from Step 2.5 (one of: missing-test, weak-test, circular-test, wrong-test, ambiguous-spec, fixture-gap, edge-case-gap, integration-gap).
- `Lessons Learned` **must be written after `fix-confirmed`**, never before. The lessons document the verified fix, not a hypothesis. Reference the `test-gap` classification.
- `severity` must be one of `P1`, `P2`, or `P3`:
  - **P1**: Data corruption, security issue, incorrect results.
  - **P2**: Performance problem, missing test, poor error handling.
  - **P3**: Minor behavior deviation, cosmetic issue.
