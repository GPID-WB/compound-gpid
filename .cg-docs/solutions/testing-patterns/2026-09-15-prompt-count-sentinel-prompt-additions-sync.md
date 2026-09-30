---
date: 2026-09-15
title: "Prompt-count sentinel in model-assignments tests must change with every .github/prompts/*.prompt.md addition"
category: "testing-patterns"
language: "both"
tags: [pester, model-assignments, sentinel, prompt-inventory, cg-help, contract]
root-cause: "tests/model-assignments.Tests.ps1 pins the exact count of .github\\prompts\\*.prompt.md files; adding a prompt file without updating the sentinel breaks the full gate with 'Expected 32, but got 33'"
severity: "P2"
plan: ".cg-docs/plans/2026-09-08-evidence-backed-cg-help-command.md"
reviewed-in: ".cg-docs/reviews/2026-09-08-evidence-backed-cg-help-command-review.md"
related: [".cg-docs/solutions/testing-patterns/2026-04-08-new-prompt-agent-addition-checklist.md", ".cg-docs/solutions/testing-patterns/2026-04-17-exact-count-assertion-prevents-silent-regression-when-test-name-states-count.md", ".cg-docs/solutions/testing-patterns/2026-05-22-skill-agent-forbidden-pattern-table-must-be-kept-in-sync.md"]
---

# Prompt-Count Sentinel in Model-Assignments Tests Must Change With Every `.github/prompts/*.prompt.md` Addition

## Problem

The Step 7 full Pester gate (`2026-09-14T19:29:01Z` – `19:32:15Z`) failed
with a genuine, StrictMode-independent regression:
`tests\model-assignments.Tests.ps1:12-13` asserts
`$promptFiles.Count | Should -Be 32` over
`.github\prompts\*.prompt.md`, but the directory held 33 files because
Step 7 added `.github/prompts/cg-help.prompt.md` without updating the
sentinel. Failure message: `Expected 32, but got 33`. The sentinel update
`32 -> 33` was resolved by explicit user decision `D5` (recorded
`2026-09-14T19:42Z`) and applied at `tests/model-assignments.Tests.ps1:13`;
the corrected full gate then ran model-assignments green (210/210) and the
full suite passed 2,845/2,843/0/2.

## Root Cause

The model-assignments suite pins the exact number of canonical prompt files
as a completeness sentinel. A plan-authorized prompt addition changed the
inventory but the sentinel was not part of the same change set, so the full
gate caught the drift as an assertion failure rather than accepting the
inventory silently. The inventory equality was later pinned to all 33
prompts in the review fix `P1.2`
(`scripts/tests/test_help_catalog.py`).

## Solution

Change the sentinel expected value in the same change set that adds the
prompt file, preserving every other byte and assertion:

```powershell
$promptFiles.Count | Should -Be 33
```

Follow the recorded D5 pattern for scoped approvals: record the decision and
exact scope first, apply only the one-value edit, then rerun the full gate
once with a harness-isolated runner.

## Prevention

- Maintain an explicit prompt-inventory contract: every
  `.github/prompts/*.prompt.md` addition/deletion must ship with the
  matching `tests/model-assignments.Tests.ps1` sentinel change in the same
  change set.
- Extend the existing prompt/agent addition checklist
  (`.cg-docs/solutions/testing-patterns/2026-04-08-new-prompt-agent-addition-checklist.md`)
  with the sentinel line.
- When adding inventory-pinning sentinel tests, keep the count assertion and
  the inventory source it counts coupled and reviewed together.

## Related

- `.cg-docs/solutions/testing-patterns/2026-04-08-new-prompt-agent-addition-checklist.md` — prompt/agent addition checklist
- `.cg-docs/solutions/testing-patterns/2026-04-17-exact-count-assertion-prevents-silent-regression-when-test-name-states-count.md` — exact-count sentinel pattern
- `.cg-docs/solutions/testing-patterns/2026-05-22-skill-agent-forbidden-pattern-table-must-be-kept-in-sync.md` — sibling kept-in-sync contract