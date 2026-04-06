---
date: 2026-04-06
title: "Per-finding status tracking in review files"
status: completed
completed-date: 2026-04-06
brainstorm: ".cg-docs/brainstorms/2026-04-06-review-finding-status-tracking.md"
language: "both"
estimated-effort: "medium"
tags: [review, fix-triage, resume, frontmatter, migration, prompts, tests]
---

# Plan: Per-Finding Status Tracking in Review Files

## Objective

Add YAML frontmatter with per-finding status (`open`/`fixed`/`skipped`) to
review files so that `/cg-resume` can distinguish resolved findings from
pending ones. Update three prompts (`cg-review`, `cg-fix-triage`,
`cg-resume`) and add a migration path for legacy review files that lack
frontmatter.

## Context

Today, `/cg-resume` Step 2e counts regex matches for `**[P1.`, `**[P2.`,
`**[P3.` in the markdown body of review files. Every finding is assumed
unresolved — there is no mechanism to mark findings as fixed or skipped.
`/cg-fix-triage` already has a File Permissions note saying "except to update
the review report status" but no status structure is defined.

The brainstorm decided on **Approach 2**: a `findings:` YAML map in
frontmatter with per-finding statuses. No file-level status field — the
consumer computes it (all fixed/skipped = resolved). Legacy files are
migrated by `/cg-fix-triage --migrate`, not by `/cg-resume` (which stays
read-only). Migration uses a companion-plan heuristic to set smart defaults.

### Finding status values

| Status    | Meaning                        |
|-----------|--------------------------------|
| `open`    | Not yet addressed              |
| `fixed`   | Fix applied and verified       |
| `skipped` | User explicitly declined       |

### Frontmatter schema (new review files)

```yaml
---
plan: .cg-docs/plans/2026-04-01-example.md   # or null
findings:
  P1.1: open
  P2.1: open
  P2.2: open
---
```

## Implementation Steps

### 1. Update `cg-review.prompt.md` — Step 3.5 (write frontmatter)

- **Files**: `.github/prompts/cg-review.prompt.md`
- **Details**:
  - In Step 3.5, after "Write the full prioritized report", add
    instructions to prepend YAML frontmatter before the markdown body.
  - The frontmatter must include:
    - `plan:` — path to the companion plan (from Step 3.5's existing
      plan-detection logic), or `null` if none.
    - `findings:` — a YAML map with every finding ID (P1.1, P2.1, etc.)
      parsed from the Step 3 report, each set to `open`.
  - Update the example/template block in the prompt to show frontmatter.
- **Tests**: Add to `tests/prompt-tools.Tests.ps1`:
  - `cg-review.prompt.md` Step 3.5 references `findings:` frontmatter key.
  - `cg-review.prompt.md` Step 3.5 mentions per-finding statuses
    (`open`, `fixed`, `skipped`).
- **Acceptance criteria**: The prompt clearly instructs the agent to add
  frontmatter with a `findings:` map where every ID defaults to `open`.

### 2. Update `cg-fix-triage.prompt.md` — per-finding status updates

- **Files**: `.github/prompts/cg-fix-triage.prompt.md`
- **Details**:
  - **Step 1** (Load Review Report): After parsing findings, also read the
    `findings:` frontmatter. If it exists, skip findings already marked
    `fixed` or `skipped` — only present `open` findings to the user.
    Display the count of already-resolved findings so the user knows.
  - **Step 3** (Apply Fixes): After each finding is fixed or skipped,
    update the corresponding entry in the YAML frontmatter from `open` to
    `fixed` or `skipped`. This is an in-place edit of the review file's
    frontmatter only — the markdown body stays untouched.
  - **Step 4** (Summary): Reflect the new statuses: show "Previously
    resolved" count alongside Fixed/Skipped/Out-of-scope.
  - **New: `--migrate` mode**: Add a new section (Step 1.5 or a top-level
    clause) that handles `/cg-fix-triage --migrate`:
    1. Scan `.cg-docs/reviews/` for `.md` files without a `findings:`
       frontmatter key (or without any frontmatter at all).
    2. For each legacy file, parse finding IDs from the body using regex
       `\*\*\[P[123]\.\d+\]\*\*`.
    3. Apply the companion-plan heuristic: strip `-review` suffix from the
       review filename stem, look for a matching file in `.cg-docs/plans/`.
       If the plan exists and its frontmatter has `status: completed`,
       default all findings to `fixed`. Otherwise, default to `open`.
    4. Add YAML frontmatter to the file with the `plan:` path (or null)
       and the `findings:` map.
    5. Report what was migrated: "Migrated N review files. M defaulted to
       `fixed` (companion plan completed), K defaulted to `open`."
- **Tests**: Add to `tests/prompt-tools.Tests.ps1`:
  - `cg-fix-triage.prompt.md` references `findings:` frontmatter key.
  - `cg-fix-triage.prompt.md` describes per-finding status update (fixed/
    skipped) in the frontmatter.
  - `cg-fix-triage.prompt.md` describes `--migrate` mode.
- **Acceptance criteria**: The prompt instructs the agent to (a) read
  finding statuses before presenting, (b) update statuses after each fix,
  and (c) handle `--migrate` for legacy files.

### 3. Update `cg-resume.prompt.md` — Step 2e (status-aware scan)

- **Files**: `.github/prompts/cg-resume.prompt.md`
- **Details**:
  - Replace the current Step 2e entirely. New logic:
    1. For each `.md` file in `.cg-docs/reviews/` (skip `.gitkeep`):
       - Read the YAML frontmatter.
       - If `findings:` key exists: count entries with value `open`. If
         zero open findings, treat the file as resolved (skip it).
       - If `findings:` key is missing (legacy file): add to a migration
         list.
    2. Collect files with ≥1 `open` finding for the "Pending Review
       Findings" section — report the count of open findings per priority
       (parse priority from the ID prefix: P1.x, P2.x, P3.x).
    3. If any legacy files were detected, collect a maintenance nudge:
       > "N review files use old format (no `findings:` frontmatter). Run
       > `/cg-fix-triage --migrate` to add status tracking."
  - Update the **Step 3 presentation template**: the "Pending Review
    Findings" section should show open counts, not total counts. If a file
    is fully resolved, it must not appear.
  - Add the migration nudge to the **Maintenance Nudges** section (same
    pattern as charter staleness).
- **Tests**: Add/update in `tests/prompt-tools.Tests.ps1`:
  - `cg-resume.prompt.md` Step 2e references `findings:` frontmatter.
  - `cg-resume.prompt.md` mentions `--migrate` nudge for legacy files.
- **Acceptance criteria**: `/cg-resume` no longer reports resolved
  findings. Legacy files trigger a migration nudge instead of being
  counted as all-open.

### 4. Update Pester tests

- **Files**: `tests/prompt-tools.Tests.ps1`
- **Details**: All test additions from Steps 1–3 above, consolidated:
  - **New Describe block**: `"cg-review.prompt.md - review findings
    frontmatter"` — tests that the prompt references `findings:` in Step
    3.5 and mentions `open`/`fixed`/`skipped` statuses.
  - **New Describe block**: `"cg-fix-triage.prompt.md - per-finding status
    tracking"` — tests for frontmatter update instructions and `--migrate`
    mode.
  - **Update existing block**: `"cg-resume.prompt.md - pending review
    findings scan"` — add test that Step 2e references `findings:`
    frontmatter and `--migrate` nudge.
- **Tests**: Run `Invoke-Pester tests/prompt-tools.Tests.ps1` to verify.
- **Acceptance criteria**: All new tests pass. Existing tests still pass.

## Testing Strategy

- **Structural tests only**: This plan modifies prompt files (natural
  language instructions), not executable code. Tests verify that prompts
  contain the required keywords, sections, and contract terms. They do not
  test runtime behavior (which depends on the LLM following the prompt).
- **Pattern**: Same as existing tests — read the prompt file content and
  regex-match for required strings.
- **Edge cases to verify via test**:
  - `cg-review.prompt.md` references `findings:` key and status values.
  - `cg-fix-triage.prompt.md` references `--migrate` and companion-plan
    heuristic.
  - `cg-resume.prompt.md` references `findings:` for status-aware scan
    and legacy migration nudge.

## Documentation Checklist

- [ ] Inline comments in prompt files explaining the frontmatter schema
- [ ] Update `docs/reference.md` if it documents `/cg-fix-triage` arguments
      (add `--migrate`)

## Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| LLM ignores frontmatter instructions and writes review files without it | Tests guard the contract; if the review file lacks `findings:`, `/cg-resume` triggers migration nudge |
| YAML frontmatter parsing varies across LLM calls | Schema is minimal (flat key-value map); the brainstorm explicitly avoided nested objects |
| `--migrate` regex fails on unusual finding formats | Regex `\*\*\[P[123]\.\d+\]\*\*` matches the template exactly; non-standard formats get caught as "0 findings parsed" and the user is warned |
| Companion-plan heuristic misidentifies plans | Only matches by filename stem (strip `-review`); false positives default to `open` which is the safe direction |

## Out of Scope

- File-level `status:` field (rejected in brainstorm — single source of
  truth is the findings map).
- Inline strikethrough markers in the markdown body (rejected — fragile).
- Modifying `/cg-resume` to write files (stays read-only by design).
- Migrating this project's 4 existing review files (will be done manually
  or via `/cg-fix-triage --migrate` after implementation).
