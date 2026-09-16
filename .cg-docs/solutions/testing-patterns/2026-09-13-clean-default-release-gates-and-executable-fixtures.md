---
date: 2026-09-13
title: "Release gates need clean default dependencies and executable fixture controls"
category: "testing-patterns"
language: "Python"
tags: [release-gates, uv, dependency-groups, fixtures, windows]
root-cause: "An optional dependency group masked a missing default test dependency, and an unverified mock executable failed before launcher argument capture"
severity: "P1"
plan: ".cg-docs/plans/2026-09-11-generic-asynchronous-release-controller.md"
reviewed-in: ".cg-docs/reviews/2026-09-12-generic-asynchronous-release-controller-phase6-verify-review.md"
---

# Clean Default Release Gates And Executable Fixtures

## Problem

Pipeline step 8 found one P1.1: the default full-package command could not collect
`test_profile_workflow_authority.py`, which imports `yaml`. A previously prepared
environment with the optional `gpid-native` group concealed the missing default
test dependency. The new isolated regression failed with
`ModuleNotFoundError: No module named 'yaml'`: 976 collected, one collection
error, inner exit 2.

Two real legacy-launcher checks also failed. A copied Bash fixture `pwsh.exe`
exited `3758096423` with empty streams before recording argv. The unchanged real
Bash launcher returned 127. These symptoms alone did not prove a product router
or argument-forwarding defect.

## Root Cause

The package's default `dev` group did not contain a dependency required to collect
its own tests. A lockfile or a warmed outer environment is not proof that the
documented default command can provision and collect the suite.

For the launcher fixture, the controlled construction change is verified, but
the lower-level Windows/CLR or host cause of the opaque startup exit is unknown.
Do not claim that all renamed .NET executables fail or that a host security
control caused this result.

## Solution

Add the existing `PyYAML==6.0.2` pin to `dev` in
`packages/cg-release/pyproject.toml`, and regenerate `uv.lock` offline. Leave the
same optional `gpid-native` pin and generic runtime dependencies unchanged. No
package version upgrade was needed.

The package-owned regression in `packages/cg-release/tests/test_install.py` uses
the actual `scripts/cg_pr_preflight.py` `FULL_PACKAGE_TEST_COMMAND`, adds
`--isolated` and `--collect-only`, and removes inherited Python/user-site and
virtual-environment contamination. It requires collection of the authority
test nodes without adding an optional group. The red run's outer optional group
did not satisfy the isolated child, which is the relevant boundary proof.

The installed-wheel check separately requires
`importlib.util.find_spec('yaml') is None` in its runtime-only environment. A
test dependency must not silently become a generic runtime dependency. Keep this
regression in the package suite; the native producer must not repeat package
pytest work.

For the Windows Bash fixture in `scripts/tests/release_shell_fixture.py`, compile
the same C# source to neutral `fixture.exe`, then copy it to the package
`python.exe` and mock `pwsh.exe`, as the CMD fixture already does. The neutral
direct control and unchanged real launcher returned the expected 37. Product
launchers, router code, exit expectations and argument assertions did not change.

`test_windows_fixture_executables_run_before_product_dispatch` directly runs both
mock names for CMD and Bash before product dispatch. It checks exit 37 and exact
empty, quoted, space-containing, ampersand and trailing-backslash arguments. Both
direct cases and both prior legacy cases now pass.

### Verified Evidence

The [step 9 triage report](../../reviews/2026-09-13-generic-asynchronous-release-controller-step9-fix-triage.md)
contains red results, the neutral-assembly probe, final source blob IDs, and the
qualified completion decision. Its immutable
[gate handoff](../../work-reports/release-controller/2026-09-13-step9-validation-180003Z-86e3cad4/handoff.json)
retains the earlier executor disposition without rewriting it.

| Check | Recorded Result |
|---|---|
| Clean default native launcher/producer/preflight selection | 90 passed, no failures or skips |
| Clean default authority/install selection | 32 passed, including 18 authority cases and isolated collection |
| Dedicated clean default full package | 995 passed, no failures, errors or skips |
| Dedicated unfiltered Pester | 2,935 passed, 0 failed, 2 skipped; 21 files |
| Ruff and offline lock consistency | Passed; 23 packages resolved |

The full package used `uv run --isolated --offline --project packages/cg-release
--locked python -B -m pytest packages/cg-release/tests -q --tb=short -p
no:cacheprovider`, with a new JUnit path and fresh short child `TEMP`/`TMP`.
It did not use `--no-sync` or select `gpid-native`. Cached distributions are not
a reused provisioned environment. Pester finished before package execution.
The focused cases overlap the full suite; do not add them as unique coverage.

Pester cleanup remained unsuccessful, with 615 diagnostic occurrences. Both
skips are in `update`, but their individual names/reasons are not retained.
This is qualified local fix-triage evidence, not independent step 9 review
convergence, a committed candidate gate, or native Unix/live qualification.

## Prevention

- Verify the exact default command in an isolated environment. Do not repair a
  missing test dependency by silently adding optional groups to the gate.
- Test package collection and runtime-only installation as separate contracts.
- Prove that fixture executables start and preserve argv before assigning a
  launcher failure to product code. Keep negative and positive controls.
- Preserve failed probes and state diagnosis limits. Do not weaken assertions,
  change host protection, or modify launchers to accommodate a broken fixture.
- Keep source identities with the gate result. `git diff --check` alone does not
  validate untracked file bytes or bind a dirty worktree to HEAD.

## Related

- [Fixtures must mirror runtime commands](2026-08-13-release-gate-fixtures-and-derived-evidence-hashes.md)
- [Authority and evidence boundaries](../git-workflows/2026-09-13-release-controller-authority-and-evidence-boundaries.md)
- [Short private GPG roots](../environment-issues/2026-09-13-windows-gpg-agent-socket-path-budget.md)
