---
date: 2026-08-17
title: "Windows long-path prefix required for staged file publication"
category: "bugs"
language: "Python"
tags: [windows, long-path, MAX_PATH, secure_fs, CreateFileW, staging, atomic-replace]
root-cause: "CreateFileW temp sibling path without \\\\?\\\\ prefix exceeds MAX_PATH 260 when staged under .compound-gpid/staging/<tx>/<root>/..."
severity: "P1"
---

# Windows Long-Path Prefix Required for Staged File Publication

## Problem

The manifest-driven projection synchronizer (`cg_project_projection.py`) stages files under `<project>/.compound-gpid/staging/<32-hex-tx>/<root>/...` before atomic replacement. On Windows, deep canonical skill files (e.g. `cg-skill-wb-report-writing/evals/benchmarks/*.benchmark.json`) produce staged paths exceeding MAX_PATH 260. `CreateFileW` fails with `WinError 3` (`ERROR_PATH_NOT_FOUND`) when creating the atomic-replace temp sibling with a `.`+32-hex+`.tmp` suffix.

This blocks every manifest-driven `link`/`update` on Windows. Pytest fixtures use short trees, so the issue is untested.

## Root Cause

`secure_fs.py` used `CreateFileW` / `open` / `rename` without a `\\?\` long-path prefix. The staging directory nesting adds ~60 characters to the canonical path, pushing deep files past the 260-character limit.

## Solution

Added a `_windows_long_path(path: Path) -> str` helper to `secure_fs.py` that prepends `\\?\` to absolute paths on Windows. Applied in:

- `_windows_create_file` (line ~956)
- `_windows_open_regular` (line ~980)
- `_windows_open_directory` (line ~1083)
- `_windows_rename_handle` (line ~1240)

```python
def _windows_long_path(path: Path) -> str:
    """Prefix absolute paths with \\\\?\\\\ for Windows long-path support."""
    s = str(path)
    if sys.platform == "win32" and not s.startswith("\\\\?\\"):
        return "\\\\?\\" + s
    return s
```

The prefix is applied only after absolute normalization (`path.resolve()`) to ensure valid input.

## Prevention

- Any new `CreateFileW`/`open`/`rename` call in `secure_fs.py` must use `_windows_long_path` for the path argument.
- Staging tests should include at least one deep-nested destination (284+ chars) to exercise the long-path boundary.
- On non-Windows platforms the helper is a no-op, so it's safe to apply unconditionally.

## Related

- `.cg-docs/reviews/2026-08-13-manifest-driven-skill-loading-phase3-verify-review.md` (P1.7)
- `scripts/secure_fs.py` — `_windows_long_path` implementation
- `scripts/tests/test_project_projection.py` — `TestLongPathPublish` class
