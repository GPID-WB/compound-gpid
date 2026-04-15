---
date: 2026-04-15
title: "Roadmap out of sync when completed plan covered plan:null features"
category: "bugs"
type: "bug"
language: "both"
tags: [roadmap, cg-work, step-3-7, plan-null, status-drift, quality-loop]
root-cause: "Step 3.7 skipped features with plan:null and emitted only a soft warning — features were never updated after plan completion"
severity: "P2"
test-written: "yes"
fix-confirmed: "yes"
---

# Roadmap out of sync when completed plan covered plan:null features

## Symptom

Four Quality Loop features were delivered by plan
`.cg-docs/plans/2026-04-14-pushback-plan-review-side-ideas-schema-bypass.md`
(marked `status: completed` on 2026-04-14), but `roadmap.json` was never
updated. Specifically:

- `honest-pushback-in-brainstorm-strategy` — remained `status: idea`, `plan: null`
- `side-idea-capture-in-brainstorm` — remained `status: idea`, `plan: null`
- `plan-review-agent-and-prompt` — missing from roadmap entirely
- `schema-bypass-in-cg-resume` — missing from roadmap entirely

The `quality-loop` milestone also remained `in-progress` instead of `done`.

## Root Cause

This is a data consequence of the Bug 2 mechanism (see Related). `/cg-work`
Step 3.7 matched features by `plan` path. All four features had `plan: null`
at the time the plan ran — the two existing ones had never been linked, and
the two new ones didn't exist in the roadmap yet. Step 3.7 hit the
soft-warning path (`"No matching feature found… Verify the plan path is
linked with @cg-roadmap"`) and silently exited without updating any status.

## Reproduction Test

File: `tests/roadmap.Tests.ps1`

```powershell
Describe "roadmap.json - pushback plan features must be done and linked (Bug 2026-04-15)" {
    $roadmapPath = Join-Path (Join-Path $PSScriptRoot "..") "roadmap.json"
    $roadmap = Get-Content $roadmapPath -Raw | ConvertFrom-Json
    $planPath = ".cg-docs/plans/2026-04-14-pushback-plan-review-side-ideas-schema-bypass.md"

    $qlFeatures = @($roadmap.milestones | Where-Object { $_.id -eq "quality-loop" } | ForEach-Object { @($_.features) })

    # ... 10 It assertions checking status:done + plan linkage for all four features
}
```

Failed on current code: 10/10 assertions failed (4 features either missing or
not linked/done).

## Fix

`roadmap.json`:
- `honest-pushback-in-brainstorm-strategy`: set `status: done`, `plan: <path>`
- `side-idea-capture-in-brainstorm`: set `status: done`, `plan: <path>`
- Added `plan-review-agent-and-prompt` to `quality-loop`: `status: done`, `plan: <path>`
- Added `schema-bypass-in-cg-resume` to `quality-loop`: `status: done`, `plan: <path>`
- `quality-loop` milestone: `status` updated from `in-progress` to `done`
  (all features now done, so the derived status is `done`)

## Lessons Learned

When a plan is written before its roadmap features are fully mapped (a common
bootstrap pattern for new features), those features will have `plan: null`
at implementation time. Step 3.7's path-match logic cannot find them and
silently skips. This class of drift is invisible unless the roadmap is
audited post-completion.

The systemic fix is Bug 2's title-search fallback (see below and Related) —
which catches this pattern going forward. For historical drift, the data
must be fixed manually (as done here).

**Anti-pattern**: Marking a plan complete without also checking whether its
roadmap features are linked. The plan's Requirements table (column: Source)
names the features; these must match roadmap IDs.

## Related

- [2026-04-13: cg-work roadmap status never updated to done after plan completion](./../2026-04-13-cg-work-roadmap-status-never-updated-to-done.md) — root mechanism of Step ordering; this bug is a data consequence.
- [2026-04-15: cg-work Step 3.7 silently skips plan:null features](./../2026-04-15-cg-work-step-3-7-silent-skip-plan-null-features.md) — Bug 2: the systemic fix.
