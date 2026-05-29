---
date: 2026-05-29
title: "Python circular import: brain/__init__.py cannot promote lazy sub-module imports to top-level"
category: "bugs"
language: "Python"
tags: [circular-import, brain, architecture, lazy-import, refactor]
root-cause: "brain sub-modules import Entity from brain.__init__; promoting scanner/extractor/etc to top-level imports creates a cycle before Entity is defined"
severity: "P2"
---

# Python circular import: brain/__init__.py cannot promote lazy sub-module imports to top-level

## Problem

`scripts/brain/__init__.py` has lazy sub-module imports inside `build_brain()`:

```python
def build_brain(...):
    # Lazy imports required to avoid circular-import
    from brain.scanner import scan_all, scan_roadmap    # noqa: PLC0415
    from brain.extractor import extract_keywords        # noqa: PLC0415
    from brain.clusterer import cluster_topics          # noqa: PLC0415
    from brain.edge_detector import detect_edges        # noqa: PLC0415
    ...
```

A code review (P2.11) correctly flagged this as a code smell: intra-function
imports are generally avoided because they hide `ImportError` until runtime
and prevent static analysis. The fix attempted to promote them to module
top-level. This caused an immediate test failure:

```
ImportError: cannot import name 'Entity' from partially initialized module 'brain'
(most likely due to a circular import)
```

All 6 brain test files failed at collection time — pytest never ran a single test.

## Root Cause

The circular import chain is:

1. Python starts importing `brain` (i.e., `brain/__init__.py`)
2. `brain/__init__.py` (at module level) tries to import `from brain.scanner import scan_all`
3. `brain/scanner.py` does `from brain import Entity` at its own module level
4. But `brain/__init__.py` hasn't finished loading yet — `Entity` is not yet defined
5. `ImportError: cannot import name 'Entity' from partially initialized module 'brain'`

The same cycle exists for `brain.extractor`, `brain.clusterer`, and `brain.edge_detector`
— all four sub-modules import `Entity`, `Topic`, `Edge`, or `BrainData` directly from
the `brain` package namespace.

The lazy imports were NOT dead code or left-over scaffolding. They were architecturally
necessary from day one.

## Solution

Revert the attempted promotion — keep the lazy imports inside `build_brain()`. Update
the comment to explain WHY, so the next reviewer doesn't repeat the mistake:

```python
def build_brain(root: Path | str = ".", ...) -> BrainData:
    """..."""
    # Lazy imports required to avoid circular-import: scanner/extractor/etc
    # import Entity from this module. Importing them at module level would
    # create a cycle before Entity is defined.
    # To eliminate the lazy imports, first move Entity/Topic/Edge/BrainData
    # to a separate brain._types module and have __init__.py re-export them.
    from brain.scanner import scan_all, scan_roadmap    # noqa: PLC0415
    from brain.extractor import extract_keywords        # noqa: PLC0415
    from brain.clusterer import cluster_topics          # noqa: PLC0415
    from brain.edge_detector import detect_edges        # noqa: PLC0415
```

Add `# noqa: PLC0415` to suppress the ruff/pylint import-not-at-top-of-file
warning without triggering a lint failure.

## Proper Long-Term Fix

Extract all data classes (`Entity`, `Topic`, `Edge`, `BrainData`) from
`brain/__init__.py` into a separate `brain/_types.py` (or `brain/_models.py`) module.
Then update every sub-module to import from `brain._types` instead of `brain`:

```python
# brain/_types.py — new module (no dependencies within brain/)
@dataclass
class Entity: ...

@dataclass
class Topic: ...

# brain/scanner.py — change this:
# from brain import Entity
# to:
from brain._types import Entity

# brain/__init__.py — re-export for public API
from brain._types import Entity, Topic, Edge, BrainData  # noqa: F401, E402
```

This eliminates the cycle and allows all imports to live at module top-level.

## Prevention

- Before promoting lazy imports to module level, check whether the imported modules
  do `from <package> import <name>` where `<package>` is the same `__init__.py`.
  If yes, a circular import exists.
- A code review finding recommending "move intra-function imports to module level"
  is safe only when no sub-module imports from the package's `__init__.py`.
- Add the explanatory comment (see Solution above) so the NEXT reviewer understands
  the constraint without having to reproduce the failure.

## Related

- `scripts/brain/__init__.py` — the `# noqa: PLC0415` suppressors on the lazy imports
  are load-bearing; removing them without the `brain._types` refactor will cause a
  circular import.
- `.cg-docs/reviews/2026-05-20-team-brain-batch-d-review-3.md` — P2.11 is open,
  blocked by this architectural constraint.
- Python docs: [Circular imports](https://docs.python.org/3/faq/programming.html#what-are-the-best-practices-for-using-import-in-a-module)
