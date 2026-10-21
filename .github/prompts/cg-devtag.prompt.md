---
description: "Create a dev tag (v<MAJOR>.<MINOR>.<PATCH>.9000+) on the current branch and push it to origin. Enables end-to-end installation testing via cg-update before an official release. Developer-only."
# Model: Haiku 4.5 — 3 git commands with clear rules; reasoning=2, creativity=1. See docs/model-guide.md (2026-04-07 audit).
---

# Dev Tag

You are a senior developer creating a pre-release dev tag for end-to-end installation testing.

> **Developer-only prompt.** Dev tags follow the convention `v<MAJOR>.<MINOR>.<PATCH>.<DEV>` where DEV starts at 9000. They are accepted by `cg-update` but are invisible to regular users in `--list` output and the "Newer release available" hint.

## Process

> **Developer-tool note**: This prompt operates on the compound-gpid tool repo itself, not a user project. No project charter to read at session start.

### Step 1: Fetch latest tags

Run:

```powershell
git fetch origin --tags
```

Ensures you see all existing dev tags created by other developers before choosing the next increment number. Prevents two developers from accidentally assigning the same tag.

### Step 2: Find the base version

Run:

```powershell
git describe --tags --abbrev=0
```

- If it succeeds, that is the latest tag (e.g. `v0.1.0`).
- If it fails (no tags yet), use `v0.0.0` as the base.

Parse the 3-component base: `v<MAJOR>.<MINOR>.<PATCH>`. This becomes the prefix for the dev tag.

### Step 3: Find the next dev increment

Run:

```powershell
git tag --list "v<MAJOR>.<MINOR>.<PATCH>.*"
```

(Replace `<MAJOR>.<MINOR>.<PATCH>` with the base from Step 2.)

- If no dev tags exist yet for this base, the next tag is `v<MAJOR>.<MINOR>.<PATCH>.9000`.
- If dev tags exist, find the highest 4th component and increment by 1.
  - Example: `v0.1.0.9000` and `v0.1.0.9001` exist -> next is `v0.1.0.9002`.

### Step 4: Confirm with the user

Present:

```
Current branch:  <branch name>
Latest commit:   <git log --oneline -1>
Dev tag to create: v<MAJOR>.<MINOR>.<PATCH>.<DEV>

Create and push this tag? (yes/no)
```

Wait for confirmation before proceeding.

### Step 5: Create and push the tag

```powershell
git tag v<MAJOR>.<MINOR>.<PATCH>.<DEV>
git push origin v<MAJOR>.<MINOR>.<PATCH>.<DEV>
```

### Step 6: Report

After success, print:

```
Dev tag pushed: v<MAJOR>.<MINOR>.<PATCH>.<DEV>

To test the full installation:
  cg-update v<MAJOR>.<MINOR>.<PATCH>.<DEV>

To clean up after testing:
  git tag -d v<MAJOR>.<MINOR>.<PATCH>.<DEV>
  git push origin --delete v<MAJOR>.<MINOR>.<PATCH>.<DEV>

Note: this tag is invisible to regular users in cg-update --list.
```

## Rules

- Never create a dev tag on `main`. If the current branch is `main`, warn the user and stop.
- Always confirm before pushing -- tags on the remote are public.
- Never modify existing tags. If the intended tag already exists locally or remotely, increment and suggest the next one.

> **See also**: `docs/versioning.md` -- "Dev tags (maintainer-only)" section explains the invisibility guarantees, filtering behavior in `cg-update`, and cleanup steps.
