---
date: 2026-03-26
title: "Add roadmap.json and @cg-roadmap agent — structured milestone tracking"
status: completed
brainstorm: "N/A (iterative design with architecture advisor)"
language: "both"
estimated-effort: "medium"
tags: [roadmap, milestones, agent, project-awareness, strategic-planning]
---

# Plan: Add `roadmap.json` and `@cg-roadmap` Agent

## Objective

Add a committed, machine-readable project roadmap (`roadmap.json`) and a
dedicated agent (`@cg-roadmap`) that manages it. The roadmap is a **strategic
planning surface** the user owns — it captures milestones, features, and ideas
so that every session starts with clarity about where the project is going and
what to work on next. The agent is the single point of schema knowledge for
roadmap writes. Other prompts dispatch it as a subagent for updates and only
read the file directly for display.

## Context

- **Step 1** (completed): Fixed `.cg-docs/` gitignore — institutional knowledge
  is now committed.
- **Step 2** (completed): Created `compound-gpid.md` as the shared project
  charter. All prompts read it at session start via "Step 0: Get Bearings."
- **This is Step 3** in the project awareness effort. The charter tells the
  agent what the project IS. The roadmap tells it where the project is GOING.
- **Design decisions from prior conversation**:
  - `roadmap.json` is committed and shared (like `compound-gpid.md`).
  - Do NOT add it to universal Step 0. Load it only in specific prompt steps
    that need it.
  - The roadmap is primarily user-curated (a thinking tool), not an automation
    ledger. The user adds milestones and ideas; prompts assist with linking and
    status updates.
  - `@cg-roadmap` centralizes all write logic. Other prompts dispatch it as a
    subagent for modifications, avoiding duplicated JSON schema knowledge.
  - `@cg-roadmap` is the ONLY `user-invokable: true` agent in the plugin.
    All review agents are `user-invokable: false` (implemented in the
    2026-03-23 review architecture plan).

## Implementation Steps

### 1. Define the `roadmap.json` schema

No file to create yet — this section documents the schema that Task 2 (the
agent) and Task 3 (`/cg-setup`) will use.

**Schema (v1):**

```json
{
  "schemaVersion": "compound-gpid-roadmap-v1",
  "milestones": [
    {
      "id": "kebab-case-id",
      "title": "Human-readable milestone title",
      "objective": "One sentence: why this milestone exists.",
      "status": "in-progress",
      "features": [
        {
          "id": "kebab-case-feature-id",
          "title": "Human-readable feature title",
          "status": "idea",
          "plan": null
        }
      ]
    }
  ]
}
```

**Status Enumerations:**

| Type | Valid values |
|------|-------------|
| `milestones[].status` | `planned`, `in-progress`, `done` |
| `features[].status` | `idea`, `planned`, `active`, `done` |

Note: The two status sets are intentionally different. Feature `active` maps
to milestone `in-progress`. Milestone status is always derived, never set directly.

**Field rules:**

- `schemaVersion`: always `"compound-gpid-roadmap-v1"`. Renamed from `$schema` to avoid collision with the JSON Schema `$schema` URI keyword.
- `milestones[].id`: kebab-case, unique across milestones. Used for
  programmatic reference.
- `milestones[].title`: short human-readable name.
- `milestones[].objective`: one sentence explaining WHY this milestone exists.
  This is the strategic clarity that distinguishes milestones from mere
  groupings.
- `milestones[].status`: one of `planned`, `in-progress`, `done`. Derived
  from feature statuses by the agent (all features done → milestone done;
  any feature active → milestone in-progress; otherwise → planned).
- `features[].id`: kebab-case, unique within the parent milestone.
- `features[].title`: short human-readable name.
- `features[].status`: one of `idea` → `planned` → `active` → `done`.
  - `idea`: captured intent, no plan exists yet.
  - `planned`: a plan file exists in `.cg-docs/plans/`.
  - `active`: implementation is underway.
  - `done`: implementation is complete.
- `features[].plan`: nullable path to the `.cg-docs/plans/` file. `null` for
  ideas; set when `/cg-plan` creates a plan. This is the linking mechanism —
  the plan file is the source of truth for implementation details; the roadmap
  only holds the reference.

**What is NOT in the schema (and why):**

- No dates on features — dates live in plan filenames and frontmatter.
  Duplicating them creates sync obligations.
- No descriptions on features — the title should be self-explanatory. If it
  needs a description, it needs a brainstorm, not a JSON field.
- No `blocked`, `deferred`, or `cancelled` statuses — these are decision-rich
  states that belong in human conversation (brainstorms, plan frontmatter),
  not in a JSON file. If a feature is no longer relevant, remove it. The
  roadmap is a living document, not an audit trail.
- No priority or ordering — features within a milestone are unordered. If
  the user cares about sequence, that's a planning decision made in
  `/cg-plan`, not a schema field.
- No `updated` timestamp — a mutable timestamp creates merge conflicts when
  two team members edit `roadmap.json` on parallel branches. Git commit
  metadata (`git log -1 -- roadmap.json`) provides the same staleness signal.

### 2. Create `@cg-roadmap` agent

- **File**: `.github/agents/cg-roadmap.agent.md` (CREATE)
- **Details**:

  YAML frontmatter:

  ```yaml
  ---
  description: "Manages roadmap.json — adds milestones and features, updates statuses, and links plans. The only agent users interact with directly."
  model: Claude Sonnet 4.6 (copilot)
  tools: ['read', 'write']
  user-invokable: true
  ---
  ```

  Agent body — the full process:

  ```markdown
  # Roadmap Manager

  You manage the project's `roadmap.json` file. You are the single source of
  truth for how this file is read and written. Other prompts dispatch you as
  a subagent for roadmap modifications.

  ## File Permissions

  - You may read any file in the workspace.
  - You may create and modify `roadmap.json` in the project root.
  - You must NOT create, modify, or delete any other files.

  ## Schema

  `roadmap.json` structure -- always read the file before writing:

  ```json
  {
    "schemaVersion": "compound-gpid-roadmap-v1",
    "milestones": [
      {
        "id": "kebab-case-id",
        "title": "Human-readable milestone title",
        "objective": "One sentence: why this milestone exists.",
        "status": "planned",
        "features": [
          {
            "id": "kebab-case-feature-id",
            "title": "Human-readable feature title",
            "status": "idea",
            "plan": null
          }
        ]
      }
    ]
  }
  ```

  **Status enumerations:**

  | Field | Valid values |
  |-------|-------------|
  | `milestones[].status` | `planned`, `in-progress`, `done` |
  | `features[].status` | `idea`, `planned`, `active`, `done` |

  Milestone status is always **derived** -- never set directly. Feature `active`
  maps to milestone `in-progress`.

  **Key field rules:**
  - `schemaVersion`: always `"compound-gpid-roadmap-v1"`.
  - IDs: kebab-case matching `^[a-z0-9]+(-[a-z0-9]+)*$`. Generated from title:
    lowercase, replace spaces/special chars with hyphens, collapse consecutive
    hyphens. Never renamed after creation.
  - `features[].plan`: string path relative to project root, or `null`. Before
    writing, verify the file exists at the given path.

  ## Milestone Status Calculation

  Always derived using this ordered cascade -- apply the first rule that matches:

  1. Features array is empty → `planned`
  2. ALL features are `done` → `done`
  3. ANY feature is `active` → `in-progress`
  4. ANY feature is `done` (but not all, and none active) → `in-progress`
  5. Otherwise (all `idea`, all `planned`, or mix) → `planned`

  **Never** set milestone status directly -- always recompute from features.

  ## Operations

  You support the following operations. Infer which one the user or calling
  prompt needs from context.

  ### Add Milestone

  1. Ask for: title, objective (one sentence).
  2. Generate a kebab-case `id` from the title.
  3. Verify the id is unique across existing milestones.
  4. Add the milestone with `status: "planned"` and an empty `features` array.
  5. Write the file.

  ### Add Feature

  1. Ask for: title, and which milestone it belongs to (show list).
  2. Generate a kebab-case `id` from the title.
  3. Verify the id is unique within the target milestone.
  4. Add the feature with `status: "idea"` and `plan: null`.
  5. Recalculate the milestone's status.
  6. Write the file.

  ### Link Plan to Feature

  Typically dispatched by `/cg-plan` after creating a plan file.

  1. Receive: plan file path (relative to project root) and feature id as
     `{milestone-id, feature-id}` (preferred) or feature title.
  2. Verify the plan file exists at the given path. If not, report:
     "Plan file not found: <path>. Aborting link." and stop.
  3. Find the matching feature. If ambiguous, ask.
  4. Set `plan` to the plan file path.
  5. Set `status` to `"planned"`.
  6. Recalculate the milestone's status.
  7. Write the file.

  ### Update Feature Status

  Typically dispatched by `/cg-work` after implementation is complete.

  1. Receive: plan file path or feature id, and the new status.
  2. Find the matching feature by plan path or id.
  3. Update `status` to the new value.
  4. Recalculate the milestone's status.
  5. Write the file.

  ### Remove Feature or Milestone

  1. Confirm with the user before deleting.
  2. Remove the entry.
  3. Recalculate affected milestone status (if removing a feature).
  4. Write the file.

  ## Rules

  - Always read `roadmap.json` before making changes (never work from memory).
  - **JSON validation before every write** -- after composing the JSON, verify:
    1. No trailing commas after the last item in any array or object.
    2. All string values are quoted; no bare words.
    3. `milestones` is still an array.
    4. Every `milestones[].status` is one of `planned`, `in-progress`, `done`.
    5. Every `features[].status` is one of `idea`, `planned`, `active`, `done`.
    If any check fails, fix it before writing.
  - Confirm destructive operations (remove) with the user before executing.
  - When dispatched as a subagent, do not ask questions — use the information
    provided by the calling prompt. If critical information is missing, report
    what you need and stop.
  - Keep `id` values stable — never rename an existing id. If the title
    changes, only update the `title` field.
  ```

- **Acceptance criteria**:
  - Agent file exists with correct frontmatter.
  - `user-invokable: true` (visible in Copilot dropdown).
  - `tools: ['read', 'write']` (can modify `roadmap.json`).
  - All five operations documented in the agent body (Show Progress excluded — display is `/cg-resume`'s responsibility).
  - Model is Claude Sonnet 4.6.
  - Milestone status auto-calculation rule is explicit.
  - File permissions restrict writes to `roadmap.json` only.

### 3. Add `roadmap.json` scaffolding to `/cg-setup`

- **File**: `.github/prompts/cg-setup.prompt.md` (MODIFY)
- **Details**:

  **Mode A (new project)** — add a new step after A5 (Update `.gitignore`):

  ```markdown
  #### A5.5. Create `roadmap.json`

  Create `roadmap.json` in the project root:

  ```json
  {
    "schemaVersion": "compound-gpid-roadmap-v1",
    "milestones": []
  }
  ```

  This file tracks project milestones and features. Users can add milestones
  and ideas by invoking `@cg-roadmap` in Copilot Chat.
  ```

  **Mode A — Step A6 (Print Setup Complete)**: Add `@cg-roadmap` to the
  "Available Commands" section:

  ```
  - `@cg-roadmap`    — Add milestones, features, and ideas to your project roadmap
  ```

  **Mode B (returning project)** — add a check in B1.5 (scaffold missing
  structures):

  ```markdown
  If `roadmap.json` does not exist in the project root, mention:
  > "No `roadmap.json` found. You can create one by invoking `@cg-roadmap`
  > and asking it to set up the roadmap, or it will be created automatically
  > if you re-run `/cg-setup` in new-project mode."
  ```

  **File Permissions**: Add to the existing section:
  ```
  - You may create `roadmap.json` in the project root.
  ```

- **Acceptance criteria**:
  - New projects get an empty `roadmap.json` during setup.
  - Returning projects are informed if `roadmap.json` is missing.
  - `@cg-roadmap` listed in the setup complete message.
  - File permissions updated.

### 4. Modify `/cg-plan` to dispatch `@cg-roadmap` for linking

- **File**: `.github/prompts/cg-plan.prompt.md` (MODIFY)
- **Details**:

  Add a new step after the plan file is written (this is currently the last
  step — it will become the second-to-last, with the new step as the final
  one):

  ```markdown
  ### Step N: Register in Roadmap (if applicable)

  If `roadmap.json` exists at the project root:

  1. Read it.
  2. Scan the feature list across all milestones for a feature whose title
     closely matches this plan's title.
  3. If a match is found:
     - Ask the user: "This plan looks like it corresponds to '<feature title>'
       in the '<milestone title>' milestone. Link it? (yes/no)"
     - If yes: dispatch `@cg-roadmap` with: "Link plan
       `.cg-docs/plans/<filename>` to feature `<feature-id>` in milestone
       `<milestone-id>`. Set status to planned."
       Then verify: read `roadmap.json` again and confirm the change was
       applied. If not: "Roadmap update may not have been applied. Run
       `@cg-roadmap` directly."
  4. If no match is found:
     - Ask the user: "Should this plan be added to a milestone in the
       roadmap?"
       - If yes: show existing milestones and ask which one, or offer to
         create a new one. Dispatch `@cg-roadmap` with the appropriate
         operation (add feature, or add milestone + add feature).
         Then verify: read `roadmap.json` again and confirm the change was
         applied. If not: "Roadmap update may not have been applied. Run
         `@cg-roadmap` directly."
       - If no: skip silently.

  If `roadmap.json` does not exist, skip this step entirely.
  ```

  **File Permissions**: Add to the existing section:
  ```
  - You may read `roadmap.json` in the project root.
  ```

  Note: `/cg-plan` does NOT write `roadmap.json` directly. It dispatches
  `@cg-roadmap` for all modifications.

- **Acceptance criteria**:
  - `/cg-plan` checks for matching features before asking.
  - Auto-links when there's an unambiguous single-milestone match.
  - Dispatches `@cg-roadmap` for all writes (never writes JSON directly).
  - Skips entirely when `roadmap.json` doesn't exist.
  - File permissions include read access to `roadmap.json`.

### 5. Modify `/cg-work` to dispatch `@cg-roadmap` for status update

- **File**: `.github/prompts/cg-work.prompt.md` (MODIFY)
- **Details**:

  Add a new step after the current Step 4 (Summary):

  ```markdown
  ### Step 5: Update Roadmap Status

  If `roadmap.json` exists at the project root:

  1. Read it.
  2. Find the feature entry whose `plan` path matches the plan you just
     implemented.
  3. If found: dispatch `@cg-roadmap` with: "Update feature with plan path
     `<plan-path>` to status done."
  4. If not found: skip silently. Not every plan needs to be
     milestone-tracked.
  5. After dispatch, verify `roadmap.json` was updated (read the file again
     and check the status changed). If not, inform the user:
     > "Roadmap update may not have been applied. You can run `@cg-roadmap`
     > directly to update the status."

  If `roadmap.json` does not exist, skip this step entirely.
  ```

  **File Permissions**: Add to the existing section:
  ```
  - You may read `roadmap.json` in the project root.
  ```

- **Acceptance criteria**:
  - `/cg-work` auto-updates feature status to `done` after implementation.
  - Dispatches `@cg-roadmap` (never writes JSON directly).
  - Includes a post-dispatch verification check.
  - Skips silently when no matching feature exists or file is missing.
  - File permissions include read access to `roadmap.json`.

### 6. Modify `/cg-brainstorm` to offer roadmap registration

- **File**: `.github/prompts/cg-brainstorm.prompt.md` (MODIFY)
- **Details**:

  Add to the existing Step 5 (Handoff), after the current handoff message and
  charter update suggestion:

  ```markdown
  ### Roadmap Registration

  If `roadmap.json` exists at the project root:

  1. Ask the user: "Should this brainstorm be added to the roadmap as an
     idea?"
  2. If yes:
     - Show existing milestones and ask which one the idea belongs to, or
       offer to create a new milestone.
     - Dispatch `@cg-roadmap` with: "Add feature '<brainstorm title>' to
       milestone '<milestone-id>' with status idea."
     - Verify: read `roadmap.json` again; confirm the feature was added.
       If not: "Roadmap update may not have been applied. Run `@cg-roadmap`."
  3. If no: skip.

  If `roadmap.json` does not exist, skip this section entirely.
  ```

  **File Permissions**: Add to the existing section:
  ```
  - You may read `roadmap.json` in the project root.
  ```

- **Acceptance criteria**:
  - `/cg-brainstorm` offers roadmap registration after capturing the decision.
  - Dispatches `@cg-roadmap` (never writes JSON directly).
  - Skips when `roadmap.json` doesn't exist.
  - File permissions include read access to `roadmap.json`.

### 7. Modify `/cg-resume` to display roadmap progress and scope health

- **File**: `.github/prompts/cg-resume.prompt.md` (MODIFY)
- **Details**:

  **Insertion point: Step 2** -- add sub-step 2d (after 3c "Recent git activity"):

  ```markdown
  #### 3d. Milestone progress

  If `roadmap.json` exists at the project root, read it and compute:
  - For each milestone: count of done/total features, overall status.
  - Any features with `status: "active"` (work currently underway).
  - Scope health: what percentage of all features are `idea` or `planned`
    (not started).
  ```

  **Insertion point: Step 3 output section** -- add section after "Recent Git
  Activity":

  ```markdown
  ### 📊 Milestone Progress (<milestone count>)
  **<milestone title>** — <done>/<total> features [<status>]
    _<objective>_
    ✅ <done feature>
    🔄 <active feature>
    📋 <planned feature>
    💡 <idea feature>

  **<next milestone>** — ...
  ```

  **Scope health nudge** — add after the milestone progress section:

  ```markdown
  If more than 60% of all features across milestones are `idea` or `planned`:

  > ⚠️ **Roadmap scope check**: <N> of <total> features haven't been started.
  > Consider reviewing your roadmap with `@cg-roadmap` to archive or
  > deprioritize items that aren't near-term.
  ```

  **Insertion point: Step 4 "Suggest Next Action"** -- extend the options list: If the roadmap has
  features with `status: "idea"` in an `in-progress` milestone, include an
  option:

  ```
  N. Plan a roadmap idea: **<feature title>** (in <milestone title>) — `/cg-plan`
  ```

  `/cg-resume` reads `roadmap.json` directly — it does NOT dispatch
  `@cg-roadmap` for display. The agent is for writes; `/cg-resume` is for
  reads.

  **Cross-check** (for `in-progress` milestones only): for each feature with a
  non-null `plan` path, read the linked plan file's YAML frontmatter and check:
  - If `plan` path does not exist → stale reference warning.
  - If feature `status: "active"` but plan frontmatter `status: completed`
    → roadmap-behind-plan drift warning.
  - If feature `status: "done"` but plan frontmatter does not have
    `status: completed` → roadmap-ahead-of-plan drift warning.

  Plan files use a `status:` field in YAML frontmatter; `/cg-work` sets it to
  `completed` when implementation finishes.

  Display any discrepancies after the milestone progress section:
  > "⚠️ Feature '<title>' is marked active but its plan is completed.
  >  Run `@cg-roadmap` to update its status."
  > "⚠️ Feature '<title>' has a stale plan reference ('<path>' not found)."

- **Acceptance criteria**:
  - `/cg-resume` displays milestone progress with completion counts.
  - Scope health nudge appears when >60% features are unstarted.
  - Cross-check catches roadmap/plan status drift.
  - Suggested next action includes roadmap ideas from active milestones.
  - Reads directly (no subagent dispatch for display).
  - Gracefully skips when `roadmap.json` doesn't exist.

### 8. Verify `user-invokable: false` on all review agents

- **Files**: All 9 files in `.github/agents/`:
  1. `cg-code-quality.agent.md`
  2. `cg-testing.agent.md`
  3. `cg-documentation.agent.md`
  4. `cg-version-control.agent.md`
  5. `cg-reproducibility.agent.md`
  6. `cg-performance.agent.md`
  7. `cg-architecture.agent.md`
  8. `cg-data-quality.agent.md`
  9. `cg-learnings-researcher.agent.md`

- **Details**:

  The 2026-03-23 review architecture plan (Task 1) added
  `user-invokable: false` and `tools: ['read', 'search']` to all 9 agents.
  That plan is marked `status: completed`. Verify — do NOT re-implement.

  Run:
  ```powershell
  Select-String -Path ".github\agents\*.agent.md" -Pattern "user-invokable" | ForEach-Object { $_.Filename + ": " + $_.Line.Trim() }
  ```

  Expected output: all 9 agents show `user-invokable: false`. The new
  `cg-roadmap.agent.md` shows `user-invokable: true`.

  If any agent is missing the property, add it.

- **Acceptance criteria**:
  - All 9 review agents have `user-invokable: false`.
  - `@cg-roadmap` is the ONLY agent with `user-invokable: true`.
  - Verification grep confirms this.

### 9. Update documentation

- **Files**:
  - `docs/workflow.md` (MODIFY)
  - `docs/reference.md` (MODIFY)

- **Details**:

  **`docs/workflow.md`**:

  Add a new section after "Resume" (currently section 8), or integrate into
  the existing structure:

  ```markdown
  ### Roadmap (`@cg-roadmap`)

  **When**: Any time you want to capture a milestone, feature idea, or check
  project progress.

  **What happens**: The agent reads and modifies `roadmap.json` — adding
  milestones, registering features, linking plans, and updating statuses.
  Other prompts (`/cg-plan`, `/cg-work`, `/cg-brainstorm`) dispatch this
  agent automatically for roadmap updates.

  **How to use**: Invoke `@cg-roadmap` directly in Copilot Chat. Examples:
  - "Add a milestone for survey harmonization"
  - "I have an idea for automated PPP validation — add it to the pipeline milestone"
  - "Show me the roadmap progress"
  - "Remove the feature about X, we're not doing it anymore"

  **Output**: Updated `roadmap.json` in the project root.
  ```

  Add a note in the "Prompts vs. Agents vs. Skills" table explaining that
  `@cg-roadmap` is the only user-invokable agent — all others are dispatched
  by `/cg-review`.

  **`docs/reference.md`**:

  Add `@cg-roadmap` to the agents table. Add `roadmap.json` to the
  "Directory Structure" diagram:

  ```
  your-project/
  ├── compound-gpid.md          # Project charter (committed — shared objectives)
  ├── compound-gpid.local.md    # Your project config (gitignored)
  ├── roadmap.json              # Milestone & feature tracker (committed)
  └── .cg-docs/                 # ...
  ```

- **Acceptance criteria**:
  - `docs/workflow.md` documents `@cg-roadmap` usage with examples.
  - `docs/reference.md` lists `@cg-roadmap` in agents table.
  - Directory structure diagram includes `roadmap.json`.
  - Documentation distinguishes `@cg-roadmap` (user-invokable) from review
    agents (subagent-only).

---

## Implementation Commit Messages

Use conventional commits (`type(scope): description`). Suggested messages per task:

| Task | Suggested commit message |
|------|---------------------------|
| Plan file | `plan(roadmap): add roadmap.json and @cg-roadmap agent plan` |
| 2 | `feat(agents): add @cg-roadmap agent` |
| 3 | `feat(setup): scaffold roadmap.json in /cg-setup` |
| 4 | `feat(plan): dispatch @cg-roadmap for roadmap linking` |
| 5 | `feat(work): dispatch @cg-roadmap for status update` |
| 6 | `feat(brainstorm): offer roadmap registration on handoff` |
| 7 | `feat(resume): add milestone progress display and cross-check` |
| 8 | `test(agents): verify user-invokable flags on all agents` |
| 9 | `docs: document @cg-roadmap usage and directory structure` |

---

## Testing Strategy

### Manual Testing

1. **New project setup**: Run `/cg-setup` on a fresh project. Verify
   `roadmap.json` exists with empty milestones array and correct schema
   version.

2. **Direct agent interaction**: Invoke `@cg-roadmap` in Copilot Chat:
   - "Add a milestone called Data Pipeline with objective: Automate the
     survey harmonization workflow end-to-end."
   - Verify `roadmap.json` has the milestone with correct id, title,
     objective, and `status: "planned"`.
   - "Add a feature called 'Parse raw survey files' to the Data Pipeline
     milestone."
   - Verify feature added with `status: "idea"` and `plan: null`.

3. **Brainstorm → roadmap flow**: Run `/cg-brainstorm`, complete a
   brainstorm. At the end, accept the roadmap registration offer. Verify
   the brainstorm title appears as a feature with `status: "idea"` in the
   selected milestone.

4. **Plan → roadmap linking**: Run `/cg-plan` on the brainstorm. Verify the
   prompt detects the matching roadmap feature and offers to link. After
   linking, verify `status: "planned"` and `plan` path is set.

5. **Work → roadmap completion**: Run `/cg-work` on the plan. After
   implementation, verify the feature's status is updated to `"done"` and
   the milestone's status is recalculated.

6. **Resume → roadmap display**: Run `/cg-resume`. Verify milestone progress
   section appears with correct completion counts and status icons. If >60%
   features are unstarted, verify the scope health nudge appears.

7. **Cross-check detection**: Manually set a feature's plan frontmatter to
   `status: completed` but leave the roadmap feature at `status: "active"`.
   Run `/cg-resume`. Verify it surfaces the discrepancy.

8. **No-roadmap project**: Run `/cg-plan`, `/cg-work`, `/cg-brainstorm`, and
   `/cg-resume` on a project without `roadmap.json`. Verify no errors, no
   roadmap mentions.

9. **Agent visibility check**: Open the Copilot Chat agents dropdown. Verify
   `@cg-roadmap` appears. Verify no review agents appear.

### Automated Tests (`tests/roadmap.Tests.ps1`)

Create `tests/roadmap.Tests.ps1` covering:

```powershell
Describe "roadmap.json schema" {
    It "parses without error" { ... }
    It "requires schemaVersion field" { ... }
    It "rejects invalid milestone status" { ... }
    It "rejects invalid feature status" { ... }
    It "rejects duplicate milestone IDs" { ... }
    It "rejects duplicate feature IDs within a milestone" { ... }
}

Describe "Milestone Status Calculation" {
    It "empty features -> planned" { ... }
    It "all done -> done" { ... }
    It "any active -> in-progress" { ... }
    It "mix of done + idea (no active) -> in-progress" { ... }
    It "mix of done + planned (no active) -> in-progress" { ... }
    It "all idea -> planned" { ... }
    It "all planned -> planned" { ... }
    It "mix of planned + idea -> planned" { ... }
}

Describe "/cg-resume scope health" {
    It "nudge fires at exactly 60% unstarted" { ... }
    It "nudge does not fire below 60%" { ... }
    It "empty feature list -> no divide-by-zero" { ... }
}
```

Implement status calculation logic as pure PowerShell helper functions (no
LLM invocation) for deterministic test results.

### Structural Validation

```powershell
# Verify only @cg-roadmap is user-invokable
Select-String -Path ".github\agents\*.agent.md" -Pattern "user-invokable" | `
  ForEach-Object { $_.Filename + ": " + $_.Line.Trim() }

# Verify roadmap.json is in cg-setup scaffolding
Select-String -Path ".github\prompts\cg-setup.prompt.md" -Pattern "roadmap.json"

# Verify dispatching prompts reference @cg-roadmap
Select-String -Path ".github\prompts\cg-plan.prompt.md", `
  ".github\prompts\cg-work.prompt.md", `
  ".github\prompts\cg-brainstorm.prompt.md" -Pattern "cg-roadmap"

# Verify /cg-resume reads roadmap.json
Select-String -Path ".github\prompts\cg-resume.prompt.md" -Pattern "roadmap.json"

# Verify schemaVersion (not $schema) is used
Select-String -Path ".github\agents\cg-roadmap.agent.md", `
  ".github\prompts\cg-setup.prompt.md" -Pattern "schemaVersion"

# Verify roadmap.json is NOT in .gitignore
$isIgnored = Select-String -Path ".gitignore" -Pattern "roadmap\.json" -Quiet
"roadmap.json in .gitignore: $isIgnored"
# Expected: False
```

---

## Risks & Mitigations

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| JSON corruption from model edits | Medium | Keep file small by design (3-5 milestones, 3-8 features each). File is committed to git — corruption is recoverable via `git checkout`. Agent validates JSON before writing. |
| Subagent dispatch failure (silent) | Medium | `/cg-work`, `/cg-plan`, and `/cg-brainstorm` all include post-dispatch verification (read-back and confirm). If update not applied, user is informed and can run `@cg-roadmap` directly. |
| Roadmap/plan status drift | Medium | `/cg-resume` cross-checks feature status against plan frontmatter and surfaces discrepancies. |
| Feature ID collisions | Low | Agent checks for existing IDs before adding. IDs are scoped per-milestone. |
| Scope creep (roadmap grows indefinitely) | Medium | `/cg-resume` nudges user when >60% features are unstarted. `@cg-roadmap` supports removing features. |
| Analytical users uncomfortable with JSON | Low | `@cg-roadmap` provides full natural-language interaction. Users never need to edit JSON directly. |
| `user-invokable` not supported in user's VS Code version | Low | Property documented since VS Code 1.109. If unsupported, agent still works — it just also appears for review agents (no breakage, just UI clutter). |

---

## Out of Scope

- **Automatic milestone creation from brainstorms** — the user explicitly
  chooses milestones. The agent assists, not automates.
- **Priority or ordering of features** — sequencing decisions belong in
  `/cg-plan`, not in roadmap.json.
- **Charter↔roadmap integration** — updating `compound-gpid.md` current
  focus based on roadmap progress is a natural future connection, but should
  be implemented after both features are working independently.
- **`copilot-instructions.md` restructuring** — separate effort after Steps
  2-5 (per prior design decision).
- **Roadmap visualization or export** — if needed, this is a future feature.
  The JSON is the source of truth; rendering is `/cg-resume`'s job for now.
- **Schema migration (v1 → v2)** — the `schemaVersion` field enables future
  migration, but no migration tool or process is designed here. When a new
  schema version is needed, create a separate plan for the migration approach.

---

## Dependency Note

This plan has no blockers. Steps 1-2 of the project awareness effort are
complete. This plan can be implemented immediately.

After this plan is complete, **Step 4** (add roadmap reading to targeted
prompt steps) is largely already addressed by Tasks 4-7 above — each prompt
that needs roadmap data already gets the relevant modification. Step 4 may
reduce to a verification pass confirming all integrations work correctly.
