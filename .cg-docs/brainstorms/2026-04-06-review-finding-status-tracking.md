---
date: 2026-04-06
title: "Per-finding status tracking in review files"
status: decided
chosen-approach: "Finding-level only — file status computed from findings map"
tags: [review, fix-triage, resume, frontmatter, migration]
---

# Per-Finding Status Tracking in Review Files

## Context

Every time `/cg-resume` runs, it reports "pending Review findings" for all
review files in `.cg-docs/reviews/`, even when those findings have already
been addressed by `/cg-fix-triage`. This happens because review files have
no status tracking — `/cg-resume` simply regex-counts `**[P1.`, `**[P2.`,
`**[P3.` lines and assumes they're all unresolved.

The alternative of cross-referencing each finding against plan files or code
changes was rejected as too token-expensive.

## Requirements

1. **Per-finding granularity**: Each finding (P1.1, P2.1, etc.) must have its
   own status so partially-triaged review files are tracked correctly.
2. **Cheap reads for `/cg-resume`**: Reading frontmatter YAML is much cheaper
   than scanning the full markdown body or cross-referencing plan files.
3. **`/cg-resume` stays read-only**: It must not write to any file. Migration
   of legacy files is delegated to `/cg-fix-triage`.
4. **Backward compatibility**: Legacy review files (no frontmatter) in
   existing projects must be migrated gracefully, not silently ignored.
5. **Companion-plan heuristic for migration**: When migrating a legacy review
   file, check if a companion plan exists (matching filename stem). If the
   plan has `status: completed`, default all findings to `fixed`. Otherwise,
   default to `open`.

## Approaches Considered

### Approach 1: Explicit file-level + finding-level status

Store both a top-level `status:` (open/partial/resolved) and a per-finding
map in frontmatter. `/cg-resume` reads only the file-level status for
short-circuiting.

- **Pros**: Cheapest possible read for `/cg-resume`.
- **Cons**: Two sources of truth — desync risk if `/cg-fix-triage` updates a
  finding but forgets to recompute the file-level status. Extra instruction
  complexity.
- **Effort**: Medium.

### Approach 2: Finding-level only — file status computed (CHOSEN)

Store only per-finding statuses in frontmatter. No file-level status field.
`/cg-resume` computes file status: all fixed/skipped = resolved (skip); any
open = count them.

```yaml
---
plan: .cg-docs/plans/2026-04-01-example.md
findings:
  P1.1: fixed
  P2.1: open
  P2.2: skipped
---
```

- **Pros**: No desync possible. Single source of truth. One write per finding.
  Simple mental model.
- **Cons**: `/cg-resume` must parse the full findings map — but it's a few
  lines of YAML, not the whole body, so still very cheap.
- **Effort**: Small–Medium.

### Approach 3: Finding-level + inline strikethrough markers

Same frontmatter as Approach 2, but also modify the markdown body with
strikethrough or ✅ prefixes on fixed findings.

- **Pros**: Humans scanning the file see status at a glance.
- **Cons**: Two representations to keep in sync. Body edits are fragile.
- **Effort**: Medium.

## Decision

Approach 2 — finding-level only. Single source of truth in frontmatter;
file status is computed by any consumer that needs it.

### Finding statuses

| Status    | Meaning                                      |
|-----------|----------------------------------------------|
| `open`    | Finding has not been addressed                |
| `fixed`   | Fix was applied and verified                  |
| `skipped` | User explicitly declined to fix               |

### Changes required across three prompts

**`/cg-review` (Step 3.5)** — When creating the review file, add YAML
frontmatter with:
- `plan:` — path to the companion plan file (if identifiable)
- `findings:` — map of every finding ID to `open`

**`/cg-fix-triage` (Step 3–4)** — After fixing or skipping each finding,
update its entry in the frontmatter from `open` to `fixed` or `skipped`.

**`/cg-fix-triage` (new `--migrate` mode)** — When invoked with `--migrate`:
1. Scan `.cg-docs/reviews/` for files without a `findings:` frontmatter key.
2. Parse finding IDs from the markdown body (regex: `\*\*\[P[123]\.\d+\]`).
3. Apply companion-plan heuristic: strip `-review` suffix from filename,
   look for the matching plan in `.cg-docs/plans/`. If plan exists and has
   `status: completed`, default all findings to `fixed`. Otherwise, `open`.
4. Add frontmatter to the file.

**`/cg-resume` (Step 2e)** — Replace the current regex-counting approach:
1. Read each review file's frontmatter.
2. If `findings:` key exists, count entries with value `open`.
3. If `findings:` key is missing (legacy file), detect it and add to a
   migration nudge: "N review files use old format. Run
   `/cg-fix-triage --migrate` to add status tracking."
4. Only report files with ≥1 open finding in the "Pending Review Findings"
   section.

## Next Steps

1. Create an implementation plan with `/cg-plan` covering changes to
   `cg-review.prompt.md`, `cg-fix-triage.prompt.md`, and
   `cg-resume.prompt.md`.
2. Update existing Pester tests in `tests/prompt-tools.Tests.ps1` to verify
   the new frontmatter contract.
3. Migrate the 4 existing review files in this project as a dogfood test.
