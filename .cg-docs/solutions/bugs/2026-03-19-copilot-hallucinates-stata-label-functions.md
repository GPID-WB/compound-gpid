---
date: 2026-03-19
title: "Copilot hallucinates non-existent Stata functions for variable label checks"
category: "bugs"
language: "Stata"
tags: [stata, copilot-hallucination, labelled, variable-labels, validation, assert, regexm, PPP]
root-cause: "Copilot generates calls to labelled() and similar non-existent Stata functions when writing validation or assertion code for variable metadata."
severity: "P1"
---

# Copilot Hallucinates Non-Existent Stata Functions for Variable Label Checks

## Problem

Copilot generates calls to functions that do not exist in Stata when writing
validation or assertion code that inspects variable labels, value labels, or
variable metadata:

```stata
// Copilot-generated — labelled() does not exist in Stata
assert labelled(welfare_ppp, "2017 PPP")

// Also seen
assert haslabel(region, "urban")
assert varlabel(income) == "Monthly per-capita income"
```

These statements produce an immediate error: `unknown function labelled()`.
The analysis halts, but only if the assertion is actually reached — if guarded
by `capture`, the error is silently swallowed and validation is bypassed.

## Root Cause

Copilot's training data conflates Stata with R (where `haven::is.labelled()` and
`labelled::val_labels()` exist), Python (where `df["col"].attrs["label"]` is a
pattern), and general pseudo-code conventions. Stata has no built-in function
for inspecting label strings at run time. Label access in Stata uses the
extended macro function syntax, which is syntax rather than a function call.

## Solution

Use Stata's extended macro functions to retrieve labels, then assert on the
retrieved string:

```stata
// RIGHT — retrieve variable label into a local, then test it
local welfare_lbl : variable label welfare_ppp
assert regexm("`welfare_lbl'", "PPP"), ///
    "welfare_ppp label does not mention PPP: `welfare_lbl'"

// RIGHT — check value label exists and contains the expected string
local region_lbl : value label region
assert "`region_lbl'" != "", "region has no value label attached"

// RIGHT — retrieve a specific value label entry
local lbl_1 : label (`region_lbl') 1
assert regexm("`lbl_1'", "urban"), ///
    "Value label 1 does not match 'urban': `lbl_1'"

// RIGHT — verify variable label matches exactly
local income_lbl : variable label income
assert "`income_lbl'" == "Monthly per-capita income (LCU)", ///
    "income label mismatch: `income_lbl'"
```

### Extended macro function reference for label access

| Goal | Correct Syntax |
|------|---------------|
| Get variable label | `` local lbl : variable label varname `` |
| Get value label name attached to var | `` local lblname : value label varname `` |
| Get text for a specific value | `` local txt : label (lblname) value `` |
| Get variable type | `` local type : type varname `` |
| Get variable format | `` local fmt : format varname `` |

## Prevention

- There are no Stata built-in functions named `labelled()`, `haslabel()`,
  `varlabel()`, `val_labels()`, or `has_value_label()`.
- All variable and value label access uses the extended macro function syntax:
  `` local result : <extended macro function> ``.
- When Copilot writes `assert function_name(variable, ...)` for metadata
  validation, the function almost certainly does not exist — replace with the
  extended macro pattern.
- Add to code review checklist: scan for `assert <word>(` patterns in Stata
  code and verify each function exists.

## Related

- [Fragile matrix indexing for regression results](./2026-03-19-fragile-matrix-indexing-regression-results-stata.md) — related Copilot correctness error
- `cg-skill-stata-core`: Macro System workflow — extended macro functions
- `cg-skill-stata-research`: Research Anti-Patterns — label validation pattern
