---
date: 2026-03-17
title: "Null welfare values silently bias poverty rate — must drop before computing"
category: "data-quality"
language: "Python"
tags: [polars, poverty, welfare, null, weights, data-quality, gpid, survey-data]
root-cause: "polars .filter() excludes null rows from numerator but .sum() on the full DataFrame still includes their weights in the denominator, understating the poverty rate"
severity: "P1"
---

# Null welfare values silently bias poverty rate

## Problem

A headcount poverty rate computed over survey microdata is systematically
lower than expected. No errors or warnings are raised. The issue is silent.

```python
# WRONG — silently biased
def compute_poverty_rate(df, welfare_col, weight_col, poverty_line):
    poor = df.filter(pl.col(welfare_col) < poverty_line)
    rate = poor[weight_col].sum() / df[weight_col].sum()
    return rate
```

When `welfare_col` contains nulls, polars' `filter` excludes null-welfare rows
from `poor` (they fail the `< poverty_line` comparison), but `df[weight_col].sum()`
still counts their survey weights in the denominator. Those households are
implicitly treated as **non-poor** rather than as **missing data**, understating
the poverty rate.

A second silent failure: `df[weight_col].sum()` with null weights silently drops
those nulls, understating the denominator further.

## Root Cause

polars `.filter(expr)` propagates nulls as `false` — rows where the expression
evaluates to `null` are excluded. This is by design and mathematically correct
within polars. The bug is assuming the denominator (`df[weight_col].sum()`)
represents the same population as the numerator. When welfare nulls exist, the
two populations diverge.

The same class of error applies to any weighted statistic: weighted mean,
Gini coefficient, poverty gap, severity index.

## Solution

Drop null welfare rows explicitly before any poverty computation. Log the
affected weight share so the caller knows how much data was lost:

```python
import polars as pl
from loguru import logger
from your_package.exceptions import DataQualityError, InsufficientSampleError


def compute_poverty_rate(
    df: pl.DataFrame,
    welfare_col: str,
    weight_col: str,
    poverty_line: float,
) -> float:
    """Compute headcount poverty rate with explicit null handling."""
    # --- Input validation ---
    missing = [c for c in [welfare_col, weight_col] if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns: {missing}")

    if poverty_line <= 0:
        raise ValueError(f"poverty_line must be positive, got {poverty_line}")

    # --- Weight quality checks (null weights corrupt the denominator silently) ---
    null_weights = df[weight_col].null_count()
    if null_weights > 0:
        raise DataQualityError(
            f"Weight column {weight_col!r} contains {null_weights} null values",
            n_failing=null_weights,
        )
    if not (df[weight_col] > 0).all():
        n_bad = (df[weight_col] <= 0).sum()
        raise DataQualityError(
            f"Weight column {weight_col!r} has non-positive values",
            n_failing=n_bad,
        )

    # --- Welfare null handling — must drop BEFORE computing, not rely on filter ---
    n_null_welfare = df[welfare_col].null_count()
    if n_null_welfare > 0:
        dropped_weight_share = (
            df.filter(pl.col(welfare_col).is_null())[weight_col].sum()
            / df[weight_col].sum()
        )
        logger.warning(
            "Dropping null welfare rows before poverty computation",
            n_dropped=n_null_welfare,
            dropped_weight_share=round(dropped_weight_share, 4),
        )
        df = df.drop_nulls(subset=[welfare_col])

    if df.height < 100:
        raise InsufficientSampleError(n=df.height, minimum=100)

    # --- Compute on clean data ---
    poor = df.filter(pl.col(welfare_col) < poverty_line)
    rate = poor[weight_col].sum() / df[weight_col].sum()

    logger.debug(
        "Poverty rate computed",
        poverty_line=poverty_line,
        rate=round(rate, 4),
        n_obs=df.height,
    )
    return rate
```

## Prevention

**General rule**: Never use `fill_null(0)` on welfare or income columns.
`null` welfare means *data is missing*, not zero consumption. Filling with `0`
creates spurious extreme-poor households ($0/day) and inflates poverty rates.

**Checklist for any weighted statistic over survey microdata:**
- [ ] Check for null weights → raise error (never silently drop)
- [ ] Check for non-positive weights → raise error
- [ ] Check for null welfare/income → drop and log weight share lost
- [ ] Log the number of dropped observations and their weight share
- [ ] Validate sample size after dropping nulls

**polars null arithmetic to remember:**
- `.filter(expr)` — nulls propagate as `false` (excluded silently)
- `.sum()` — nulls are skipped silently
- `.fill_null(0)` — substitutes 0 for null (dangerous for welfare)
- `.drop_nulls()` — explicit drop; combine with logging

The `cg-skill-python-best-practices` skill (`workflows/logging-and-errors.md`
and `workflows/polars-patterns.md`) has been updated with these patterns.
The `python-anti-patterns.md` reference now includes `fill_null(0)` on
welfare columns as an explicit anti-pattern.

## Related

- `cg-skill-python-best-practices/workflows/logging-and-errors.md` §4 — canonical `compute_poverty_rate` implementation
- `cg-skill-python-best-practices/workflows/polars-patterns.md` — Schema Validation and Missing Values sections
- `cg-skill-python-best-practices/references/python-anti-patterns.md` — data manipulation anti-patterns table
