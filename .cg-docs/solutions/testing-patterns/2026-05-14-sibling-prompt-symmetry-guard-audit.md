---
date: 2026-05-14
title: "Sibling-prompt symmetry: apply guard fixes to all prompts with the same operation"
category: "testing-patterns"
language: "both"
tags: [prompt-design, guard-conditions, symmetry, code-review, verify-pass, cg-commit-push-pr, cg-verify-pr]
root-cause: "A guard fixed in one prompt was not mirrored to a sibling prompt with an identical operation, leaving the sibling unguarded"
severity: "P1"
---

# Sibling-prompt symmetry: apply guard fixes to all prompts with the same operation

## Problem

When a P1 review finding adds a guard to prompt A (e.g., "exit-code check after
`git add`"), the fix is scoped to that file. A sibling prompt B that performs the
same operation (also `git add` → `git commit`) is not in scope, so the fix is
never applied there.

This pattern is invisible to per-file testing: all tests for prompt A pass because
the guard is present; all tests for prompt B pass because there were no tests for
the guard. The verify pass is the first time the gap surfaces.

**Example from this session**: P1.1 in the original review added an exit-code check
after `git add` to `cg-commit-push-pr` Step 4. The identical operation in
`cg-verify-pr` Step 4 ("Commit and push fixes") lacked the same check. The verify
pass found it as a new P1.1.

Also found: detached HEAD guard added to both prompts, but only one was tested; null
`statusCheckRollup` guard added but untested; empty `gh run list` guard added but
untested.

## Root Cause

Fix-triage works file-by-file. The finding IDs (`P1.1`, `P2.3`) are anchored to
one file. When a class of bug applies to N files, only the first occurrence is
reported and fixed; siblings with the same structure are never audited.

## Solution

### During fix-triage

When applying a guard fix to a `.prompt.md` file, immediately ask: "Does any sibling
prompt perform the same operation?" Common shared operations:

| Operation | Typically shared across |
|-----------|------------------------|
| `git add` → `git commit` | All commit-writing prompts |
| `git branch --show-current` (detached HEAD check) | All prompts that push |
| `git merge-base HEAD <default>` | All prompts using branch-point diffs |
| `gh pr view` (null/empty result) | All prompts that read PR state |

For each sibling prompt identified, apply the same fix in the same session.

### During review/verify dispatch

When dispatching `@cg-code-quality` or `@cg-testing` agents in verify mode,
include this instruction:
> "For each fix applied in the prior session, check all sibling prompts that
> share the same operation. If a sibling prompt performs the same operation
> (e.g., `git add`, `git push`) without the same guard, report as a new P1."

### Test coverage rule

Every guard added to a `.prompt.md` file during fix-triage must have a companion
Pester test that asserts the guard text appears in the file. The test must be
specific enough to catch the guard being removed independently of other content.

```powershell
# Good — specific to the guard behavior
It "halts after git add failure without attempting git commit (P1.1)" {
    ($content -match 'Verify exit code after.*git add|exit code.*git add') | Should -Be $true
}

# Too broad — "halt" appears in 20 other places
It "handles git add failures" {
    ($content -match 'halt') | Should -Be $true
}
```

## Prevention

- After any fix-triage session that touches prompt files with `git`, `gh`, or
  shell operations: run a mental "sibling audit" before marking the session done.
- Add a `cg-fix-triage` process note: "After applying each guard fix to a
  `.prompt.md`, search for sibling prompts with the same operation using
  `grep_search` on the operation text."
- Verify pass should always check sibling prompts for the same guard class.

## Related

- `.cg-docs/solutions/testing-patterns/2026-05-01-fix-triage-prompt-changes-need-co-authored-tests.md` — co-author tests immediately during fix-triage
- `.cg-docs/solutions/testing-patterns/2026-04-28-prompt-guard-conditions-need-immediate-pester-coverage.md`
- `.cg-docs/solutions/testing-patterns/2026-04-23-verify-mode-suppression-must-be-anchored-to-fixed-finding-scope.md`
