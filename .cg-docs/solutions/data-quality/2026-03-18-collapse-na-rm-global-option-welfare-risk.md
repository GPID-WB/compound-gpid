---
date: 2026-03-18
title: "collapse na.rm global option differs from base R and affects all f* functions"
category: "data-quality"
language: "R"
tags: [collapse, na.rm, global-options, set_collapse, welfare-measurement, silent-errors]
root-cause: "collapse defaults na.rm = TRUE via a global option system, opposite of base R's FALSE; changing it globally breaks all welfare patterns silently"
severity: "P1"
---

# collapse na.rm Global Option: Default TRUE, Opposite of Base R

## Problem

All collapse Fast Statistical Functions (`fmean`, `fsum`, `fmedian`, `fvar`, etc.) default to `na.rm = TRUE` — the **opposite** of base R functions like `mean()` which propagate NA. This is controlled by a global option system, not a hardcoded default.

Two failure modes:

1. **Unaware mode**: Code silently drops NA observations from welfare aggregations. A survey with 5% missing welfare values computes poverty rates over 95% of the population as if it were 100%. No warning.

2. **Changed-mode**: A script earlier in the session calls `set_collapse(na.rm = FALSE)`. All subsequent `fmean`/`fsum` calls now propagate NA and return `NA` instead of estimates. Welfare calculations silently fail.

## Root Cause

collapse uses an internal `.op` environment for performance-critical configuration. All Fast Statistical Functions read:

```r
na.rm = .op[["na.rm"]]
```

The package default is `TRUE`. Users can change this globally:

```r
set_collapse(na.rm = FALSE)  # Now ALL f* functions propagate NA
```

If any code in a session calls `set_collapse(na.rm = FALSE)` and doesn't restore it, all downstream welfare patterns return `NA` without any error.

## Solution

### Document the behavior

The `collapse-reference.md` Global Options section now explains this:

```r
# Default behavior (na.rm = TRUE)
fmean(c(1, 2, NA, 4))          # Returns 2.333...

# Changed globally — breaks all welfare patterns!
set_collapse(na.rm = FALSE)
fmean(c(1, 2, NA, 4))          # Returns NA

# Per-call override
fmean(c(1, 2, NA, 4), na.rm = TRUE)
```

### Defensive pre-checks for welfare work

Add explicit NA validation before any FGT, Gini, or SE calculation:

```r
# Before FGT block
stopifnot(!anyNA(dt$welf_pc_ppp_day), !anyNA(dt$weight), all(dt$weight > 0))
```

This makes NA failures explicit (error) rather than silent (wrong number).

### Never change global na.rm in analytical scripts

```r
# WRONG — do not use in scripts with welfare calculations
set_collapse(na.rm = FALSE)

# RIGHT — override per call if needed
fmean(x, na.rm = FALSE)
```

## Prevention

- Add `!anyNA()` check before every welfare aggregation block.
- Never call `set_collapse(na.rm = FALSE)` in scripts that perform welfare calculations.
- If you need base-R-like NA propagation for a single call, use the `na.rm = FALSE` argument directly rather than changing the global setting.
- The `weighted_gini()` helper drops NA silently with a warning — always validate inputs upstream.

## Related

- `cg-skill-r-analytical/references/collapse-reference.md` — Global Options section
- `cg-skill-r-analytical/workflows/welfare-patterns.md` — NA callout and `stopifnot` guard before FGT
- `2026-03-17-null-welfare-silently-biases-poverty-rate.md` — related silent failure from null welfare values
