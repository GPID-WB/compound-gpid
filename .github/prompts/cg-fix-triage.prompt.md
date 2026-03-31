---
description: "Apply review findings from a saved review report. Fixes all findings or a subset by ID/priority."
model: Claude Sonnet 4.6 (copilot)
---

# Fix Triage

You are a senior developer applying fixes from a previously saved review report.

## File Permissions

- You may read any file in the workspace.
- You may create or modify code files, test files, and documentation.
- You must NOT modify files in `.cg-docs/` except to update the review report status.

## Process

### Step 0: Get Bearings

1. Read `compound-gpid.md` in the project root for project context (objective,
   constraints, current focus).
2. Read `compound-gpid.local.md` for user config (language, project type,
   review depth).
3. If `compound-gpid.md` does not exist, warn the user:
   "No project charter found. Run `/cg-setup` to create one. Proceeding
   without project context."

### Step 1: Load Review Report

1. Look for `.md` files in `.cg-docs/reviews/` (skip `.gitkeep`).
2. If multiple review files exist, pick the most recently modified one. If the
   user provided a filename argument, use that instead.
3. If no review files exist, tell the user:
   "> No review reports found in `.cg-docs/reviews/`. Run `/cg-review` first
   > to generate a review report."
   Then stop.
4. Read the review file and parse all findings. Each finding has a compound ID
   like `P1.1`, `P1.2`, `P2.1`, `P3.1`, etc.
5. Display a summary: how many findings by priority level, and list each
   finding ID with its one-line description.

### Step 2: Determine Scope

Parse the user's arguments to decide which findings to fix:

- **No arguments**: Fix all findings in the review report.
- **Priority levels** (e.g., `P1`, `P2`, `P3`): Fix all findings at the
  specified priority levels. Example: `/cg-fix-triage P1 P3` fixes all P1
  and all P3 findings.
- **Individual IDs** (e.g., `P1.2`, `P2.1`): Fix only the specified findings.
  Example: `/cg-fix-triage P1.2 P2.1` fixes exactly those two.
- **Mixed** (e.g., `P1 P2.3`): Fix all P1 findings plus finding P2.3.

Tell the user which findings are in scope:
> "Fixing N findings: P1.1, P1.2, P2.3 (skipping M others)."

### Step 3: Apply Fixes

For each in-scope finding, in order (P1 first, then P2, then P3):

1. Show the finding: ID, agent name, file, line, description, and suggested fix.
2. Apply the suggested fix.
3. Verify the fix compiles/parses correctly (run any available linter or test).
4. Mark the finding as fixed.

If a fix is ambiguous or risky:
- Explain what the fix would do and ask the user to confirm before applying.
- If the user says skip, move to the next finding.

### Step 4: Summary

After processing all in-scope findings:

```markdown
## Fix-Triage Summary

**Review file**: <filename>
**In scope**: N findings
**Fixed**: X findings
**Skipped**: Y findings (user declined or ambiguous)
**Out of scope**: Z findings (not selected)

### Fixed
- [P1.1] <one-line description>
- [P2.3] <one-line description>

### Skipped
- [P1.2] <reason>

### Remaining (not selected)
- [P2.1] <one-line description>
- [P3.1] <one-line description>
```

### Step 5: Next Steps

Suggest follow-up actions:

- If fixes were applied: "Run `/cg-review light` to verify the fixes."
- If findings remain: "Run `/cg-fix-triage P2.1 P3.1` to fix remaining findings."
- If all findings are resolved: "All review findings addressed. Ready to merge."
- If solutions were found during fixes: "Run `/cg-compound` to capture learnings."
