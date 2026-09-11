---
date: 2026-09-09
title: "Validate registry identities before building derived maps"
category: "data-quality"
language: "Python"
tags: [registry, identity, validation, derived-map, workflow-audit, regression-test]
root-cause: "The registry validator checked IDs and paths only after a command-keyed dictionary had already been built, so duplicate command names could silently replace one entry and evade guardrails."
severity: "P2"
---

# Validate Registry Identities Before Building Derived Maps

## Problem

A workflow registry had three identity fields: `workflow_id`, `workflow`, and
`path`. Validation rejected duplicate IDs and paths, but accepted duplicate
`workflow` command names. A dictionary keyed by `workflow` was built before the
validator ran, so Python kept only the last duplicate without an error. Derived
high-frequency prompt checks could then omit one registered source path.

The related prompt tests had a similar weakness: they checked that H/S gate row
labels existed, but did not verify each row's complete route or threshold.

## Root Cause

Validation was incomplete and too late. It did not prove that each row was a
mapping with three non-empty strings, did not enforce uniqueness for every
identity field, and ran only when later telemetry was built. The derived map had
already lost information by then.

Label-only table assertions also proved structure without proving semantics.

## Solution

Define the registry validator before the registry-derived constants and call it
immediately after the canonical registry tuple:

```python
validate_workflow_registry(WORKFLOW_REGISTRY)
BENCHMARK_PROMPTS = {
    row["workflow"]: row["path"]
    for row in WORKFLOW_REGISTRY
}
```

The validator now requires every row to be a mapping, requires
`workflow_id`, `workflow`, and `path` to be non-empty strings, and tracks three
independent uniqueness sets. Duplicate command names raise a stable
`Duplicate workflow command` error before any keyed map is created.

Negative pytest fixtures cover duplicate IDs, commands, paths, non-mapping rows,
non-string values, and whitespace-only values. Pester table tests compare each
complete H1-H7 and S1-S10 row against a table-driven expected value instead of
checking labels alone.

Verification completed with 108 audit tests passed and 1 platform skip,
1,696 focused Pester checks passed, and an unfiltered Pester gate with 2,863
passed, 0 failed, and 2 skipped.

## Prevention

- Validate all identity fields before constructing sets, dictionaries, indexes,
  caches, or projections from registry data.
- Test each field's duplicate case independently; do not infer full identity
  coverage from one unique field.
- Reject malformed types and blank strings at the registry boundary.
- For policy tables, assert complete normalized rows or parsed field values.
  Label-presence tests do not protect routes, limits, or safety semantics.
- Keep the validator call adjacent to the canonical registry and before every
  derived constant so later refactors cannot reverse the order silently.

## Related

- `.cg-docs/reviews/2026-08-28-scalable-skill-management-suite-verify-review-3.md`
- `.cg-docs/plans/2026-09-04-cg-light-work-unified-small-task-workflow.md`
- `.cg-docs/solutions/testing-patterns/2026-03-30-derived-invariant-validation-in-schema-tests.md`
- `.cg-docs/solutions/testing-patterns/2026-05-15-common-word-regex-false-positive-in-security-assertions.md`
- `.cg-docs/solutions/testing-patterns/2026-05-01-regex-alternation-masks-coverage-split-into-independent-assertions.md`
