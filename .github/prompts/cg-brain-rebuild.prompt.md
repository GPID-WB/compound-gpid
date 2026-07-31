---
description: "Rebuild the project knowledge brain (BRAIN.md + indexes)."
---

# Brain Rebuild

You are a knowledge index maintainer. BRAIN.md is the team's semantic knowledge
index — it clusters `.cg-docs/` solutions into topics and maps relationships
between entities, enabling future work sessions to surface relevant past
learnings automatically. Your job is to trigger a full rebuild of this index
and report the results clearly.

## When to Use

Run `/cg-brain-rebuild` directly when:

- **After pulling `.cg-docs/` changes from collaborators** — the BRAIN files
  are not committed; each machine rebuilds from the source solution files.
- **After manually editing solution files** in `.cg-docs/solutions/` — the
  brain won't reflect your edits until rebuilt.
- **After a `/cg-compound` run where brain rebuild was skipped** — for example,
  when `cg-index` was unavailable during that session.
- **When the brain is stale** — e.g., after a failed or interrupted prior
  rebuild, or when `BRAIN.md` is missing.

For normal knowledge-capture workflows use `/cg-compound`, which calls brain
rebuild automatically at the end.

## File Permissions

- You may read any file in the workspace.
- You may run `cg-index --brain` in a terminal.
- You must NOT create or modify any files directly — the brain files are
  written by `cg-index`, not by this prompt.

## Process

### Step 0: Get Bearings

1. Read `compound-gpid.md` in the project root for project context (objective,
   constraints, current focus).
2. Read `compound-gpid.local.md` for user config (language, project type,
   review depth).
3. Load `.github/shared/context-loading.contract.md`. Do not read
   `compound-gpid.context.md` by default; this maintenance prompt rebuilds the
   Knowledge Brain from `.cg-docs/` via `cg-index --brain`, and only needs
   targeted user/config context if a user-specific setting is relevant. If such
   context is needed, state `Context expansion: reading <artifact/section>
   because <reason>.`
4. If `compound-gpid.md` does not exist, warn the user:
   "No project charter found. Run `/cg-setup` to create one. Proceeding
   without project context."

### Step 1: Run the brain rebuild

Run `cg-index --brain` from the project root in a terminal.

### Step 2: Verify success

Evaluate in this order. Stop at Step 3 on the first sign of failure; proceed
to the next tier on success for additional confirmation:

1. **Primary — exit code**: If the command exited with a non-zero code, go to
   Step 3 (error handling). If exit code is 0, proceed to the secondary check.
2. **Secondary — stdout pattern**: Scan stdout for a line matching
   `[cg-index] Brain index written to`. If found, parse the entity, topic, and
   edge counts from the parenthesised suffix
   (e.g., `(127 entities, 18 topics, 43 edges)`) and report them to the user.
   Do NOT rely on the last line of stdout — legacy file removal messages
   (`[cg-index] Removed legacy DIGEST.md`, etc.) may follow the stats line.
   If the stats line is not found despite exit 0, report counts as
   'unavailable' and note that the brain was rebuilt but metrics could not
   be parsed from output.
   If entity count is 0, emit an advisory: "No entities indexed — check
   that `.cg-docs/solutions/` contains at least one captured solution, or
   run `/cg-compound` to capture your first solution."
3. **Tertiary — file existence**: Confirm `.cg-docs/BRAIN.md` exists as a
   sanity check after a successful run. If `BRAIN.md` is absent despite a
   successful exit code and stats line, warn:
   "BRAIN.md not found despite a successful run — re-run `/cg-brain-rebuild`
   or check write permissions in `.cg-docs/`."

Report success:
> "Brain rebuild complete.
> - **X** entities indexed
> - **Y** topics clustered
> - **Z** edges detected
> - Output: `.cg-docs/BRAIN.md` (+ partition files — `BRAIN-01.md`, `BRAIN-log.md` — and `brain-index.json`)"

### Step 3: Handle errors

If `cg-index` is not available or exits with a non-zero code, report the error
clearly and suggest the three most likely causes:

1. **`cg-index` not on PATH**: Verify the install with `cg-index --version`.
   If that fails, check that `bin/` was added to PATH during `install.ps1` /
   `install.sh`.
2. **Not running from project root**: `cg-index` requires a `.cg-docs/`
   directory in the current working directory. Run from the project root.
3. **`.cg-docs/` directory not yet created**: If this is a freshly linked
   project, run `/cg-setup` to initialize the project structure, which
   creates `.cg-docs/` along with the required subdirectories.

Show the raw error output from `cg-index` verbatim so the user can diagnose
unexpected failures beyond these two common causes.
