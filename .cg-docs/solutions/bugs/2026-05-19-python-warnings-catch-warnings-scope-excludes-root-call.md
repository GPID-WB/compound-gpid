---
date: 2026-05-19
title: "warnings.catch_warnings() context must wrap the root call, not just its callees"
category: "bugs"
language: "Python"
tags: [warnings, context-manager, catch_warnings, scope, build_brain, cg-index]
root-cause: "build_brain() was called before the `with warnings.catch_warnings()` block opened, so all scanner/extractor/clusterer warnings emitted inside the call were never captured"
severity: "P2"
---

# `warnings.catch_warnings()` context must wrap the root call, not just its callees

## Problem

`cg_index.py` wrapped only `render_brain()` in a `with warnings.catch_warnings(record=True)`
block — `build_brain()` was called immediately before it. All `warnings.warn()` calls
emitted deep inside `build_brain()` (scanner, extractor, clusterer, edge_detector)
escaped the managed context and were subject to Python's default `once`-per-location
deduplication filter, silently swallowing them on repeated same-process invocations.

The bug meant that the P1–P3 warning fixes added during fix-triage
(missing frontmatter, UnicodeDecodeError skip, duplicate keys, no-id roadmap features)
produced no visible output at runtime — completely defeating their purpose.

```python
# BROKEN — build_brain warnings escape the context
data = build_brain(root)                        # ← outside catch_warnings
with warnings.catch_warnings(record=True) as captured:
    warnings.simplefilter("always")
    render_brain(data, out_dir=cg_docs_dir)
    for w in captured:
        print(f"[cg-index] WARNING: {w.message!s}", file=sys.stderr)
```

## Root Cause

`warnings.catch_warnings(record=True)` is a context manager that redirects warnings
emitted **within its `with` block** into the `captured` list. Any `warnings.warn()` call
made before the `with` statement opens is processed by the standard warning machinery
(default filter: show each unique location once). If `build_brain()` emits warnings on
the first run they are shown once to stderr; on subsequent runs they are silently
suppressed by the deduplication filter.

The error was introduced because only `render_brain()` was originally wrapped (renderer
warnings were the initial concern), and `build_brain()` was added to the call site without
noticing the scope boundary.

## Solution

Move `build_brain()` **inside** the `with warnings.catch_warnings()` block, and move the
`for w in captured:` print loop **outside** (after the `with` block exits, `captured` is
fully populated):

```python
# CORRECT — all warnings from build_brain and render_brain are captured
with warnings.catch_warnings(record=True) as captured:
    warnings.simplefilter("always")
    data = build_brain(root)                    # ← inside catch_warnings
    render_brain(data, out_dir=cg_docs_dir)
for w in captured:
    print(f"[cg-index] WARNING: {w.message!s}", file=sys.stderr)
```

The `for w in captured:` loop works both inside and outside the `with` block
(the list is populated continuously), but moving it outside is idiomatic and
documents intent — "iterate after all warnings have been collected."

## Prevention

**Rule**: When using `warnings.catch_warnings(record=True)` to funnel warnings from a
multi-function pipeline, the outermost entry point of the pipeline must be the **first**
statement inside the `with` block. Never call the entry point before opening the context.

**Review checklist**: After adding `with warnings.catch_warnings(record=True)`, verify
that every function known to emit `warnings.warn()` is reachable from within the block.
Look for calls immediately before `with` — they are the most common mistake.

**Test signal**: If `warnings.simplefilter("always")` is set and the `captured` list is
unexpectedly empty after a pipeline run that should emit warnings, the entry point is
outside the block.

## Related

- `scripts/cg_index.py` — the fixed call site
- `scripts/brain/scanner.py`, `clusterer.py`, `edge_detector.py` — warning emission sites
- [Python docs: `warnings.catch_warnings`](https://docs.python.org/3/library/warnings.html#warnings.catch_warnings)
