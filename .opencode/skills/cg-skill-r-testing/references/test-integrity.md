# Test Integrity Reference

Companion to `cg-skill-r-testing`. Covers how to verify that tests assert the intended
behavior of a function, not merely the behavior the current implementation happens to
produce. Load this file when working on bug fixes or when reviewing tests for tautology.

> **Language scope**: Examples are in R, but the taxonomy and protocol apply equally to Python and Stata projects.

---

## Expected Behavior Sources

Before writing a test, identify where the *correct* expected value comes from.
**Never derive expected values by running the function under test.**

Valid sources (in priority order):

| # | Source | Example |
|---|--------|-------------------------------|
| 1 | **User requirement** | "The function should return the count of elements below the line" |
| 2 | **Documentation** | roxygen2 `@returns` or `@examples` in the function header |
| 3 | **Mathematical/statistical definition** | FGT₀ = fraction of population with consumption < z |
| 4 | **External reference** | World Bank Poverty Handbook, methodology note |
| 5 | **Package convention** | `collapse::fmean()` returns a named numeric vector |
| 6 | **Hand-computed example** | For `c(1, 2, 3)` with line = 2: FGT₀ = 2/3 = 0.667 |
| 7 | **Backward-compatibility contract** | Prior tagged release documented output shape |

> This list mirrors the source types declared in `/cg-fixbug` Step 1.5.

**If no source can be identified**: ask the maintainer. Do not proceed with a guess.

---

## Red-Green Verification Protocol

A sequence to confirm a test genuinely detects the absence of the intended behavior. (Formerly "Mutation Verification Protocol" — renamed to avoid confusion with deliberate defect injection.)

1. **Write the test first** — using expected values from an independent source (see above),
   before touching the implementation.

2. **Confirm red phase** — run the test against the current (broken or unimplemented) code.
   The test must **fail**. Record the failure message:
   > "Red phase: `[test name]` fails with: `[one-line error]`"
   If the test passes on broken code, it does not detect the bug — revise the test.

3. **Confirm failure matches symptom** — verify the failure message corresponds to the bug
   symptom reported in the intake. If the test fails for a different reason, the test does not
   exercise the triggering scenario.

4. **Implement the fix** — change only the implementation, not the test.

5. **Confirm green phase** — run the test again. The test must now **pass**:
   > "Green phase: `[test name]` passes after fix."

6. **Confirm no regressions** — run the full test suite. All previously passing tests must
   still pass. If regressions appear, investigate before proceeding.
   > "Existing tests: N passing, 0 regressions."

Only after all six steps are complete is the fix verified. A test that was never seen
to fail is not a safety net — it is noise.

> **When using this protocol in `/cg-fixbug`**: sub-points 1–5 of Step 4 correspond to
> steps 2–6 of this protocol (step 1 — write the test first — happens in cg-fixbug Step 2).
> Sub-point 6 (flawed test repair) is an extension beyond this protocol.
> Sub-point 2 = step 3 above (failure matches symptom); sub-point 5 = step 6 above (regressions).

---

## Test Gap Taxonomy

Classification of why an existing test suite missed a bug. Use this when a bug
reaches production despite tests being present.

| Category | Meaning | Typical Signal |
|----------|---------|----------------|
| **missing-test** | No test existed for this function or behavior | Grep finds no test file or no test block for the function |
| **weak-test** | Test existed but asserted too loosely | `expect_type()` instead of `expect_equal()`, or `expect_true(length(x) > 0)` |
| **circular-test** | Test derived expected values from the same implementation | `expect_equal(fn(x), fn(x))` or expected computed via `fn()` before the assertion |
| **wrong-test** | Test asserted incorrect expected values (codifies the bug) | Expected value is the wrong result; test passes on broken code with the same input |
| **ambiguous-spec** | Specification was unclear; test matched one valid interpretation | Two valid readings of the docs, test picked the one the bug implements |
| **fixture-gap** | Fixtures didn't cover the triggering data shape | Bug only appears with NA values, zero weights, or edge factor levels not in fixtures |
| **edge-case-gap** | Test covered the happy path but not the boundary condition | Off-by-one errors, empty inputs, single-row data frames |
| **integration-gap** | Unit tests passed but bug emerges from component interaction | Two functions each correct in isolation; bug in the composition |

Record the classification in the bug document (`test-gap` frontmatter field) and
reference it in Lessons Learned.

---

## Detection Signals for Tautological Tests

A tautological test passes on broken code. Signals to look for during review:

- **Expected value computed from the function itself**:
  ```r
  # ❌ Tautological — always passes regardless of what fn() does
  expected <- fn(input)
  expect_equal(fn(input), expected)
  ```
- **Expected value hard-coded by running the function once and copying output**: the
  test was written by running the code, not from a specification.
- **Test passes with the same input that the bug reporter used**: a test that exercises
  the exact triggering input yet passes on unpatched code is asserting buggy behavior.
- **No independent computation exists in the test file**: all expected values derived
  from function calls, not from literals, formulas, or external references.
- **`circular-test` or `wrong-test` classification**: these are the two tautological
  categories — a test with either classification must be repaired when the bug is fixed.

Repair procedure:
1. Identify the correct expected value from an independent source (see above).
2. Replace the derived expected value with the correct literal.
3. Re-run the test on the *unpatched* code — it must now fail (red phase).
4. Apply the fix — the test must pass (green phase).

---

## When to Apply

| Priority | Situation |
|----------|-----------|
| **P1** | Any bug in welfare, FGT, poverty, inequality, or weight computation functions. These produce the team's headline outputs — a tautological test here means a systematic error could appear in published figures. |
| **P2** | Any other bug where a prior test was present but did not catch the issue. The gap classification informs whether to add tests, fix fixtures, or tighten assertions. |
| **Skip** | New features with no prior tests and no user report of wrong behavior — just write tests normally from the specification. |
