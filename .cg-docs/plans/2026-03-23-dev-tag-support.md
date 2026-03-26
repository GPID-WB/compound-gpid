---
date: 2026-03-23
title: "Dev-tag support -- allow 4-component pre-release tags for testing"
status: completed
brainstorm: ~
language: "both"
estimated-effort: "small"
tags: [versioning, testing, dev-workflow, update, tags]
---

# Plan: Dev-Tag Support

## Objective

Allow the maintainer to create and test 4-component "dev tags" (e.g.
`v0.1.0.9000`) via `cg-update` without exposing them to end users. This enables
full end-to-end installation testing of pre-release commits before merging to
`main` and creating an official 3-component release.

## Context

Today `cg-update` enforces a strict `v<MAJOR>.<MINOR>.<PATCH>` format:

- The validation regex `^(latest|v\d+\.\d+\.\d+)$` rejects 4-component tags.
- `--list` shows all `v*` tags including any dev tags if they existed.
- `$latestTag` (used for the "Newer release available" hint) is the first tag in
  `--sort=-version:refname` order -- a dev tag like `v0.1.0.9000` would sort
  above `v0.1.0` and leak into the hint.

The convention follows R's development version pattern: `MAJOR.MINOR.PATCH.DEV`
where DEV >= 9000 signals "development snapshot, not for general use". The 4th
component makes it visually distinct from official releases.

**Design principle**: dev tags are a power-user escape hatch. Normal users must
never see them in `--list`, in hints, or in error suggestions.

## Implementation Steps

### 1. Widen the validation regex to accept 4-component tags

- **File**: `scripts/update.ps1` (~line 118)
- **Change**: Update the regex from:
  ```
  ^(latest|v\d+\.\d+\.\d+)$
  ```
  to:
  ```
  ^(latest|v\d+\.\d+\.\d+(\.\d+)?)$
  ```
  This accepts both `v0.1.0` (release) and `v0.1.0.9000` (dev).
- **Error message**: Update the error text to mention the dev format:
  ```
  Expected a tag like 'v0.2.0' (or 'v0.2.0.9000' for dev), 'latest', or use --list to browse.
  ```
- **Tests**: Update `tests/update.Tests.ps1`:
  - Change the "rejects a 4-segment tag" test to "accepts a 4-segment dev tag".
  - Add a test that rejects `v0.2.0.` (trailing dot, no 4th number).
  - Add a test that rejects `v0.2.0.1.2` (5 segments).
- **Acceptance criteria**: `cg-update v0.1.0.9000` passes validation.

### 2. Filter dev tags from `--list` output

- **File**: `scripts/update.ps1` (~line 154, the `--list` branch)
- **Change**: After fetching `$tags`, filter to 3-component only for display:
  ```powershell
  $releaseTags = $tags | Where-Object { $_ -match '^v\d+\.\d+\.\d+$' }
  ```
  Use `$releaseTags` for the display loop. Keep using `$tags` (unfiltered) for
  the `$currentPin` marker -- if the user is pinned to a dev tag, it should still
  show `<-- current` at the bottom or top with a `(dev)` label.
- **Details**: When the user is pinned to a dev tag, show it separately:
  ```
  Available releases:
    v0.2.0
    v0.1.0  <-- current pinned to dev tag v0.1.0.9000
  ```
  Actually, simpler: just show release tags, and if the current pin is a dev tag,
  show the mode label as `v0.1.0.9000 (dev -- not listed above)`.
- **Tests**: Update `tests/update.Tests.ps1` `--list formatting`:
  - Add test: dev tags are excluded from the displayed list.
  - Add test: current dev-tag pin is indicated in the mode label.
- **Acceptance criteria**: `cg-update --list` never shows 4-component tags in the
  release list. If pinned to a dev tag, the status line says so.

### 3. Filter dev tags from `$latestTag` (newer release hint)

- **File**: `scripts/update.ps1` (~line 269, inside pinned-mode branch)
- **Change**: After capturing `$allTags`, derive `$latestTag` from release-only
  tags:
  ```powershell
  $latestTag = $allTags | Where-Object { $_ -match '^v\d+\.\d+\.\d+$' } | Select-Object -First 1
  ```
  This ensures the "Newer release available" hint never suggests a dev tag.
- **Tests**: Update `tests/update.Tests.ps1` "newer release hint":
  - Add test: dev tag at top of sort order is skipped; hint shows next release.
  - Add test: when only dev tags exist, hint is suppressed (`$latestTag = $null`).
- **Acceptance criteria**: A user pinned to `v0.1.0` never sees "Newer release
  available: v0.1.0.9000".

### 4. Filter dev tags from the "not found" error suggestions

- **File**: `scripts/update.ps1` (~line 276, the `$similar` variable)
- **Change**: When building the "Available releases" hint for a bad tag, filter
  to release-only:
  ```powershell
  $similar = $allTags | Where-Object { $_ -match '^v\d+\.\d+\.\d+$' } | Select-Object -First 5
  ```
- **Tests**: Add test in "tag validation" context: dev tags don't appear in
  error suggestions.
- **Acceptance criteria**: Typing `cg-update v9.9.9` never lists dev tags in the
  hint.

### 5. Create the `/cg-devtag` prompt

- **File**: `.github/prompts/cg-devtag.prompt.md` (new file)
- **Purpose**: Creates a dev tag on the current branch and pushes it to origin.
- **Behavior**:
  1. Read the latest tag: `git describe --tags --abbrev=0`
  2. Parse its 3-component base (e.g. `v0.1.0`).
  3. Check for existing dev tags on this base: `git tag --list "v0.1.0.*"`.
  4. If none exist, create `v0.1.0.9000`. If `v0.1.0.9000` exists, increment
     to `v0.1.0.9001`, etc.
  5. Confirm with the user: "Create and push tag `v0.1.0.9000`?"
  6. Run: `git tag v0.1.0.9000 && git push origin v0.1.0.9000`
  7. Print: "Dev tag pushed. Test with: `cg-update v0.1.0.9000`"
- **Scope**: This is a developer-only prompt. It lives in `.github/prompts/`
  (junctioned to all linked projects via `.github/`). This is acceptable because
  the prompt only runs when explicitly invoked by a user who knows it exists.
- **Acceptance criteria**: Running `/cg-devtag` in Copilot Chat creates and
  pushes a dev tag on the current branch with auto-incrementing 4th component.

### 6. Document dev-tag workflow

- **File**: `docs/versioning.md`
- **Change**: Add a "Dev tags" section explaining:
  - Convention: `v<MAJOR>.<MINOR>.<PATCH>.<DEV>` where DEV starts at 9000.
  - Dev tags are invisible to `--list` and the "newer release" hint.
  - How to create: `/cg-devtag` or manually `git tag v0.1.0.9000 && git push origin v0.1.0.9000`
  - How to test: `cg-update v0.1.0.9000`
  - How to clean up: `git tag -d v0.1.0.9000 && git push origin --delete v0.1.0.9000`
- **Acceptance criteria**: `docs/versioning.md` explains the dev-tag workflow.

## Testing Strategy

### Automated (Pester)

All tests are in `tests/update.Tests.ps1`, inline-logic style (no git calls):

1. **Validation regex**: 3-component accepted, 4-component accepted, 5-component
   rejected, trailing-dot rejected, missing-v rejected.
2. **`--list` filtering**: Given `@("v0.2.0", "v0.1.0.9001", "v0.1.0.9000", "v0.1.0")`,
   release-only filter returns `@("v0.2.0", "v0.1.0")`.
3. **`$latestTag` filtering**: Same array, filtered first = `v0.2.0` (not `v0.2.0.9001`).
4. **Newer release hint**: With dev tag at top, hint still points to real release.
5. **Error suggestions**: Dev tags excluded from "Available releases" hint.

### Manual

1. Push a dev tag to the `Stop-Gitignoring-cg-docs` branch.
2. From a linked project, run `cg-update v0.1.0.9000` -- verify full install.
3. Run `cg-update --list` -- verify dev tag is hidden.
4. Run `cg-update latest` -- verify no dev tag leakage.
5. Clean up: delete the remote dev tag after testing.

## Documentation Checklist

- [ ] `docs/versioning.md` -- dev-tag section
- [ ] Inline comments in `update.ps1` where filtering happens
- [ ] `/cg-devtag` prompt is self-documenting

## Risks & Mitigations

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| Dev tag sorts above release tag in git | Certain | Filter with `^v\d+\.\d+\.\d+$` before display/hint |
| User discovers dev tag and pins to it | Low | Works fine -- they just won't see it in `--list`. Intentional: if you know the tag name, you can use it |
| Forgotten dev tags accumulate on remote | Medium | Document cleanup in `docs/versioning.md`; `/cg-devtag` could eventually list and clean old ones |
| `create-release.ps1` accepts dev tags | None | Already enforces `^v\d+\.\d+\.\d+$` -- no change needed |

## Out of Scope

- Auto-cleanup of old dev tags (can be added later).
- CI/CD integration (no CI exists yet).
- Changing the 3-component release format.
- Modifying `create-release.ps1` (it already rejects non-semver tags).
