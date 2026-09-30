---
date: 2026-05-22
title: "Agent dispatched for multiple task types needs an explicit execution mode guard"
category: "testing-patterns"
language: "both"
tags: [agent-design, dispatch, task-type, mode-guard, cr-academic-writing, writing, tables-figures, spurious-findings, review-protocol]
root-cause: "cr-academic-writing.agent.md was added to the Tables/Figures dispatch row without adding a guard that skips Writing-only checks (1–5, 7) when the task type is Tables/Figures. All 5 Writing checks would run against figure/code files and emit spurious findings."
severity: "P2"
---

# Agent Dispatched for Multiple Task Types Needs an Explicit Execution Mode Guard

## Problem

`cr-academic-writing.agent.md` was updated to run for both Writing and Tables/Figures
task types. The dispatch table in `cr-review.prompt.md` was correctly updated:

```
| Tables/Figures | @cg-documentation, @cr-academic-writing |
```

However, the agent's Review Protocol was not updated to skip Writing-specific
checks when the task type is Tables/Figures. Checks 1–5 (Section Structure,
Abstract Quality, Equation Exposition, Notation Consistency, Citation Completeness)
and Check 7 (Argument Flow) are all Writing-specific. When dispatched for a T/F
task, they would run against figure captions and table code files, producing:

- Spurious findings: "Results section precedes methodology" on a `.tex` figure file
- Incorrect P2 flags: Abstract quality check on a table note block
- Check 6 (Figure and Table Presentation) being diluted among irrelevant findings

The bug was latent — no T/F review was run before the second standard review
caught it, so no spurious output was produced.

## Root Cause

The dispatch update and the agent update are **two separate changes that must
be co-authored**. Adding an agent to a new task-type dispatch row creates
a contract: every check in the agent must either be valid for the new task type
OR gated behind an explicit task-type check.

When an agent has checks from two domains (Writing vs. presentation quality),
the Writing checks are meaningless against figure/table files. Without a guard,
the agent's "perform all N checks in sequence" instruction executes all of them
regardless.

## Solution

Add a task-type guard early in the Review Protocol, before the check sequence:

```markdown
## Review Protocol

Before beginning: if the file contains only whitespace or comments (no prose
content), report: "`[file]` is empty — academic writing review skipped for
this file." Do not run Checks 1–7 against empty files.

**Task type guard**: If dispatched for a Tables/Figures task, skip Checks 1–5
and 7 (Writing-specific). Execute Check 6 only, delegating figure-caption
and table-note criteria to `cr-skill-publication-output` Sections 5–6.

For each file under review, perform all 7 checks below in sequence.
```

## Prevention

**Rule**: When adding an agent to a new task-type dispatch row, immediately audit
every check in the agent:

1. Is this check valid for the new task type?
2. If not, add an explicit guard skipping it.
3. Update the frontmatter `description` to list all task types the agent now serves.
4. Add a test covering both dispatch rows.

**Test pattern** — dispatch rows must route to both agents:

```powershell
It "Tables/Figures dispatch row routes to @cg-documentation" {
    ($content -match 'Tables/Figures.*@cg-documentation') | Should -Be $true
}

It "Tables/Figures dispatch row routes to @cr-academic-writing" {
    ($content -match 'Tables/Figures.*cr-academic-writing') | Should -Be $true
}
```

**Generalized rule**: An agent's review protocol must either be task-type-neutral
(all checks apply to all task types) OR include explicit guards for task-type-specific
checks. There is no safe middle ground.

## Related

- `.cg-docs/solutions/testing-patterns/2026-05-14-dispatch-table-must-cover-all-taxonomy-entries.md` — companion rule: every task type must have a dispatch row (coverage). This solution is the mirror: every dispatched check must be valid for the dispatched task type (validity).
- `.cg-docs/solutions/testing-patterns/2026-05-01-fix-triage-prompt-changes-need-co-authored-tests.md` — dispatch changes need co-authored tests.
