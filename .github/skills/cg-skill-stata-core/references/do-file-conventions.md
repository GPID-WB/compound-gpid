# Do-file Conventions

Standard conventions for Stata do-files in GPID projects. These ensure
consistency, readability, and reproducibility across the team.

---

## 1. Standard Do-file Header

Every production do-file begins with this block. No exceptions.

```stata
/*==================================================
Project:    [Project name]
Do-file:    [filename].do
Date:       YYYY-MM-DD
Author:     [name]
Modified:   YYYY-MM-DD [name] — [brief description of change]

Purpose:    [One paragraph: what this do-file does and why.]
            [Include key methodological choices made here.]

Inputs:     [List all input files with full macro-expanded paths]
            ${gpid_data}/raw/hh_survey_2022.dta
            ${gpid_data}/intermediate/02_cleaned.dta

Outputs:    [List all output files]
            ${gpid_data}/intermediate/03_welfare.dta
            ${gpid_out}/tables/welfare_summary.xlsx

Notes:      [Anything a future reader needs to know]
            PPP conversion uses 2017 ICP round.
            Survey weights: per Eurostat guidelines, not rescaled.
            Random seed: 20240301 (bootstrap CI in section 4 only)
==================================================*/
```

---

## 2. Do-file Setup Block

Immediately after the header, before any data operations:

```stata
* ---- Setup ----------------------------------------------------------
version 17
set more off
set linesize 120
clear all
macro drop _all

* Package environment
repado using "${gpid_root}/code/ado"

* Random seed (include only if this do-file uses random processes)
* set seed 20240301

* Open log
capture log close
log using `"${gpid_root}/output/logs/${dofile_name}.log"', replace text
```

---

## 3. Section Delimiters

Use consistent section markers throughout. Makes do-files navigable and
makes log output readable.

```stata
* ---- 1. Load and validate -------------------------------------------
use `"${gpid_data}/raw/hh_survey_2022.dta"', clear
isid hhid                    // assert unique identifier
describe
codebook welfare urban

* ---- 2. Clean welfare variable --------------------------------------
// welfare is: monthly per-capita consumption, LCU nominal

replace welfare = . if welfare < 0
replace welfare = . if welfare > 99999   // implausible upper bound — document threshold

// welfare is now: monthly per-capita consumption, LCU nominal, cleaned

* ---- 3. PPP conversion ----------------------------------------------
// welfare is: monthly per-capita consumption, LCU nominal, cleaned
merge m:1 country year using `"${gpid_data}/reference/ppp_factors.dta"', ///
    keep(1 3) nogenerate

replace welfare = welfare / ppp_factor_2017
// welfare is now: monthly per-capita consumption, 2017 PPP USD

* ---- 4. Save --------------------------------------------------------
label data "GPID welfare aggregate — `c(current_date)'"
compress
save `"${gpid_data}/intermediate/03_welfare.dta"', replace
```

---

## 4. Do-file Organization — Standard Section Order

1. **Header** (as above)
2. **Setup block** (`version`, `set more off`, `repado`, `set seed`, log open)
3. **Load data** (single `use` command; validate with `isid`, `describe`)
4. **Processing sections** (one logical block per delimiter)
5. **Save output** (`compress` first, then `save`; export tables if needed)
6. **Log close** (`log close`)

Never mix data loading and processing in the same section. Never save
intermediate states mid-section.

---

## 5. Naming Conventions

### Variables

```stata
* lowercase_with_underscores
welfare_pc          // per-capita welfare
survey_year         // survey reference year
is_urban            // binary flag (is_ prefix for dummies)
ln_welfare          // log transformation (ln_ prefix)
welfare_pc_ppp      // with currency/deflation suffix
d_welfare           // first difference (d_ prefix)
```

Never use:
- CamelCase: `WelfarePc` ← wrong
- All caps: `WELFARE_PC` ← wrong (reserved for dataset-level labels)
- Dots: `welfare.pc` ← invalid Stata variable name
- Spaces: not possible in Stata variable names

### Locals

```stata
* Short and descriptive; match the variable they reference when possible
local welfare_var "cons_pc"
local survey_yr   2022
local pov_line    2.15
local n_iters     500
```

### Programs (`.ado` files and `program define`)

```stata
* lowercase with underscores; prefix with project identifier for team programs
program define gpid_fgt        // team prefix + descriptive name
program define gpid_summarize
program define gpid_ppp_convert
```

---

## 6. Master Do-file Structure

The master do-file is the only entry point for running the full analysis.
It must be runnable in one click with no manual intervention.

```stata
/*==================================================
Project:    GPID Poverty Analysis 2022
Do-file:    master.do
Purpose:    Run complete analysis pipeline from raw data to final outputs.
            Typical run time: ~45 minutes.
            
Run with:   do "C:/WBG/gpid-analysis/code/master.do"
==================================================*/

version 17
set more off
set linesize 120
clear all
macro drop _all

* ---- Root paths (globals — only place globals are defined) ----------
global gpid_root "C:/WBG/gpid-analysis"
global gpid_data "${gpid_root}/data"
global gpid_code "${gpid_root}/code"
global gpid_out  "${gpid_root}/output"

* ---- Package environment -------------------------------------------
repado using "${gpid_code}/ado"

* ---- Open master log -----------------------------------------------
capture log close
log using `"${gpid_out}/logs/master_$S_DATE.log"', replace text

* ---- Run pipeline --------------------------------------------------
display "Pipeline start: $S_TIME"

do "${gpid_code}/01_raw_validation.do"
do "${gpid_code}/02_cleaning.do"
do "${gpid_code}/03_welfare_aggregation.do"
do "${gpid_code}/04_ppp_conversion.do"
do "${gpid_code}/05_poverty_estimates.do"
do "${gpid_code}/06_tables_and_figures.do"

display "Pipeline complete: $S_TIME"

* ---- Close master log ----------------------------------------------
log close
```

**Rules for master.do:**
- Contains zero substantive analysis code
- Defines all globals; subordinate do-files define only locals
- Every subordinate do-file is independent: can be rerun standalone without running master first
- Run time is documented in the header
- Output logs use date stamp: `master_$S_DATE.log`

---

## 7. `program define` File Conventions (`.ado` files)

When writing reusable programs for the team:

```stata
*! gpid_fgt.ado
*! Compute FGT poverty index from welfare variable
*! Version 1.0.0  2025-03-01  [name]
*! Version 1.1.0  2025-06-15  [name]  Added strata/cluster SE option

program define gpid_fgt, rclass
    version 17
    
    syntax varname(numeric) [if] [in] [pweight], ///
        PLINe(real)                               ///
        [ Alpha(integer 0)                        ///
          STRata(varname)                         ///
          CLuster(varname) ]
    
    // ... program body ...
    
    return scalar fgt   = `fgt_value'
    return scalar pline = `pline'
    return scalar alpha = `alpha'
    return scalar N     = `n_obs'
end
```

The `*!` version comment is parsed by `which` and `ado describe` — always include it.

---

## 8. Continuation Lines

Long commands use `///` (not `#delimit ;`). Three spaces of indentation per
continuation level.

```stata
* Correct continuation style
regress welfare                    ///
    i.urban                        ///
    i.year                         ///
    c.age##c.age                   ///
    i.education                    ///
    [pw=weight],                   ///
    vce(cluster hhid)

merge m:1 country year             ///
    using `"${gpid_data}/reference/ppp.dta"', ///
    keep(1 3)                      ///
    nogenerate                     ///
    assert(1 3)

* Never use #delimit ; — it complicates copy-paste and breaks lint
```
