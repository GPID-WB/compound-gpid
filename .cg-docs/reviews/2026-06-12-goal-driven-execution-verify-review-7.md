---
date: 2026-07-05
depth: light
parent-review: .cg-docs/reviews/2026-06-12-goal-driven-execution-review.md
type: verification
findings:
  P1.1: fixed
  P1.2: fixed
  P1.3: fixed
  P2.1: fixed
  P2.2: fixed
  P2.3: skipped
---

# Goal-Driven Execution Review - Verification Pass 7

## Review Context

- **Mode**: verify (`mode:verify`; light depth)
- **Parent review**: `.cg-docs/reviews/2026-06-12-goal-driven-execution-review.md`
- **Branch**: `feat/cross-agent-native-trees`
- **Scope**: Convergence pass after fixing default-all multi-platform linking/update findings.

## Findings Fixed In This Pass

### P1 - Critical

**[P1.1]** [cg-code-quality] `scripts/helpers.ps1`, `scripts/update.sh` - Manifest-managed refresh trusted manifest paths when copying files.

**Fix applied**: Added containment checks for manifest source and target paths in PowerShell and bash refresh paths. Absolute paths and `..` escapes are rejected before hashing or copying.

**[P1.2]** [cg-code-quality] `scripts/helpers.ps1`, `scripts/update.sh` - Manifest containment checks did not reject symlink/reparse targets.

**Fix applied**: PowerShell refresh now skips source/target paths with reparse-point attributes; bash refresh skips symlink source/target paths. Added a regression test for symlink managed targets.

**[P1.3]** [cg-code-quality] `scripts/install.sh` - `--uninstall` removed wrappers that install did not recreate.

**Fix applied**: `install.sh` now regenerates the summary wrappers (`cg-diff-summary`, `cg-log-summary`, `cg-problems-summary`, `cg-test-summary`, `cg-tree-summary`) and the uninstall smoke test verifies uninstall followed by install restores every no-extension `bin/cg-*` wrapper.

### P2 - Important

**[P2.1]** [cg-testing] `tests/link.Tests.ps1` - Stale `.cg-docs/` gitignore cleanup tests were detached from production.

**Fix applied**: Restored production stale `.cg-docs/` cleanup in both `link.ps1` and `link.sh`, with regression guards asserting the production cleanup exists.

**[P2.2]** [cg-testing] `scripts/tests/test_update_generates_targets.py` - Direct-`python3` negative assertions were too narrow.

**Fix applied**: Replaced exact-string checks with a command-line regex that bans direct executable `python3` invocations while allowing candidate-probe loops; applied to committed wrappers and install-generated wrapper templates.

**[P2.3]** [cg-testing] `tests/bash-scripts.Tests.ps1` - Bash manifest containment did not have behavior-level coverage.

**Status**: Partially mitigated. The bash path now has explicit `contained_path()` and symlink rejection logic, and the PowerShell production helper has behavioral coverage for traversal and symlink targets. Full bash execution coverage remains a residual test-depth gap because `update.sh` is a full updater script rather than an extracted helper.

## Verification

- `python3 -m pytest scripts/tests` -> `259 passed`
- Safe targeted Pester via `tests/Run-Tests.ps1`:
  - `bash-scripts`: `93 passed`
  - `update`: `125 passed`
  - `link`: `1 passed` (macOS placeholder)
  - `parity`: `22 passed`
- Full safe Pester gate via `tests/Run-Tests.ps1`: `2227 passed`, `0 failed`

## Summary

All P1 findings from the convergence review were fixed and regression-tested. One residual P2 test-depth gap remains noted for future extraction of the bash manifest-refresh helper, but current behavior is guarded by source checks and the PowerShell production helper tests.
