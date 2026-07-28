# Stata Coding Principles

Universal principles for writing correct, reproducible Stata code. Each section
covers a pattern that produces silent bugs when violated — code that runs without
errors but yields wrong results.

---

## 1. Compound Double Quotes

Plain quotes `"..."` break silently when a macro value contains embedded quotes,
apostrophes, or leading/trailing spaces. Compound double quotes handle any string
content.

**Syntax:** opening delimiter is backtick + double-quote (`` ` `` + `"`), closing
delimiter is double-quote + single-quote (`"` + `'`). Regular double quotes
(`""`, ASCII 34) can appear freely inside compound double quotes.

```stata
* BREAKS silently — the label contains double quotes
local desc "Results "adjusted" for inflation"
label variable income "`desc'"
// Stata parses this as: label variable income "Results "  (truncated at inner quote)

* RIGHT — compound quotes handle embedded quotes
local desc `"Results "adjusted" for inflation"'
label variable income `"`desc'"'
```

```stata
* File paths are unpredictable — always use compound quotes with tempfile
tempfile merged
save `"`merged'"', replace
use  `"`merged'"', clear

* Strings with apostrophes (e.g., country names, labels)
local country `"Côte d'Ivoire"'
display `"`country'"'          // safe
notes: Survey: `"`country'"' 2022
```

**Rule of thumb:** use compound quotes whenever the macro value:
- Will be used in a `label`, `notes`, or `display` statement
- Comes from user input, a file name, or a variable
- Contains or might contain embedded quotes, apostrophes, or special characters
- Is a `tempfile` path — always, without exception

---

## 2. Eager Macro Expansion

Macros store a **frozen string**, not a live formula. When one macro references
another, the inner macro is resolved immediately at assignment time. If the source
macro changes later, the derived macro does not update.

```stata
* --- THE TRAP: eager expansion freezes the value at definition time ---
local suffix "_pc"
local varname "cons`suffix'"    // `suffix' expands NOW → varname = "cons_pc"

display "`varname'"             // Prints: cons_pc  ✓

local suffix "_ppp"
display "`varname'"             // Prints: cons_pc  ✗ — NOT "cons_ppp"

* --- WHERE THIS BITES: a loop that changes the inner macro ---
local base "income"
local fullvar "`base'_annual"   // Expands NOW → fullvar = "income_annual"

foreach b in income expenditure {
    display "`fullvar'"         // Prints "income_annual" EVERY iteration
                                // never becomes "expenditure_annual"
}

* --- THE FIX: rebuild the derived macro inside the loop ---
foreach b in income expenditure {
    local fullvar "`b'_annual"  // Re-expand on each iteration
    display "`fullvar'"         // Prints: income_annual, then expenditure_annual  ✓
}
```

**Rule:** A macro stores a string, not a formula. Any backtick references inside
it are resolved once, at the moment the `local` (or `global`) command runs. If
you need the reference to "stay live," rebuild the macro after every change to
its inputs.

---

## 3. Stored Results Disappear After the Next Command

After any `r`-class or `e`-class command, calling **another command of the same
class** immediately overwrites the stored results. There is no warning.

```stata
* WRONG — r(mean) from x1 is silently overwritten
summarize x1
summarize x2      // r(mean) is now x2's mean — x1's is GONE
display r(mean)   // prints x2 mean, not x1 mean

* RIGHT — save to locals immediately after the command
summarize x1
local mean_x1 = r(mean)    // save NOW, before anything else
local sd_x1   = r(sd)

summarize x2
local mean_x2 = r(mean)

display "x1 mean: `mean_x1'   x2 mean: `mean_x2'"
```

```stata
* Same problem with estimation results
regress y x1 x2
local r2 = e(r2)    // save r-squared IMMEDIATELY
local N  = e(N)

regress y x1 x2 x3  // e(r2) is now overwritten
// `r2' and `N' are safe — they were saved to locals before this line
```

**Rule:** Immediately after any estimation or summary command, if you need any
stored result, save it to a local. Do not assume `r()` or `e()` will survive
even one more line of code.

---

## 4. `subpop()` vs `if` with `svy:` Commands

Using an `if` condition with `svy:` commands to restrict to subgroups corrupts
variance estimation. The `if` qualifier restricts the sample *before* variance
estimation, discarding PSUs and strata from the effective design.

```stata
* WRONG — svy with if changes the effective survey design
svy: mean income if is_urban == 1

* RIGHT — subpop() preserves the full design
svy, subpop(is_urban): mean income

* RIGHT — create the subpop indicator first when the condition is complex
gen in_subpop = (region == "North") & (year == 2022)
svy, subpop(in_subpop): mean income
```

**Why it matters:** Standard errors can differ by 20–30% or more in clustered
samples with small subgroups. Using `if` typically understates SEs by discarding
PSUs with no observations in the subgroup.

**Rule:** Any time you work with `svy:` commands and need subgroup estimates,
use `subpop()` — never `if`.

---

## 5. Clustering at the Correct Level

Standard errors must be clustered at the level of treatment assignment or
correlation, not at the individual observation level.

```stata
* WRONG — treatment assigned at school level, clustered at student
regress test_score treatment age, vce(robust)      // too small SEs

* RIGHT — cluster at the level of treatment assignment
regress test_score treatment age, vce(cluster school_id)

* WRONG — errors correlated at district level, clustered at school
reghdfe y treatment controls, absorb(school year) vce(cluster school_id)

* RIGHT — cluster at the level where errors correlate
reghdfe y treatment controls, absorb(school year) vce(cluster district_id)
```

**Rules:**
- Cluster at the level of treatment assignment or higher
- When treatment varies at a higher level than the unit of observation, cluster
  at the treatment level
- With very few clusters (< 40), consider wild cluster bootstrap (`boottest`)

---

## 6. Anti-Patterns Checklist

Patterns that produce wrong results without erroring. Review this list whenever
reading or writing Stata code.

### 6.1 `=` vs `==` in `if` Conditions

`=` is assignment; in some Stata contexts an `if (x = 0)` expression evaluates
to 0 (false) for all observations, silently producing all-missing results.

```stata
* WRONG
generate flag = 1 if (income = 0)
keep if (country = "USA")

* RIGHT
generate flag = 1 if (income == 0)
keep if (country == "USA")
```

### 6.2 String vs Numeric Type Confusion

Stata does not error when you compare a string variable to a number or vice
versa — it silently produces no matches.

```stata
* Check storage type before writing conditions
describe country_code year
codebook country_code year

* WRONG — country_code stored as string "840"
keep if country_code == 840

* WRONG — year stored as numeric 2022
keep if year == "2022"

* RIGHT
keep if country_code == "840"    // string variable
keep if year == 2022             // numeric variable
```

### 6.3 `replace` Without a Units Comment

Unit-transforming `replace` commands must document what units the variable holds
before and after. Without this, future readers have no way to verify correctness.

```stata
* WRONG
replace price = price * 1.08

* RIGHT
// price is currently: pre-tax USD
replace price = price * 1.08
// price is now: post-tax USD (8% sales tax applied)
label variable price "Post-tax price (USD)"
```

### 6.4 Missing `quietly` in Loops and Programs

Omitting `quietly` inside loops prints output for every iteration, burying
meaningful output and slowing execution.

```stata
* WRONG — prints output for every iteration
forvalues i = 1/100 {
    summarize var_`i'
    regress y var_`i' controls
}

* RIGHT — suppress by default, reveal only what you intend
quietly forvalues i = 1/100 {
    summarize var_`i'
    local mean_`i' = r(mean)
    regress y var_`i' controls
    local r2_`i' = e(r2)
}

* Use noisily explicitly when you want specific output
quietly foreach v of varlist x1 x2 x3 {
    noisily regress y `v' controls    // only this command outputs
}
```

### 6.5 `merge` Without Checking `_merge`

Unmatched observations silently enter the dataset when `_merge` is not checked.

```stata
* WRONG
merge 1:1 id using "supplemental.dta"
drop _merge

* RIGHT
merge 1:1 id using "supplemental.dta"
tabulate _merge
assert _merge == 3   // stops if any mismatches — fix the data, don't ignore
drop _merge

* When unmatched observations are intentional and documented
merge 1:1 id using "supplemental.dta", keep(1 3) nogenerate
```

### 6.6 `append` Losing Variable Labels

When appending datasets where a variable exists in only one file, Stata assigns
the label from whichever file defines it — or leaves it empty.

```stata
* Store labels before appending
local varlist x1 x2 x3
foreach v of varlist `varlist' {
    local label_`v' : variable label `v'
}

append using "other_data.dta"

* Re-apply labels after appending
foreach v of varlist `varlist' {
    label variable `v' `"`label_`v''"'
}
```

### 6.7 Globals in Production Do-files

Globals defined in analysis do-files persist into subsequent sessions and other
do-files, producing non-reproducible results across users and runs.

```stata
* WRONG — globals pollute the Stata session
global analysis_var "income"
global year 2022

* RIGHT — use locals for everything within scripts
local analysis_var "income"
local year 2022

* Acceptable global use: root paths only, in master do-files only
// master.do:
global project_root "C:/Users/myname/project"
```

### 6.8 Missing `set more off` and `version`

Do-files without `set more off` pause for user input when run unattended.
Missing `version` means behavior can change silently when Stata is upgraded.

```stata
* WRONG
clear all
use "data/myfile.dta", clear

* RIGHT — every production do-file starts with these
version 17
set more off
set linesize 120
clear all
macro drop _all
```

### 6.9 `log using` Without `replace` or `append`

Stata errors if the log file already exists — which it always does after the
first run — unless a mode is specified.

```stata
* WRONG — errors on second run
log using "output/analysis.log"

* RIGHT
capture log close
log using "output/analysis.log", replace text
// ... do-file body ...
log close
```

### 6.10 `forvalues` When `foreach` Is Correct

`forvalues` iterates over sequential integer ranges only. Using it for variable
name lists, string lists, or non-sequential numbers causes errors or wrong results.

```stata
* WRONG
forvalues v = income education age {   // syntax error
    summarize `v'
}

forvalues year = 2010 2015 2019 {      // syntax error — not sequential
    use "data_`year'.dta", clear
}

* RIGHT
foreach v of varlist income education age {
    quietly summarize `v'
    display "`v': mean = " r(mean)
}

foreach year in 2010 2015 2019 {
    use "data_`year'.dta", clear
}

* forvalues IS correct for sequential integers
forvalues i = 1/100 {
    generate x_`i' = .
}
```

### 6.11 Unweighted Statistics on Survey Data

On complex survey data, unweighted statistics are biased for population
parameters. Every statistical command on survey data must use `svy:` prefix or
explicit `[pw=weight]` syntax.

```stata
* WRONG — unweighted
summarize income
regress ln_income education age

* RIGHT — always use survey weights
svyset psu [pw=weight], strata(stratum)
svy: mean income
svy: regress ln_income education age
```

### 6.12 `if` Instead of `subpop()` for Subgroup Analysis

See §4 above for full explanation.

```stata
* WRONG
svy: mean income if region == 1

* RIGHT
svy, subpop(if region == 1): mean income
```

### 6.13 Missing Overlap Check Before Matching

Running propensity score matching without checking common support produces
extrapolated estimates when treated and control groups don't overlap.

```stata
* Always check overlap before matching
logit treated x1 x2 x3
predict pscore, pr

// Visual overlap check
twoway (histogram pscore if treated == 1, color(blue%30)) ///
       (histogram pscore if treated == 0, color(red%30)), ///
    legend(order(1 "Treated" 2 "Control")) ///
    title("Propensity Score Overlap Check")

// Impose common support
psmatch2 treated x1 x2 x3, outcome(y) common caliper(0.05)

// Balance check — always verify after matching
pstest x1 x2 x3, both
```

### 6.14 P-Hacking via Specification Search

Running many specifications and reporting only the one with a significant result
is not robustness — it inflates false positive rates and invalidates inference.

```stata
* WRONG — trying specifications until p < 0.05
regress y treat x1 x2              // p = 0.12, not reported
regress y treat x1 x3              // p = 0.08, not reported
regress y treat x1 x2 x3           // p = 0.04 ← "use this one"

* RIGHT — commit specifications before looking at results
// Write down all specifications you intend to run, get agreement,
// then run all of them and report all results regardless of significance
```

### 6.15 Missing Values in Inequality Measures

Some inequality commands silently drop missings; others treat them as zeros,
producing wildly wrong Gini coefficients or other inequality indices.

```stata
* WRONG — behavior with missing values is command-dependent
ineqdeco income

* RIGHT — always restrict to non-missing observations explicitly
ineqdeco income if !missing(income) [pw=weight]

* BETTER — assert no missings in the analysis sample
assert !missing(income) if in_sample == 1
ineqdeco income if in_sample == 1 [pw=weight]
```

### 6.16 `bysort` Without a Secondary Sort Variable

When `bysort` is used for order-sensitive operations (row numbering, cumulative
sums, lags) and the by-variable does not uniquely identify observations, Stata
breaks ties in an arbitrary and non-deterministic order. Results differ between
runs and across machines — `reprun` will flag this as a reproducibility failure.

```stata
* WRONG — sort order within hhid is arbitrary when multiple years exist
bysort hhid: gen obs_n = _n

* WRONG — cumulative sum depends on arbitrary observation order
bysort hhid: gen cum_income = sum(income)

* RIGHT — always add a secondary sort variable in parentheses
bysort hhid (year): gen obs_n = _n            // deterministic: earlier years first
bysort hhid (year): gen cum_income = sum(income)  // reproducible cumulative sum

* RIGHT — multiple secondary sort variables when needed
bysort country_code year (hhid member_id): gen seq = _n
```

**Test:** run `reprun` on any do-file that uses `bysort`. A "Sort Order RNG
DIFF" in the output means at least one `bysort` lacks a secondary sort.

---

## 7. Random Number Seeds

Any command that uses Stata's random number generator (RNG) — `runiform()`,
`rnormal()`, `bootstrap`, `simulate`, `sample`, `splitsample`, `drawnorm`,
`permute` — produces different results on every run unless the seed is explicitly
set beforehand.

```stata
* WRONG — different results every run
gen assignment = runiform() < 0.5
bootstrap, reps(500): regress y x
sample 10

* RIGHT — set seed before any random process
set seed 20240301              // date-based seeds are readable and memorable
gen assignment = runiform() < 0.5

set seed 20240301
bootstrap, reps(500): regress y x

set seed 20240301
sample 10
```

```stata
* In a loop — reset the seed at the start of the full loop, not inside it
set seed 99999
forvalues i = 1/100 {
    simulate, reps(200): regress y x
    // resetting inside the loop makes each rep's draw depend on iteration count
}
```

**Rules:**
- Set `set seed <integer>` immediately before the first random call in each do-file
- Use a memorable, documented seed value (e.g., a date in YYYYMMDD format)
- Never reset the seed inside a loop — this breaks the independence of draws
- Run `repscan` to locate all random commands in a do-file
- Run `reprun` to confirm the do-file is fully deterministic between runs
