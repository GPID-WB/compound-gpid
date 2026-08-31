---
date: 2026-07-28
title: "Filesystem race fixes require handle-relative mutation and real boundary tests"
category: "testing-patterns"
language: "both"
tags: [filesystem, security, toctou, symlink, dir-fd, nofollow, pytest, pester, release, updater]
root-cause: "Pathname validation and source-text tests were mistaken for guarantees about later filesystem mutations and failure boundaries"
severity: "P0"
---

# Filesystem Race Fixes Require Handle-Relative Mutation and Real Boundary Tests

## Problem

The native target generator validated destination ancestors, hashes, and ownership before writing or deleting generated files. A concurrent actor could replace an ancestor or stale file after validation but before the pathname-based mutation. Initial regression tests swapped paths before the final validation, so they passed without exercising the vulnerable window.

Release and updater tests had a related weakness: some checked source ordering or an unrelated sentinel instead of executing the real script and observing credential, API, or managed-file boundaries.

## Root Cause

A pathname is not a stable filesystem identity. A check such as `is_symlink()`, `stat()`, or a content hash says what the path resolved to at that instant; a later `replace()` or `unlink()` resolves the path again.

Tests were also vacuous when their asserted sentinel was not an output the production continuation path could mutate, or when a test flag disabled the downstream behavior being claimed.

## Solution

On POSIX, generation now traverses from an opened repository root using `dir_fd`, `O_DIRECTORY`, and `O_NOFOLLOW`. Writes create and fsync a temporary file inside the pinned parent directory and use handle-relative `os.replace()`.

Stale cleanup uses a quarantine pattern:

1. Atomically rename the stale name to a random quarantine name through the pinned parent handle.
2. Hash the quarantined file.
3. Restore it if ownership no longer matches.
4. Unlink only the verified quarantined name.

Race tests inject replacements at `_before_secure_replace` and `_before_secure_unlink`, after setup and immediately at the mutation boundary. Script tests invoke the actual release/updater entry points and assert real boundaries: credential/API mocks remain untouched and managed destinations retain their bytes.

## Prevention

- Never describe pathname revalidation as race-safe when mutation resolves the pathname again.
- Pin directory identity with no-follow handles and perform replacement relative to those handles.
- For delete-after-verify workflows, quarantine atomically, verify the quarantined object, then delete it.
- Inject adversarial test changes at the final mutation boundary, not before the guard under test.
- Assert a downstream artifact that production code would actually mutate; do not use unrelated sentinels.
- Do not enable test flags that suppress the continuation path being tested.
- Ensure global command mocks are removed so one Pester file cannot contaminate later files.

## Related

- `.cg-docs/solutions/bugs/2026-08-01-secure-publication-rollback-must-not-clobber.md` — follow-up: publication and rollback need non-replacing collision semantics even after parent handles are pinned
- `.cg-docs/solutions/bugs/2026-05-20-python-path-startswith-bypass-use-relative-to.md`
- `.cg-docs/solutions/bugs/2026-06-11-llm-prose-only-syscall-is-unenforceable.md`
- `.cg-docs/reviews/2026-07-28-canonical-native-packaging-foundation-verify-review.md`
- `.cg-docs/solutions/data-quality/2026-08-28-exact-json-registry-mutation-boundaries.md` - uses the real final secure-write hook to prove rollback and byte preservation
