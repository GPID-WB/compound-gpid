---
name: cg-skill-fix-triage-migrate
description: Migration mode for /cg-fix-triage. Adds findings: tracking frontmatter to legacy review files. Does NOT apply fixes. Load only when invoked as /cg-fix-triage --migrate.
---

# Fix-Triage Migration Mode (`--migrate`)

When invoked as `/cg-fix-triage --migrate`, add `findings:` tracking frontmatter to legacy review files. Does NOT apply fixes.

## Steps

1. Scan `.cg-docs/reviews/` for `.md` files without a `findings:` key (skip `.gitkeep`).
2. For each legacy file:
   a. Parse finding IDs (`**[P0.`, `**[P1.`, etc.).
   b. Apply the companion-plan heuristic: strip `-review` suffix → find matching plan in `.cg-docs/plans/`. **This relies on review files being named `<plan-stem>-review.md` per `cg-review.prompt.md` Step 3.5.** Set all findings to `open`. If no matching plan found, log: `No companion plan found for <filename> — defaulting all findings to open.` <!-- heuristic: completed status cannot distinguish fixed from skipped — default to open; mark resolved ones fixed manually -->
   c. Add frontmatter. If none exists: prepend full block using this template:
      ```yaml
      ---
      plan: <path to companion plan, or null if not found>
      findings:
        <id>: open   # one entry per parsed ID — replace <id> with actual IDs (e.g., P1.1, P2.3)
      ---
      ```
      If frontmatter exists but lacks `findings:`: insert the `findings:` map as the last key before the closing `---` delimiter (do not create a second `---` block).
      **Write directly — do NOT delegate to a subagent.**
3. Report: > "Migrated N review file(s). All findings defaulted to `open` — mark resolved ones fixed manually with `/cg-fix-triage <IDs>`. Run `/cg-resume` to see updated pending findings."
4. If none found: > "No legacy review files found. All review files already have per-finding status tracking."
