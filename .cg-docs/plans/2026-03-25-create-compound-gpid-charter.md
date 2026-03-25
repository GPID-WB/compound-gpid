---
date: 2026-03-25
title: "Create compound-gpid.md as the shared project charter and context file"
status: active
brainstorm: ~
language: "both"
estimated-effort: "medium"
tags: [project-awareness, charter, roadmap, setup, context, anthropic-harness]
prerequisite: "2026-03-23-fix-cg-docs-gitignore (implemented)"
---

# Plan: Create `compound-gpid.md` — Shared Project Charter

## Context

Copilot currently has no awareness of what a project is trying to achieve. The
only project-level file is `compound-gpid.local.md`, which stores three fields
(language, project type, review depth) and is gitignored.

This means:
- Every Copilot session starts without knowing the project's goals or priorities.
- No prompt can check whether a requested task aligns with the project roadmap.
- Small tasks that skip the brainstorm→plan→work loop are never contextualized.
- Team members have no shared, machine-readable description of what the project
  is building.

**Solution**: Create `compound-gpid.md` — a committed, shared file in the project
root that serves as the project charter. Every prompt reads it at startup.
Combined with `roadmap.json` (a future step), this gives Copilot the "get
bearings" capability described in Anthropic's long-running agent harness pattern.

## Design Decisions

### Why a separate file from `compound-gpid.local.md`?

- `compound-gpid.local.md` is gitignored and personal. Renaming or repurposing
  it would break its semantic contract and the existing architecture.
- The charter is shared institutional knowledge. It belongs in version control.
- The naming is self-documenting: `compound-gpid.md` = project file,
  `compound-gpid.local.md` = personal overlay.

### Why Markdown and not JSON?

The charter is primarily prose — project description, objectives, constraints,
architecture notes. Markdown is the right format for human-readable, mergeable
prose. The roadmap (future step) will use JSON because it's structured status
tracking where the Anthropic finding about JSON resistance to model mangling
applies.

### What goes in the file?

The charter is a **pointer file with embedded prose** — it contains the project
description, objectives, and constraints directly, but points to `roadmap.json`
and `.cg-docs/` for detailed state. This keeps it stable (infrequent edits)
while still being the single entry point Copilot reads.

### What does NOT go in the file?

- Per-user config (stays in `compound-gpid.local.md`)
- Detailed feature tracking (goes in `roadmap.json` — future step)
- Brainstorms, plans, solutions (stay in `.cg-docs/`)
- Language/coding conventions (stay in `copilot-instructions.md`)

## Implementation Steps

### Batch 1: Core charter generation (Steps 1–4)

#### 1. Define the `compound-gpid.md` template

- **Details**: The file has two sections — a YAML frontmatter for machine-readable
  fields, and a Markdown body for prose that Copilot reads as context.

  Template:

  ```markdown
  ---
  project-name: "<name>"
  team: "DECDG / GPID — World Bank"
  created: "YYYY-MM-DD"
  last-updated: "YYYY-MM-DD"
  ---

  # <Project Name>

  ## Objective

  <1–3 sentences: What is this project? What problem does it solve? Who is it for?>

  ## Key Deliverables

  <Bulleted list of the concrete outputs this project produces. Examples:
  - R package published on internal CRAN
  - REST API serving poverty indicators
  - Harmonized survey microdata for 150 countries
  - Analytical report for the Poverty, Prosperity and Planet Report>

  ## Constraints

  <Things Copilot must always respect when working on this project. Examples:
  - All estimates must be reproducible from raw survey microdata
  - No PII may appear in committed files
  - Poverty lines must use 2017 PPP $2.15/day unless explicitly overridden
  - API responses must match PIP methodology exactly>

  ## Architecture Notes

  <Brief description of how the project is structured. Examples:
  - Package follows standard R package layout (R/, tests/, man/)
  - API built with plumber, deployed via Docker
  - Survey processing pipeline uses targets for reproducibility>

  ## Current Focus

  <What is the team working on RIGHT NOW? 1–2 sentences. This section is
  the one that gets updated most frequently. Examples:
  - Implementing urban/rural decomposition for headcount poverty rates
  - Migrating consumption aggregate code from Stata to R
  - Building test suite for API endpoint validation>

  ## Roadmap

  <Bulleted list of planned milestones. In the future, create `roadmap.json`
  for structured milestone/feature tracking.>

  ## Related Resources

  <Links to external docs, specs, or references that Copilot should know about.
  Examples:
  - PIP Methodology Handbook: [link]
  - Survey Harmonization Guidelines: [link]
  - Team coding standards: see `.github/copilot-instructions.md`>
  ```

- **Acceptance criteria**: Template is clear, has examples, and can be generated
  interactively by `/cg-setup`.

#### 2. Modify `/cg-setup` Mode A to generate `compound-gpid.md`

- **File**: `.github/prompts/cg-setup.prompt.md`
- **Section**: Mode A, after Step A3 (create `compound-gpid.local.md`), before
  Step A4 (scaffold `.cg-docs/`).
- **Details**: After the existing three questions (language, project type, review
  depth) and after creating `compound-gpid.local.md`, add a **charter generation
  phase** as a new step A3.5:

  ```markdown
  #### A3.5. Create project charter (`compound-gpid.md`)

  > The following questions create your project charter (`compound-gpid.md`).
  > You can skip all of them and create it later.

  Ask each question and wait for the answer before asking the next.

  **Question 4 — Project name**

  > What is the name of this project?

  **Question 5 — Objective**

  > In 1–3 sentences, what is this project building? Who is it for?

  **Question 6 — Key deliverables** (optional — user may skip)

  > What are the concrete outputs? (e.g., R package, REST API, analytical
  > report, harmonized dataset). List as many as apply. You can skip this
  > and add them later.

  **Question 7 — Constraints** (optional — user may skip)

  > Are there any hard constraints Copilot should always respect? (e.g.,
  > reproducibility requirements, data privacy rules, methodological
  > standards). You can skip this and add them later.

  Write `compound-gpid.md` in the project root using the template from Step 1,
  filling in the user's answers. Leave "Architecture Notes", "Current Focus",
  and "Roadmap" sections with placeholder text:

  - Architecture Notes: `<Describe the project structure here, or let Copilot fill this in after examining the codebase.>`
  - Current Focus: `<What is the team working on right now? Update this section as priorities change.>`
  - Roadmap: `<Add milestones here. In the future, create roadmap.json for structured tracking.>`
  - Related Resources: `<Add links to external docs, specs, or methodology references.>`

  Do NOT add `compound-gpid.md` to `.gitignore` — it must be committed.
  ```

- **Acceptance criteria**:
  - `/cg-setup` asks the 4 charter questions after creating `compound-gpid.local.md`.
  - The skip-all message is shown before Question 4.
  - Questions 6 and 7 are optional — skipped questions produce placeholder text.
  - `compound-gpid.md` is created in the project root.
  - The file is NOT gitignored.

#### 3. Modify `/cg-setup` Mode B to read `compound-gpid.md`

- **File**: `.github/prompts/cg-setup.prompt.md`
- **Section**: Mode B (returning project), after B1 (read local config)
- **Details**: Add a new step B1.1 immediately after B1:

  ```markdown
  #### B1.1. Read project charter

  Check if `compound-gpid.md` exists in the project root.

  - If it exists: read it and extract the project name, objective, and
    current focus for use in the context summary (Step B2).
  - If it does not exist: note that no project charter exists. After
    presenting the context summary, offer to create one by asking the
    charter questions (Questions 4–7 from Mode A Step A3.5).
  ```

  Update the Mode B summary output (Step B2) to include charter info. Change
  the existing summary format from:

  > "This project is configured for [language], [project-type], [review-depth].
  > It has X brainstorms, Y plans, and Z captured solutions."

  To:

  > "This project is **<project-name>**: <objective>.
  > Currently focused on: <current-focus>.
  > Configured for [language], [project-type], [review-depth].
  > It has X brainstorms, Y plans, and Z captured solutions."

  If `compound-gpid.md` does not exist, the summary should say:

  > "This project is configured for [language], [project-type], [review-depth].
  > **No project charter found.** It has X brainstorms, Y plans, and Z captured
  > solutions."
  >
  > "Would you like to create a project charter now? This helps Copilot
  > understand your project's goals, deliverables, and constraints."

- **Acceptance criteria**: Returning projects show the charter summary. Projects
  without a charter are offered one.

#### 4. Update `/cg-setup` file permissions

- **File**: `.github/prompts/cg-setup.prompt.md`
- **Section**: File Permissions block at the top
- **Change**: Add one line to the existing permissions list:

  ```
  - You may create or overwrite `compound-gpid.md` in the project root.
  ```

  The full permissions block should now read:

  ```markdown
  ## File Permissions

  - You may read any file in the workspace.
  - You may create or overwrite `compound-gpid.local.md` in the project root.
  - You may create or overwrite `compound-gpid.md` in the project root.
  - You may create new files and directories under `.cg-docs/`.
  - You may append lines to `.gitignore` and `.Rbuildignore`.
  - You must not modify any other existing file.
  - You must not create files outside the project root or `.cg-docs/`.
  ```

- **Acceptance criteria**: Permission is explicit. No other permission changes.

### Batch 2: Add "Step 0: Get bearings" to all prompts (Steps 5–11)

All prompts in this batch get the same pattern. The text to insert is:

```markdown
### Step 0: Get Bearings

1. Read `compound-gpid.md` in the project root for project context (objective,
   constraints, current focus).
2. Read `compound-gpid.local.md` for user config (language, project type,
   review depth).
3. If `compound-gpid.md` does not exist, warn the user:
   "No project charter found. Run `/cg-setup` to create one. Proceeding
   without project context."
```

Renumber all subsequent steps (existing Step 1 becomes Step 1, etc. — the
numbering stays the same since "Step 0" precedes Step 1).

#### 5. Add "Step 0: Get bearings" to `/cg-work`

- **File**: `.github/prompts/cg-work.prompt.md`
- **Section**: Insert before the current "Step 1: Load the Plan"
- **Change**: Add the Step 0 block above. The current Step 1 stays as Step 1
  but its sub-step 1 ("Read `compound-gpid.local.md` for project config")
  should be removed since Step 0 now handles it. Update Step 1 sub-step 1 to:

  ```
  1. Find the most recent plan in `.cg-docs/plans/` or ask the user which
     plan to implement.
  ```

  (The language/project-type info is now available from Step 0.)

- **Acceptance criteria**: `/cg-work` reads the charter before loading the plan.
  No duplicate reads of `compound-gpid.local.md`.

#### 6. Add "Step 0: Get bearings" to `/cg-plan`

- **File**: `.github/prompts/cg-plan.prompt.md`
- **Section**: Insert before the current first step.
- **Change**: Add the Step 0 block. The current Step 1 ("Gather Context")
  reads `compound-gpid.local.md` — remove that sub-step since Step 0 now
  handles it. Additionally, add this line at the end of Step 0:

  ```
  4. Verify that the planned work aligns with the project's stated objective
     and constraints. If it does not, flag this to the user before proceeding.
  ```

- **Acceptance criteria**: `/cg-plan` reads the charter and checks alignment.
  No duplicate reads of `compound-gpid.local.md`.

#### 7. Add "Step 0: Get bearings" to `/cg-brainstorm`

- **File**: `.github/prompts/cg-brainstorm.prompt.md`
- **Section**: Insert before the current first step.
- **Change**: Add the Step 0 block. The current Step 1 ("Lightweight Research")
  reads `compound-gpid.local.md` — remove that sub-step since Step 0 now
  handles it. Additionally, add an instruction at the END
  of the brainstorm prompt (after the brainstorm output is produced):

  ```markdown
  ### Charter Update Suggestion

  If the brainstorm produced ideas that would change the project's objectives,
  scope, or current focus, suggest updating `compound-gpid.md`:

  > "This brainstorm suggests a shift in project scope. Consider updating the
  > 'Current Focus' or 'Key Deliverables' sections of `compound-gpid.md`."
  ```

- **Acceptance criteria**: `/cg-brainstorm` reads the charter. Scope-changing
  brainstorms trigger an update suggestion. No duplicate reads of
  `compound-gpid.local.md`.

#### 8. Add "Step 0: Get bearings" to `/cg-review`

- **File**: `.github/prompts/cg-review.prompt.md`
- **Section**: Insert before the current "Step 1: Determine Scope"
- **Change**: Add the Step 0 block. The current Step 1 ("Determine Scope")
  reads `compound-gpid.local.md` for review depth — remove that sub-step
  since Step 0 now handles it. The constraints from the charter should be
  available to review agents, particularly `cg-data-quality` and
  `cg-architecture`, so they can flag violations of project-specific rules.
- **Acceptance criteria**: `/cg-review` reads the charter before dispatching
  agents. No duplicate reads of `compound-gpid.local.md`.

#### 9. Add "Step 0: Get bearings" to `/cg-fixbug`

- **File**: `.github/prompts/cg-fixbug.prompt.md`
- **Section**: Insert before the current first step.
- **Change**: Add the Step 0 block.
- **Acceptance criteria**: `/cg-fixbug` reads the charter.

#### 10. Add "Step 0: Get bearings" to `/cg-compound`

- **File**: `.github/prompts/cg-compound.prompt.md`
- **Section**: Insert before the current first step.
- **Change**: Add the Step 0 block. Knowing the project objective and
  constraints improves the quality of captured solutions — the agent can
  tag and describe solutions in terms of the project's domain.
- **Acceptance criteria**: `/cg-compound` reads the charter.

#### 11. Update `/cg-resume` to read `compound-gpid.md`

- **File**: `.github/prompts/cg-resume.prompt.md`
- **Section**: Step 1 ("Load Project Config")
- **Change**: The current Step 1 reads only `compound-gpid.local.md`. Extend it
  to also read `compound-gpid.md`. Replace the current Step 1 with:

  ```markdown
  ### Step 1: Load Project Context

  #### 1a. Read project charter

  Read `compound-gpid.md` in the project root. If it exists, extract:
  - `project-name`
  - Objective
  - Current Focus
  - Constraints

  If it does not exist, note: "No project charter found. Consider running
  `/cg-setup` to create one."

  #### 1b. Read user config

  Read `compound-gpid.local.md`. If it does not exist, this project has not
  been set up — reply:

  > "This project hasn't been configured yet. Run `/cg-setup` first."

  And stop.

  Extract: `language`, `project-type`, `review-depth`, and `cg-schema-version`.
  ```

  Also update **Step 4** (the summary output). The current Step 4 presents
  pending work. Extend it to include charter context at the top:

  ```markdown
  ### Step 4: Present Summary

  Present a summary in this format:

  > **<project-name>**: <objective> | Focus: <current-focus>

  Language: <language> | Type: <project-type> | Review depth: <review-depth>

  #### Pending Work
  <existing pending work output from Steps 3a–3c>

  #### Suggested Next Steps
  <existing suggestions>
  ```

  If `compound-gpid.md` does not exist, omit the charter line and show:

  > ⚠️ No project charter found. Run `/cg-setup` to create one.

- **Acceptance criteria**: `/cg-resume` reads both files. The summary includes
  project context from the charter. Missing charter produces a note, not a
  hard stop.

### Batch 3: Documentation, schema version, and soft nudge (Steps 12–16)

#### 12. Add "Project Context" section to `copilot-instructions.md`

- **File**: `.github/copilot-instructions.md`
- **Section**: Add a new section after "Language Preferences", before "Coding
  Standards"
- **Change**: Add:

  ```markdown
  ## Project Context

  - Read `compound-gpid.md` in the project root for project objectives,
    constraints, and current focus. This file is the authoritative source of
    what this project is building and why.
  - If `compound-gpid.md` does not exist, suggest the user run `/cg-setup`.
  - Do not modify `compound-gpid.md` without explicit user approval.
  ```

- **Acceptance criteria**: Copilot is nudged to read the charter even in
  free-form conversations outside slash commands.

#### 13. Update `cg-skill-setup/SKILL.md` to document the charter

- **File**: `.github/skills/cg-skill-setup/SKILL.md`
- **Change**: Update the "Key path conventions" table to include `compound-gpid.md`.
  The table should now be:

  ```markdown
  ### Key path conventions

  | Path | Purpose | Committed? |
  |------|---------|-----------|
  | `compound-gpid.md` | Project charter: objectives, deliverables, constraints, current focus | Yes |
  | `compound-gpid.local.md` | Per-user config: language, review depth | No (gitignored) |
  | `.cg-docs/` | Brainstorms, plans, captured solutions | Yes |
  | `roadmap.json` | Milestone/feature tracking (future) | Yes |
  ```

- **Acceptance criteria**: Setup skill documents both files clearly.

#### 14. Update `docs/reference.md`

- **File**: `docs/reference.md`
- **Change**: Add `compound-gpid.md` to the directory structure diagram. Update
  it to:

  ```
  your-project/
  ├── .github/
  │   ├── prompts/              → junction to compound-gpid
  │   ├── skills/               → junction to compound-gpid
  │   ├── agents/               → junction to compound-gpid
  │   ├── instructions/         → junction to compound-gpid
  │   ├── copilot-instructions.md  # copied from global clone (managed marker)
  │   └── workflows/            # your own GitHub Actions (untouched by cg-link)
  ├── compound-gpid.md          # Project charter (committed — shared context)
  ├── compound-gpid.local.md    # Your user config (gitignored)
  └── .cg-docs/                 # Compound GPID knowledge base (committed)
      ├── brainstorms/
      ├── plans/
      └── solutions/
  ```

  Also update the `/cg-setup` description to mention that it creates both files.

- **Acceptance criteria**: Reference doc shows `compound-gpid.md` in the
  directory structure.

#### 15. Update `ROADMAP.md`

- **File**: `ROADMAP.md`
- **Change**: Add a checklist item under Phase 1 (or a new "Phase 1.5: Project
  Awareness" section if it doesn't fit):

  ```markdown
  - [ ] Project charter file (`compound-gpid.md`) — shared project context
        read by all prompts at session start
  ```

- **Acceptance criteria**: Roadmap reflects this feature.

#### 16. Bump `SCHEMA_VERSION` and add migration

- **File**: `SCHEMA_VERSION` and the migration logic in `cg-update`
  (or whichever script handles schema migrations).
- **Change**: Bump `SCHEMA_VERSION` to the next integer. Add a migration
  step that checks whether `compound-gpid.md` exists in the target project.
  If it does not, print a message:

  > "New feature: project charter. Run `/cg-setup` to create
  > `compound-gpid.md` for shared project context."

  The migration should NOT create the file automatically — it's an
  interactive process that requires user answers. It only informs the user.
- **Acceptance criteria**: `SCHEMA_VERSION` is bumped. Existing projects
  that run `cg-update` are informed about the new charter feature.

## Testing Strategy

### Manual

1. **New project**: Run `cg-link` then `/cg-setup`. Verify the skip-all
   message appears before Question 4. Verify Questions 6 and 7 can be
   skipped. Verify both `compound-gpid.md` (not gitignored) and
   `compound-gpid.local.md` (gitignored) are created.

2. **Returning project without charter**: Run `/cg-setup` on a project that has
   `compound-gpid.local.md` but no `compound-gpid.md`. Verify it offers to
   create one.

3. **`/cg-work` with charter**: Create a plan, then run `/cg-work`. Verify the
   output shows it read the project charter (mentions the project name or
   objective).

4. **`/cg-work` without charter**: Delete `compound-gpid.md`, run `/cg-work`.
   Verify the warning appears: "No project charter found."

5. **`/cg-plan` alignment check**: Create a charter with a specific objective
   (e.g., "build a poverty API"), then run `/cg-plan` for something unrelated
   (e.g., "build a Shiny dashboard for climate data"). Verify `/cg-plan` flags
   the misalignment.

6. **`/cg-resume` with charter**: Run `/cg-resume` in a project with both files.
   Verify the charter appears as a **single-line header** (not a multi-paragraph
   block) above the pending work scan.

7. **`/cg-resume` without charter**: Run `/cg-resume` in a project with only
   `compound-gpid.local.md`. Verify it notes "No project charter found" but
   still shows pending work.

8. **`/cg-compound` with charter**: Capture a solution with `/cg-compound`.
   Verify it reads the charter (the captured solution should reference project
   context where relevant).

9. **Skip all charter questions**: Run `/cg-setup` on a new project and skip
   the charter block entirely. Verify `compound-gpid.md` is NOT created and
   the setup completes with only `compound-gpid.local.md`.

## Risks & Mitigations

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| Charter questions make `/cg-setup` too long | Medium | Charter questions have a skip-all option; Questions 6–7 individually optional too |
| Team ignores the charter / lets it go stale | Medium | "Current Focus" section is designed to be updated frequently; `/cg-brainstorm` prompts updates |
| Copilot modifies `compound-gpid.md` without permission | Low | `copilot-instructions.md` rule: "Do not modify without explicit user approval" |
| Merge conflicts on `compound-gpid.md` | Low | File is mostly stable prose, edited infrequently; "Current Focus" is the only volatile section |

## Out of Scope

- `roadmap.json` creation (that's Step 3 of the larger roadmap).
- File declaration rule in `copilot-instructions.md` (that's Step 5).
- Modifications to agent `.agent.md` files — agents inherit charter context
  via the prompts that dispatch them.
- CI regression check for "Step 0" presence in prompts — deferred until a
  broader prompt validation suite exists.

## Sequencing

- **Batch 1 (Steps 1–4)**: Do first. Test `/cg-setup` end-to-end before
  proceeding.
- **Batch 2 (Steps 5–11)**: All independent of each other. Can be done in
  any order or in parallel. Each prompt gets the same "Step 0" pattern.
- **Batch 3 (Steps 12–16)**: Do last, after Batch 2 is verified working.
  Step 12 (`copilot-instructions.md`) affects all interactions globally.
  Step 16 (schema version) should be the final step.
