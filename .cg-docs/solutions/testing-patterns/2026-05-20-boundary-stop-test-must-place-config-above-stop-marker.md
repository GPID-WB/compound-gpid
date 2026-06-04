---
date: 2026-05-20
title: "Boundary-stop test layout: the guarded item must live ABOVE the stop marker, not at the same level"
category: "testing-patterns"
language: "Python"
tags: [python, pytest, testing, boundary, directory-traversal, walk, config-discovery]
root-cause: "Test placed the config file at the same directory level as the stop marker; the function finds the candidate before evaluating the stop condition, so the guard appears not to fire"
severity: "P2"
---

# Boundary-Stop Test Layout: Config Must Sit Above the Stop Marker

## Problem

A test for `_find_local_config()` was written to verify that the function stops
walking up the directory tree when it encounters a `.git/` directory. The test
created `.git/` and `compound-gpid.local.md` at the **same** level (`tmp_path`),
then started the search from a subdirectory:

```
tmp_path/
  .git/                        ← stop marker
  compound-gpid.local.md       ← config (should NOT be found — wrong assumption)
  subdir/                      ← search starts here
```

The test asserted `result is None`, but the function returned the config. No
regression — the guard was working correctly. The test was simply wrong.

## Root Cause

The function's inner loop has this order of operations for each `parent`:

```python
for parent in [current, *current.parents]:
    candidate = parent / DEFAULT_LOCAL_CONFIG_NAME
    if candidate.exists():
        return candidate          # ← check 1: found the file
    if (parent / ".git").exists() or (parent / "compound-gpid.md").exists():
        break                     # ← check 2: stop condition
```

**Candidate check runs before stop check.** When `.git` and
`compound-gpid.local.md` sit at the same directory level (`tmp_path`), the
function reaches that level, finds the candidate first, and returns it — the
stop condition is never evaluated.

The test assumed `.git` would *block* the config at the same level. It doesn't:
the stop condition only prevents climbing to levels **above** the `.git` marker.

## Solution

Place the "should not be found" config **above** the stop marker level, and put
`.git` in a child directory (the boundary project):

```
tmp_path/
  compound-gpid.local.md        ← ancestor config (should NOT be found)
  project/
    .git/                        ← stop boundary (at this project's root)
    subdir/                      ← search starts here
```

Walking up from `subdir`:
- `subdir` → no candidate → no `.git` → continue
- `project` → no candidate → `.git` exists → **break**
- Return `None` ✓

The config at `tmp_path/compound-gpid.local.md` is never reached.

```python
def test_find_local_config_stops_at_git_boundary(tmp_path):
    (tmp_path / "compound-gpid.local.md").write_text(MINIMAL_MD, encoding="utf-8")
    project = tmp_path / "project"
    project.mkdir()
    (project / ".git").mkdir()
    subdir = project / "subdir"
    subdir.mkdir()
    result = _find_local_config(start=subdir)
    assert result is None
```

## Prevention

**Rule for boundary-stop tests**: When a function walks upward until it hits a
stop condition, the "should not be found" item must be placed in a directory
that is **only reachable by passing through the stop marker**. If it's at the
same level as the marker, the function may find it before reaching the marker.

**Mental model**: Draw the directory tree and trace the loop. At each level,
ask: "Does the candidate exist first? If yes, is it the one I want to block?"

**Template layout** (works for `.git`, `compound-gpid.md`, or any other
sentinel file used as a stop condition):

```
root/
  ancestor-config.yml     ← must NOT be returned — above the stop
  child-project/
    .git/                  ← stop marker at this level
    src/                   ← search starts here (can be deeper)
```

For the sibling test (config AT the stop marker — should be found):

```
root/
  .git/                    ← stop marker
  config.yml               ← AT the stop level — found before stop fires ✓
  subdir/                  ← search starts here
```

## Related

- `scripts/team_brain/config.py` — `_find_local_config()` implementation
- `scripts/team_brain/tests/test_config.py` — the corrected test
- `.cg-docs/solutions/testing-patterns/2026-04-21-test-fixture-must-match-function-input-contract.md`
  — related: test fixtures must accurately model the function's input contract
