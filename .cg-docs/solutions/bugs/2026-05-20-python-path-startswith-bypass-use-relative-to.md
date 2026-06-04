---
date: 2026-05-20
title: "Python: str.startswith() for path containment allows sibling-directory bypass — use relative_to()"
category: "bugs"
language: "Python"
tags: [python, path, security, symlink, path-traversal, scanner, file-io]
root-cause: "str.startswith() compares path strings as text, not as path components — a sibling directory sharing the same string prefix bypasses the guard"
severity: "P1"
---

# Python: `str.startswith()` Path Containment Allows Sibling-Directory Bypass

## Problem

`brain.scanner` contained a symlink escape guard intended to reject files
whose resolved path lay outside `.cg-docs/`:

```python
cg_docs_real = cg_docs.resolve()
if not str(resolved_path).startswith(str(cg_docs_real)):
    warnings.warn("Skipping: symlink escapes .cg-docs/ boundary")
    continue
```

The guard appeared safe but allowed an attacker to bypass it with a sibling
directory named `.cg-docs-evil/`. Because the string
`"/root/.cg-docs-evil/payload.md"` starts with `"/root/.cg-docs"` (the common
prefix), `startswith()` returned `True` — silently treating the adversarial
path as inside `.cg-docs/`.

Symptoms:
- Symlinks inside `.cg-docs/` pointing to files in a sibling directory
  `<root>/.cg-docs-extra/` or `<root>/.cg-docsX/` were accepted without
  warning.
- No error was raised; the malicious file was scanned and indexed.

## Root Cause

`str.startswith()` performs **string prefix matching**, not **path component
matching**. The strings `"/home/user/.cg-docs"` and
`"/home/user/.cg-docs-evil"` share the prefix `"/home/user/.cg-docs"`, so the
guard incorrectly classifies `.cg-docs-evil/` as being inside `.cg-docs/`.

This is a well-known class of path-traversal vulnerability that appears
whenever developers treat file paths as plain strings.

## Solution

Replace `startswith()` with `Path.relative_to()`, which performs component-
level containment: it only succeeds if the candidate is truly a descendant of
the base path.

```python
# ✅ CORRECT — component-level comparison
cg_docs_real = cg_docs.resolve()   # resolve once, outside the loop

try:
    resolved_path = md_path.resolve()
except OSError:
    continue

try:
    resolved_path.relative_to(cg_docs_real)   # raises ValueError if not inside
except ValueError:
    warnings.warn(
        f"[brain.scanner] Skipping {md_path}: symlink escapes .cg-docs/ boundary.",
        stacklevel=2,
    )
    continue
```

Key differences from the buggy version:
1. `relative_to()` raises `ValueError` when the path is not a descendant —
   there is no silent false-positive case.
2. `cg_docs_real = cg_docs.resolve()` is moved **outside the loop** (O(1)
   syscalls instead of O(n)).

## Prevention

**Rule**: Never use `str(path).startswith(str(base))` to test whether a path
is inside a directory. The correct idiom:

```python
# Pattern A — try/except (explicit, clear error site)
try:
    candidate.relative_to(base)
except ValueError:
    # candidate is outside base
    ...

# Pattern B — is_relative_to() (Python 3.9+)
if not candidate.is_relative_to(base):
    ...
```

The `is_relative_to()` method was added in Python 3.9. For Python 3.8
compatibility (this project targets 3.8+), use the `try/except` form.

**Anti-pattern to avoid**:
```python
# ❌ WRONG — string prefix match, vulnerable to sibling-directory bypass
if not str(resolved).startswith(str(base)):
    reject()
```

**Code review checklist**: When reviewing any path containment check, search
for `.startswith(str(` or `startswith(os.fspath(` and replace with
`relative_to()` or `is_relative_to()`.

## Related

- `scripts/brain/scanner.py` — where this fix was applied (lines ~83-96)
- `scripts/brain/tests/test_scanner.py` — symlink escape test (platform-
  skipped on Windows; verify on Linux/macOS)
- `.cg-docs/solutions/bugs/2026-05-07-python-nonatomic-path-write-use-mkstemp-replace.md`
  — related Python file-I/O safety pattern
- OWASP: Path Traversal (CWE-22)
