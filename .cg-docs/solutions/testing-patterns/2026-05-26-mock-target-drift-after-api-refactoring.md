---
date: 2026-05-26
title: "Mock target drift: existing mocks bypassed after function split"
category: "testing-patterns"
language: "Python"
tags: [mock, patch, refactoring, api-drift, unittest.mock, github-api, urllib, integration]
root-cause: "Tests mocked _put_remote_file to block GitHub API calls, but a JSONL-first refactor introduced _put_jsonl_with_retry (a new function) as the first write step. The new function was not mocked, so it called the real API and got HTTP 401."
severity: "P1"
---

# Mock target drift: existing mocks bypassed after function split

## Problem

`TestPushEntryLive` in `scripts/team_brain/tests/test_push.py` used
`patch("team_brain.push._put_remote_file")` to prevent the test from
hitting the real GitHub API:

```python
with patch("team_brain.push._put_remote_file") as mock_put:
    result = push_entry(solution_path, config=_CONFIG)
```

After implementing **ADV-P1.3 — JSONL-first write ordering**, `push_entry`
was refactored to call `_put_jsonl_with_retry` (a new function) *before*
`_put_remote_file`. The mock on `_put_remote_file` was still in place and
still patched correctly — but `_put_jsonl_with_retry` was never mocked.

At runtime, `_put_jsonl_with_retry` invoked `_api_request`, which sent a
real HTTPS request to `api.github.com`. The response was HTTP 401
(Unauthorized) because the test token `"fake-token"` has no real GitHub
credentials.

The three `TestPushEntryLive` tests failed:

```
urllib.error.HTTPError: HTTP Error 401: Unauthorized
```

The failure was easy to mis-diagnose as "the mock is missing" when in fact
the mock was present — it was just no longer guarding the first call that
reached the network.

## Root Cause

When a function is refactored so that a **new** function is called **before**
the previously mocked one, the existing mock remains valid but incomplete.
The test has no syntax error, no import error, no missing `patch` call — the
mock is there and would execute correctly. The test simply doesn't know about
the new code path that now runs ahead of the one it guards.

This is a form of **mock target drift**: the mock's target symbol still
exists and still works, but it no longer sits at the boundary between the
test and the external system.

## Solution

Identify the *outermost* function that starts the external call chain and
mock that. When the call chain has two branches (entry PUT + JSONL PUT),
mock both:

```python
def _run_push(self, solution_path, *, existing_entry=None, existing_jsonl=None):
    def fake_get_remote(_owner_repo, path, _token):
        if "entries/" in path and existing_entry:
            return existing_entry
        if "patterns/" in path and existing_jsonl:
            return existing_jsonl
        return None

    with patch("team_brain.push.get_token", return_value="fake-token"):
        with patch("team_brain.push._get_remote_file", side_effect=fake_get_remote):
            with patch("team_brain.push._put_remote_file") as mock_put:
                with patch("team_brain.push._put_jsonl_with_retry") as mock_put_jsonl:
                    result = push_entry(solution_path, config=_CONFIG)
    return result, mock_put, mock_put_jsonl
```

Both `_put_remote_file` (entry) and `_put_jsonl_with_retry` (JSONL) are
mocked. Tests assert on each independently:

```python
def test_creates_new_entry_and_jsonl(self) -> None:
    result, mock_put, mock_put_jsonl = self._run_push(solution)

    self.assertEqual(mock_put.call_count, 1)        # entry via _put_remote_file
    self.assertEqual(mock_put_jsonl.call_count, 1)  # JSONL via _put_jsonl_with_retry
```

## Prevention

**Refactoring rule**: when splitting a function into two (or reordering
calls), immediately grep all test files for `patch("module.old_function")`
and audit whether the new function also reaches the external boundary. If
it does, add a mock for it in the same commit.

**Detection heuristic**: if a test was passing with one mock and begins
failing with HTTP 4xx/5xx or a `ConnectionError` after a refactor, suspect
mock target drift — not a broken test fixture.

**Structural principle**: mocks should guard the *boundary* (network,
filesystem, time), not a *specific internal function*. When the internal
implementation changes, the boundary guard stays valid; a function-specific
mock may not.

**Test helper design**: return mock handles for all mocked callables from
helper methods (e.g., `_run_push`). If the helper only returns some mocks,
a refactor that adds new callables may silently lose coverage.

## Related

- `.cg-docs/solutions/bugs/2026-05-20-fix-helper-written-but-not-wired-into-call-site.md`
  — a complementary failure mode: the helper exists but is never called.
  Both are cases of "the fix looks complete from outside but a hidden code path
  is still unprotected."
- `.cg-docs/solutions/testing-patterns/2026-03-17-httpx-async-client-asgi-transport.md`
  — similar story: HTTP calls in tests must be intercepted at the correct layer.
