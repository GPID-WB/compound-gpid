---
date: 2026-09-17
title: "Documented quarantine skip marker for time-boxed flake root-causes, never a silent skip"
category: "testing-patterns"
language: "Python"
tags: [flaky-test, quarantine, skip-marker, timebox, ci-noise]
root-cause: "A single unreproducible macos-py3.11 transport failure (E_PROCESS_ARGUMENT in a shared prepare helper) would keep blocking merges indefinitely while the root cause stayed a suspected real-process boundary."
severity: "P2"
plan: ".cg-docs/plans/2026-09-16-cg-release-prerelease-automation.md"
---

# Documented Quarantine Skip Marker For Flakes

## Problem

`test_lost_response_and_unreadable_observation_remain_unknown_until_fresh_recovery
[asset-package.whl]` failed once on macos-latest-py3.11 with
`E_PROCESS_ARGUMENT` inside the shared `prepare()` helper of the strict fake
transport tests, while passing in four other runs. One contradictory CI
signal can block merges indefinitely, and a silent `skip` would hide a
possible real bug.

## Root Cause

Audit: `E_PROCESS_ARGUMENT` is raised only by the real
`process.run_process`/`profile_process._capture` validation. In `prepare()`
every GH/Git call is monkeypatched to `world.run` except `apply_edits`
(reached via controller `advance` -> `prepare_step`), which executes a real
`git` subprocess in a `TemporaryDirectory` while mixing the strict fake
clocks with a real `time.monotonic()` deadline. That real-subprocess boundary
is the only plausible source; it is order/environment dependent and not
reproducible on win32. The fake transport's time/seed inputs were already
explicit and fixed, so no test-side determinism change could remove the
variance without changing production preparation semantics.

## Solution

The plan-mandated outcome for an inconclusive time-boxed root-cause:
quarantine with a documented skip marker. The skips carry:

- the `@pytest.mark.skip(reason=...)` text with the exact failure signature,
- the suspected real-process boundary (`apply_edits` git under strict fake
  clocks),
- a reference to this work report (`.cg-docs/work-reports/2026-09-17-cg-release-prerelease-automation.md`) for the audit trail.

The quarantine was verified stable across the focused rerun (29 passed, 4
quarantined skips, 0 failed) and the full package uv matrix (1010 passed, 4
R7 skips plus 1 symlink skip), so the package matrix stopped blocking merges
on this noise. Reproduction attempts remain possible by running the
quarantined test against the pre-quarantine commit; the quarantine does not
weaken any other assertion.

## Prevention

- Time-box the root-cause first; the quarantine is a documented last resort,
  never the first response.
- A skip marker is quarantine only if it records the failure signature, the
  suspected cause/boundary, and a run-link or report reference — never a
  bare `skip`/`@skip("flaky")`.
- Verify quarantine stability in the full matrix before claiming the CI
  noise is resolved; if the quarantined test would catch a real regression,
  keep a sibling path that still exercises the boundary.
- Do not claim a root-cause result the audit did not reach: "inconclusive
  after audit" is a valid, recorded outcome when the plan allows quarantine.

## Related

- `.cg-docs/solutions/testing-patterns/2026-06-09-external-validation-must-not-be-marked-passed.md`
- `.cg-docs/solutions/git-workflows/2026-09-13-release-controller-authority-and-evidence-boundaries.md`
- `.cg-docs/plans/2026-09-16-cg-release-prerelease-automation.md`