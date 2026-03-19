---
description: "Create a GitHub Release for compound-gpid. Detects the next semver tag from git history, drafts curated release notes, checks SCHEMA_VERSION, confirms with the user, and publishes. Developer-only — this file lives at the repo root and is NOT junctioned into user projects."
model: Claude Sonnet 4.6 (copilot)
---

# Release

You are a senior developer preparing a GitHub Release for the GPID-WB/compound-gpid repository.

> **Developer-only prompt.** This file is intentionally at the repo root, not in `.github/prompts/`. It is NOT distributed to linked user projects via junctions. Only invoke this from the compound-gpid workspace itself.

## Process

### Step 1: Detect the current version

Run the following in the terminal:

```powershell
git describe --tags --abbrev=0
```

- If the command succeeds, that is the **latest tag** (e.g. `v0.0.5`).
- If the command fails (no tags exist), treat the baseline as `v0.0.0` (first release).

Record the latest tag — all subsequent steps reference it.

### Step 2: Analyze changes since the last tag

Run:

```powershell
git log <latest-tag>..HEAD --oneline
```

(Replace `<latest-tag>` with the value from Step 1. For a first release, use `git log --oneline`.)

**Classify each commit** by its conventional commit type prefix:

| Type | Semver impact |
|------|--------------|
| `feat` | Minor bump |
| `fix` | Patch bump |
| `docs`, `test`, `refactor`, `chore`, `data`, `analysis` | Patch bump (no new features) |
| Message contains `BREAKING CHANGE` or `!:` | **Major bump** (overrides all) |

**Suggest the next tag** by applying the highest-impact rule across all commits:

- Any `BREAKING CHANGE` or `!:` commit → bump major
- Any `feat` commit → bump minor
- Otherwise → bump patch

Present the suggestion to the user and allow override before proceeding.

**Also scan `.cg-docs/` for entries dated after the last release tag:**
- `.cg-docs/brainstorms/` — decisions that shaped this release
- `.cg-docs/plans/` — features that were implemented
- `.cg-docs/solutions/` — bugs fixed, patterns discovered

Note which entries are relevant (by date). These feed the release notes in Step 4.

### Step 3: Check SCHEMA_VERSION

Read `SCHEMA_VERSION` from the repo root.

Scan the changes since the last tag for structural migrations — signs include:
- New or renamed subdirectories under `.cg-docs/`
- New fields added to `compound-gpid.local.md` (as reflected in `cg-setup.prompt.md` templates)
- New migration blocks added to `scripts/update.ps1`
- New entries in the `$ManagedDirs` array in `scripts/link.ps1`

**If structural changes are detected:**

> WARNING: This release includes structural changes that affect user project layouts. Consider bumping `SCHEMA_VERSION` (currently `<value>`) before publishing. Update the file content to a descriptive slug matching this release (e.g. `2026-03-19-release-automation`). After bumping, `cg-update` will automatically stamp the new schema version into each user project on their next update run.

**If no structural changes:**

> `SCHEMA_VERSION` is `<value>` — no structural migrations detected. No bump needed.

Do NOT automatically modify `SCHEMA_VERSION`. Warn only — the user decides.

### Step 4: Draft release notes

Write a curated, human-friendly narrative to `RELEASE_NOTES.md` in the repo root. Do NOT write a raw commit log.

**Structure** (use only sections that have content — omit empty ones):

```markdown
## What's new

### <Feature name> (`<command or file>`)

<Prose description of the feature. What problem it solves, how it works, any
relevant commands or configuration. Use tables for command references, code
blocks for examples.>

## Bug fixes

- <Brief description of bug and fix — one line per bug>

## Under the hood

- <Internal improvements, refactors, new tests — one line each>

## Upgrading

\`\`\`powershell
cg-update
\`\`\`

Or pin to this specific release:

\`\`\`powershell
cg-update <new-tag>
\`\`\`
```

**Sources to draw from** (in priority order):
1. The relevant `.cg-docs/plans/` entry — use its objective and step descriptions to understand *what* was built
2. The relevant `.cg-docs/brainstorms/` entry — use its context section to understand *why*
3. The relevant `.cg-docs/solutions/` entries — use titles and root-cause lines for the bug fixes section
4. The commit messages — for anything not covered above

**Style guidance**: Match the tone of existing release notes (e.g. v0.0.5). Prefer prose over bullet lists for major features. Use tables for command references. Use code blocks for commands. Write for a technical audience who uses the tool daily.

After writing, save the file as `RELEASE_NOTES.md` in the repo root.

### Step 5: Present a confirmation summary

Show the user a summary before executing anything:

```
Ready to publish:

  Tag:             <proposed-tag>
  Name:            <proposed-name>  (e.g. "<tag> - <short feature title>")
  Draft:           No  (or Yes if requested)
  Prerelease:      No  (or Yes if requested)
  SCHEMA_VERSION:  <status from Step 3>

Release notes preview:
---
<first 20 lines of RELEASE_NOTES.md>
---
(full notes in RELEASE_NOTES.md)

Confirm? (yes / adjust tag / adjust name / edit notes first)
```

Wait for the user's explicit confirmation before proceeding to Step 6.

If the user asks to adjust the tag or name, update accordingly and re-display the summary.
If the user wants to edit the notes, pause — they will edit `RELEASE_NOTES.md` directly and then confirm.

### Step 6: Execute

On confirmation, run in the terminal:

```powershell
.\create-release.ps1 -Tag <tag> -Name "<name>" -NotesFile RELEASE_NOTES.md
```

Add `-Draft` if the user requested a draft release.
Add `-Prerelease` if the user requested a prerelease.

After the script completes, read `release-result.txt`:
- If it starts with `CREATED|` — extract the URL and report success:
  > Release published: <url>
- If it starts with `EXISTS|` — report idempotency:
  > A release for <tag> already exists: <url>. No changes were made.
- If the script errored — report the error message and suggest checking GCM authentication:
  > Authentication check: run `"protocol=https`nhost=github.com`n" | git credential fill` to verify a token is available.

## Rules

- Never run `create-release.ps1` without explicit user confirmation in Step 5.
- Never modify `SCHEMA_VERSION` automatically. Warn only.
- `RELEASE_NOTES.md` is ephemeral and gitignored. The GitHub Release is the source of truth.
- If you are unsure whether a change is "structural" for SCHEMA_VERSION purposes, err on the side of warning the user.
