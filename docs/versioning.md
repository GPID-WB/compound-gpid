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

Because all linked projects share the same global clone via directory junctions, **pinning affects every linked project on the machine simultaneously** — there is no per-project version setting.

---

## How it works

Version preference is stored per-machine in a single file:

```
C:\WBG\.compound-gpid\.cg-version          # local machine (OneDrive)
$env:USERPROFILE\.compound-gpid\.cg-version # remote server
```

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

Fetches the latest tag metadata from GitHub and prints a table of all available releases, newest first. Your current preference is marked with `<-- current`.

**Example output:**
```
Fetching available releases...

Available releases (newest first):
  v0.3.0
  v0.2.0  <-- current
  v0.1.0

Mode: pinned (v0.2.0)
```

If you are tracking `main`, the mode line reads `Mode: tracking main (latest)` and no tag is marked as current.

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
updated in all linked projects immediately via junctions.

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
updated in all linked projects immediately via junctions.
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
```powershell
Get-Content "C:\WBG\.compound-gpid\.cg-version"
# or
Get-Content "$env:USERPROFILE\.compound-gpid\.cg-version"
```
If missing or corrupted, delete it and run `cg-update` — it defaults to `latest`. See the [Troubleshooting](troubleshooting.md#cg-version-missing-or-corrupted) page for the full fix.

**Pinned but still seeing new files** — prompts, skills, and agents live inside junction directories that always point to the checked-out commit. If you pinned to an old tag, those files will reflect that tag's content. This is expected behaviour.

---

> **See also**: [Reference → Version Management](reference.md#version-management) for a quick command table. [Troubleshooting](troubleshooting.md) for known issues.
