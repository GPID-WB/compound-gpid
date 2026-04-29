---
date: 2026-04-29
title: "Writing a Pester test for an unshipped schema marker creates a persistent pre-existing failure"
category: "testing-patterns"
language: "both"
tags: [pester, testing, schema-version, SCHEMA_VERSION, pre-existing-failure, tdd, test-hygiene, compound-gpid]
root-cause: "A Pester test asserting a SCHEMA_VERSION marker was written based on a review recommendation, but the corresponding SCHEMA_VERSION update was never applied. The test became a persistent failure for 20+ days across multiple sessions."
severity: "P2"
---

# Writing a Pester Test for an Unshipped Schema Marker Creates a Persistent Pre-Existing Failure

## Problem

A review finding (P2.6 in `2026-04-09-ce-improvements-phase3-fix-verify-review.md`)
recommended bumping `SCHEMA_VERSION` to `2026-04-09-scope-fields` when the `scope:`
frontmatter field was introduced in plan and brainstorm artifacts. A Pester test was
written to enforce this contract:

```powershell
It "SCHEMA_VERSION contains scope-fields marker" {
    ($content -match 'scope-fields') | Should Be $true
}
```

The SCHEMA_VERSION update was never applied. The file continued to read
`2026-04-07-r-syntax-dialect`, then `2026-04-28-release-scanner-agent` after a later
unrelated bump — neither contained `scope-fields`.

The test failed from the day it was committed (2026-04-09) until it was diagnosed and
fixed on 2026-04-29 — a span of 20 days and multiple review/fix-triage cycles. Every
test run reported 1 pre-existing failure in `prompt-tools.Tests.ps1`, creating noise
that made it harder to spot genuine regressions.

## Root Cause

A test was written to assert **future state** — a state the codebase did not yet
occupy and was never moved into. The pattern is identical to failing TDD (write the
test, forget to write the implementation), but harder to spot because:

1. The test and implementation are in different files (`tests/prompt-tools.Tests.ps1`
   vs. `SCHEMA_VERSION`)
2. The "implementation" is a one-line text file bump, not a code change — easy to
   treat as a follow-on cleanup item and defer indefinitely
3. No signal in either file linked them: a developer bumping SCHEMA_VERSION for a
   later feature had no reason to know the `scope-fields` marker was expected

The SCHEMA_VERSION file is also subject to the same anti-pattern: each bump
overwrites the previous value entirely, so a later feature bump (`release-scanner-agent`)
silently erased the pending `scope-fields` marker.

## Solution

**Rule: never write a test that asserts a state the codebase does not currently
occupy.** A test for a schema marker must ship in the same commit as the marker itself.

If the test is being written before the implementation (TDD), mark it `Pending` until
the implementation is ready:

```powershell
# ⚠️ PENDING until SCHEMA_VERSION is bumped to include scope-fields
It "SCHEMA_VERSION contains scope-fields marker" -Pending {
    ($content -match 'scope-fields') | Should Be $true
}
```

Pester 3.4 treats `Pending` tests as skipped — they don't fail the suite and they
are visible in output as a reminder.

### Fixing a Backlog of Schema Markers

When a schema marker test is already failing due to this pattern:

1. Identify *all* pending markers from deferred review findings (grep solutions/ and
   reviews/ for `SCHEMA_VERSION` + `marker`)
2. Include all pending markers in the next SCHEMA_VERSION bump, combined:
   ```
   2026-04-29-project-scanner-scope-fields
   ```
   (Combine by using the most descriptive marker — not a hyphenated concatenation of
   all markers, which would be unreadable. The marker names the feature family, not
   every individual field.)
3. Update SCHEMA_VERSION and commit alongside the test fix.

### Prevention via SCHEMA_VERSION Maintenance Convention

When introducing a new frontmatter field to any compound-gpid artifact (plans,
brainstorms, reviews, local config), the commit that introduces the field must also
bump SCHEMA_VERSION to include a descriptive marker for the new field. If a test is
also added, all three changes (field, marker, test) ship together.

## Prevention

- **Test only current state**: Pester tests assert what is true now, not what will be
  true after a deferred follow-up. Mark aspirational tests as `Pending`.
- **Atomic commits for schema changes**: SCHEMA_VERSION bump + test for that bump
  must be in the same commit — never split across PRs or sessions.
- **Later SCHEMA_VERSION bumps are not additive**: bumping for feature B erases any
  pending intent to include feature A's marker. Audit open SCHEMA_VERSION todos
  before each bump.

## Related

- `.cg-docs/solutions/testing-patterns/2026-04-22-schema-constant-coupling-value-equality-test-and-maintenance-anchor.md` — general pattern for cross-file schema constant coupling
- `.cg-docs/solutions/testing-patterns/2026-04-28-prompt-guard-conditions-need-immediate-pester-coverage.md` — similar "write test at the same time as the code" principle for prompt guards
