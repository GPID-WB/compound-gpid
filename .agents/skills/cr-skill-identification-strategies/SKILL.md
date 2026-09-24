---
name: cr-skill-identification-strategies
module: research
description: "Identification strategies for causal inference in economics research.
  Covers IV/2SLS, RDD, DiD, event studies, synthetic control, matching/IPW,
  and strategy selection guidance. Each strategy includes when it is applicable,
  required diagnostics (P0 if missing), code patterns, and anti-patterns. Loaded
  by @cr-identification-audit for Identification/Estimation tasks."
---

# Identification Strategies

Reference skill for causal identification in economics research. Used alongside
`cr-skill-research-integrity` (Error Class 3 = P0 detection triggers) — that
skill flags when required diagnostics are absent; this skill provides the full
diagnostic protocols.

Cross-reference: `@cr-identification-audit` dispatches this skill and runs
targeted audits of the identification strategy claimed in the plan/derivation.

---

## 1. Instrumental Variables (IV / 2SLS)

**When applicable**: Endogenous regressor $X$ (Cov(X, ε) ≠ 0); one or more
instruments $Z$ that are relevant and exogenous.

**Required diagnostics (P0 if missing)**:

| Diagnostic | Test | P0 Threshold |
|-----------|------|-------------|
| First-stage relevance | F-statistic on excluded instruments | F < 10 → weak instrument flag |
| Weak instrument test | Stock-Yogo critical values | Report at 10% maximal IV size |
| Overidentification (if overid) | Hansen J-test | Report J-stat and p-value |
| Endogeneity test | Durbin-Wu-Hausman | Report if X suspected endogenous |

```r
# R — IV estimation via ivreg (AER) or feols (fixest)
library(AER)
iv_fit <- ivreg(y ~ x + controls | z1 + z2 + controls, data = df)
summary(iv_fit, diagnostics = TRUE)  # includes Weak Instruments, Wu-Hausman, Sargan

# fixest (preferred for FE)
library(fixest)
iv_feols <- feols(y ~ controls | fe1 | x ~ z1 + z2, data = df, cluster = ~cluster_var)
fitstat(iv_feols, ~ivf)  # first-stage F

# Stata
ivregress 2sls y (x = z1 z2) controls, cluster(cluster_var)
estat firststage                  // first-stage F
estat overid                      // Sargan J-test (if overidentified)
estat endogenous                  // Durbin-Wu-Hausman
```

**LATE vs. ATE**: IV identifies LATE (Local Average Treatment Effect) for
compliers only. Document the complier sub-population and discuss external
validity.

> **PPP vintage consistency**: When instruments or controls include income or
> welfare aggregates, ensure all series use the same PPP vintage (2011 or 2017).
> Mixing vintages invalidates cross-country or cross-period comparisons.
> Document the vintage in the data section of the plan.

**Anti-patterns**:
- Using F-statistic on all first-stage regressors (should be F on excluded instruments only)
- Reporting IV without first-stage results
- Claiming exogeneity of instrument without economic argument
- Ignoring heterogeneous treatment effects (LATE ≠ ATE without homogeneity assumption)

**References**: Stock & Watson (2020); Andrews, Stock & Sun (2019) AER:I;
Imbens & Angrist (1994) Econometrica

---

## 2. Regression Discontinuity Design (RDD)

**When applicable**: Treatment assignment determined by whether a continuous
running variable $R$ crosses a known threshold $c$. Units cannot precisely
manipulate $R$.

**Required diagnostics (P0 if missing)**:

| Diagnostic | Test | P0 Threshold |
|-----------|------|-------------|
| Manipulation test | McCrary (2008) density test | Report statistic and p-value; p < 0.05 is a problem |
| Covariate balance at cutoff | Local linear regression of covariates on $R$ near $c$ | Report table of balance tests |
| Placebo cutoffs | Estimate RDD at non-cutoff values | Should find no effect |
| Bandwidth selection | Optimal bandwidth (Imbens-Kalyanaraman) | Report IK bandwidth; try half and double |
| Polynomial order | Sensitivity to p=1 vs p=2 | Report results for both |

```r
# R — rdrobust
library(rdrobust)
rdd_fit <- rdrobust(y, r, c = cutoff)
summary(rdd_fit)             # estimates, bandwidth, SE

# Manipulation test (McCrary)
library(rddensity)
rdd_density <- rddensity(r, c = cutoff)
summary(rdd_density)

# Covariate balance
rdplot(x1, r, c = cutoff, title = "Covariate Balance: X1")

# Stata
rdrobust y r, c(cutoff) all    // all bandwidth selectors
rddensity r, c(cutoff)         // manipulation test
```

**Fuzzy RDD**: When treatment probability (not treatment status) jumps at
cutoff — use IV where instrument is I(R > c). First-stage F-test required.

**Anti-patterns**:
- Omitting McCrary test (P0)
- Using global polynomial instead of local linear/polynomial (over-fitting bias)
- No bandwidth sensitivity analysis
- Interpreting fuzzy RDD as sharp (understates standard errors)
- Not checking for bunching/heaping in running variable

**References**: Lee & Lemieux (2010) JEL; Calonico, Cattaneo & Titiunik (2014) Econometrica

---

## 3. Difference-in-Differences (DiD)

**When applicable**: Panel data; treatment assigned to some units in some
periods; untreated units are valid counterfactuals (parallel trends assumption).

**Required diagnostics (P0 if missing)**:

| Diagnostic | Test | P0 Threshold |
|-----------|------|-------------|
| Pre-trends | Event study coefficients pre-treatment | No significant pre-trends; report all pre-period estimates |
| Parallel trends (formal) | Callaway-Sant'Anna or Rambachan-Roth | Report sensitivity to violations |
| Spillovers/SUTVA | Design discussion | Documented |
| Staggered adoption check | If staggered, use Callaway-Sant'Anna or Sun-Abraham | Never use TWFE alone for staggered DiD |

```r
# R — staggered DiD with Callaway-Sant'Anna (did package)
library(did)
cs_fit <- att_gt(yname = "y", tname = "period", idname = "id",
                  gname = "first_treated", data = df,
                  control_group = "notyettreated",
                  est_method = "reg")
aggte(cs_fit, type = "dynamic")   # event-study aggregation

# Sun-Abraham via sunab() in fixest
feols(y ~ sunab(first_treated, period) + controls | id + period,
      data = df, cluster = ~id)

# Rambachan-Roth sensitivity (HonestDiD package)
library(HonestDiD)
# ... see package documentation

# Stata
csdid y, ivar(id) tvar(period) gvar(first_treated) notyet
csdid_plot                         // event study
```

**Anti-patterns**:
- Using TWFE (two-way FE) for staggered DiD without Callaway-Sant'Anna or
  Sun-Abraham (P0 — "contaminated" estimates from negative weighting)
- Reporting only the post-treatment average effect without event study
- Pre-trends test that only checks "significance" of individual pre-period
  coefficients (should also test joint significance)
- Ignoring anticipation effects in DiD

**References**: Callaway & Sant'Anna (2021) JoE; Sun & Abraham (2021) JoE;
Rambachan & Roth (2023) ReStud; Baker et al. (2022) AER

---

## 4. Event Studies

**When applicable**: Sharp change in policy or environment at a known date;
estimate dynamic treatment effects over time relative to event.

**Required diagnostics (P0 if missing)**:

| Diagnostic | Code Pattern |
|-----------|-------------|
| Normalize period t=-1 (omit base period) | `reltime = period - event_time; omit -1` |
| Report all pre-event estimates | Full event-study plot with CIs |
| Test joint pre-significance | `joint_pretest()` or `linearHypothesis()` |
| Cluster at unit level | `cluster = ~id` |

```r
# fixest event study
feols(y ~ i(reltime, ref = -1) + controls | id + period,
      data = df, cluster = ~id)
iplot(fit)   # event study plot

# Test pre-trends jointly
library(car)
linearHypothesis(fit, c("reltime::-4 = 0", "reltime::-3 = 0",
                          "reltime::-2 = 0"))
```

**Anti-patterns**:
- Binning event-time endpoints without transparency (affects pre-trend estimates)
- Using period 0 as base period (conflates effect onset with normalization)
- Not showing the full pre-period even when long

---

## 5. Synthetic Control

**When applicable**: Single (or few) treated units; long pre-treatment period;
can construct a weighted average of donor units to match pre-treatment outcomes.

**Required diagnostics (P0 if missing)**:

| Diagnostic | Test |
|-----------|------|
| Pre-treatment fit | MSPE ratio (treated vs. synthetic control); report |
| In-space placebo | Run synthetic control for all donor units; show distribution of ratios |
| In-time placebo | Run synthetic control ending before actual treatment |
| Covariate predictors | Document which covariates enter the synthetic control matching |

```r
# R — Synth package
library(Synth)
dp <- dataprep(
  foo = df, predictors = c("gdp", "trade", "invest"),
  dependent = "outcome", unit.variable = "id",
  time.variable = "year", treatment.identifier = 1,
  controls.identifier = 2:20,
  time.predictors.prior = 1975:1990,
  time.optimize.ssr = 1975:1990,
  time.plot = 1975:2000
)
synth_out <- synth(dp)
path.plot(synth.res = synth_out, dataprep.res = dp)

# In-space placebo: loop over all donor units
```

**Anti-patterns**:
- Poor pre-treatment fit (high MSPE) without comment
- Not running in-space placebos
- Adding donor units until fit is good (cherry-picking)

**References**: Abadie, Diamond & Hainmueller (2010) JASA;
Abadie (2021) JEL

---

## 6. Matching and Inverse Probability Weighting (IPW)

**When applicable**: Selection-on-observables assumption; rich set of covariates
that explain treatment assignment.

**Required diagnostics (P0 if missing)**:

| Diagnostic | Test |
|-----------|------|
| Common support | Overlap plot (propensity score distributions by treatment status) |
| Covariate balance | Standardized mean differences before/after matching; target < 0.1 |
| Balance table | Report SMDs for all key covariates |
| Trimming rule | Document any trimming of extreme propensity scores |

```r
# R — MatchIt (requires MatchIt >= 4.0; v3 → v4 has breaking API changes)
library(MatchIt)
stopifnot("MatchIt >= 4.0.0 required (v3 -> v4 has breaking API changes)" =
  packageVersion("MatchIt") >= "4.0.0")
m_out <- matchit(treat ~ x1 + x2 + x3, data = df, method = "nearest",
                  distance = "logit", ratio = 1)
summary(m_out, standardize = TRUE)   # balance table
love.plot(m_out, threshold = 0.1)     # Love plot

# Matched-sample N validation
matched_n <- nrow(match.data(m_out))
message("Matched sample N: ", matched_n, " of ", nrow(df), " original observations")
stopifnot("Matching dropped >50% of sample" = matched_n > nrow(df) * 0.5)

# IPW with WeightIt
library(WeightIt)
w_out <- weightit(treat ~ x1 + x2 + x3, data = df,
                   method = "ps", estimand = "ATE")
summary(w_out)

# Stata — prefer teffects psmatch over psmatch2 (psmatch2 has known caliper/ties bugs)
teffects psmatch (y) (treat x1 x2 x3), atet nn(1)
tebalance summarize                      // balance table
```

**Doubly-robust estimator** (preferred):
```r
# AIPW — combines outcome regression + IPW
library(AIPW)
aipw_fit <- AIPW$new(Y = df$y, A = df$treat,
                      W = df[, c("x1","x2","x3")],
                      Q.SL.library = c("SL.glm", "SL.mean"),
                      g.SL.library = c("SL.glm", "SL.mean"))
aipw_fit$stratified_fit()
aipw_fit$summary(g.bound = 0.025)
```

**Anti-patterns**:
- Matching without checking common support (extrapolation beyond support)
- Reporting only pre-matching balance
- Using 1:1 matching when k:1 with caliper gives better balance
- Ignoring heavy-tailed propensity scores (trim or stabilize weights)

---

## 7. Strategy Selection Guide

| Setting | Recommended Strategy | Key Assumption |
|---------|---------------------|----------------|
| Known threshold, running variable | RDD | No manipulation at cutoff |
| Natural experiment, valid instrument | IV/2SLS | Relevance + exogeneity |
| Panel data, staggered treatment | Callaway-Sant'Anna DiD | Parallel trends |
| Single treated unit, long panel | Synthetic Control | Convex hull of donors |
| Rich covariates, no panel | Matching/IPW/AIPW | Unconfoundedness |
| Time series event | Event study | Stable unit / no anticipation |
| Structural model, theory | Structural estimation | Model correctly specified |

**Decision tree for instrument validity**:
1. Can you articulate the economic mechanism linking Z → X (relevance)?
   - No → not a valid instrument
2. Can you argue Cov(Z, ε) = 0 (exogeneity) from first principles?
   - No → not a valid instrument
3. Does the first-stage F exceed Stock-Yogo critical value?
   - No → weak instrument; consider LIML or Fuller-k estimator

---

## 8. Anti-Patterns

| Anti-Pattern | Why It's Wrong | Fix |
|-------------|----------------|-----|
| Omitting McCrary test for RDD | Cannot verify no manipulation | Always run `rddensity` |
| TWFE for staggered DiD | Negative-weighted estimates | Use Callaway-Sant'Anna |
| IV without first-stage table | Cannot assess instrument strength | Always report first-stage |
| Matching without Love plot | Reader cannot assess balance | Use `love.plot()` or equivalent |
| Calling selection-on-observables "causal" without overlap check | Extrapolation | Trim extreme propensity scores |
| Checking pre-trends only graphically | Informal | Run joint hypothesis test too |
| Claiming exogeneity of IV from test alone | J-test only tests over-identifying restrictions; one instrument always passes | Provide economic argument |
