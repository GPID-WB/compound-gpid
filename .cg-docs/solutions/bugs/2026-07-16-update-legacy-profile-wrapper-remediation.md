---
date: 2026-07-16
title: "Updater remediation for legacy CLM-prone PowerShell profile wrappers"
category: "bugs"
type: "bug"
language: "both"
tags: [powershell, clm, profiles, encoding, updater]
root-cause: "Early installs left cg-* functions in the PowerShell profile that dot-sourced scripts from an untrusted path, while the updater only cleaned the profile during installation and rewrote files with potentially lossy encoding defaults."
severity: "P1"
test-written: "yes"
fix-confirmed: "yes"
---

# Updater remediation for legacy CLM-prone PowerShell profile wrappers

## Problem

On enterprise Windows machines using Constrained Language Mode (CLM), an old
Compound GPID profile function such as `cg-link` could fail with:

```
Cannot dot-source this command because it was defined in a different language mode.
```

The current installer removed the old functions, but updater-only users did not
necessarily run the installer again. A cleanup that used `Get-Content` and
`Set-Content` defaults could also change a profile's encoding, BOM, or non-ASCII
content.

## Root Cause

Legacy releases emitted one-statement `cg-link`, `cg-unlink`, and `cg-update`
functions directly into `$PROFILE`. Those functions shadowed the newer PATH
`.cmd` wrappers and directly dot-sourced the PowerShell scripts. Cleanup was
duplicated in the installer and was too broad to safely distinguish a managed
wrapper from a customized function. PowerShell content cmdlets also do not
provide a reliable round trip for all profile encodings on Windows PowerShell
5.1.

An updater that is already running cannot execute code added by a `git pull`
later in the same process. This means a process started from a pre-remediation
updater may require a second run after the pull; the limitation is documented
rather than hidden.

## Solution

Centralize profile remediation in `scripts/helpers.ps1`:

- `Read-CgProfileText` detects UTF-8, UTF-16, UTF-32, and ANSI bytes and keeps
  the original preamble/BOM.
- `Write-CgProfileText` writes bytes using the detected encoding and preamble.
- `Get-CgLegacyProfilePatterns` matches only the exact one-statement wrappers
  for the three Compound GPID commands, including `&` and dot-source forms.
- `Remove-LegacyProfileCommands` removes the managed block and exact legacy
  wrappers while preserving unrelated profile content and customized
  functions.

Both `install.ps1` and `scripts/update.ps1` use the shared helper. After file
cleanup, they remove a live function only when its current definition still
matches the exact legacy wrapper. A customized live function is preserved and
reported to the user. If no matching function is loaded (for example, the
wrapper is being inspected from a `-NoProfile` process), no misleading warning
is emitted.

The byte-preserving cleanup path intentionally requires FullLanguage mode
because its .NET file and encoding APIs are blocked in Constrained Language
Mode. In CLM the helper fails before changing the profile; the
installer/updater reports the warning and directs the user to run the
no-profile PATH wrapper or remove the exact legacy function manually. This
avoids silently rewriting a profile with a lossy encoding fallback.

## Verification

Regression coverage in `tests/install.Tests.ps1` and `tests/update.Tests.ps1`
checks:

- exact wrapper matching, global-scoped definitions, and dot-source forms;
- preservation of customized functions and unrelated comments/functions;
- live-session cleanup without deleting customized commands;
- UTF-8 with and without BOM, UTF-16LE/BE, UTF-32LE/BE, active Windows ANSI
  code-page fallback on Windows PowerShell 5.1 and PowerShell 7 on Windows,
  exact encoding-name detection, BOM preservation, CRLF/LF line-ending
  preservation, and non-ASCII round trips;
- the shared helper integration in both installer and updater.

The latest complete safe local-worktree Pester run passed with **2267 passed,
0 failed, and 0 skipped** (`2267` test cases discovered) and
`filteredFiles: null` in `tests/last-run.json`. The update file reported 135
cases with 135 passed. The generated artifact is ignored and records the
current `HEAD`, not the dirty worktree contents, so the result is a local
verification record rather than a commit-level test receipt.

## Prevention

- Keep user-facing command launchers as PATH `.cmd` wrappers when CLM can
  restrict profile dot-sourcing.
- Centralize profile byte/encoding handling; do not replace a profile with
  default `Get-Content`/`Set-Content` round trips.
- Match and remove exact managed definitions, not command names alone.
- Treat code pulled by an updater as unavailable to the already-running
  process; document or explicitly re-execute when a migration depends on new
  updater code.
- Run the canonical full suite through `tests/Run-Tests.ps1` and inspect
  `tests/last-run.json` before release.

## Related

- [Related installer idempotency solution](2026-06-25-install-self-copy-wrapper-crash.md)
- [PS 5.1 strict-mode compatibility](2026-05-18-ps51-strict-mode-iswindows-variable-not-set-crash.md)
