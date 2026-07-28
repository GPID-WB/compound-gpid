---
date: 2026-07-28
depth: light
parent-review: .cg-docs/reviews/2026-07-28-canonical-native-packaging-foundation-review.md
type: verification
findings:
  P0.1: fixed
  P0.2: fixed
  P0.3: fixed
  P0.4: fixed
  P1.1: fixed
  P1.2: fixed
  P1.3: fixed
  P1.4: fixed
  P1.5: fixed
---

# Canonical-to-Native Packaging Foundation Verification Review

## Review Report

**Review mode**: light verification
**Files reviewed**: 8
**Findings**: 9 (P0: 4, P1: 5, P2: 0, P3: 0)

### P0 - BLOCKING

**[P0.1]** `cg-code-quality` - `scripts/cg_generate_targets.py:1212` - Destination ancestor revalidation remains vulnerable to a TOCTOU symlink race. The pathname check is separated from directory creation, replacement, stat, and chmod. Use verified no-follow directory handles for mutation.

**[P0.2]** `cg-code-quality` - `scripts/cg_generate_targets.py:1222` - Stale-file ownership verification remains separated from deletion. Verify identity and unlink relative to the same retained no-follow directory handle.

**[P0.3]** `cg-testing` - `scripts/tests/test_target_ownership.py:232` - The destination race test swaps before revalidation rather than after it, so it does not exercise the final write window. Inject replacement at the write boundary.

**[P0.4]** `cg-testing` - `scripts/tests/test_target_ownership.py:232` - The stale cleanup test does not exercise replacement after the final hash and before unlink. Inject replacement at the unlink boundary and verify it survives.

### P1 - CRITICAL

**[P1.1]** `cg-code-quality` - `create-release.ps1:77` - Tag and cleanliness checks run in the caller's repository. Execute all repository-sensitive Git commands with `git -C $PSScriptRoot` and test the argument.

**[P1.2]** `cg-code-quality` - `scripts/tests/test_update_generates_targets.py:73` - The updater integration fixture is POSIX-specific and unsafe on Windows CI. Mark it POSIX-only or provide native shims and add equivalent PowerShell coverage.

**[P1.3]** `cg-code-quality` - `scripts/tests/test_release_gate_targets.py:36` - Release fixture command interception is not reliable on Windows. Use platform-native shims or POSIX gating plus Windows-native coverage.

**[P1.4]** `cg-testing` - `scripts/tests/test_update_generates_targets.py:66` - The downstream mutation assertion is vacuous because the sentinel is unmanaged and `CG_INTERNAL_CALL=1` suppresses refresh. Use a real managed manifest and destination without suppression.

**[P1.5]** `cg-testing` - `scripts/tests/test_update_generates_targets.py:94` - PowerShell updater failure scenarios remain source-only. Execute `update.ps1` in isolated fixtures and assert failure before managed-output mutation.

## Passed

- Python regression suite: 456 passed before verification review.
- Pester full-suite gate: passed with zero failures before verification review.
