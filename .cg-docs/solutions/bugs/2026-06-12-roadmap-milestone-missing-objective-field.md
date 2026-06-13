---
date: 2026-06-12
title: "roadmap.json milestone missing required 'objective' field passes silently until schema validation"
category: "bugs"
language: "both"
tags: [roadmap, schema, validation, milestone, objective, json, roadmap.json, schema-validation, pester]
root-cause: "A milestone was written (and later marked 'done') without the required 'objective' field. The omission was never caught by @cg-roadmap dispatch or manual review — only surfaced by the Pester schema validation test during a full-suite regression gate."
severity: "P2"
fix-confirmed: "yes"
reviewed-in: ".cg-docs/reviews/2026-06-12-goal-driven-execution-verify-review.md"
---

# `roadmap.json` Milestone Missing Required `objective` Field — Silent Until Schema Validation

## Problem

During a full-suite regression gate after an unrelated fix-triage session, the
roadmap schema test failed:

```
FAIL: roadmap > roadmap.json file validation > actual roadmap.json passes schema validation
     roadmap.json has 1 schema error(s):
     Milestone 'workflow-maturity' missing required field: objective
```

The `workflow-maturity` milestone had been present for weeks and had already been
marked `"status": "done"`, but it was created and maintained without an `objective`
field. The schema validation test caught it only because the full suite happened
to run as part of a regression gate.

## Root Cause

The roadmap JSON schema requires every milestone to have an `objective` field
(a human-readable description of what the milestone is trying to achieve). The
`workflow-maturity` milestone was written with only `id`, `title`, `status`, and
`features` — no `objective`.

This gap existed silently because:
1. `@cg-roadmap` dispatches do not enforce schema at write time — they write
   the specified structure and trust the author to include required fields.
2. The `roadmap.json` file is not modified through a schema-validating editor.
3. Code review of `roadmap.json` diff does not automatically check the schema.
4. The Pester schema validation test (`roadmap.Tests.ps1`) does catch it — but
   only when the full test suite runs.

## Solution

Added the missing `objective` field to `workflow-maturity`:

```json
{
  "id": "workflow-maturity",
  "title": "Workflow Maturity",
  "objective": "Improve the plan-to-execute cycle with branch-aware planning, phased execution, GitHub Issues integration, and a goal-driven completion contract — giving teams clearer scope, better continuity across sessions, and stronger integration with GitHub workflows.",
  "status": "done",
  "features": [...]
}
```

After the fix, `roadmap.Tests.ps1` returned 100/100 passing.

## Prevention

**When creating or completing a milestone:**

1. **Always include `objective` at milestone creation.** The `objective` field
   is required by schema — add it at the same time as `id`, `title`, and
   `status`. A one-sentence description is sufficient.

2. **Before marking a milestone `done`, run `roadmap` tests:**
   ```powershell
   . tests\Run-Tests.ps1 -File roadmap
   ```
   This catches schema gaps before they accumulate.

3. **When dispatching `@cg-roadmap` to create a new milestone**, explicitly
   provide the `objective` in the dispatch instruction. Do not let @cg-roadmap
   infer or omit it.

4. **Template for a valid milestone**:
   ```json
   {
     "id": "<kebab-case-id>",
     "title": "<Human-Readable Title>",
     "objective": "<One sentence: what this milestone achieves and why.>",
     "status": "planned",
     "features": []
   }
   ```

5. **Run the full regression gate** (`Run-Tests.ps1` with no `-File` flag)
   after any direct edit to `roadmap.json`. The schema test catches gaps that
   targeted partial runs miss.

## Related

- `tests/roadmap.Tests.ps1` — contains the schema validation test that caught this
- `.cg-docs/solutions/bugs/2026-04-13-cg-work-roadmap-status-never-updated-to-done.md` — related: roadmap completion state not updated; both are gaps between implementation and roadmap bookkeeping
- `.cg-docs/solutions/testing-patterns/2026-04-15-roadmap-plan-linkage-must-be-audited-at-completion.md` — related: completeness checks at milestone done time
