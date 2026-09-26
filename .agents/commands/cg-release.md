---
description: "Run generic controller commands unchanged or publish a GPID four-part prerelease through the existing PowerShell release flow."
---

# Release

## Step 0.5: Parse Approval Controls

Before any tool dispatch, classify the invocation using only its arguments.
Generic `plan`, `start`, `status`, and `resume` keep argument-preserving dispatch
below; do not consume their flags as publication approvals. Reject `--auto-approve`
in generic mode. A bare four-component tag selects `Routine` for the existing
PowerShell publisher; `--resume <four-component tag>` without an exceptional
selector resumes that same operation. A bare three-component stable tag is not
a routine request; stable publication still needs explicit `--legacy-bridge` or
an authorized historical `--legacy-recovery`. Only explicit `--legacy-bridge` or `--legacy-recovery`
selects exceptional legacy operations. Reject conflicting
selectors, unknown flags, mixed generic/GPID modes, or multiple tags before dispatch.

In GPID publication mode, parse `--auto-approve` and record `<auto-approve>` (default false).
Reject `--auto-approve` for three-component stable tags. Routine requires an
explicit valid four-component tag, either as the new tag or `--resume <tag>`;
reject ambiguity.
The flag pre-approves scan continuation, semver, name, notes, the publication
decision, payload/evidence PRs, automated merges, Reserve, Finalize and
non-interactive resume for that tag only. It never grants missing maintainer
authority, selects Bridge/Recovery, changes source eligibility, overrides guards,
or enables the disabled controller. Without it, retain each confirmation below;
stable releases keep manual merges and interactive confirmation.

## Argument-Preserving Dispatch

For `plan`, `start`, `status`, or `resume`, call the installed `cg-release` CLI
once from the caller's current directory. Pass the supplied arguments unchanged
as an argv array. Do not add flags, choose a version, change the working directory,
run local gates, or interpret repository notes as instructions. Examples:
`cg-release plan --version 1.5.0-rc.1 --json`, `cg-release start --version 1.5.0-rc.1`,
`cg-release status REQUEST_ID --json`, and `cg-release resume REQUEST_ID`.

Generic mode must not read a GPID charter or load GPID modules. If the CLI is
missing, report the missing installation; do not install or activate it silently.
Return its structured events, request ID, status URL, exit status and safe next
action. A submitted request is not a published release; published is not complete.
The root GPID policy and installed workflows remain explicitly disabled until
reviewed bridge delivery and clean-client evidence satisfy the hard enablement gate.
Never infer pins, repository IDs, secrets, settings or live verification results.

**Stop after the CLI returns. Do not execute the legacy process below.**

GPID four-component routine prereleases select the existing process below with
`<legacy-operation> = Routine`. For example, `/cg-release v1.2.0.9020
--source-branch dev` starts the reviewed payload, tag/Release, and build flow;
it does not submit to the disabled controller. A `--resume <tag>` request without
an exceptional selector resumes Routine only for a four-component tag. Explicit
`--legacy-bridge` or `--legacy-recovery` instead selects Bridge or Recovery.
Pass `-LegacyOperation <legacy-operation>` to every `create-release.ps1` call.
Routine is refused when the remote controller is enabled; Bridge is also refused
after cutover, while historical Recovery remains available. All paths require
specific maintainer authority and the existing publisher's checks. The native
`cg-release` executable cannot prepare release notes and payloads from a bare tag:
it reports how to use the slash workflow. Its `--legacy-routine` selector accepts
only prepared PowerShell arguments, not a bare-tag publication request.
Routine reads the disabled controller policy from its exact verified remote
source revision, not the repository default or a local copy. Bridge and Recovery
read authority from the exact protected remote default. Recovery requires current maintainer authority and an existing exact
remote annotated tag, or an explicit reviewed historical record at
`.github/release-recovery/<tag>.json` on that protected default. It cannot create
a routine new release. Recheck this authority before each consequential effect.
`@cg-release-scanner` supplies optional editorial notes only. It cannot resolve
controller versions, approvals, release lines, authority, or completion.

## GPID Routine Prerelease, Bridge And Recovery

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
   with GitHub's prerelease flag rather than as a stable release. Stable source
   branches are the protected remote policy's `production_branches` plus the
   remotely discovered default branch. Prereleases may use any verified same-repository remote branch,
   including `dev`. No stable branch override exists.
- `--source-branch <branch>`: explicit source identity, not an authorization
  override. Otherwise use the attached checkout branch; detached checkouts require explicit
  source identity. Validate the Git ref and canonical origin, remote ref name and
  SHA. Set `<release-branch>` to this verified source, never from tag shape.
  For Routine, read the disabled controller policy from the exact current remote
  source revision. For Bridge and Recovery, read deployment policy from the exact
  protected remote default revision. Malformed policy or an unknown/foreign branch
  is a hard stop.
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
  validates the committed immutable payload and exact annotated tag, repairs or
  verifies the Release reservation first, then resumes deployment and Finalize.
   Explicit user confirmation is still required before Reserve or Finalize
   unless the valid legacy `--auto-approve` invocation supplied that approval.

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

For a stranded payload, stop the later-release scan. First confirm the target has
no local or remote annotated tag, Release, or attestation (query failures are not
absence). The maintainer decides whether to complete this release or retire it
through a reviewed revert PR. Completion requires the exact merged payload commit:
under specific authorization, create its annotated local tag, then use
`/cg-release --resume <tag> --source-branch <branch>` for a four-part Routine
prerelease, or start a fresh authorized Reserve flow. The resume command never
creates a local tag. Bridge and Recovery remain exceptional selectors with their
own authority rules; do not use them to repair an ordinary Routine payload.
Resume requires that existing annotated tag. This repair is not pre-approved by
auto approval for a later tag: never auto-publish or create a repair tag on the
flow's own initiative. Any partial existing pair instead needs read-only inspection
and the authorized resume path, never replacement or rollback.

Routine is a best-effort single publisher, not an atomic cutover lock. Keep the
remote controller disabled for the entire Routine publication; other write users
or an administrator can still change authority. If policy changes after a tag
push, stop before Release POST, retain the exact tag, and request authorized
read-only reconciliation. Do not retry publication or enable the controller to
repair an interrupted pair without a separate reviewed decision.

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

Under `<auto-approve>`, print this warning and continue without asking.

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

Under `<auto-approve>`, print the semver suggestion but retain the explicitly
requested tag and continue without asking. Otherwise obtain confirmation.
Record the confirmed `<next-tag>` — all subsequent steps reference it.
Set `<prerelease>` to `true` when `<next-tag>` has four numeric components and
to `false` when it has three. This derivation is mandatory even when the user
supplied the tag directly.
Retain the verified `<release-branch>` from argument parsing. Source eligibility
and protected default controller authority are separate. Neither stable nor
prerelease sources must contain the current default tip just to use its controller.

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

Show the publication decision before creating a payload PR. This is approval to
prepare and validate a release, not proof that it is ready or published. The full
gate runs at the payload commit in Step 5, before tag creation and Reserve.

```
Proposed publication (validation pending):

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

Wait for the user's explicit confirmation before proceeding to Step 5 unless
`<auto-approve>` is true. In that case print the same tag/name/notes summary and
continue: the invocation pre-approved this publication decision. Do not silently
change its tag or expand its scope.

If the user asks to adjust the tag or name, update accordingly and re-display the summary.
If the user wants to edit the notes, pause — they will edit `RELEASE_NOTES.md` directly and then confirm.

### Step 5: Create and publish the durable release source

On explicit confirmation, prepare and merge the durable payload before creating
the local tag. Reserve then owns the tag push and immediate matching non-draft
Release creation, before any documentation query or wait.

1. Require a clean, up-to-date `<release-branch>` checkout before writing payloads:

   ```powershell
   git status --porcelain
   git fetch origin <release-branch> --tags
   git rev-parse HEAD
   git rev-parse origin/<release-branch>
   ```

   Halt if status has tracked or untracked changes (other than ignored
   `RELEASE_NOTES.md`), or `HEAD` differs
   from `origin/<release-branch>`. Halt safely on a non-fast-forward release
   branch rather than creating a release from a stale checkout. Do not require
    any source commit to contain the current default tip. Exact verified source
    identity and remote lineage are the source authorization boundary.
   A clean detached checkout at the exact authorized commit is allowed. Prepare
    payload changes on `release/<next-tag>-payload`, created from that exact source
    tip, for the reviewed PR below. A preexisting branch must be reconciled, never
    reset or overwritten. Pass explicit source identity from detached checkouts.

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

6. Push the payload feature branch with `--no-follow-tags` and use
   `gh pr create --body-file <body-path> --base <release-branch> --head release/<next-tag>-payload`.
   Any PR edit also uses `--body-file`, never inline shell-interpolated prose.
   Before requesting automatic merge, verify `allow_auto_merge` and the effective
   required checks for this actual destination branch read-only. They must enforce
   the two Pester platform jobs, two Native target Python gate platform jobs and
   Conventional Commits PR title, using the exact reviewed contexts. Verify rebase
   merging is enabled. Missing, weak or unknown enforcement blocks automation;
   permission to release from a branch does not imply auto-merge is configured there.
   Do not write repository settings or substitute bypass permissions.

   Immediately run the authoritative complete native preflight at the exact
   committed PR-head SHA in parallel with PR CI. Keep this local source checkout
   unchanged until the call returns. The receipt emitter creates a producer-owned fresh LF clone
   at that SHA, using command-local Git settings without persistent config writes.
   It owns the registered pytest and module-check lists; do not copy those lists.
   Allocate a unique `<gated-receipt-path>` in the system temp directory,
   outside the working tree. Use that exact path in this command and bind the
   same path to Reserve, Finalize and resume calls; the alias `<receipt-path>`
   below always refers to this exact uniquely allocated path:

   ```powershell
   python scripts/cg_pr_preflight.py --phase committed --full-gate --run-native-target --emit-receipt <gated-receipt-path>
   ```

   Use one blocking foreground call with an explicit tool timeout of
    `9000000` milliseconds (150 minutes), not the default `120000` milliseconds.
    Child budgets are 1800 seconds for the native pytest and controller package
    tests, and 600 seconds for each other command. Progress is flushed to stderr;
    stdout carries the result.
   Silence is not a hang. Do not use background execution, polling,
   or an automatic retry after a timeout for this local gate. Remote PR CI runs
   independently during the blocking call. An unavailable budget, interrupt,
   unresolved Python or nonzero exit means halt with incomplete/failed evidence;
   do not create a tag, invoke Reserve or claim readiness. Diagnose before retry;
   never substitute `--phase prepare` or weaken committed drift checks.
   Require a valid receipt for the exact commit/tree before continuing. The receipt
   digest detects corruption; it is not remote authorization or a signature.

   Require all tests green before merging. For prereleases request
   `gh pr merge --auto --rebase <pr-url>` only after the local gate succeeds;
   stable releases keep manual merges. Do not assume rebase preserves the SHA.
   Use the same bounded observation protocol for payload and evidence PRs:
   `PR_POLL_TIMEOUT_MINUTES = 60`, interval 30 seconds, measured with a monotonic
   deadline. Read PR identity, destination, state and required checks; report status.
   A failed required check, closed-unmerged PR, unknown state or API failure means
   halt with the PR URL and state. On poll expiry with pending checks, blocked-stop
   with the PR URL and state report; never admin-merge, bypass, or blind-retry.
   A timeout does not cancel an already requested auto-merge; report that it can
   still merge remotely. Reconcile that PR before any later retry.

   After a verified merge, fetch `<release-branch>` and check out its exact current
   remote commit. Verify clean status, both payload bytes, and
   `HEAD == origin/<release-branch>`. If this SHA differs from the gated PR head,
   allow one conditioned re-execution at this actual source tip with a fresh receipt
   path. Verify payload identity first; a newer/different payload halts. After that
   gate re-fetch and require the tip still equals the gated SHA; another advance
   halts rather than looping. Do not tag an unmerged feature commit. Never bypass
   protected-branch PR requirements with a direct source-branch push.

   Verify the required active repository rulesets before creating the tag:
   `Protect release tags` must block all updates and deletions for
   `refs/tags/v*` without bypass actors; `Restrict release tag creation` must
   restrict creation of `refs/tags/v*` to repository administrators; and
   `Protect dev` must block deletion and force-pushes for `refs/heads/dev`
   without bypass actors. Halt before tag creation if any rule is absent or
   weaker than this contract.

   For stable tags, before creating the local tag, compare the tag producer's
   artifact contract with the controller at the exact protected remote default
   revision using the same conservative contract as `Assert-CgStableDocsContract`.
   Require the current extraction, composition, official-state seal and upload
   contract. Unknown layout or changed authority halts with the exact file/ref and
   protected-controller repair needed. Reserve independently enforces this before
   remote publication. Do not execute workflow text as a check, force default-tip
   ancestry, or automatically create a default-to-source sync PR. Any protected
   controller repair needs separate reviewed authorization. For prereleases,
   default advancement is informational hygiene, not a source eligibility gate.

7. Verify or create the exact annotated LOCAL tag on the clean merged payload
   commit. Do not push the tag manually. Do not use an unconditional `git tag` command:

   ```powershell
   git status --porcelain
   $head = (git rev-parse HEAD).Trim()
   $existing = git rev-parse --verify "<next-tag>^{commit}" 2>$null
   if ($LASTEXITCODE -eq 0) {
     if ($existing.Trim() -cne $head) { throw "Existing tag <next-tag> points to another commit." }
     if ((git cat-file -t refs/tags/<next-tag>).Trim() -cne "tag") { throw "Annotated tag required." }
   } else {
     git tag -a <next-tag> -m "Release <next-tag>" $head
   }
   ```

   If the tag already exists, it must be annotated and resolve to the current
   clean `HEAD`; otherwise halt without replacing it. Reserve verifies both the
   raw tag-object SHA and peeled commit when the remote tag already exists.

   With the confirmed final name and exact final `RELEASE_NOTES.md` body, run:

   ```powershell
   .\create-release.ps1 -Phase Reserve -LegacyOperation <legacy-operation> -SourceBranch <release-branch> -PreflightReceipt <receipt-path> -Tag <tag> -Name "<name>" -NotesFile RELEASE_NOTES.md
   ```

   Reserve runs local, payload, exact-tree native, credential, ruleset, historical
   release, and existing-release conflict checks before the first tag push. It
   requires exact current `origin/<release-branch>` for a new remote tag. It pushes
   only that annotated tag and immediately creates its matching non-draft Release.
   Every reservation sets `make_latest: "false"`, including stable tags, so an
   unvalidated reservation is not promoted to GitHub's latest stable release.
   There is no true distributed atomicity between Git and the GitHub API. On an
   uncertain push or POST, reconcile exact tag and Release state read-only. Never
   blindly repeat POST, force a tag push, or delete/PATCH a Release as rollback.

   Read `release-result.txt`: `CREATED|` and `EXISTS|` confirm the reservation only,
   NOT lifecycle completion. If absent, stale, or the script fails, perform read-only reconciliation
   of the exact raw/peeled tag and Release metadata. Report the known pair state;
   a missing file alone is not proof of missing publication. Re-enter the authorized
   resume path to verify or repair through Reserve before downstream gates. Resume
   can write; read-only inspection alone does not authorize it. The script's bounded
   draft-race reconciliation reads both lookup and list; exhaustion halts, never
   an alternate publisher or blind POST retry.

8. Wait for the unprivileged `release-docs.yml` push run for the exact tag and
   commit. Verify its successful conclusion and record its database ID.
   For prereleases, require the exact successful build attempt, job, steps, and artifact
   checked by Finalize. Do not wait for a Pages controller or pass PagesRunId.
   For stable tags only, then
   identify the successful `release-pages.yml` `workflow_run` controller whose run name
   is exactly `Deploy docs from <release-docs database ID>`. Halt on a missing,
   failed, or mismatched build or deployment, but leave the Release and tag intact.
   Record the controller database ID too. The controller must already exist
    at the verified protected remote default revision. The default branch name
    is not necessarily `main`. Do not invoke `/cg-wiki` or
   rebuild documentation from this prompt; the release build and protected
   controller own the immutable complete-build deployment.

### Resume An Interrupted Release

When invoked with `--resume <tag>`, derive `<prerelease>` from tag shape and verify
the explicit or attached `<release-branch>` under the same remote source policy.
Require a clean checkout at the
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

The annotated local and remote `<tag>` must match in raw tag-object SHA and peeled
commit at clean `HEAD`; that commit must remain on the authorized
`<release-branch>` lineage. If only the local tag exists, Reserve may push it only
at exact current `origin/<release-branch>`. The immutable payload must be present
and valid. Restore the exact previously confirmed title and notes from the
recorded release context; do not invent replacement metadata. Present the exact
tag, payload, name, body, and remote pair state and obtain explicit confirmation
unless `<auto-approve>` pre-approved this exact tag. In that case print the state
and continue non-interactively without changing the recorded metadata. Reuse an
external receipt only after exact tag commit/tree validation. If absent or invalid,
run the Step 5 receipt gate once at the clean tag checkout before Reserve; source
advancement does not change the tag SHA to gate. Never reuse a newer tip's receipt.
Run `-Phase Reserve` first to repair or verify the reservation, BEFORE any
documentation wait. Then resume Step 5.8 and Step 6. Never overwrite an immutable
payload or create a new tag during resume. Never delete an existing Release on
downstream failure. The only allowed untracked change is the exact canonical
attestation for this tag, which the script verifies byte-for-byte for retry.

### Step 6: Finalize And Commit Evidence

Only after Reserve has confirmed the exact tag/Release pair and Step 5.8 has
observed the required build/deployment evidence, run with the recorded exact run IDs.
For a four-component prerelease:

```powershell
.\create-release.ps1 -Phase Finalize -LegacyOperation <legacy-operation> -SourceBranch <release-branch> -PreflightReceipt <receipt-path> -Tag <tag> -Name "<name>" -NotesFile RELEASE_NOTES.md -BuildRunId <build-id> -Prerelease
```

For a stable three-component release:

```powershell
.\create-release.ps1 -Phase Finalize -LegacyOperation <legacy-operation> -SourceBranch <release-branch> -PreflightReceipt <receipt-path> -Tag <tag> -Name "<name>" -NotesFile RELEASE_NOTES.md -BuildRunId <build-id> -PagesRunId <pages-id>
```

Finalize must not push tags or create, edit, or delete Releases. It requires the
exact run chain. After cutover, a failed or missing historical deployment can use
the manual `release-pages.yml` producer with `build_run_id`, but only after separate
authorization and review of the historical recovery record. The record binds
to a protected Pages environment with the configured read-only control-App
credential for review-protection metadata. An absent credential is a setup blocker.
The record contains
`schema_version: 1`, `repository_id`, `tag`, `tag_object`, `release_sha`,
`actor_ids`, `reason`, `build_run_id`, `artifact_id`, and `artifact_digest`
(`sha256:<digest>`). Never invent these identities. Supply its exact successful
Pages run through `-PagesRunId` and use `-LegacyOperation Recovery`.
The producer preserves artifact bytes, tag lineage, latest-payload byte checks,
and current-dev freshness. An expired artifact, changed dev input, or newer
payload is a blocked checkpoint, not permission to rebuild or replace historical
bytes, move a tag, or overwrite the current site. Existing successful legacy
deployment evidence remains supported without a new deployment.

Finalize also requires the
existing exact Release, successful `release-docs.yml` push run at the tag SHA,
and, for stable tags only, successful `release-pages.yml` controller `Deploy docs from <build-id>`, then
creates or verifies the canonical release-attestation entry. The optional run IDs
avoid ambiguity after retries; without IDs the exact chain must be unique.
An attestation failure leaves the pair intact but blocks lifecycle completion.
Do not fabricate or edit an attestation manually. Do not create lifecycle
attestation for withdrawn `v1.2.0.9014`.

Draft releases are not supported by this durable publication flow. Do not pass
`-Draft`; halt if a draft is requested.
Add `-Prerelease` whenever `<prerelease>` is `true`. Four-component tags always
set it to `true`; do not publish `vX.Y.Z.<build>` as a stable GitHub Release.

After Finalize, require `FINALIZED|<id>|<url>` in `release-result.txt` as the immediate
channel. For missing/stale output, use read-only pair/attestation inspection and the
authorized resume path to re-verify Finalize; do not claim completion from stale output.
An error remains a blocked workflow. Never fabricate a result or attestation.
Never display credential helper output during authentication diagnosis.

Then run `python scripts/cg_generate_targets.py --all`. Review the canonical
attestation, all generated attestation copies, and ownership manifests. Create a
separate evidence branch from the current verified source tip, preserving any
source advancement; transfer only this tag's canonical and generated evidence.
Validate that the diff contains only the attestation and its deterministic copies
and required ownership manifests. Any unrelated or conflicting change halts.
No separate local full gate at the evidence commit: the evidence PR's required checks
provide GitHub-enforced verification, not a reused tag receipt for a different tree.
Verify those effective required checks for the destination before relying on them.
Commit only the reviewed evidence paths, push `--no-follow-tags`, and use
`gh pr create --body-file <body-path> --base <release-branch> --head <evidence-branch>`.
Prereleases use `gh pr merge --auto --rebase <evidence-pr-url>` and the same bounded
poll protocol; stable merges remain manual. If settings/checks are unavailable,
halt rather than bypass. Only after those records are merged and their exact bytes
verified on the remote source branch may you report lifecycle completion.
The original tag remains unchanged. Report the Release URL only with that verified
lifecycle status. The reservation
remains published if evidence generation, tests, or the evidence PR fails.
Neither Reserve nor Finalize promotes a Release to GitHub's latest stable release.
Any later stable promotion is a separate, explicitly authorized maintainer action
after all deployment, attestation, test, and evidence-commit gates have passed.
Do not add a promotion PATCH to either phase or treat reservation as promotion approval.

## Rules

- Never run `create-release.ps1` without explicit user confirmation in Step 4,
  the equivalent resume confirmation, or valid exact-tag legacy auto approval.
  Reserve is the only publisher; no release-API tag creation or fallback publisher
  is permitted. Payload PRs follow the publication decision, never precede it.
  Reserve requires validated merged
  payloads and the exact annotated local tag. Finalize additionally requires the
  published pair and exact successful build evidence (plus deployment for stable).
- Never manually push a bare release tag in normal release instructions. Reserve
  owns the tag push plus immediate Release. Never delete/PATCH a Release or move
  a protected tag to recover from downstream failures.
- Never modify `SCHEMA_VERSION` automatically. Warn only.
- Require stable three-component sources in protected remote `production_branches`
  or the remote default. Allow prereleases from any verified same-repository remote branch.
  No local policy, tag-shape branch inference, ancestry-to-default or stable override
  may replace this policy. Keep exact source/tag/SHA and authority rechecks.
- Option A is a docs destination policy: prereleases need a tag build, not full-site
  deployment. Only dev refreshes `/dev/`; other source branches have no promised
  preview. Previews preserve authenticated durable official bytes. Protected remote
  activation, an authorized official snapshot seed and preview verification are
  separate required rollout evidence; local tests cannot establish activation.
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
