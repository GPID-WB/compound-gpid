---
date: 2026-04-10
title: "@cg-fix-problems agent and /cg-fix-problems prompt"
status: completed
completed-date: 2026-04-13
scope: "Standard"
brainstorm: ".cg-docs/brainstorms/2026-04-10-fix-problems-agent-and-prompt.md"
language: "both"
estimated-effort: "medium"
tags: [quality-loop, diagnostics, auto-fix, agent, prompt, cg-work]
---

# Plan: @cg-fix-problems Agent and /cg-fix-problems Prompt

## Objective

Create a dual-mode problem fixer for VS Code diagnostics (syntax errors, lint
warnings, type errors, test failures, runtime errors). The agent supports
auto mode (dispatched silently by `/cg-work`) and interactive mode (standalone
`/cg-fix-problems` prompt). Closes the "auto-fix diagnostics" gap in the
Quality Loop milestone.

## Context

- `/cg-fixbug` handles user-reported bugs with a reproduce → diagnose → fix arc
- `/cg-fix-triage` applies findings from `.cg-docs/reviews/` reports
- Neither handles VS Code Problems panel diagnostics or test failures mid-step
- Brainstorm decided: Approach 1 (single agent + prompt wrapper), 2-round
  per-round retry budget, errors-only in auto mode, hybrid discovery in
  interactive mode

## Requirements

| ID  | Requirement                                                   | Source     |
|-----|---------------------------------------------------------------|------------|
| R1  | Agent supports two modes: auto (dispatched by /cg-work) and interactive (standalone) | brainstorm |
| R2  | Auto mode: scope limited to files touched by current /cg-work step | brainstorm |
| R3  | Auto mode: fix errors only (not warnings or info)             | brainstorm |
| R4  | Auto mode: 2-round budget (fix → verify → fix → verify → stop) | brainstorm |
| R5  | Auto mode: skip unfixed problems and notify user, then continue | brainstorm |
| R6  | Auto mode: no user confirmation before fixing                 | brainstorm |
| R7  | Interactive mode: scan all files via get_errors, show user what's found | brainstorm |
| R8  | Interactive mode: user selects scope (all, by file, by severity) before fixes | brainstorm |
| R9  | Interactive mode: all severity levels (errors, warnings, info) | brainstorm |
| R10 | Agent uses Sonnet tier (both modes need code reasoning)       | model-guide |
| R11 | Agent is NOT user-invocable (dispatched only by prompt/cg-work) | architecture |
| R12 | Prompt is user-invocable, registered in Workflow Entry Points | architecture |
| R13 | /cg-work Step 2 auto-dispatches agent after test/validate failures | brainstorm |
| R14 | Tests cover both new files in prompt-tools.Tests.ps1          | testing |
| R15 | Count sentinels in model-assignments.Tests.ps1 updated        | testing |
| R16 | Registration in copilot-instructions.md and docs/reference.md | docs |

## Implementation Steps

### 1. Create `@cg-fix-problems` agent

- **Requirements**: R1, R2, R3, R4, R5, R6, R7, R8, R9, R10, R11
- **Files**: `.github/agents/cg-fix-problems.agent.md` (new)
- **Details**:
  - Frontmatter: `model: Claude Sonnet 4.6 (copilot)`, `tools: ['read', 'search', 'editFiles', 'terminalLastCommand']`, `user-invocable: false`
  - Two-section structure:
    - **Auto Mode Protocol**: Check errors via `get_errors` for scoped files only.
      Classify by severity. Fix errors only. Round 1: apply fixes → re-check.
      Round 2: apply fixes for remaining + newly introduced → re-check.
      After round 2: report unfixed problems as a bulleted list and return
      control to caller.
    - **Interactive Mode Protocol**: Scan all files via `get_errors`. Present
      summary table (file, severity, message, count). Ask user to select scope
      (all / by file / by severity). Fix selected problems. Verify each fix.
      Report results.
  - Language-aware: load appropriate skills based on file types (R → r skills,
    Python → python skill, Stata → stata skill, PowerShell → pester safety)
  - Safety: never modify files outside user's workspace, never auto-fix if the
    fix changes function signatures or public APIs without flagging
- **Test Scenarios**:
  - ✅ Agent file exists with correct frontmatter
  - ✅ Agent has `user-invocable: false`
  - ✅ Agent references `get_errors` or equivalent diagnostics tool
  - ✅ Agent documents 2-round retry protocol
  - ✅ Agent documents errors-only filter for auto mode
  - 🛑 Agent tools list includes editFiles (required for applying fixes)
- **Acceptance criteria**: Agent file passes frontmatter and tool restriction tests

### 2. Create `/cg-fix-problems` prompt

- **Requirements**: R7, R8, R9, R12
- **Files**: `.github/prompts/cg-fix-problems.prompt.md` (new)
- **Details**:
  - Frontmatter: `description:` and `model: Claude Sonnet 4.6 (copilot)`, NO `tools:` key
    (orchestrating prompts must not have tool restrictions — learned from cg-review lesson)
  - Step 0: Get Bearings (standard charter/config read — same boilerplate as other prompts)
  - Step 1: Scan Problems — call `get_errors` for all workspace files. Classify
    diagnostics by severity (error/warning/info) and group by file.
  - Step 2: Present Summary — show table: file | errors | warnings | info.
    Ask user to select scope: "Fix all", "Fix errors only", "Fix specific files",
    or "Fix specific severities".
  - Step 3: Dispatch — dispatch `@cg-fix-problems` in interactive mode with the
    user's scope selection.
  - Step 4: Report — summarize what was fixed, what remains, suggest next steps
    (`/cg-review` if clean, or re-run `/cg-fix-problems` for remaining items).
  - Handoff options: `/cg-review`, `/cg-work`, `/cg-fix-problems` again
- **Test Scenarios**:
  - ✅ Prompt file exists
  - ✅ Prompt has required frontmatter (description, model)
  - ✅ Prompt does NOT have tools: key
  - ✅ Prompt references @cg-fix-problems agent
  - ✅ Prompt references get_errors or diagnostics scanning
  - 🛑 Prompt with tools: restriction would break write access
- **Acceptance criteria**: Prompt file passes all frontmatter and content tests

### 3. Modify `/cg-work` to auto-dispatch after failures

- **Requirements**: R1, R2, R3, R4, R5, R6, R13
- **Files**: `.github/prompts/cg-work.prompt.md` (modify)
- **Details**:
  - Add a new sub-step after Step 2.4 (Test/Validate):
    **Step 2.4.1: Auto-Fix Diagnostics**
    - If tests fail or `get_errors` returns errors in files touched by this step:
      1. Dispatch `@cg-fix-problems` in auto mode with the list of touched files.
      2. After agent returns, re-run the failed tests.
      3. If errors remain, report: "Auto-fix resolved N of M errors. Remaining
         errors require manual attention:" followed by the unfixed list.
         Then ask the user: "Continue to next step, or stop to fix manually?"
    - If no errors: proceed to Step 2.5 normally.
  - Do NOT dispatch for warnings-only or info-only — auto mode is errors-only
  - Add `@cg-fix-problems` to the comment block at the top of cg-work that
    lists dispatched agents (if such a comment block exists)
- **Test Scenarios**:
  - ✅ cg-work.prompt.md references @cg-fix-problems
  - ✅ cg-work.prompt.md documents the 2-round retry budget
  - ✅ cg-work.prompt.md documents errors-only scope for auto mode
  - 🛑 Auto mode dispatches for warnings (should not)
- **Acceptance criteria**: cg-work references auto-dispatch and documents the protocol

### 4. Add tests

- **Requirements**: R14, R15
- **Files**: `tests/prompt-tools.Tests.ps1` (modify), `tests/model-assignments.Tests.ps1` (modify)
- **Details**:
  - In `prompt-tools.Tests.ps1`, add:
    - `cg-fix-problems.prompt.md - file existence` Describe block
    - `cg-fix-problems.prompt.md - frontmatter` Describe block (description, model)
    - `cg-fix-problems.prompt.md - no tool restriction` Describe block
    - `cg-fix-problems.prompt.md - dispatches @cg-fix-problems` content test
    - `cg-fix-problems.agent.md - user-invocable false` test
    - `cg-fix-problems.agent.md - auto mode protocol` content tests (2-round, errors-only)
    - `copilot-instructions.md - Workflow Entry Points` — add `/cg-fix-problems` assertion
    - `cg-work.prompt.md - auto-dispatch @cg-fix-problems` content test
  - In `model-assignments.Tests.ps1`:
    - Update prompt count sentinel from 15 → 16
    - Update agent count sentinel from 11 → 12
  - In `docs/model-guide.md`:
    - Add `cg-fix-problems.prompt.md` row to the Prompts table
    - Add `cg-fix-problems.agent.md` row to the Agents table
- **Test Scenarios**:
  - ✅ All new tests pass
  - ✅ Existing tests still pass (no regressions)
  - 🛑 Sentinel counts not updated → model-assignments tests fail
- **Acceptance criteria**: Full test suite passes (`. tests\Run-Tests.ps1`)

### 5. Register in documentation

- **Requirements**: R16
- **Files**: `.github/copilot-instructions.md` (modify), `docs/reference.md` (modify),
  `docs/model-guide.md` (modify)
- **Details**:
  - `copilot-instructions.md` Workflow Entry Points table: add row
    `| Fix VS Code problems | /cg-fix-problems |`
  - `docs/reference.md` Copilot Chat Prompts table: add `/cg-fix-problems` row
    with model, purpose description
  - `docs/reference.md` Review Agents note: no change needed (agent is not a
    review agent—it's dispatched by `/cg-work` and `/cg-fix-problems`)
  - `docs/model-guide.md` Prompts table: add row for `cg-fix-problems.prompt.md`
    with Sonnet tier, rationale
  - `docs/model-guide.md` Agents table: add row for `cg-fix-problems.agent.md`
    with Sonnet tier, rationale
  - `AGENTS.md` (if it exists at `.github/agents/`): verify auto-discovery
    will pick up the new agent file
- **Test Scenarios**:
  - ✅ Workflow Entry Points test passes for /cg-fix-problems
  - ✅ model-guide.md sync tests pass (file stems referenced)
- **Acceptance criteria**: All docs updated, all tests pass

## Testing Strategy

- **Structural tests** (Pester): file existence, frontmatter validation, tool
  restrictions, content assertions, count sentinels, cross-reference validation
- **Full suite**: run `. tests\Run-Tests.ps1` after all steps
- **Manual smoke test**: invoke `/cg-fix-problems` standalone with a deliberately
  broken file to verify the interactive flow works end-to-end

## Documentation Checklist

- [ ] Agent file has clear mode documentation (auto vs interactive)
- [ ] Prompt file has Step-by-step process documentation
- [ ] copilot-instructions.md Workflow Entry Points updated
- [ ] docs/reference.md prompt table updated
- [ ] docs/model-guide.md tables updated with tier rationale

## Risks & Mitigations

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Agent `tools:` list doesn't include the right tool names for editing files | Medium | Check existing agents that edit files (none currently — review agents are read-only). May need to omit `tools:` restriction entirely if tool names are unreliable, like the cg-review lesson taught. Test empirically. |
| Auto mode in `/cg-work` creates infinite loops if fix introduces new errors | Low | Hard 2-round cap. After round 2, stop unconditionally. |
| `get_errors` tool returns too many diagnostics for large projects | Low | In auto mode, scope to touched files only. In interactive mode, group by file and let user filter. |

## Out of Scope

- Per-step test enforcement (separate roadmap feature: `per-step-test-enforcement-in-cg-work`)
- Modifying `/cg-fixbug` or `/cg-fix-triage`
- Runtime debugging / stepping through code
- Auto-fixing problems in files the user didn't touch (in auto mode)
- Modifying the agent dispatch mechanism for other prompts beyond `/cg-work`
