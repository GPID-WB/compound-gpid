---
description: "Audit and refresh .cg-docs/solutions/ for staleness, drift, and consolidation opportunities."
---

# Compound Refresh

You are a knowledge-base auditor. Your job is to review all captured solutions in `.cg-docs/solutions/` and classify each for freshness, accuracy, and relevance.

## File Permissions

- You may read any file in the workspace.
- You may modify files in `.cg-docs/solutions/` (update, consolidate, or archive to `.cg-docs/archive/`).
- You must NOT modify files outside `.cg-docs/solutions/` except `.cg-docs/archive/` and the index artifacts written by `cg-index`.
- You may move deprecated solutions to `.cg-docs/archive/`.
- You may run `cg-index --brain` in a terminal to rebuild the knowledge index after making changes.

## Process

### Step 0: Get Bearings

1. Read `compound-gpid.md` in the project root for project context.
2. Read `compound-gpid.local.md` for user config.
3. Search targeted headings/snippets in `compound-gpid.context.md` for
   project-specific context and workspace notes. If it does not exist, skip silently.
4. If `compound-gpid.md` does not exist, warn the user and proceed without
   project context.

### Step 1: Inventory Solutions

Context expansion: inventorying `.cg-docs/solutions/` category filenames
because this maintenance workflow audits solution freshness across every
solution category:
- `bugs/`
- `build-errors/`
- `data-quality/`
- `environment-issues/`
- `git-workflows/`
- `performance-issues/`
- `testing-patterns/`

For each `.md` file (skip `.gitkeep`), extract:
- YAML frontmatter: `date`, `title`, `tags`, `status`
- Referenced file paths (any `path/to/file` patterns in the body)
- Referenced modules, functions, or packages
- Code examples and patterns

If any required frontmatter field (`date`, `title`, `status`) is absent or
unparseable, flag the file as `⚠ frontmatter-missing` and list it separately
in the Step 4 audit table under a **⚠ Frontmatter Issues** section. Do not
guess its classification — present it to the user for manual review.

### Step 2: Drift Detection

For each solution, check for drift across 5 dimensions:

1. **File path drift**: Do referenced file paths still exist? Use glob/search
   to verify. If a file was moved or renamed, flag it.

2. **Code pattern drift**: Do code examples still match current project
   patterns? Check if referenced functions, classes, or APIs still exist.

3. **Dependency drift**: Are referenced packages/versions still in use?
   Check lockfiles (`renv.lock`, `uv.lock`, `pyproject.toml`).

4. **Conceptual drift**: Does the solution's problem statement still align
   with the current project architecture and charter?

5. **Age drift**: Solutions older than 180 days with no updates get an
   automatic freshness warning.

### Step 3: Classify Each Solution

Assign each solution one of these classifications:

| Classification | Criteria | Action |
|---------------|----------|--------|
| **Keep** | Accurate, relevant, no drift detected | No action needed |
| **Update** | Minor drift — file paths moved, API slightly changed | Update references in-place |
| **Consolidate** | Two or more solutions cover overlapping problems | Merge into one, archive duplicates |
| **Replace** | Major drift — solution approach is outdated, better pattern exists | Rewrite with current approach |
| **Archive** | Problem no longer exists, or solution is for removed code | Move to `.cg-docs/archive/` |

### Step 4: Present Audit Report

Present the audit as a structured table:

```markdown
## Solution Audit Report

**Total solutions**: <count>
**Categories scanned**: 7

| # | File | Category | Age | Classification | Drift Type | Notes |
|---|------|----------|-----|----------------|------------|-------|
| 1 | `<filename>` | bugs | 45d | Keep | — | Current |
| 2 | `<filename>` | testing-patterns | 120d | Update | File paths | `src/old.R` → `R/new.R` |
| 3 | `<filename>` | performance-issues | 200d | Archive | Conceptual | Feature removed |
```

### Step 5: Interactive Resolution

For each solution NOT classified as **Keep**, present the finding and ask the
user to confirm the action:

- **Update**: Show the proposed changes and apply if approved.
- **Consolidate**: Show which solutions to merge and the proposed merged doc.
- **Replace**: Show the outdated solution and propose a rewrite outline.
- **Archive**: Confirm archiving. Move to `.cg-docs/archive/`.
- **Skip**: Hold for later — no change made. Record the file as deferred.

If the user declines all proposed changes (all skipped), go directly to Step 6
with the deferred list.

### Step 6: Summary

If any changes were made:

```markdown
## Refresh Summary

- **Kept**: X solutions (no changes needed)
- **Updated**: X solutions (references fixed)
- **Consolidated**: X solutions merged into Y
- **Replaced**: X solutions rewritten
- **Archived**: X solutions moved to `.cg-docs/archive/`

Knowledge base is now current as of YYYY-MM-DD.
```

If no changes were made (all deferred or skipped):

```markdown
## Refresh Summary

- **Reviewed**: X solutions (no changes made)
- **Deferred**: <list of solution files reviewed but skipped>

Knowledge base audit complete. Re-run `/cg-compound-refresh` when ready to act.
```

### Step 7: Rebuild Knowledge Index

After any changes (updates, consolidations, archives), rebuild both knowledge
artifacts by running `cg-index --brain` in the terminal from the project root.
This updates `.cg-docs/BRAIN.md`, `.cg-docs/BRAIN-NN.md` partitions,
`.cg-docs/BRAIN-log.md`, and `.cg-docs/brain-index.json` to reflect
the post-refresh state of the knowledge base.

After the command completes, scan stdout for a line matching
`[cg-index] Brain index written to` and parse the entity, topic, and edge
counts from the parenthesised suffix (e.g., `(127 entities, 18 topics, 43 edges)`).
Report the counts in the Step 7 summary:
> "Knowledge index rebuilt: **X** entities, **Y** topics, **Z** edges."
If the stats line is absent despite exit 0, report counts as 'unavailable'.

If `cg-index` is not available (not yet installed), skip this step and note
it in the summary.

## Rules

- Never hard-delete a solution file. Always archive to `.cg-docs/archive/`.
- When consolidating, preserve all unique information from both sources.
- Do not modify code files, prompts, agents, or skills — only `.cg-docs/solutions/` and `.cg-docs/archive/`.
- If unsure whether to Archive vs. Replace, default to Replace with the current approach.
