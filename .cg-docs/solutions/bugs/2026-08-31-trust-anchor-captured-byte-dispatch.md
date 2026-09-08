---
date: 2026-08-31
title: "Trusted dispatch requires immutable anchors and captured bytes"
category: "bugs"
language: "Python"
tags: [security, trust-anchor, dynamic-dispatch, nofollow, hardlink, toctou, git, contracts]
root-cause: "Mutable Git metadata and pathname checks were treated as authority and code identity after later operations resolved the same inputs again"
severity: "P0"
---

# Trusted Dispatch Requires Immutable Anchors and Captured Bytes

## Problem

The private skill-management dispatcher used local Git origin and branch data to
grant maintainer authority. A fixture could create unrelated history, assign the
canonical origin string, create a local `origin/main` reference, and receive the
maintainer role.

Handler dispatch had a second boundary error. The dispatcher imported a module
and only then checked `module.__file__`. Python executes module-level code during
import, so a wrong, linked, swapped, or preloaded module could run before the
origin check rejected it. Module validation also inventoried files safely and
then reopened their pathnames for content scans.

## Root Cause

A candidate-controlled label is not a trust anchor. Remote URLs, branch names,
and local remote-tracking references can all be rewritten. Likewise, validating
a pathname does not bind a later import or read to the validated object.

The common mistake was correct ordering at the source level but incorrect
identity at the system boundary:

1. validate mutable metadata or a path;
2. perform a later operation that resolves it again;
3. assume the later object is the validated object.

## Solution

Maintainer context now requires ancestry from an immutable canonical commit hash
embedded in the trusted dispatcher, plus canonical origin, default-branch
ancestry, complete registry validation, equal roots, and a nonprotected feature
branch. Git subprocesses remove inherited `GIT_*` variables and read the raw
local remote value rather than a rewritten fetch URL.

Dynamic handlers are loaded from bytes returned by the existing root-anchored
`secure_read_bytes()` API. The read rejects linked ancestors, leaf links,
reparse points, hard links, oversized files, and nonregular files. The dispatcher
compiles and executes those captured bytes directly; it does not import a path
and inspect it after execution.

Module validation uses the same no-follow reader and caches one byte snapshot per
validation entry point. A swap or unsafe identity becomes a validation finding
instead of a skipped content scan.

Regression tests prove these boundaries:

- unrelated history with forged origin and refs remains `consumer`;
- a hard-linked handler is rejected before its side effect can run;
- simulated asset swaps return validation errors;
- strict contracts reject malformed Unicode, unsafe regexes, invalid pointers,
  duplicate action paths, and mutable plan revisions.

## Prevention

- Use immutable object identity as the trust anchor; never grant authority from
  an origin string, branch name, or free-text approval.
- Validate dynamic code before execution. Import-then-check is too late.
- Read security-sensitive content once through the checked no-follow handle and
  pass captured bytes forward.
- Reject hard links when one pathname must identify one authorized source.
- Clear snapshot caches at public validation boundaries so repeated runs see a
  new state while one run remains internally consistent.
- Test the actual side-effect boundary. Assert that malicious module-level code
  did not execute, not only that a path check returned an error.

## Related

- `.cg-docs/solutions/testing-patterns/2026-07-28-handle-relative-filesystem-mutations-and-real-boundary-tests.md`
- `.cg-docs/solutions/bugs/2026-08-01-secure-publication-rollback-must-not-clobber.md`
- `.cg-docs/solutions/testing-patterns/2026-07-24-cross-file-contract-state-must-align-docs-validator-tests.md`
- `.cg-docs/solutions/bugs/2026-09-02-captured-byte-trust-must-cover-dependency-closure.md`
- `.cg-docs/reviews/2026-08-28-scalable-skill-management-suite-review.md`
- `.cg-docs/reviews/2026-08-28-scalable-skill-management-suite-verify-review.md`
