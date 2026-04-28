---
date: 2026-04-28
title: "Agent Inputs description uses snake_case when prompt defines kebab-case variable names"
category: "bugs"
language: "both"
tags: [agents, prompt-design, naming-convention, kebab-case, snake_case, naming-drift, cg-release, cg-release-scanner]
root-cause: "cg-release-scanner.agent.md Inputs description used window_days and tag_date (underscores) while cg-release.prompt.md defined and passed window-days and tag-date (hyphens) — caught in code-quality review but missed during initial implementation"
severity: "P3"
fix-confirmed: "yes"
reviewed-in: ".cg-docs/reviews/2026-04-28-cg-release-scan-optimization-verify-review.md"
---

# Agent Inputs Description Uses Snake_case When Prompt Defines Kebab-Case Variable Names

## Problem

`cg-release.prompt.md` defines and passes a computed variable named `window-days`
(hyphen) and `tag-date` (hyphen) to the `@cg-release-scanner` agent. The agent's
`Inputs` section, however, described the formula using underscores:

```markdown
<!-- cg-release-scanner.agent.md line 20 — BEFORE fix -->
- `window-start` — ISO date string (YYYY-MM-DD) marking the start of the scan
  window (pre-computed by the prompt as `max(today - window_days, tag_date)`)
```

The hyphens in the actual variable names were correct everywhere else in both
files — this was a naming-convention inconsistency confined to the parenthetical
formula in the Inputs description.

## Root Cause

The agent was written independently of the prompt variable naming. When the
prompt was later edited to standardize on `window-days` / `tag-date` (hyphens
replacing an earlier underscore convention), the parenthetical formula in the
agent's Inputs description was missed because:

1. It is a natural-language parenthetical `(pre-computed by the prompt as …)`,
   not a code reference — not highlighted by syntax
2. The variable names appear in both forms (`window-days` used elsewhere in the
   same agent) so grep for `window-days` returns results and looks clean
3. The inconsistency does not affect runtime behavior — it is documentation drift

The `cg-code-quality` agent found it during the verify review pass.

## Solution

Change the parenthetical formula to match the prompt's naming convention:

```markdown
<!-- AFTER fix -->
- `window-start` — ISO date string (YYYY-MM-DD) marking the start of the scan
  window (pre-computed by the prompt as `max(today - window-days, tag-date)`)
```

Additionally, add regression tests to catch a future reversion:
```powershell
It "uses window-days (hyphen, not underscore) in window-start description" {
    ($agentContent -match 'window-days') | Should Be $true
}
It "uses tag-date (hyphen, not underscore) in window-start description" {
    ($agentContent -match 'tag-date') | Should Be $true
}
```

## Prevention

When an agent file's Inputs section contains a formula or expression using
variable names from the calling prompt, verify naming convention consistency
by searching for **both forms** of each variable name:

```powershell
# Quick check — should find results for hyphens, zero for underscores
Select-String -Path .github/agents/cg-release-scanner.agent.md -Pattern 'window-days'
Select-String -Path .github/agents/cg-release-scanner.agent.md -Pattern 'window_days'  # should be empty
```

**Rule**: When renaming a prompt variable (e.g., `window_days` → `window-days`),
always grep **all agent files** for the old name — not just the prompt file.
Agent Inputs descriptions are prose and do not fail any build; they are
invisible to automated rename tools.

## Related

- [Hardcoded R Hierarchy in Agent Files Bypasses Dialect Config](../bugs/2026-04-08-hardcoded-r-hierarchy-in-agent-files-bypasses-dialect-config.md) — same pattern: agent files carry stale terminology that diverges from the system-wide convention
- [Prompt Guard Conditions Need Immediate Pester Coverage](../testing-patterns/2026-04-28-prompt-guard-conditions-need-immediate-pester-coverage.md) — companion: the tests that would have caught this regression
