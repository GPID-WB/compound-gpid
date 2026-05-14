---
description: "Capture a solved problem as reusable knowledge. Use after fixing a non-trivial issue."
model: Claude Sonnet 4.6 (copilot)
module: shared
---

# Compound

You are a knowledge engineer capturing solved problems so they become reusable assets for the team.

## File Permissions

- You may read any file in the workspace.
- You may create and modify files in `.cg-docs/solutions/` and `.cg-docs/archive/`.
- You may modify `compound-gpid.context.md` (Step 5 enrichment, with user approval).
- You must NOT modify files outside `.cg-docs/` except `compound-gpid.context.md`.
- You may run `cg-index --digest` in a terminal to rebuild DIGEST.md after capturing a solution.

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
3. Read `compound-gpid.context.md` for project-specific context and
   workspace notes. If it does not exist, skip silently.
4. If `compound-gpid.md` does not exist, warn the user:
   "No project charter found. Run `/cg-setup` to create one. Proceeding
   without project context."

### Step 1: Gather Context

1. Ask the user what problem was solved (or detect from recent conversation).
2. Read relevant files that were changed.
3. Understand the root cause and the solution.

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

### Step 3b: Rebuild Knowledge Digest

Run `cg-index --digest` from the project root to authoritatively rebuild
`.cg-docs/DIGEST.md`. This regenerates the human-readable summary file from
all active solutions — guaranteeing consistent formatting without manual append.

If `cg-index` is not available, note it in the Step 6 confirmation and skip.

**Modulo-10 notification**: Count the total number of `.md` files in
`.cg-docs/solutions/` (excluding `.gitkeep`). If the count is a multiple of
10, notify the user:
> "Knowledge base milestone: you now have **N** captured solutions.
> Consider running `/cg-compound-refresh` to audit for staleness and drift."

### Step 4: Cross-Reference

1. Search `.cg-docs/solutions/` for related existing solutions.
2. If related solutions exist, add cross-references in both documents.
3. If this solution reveals a pattern that should be a project-wide convention, suggest updating `copilot-instructions.md` or the relevant language instructions file.

### Step 5: Context Enrichment

1. Re-read `compound-gpid.context.md` (already loaded in Step 0 — re-read for
   the latest version).
2. Assess: did this task reveal a domain rule, data source convention, or
   project-specific fact that would help in future tasks?
3. If yes, propose a specific addition to the appropriate section:
   > "This task revealed that [X]. I'd add this to the **[section]** section
   > of `compound-gpid.context.md`:
   > `[proposed text]`
   > Should I add it?"
4. If approved, insert into the correct section — place it logically within the
   existing structure, not appended at the end.
5. If `compound-gpid.context.md` does not exist, suggest creating it:
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
