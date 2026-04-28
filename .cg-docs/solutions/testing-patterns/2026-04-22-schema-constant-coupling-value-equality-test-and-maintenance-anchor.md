---
date: 2026-04-22
title: "Schema constants mirroring JSON registries need value-equality tests and cross-file maintenance anchors"
category: "testing-patterns"
language: "both"
tags: [pester, testing, schema-version, json, registry, coupling, maintenance-anchor, prompt-design, value-equality]
root-cause: "Presence-only tests (Should Not BeNullOrEmpty) for schema version constants don't catch drift when the same constant appears in both a JSON registry and a prompt file. Neither file reminded developers to update the other, causing silent mismatch risk."
severity: "P2"
---

# Schema Constants Mirroring JSON Registries Need Value-Equality Tests and Cross-File Maintenance Anchors

## Problem

`repos.json` contains a `schemaVersion` field:

```json
{
  "schemaVersion": "compound-gpid-competitive-reviews-v1",
  "repos": [...]
}
```

`cg-review-repos.prompt.md` Step 1 checks that the file's `schemaVersion` matches
a hardcoded expected value. The Pester test for `repos.json` only verified presence:

```powershell
It "has schemaVersion field" {
    $json.schemaVersion | Should Not BeNullOrEmpty
}
```

This test would pass even if:
- The constant was bumped in `repos.json` but not in the prompt (or vice versa)
- A typo was introduced during a manual schema bump
- A future developer created a new `repos.json` from scratch with an incorrect constant

Additionally, neither the JSON file nor the prompt file contained any comment
directing developers to keep the two values in sync.

## Root Cause

Two anti-patterns combined:

1. **Presence test instead of value-equality test** — `Should Not BeNullOrEmpty` is
   appropriate for fields where the exact value is user-defined (e.g., a repo `id`).
   It is wrong for constants that must equal a specific hardcoded string. Presence
   tests cannot enforce equality invariants.

2. **Missing maintenance anchors** — when the same literal string appears in multiple
   files, each file should contain a comment explaining the coupling. Without anchors,
   the coupling is only visible to developers who already know about it.

This is distinct from the *derived-state-drift* pattern
(see `2026-03-30-derived-invariant-validation-in-schema-tests.md`) — there, the
problem is a computed value that diverges from its source data. Here, the problem
is two static constants that must stay equal across files with no automated enforcement
and no documentation of the dependency.

## Solution

### 1. Pin the test to the exact expected value

```powershell
# Presence test (weak — does not catch drift):
It "has schemaVersion field" {
    $json.schemaVersion | Should Not BeNullOrEmpty
}

# Value-equality test (strong — catches any mismatch):
It "schemaVersion equals expected constant" {
    $json.schemaVersion | Should Be 'compound-gpid-competitive-reviews-v1'
}
```

Keep the presence test if it serves as a schema-structural check, but always
add a separate value-equality test for any constant that appears in multiple files.

### 2. Add maintenance anchors in both files

In the JSON registry (`repos.json`), add a comment (in a comment field or in adjacent
documentation) explaining where the constant is consumed:

> The `schemaVersion` value is hardcoded in Step 1 of
> `.github/prompts/cg-review-repos.prompt.md`. Both must be updated together if the
> schema changes.

In the prompt file (`cg-review-repos.prompt.md`), add an inline note in the Step 1
validation section:

```markdown
> **Schema version sync**: The `schemaVersion` value in `repos.json` and the expected
> value checked here must always match. When bumping the schema version, update both
> files together.
```

### 3. Document the coupling in reference.md

In the user-facing documentation for the feature, add a schema version sync note to
the "Adding a new repo" instructions:

```markdown
The registry root must also include `"schemaVersion": "compound-gpid-competitive-reviews-v1"`.

> **Schema version sync**: The `schemaVersion` value in `repos.json` and the expected
> value hardcoded in Step 1 of `cg-review-repos.prompt.md` must always match.
> When bumping the schema version, update both files together.
```

## Prevention

**Code review heuristic**: when a schema test uses `Should Not BeNullOrEmpty` for a
field whose value is a hardcoded constant (e.g., `schemaVersion`), flag it as a test
quality issue. The test should use `Should Be '<exact-expected-value>'`.

**Pattern to follow** — three components whenever a constant appears in ≥ 2 files:

| Component | Where | What |
|-----------|-------|------|
| Value-equality test | `tests/` | `$json.schemaVersion \| Should Be 'compound-gpid-competitive-reviews-v1'` |
| Cross-file note in consumer | The prompt/script that reads the constant | `<!-- must match schemaVersion in repos.json — update together -->` |
| Reference doc coupling note | `docs/reference.md` or equivalent | Explicit sentence: "X and Y must stay in sync" |

**Corollary: prompt-embedded tables mirroring registry entries need maintenance anchors too.**

When a prompt file contains a table whose columns correspond to entries in a JSON
registry (e.g., a concept mapping table with one column per repo), add:

```markdown
<!-- Update this table when repos.json entries change. -->
```

This prevents column drift when repos are added or removed from the registry.

## Related

- [`2026-03-30-derived-invariant-validation-in-schema-tests.md`](./2026-03-30-derived-invariant-validation-in-schema-tests.md) — same root idea (stored value must match a recomputed value) but applies to *derived computed state*, not static constants
- [`2026-04-17-exact-count-assertion-prevents-silent-regression-when-test-name-states-count.md`](./2026-04-17-exact-count-assertion-prevents-silent-regression-when-test-name-states-count.md) — related: test assertions must precisely match what the test name claims
- [`2026-04-28-guard-test-vacuous-pass-when-mixed-array-has-static-member.md`](./2026-04-28-guard-test-vacuous-pass-when-mixed-array-has-static-member.md) — related: guard test checking a composite array (extracted + static) passes vacuously when extraction returns empty; always guard on the extracted variable, not the composite
