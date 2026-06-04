---
date: 2026-05-19
title: "sorted(reverse=True) on compound tuple key reverses all components — use two-pass stable sort for mixed direction"
category: "bugs"
language: "Python"
tags: [sort, sorted, reverse, compound-key, stable-sort, tuple, secondary-sort]
root-cause: "sorted(items, key=lambda e: (date, title), reverse=True) reverses both date (intended: newest-first) and title (unintended: Z→A); the reverse flag applies to the entire compound key"
severity: "P3"
---

# `sorted(reverse=True)` on compound tuple key reverses all components

## Problem

`_write_brain_log()` in `renderer.py` sorted entities newest-first by date, then
alphabetically by title. The implementation used a single `sorted()` call with a
compound key and `reverse=True`:

```python
def _sort_key(e: Entity) -> Tuple[str, str]:
    d = e.date_str or "0000-00-00"
    return (d, e.title.lower())

sorted_entities = sorted(non_features, key=_sort_key, reverse=True)
```

Within each date group, entities appeared in **reverse-alphabetical (Z→A) title order** —
the opposite of the documented intent ("newest first, then alphabetically by title").

The output was visually valid (no crash, no empty output) so the bug was never noticed
until a code review examined the sort semantics.

## Root Cause

Python's `sorted()` with `reverse=True` reverses the **entire comparison**, not just
the primary sort key. When the key returns a tuple `(date, title)`, both components are
compared in reverse: date descending ✓, title descending ✗.

There is no built-in way to specify ascending for one field and descending for another
in a single `sorted()` call. Numeric negation (`-int(date)`) works for date integers
but not for string titles.

## Solution

Use a **two-pass stable sort** — Python's sort is guaranteed stable (preserves relative
order of equal elements):

```python
# Pass 1: sort by secondary key ascending (A→Z title)
sorted_entities = sorted(non_features, key=lambda e: e.title.lower())

# Pass 2: sort by primary key descending (newest-first date)
# Stable sort preserves A→Z title order within each date group.
sorted_entities.sort(key=lambda e: e.date_str or "0000-00-00", reverse=True)
```

Result: entities are newest-first by date; within the same date, A→Z by title.

The `_sort_key` helper function can be removed entirely.

**Alternative for numeric keys**: If the primary key is an integer (e.g., a date
formatted as `YYYYMMDD`), negation works in a single pass:

```python
sorted_entities = sorted(
    non_features,
    key=lambda e: (-int((e.date_str or "00000000").replace("-", "")), e.title.lower()),
)
```

This avoids the two-pass approach but only works when the primary key can be negated.

## Prevention

**Rule**: Never use `sorted(items, key=lambda e: (primary, secondary), reverse=True)` when
you want ascending order on the secondary key. The `reverse` flag is applied to the entire
tuple comparison — there is no per-component direction in a single sort call.

**Mental model**: `reverse=True` is equivalent to multiplying every comparison result by −1.
For a tuple `(a, b)`, both `a` and `b` are reversed — not just `a`.

**Checklist when writing a multi-field sort**:
1. Does each field need the same direction? → Single-pass OK.
2. Do fields need different directions? → Two-pass stable sort, or numeric negation for integers.
3. After writing: read the key tuple aloud: "date DESC, title DESC" — if any component
   direction is wrong, fix it.

## Related

- `scripts/brain/renderer.py:_write_brain_log` — the fixed call site
- [Python docs: Sorting HOW TO](https://docs.python.org/3/howto/sorting.html#sort-stability-and-complex-sorts) — two-pass stable sort pattern
- `.cg-docs/solutions/bugs/2026-05-19-python-warnings-catch-warnings-scope-excludes-root-call.md` — co-discovered in the same verify pass
