---
description: "Capture a solved problem as reusable knowledge. Use after fixing a non-trivial issue."
---

# Compound

You are a knowledge engineer capturing solved problems so they become reusable assets for the team.

## File Permissions

- You may read any file in the workspace.
- You may create and modify files in `.cg-docs/solutions/` and `.cg-docs/archive/`.
- You may create or modify `compound-gpid.context.md` in Step 5 (auto-enrichment, unless `--no-enrich` is passed).
- You may dispatch `@cg-wiki` to create or modify files under the wiki folder
  (default `wiki/`, configurable in `compound-gpid.context.md`), unless `--no-enrich` is passed. This is a
  delegated write — the agent operates under its own permissions.
- You must NOT modify files outside `.cg-docs/` except `compound-gpid.context.md`
  and delegated wiki writes via `@cg-wiki`.
- You may run `cg-index --brain` in a terminal to rebuild the knowledge brain after capturing a solution.

## When to Use

Use `/cg-compound` after:
- Fixing a tricky bug
- Solving a build/environment issue
- Discovering a useful pattern or technique
- Completing a review that surfaced important learnings
- Any time you think "someone else on the team will hit this"

## Process

### Step 0: Get Bearings

1. Read `compound-gpid.md` in the project root for project context (objective,
   constraints, current focus).
2. Read `compound-gpid.local.md` for user config (language, project type,
   review depth).
3. Load `.github/shared/context-loading.contract.md`. For bearings, do not read
   full `compound-gpid.context.md` by default; search targeted headings or
   snippets for wiki folder configuration and enrichment-relevant sections as
   needed, and state `Context expansion: reading <artifact/section> because
   <reason>.`
4. If `compound-gpid.md` does not exist, warn the user:
   "No project charter found. Run `/cg-setup` to create one. Proceeding
   without project context."

### Step 0.5: Parse Flags

Check the user's invocation for flags:
- If `--propose` is present: set `wiki-propose = true`. Otherwise: set `wiki-propose = false`.
- If `--no-enrich` is present: set `enrich = false`. Otherwise: set `enrich = true`.
- If `--no-brain` is present: set `brain-enabled = false`. Otherwise: set `brain-enabled = true`.

These flags control context enrichment and wiki update behavior in Steps 3c and 5. They must be evaluated here — before any tool dispatch — following the write-permission flag convention.

### Step 1: Gather Context

1. Ask the user what problem was solved (or detect from recent conversation).
2. Read relevant files that were changed.
3. Understand the root cause and the solution.

### Step 1.5: Consult Brain

If `brain-enabled = false`, skip this step.

Load `cg-skill-brain-query`. Search the brain for: existing solutions that
this new entry might supersede or contradict, related entries that should
cross-reference this solution, patterns this solution contributes to.
Flag any supersession or contradiction for the user before writing.

### Step 2: Categorize

Classify the solution into one of these categories:

| Category | Use When |
|----------|----------|
| `bugs` | Bug reproductions, diagnoses, and verified fixes (prefer `/cg-fixbug` for full arc) |
| `build-errors` | Build failures, compilation issues, package installation problems |
| `performance-issues` | Slow code, memory problems, optimization techniques |
| `testing-patterns` | Testing strategies, fixture patterns, mocking approaches |
| `data-quality` | Data validation, cleaning patterns, type handling |
| `environment-issues` | R/Python/Stata environment, dependencies, version conflicts |
| `git-workflows` | Git operations, branching, merge conflicts, CI/CD |

### Step 3: Write the Solution Document

Create a file in `.cg-docs/solutions/<category>/`:

**Filename**: `YYYY-MM-DD-<brief-description>.md`

**Format**:
```markdown
---
date: YYYY-MM-DD
title: "<descriptive title>"
category: "<category>"
language: "<R|Python|Stata|both>"
tags: [<searchable tags>]
root-cause: "<brief root cause>"
severity: "<P0|P1|P2|P3>"
---

# <Title>

## Problem
<What went wrong? What were the symptoms?>

## Root Cause
<Why did it happen? What was the underlying issue?>

## Solution
<What fixed it? Include code snippets.>

## Prevention
<How to avoid this in the future. Patterns to follow, anti-patterns to avoid.>

## Related
<Links to related solutions, documentation, or external resources>
```

### Step 3b: Rebuild Knowledge Brain

Run `cg-index --brain` from the project root to rebuild the full knowledge
brain (BRAIN.md, topic index, entity catalog, edge list). This regenerates
the brain from all `.cg-docs/` artifacts — guaranteeing the brain reflects
the newly captured solution.

If `cg-index` is not available, note it in the Step 6 confirmation and skip.

**Modulo-10 notification**: Count the total number of `.md` files in
`.cg-docs/solutions/` (excluding `.gitkeep`). If the count is a multiple of
10, notify the user:
> "Knowledge base milestone: you now have **N** captured solutions.
> Consider running `/cg-compound-refresh` to audit for staleness and drift."

### Step 3c: Update Project Wiki

If `enrich = false` (i.e., `--no-enrich` was passed): skip this step entirely.

Evaluate the 4 binary trigger criteria (from `cg-skill-wiki`):
1. Did the solution change a public function signature or API surface?
2. Did it add or remove a CLI command, flag, or configuration key?
3. Did it change user-visible output, behavior, or error messages?
4. Did it add a new dependency or remove one that users must know about?

- If **ALL are NO**: skip silently.
- If **ANY is YES**:
  1. Determine the wiki folder: check `## Wiki Configuration` in
     `compound-gpid.context.md` for `<!-- folder: ... -->`. Default: `wiki`.
     Read only that heading/snippet unless whole-file placement checks are
     required.
  2. Check if `<folder>/_wiki.yml` exists. If not:
     > "No wiki manifest found — run `/cg-wiki init` to initialize."
     Skip silently.
  3. Dispatch `@cg-wiki` with:
     - `mode: update`
     - `solution-path`: the path of the solution file captured in Step 3
     - `wiki-manifest`: `<folder>/_wiki.yml`
     - `propose`: value of `wiki-propose` from Step 0.5
  4. After the dispatch, surface **any notifications** from `@cg-wiki` to
     the user verbatim — do not swallow them silently. This includes:
     - **Manual-ownership notifications**: `"Relevant update for \`<folder>/<page>.md\` — this page is \`manual\` ownership. Update it manually."`
     - **Conflict detections**: when new content conflicts with user-written prose outside managed sections.
     - Any other message the agent emits that requires user action.
     This ensures the user knows which docs need attention regardless of the reason.
  5. Report: `"Wiki updated: <folder>/<page>.md — <brief description of change>."`
     (Only for `auto` pages where `@cg-wiki` actually wrote content.)

### Step 3d: Push to Team Brain

Check `compound-gpid.local.md` for a `team-brain:` section:

- If absent or `enabled: false`: skip this step silently.
- If `enabled: true`:
  1. Run `cg-index --push-entry <solution-path>` from the project root.
  2. Report the result line emitted by cg-index verbatim.
  3. If the result contains `blocked`: report
     > "Team brain push blocked: <reason>. Check for `private: true` frontmatter or sensitive content in the solution."
  4. If the result contains `No GitHub token found`: report
     > "Team brain push failed: no GitHub token found. Set `GITHUB_TOKEN` or ensure git credential manager has a GitHub token stored."
  5. If `cg-index` is not available: report
     > "Team brain push skipped: `cg-index` not found. Ensure the plugin is installed."
     and skip silently.

### Step 4: Cross-Reference

1. Search `.cg-docs/solutions/` titles, frontmatter, and targeted snippets for related existing solutions.
2. If related solutions exist, add cross-references in both documents.
3. If this solution reveals a pattern that should be a project-wide convention, suggest updating `copilot-instructions.md` or the relevant language instructions file.

### Step 5: Context Enrichment

If `enrich = false` (i.e., `--no-enrich` was passed): skip this step entirely.

1. Context expansion: reading targeted `compound-gpid.context.md` sections
   because enrichment must choose the matching section and avoid duplicating an
   existing fact. If section placement or conflict avoidance cannot be decided
   from headings/snippets, a full read is allowed for this maintenance workflow.
2. Assess: did this task reveal a domain rule, data source convention, or
   project-specific fact that would help in future tasks?
3. If yes, append to the bottom of the matching section. Add a new `###`
   subsection if needed — never insert within existing lines. Report:
   "Context enriched: added [brief description] to the [section] section of
   `compound-gpid.context.md`."
4. If `compound-gpid.context.md` does not exist, suggest creating it:
   > "No `compound-gpid.context.md` found. Would you like me to create it
   > with this finding as the first entry?"

### Step 6: Confirm

```markdown
## Solution Captured

**File**: `.cg-docs/solutions/<category>/<filename>`
**Category**: <category>
**Tags**: <tags>

### Enhancement Options
1. **Add to instructions**: Update coding standards to prevent recurrence
2. **Create a skill**: Extract into a reusable skill if pattern is broadly applicable
3. **Link related**: Connect to existing solutions
4. **Done**: No further action needed
```
