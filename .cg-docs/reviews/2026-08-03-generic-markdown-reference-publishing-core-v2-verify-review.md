---
date: 2026-08-03
depth: light
parent-review: .cg-docs/reviews/2026-08-03-generic-markdown-reference-publishing-core-v2-review.md
type: verification
findings:
  P1.1: fixed
  P1.2: fixed
  P1.3: fixed
  P2.1: fixed
---

# Verification Review: Generic Markdown and Reference Publishing Core (V2)

## Verification Summary

**Review mode**: light verification

**Parent review**: `.cg-docs/reviews/2026-08-03-generic-markdown-reference-publishing-core-v2-review.md`

**Result**: The prior review's 17 findings are marked fixed, but this verify
pass found four unresolved correctness, security, coverage, and documentation
issues. No files were edited during verification.

**Suppression policy applied**:

- P0/P1 correctness, security, and data-integrity issues were reported even
  when they overlap a prior fixed finding.
- Cross-file breakage was reported.
- P2/P3 findings were suppressed only when strictly within a prior fixed
  finding's explicitly covered block; the documentation omission is outside
  that suppression scope.

## P1 - Critical

### P1.1 - Secure stale deletion has no safe durability commit point

- **Files**: `scripts/secure_fs.py:612`, `scripts/secure_fs.py:822`
- **Sources**: `cg-code-quality`, `cg-testing`
- **Issue**: POSIX stale deletion unlinks the quarantined file, clears its
  recovery state, and only then calls a fallible parent-directory `fsync`.
  A directory-flush failure can therefore raise after the only recovery bytes
  have been destroyed. On Windows, rollback restoration failures after a
  concurrent creator occupies the original name are silently discarded, so a
  recovery artifact may exist without being named in the surfaced error.
- **Impact**: A failed publication or generation can report failure after
  deleting managed bytes or can hide the recovery path, violating the
  non-clobbering publication and rollback contract.
- **Fix**: Define the deletion commit point explicitly. Retain quarantine
  identity and recovery bytes through all precommit failures, restore with
  no-replace semantics before commit, and propagate a typed error naming any
  recovery artifact when restoration collides. Add POSIX directory-`fsync`
  failure coverage and a Windows concurrent-winner/recovery-path assertion.

### P1.2 - Mixed-case explicit output namespaces are accepted inconsistently

- **File**: `scripts/artifact_views/paths.py:284`
- **Source**: `cg-code-quality`
- **Issue**: `_portable_output_path()` accepts case-folded variants of the
  registered `.cg-docs/views/documents` namespace but returns the caller's
  original spelling. Later canonical destination and collision checks require
  the registered spelling, producing platform-dependent behavior: Windows can
  create the mixed-case path and subsequent checks reject it, while POSIX can
  pass the portable validator and fail at the typed `ViewDestination` boundary.
- **Impact**: Render-then-check behavior is inconsistent across supported
  backends, and explicit output identity can diverge from the registered
  namespace and provenance ownership.
- **Fix**: Require the registered namespace spelling exactly, or canonicalize
  it before constructing `GenericPaths`, `ViewDestination`, provenance, and
  collision keys. Add render-then-check tests for mixed-case explicit output on
  Windows and POSIX.

### P1.3 - Supported CI does not execute the publisher/security Python surface

- **File**: `.github/workflows/tests.yml:28`
- **Source**: `cg-testing`
- **Issue**: The Windows/macOS `native-targets` Python job runs target-generation
  tests only. The separate Windows/macOS job runs Pester, but the workflow has
  no Python coverage for `scripts/tests/test_secure_fs.py`,
  `scripts/artifact_views/tests/test_writer.py`, generic CLI/provenance/
  renderer/security tests, or launcher Python tests.
- **Impact**: The supported-backend release gate can pass while the generic
  publisher's secure filesystem and image/security behavior is unexecuted.
  The prior P1.5 fix is not independently durable in CI evidence.
- **Fix**: Add a Windows/macOS Python publisher/security job or extend the
  existing matrix with the focused secure filesystem, writer, generic CLI,
  provenance, renderer/security, and launcher modules. Assert that applicable
  backend race tests are not skipped and publish durable per-file evidence.

## P2 - Important

### P2.1 - The reference file map omits the generic document-view namespace

- **File**: `docs/reference/files.md:44`
- **Source**: `cg-code-quality`
- **Issue**: The file map documents `.cg-docs/views/brainstorms/` and
  `.cg-docs/views/plans/`, but omits `.cg-docs/views/documents/`, even though
  the generic publisher uses that namespace and related documentation refers
  to it.
- **Impact**: Users consulting the canonical file map cannot discover the
  generic publisher's generated output location.
- **Fix**: Add a `views/documents/` row and a focused documentation assertion
  covering all three generated view namespaces.

## Verification Evidence

- `cg-code-quality`: usable review output with three findings; no files edited.
- `cg-testing`: usable review output with two findings; no files edited.
- Focused publisher/security/CLI suite: `172 passed, 20 skipped` reported by
  `cg-code-quality`.
- Focused publisher/filesystem/security/CLI/ownership suite: `182 passed, 21
  skipped` reported by `cg-testing`.
- Target-generation/canonical-output suite: `203 passed, 4 skipped`.
- Secure-filesystem/bitmap-security subset: `68 passed, 10 skipped`.
- Python compilation, workspace diagnostics, `git diff --check`, EOL policy,
  and generated-tree drift checks passed as reported by the agents.
- Current branch ancestry: `HEAD...origin/main = 0 0`.
- Generated `.cg-docs/views/**` bodies were excluded from context; only paths
  and counts were considered.

## Passed

- Both required light verification agents returned usable, in-scope output.
- The prior fixed findings were not blindly suppressed; P0/P1 and cross-file
  regressions were re-evaluated.
- No protected artifact was recommended for deletion, replacement, renaming,
  or movement.

## Status

Verification is blocked on P1.1, P1.2, and P1.3. P2.1 should also be addressed
before merge. No autofix was applied because `mode:verify` is read-only.
