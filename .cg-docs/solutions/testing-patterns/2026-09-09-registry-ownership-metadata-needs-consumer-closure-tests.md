---
date: 2026-09-09
title: "Registry ownership metadata needs consumer-closure tests"
category: "testing-patterns"
language: "Python"
tags: [module-registry, ownership-exclusions, generated-targets, compatibility, fixtures, phase-gates]
root-cause: "A backward-compatible registry field was validated at its source but several consumers still used raw ownership globs, while generated-target drift tests assumed later-phase output was already committed."
severity: "P1"
---

# Registry ownership metadata needs consumer-closure tests

## Problem

Adding `ownershipExclusions` and the `cap-help` module passed focused schema and
catalog tests, but broader verification found failures and silent routing risks:

- catalog, lifecycle, CLI, and benchmark consumers still matched raw
  `ownedAssets` globs;
- legacy manifests were forced to contain a new optional field;
- unfiltered target scans derived suite closures that their fixtures did not
  declare;
- projection benchmarks did not compare the resolved owner with
  `expectedRoute`;
- generated-target drift tests expected Phase 5 help output during Phase 2.

The feature looked locally correct because its source validator was green. The
consumer closure was not green.

## Root Cause

Registry compatibility is not only a schema concern. Every reader that makes an
ownership, activation, removal, routing, or generation decision is part of the
contract. A raw glob such as this bypasses exclusions:

```python
any(glob_match(pattern, asset) for pattern in module["ownedAssets"])
```

The implementation also mixed two states in generated-output tests: sources
that are valid now and native artifacts whose integration is explicitly planned
for a later phase. Ordinary drift comparison then reported intentional deferred
output as current drift.

## Solution

Centralize effective ownership and use it in every decision:

```python
owners = matching_asset_owners(registry, asset)
owner = owners[0] if len(owners) == 1 else None
```

The shared resolver applies `ownedAssets` and `ownershipExclusions` together.
Consumers now require one resolved owner, verify that the owner is active when
needed, and compare it with route expectations.

Preserve backward compatibility at each serialized boundary. A missing optional
`ownershipExclusions` field in a legacy manifest means `{}`; it is not a parse
failure. Unfiltered target scans preserve their old behavior and derive suite
closure only when the caller supplies suite or module filters.

For phased generated output, use an explicit, exact deferred source set in the
drift fixture. Assert that the set contains only the approved Phase 2 sources,
that the not-yet-created public prompt is absent, and that deferred destinations
are excluded only from committed-output drift comparisons. This keeps Phase 2
green without generating or claiming Phase 5 artifacts.

The completed fix passed 446 focused Python tests with 23 environment skips and
the unfiltered Pester gate with 2,827 total tests and no failures.

## Prevention

- Search all registry consumers when adding an ownership field; source-schema
  validation is necessary but not sufficient.
- Prohibit direct `ownedAssets` matching outside the central registry service.
- Add a fixture where a broad owner excludes an asset and the replacement owner
  is outside the active closure.
- Test legacy documents without each newly optional field.
- Test filtered and unfiltered generator entry points separately.
- Require routing oracles to compare the unique resolved owner with the expected
  route.
- Represent later-phase generated output with a small exact deferral set, not a
  broad drift-test disable.
- Run focused feature tests and the broader consumer/target fixture matrix before
  closing a phase.

## Related

- `.cg-docs/solutions/environment-issues/2026-07-03-cross-agent-native-platform-trees-require-generator-drift-tests-consistent-python.md`
- `.cg-docs/solutions/bugs/2026-08-14-capability-eligibility-namespace-mismatch.md`
- `.cg-docs/plans/2026-07-27-canonical-native-packaging-foundation.md`
- `.cg-docs/plans/2026-08-28-scalable-skill-management-suite.md`
- `.cg-docs/reviews/2026-09-04-minimal-adaptive-grilling-verify-review.md`
