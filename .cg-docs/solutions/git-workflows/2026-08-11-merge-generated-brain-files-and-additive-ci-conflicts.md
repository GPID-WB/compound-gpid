---
date: 2026-08-11
title: "Merge strategy for generated Brain files and additive CI matrix conflicts"
category: "git-workflows"
language: "both"
tags: [merge-conflict, generated-files, brain, ci, tests-yml, release, 422]
root-cause: "Generated knowledge artifacts accumulate parallel edits from both branches; manual resolution of 28+ conflict markers in auto-generated JSON/Markdown is error-prone and unnecessary when rebuild scripts exist"
severity: "P2"
---

# Merge Strategy for Generated Brain Files and Additive CI Matrix Conflicts

## Problem

Merging `origin/main` into `refactor-modular-plugin` produced 7 conflicting files:
- `.github/workflows/tests.yml` — both branches added different test entries to the same CI matrix list
- 6 generated Brain/index files (`.cg-docs/BRAIN-01.md`, `BRAIN-02.md`, `BRAIN-log.md`, `BRAIN.md`, `active-state/current.json`, `brain-index.json`) — 28+ conflict regions from parallel knowledge accumulation

Additionally, `create-release.ps1` failed with a GitHub API 422 error when creating a release before pushing the branch to the remote.

## Root Cause

**Generated file conflicts**: Both the modular-architecture work and the main-branch readiness-validator work independently added `.cg-docs/` entries. The Brain rebuild indexes these entries, causing parallel edits to the same generated regions. Manually resolving 28+ conflict markers in auto-generated JSON/Markdown is error-prone, slow, and unnecessary — the rebuild script will regenerate these files correctly from the merged `.cg-docs/` corpus.

**CI matrix conflict**: Both branches independently added test file entries to the `pytest` invocation in `.github/workflows/tests.yml`. These are always additive — no branch removes a test entry.

**Release 422 error**: `create-release.ps1` creates a GitHub release targeting `HEAD`'s commit SHA. If that commit exists only locally, the GitHub API rejects it with `"tag_name is not a valid tag"` and `"target_commitish"` errors because the commit is unreachable on the remote.

## Solution

### Generated Brain files: accept-ours + regenerate

```powershell
# Accept ours for all generated Brain/index files
git checkout HEAD -- .cg-docs/BRAIN-01.md .cg-docs/BRAIN-02.md .cg-docs/BRAIN-log.md .cg-docs/BRAIN.md .cg-docs/active-state/current.json .cg-docs/brain-index.json
git add .cg-docs/BRAIN-01.md .cg-docs/BRAIN-02.md .cg-docs/BRAIN-log.md .cg-docs/BRAIN.md .cg-docs/active-state/current.json .cg-docs/brain-index.json
```

After the merge commit, rebuild the Brain from the merged corpus:
```powershell
# Rebuild brain (picks up all knowledge from both branches)
cg-index --brain
```

### CI matrix conflicts: keep both sides

When both branches add test entries to the same `pytest` list in `tests.yml`, keep all entries from both sides. These are always independent and additive.

### Release 422: push before creating release

```powershell
# Push the branch FIRST so HEAD is reachable on remote
git push origin <branch>
# THEN create the release
.\create-release.ps1 -Tag <tag> -Name "<name>" -NotesFile RELEASE_NOTES.md
```

The release script's isolated preflight runs against a local clone, so it passes even when HEAD is unreachable from GitHub. The API call then fails. This is a timing issue, not a test failure.

## Prevention

1. **Generated files**: Always `git checkout HEAD -- <generated-files>` during merges, then rebuild. Never manually resolve conflict markers in auto-generated artifacts.
2. **CI matrix**: Treat `tests.yml` test lists as set-union during merges — always keep both sides.
3. **Release workflow**: Push the release branch before invoking `create-release.ps1`. The script validates locally but publishes to GitHub, so the remote must have the commit.
4. **Merge order**: When merging a long-lived feature branch that also needs periodic main merges, merge main first, resolve conflicts, commit, push, then create the release — not the reverse.

## Related

- `.cg-docs/solutions/git-workflows/2026-05-14-git-merge-base-multiple-ancestors-take-first-line.md` — merge-base gotcha
- `.kilo/commands/cg-release.md` — release workflow with push-before-publish requirement
