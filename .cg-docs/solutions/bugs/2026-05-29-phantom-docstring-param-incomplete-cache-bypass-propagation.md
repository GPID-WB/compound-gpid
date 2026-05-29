---
date: 2026-05-29
title: "Phantom docstring parameter from incomplete cache-bypass propagation in refactors"
category: "bugs"
language: "Python"
tags: [python, refactoring, docstring, cache, api-surface, propagation, refresh, silent-bug]
root-cause: "When adding a local cache to a helper function, the developer documented 'refresh: bool = False' in the docstring but never added it to the function signature or call sites. The cache bypass is therefore unavailable to callers — a silent functional inconsistency where higher-level refresh=True is honoured for some fetches but not others."
severity: "P2"
---

# Phantom Docstring Parameter from Incomplete Cache-Bypass Propagation

## Problem

After adding a per-project JSONL cache to `_fetch_project_jsonl` (fix P2.3),
the function's `Args:` block was written with `refresh: If True, bypass cache
and fetch from remote.` — but `refresh` was never added to the function
signature or wired in the cache logic.

A caller invoking `pull_from_team_brain(kws, config, refresh=True)` gets a
freshly-fetched `TEAM-BRAIN.md` index (the `refresh` parameter is correctly
propagated to `_fetch_team_brain_index`) but receives stale JSONL pattern
entries (the `refresh` parameter never reaches `_fetch_project_jsonl`). The
caller has no way to know this: the result is a coherent but inconsistent
state — fresh topic index, stale pattern entries.

The phantom docstring line was the only evidence of the intended-but-missing
parameter. It passed code review unnoticed.

## Root Cause

The caching refactor was applied in two conceptual steps:
1. ✅ Add the 1-hour TTL cache read/write logic to `_fetch_project_jsonl`
2. ❌ Add `refresh: bool = False` to the signature and propagate it from
   every call site

The docstring was written with step 2 in mind, but step 2 was omitted.
Because the phantom docstring line looked intentional, the omission was not
caught until the verify pass ran after fix-triage.

## Solution

Whenever adding a cache to a helper that is called from a higher-level function
which already has a `refresh` parameter, propagate the parameter atomically —
signature, body, docstring, and all call sites in one change.

**Complete fix:**

```python
# Function signature — add refresh parameter
def _fetch_project_jsonl(
    config: TeamBrainLocalConfig,
    project_name: str,
    *,
    refresh: bool = False,
) -> List[dict]:
    """...
    Args:
        config: ...
        project_name: ...
        refresh: If True, bypass cache and fetch from remote.
    ...
    """
    cache_file = _cache_dir(config.repo) / f"{project_name}.jsonl"
    # Honour refresh — skip freshness check when caller requests a forced fetch
    if not refresh and _is_cache_fresh(cache_file):
        try:
            content = cache_file.read_text(encoding="utf-8-sig")
        except (OSError, ValueError):
            content = None
    else:
        content = None
    ...
```

**Call site in `pull_from_team_brain`:**

```python
entries = _fetch_project_jsonl(config, project_name, refresh=refresh)
```

## Prevention

- **Atomic propagation rule**: if a helper gains a `refresh`/`force`/`bypass`
  parameter, grep the entire codebase for its callers and update all call sites
  in the same commit. Do not split the change across sessions.
- **Docstring commitment**: writing a parameter in the `Args:` block is a
  commitment to implement it. If you write it as a placeholder, add a
  `# TODO: implement` comment in the body — not a complete-looking docstring line.
- **Review heuristic**: any function whose docstring `Args:` section names a
  parameter not present in the `def` line is a phantom parameter. Flag it immediately.
- **Verify pass**: always run `/cg-review mode:verify` after a fix-triage session
  to catch incomplete propagation before merge. The verify pass specifically
  checks for regressions and incomplete fixes introduced by prior changes.

## Related

- `.cg-docs/solutions/testing-patterns/2026-04-08-cross-cutting-enumeration-propagation-audit.md` — same incomplete propagation pattern across a call chain
- `.cg-docs/solutions/bugs/2026-05-07-python-nonatomic-path-write-use-mkstemp-replace.md` — also found in same caching refactor session
- `.cg-docs/solutions/testing-patterns/2026-05-26-mock-target-drift-after-api-refactoring.md` — verify pass as safety net for incomplete refactors
