# Data Management

Core patterns for data manipulation in Stata. These are the idioms Copilot
most frequently gets wrong in ways that either corrupt data silently or produce
non-reproducible results.

---

## 1. `tempvar`, `tempname`, `tempfile` — Never Invent Temporary Names

Stata provides three commands that create guaranteed-unique, automatically
cleaned-up temporary objects. Use them exclusively. Never invent `_temp_` prefixes.

### `tempvar` — temporary variables in memory

```stata
* WRONG — manual naming pollutes the dataset and is easy to forget to drop
generate _temp_log_welfare = log(welfare)
// ... use it ...
drop _temp_log_welfare   // easy to forget; variable stays in dataset if program exits early

* RIGHT — tempvar creates a unique name and drops it automatically at program/do-file end
tempvar log_welfare
generate `log_welfare' = log(welfare)
// No drop needed — `log_welfare' vanishes when the program or do-file ends
// The actual variable name in memory is something like __000001 — never reference it directly
```

Multiple tempvars in one call:
```stata
tempvar log_welfare welfare_sq residual flag_outlier
generate `log_welfare'    = log(welfare)
generate `welfare_sq'     = welfare^2
// All four are cleaned up automatically
```

### `tempname` — temporary scalar, matrix, or macro names

```stata
* For scalars and matrices stored in r() or e() — or just computed in-memory
tempname poverty_mat vcov_mat threshold

scalar `threshold' = 2.15
matrix `poverty_mat' = J(10, 3, .)
matrix `vcov_mat'    = I(3)
// Cleaned up automatically
```

### `tempfile` — temporary .dta files on disk

```stata
* ALWAYS use compound quotes with tempfile — paths may contain spaces
tempfile hh_collapsed region_totals

preserve
    collapse (mean) welfare [pw=weight], by(region year)
    save `"`hh_collapsed'"', replace
restore

merge m:1 region year using `"`hh_collapsed'"', nogenerate

* Multi-tempfile workflow
tempfile raw_merged poverty_flags final

use "data/households.dta", clear
merge 1:1 hhid using "data/expenditure.dta", keep(3) nogenerate
save `"`raw_merged'"'

// ... later ...
use `"`raw_merged'"', clear
```

---

## 2. `preserve`/`restore` vs `tempfile` — Choosing the Right Tool

Both allow you to work with a transformed version of data and then return to the
original. The choice matters for correctness and clarity.

### `preserve`/`restore` — for within-do-file transforms

Use when: you need a temporary reshape, collapse, or filter *within a single
do-file*, and you will restore before the do-file ends.

```stata
preserve
    keep if year == 2022
    collapse (mean) welfare (sum) pop [pw=weight], by(country region)
    label variable welfare "Mean welfare 2022"
    export excel using "output/welfare_2022.xlsx", firstrow(variables) replace
restore
// Back to the full dataset — all original variables and observations intact
```

**Limits of `preserve`:**
- Only one level deep — `preserve` inside a `preserve` block errors
- Does not survive a program call — if you `preserve`, call a program, then the
  program exits normally or with error, `restore` still works, but the program
  itself cannot `restore` the outer `preserve`
- Does not survive `clear` or loading a new dataset

### `tempfile` — when data must survive program boundaries

Use when: the transformed data needs to be referenced after a program call,
used in a merge back into the original data, or passed between do-files.

```stata
* Pattern: transform → save to tempfile → restore → merge back
tempfile welfare_regional

preserve
    collapse (mean) welfare_pc = welfare [pw=weight], by(country year)
    save `"`welfare_regional'"'
restore

merge m:1 country year using `"`welfare_regional'"', nogenerate

* Pattern: build a dataset incrementally across a loop
tempfile combined
save `"`combined'"', emptyok replace   // create empty file to append to

foreach year of numlist 2010/2022 {
    use "data/raw/hh_`year'.dta", clear
    generate survey_year = `year'
    append using `"`combined'"'
    save `"`combined'"', replace
}

use `"`combined'"', clear
```

---

## 3. `by:` vs `bysort:` — Sort Order and Order-Sensitive Operations

This distinction produces non-reproducible results when ignored. Copilot
almost always generates `bysort` without a secondary sort variable — this is
correct for order-independent operations and wrong for everything else.

### The core difference

```stata
* by: — requires data to already be sorted; errors if not sorted correctly
sort country year
by country: generate obs_in_country = _n        // works — data is pre-sorted

* bysort: — sorts first, then processes; always safe for order-independent ops
bysort country: generate obs_in_country = _n    // works — but what is _n?
// WARNING: within each country, obs are in arbitrary order unless secondary sort specified
```

### Secondary sort — critical for order-sensitive operations

The variable in parentheses after the by-variable specifies the **within-group
sort order**. Omitting it for any order-sensitive operation produces
non-reproducible results.

```stata
* Order-sensitive operations — ALWAYS specify secondary sort
bysort hhid (year): generate obs_number    = _n           // 1,2,3,... within household
bysort hhid (year): generate total_obs     = _N           // total obs in household
bysort hhid (year): generate is_first_year = (_n == 1)    // flag earliest year
bysort hhid (year): generate is_last_year  = (_n == _N)   // flag latest year
bysort hhid (year): generate lag_welfare   = welfare[_n-1]  // previous year's welfare
bysort hhid (year): generate lead_welfare  = welfare[_n+1]  // next year's welfare
bysort hhid (year): generate cum_welfare   = sum(welfare)   // cumulative sum by year

* Order-independent operations — secondary sort optional but documents intent
bysort country (year): egen mean_welfare = mean(welfare)    // same regardless of order
bysort country (year): egen sd_welfare   = sd(welfare)
```

### Multiple sort variables in parentheses

```stata
* Sort within household by year, then by month within year
bysort hhid (year month): generate period_num = _n

* Sort descending — Stata doesn't support desc in bysort directly
gsort hhid -year         // sort descending by year within household
by hhid: generate rank_year = _n    // now _n=1 is most recent year
```

---

## 4. `_n`, `_N`, and By-group Idioms

Complete reference for observation-level operations within groups.

```stata
* Basic identifiers
bysort hhid (year): generate obs_num   = _n    // 1,2,3,...
bysort hhid (year): generate total_obs = _N    // same for all obs in group

* Flags
bysort hhid (year): generate is_first  = (_n == 1)
bysort hhid (year): generate is_last   = (_n == _N)
bysort hhid (year): generate is_single = (_N == 1)   // singleton groups

* Lags and leads — always check bounds to avoid missing values at edges
bysort hhid (year): generate welfare_lag  = welfare[_n-1]
bysort hhid (year): generate welfare_lead = welfare[_n+1]
bysort hhid (year): generate welfare_lag2 = welfare[_n-2]

* Growth rates
bysort hhid (year): generate welfare_growth = (welfare - welfare[_n-1]) / welfare[_n-1]
replace welfare_growth = . if _n == 1   // first observation has no lag

* Carry forward last non-missing value (panel gap fill)
bysort hhid (year): replace welfare = welfare[_n-1] if missing(welfare) & _n > 1

* Cumulative operations
bysort country (year): generate cum_pop     = sum(pop)
bysort country (year): generate running_avg = sum(welfare) / _n

* Select first/last observation per group
bysort hhid (year): keep if _n == 1     // keep earliest observation per household
bysort hhid (year): keep if _n == _N    // keep latest observation per household
```

---

## 5. `merge` — Correct Patterns and Mandatory Checks

Copilot generates `merge` commands without the required post-merge checks.
This silently accepts unmatched observations.

```stata
* Always check _merge after every merge
merge 1:1 hhid using "data/hh_characteristics.dta"

* MANDATORY — check merge results before proceeding
tabulate _merge
// Expected for required matches: all observations should be _merge==3

* Assert the expected merge result — fails loudly if violated
assert _merge == 3   // if any unmatched obs exist, do-file stops with an error

* Drop _merge before the next merge
drop _merge

* Selective merge — keep only matched observations
merge 1:1 hhid using "data/hh_characteristics.dta", keep(3) nogenerate
// keep(3) = keep only matched; nogenerate = don't create _merge variable
// Use only when unmatched observations are expected and intentionally discarded

* Many-to-one merge — household data onto individual data
merge m:1 hhid using "data/hh_level.dta", keep(1 3) nogenerate
// keep(1 3) = keep master-only and matched — individual may not have hh match

* Diagnose a failed merge
merge 1:1 hhid using "data/hh_characteristics.dta"
tabulate _merge
list hhid if _merge == 1   // in master only — not in using
list hhid if _merge == 2   // in using only — not in master
```
