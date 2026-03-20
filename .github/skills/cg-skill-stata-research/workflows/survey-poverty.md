# Survey Design & Poverty Measurement

Patterns for working with household survey microdata at GPID. Covers survey
design declaration, weighted estimation, poverty indices, welfare aggregation,
and inequality measures. Every command in this file assumes the data has
survey structure — if it doesn't, you're probably using the wrong dataset.

---

## 1. Survey Design Declaration

### Standard GPID Survey Setup

```stata
// Most GPID household surveys: stratified cluster sample
svyset psu [pw=weight], strata(stratum)

// Two-stage design (e.g., LSMS)
svyset psu [pw=weight], strata(stratum) || ssu

// Verify the design
svyset                       // display current settings
svydescribe                  // detailed design description
svydescribe, single          // check for singleton strata (common problem)
```

### Singleton Strata

Singleton strata (one PSU per stratum) make variance estimation impossible.
GPID convention: use the centered approach.

```stata
// Check for singletons
svydescribe, single

// If singletons exist, set adjustment
svyset psu [pw=weight], strata(stratum) singleunit(centered)
// centered = uses average of other strata variances
// DO NOT use singleunit(certainty) — it drops them from variance estimation
```

### Weight Diagnostics

```stata
// Always run these before any analysis
summarize weight, detail
assert weight > 0 & !missing(weight)   // no zero or missing weights

// Distribution check — extreme weights inflate variance
centile weight, centile(1 5 95 99)
// If max/min ratio > 50, consider trimming (document threshold)

// Verify weights sum to population (if calibrated)
quietly count
display "Sample N: " r(N)
summarize weight, meanonly
display "Weighted N: " r(sum)
```

---

## 2. Survey-Weighted Estimation

### The Iron Rule

**Every statistical command on survey data must use `svy:` prefix or explicit
weight syntax.** There are no exceptions in GPID work. An unweighted mean on
survey data is wrong.

```stata
// WRONG — unweighted
summarize welfare
tabulate urban

// RIGHT — survey-weighted
svy: mean welfare
svy: proportion is_urban

// Subpopulation analysis — MUST use subpop(), not if
// WRONG — restricts sample, corrupts variance estimation
svy: mean welfare if is_urban == 1

// RIGHT — subpopulation analysis
svy, subpop(is_urban): mean welfare
```

### Why `subpop()` and not `if`

The `if` qualifier restricts the sample *before* variance estimation, which
changes the effective design. `subpop()` keeps the full design but estimates
only for the subgroup. Using `if` typically understates standard errors because
it discards PSUs and strata with no observations in the subgroup, reducing
apparent design variance. The bias is design-dependent; differences of 20–30%
or more are plausible in clustered samples with small subgroups.

### Common Survey Commands

```stata
// Means
svy: mean welfare income education

// Proportions
svy: proportion is_urban is_female

// Totals (population aggregates)
svy: total income

// Ratios
svy: ratio welfare income

// Tabulations with design-based tests
svy: tabulate urban region, pearson

// Regression with survey weights
svy: regress ln_welfare education age i.urban

// Quantiles (requires epctile or specialized commands)
// Note: svy: does NOT support summarize detail — no percentiles
epctile welfare [pw=weight], percentiles(10 25 50 75 90)
```

---

## 3. Welfare Aggregation

### Standard GPID Welfare Construction

Welfare = per-capita consumption or income, expressed in comparable units.
The construction sequence matters — each step must be documented with
before/after unit comments (see `cg-skill-stata-core` Anti-Pattern #3).

```stata
// ---- Step 1: Start with household total consumption (LCU, nominal)
// welfare_hh is: total household consumption, LCU nominal, [survey period]

// ---- Step 2: Per-capita (or adult-equivalent)
generate welfare_pc = welfare_hh / hh_size
// welfare_pc is: per-capita consumption, LCU nominal, [survey period]

// ---- Step 3: Temporal deflation (if multi-period)
// Deflate to reference year using CPI
replace welfare_pc = welfare_pc * (cpi_ref / cpi_survey)
// welfare_pc is: per-capita consumption, LCU real [ref year]

// ---- Step 4: Spatial deflation (if subnational price differences)
replace welfare_pc = welfare_pc / spatial_price_index
// welfare_pc is: per-capita consumption, LCU real [ref year], spatially adjusted

// ---- Step 5: PPP conversion
replace welfare_pc = welfare_pc / ppp_factor
// welfare_pc is: per-capita consumption, PPP USD [ICP round year]

// ---- Step 6: Time period conversion
// GPID convention: daily per-capita
replace welfare_pc = welfare_pc / 365.25
// welfare_pc is: daily per-capita consumption, PPP USD [ICP round year]

// ---- Step 7: Label
label variable welfare_pc "Daily per-capita consumption (2017 PPP USD)"
```

### PPP Conversion Notes

- GPID uses 2017 ICP round PPP factors (as of 2024-2025)
- PPP factors convert local currency to international dollars
- The PPP factor is applied AFTER temporal and spatial deflation
- Country-year-specific PPP factors are in the GPID reference tables
- Do NOT use market exchange rates — they do not reflect purchasing power

---

## 4. Poverty Measurement

### FGT Class of Poverty Indices

The Foster-Greer-Thorbecke (FGT) index with parameter α:

- **FGT(0)** = Headcount ratio (proportion poor) — incidence
- **FGT(1)** = Poverty gap (average shortfall as share of line) — depth
- **FGT(2)** = Squared poverty gap (penalizes deeper poverty) — severity

```stata
// ---- Poverty headcount (FGT 0) ------------------------------------
local pov_line = 2.15   // $2.15/day, 2017 PPP

// Generate poverty indicator
generate poor = (welfare_pc < `pov_line') if !missing(welfare_pc)
label variable poor "Poor ($2.15/day, 2017 PPP)"
label define poor_lbl 0 "Non-poor" 1 "Poor"
label values poor poor_lbl

// Survey-weighted headcount
svyset psu [pw=weight], strata(stratum)
svy: proportion poor
// Store the result — use named coefficient for clarity and robustness
local headcount = _b[1.poor]         // 1.poor = proportion in "Poor" category
local hc_se    = _se[1.poor]         // standard error

// ---- Poverty gap (FGT 1) ------------------------------------------
generate gap = max(0, (`pov_line' - welfare_pc) / `pov_line') ///
    if !missing(welfare_pc)
svy: mean gap
local pov_gap = e(b)[1,1]

// ---- Squared poverty gap (FGT 2) ----------------------------------
generate sq_gap = gap^2 if !missing(welfare_pc)
svy: mean sq_gap
local sq_pov_gap = e(b)[1,1]
```

### Multiple Poverty Lines

GPID reports at three international lines:

```stata
local lines "2.15 3.65 6.85"
foreach z of local lines {
    local z_label = subinstr("`z'", ".", "", .)
    generate poor_`z_label' = (welfare_pc < `z') if !missing(welfare_pc)
    label variable poor_`z_label' "Poor ($`z'/day, 2017 PPP)"    // include PPP year
}

// Headcounts at all three lines
svy: proportion poor_215 poor_365 poor_685
```

### Shared Prosperity (Bottom 40% Mean)

The shared prosperity indicator tracks income/consumption growth of the bottom
40% relative to the overall population over time. This section computes the
necessary single-period mean; combine two periods to produce a growth rate.

```stata
// Bottom 40% mean — single cross-section
// Combine two survey years to compute annualised growth for the indicator
_pctile welfare_pc [pw=weight], percentiles(40)
local p40 = r(r1)
svy, subpop(if welfare_pc <= `p40'): mean welfare_pc
local b40_mean = e(b)[1,1]

// Overall mean
svy: mean welfare_pc
local overall_mean = e(b)[1,1]

// Growth rate (requires two periods: compute b40_mean and overall_mean for each)
// local sp_premium = (`b40_mean_t1' / `b40_mean_t0')^(1/`n_years') - 1
```

---

## 5. Inequality Measures

### Gini Coefficient

```stata
// Using ineqdeco (preferred — handles survey weights)
ineqdeco welfare_pc [pw=weight]
local gini = r(gini)

// By subgroup
ineqdeco welfare_pc [pw=weight], by(region)
// Returns: r(gini), r(between_ge0), r(within_ge0), etc.

// Alternative: fastgini (faster on large datasets)
fastgini welfare_pc [pw=weight]
```

### Theil Index and GE Family

```stata
ineqdeco welfare_pc [pw=weight]
local ge0    = r(ge0)      // Mean log deviation (GE(0))
local ge1    = r(ge1)      // Theil index (GE(1))
local ge2    = r(ge2)      // Half coeff of variation squared (GE(2))
local atkin1 = r(a1)       // Atkinson (epsilon=1)
```

### Percentile Ratios

```stata
_pctile welfare_pc [pw=weight], percentiles(10 50 90)
local p10 = r(r1)
local p50 = r(r2)
local p90 = r(r3)

display "P90/P10 ratio: " `p90' / `p10'
display "P90/P50 ratio: " `p90' / `p50'
display "P50/P10 ratio: " `p50' / `p10'
```

---

## 6. Replicate Weights

Some surveys (e.g., LSMS, DHS) provide replicate weights for variance
estimation instead of PSU/stratum information.

```stata
// Balanced repeated replication (BRR)
svyset [pw=weight], brrweight(brrwt_1-brrwt_80) vce(brr)

// Jackknife
svyset [pw=weight], jkrweight(jkwt_1-jkwt_100) vce(jackknife)

// Bootstrap replicate weights
svyset [pw=weight], bsrweight(bswt_1-bswt_200) vce(bootstrap)

// Fay's adjustment for BRR (reduces variance of variance estimate)
svyset [pw=weight], brrweight(brrwt_1-brrwt_80) vce(brr) fay(0.5)
```

---

## 7. Common Pitfalls in GPID Survey Work

| Pitfall | Consequence | Prevention |
|---------|------------|------------|
| Using `if` instead of `subpop()` | Wrong standard errors | Always use `svy, subpop():` for subgroups |
| Unweighted statistics on survey data | Biased estimates | Every command uses `svy:` or `[pw=weight]` |
| PPP before spatial deflation | Wrong comparability | Follow the construction sequence strictly |
| Poverty line in wrong units | Wrong headcount | Verify welfare and line are in same units |
| Missing `svyset` before `svy:` commands | Error or wrong design | Set design once at top of do-file |
| Ignoring singleton strata | Variance estimation fails | Use `singleunit(centered)` |
| `summarize, detail` with `svy:` | Not supported | Use `epctile` or `_pctile` for quantiles |
