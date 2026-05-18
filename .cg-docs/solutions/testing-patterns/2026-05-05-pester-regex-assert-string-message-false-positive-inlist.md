---
date: 2026-05-05
title: "Pester regex for assert-with-string-message false-positives on inlist/inrange"
category: "testing-patterns"
language: "both"
tags: [pester, regex, powershell, stata, assert, inlist, inrange, false-positive, guard-test]
root-cause: "Character class [^`\\r\\n] does not exclude commas inside parentheses; inlist/inrange calls match the pattern"
severity: "P2"
---

# Pester Regex for `assert`-With-String-Message False-Positives on `inlist`/`inrange`

## Problem

A Pester guard test intended to detect invalid Stata `assert expr, "message"` syntax
used the regex `assert\b[^\`\r\n]+,\s*"`. This correctly rejects:

```stata
assert dup_flag == 0, "duplicates found"   // ← invalid Stata syntax
```

But it also incorrectly matched valid Stata:

```stata
assert inlist(survey_type, "IHS", "HIES", "LSMS", "SES")
```

Because the regex sees `assert inlist(survey_type,` followed by a space and `"` — the
comma is **inside parentheses** and belongs to `inlist()`, not to the `assert` option syntax.
The test returned `True` (match found) when it should have returned `False` (no bad assert).

## Root Cause

The character class `[^\`\r\n]` only excludes backticks and line breaks. It does not
account for parentheses. In Stata, `assert` with a function call argument
(`inlist`, `inrange`, `reldif`, etc.) can have a comma inside the function without
constituting the `assert , "message"` syntax error. The regex cannot distinguish
between a comma as an `assert` option separator and a comma as a function argument.

## Solution

Exclude parentheses from the character class: `[^()\r\n]`. This prevents the
regex from crossing function call boundaries — if a comma is preceded by an open paren
(i.e., it is inside a function call), the pattern fails to match.

```powershell
# Wrong — matches assert inlist(survey_type, "IHS", ...)
($dv -match 'assert\b[^`\r\n]+,\s*"') | Should Be $false

# Correct — excludes commas inside parentheses
($dv -match 'assert\b[^()\r\n]+,\s*"') | Should Be $false
```

After the fix, `assert inlist(survey_type, "IHS", "HIES")` correctly does not match,
while `assert dup_flag == 0, "message"` (which has no open paren before the comma)
still matches.

## Limitations

This approach handles one level of nesting. A pathological case like:

```stata
assert cond(dup_flag, 0, 1) == 0, "found duplicates"
```

…would not be caught because `(` appears before the option comma. In practice,
this pattern is not used in Stata code, and the real-world risk is negligible.

## Prevention

When writing Pester regex guards for Stata syntax errors:
1. Always test the regex against both the **target bad pattern** and **common
   legitimate patterns** (especially `inlist`, `inrange`, `reldif`, `cond`) before
   committing the test.
2. Use `[^()\r\n]` instead of `[^\`\r\n]` when the match must not cross function call
   argument boundaries.
3. After writing a new regex guard, run the targeted test file immediately to
   confirm zero false positives on the current codebase.

## Related

- `.cg-docs/solutions/testing-patterns/2026-04-15-pester-dotall-flag-required-for-multiline-regex.md` — multiline regex behaviour in Pester
- `.cg-docs/solutions/testing-patterns/2026-05-01-regex-alternation-masks-coverage-split-into-independent-assertions.md` — related regex pitfall in test assertions
- `tests/prompt-tools.Tests.ps1` — the P0.1 guard test was affected
- `.cg-docs/solutions/testing-patterns/2026-05-15-common-word-regex-false-positive-in-security-assertions.md` — related: common English words in security assertions pass trivially regardless of whether the specific rule is present
