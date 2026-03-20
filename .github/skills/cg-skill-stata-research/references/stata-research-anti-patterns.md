# Stata Research Anti-Patterns

Methodological errors Copilot generates in analytical code. These are not
syntax errors — the code runs without warnings but produces wrong conclusions.
Consult this file when reviewing any analytical Stata output.

**Start here:** Anti-patterns #1, #2, #3, and #4 below are so critical they
are also highlighted in the main [SKILL.md](../SKILL.md). Review those first.

---

## 1. Unweighted Statistics on Survey Data

**Problem:** Copilot uses `summarize`, `tabulate`, `regress` without survey
weights or `svy:` prefix. On complex survey data, unweighted estimates are
biased for population parameters.

```stata
// WRONG — unweighted
summarize welfare
regress ln_welfare education age

// RIGHT — survey-weighted
svyset psu [pw=weight], strata(stratum)
svy: mean welfare
svy: regress ln_welfare education age
```

**Rule:** If the dataset has survey weights, every statistical command uses
`svy:` or explicit `[pw=weight]` syntax. No exceptions.

---

## 2. `if` Instead of `subpop()` for Subgroup Analysis

**Problem:** Copilot uses `if` conditions with `svy:` commands to restrict
to subgroups. This corrupts the variance estimation because `if` changes the
effective survey design.

```stata
// WRONG — svy with if
svy: mean welfare if is_urban == 1

// RIGHT — subpop preserves full design
svy, subpop(is_urban): mean welfare
```

**Why it matters:** Standard errors can differ by 20-30%. Published poverty
rates with wrong SEs cannot be defended in peer review.

---

## 3. PPP Conversion in Wrong Order

**Problem:** Copilot applies PPP conversion before temporal or spatial
deflation, or confuses PPP factors with exchange rates.

```stata
// WRONG — PPP before deflation
replace welfare = welfare / ppp_factor
replace welfare = welfare / cpi_index

// RIGHT — deflate first, then convert
replace welfare = welfare / cpi_index      // temporal deflation
replace welfare = welfare / spatial_index   // spatial deflation (if applicable)
replace welfare = welfare / ppp_factor     // PPP conversion last
```

**Rule:** PPP conversion is always the last step in welfare construction.
Document units before and after every transformation (Anti-Pattern #3 in
`cg-skill-stata-core`).

---

## 4. TWFE with Staggered Treatment Timing

**Problem:** Copilot generates classic two-way fixed effects (TWFE) DiD for
staggered treatment. With heterogeneous treatment effects and staggered
timing, TWFE produces negative weights and biased estimates.

```stata
// WRONG — classic TWFE with staggered timing
reghdfe y treat_post, absorb(id year) cluster(id)

// RIGHT — use a robust modern estimator
csdid y, ivar(id) time(year) gvar(first_treat) notyet
```

**Prevention:** Ask "Is treatment timing the same for all treated units?"
If not, use Callaway-Sant'Anna, de Chaisemartin-D'Haultfoeuille, or
Borusyak-Jaravel-Spiess. See [Causal Inference](../workflows/causal-inference.md).

---

## 5. Missing Overlap Check Before Matching

**Problem:** Copilot runs propensity score matching without checking common
support. Without overlap, matched pairs are extrapolating.

```stata
// WRONG — match without checking overlap
psmatch2 treated x1 x2 x3, outcome(y)

// RIGHT — check overlap first
logit treated x1 x2 x3
predict pscore, pr

// Visual overlap check
twoway (histogram pscore if treated==1, color(blue%30)) ///
       (histogram pscore if treated==0, color(red%30))

// Impose common support
psmatch2 treated x1 x2 x3, outcome(y) common caliper(0.05)

// Balance check — always
pstest x1 x2 x3, both
```

---

## 6. Clustering at the Wrong Level

**Problem:** Copilot clusters standard errors at the individual level or at
a level that doesn't match the treatment assignment or error correlation
structure.

```stata
// WRONG — treatment assigned at village level, clustered at individual
reghdfe y treatment, absorb(id year) vce(robust)

// RIGHT — cluster at the level of treatment assignment
reghdfe y treatment, absorb(id year) cluster(village_id)

// RIGHT — or at a higher level if errors correlate there
reghdfe y treatment, absorb(id year) cluster(district_id)
```

**Rule of thumb:** Cluster at the level of treatment assignment or higher.
With few clusters (< 40), consider wild cluster bootstrap.

---

## 7. P-Hacking via Specification Search

**Problem:** Copilot runs many specifications and highlights the one that
gives a significant result. The phased workflow (Phase 2 → Phase 3) exists
to prevent this.

```stata
// WRONG — trying specifications until p < 0.05
reghdfe y treat x1 x2, absorb(id year) cluster(id)      // p = 0.12
reghdfe y treat x1 x3, absorb(id year) cluster(id)      // p = 0.08
reghdfe y treat x1 x2 x3, absorb(id year) cluster(id)   // p = 0.04 ← "let's use this one"

// RIGHT — commit to specifications in Phase 2, run in Phase 3
// All specifications are reported, regardless of significance
```

**Prevention:** The specification memo (Phase 2) is written and approved
before any estimation. All committed specifications are reported in the
results.

---

## 8. Poverty Line / Welfare Unit Mismatch

**Problem:** Copilot applies a daily poverty line to monthly welfare, or uses
the wrong PPP year, producing meaningless headcount rates.

```stata
// WRONG — welfare is monthly, poverty line is daily
local pov_line = 2.15
generate poor = (welfare_monthly < `pov_line')
// This overstates poverty catastrophically

// RIGHT — match units explicitly
// welfare is: daily per-capita consumption, 2017 PPP USD
local pov_line = 2.15   // $2.15/day, 2017 PPP
generate poor = (welfare_daily < `pov_line') if !missing(welfare_daily)
```

**Rule:** Document welfare units in every do-file header and verify the
poverty line matches those units before computing any poverty rate.

---

## 9. Missing Values in Inequality Measures

**Problem:** Copilot passes variables with missing values to inequality
commands. Some commands silently drop missings; others include them as zeros,
producing wildly wrong Gini coefficients.

```stata
// WRONG — may include or silently drop missings
ineqdeco welfare

// RIGHT — restrict to non-missing observations explicitly
ineqdeco welfare if !missing(welfare) [pw=weight]

// BETTER — assert no missings in the analysis sample
assert !missing(welfare) if in_sample == 1
ineqdeco welfare if in_sample == 1 [pw=weight]
```

---

## 10. Ignoring Weak Instruments

**Problem:** Copilot runs IV/2SLS without checking first-stage strength.
Weak instruments produce estimates more biased than OLS.

```stata
// WRONG — IV without diagnostics
ivregress 2sls y (endogenous = instrument), cluster(id)

// RIGHT — always check first stage
ivreg2 y (endogenous = instrument), cluster(id) first
// Check: Kleibergen-Paap F > 23 (Lee et al. 2022)
// If F < 10: instruments are weak, consider LIML or reduced form
// If F 10-23: report Anderson-Rubin confidence intervals
```

---

## 11. Cross-Country Analysis Without PPP

**Problem:** Copilot compares welfare or income across countries in local
currency units, which is meaningless without PPP conversion.

```stata
// WRONG — comparing LCU across countries
bysort country: summarize welfare

// RIGHT — all cross-country comparisons in PPP terms
// Ensure welfare is in 2017 PPP USD before any cross-country operation
// Check the variable label contains "PPP" as a convention guard
local welfare_lbl : variable label welfare_ppp
assert regexm("`welfare_lbl'", "PPP"), message("welfare_ppp label must contain 'PPP' — check unit labelling")
bysort country: summarize welfare_ppp
```

---

## Quick Diagnostic Checklist

Before accepting any analytical result, verify:

| Check | Command | Expected |
|-------|---------|----------|
| Survey design declared | `svyset` | Shows PSU, strata, weight |
| Weights used in estimation | `svy:` prefix or `[pw=]` | Present on every statistical command |
| Welfare units documented | Check do-file comments | Units stated before/after every transformation |
| Poverty line matches welfare units | Visual inspection | Same periodicity, same PPP year |
| Cluster level matches design | `vce(cluster ...)` | At or above treatment assignment level |
| First stage checked (IV) | `estat firststage` | F > 23 |
| Overlap checked (matching) | Histogram of propensity scores | Support in both groups |
| Subpop used for subgroup analysis | `svy, subpop():` not `svy: ... if` | No `if` qualifier on any `svy:` command |
| Inequality measures exclude missing | `ineqdeco var if !missing(var)` | Explicit `if !missing()` restriction |
| Pre-trends tested (DiD) | Event study plot | No significant pre-treatment effects |
| Modern DiD used (staggered) | `csdid` or equivalent | Not plain TWFE |
| Specifications committed before estimation | Phase 2 memo | Written and approved |
