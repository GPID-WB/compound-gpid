---
date: 2026-05-06
title: "Roadmap visualization — hidden agent + /cg-roadmap-view prompt"
status: completed
completed-date: 2026-05-06
scope: "Standard"
brainstorm: ".cg-docs/brainstorms/2026-05-06-roadmap-visualization.md"
language: "both"
estimated-effort: "medium"
tags: [roadmap, visualization, agent, prompt, ux, workflow-maturity]
phases: 3
completed-phases: [1, 2, 3]
---

# Plan: Roadmap Visualization — Hidden Agent + /cg-roadmap-view Prompt

## Objective

Create a fast, zero-dependency roadmap visualization system with two components:
a hidden read-only agent (`cg-roadmap-view.agent.md`) that handles all rendering
logic, and a thin user-facing prompt (`cg-roadmap-view.prompt.md`) that parses
flags and dispatches the agent. The agent is reusable by other prompts/agents
internally for contextual roadmap display.

## Context

- `roadmap.json` is the single source of truth for project progress (9 milestones, ~57 features)
- `@cg-roadmap` already exists as the write-only agent — this creates the read-only counterpart
- Pattern precedent: `cg-release-scanner` and `cg-project-scanner` are both hidden agents dispatched by prompts
- Output format: Markdown tables + emoji badges rendered in Copilot chat (Example 1 from brainstorm)
- Fuzzy matching: LLM-based (not algorithmic) — acceptable since the agent reads full JSON

## Requirements

| ID  | Requirement                                      | Source     |
|-----|--------------------------------------------------|------------|
| R1  | Summary table view (default): all milestones, status badges, done/total | brainstorm |
| R2  | `--milestone <name>`: single milestone with objective, progress, feature list | brainstorm |
| R3  | `--tasks`: all milestones with feature lists and statuses | brainstorm |
| R4  | `--tasks <name>`: features in one milestone | brainstorm |
| R5  | `--detail <name>`: feature description, status, linked plan path | brainstorm |
| R6  | `--detail <name> --plan`: feature detail + reads and summarizes linked plan | brainstorm |
| R7  | `--status <status>`: filter features across all milestones by status | brainstorm |
| R8  | `--wip`: shortcut for in-progress milestones with features | brainstorm |
| R9  | Fuzzy matching on milestone/feature names (not exact IDs required) | brainstorm |
| R10 | Agent is hidden (`user-invocable: false`) and read-only (`tools: ['read']`) | brainstorm |
| R11 | Agent uses Haiku model for speed | brainstorm |
| R12 | Internal dispatch from `/cg-resume`, `/cg-plan`, `/cg-brainstorm`, `/cg-strategy` | brainstorm |
| R13 | Prompt provides `--help` flag showing available options | user |

## Phase 1: Core Agent + Prompt

### 1. Create `cg-roadmap-view.agent.md`

- **Requirements**: R1–R11
- **Files**: `.github/agents/cg-roadmap-view.agent.md` (new)
- **Details**:
  - Frontmatter: `user-invocable: false`, `model: Claude Haiku 4.5 (copilot)`, `tools: ['read']`
  - Description: "Read-only roadmap renderer. Dispatched by /cg-roadmap-view and other prompts for contextual roadmap display. Never modifies files."
  - Sections:
    - **Inputs**: Describe what the dispatching prompt/agent passes (view mode, filter arguments)
    - **Views**: Define each view mode with exact Markdown output templates
    - **Fuzzy Matching Rules**: How to match user-provided names to milestone/feature IDs
    - **Output Format**: Prescriptive templates (tables, badges, progress indicators)
  - View templates (embed exact output format for each view mode):
    - Summary: `| Milestone | Status | Progress |` table with emoji badges
    - Milestone detail: objective, progress bar (text-based), feature list with icons
    - Task list: nested under each milestone
    - Feature detail: all fields from JSON + plan path
    - Status filter: grouped by milestone
    - WIP: subset of tasks view filtered to in-progress milestones
- **Test Scenarios**:
  - ✅ Agent file has correct frontmatter (user-invocable: false, tools: ['read'], Haiku model)
  - ✅ Agent file contains all view mode templates
  - 🛑 Agent file does NOT have write tools
  - ❌ Agent file is not referenced in prompt files incorrectly
- **Acceptance criteria**: Agent file exists with correct frontmatter and all view templates documented

### 2. Create `cg-roadmap-view.prompt.md`

- **Requirements**: R1–R9, R12, R13
- **Files**: `.github/prompts/cg-roadmap-view.prompt.md` (new)
- **Details**:
  - Frontmatter: `description` explaining the prompt's purpose, no `tools:` restriction (it dispatches the agent via subagent)
  - Sections:
    - **Usage**: Document all flags with examples
    - **Process**:
      1. Parse user arguments (flags + optional name)
      2. If `--help`: display usage guide and stop
      3. Read `roadmap.json` — if missing, tell user to create one via `@cg-roadmap`
      4. Dispatch `@cg-roadmap-view` agent with the parsed view mode and arguments
      5. Present the agent's output to the user
    - **Flag Reference**: Table of all flags, what they do, examples
  - The prompt is thin — it just maps flags to agent dispatch instructions
- **Test Scenarios**:
  - ✅ Prompt file exists with valid frontmatter
  - ✅ Prompt file does NOT have a `tools:` key (orchestrator pattern)
  - ✅ Prompt references `@cg-roadmap-view` agent
  - ✅ Prompt documents all flags (--milestone, --tasks, --detail, --plan, --status, --wip, --help)
  - 🛑 Prompt does NOT have `user-invocable: false`
- **Acceptance criteria**: Prompt file exists, references the agent, documents all flags

## Phase 2: Integration with Existing Prompts

### 3. Add dispatch instructions to `/cg-resume`

- **Requirements**: R12
- **Files**: `.github/prompts/cg-resume.prompt.md` (modify)
- **Details**:
  - In the step where `/cg-resume` shows current project state, add:
    "Dispatch `@cg-roadmap-view` with `--wip` to show the user which milestones and features are in progress."
  - This replaces any manual roadmap.json reading for display purposes
- **Test Scenarios**:
  - ✅ cg-resume.prompt.md mentions @cg-roadmap-view
- **Acceptance criteria**: `/cg-resume` dispatches the view agent for status display

### 4. Add dispatch instructions to `/cg-brainstorm`

- **Requirements**: R12
- **Files**: `.github/prompts/cg-brainstorm.prompt.md` (modify)
- **Details**:
  - In Step 5b (Roadmap Registration), before showing milestones for the user to choose from, add:
    "Dispatch `@cg-roadmap-view` with summary view (no flags) to show the user current milestones."
- **Test Scenarios**:
  - ✅ cg-brainstorm.prompt.md mentions @cg-roadmap-view in Step 5b
- **Acceptance criteria**: `/cg-brainstorm` dispatches the view agent when showing milestone options

### 5. Add dispatch instructions to `/cg-plan`

- **Requirements**: R12
- **Files**: `.github/prompts/cg-plan.prompt.md` (modify)
- **Details**:
  - In Step 5 (Register in Roadmap), when showing existing milestones to the user, add:
    "Dispatch `@cg-roadmap-view` with summary view to show current milestones."
- **Test Scenarios**:
  - ✅ cg-plan.prompt.md mentions @cg-roadmap-view in Step 5
- **Acceptance criteria**: `/cg-plan` dispatches the view agent when showing milestone options

### 6. Add dispatch instructions to `/cg-strategy`

- **Requirements**: R12
- **Files**: `.github/prompts/cg-strategy.prompt.md` (modify)
- **Details**:
  - In Step 0 or the strategy context display, add:
    "Dispatch `@cg-roadmap-view` with `--tasks` view to show the user a full picture of roadmap state."
- **Test Scenarios**:
  - ✅ cg-strategy.prompt.md mentions @cg-roadmap-view
- **Acceptance criteria**: `/cg-strategy` dispatches the view agent for context display

## Phase 3: Tests and Polish

### 7. Pester tests for agent structure

- **Requirements**: R10, R11
- **Files**: `tests/prompt-tools.Tests.ps1` (modify — add new Describe blocks)
- **Details**:
  - Test that `cg-roadmap-view.agent.md` exists
  - Test frontmatter: `user-invocable: false`
  - Test frontmatter: `tools:` includes only `read` (no write)
  - Test frontmatter: `model:` is Haiku
  - Test body contains view mode documentation (summary, milestone, tasks, detail, status, wip)
- **Acceptance criteria**: All structural tests pass

### 8. Pester tests for prompt structure

- **Requirements**: R13
- **Files**: `tests/prompt-tools.Tests.ps1` (modify — add new Describe blocks)
- **Details**:
  - Test that `cg-roadmap-view.prompt.md` exists
  - Test that it does NOT have a `tools:` key
  - Test that it references `@cg-roadmap-view`
  - Test that it documents flags: `--milestone`, `--tasks`, `--detail`, `--plan`, `--status`, `--wip`, `--help`
- **Acceptance criteria**: All structural tests pass

### 9. Clean up demo files

- **Requirements**: N/A (housekeeping)
- **Files**: `_examples/` directory (delete)
- **Details**: Remove the `_examples/roadmap-mermaid.md` and `_examples/roadmap-dashboard.html` files created during brainstorming — they were demos, not deliverables
- **Acceptance criteria**: `_examples/` directory removed

## Testing Strategy

- **Structural tests** (Pester): Verify agent frontmatter (model, tools, user-invocable), prompt structure (no tools key, flag documentation, agent reference), integration references in modified prompts
- **No behavioral tests**: The agent's rendering is LLM-generated — cannot be deterministically tested. Trust the prescriptive templates in the agent file.
- **Pattern**: Follow existing `prompt-tools.Tests.ps1` convention — `Describe` block per file, `It` assertions on content matching

## Documentation Checklist

- [x] Agent file is self-documenting (view templates serve as both instructions and documentation)
- [x] Prompt file includes `--help` flag output as inline documentation
- [x] `docs/reference.md` updated with `/cg-roadmap-view` entry
- [x] No README changes needed (plugin-internal feature)

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Large roadmaps (100+ features) slow Haiku rendering | Medium | Agent instructions tell it to collapse done milestones to one-line summaries when total features > 50 |
| Fuzzy matching ambiguity (multiple milestones match) | Low | Agent instructions say: if multiple matches, list them and ask user to clarify |
| Integration changes break existing prompt tests | Low | Run full test suite after each prompt modification |
| Model doesn't follow prescriptive templates precisely | Low | Templates are explicit Markdown — Haiku follows these well; iterate on template wording if needed |

## Out of Scope

- Auto-generating `ROADMAP.md` from `roadmap.json` (separate follow-up task)
- Interactive filtering (e.g., "show me features added this month")
- Terminal/HTML/Mermaid output modes (stick to chat Markdown)
- Python dependency for rich rendering
- Algorithmic fuzzy matching (LLM handles it)
