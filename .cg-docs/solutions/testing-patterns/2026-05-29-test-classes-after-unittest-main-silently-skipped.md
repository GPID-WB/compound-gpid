---
date: 2026-05-29
title: "Test classes defined after unittest.main() are silently skipped on direct execution"
category: "testing-patterns"
language: "Python"
tags: [python, unittest, test-discovery, pytest, main-guard, silent-skip]
root-cause: "A test class defined after 'if __name__ == \"__main__\": unittest.main()' is never registered when the file is run directly — Python calls sys.exit() at unittest.main() before the interpreter reaches the class. Under pytest the module is imported (not run as __main__), so all classes are discovered normally. This creates a pass-in-CI / silently-absent-on-direct-run split."
severity: "P2"
---

# Test Classes After `unittest.main()` Are Silently Skipped on Direct Execution

## Problem

Test classes added below `if __name__ == "__main__": unittest.main()` pass in CI
(pytest discovers them via import) but are silently absent when the file is run
directly with `python test_file.py`. The developer sees green output with a test
count that is too low, but no warning is emitted.

Discovered in `scripts/team_brain/tests/test_pull.py` and `test_distiller.py`
during the Phase 2 verify pass — `TestPullEdgeCases` (7 tests) and
`TestDistillerReviewFindings` (6 tests) were both placed after the main guard
by the fix-triage session that added them.

## Root Cause

When Python executes `python test_file.py`, the module runs as `__main__`. The
interpreter proceeds top-to-bottom: when it reaches `unittest.main()`, it runs
the test suite for all classes registered so far and then calls `sys.exit()`.
Any class defined below that line is **never parsed**.

When pytest imports the file, `__name__` is the module's dotted import path
(not `"__main__"`), so the guard block is skipped entirely and pytest scans all
`class Test*` definitions in the file — including those after the main guard.

This creates a silent split:

| Runner | Sees post-main classes? |
|--------|------------------------|
| `python test_file.py` | ❌ No — exits at `unittest.main()` |
| `pytest test_file.py` | ✅ Yes — import path, guard never fires |
| CI (pytest) | ✅ Yes |

Because CI uses pytest, the gap is invisible until someone runs the file directly
or the CI framework changes.

## Solution

Always place all test classes **before** the `if __name__ == "__main__":` guard.
The guard must be the final non-whitespace block in the file.

**Canonical file structure:**

```python
import unittest
from mymodule import thing_under_test


class TestFoo(unittest.TestCase):
    def test_something(self): ...


class TestBar(unittest.TestCase):           # ← all classes before main guard
    def test_other(self): ...


class TestEdgeCases(unittest.TestCase):     # ← NEW: also before main guard
    def test_edge(self): ...


# Must be last — anything after this line is dead code on direct execution
if __name__ == "__main__":
    unittest.main()
```

**Fixing an existing file:** move the misplaced class above the guard. This is
always safe — `unittest.main()` has no semantic relationship with the classes
above it; it simply runs whatever has been registered by that point.

## Prevention

- **Code review**: treat `if __name__ == "__main__": unittest.main()` as an
  implicit EOF marker — flag any class definition that appears below it.
- **When appending tests**: before committing, scan for `unittest.main()` in the
  file and confirm it is still the last non-blank block.
- **Linting**: `grep -n "class Test" test_file.py` vs `grep -n "unittest.main"
  test_file.py` — if any class line number is greater than the main guard line,
  that class is dead on direct execution.
- **Fix-triage sessions**: when appending new test classes to an existing file,
  always paste above the `if __name__ == "__main__":` line, not below it.

## Related

- `.cg-docs/solutions/testing-patterns/2026-05-26-mock-target-drift-after-api-refactoring.md` — similar "passes CI but silently wrong locally" pattern
- `.cg-docs/solutions/testing-patterns/2026-04-17-exact-count-assertion-prevents-silent-regression-when-test-name-states-count.md` — exact count assertions detect missing tests early
