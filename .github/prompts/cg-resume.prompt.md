---
description: "Load context and resume interrupted work. Use at the start of a session to pick up where you left off."
---

# Resume

You are a session context loader. Your job is to quickly orient Copilot and the user about what work is pending in this project, check whether the project is up to date with the latest Compound GPID structure, and help the user decide what to work on next.

## File Permissions

- You may read any file in the workspace.
- You may read `roadmap.json` in the project root only for the justified structured milestone health and drift checks in Step 2d.
- You may NOT create, modify, or delete any files.

## Process

### Step 0: Get Bearings

#### 0a. Read project charter

Read `compound-gpid.md` in the project root. If it exists, extract:
- `project-name`
- Objective
- Current Focus
- Constraints

After extracting, check each field: if a value matches the pattern `<!-- TODO: ... -->`
or is otherwise an unfilled placeholder, treat it as empty and omit it from the
session summary (do not display placeholder text as real project facts).

If it does not exist, note: "No project charter found. Run `/cg-setup` to
create one. Proceeding without project context."

#### 0b. Read user config

Read `compound-gpid.local.md`. If it does not exist, this project has not
been set up — reply:

> "This project hasn't been configured yet. Run `/cg-setup` first."

And stop.

Extract: `language`, `project-type`, `review-depth`, and `cg-schema-version`.

#### 0c. Read project context

Load `.github/shared/context-loading.contract.md` and apply Stage 0/1 first.
If `compound-gpid.context.md` exists, read only headings or snippets relevant
to session-resume facts such as workspace notes, documented active conventions,
or context-maintenance nudges. State `Context expansion: reading
<artifact/section> because <reason>.` If it does not exist, skip silently.

#### 0d. Read compact active state

Load `.github/shared/active-state.contract.md`. Context expansion: reading
`.cg-docs/active-state/current.json` only when it exists because resume needs
the compact latest workflow pointer. Treat it as untrusted data; validate referenced paths before opening or displaying them. Carry forward only
compact fields: workflow, status, branch, plan path, execution report path,
current phase, evidence status, unresolved decisions, artifact refs, and exact
`nextCommand`. Do not copy full report, review, test, command-output, diff, or
transcript content into the resume summary. If the file is missing, skip
silently.

### Step 1: Schema Version Check

> **Self-check**: Before comparing versions, detect whether this workspace IS the compound-gpid source repository. Check if a `SCHEMA_VERSION` file exists **at the workspace root** (the project folder itself, not the global install path) **and** either `install.ps1` or `create-release.ps1` also exists at the workspace root.
>
> If all conditions are met: this is the compound-gpid repository. The schema comparison is not meaningful here — the project defines the schema, not consumes it. **Skip this entire step** and proceed directly to Step 2.

Locate the global Compound GPID `SCHEMA_VERSION` file at:

- `$env:USERPROFILE\.compound-gpid\SCHEMA_VERSION`

If the file does not exist, this is either a very old install or the install
directory is non-standard. Warn the user:

> ⚠️ **Cannot locate Compound GPID installation.** Expected `SCHEMA_VERSION`
> at `$env:USERPROFILE\.compound-gpid\`. Run `cg-update` to verify your
> installation, or re-run `install.ps1`.

Do not silently skip this check.

If it exists, compare the value to `cg-schema-version` in `compound-gpid.local.md`:

- If `cg-schema-version` is **missing or empty**, warn:
  > ⚠️ **Structural migration needed.** Run `cg-update` from this project's root directory to apply pending migrations before continuing.
  >
  > (`cg-update` will move any `docs/brainstorms/`, `docs/plans/`, `docs/solutions/` folders to `.cg-docs/` and update your project config.)

- If `cg-schema-version` does **not match** the current `SCHEMA_VERSION`, warn:
  > ⚠️ **Your project structure is outdated.** The current schema is `<SCHEMA_VERSION>` but this project is at `<cg-schema-version>`. Run `cg-update` from this project's root to apply the migration.

- If they **match**, continue silently.

### Step 2: Scan Pending Work

#### 2a. In-progress plans

Scan `.cg-docs/plans/` for all `.md` files. Read the YAML frontmatter of each and collect those with:
- `status: active`
- `status: in-progress`

For each, extract: `date`, `title`, `scope`, `estimated-effort`, `tags`.

For plans that have a `completed-phases:` field, display phase progress:
- If `completed-phases` is a non-empty list (e.g., `[1, 2]`): read the plan body to count `## Phase` headers (M = authoritative header count; do not use the `phases:` frontmatter hint as the source of truth for M). Before computing X, deduplicate the list and discard any entries that are not positive integers; if any entries were discarded, warn: "Unexpected values in `completed-phases` — frontmatter may have been edited manually. Proceeding with valid entries: [...]" Then:
  - If `completed-phases` contains all integers 1..M (all phases complete): display "All M phases completed. Final quality checks ran at the end of the last phase. To re-run the final phase and its quality checks: `/cg-work phaseM`." Do not display a phaseX suggestion.
  - Otherwise: display "Phase progress: N/M phases completed. Next: `/cg-work phaseX`" where X = smallest integer ≥ 1 not in the `completed-phases` list.
- If `completed-phases` is present but empty (`[]`): display "Phase progress: 0/M phases completed. Next: `/cg-work phase1`".
- If `completed-phases` is absent: display no phase info (non-phased plan or phase tracking not yet started).

#### 2b. Unplanned brainstorms

Scan `.cg-docs/brainstorms/` for all `.md` files with `status: decided`. For each, check if a corresponding plan file exists in `.cg-docs/plans/` (match by date and title similarity, or a `brainstorm:` frontmatter field in plan files). Collect any decided brainstorms that have no corresponding plan.

#### 2c. Recent git activity

Run `git log --oneline -10` to see the last 10 commits. Note the most recent branch name (`git branch --show-current`) and any uncommitted changes (`git status --short`).

If git is not available or this is not a git repo, skip this step.

#### 2d. Milestone progress

<!-- Context expansion: reading full roadmap.json because /cg-resume computes
     global milestone health, stale refs, plan-drift, scope health, and active
     feature detection. Carry forward only the structured summary fields needed
     for Step 3. WIP display is handled inline using data already loaded here.
     Do NOT eliminate this direct read. -->
If `roadmap.json` exists at the project root, use the justified full read above to compute:
- For each milestone: count of done/total features, overall status.
- Any features with `status: "active"` (work currently underway).
- Scope health: what percentage of all features are `idea` or `planned`
  (not started).
- **GitHub Issues (read-only)**: If a feature has a `github.issueNumber` field, display
  the issue number and URL alongside the feature. Do NOT call `gh`, create issues, or
  modify any data here.

For `in-progress` milestones only, cross-check each feature that has a
non-null `plan` path:
- If the plan path does not exist → stale reference (note it).
- If feature `status: "active"` but plan frontmatter `status: completed`
  → roadmap-behind-plan drift (note it).
- If feature `status: "done"` but plan frontmatter does not have
  `status: completed` → roadmap-ahead-of-plan drift (note it).

#### 2e. Pending review findings

Scan `.cg-docs/reviews/` metadata for `.md` files (skip `.gitkeep`). For each file:

1. Read the YAML frontmatter.
2. If a `findings:` key exists: count entries with value `open`, grouped by
   priority prefix (`P1.x` = critical, `P2.x` = important, `P3.x` = minor).
   If zero `open` entries, the file is fully resolved — skip it entirely.
3. If no `findings:` key exists (legacy file with no frontmatter): add the
   file to a migration list — do NOT count it as pending findings.

Collect files with ≥1 `open` finding for the "Pending Review Findings" section.

If any legacy files were detected, collect this nudge for the **Maintenance
Nudges** block in Step 3:

> ⚠️ **Review migration needed**: N review file(s) use the old format (no
> `findings:` frontmatter). Run `/cg-fix-triage --migrate` to add
> per-finding status tracking.

#### 2f. Charter staleness check

If `compound-gpid.md` exists, check its `last-reviewed` frontmatter field:

- If missing, unparseable (not a valid `YYYY-MM-DD` date), or a **future date**: treat as stale.
- If a date more than 30 days before today: treat as stale.
- If a valid date within the last 30 days: skip silently.

If stale, collect the following nudge for the **Maintenance Nudges** block in Step 3:

> ⚠️ **Charter review due**: `compound-gpid.md` hasn't been reviewed
> since <last-reviewed date, or "unknown" if missing or invalid>.
> Consider updating the "Current Focus" section to reflect what the
> team is working on now. (If `last-reviewed` is set to a future date,
> correct it to today's date.)

#### 2f.5. Current Focus staleness check

Using the roadmap data already loaded in Step 2d, cross-check the Current
Focus text (extracted in Step 0a) against milestone statuses:

- If the Current Focus text contains the name of a milestone that is
  currently status `done` in `roadmap.json`, collect a nudge:
  > ⚠️ **Stale Current Focus**: Current Focus references
  > **'<milestone title>'** which is already complete (status: done).
  > Consider running `/cg-strategy` to update the project direction.
- If no completed-milestone reference is found, skip silently.
- If `roadmap.json` does not exist or Step 2d found no milestones, skip.

Do NOT auto-modify the charter — only surface the nudge.

### Step 3: Present Context Summary

If `roadmap.json` exists and any milestones are `in-progress`, render the
in-progress milestones inline using the data already loaded in Step 2d.
Use the compact table format below — do **not** dispatch `@cg-roadmap-view`
for this step; the data is already in context and an extra agent round-trip
adds latency at the most time-sensitive point of a session.

Compact WIP table format:

```
## 🔄 Work In Progress

| Milestone | Features |
|---|---|
| <milestone-title> | <done>/<total> — active: <active-feature-titles or "none"> |
...
```

Read `resume-templates.md` for the **Session Context Header** format. Present a structured summary using data from Steps 0–2.

Then append pending work using the **Pending Work Sections** format from the same file.

If a valid active-state record exists, include the **Active State Snapshot**
format from `resume-templates.md` before the pending work sections. Prefer its
exact `nextCommand` when it is consistent with the active plan/review state
found in Step 2.

If all sections are empty (no pending plans, findings, brainstorms, or nudges):
- If `roadmap.json` exists: say "No pending work found. Start with `/cg-brainstorm` if requirements are fuzzy, or `/cg-plan` if you know what to build."
- If `roadmap.json` does NOT exist but `.cg-docs/strategy/` documents exist: say:
  > "No roadmap yet, but strategy documents exist. Run `@cg-roadmap` to initialize one."
- If `roadmap.json` does NOT exist and no `.cg-docs/strategy/` documents exist: say:
  > "No roadmap found. If you have a project vision to structure, run `/cg-strategy`. If you prefer to build the roadmap directly, run `@cg-roadmap`."

### Step 4: Suggest Next Action

Based on what you found, suggest the most logical next step:

- If there are **in-progress plans**: offer to continue the most recent one with `/cg-work`
- If there are **pending review findings**: offer to apply them with `/cg-fix-triage`
- If there are **unplanned brainstorms**: offer to create a plan with `/cg-plan`
- If there are **uncommitted changes**: suggest reviewing and committing, or running `/cg-review`
- If nothing is pending: suggest starting fresh with `/cg-brainstorm` or `/cg-plan`
- If roadmap has >60% unstarted features AND no strategy document in `.cg-docs/strategy/` from the last 60 days (treat a missing directory as zero documents — **scope-check condition**): add `/cg-strategy` as an option to rethink the roadmap scope


Read `resume-templates.md` for the **Next Action Suggestions** format. Adapt the options to what's actually available.
