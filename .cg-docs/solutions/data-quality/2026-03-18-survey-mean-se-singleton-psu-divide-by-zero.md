---
date: 2026-03-18
title: "survey_mean_se() divides by zero on singleton PSU strata"
category: "data-quality"
language: "R"
tags: [collapse, survey, standard-errors, taylor-linearization, poverty-measurement, divide-by-zero]
root-cause: "Variance formula n_h/(n_h-1) produces Inf when a stratum has exactly 1 PSU (certainty strata)"
severity: "P1"
---

# survey_mean_se() Divides by Zero on Singleton PSU Strata

## Problem

`survey_mean_se()` returns `se = Inf` and `ci_lower/ci_upper = ±Inf` with no error or warning when any stratum contains exactly one Primary Sampling Unit (PSU). This is silent — the function completes and returns a result that looks plausible but is meaningless.

Certainty strata (strata with a single PSU selected with probability 1) are common in complex LSMS and household survey designs. Analysts may not notice the Inf values if they don't inspect SE output carefully.

## Root Cause

The Taylor linearization variance formula is:

```
V(θ̂) = (1/N²) * Σ_h [ n_h / (n_h - 1) ] * Σ_k (z_hk - z̄_h)²
```

When `n_h = 1` (one PSU in stratum h), `n_h - 1 = 0`, so `n_h / (n_h - 1) = Inf`.

The entire variance sum becomes `Inf`, leading to `se = sqrt(Inf) = Inf`.

## Solution

Add an explicit guard before computing `v_h`, providing a descriptive error that names the offending strata:

```r
# In the strat_stats data.table, after computing n_psu:
singleton_strata <- strat_stats[n_psu < 2, stratum]
if (length(singleton_strata) > 0)
  stop("Certainty strata (1 PSU) cannot use Taylor linearization: ",
       paste(singleton_strata, collapse = ", "),
       "\n  Consider collapsing with adjacent strata or using a replicate weight method.")
```

Also add input validation at function entry to catch NA/length mismatches early:

```r
survey_mean_se <- function(x, w, psu, stratum) {
  n <- length(x)
  stopifnot(
    is.numeric(x), is.numeric(w),
    !anyNA(x), !anyNA(w), !anyNA(psu), !anyNA(stratum),
    length(w) == n, length(psu) == n, length(stratum) == n,
    all(w > 0)
  )
  # ...
}
```

## Prevention

- Always validate survey design inputs before variance estimation.
- Taylor linearization requires ≥ 2 PSUs per stratum. For certainty strata, use one of:
  1. Collapse the certainty stratum with an adjacent stratum (common in practice)
  2. Use a replicate weight method (BRR or jackknife via `srvyr`) for designs with singleton strata
  3. Set the variance contribution of certainty strata to zero (advanced — requires domain knowledge)
- When building survey SE helpers, always add a stratum-level check before any `n_h / (n_h - 1)` computation.

## Related

- `cg-skill-r-analytical/workflows/survey-analysis.md` — canonical `survey_mean_se()` helper with this guard applied
- `2026-03-17-null-welfare-silently-biases-poverty-rate.md` — related silent data quality failure in welfare measurement
