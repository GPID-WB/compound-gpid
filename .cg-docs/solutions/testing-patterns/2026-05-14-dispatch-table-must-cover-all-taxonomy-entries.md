---
date: 2026-05-14
title: "Dispatch table driven by a taxonomy must cover all taxonomy entries — missing rows fall through to wrong default"
category: "testing-patterns"
language: "both"
tags: [prompt-design, dispatch-table, taxonomy, task-type, cr-review, completeness-check, enumeration, default-fallback, agent-dispatch]
root-cause: "The cr-review.prompt.md Step 3 dispatch table mirrored a taxonomy from cr-skill-research-workflow (8 task types) but had rows for only 6. EDA and Implementation tasks fell through to @cr-econometric-reasoning as the catch-all — semantically wrong for both task types."
severity: "P2"
---

# Dispatch Table Driven by a Taxonomy Must Cover All Taxonomy Entries

## Problem

`cr-review.prompt.md` Step 3 contained a dispatch table routing task types to
research agents:

```markdown
| Task Type             | Additional Agents                            |
|-----------------------|----------------------------------------------|
| Theory/Modeling       | @cr-identification-audit, @cr-econometric-reasoning |
| Specification Analysis| @cr-specification-analysis *(Phase 4)*       |
| ML/Prediction         | @cr-ml-methodology *(Phase 5)*, @cg-performance |
| Writing               | @cr-academic-writing *(Phase 6)*             |
| Reproducibility       | @cr-replication-package *(Phase 7)*          |
| Tables/Figures        | @cg-documentation                            |
```

`cr-skill-research-workflow` defines **8** task types. The table covers **6**.
Missing: `EDA` and `Implementation`.

When the task type is `EDA` or `Implementation`, the agent falls through to:
> "Task type cannot be determined → dispatch `@cr-econometric-reasoning` by default"

This dispatches a structural econometrics reviewer to EDA and implementation
work — no findings on theory or model structure, but also no `@cg-performance`
or `@cg-data-quality` which are the natural agents for those task types.

Found as **P2.11** in the 2026-05-14 thorough review of Compound Research Phase 3.

## Root Cause

The dispatch table and the taxonomy were written at different points in time.
The table was built from the "obvious" research task types (theory, writing,
reproducibility) without systematically consulting the skill's taxonomy entries.
The `cr-skill-research-workflow` skill was the authoritative source but wasn't
checked against the table during authoring.

This is an instance of the enumeration propagation problem: when a canonical
list exists in one file (the skill), all derived lists that mirror it (dispatch
tables, test lists, reference docs) must be audited against the canonical source
whenever either changes.

## Solution

1. Add the missing rows:
   ```markdown
   | EDA             | @cg-performance, @cg-data-quality |
   | Implementation  | @cg-performance                   |
   ```

2. Add a catch-all audit note in the dispatch step:
   ```markdown
   > If the task type does not match any row above, dispatch
   > `@cr-econometric-reasoning` as default **and** log a warning:
   > "Unrecognized task type '[type]' — defaulting to @cr-econometric-reasoning.
   > If this is a recurring task type, add it to the dispatch table in Step 3
   > and to cr-skill-research-workflow."
   ```
   This turns the silent wrong-default into a visible maintenance signal.

## Pattern

**When a dispatch table mirrors an externally-defined taxonomy, add a
completeness check:**

```powershell
# Test: dispatch table must cover all taxonomy entries
$taxonomyTypes  = @('Theory/Modeling','Specification Analysis','EDA',
                    'Implementation','ML/Prediction','Writing',
                    'Tables/Figures','Reproducibility')
$dispatchContent = Get-Content $dispatchFile -Raw
foreach ($type in $taxonomyTypes) {
    It "dispatch table contains row for '$type'" {
        ($dispatchContent -match [regex]::Escape($type)) | Should -Be $true
    }
}
```

This test will fail the moment a new task type is added to the taxonomy without
updating the dispatch table.

## Prevention

When adding a new entry to a taxonomy:
1. Search for all dispatch tables, test lists, and documentation tables that
   mirror the taxonomy
2. Add the new entry to each
3. If a dispatch table has a catch-all default, decide whether the new type
   has a better default than the generic one

When reviewing a dispatch table:
- Count table rows vs. taxonomy entries
- If rows < entries: P2 (non-exhaustive dispatch — semantic-wrong default silently fires)

## Related

- [`2026-04-08-cross-cutting-enumeration-propagation-audit.md`](./2026-04-08-cross-cutting-enumeration-propagation-audit.md) — canonical source: when a list changes, audit all mirrors
- [`2026-04-17-exact-count-assertion-prevents-silent-regression-when-test-name-states-count.md`](./2026-04-17-exact-count-assertion-prevents-silent-regression-when-test-name-states-count.md) — exact-count tests catch incomplete enumeration
