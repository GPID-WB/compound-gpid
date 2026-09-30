---
date: 2026-09-15
title: "Runner harness leaking Set-StrictMode or ErrorActionPreference into the canonical Pester scope invalidates full-gate results"
category: "testing-patterns"
language: "both"
tags: [pester, powershell, harness, isolation, strictmode, erroractionpreference, full-gate, run-tests]
root-cause: "A supervisor worker that dot-sources tests\\Run-Tests.ps1 while Set-StrictMode or $ErrorActionPreference='Stop' is set in the same script scope propagates those settings into the canonical runner and every Pester test scope, producing mass invalid failures that vanish when the harness is clean"
severity: "P1"
plan: ".cg-docs/plans/2026-09-08-evidence-backed-cg-help-command.md"
related: [".cg-docs/solutions/testing-patterns/2026-04-02-invoke-pester-full-suite-passthru-crashes-vscode.md", ".cg-docs/solutions/testing-patterns/2026-04-17-canonical-run-tests-json-artifact-decouples-test-results-from-agent-context.md", ".cg-docs/solutions/bugs/2026-05-18-ps51-strict-mode-iswindows-variable-not-set-crash.md"]
---

# Runner Harness Leaking `Set-StrictMode` or `ErrorActionPreference` Into the Canonical Pester Scope Invalidates Full-Gate Results

## Problem

Two supervised full-gate attempts were invalidated by harness contamination
of the canonical Pester scope:

1. **StrictMode leak** — `2026-09-14T19:29:01Z` – `19:32:15Z`, osExit 1:
   159 invalid failures with exclusive StrictMode signatures (`The property
   'Count'/'Name'/'schemaVersion'/'githubIssues' cannot be found`, `The
   variable '$IsMacOS'/'$Version'/... cannot be retrieved because it has
   not been set`) across roadmap (51), pester-safety (76), bash-scripts (1),
   cg-index (12), update (9), and link (10). Cause: the generated worker set
   `Set-StrictMode -Version Latest` in the canonical scope before
   dot-sourcing `tests\Run-Tests.ps1`.
2. **`$ErrorActionPreference='Stop'` leak** — fullgate2 `2026-09-14T20:18:37Z` –
   `20:22:16Z`, osExit 1: 14 failures (cg-index 12, link 2) with
   `NativeCommandError` signatures because native-command stderr surfaced as
   a terminating error when `2>&1` was used under EAP Stop.

In both cases the same files had run green under the clean Phase 3 worker
(2,837/2,839 passed), proving the failures were harness artifacts, not
worktree regressions.

## Root Cause

The supervisor worker executed `. tests\Run-Tests.ps1` by dot-sourcing it
(`.`), so the worker's script scope IS the canonical runner scope. Any
preference or mode set earlier in that scope (strict mode, error action,
debug, or other setup assignments) propagated into `Run-Tests.ps1` and every
Pester test scope launched from it.

## Solution

- The worker generator never sets `Set-StrictMode`, `$ErrorActionPreference`,
  `Set-PSDebug`, or any other preference/setup assignment at canonical scope;
  exactly one canonical `. tests\Run-Tests.ps1` line is generated.
- A `verify_worker_isolation()` check runs before every launch and asserts
  the generated worker contains NO `Set-StrictMode`, NO
  `$ErrorActionPreference`, NO `Set-PSDebug`, and no other preference/setup
  assignments, and exactly one canonical run line.
- The corrected isolated run (fullgate3, `2026-09-14T20:41:57Z` –
  `20:45:24Z`) passed: osExit 0, 2,845 total / 2,843 passed / 0 failed /
  2 skipped, `filteredFiles: null`, all 19 rows green.

## Prevention

- Keep all verification helpers, supervisor state, and preferences OUT of
  the clean runner process; the runner scope must be pristine.
- Prove isolation before launch with an automated worker-content assertion,
  not by inspection after a failed run.
- When a full gate fails with a homogeneous failure cluster matching
  preference/scope signatures, treat the harness as the suspected cause and
  verify against a clean-run baseline before labeling the worktree.

## Related

- `.cg-docs/solutions/testing-patterns/2026-04-17-canonical-run-tests-json-artifact-decouples-test-results-from-agent-context.md` — canonical runner consumption pattern
- `.cg-docs/solutions/testing-patterns/2026-04-02-invoke-pester-full-suite-passthru-crashes-vscode.md` — safe Pester execution rules
- `.cg-docs/solutions/bugs/2026-05-18-ps51-strict-mode-iswindows-variable-not-set-crash.md` — StrictMode crash class on PS 5.1