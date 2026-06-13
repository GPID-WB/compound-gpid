---
date: 2026-05-15
title: "Common-word regex false positives in security and behavioral test assertions"
category: "testing-patterns"
language: "both"
tags: [pester, regex, false-positive, security-tests, -match, wiki, injection-scan, behavioral-testing]
root-cause: "Security and behavioral test assertions use common English words (Ignore, Override, Forget, nested) as -match patterns. These words appear throughout agent prose in unrelated contexts, so the test passes even when the specific behavior being tested is absent."
severity: "P3"
---

# Common-Word Regex False Positives in Security and Behavioral Test Assertions

## Problem

After the thorough review of the `@cg-wiki` feature, a verify pass found that
several new Pester tests passed trivially rather than meaningfully:

**Injection scan test** (P3.2 in verify review):
```powershell
It "flags SYSTEM: and Ignore/Override/Forget AI-redirect phrases (P1.4)" {
    ($content -match 'SYSTEM:|Ignore|Override|Forget') | Should -Be $true
}
```
`Ignore`, `Override`, and `Forget` are ordinary English words. Any agent file
containing "do not override user preferences" or "ignore this field when empty"
passes this test regardless of whether an injection scan rule exists.

**Nested marker test** (P3.3):
```powershell
It "documents that nested markers are forbidden" {
    ($content -match '[Nn]ested') | Should -Be $true
}
```
"Nested" appears in documentation for nested YAML, nested lists, nested JSON,
and dozens of other contexts. The test passes without verifying the marker-
nesting rule.

**Code-block marker test** (P3.5):
```powershell
It "specifies that cg:auto:end inside fenced code blocks is ignored" {
    ($content -match 'code block|fenced code|inline code') | Should -Be $true
}
```
"Code block" appears in any skill file that discusses markdown. The test cannot
distinguish "we document code blocks" from "we specify that `cg:auto:end`
inside code blocks is inert."

## Root Cause

When writing presence tests for behavioral rules, the pattern is typically
derived from the rule's most prominent keyword. For injection scans, that is
`Ignore` or `Override`. For marker rules, it is `nested`. These feel specific
in context but are general English words that appear throughout instruction prose.

The tests pass at creation time (the rule text is present and contains the word)
but become permanently green even if the rule is later edited, removed, or
replaced with different phrasing — because the word still appears elsewhere.

This is distinct from but related to the **alternation-masking** problem (see
Related): alternation (`a|b|c`) can hide that only one branch is being tested.
Here the problem is that all branches may be universally present.

## Solution

### Anchor to Context, Not to Common Words

For security/behavioral assertions, anchor the pattern to the specific behavior
being tested — not just a keyword from the rule text:

| Weak pattern | Strong pattern |
|---|---|
| `'Ignore\|Override\|Forget'` | `'SYSTEM:\|injection scan\|content flagged'` |
| `'[Nn]ested'` | `'[Nn]ested.*marker\|[Nn]ested.*cg:auto'` |
| `'code block\|fenced code'` | `'cg:auto:end.*code block\|fenced.*cg:auto'` |
| `'must NOT'` | `'must NOT.*\.github\|\.github.*must NOT'` |

### Co-condition Pattern

When testing that a security rule covers a specific class, combine the target
word with an anchor that can only be present near the security context:

```powershell
# Weak: any "Ignore" anywhere in the file
($content -match 'Ignore') | Should -Be $true

# Strong: "Ignore" co-occurring with injection-scan vocabulary
($content -match 'Injection scan|injection scan') | Should -Be $true
```

If the injection scan vocabulary itself could appear elsewhere, require that the
target phrase appears on the same line or paragraph:

```powershell
# Requires "SYSTEM:" explicitly mentioned in the scan rule context
($content -match 'SYSTEM:') | Should -Be $true
```

`SYSTEM:` is a domain-specific AI term unlikely to appear outside the injection
scan rule itself, making it a reliable anchor.

### Test Smell Checklist

Before committing a behavioral `-match` assertion, verify:

1. **Grep the file for the word** outside the target rule. If it appears more
   than once in an unrelated context, the pattern is too broad.
2. **Delete the rule text and re-run the test.** If the test still passes, the
   pattern is measuring the wrong thing.
3. **Use the most specific phrase from the rule**, not the most obvious word.
   `"injection scan"` is more specific than `"Ignore"`. `"cg:auto:end.*code block"`
   is more specific than `"code block"`.

## Prevention

When adding presence tests for new security or behavioral rules in `.md` files:

- Use 2-word phrases rather than single common words where possible
- For rules with domain-specific vocabulary (`cg:auto:end`, `SYSTEM:`, `injection`),
  prefer those terms over their plain-English synonyms
- Run the test against a file that has the common word but NOT the rule, to
  confirm it would fail correctly

## Related

- `.cg-docs/solutions/testing-patterns/2026-05-01-regex-alternation-masks-coverage-split-into-independent-assertions.md` — alternation (`a|b|c`) hides which branch is actually tested
- `.cg-docs/solutions/testing-patterns/2026-06-12-regex-arm-dead-from-inception-typo-passes-via-sibling.md` — alternation arm dead from inception due to spelling typo; test passes via sibling arm
- `.cg-docs/solutions/testing-patterns/2026-05-05-pester-regex-assert-string-message-false-positive-inlist.md` — false positives from list membership tests
- `.cg-docs/solutions/testing-patterns/2026-05-15-injection-scan-required-for-every-agent-that-reads-user-adjacent-files.md` — the injection scan rule these tests should verify
