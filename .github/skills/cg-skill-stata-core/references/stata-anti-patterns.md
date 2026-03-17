# Stata Anti-Patterns

Ten patterns Copilot generates incorrectly. Consult this file when reviewing
any Copilot-generated Stata code. Each entry: what the pattern is, what goes
wrong, wrong example, correct example.

---

## 1. `=` vs `==` in `if` Conditions

**Problem:** Stata accepts `=` in some `if` conditions and produces wrong
results without erroring. Copilot generates `=` when it means `==` in
`generate`, `replace`, and `keep`/`drop` conditions.

```stata
* WRONG — this is an assignment expression, not a test
generate flag = 1 if income = 0
keep if country = "ETH"

* RIGHT
generate flag = 1 if income == 0
keep if country == "ETH"
```

**Why it matters:** In some Stata contexts `if income = 0` evaluates as the
scalar value 0 (false) for all observations, silently producing all-missing
or all-zero results instead of a conditional.

---

## 2. String vs Numeric Type Confusion in `if`

**Problem:** Copilot frequently generates numeric comparisons for string
variables and string comparisons for numeric variables. Stata does not
error — it silently produces no matches.

```stata
* WRONG — country is stored as string "840", not numeric 840
keep if country_code == 840

* WRONG — year is stored as numeric 2022, not string "2022"
keep if year == "2022"

* RIGHT — match the variable's actual storage type
keep if country_code == "840"    // string variable
keep if year == 2022             // numeric variable

* Diagnose storage type before writing conditions
describe country_code year
codebook country_code year
```

**Prevention:** Run `describe varname` or `codebook varname` before writing
`if` conditions on any variable you haven't explicitly created in this do-file.

---

## 3. `replace` Without a Units Comment

**Problem:** Copilot generates unit-transforming `replace` commands with no
documentation of what units the variable is in before and after. In welfare
analysis (monthly vs annual, local currency vs PPP USD), this is catastrophic.

```stata
* WRONG — what were the units before? What are they after?
replace welfare = welfare * 12
replace welfare = welfare / cpi_index
replace welfare = welfare * ppp_factor

* RIGHT — document units before and after every transformation
* welfare is currently: monthly per-capita consumption, LCU nominal
replace welfare = welfare * 12
* welfare is now: annual per-capita consumption, LCU nominal

replace welfare = welfare / cpi_2017
* welfare is now: annual per-capita consumption, LCU 2017 real

replace welfare = welfare / ppp_2017
* welfare is now: annual per-capita consumption, 2017 PPP USD
```

**Rule:** Every `replace` that transforms units must have a before/after
comment. Label the variable after the final transformation with the full
unit description.

---

## 4. Forgetting `quietly` in Loops and Programs

**Problem:** Copilot omits `quietly` on commands inside loops and programs,
causing enormous log output that obscures real results and slows execution.

```stata
* WRONG — prints summary output for every iteration
forvalues i = 1/100 {
    summarize welfare_`i'
    regress welfare_`i' urban age education
}

* RIGHT — suppress output inside loops; display only what you intend
forvalues i = 1/100 {
    quietly summarize welfare_`i'
    local mean_`i' = r(mean)
    
    quietly regress welfare_`i' urban age education
    local r2_`i' = e(r2)
}

display "Completed 100 regressions"
```

**Exceptions:** Use `noisily` explicitly when you want to see output from a
specific iteration during debugging: `noisily regress welfare urban`.

---

## 5. `merge` Without Checking `_merge`

**Problem:** Copilot generates `merge` commands without the mandatory
post-merge check. Unmatched observations silently enter the dataset.

```stata
* WRONG — no check; unmatched observations silently accepted
merge 1:1 hhid using "data/hh_characteristics.dta"
drop _merge

* RIGHT — always check, assert expected result, then drop
merge 1:1 hhid using "data/hh_characteristics.dta"
tabulate _merge
assert _merge == 3   // stops execution if any unmatched obs — fix the data, don't ignore
drop _merge

* When unmatched observations are intentional and expected
merge 1:1 hhid using "data/supplemental.dta", keep(1 3) nogenerate
* keep(1 3) documents that master-only observations are intentionally kept
* nogenerate avoids creating _merge when you've already decided what to keep
```

---

## 6. `append` Losing Variable Labels

**Problem:** When appending datasets where a variable exists in only one of
the files, Stata uses the label from whichever file defines it. If the master
file doesn't have the variable, the label comes from the using file — or is
missing entirely. Copilot never flags this.

```stata
* This can lose labels silently
append using "data/hh_2022.dta"

* RIGHT — explicitly set labels after appending when label consistency matters
append using "data/hh_2022.dta"
label variable welfare    "Monthly per-capita welfare (2017 PPP USD)"
label variable survey_yr  "Survey reference year"
label variable country    "ISO3 country code"

* Check what happened to labels
describe welfare survey_yr country
```

---

## 7. Global Macros in Production Do-files

**Problem:** Copilot defines globals freely throughout do-files. Globals from
one run persist into subsequent interactive sessions and other do-files.

```stata
* WRONG — globals defined in analysis do-files
global welfare_var "cons_pc"
global pov_line 2.15
global survey_year 2022

* WRONG — globals for anything other than root paths
global output_file "results_table.xlsx"

* RIGHT — use locals for everything except root paths in master.do
local welfare_var "cons_pc"
local pov_line    2.15
local survey_year 2022

* The only acceptable global: root paths, in master.do only
* master.do:
global gpid_root "C:/WBG/gpid-analysis"
global gpid_data "${gpid_root}/data"
```

---

## 8. Missing `set more off` and `version`

**Problem:** Do-files without `set more off` pause for user input when run
unattended (batch mode, scheduled jobs, automated pipelines). Missing `version`
means behavior can change silently when Stata is upgraded.

```stata
* WRONG — do-file will pause at output breaks; behavior undefined across Stata versions
clear all
use "data/households.dta", clear

* RIGHT — every production do-file starts with these lines
version 17           // require Stata 17+; errors on older versions
set more off         // never pause for output; required for batch execution
set linesize 120     // consistent log formatting
clear all
macro drop _all
```

---

## 9. `log using` Without `replace` or `append`

**Problem:** Copilot generates `log using "file.log"` without a mode
specifier. Stata errors if the log file already exists — which it always
does after the first run.

```stata
* WRONG — errors on second and subsequent runs
log using "output/analysis.log"

* RIGHT — always specify replace or append
log using "output/analysis.log", replace   // overwrite previous log
log using "output/analysis.log", append    // add to existing log (for incremental runs)

* Best practice: close any open log first
capture log close
log using "output/analysis.log", replace text
* ... do-file body ...
log close
```

---

## 10. `forvalues` When `foreach` Is Correct

**Problem:** `forvalues` iterates over integer sequences only. Copilot uses it
for variable name lists, string lists, and non-sequential numeric lists — all
of which silently fail or iterate incorrectly.

```stata
* WRONG — forvalues cannot iterate over variable names or strings
forvalues v = welfare urban education region {   // syntax error
    summarize `v'
}

forvalues year = 2010 2015 2018 2022 {   // syntax error — not sequential integers
    use "data/hh_`year'.dta", clear
}

* RIGHT — foreach for variable lists, string lists, and non-sequential numbers
foreach v of varlist welfare urban education region {
    quietly summarize `v'
    display "`v': mean = " r(mean)
}

foreach year in 2010 2015 2018 2022 {
    use "data/hh_`year'.dta", clear
    * ...
}

* forvalues IS correct for sequential integer loops
forvalues i = 1/100 {
    generate var_`i' = .
}

forvalues year = 2010/2022 {   // 2010, 2011, ..., 2022
    use "data/hh_`year'.dta", clear
}
```

**Quick rule:** if the list is sequential integers with no gaps, use
`forvalues`. Everything else: `foreach`.
