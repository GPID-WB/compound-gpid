---
date: 2026-05-21
title: "mice(m=1) is single imputation for ML prediction — not multiple imputation"
category: "data-quality"
language: "R"
tags: [mice, imputation, single-imputation, multiple-imputation, ml-pipeline, cv-fold, data-leakage]
root-cause: "mice() with m=1 is invoked through the multiple imputation framework but produces only one imputed dataset — equivalent to single imputation. Labeling it 'multiple imputation' misleads practitioners about inference validity."
severity: "P2"
---

# mice(m=1) Is Single Imputation for ML Prediction — Not Multiple Imputation

## Problem

`cr-skill-ml-economics/SKILL.md` documented the preferred missing-data strategy for MAR data as "**Multiple imputation inside each CV fold**" and showed:

```r
train_imputed <- mice(train_df, m = 1, method = "pmm", seed = 42)
train_complete <- complete(train_imputed)
# Fit model on train_complete; impute test fold using the same mice object
```

Two problems:
1. `m=1` is **single** imputation. Calling it "multiple imputation" misleads practitioners into thinking it has the statistical properties of multiple imputation (variance accounting, Rubin's rules).
2. The comment "impute test fold using the same mice object" was a stub — no working code was provided. Applying `complete()` to the training `mids` object on test data silently fails or produces wrong output.

## Root Cause

The author likely conflated "using the `mice` package" with "doing multiple imputation." `mice` is designed for multiple imputation but works with `m=1` for single imputation. For ML **prediction** tasks, `m=1` is statistically sufficient and computationally cheaper — but only if labeled correctly.

The test-fold stub was a placeholder that was never completed.

## Solution

### Labeling

Use `m=1` and label it explicitly as single imputation:

| Missing mechanism | Strategy |
|---|---|
| MCAR | Listwise deletion acceptable — document explicitly |
| MAR | Single imputation per CV fold — use m≥5 with Rubin's rules for inference (see below) |
| MNAR | Document + sensitivity analysis |

### Working test-fold imputation (prevents data leakage)

```r
# m=1: single imputation — sufficient for ML prediction
train_imputed  <- mice(train_df, m = 1, method = "pmm", seed = 42)
train_complete <- complete(train_imputed)

# Apply the FITTED mice object to the test fold (prevents leakage)
# Option A: mice.reuse() (mice >= 3.16)
test_imputed  <- mice.reuse(train_imputed, test_df, seed = 42)
test_complete <- complete(test_imputed)

# Option B: tidymodels — step_impute_bag() inside a recipe;
# prep() fits on train fold, bake() applies fitted imputer to test fold
```

**Key distinction**:
- `mice.reuse()` applies the **fitted** mice object to new data without refitting — equivalent to `predict()` for imputation, which is what prevents leakage.
- `mice(test_df, ...)` from scratch would refit on test data — **leakage**.

### When to use m ≥ 5 (inference context)

For econometric inference (standard errors, confidence intervals, hypothesis tests):
- Use `m >= 5` to generate multiple imputed datasets
- Pool estimates with Rubin's rules: `pool(with(imputed_list, lm(...)))`
- `m=1` is inappropriate for inference — it underestimates variance

## Prevention

- In any code block using `mice()`, check `m=`: if `m=1`, label as "single imputation"; if `m>=5`, label as "multiple imputation with Rubin's rules pooling"
- Never leave test-fold imputation as a comment stub — always provide a working `mice.reuse()` or recipe-based alternative
- Pester test guard: `($content -match '(?i)m\s*=\s*1.*single imputation|single imputation.*m\s*=\s*1')` — verifies the m=1 labeling is present

## Related

- `cr-skill-ml-economics/SKILL.md` Section 2b — Missing Data in ML Pipelines (source of this fix)
- `.cg-docs/solutions/data-quality/2026-03-17-null-welfare-silently-biases-poverty-rate.md` — related: silent correctness failures from mislabeled operations
