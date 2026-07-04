---
date: 2026-06-25
title: "install.ps1 self-copy wrapper crash when source equals destination"
category: "bugs"
type: "bug"
language: "both"
tags: [install, powershell, wrappers, copy-item, idempotency, windows]
root-cause: "install.ps1 attempted Copy-Item where source and destination resolved to the same canonical path, triggering a self-overwrite IOException under strict stop behavior."
severity: "P2"
test-written: "yes"
fix-confirmed: "yes"
red-phase-confirmed: "yes"
expected-behavior-source: "user-requirement"
test-gap: "edge-case-gap"
---

# install.ps1 self-copy wrapper crash when source equals destination

## Symptom
Running install.ps1 on a canonical install layout failed during wrapper registration with:

Copy-Item : Cannot overwrite the item ...\bin\cg-index.cmd with itself.

The install stopped before completion.

## Expected Behavior Source
User requirement.

The expected behavior is that installation remains idempotent and does not fail when wrapper source and destination resolve to the same file path. In that case, the installer should treat the operation as already satisfied and continue.

## Root Cause
The wrapper copy logic built both source and destination paths inside the same bin directory:

- Source pattern: Join-Path $CompoundGpidDir "bin\<wrapper>.cmd"
- Destination pattern: Join-Path $binDir "<wrapper>.cmd"

Because $binDir is Join-Path $CompoundGpidDir "bin", both paths can be identical. Copy-Item then attempted a self-copy and raised an IOException.

## Reproduction Test
Regression tests were written in tests/install.Tests.ps1:

- does not throw when cg-index.cmd source and destination are the same path
- does not throw when cg-brain-init.cmd source and destination are the same path
- does not throw when cg-token-audit.cmd source and destination are the same path

Red phase was confirmed before implementation changes.

## Test Gap
edge-case-gap.

Existing tests validated wrapper existence, Python-probe structure, and that install.ps1 referenced Copy-Item for committed wrappers, but they did not exercise the boundary case where source and destination collapse to the same canonical file. This allowed idempotency-breaking behavior to pass the suite.

## Fix
Added canonical path equality guards before wrapper copy operations for cg-index.cmd, cg-brain-init.cmd, and cg-token-audit.cmd in install.ps1.

Applied behavior:

- Compute full canonical paths for source and destination.
- If paths are equal (case-insensitive), skip copy and report Already present.
- Otherwise perform Copy-Item as before.

This preserves normal copy behavior while preventing self-overwrite failure.

## Lessons Learned
For installer idempotency, any file synchronization step that may target repository-owned files should guard against source equals destination before copy/move operations. This bug is an edge-case-gap pattern: happy-path tests around presence and wiring are insufficient unless boundary path-collapse scenarios are explicitly included.

## Related
None.
