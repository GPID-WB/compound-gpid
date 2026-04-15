---
date: 2026-04-15
title: "New validation branch added without a test for the new code path"
category: "testing-patterns"
language: "both"
tags: [pester, powershell, coverage, validation, schema, new-branch, silent-failure, test-gap]
root-cause: "A new conditional branch (cross-milestone duplicate ID check) was added to a validation function without adding a test that exercises the new branch — leaving the validation silently untested"
severity: "P1"
fix-confirmed: "yes"
reviewed-in: ".cg-docs/reviews/2026-04-15-per-step-test-failure-handling-verify-review.md"
---

# New Validation Branch Added Without a Test for the New Code Path

## Problem

`tests/roadmap.Tests.ps1`'s `Test-RoadmapSchema` function was extended with a
cross-milestone duplicate feature ID check:

```powershell
$allFeatureIds = @{}
# inside feature loop:
if ($allFeatureIds.ContainsKey($f.id)) {
    $errors += "Duplicate feature id '$($f.id)' appears in multiple milestones"
} else {
    $allFeatureIds[$f.id] = $true
}
```

The existing test for duplicate feature IDs used a single-milestone fixture:
```powershell
It "rejects duplicate feature IDs within a milestone" {
    $roadmap = @{
        milestones = @(@{
            id = "m1"; ...
            features = @(
                @{ id = "dup-feat"; ... }
                @{ id = "dup-feat"; ... }  # same milestone
            )
        })
    }
    ...
}
```

This test never reaches the `$allFeatureIds` cross-milestone branch — it fires
the *intra-milestone* `$featureIds` check instead. Both checks produce a
"Duplicate feature id" error, so the test passes, and there is no signal that
the cross-milestone path is untested.

The fix (P3.9 from the standard review) added the validation code. The light
verify-review caught it as P1.1: the new branch had zero test coverage.

## Root Cause

When extending a validation function with a **new branch** that handles a
**new case**, the existing tests for the existing case still pass. Nothing
fails. The new branch is exercised only when input matches the new case — and
if no test provides that input, the new branch is permanently unreachable from
the test suite.

**The general pattern**: Adding a new conditional path to an existing
function requires adding a new test that specifically triggers that path.
The existing tests are not sufficient because they exercise the existing path,
not the new one.

This is easy to miss because:
- The function signature didn't change
- Existing tests still pass
- The error *message* is similar enough to the existing message that casual
  review doesn't notice the branch is different

## Solution

Add a dedicated test that constructs the minimal fixture triggering the new path:

```powershell
It "rejects duplicate feature IDs across milestones" {
    $roadmap = @{
        schemaVersion = "compound-gpid-roadmap-v1"
        milestones    = @(
            @{
                id       = "m1"; title = "M1"; objective = "x"; status = "planned"
                features = @(@{ id = "shared-feat"; title = "F1"; status = "idea"; plan = $null })
            }
            @{
                id       = "m2"; title = "M2"; objective = "x"; status = "planned"
                features = @(@{ id = "shared-feat"; title = "F2"; status = "idea"; plan = $null })
            }
        )
    }
    $errors = Test-RoadmapSchema $roadmap
    ($errors -join " ") | Should Match "multiple milestones"
}
```

The key difference from the existing test:
- **Two milestones** (not one) — this is the new-path trigger
- Match on `"multiple milestones"` — pinned to the new error message, not the
  generic "Duplicate feature id" that both paths produce

## Prevention

**Rule**: Every new conditional branch in a validation or schema function
requires a new `It` block that:
1. Constructs a fixture that triggers **only** the new branch (not the existing one)
2. Matches the **specific error message or output** of the new branch (not a
   generic substring that both branches produce)

**Checklist when adding a new validation case**:
- [ ] What input scenario triggers the new branch exclusively?
- [ ] Does the new branch produce a distinct error message? If so, use that
  in the `Should Match` assertion, not a generic substring.
- [ ] Does the existing test fixture reach the new branch? (Check manually —
  don't assume it does because the test passes.)

**Review heuristic**: If a validation function has N conditional paths,
it needs at least N `It` blocks — one per path. A count mismatch is a signal
that a path is untested.

## Related

- `.cg-docs/solutions/testing-patterns/2026-04-07-pester-test-quality-patterns.md`
  — Pattern 4 (named-criteria guards): named prompt criteria without a test
  are a parallel pattern (feature present but untested)
- `.cg-docs/solutions/testing-patterns/2026-03-30-derived-invariant-validation-in-schema-tests.md`
  — testing derived/computed invariants in schema validation (complementary)
- `.cg-docs/solutions/testing-patterns/2026-03-30-prompt-pipeline-contract-testing.md`
  — upstream pattern for testing prompt contracts (adjacent: what to test)
