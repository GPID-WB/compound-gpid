# Test Scaffolding in Stata

Stata has no built-in test runner, but you can build reliable test harnesses with `preserve`/`restore`, `foreach` loops, `tempfile`, and a pass/fail counter pattern.

## Test Isolation with `preserve`/`restore`

Every test block that modifies data must wrap its changes in `preserve`/`restore` so subsequent tests start with the same dataset:

```stata
preserve

    // Test: verify poverty calculation for z = 1.90
    poverty welfare [aw=weight], line(1.90)
    assert inrange(r(head_count), 0, 1)

restore    // data is back to pre-test state for next test
```

Nesting `preserve`/`restore` is allowed up to 2 levels deep in Stata. For more complex isolation, use `tempfile`.

## Batch Testing with `foreach` Loops

```stata
* Test multiple poverty lines in one loop
local tests_passed = 0
local tests_failed = 0

preserve

foreach z in 1.90 3.20 5.50 6.85 {
    quietly poverty welfare [aw=weight], line(`z')

    capture assert inrange(r(head_count), 0, 1)
    if _rc {
        local ++tests_failed
        display as error "FAIL [z=`z']: FGT0 out of range (r(head_count) = `r(head_count)')"
    }
    else {
        local ++tests_passed
    }

    capture assert r(poverty_gap) <= r(head_count)
    if _rc {
        local ++tests_failed
        display as error "FAIL [z=`z']: poverty_gap > head_count (monotonicity violation)"
    }
    else {
        local ++tests_passed
    }
}

restore

display as result _n "Tests passed: `tests_passed'  Failed: `tests_failed'"
if `tests_failed' > 0 display as error "Some poverty-line tests failed — see above"
assert `tests_failed' == 0
```

## Temporary Files for Test State

Use `tempfile` to save intermediate results that need to persist across `preserve`/`restore` boundaries:

```stata
tempfile pre_test_data
save `pre_test_data'

// ... run tests that modify data ...

// Restore from tempfile instead of preserve/restore
use `pre_test_data', clear
```

Use `tempfile` when:
- You need more than 2 levels of nested save/restore
- You want to compare the state before and after a transformation
- Tests run across multiple do-files that need a shared starting point

```stata
* Compare dataset before/after transformation
tempfile before_ppp after_ppp

preserve
    save `before_ppp'
restore

// Apply PPP conversion
do "${root_code}/transform/apply_ppp.do"
save `after_ppp'

// Load both and compare row counts
use `before_ppp', clear
local n_before = _N
use `after_ppp', clear
local n_after = _N
assert `n_after' == `n_before'    // transformation must not drop rows
```

## Pass/Fail Counter Pattern

The standard test harness pattern for a do-file:

```stata
/* ============================================================
   TEST HARNESS: poverty_indices.do
   Run with: do "${root_code}/tests/test_poverty_indices.do"
   Expected: "Tests passed: N  Failed: 0"
   ============================================================ */

local tests_passed = 0
local tests_failed = 0

* Helper macro to record pass/fail
capture program drop assert_soft
program define assert_soft
    // args: condition  label  tests_failed_var  tests_passed_var
    // Example: assert_soft "inrange(welfare,0,1)" "welfare non-neg" tests_failed tests_passed
    args condition label tf_var tp_var
    capture assert `condition'
    if _rc {
        di as error "FAIL: `label'"
        c_local `tf_var' = ``tf_var'' + 1
    }
    else {
        c_local `tp_var' = ``tp_var'' + 1
    }
end

preserve

// --- Test 1: FGT0 is a proportion ---
poverty welfare [aw=weight], line(1.90)
capture assert inrange(r(head_count), 0, 1)
if _rc { local ++tests_failed ; display as error "FAIL: FGT0 not in [0,1]" }
else   { local ++tests_passed ; display as text  "PASS: FGT0 in [0,1]" }

// --- Test 2: FGT1 ≤ FGT0 ---
capture assert r(poverty_gap) <= r(head_count)
if _rc { local ++tests_failed ; display as error "FAIL: FGT1 > FGT0" }
else   { local ++tests_passed ; display as text  "PASS: FGT1 ≤ FGT0" }

// --- Test 3: Monotonicity across lines ---
local hc_190 = r(head_count)
poverty welfare [aw=weight], line(3.20)
capture assert r(head_count) >= `hc_190'
if _rc { local ++tests_failed ; display as error "FAIL: headcount(3.20) < headcount(1.90)" }
else   { local ++tests_passed ; display as text  "PASS: monotonicity holds" }

restore

// --- Final report ---
display as result _n "================================"
display as result    "Tests passed: `tests_passed'"
display as result    "Tests failed: `tests_failed'"
display as result    "================================"

assert `tests_failed' == 0
```

## Multi-File Test Runner

Create a master do-file that runs all test files and reports aggregate results:

```stata
/* ============================================================
   MASTER TEST RUNNER
   Run: do "${root_code}/tests/run_all_tests.do"
   ============================================================ */

local test_files ///
    "tests/test_data_validation.do" ///
    "tests/test_poverty_indices.do" ///
    "tests/test_ppp_conversion.do"

local total_passed = 0
local total_failed = 0

foreach f of local test_files {
    display as text _n "Running: `f'"
    capture do "`f'"
    if _rc {
        display as error "ERROR in `f': _rc = `_rc'"
        local ++total_failed
    }
    else {
        display as result "DONE: `f'"
    }
}

display as result _n "=========================="
display as result    "Total failed files: `total_failed'"
display as result    "=========================="
assert `total_failed' == 0
```

## Test Data Strategy

Use synthetic data for unit tests and production data for integration tests.

**Unit tests** (logic checks, formula validation): generate minimal synthetic data in-memory.
Never rely on a real survey file — it may not be present on every machine.

```stata
/* Unit test: generate 500 synthetic observations */
clear
set obs 500
set seed 42
gen welfare = runiform() * 100    // continuous, non-negative
gen weight  = runiform() + 0.1   // strictly positive
gen urban   = (runiform() > 0.5)

* Run and assert on synthetic data
poverty welfare [aw=weight], line(10)
assert inrange(r(head_count), 0, 1)
```

**Integration tests**: use `preserve`/`restore` around a real survey file loaded by the master runner.
Keep integration test do-files in a separate folder (`tests/integration/`) to separate from unit tests.

## Test File Naming Convention

- Test files: `tests/test_<module>.do`
- Expected output files: `tests/expected/<module>_results.txt`
- Master runner: `tests/run_all_tests.do`

Keep test do-files short (under 100 lines). If a test file grows large, split by domain (data validation, estimation, output).
