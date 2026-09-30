---
date: 2026-05-20
title: "Welfare column guard must check existence, NA, and positivity in order"
category: "data-quality"
language: "R"
tags: [welfare, GPID, data-validation, guard, NA-handling, poverty-measurement, FGT, stopifnot]
root-cause: "all(df$welfare > 0) silently returns NA (not FALSE) when the column contains NAs, and passes vacuously when the column is absent or renamed — both of which are common in GPID datasets."
severity: "P1"
---

# Three-Step Welfare Column Guard: Existence → NA → Positivity

## Problem

A welfare validation guard in a research EDA skill read:

```r
stopifnot(all(df$welfare > 0))
```

This has two silent failure modes:

1. **NA values silently bypass the guard**: `all(NA > 0)` returns `NA`, not `FALSE`.
   `stopifnot(NA)` throws "is not TRUE" — a cryptic error with no information about
   which observations have missing welfare.

2. **Absent or renamed column passes vacuously**: GPID welfare variables are context-specific
   (`welfare_ppp11`, `welfare_ppp17`, `pcexp`, `hhincome`, etc.). When the actual column
   is named `welfare_ppp17` and the guard checks `df$welfare`, R returns `NULL`.
   `all(NULL > 0)` evaluates to `TRUE` — the guard passes with zero checking done.

## Root Cause

`stopifnot(condition)` only fails for `FALSE`. `NA` and `NULL` have different semantics
that bypass the intended check or produce uninformative error messages.

GPID datasets rarely use the generic column name `welfare`. A hardcoded guard in a skill
document becomes a documentation lie on real datasets — it always passes, catches nothing,
and creates false confidence in data quality.

## Solution

Always use three sequential guards with explicit error messages:

```r
# Step 1: Column existence (adapt name to actual dataset variable)
stopifnot(
  "Column 'welfare' not found — adapt to actual name (welfare_ppp17, pcexp, hhincome, etc.)" =
    "welfare" %in% names(df)
)

# Step 2: No missing values
stopifnot(
  "welfare contains NA values" =
    !anyNA(df$welfare)
)

# Step 3: All positive (welfare < 0 is impossible; = 0 is suspicious)
stopifnot(
  "welfare contains non-positive values" =
    all(df$welfare > 0)
)
```

Skill documents should include the inline comment on Step 1 to make the column-name
variability visible to the reader.

## Prevention

- Never write `all(df$col > 0)` without preceding `!anyNA(df$col)` — treat them as an
  inseparable atomic pair.
- Never hardcode a GPID welfare column name in a guard without a comment acknowledging
  the variability: `# adapt to: welfare_ppp11, welfare_ppp17, pcexp, hhincome, etc.`
- Sequence matters: existence check → NA check → value check. A later check cannot
  be trusted if an earlier one was skipped.
- `"col" %in% names(df)` is cheaper and clearer than `!is.null(df$col)` — prefer it.

## Related

- `.github/skills/cr-skill-research-eda/SKILL.md` — welfare validation section (fixed 2026-05-20)
- `.cg-docs/solutions/data-quality/2026-03-17-null-welfare-silently-biases-poverty-rate.md` — consequence when NA welfare reaches FGT calculation
- `.cg-docs/solutions/data-quality/2026-03-18-zero-negative-welfare-inflates-fgt-beyond-1.md` — consequence when non-positive welfare reaches FGT calculation
- `.cg-docs/solutions/data-quality/2026-03-18-collapse-na-rm-global-option-welfare-risk.md` — related: collapse default `na.rm = FALSE` silently drops welfare observations
