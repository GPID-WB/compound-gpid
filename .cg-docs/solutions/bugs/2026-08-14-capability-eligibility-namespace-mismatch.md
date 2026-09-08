---
date: 2026-08-14
title: "Capability suite-eligibility namespace mismatch makes activation dead code"
category: "bugs"
language: "Python"
tags: [capability-selection, module-registry, dead-code, silent-fallback, manifest, eligibility, namespaces]
root-cause: "Suite-eligibility logic intersected resolved module ids (suite-cg) against user-facing names (cg), so the branch was permanently empty and capabilities silently never activated."
severity: "P1"
---

# Capability suite-eligibility namespace mismatch

## Problem

The v2 module registry introduced `capabilities[]` records with
`supportedSuites` (user-facing names like `cg`/`cr`) and two activation paths:
selector-driven (`configSelectors` + config) and suite-eligible (empty
`configSelectors`, activated when a supported suite is active). The suite-eligible
branch was dead: `bool(supported & active)` was always `False`, so `pester`,
`git-workflow`, `research-output`, etc. were never activated through the
capability layer. This was masked because the owning modules also remained in
each suite's `dependsOn`; after pruning blanket suite dependencies (Step 4 of
the manifest-driven skill-loading plan) it would have silently dropped them.

Symptom: `selection.derivedCapabilities` in the active manifest under-reported to
`[]`, and a maintainer relying on `supportedSuites` got silent non-loading with
no error.

## Root Cause

Two different namespace forms were compared:
`resolve_active_suite_ids(...)` returns module ids (`{"suite-cg", "suite-cr"}`),
while capability records store the user-facing names (`{"cg", "cr"}`). The
intersection of those two sets is always empty. The same data-model mismatch also
broke the structural validator's derived closure, which passed module ids when
the resolver expected user-facing names.

A second, related defect: capability capability records declared platform
`"claude"` while the canonical id in `target-mapping.json` is `"claude-code"`.
The eligibility comparator never matches, so `platformEligibility.allEligible`
reported `False` on the default manifest — again a silent, datum-level mismatch.

## Solution

- Normalize on one namespace: `_capability_eligible(capability, active_suites, config)`
  now intersects `supportedSuites` against the **user-facing** active suite set and
  requires selector match AND suite eligibility (additive, never subtractive) —
  `scripts/cg_context_budget.py`.
- The structural reference closure (`cg_validate_modules._derived_capability_ids_for`)
  computes the derived set per module with the module's own user-facing suite
  context (a suite only sees capabilities it is eligible for), keeping
  suite-boundary enforcement intact.
- Canonical platform ids are the single source of truth: registry `supportedPlatforms`
  changed to `claude-code`, matching `target-mapping.json`.
- Defensive checks: unknown explicit capability names, capabilities without an
  `owningModule`, undeclared owning modules, unknown platforms, and a
  non-supported `config-schema-version` all fail loudly (no silent no-op).

## Prevention

- Compare identifiers in exactly one canonical namespace; when two layers model
  the same concept (user-facing name vs. module id), add a mapper and a test that
  proves the branch fires (e.g. assert `derivedCapabilities` lists a suite-eligible
  capability when its suite is active).
- Never rely on a second mechanism (a copy of the data via `dependsOn`) to mask a
  dead activation branch — test the activation path directly.
- Keep platform/capability ids canonicalized in one artifact and validate
  cross-references (`supportedPlatforms` vs `target-mapping.json` ids) so a typo
  produces an ineligibility verdict instead of silence.

## Related

- `.cg-docs/plans/2026-08-13-manifest-driven-skill-loading.md` (Steps 3-5)
- `docs/configuration.md` (strict config grammar and active-manifest fields)
- `scripts/cg_context_budget.py`, `scripts/cg_project_manifest.py`
