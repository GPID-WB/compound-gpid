---
date: 2026-04-01
title: "Add /cg-strategy command and fix @cg-roadmap model to Haiku"
status: active
brainstorm: "N/A (architecture session 2026-04-01)"
language: "both"
estimated-effort: "medium"
tags: [strategy, roadmap, vision, cg-strategy, cg-roadmap, project-awareness]
---

# Plan: Add `/cg-strategy` and Fix `@cg-roadmap` Model

## Objective

Add a `/cg-strategy` command that supports high-level project visioning and
mid-project direction-setting. It is the entry point for structured thinking
about the whole project — at any stage. It reads full project context,
conducts a focused conversation, proposes concrete roadmap changes, and
dispatches `@cg-roadmap` to execute them. Also fix `@cg-roadmap` model from
Sonnet to Haiku (verified deviation from design).

## Context

- **Steps 1–3** of project awareness are complete (gitignore fix, charter,
  roadmap.json + @cg-roadmap).
- **Step 1 (charter maintenance)** is handled in the plan
  `2026-04-01-charter-maintenance.md`. Implement Step 1 **before** this
  plan — both plans touch `copilot-instructions.md`, and the charter
  maintenance plan's Task 3 must be applied first to avoid conflicts.
- **The problem this solves**: the existing workflow assumes you arrive with
  a specific task in mind. There is no entry point for "I have a full project
  vision and want to think through it" or "something has shifted and I need
  to rethink direction." `/cg-strategy` fills this gap for both day-zero
  and mid-project cases.

## Design Decisions

### Division of labor (locked)

| Command/Agent | Role |
|---|---|
| `/cg-strategy` | Strategic conversation. Reads all context, reasons about the project, proposes roadmap changes. Model: Opus. |
| `@cg-roadmap` | Pure write interface. Executes specific JSON modifications. Model: Haiku. |
| `/cg-brainstorm` | Single-task clarification. One fuzzy feature at a time. |
| `/cg-resume` | Session start. What to work on now. |

### When to use `/cg-strategy`

- **Day zero**: "I know the objective, here are all my ideas, help me
  structure them into milestones and features."
- **Mid-project**: "Something has shifted. New ideas, dropped assumptions,
  team feedback. Help me rethink the roadmap."
- **After a milestone**: "We finished Phase 1. What should Phase 2 look
  like given what we learned?"

### Hard prerequisite

`compound-gpid.md` must exist. If it doesn't, `/cg-strategy` hard-stops:
> "No project charter found. Run `/cg-setup` first to define the project
> objective and constraints."

`roadmap.json` is NOT required — `/cg-strategy` creates it if missing,
after the conversation concludes and the user approves the proposed
structure.

### Context reading at session start

`/cg-strategy` reads both:
- `compound-gpid.md` — shared project charter (objective, deliverables,
  constraints, current focus)
- `compound-gpid.local.md` — user config (language, project type,
  review depth)

If `roadmap.json` exists, it reads that too. If `.cg-docs/` artifacts
exist (recent plans, brainstorms), it scans them for context. The more
material exists, the richer the conversation.

### Context-aware behaviour

`/cg-strategy` adapts to `project-type` from `compound-gpid.local.md`:
- **Analytical project**: conversation focuses on research questions,
  methodology trade-offs, data constraints, output validity, stakeholder
  framing.
- **Technical project**: conversation focuses on architecture, build order,
  dependency risks, API design, infrastructure.
- **Both/unknown**: covers both dimensions.

Same command, same interface, same output format for all users.

### Output artifact

Every `/cg-strategy` session produces a strategy document committed to
`.cg-docs/strategy/`:

**Filename**: `YYYY-MM-DD-<brief-title>.md`

**Format**:
```markdown
---
date: YYYY-MM-DD
title: "<descriptive title>"
trigger: "new-project | mid-project | post-milestone | other"
outcome: "roadmap-updated | no-change | deferred"
---

# Strategy Session: <Title>

## Context at Session Start

<Brief summary of project state: roadmap status, recent work, what
prompted this session.>

## Discussion Summary

<Key points from the conversation. What ideas were considered, what
trade-offs were discussed, what was ruled out and why.>

## Proposed Changes

<Concrete list of roadmap changes proposed. Format:
- ADD milestone: <title> — <objective>
- ADD feature: <title> to <milestone>
- RETIRE feature: <title> — reason: <why>
- REPRIORITIZE: move <feature> from <milestone A> to <milestone B>
- NO CHANGE: <reason>
>

## Decision

<What was approved. If no changes, explicit statement: "No roadmap
changes made. Reason: <X>.">

## Charter Updates

<If Current Focus was updated in compound-gpid.md, note what changed
and why. If no charter changes, omit this section.>
```

A strategy session ALWAYS ends with one of:
1. A set of approved roadmap changes → dispatches `@cg-roadmap`
2. An explicit "no change" decision → recorded in the strategy document

It never ends with "here are some thoughts." Output is always a decision.

### `.cg-docs/strategy/` folder

New folder. Scaffolded by `/cg-setup` (alongside brainstorms, plans,
solutions). Never loaded at session start — strategy documents are
historical records, not live context.

---

## Implementation Tasks

### Task 1: Fix `@cg-roadmap` model to Haiku

- **File**: `.github/agents/cg-roadmap.agent.md`
- **What to change**:

  In YAML frontmatter, change:
  ```yaml
  model: Claude Sonnet 4.6 (copilot)
  ```
  to:
  ```yaml
  model: Claude Haiku 4.5 (copilot)
  ```

  No other changes to this file.

- **Rationale**: `@cg-roadmap` performs bounded JSON read-modify-write
  operations. It requires no complex reasoning — only schema adherence and
  JSON validation. Haiku is the correct model. Sonnet was a deviation from
  the agreed design (verified 2026-04-01).

- **Acceptance criteria**:
  - `@cg-roadmap` frontmatter shows `model: Claude Haiku 4.5 (copilot)`.
  - No other changes to the agent file.

---

### Task 2: Scaffold `.cg-docs/strategy/` in `/cg-setup`

- **File**: `.github/prompts/cg-setup.prompt.md`
- **What to change**:

  In Step A4 (scaffold `.cg-docs/` structure), add `.cg-docs/strategy/`.
  Note: `.cg-docs/archive/` is created by the Step 1 (charter maintenance)
  plan — if Step 1 has already been implemented, do not add it again here.

  The full structure after both plans are applied:
  ```
  .cg-docs/
  ├── archive/
  │   └── .gitkeep        ← from Step 1 plan
  ├── brainstorms/
  │   └── .gitkeep
  ├── plans/
  │   └── .gitkeep
  ├── strategy/
  │   └── .gitkeep        ← ADD THIS
  └── solutions/
      └── ...
  ```

  Also update the Setup Complete message (Step A6) to mention
  `/cg-strategy`:

  ```markdown
  ### Next Steps

  **If you have a vision for the full project scope:**
  → Run `/cg-strategy` to think through your ideas and build an initial
    milestone and feature structure

  **If requirements for a specific task are fuzzy:**
  → Run `/cg-brainstorm` to clarify before planning

  **If you already know what to build:**
  → Run `/cg-plan` to create an implementation plan
  ```

- **Acceptance criteria**:
  - New projects get `.cg-docs/strategy/` on setup.
  - Setup complete message mentions `/cg-strategy` as the entry point
    for project-level visioning.
  - `/cg-brainstorm` and `/cg-plan` still listed as alternatives.

> **Existing projects**: `/cg-setup` only scaffolds new projects. Users
> who already have a linked project will not get `.cg-docs/strategy/`
> automatically. Add a one-line note to `docs/installation.md` (or the
> equivalent update/migration doc): "If you linked your project before
> this release, create `.cg-docs/strategy/` manually with
> `mkdir .cg-docs\strategy` and add a `.gitkeep` file."

---

### Task 3: Create `/cg-strategy` prompt

- **File**: `.github/prompts/cg-strategy.prompt.md` (CREATE)
- **Important**: Prompts must NOT declare `tools:` or `agents:` in
  frontmatter. Only agents declare tools. Adding `tools:` to a prompt
  (especially `'agent'`) overwrites Copilot's tool context and breaks
  the session. `@cg-roadmap` is dispatched by natural language instruction
  in the prompt body — not via frontmatter wiring.
- **Full content**:

```markdown
---
description: "Strategic project visioning and direction-setting. Use when
you have a full project in mind to structure, or when you need to rethink
direction mid-project. Produces concrete roadmap changes."
model: Claude Opus 4.6 (copilot)
---

# Strategy

You are a senior project strategist helping structure a project vision
into a clear, actionable roadmap — or helping rethink the direction of a
project already underway. You are a thinking partner, not a code
generator. Your job is to ask good questions, surface trade-offs, and
produce concrete decisions.

## File Permissions

- You may read any file in the workspace.
- You may create files ONLY under `.cg-docs/strategy/`.
- You may create `roadmap.json` in the project root if it does not exist.
- You may modify `compound-gpid.md` ONLY to update the `Current Focus`
  and `last-reviewed` fields — no other fields, no other sections.
- You must NOT create or modify any other files.
- You must NOT modify any code, tests, or existing plans.

## Process

### Step 0: Prerequisite Check

1. Read `compound-gpid.md`. If it does not exist, hard-stop:
   > "No project charter found. Run `/cg-setup` first to define the
   > project objective and constraints. Then return to `/cg-strategy`."

2. Read `compound-gpid.local.md`. Extract: `language`, `project-type`,
   `review-depth`. Note `project-type` — it shapes the conversation.

3. If `roadmap.json` exists, read it. Note: current milestones, features,
   their statuses. Compute: how many features are unstarted vs. in
   progress vs. done.

4. If `.cg-docs/brainstorms/` or `.cg-docs/plans/` contain recent files
   (last 60 days), skim their titles and statuses for context. Do not
   read full content unless directly relevant.

5. Present what you found:
   ```
   ## Strategy Session

   **Project**: <project-name>
   **Objective**: <objective>
   **Current Focus**: <current-focus or "not set">
   **Roadmap**: <milestone count> milestones, <feature count> features
               (<done> done, <active> active, <unstarted> unstarted)
   **Recent work**: <brief summary or "no recent plans found">
   ```

### Step 1: Understand the Trigger

Ask ONE opening question — do not ask multiple questions at once:

> "What's prompting this session? Are you:
> 1. Starting fresh — you have a project vision to think through
> 2. Mid-project — something has shifted or new ideas have come up
> 3. Post-milestone — ready to plan the next phase
> 4. Something else"

Wait for the answer. Use it to calibrate the rest of the conversation.

### Step 2: Structured Conversation

Ask questions ONE AT A TIME. Adapt based on `project-type`:

**For new projects (trigger 1):**
- "Describe the project in your own words. What is it building and for
  whom?"
- "Walk me through the ideas you have in mind — big or small, rough or
  specific. What do you want this thing to do?"
- "Are there dependencies between those ideas — things that must exist
  before other things can be built?"
- "What does success look like at the end of the first milestone — what
  is the simplest version that would be genuinely useful?"

**For mid-project / post-milestone (triggers 2, 3):**
- "What has changed? New information, dropped assumptions, feedback from
  the team?"
- "Looking at the current roadmap — what still feels right? What feels
  off?"
- "What would you add, cut, or reprioritize if you were starting fresh
  today?"
- "Is this a scope question (what to build) or a sequencing question
  (what to build next)?"

**For analytical projects** (regardless of trigger), also probe:
- Methodology constraints, data availability, stakeholder needs, output
  validity requirements.

**For technical projects**, also probe:
- Architecture dependencies, infrastructure requirements, API contracts,
  build order constraints.

Stop asking questions when you have enough to propose a clear structure.
Usually 4–6 questions. Never ask more than 8.

### Step 3: Propose Roadmap Structure

Present a concrete proposal. Format:

```
## Proposed Roadmap

**Milestone 1: <title>**
_<one-sentence objective>_
- Feature: <title> [status: idea]
- Feature: <title> [status: idea]

**Milestone 2: <title>**
_<one-sentence objective>_
- Feature: <title> [status: idea]
...

**Changes to existing roadmap** (if roadmap.json existed):
- RETIRE: <feature title> — reason: <why>
- MOVE: <feature> from <milestone A> to <milestone B>
- NO CHANGE: <features staying as-is>
```

If the proposed change involves retiring features or milestones, be
explicit about why. Don't soften it — if something shouldn't be built,
say so clearly.

Ask: "Does this structure make sense? What would you change?"

Iterate until the user approves. Do not proceed to Step 4 without
explicit approval.

### Step 4: Execute Approved Changes

Once approved:

1. **Dispatch `@cg-roadmap`** to apply each change:
   - New milestones: "Add milestone '<title>' with objective '<objective>'."
   - New features: "Add feature '<title>' to milestone '<id>'."
   - Retired features: "Remove feature '<id>' from milestone '<id>'."
   - Status changes: "Update feature '<id>' to status '<status>'."
   - If `roadmap.json` doesn't exist: "Initialize roadmap.json, then add
     milestone..."

2. **Verify** each change: read `roadmap.json` after each dispatch and
   confirm the change was applied. If not, inform the user:
   > "Roadmap update may not have been applied. Run `@cg-roadmap`
   > directly to apply: <specific instruction>"

3. **Update charter if needed**: if the project's "Current Focus" has
   shifted based on this session, ask: "Should I update 'Current Focus'
   in the charter to reflect the new direction?" If yes, update both
   `Current Focus` and `last-reviewed` (set to today's date) in
   `compound-gpid.md`. These two fields always update together — never
   update one without the other.

### Step 5: Save Strategy Document

Save the session record to `.cg-docs/strategy/YYYY-MM-DD-<title>.md`
using the strategy document format. Include:
- What was discussed
- What was proposed
- What was approved (or explicitly: no changes made)
- Any charter updates

### Step 6: Handoff

Suggest the logical next action based on what was decided:

- If new features were added as ideas: "Ready to start on the first
  feature? Run `/cg-brainstorm` to clarify requirements, or `/cg-plan`
  if you already know what to build."
- If features were reprioritized: "Run `/cg-resume` to see your updated
  roadmap and choose where to start."
- If no changes were made: "Strategy session recorded. Run `/cg-resume`
  to continue where you left off."

## Rules

- Always read `compound-gpid.md` AND `compound-gpid.local.md` before
  starting. Never skip Step 0.
- Ask questions one at a time. Never dump a list of questions.
- Never suggest adding a feature you haven't discussed with the user.
- The proposal in Step 3 must be concrete enough that the user can
  approve or modify it directly — no vague categories.
- Always end with a decision. "Here are some thoughts" is not an output.
- Dispatch `@cg-roadmap` for all `roadmap.json` writes. Never write JSON
  directly.
- When updating `compound-gpid.md`, always update both `Current Focus`
  and `last-reviewed` together. Never update one without the other.
- Only modify `compound-gpid.md` if the user explicitly approves the
  update in Step 4.
```

- **Acceptance criteria**:
  - `/cg-strategy` appears as a slash command in Copilot Chat.
  - Hard-stops cleanly if `compound-gpid.md` is missing.
  - Reads both charter and local config at session start.
  - Adapts conversation to project type.
  - Always produces a strategy document in `.cg-docs/strategy/`.
  - Dispatches `@cg-roadmap` for all roadmap writes — never writes JSON
    directly.
  - Always updates `last-reviewed` alongside `Current Focus` — never
    one without the other.
  - Session ends with an explicit decision (roadmap changes OR no-change
    statement), never open-ended.
  - No `tools:` or `agents:` in prompt frontmatter.

---

### Task 4: Add `/cg-strategy` to `/cg-resume` next-step suggestions

- **File**: `.github/prompts/cg-resume.prompt.md`
- **What to change**:

  In Step 4 (Suggest Next Action), add `/cg-strategy` as an option when
  the roadmap has many unstarted features OR when the last strategy session
  was more than 60 days ago:

  ```markdown
  - If roadmap has >60% unstarted features AND no strategy document in
    `.cg-docs/strategy/` from the last 60 days:
    "N. Rethink the roadmap scope — `/cg-strategy`"
  ```

  Also: if `/cg-resume` detects there is NO `roadmap.json` and no strategy
  documents, add:
  ```markdown
  > No roadmap found. If you have a project vision to structure, run
  > `/cg-strategy`. If you prefer to build the roadmap directly, run
  > `@cg-roadmap`.
  ```

- **Acceptance criteria**:
  - `/cg-resume` surfaces `/cg-strategy` when appropriate.
  - Suggestion is contextual — not shown on every run.

---

### Task 5: Update `copilot-instructions.md`

- **File**: `.github/copilot-instructions.md`
- **Dependency**: Implement AFTER the Step 1 (charter maintenance) plan has
  been applied. Both plans modify this file, and charter maintenance must
  be applied first.
- **What to change**:

  Add a `## Workflow Entry Points` section. The right location is after
  the `## Charter Rules` section added by the Step 1 plan:

  ```markdown
  ## Workflow Entry Points

  | Situation | Command |
  |---|---|
  | Full project vision to structure | `/cg-strategy` |
  | Mid-project direction question | `/cg-strategy` |
  | One fuzzy task to clarify | `/cg-brainstorm` |
  | Known task to plan | `/cg-plan` |
  | Direct roadmap edit | `@cg-roadmap` |
  | Resume interrupted work | `/cg-resume` |
  ```

- **Acceptance criteria**:
  - `## Workflow Entry Points` table is present after `## Charter Rules`.
  - `/cg-strategy` is correctly described as the vision/direction command.
  - Section does not duplicate or conflict with Charter Rules content.

---

### Task 6: Update documentation

- **Files**:
  - `docs/workflow.md` (MODIFY)
  - `docs/reference.md` (MODIFY)

- **What to change**:

  **`docs/workflow.md`**:

  Add a new section after "Roadmap (`@cg-roadmap`)":

  ```markdown
  ### Strategy (`/cg-strategy`)

  **When**: You have a full project vision to structure into milestones
  and features — at any stage of the project. Use at day zero to build
  the initial roadmap, mid-project to rethink direction, or after a
  milestone to plan the next phase.

  **What happens**: Reads your project charter, roadmap, and recent work.
  Asks focused questions one at a time to understand your ideas, surface
  trade-offs, and clarify priorities. Proposes a concrete roadmap
  structure for your approval, then dispatches `@cg-roadmap` to apply the
  changes. Saves a record of the session to `.cg-docs/strategy/`.

  **Hard prerequisite**: `compound-gpid.md` must exist (run `/cg-setup`
  first). `roadmap.json` is optional — `/cg-strategy` will create it if
  needed.

  **Output**: Updated `roadmap.json` + `.cg-docs/strategy/YYYY-MM-DD-<title>.md`
  ```

  Update the workflow loop diagram to include `/cg-strategy`:

  ```
  Setup -> Strategy -> Brainstorm -> Plan -> Work -> Review -> Compound
              ^              ^
         (vision/rethink)  (one task)
  ```

  Update the "Prompts vs. Agents vs. Skills" table to add `/cg-strategy`.

  **`docs/reference.md`**:

  Add `/cg-strategy` to the prompts table:

  ```markdown
  | `/cg-strategy` | Full project visioning and direction-setting.
  Structures ideas into milestones, or rethinks the roadmap mid-project.
  Dispatches `@cg-roadmap` for all writes. | Opus |
  ```

  Add `.cg-docs/strategy/` to the directory structure diagram:

  ```
  .cg-docs/
  ├── archive/              # Archived charter content (never loaded at
  │                         # session start)
  ├── brainstorms/
  ├── plans/
  ├── strategy/             # Strategy session records
  └── solutions/
  ```

  Update the "When to use what" quick reference table to include
  `/cg-strategy`.

- **Acceptance criteria**:
  - `docs/workflow.md` documents `/cg-strategy` with examples and
    prerequisites.
  - `docs/reference.md` includes `/cg-strategy` in the prompts table and
    the directory structure.
  - The workflow loop diagram reflects the new entry point.
  - No documentation gap between what the plugin does and what the docs
    say.

---

## Testing Strategy

1. **Haiku model check**:
   ```powershell
   Select-String -Path ".github\agents\cg-roadmap.agent.md" -Pattern "model:"
   ```
   Expected: `model: Claude Haiku 4.5 (copilot)`

2. **No tools in prompt frontmatter**:
   ```powershell
   Select-String -Path ".github\prompts\cg-strategy.prompt.md" -Pattern "tools:"
   ```
   Expected: no output (tools: must not appear).

3. **New project, day zero** ⚠️ _requires live Copilot Chat session —
   cannot be validated structurally_: Run `/cg-setup` then `/cg-strategy`.
   Enter a project vision with 4-5 ideas. Verify: questions come one at a
   time, a milestone structure is proposed, user approval is sought before
   any writes, `roadmap.json` is created/updated, strategy document is
   saved to `.cg-docs/strategy/`.

4. **Mid-project session** ⚠️ _live session_: On a project with an
   existing roadmap, run `/cg-strategy`. Verify it reads and references
   the current roadmap state. Verify it proposes specific changes (not
   just observations).

5. **Missing charter hard-stop** ⚠️ _live session_: Run `/cg-strategy`
   in a project without `compound-gpid.md`. Verify it stops immediately
   with the correct message and does not proceed.

6. **No-change session** ⚠️ _live session_: Run `/cg-strategy` and
   conclude that nothing should change. Verify the strategy document is
   still saved with an explicit "no change" decision.

7. **Roadmap writes via `@cg-roadmap`** ⚠️ _live session_: After a
   strategy session, verify `/cg-strategy` never wrote `roadmap.json`
   directly — all changes went through `@cg-roadmap` dispatch.

8. **Charter update — both fields** ⚠️ _live session_: After a session
   that updates Current Focus, verify `compound-gpid.md` shows both
   `Current Focus` updated AND `last-reviewed` set to today's date.

9. **Project type adaptation** ⚠️ _live session_: Run `/cg-strategy` on
   a project with `project-type: analytical`. Verify the questions address
   methodology and data constraints. Run on a `project-type: package`
   project. Verify the questions address architecture and build order.

10. **Agent visibility check** ⚠️ _requires VS Code Copilot_
    (regression guard): Open Copilot Chat agents dropdown. Verify
    `@cg-roadmap` appears. Verify no review agents appear.

---

## Risks & Mitigations

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| `/cg-strategy` becomes a therapy session, no decision | Medium | Hard rule: session always ends with roadmap diff OR explicit no-change statement. Documented in Rules section. |
| Opus cost for frequent users | Low | `/cg-strategy` is infrequent by design (project-level, not task-level). Scope health nudge in `/cg-resume` guards against overuse. |
| `@cg-roadmap` dispatch fails silently | Medium | Post-dispatch verification in both `@cg-roadmap` design and `/cg-strategy` Step 4. |
| User confusion between `/cg-strategy` and `/cg-brainstorm` | Medium | Entry point table in `copilot-instructions.md`. Different scopes: strategy = whole project, brainstorm = one task. |
| `last-reviewed` not updated alongside `Current Focus` | Low | Explicit rule in both prompt body and Rules section: always update together. Test 8 catches this. |
| Strategy document grows stale as reference | Low | Strategy docs are historical records, never loaded at session start. |

---

## Out of Scope

- Automated charter updates beyond `Current Focus` and `last-reviewed`.
- Strategy session triggered automatically by `/cg-resume`.
- Comparison or diff viewer for strategy documents.
- Multi-session strategy (one session = one document = one decision).
- Integration with external project management tools.

---

## Dependency Note

This plan depends on:
- Step 1 plan (`2026-04-01-charter-maintenance.md`) being implemented
  **first** — both plans modify `copilot-instructions.md`, and Task 5
  here inserts content after sections created by the Step 1 plan.
- `@cg-roadmap` existing and working correctly (verified ✅).

Task 1 (Haiku fix) is independent and should be done first — it takes
15 minutes and corrects a live deviation.

---

## Commit Messages

| Task | Suggested commit |
|------|-----------------|
| 1 | `fix(agents): revert @cg-roadmap model to Haiku 4.5` |
| 2 | `feat(setup): scaffold .cg-docs/strategy/, add /cg-strategy to next steps` |
| 3 | `feat(prompts): add /cg-strategy command` |
| 4 | `feat(resume): surface /cg-strategy when roadmap scope is heavy` |
| 5 | `feat(instructions): add workflow entry point map` |
| 6 | `docs: document /cg-strategy in workflow.md and reference.md` |

