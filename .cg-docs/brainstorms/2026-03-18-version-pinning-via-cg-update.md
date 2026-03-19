---
date: 2026-03-18
title: "Version pinning via cg-update"
status: decided
chosen-approach: "Tag-pinning via cg-update with .cg-version file"
tags: [versioning, releases, cg-update, stability, git-tags]
---

# Version pinning via cg-update

## Context

Compound GPID currently tracks `main` HEAD — `cg-update` does a `git pull --ff-only` and every linked project immediately gets the latest code. There is no concept of releases, tags, or version pinning. This creates two problems:

1. **Stability risk**: a broken push to `main` instantly breaks every linked project.
2. **No opt-in experimentation**: beta features cannot be tested by early adopters without exposing everyone.

Users need the ability to install specific releases of the plugin, choosing between stable versions and bleeding-edge.

## Requirements

- Per-user version choice (not per-project). Default is "latest" (track `main`).
- Use GitHub Releases (which create git tags) as the release mechanism.
- Version preference stored in a `.cg-version` file inside the global install directory.
- No new commands — extend `cg-update` with an optional version argument.
- `cg-update --list` to show available releases without visiting GitHub.
- Pinned users stay pinned until they explicitly change; "latest" users auto-update.
- Minimal friction — the less terminal interaction, the better.

## Approaches Considered

### Approach 1: Tag-pinning via `cg-update` with `.cg-version` file (CHOSEN)

Extend `cg-update` to accept an optional version argument. Store the user's choice in a `.cg-version` file inside the global install directory. Use `git checkout` for pinned tags, `git pull --ff-only` for latest.

- `cg-update` (no args) — if `.cg-version` says `latest`, pulls latest `main`. If it says `v0.2.0`, fetches tags and checks out that tag.
- `cg-update v0.2.0` — writes `v0.2.0` to `.cg-version` and checks out that tag.
- `cg-update latest` — writes `latest` to `.cg-version` and pulls latest `main`.
- `cg-update --list` — lists available releases (tags).

**Pros**: Minimal new surface area (no new command). Familiar `cg-update` stays the single entry point. `.cg-version` is simple and inspectable. Supports both stable pins and bleeding-edge tracking.

**Cons**: `cg-update` now has two modes (pull vs. checkout), which adds some complexity to the script. Pinned users must explicitly run `cg-update <new-version>` or `cg-update latest` to adopt a new release.

**Effort**: Small-medium.

### Approach 2: `cg-update` + `cg-releases` companion command

Same as Approach 1, but extract the `--list` functionality into a dedicated `cg-releases` command with richer output (release notes, dates, current indicator).

**Pros**: Cleaner separation of concerns.

**Cons**: One more command to maintain, one more `.cmd` wrapper. Extra overhead for a small team.

**Effort**: Medium.

### Approach 3: Channel-based system (`stable` / `beta` / `main`)

Users pick a channel instead of exact tags. `stable` tracks the latest non-prerelease tag, `beta` tracks the latest prerelease tag, `main` tracks HEAD.

**Pros**: Users don't need to know version numbers.

**Cons**: Requires disciplined semver tagging. More complex version resolution logic. "Channel" concept may confuse users.

**Effort**: Medium-large.

## Decision

Approach 1 — tag-pinning via `cg-update` with `.cg-version` file. Simplest for users, minimal new infrastructure, and channels or richer browsing can be layered on later if needed.

## Next Steps

1. Modify `scripts/update.ps1` to accept an optional positional argument (`latest`, a tag name, or `--list`).
2. Add `.cg-version` file logic: read on startup, write when user specifies a version.
3. Implement `--list` flag to fetch and display available tags.
4. Add `git fetch --tags` before checkout/pull operations.
5. Handle detached HEAD state when pinned to a tag (suppress git warnings).
6. Update `install.ps1` to initialize `.cg-version` with `latest` on first install.
7. Update `scripts/link.ps1` to respect pinned version (currently calls `update.ps1`).
8. Add/update tests in `tests/update.Tests.ps1`.
9. Update `docs/installation.md` and `docs/reference.md` with versioning documentation.
10. Create first GitHub Release to have something to test against.
