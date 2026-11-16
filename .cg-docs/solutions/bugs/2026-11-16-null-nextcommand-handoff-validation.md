---
date: 2026-11-16
title: "Active-state handoff validation crashes on a null nextCommand"
category: "bugs"
type: "bug"
language: "Python"
tags: [active-state, nextCommand, null, handoff, pytest, publication-preflight]
root-cause: "The handoff test assumed a string; dict.get's default does not replace an explicit JSON null before lower()."
severity: "P2"
test-written: "yes"
fix-confirmed: "yes"
red-phase-confirmed: "yes"
expected-behavior-source: "user-requirement"
test-gap: "edge-case-gap"
---

# Active-State Handoff Validation Crashes On A Null nextCommand

## Symptom

The prepare publication gate failed in
`TestActiveStateIntegrity.test_handoff_targets_dev_branch` in
`scripts/tests/test_issue_dispatch.py`. The completed active-state record had
`"nextCommand": null`, and the test raised
`AttributeError: 'NoneType' object has no attribute 'lower'` instead of accepting
the nullable value.

## Expected Behavior Source

**User requirement:** accept the nullable handoff value according to the
active-state contract while retaining rejection of main-only string handoffs.
The user explicitly required preserving the completed Plan, Work Report,
active-state record, and accepted completion exceptions.

The requirement is corroborated by
`.kilo/shared/active-state.contract.md`, whose required-field section permits
null values while requiring the `nextCommand` key to be present. Existing
case-insensitive dev/main string validation remains unchanged. No new handoff
or schema policy is inferred from the buggy test.

## Root Cause

`json.loads(text).get("nextCommand", "")` returns its fallback only when the key
is missing. An explicit JSON null becomes Python `None`, which has no `.lower()`
method. The test handled missing keys and strings but not this permitted boundary.

## Reproduction Test

The existing `test_handoff_targets_dev_branch` was run before correction and
failed with the reported exception: **1 failed in 0.21 seconds**. The user
confirmed this failing reproduction before diagnosis, then approved the diagnosis.

Before changing the validator, nine parameterized cases were added in
`TestActiveStateIntegrity.test_handoff_command_cases` in the same file. Running
the class produced **2 failed, 10 passed**: the real completed record and the
isolated null fixture both failed with the same exception. All string cases,
including rejection of main-only commands, already behaved as expected.

## Test Gap

**edge-case-gap:** the nullable command boundary lacked an isolated regression
case. The check depended on the current repository record, so a string-valued
record concealed the assumption until completion supplied a null value.

The new cases cover a missing key, null, an empty command, a command without a
branch reference, dev/DEV handoffs, rejected main/MAIN-only handoffs, and a dev
handoff that also mentions main. Expected outcomes come from the user requirement
and the preserved assertion, not from copying the validator's output.

## Fix

Normalize only `None` before the existing assertion:

```python
next_cmd = json.loads(text).get("nextCommand", "")
if next_cmd is None:
    next_cmd = ""
assert "main" not in next_cmd.lower() or "dev" in next_cmd.lower(), (
    "nextCommand must reference dev, not main"
)
```

This does not coerce every false-like or non-string value. The existing branch
assertion and its message are unchanged. Regression fixtures use `tmp_path` and
a scoped monkeypatch of `ACTIVE_STATE`; they do not rewrite the actual record.

Red-green proof after correction:

- Original reproducer: **1 passed in 0.16 seconds**.
- Entire affected test file: **92 passed in 0.30 seconds** (83 pre-existing,
  9 new), with zero regressions.
- `git diff --check` passed.
- Completed Plan, Work Report, and active-state Git-blob fingerprints matched
  their pre-fix values.

The user explicitly confirmed the verified fix before this document was created.
These are focused bug-fix results, not a claim that the full prepare/committed
publication gates have passed. Those gates must be rerun before publication.

## Lessons Learned

For optional JSON fields, test both a missing key and an explicit null;
`dict.get(key, default)` does not make those inputs equivalent. Normalize only
the permitted boundary and retain negative cases proving that the original
policy is still enforced. Do not alter valid workflow state merely to satisfy
a string-only assumption in an integrity test.

## Related

- `.kilo/shared/active-state.contract.md`
- `scripts/tests/test_issue_dispatch.py`
- `.cg-docs/plans/2026-11-12-reviewed-cg-agent-coordinator.md`
