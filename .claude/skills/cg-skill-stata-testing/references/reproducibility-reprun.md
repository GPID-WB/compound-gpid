# Reproducibility & reprun Patterns

> **Full API reference**: Load `cg-skill-stata-best-practices` and read its `packages/repkit.md` resource for complete `reprun`, `reproot`, and `repscan` documentation. This file focuses on **testing patterns** — how to use repkit tools to verify your code is reproducible.

## What is Reproducibility Testing?

A do-file is reproducible if running it twice produces **bit-identical output**. The three most common reproducibility failures in Stata are:

1. **RNG state**: Not setting `set seed` before random processes → different results each run
2. **Non-unique sort**: `sort mpg` with ties resolved differently → different row order → different merge keys
3. **bysort without secondary sort**: `bysort id: gen x = _n` with ties in the by-group → unstable output

## Basic `reprun` Workflow

```stata
* Run your do-file once, then test it:
reprun "analysis/main.do"
```

`reprun` runs the file twice and compares Stata's state at each line. It produces a table with three columns:

| Column | Meaning |
|--------|---------|
| **Seed RNG State** | Random number generator state changed between runs |
| **Sort Order RNG** | Sort order differed (non-unique sort) |
| **Data Checksum** | Dataset changed between the two runs |

**All three should be 0**. Any non-zero value identifies the exact line where reproducibility breaks.

## Reading reprun Output

```stata
reprun "analysis/poverty_analysis.do"
```

Example output requiring action:
```
Line 47: Data Checksum (1)   --> sort welfare         // ← fix: sort welfare id
Line 83: Seed RNG (1)        --> sample 1000          // ← fix: set seed before sample
```

Fix strategy:
- **Seed RNG**: Add `set seed <value>` immediately before the offending line
- **Sort Order RNG / Data Checksum on sort**: Add a tiebreaker: `sort welfare id` instead of `sort welfare`
- **Sort inside `bysort`**: Add a secondary variable: `bysort id (year): gen x = _n`

## Pre-Flight with `repscan`

Before running the full `reprun`, use `repscan` to quickly check for known patterns:

```stata
repscan "analysis/main.do"
```

`repscan` checks for common issues without running the file twice. It is fast and catches:
- `sort` without unique key
- `bysort` without a secondary sort variable
- Random functions without `set seed`

Run `repscan` as the first reproducibility check. Only proceed to `reprun` after `repscan` is clean.

## Portable Paths with `reproot`

Hard-coded paths break reproducibility across machines. Use `reproot` to define a project root and reference all paths relative to it:

```stata
* At the top of master do-file:
* roots() takes NAME IDs defined in reproot-env.yaml — NOT absolute paths.
* Run `reproot_setup` once per machine to configure the machine-local env file.
reproot, project("my_project") roots("code" "data")

* Use the root in all paths:
use "${root_data}/raw/survey.dta", clear
do  "${root_code}/analysis/poverty_analysis.do"
```

In test assertions, use `${root_code}` (not hard-coded paths) to ensure the test works for all team members.

**Never write**:
```stata
use "C:/Users/analyst/projects/poverty/data/survey.dta", clear   // ← BREAKS on other machines
```

## Result Caching and Comparison

To verify that results haven't changed between code revisions, cache expected values to a file and compare on re-run:

### Step 1: Save expected results (run once to establish baseline)
```stata
* After estimation:
regress outcome treatment controls [aw=weight]
local b_treatment = _b[treatment]
local se_treatment = _se[treatment]
local n_obs = e(N)

* Save to cache file
file open cache using "${root_code}/tests/expected_results.txt", write replace
file write cache "b_treatment=" `b_treatment' _n
file write cache "se_treatment=" `se_treatment' _n
file write cache "n_obs=" `n_obs' _n
file close cache
```

### Step 2: Compare against cache (run on every subsequent execution)
```stata
* Load all cached values
local cached_b  = .
local cached_se = .
local cached_n  = .
file open cache using "${root_code}/tests/expected_results.txt", read
file read cache line
while r(eof) == 0 {
    local key = substr("`line'", 1, strpos("`line'", "=") - 1)
    local val = real(substr("`line'", strpos("`line'", "=") + 1, .))
    if "`key'" == "b_treatment"  local cached_b  = `val'
    if "`key'" == "se_treatment" local cached_se = `val'
    if "`key'" == "n_obs"        local cached_n  = `val'
    file read cache line
}
file close cache

* Assert current results match all cached values
regress outcome treatment controls [aw=weight]
assert reldif(_b[treatment],  `cached_b')  < 1e-8
assert reldif(_se[treatment], `cached_se') < 1e-8
assert e(N) == `cached_n'
```

For simpler caching, use a CSV file read with `import delimited` and check with `assert reldif()`.

## Common Reproducibility Failures and Fixes

| Failure | Symptom | Fix |
|---------|---------|-----|
| Missing `set seed` | Seed RNG column non-zero | Add `set seed 12345` before `sample`, `runiform()`, etc. |
| Non-unique sort | Sort Order RNG non-zero | Always sort by unique key: `sort welfare id` |
| `bysort` without secondary | Data Checksum non-zero | Use `bysort id (year): ...` |
| Hard-coded paths | Fails on other machines | Use `reproot` globals |
| `tempfile` across runs | Different temp names | `tempfile` names are local — this is fine |
| `preserve`/`restore` with sort | Sort order not restored | Explicitly re-sort after `restore` |

## Integrating reprun into a Test Workflow

```stata
/* ============================================================
   REPRODUCIBILITY TEST
   Run this do-file at the end of development to verify all
   analysis scripts are reproducible.
   ============================================================ */

local analysis_scripts ///
    "analysis/01_clean.do" ///
    "analysis/02_poverty.do" ///
    "analysis/03_tables.do"
local total_failed = 0

foreach script of local analysis_scripts {
    display as text _n "Testing: `script'"
    capture reprun "`script'"
    if _rc {
        // reprun exited with error or detected non-reproducible output
        display as error "FAIL: `script' is NOT reproducible (rc = `_rc')"
        local ++total_failed
    }
    else {
        display as result "PASS: `script' is reproducible"
    }
}

display as result _n "All reproducibility tests passed."
assert `total_failed' == 0
// Note: verify `capture reprun` exit code behavior against your installed repkit version.
// If reprun always exits 0 (only printing a report), check the SMCL output file instead.
// See: help reprun for _rc documentation.
```
