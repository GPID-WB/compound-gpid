---
date: 2026-05-05
title: "Regex alternation branches become stale dead code after prompt refactoring"
category: "testing-patterns"
language: "both"
tags: [pester, powershell, regex, alternation, dead-code, prompt-refactoring, stale-pattern, -match, coverage]
root-cause: "After P2.3 replaced hardcoded main/master detection with dynamic git symbolic-ref, the first branch of an OR-pattern test (not.*main.*master.*skip silently) became permanently non-matching; the test still passed via the second branch, hiding the dead code"
severity: "P3"
reviewed-in: ".cg-docs/reviews/2026-05-05-branch-creation-from-plan-verify-review.md"
---

# Regex Alternation Branches Become Stale Dead Code After Prompt Refactoring

## Problem

A test was written in two-branch alternation form to cover two possible phrasings
of the "skip silently" guard in `cg-plan.prompt.md`:

```powershell
It "Branch Offer skips silently when already on a feature branch" {
    ($content -match 'not.*main.*master.*skip silently|already on a.*branch.*skip silently') | Should Be $true
}
```

The first branch (`not.*main.*master.*skip silently`) was written for the original
prompt text, which checked the current branch against the literal names `main` or
`master`. After P2.3 replaced this with dynamic default-branch detection, the
prompt text changed to:

> "If the current branch is not the default branch (i.e., already on a feature
> branch): skip silently."

The words `main` and `master` no longer appear in this clause. The first alternation
branch became permanently non-matching. The test continued to pass via the second
branch (`already on a.*branch.*skip silently`), which still matched.

The consequence: if the second branch were also removed from the prompt (through a
future refactor), the test would still pass momentarily via the stale first branch
if `main` or `master` appeared anywhere else in the file.

## Root Cause

This is distinct from the **always-true first branch** pattern
(see `2026-05-01-regex-alternation-masks-coverage-split-into-independent-assertions.md`).
Here the first branch was correct when written, then became permanently false after
a prompt text change. The alternation was appropriate at creation time — it was
a test that tolerated two valid phrasings. But prompt refactoring silently killed
one branch without invalidating the test.

**The general form**: `A|B` tests that cover alternate phrasings become stale when
the prompt settles on one phrasing permanently. The surviving branch is the only
live coverage; the dead branch creates a false sense of redundancy that actually
masks the absence of the original text.

## How to Detect

Stale alternation branches are caught in verify passes: when a prompt is refactored,
re-check all tests that use `|` alternation and confirm both branches still match
the current text. A branch that no longer matches any substring of the file is dead.

Manual check (PowerShell):

```powershell
$content = Get-Content '.github\prompts\cg-plan.prompt.md' -Raw
# Test each branch independently
$content -match 'not.*main.*master.*skip silently'  # should be $true if live
$content -match 'already on a.*branch.*skip silently'  # should be $true if live
```

## Solution

When a prompt settles on a single phrasing, drop the stale alternation branch
and use a single precise assertion:

```powershell
# ❌ After refactoring — first branch is dead
($content -match 'not.*main.*master.*skip silently|already on a.*branch.*skip silently')

# ✓ After fixing — single live assertion
($content -match 'already on a.*branch.*skip silently') | Should Be $true
```

## Prevention

### Rule: Alternation Tests Are Temporary Tolerance Patterns

OR-pattern assertions (`A|B`) in prompt tests are appropriate when a behavior
has two valid textual implementations. They should be treated as **temporary**:
once the prompt stabilizes on one phrasing, remove the other branch.

Add a comment at creation time marking the intent:

```powershell
# NOTE: two valid phrasings — simplify to one assertion once prompt settles
($content -match 'phrasing-A|phrasing-B') | Should Be $true
```

### Rule: Verify Passes Must Audit Alternation Branches

After any prompt refactoring pass (especially one that changes guard language),
search the test file for `|` within `-match` expressions and verify each branch
independently against the updated prompt text.

### Rule: Independent Assertions Are Safer When Both Must Match

If the intent is "both A and B must be present," use two separate assertions
rather than alternation:

```powershell
# ❌ OR — "at least one of these"
($content -match 'A|B') | Should Be $true

# ✓ AND — "both of these"
($content -match 'A') | Should Be $true
($content -match 'B') | Should Be $true
```

## Related

- [2026-05-01-regex-alternation-masks-coverage-split-into-independent-assertions.md](2026-05-01-regex-alternation-masks-coverage-split-into-independent-assertions.md) — always-true first branch variant (root cause differs: structural vs. became-stale)
- [2026-04-15-pester-dotall-flag-required-for-multiline-regex.md](2026-04-15-pester-dotall-flag-required-for-multiline-regex.md) — related regex correctness issue in Pester
- [2026-06-12-regex-arm-dead-from-inception-typo-passes-via-sibling.md](2026-06-12-regex-arm-dead-from-inception-typo-passes-via-sibling.md) — third variant: arm dead from inception due to typo; distinct from stale-after-refactoring
