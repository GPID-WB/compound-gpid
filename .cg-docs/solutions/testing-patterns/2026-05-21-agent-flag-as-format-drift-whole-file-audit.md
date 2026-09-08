---
date: 2026-05-21
title: "Agent 'Flag as' format drift — incremental check additions leave old-format directives"
category: "testing-patterns"
language: "both"
tags: [agent, flag-as, format-drift, incremental-additions, audit, cr-agents]
root-cause: "When a new check is added to an agent file using the new priority-first format, existing checks retain the old format — creating inconsistency across the same file."
severity: "P1"
---

# Agent "Flag as" Format Drift — Incremental Check Additions Leave Old-Format Directives

## Problem

After a Phase 5 review of `cr-ml-methodology.agent.md` and `cr-specification-analysis.agent.md`, a second standard review found that 7 of 8 "Flag as" directives in `cr-ml-methodology.agent.md` still used the **old** format:

```
Flag as **[cr-ml-methodology] [P0.N]** if preprocessing is fit on any data…
```

Check 8 (newly added in the Phase 5 pass) and the output template both used the **new** priority-first format:

```
Flag as **[P0.N]** [cr-ml-methodology] if…
```

The result: when the agent reasons check-by-check, it follows the proximal "Flag as" instruction — so Checks 1–7 produce old-format findings, Check 8 produces new-format findings. Compiled review reports are inconsistent and potentially unparseable by `/cg-fix-triage`.

The same pattern appeared in `cr-specification-analysis.agent.md`: Check 1 had been updated to new format (during a prior fix-triage), but Checks 2–6 retained the old format.

## Root Cause

Format normalization was done **incrementally** — new checks were added with the new format, and prior passes fixed only the specific lines mentioned in the review report. No whole-file audit was performed after each partial fix. The old-format checks survived because they were "not the problem at the time."

This is a meta-pattern of incomplete normalization: when you fix N instances, there are N+K instances, and K remain unfixed because the review only cited N.

## Solution

After any review pass that touches "Flag as" directives in an agent file, run a whole-file audit:

```powershell
# Check for old-format directives in any agent file
Select-String -Path ".github/agents/*.agent.md" -Pattern '\*\*\[cr-[a-z-]+\] \[P[0-9]' 
```

All matches indicate old-format directives that must be updated.

**New format** (priority-first):
```markdown
Flag as **[P0.N]** [agent-name] if <condition>.
```

**Old format** (agent-first — deprecated):
```markdown
Flag as **[agent-name] [P0.N]** if <condition>.
```

Applied the whole-file fix across both agents in commit `2f6aa8a`:
- `cr-ml-methodology.agent.md`: 7 directives updated (lines 66, 93, 118, 146, 179, 208, 230)
- `cr-specification-analysis.agent.md`: 5 directives updated (lines 65, 100, 129, 152, 176, 193)

## Corollary: Empty-File Guards Need Updating When Checks Are Added

`cr-ml-methodology.agent.md` line 39 had the guard:

> "Do not run Checks 1–7 against empty files."

After adding Check 8, the guard was not updated. Whenever a new check is added, search for the guard text `Do not run Checks 1–` and update the count to include the new check.

## Prevention

1. **After adding any new check to an agent file**: run the `Select-String` grep above and update all old-format directives in the same commit.
2. **After adding any new check**: search for `Do not run Checks 1–` in the same file and update the count.
3. **Pester test pattern**: Add a test that the old format does NOT appear anywhere in the file:
   ```powershell
   It "uses priority-first format for all Flag-as directives" {
       ($content -match '\*\*\[cr-[a-z]+-[a-z]+\] \[P[0-9]') | Should -Be $false
   }
   ```
   This is a **negative assertion** — catching old-format occurrences rather than confirming new-format ones.

## Related

- `.cg-docs/solutions/testing-patterns/2026-05-01-regex-alternation-masks-coverage-split-into-independent-assertions.md` — related: tests that tolerate two phrasings mask regressions on either branch
- `.cg-docs/solutions/testing-patterns/2026-05-20-agent-step-carveout-must-not-contradict-global-deferral-policy.md` — related: other agent-file maintenance patterns that require whole-file audits
- `.cg-docs/solutions/testing-patterns/2026-04-08-cross-cutting-enumeration-propagation-audit.md` — related: when a schema value is added, all agent badge tables must be updated (same "audit on change" meta-pattern)
