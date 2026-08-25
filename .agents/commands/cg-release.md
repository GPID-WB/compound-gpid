---
description: "Create a GitHub Release for compound-gpid. Detects the next semver tag from git history, drafts curated release notes, checks SCHEMA_VERSION, confirms with the user, and publishes. Developer-only \u2014 guarded to the compound-gpid repo; Step 0 stops execution in consumer projects."
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

- `<tag>`: Request the tag for a new release. It must match
  `^v\d+\.\d+\.\d+(\.\d+)?$`, accepting either a stable `vX.Y.Z` tag or a
  four-component `vX.Y.Z.<build>` prerelease tag. A supplied tag overrides the
  scanner's semver suggestion but still requires confirmation in Step 1f. A
  four-component tag always sets `<prerelease>` to `true`; it must be published
  with GitHub's prerelease flag rather than as a stable release. Stable tags are
  released from `main`; four-component prerelease tags are released directly
  from `dev`.
- `--since <value>`: Override the default 60-day scan window floor.
  - If value matches `^\d+$` (digits only, e.g., `--since 90`): treat as days.
  - If value matches `^\d{4}-\d{2}-\d{2}$` (e.g., `--since 2026-03-01`): treat as an ISO cutoff date. If the parsed date is after today, warn the user and fall back to the 60-day default.
  - If value doesn't match either pattern: warn the user and fall back to 60-day default.
  - If absent: default to 60 days.
- **Precedence rule**: `--since` sets the scan window *floor*. The effective window is always
  `max(--since value, tag age)` when a prior tag exists. This ensures release notes never omit
  work done since the last release.
- `--resume <tag>`: Resume an interrupted release for an existing tag. The tag
  must match `^v\d+\.\d+\.\d+(\.\d+)?$`; do not combine it with `--since` or
  the new-release `<tag>` argument. Resume skips
  the new-release scan, payload creation, commit, and tag creation steps. It
  validates the committed immutable payload and exact tag, waits for that tag's
  Pages deployment, then retries only the unfinished GitHub Release API call.

## Process

### Step 1: Collect git data and dispatch the scanner

**1a. Detect the latest published release tag:**

```powershell
node scripts/generate-whats-new.js --validate-release-set
$latestTag = $null
if (Test-Path -LiteralPath releases/latest.json) {
  $latestPayload = Get-Content releases/latest.json -Raw -Encoding UTF8 | ConvertFrom-Json
  $latestTag = [string]$latestPayload.tag
  git rev-parse --verify "$latestTag^{commit}"
  gh release view $latestTag --json tagName,name,isDraft,isPrerelease,targetCommitish
  Get-ChildItem releases -Filter 'v*.json' | ForEach-Object {
    $record = Get-Content $_.FullName -Raw -Encoding UTF8 | ConvertFrom-Json
    gh release view $record.tag --json tagName,name,isDraft,isPrerelease,targetCommitish
  }
}
```

- If `releases/latest.json` exists and the release set validates, record its tag
  as `<latest-tag>` (e.g. `v0.0.5`) after verifying that exact tag exists and
  has a GitHub Release whose tag, name, target commit, draft state, and
  three-/four-component prerelease classification match the durable payload.
  If the release is absent or mismatched, halt and require `--resume` or
  maintainer repair before scanning a later release.
- Every immutable payload must have a matching non-draft GitHub Release with
  the correct tag, name, target commit, and three-/four-component prerelease
  classification. Halt for historical repair if any durable record is missing
  or mismatched.
- If no immutable payloads and no `releases/latest.json` exist, `<latest-tag>` is
  `null` — this is the first release.
- Never use unrestricted `git describe` as the release baseline. Temporary
  `/cg-devtag` tags do not have durable payloads and must not truncate the scan.

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
# If latest-tag exists (never apply --since to the tag range):
git log <latest-tag>..HEAD --format="%H%x1f%s%x1f%b%x1e"

# First release (no tag):
git log --format="%H%x1f%s%x1f%b%x1e"
```

Capture the full output as `<commit-log>` text. Each commit record ends with ASCII
record separator `0x1e`; SHA, subject, and body use ASCII field separator `0x1f`.
The body may contain blank paragraphs. The scanner must preserve it so
`BREAKING CHANGE:` footers remain attributable to their exact commit.

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
New Features, Bug Fixes, Under the Hood, SCHEMA_VERSION Signals, and a `## Release Payload`
JSON block.

**1f. Present semver suggestion and allow override:**

From the agent's **Suggested Semver Impact** section, extract the recommended bump.
Present to the user:

> Suggested next tag: `<proposed-tag>` (based on `<reasoning from agent>`)
> Override? (yes / no)

If the scan summary shows excluded entries, note:
> _N commits and M .cg-docs entries older than the scan window were excluded from this report._

Record the confirmed `<next-tag>` — all subsequent steps reference it.
Set `<prerelease>` to `true` when `<next-tag>` has four numeric components and
to `false` when it has three. This derivation is mandatory even when the user
supplied the tag directly.
Set `<release-branch>` to `dev` when `<prerelease>` is `true`; otherwise set it
to `main`. Stable releases must never be cut from `dev`, and four-component
prereleases must be publishable directly from `dev`.

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
  Draft:           No
  Prerelease:      <Yes for a four-component tag; otherwise No>
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

### Step 5: Create and publish the durable release source

On explicit confirmation, do **not** call `create-release.ps1` yet. The durable
release payload, its exact tag, and the tag documentation deployment must exist
first.

1. Require a clean, up-to-date `<release-branch>` checkout before writing payloads:

   ```powershell
   git status --porcelain
   git fetch origin <release-branch> --tags
   git branch --show-current
   git rev-parse HEAD
   git rev-parse origin/<release-branch>
   ```

   Halt if status has tracked or untracked changes (other than ignored
   `RELEASE_NOTES.md`), the branch is not `<release-branch>`, or `HEAD` differs
   from `origin/<release-branch>`. Halt safely on a non-fast-forward release
   branch rather than creating a release from a stale checkout. Do not require
   a four-component prerelease commit on `dev` to contain the current `main`
   tip; exact `origin/dev` lineage is the prerelease authorization boundary.

2. Extract exactly one fenced JSON object from the scanner's `## Release
   Payload` section. Parse it before writing any payload. It must contain only a
   non-empty `sections` array. Reject every `kind` other than `new`, `fixed`, or
   `internal`, duplicate kinds, control characters, and any title or entry that
   exceeds these bounds: name 200 characters, section title 120 characters,
   entry 500 characters, and at most 50 entries per section. Do not derive kinds by scraping
   `RELEASE_NOTES.md` or any other prose.

3. Build the complete payload from the confirmed scanner block:

   ```json
   {
     "schemaVersion": 1,
     "tag": "<next-tag>",
     "publishedAt": "<UTC preparation timestamp in YYYY-MM-DDTHH:mm:ssZ form>",
     "releaseDate": "<today YYYY-MM-DD>",
     "name": "<confirmed name>",
     "url": "https://github.com/GPID-WB/compound-gpid/releases/tag/<next-tag>",
     "sourceUrl": "https://github.com/GPID-WB/compound-gpid/tree/<next-tag>",
     "sections": <scanner Release Payload sections>
   }
   ```

   Serialize it deterministically once, then write the exact same UTF-8 bytes to
   `releases/<next-tag>.json` and `releases/latest.json`. If the immutable
   versioned file already exists, continue only when its bytes exactly match the
   new payload; otherwise halt without overwriting it. `latest.json` may be
   updated only as the byte-for-byte current payload copy.

4. Validate both files before staging. The unknown-kind precheck in step 2 must
   occur before either file write; these commands are the machine-checkable
   schema guard before commit:

   ```powershell
   node scripts/generate-whats-new.js --validate-payload releases/<next-tag>.json
   node scripts/generate-whats-new.js --validate-payload releases/latest.json
   node scripts/generate-whats-new.js --validate-release-set
   ```

   Halt on any validation failure. Report whether either durable file was
   written, but do not create a tag or call the GitHub API.

5. Stage only the two payload files and commit only if this retry did not already
   create the byte-identical source commit:

   ```powershell
   git add -- releases/<next-tag>.json releases/latest.json
   git diff --cached --name-only
   git commit -m "chore(release): prepare <next-tag> payload"
   ```

   Verify the staged-name list contains only those two paths. If it contains any
   other path, unstage only that unrelated path and halt for maintainer review.
   If no staged diff exists because both payload files are already byte-identical,
   do not create an empty commit.

6. Verify the required active repository rulesets before creating the tag:
   `Protect release tags` must block all updates and deletions for
   `refs/tags/v*` without bypass actors; `Restrict release tag creation` must
   restrict creation of `refs/tags/v*` to repository administrators; and
   `Protect dev` must block deletion and force-pushes for `refs/heads/dev`
   without bypass actors. Halt before tag creation if any rule is absent or
   weaker than this contract.

7. Verify or create the exact tag on the clean payload commit, then push the
   release branch and tag. Do not use an unconditional `git tag` command:

   ```powershell
   git status --porcelain
   $head = (git rev-parse HEAD).Trim()
   $existing = git rev-parse --verify "<next-tag>^{commit}" 2>$null
   if ($LASTEXITCODE -eq 0) {
     if ($existing.Trim() -ne $head) { throw "Existing tag <next-tag> points to another commit." }
   } else {
     git tag <next-tag>
   }
   git push origin <release-branch>
   git push origin <next-tag>
   $remote = git ls-remote --tags origin refs/tags/<next-tag>
   if ($remote -notmatch $head) { throw "Remote tag <next-tag> does not resolve to the payload commit." }
   ```

   If the tag already exists, it must resolve to the current clean `HEAD`; if it
   resolves elsewhere, halt. If either push fails, halt and report the committed
   payload/tag state so a maintainer can resume without overwriting a release
   record.

8. Wait for the unprivileged `release-docs.yml` push run for the exact tag and
   commit. Verify its successful conclusion and record its database ID. Then
   identify the successful `release-pages.yml` `workflow_run` controller whose run name
   is exactly `Deploy docs from <release-docs database ID>`. Halt on a missing,
   failed, or mismatched build or deployment. The controller must already exist
   on protected `main`. Do not invoke `/cg-wiki` or
   rebuild documentation from this prompt; the release build and protected
   controller own the immutable complete-build deployment.

### Resume An Interrupted Release

When invoked with `--resume <tag>`, derive `<prerelease>` and
`<release-branch>` from the tag using the same three-component/`main` and
four-component/`dev` policy as a new release. Require a clean checkout at the
exact tag commit; a detached checkout is allowed so resume remains possible
after the release branch advances. Do not prepare a new scanner payload.
Confirm all of the following before retrying any publication step:

```powershell
git status --porcelain
git fetch origin <release-branch> --tags
git rev-parse HEAD
git rev-parse origin/<release-branch>
git rev-parse "<tag>^{commit}"
git merge-base --is-ancestor "<tag>^{commit}" origin/<release-branch>
git ls-remote --tags origin refs/tags/<tag>
node scripts/generate-whats-new.js --validate-payload releases/<tag>.json
node scripts/generate-whats-new.js --validate-payload releases/latest.json
node scripts/generate-whats-new.js --validate-release-set
```

The local and remote `<tag>` must resolve to the clean `HEAD`, and that commit
must remain on the authorized `<release-branch>` lineage. The immutable payload
must be present and valid. Then wait for the exact tag-site deployment as in Step 5.8.
If it failed, resume the deployment before the API record. If it succeeded but
the API record is absent, recreate `RELEASE_NOTES.md` from the recorded
scanner/release context and run Step 6 only. Never overwrite an immutable
payload or create a new tag during resume.

### Step 6: Publish the GitHub Release API record

Only after Step 5 has committed/validated the payload, verified the exact pushed
tag, and observed successful tag-site deployment, run:

```powershell
.\create-release.ps1 -Tag <tag> -Name "<name>" -NotesFile RELEASE_NOTES.md
```

Draft releases are not supported by this durable publication flow. Do not pass
`-Draft`; halt if a draft is requested.
Add `-Prerelease` whenever `<prerelease>` is `true`. Four-component tags always
set it to `true`; do not publish `vX.Y.Z.<build>` as a stable GitHub Release.

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

- Never run `create-release.ps1` without explicit user confirmation in Step 4,
  validated durable payloads, an exact pushed tag, and a successful tag-site deployment.
- Never modify `SCHEMA_VERSION` automatically. Warn only.
- Require stable three-component tags on `main` and four-component prerelease
  tags on `dev`; never weaken this branch/tag matrix.
- Require an active repository tag ruleset named `Protect release tags` that
  blocks all updates and deletions for `refs/tags/v*` without exclusions or
  bypass actors before API publication.
- Require `Restrict release tag creation` to limit new `refs/tags/v*` tags to
  repository administrators, and `Protect dev` to block deletion and
  non-fast-forward updates of `refs/heads/dev` without bypass actors.
- Always publish four-component `vX.Y.Z.<build>` tags as GitHub prereleases.
- `RELEASE_NOTES.md` is ephemeral and gitignored. Release payload JSON is the
  durable What's New source; the GitHub Release is the public release record.
- If you are unsure whether a change is "structural" for SCHEMA_VERSION purposes, err on the side of warning the user.
