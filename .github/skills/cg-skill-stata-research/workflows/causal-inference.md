# Causal Inference Methods

Estimation patterns for causal claims in GPID work. Each method includes
the identifying assumptions, the preferred estimator, diagnostics, and
the most common Copilot mistakes. Always start from the research design
(Phase 0) — the estimator must match the identification strategy.

---

## 1. Difference-in-Differences (DiD)

### When to Use
- Treatment occurs at a known time for a known group
- Untreated group provides a valid counterfactual trend
- Key assumption: parallel trends in the absence of treatment

### Classic 2×2 DiD

```stata
// Create treatment indicators
generate post = (year >= treatment_year)
generate treat_post = treated * post

// DiD with unit and time FE
reghdfe y treat_post, absorb(id year) cluster(id)

// Equivalent explicit interaction form
regress y i.treated##i.post controls, cluster(id)
```

### Staggered Treatment Timing

**Do NOT use classic TWFE with staggered adoption.** TWFE produces biased
estimates with heterogeneous treatment effects and staggered timing
(Goodman-Bacon 2021, Sun & Abraham 2021).

```stata
// ---- Diagnostic: Bacon decomposition --------------------------------
// See which 2x2 comparisons drive the TWFE estimate
bacondecomp y treat_post, ddetail

// ---- Callaway & Sant'Anna (2021) ------------------------------------
// Preferred for staggered DiD with covariates
// gvar = first period of treatment (0 for never-treated)
csdid y x1 x2, ivar(id) time(year) gvar(first_treat) notyet

// Aggregate to event time
csdid_estat event
csdid_plot

// Simple ATT
csdid_estat simple

// Group-specific effects
csdid_estat group

// ---- de Chaisemartin & D'Haultfoeuille (2020) -----------------------
// Alternative robust DiD estimator
did_multiplegt y id year treatment, robust_dynamic ///
    placebo(5) dynamic(5) breps(100) cluster(id)

// ---- Borusyak, Jaravel & Spiess (2024) — Imputation ----------------
did_imputation y id year first_treat, ///
    horizons(0/5) pretrend(5) minn(0)
event_plot, default_look
```

### Pre-Trend Testing

Pre-trends are necessary but not sufficient for parallel trends.

```stata
// Event study specification
reghdfe y ib(-1).event_time##1.treated, ///
    absorb(id year) cluster(id)
coefplot, vertical drop(_cons) ///
    xline(-0.5, lcolor(red)) ///
    yline(0, lcolor(gray)) ///
    title("Event Study — Treatment Effects") ///
    xtitle("Periods Relative to Treatment")
```

---

## 2. Regression Discontinuity (RD)

### When to Use
- Treatment assigned by a threshold rule on a running variable
- Key assumption: no manipulation of the running variable around the cutoff

### Sharp RD

```stata
// rdrobust — preferred implementation
rdrobust y running_var, c(0) kernel(triangular) bwselect(mserd)

// With covariates
rdrobust y running_var, c(0) covs(x1 x2) kernel(triangular)

// Bandwidth selection
rdbwselect y running_var, c(0) all
// Reports: MSE-optimal, CER-optimal, IK

// RD plot — visualization
rdplot y running_var, c(0) nbins(20 20) ///
    title("Regression Discontinuity") ///
    x(Running Variable) y(Outcome)
```

### Fuzzy RD

```stata
// When treatment is not perfectly determined by the threshold
rdrobust y running_var, c(0) fuzzy(treatment) kernel(triangular)
```

### RD Diagnostics

```stata
// McCrary density test (manipulation check)
rddensity running_var, c(0)
// H0: no discontinuity in density at cutoff
// Rejection suggests manipulation

// Covariate balance at cutoff
foreach var of varlist x1 x2 x3 {
    rdrobust `var' running_var, c(0)
}
// Pre-determined covariates should NOT jump at the cutoff

// Sensitivity to bandwidth choice
foreach bw in 0.5 1 1.5 2 2.5 {
    rdrobust y running_var, c(0) h(`bw')
}
```

---

## 3. Matching Methods

### When to Use
- Selection on observables (conditional independence / CIA)
- No valid instrument or discontinuity
- Treatment not randomly assigned but confounders are measured

### Propensity Score Matching (PSM)

```stata
// Step 1: Estimate propensity score
logit treated x1 x2 x3 x4
predict pscore, pr

// Step 2: Check overlap (common support)
twoway (histogram pscore if treated==1, color(blue%30)) ///
       (histogram pscore if treated==0, color(red%30)), ///
    title("Propensity Score Distribution") ///
    legend(order(1 "Treated" 2 "Control"))

// Step 3: Match
psmatch2 treated x1 x2 x3, outcome(y) neighbor(5) caliper(0.05) common

// Step 4: Balance check
pstest x1 x2 x3 x4, both graph

// Step 5: ATT estimate
// psmatch2 reports ATT automatically
// Or use teffects for built-in matching:
teffects psmatch (y) (treated x1 x2 x3, logit), atet nn(5)
```

### Inverse Probability Weighting (IPW)

```stata
teffects ipw (y) (treated x1 x2 x3, logit), atet
// Doubly-robust: AIPW
teffects aipw (y x1 x2 x3) (treated x1 x2 x3, logit), atet
```

### Nearest-Neighbor Matching (Non-Parametric)

```stata
teffects nnmatch (y x1 x2 x3) (treated), atet nn(4) biasadj(x1 x2 x3)
// biasadj corrects for remaining covariate imbalance
```

---

## 4. Instrumental Variables (IV)

### When to Use
- Endogenous regressor (omitted variables, reverse causality, measurement error)
- Instrument satisfies: relevance (correlated with endogenous X), exclusion
  (affects Y only through X), independence (uncorrelated with error)

### 2SLS Estimation

```stata
// Built-in ivregress
ivregress 2sls y controls (endogenous = instrument1 instrument2), ///
    vce(cluster id)

// First-stage diagnostics
estat firststage
// Partial F > 10 (Staiger-Stock rule) or preferably > 23 (Lee et al. 2022)

// Overidentification test (if more instruments than endogenous)
estat overid

// Using ivreg2 (preferred — more diagnostics)
ivreg2 y controls (endogenous = instrument1 instrument2), ///
    first cluster(id)
// Reports: Kleibergen-Paap F, Hansen J, Anderson-Rubin CI
```

### Weak Instrument Robust Inference

```stata
// Anderson-Rubin confidence set (valid regardless of instrument strength)
ivregress 2sls y controls (endogenous = instrument), vce(robust)
weakivtest

// Or with ivreg2
ivreg2 y controls (endogenous = instrument), cluster(id) first
// Check: Kleibergen-Paap F statistic
```

### Common IV Pitfalls in GPID Work

| Pitfall | Problem | Fix |
|---------|---------|-----|
| Rainfall as instrument for everything | Often violates exclusion | Document the exclusion restriction argument carefully |
| Weak first stage (F < 10) | Biased toward OLS, wide CIs | Report Anderson-Rubin CIs; consider LIML |
| Many instruments | Over-fitting first stage | Use fewer, stronger instruments; report Hansen J |
| Geographic instruments with spatial correlation | SEs too small | Cluster at geographic level, use Conley SEs |

---

## 5. Panel Fixed Effects

### Within Estimator

```stata
// Declare panel
xtset id year

// Unit fixed effects (within estimator)
xtreg y x1 x2, fe vce(cluster id)

// Preferred: reghdfe (faster, handles multiple FE sets)
reghdfe y x1 x2, absorb(id year) cluster(id)

// Hausman test: FE vs RE
quietly xtreg y x1 x2, fe
estimates store fe
quietly xtreg y x1 x2, re
estimates store re
hausman fe re
// Reject H0 → use FE
```

### Dynamic Panel (Arellano-Bond)

```stata
// When lagged dependent variable is included
xtabond2 y L.y x1 x2, gmm(L.y, lag(2 5)) iv(x1 x2) ///
    twostep robust small

// Diagnostics
// AR(1) should reject, AR(2) should not reject
// Hansen J should not reject (instrument validity)
```

---

## Method Selection Guide

| Design question | Method | Key assumption | Diagnostic |
|----------------|--------|---------------|------------|
| Treatment at known time + untreated group | DiD | Parallel trends | Event study, Bacon decomp |
| Treatment by threshold rule | RD | No manipulation | McCrary test, covariate balance |
| Treatment not random, confounders measured | Matching/IPW | CIA | Balance tests, overlap |
| Endogenous X + valid instrument | IV/2SLS | Exclusion restriction | First-stage F, Hansen J |
| Panel with time-invariant confounders | FE | Strict exogeneity | Hausman test |
| Staggered treatment timing | Modern DiD | No anticipation | Pre-trends, C&S/BJS |
