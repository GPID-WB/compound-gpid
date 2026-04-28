---
date: 2026-04-28
title: "Prompt guard conditions added without Pester regression tests"
category: "testing-patterns"
language: "both"
tags: [pester, powershell, prompt-testing, guard-conditions, regression, coverage, silent-failure, cg-release]
root-cause: "Multiple guard conditions (shallow-clone fallback, --since future-date warn, window-start >= today warn, 500-line limit, release-result.txt catch-all) were added to cg-release.prompt.md across fix-triage cycles without adding matching Pester text-presence assertions — leaving all guards silently unverified"
severity: "P2"
fix-confirmed: "yes"
reviewed-in: ".cg-docs/reviews/2026-04-28-cg-release-scan-optimization-verify-review.md"
---

# Prompt Guard Conditions Added Without Pester Regression Tests

## Problem

Five distinct guard conditions were added to `cg-release.prompt.md` during the
P0–P3 fix-triage cycle for the cg-release scan optimization feature:

| Guard | Prompt location | Symptom if missing |
|---|---|---|
| `--since` ISO date after today → warn + fallback | Arguments section | Silent bad date accepted |
| Shallow-clone `git log -1` empty → fallback | Step 1b | No fallback on sparse checkout |
| `window-start >= today` → zero-context warning | Step 1c | User confused by empty scan |
| Commit log > 500 lines → context-truncation warning | Step 1d | Silent truncation, incomplete notes |
| `release-result.txt` absent or unrecognized → catch-all | Step 5 | Silent failure, no user guidance |

All five were added to the prompt text, but no Pester tests were written
alongside them. The first `/cg-review mode:verify` pass found all five as P2
findings (P2.1–P2.5) — they could each have silently regressed.

A sixth gap (P2.6) was also surfaced: the `cg-release-scanner.agent.md` empty-log
path (`Highest impact: none — no commits found`) had no test.

## Root Cause

When extending a prompt with a new **guard condition**, the mental model is
"writing instructions for the AI", not "adding a branch that needs a test."
Unlike code `if`-statements where missing coverage is tool-detectable, prompt
guards are plain text. Nothing signals that a guard is untested — it just
silently disappears if the text is removed or renamed.

The existing `tests/prompt-tools.Tests.ps1` pattern (text-presence assertions
via `-match`) is precisely designed for this, but the habit of "add guard →
add test" wasn't applied during the fix-triage cycles. All guards were added
and verified to work by human inspection, but no regression anchors were
planted.

## Solution

Add a `($content -match 'guard-text') | Should Be $true` assertion to the
relevant `Describe` block immediately when each guard is added.

**Pattern** (Pester 3.4 style):
```powershell
Describe "cg-release.prompt.md - window guards" {
    BeforeAll {
        $file = Join-Path $PSScriptRoot '..' 'cg-release.prompt.md'
        $content = Get-Content $file -Raw -Encoding UTF8
    }

    It "warns when --since ISO date is after today" {
        ($content -match 'after today.*fall back|parsed.*after today') | Should Be $true
    }
    It "warns on shallow clone and falls back to window-days formula" {
        ($content -match 'shallow clone') | Should Be $true
    }
    It "warns when window-start is on or after today" {
        ($content -match 'window-start.*today|All.*cg-docs.*entries will be excluded') | Should Be $true
    }
    It "warns when commit log exceeds 500 lines" {
        ($content -match '500 lines|exceeds 500') | Should Be $true
    }
    It "catch-all when release-result.txt is absent or unrecognized" {
        ($content -match 'may have failed|release-result\.txt.*absent|neither.*CREATED') | Should Be $true
    }
}
```

**For agent empty-log paths** (in a separate `Describe` for the agent file):
```powershell
It "documents Highest impact: none for empty commit log" {
    ($agentContent -match 'Highest impact: none') | Should Be $true
}
```

## Prevention

**Rule**: Every guard/fallback/warning added to a prompt file must be followed
immediately by a `Should Be $true` text-presence assertion in the
corresponding Pester test file.

Checklist when adding a guard to any `.prompt.md` or `.agent.md`:
1. Identify the unique guard phrase (e.g., `shallow clone`, `500 lines`, `after today`)
2. Add `It "..." { ($content -match 'unique-phrase') | Should Be $true }` to
   the relevant `Describe` block in `tests/prompt-tools.Tests.ps1`
3. Run the test immediately to verify the assertion passes

If there is no existing `Describe` block for the file, create one following the
script-scoped `BeforeAll` pattern from the existing test file.

## Related

- [New Validation Branch Added Without Test](./2026-04-15-new-validation-branch-requires-dedicated-test.md) — same root cause in code; this solution covers the prompt-text equivalent
- [Prompt Pipeline Contract Testing](./2026-03-30-prompt-pipeline-contract-testing.md) — broader contract testing patterns for prompt files
- [Prompt Step Silent Skip Antipattern](./2026-04-15-prompt-step-silent-skip-antipattern-fallback-required.md) — related: guard conditions that silently skip instead of failing loudly
