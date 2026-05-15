---
date: 2026-05-01
title: "Regex alternation in Pester -match can mask coverage when first branch is always true"
category: "testing-patterns"
language: "both"
tags: [pester, powershell, regex, alternation, coverage, always-true, -match, prompt-testing, cg-setup]
root-cause: "A test using `(?i)Ignore.*Override|Override.*Forget` claimed to verify three injection trigger words but only reliably verified two — the first alternation branch always matched, so the second branch (and the word 'Forget') was never required to be present"
severity: "P3"
fix-confirmed: "yes"
reviewed-in: ".cg-docs/reviews/2026-05-01-smart-setup-phase2-revised-verify-review-2.md"
---

# Regex Alternation in Pester `-match` Can Mask Coverage When First Branch Is Always True

## Problem

A test was written to verify that the scanner injection sanitization block in
`cg-setup.prompt.md` named all three trigger words: "Ignore", "Override", "Forget".

```powershell
# ❌ Flawed — "Forget" is never independently required
It "names specific injection trigger words (Ignore, Override, Forget)" {
    ($content -match '(?i)Ignore.*Override|Override.*Forget') | Should Be $true
}
```

The source text at line 62 is:
> `sentences beginning with "Ignore", "Override", or "Forget"`

The regex `Ignore.*Override` matches this line (both words appear in order),
so the first alternation branch is satisfied. PowerShell's `-match` short-circuits
on the first match — `Override.*Forget` is never evaluated.

If "Forget" were removed from the source text, the test would still pass.
Despite the `It` name claiming all three words are verified, only two are
effectively tested.

## Root Cause

Regex alternation (`A|B`) in `-match` evaluates left to right and short-circuits
on first success. When `A` matches any input that also satisfies the test intent,
`B` is never required. If the test intent is "all of these words must be present,"
alternation expresses "at least one of these words must be present" — the wrong
semantics.

This is a subtle cousin of the unescaped `|` bug (where `'| skip'` becomes
`(empty string) | " skip"` and always matches). Here the regex syntax is correct,
but the logical coverage is still incomplete.

## Solution

When an `It` block claims to verify the presence of multiple independent words
or phrases, use **separate assertions** rather than a single alternating regex:

```powershell
# ✓ Correct — each word independently required
It "names specific injection trigger words (Ignore, Override, Forget)" {
    ($content -match '(?i)\bIgnore\b')   | Should Be $true
    ($content -match '(?i)\bOverride\b') | Should Be $true
    ($content -match '(?i)\bForget\b')   | Should Be $true
}
```

Each assertion fails independently if its word is removed. The `\b` word-boundary
anchors prevent false positives (e.g., "Forgotten" matching `\bForget\b` is debatable
— use based on context).

### When alternation IS correct

Use `A|B` when the test truly means "at least one of A or B must be present" —
for example, checking a fallback clause:

```powershell
# ✓ Correct use of alternation: either phrasing is valid
($content -match 'carry forward.*cg-schema-version|cg-schema-version.*unchanged') | Should Be $true
```

Here either phrase proves the same behavior. The intent is "one of two phrasings
of the same rule." This is correct alternation.

### Alternation vs. independent assertions — decision rule

| Intent | Pattern |
|--------|---------|
| "All N things must be present" | N separate `Should Be $true` assertions |
| "At least one of N phrasings of the same thing must be present" | Single alternating regex |
| "Either of two valid forms of the same fix" | Single alternating regex |
| "N independent requirements" | N separate assertions |

## Prevention

When writing multi-word presence tests, ask: "If word X were deleted, would this
test fail?" If the answer is "no" for any word in the `It` name, split into
separate assertions.

**Code review heuristic for Pester**: Any `-match` regex containing `|` that is
intended to verify multiple independent items is a candidate for false safety.
Check whether the first branch alone would satisfy the assertion.

## Related

- `.cg-docs/solutions/testing-patterns/2026-04-07-pester-test-quality-patterns.md` — Pattern 2 (anchored regex): covers escaping `.` and `|` in regex, but not alternation coverage semantics
- `.cg-docs/solutions/testing-patterns/2026-04-15-pester-dotall-flag-required-for-multiline-regex.md` — regex flags in Pester
- Original P1.1 fix (from `2026-05-01-smart-setup-phase2-revised-review.md`): unescaped `|` in `'| skip'` — structurally similar but different failure mode (always true vs. never true)
- `2026-05-05-stale-alternation-after-prompt-refactoring.md` — variant where alternation was correct at creation time but became stale after prompt text changed (first branch becomes permanently non-matching)
- `.cg-docs/solutions/testing-patterns/2026-05-15-common-word-regex-false-positive-in-security-assertions.md` — related pitfall: single common-word patterns (not alternation) pass trivially because the word appears in unrelated prose
