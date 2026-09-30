---
date: 2026-08-26
title: "Release drift ignore checks spawn thousands of Git processes"
category: "bugs"
type: "bug"
language: "Python"
tags: [release, performance, git, check-ignore, subprocess, drift-gate, prerelease]
root-cause: "The release drift gate invoked git check-ignore separately for every generated path and repeated the traversal across assertions."
severity: "P2"
test-written: "yes"
fix-confirmed: "yes"
red-phase-confirmed: "yes"
expected-behavior-source: "user-requirement"
test-gap: "missing-test"
---

# Release Drift Ignore Checks Spawn Thousands of Git Processes

## Symptom

The `/cg-release` packaging gate took more than 20 minutes in the full workflow.
The native packaging test portion alone took 405.57 seconds, delaying release
confirmation and increasing the chance that the shell timeout would trigger a
redundant rerun.

The same release attempt also exposed stale `main`-only prompt text, even though
the current canonical and generated release commands already map four-component
prerelease tags to `dev`.

## Expected Behavior Source

User requirement -- four-component tags such as `v1.2.0.9010` must be publishable
as GitHub prereleases directly from a clean `dev` checkout, and the release gate
must run efficiently without weakening generated-target drift validation.

Specifically, ignore-state evaluation for the 1,238 expected generated paths
should use a bounded batch operation rather than starting one Git process per
path. Every materialized release command must retain the `prerelease -> dev`
branch policy.

## Root Cause

`scripts/tests/test_target_drift.py` used `_is_git_ignored()` inside set
comprehensions. The helper ran `git check-ignore --quiet` once for every expected
generated path. Two drift assertions repeated the same filtering, producing up
to 2,476 Git subprocesses before generated content validation began.

The release-policy tests checked the canonical prompt but did not directly
assert the branch policy across all materialized command projections. That gap
did not cause the performance problem, but it made stale command materialization
harder to distinguish from a current source regression.

## Reproduction Test

`scripts/tests/test_target_drift.py::test_git_ignore_checks_are_batched` requires
one NUL-delimited `git check-ignore --stdin -z` invocation for multiple paths.
Before the fix it failed with:

```text
NameError: name '_git_ignored_paths' is not defined
```

## Test Gap

`missing-test` -- drift correctness was covered, but no test constrained the
number of subprocesses used to evaluate ignore state. A correct final result
therefore hid an unnecessarily expensive N+1 process-spawning implementation.
The release-policy suite also lacked a fast assertion over every generated
command surface.

## Fix

The drift gate now sends all expected paths through one NUL-delimited Git query
and caches the resulting ignored-path set across assertions:

```python
result = subprocess.run(
    ["git", "check-ignore", "--stdin", "-z"],
    input="".join(f"{path}\0" for path in paths),
    ...,
)
```

Nonzero results other than Git's normal `0` and `1` outcomes remain blocking.
The release-policy suite now verifies the `prerelease -> dev` contract in the
canonical, Kilo, Claude, Codex, and OpenCode release commands.

The exact packaging gate improved from 405.57 seconds to 237.24 seconds, a
41.5 percent reduction. It passed 262 tests with 10 skips; the release-policy
suite passed five additional tests.

## Lessons Learned

For repository-wide metadata checks, prefer one bounded batch subprocess over
per-path process spawning. Correctness tests must include a resource-shape
contract when an implementation can silently become N+1 at realistic project
size. The `missing-test` gap allowed thousands of subprocesses because tests
asserted only the final ignored-path result, not how efficiently it was derived.

Cross-adapter workflow policy should also have one fast test over every
materialized command surface. This separates stale host/session content from a
current canonical-source regression before release work begins.

## Related

- `.cg-docs/solutions/bugs/2026-08-14-pages-immutable-ref-gate-rejects-dev-series-pre-release-tags.md`
