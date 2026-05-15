---
date: 2026-05-14
title: "git merge-base can return multiple ancestors — always take the first line"
category: "git-workflows"
language: "both"
tags: [git, merge-base, PowerShell, bash, prompt-design, branch-detection, cg-commit-push-pr, cg-verify-pr]
root-cause: "git merge-base can output more than one hash when multiple merge bases exist; scripts that assign the raw output to a variable get a multi-element array instead of a string"
severity: "P2"
---

# git merge-base can return multiple ancestors — always take the first line

## Problem

Scripts and prompt instructions that compute the branch point with:

```powershell
$mergeBase = git merge-base HEAD <default-branch>
```

assume `git merge-base` returns exactly one hash. In repositories with a complex
merge history (e.g., after an octopus merge or a criss-cross merge), the command
can return **multiple SHA hashes on separate lines**. When assigned directly:

- PowerShell: `$mergeBase` becomes a `string[]` array; subsequent commands such as
  `git diff $mergeBase..HEAD` receive `"sha1 sha2"` (space-joined) and fail or
  produce wrong output.
- bash: `MERGE_BASE=$(git merge-base HEAD main)` captures a newline-delimited
  string; commands using it unquoted get word-split.

Discovered as P2.3 in the `cg-commit-push-pr`/`cg-verify-pr` thorough review.

## Root Cause

`git merge-base` outputs one line per common ancestor when called without `--all`.
The default mode already selects the "best" common ancestor, but in rare DAG
topologies with symmetric criss-cross merges it can emit more than one. The
assignment pattern silently captures all lines.

## Solution

**PowerShell** — pipe through `Select-Object -First 1`:

```powershell
$mergeBase = (git merge-base HEAD $defaultBranch) | Select-Object -First 1
```

**bash/zsh** — pipe through `head -n 1`:

```bash
merge_base=$(git merge-base HEAD "$default_branch" | head -n 1)
```

Both idioms are safe even when only one hash is returned.

## Prevention

- Any prompt instruction or script that calls `git merge-base HEAD <branch>` must
  immediately pipe the output through the first-line guard.
- Canonical template for PowerShell prompts:
  ```
  $mergeBase = (git merge-base HEAD <default-branch>) | Select-Object -First 1
  ```
- Add a test assertion to verify the `Select-Object -First 1` guard appears in
  any `.prompt.md` that uses `git merge-base`:
  ```powershell
  It "takes only the first line of git merge-base output" {
      ($content -match 'merge-base.*Select-Object -First 1|head -n 1.*merge-base') | Should -Be $true
  }
  ```

## Related

- `.cg-docs/solutions/git-workflows/2026-03-04-git-pull-stderr-swallowed-by-redirect.md`
- `.cg-docs/solutions/testing-patterns/2026-05-14-sibling-prompt-symmetry-guard-audit.md`
