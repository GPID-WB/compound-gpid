---
date: 2026-05-22
title: "Compound Research Phase 8: Integration Polish & Documentation"
status: completed
completed-date: 2026-05-22
scope: "Lightweight"
brainstorm: ".cg-docs/brainstorms/2026-05-13-compound-research-extension.md"
language: "Markdown, PowerShell"
estimated-effort: "small"
tags: [research, documentation, integration, compound-research, charter, README, polish]
---

# Plan: Compound Research Phase 8 — Integration Polish & Documentation

## Objective

Final integration pass for the compound-research milestone: update the project
charter's Current Focus (research module is now complete), add compound-research
to the README, add a Research Workflow section to `docs/workflow.md`, update
`docs/manual.md` to reference the research docs, and run a full test pass to
confirm everything is green before the branch is ready for merge.

## Context

Phases 1–7 of compound-research are complete and committed on the
`compound-research` branch (2,341/2,341 tests passing). All CR prompts,
agents, and skills are implemented and documented in `docs/reference.md`,
`docs/model-guide.md`, and `copilot-instructions.md`. What remains is
surface-level documentation that a user would encounter before reading the
reference — the README, the workflow guide, the manual TOC, and the charter
itself.

### What already exists (no work needed)
- `docs/reference.md` — complete: Research Workflow Prompts table, Research
  Agents table, all 12 CR skills listed
- `docs/model-guide.md` — complete: all 48 files documented with tier
  rationale
- `copilot-instructions.md` — complete: Compound Research (CR) Skills section
  with all 12 skills listed
- `copilot-instructions.template.md` — complete: `{{modules}}` substitution,
  module description

### What needs work
1. `compound-gpid.md` — Current Focus still says "starting with the module
   system foundation (Phase 1) and research workflow scaffolding (Phase 2)";
   needs update to reflect completion
2. `README.md` — no mention of compound-research, research module, or `/cr-*`
   commands
3. `docs/workflow.md` — no Research Workflow section; only covers `/cg-*` loop
4. `docs/manual.md` — no entry pointing to research workflow documentation
5. Full test pass — confirm 2,341+ tests still green after documentation edits

## Requirements

| ID  | Requirement                                              | Source            |
|-----|----------------------------------------------------------|-------------------|
| R1  | Update `compound-gpid.md` Current Focus to reflect that compound-research Phases 1–7 are complete | charter convention |
| R2  | Add compound-research mention to README.md Key Benefits and Documentation table | user-facing docs |
| R3  | Add Research Workflow section to `docs/workflow.md` covering the `/cr-*` loop | user-facing docs |
| R4  | Add Research Workflow entry to `docs/manual.md` page table | user-facing docs |
| R5  | Run full test pass to confirm everything passes | convention |

## Implementation Steps

### 1. Update Charter Current Focus
- **Requirements**: R1
- **Files**: `compound-gpid.md`
- **Details**: Replace the Current Focus text to reflect that compound-research
  Phases 1–7 are complete. The milestone still has a Phase 9 idea (dedicated
  Tables/Figures agent) but the core extension is done. Update `last-reviewed`
  frontmatter to today.
- **Acceptance criteria**: Current Focus reflects completion; `last-reviewed`
  is `2026-05-22`

### 2. Update README.md
- **Requirements**: R2
- **Files**: `README.md`
- **Details**:
  - Add a Key Benefit bullet for research module: opt-in `/cr-*` commands for
    economics research workflows (econometrics, ML, academic writing,
    replication packaging)
  - No changes to the Documentation table (workflow.md entry already exists)
- **Acceptance criteria**: README mentions research module and `/cr-*` commands

### 3. Add Research Workflow to docs/workflow.md
- **Requirements**: R3
- **Files**: `docs/workflow.md`
- **Details**: Add a `## Research Workflow` section after the existing Steps
  sections. Cover:
  - How to enable: `modules: "engineering, research"` in
    `compound-gpid.local.md` (or via `/cg-setup`)
  - The research loop: `/cr-brainstorm → /cr-plan → /cr-work → /cr-review →
    /cr-compound`
  - The 8 task types with brief descriptions
  - How research review differs from engineering review (shared `cg-*` agents
    plus task-type-specific `cr-*` agents)
  - Cross-reference to `docs/reference.md` for full tables
- **Acceptance criteria**: `docs/workflow.md` has a Research Workflow section
  that a new user can follow to enable and use `/cr-*` commands

### 4. Update docs/manual.md
- **Requirements**: R4
- **Files**: `docs/manual.md`
- **Details**: Add a row to the Pages table for the Research Workflow section
  (since it lives in workflow.md, this is an anchor link, not a new page).
  Update the "Quick orientation" section to mention `/cr-*` commands for
  research.
- **Acceptance criteria**: `docs/manual.md` mentions research workflow

### 5. Full Test Pass
- **Requirements**: R5
- **Details**: Run the full test suite via `. tests/Run-Tests.ps1`. Verify
  2,341+ tests pass, 0 failures.
- **Acceptance criteria**: All tests pass

## Testing Strategy

This is a documentation-only plan. Existing Pester tests already validate
prompt frontmatter, agent structure, skill content, and dispatch routing.
Step 5 confirms no regressions. No new tests needed — the documentation
changes don't affect testable contract surfaces.

## Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| Charter update requires user approval per convention | Ask before modifying `compound-gpid.md` body |

## Out of Scope

- Phase 9 (dedicated Tables/Figures agent) — separate future work
- `docs/context-files.md` — already covers the module system via the template
  description
- `docs/installation.md` — no changes needed (modules are configured post-install
  via `/cg-setup`)
- `docs/troubleshooting.md` — no research-specific troubleshooting needed yet
- New Pester tests — no testable contract surfaces introduced
