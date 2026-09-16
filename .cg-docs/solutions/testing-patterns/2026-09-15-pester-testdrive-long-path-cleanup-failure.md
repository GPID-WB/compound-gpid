---
date: 2026-09-15
title: "Pester 4.10.1 TestDrive cleanup fails on Windows long paths; short process-local TEMP and owned-temp disposal are required"
category: "testing-patterns"
language: "both"
tags: [pester, powershell, windows, testdrive, long-path, temp, cleanup, full-gate, supervision]
root-cause: "Pester 4.10.1 Clear-TestDrive/Remove-TestDrive (Functions/TestDrive.ps1:42,146) cannot remove fixture trees deeper than ~260 chars under the default long C:\\Users\\...\\AppData\\Local\\Temp root, raising DirectoryNotFound/DirectoryNotEmpty exceptions; separate test helpers (cg-index pyfm-/pysum- helpers) write straight into process temp with no cleanup path"
severity: "P2"
plan: ".cg-docs/plans/2026-09-08-evidence-backed-cg-help-command.md"
related: [".cg-docs/solutions/testing-patterns/2026-03-04-pester-testdrive-follows-junctions-freezes-vscode.md", ".cg-docs/solutions/testing-patterns/2026-04-02-invoke-pester-full-suite-passthru-crashes-vscode.md", ".cg-docs/solutions/testing-patterns/2026-04-17-canonical-run-tests-json-artifact-decouples-test-results-from-agent-context.md", ".cg-docs/solutions/bugs/2026-08-17-windows-long-path-staged-publication.md"]
---

# Pester 4.10.1 TestDrive Cleanup Fails on Windows Long Paths; Short Process-Local TEMP and Owned-Temp Disposal Are Required

## Problem

The unfiltered full Pester gate passed its assertions but left fixture
directories behind. The supervised run of `2026-09-13T02:05:25Z` –
`02:08:14Z` (2,839 total / 2,837 passed / 0 failed / 2 skipped,
`filteredFiles: null`) also produced 192 genuine cleanup exception records:
78 `DirectoryNotFoundException`, 108 `IOException` ("The directory is not
empty"), and 6 `ItemNotFoundException`. They originate in Pester 4.10.1
`Functions/TestDrive.ps1:42` (131 records) and `:146` (61 records) during
`Clear-TestDrive` / `Remove-TestDrive`. Cleanup errors are NOT counted in
`failedCount`, so a green canonical artifact can coexist with unresolved
residue. Retained residue roots:
`<USER_HOME>\AppData\Local\Temp\3\4f28d182-c040-4660-b810-61cb788e293d`
(deepest path 267 chars) and
`<USER_HOME>\AppData\Local\Temp\3\f2436869-bcc9-4c79-908a-a5c9d3b53c32`
(deepest path 265 chars).

## Root Cause

Pester 4.10.1's normal-path TestDrive cleanup cannot remove fixture trees
whose paths exceed the Windows long-path boundary under the default
`C:\Users\...\AppData\Local\Temp` root. Additionally, the cg-index escaped
tests write helper files (`pyfm-*.py` x3, `pysum-*.py` x5) directly into
process temp (`tests/cg-index.Tests.ps1:432-439,477-484`, eight helper
cases) with no cleanup path, so even a clean Pester leaves runtime-owned
residue.

## Solution

1. **Short private process-local TEMP/TMP**: give the runner its own fresh
   child under `C:\Temp` (e.g. `C:\Temp\p6a4` setup worker,
   `C:\Temp\p7f2` full gate) with a private current-SID/SYSTEM DACL and
   no-reparse verification. Known fixture bounds dropped to 203 directory /
   241 file characters, margins 45/19 below the 248/260 limits. Never reuse
   or delete old private children.
2. **Supervise full-gate runs with independent control and streams**: exclusive
   start reservation, Windows kernel job, separate `stdout.raw` / `stderr.raw`,
   and residue classification before phase closure. The `2026-09-13T21:51:17Z` –
   `21:53:52Z` owned-resource run passed 2,839/2,837/0/2 yet still retained
   nine entries under `C:\Temp\p7f2`.
3. **Treat runtime-owned temp as owned and dispose manually under approval**:
   the retained helper residue is expected, deterministic behavior of the
   escaped tests, not a test failure. It was removed only after explicit
   user approval (`Approve cleanup and closure`) on `2026-09-14T12:28:39Z`
   via pinned no-follow `FileDispositionInfo` deletions of the ten exact
   targets, with after-absence verification (receipts
   `cg-p3-manual-cleanup-20260914-a81f37-bfcb3419a797.receipt.json`,
   `cg-p3-manual-final-20260914-d59b82-68eeb91b66.receipt.json` under
   `<USER_HOME>\AppData\Local\Temp\3\kilo`).

## Prevention

- Run full gates under a short process-local temp root and independent
  stdout/stderr control streams; never infer clean cleanup from assertion
  passes.
- Classify residue (TestDrive GUID vs direct-to-temp helper files) before
  closing a phase; runtime-owned temp residue is owned by the runner and
  must be disposed explicitly under approval.
- Keep long-path awareness for any Windows temp hierarchy
  (`\\?\` prefixing per the staged-publication lesson).

## Related

- `.cg-docs/solutions/testing-patterns/2026-03-04-pester-testdrive-follows-junctions-freezes-vscode.md` — TestDrive cleanup hazards on Windows
- `.cg-docs/solutions/testing-patterns/2026-04-02-invoke-pester-full-suite-passthru-crashes-vscode.md` — safe full-suite execution patterns
- `.cg-docs/solutions/testing-patterns/2026-04-17-canonical-run-tests-json-artifact-decouples-test-results-from-agent-context.md` — canonical runner + artifact pattern used by the supervised gate
- `.cg-docs/solutions/bugs/2026-08-17-windows-long-path-staged-publication.md` — Windows long-path handling in this repo