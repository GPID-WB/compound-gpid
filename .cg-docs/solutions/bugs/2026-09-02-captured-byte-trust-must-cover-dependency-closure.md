---
date: 2026-09-02
title: "Captured-byte trust must cover the complete dependency closure"
category: "bugs"
language: "Python"
tags: [security, dynamic-dispatch, imports, captured-bytes, nofollow, hardlink, toctou, line-endings]
root-cause: "The selected handler was captured securely, but its imports and later text rendering still resolved state outside the captured trust boundary"
severity: "P0"
---

# Captured-Byte Trust Must Cover the Complete Dependency Closure

## Problem

A dynamic Python dispatcher captured and validated the selected operation file
before execution. The handler still imported shared operation helpers, services,
and providers through Python's normal importer. A linked, hard-linked, swapped,
or preloaded helper could therefore execute module-level code even though the
handler leaf was trusted.

The same fix pattern exposed a second regression in target generation. Replacing
`read_text()` with captured raw bytes removed Python's universal-newline
normalization. Generated text could retain CRLF on Windows and violate the
deterministic LF output contract.

## Root Cause

A trust boundary is incomplete when it protects only the first executable file.
`exec()` does not make later imports safe: imports perform new path resolution
and execute the object found at that later boundary.

Captured bytes also change API semantics. A prior text API can decode and
normalize content, while a byte API preserves every byte. Security refactors
must reproduce required semantic transformations explicitly after capture.

## Solution

Before executing an operation, the dispatcher now captures the complete
repository-local `skill_management` dependency closure with root-anchored,
bounded, no-follow reads and hard-link rejection. A bounded import finder serves
only those validated bytes. Unsafe preloaded modules, missing helpers, wrong-root
modules, links, and dynamic import bypasses fail before module-level side effects.

The generator follows a two-step rule:

```python
captured = secure_read_bytes(root, relative_path, reject_hardlinks=True)
text = captured.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")
```

Normalization applies only to declared UTF-8 text assets. Opaque and binary
skill resources remain byte-exact. Tests separately assert dependency side
effects, leaf and ancestor swaps, hard links, preloaded modules, CRLF text
normalization, and binary resource hashes.

## Prevention

- Define the transitive execution closure before calling `exec()`.
- Do not allow trusted code to import repository-local helpers through the
  normal importer unless the complete installation is independently immutable.
- Reject unsafe preloaded modules; a valid module name is not valid provenance.
- Test absence of malicious side effects, not only the final error code.
- Record the semantic behavior of the API being replaced. After secure byte
  capture, explicitly restore required decoding and newline normalization.
- Keep text normalization separate from binary resource handling.

## Related

- `.cg-docs/solutions/bugs/2026-08-31-trust-anchor-captured-byte-dispatch.md`
- `.cg-docs/solutions/testing-patterns/2026-07-28-handle-relative-filesystem-mutations-and-real-boundary-tests.md`
- `.cg-docs/solutions/bugs/2026-08-01-secure-publication-rollback-must-not-clobber.md`
- `.cg-docs/reviews/2026-08-28-scalable-skill-management-suite-verify-review-2.md`
