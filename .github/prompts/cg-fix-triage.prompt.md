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
3. Read `compound-gpid.context.md` for project-specific context and
   workspace notes. If it does not exist, skip silently.
4. If `compound-gpid.md` does not exist, warn the user:
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
4. Read the review file and parse all findings from the markdown body. Each
   finding has a compound ID like `P1.1`, `P1.2`, `P2.1`, `P3.1`, etc.
5. Read the YAML frontmatter. If a `findings:` key exists, use it to determine
   which findings are already resolved:
   - `open` — actionable; present to the user for fixing.
   - `fixed` or `skipped` — already resolved; exclude from the active findings
     list but count them.
   If no `findings:` key exists, treat all parsed findings as `open` (legacy
   file — run `/cg-fix-triage --migrate` to add tracking frontmatter).
6. Display a summary: total findings, how many are already resolved (fixed +
   skipped), how many are `open` and actionable. List each `open` finding ID
   with its one-line description.

### Step 2: Determine Scope

Parse the user's arguments to decide which findings to fix:

- **No arguments**: Fix all findings in the review report.
- **Priority levels** (e.g., `P0`, `P1`, `P2`, `P3`): Fix all findings at the
  specified priority levels. Example: `/cg-fix-triage P1 P3` fixes all P1
  and all P3 findings.
- **Individual IDs** (e.g., `P1.2`, `P2.1`): Fix only the specified findings.
  Example: `/cg-fix-triage P1.2 P2.1` fixes exactly those two.
- **Mixed** (e.g., `P1 P2.3`): Fix all P1 findings plus finding P2.3.
- **`--migrate`**: Run migration mode instead of the normal fix flow (see
  Special Mode: `--migrate` at the bottom). Adds `findings:` tracking
  frontmatter to legacy review files. Does NOT apply any fixes.

If any argument is not in the recognized list above, warn:
> "Unrecognized argument '`<arg>`' — ignoring. Recognized arguments: `P0`, `P1`, `P2`, `P3`, individual IDs (e.g., `P1.2`), or `--migrate`."

**Large report notice**: If there are more than 15 open findings in scope and no arguments were provided, warn the user before proceeding:
> "This report has N open findings. Fixing all at once may hit response length limits.
> Recommended: use priority batches — run `/cg-fix-triage P0 P1` first, then
> `/cg-fix-triage P2`, then `/cg-fix-triage P3`. Proceed with all N anyway? [yes/batch]"
> Wait for the user's response before continuing.
> If the user responds `batch`: display the three recommended commands
> (``/cg-fix-triage P0 P1``, ``/cg-fix-triage P2``, ``/cg-fix-triage P3``) and stop —
> do not proceed with triage.

Tell the user which findings are in scope:
> "Fixing N findings: P1.1, P1.2, P2.3 (M out of scope)."​

### Step 3: Apply Fixes

For each in-scope finding, in order (P0 first, then P1, then P2, then P3):

1. Show the finding: ID, agent name, file, line, description, and suggested fix.
2. Apply the suggested fix.
3. Verify the fix compiles/parses correctly (run any available linter or test).
4. Mark the finding as fixed: update its entry in the review file's YAML
   frontmatter from `open` to `fixed` (or `skipped` if the user declined).
   Edit only the frontmatter — do not modify the markdown body.
   **Do NOT delegate this frontmatter update to a subagent. Edit the file directly.**

If a fix is ambiguous or risky:
- Explain what the fix would do and ask the user to confirm before applying.
- If the user says skip, move to the next finding.

If a fix fails validation (compile/parse error):
- Display the error message.
- Ask the user whether to (a) skip this finding and continue, or (b) stop for manual review.
- Track failed fixes in the summary under 'Failed'.

### Step 4: Summary

After processing all in-scope findings:

```markdown
## Fix-Triage Summary

**Review file**: <filename>
**Previously resolved**: R findings (from prior sessions)
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

---

## Special Mode: `--migrate`

When invoked as `/cg-fix-triage --migrate`, run the following migration
instead of the normal fix flow:

1. Scan `.cg-docs/reviews/` for all `.md` files (skip `.gitkeep`) that do
   **not** have a `findings:` key in their YAML frontmatter (or have no
   frontmatter at all). These are legacy review files.
2. For each legacy file:
   a. Parse finding IDs from the markdown body using the pattern
      `**[P0.`, `**[P1.`, `**[P2.`, `**[P3.` (e.g., `P0.1`, `P1.1`, `P2.3`).
   b. Apply the companion-plan heuristic to determine default status:
      - Strip the `-review` suffix from the review filename stem
        (e.g., `2026-04-01-cg-strategy-review.md` → stem
        `2026-04-01-cg-strategy`).
      - Look for a matching file in `.cg-docs/plans/` (exact stem match).
      - If the plan exists **and** its frontmatter has `status: completed`:
        set all findings to `fixed`.
      - Otherwise (plan not found, or plan not completed): set all findings
        to `open`.
   c. Add tracking frontmatter to the file using this split logic:
      - **If no frontmatter exists**: prepend a full block:
        ```yaml
        ---
        plan: <path to companion plan, or null>
        findings:
          P1.1: fixed   # or open
          P2.1: fixed
        ---
        ```
      - **If frontmatter exists but lacks a `findings:` key**: insert only the
        `findings:` map into the existing block (do not create a second `---`
        block — malformed YAML).
      **Write the updated file directly. Do NOT delegate this step to a subagent.**
3. Report what was migrated:
   > "Migrated N review file(s). M defaulted to `fixed` (companion plan
   > completed), K defaulted to `open`. Run `/cg-resume` to see updated
   > pending findings."
4. If no legacy files are found:
   > "No legacy review files found. All review files already have
   > per-finding status tracking."
