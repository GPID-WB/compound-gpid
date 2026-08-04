# Workflow Examples: End-to-End Testing

Each example follows the same four-phase structure:
1. **Setup** — load data, validate inputs
2. **Execute** — run the analysis
3. **Verify** — assertions on results
4. **Reproduce** — reprun / reproducibility check

Examples focus on **testing the analysis**, not on performing it. Adapt the placeholders (file paths, variable names, thresholds) to your project.

---

## Example 1: Testing FGT Poverty Indices

**Domain**: Poverty measurement  
**Test goal**: Verify FGT0/FGT1/FGT2 satisfy mathematical properties and are reproducible.

```stata
/* ============================================================
   TEST: FGT Poverty Indices
   File: tests/test_poverty_indices.do
   Expected: "Tests passed: 6  Failed: 0"
   ============================================================ */

local tests_passed = 0
local tests_failed = 0

// ---- 1. SETUP ----
use "${root_data}/processed/survey_clean.dta", clear

* Validate inputs before any estimation
isid welfare_id
assert !missing(welfare)
assert !missing(weight)
assert weight > 0
assert welfare >= 0

// ---- 2. EXECUTE ----
preserve

local poverty_line = 2.15    // 2017 USD/day

quietly poverty welfare [aw=weight], line(`poverty_line')
local fgt0 = r(head_count)
local fgt1 = r(poverty_gap)
local fgt2 = r(poverty_severity)

// ---- 3. VERIFY ----

* FGT0: headcount rate is a proportion
capture assert inrange(`fgt0', 0, 1)
if _rc { local ++tests_failed ; display as error "FAIL: FGT0 = `fgt0' not in [0,1]" }
else   { local ++tests_passed ; display as text  "PASS: FGT0 in [0,1]" }

* FGT1 ≤ FGT0 (poverty gap ≤ headcount — mathematical property)
capture assert `fgt1' <= `fgt0'
if _rc { local ++tests_failed ; display as error "FAIL: FGT1 (`fgt1') > FGT0 (`fgt0')" }
else   { local ++tests_passed ; display as text  "PASS: FGT1 ≤ FGT0" }

* FGT2 ≤ FGT1 (severity ≤ gap — mathematical property)
capture assert `fgt2' <= `fgt1'
if _rc { local ++tests_failed ; display as error "FAIL: FGT2 (`fgt2') > FGT1 (`fgt1')" }
else   { local ++tests_passed ; display as text  "PASS: FGT2 ≤ FGT1" }

* Monotonicity: higher line → weakly higher headcount
quietly poverty welfare [aw=weight], line(3.65)
local fgt0_365 = r(head_count)

capture assert `fgt0_365' >= `fgt0'
if _rc { local ++tests_failed ; display as error "FAIL: headcount(3.65) < headcount(2.15)" }
else   { local ++tests_passed ; display as text  "PASS: monotonicity holds" }

* Headcount is plausible for this context (not 0% or 100%)
capture assert `fgt0' > 0.01
if _rc { local ++tests_failed ; display as error "FAIL: FGT0 suspiciously low (`fgt0')" }
else   { local ++tests_passed }

capture assert `fgt0' < 0.99
if _rc { local ++tests_failed ; display as error "FAIL: FGT0 suspiciously high (`fgt0')" }
else   { local ++tests_passed }

restore

display as result _n "Tests passed: `tests_passed'  Failed: `tests_failed'"
assert `tests_failed' == 0

// ---- 4. REPRODUCE ----
// Run from project root: reprun "analysis/02_poverty.do"
// Expected: all three reprun columns = 0
```

---

## Example 2: Testing PPP Conversion

**Domain**: Data harmonization  
**Test goal**: Verify PPP conversion factors are aligned to correct vintage and conversion produces valid welfare values.

```stata
/* ============================================================
   TEST: PPP Conversion
   File: tests/test_ppp_conversion.do
   ============================================================ */

local tests_passed = 0
local tests_failed = 0

// ---- 1. SETUP ----
use "${root_data}/raw/survey_lcu.dta", clear

* Input validation
isid welfare_id
confirm numeric variable welfare_lcu weight ppp_2017
assert !missing(welfare_lcu) if !missing(weight)
assert !missing(ppp_2017)

// ---- 2. EXECUTE ----
preserve

* Apply PPP conversion
* welfare_lcu must be ANNUAL (LCU per year); / ppp_2017 converts to 2017 USD; / 365 gives daily
gen welfare_ppp = welfare_lcu / ppp_2017 / 365
assert welfare_ppp < 500 if !missing(welfare_ppp)    // plausibility: < $500/day

// ---- 3. VERIFY ----

* PPP factors are positive and in plausible range
count if ppp_2017 <= 0
capture assert r(N) == 0
if _rc { local ++tests_failed ; display as error "FAIL: non-positive PPP factors found" }
else   { local ++tests_passed ; display as text  "PASS: all PPP factors positive" }

capture assert inrange(ppp_2017, 0.01, 10000)
if _rc { local ++tests_failed ; display as error "FAIL: PPP outside [0.01, 10000]" }
else   { local ++tests_passed ; display as text  "PASS: PPP in plausible range" }

* Converted welfare is non-negative
count if welfare_ppp < 0
capture assert r(N) == 0
if _rc { local ++tests_failed ; display as error "FAIL: `r(N)' negative welfare_ppp values" }
else   { local ++tests_passed ; display as text  "PASS: no negative welfare_ppp" }

* No missing welfare_ppp where welfare_lcu is present
count if missing(welfare_ppp) & !missing(welfare_lcu)
capture assert r(N) == 0
if _rc { local ++tests_failed ; display as error "FAIL: missing welfare_ppp where lcu present" }
else   { local ++tests_passed ; display as text  "PASS: no unexpected missing in welfare_ppp" }

* Row count unchanged (conversion must not drop rows)
local n_before = _N
// (welfare_ppp already generated above)
assert _N == `n_before'
local ++tests_passed

restore

display as result _n "Tests passed: `tests_passed'  Failed: `tests_failed'"
assert `tests_failed' == 0

// ---- 4. REPRODUCE ----
// Verify the PPP conversion is deterministic:
// reprun "analysis/01_clean.do"    // should show Data Checksum = 0 for the gen line
```

---

## Example 3: Testing Survey-Weighted Estimates

**Domain**: Survey analysis  
**Test goal**: Verify survey design is correctly specified and weighted estimates are plausible.

```stata
/* ============================================================
   TEST: Survey-Weighted Mean Income
   File: tests/test_survey_estimates.do
   ============================================================ */

local tests_passed = 0
local tests_failed = 0

// ---- 1. SETUP ----
use "${root_data}/processed/survey_clean.dta", clear

* Validate survey design variables
confirm numeric variable psu strata weight
assert !missing(psu)
assert !missing(strata)
assert weight > 0

// ---- 2. EXECUTE ----
preserve

svyset psu [pw=weight], strata(strata) singleunit(centered)
svy: mean welfare

local mean_est  = e(b)[1,1]
local mean_se   = sqrt(e(V)[1,1])
local deff      = e(deff)[1,1]    // [1,1] = first variable; e(deff) is a matrix for multi-variable svy: mean

// ---- 3. VERIFY ----

* Mean is positive
capture assert `mean_est' > 0
if _rc { local ++tests_failed ; display as error "FAIL: non-positive mean welfare" }
else   { local ++tests_passed ; display as text  "PASS: mean welfare positive" }

* Standard error is smaller than mean (CV < 100%)
capture assert `mean_se' < `mean_est'
if _rc { local ++tests_failed ; display as error "FAIL: SE >= mean (CV ≥ 100%)" }
else   { local ++tests_passed ; display as text  "PASS: SE < mean" }

* Design effect is plausible (between 1 and 20)
capture assert inrange(`deff', 0.5, 30)    // DEFF < 1 is valid for calibrated/post-stratified weights
if _rc { local ++tests_failed ; display as error "FAIL: DEFF = `deff' outside [0.5,30]" }
else   { local ++tests_passed ; display as text  "PASS: DEFF in plausible range" }

* Sample size is adequate
capture assert e(N) >= 100
if _rc { local ++tests_failed ; display as error "FAIL: sample too small (N = `e(N)')" }
else   { local ++tests_passed ; display as text  "PASS: N = `e(N)'" }

restore

display as result _n "Tests passed: `tests_passed'  Failed: `tests_failed'"
assert `tests_failed' == 0

// ---- 4. REPRODUCE ----
// Survey estimates depend on sort order — ensure stable sort before svy:
// bysort psu strata (welfare_id): gen obs_order = _n
// sort psu strata obs_order
// reprun "analysis/03_survey_means.do"
```

---

## Example 4: Testing a Difference-in-Differences Specification

**Domain**: Causal inference  
**Test goal**: Verify pre-treatment parallel trends and bound treatment effect magnitude.

```stata
/* ============================================================
   TEST: DiD Specification
   File: tests/test_did.do
   ============================================================ */

local tests_passed = 0
local tests_failed = 0

// ---- 1. SETUP ----
use "${root_data}/processed/panel_clean.dta", clear

* Validate panel structure
isid district_id year
xtset district_id year

* Validate treatment assignment
assert inlist(treated, 0, 1)
assert !missing(treated)
assert !missing(outcome)
local treatment_year = 2018    // adjust to actual treatment year

// ---- 2. EXECUTE ----
preserve

* Pre-treatment: test parallel trends
* Keep only pre-treatment periods and test year x treated interactions.
* Do NOT include i.pre_period alongside i.year — they are collinear and get dropped.
keep if year < `treatment_year'

regress outcome i.treated##i.year controls, ///
    vce(cluster district_id)

// ---- 3. VERIFY: Pre-trends ----

* Joint test: all treated x year interactions are zero (parallel trends)
testparm i.treated#i.year
local p_pretrend = r(p)

capture assert `p_pretrend' > 0.05
if _rc { local ++tests_failed ; display as error "FAIL: pre-trends p = `p_pretrend' (parallel trends violated)" }
else   { local ++tests_passed ; display as text  "PASS: pre-trends p = `p_pretrend'" }

restore

* Post-treatment: estimate main DiD effect
preserve

regress outcome i.treated##i.post_period controls i.year, ///
    vce(cluster district_id)

local b_did  = _b[1.treated#1.post_period]
local se_did = _se[1.treated#1.post_period]

* Treatment effect sign is positive (program expected to increase outcome)
capture assert `b_did' > 0
if _rc { local ++tests_failed ; display as error "FAIL: treatment effect negative (`b_did')" }
else   { local ++tests_passed ; display as text  "PASS: treatment effect positive" }

* Treatment effect is statistically significant at 10%
test 1.treated#1.post_period = 0
capture assert r(p) < 0.10
if _rc { local ++tests_failed ; display as error "FAIL: treatment effect not significant (p = `r(p)')" }
else   { local ++tests_passed ; display as text  "PASS: treatment significant at 10%" }

* Magnitude is plausible (< 50 pp for a binary outcome)
capture assert abs(`b_did') < 0.50
if _rc { local ++tests_failed ; display as error "FAIL: implausibly large effect (`b_did')" }
else   { local ++tests_passed ; display as text  "PASS: effect magnitude plausible" }

* Sufficient observations
capture assert e(N) >= 200
if _rc { local ++tests_failed ; display as error "FAIL: N too small (N = `e(N)')" }
else   { local ++tests_passed ; display as text  "PASS: N = `e(N)'" }

restore

display as result _n "Tests passed: `tests_passed'  Failed: `tests_failed'"
assert `tests_failed' == 0

// ---- 4. REPRODUCE ----
// Panel regressions with cluster SE are sensitive to sort order.
// Sort by cluster before running:
// sort district_id year
// reprun "analysis/05_did.do"
```
