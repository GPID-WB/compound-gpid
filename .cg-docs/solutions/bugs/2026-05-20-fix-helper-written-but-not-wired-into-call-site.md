---
date: 2026-05-20
title: "Security fix helpers written but never called from the protected call site"
category: "bugs"
language: "Python"
tags: [refactor, dead-code, call-site, security, url-encoding, sanitization, path-traversal, verify-pass, renderer, edge-detector]
root-cause: "Two helper functions (_sanitize_inline, quote) were added to renderer.py as security fixes but _entity_line() — the only caller — was never updated to invoke them, leaving both functions as dead code and the vulnerabilities intact"
severity: "P1"
---

# Security fix helpers written but never called from the protected call site

## Problem

A `/cg-review` thorough pass on `scripts/brain/renderer.py` identified two
security findings:

- **P1.2** — Paths in markdown links must be URL-encoded (e.g. `fix(v2).md`
  terminates the link early at the `)`)
- **P2.4** — Titles in markdown links must escape `(`, `)`, `]`, and strip
  newlines to prevent link-attribute injection

The fix session added the protective helpers:

```python
# Added to renderer.py — both visible at module level
from urllib.parse import quote          # for URL encoding
def _sanitize_inline(text: str) -> str: # escapes ], (, ), strips \n
    ...
```

But `_entity_line()` — the only function that builds `[title](path)` links —
was never updated:

```python
def _entity_line(entity: Entity) -> str:
    # ❌ Still uses .replace("]", "\\]") — not _sanitize_inline()
    title = (entity.title or entity.slug).replace("]", "\\]")
    # ❌ Still raw string — quote() is imported but never called
    path_str = str(entity.path).replace("\\", "/")
    ...
```

Both functions were dead code. The vulnerabilities were still present. The
prior review session marked both findings as `fixed` in the frontmatter —
incorrectly.

A companion bug in `edge_detector.py`: `_resolve_path()` correctly guarded
**relative** paths with `.resolve()` but passed unresolved `Path` objects
for absolute inputs, making the traversal guard lexical-only for absolute
paths like `/project/root/../../../etc/passwd`.

```python
# ❌ Absolute paths bypass .resolve() — dotdot not normalized
resolved = p if p.is_absolute() else (root / p).resolve()
```

## Root Cause

**Last-mile wiring failure**: the fix session correctly identified what to
build (helper functions) and built them, but did not update the call site.
This is the mirror image of a missing-function bug — instead of "called but
not defined", it is "defined but not called".

The pattern appears whenever a fix is structured as:
1. Extract the protective logic into a standalone helper.
2. (Forgotten) Update every call site to invoke the helper.

Step 2 is easily missed, especially in long fix-triage sessions covering many
findings, because the file passes a grep/import check ("yes, `quote` is
imported") and the helper definition exists ("yes, `_sanitize_inline` is
defined"). The call site is not re-read.

For `_resolve_path`, the gap was subtler: `.resolve()` was applied to relative
paths but the `if p.is_absolute()` branch short-circuited it. The existing
tests only exercised the relative-path traversal case.

## Solution

**`renderer.py`** — wire both helpers into `_entity_line()`:

```python
def _entity_line(entity: Entity) -> str:
    # ✅ Use _sanitize_inline — escapes ], (, ), strips newlines
    title = _sanitize_inline(entity.title or entity.slug)
    # ✅ Use quote — percent-encodes spaces, parens, and other unsafe chars
    path_str = quote(str(entity.path).replace("\\", "/"), safe="/#-_.")
    ...
```

**`edge_detector.py`** — apply `.resolve()` for absolute paths too:

```python
# ✅ Both branches normalize dotdot components before the prefix check
resolved = p.resolve() if p.is_absolute() else (root / p).resolve()
```

**Tests added** to guarantee convergence:
- `test_renderer.py::TestEntityLineSanitization` — 6 tests: parens in title
  escaped, closing bracket escaped, newline stripped, space in path → `%20`,
  parens in path → `%28`/`%29`
- `test_edge_detector.py::TestResolvePath::test_absolute_path_with_dotdot_returns_none`
- `test_edge_detector.py::TestDecidedFromEdges::test_traversal_path_in_brainstorm_produces_no_edge`
  (integration test through `detect_edges()`, not just the helper)

The verify pass caught this because it re-read `_entity_line()` and noticed
`quote` was imported but grep-confirmed zero calls.

## Prevention

**1. Verify the call site, not just the module** — when adding a helper as a
fix, immediately verify the call site uses it by reading the calling function
immediately after writing the helper. "Is `quote` imported?" is not the right
check — "Is `quote` called in `_entity_line()`?" is.

**2. Write call-site tests before writing the helper** — a failing test for
"`test_path_with_spaces_url_encoded`" will refuse to pass until `quote()` is
actually called. Helper-first without a call-site test leaves the gap
undetected.

**3. Run `/cg-review mode:verify` after every fix-triage session** — the
verify pass performs a convergence check designed to catch exactly this class
of failure. The suppression policy (suppress P2/P3 on explicitly-fixed scope)
lets the agents focus on what's new without drowning in already-fixed noise.
The P1.1/P1.2 findings in the verify review were directly attributable to the
agents re-reading `_entity_line()` and noticing the dead imports.

**4. Flag dead-code imports in code review** — an `import quote` with zero
call sites is a `ruff F401` unused-import warning. If the project runs
`ruff check`, this class of gap would be caught automatically at CI time.

## Related

- `.cg-docs/solutions/bugs/2026-05-19-python-warnings-catch-warnings-scope-excludes-root-call.md`
  — same class of bug: the protective context (`catch_warnings`) was positioned
  around the wrong call site (`render_brain` instead of `build_brain`), leaving
  the actual warning-emitters uncovered.
- `.cg-docs/solutions/testing-patterns/2026-05-01-fix-triage-prompt-changes-need-co-authored-tests.md`
  — co-authoring tests with fixes prevents exactly this gap.
