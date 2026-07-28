---
date: 2026-07-28
title: "Canonical-to-Native Packaging Foundation Review"
review-depth: full
mode: full
branch: feat/implement-canonical-native-packaging
plan: ".cg-docs/plans/2026-07-27-canonical-native-packaging-foundation.md"
findings:
  P0.1:
    status: open
    description: "Destination ancestor symlink race can redirect writes outside the repository"
  P0.2:
    status: open
    description: "Stale cleanup does not revalidate ownership immediately before unlink"
  P0.3:
    status: open
    description: "Missing canonical asset roots can produce a destructive partial generation plan"
  P0.4:
    status: open
    description: "Missing model catalog silently degrades to an empty catalog"
  P1.1:
    status: open
    description: "Windows-forbidden path characters and NTFS alternate stream names pass validation"
  P1.2:
    status: open
    description: "Release preflight validates the working tree rather than the tagged commit"
  P1.3:
    status: open
    description: "Release preflight test paths depend on the caller working directory"
  P1.4:
    status: open
    description: "Update failure tests assert source text rather than executing failure scenarios"
  P1.5:
    status: open
    description: "Release blocking tests do not execute a failing preflight against credential/API boundaries"
---

# Canonical-to-Native Packaging Foundation Review

## Review Context

- **Resolved mode**: full (`review:auto`, security-risk route)
- **Review focus**: generated-tree writes/deletes, path portability, malformed
  canonical state, update/link handoffs, and release publication
- **Protected artifacts**: reviewed without modification

## Findings

**[P0.1]** `scripts/cg_generate_targets.py:1171` - A destination ancestor can
be replaced by a symlink between preflight and commit, redirecting writes
outside the repository. Commit through verified no-follow directory handles or
revalidate identity immediately before every replacement.

**[P0.2]** `scripts/cg_generate_targets.py:1178` - Stale cleanup verifies the
checksum during preflight but does not recheck identity/content immediately
before unlink. A concurrent replacement can delete new user-owned content.

**[P0.3]** `scripts/cg_generate_targets.py:467` - Missing or unexpectedly empty
canonical asset roots are accepted as empty inventories, allowing a partial
checkout to classify valid generated files as stale. Require mandatory roots
and minimum inventories before planning.

**[P0.4]** `scripts/cg_generate_targets.py:654` - A missing model catalog falls
back to an empty catalog. Treat absence or malformed required catalog fields as
fatal before generation.

**[P1.1]** `scripts/cg_generate_targets.py:180` - Windows-forbidden characters
and NTFS alternate-data-stream colons pass path validation. Reject control
characters and `<>:\"|?*` in every path component.

**[P1.2]** `create-release.ps1:105` - Release preflight validates the current
working tree, not necessarily the commit referenced by the release tag. Resolve
the tag commit, require a clean matching checkout, and test that exact commit.

**[P1.3]** `create-release.ps1:91` - Relative pytest paths make preflight depend
on the caller's working directory. Resolve paths from `$PSScriptRoot` or execute
inside a restored `Push-Location` scope.

**[P1.4]** `scripts/tests/test_update_generates_targets.py:35` - Failure cases
only inspect source text. Execute isolated updater fixtures with injected
Python/generator/mapping failures and assert no downstream mutation.

**[P1.5]** `scripts/tests/test_release_gate_targets.py:32` - Publication
blocking is source-order-only. Execute a failing preflight with mocked
credential/API boundaries and assert neither boundary is called.

## Important P2 Follow-Up

- Add documentation tests to CI and release preflight.
- Test the declared Python 3.8 minimum and pin the pytest environment.
- Remove stale uncertainty text from the completed work report.
- Reduce repeated O(outputs x assets) index construction and no-op rewrites.
- Split the 1,400-line generator into safety-focused modules after blockers are fixed.

## Summary

- P0: 4 open
- P1: 5 open
- P2: follow-up themes recorded above
- Merge status: blocked
