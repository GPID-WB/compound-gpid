# Version Management

This page explains how to choose which version of Compound GPID runs on your machine, switch between releases, and understand what happens under the hood.

> **Prerequisites**: Compound GPID installed and at least one project linked. See [Installation](installation.md) if you haven't done that yet.

---

## Overview

By default `cg-update` tracks the `main` branch and always pulls the newest commit. You can instead **pin** to a specific tagged release for stability, or switch back to tracking main at any time — all with a single command.

| Situation | Command |
|-----------|---------|
| See what's available | `cg-update --list` |
| Pin to a specific release | `cg-update v0.2.0` |
| Return to tracking main | `cg-update latest` |
| Check (and update) current preference | `cg-update` |
| Repair a broken installation | `cg-update --fix` |

Because all linked projects share the same global clone via symlinks (junctions on Windows, symlinks on macOS), **pinning affects every linked project on the machine simultaneously** — there is no per-project version setting.

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

Fetches the latest tag metadata from GitHub and prints a table of all available releases, newest first. Your installed version is marked with `<-- current`.

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

### `cg-update v0.2.0` — pin to a release

```powershell
cg-update v0.2.0
```

1. Fetches tag metadata from GitHub.
2. Validates the tag exists.
3. Checks out the tag (detached HEAD — expected for releases).
4. **Then** writes `v0.2.0` to `.cg-version` (only after a successful checkout — never on failure).

**Example output:**
```
Mode: pinned (v0.2.0)
Checking out v0.2.0...
Pinned to v0.2.0.

Managed subdirectories (prompts/, skills/, agents/, instructions/) are
updated in all linked projects immediately via symlinks.

Run: cg-update latest   to return to tracking main.
```

Subsequent bare `cg-update` calls stay on `v0.2.0` — they do not pull any newer commits.

> **Tag format**: tags must match `v<major>.<minor>.<patch>`, e.g. `v0.2.0`. Two-segment tags (`v0.2`) and non-`v` prefixes (`0.2.0`) are rejected with a clear error.

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

Repairs a corrupted or inconsistent global clone without losing your version preference. Performs three steps in order:

1. **Clean** — removes untracked files and stale artifacts left from old project links (`git clean -fd`)
2. **Reset** — discards any local modifications to tracked files (`git checkout .`)
3. **Pull** — fetches and applies the latest code for your current mode (`git pull --ff-only`)

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
- `cg-update` fails with "untracked files would be overwritten" or merge conflicts
- The global clone has unexpected local changes that you want to discard
- Scripts error with "corrupted installation" messages and suggest `cg-update --fix`
- After a failed partial update left the clone in an inconsistent state

**When NOT to use**:
- If you intentionally modified files in the global clone — `--fix` discards those changes
- As a first response to a PATH or authentication issue — those need different fixes (see [Troubleshooting](troubleshooting.md))

> **If `--fix` itself fails** (e.g. the installed copy predates this feature): see [Repairing a broken installation](installation.md#repairing-a-broken-installation) for the equivalent manual commands.

---

## Newer-release hint

When you are pinned to a tag and a newer release is available, `cg-update` displays a yellow hint at the end of its output:

```
Newer release available: v0.3.0
Run: cg-update v0.3.0   to upgrade.
```

This is **informational only** — no action is required unless you want to upgrade. Your pin stays in place.

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
- A remote compute server can be pinned to the production-certified release.

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

If missing or corrupted, delete it and run `cg-update` — it defaults to `latest`. See the [Troubleshooting](troubleshooting.md#cg-version-missing-or-corrupted) page for the full fix.

**Pinned but still seeing new files** — prompts, skills, and agents live inside symlink directories that always point to the checked-out commit. If you pinned to an old tag, those files will reflect that tag's content. This is expected behaviour.

---

## Dev tags (maintainer-only)

Dev tags follow the convention `v<MAJOR>.<MINOR>.<PATCH>.<DEV>` where DEV starts at 9000 (e.g. `v0.1.0.9000`, `v0.1.0.9001`). They are used to test a pre-release commit end-to-end via `cg-update` **before** merging to `main` and cutting an official release.

**Dev tags are invisible to regular users:**

- `cg-update --list` shows only 3-component release tags.
- The "Newer release available" hint is never triggered by a dev tag.
- `cg-update` (bare) and `cg-update latest` pull `main` and are unaware of any tags.

### Creating a dev tag

Use the `/cg-devtag` prompt in Copilot Chat — it auto-increments from the latest dev tag for the current base version, confirms with you, and pushes:

```
/cg-devtag
```

Or manually:

```powershell
git tag v0.1.0.9000
git push origin v0.1.0.9000
```

### Testing with a dev tag

From any linked project:

```powershell
cg-update v0.1.0.9000
```

This checks out the tagged commit in the global clone. All linked projects immediately see the new code via junctions.

### Cleaning up

After testing, delete the dev tag locally and from the remote:

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
