---
date: 2026-06-12
title: "Regex arm silently dead from inception due to typo — test passes via sibling arm"
category: "testing-patterns"
language: "both"
tags: [pester, powershell, regex, alternation, dead-arm, typo, spelling, -match, prompt-testing, false-positive]
root-cause: "A regex alternation arm contained a misspelling ('fall back' instead of 'falls back'), making it never match the prompt text it was written for. The test still passed because a sibling arm matched. The dead arm was invisible at creation and review time."
severity: "P3"
fix-confirmed: "yes"
reviewed-in: ".cg-docs/reviews/2026-06-12-goal-driven-execution-review.md"
---

# Regex Arm Silently Dead from Inception Due to Typo — Test Passes via Sibling Arm

## Problem

A journey-fixture test was written to verify that `/cg-work` warns when an
invalid `deviate:` override is provided and falls back to the plan's policy:

```powershell
# ❌ Third arm has typo — never matches prompt text
It "cg-work invalid deviate: override warns and uses plan policy" {
    ($workContent -match 'warn.*plan policy|invalid.*deviate.*override|fall back.*plan') | Should -Be $true
}
```

The prompt text being tested (from `cg-work.prompt.md` Step 0 flag parsing):
> `invalid warns, falls back to plan policy`

At first glance, `fall back.*plan` appears to match. However:
- The prompt text contains **"falls back"** (with "s")
- The regex arm requires **"fall back"** (without "s")

PowerShell's `-match` is case-insensitive but not spelling-tolerant. The third
arm **never matched**. The second arm also never matched (the prompt does not
contain "override" in this context). The test passed entirely via the first arm
`warn.*plan policy`.

The test claimed to exercise a specific fallback behavior but only exercised the
"warns" + "plan policy" co-occurrence. If someone rewrote the prompt to say
"alerts user; reverts to stored plan policy", the test would fail — but for the
wrong reason. The fragility was invisible.

## Root Cause

A one-character typo (`fall back` vs `falls back`) created a dead arm that was:
1. Syntactically valid regex — no parse error
2. Not reported as unreachable — PowerShell doesn't warn about never-matching alternation arms
3. Never tested independently at authoring time
4. Invisible during code review (the misspelling looks plausible)

This is **distinct from** but **related to** two known patterns:
- **Always-true first branch** (2026-05-01): the first arm matches all inputs,
  so later arms are never required. Here, the first arm is valid and correct.
- **Stale alternation after refactoring** (2026-05-05): an arm was correct at
  creation but became dead after the prompt changed. Here, the arm was dead
  **from inception** due to a typo.

The shared failure mode: a multi-arm alternation test passes while one or more
arms contribute nothing to coverage. You cannot determine which arm is carrying
the load without testing each arm in isolation.

## Solution

Replace any arm with an imprecise or potentially non-matching phrase with an
arm that exactly reproduces the wording from the prompt:

```powershell
# ✅ Every arm matches a real substring; 'falls back' has the correct spelling
It "cg-work invalid deviate: override warns and uses plan policy" {
    ($workContent -match 'warn.*plan policy|invalid.*deviate.*warn|falls back.*plan') | Should -Be $true
}
```

Changes:
- `fall back.*plan` → `falls back.*plan` (correct spelling)
- `invalid.*deviate.*override` → `invalid.*deviate.*warn` (removed "override" which doesn't appear; replaced with "warn" which does)

## Prevention

**When writing prompt-tools regex tests:**

1. **Quote directly from the prompt text.** Before writing a regex arm, read the
   actual prompt line being tested and derive the pattern from that literal text,
   not from memory of what you intended the prompt to say.

2. **Test each alternation arm independently.** In a scratch terminal or test,
   verify that each arm alone would match the target text. A passing test does
   not prove all arms match — it only proves at least one arm matches.

3. **Prefer narrow single-arm assertions over broad multi-arm fallbacks.** If the
   prompt uses a specific phrase, match that phrase specifically:
   ```powershell
   # ✅ Narrow and exact
   ($content -match 'invalid warns, falls back to plan') | Should -Be $true
   # ⚠️ Multi-arm — harder to verify each arm independently
   ($content -match 'warn.*plan|invalid.*deviate.*warn|falls back.*plan') | Should -Be $true
   ```

4. **Pay extra attention to conjugation and inflection.** Common misspellings in
   regex arms: `fall back` vs `falls back`, `warn` vs `warns`, `return` vs
   `returns`. These all change match behavior.

5. **After a prompt is refactored, re-derive all related regex patterns** from the
   new prompt text rather than editing the old patterns minimally.

## Related

- `.cg-docs/solutions/testing-patterns/2026-05-01-regex-alternation-masks-coverage-split-into-independent-assertions.md` — alternation where the first arm is always true, making later arms unreachable
- `.cg-docs/solutions/testing-patterns/2026-05-05-stale-alternation-after-prompt-refactoring.md` — arm was correct at creation but became dead after a prompt refactor
- `.cg-docs/solutions/testing-patterns/2026-05-15-common-word-regex-false-positive-in-security-assertions.md` — regex patterns that use common English words appearing elsewhere in the file
