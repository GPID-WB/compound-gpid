---
date: 2026-04-01
title: "Charter maintenance — archive on removal, staleness check, structural rule"
status: completed
completed-date: 2026-04-01
brainstorm: "N/A (architecture session 2026-04-01)"
language: "both"
estimated-effort: "small"
tags: [charter, compound-gpid.md, maintenance, resume, setup]
---

# Plan: Charter Maintenance (Approach C revised)

## Objective

Prevent `compound-gpid.md` from drifting stale or growing into an
unfocused dumping ground, without imposing artificial size limits. Three
mechanisms: archive removed content rather than delete it; prompt the user
when the charter hasn't been reviewed in 30 days; enforce a structural rule
(exactly four sections) rather than a line count.

## Context

- `compound-gpid.md` is the shared project charter, committed and read at
  session start by all prompts via "Step 0: Get Bearings."
- As more team members use the plugin, charters will drift — content becomes
  outdated, sections grow unfocused, and the "Current Focus" section stops
  being updated.
- **No size cap** — dropped in favour of a structural rule. The charter
  should have exactly four sections. If content doesn't fit those four
  categories, it belongs elsewhere (skill files, `.cg-docs/`, or
  `copilot-instructions.md`), not in the charter.
- **Approach C** was agreed in the architecture session on 2026-04-01.

## Design Decisions

### The four sections rule
`compound-gpid.md` has exactly these sections:
1. **Objective** — 1–3 sentences. What is this project? Who is it for?
2. **Key Deliverables** — concrete outputs the project produces.
3. **Constraints** — hard rules Copilot must always respect.
4. **Current Focus** — what the team is working on RIGHT NOW. Updated
   frequently. 1–2 sentences maximum.

Everything else goes elsewhere:
- Architecture notes → skill files or `copilot-instructions.md`
- Historical decisions → `.cg-docs/brainstorms/`
- Removed charter content → `.cg-docs/archive/charter-history.md`
- Roadmap / milestones → `roadmap.json`
- Related resources → `copilot-instructions.md` or a skill file

### Archive on removal
When content is removed from `compound-gpid.md`, it is appended to
`.cg-docs/archive/charter-history.md` with a date stamp. The charter
stays current; history is preserved but never loaded at session start.

### Staleness check
`compound-gpid.md` YAML frontmatter gains a `last-reviewed` field.
`/cg-resume` checks it and surfaces a nudge if it hasn't been updated
in 30+ days.

---

## Implementation Tasks

### Task 1: Update `compound-gpid.md` template in `/cg-setup`

- **File**: `.github/prompts/cg-setup.prompt.md`
- **What to change**:

  The charter template currently has six sections (Objective, Key
  Deliverables, Constraints, Architecture Notes, Current Focus, Roadmap,
  Related Resources). Reduce it to exactly four sections and update
  frontmatter to include `last-reviewed`.

  Updated YAML frontmatter block:
  ```yaml
  ---
  project-name: "<name>"
  team: "DECDG / GPID — World Bank"
  created: "YYYY-MM-DD"
  last-reviewed: "YYYY-MM-DD"
  ---
  ```

  Updated template body (four sections only):
  ```markdown
  # <Project Name>

  ## Objective

  <1–3 sentences: What is this project? What problem does it solve?
  Who is it for?>

  ## Key Deliverables

  <Bulleted list of the concrete outputs this project produces. Examples:
  - R package published on internal CRAN
  - REST API serving poverty indicators
  - Harmonized survey microdata for 150 countries>

  ## Constraints

  <Hard rules Copilot must always respect when working on this project.
  Examples:
  - All estimates must be reproducible from raw survey microdata
  - No PII may appear in committed files
  - Poverty lines must use 2017 PPP $2.15/day unless explicitly overridden>

  ## Current Focus

  <What is the team working on RIGHT NOW? 1–2 sentences. Update this
  whenever priorities shift.>
  ```

  Add a comment in the setup prompt explaining the structural rule:
  ```markdown
  > These are the only four sections. If content doesn't fit one of them,
  > it belongs elsewhere — architecture notes go in `copilot-instructions.md`
  > or a skill file; historical decisions go in `.cg-docs/brainstorms/`;
  > removed content goes in `.cg-docs/archive/charter-history.md`.
  ```

  Also update `/cg-setup` Mode A Step A3.5 to set `last-reviewed` to
  today's date when generating the charter.

- **Acceptance criteria**:
  - New charters have exactly four sections.
  - `last-reviewed` is set to creation date.
  - Architecture Notes, Roadmap, and Related Resources sections are gone
    from the template.

---

### Task 2: Scaffold `.cg-docs/archive/` in `/cg-setup`

- **File**: `.github/prompts/cg-setup.prompt.md`
- **What to change**:

  In Step A4 (scaffold `.cg-docs/` structure), add `.cg-docs/archive/`
  with a `.gitkeep`:

  ```
  .cg-docs/
  ├── archive/
  │   └── .gitkeep        ← ADD THIS
  ├── brainstorms/
  │   └── .gitkeep
  ├── plans/
  │   └── .gitkeep
  └── solutions/
      └── ...
  ```

- **Acceptance criteria**:
  - New projects get `.cg-docs/archive/` on setup.
  - `.gitkeep` ensures the folder is committed.

---

### Task 3: Add archive-on-removal rule to `copilot-instructions.md`

> **Dependency**: This task must be applied **after** the Step 2 plan is
> implemented. The Step 2 plan significantly reshapes `copilot-instructions.md`
> (adds a workflow entry-point table and restructures the Project Context
> section). Applying Task 3 independently risks merge conflicts and an
> incoherent final structure.

- **File**: `.github/copilot-instructions.md`
- **What to change**:

  In the existing `## Project Context` section, qualify the existing
  "do not modify" rule to distinguish body content from metadata, then
  add the Charter Rules block:

  Replace:
  > Do not modify `compound-gpid.md` without explicit user approval.

  With:
  > Do not modify the **body** of `compound-gpid.md` (Objective, Key
  > Deliverables, Constraints, Current Focus sections) without explicit
  > user approval. The `last-reviewed` frontmatter field is metadata —
  > update it automatically whenever the user explicitly approves a
  > charter change.

  Then add, immediately after that rule:

  ```markdown
  ## Charter Rules

  `compound-gpid.md` has exactly four sections: Objective, Key
  Deliverables, Constraints, Current Focus. Do not add sections.

  When removing **body content** from `compound-gpid.md`:
  1. Append the removed content to `.cg-docs/archive/charter-history.md`
     with a date stamp:
     ```markdown
     ## Archived YYYY-MM-DD
     **Removed from**: <section name>
     <content>
     ```
  2. Update `last-reviewed` in the frontmatter to today's date.
  3. Never delete body content without archiving it first.

  When updating `compound-gpid.md` for any reason, update `last-reviewed`
  to today's date.
  ```

- **Acceptance criteria**:
  - The "do not modify" rule is split: body requires explicit approval;
    `last-reviewed` may be updated automatically on approved changes.
  - Copilot knows the four-section rule in all free-form conversations.
  - Archive instruction is present, specific, and scoped to body content.
  - `last-reviewed` update is explicitly required on any charter change.

---

### Task 4: Add staleness check to `/cg-resume`

- **File**: `.github/prompts/cg-resume.prompt.md`
- **What to change**:

  After the existing Step 2e (Pending review findings), add a new
  sub-step 2f. Do **not** renumber or modify 2e.

  ```markdown
  #### 2f. Charter staleness check

  If `compound-gpid.md` exists, read its `last-reviewed` frontmatter
  field. Compute days since that date.

  If `last-reviewed` is missing or more than 30 days ago:
  > ⚠️ **Charter review due**: `compound-gpid.md` hasn't been reviewed
  > since <last-reviewed date or "unknown">. Consider updating the
  > "Current Focus" section to reflect what the team is working on now.
  ```

  If `last-reviewed` is within 30 days, skip silently.

- **Acceptance criteria**:
  - `/cg-resume` surfaces the nudge when charter is stale.
  - Nudge is skipped when charter is current.
  - Missing `last-reviewed` field is treated as stale.
  - Existing step 2e (Pending review findings) is unchanged.

---

### Task 5: Update documentation

- **Files**:
  - `docs/workflow.md` (MODIFY)
  - `docs/reference.md` (MODIFY)

- **What to change**:

  **`docs/workflow.md`**: Update the "Project Charter" callout box near
  the top to reflect the four-section structure and archive convention:

  ```markdown
  > **Project Charter** (`compound-gpid.md`): Before any workflow step,
  > Copilot reads your project's charter to understand objective,
  > deliverables, constraints, and current focus. Create or update it via
  > `/cg-setup`. The charter has exactly four sections — content that
  > doesn't fit those sections belongs elsewhere. When content is removed,
  > it is archived to `.cg-docs/archive/charter-history.md` automatically.
  > `/cg-resume` will nudge you if the charter hasn't been reviewed in
  > 30+ days.
  ```

  **`docs/reference.md`**: Update the `compound-gpid.md` entry in the
  directory structure table:

  ```markdown
  | `compound-gpid.md` | Project charter (4 sections: Objective, Key
  Deliverables, Constraints, Current Focus). Committed — shared. |
  ```

  Add `.cg-docs/archive/` to the directory structure diagram:
  ```
  .cg-docs/
  ├── archive/              # Archived charter content (never loaded at
  │                         # session start)
  ├── brainstorms/
  ├── plans/
  └── solutions/
  ```

- **Acceptance criteria**:
  - `docs/workflow.md` reflects four-section rule and archive convention.
  - `docs/reference.md` directory diagram includes `archive/`.
  - No references to the old six-section charter template remain.

---

## Testing Strategy

1. **New project setup**: Run `/cg-setup`. Verify `compound-gpid.md` has
   exactly four sections and `last-reviewed` is today's date. Verify
   `.cg-docs/archive/` exists.

2. **Staleness nudge**: Set `last-reviewed` to 31 days ago. Run
   `/cg-resume`. Verify nudge appears.

3. **Current charter**: Set `last-reviewed` to today. Run `/cg-resume`.
   Verify nudge does NOT appear.

4. **Archive instruction**: In a Copilot free-form conversation, ask it
   to remove a section from `compound-gpid.md`. Verify it archives the
   content to `charter-history.md` and updates `last-reviewed`.

5. **Missing last-reviewed**: Remove `last-reviewed` from frontmatter.
   Run `/cg-resume`. Verify it's treated as stale.

---

## Risks & Mitigations

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| Existing projects have old six-section charter | High | Archive instruction in `copilot-instructions.md` guides cleanup; no forced migration |
| `last-reviewed` not updated after charter edits | Medium | `copilot-instructions.md` rule makes it explicit; `/cg-resume` nudge catches drift |
| Archive file grows large over time | Low | It's never loaded at session start; size doesn't affect performance |

---

## Out of Scope

- Automated migration of existing charters to four-section format.
- Hard enforcement (rejected writes) for out-of-format charters.
- Charter diff or history viewer.
- `/cg-strategy` integration with charter updates (handled in Step 2 plan).

---

## Commit Messages

| Task | Suggested commit |
|------|-----------------|
| 1 | `feat(setup): reduce charter to four sections, add last-reviewed` |
| 2 | `feat(setup): scaffold .cg-docs/archive/ on new project` |
| 3 | `feat(instructions): add charter structural rule and archive convention` |
| 4 | `feat(resume): add 30-day charter staleness nudge` |
| 5 | `docs: update workflow and reference for charter maintenance` |
