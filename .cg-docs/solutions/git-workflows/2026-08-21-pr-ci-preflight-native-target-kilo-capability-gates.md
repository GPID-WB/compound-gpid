---
date: 2026-08-21
title: "Authoritative PR preflight prevents native-target and Kilo capability reruns"
category: "git-workflows"
language: "both"
tags: [ci, pull-request, preflight, native-targets, module-registry, cache-hygiene, kilo, capability, base-branch, actions-job, pester]
root-cause: "Local commit and PR workflows owned divergent test lists, guessed base revisions, treated Kilo host absence ambiguously, and repaired CI without exact job or clean-worktree evidence."
severity: "P1"
plan: ".cg-docs/plans/2026-08-21-pr-ci-preflight-and-kilo-capability-gates.md"
reviewed-in: ".cg-docs/reviews/2026-08-21-pr-ci-preflight-and-kilo-capability-gates-verify-review.md"
verified-in: "PR #141"
---

# Authoritative PR Preflight Prevents Native-Target And Kilo Capability Reruns

## Problem

PR #141 exposed several failures that local guidance did not catch before a
remote run: interpreter cache files could enter generated skill inventories,
active-suite filtering could disagree with projection roots, generic CI could
imply Kilo integration without a Kilo host, PR repair could inspect an
unrelated latest Actions run, and auto-fix could operate without a clean
worktree or exact PR base.

## Root Cause

The commit, verify, generator, projection, and CI workflow each owned pieces of
the release gate. Their duplicated lists and implicit fallbacks drifted. In
particular, `origin/HEAD` was not the actual PR base, `gh run list --limit 1`
could select the wrong job, and a missing Kilo executable was not a typed
capability result. Generated trees are committed product surfaces, so a local
prepare check also needs to distinguish uncommitted generated output from a
committed HEAD drift check.

## Solution

- `scripts/cg_pr_preflight.py` is the single Python 3.8+ stdlib-only selector
  and runner. It classifies changed files, resolves explicit PR/push history,
  reports bounded cache provenance, runs one ordered native pytest command with
  `-m "not integration"`, and executes dependency, cross-suite, and ownership
  module gates.
- Prepare mode validates native and module behavior without requiring the
  generated-tree HEAD comparison; committed mode includes the drift test.
  Both modes fail visibly on missing history and use an explicit full-gate
  fallback for a zero push-before revision.
- Generated skill inventory rejects regular `.pyc` files, preserves the
  `__pycache__` exclusion, rejects cache paths in ownership manifests, and
  rejects unowned registered-mode skill directories. Generator and
  manifest-driven projection fixtures compare CG-only and CG+CR membership.
- The preflight adapter preserves `cg_kilo_preflight.py` statuses and evidence.
  Generic host absence is `generic-not-applicable`; certified success and
  blocking configuration/content/containment outcomes remain distinct.
- CI passes the pull-request base SHA or push-before SHA, never `origin/HEAD`.
  Generic E2E consumes an always-on neutral Kilo capability report. The
  certified-host job is limited to protected default-branch pushes or matching
  manual dispatch, uses a protected environment and trusted checkout, verifies
  the observed version and executable SHA-256, and runs integration-marked
  evidence only after the check.
- `/cg-commit-push-pr` resolves one base before staging, runs prepare and
  committed preflights, and propagates the base to `gh` and extension PR paths.
  `/cg-verify-pr` reads each failed check's exact `detailsUrl`, requires run and
  job IDs, uses `gh run view --job --log-failed`, halts on dirty worktrees, and
  creates at most one targeted trailer-bearing `fix(ci)` commit per PR round.

## Prevention

- Keep native pytest ownership in `cg_pr_preflight.py`; do not duplicate the
  authoritative file list in workflows or prompts.
- Treat `__pycache__` and `.pyc` as local noise only when they are untracked
  and absent from manifests. Fail closed when Git provenance cannot be checked.
- Use the actual PR `baseRefName` for every comparison, fetch, merge-base,
  preflight, rebase, and PR creation operation.
- Never infer a failed Actions job from workflow name or recency. Require the
  exact run/job URL and use a manual provider route when it is unavailable.
- Run Pester only through `tests/Run-Tests.ps1` and consume
  `tests/last-run.json`; generated targets must be regenerated and committed
  before the committed drift gate.
- Treat missing certified-host configuration as explicit not-applicable
  evidence, never as proof of Kilo functional correctness.

## Verification

The implementation was committed and pushed to PR #141 against `dev`.
Committed drift passed 18 tests. The committed preflight passed 1,588 native
tests with 16 skipped and 2 integration deselections, followed by all three
module validators. Remote checks for Windows/macOS native gates, Windows/macOS
Pester, browser evidence, link-check, docs staleness, and title lint passed.
The certified-host job was skipped by its protected configuration boundary,
while the always-on generic Kilo capability report passed with
`generic-not-applicable` and explicitly recorded that no real-host integration
ran.

## Related

- `.cg-docs/plans/2026-07-27-canonical-native-packaging-foundation.md`
- `.cg-docs/solutions/environment-issues/2026-08-14-kilo-contained-launch-and-no-follow-copy.md`
- `.cg-docs/solutions/bugs/2026-08-20-kilo-cross-adapter-skill-autodiscovery.md`
- `.cg-docs/solutions/testing-patterns/2026-04-17-canonical-run-tests-json-artifact-decouples-test-results-from-agent-context.md`
- `scripts/cg_pr_preflight.py`
- `.github/workflows/tests.yml`
