---
date: 2026-05-29
title: "Warning emission tests need assertWarns — verify pass systematically catches the gap"
category: "testing-patterns"
language: "Python"
tags: [warnings, assertWarns, pytest-warns, verify-mode, test-coverage-gap, warnings-warn]
root-cause: "Adding warnings.warn() to error-handling code does not break existing tests, so tests that only assert the code continues to work silently miss whether the warning was emitted"
severity: "P2"
---

# Warning emission tests need `assertWarns` — verify pass systematically catches the gap

## Problem

A fix-triage session added `warnings.warn(UserWarning, ...)` to four error-handling
paths across `privacy.py`, `pull.py`, and `dedup.py`. All existing tests continued
to pass after the fix — there were no failures.

A subsequent verify pass (`/cg-review mode:verify`) ran `@cg-testing` against the
patched files and found 4 coverage gaps:

| File | Added warning | Test verified skip | Test verified warning |
|------|--------------|-------------------|----------------------|
| `privacy.py` | Unclosed code fence | N/A | ❌ No `pytest.warns` |
| `pull.py` | Malformed JSONL line | ✅ (len assertion) | ❌ No `assertWarns` |
| `dedup.py` | Malformed JSONL line | ✅ (existing test) | ✅ (already had `assertWarns`) |

The pattern: the skip/continue behaviour is tested; the *warning emission* is not.
Since `warnings.warn()` is silent when no `assertWarns` context is active, the test
passed both before and after the fix — making it impossible to know from the test
suite alone that the warning was added.

## Root Cause

`warnings.warn(UserWarning, ...)` does not raise. Existing tests that assert the
function returns the right result (e.g., "1 valid entry returned", "content not
blocked") pass unchanged whether the warning fires or not.

The warning emission is a **side-effect that only tests can verify** — the production
behaviour is invisible to the caller at runtime unless `warnings.simplefilter("error")`
is active.

## Solution

For every `warnings.warn(...)` added to production code, wrap the corresponding test
call in `assertWarns` / `pytest.warns`:

### `unittest.TestCase` pattern

```python
def test_malformed_jsonl_lines_are_skipped(self, mock_fetch, _mock_fresh):
    """Malformed JSONL lines are skipped with a UserWarning; valid lines returned."""
    mock_fetch.return_value = "NOT JSON\n" + _SAMPLE_JSONL_LINE + "\n"
    from team_brain.pull import _fetch_project_jsonl
    with self.assertWarns(UserWarning):        # ← wraps the call
        entries = _fetch_project_jsonl(_CONFIG, "compound-gpid")
    self.assertEqual(len(entries), 1)          # existing assertions preserved
```

### `pytest` (function-based) pattern

```python
def test_regex_unclosed_code_fence_emits_warning():
    """Unclosed code fence emits UserWarning at end of document."""
    content = "Before.\n\n```python\nx = 1\n# no closing fence"
    with pytest.warns(UserWarning, match="[Uu]nclosed"):
        apply_regex_filter(content)
```

Note: `pytest.warns` accepts a `match=` regex for specificity. `assertWarns` does not,
but `assertWarns(UserWarning)` is sufficient to distinguish warning vs. no warning.

## Prevention

**Checklist when adding `warnings.warn(...)` to production code:**

1. Find the existing test that exercises the code path being warned on.
2. Wrap the call in `with self.assertWarns(UserWarning):` (unittest) or
   `with pytest.warns(UserWarning, match="..."):` (pytest).
3. Keep any existing result assertions *outside* the `with` block — they remain valid.
4. If no test exists for that code path, add one (this is the larger gap).

**Why this gap persists**: The fix adds new behaviour (the warning) but existing
tests were written against the old behaviour (silent skip). Adding `assertWarns` is
not forced by any failure — it requires deliberate addition. Code review often misses
it because the *code* change is obviously correct.

**Why verify mode catches it**: `@cg-testing` in verify mode specifically checks
whether fixed findings have their new behaviours tested, not just that the function
continues to work. This is the correct tool for catching this class of gap.

## Related

- `scripts/team_brain/tests/test_pull.py` — `test_malformed_jsonl_lines_are_skipped`
  now wraps in `self.assertWarns(UserWarning)` (fixed 2026-05-29)
- `scripts/team_brain/tests/test_privacy.py` — `test_regex_unclosed_code_fence_emits_warning`
  added (2026-05-29)
- `scripts/team_brain/tests/test_push.py` — `test_api_request_success_path_non_json_body`
  and two `_get_remote_file` 200-missing-field tests added (2026-05-29)
- `.cg-docs/reviews/2026-05-20-team-brain-batch-d-verify-review-3.md` — P2.1–P2.4
  that surfaced these gaps
- `.cg-docs/solutions/bugs/2026-05-19-python-warnings-catch-warnings-scope-excludes-root-call.md`
  — related: `catch_warnings` scope also silently excludes the root caller
