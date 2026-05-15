---
date: 2026-05-14
title: "git log without --first-parent double-counts upstream merge commits when measuring branch-local work"
category: "git-workflows"
language: "both"
tags: [git, git-log, first-parent, branch-commits, merge-commits, cg-verify-pr, ci]
root-cause: "git log <base>..HEAD without --first-parent traverses both sides of any merge, counting commits from upstream branches that were merged in"
severity: "P2"
---

# git log without --first-parent double-counts upstream merge commits when measuring branch-local work

## Problem

When counting commits authored **on the current branch** since a branch point,
the common pattern:

```powershell
git log --oneline --grep="^fix(ci):" $mergeBase..HEAD
```

silently includes commits from any merged-in upstream branches. If `main` was
rebased into the feature branch via a merge commit, all commits reachable from
`main` between `$mergeBase` and `HEAD` are also included — inflating the count.

**Example**: A feature branch with 1 `fix(ci):` commit, merged with an upstream
`main` that has 3 unrelated commits, reports **4** `fix(ci):` commits if any of
those upstream commits happen to match the grep pattern (unlikely but possible),
and more subtly produces **wrong commit ordering** even without a pattern match.

In `cg-verify-pr`, this caused the 2-round cap check to potentially fire
prematurely: the `git log --grep="^fix(ci):"` count included upstream commits
that happened to match the pattern. Discovered as P2.2 in the
`cg-commit-push-pr`/`cg-verify-pr` thorough review.

## Root Cause

`git log <base>..HEAD` uses reachability — it includes all commits reachable
from `HEAD` but not from `<base>`. After a `git merge origin/main` (non-rebase
flow), commits from `origin/main` are reachable from `HEAD`. Without
`--first-parent`, the traversal follows both sides of the merge commit.

`--first-parent` restricts traversal to the mainline of the branch — i.e., only
the commits made directly on the feature branch, not those merged in from
upstream.

## Solution

Add `--first-parent` to any `git log` command intended to count or list
**branch-local commits**:

```powershell
# Count fix(ci): commits on this branch only
git log --oneline --first-parent --grep="^fix(ci):" $mergeBase..HEAD
```

```bash
git log --oneline --first-parent --grep="^fix(ci):" "$merge_base..HEAD"
```

`--first-parent` is safe even on linear histories (no merge commits) — it has
no effect when there is nothing to filter.

## Prevention

- Any prompt step that counts commits since a branch point to enforce a cap
  (e.g., round limits, rebase guards) must use `--first-parent`.
- Any prompt step that lists "what changed on this branch" for display purposes
  should also use `--first-parent` to avoid showing upstream history.
- Canonical template:
  ```
  git log --oneline --first-parent --grep="<pattern>" $mergeBase..HEAD
  ```
- Test signal:
  ```powershell
  It "uses --first-parent when counting branch-local commits" {
      ($content -match 'first-parent') | Should -Be $true
  }
  ```

## Related

- `.cg-docs/solutions/git-workflows/2026-05-14-git-merge-base-multiple-ancestors-take-first-line.md`
- `.cg-docs/solutions/testing-patterns/2026-05-14-sibling-prompt-symmetry-guard-audit.md`
