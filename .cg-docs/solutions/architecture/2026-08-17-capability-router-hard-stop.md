---
date: 2026-08-17
category: architecture
tags: [manifest, capability-router, hard-stop, context-efficiency]
related: [".cg-docs/plans/2026-08-13-manifest-driven-skill-loading.md"]
---

# Manifest-Aware Capability Router: Hard-Stop Pattern

## Problem

When a command explicitly requests a capability (by id, task trigger, or
skill reference) that is not active in the project manifest, the system
should stop with an actionable message rather than silently falling back
to all-skill global source or continuing with degraded output.

## Solution

Implement a `route_capability()` function that:

1. Loads the active manifest (with staleness guard)
2. Finds the capability record in the module registry by id
3. Checks if the owning module is in the manifest's module closure
4. If inactive, returns a structured `RouteResult` with:
   - `capability_id`: the requested capability
   - `inactive_reason`: why it's absent (selector mismatch, suite
     ineligibility, or module not in closure)
   - `selector`: the authoritative config selector (field/operator/value)
   - `remedy`: the exact `compound-gpid.local.md` field change and
     `cg-update` command needed

The router is read-only — it never writes or modifies the manifest.

## Hard-Stop Behavior

When `route_capability()` returns `found: false`:
- Stop before doing any work
- Display the inactive reason and remedy
- Do NOT silently fall back to global source
- Do NOT write a transient session projection
- Do NOT alter configuration

## Inventory Leak Detection

The `check_inventory_leaks()` function scans all active assets for
references to inactive assets (those outside the selected module closure).
It uses the same canonical runtime reference regex as the target closure
tests to detect `.github/prompts/`, `.github/skills/`, `.github/agents/`,
`.github/instructions/`, and `.github/shared/` paths.

## Verification

```bash
python -m pytest scripts/tests/test_skill_catalog.py::TestCapabilityRouter -q
python -m pytest scripts/tests/test_skill_catalog.py::TestInventoryLeaks -q
```
