---
date: 2026-04-17
title: "Exact count assertions prevent silent regression when test name states a specific count"
category: "testing-patterns"
language: "both"
tags: [pester, testing, assertion, regression, count, begreatertan, shouldbe, ps5.1, test-quality]
root-cause: "A test named 'all three X fall back' that asserts BeGreaterThan 1 (not Be 3) passes if only 2 fields fall back, silently hiding a regression where the third field stopped working"
severity: "P3"
---

# Exact Count Assertions Prevent Silent Regression When Test Name States a Specific Count

## Problem

A test in `helpers.Tests.ps1` was named:

> "all three unconfigured fields (project-type, language, review-depth) fall back"

But the assertion used a range:

```powershell
It "all three unconfigured fields (project-type, language, review-depth) fall back" {
    ([regex]::Matches($result, [regex]::Escape('<not configured>')).Count) | Should BeGreaterThan 1
}
```

If one of the three fields silently stopped falling back to `<not configured>` (due
to a regex change, a new default value, or a guard bug), the match count would drop
from 3 to 2. The test would still **pass** because `2 BeGreaterThan 1` is `$true`.

The regression would be invisible until a user encountered malformed
`copilot-instructions.md` output in production.

## Root Cause

The assertion was written defensively — "at least 2 is good enough if we have 3."
This is a common pattern when the exact count feels fragile (e.g., if the template
might gain more `<not configured>` fields in the future). However, the approach
trades correctness for perceived flexibility.

The test name and the assertion are in direct conflict: the name documents a
specific invariant (exactly 3), but the assertion verifies a weaker property (at
least 2). The weaker assertion cannot enforce the stated invariant.

## Solution

When the test name states a specific count, the assertion must match:

```powershell
It "all three unconfigured fields (project-type, language, review-depth) fall back" {
    ([regex]::Matches($result, [regex]::Escape('<not configured>')).Count) | Should Be 3
}
```

If the count is legitimately variable (e.g., the template may grow), either:
1. Update the test name to reflect the actual invariant: `"all unconfigured fields fall back"` + `BeGreaterThan 0`
2. Or enumerate the fields individually with one `It` per field — this gives a precise failure message pinpointing which field broke

## Prevention

**Code review heuristic**: when a test name contains a number or a word like "all",
"both", "three", "each", verify that the assertion is exact (not `BeGreaterThan` or
`BeGreaterOrEqualTo`). A mismatch between the name and the assertion is a test
quality bug.

**Pattern to follow** for exact field coverage:

```powershell
# Option 1 — explicit per-field tests (best for diagnostics)
It "language falls back to <not configured>" {
    $result | Should Match [regex]::Escape('<not configured>')
}
It "project-type falls back to <not configured>" {
    $result | Should Match [regex]::Escape('<not configured>')
}
It "review-depth falls back to <not configured>" {
    $result | Should Match [regex]::Escape('<not configured>')
}

# Option 2 — exact count (compact, acceptable if field list is stable)
It "all three unconfigured fields fall back" {
    ([regex]::Matches($result, [regex]::Escape('<not configured>')).Count) | Should Be 3
}
```

Avoid:
```powershell
# ❌ Name says "three", assertion says "more than one" — silent regression risk
It "all three unconfigured fields fall back" {
    $count | Should BeGreaterThan 1
}
```

## Related

- [2026-04-07 — Pester test quality patterns](2026-04-07-pester-test-quality-patterns.md) — broader test quality reference for this project
- `tests/helpers.Tests.ps1` — where this fix was applied
