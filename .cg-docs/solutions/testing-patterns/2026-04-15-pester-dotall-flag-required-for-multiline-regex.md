---
date: 2026-04-15
title: "Pester regex without (?s) gives silent false-negative on multi-line prompt content"
category: "testing-patterns"
language: "both"
tags: [pester, regex, powershell, dotall, multiline, prompt-testing, silent-failure]
root-cause: "PowerShell -match uses .NET regex where . does not cross \\n by default; multi-hop .* patterns silently fail when the target text spans a line break in the file"
severity: "P2"
fix-confirmed: "yes"
reviewed-in: ".cg-docs/reviews/2026-04-15-per-step-test-failure-handling-standard-review.md"
---

# Pester Regex Without `(?s)` Gives Silent False-Negative on Multi-Line Prompt Content

## Problem

Several Pester tests for `cg-work.prompt.md` used `.*` to span across a
prompt phrase that happened to wrap across a line break:

```powershell
# BROKEN — first alternative never fires
It "requires full-suite re-run … to catch regressions" {
    ($content -match 'full test suite.*catch regressions|regressions introduced by the fix') |
        Should Be $true
}

It "double-notification skip-guard exists" {
    ($content -match 'already notified.*skip this surface|avoid\s+double.notification') |
        Should Be $true
}

It "separates test failures from @cg-fix-problems" {
    ($content -match 'Do NOT dispatch.*@cg-fix-problems.*test fail') |
        Should Be $true
}
```

All three tests **pass** — but only via their fallback alternatives. The
primary alternatives die silently because `.*` in `.NET` regex does not
cross `\n`. The consequence: when the fallback phrase is later
renamed/rephrased, the test still passes (false negative). The primary
requirement goes undetected.

**Discovered as P2.6, P2.7, P2.8** in the standard review of the
per-step test failure handling feature (2026-04-15).

## Root Cause

In .NET's regex engine (used by PowerShell `-match`), `.` matches any
character **except** `\n` by default. Multi-part patterns like:

```
'first phrase.*second phrase'
```

silently fail when `first phrase` appears on line N and `second phrase`
appears on line N+1 of the file. Because tests are typically phrased as
alternations with a fallback (`A.*B|phrase_from_B_only`), the test still
passes via the fallback — masking the broken primary.

There is no warning. The test output shows green.

## Solution

Add `(?s)` (Singleline / Dotall mode) at the start of any pattern that
needs `.` to cross line breaks:

```powershell
# FIXED
It "requires full-suite re-run … to catch regressions" {
    ($content -match '(?s)full test suite.*catch regressions|regressions introduced by the fix') |
        Should Be $true
}

It "double-notification skip-guard exists" {
    ($content -match '(?s)already notified.*skip this surface|avoid\s+double-notification') |
        Should Be $true
}

It "separates test failures from @cg-fix-problems" {
    ($content -match '(?s)Do NOT dispatch.*@cg-fix-problems.*test fail') |
        Should Be $true
}
```

`(?s)` enables Singleline mode where `.` matches `\n` as well — the whole
`Get-Content -Raw` string is treated as one flat sequence of characters.

### Bonus fix in P2.7

The original `double.notification` used `.` as a **wildcard** (matches any
character) rather than a **literal hyphen**. Use `double-notification` with
an explicit literal hyphen to avoid false positives like `doubleXnotification`.

## Prevention

**Rule**: Any Pester test that reads a prompt file with `Get-Content -Raw`
and uses `-match` with `.*` should use `(?s)` if the matched phrase could
span a line break.

**Checklist when authoring prompt content tests**:
- [ ] Does the pattern use `.*`?
- [ ] Could the two ends of the pattern appear on different lines in the file?
- [ ] If yes → add `(?s)` at the start of the pattern.
- [ ] Does the pattern include `.` to match a literal punctuation character?
  → Use the literal character (e.g., `-` instead of `.`) to avoid wildcards.

**Pattern to audit for in existing tests**:
```powershell
# Check for multi-hop .* without (?s)
Get-Content tests\*.Tests.ps1 -Raw |
    Select-String '\-match\s+''[^(][^?][^s].*\.\*.*\.\*' -AllMatches
```

## Related

- `.cg-docs/solutions/testing-patterns/2026-03-30-prompt-pipeline-contract-testing.md`
  — general strategy for testing prompt content contracts
- `.cg-docs/solutions/testing-patterns/2026-04-15-pester-verbose-output-floods-context-long-session.md`
  — another class of silent Pester test failure (context overflow)
- `.cg-docs/solutions/bugs/2026-04-15-self-defeating-guardrail-exception-in-llm-prompts.md`
  — from the same review; adversarial prompt logic patterns
- `.cg-docs/solutions/testing-patterns/2026-05-06-pester-caret-anchor-requires-multiline-flag.md`
  — the companion `(?m)` case: `^`/`$` anchors silently only match string start/end without `(?m)`
- `.cg-docs/solutions/testing-patterns/2026-05-07-ps51-python-c-heredoc-unreliable-use-temp-file.md`
  — related PS 5.1 gotcha: here-string + `python -c` is unreliable due to interpolation and CRLF; write a temp `.py` file instead
