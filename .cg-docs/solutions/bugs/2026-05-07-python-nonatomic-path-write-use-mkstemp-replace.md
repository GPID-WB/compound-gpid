---
date: 2026-05-07
title: "Python non-atomic Path.write_text() truncates on crash — use mkstemp + os.replace"
category: "bugs"
language: "Python"
tags: [python, atomic-write, file-io, stdlib, mkstemp, crash-safety, data-integrity]
root-cause: "Path.write_text() truncates the destination file before writing; a crash mid-write leaves a partially written or empty file with no way to recover the prior content"
severity: "P2"
fix-confirmed: "yes"
reviewed-in: ".cg-docs/reviews/2026-05-07-python-utility-layer-cg-index-review.md"
---

# Python Non-Atomic `Path.write_text()` Truncates on Crash — Use `mkstemp + os.replace`

## Problem

`Path.write_text(content)` and `open(path, 'w')` are not atomic. The OS
truncates the destination file to zero bytes **before** writing any content.
If the process is interrupted mid-write (SIGKILL, power failure, out-of-disk,
exception after truncation), the destination file is left empty or partially
written — the previous content is gone with no recovery path.

This was flagged as P2.4 in the `cg_index.py` code review. The indexer wrote
`search-index.json` and `DIGEST.md` using `path.write_text()`, meaning a crash
during indexing would silently destroy the knowledge base files.

## Root Cause

All POSIX file writes via `open(path, 'w')` follow this sequence:
1. `open()` — truncates the file to 0 bytes (creates if absent)
2. Iterative `write()` calls — content written in chunks
3. `close()` / flush — buffers flushed, file descriptor closed

Steps 1 and 3 are not a transaction. Any exception, signal, or OS interruption
between step 1 and 3 leaves the file in an inconsistent state.

## Solution

Use `tempfile.mkstemp(dir=path.parent)` to write into a temp file on the
**same filesystem** as the destination, then call `os.replace()` to atomically
rename it over the destination:

```python
import os
import tempfile
from pathlib import Path


def _write_atomic(path: Path, content: str) -> None:
    """Write content to path atomically using a temp file + os.replace().

    The temp file is created in path.parent to ensure it lives on the same
    filesystem — required for os.replace() to be atomic (single rename syscall).
    """
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".tmp-")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(content)
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise
```

Usage — replace every `path.write_text(content)` call:

```python
# Before (non-atomic):
output_path.write_text(json.dumps(index, indent=2), encoding="utf-8")

# After (atomic):
_write_atomic(output_path, json.dumps(index, indent=2))
```

**Why `dir=path.parent` is required**: `tempfile.mkstemp()` defaults to
`/tmp` (or `%TEMP%` on Windows). If the destination is on a different mount,
`os.replace()` raises `OSError: [Errno 18] Invalid cross-device link`. Placing
the temp file in `path.parent` guarantees same-device placement.

**Windows note**: `os.replace()` is not fully atomic on Windows when the
destination is locked by another process (it raises `PermissionError` instead
of performing an atomic swap). For the `cg_index.py` use case (single-writer
indexer), this is acceptable. Use `python-atomicwrites` (third-party) if true
atomic Windows semantics are required.

## Prevention

- Never use `Path.write_text()` for any output file that must survive crashes.
- Apply `_write_atomic()` to all file outputs in scripts that produce knowledge
  base artefacts, index files, or digest files.
- Stdlib only — no pip install needed. `tempfile`, `os`, `pathlib` are built-in.

## Related

- `.cg-docs/solutions/bugs/2026-03-19-persistent-state-written-before-validation-causes-corruption.md` — writing state before validation causes similar corruption
- Python docs: [`tempfile.mkstemp`](https://docs.python.org/3/library/tempfile.html#tempfile.mkstemp), [`os.replace`](https://docs.python.org/3/library/os.html#os.replace)
