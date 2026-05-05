---
date: 2026-05-05
title: "duplicates tag clears r(N) — insert count before conditional display"
category: "data-quality"
language: "Stata"
tags: [stata, duplicates, stored-results, r-class, data-validation, assertion]
root-cause: "duplicates tag only stores r(unique_tag), not r(N); prior r(N) is cleared"
severity: "P2"
---

# `duplicates tag` Clears `r(N)` — Insert `count` Before Conditional Display

## Problem

The following pattern produces a silently-suppressed diagnostic: `display as error` never
fires even when duplicates exist, because `if r(N) > 0` evaluates to false.

```stata
duplicates tag country_code year, gen(dup_flag)
if r(N) > 0 display as error "FAIL: dataset is not uniquely identified"
assert dup_flag == 0    // ← this still catches the error, but silently
```

The `assert` line does correctly fail when duplicates exist, but the informative error
message is always suppressed — making failures harder to diagnose.

## Root Cause

`duplicates tag` is an r-class command that stores only `r(unique_tag)` in `r()`.
It **clears** any prior `r(N)` (e.g., from a preceding `duplicates report`). Immediately
after `duplicates tag`, `r(N)` is undefined — Stata evaluates it as `.` (missing),
and `if . > 0` is false. The `display as error` line is never reached.

This is distinct from `duplicates report`, which does set `r(N)` to the number of
duplicate observations.

## Solution

Insert `count if dup_flag > 0` between `duplicates tag` and the conditional display.
`count` is a reliable r-class command that always sets `r(N)`:

```stata
duplicates tag country_code year, gen(dup_flag)
count if dup_flag > 0    // sets r(N) — duplicates tag only sets r(unique_tag)
if r(N) > 0 display as error "FAIL: `r(N)' observations have duplicates on country_code + year"
assert dup_flag == 0
```

## Prevention

- After any `duplicates tag`, never rely on `r(N)` being set. Always use `count if`
  to explicitly set `r(N)` before a conditional display or assertion.
- Prefer `isid country_code year` for hard uniqueness assertions — it is cleaner and
  has no diagnostic vs. r-class ambiguity. Reserve `duplicates tag` + `count` for
  contexts where you need to inspect or log which observations are duplicated.
- When writing test-guard Pester assertions, note that the hard `assert` line still
  protects correctness — only the human-readable diagnostic is lost.

## Related

- `.cg-docs/solutions/data-quality/2026-03-17-null-welfare-silently-biases-poverty-rate.md` — another silent-failure pattern in Stata validation code
- `cg-skill-stata-testing/references/data-validation.md` — fixed to use `count if dup_flag > 0`
