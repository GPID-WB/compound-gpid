---
date: 2026-03-30
title: "Validate derived state against stored state in schema tests"
category: "testing-patterns"
language: "both"
tags: [powershell, pester, schema-validation, derived-state, invariant, status-drift, roadmap]
root-cause: "Schema tests only checked field presence and enum membership, not that derived fields were consistent with their source fields. Stale status values could persist in roadmap.json without any test catching the drift."
severity: "P2"
---

# Validate Derived State Against Stored State in Schema Tests

## Problem

`Test-RoadmapSchema` validated that `milestone.status` was a member of the allowed
enum (`planned`, `in-progress`, `done`). It did **not** verify that the stored
status matched the value that `Get-MilestoneStatus` would derive from the
milestone's features array.

A roadmap file could therefore contain `{"status":"done"}` while all its features
had `status: "planned"`. The schema validator passed it; the discrepancy was
invisible at commit time.

```json
{
  "id": "m1",
  "status": "done",
  "features": [{"id": "f1", "status": "planned", ...}]
}
```

`Test-RoadmapSchema` would return 0 errors. `Get-MilestoneStatus` would return
`"planned"`. No test caught the mismatch.

## Root Cause

The schema test focused on structural validity (required fields, enum membership,
ID format). It treated `status` as an independent stored field, not as a derived
field with an invariant that must stay in sync with its source data (`features`).

This class of bug — **derived state diverges from source state** — is common in
systems where the same logical fact is stored redundantly. The invariant is only
enforced if a test explicitly recomputes and compares.

## Solution

In `Test-RoadmapSchema`, after the status enum check passes, recompute the expected
status from features and compare:

```powershell
# In Test-RoadmapSchema, after status enum check and after features are coerced:
if ($m.status -and $validMilestoneStatuses -contains $m.status) {
    $derived = Get-MilestoneStatus $features
    if ($m.status -ne $derived) {
        $errors += "Milestone '$($m.id)' status is '$($m.status)' but derived status from features is '$derived'"
    }
}
```

Add a Pester test that specifically triggers the mismatch rejection:

```powershell
It "rejects a milestone whose stored status does not match derived status" {
    $roadmap = @{
        schemaVersion = "compound-gpid-roadmap-v1"
        milestones    = @(
            @{
                id        = "m1"
                title     = "Milestone One"
                objective = "Do something"
                status    = "done"   # stored as done...
                features  = @(
                    @{ id = "f1"; title = "Feature"; status = "planned" }  # ...but features say planned
                )
            }
        )
    }
    $errors = Test-RoadmapSchema $roadmap
    $errors | Should -Contain "Milestone 'm1' status is 'done' but derived status from features is 'planned'"
}
```

### General Pattern

For any schema that has a derived field `D` computed from source fields `S`:

1. Implement a pure function `Get-DerivedValue(S)` — deterministic, no side effects.
2. In the schema validator, call `Get-DerivedValue(S)` and compare to the stored `D`.
3. Return an explicit error string naming both the stored and computed values.
4. Write a Pester/test case for each status transition that could produce a mismatch.

## Prevention

- Whenever adding a field to a JSON schema that is **derived** from other fields,
  immediately add a validator step that calls the derivation function and compares.
- Document derived fields explicitly: mark them with a note like
  `DERIVED: computed from features — do not set directly` in agent instructions,
  schema docs, and code comments.
- Mirror derivation logic in tests: keep the pure helper function (`Get-MilestoneStatus`)
  synchronized with the agent spec and test it independently (unit tests for the
  helper, integration tests for the invariant check).

```powershell
# Document that status is derived in the agent/schema spec:
# Milestone status is DERIVED from features — never set directly by a user or agent.
# @cg-roadmap.agent.md: Milestone Status Calculation section.
```

## Related

- `.cg-docs/solutions/bugs/2026-03-30-ps51-convertfrom-json-single-element-array-coercion.md`
  — PS 5.1 array coercion fix applied in the same schema validator
- `.cg-docs/solutions/bugs/2026-03-19-persistent-state-written-before-validation-causes-corruption.md`
  — related pattern: validate before writing persistent state
