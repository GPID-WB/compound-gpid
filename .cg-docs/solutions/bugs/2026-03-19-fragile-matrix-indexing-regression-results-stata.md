---
date: 2026-03-19
title: "Fragile matrix indexing for regression results in Stata"
category: "bugs"
language: "Stata"
tags: [stata, regression, coefficients, e(b), matrix-indexing, poverty, FGT, survey]
root-cause: "Copilot extracts regression coefficients via positional matrix indexing (e(b)[1,2]) instead of named access (_b[varname]). Position changes silently when model specification changes."
severity: "P1"
---

# Fragile Matrix Indexing for Regression Results in Stata

## Problem

Code that extracts regression coefficients or standard errors using positional
matrix indexing silently produces wrong results if the model specification changes
(different variable order, additional controls, dropped observations):

```stata
// Produced by Copilot — silently wrong if variable order changes
svy: logit poor i.poor ln_welfare
local hr = e(b)[1,2]            // position 2 today, but could be any position tomorrow
local se = sqrt(e(V)[2,2])
```

In poverty analysis this manifests as extracting the wrong coefficient from a
welfare regression — the estimated headcount ratio or standard error will be
numerically plausible but correspond to the wrong regressor. There is no error
message.

## Root Cause

Stata's `e(b)` and `e(V)` are row/column matrices whose positional indices
correspond to the order variables appear in the model. Copilot generates
positional indexing because it mirrors the `[row, col]` matrix access pattern
common in other languages. In Stata, position is model-dependent and changes
whenever:
- A covariate is added or removed
- Factor variable base levels change
- Variables are renamed or reordered in the varlist

## Solution

Always extract coefficients by name using Stata's coefficient reference syntax:

```stata
// RIGHT — named access, robust to specification changes
svy: logit poor i.poor ln_welfare
local hr = _b[1.poor]           // factor variable: 1.varname
local se = _se[1.poor]          // standard error: _se[varname]

// For continuous variables
local coef = _b[ln_welfare]
local se   = _se[ln_welfare]

// For interaction terms
local coef = _b[1.treatment#c.year]

// Saved immediately after estimation (before the next e-class command wipes e(b))
local hr = _b[1.poor]
local se = _se[1.poor]
```

For FGT index extraction from `svy: mean`:

```stata
// RIGHT — named result access
svy: mean poor [pw=weight], over(year)
local fgt0 = _b[1bn.year:poor]   // e.g., 2019 base
local se   = _se[1bn.year:poor]

// Or scalar storage for readability
matrix b = e(b)
local fgt0 = b[1, colnumb(b, "poor")]   // colnumb() is name-safe
```

## Prevention

- Never use `e(b)[1,N]` or `e(V)[N,N]` with hardcoded integers in production code.
- Always use `_b[varname]`, `_se[varname]`, or `lincom` for linear combinations.
- Save stored results to locals **immediately** after estimation — any subsequent
  e-class command (including `quietly reghdfe` in a loop) wipes `e(b)`.
- Add `assert !missing(_b[1.poor])` after extraction to catch dropped variables.

## Related

- [Stata survey SE singleton PSU divide-by-zero](../data-quality/2026-03-18-survey-mean-se-singleton-psu-divide-by-zero.md) — related SE extraction issue
- `cg-skill-stata-core`: Program Scoping workflow — stored results lifetime
- `cg-skill-stata-research`: Survey & Poverty workflow — FGT extraction patterns
