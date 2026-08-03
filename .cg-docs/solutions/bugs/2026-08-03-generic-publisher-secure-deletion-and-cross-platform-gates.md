---
date: 2026-08-03
title: "Generic publisher deletion commit points and cross-platform release gates"
category: "bugs"
language: "Python"
tags: [generic-publishing, secure-filesystem, deletion, fsync, quarantine, recovery, path-identity, ci, windows, posix]
root-cause: "Secure stale deletion had no explicit durability commit point, output namespace validation accepted mixed-case identities, and supported-OS CI omitted the generic publisher security surface"
severity: "P1"
---

# Generic Publisher Deletion Commit Points and Cross-Platform Release Gates

## Problem

The generic Markdown publisher passed its initial implementation gates, but
verification found four closure gaps:

- POSIX stale deletion removed quarantine bytes before a fallible directory
  `fsync`, so a reported failure could follow irreversible deletion.
- Windows stale-delete rollback could suppress a no-replace restoration failure,
  leaving a recovery artifact unnamed and difficult to recover.
- Explicit output paths accepted case-folded variants of the registered
  `.cg-docs/views/documents` namespace, while typed destinations and later
  ownership checks required the canonical spelling.
- The Windows/macOS Python matrix covered native target generation but did not
  execute the generic publisher's secure filesystem, writer, renderer, image,
  provenance, CLI, and launcher tests or require backend race evidence.

The reference file map also omitted the generic `views/documents/` namespace.

## Root Cause

Secure deletion treated quarantine removal and directory durability as one
undifferentiated operation. It cleared the recovery state before the durability
boundary, so the error path could no longer distinguish a precommit rollback
from a deletion that had already happened.

The Windows path also attempted rollback while the file handle was still open
and hid a failed no-replace restore. Even when the recovery bytes survived,
the caller did not receive their identity.

Path validation compared the namespace case-insensitively but returned the
original spelling. That allowed a path to pass the portable validator and then
fail at the typed `ViewDestination` or provenance boundary.

Finally, CI treated target generation as sufficient cross-platform Python
coverage. The generic publisher's backend-specific race behavior was only
represented in local focused evidence, not in the supported-OS release gate.

## Solution

### Define the deletion commit point

POSIX stale deletion now treats successful quarantine verification followed by
`unlink(quarantine)` as the deletion commit point. A later directory `fsync`
failure emits a `RuntimeWarning` identifying the committed deletion instead of
pretending that the bytes can still be restored.

Before that commit point, rollback uses non-replacing restoration. If the
original name was recreated by another process, the concurrent winner remains
at the original name and the quarantine is preserved. The raised
`SecureMutationError` includes the recovery filename.

Windows keeps the quarantine state until disposal and rollback handling finish.
If a concurrent winner occupies the original name, the typed recovery error is
delayed until file and parent handles close, leaving the quarantine artifact
readable by the caller.

### Enforce canonical output identity

Generic output validation now requires the exact registered prefix:

```python
if output.parts[:3] != (".cg-docs", "views", "documents"):
    raise ArtifactPathError("Generic output must stay in the registered documents namespace.")
```

Portable case-collision keys remain useful for rejecting distinct filesystem
spellings, but they are not used to authorize a different registered
namespace spelling. Resolver, typed destination, provenance, and check-mode
identity now agree.

### Make backend evidence durable

The existing Windows/macOS Python matrix now runs the generic publisher and
security modules, including secure filesystem, writer, CLI, parser, renderer,
launcher, provenance, path, image-security, theme, and integration tests.

Backend-specific race tests use `backend_posix` and `backend_windows` markers.
Each matrix leg emits JUnit XML and runs a small gate that fails when no
applicable test is collected or when an applicable backend test is skipped.
The results are uploaded as CI artifacts for per-OS evidence.

### Keep the documentation contract complete

The canonical file map lists `.cg-docs/views/documents/` alongside the
Brainstorm and Plan view namespaces. A documentation test asserts all three
view namespaces remain discoverable.

## Verification

Focused triage validation passed:

- `228 passed, 23 skipped` across secure deletion, path routing, CI contracts,
  ownership, publisher, security, launcher, and documentation tests.
- Complete Python suite: `1344 passed, 39 skipped, 21 warnings, 5 subtests
  passed`.
- Canonical unfiltered Pester: `2343/2343 passed`, zero failures, and
  `filteredFiles: null`.
- Applicable Windows backend gate: `6 passed, 50 deselected`; the JUnit gate
  reported six backend tests with no skips. The POSIX backend is configured for
  the macOS matrix leg.
- Touched-file diagnostics reported no errors.
- `git diff --check` passed; no package or lockfile changes were introduced.
- `bin/cg-publish-markdown` retained Git mode `100755`.
- `HEAD...origin/main` remained `0 0`.

## Prevention

- Name the commit point for every secure delete, publish, and rollback path.
  After commit, report cleanup or durability uncertainty as a warning with the
  surviving recovery identity; before commit, restore without replacement.
- Never suppress a failed recovery rename. Preserve and name the quarantine
  artifact so operators can recover bytes without guessing a temporary name.
- Require exact registered namespace spelling at typed path boundaries; use
  normalized case-collision keys only to reject ambiguous filesystem entries.
- Run the full publisher/security surface on every supported backend, and make
  the applicable race marker fail when it collects zero tests or skipped tests.
- Treat documentation namespace maps and generated-view contracts as tested
  interfaces, not informal prose.
- Inject races immediately before the final mutation and assert the bytes of
  every competing identity.

## Related

- `.cg-docs/solutions/bugs/2026-08-01-secure-publication-rollback-must-not-clobber.md` - foundational non-clobbering publication, quarantine, umask, and pinned-read pattern
- `.cg-docs/solutions/testing-patterns/2026-07-28-handle-relative-filesystem-mutations-and-real-boundary-tests.md` - final-boundary race injection and real managed-output assertions
- `.cg-docs/reviews/2026-08-03-generic-markdown-reference-publishing-core-v2-verify-review.md` - verification findings and fixed-status ledger
- `.cg-docs/plans/2026-08-03-generic-markdown-reference-publishing-core-v2.md` - authoritative generic publishing Plan
