---
date: 2026-03-16
title: "Add /cg-fixbug prompt — structured bug-fix workflow"
status: completed
language: "both"
estimated-effort: "medium"
tags: [prompt, bug-fix, workflow, compound-docs, learnings]
---

# Plan: Add `/cg-fixbug` Prompt — Structured Bug-Fix Workflow

## Objective

Build a new `/cg-fixbug` prompt that guides the user through a structured five-step bug-fix arc: **Intake → Reproduce → Diagnose → Fix → Document**. The prompt enforces hard stops at Steps 2 and 4 (user must confirm the test fails, then confirm the test passes) before a verified bug document is written. Supporting files are updated so the new `bugs` category is scaffolded, searchable, and documented throughout the plugin.

## Context

- The current workflow loop is: Brainstorm → Plan → Work → Review → Compound, with Resume for re-entry.
- `/cg-fixbug` sits logically between Work and Review but can be invoked standalone at any point.
- The `cg-compound` prompt already captures solutions in `.cg-docs/solutions/<category>/`; `/cg-fixbug` adds a new `bugs` category with an extended schema (adds `type`, `test-written`, `fix-confirmed` fields and `Reproduction Test` / `Lessons Learned` sections).
- No brainstorm document exists — the full specification was provided directly by the user.

## Implementation Steps

### 1. Create `.github/prompts/cg-fixbug.prompt.md`

- **Files**: `.github/prompts/cg-fixbug.prompt.md` (CREATE)
- **Details**:
  - YAML frontmatter:
    ```yaml
    ---
    description: "Structured bug-fix workflow: reproduce, diagnose, fix, verify, document."
    model: Claude Sonnet 4.6 (copilot)
    ---
    ```
  - H1 title: `# Fix Bug`
  - File Permissions section (READ any file; CREATE only under `.cg-docs/solutions/bugs/` and test files; MODIFY only source files related to the confirmed fix; NEVER modify other `.cg-docs/` files).
  - Five-step Process section:
    - **Step 1 — Intake**: Ask user to describe symptom, expected vs actual. Search `.cg-docs/solutions/bugs/` for similar past bugs (keyword match on title, tags, root-cause). If found, surface them and ask whether it's the same issue.
    - **Step 2 — Reproduce (HARD STOP)**: Write a failing test. Print explicit stop message: _"Run this test and confirm it fails before we continue. Reply 'confirmed failing' to proceed."_ Do NOT continue until user confirms.
    - **Step 3 — Diagnose**: State root-cause hypothesis: _"The root cause appears to be X because Y."_ Ask if diagnosis is correct or needs investigation. Ask clarifying questions one at a time.
    - **Step 4 — Fix (HARD STOP)**: Implement the fix. Print explicit stop message: _"Run the test again and confirm it now passes. Reply 'confirmed fixed' to proceed to documentation."_ Do NOT continue until user confirms.
    - **Step 5 — Document**: Create `.cg-docs/solutions/bugs/YYYY-MM-DD-<title>.md` with the specified schema (date, title, category, type, language, tags, root-cause, severity, test-written, fix-confirmed). Sections: Symptom, Root Cause, Reproduction Test, Fix, Lessons Learned, Related. After writing, suggest: _"If this bug reveals a pattern the whole team should avoid, run `/cg-compound` to capture it as a team-wide lesson."_
  - Schema Rules section: `test-written` and `fix-confirmed` must be `"yes"` at document-write time. `lessons-learned` written only after fix is confirmed.
- **Tests**: No automated test (prompt file). Manual verification: invoke `/cg-fixbug` in Copilot Chat, walk through each step, confirm hard stops block progression.
- **Acceptance criteria**:
  - Prompt exists at `.github/prompts/cg-fixbug.prompt.md`.
  - YAML frontmatter matches convention (description + model).
  - All five steps are present with correct hard-stop language in Steps 2 and 4.
  - File Permissions section is present.
  - Bug document schema matches spec exactly (all fields, all sections).

---

### 2. Modify `.github/agents/cg-learnings-researcher.agent.md`

- **Files**: `.github/agents/cg-learnings-researcher.agent.md` (MODIFY)
- **Details**:
  - In the **Knowledge Sources** section, under `.cg-docs/solutions/`, add a new bullet:
    ```
    - `bugs/` — Bug reproductions, diagnoses, and verified fixes
    ```
  - Insert it in alphabetical order among the existing sub-bullets (i.e. after `build-errors/` and before `data-quality/`).
- **Tests**: Grep for `bugs/` in the file after editing.
- **Acceptance criteria**: The `bugs/` directory appears in the learnings researcher's search scope list.

---

### 3. Modify `.github/prompts/cg-setup.prompt.md`

- **Files**: `.github/prompts/cg-setup.prompt.md` (MODIFY)
- **Details**:
  - **Mode A (A4)**: In the directory tree under `.cg-docs/solutions/`, add:
    ```
    ├── bugs/
    │   └── .gitkeep
    ```
    Insert in alphabetical order (after `build-errors/`, before `data-quality/`).
  - **Mode B (B1.5)**: In the list of directories to scaffold if missing, add:
    ```
    .cg-docs/solutions/bugs/
    ```
    Insert in alphabetical order (after `build-errors/`, before `data-quality/`).
- **Tests**: Grep for `bugs/` in the file after editing.
- **Acceptance criteria**: Both Mode A and Mode B scaffold `.cg-docs/solutions/bugs/`.

---

### 4. Modify `.github/skills/cg-skill-compound-docs/SKILL.md`

- **Files**: `.github/skills/cg-skill-compound-docs/SKILL.md` (MODIFY)
- **Details**:
  - In the **Categories** table, add a new row:
    ```
    | Bugs | `.cg-docs/solutions/bugs/` | Bug reproduction, diagnosis, fix verification |
    ```
    Insert in alphabetical order (after Build Errors, before Data Quality).
- **Tests**: Grep for `Bugs` in the table after editing.
- **Acceptance criteria**: `bugs` appears as a category in the skill's categories table.

---

### 5. Modify `.github/prompts/cg-review.prompt.md`

- **Files**: `.github/prompts/cg-review.prompt.md` (MODIFY)
- **Details**:
  - In **Step 5 (Summary)**, in the `### Next Steps` block, add a new bullet:
    ```
    - If this review surfaced a bug that was fixed: Run `/cg-fixbug` to document it with a verified test
    ```
    Insert after the existing "Run `/cg-compound`" bullet and before the "Ready to merge" bullet.
- **Tests**: Grep for `cg-fixbug` in the file after editing.
- **Acceptance criteria**: The review summary mentions `/cg-fixbug` as a follow-up option.

---

### 6. Modify `docs/workflow.md`

- **Files**: `docs/workflow.md` (MODIFY)
- **Details**:
  - In the **Loop** diagram, update to show Fix Bug as an optional side-branch:
    ```
    Brainstorm → Plan → Work → Review → Compound
              ↑               ↗
           Resume       Fix Bug  (enter at any stage when a bug is found)
    ```
  - Add a new section **between** Work (section 3) and Review (section 4), renumbering Review to 5, Compound to 6, and Resume to 7:

    ```markdown
    ### 4. Fix Bug (`/cg-fixbug`)

    **When**: After identifying a bug — during work, review, or standalone.

    **What happens**: The prompt walks through five steps: intake (describe the bug and search past bugs), reproduce (write a failing test — hard stop until confirmed), diagnose (root-cause hypothesis), fix (implement and verify — hard stop until confirmed), and document (write a verified bug report).

    **Output**: `.cg-docs/solutions/bugs/YYYY-MM-DD-<title>.md`
    ```
  - Update the existing section numbers (Review becomes 5, Compound becomes 6, Resume becomes 7).
- **Tests**: Visual inspection of rendered markdown; grep for `/cg-fixbug` after editing.
- **Acceptance criteria**: `/cg-fixbug` has its own section between Work and Review, section numbers are consistent.

---

### 7. Modify `docs/reference.md`

- **Files**: `docs/reference.md` (MODIFY)
- **Details**:
  - In the **Copilot Chat Prompts** table, add a new row:
    ```
    | `/cg-fixbug` | Claude Sonnet 4.6 | Structured bug-fix: reproduce, diagnose, fix, verify, document |
    ```
    Insert in alphabetical order (after `/cg-compound`, before `/cg-plan`).
  - In the **Directory Structure** section, add `bugs/` to the solutions tree:
    ```
    ├── bugs/
    ```
    Insert in alphabetical order (after `build-errors/`, before `data-quality/`).
- **Tests**: Grep for `cg-fixbug` and `bugs/` after editing.
- **Acceptance criteria**: `/cg-fixbug` appears in the prompts table and `bugs/` appears in the directory tree.

---

### 8. Modify `.github/copilot-instructions.md`

- **Files**: `.github/copilot-instructions.md` (MODIFY)
- **Details**:
  - In the **Knowledge Compounding** section, add `bugs` to the categories list. Current text:
    ```
    Categories: `build-errors`, `performance-issues`, `testing-patterns`, `data-quality`, `environment-issues`, `git-workflows`.
    ```
    Change to:
    ```
    Categories: `bugs`, `build-errors`, `data-quality`, `environment-issues`, `git-workflows`, `performance-issues`, `testing-patterns`.
    ```
    (Alphabetized and with `bugs` added.)
- **Tests**: Grep for `bugs` in the Knowledge Compounding section after editing.
- **Acceptance criteria**: `bugs` is listed as a category in the copilot-instructions Knowledge Compounding section.

---

## Testing Strategy

This feature is primarily prompt/documentation changes — no executable code is added. Testing is:

1. **Structural validation**: After all edits, run grep searches to confirm each keyword (`cg-fixbug`, `bugs/`) appears in the expected files.
2. **Manual walkthrough**: Invoke `/cg-fixbug` in Copilot Chat and confirm:
   - Step 1 asks for symptom description and searches past bugs.
   - Step 2 writes a test and stops (does not proceed without user confirmation).
   - Step 3 states a root-cause hypothesis and asks for confirmation.
   - Step 4 implements a fix and stops (does not proceed without user confirmation).
   - Step 5 writes a bug document with all required fields set to `"yes"`.
3. **Integration check**: Run `/cg-setup` on a test project and verify `.cg-docs/solutions/bugs/` is scaffolded.
4. **Learnings researcher check**: Invoke `@cg-learnings-researcher` and confirm it searches `bugs/`.

## Documentation Checklist

- [x] Prompt file has YAML frontmatter with description and model
- [ ] `docs/workflow.md` has a section for `/cg-fixbug`
- [ ] `docs/reference.md` lists `/cg-fixbug` in the prompts table
- [ ] Category `bugs` documented in `cg-skill-compound-docs` SKILL.md
- [ ] `copilot-instructions.md` lists `bugs` category
- [ ] Bug document schema documented inside the prompt file itself

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Hard stops ignored by model | Bug document written without verification | Explicit capitalized instructions ("Do NOT proceed") + schema rules enforcing `test-written: "yes"` |
| Section renumbering in `workflow.md` breaks existing links | Broken anchors if other docs link to `#4-review-cg-review` | Grep for anchor references before renumbering; update any found |
| `cg-setup` scaffolding change not picked up by existing projects | Existing projects won't have `bugs/` directory | Mode B (B1.5) explicitly adds missing directories — no action needed for existing projects once they re-run `/cg-setup` |
| Conflict with `cg-compound` flow | User confused about when to use `/cg-fixbug` vs `/cg-compound` | Clear differentiation in docs: `/cg-fixbug` = structured bug arc with test gates; `/cg-compound` = general knowledge capture |

## Out of Scope

- Automated bug detection/triage (this prompt is user-initiated).
- Changes to review agents to automatically detect bugs.
- Severity auto-classification (user/prompt assigns severity manually).
- Integration with GitHub Issues or other external trackers.
- New Pester tests for scaffolding (existing `install.Tests.ps1` / `link.Tests.ps1` cover directory structure; `bugs/` follows the same pattern).
