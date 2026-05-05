# Data Validation Patterns in Stata

Run these checks at the top of analysis do-files, after each merge, and before any estimation. Validation must fail loudly — never silently skip bad data.

## Uniqueness Checks

```stata
* Assert dataset is uniquely identified by key variables
isid country_code year        // halts if duplicates found

* Report duplicates without halting (for diagnosis)
duplicates report country_code year

* Tag duplicates for inspection
duplicates tag country_code year, gen(dup_flag)
count if dup_flag > 0    // sets r(N) — duplicates tag only sets r(unique_tag)
if r(N) > 0 display as error "FAIL: `r(N)' observations have duplicates on country_code + year"
assert dup_flag == 0
```

`isid` is preferred for hard assertions. `duplicates report` is for diagnosis. Never use `duplicates drop` without first asserting the duplicate rate is expected.

## Missingness Validation

```stata
* Tabulate missing values across all variables
misstable summarize

* Assert no missing values on critical variables
assert !missing(welfare)
assert !missing(weight)

* Count and report before asserting
count if missing(welfare)
if r(N) > 0 {
    display as error "FAIL: `r(N)' observations have missing welfare"
    error 459
}

* Assert missing within a subgroup
assert !missing(welfare) if !missing(weight)
```

## Value Range Checks

```stata
* Assert variable is within expected bounds
assert welfare_ppp >= 0 & !missing(welfare_ppp)    // non-negative and non-missing welfare
// Note: inrange(welfare_ppp, 0, .) silently passes missing values (Stata: . > any number)
assert inrange(headcount, 0, 1)        // poverty rate is a proportion
assert inrange(ppp_2017, 0.01, 10000) // plausible PPP range

* Assert categorical variable has only expected values
assert inlist(survey_type, "IHS", "HIES", "LSMS", "SES")

* Compound range assertion with diagnostics
count if welfare_ppp < 0
if r(N) > 0 {
    display as error "FAIL: `r(N)' observations have negative welfare_ppp"
    error 459
}
```

## Pre-FGT Validation Block

Always run this guard before any `poverty` command. Zero welfare produces FGT1 = 1 (maximum gap);
negative welfare produces FGT1 > 1 — both values corrupt any headcount or poverty gap reported.

```stata
/* Pre-FGT guard: run before any poverty command */
assert !missing(welfare)    // missing welfare silently inflates the denominator
assert welfare > 0          // zero or negative welfare produces invalid FGT (gap ≥ 1)
assert !missing(weight)     // missing weight passes the > 0 check (Stata: . > any number)
assert weight > 0           // zero weight biases all weighted estimates
```

## Panel Structure Validation

```stata
* Declare panel structure
xtset country_code year

* Assert balanced panel (expected N * T observations)
local expected_obs = `n_countries' * `n_years'
count
assert r(N) == `expected_obs'

* Assert no gaps in time series for each unit
xtset country_code year
assert r(balanced) == "strongly balanced"    // r() from xtset, not e()

* Alternative: assert using xtdescribe
quietly xtdescribe
assert r(T_min) == r(T_max)    // all panels have the same time span
```

## Survey Design Checks

```stata
* Validate PSU/strata/weight variables exist and are non-missing
confirm numeric variable psu strata weight
assert !missing(psu)
assert !missing(strata)
assert !missing(weight)

* Assert all weights are positive
count if weight <= 0
assert r(N) == 0

* Assert weights sum to expected population
summarize weight
local total_weight = r(sum)
assert inrange(`total_weight', `pop_lower', `pop_upper')

* Guard against singleton PSUs — 1 PSU per stratum makes DEFF estimation undefined
bysort strata: assert _N >= 2    // use singleunit(centered) for confirmed certainty strata

* Declare survey design and run a test estimate
svyset psu [pw=weight], strata(strata) singleunit(centered)
svy: mean welfare
```

## Cross-Dataset Consistency

Always validate merge results immediately after `merge`. Never proceed with a `:3 not matched` merge silently.

```stata
* Validate merge completeness
merge 1:1 country_code year using ppp_factors
assert _merge == 3    // all records matched on both sides
drop _merge

* Partial merge with diagnostics
merge m:1 country_code using country_metadata, keep(master match)
count if _merge == 1
if r(N) > 0 {
    display as text "INFO: `r(N)' observations had no country metadata"
}
drop _merge

* Row count consistency check
local pre_merge_n = _N
merge ...
local post_merge_n = _N
assert `post_merge_n' == `pre_merge_n'    // 1:1 merge should not change row count
```

## Type Safety

```stata
* Confirm variable type before operations
confirm numeric variable welfare weight
confirm string variable country_code survey_acronym

* Assert string variable has expected length
assert strlen(country_code) == 3    // ISO 3-letter codes

* Check for encoded variables
capture confirm byte variable survey_type_enc
if _rc {
    display as error "FAIL: survey_type_enc is not encoded (byte)"
    error 7
}
```

## Pre-Analysis Checklist Pattern

Structure validation code as a named block at the top of each do-file:

```stata
/* ============================================================
   PRE-ANALYSIS VALIDATION
   Purpose: Assert all input assumptions before estimation.
   Fail loudly if violated — do not silently skip.
   ============================================================ */

* 1. Uniqueness
isid welfare_id

* 2. No missing on analysis variables
foreach v of varlist welfare weight strata psu {
    count if missing(`v')
    assert r(N) == 0
}

* 3. Non-negative welfare (check missing separately: . > 0 is true in Stata)
assert !missing(welfare)
assert welfare >= 0

* 4. Positive weights (check missing separately: . > 0 is true in Stata)
assert !missing(weight)
assert weight > 0

* 5. Poverty line is positive
assert `poverty_line' > 0

display as result "VALIDATION PASSED"
```
