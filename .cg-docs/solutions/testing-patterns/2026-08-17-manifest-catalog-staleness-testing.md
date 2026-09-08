---
date: 2026-08-17
category: testing-patterns
tags: [manifest, catalog, staleness, testing, capability-router]
related: [".cg-docs/plans/2026-08-13-manifest-driven-skill-loading.md"]
---

# Manifest-Backed Catalog: Staleness Guard Testing Pattern

## Problem

The `cg_skill_catalog.py` catalog has a staleness guard that compares the
on-disk manifest's immutable selection fields against a freshly resolved
manifest. This makes unit testing difficult because test fixtures with
hardcoded digests will always fail the staleness comparison against the real
resolver.

## Solution

Separate structural validation from source-revision staleness comparison
using a `skip_stale_check` parameter:

1. `_load_manifest(root, *, skip_stale_check=False)` — always validates
   manifest structure (header, required fields, digest format), but only
   runs the expensive `manifest_stale()` comparison when
   `skip_stale_check` is `False`.

2. Tests that verify catalog logic (build, filter, format, route, leak
   check) pass manifest and registry dicts directly to `build_catalog()`
   and `route_capability()`, bypassing `_load_manifest` entirely.

3. CLI integration tests use `--skip-stale-check` to test the full CLI
   path without requiring a real resolved manifest.

4. The default production path always performs the stale check.

## Key Design Decisions

- **Staleness guard is a CLI-layer concern**: the catalog builder and
  router accept pre-loaded manifest/registry dicts, making them testable
  in isolation.
- **`--skip-stale-check` is a testing convenience**: it is documented as
  such and should not be used in production workflows.
- **Compact output must not spill extended fields**: verified by
  `test_compact_format_no_spill` which checks that the compact table
  header does not contain FULL_EXTRA_FIELDS names.

## Verification

```bash
python -m pytest scripts/tests/test_skill_catalog.py -q
# 35 passed, 1 skipped
```
