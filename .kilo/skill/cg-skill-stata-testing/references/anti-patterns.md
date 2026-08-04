# Testing Anti-Patterns in Stata

> **Universal coding anti-patterns** (compound quote traps, `*` mid-line comments,
> global macro misuse, etc.) are covered in
> the `references/coding-principles.md` resource in `cg-skill-stata-best-practices`.
> This file covers **testing-specific** anti-patterns only.

---

## 1. Silent-Passing Assertions

❌ **Wrong** — `capture assert` without checking `_rc` does nothing:
```stata
capture assert welfare >= 0    // SILENT — never fails, never tells you anything
```

✅ **Correct** — always inspect `_rc` after `capture assert`:
```stata
capture assert welfare >= 0
if _rc {
    count if welfare < 0
    display as error "FAIL: `r(N)' observations have negative welfare"
    error 459
}
```

**Why it fails**: `capture` suppresses the error and continues. Without checking `_rc`, a failing assertion appears to pass. This is the most dangerous testing anti-pattern — your test suite shows green while the data is wrong.

---

## 2. Not Preserving Data Before Tests

❌ **Wrong** — test modifies master data without isolation:
```stata
// Test PPP conversion
replace welfare = welfare / ppp_2017    // ← permanently modifies the loaded data
assert welfare >= 0
// Now all subsequent code uses converted welfare — not what you intended
```

✅ **Correct** — always wrap data-modifying tests in `preserve`/`restore`:
```stata
preserve
    replace welfare = welfare / ppp_2017
    assert welfare >= 0
restore
// Master data is unchanged
```

**Why it fails**: Without `preserve`/`restore`, a test that modifies data corrupts the state for all subsequent tests and code. The bug may only appear in the third analysis step, far from the test that caused it.

---

## 3. Magic Numbers in Assertions Without Documentation

❌ **Wrong** — threshold has no explanation:
```stata
assert _b[treatment] < 0.15
assert reldif(_b[treatment], 0.0342) < 1e-6
```

✅ **Correct** — document the source and meaning of every threshold:
```stata
* Upper bound: based on literature review (Smith 2022, Table 3)
* Treatment effect > 15 pp is implausibly large for this context
assert _b[treatment] < 0.15

* Cached value from baseline run 2026-04-01, commit a3f4b2c
assert reldif(_b[treatment], 0.0342) < 1e-6
```

**Why it fails**: Undocumented thresholds become mystery numbers. When the assertion fails six months later, no one knows whether to update the threshold or investigate the code. Magic numbers also accumulate stale values when the true expected range changes.

---

## 4. Floating-Point Equality Comparison

❌ **Wrong** — exact equality fails due to floating-point representation:
```stata
assert _b[treatment] == 0.034
assert headcount == 0.4231
```

✅ **Correct** — use `reldif` for relative comparison or `float()` for single-precision values:
```stata
* Relative difference (preferred when expected value is well away from zero)
assert reldif(_b[treatment], 0.034) < 1e-8

* Absolute tolerance (for near-zero values)
assert abs(_b[treatment] - 0.034) < 0.0001

* float() cast for Stata single-precision display values
assert float(headcount) == float(0.4231)
```

**Why it fails**: Stata stores results in IEEE 754 double precision. The value `0.034` cannot be represented exactly, so `== 0.034` may fail even for a "correct" result. `reldif(a, b) = |a - b| / (|b| + 1)` is always safe because it scales by the magnitude of `b`.

---

## 5. Hard-Coded Paths That Break reprun

❌ **Wrong** — absolute paths break reproducibility across machines:
```stata
do "C:/Users/analyst/projects/poverty/tests/test_ppp.do"
use "D:/data/survey_2023.dta", clear
```

✅ **Correct** — use `reproot` globals for all paths:
```stata
* roots() takes NAME IDs (e.g., "code", "data") — NOT absolute paths.
* Absolute paths live in the machine-local reproot-env.yaml (configured once via reproot_setup).
reproot, project("poverty_analysis") roots("code" "data")
do "${root_code}/tests/test_ppp.do"
use "${root_data}/raw/survey_2023.dta", clear
```

**Why it fails**: Hard-coded paths work only on the original machine. On any other machine — or after moving the project folder — every file reference breaks. Hard-coded paths also make `reprun` fail because the path may not exist in a headless or scheduled run environment.

---

## 6. Order-Dependent Tests

❌ **Wrong** — test B can only pass if test A runs first:
```stata
* test A: generate ppp-adjusted welfare
replace welfare = welfare / ppp_2017
* test B: asserts on ppp-adjusted welfare (but breaks if test A is skipped)
assert welfare < 100
```

✅ **Correct** — each test sets up its own state:
```stata
* test A: ppp conversion
preserve
    replace welfare = welfare / ppp_2017
    assert welfare >= 0
restore

* test B: independent check — generates its own transformed variable
preserve
    gen welfare_ppp = welfare / ppp_2017
    assert welfare_ppp < 100
restore
```

**Why it fails**: Order-dependent tests create hidden coupling. Reordering, skipping, or isolating a test causes cascade failures. When test B fails, it's unclear whether the failure is in B or A. Each test must be runnable in isolation.

---

## 7. Undocumented Test Purpose

❌ **Wrong** — no comment explaining what is being tested or why:
```stata
assert _b[treatment] > 0
assert r(p) < 0.05
assert e(N) > 500
```

✅ **Correct** — each assertion has a comment explaining the invariant:
```stata
* Treatment effect must be positive (program designed to increase income)
assert _b[treatment] > 0

* Effect must be statistically significant at 5% (pre-registered hypothesis)
assert r(p) < 0.05

* Minimum sample for reliable standard errors (power calculation: n > 500)
assert e(N) > 500
```

**Why it fails**: Uncommented assertions become opaque when they fail. Maintainers cannot distinguish a legitimate failure from a stale threshold. Comments also document *intent* — if the correct result changes, the comment explains whether the threshold should be updated or the code investigated.

---

## 8. Mixing Assertions with Data-Modifying Code

❌ **Wrong** — assertions interleaved with data transformations:
```stata
gen welfare_ppp = welfare / ppp_2017
assert welfare_ppp >= 0        // ← assertion after generate — hard to isolate
replace welfare_ppp = . if welfare_ppp > 999
assert !missing(welfare_ppp)   // ← this passes trivially after the replace above
```

✅ **Correct** — test the generation logic before capping, then verify the final state separately:
```stata
* --- Transformation (in analysis do-file) ---
* Note: welfare_lcu assumed daily-rate LCU; annual surveys additionally require / 365
gen welfare_ppp = welfare / ppp_2017

* --- Validation (in test do-file or labeled test block) ---
/* TEST: verify PPP conversion formula — re-derive and test before capping */
preserve
    gen welfare_ppp_test = welfare / ppp_2017    // re-derive to test the formula, not the replace
    assert welfare_ppp_test >= 0                  // catches sign errors in the gen formula
restore

/* TEST: verify post-transformation state */
assert welfare_ppp >= 0
assert !missing(welfare_ppp) if !missing(welfare)
```

**Why it fails**: Interleaved assertions hide logical errors. The second assertion (`!missing`) passes only because the first `replace` already removed the invalid values — it tests the `replace`, not the `gen`. Separating test code into labeled blocks makes each assertion's purpose clear and allows the test to catch regressions when the generation logic changes.

---

## 9. Survey Subgroup Analysis with `if` Instead of `subpop()`

❌ **Wrong** — using `if` to restrict to a subgroup gives incorrect variance estimates:
```stata
svy: mean welfare if urban == 1
svy: mean welfare if region == "North"
```

✅ **Correct** — use `subpop()` to preserve the full survey design for variance estimation:
```stata
svy, subpop(if urban == 1): mean welfare
svy, subpop(if region == "North"): mean welfare
```

**Why it fails**: Complex survey designs estimate variance using the full PSU/strata structure across all observations. Conditioning with `if` before `svy:` removes non-subgroup observations before variance computation, discarding cross-stratum covariance information. The result is standard errors that are too small — confidence intervals on rural/urban poverty rates appear more precise than they actually are. For World Bank poverty publications this means falsely narrow uncertainty bounds on official statistics.

The `subpop()` approach keeps all observations in memory during variance estimation but restricts point estimates to the subpopulation — correctly propagating design uncertainty.
