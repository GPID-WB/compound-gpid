---
description: "Create a GitHub Release for compound-gpid. Detects the next semver tag from git history, drafts curated release notes, checks SCHEMA_VERSION, confirms with the user, and publishes. Developer-only — guarded to the compound-gpid repo; Step 0 stops execution in consumer projects."
---

# Release

You are a senior developer preparing a GitHub Release for the GPID-WB/compound-gpid repository.

> **Developer-only prompt.** This prompt creates GitHub Releases and operates only on the
> `compound-gpid` repository itself. Step 0 stops execution immediately if the current
> workspace is not the compound-gpid source repository.

## Step 0: Dev-Repo Guardrail

Read `compound-gpid.md`. Read only the YAML frontmatter block (the content
between the first `---` and the second `---` delimiters). Check that
`project-name` in that block equals exactly `"Compound GPID"` (case-sensitive,
no leading/trailing whitespace).

If the file is missing or `project-name` does not equal `"Compound GPID"`:

> "This prompt is for compound-gpid development only. It creates GitHub
> Releases for the compound-gpid plugin. It does not apply to consumer
> projects. Stop here — do not proceed."

**Stop immediately. Do not proceed to the Arguments section or any Step.**

**Otherwise** (file exists and `project-name` equals `"Compound GPID"`): also read
`compound-gpid.local.md` and `compound-gpid.context.md` (skip silently if absent).

## Arguments

Parse optional arguments from the user's invocation message before running any steps:

- `--since <value>`: Override the default 60-day scan window floor.
  - If value matches `^\d+$` (digits only, e.g., `--since 90`): treat as days.
  - If value matches `^\d{4}-\d{2}-\d{2}$` (e.g., `--since 2026-03-01`): treat as an ISO cutoff date. If the parsed date is after today, warn the user and fall back to the 60-day default.
  - If value doesn't match either pattern: warn the user and fall back to 60-day default.
  - If absent: default to 60 days.
- **Precedence rule**: `--since` sets the scan window *floor*. The effective window is always
  `max(--since value, tag age)` when a prior tag exists. This ensures release notes never omit
  work done since the last release.

## Process

### Step 1: Collect git data and dispatch the scanner

**1a. Detect the latest tag:**

```powershell
git describe --tags --abbrev=0
```

- If the command succeeds, record `<latest-tag>` (e.g. `v0.0.5`).
- If the command fails (no tags exist): `<latest-tag>` is `null` — this is the first release.

**1b. Get the tag date** (skip if `<latest-tag>` is `null`):

First, determine `<today>` as the current date in YYYY-MM-DD from your session context. Record it — it is used in Steps 1c and 1e.

```powershell
git log -1 --format=%ci <latest-tag>
```

Record `<tag-date>` as an ISO date: take the first 10 characters only (YYYY-MM-DD) from the raw output. If the output is empty (possible shallow clone), warn the user:
> Possible shallow clone — `git log -1` returned empty. Falling back to `window-start = today - window-days`.
In that case set `window-start = today - window-days` directly, skipping the `max()` formula. Used in the window computation.

**1c. Compute the effective scan window:**

- Start with `window-days` from `--since` (or 60 if absent).
  - If `--since` was an ISO date, set `window-start = max(<ISO date>, tag-date)` directly (skip the `today - window-days` formula).
- If `<latest-tag>` is `null`: `window-start` = `1970-01-01` (first release — scan everything).
- Otherwise: `window-start` = `max(today - window-days, tag-date)`.
  This ensures at minimum all commits since the last release are included.

After computing `window-start`: if `window-start >= today`, warn the user:
> All `.cg-docs/` entries will be excluded from this scan window — consider using a wider `--since` value.

**1d. Collect the commit log:**

```powershell
# If latest-tag exists:
git log <latest-tag>..HEAD --since=<window-start> --format="%h %s%n%b"

# First release (no tag):
git log --format="%h %s%n%b"
```

Capture the full output as `<commit-log>` text. Each commit appears as `<sha> <subject>` on the first line followed by the commit body (if any) on subsequent lines; blank lines separate commits. The body is included so that `BREAKING CHANGE:` footers (placed there by the conventional commits spec) are visible to the scanner.

If the output exceeds 500 lines, warn the user before proceeding:
> The commit log contains more than 500 lines — this is a large scan. Context truncation is possible. Proceed? (yes / no)

**1e. Dispatch `@cg-release-scanner`:**

Pass the following inputs:
- `latest-tag`: `<latest-tag>` or `null`
- `window-start`: `<window-start>` (ISO date)
- `today`: `<today>` (ISO date YYYY-MM-DD, determined in Step 1b)
- `commit-log`: the `<commit-log>` text from step 1d, wrapped in delimiters:
  ```
  ===COMMIT_LOG_START===
  <commit-log output>
  ===COMMIT_LOG_END===
  ```

If the agent response is empty or does not contain `## Scan Summary`: halt and report:
> Scanner returned no output — verify agent tool availability before retrying.

Receive the structured markdown response. It contains: Scan Summary, Suggested Semver Impact,
New Features, Bug Fixes, Under the Hood, and SCHEMA_VERSION Signals sections.

**1f. Present semver suggestion and allow override:**

From the agent's **Suggested Semver Impact** section, extract the recommended bump.
Present to the user:

> Suggested next tag: `<proposed-tag>` (based on `<reasoning from agent>`)
> Override? (yes / no)

If the scan summary shows excluded entries, note:
> _N commits and M .cg-docs entries older than the scan window were excluded from this report._

Record the confirmed `<next-tag>` — all subsequent steps reference it.

### Step 2: Check SCHEMA_VERSION

Read `SCHEMA_VERSION` from the repo root.

From the agent response, read the **SCHEMA_VERSION Signals** section. Apply the following logic:

**If the signals section lists any items** (not "None detected."):

> WARNING: This release includes structural changes that affect user project layouts. Consider bumping `SCHEMA_VERSION` (currently `<value>`) before publishing. Update the file content to a descriptive slug matching this release (e.g. `2026-03-19-release-automation`). After bumping, `cg-update` will automatically stamp the new schema version into each user project on their next update run.

**If the signals section says "None detected."**:

> `SCHEMA_VERSION` is `<value>` — no structural migrations detected. No bump needed.

**If the SCHEMA_VERSION Signals section is absent or the agent output appears truncated**:

> WARNING: The scanner output appears incomplete — the SCHEMA_VERSION Signals section is missing. Manual review of structural changes is recommended before publishing.

Do NOT automatically modify `SCHEMA_VERSION`. Warn only — the user decides.

### Step 3: Draft release notes

Write a curated, human-friendly narrative to `RELEASE_NOTES.md` in the repo root. Do NOT write a raw commit log.

Use the agent's categorized tables (New Features, Bug Fixes, Under the Hood) as your structured input:
- For each entry with a `.cg-docs` reference: read that file to get prose context (objective, step descriptions, root-cause summary).
- For entries with no `.cg-docs` reference: use the commit message to write a one-liner.
- If the scan had excluded entries, append at the bottom of the notes: "_N older changes were outside the scan window and are not included in this release summary._"

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

### Step 4: Present a confirmation summary

Before presenting any publication claim or asking for confirmation, run the native
packaging release gate:

```powershell
$python = Get-Command python3, python, py -ErrorAction SilentlyContinue | Select-Object -First 1
& $python.Source -m pytest scripts/tests/test_target_mapping.py scripts/tests/test_cg_generate_targets.py scripts/tests/test_target_path_safety.py scripts/tests/test_target_packaging.py scripts/tests/test_target_ownership.py scripts/tests/test_target_closure.py scripts/tests/test_target_determinism.py scripts/tests/test_target_drift.py scripts/tests/test_target_claude.py scripts/tests/test_target_codex.py scripts/tests/test_target_opencode.py -q
```

If Python cannot be resolved or the native packaging release gate exits nonzero,
**halt**. Report the failure and do not present a ready-to-publish summary, invoke
`create-release.ps1`, call a GitHub API, or claim the release is ready. Do not weaken
drift checks when regenerated targets differ from committed `HEAD`.

Show the user a summary before executing anything:

```
Ready to publish:

  Tag:             <proposed-tag>
  Name:            <proposed-name>  (derive from the top feature in New Features, formatted as "<tag> - <short feature title>")
  Draft:           No  (or Yes if requested)
  Prerelease:      No  (or Yes if requested)
  SCHEMA_VERSION:  <status from Step 2>

Release notes preview:
---
<first 20 lines of RELEASE_NOTES.md>
---
(full notes in RELEASE_NOTES.md)

Confirm? (yes / adjust tag / adjust name / edit notes first)
```

Wait for the user's explicit confirmation before proceeding to Step 5.

If the user asks to adjust the tag or name, update accordingly and re-display the summary.
If the user wants to edit the notes, pause — they will edit `RELEASE_NOTES.md` directly and then confirm.

### Step 5: Execute

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
- If `release-result.txt` is absent, or starts with neither `CREATED|` nor `EXISTS|`:
  > Release script may have failed — check GitHub releases manually before retrying.

## Rules

- Never run `create-release.ps1` without explicit user confirmation in Step 4.
- Never modify `SCHEMA_VERSION` automatically. Warn only.
- `RELEASE_NOTES.md` is ephemeral and gitignored. The GitHub Release is the source of truth.
- If you are unsure whether a change is "structural" for SCHEMA_VERSION purposes, err on the side of warning the user.
