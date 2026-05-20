---
date: 2026-05-19
title: "Python try/except scope: cleanup code inside try causes false exit-1; ImportError not caught by OSError-only handler"
category: "bugs"
language: "Python"
tags: [python, cg-index, try-except, exception-handling, ImportError, OSError, cleanup, false-exit-code, file-lock, Windows, brain-mode]
root-cause: "Two distinct except-scope failures in cg_index.py brain mode: (1) cleanup code inside the try block caused false exit-1 when a Windows file lock prevented legacy deletion after a successful brain write; (2) a bare `except OSError` handler did not catch `ImportError` from the deferred import, producing an unhandled traceback and misleading user-facing guidance"
severity: "P1"
fix-confirmed: "yes"
reviewed-in: ".cg-docs/reviews/2026-05-19-knowledge-brain-triggers-batch-b-review.md"
---

# Python `try/except` Scope: Cleanup Inside Try Causes False Exit-1; `ImportError` Not Caught by `OSError`-Only Handler

## Problem

Running `cg-index --brain` on Windows with legacy `DIGEST.md` or
`search-index.json` present sometimes returned exit code 1 even though
`BRAIN.md` was written successfully and the stats line
`[cg-index] Brain index written to ...` had already been printed to stdout.

Separately, if the `brain` package was absent (e.g., after a partial
install, corrupted `sys.path`, or `pip install -e` not re-run after
updating), Python raised an unhandled `ImportError` traceback. The
prompt's error handler then told the user to "check cg-index PATH"
— the wrong diagnosis for a missing Python package.

## Root Cause

### Bug 1 — Cleanup inside try block (P1.2)

The legacy-file deletion loop was inside the same `try/except OSError` block
as the brain build:

```python
# BROKEN — cleanup inside brain-build try block
try:
    from brain import build_brain
    from brain.renderer import render_brain
    data = build_brain(root)
    render_brain(data, out_dir=cg_docs_dir)
    print("[cg-index] Brain index written to ...")       # ← already printed

    # Cleanup for legacy files — inside the SAME try block
    for legacy_name in ("DIGEST.md", "search-index.json"):
        legacy_path = cg_docs_dir / legacy_name
        if legacy_path.exists():
            legacy_path.unlink()                         # ← can raise OSError
            print(f"[cg-index] Removed legacy {legacy_name}")
except OSError as exc:
    print(f"[cg-index] ERROR: {exc}", file=sys.stderr)
    return 1                                             # ← fires on unlink failure
```

On Windows, AV scanners, indexing services, or another process briefly
holding a handle on `DIGEST.md` can cause `unlink()` to raise `OSError`.
When that fires, the handler returns 1 — even though `BRAIN.md` was
successfully written and the stats line was already printed.

The `cg-brain-rebuild.prompt.md` prompt treats exit code as the *primary*
success signal. So the user sees a failure report for a successful build.

### Bug 2 — `ImportError` not caught by `except OSError` (P1.1)

```python
# BROKEN — ImportError escapes OSError-only handler
try:
    from brain import build_brain      # ← raises ImportError on missing package
    from brain.renderer import render_brain
    ...
except OSError as exc:                 # ← does NOT catch ImportError
    print(f"[cg-index] ERROR: {exc}", file=sys.stderr)
    return 1
# → Unhandled ImportError traceback reaches the user
```

`from brain import build_brain` raises `ImportError` when the `brain`
package is not installed (partial install, `pip install -e .` not run,
or wrong virtualenv). `except OSError` is not a base class of `ImportError`
— the exception propagates uncaught, producing a raw Python traceback.

The user-facing `cg-brain-rebuild.prompt.md` guidance then says:
"1. `cg-index` not on PATH — verify with `cg-index --version`"
which is entirely wrong. `cg-index` *is* on PATH; the Python package
is just missing.

## Solution

### Fix 1 — Move cleanup outside the try block

```python
try:
    from brain import build_brain
    from brain.renderer import render_brain
    data = build_brain(root)
    render_brain(data, out_dir=cg_docs_dir)
    print(
        f"[cg-index] Brain index written to {cg_docs_dir} "
        f"({len(data.entities)} entities, ...)"
    )
except ImportError as exc:                    # ← separate ImportError handler
    print(
        f"[cg-index] ERROR: brain package not available ({exc}).\n"
        "Reinstall compound-gpid or run: pip install -e scripts/",
        file=sys.stderr,
    )
    return 1
except OSError as exc:
    print(f"[cg-index] ERROR: {exc}", file=sys.stderr)
    return 1

# Cleanup is now OUTSIDE the try block — failure only warns, never fails the build
for legacy_name in ("DIGEST.md", "search-index.json"):
    legacy_path = cg_docs_dir / legacy_name
    if legacy_path.exists():
        try:
            legacy_path.unlink()
            print(f"[cg-index] Removed legacy {legacy_name}")
        except OSError as exc:
            print(
                f"[cg-index] WARNING: could not remove legacy {legacy_name}: {exc}",
                file=sys.stderr,
            )
return 0
```

Key decisions:
- `ImportError` is listed **before** `OSError` (standard: specific before broad)
- Cleanup gets its own `try/except` that only warns — it can never return 1
- The `return 0` is now unconditional after the main try/except exits cleanly

### Fix 2 — User-facing error guidance updated

`cg-brain-rebuild.prompt.md` Step 3 now lists **three** error causes:
1. `cg-index` not on PATH → `cg-index --version`
2. Not running from project root → `.cg-docs/` required in cwd
3. `.cg-docs/` not yet created (fresh project) → run `/cg-setup`

The `ImportError` path is handled at the Python layer (clean message)
before the prompt guidance fires, so it no longer reaches Step 3.

## Prevention

### General rules

1. **Cleanup code in its own try block**: Never put optional cleanup (file
   deletion, temp file removal, log rotation) inside the same `try` block
   as the main operation. A cleanup failure should warn, not fail.
   Pattern:
   ```python
   try:
       do_main_work()         # the operation that defines success/failure
   except SpecificError as e:
       handle_failure(e)
       return 1
   # success path — cleanup below can only warn
   try:
       do_cleanup()
   except OSError as e:
       warn(e)                # cleanup failure ≠ operation failure
   return 0
   ```

2. **Catch ImportError separately from OSError**: When a try block contains
   a deferred import (`from pkg import thing` inside a function or conditional
   branch), always add an explicit `except ImportError` handler with a
   user-actionable message. `OSError` does not catch `ImportError`.

3. **Order exception handlers specific-to-broad**: `ImportError` → `OSError`
   → `Exception`. A broad handler that precedes a specific one can shadow it.

4. **Exit code is primary**: When building a three-tier verification chain
   (exit code → stdout pattern → file existence), any code path that can
   succeed at the primary level but fail at cleanup must ensure that the
   cleanup failure does not flip the exit code.

5. **Source-code assertions are insufficient for error-path testing**: Both
   bugs survived initial test coverage because the only tests were
   `$source -match 'except ImportError'` string matches. Behavioral tests
   that actually invoke the failure path (mocked PYTHONPATH for ImportError,
   read-only file for OSError-on-unlink) are needed to lock the contract.

## Related

- `.cg-docs/solutions/bugs/2026-05-19-python-warnings-catch-warnings-scope-excludes-root-call.md` — same file (`cg_index.py`), same review cycle: `with` context manager not wrapping the root call; all three bugs are Python scope traps in brain mode
- `.cg-docs/solutions/bugs/2026-04-15-loop-early-exit-skips-per-iteration-cleanup.md` — analogous pattern in prompt files: early-exit skips per-iteration cleanup steps
- `.cg-docs/reviews/2026-05-19-knowledge-brain-triggers-batch-b-review.md` — P1.1 and P1.2 findings
