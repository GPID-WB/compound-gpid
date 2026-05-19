---
date: 2026-05-18
title: "Use git rev-parse for repo detection; guard against detached HEAD state"
category: "git-workflows"
language: "both"
tags: [git, branch, detached-head, prompt-design, guard, repo-detection]
root-cause: "git branch --show-current was used as both a repo-detection test and a branch-name source; it fails silently in two distinct bad states"
severity: "P1"
---

# Use git rev-parse for repo detection; guard against detached HEAD state

## Problem

Two prompts (`/cg-brainstorm` and `/cg-plan`) used `git branch --show-current` as a proxy for detecting whether the workspace is a git repository. The same command was used to obtain the current branch name. This conflates two operations that have different failure modes.

### Failure mode 1: Detached HEAD (empty output, exit 0)

In a detached HEAD state (`git checkout <tag>` or `git checkout <sha>`), `git branch --show-current` exits **0** and returns **empty string**. The prompt treated this as "on a feature branch with name `"` — the model displayed messages like "You're already on ``" and offered to create a branch from that position.

If the user chose to create a new branch, `git checkout -b feat/some-feature` succeeded — but from the wrong base commit (the detached SHA, not `main`). The error was invisible at creation time and surfaced only as confusing merge conflicts later.

### Failure mode 2: git version < 2.22 (exit 1 in a valid repo)

`--show-current` was introduced in git 2.22 (2019). Ubuntu 20.04 ships git 2.25, but some Docker base images and institutional environments still have older versions. On these, the flag causes an "unknown option" error (exit 1) even inside a perfectly valid git repository.

The prompt interpreted this failure as "not a git repo" and offered `git init` — which silently re-initializes an existing repository.

## Root Cause

Using a single command (`git branch --show-current`) for two separate purposes:
1. **Repo detection** — "are we inside a git repository?"
2. **Branch detection** — "what branch are we on?"

These have different natural commands and different failure semantics.

## Solution

**Split into two separate checks with the correct command for each purpose:**

### Step 1: Repo detection

```bash
git rev-parse --git-dir 2>/dev/null   # bash
git rev-parse --git-dir 2>$null       # PowerShell
```

- Exit 0 → we are inside a git repository (`.git/` found at current dir or ancestor)
- Exit non-zero → not a git repo → offer `git init`
- Works on git 1.7+ (universally available)

### Step 2: Branch detection (only after repo is confirmed)

```bash
git branch --show-current    # or: git rev-parse --abbrev-ref HEAD
```

- **Non-empty output** → on a named branch; value is the branch name
- **Empty output (exit 0)** → detached HEAD state → **do not proceed with auto-branching**; warn:
  > "Detected detached HEAD. Cannot safely auto-branch. Reattach to a branch first (`git checkout main`) or pass `--no-branch` to skip branching."

### Revised pre-flight pattern

```
1. Run `git rev-parse --git-dir 2>$null`.
   - If fails → not a git repo → offer `git init`. If user declines → skip step silently.
2. Run `git branch --show-current`.
   - If empty → detached HEAD → warn and skip branching.
   - If non-empty → on named branch → proceed to default-branch check.
```

## Prevention

- **Never use `git branch --show-current` as a repo-detection proxy.** It has two silent failure modes (old git, detached HEAD) that produce incorrect behavior with exit 0.
- **Treat empty output from `git branch --show-current` as a distinct state**, not equivalent to "on an unnamed branch." Empty output = detached HEAD.
- **The canonical two-step pattern** appears in `cg-brainstorm.prompt.md` Step 1.7. Reference it when adding git branching to any other prompt.
- Apply the **sibling-prompt guard symmetry** convention: after adding this guard to one prompt, grep all `.github/prompts/` files for `git branch --show-current` and apply the same fix.

## Related

- `.cg-docs/solutions/testing-patterns/2026-05-14-sibling-prompt-symmetry-guard-audit.md`
- `.cg-docs/solutions/git-workflows/2026-03-05-ps51-stderr-stop-terminates-on-git-informational-output.md`
