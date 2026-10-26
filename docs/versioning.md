# Version Management

This page explains how to choose which version of Compound GPID runs on your machine, switch between releases, and understand what happens under the hood.

> **Prerequisites**: Compound GPID installed and at least one project linked. See [Installation](installation.md) if you haven't done that yet.

For an older installation, follow the [Upgrade Guide](upgrade.md) before using
the installed updater.

---

## Overview

By default `cg-update` tracks the `main` branch and always pulls the newest commit. You can instead **pin** to a specific tagged release for stability, or switch back to tracking main at any time — all with a single command.

| Situation | Command |
|-----------|---------|
| See what's available | `cg-update --list` |
| Pin to a specific release | `cg-update v1.2.0.9024` |
| Return to tracking main | `cg-update latest` |
| Check (and update) current preference | `cg-update` |
| Inspect and recover a broken installation | [Safe recovery](installation.md#repairing-a-broken-installation) |

All linked projects share the global installation preference. Linked directories reflect a checkout immediately; managed copies and projections need the [consumer refresh](installation.md#refreshing-existing-consumer-projects) steps. A projection records its source revision and must be relinked when that revision changes.

---

## How it works

Version preference is stored per-machine in a single file:

**Windows:**
```
C:\WBG\.compound-gpid\.cg-version          # local machine (OneDrive)
$env:USERPROFILE\.compound-gpid\.cg-version # remote server
```

**macOS:**
```
~/.compound-gpid/.cg-version                # default install path
```
(Substitute your chosen install path if you cloned elsewhere.)

This file contains either the string `latest` or a tag name such as `v0.2.0`. It is gitignored and never committed — each team member keeps their own preference independently.

`cg-update` reads this file every time it runs:

- **`latest`** (default) — runs `git pull --ff-only` on `main`, updating to the newest commit.
- **`v0.2.0`** (or any tag) — checks out that tag in detached HEAD mode; the working tree matches the exact release.

---

## Commands in depth

### `cg-update --list` — browse releases

```powershell
cg-update --list
```

Fetches tag metadata from GitHub and prints three-component release tags, newest first. Your installed version is marked with `<-- current` if it is listed. Four-component tags are omitted from the table; a four-component pin appears in the current-mode label instead.

**Example output (pinned to v0.2.0):**
```
Fetching available releases...

Available releases:
  v0.3.0
  v0.2.0  <-- current
  v0.1.0

Current: v0.2.0 (pinned)

  cg-update <version>  -- pin to a specific release
  cg-update latest     -- unpin and track main
```

When tracking `main`, the label reads `Current: main (latest)`. If your local HEAD points to a release tag (e.g. you just ran `cg-update latest` on a clean checkout), that tag is still marked with `<-- current`. If HEAD is between releases (e.g. on a newer unreleased commit), no tag is marked.

> **Offline use**: if the network is unavailable, `--list` shows cached tag data from your last successful fetch and displays a warning.

---

### `cg-update v1.2.0.9024` — pin to a release

```powershell
cg-update v1.2.0.9024
```

1. Fetches tag metadata from GitHub.
2. Validates the tag exists.
3. Checks out the tag (detached HEAD — expected for releases).
4. Validates the required target scripts and generated platform trees.
5. **Then** writes `v1.2.0.9024` to `.cg-version`; failures restore the previous checkout and pin rather than publishing an unvalidated target.

**Example output:**
```
Mode: pinned (v1.2.0.9024)
Checking out v1.2.0.9024...
Pinned to v1.2.0.9024.

Managed subdirectories (prompts/, skills/, agents/, instructions/) are
updated in all linked projects immediately via symlinks.

Run: cg-update latest   to return to tracking main.
```

Subsequent bare `cg-update` calls stay on `v1.2.0.9024` — they do not pull any newer commits. Tracked or staged user edits block normal updates rather than being discarded.

> **Tag format**: tags must match `v<major>.<minor>.<patch>` or `v<major>.<minor>.<patch>.<build>`, e.g. `v1.2.0.9024`. Two-segment tags (`v0.2`) and non-`v` prefixes (`0.2.0`) are rejected with a clear error. An accepted tag must also pass target validation; the format alone does not make an older release compatible with the current updater.

---

### `cg-update latest` — return to tracking main

```powershell
cg-update latest
```

1. Writes `latest` to `.cg-version`.
2. Checks back out to the `main` branch (if the working tree is currently in detached HEAD from a prior pin).
3. Runs `git pull --ff-only` to sync with the remote.

**Example output:**
```
Mode: tracking main (latest)
Checking for updates...
Updated: abc1234 -> def5678

Changes:
fix(update): correct Set-Content placement after checkout

Managed subdirectories (prompts/, skills/, agents/, instructions/) are
updated in all linked projects immediately via symlinks.
```

---

### `cg-update` (bare) — check and apply current preference

```powershell
cg-update
```

Reads `.cg-version` and either pulls the latest commit (if `latest`) or stays on the currently pinned tag (if pinned). Always shows the active mode upfront:

```
Mode: tracking main (latest)
```
or
```
Mode: pinned (v0.2.0)
```

---

### `cg-update --fix` — repair a broken installation

```powershell
cg-update --fix   # Windows
cg-update --fix   # macOS
```

This is a destructive opt-in for a branch checkout with an upstream, not a safe
default repair or a migration procedure. Back up the entire clone, including
untracked files and `.cg-version`, before deliberately choosing to discard
changes. It performs three steps in order:

1. **Clean** — removes untracked files and stale artifacts left from old project links (`git clean -fd`)
2. **Reset** — discards any local modifications to tracked files (`git checkout .`)
3. **Pull** — runs `git pull --ff-only` on the current checkout, without selecting a branch or validating the saved pin

A normal tag-pinned installation is detached, so the pull fails after the
destructive steps. Use [safe recovery](installation.md#repairing-a-broken-installation)
for pinned, divergent, or edited installations.

**Example output:**
```
Repairing compound-gpid installation...
  Install dir: C:\WBG\.compound-gpid

  Cleaning untracked files...
  Discarding local changes...
  Pulling latest...
Repair complete.
```

**When to use**:
- Only on a branch with an upstream, after inspecting and backing up the clone and explicitly choosing to discard its untracked files and tracked edits

**When NOT to use**:
- If you intentionally modified files in the global clone — `--fix` discards those changes
- On a detached release tag, a divergent clone, or an older installation needing migration
- As a first response to a PATH or authentication issue — those need different fixes (see [Troubleshooting](troubleshooting.md))

> **If `--fix` itself fails**: preserve the remaining clone and backup; see [Repairing a broken installation](installation.md#repairing-a-broken-installation). Do not repeat destructive commands as a fallback.

---

## Newer-release hint

When you are pinned to a tag, `cg-update` may display a yellow hint for the highest available three-component release tag when it differs from your pin:

```
Newer release available: v0.3.0
Run: cg-update v0.3.0   to upgrade.
```

This is **informational only** — no action is required unless you want to upgrade. Your pin stays in place.

The comparison checks whether the tags differ, not whether the suggested tag
is newer than a four-component pin. Review the target before changing versions.

---

## When to use each mode

| Use case | Recommended mode |
|----------|-----------------|
| Active development, want the latest fixes | `latest` (default) |
| Preparing to run analysis — want a stable baseline | Pin to the most recent release tag |
| Testing a new beta release before committing the team | Pin to the beta tag on your own machine |
| Something broke after an auto-update, need to roll back | Pin to the last known good tag |
| Done with the analysis, ready to move to latest again | `cg-update latest` |

---

## Multiple machines

`.cg-version` is gitignored and never committed. Each machine manages its own preference:

- Your laptop can be pinned to `v0.2.0` for a stable analysis run.
- A colleague's laptop can track `main` and get the latest features.
- A remote compute server can be pinned to the team's selected stable release.

There is no synchronisation between machines — this is intentional.

---

## Troubleshooting

**"Release 'v9.9.9' not found"** — the tag does not exist. Run `cg-update --list` to see available tags. Check for typos.

**`cg-update` re-pins unexpectedly** — your `.cg-version` file may have been overwritten or corrupted. Check its contents:

**Windows:**
```powershell
Get-Content "C:\WBG\.compound-gpid\.cg-version"
# or
Get-Content "$env:USERPROFILE\.compound-gpid\.cg-version"
```

**macOS:**
```bash
cat ~/.compound-gpid/.cg-version
```

If missing or corrupted, preserve the file and recover your intended preference from records or a backup, then pass that tag explicitly to `cg-update`. Do not delete the pin and silently switch to `latest`. See the [Troubleshooting](troubleshooting.md#cg-version-missing-or-corrupted) page for the full fix.

**Pinned but still seeing new files** — linked directories reflect the global checkout immediately, but managed copies and project-local projections need a refresh from that project's root. Rerun `cg-link` with the intended platform selection when the projection's source revision changes, and review ownership diagnostics; modified or unowned files are preserved rather than silently replaced.

---

## Four-component prerelease tags (maintainer-only)

Prerelease tags follow the convention `v<MAJOR>.<MINOR>.<PATCH>.<BUILD>` where
BUILD starts at 9000 (for example, `v1.2.0.9000` and `v1.2.0.9001`). They let
maintainers publish an installable GitHub prerelease and test the complete
release path through `cg-update` before promoting a stable three-component
release.

**Prerelease tags stay out of the stable update channel:**

- `cg-update --list` shows only 3-component release tags.
- The "Newer release available" hint is never triggered by a prerelease tag.
- `cg-update` (bare) honors the saved preference, including a four-component pin. `cg-update latest` explicitly unpins and pulls `main`; it does not select the newest tag.
- Testers can install a known prerelease explicitly with `cg-update v1.2.0.9008`.

### Publishing an installable prerelease

From a clean `dev` checkout whose `HEAD` matches `origin/dev`, run:

```text
/cg-release v1.2.0.9008
```

The release workflow creates the durable payload, exact tag, immutable Pages
deployment, and GitHub Release record. A four-component tag is automatically
marked as a GitHub prerelease. It is accepted by both new-release and
`--resume` flows. Stable three-component releases remain restricted to a clean,
up-to-date `main` checkout.

Published prerelease tags are immutable release records. Do not delete or reuse
them; increment the build component for the next candidate.

Only repository administrators can create release-shaped `v*` tags. The `dev`
branch rejects deletion and force-pushes, and published tags reject every update
or deletion. The release flow does not publish drafts because its durable
payload and Pages deployment are public before the GitHub Release API record.

### Creating a temporary dev tag

Use `/cg-devtag` only for temporary branch testing that does not create a GitHub
Release. It auto-increments from the latest dev tag for the current base
version, confirms with you, and pushes:

```
/cg-devtag
```

Or manually:

```powershell
git tag v0.1.0.9000
git push origin v0.1.0.9000
```

### Testing with a prerelease or temporary dev tag

From any linked project:

```powershell
cg-update v0.1.0.9000
```

This checks out and validates the tagged commit in the global clone. Linked directories reflect it immediately; follow the consumer refresh steps from each project root to update checksum-owned copies and projections.

### Cleaning up temporary tags

Delete a tag only when it was created temporarily with `/cg-devtag` and never
published as a GitHub Release. After testing, delete that temporary tag locally
and from the remote:

```powershell
git tag -d v0.1.0.9000
git push origin --delete v0.1.0.9000
```

Then return to your normal mode:

```powershell
cg-update latest     # or cg-update v0.1.0 to pin back to the last release
```

---

> **See also**: [Reference → Version Management](reference.md#version-management) for a quick command table. [Troubleshooting](troubleshooting.md) for known issues.
