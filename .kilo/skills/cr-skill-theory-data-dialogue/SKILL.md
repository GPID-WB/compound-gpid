---
name: cr-skill-theory-data-dialogue
module: research
description: "Theory-data dialogue for structural economics research. Covers
  distributional assumption tests, conditional moment checks, support analysis,
  reduced-form regressions before structural estimation, exclusion restriction
  validation, monotonicity tests, balance tests, and the documentation trail
  in .cg-docs/research/specifications/. Loaded for Specification Analysis and
  Theory/Modeling tasks."
---

# Theory-Data Dialogue

Reference skill for aligning structural model assumptions with the data.
The core principle: **before estimating structural parameters, verify that
the data are consistent with each maintained assumption.**

Store all specification checks in `.cg-docs/research/specifications/` with
dated file names and the `status: draft | reviewed | final` frontmatter field.

---

## 1. Theory-Data Dialogue Pattern

**The dialogue loop** (run before structural estimation):

```
1. State assumption: "I assume errors ε_i ~ N(0, σ²)"
2. Derive testable implication: "Residuals should be approximately normal"
3. Test with data: "Q-Q plot + Shapiro-Wilk + Jarque-Bera"
4. Evaluate: "p = 0.003 — normality rejected"
5. Model response: "Switch to t-distributed errors; add skew-normal robustness check"
6. Document: Write up in .cg-docs/research/specifications/
```

Every maintained assumption that is testable must go through this loop.
Assumptions that are not directly testable must be justified economically.

**Specification file template** (`.cg-docs/research/specifications/`):

```yaml
---
title: "Distributional Assumption Check — Normal Wage Errors"
model: "Normal wage equation"
assumption: "ε_i ~ N(0, σ²)"
date: YYYY-MM-DD
status: "draft"
outcome: "rejected | supported | inconclusive"
action-taken: "Switched to student-t errors"
code-file: "spec-checks/distributional-checks.R"
---
```

---

## 2. Distributional Tests

**When to use**: Before imposing parametric assumptions on error terms,
residuals, or unobservables.

```r
# R — normality tests on residuals
residuals_fit <- residuals(lm(y ~ x, data = df))

# Shapiro-Wilk (recommended for n < 5000)
shapiro.test(residuals_fit)

# Jarque-Bera (skewness + kurtosis)
library(moments)
jarque.test(residuals_fit)

# Q-Q plot (always include graphically)
qqnorm(residuals_fit); qqline(residuals_fit)

# Kolmogorov-Smirnov test against normal
ks.test(scale(residuals_fit), "pnorm")

# Stata
predict resid, resid
qnorm resid                              // Q-Q plot
sktest resid                             // skewness-kurtosis test
```

**For non-normal alternatives**:
```r
# Fit t-distribution to residuals
library(MASS)
fitdistr(residuals_fit, densfun = "t")  # estimate df parameter

# Test against exponential (for duration models)
library(fitdistrplus)
fitdist(abs(residuals_fit), "exp")
```

**Documentation**: Always report the test statistic, degrees of freedom,
p-value, and sample size. State the action taken if assumption is rejected.

---

## 3. Conditional Moment Checks

**When to use**: Verify that conditional expectations implied by the model
hold in the data (key for GMM validity and model specification).

```r
# Check E[ε | X] = 0 (mean independence)
# Method: regress residuals on X; test joint significance
resid_model <- lm(residuals_fit ~ poly(x1, 2) + poly(x2, 2) + x1:x2,
                   data = df)
car::linearHypothesis(resid_model, matchCoefs(resid_model, "x"))
# H0: all coefficients on X are zero → should not reject

# RESET test for functional form
library(lmtest)
resettest(fit, power = 2:3, type = "fitted")

# Stata
estat imtest                // White's test for heteroscedasticity + specification
estat ovtest                // Ramsey RESET
```

**Weighted conditional moments** (for survey data):
```r
library(collapse)
# Weighted mean of residuals by covariate quartile
df[, resid := residuals(fit)][, x1_q := cut(x1, quantile(x1, 0:4/4))]
fmean(df$resid, g = df$x1_q, w = df$weight)
# All cells should be near zero
```

---

## 4. Support Analysis

**When to use**: Before structural estimation, verify that the joint support
of the data is compatible with the model (e.g., a logit cannot predict
probabilities of 0 or 1, but perfect separation causes this).

```r
# Check for perfect separation in discrete choice models
library(brglm2)
# Attempt to estimate logit; brglm2 warns on separation
brglm_fit <- glm(y ~ x, data = df, family = binomial,
                  method = brglm_fit)

# Check continuous model support: are any regressors constant?
stopifnot(all(apply(df[, .SD, .SDcols = regressor_cols], 2, var) > 0))

# Check for extreme values that distort estimation
summary(df[, .SD, .SDcols = regressor_cols])
# Winsorize or flag outliers

# Stata
inspect y x1 x2           // min, max, missing counts
tabulate y                  // frequency table for discrete outcomes
```

**Identification at infinity flag**: If the structural model is identified
only as a covariate approaches the boundary of its support (e.g., Heckman
selection model), flag this explicitly:

```markdown
> **Identification at Infinity Risk**: The exclusion restriction operates near
> the upper tail of Z. Only X% of observations have Z > 2σ above mean.
> Finite-sample estimates may be fragile to this subpopulation.
> Sensitivity analysis: re-estimate excluding the top 5% of Z values.
```

---

## 5. Reduced-Form Regressions

**When to use**: Before structural estimation, run flexible reduced-form
regressions to verify that the reduced-form relationships implied by the
structural model are present in the data.

**The reduced-form roadmap**:
1. What does the structural model predict about reduced-form relationships?
2. Run flexible OLS/non-parametric regression to test each prediction
3. If reduced form is inconsistent with structural model predictions → stop
   and diagnose before proceeding to structural estimation

```r
# Example: structural model predicts y = f(x, z) where z → x → y
# Reduced-form check 1: first stage x on z
fs <- feols(x ~ z + controls | fe, data = df)
summary(fs)  # must be significant with correct sign

# Reduced-form check 2: reduced form y on z
rf <- feols(y ~ z + controls | fe, data = df)
summary(rf)  # sign of z on y should be consistent with β_x × β_z

# Reduced-form check 3: flexible relationship shape
library(mgcv)
gam_fit <- gam(y ~ s(x) + s(z), data = df)
plot(gam_fit)  # visual check of functional form
```

**Anti-patterns**:
- Running structural estimation without first verifying reduced-form
  relationships ("black box" structural estimation)
- Finding conflicting reduced-form results and proceeding anyway without
  diagnosing

---

## 6. Exclusion Restriction Checks

**When to use**: Validate that proposed instruments do not directly affect
the outcome through channels other than the endogenous variable.

**Falsification tests**:
```r
# Test 1: instrument should not predict outcome in subgroups where it
# cannot affect the endogenous variable
# Example: if Z is a supply-side shock, test Z on y for consumers unaffected
# by the supply shift
feols(y ~ z, data = df[unaffected_group == 1])
# Should find near-zero coefficient

# Test 2: instrument should not predict pre-treatment outcome
feols(y_pre ~ z + controls, data = df)
# Should find near-zero coefficient

# Test 3: over-identification test (if multiple instruments)
iv_fit <- feols(y ~ controls | fe | x ~ z1 + z2, data = df)
fitstat(iv_fit, ~sargan)  # Sargan J-test
```

**Documentation requirement**: Provide the economic argument for why each
instrument satisfies the exclusion restriction. Tests alone are insufficient
(they only check over-identifying restrictions; a just-identified model
always passes). File: `.cg-docs/research/specifications/instrument-validity.md`

---

## 7. Monotonicity Checks (IV)

**When to use**: IV identifies LATE for compliers only under the monotonicity
assumption (treatment probability weakly increases in instrument for all units).

```r
# Check monotonicity: treatment rate should be monotone in instrument
df |>
  group_by(z) |>
  summarise(p_treat = mean(treat), .groups = "drop") |>
  arrange(z)
# p_treat should be weakly increasing in z

# Violation: some z values increase treatment for some groups but
# decrease it for others (defiers exist) → LATE is not identified
# Check by subgroup
df |>
  group_by(z, subgroup) |>
  summarise(p_treat = mean(treat), .groups = "drop")
```

---

## 8. Balance Tests

**When to use**: Verify that conditioning on observables (or randomization)
produces balanced groups. Required for matching, RCTs, DiD pre-trends.

```r
# R — standardized mean differences
library(tableone)
CreateTableOne(vars = covariates, strata = "treat", data = df,
               test = FALSE) |>
  print(smd = TRUE)     # standardized mean differences; target < 0.1

# Balance test with regression (joint F-test)
balance_model <- lm(treat ~ x1 + x2 + x3 + x4, data = df)
car::linearHypothesis(balance_model,
                       matchCoefs(balance_model, c("x1","x2","x3","x4")))
# H0: all covariates balanced; should NOT reject under randomization

# Stata
iebaltab x1 x2 x3, grpvar(treat) vce(robust) savetex(balance.tex)
```

**Stata (iebaltab — from ietoolkit)**:
```stata
iebaltab x1 x2 x3 x4, grpvar(treat) vce(robust) savetex(balance-table.tex)
```

---

## 9. Documentation Trail

All specification checks must be traceable. Structure:

```
.cg-docs/research/specifications/
  YYYY-MM-DD-[model-name]-distributional-checks.md
  YYYY-MM-DD-[model-name]-instrument-validity.md
  YYYY-MM-DD-[model-name]-reduced-form-regressions.md
  YYYY-MM-DD-[model-name]-support-analysis.md
  YYYY-MM-DD-[model-name]-balance-tests.md
```

Each file should have:
- Assumption stated precisely
- Test run (with code reference)
- Result (test statistic, p-value, sample size)
- Outcome: supported / rejected / inconclusive
- Action taken if rejected

---

## 10. Anti-Patterns

| Anti-Pattern | Why It's Wrong | Fix |
|-------------|----------------|-----|
| No distributional tests before parametric MLE | Inconsistent if misspecified | Always run Q-Q + Jarque-Bera |
| Checking reduced form after structural estimation | Confirmation bias | Reduced form first, always |
| Documenting only passing tests | Selective reporting (P0) | Report all tests; note failures |
| "Instrument is valid by design" | Exogeneity not tested | Provide falsification tests + economic argument |
| No support check before estimation | Extrapolation, perfect separation | Check with `inspect`, `summary`, overlap plot |
| Monotonicity assumed, not checked | LATE not identified with defiers | Tabulate treatment rate by instrument |
| Balance table in appendix only | Obscures potential imbalance | Always in main text or summary |
