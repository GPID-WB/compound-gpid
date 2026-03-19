---
date: 2026-03-18
title: "Zero or negative welfare values silently inflate FGT(1) and FGT(2) beyond their valid range"
category: "data-quality"
language: "R"
tags: [fgt, poverty-measurement, welfare, data-validation, collapse, fifelse, poverty-gap, silent-errors]
root-cause: "FGT gap formula (poverty_line - welfare) / poverty_line returns values > 1 when welfare <= 0; collapse computes this silently with no warning"
severity: "P1"
---

# Zero or Negative Welfare Values Silently Inflate FGT(1) and FGT(2) Beyond Their Valid Range

## Problem

The FGT(1) poverty gap index and FGT(2) squared poverty gap index both assume welfare is **strictly
positive**. When a welfare value is zero or negative, the gap formula produces a value **greater
than 1**:

```r
poverty_line <- 2.15
welfare      <- 0        # zero consumption — possible coding error

gap <- (poverty_line - welfare) / poverty_line
# gap = (2.15 - 0) / 2.15 = 1.0   ← exactly 1, valid edge case

welfare <- -0.5          # negative — always a data error
gap <- (2.15 - (-0.5)) / 2.15
# gap = 2.65 / 2.15 = 1.233...    ← > 1, INVALID
```

Since `fmean()` averages all gaps (including those > 1) without any bounds checking or warning,
the resulting FGT(1) silently exceeds 1 — which is mathematically impossible for a correctly
computed poverty gap index.

## Root Cause

The FGT gap formula assumes `0 < welfare < poverty_line` for poor households. collapse's `fmean()`
and `fifelse()` are general-purpose functions with no domain awareness; they apply the formula
to whatever values are present. Negative welfare can enter the data from:

- Unit errors (currency sign reversal)
- Imputation artifacts
- Survey coding conventions (negative = "refused to answer")
- Merge/join errors producing negative imputed consumption

## Solution

Add an explicit pre-check before any FGT calculation block:

```r
# Before FGT computation — fail loudly rather than silently corrupt results
stopifnot(
  !anyNA(dt$welf_pc_ppp_day),
  all(dt$welf_pc_ppp_day > 0),   # negative/zero welfare inflates gap beyond 1
  !anyNA(dt$weight),
  all(dt$weight > 0)
)

# Now safe to compute gaps
dt[, `:=`(
  poor   = welf_pc_ppp_day < 2.15,
  gap    = fifelse(welf_pc_ppp_day < 2.15, (2.15 - welf_pc_ppp_day) / 2.15, 0),
  gap_sq = fifelse(welf_pc_ppp_day < 2.15, ((2.15 - welf_pc_ppp_day) / 2.15)^2, 0)
)]
```

If zero welfare is a valid boundary condition in your data (subsistence farming, in-kind transfers):
- Decide on a handling policy (exclude, floor at ε, treat as 0 gap)
- Document the decision explicitly in code comments before the pre-check

## Prevention

- **Always** run the 4-condition `stopifnot` block before any FGT calculation (see `welfare-patterns.md`)
- Add `all(dt$welf_pc_ppp_day > 0)` specifically — NA-check alone is not sufficient
- Include a validity test in your test suite:

```r
test_that("FGT pre-check rejects non-positive welfare", {
  dt_bad <- data.table(welfare = c(-1, 0.5, 1), weight = c(1, 1, 1))
  expect_error(
    stopifnot(all(dt_bad$welfare > 0)),
    regexp = NA   # any error is acceptable — we just want it to stop
  )
})
```

- After computing FGT values, add a post-condition assertion:

```r
stopifnot(fgt1 >= 0, fgt1 <= 1, fgt2 >= 0, fgt2 <= fgt1)
```

## Related

- [collapse na.rm global option](./2026-03-18-collapse-na-rm-global-option-welfare-risk.md) — companion data-quality risk: NA welfare silently excluded
- [`welfare-patterns.md`](../../../../.github/skills/cg-skill-r-analytical/workflows/welfare-patterns.md) — full FGT pre-check pattern and PPP/CPI deflator validation guards
- [`r-analytical-anti-patterns.md`](../../../../.github/skills/cg-skill-r-analytical/references/r-analytical-anti-patterns.md) — "Computing FGT or Gini without validating welfare and weights first" anti-pattern
