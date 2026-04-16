---
date: 2026-04-15
title: "Roadmap feature linkage must be audited when marking a plan complete"
category: "testing-patterns"
language: "both"
tags: [roadmap, cg-work, plan, feature-linkage, data-integrity, status-drift, quality-loop]
root-cause: "Plans are sometimes written before all target features exist or are linked in roadmap.json; if not audited at completion, features silently remain unlinked and their status is never updated"
severity: "P2"
---

# Roadmap Feature Linkage Must Be Audited When Marking a Plan Complete

## Problem

A plan was marked `status: completed` on 2026-04-14 but four features it
delivered remained unlinked (`plan: null`) and at their old status
(`idea`) in `roadmap.json`. The `quality-loop` milestone continued to show
as `in-progress` for a day after everything was shipped.

This is a silent data integrity failure — no error, no test failure, no
visible indicator. The only way to catch it is to audit the roadmap
against the plan's requirements.

## Root Cause

Plans are often written *before* all target roadmap features are created.
The plan's Requirements table lists feature IDs, but if those features
aren't yet in `roadmap.json`, their `plan` field is `null`. When `/cg-work`
Step 3.7 runs, it only matches features by `plan` path — `plan: null`
features are structurally unreachable. Step 3.7 emits a soft warning and
exits without updating anything.

The same failure occurs when a plan covers *existing* features that were
never linked (still have `plan: null`).

## Solution

**Invariant to enforce:** Every feature listed in a plan's Requirements
table must have a non-null `plan` field in `roadmap.json` before the plan
is marked `status: completed`.

### At implementation time (in `/cg-work` Step 3.5)

Before marking the plan complete, verify that all features named in the
plan's requirements are present and linked in `roadmap.json`:

```
For each requirement in the plan's Requirements table:
  1. Find the matching feature in roadmap.json by ID or title
  2. If missing: add it to the correct milestone
  3. If plan: null: dispatch @cg-roadmap to link it
  4. Only then mark the plan completed
```

### At review time (in `roadmap.Tests.ps1`)

For high-value milestones, add explicit data-integrity assertions:

```powershell
Describe "roadmap.json - <milestone> plan linkage integrity" {
    $planPath = ".cg-docs/plans/YYYY-MM-DD-plan-name.md"
    $features = @($roadmap.milestones | Where-Object { $_.id -eq "<milestone>" } |
                  ForEach-Object { @($_.features) })

    It "<feature-id> is linked to the correct plan" {
        $f = $features | Where-Object { $_.id -eq "<feature-id>" }
        (@($f))[0].plan | Should Be $planPath
    }

    It "<feature-id> has status done" {
        $f = $features | Where-Object { $_.id -eq "<feature-id>" }
        (@($f))[0].status | Should Be "done"
    }
}
```

This pattern was added for the pushback plan (2026-04-15) and catches drift
immediately when running the full test suite.

## Prevention

### Checklist before marking a plan complete

Before writing `status: completed` to a plan's frontmatter:

- [ ] Open `roadmap.json` and find every feature listed in the plan's
      Requirements table
- [ ] Confirm each feature has `"plan": "<this-plan-path>"` (not null)
- [ ] Confirm each feature has `"status": "done"` (or dispatch `@cg-roadmap`)
- [ ] Confirm the milestone `status` field matches the derived status
      (all-done features → `done`)

### Anti-pattern to avoid

Writing a plan that references features by ID *before adding those features
to `roadmap.json`*, then never circling back to add them. Plans and roadmap
must be kept in sync as a pair.

## Related

- [2026-04-15 — Roadmap out of sync after plan:null features completed](../bugs/2026-04-15-roadmap-out-of-sync-after-plan-null-features-completed.md)
- [2026-04-15 — cg-work Step 3.7 silently skips plan:null features](../bugs/2026-04-15-cg-work-step-3-7-silent-skip-plan-null-features.md)
- [2026-04-13 — cg-work roadmap status never updated to done after plan completion](../bugs/2026-04-13-cg-work-roadmap-status-never-updated-to-done.md)
