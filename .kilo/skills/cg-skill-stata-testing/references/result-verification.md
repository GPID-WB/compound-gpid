# Result Verification in Stata

Verify model outputs immediately after estimation. Assertions on coefficients, significance, and diagnostics catch specification errors before they propagate to tables and reports.

## Coefficient Sign and Magnitude

Access stored estimation results via `_b[]` and `_se[]`:

```stata
regress log_welfare log_income i.urban [aw=weight]

* Assert income elasticity is positive
assert _b[log_income] > 0

* Assert elasticity is in a plausible range (0 to 2)
assert _b[log_income] < 2.0

* Assert urban coefficient is positive (urban premium exists)
assert _b[1.urban] > 0
```

For complex specifications, store coefficients in locals for readable assertions:

```stata
local b_income = _b[log_income]
local se_income = _se[log_income]

assert `b_income' > 0
assert `b_income' < 2.0
assert `se_income' < 0.5    // standard error not unreasonably large
```

## Precision-Aware Comparison with `reldif`

Never use `==` to compare floating-point results. Use `reldif()` for relative difference or `abs()` for absolute tolerance:

```stata
* reldif(a, b) = |a - b| / (|b| + 1)
* Close to 0 means a ≈ b

* Assert estimate matches cached value within 1 part per million
assert reldif(_b[treatment], 0.0342) < 1e-6

* Absolute tolerance for near-zero values
assert abs(_b[treatment] - 0.0342) < 0.0001
```

Use `reldif` when the expected value is well away from zero; use `abs()` tolerance when the value may be near zero (to avoid division by near-zero in `reldif`).

## Statistical Significance Checks

Use the `test` command and inspect `r(p)` for p-values:

```stata
regress outcome treatment controls

* Assert treatment effect is statistically significant at 5%
test treatment = 0
assert r(p) < 0.05

* Assert pre-treatment period is NOT significant (parallel trends)
test 1.treated#1.pre_period = 0
assert r(p) > 0.05

* Joint significance of controls
test controls_var1 controls_var2 controls_var3
assert r(p) < 0.10
```

For Wald tests on nonlinear combinations, use `lincom` and inspect `r(se)` and `r(estimate)`.

## Model Diagnostic Assertions

```stata
regress outcome treatment controls [aw=weight]

* Assert observation count is within expected range
assert e(N) >= 1000
* Note: exact equality (e(N) == _N) fires for any missing covariate via listwise deletion — a
* normal Stata behavior, not a bug. Assert a minimum retention rate instead:
assert e(N) >= _N * 0.90    // at least 90% of observations retained after listwise deletion

* Assert R-squared is plausible (not suspiciously perfect)
assert e(r2) > 0.01
assert e(r2) < 0.99

* Assert F-statistic is significant (model has explanatory power)
assert e(F) > 1.0

* Assert model converged (for ML estimators)
assert e(converged) == 1    // logit, probit, etc.
```

## Cross-Specification Stability

Run multiple specifications and assert coefficient stability:

```stata
* Specification 1: basic
regress outcome treatment
local b1 = _b[treatment]

* Specification 2: with controls
regress outcome treatment controls
local b2 = _b[treatment]

* Specification 3: clustered SE
regress outcome treatment controls, vce(cluster district)
local b3 = _b[treatment]

* Assert stable across specs — calibrate tolerance to domain:
* < 0.05 for welfare/poverty estimates (5% rel. difference ≈ ±2pp on a 0.45 headcount)
* Looser tolerances (< 0.20) risk masking large covariate sensitivity — document if used.
assert reldif(`b1', `b2') < 0.05    // welfare statistics: 5% max relative difference
assert reldif(`b2', `b3') < 0.01    // same point estimate, only SE changes
```

## FGT Poverty Index Checks

FGT indices must satisfy mathematical properties:

```stata
* After computing poverty measures
* Requires: ssc install povdeco (or equivalent). Return names (head_count, poverty_gap,
* poverty_severity) are povdeco-specific. Other packages: r(p0)/r(FGT0), r(p1), r(p2) — check help.
poverty welfare [aw=weight], line(`poverty_line')

* Assert FGT0 (headcount) is a proportion
assert inrange(r(head_count), 0, 1)

* Assert FGT1 (poverty gap) ≤ FGT0 (poverty gap ≤ headcount always)
assert r(poverty_gap) <= r(head_count)

* Assert FGT2 (squared gap) ≤ FGT1
assert r(poverty_severity) <= r(poverty_gap)

* Assert monotonicity: higher line → higher headcount
local hc_190 = r(head_count)
poverty welfare [aw=weight], line(3.20)
assert r(head_count) >= `hc_190'
```

## Checking Scalar Results from Stored Returns

After any command, inspect `r()` or `e()` returns immediately — they are overwritten by the next command:

```stata
* Capture result before it is overwritten
summarize welfare [aw=weight]
local mean_welfare = r(mean)
local sd_welfare = r(sd)

* Run next command
...

* Now assert on stored locals (not r() which has changed)
assert `mean_welfare' > 0
assert `sd_welfare' > 0
assert `mean_welfare' < `sd_welfare' * 10    // mean within 10 SDs
```

## Regression Table Spot-Checks

After building a results matrix with `estimates store` / `estout`, verify key cells:

```stata
estimates store spec1
estimates store spec2

* Retrieve and check coefficient from stored estimate
estimates restore spec1
local b_spec1 = _b[treatment]    // store before switching to spec2
assert `b_spec1' > 0

estimates restore spec2
assert reldif(`b_spec1', _b[treatment]) < 0.20    // stability check
```
