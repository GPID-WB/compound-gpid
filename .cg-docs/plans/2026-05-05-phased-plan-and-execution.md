---
date: 2026-05-05
title: "Phased plan structure and phased execution"
status: completed
completed-date: 2026-05-05
scope: Standard
brainstorm: ".cg-docs/brainstorms/2026-05-05-phased-plan-and-execution.md"
language: "both"
estimated-effort: medium
tags: [workflow, cg-plan, cg-work, phased-execution, cross-session]
---

# Plan: Phased Plan Structure and Phased Execution

## Objective

Add phase-awareness to `/cg-plan` (output phased plans) and `/cg-work` (execute by phase, track progress in frontmatter) so that large plans can be broken into phases, executed across sessions, and inspected at checkpoints — while preserving 100% backward compatibility with non-phased plans.

## Context

The brainstorm (`.cg-docs/brainstorms/2026-05-05-phased-plan-and-execution.md`) decided on Approach 1: Unified Prompt Modification. Both features are already registered in `roadmap.json` under the `workflow-maturity` milestone as `phased-plan-structure` and `phased-execution-cg-work`.

Current state:
- `/cg-plan` already recommends "organizing steps into numbered phases" for Deep scope (Step 1.5) but provides no structured format or frontmatter support.
- `/cg-work` executes all steps sequentially with no phase boundary concept.
- Plan frontmatter currently supports: `status`, `completed-date`, `failing-steps`.

## Requirements

| ID   | Requirement                                          | Source     |
|------|------------------------------------------------------|------------|
| R1   | `/cg-plan` asks about phase breakdown for Deep plans (recommend for Standard) | brainstorm |
| R2   | Plan output uses `## Phase N: <title>` wrapper sections | brainstorm |
| R3   | Plan frontmatter includes `phases: N` as convenience hint (authoritative count derived from `## Phase` headers) | brainstorm + review P3.1 |
| R4   | `/cg-work` parses optional `phaseX` argument (accepted forms: `phase1`, `phase 1`, `Phase 1` — case-insensitive, space-tolerant) | brainstorm + review P3.2 |
| R5   | Phase-scoped execution: only steps in that phase run (membership = `### N.` headings between `## Phase K:` and next `## Phase` or end-of-document) | brainstorm + review P2.1 |
| R6   | Frontmatter tracking: `completed-phases: []`, `current-phase: N` | brainstorm |
| R7   | Phase boundary: commit checkpoint → summary → offer continue/stop. Suppress the per-step commit (Step 2.6) for the final step of a phase — Step 2.5 subsumes it | brainstorm + review P1.1 |
| R8   | Non-phased plans run identically to current behavior | brainstorm |
| R9   | Out-of-bounds phase → error with phase list and status | brainstorm |
| R10  | Phase skip → error, suggest next phase or `/cg-plan-review` | brainstorm |
| R11  | `/cg-work` with no phase arg on a phased plan: skip phases already in `completed-phases`, start from first incomplete phase | brainstorm + review P1.2 |
| R12  | File permissions updated to allow `completed-phases` and `current-phase` writes | brainstorm |
| R13  | Plan file remains `status: active` when user stops at a phase boundary. `/cg-resume` distinguishes "paused between phases" from "never started" by checking `completed-phases` list | review P2.3 |

## Implementation Steps

### 1. Add Phase Structure step to `/cg-plan`

- **Requirements**: R1, R2, R3
- **Files**: `.github/prompts/cg-plan.prompt.md`
- **Details**:
  - Insert a new **Step 3.5: Phase Structure** (after Step 3 plan creation, before Step 4 save).
  - For **Deep** scope: "This plan has N steps. I recommend organizing them into phases. Do you have a phase breakdown in mind, or should I suggest one? (Last phase defaults to testing/validation/polish.)"
  - For **Standard** scope: "Would you like to organize this plan into phases for cross-session execution? (optional)"
  - For **Lightweight** scope: skip silently.
  - If user wants phases: restructure the Implementation Steps section into `## Phase N: <title>` wrapper sections. Steps retain global numbering (1, 2, 3... across phases).
  - Add `phases: N` to frontmatter (convenience hint — the authoritative phase count is always derived from `## Phase` headers in the document body).
  - Update the plan template in Step 3 to show the phased variant as an alternative format.
- **Test Scenarios**:
  - ✅ Plan output for Deep scope includes Phase sections and `phases:` in frontmatter
  - 🛑 Lightweight plan never triggers phase prompt
  - ❌ User declines phases → plan output has no Phase sections, no `phases:` field
- **Tests**: Add test in `prompt-tools.Tests.ps1`:
  - Assert `cg-plan.prompt.md` contains the string `Phase Structure`
  - Assert `cg-plan.prompt.md` contains `phases:` in its phased template example
- **Acceptance criteria**: `/cg-plan` prompt contains Step 3.5 with phase structure logic; phased template variant is documented in the plan body.

### 2. Add phased execution support to `/cg-work` (argument parsing, phase boundary, validation)

- **Requirements**: R4, R5, R6, R7, R8, R9, R10, R11, R12, R13
- **Files**: `.github/prompts/cg-work.prompt.md`
- **Details** (single coherent edit with three logical sections):

  #### 2a. Frontmatter and permissions
  - Update `description:` to: "Implement a plan step by step. Use after /plan has created an implementation plan. Supports `/cg-work [phaseX] [plan_file]`."
  - Update File Permissions bullet to: "You may modify the YAML frontmatter of the plan file currently being implemented (status, completed-date, failing-steps, completed-phases, and current-phase fields only)."

  #### 2b. Step 1.2: Parse Phase Argument (insert between Step 1 and Step 1.5)

  - **Argument parsing**: Parse user input for `phaseX` pattern. Accepted forms: `phase1`, `phase 1`, `Phase 1` (case-insensitive, strip spaces between "phase" and digit, normalize to integer).
  - **Plan type detection**: Scan plan body for `## Phase` headers. If found → phased plan. If none → non-phased plan.
  - **Phase membership rule**: A phase's steps are all `### N.` headings between `## Phase K:` and the next `## Phase` header (or end of document). Content above the first `## Phase` header is preamble (context/objective) — not executed as steps.
  - **Dispatch logic**:

    | Plan type | Argument | Behavior |
    |-----------|----------|----------|
    | Non-phased | none | Execute all steps (current behavior, unchanged) |
    | Non-phased | `phaseX` | Warn: "This plan has no phases. Executing all steps." Proceed as today |
    | Phased | none | Skip phases already in `completed-phases`; start from first incomplete phase; execute remaining phases sequentially (R11) |
    | Phased | `phaseX` | Scope Step 2 to only that phase's steps |

  - **Validation (before proceeding to Step 2)**:
    - **Out-of-bounds**: If requested phase > total phases (counted from `## Phase` headers — NOT from `phases:` frontmatter):
      > "Error: Plan has N phases. Phase X does not exist.
      > Available phases:
      > • Phase 1: \<title\> — ✅ completed
      > • Phase 2: \<title\> — 🔄 next
      > • Phase 3: \<title\> — ⬜ not started
      >
      > Suggested next: `/cg-work phase2`"
    - **Sequential enforcement**: If requested phase X but phase X-1 not in `completed-phases` (exception: phase 1 is always allowed):
      > "Error: Phase X cannot start — Phase X-1 is not yet completed.
      >
      > Suggested next: `/cg-work phaseX-1`
      > Or review the plan: `/cg-plan-review`"
    - Both errors halt execution (do not proceed to Step 2).

  #### 2c. Step 2.5: Phase Boundary (fires after all steps in a phase complete)

  - **Phase-terminal commit suppression** (R7): For the final step of a phase, skip the normal Step 2 sub-step 6 (per-step commit offer). Step 2.5 handles the commit for the entire phase instead. Non-terminal steps within a phase still get per-step commit offers as today.
  - **Phase boundary sequence**:
    1. Run full-suite test gate (same as current commit-gate pattern).
    2. Suggest commit message: `feat(scope): complete phase N — <phase title>`.
    3. Present phase completion summary (steps completed, files touched, tests passing).
    4. Update plan frontmatter: append phase number to `completed-phases`, set `current-phase` to N+1 (or remove `current-phase` if this was the final phase).
    5. Offer: "Phase N complete. **Continue to Phase N+1?** Or stop here and resume with `/cg-work phaseN+1`?"
    6. If user continues: proceed to next phase's steps.
    7. If user stops: halt gracefully. Plan remains `status: active` with `completed-phases` updated. Step 3 quality checks do NOT run (plan is incomplete).
  - **All-phases-complete**: When the final phase boundary fires (or the last phase in a no-arg sequential run finishes): proceed to existing Step 3 quality checks → Step 3.2 self-review → Step 3.5 mark complete → Step 3.7 roadmap update.
  - **Status progression**: Plan stays `status: active` throughout. Only transitions to `status: completed` after all phases finish and quality checks pass. A plan with non-empty `completed-phases` but `status: active` means "paused between phases" — this is the normal state for cross-session work (R13).

- **Test Scenarios**:
  - ✅ Non-phased plan: `/cg-work` runs all steps (unchanged behavior)
  - ✅ Phased plan + no arg + empty `completed-phases`: runs all phases from 1
  - ✅ Phased plan + no arg + `completed-phases: [1]`: starts from phase 2
  - ✅ Phased plan + `phase2` + phase 1 completed: runs only Phase 2 steps
  - ✅ Phase-terminal step: no per-step commit offer; phase boundary handles it
  - ✅ User stops at boundary: `status: active`, `completed-phases` updated
  - ✅ All phases done: `status: completed`, `completed-date` set
  - 🛑 Non-phased plan + `phase1`: warns, runs all steps
  - ❌ `/cg-work phase5` on 3-phase plan → out-of-bounds error with phase listing
  - ❌ `/cg-work phase3` when only phase 1 completed → sequential enforcement error
  - 🛑 Mid-phase failure: `failing-steps` still works within a phase
- **Tests**: Add tests in `prompt-tools.Tests.ps1` (enumerated in Step 4 below).
- **Acceptance criteria**: `/cg-work` prompt contains Step 1.2 (argument parsing + validation) and Step 2.5 (phase boundary) with all dispatch logic, error messages, and commit suppression rule.

### 3. Update `/cg-resume` to surface phase progress

- **Requirements**: R6, R13 (display side)
- **Files**: `.github/prompts/cg-resume.prompt.md`
- **Details**:
  - In Step 2a (In-progress plans), when reporting plans with `status: active`:
    - If plan has `completed-phases:` field (non-empty list): display "Phase progress: N/M phases completed. Next: `/cg-work phaseX`" (where M = count of `## Phase` headers or `phases:` hint, X = first phase not in completed list).
    - If plan has no `completed-phases:` field or it's empty: display as today (no phase info).
  - Small addition (~5 lines) to the existing scan logic.
- **Test Scenarios**:
  - ✅ Phased plan with `completed-phases: [1, 2]` → shows "Phase progress: 2/3 completed. Next: `/cg-work phase3`"
  - ✅ Non-phased plan → no phase info shown (backward compat)
  - ✅ Phased plan with empty `completed-phases: []` → shows "Phase progress: 0/3 completed. Next: `/cg-work phase1`"
- **Tests**: No new Pester test needed — resume output is runtime behavior.
- **Acceptance criteria**: `/cg-resume` prompt references `completed-phases` and displays phase progress for phased plans.

### 4. Add Pester tests for prompt structure

- **Requirements**: R2, R3, R4, R5, R6, R7, R8
- **Files**: `tests/prompt-tools.Tests.ps1`
- **Details** — specific assertions enumerated:

  **Block: "cg-plan.prompt.md - phase structure support"**
  - `$content -match 'Phase Structure'` — Step 3.5 exists
  - `$content -match 'phases:'` — phased frontmatter field documented
  - `$content -match '## Phase'` — phased format example present

  **Block: "cg-work.prompt.md - phased execution support"**
  - `$content -match 'Step 1\.2'` or `$content -match 'Parse Phase Argument'` — parsing step exists
  - `$content -match 'completed-phases'` — frontmatter tracking referenced
  - `$content -match 'current-phase'` — frontmatter tracking referenced
  - `$content -match 'Phase Boundary'` or `$content -match 'Step 2\.5'` — boundary step exists
  - `$content -match 'Phase X does not exist'` or equivalent — out-of-bounds error present
  - `$content -match 'Phase X cannot start'` or equivalent — sequential error present
  - `$content -match 'phase-terminal'` or `$content -match 'skip.*sub-step 6'` — commit suppression documented

  **Block: "cg-work.prompt.md - file permissions include phase fields"**
  - Extract File Permissions section; assert it contains `completed-phases` or `current-phase`

  **Limitations note**: These are structural presence tests — they verify the prompt contains the required sections and keywords. They cannot verify semantic correctness of the phase logic at runtime. This is the practical ceiling for prompt file testing (documented explicitly).

- **Test Scenarios**:
  - ✅ All assertions pass on correctly modified prompts
  - ❌ Missing keyword → test fails with descriptive "should contain X" message
- **Tests**: Self-referential — this step IS the tests.
- **Acceptance criteria**: All new Pester tests pass. Tests are specific enough that removing a phase-related section would cause at least one failure.

## Testing Strategy

- **Structural tests** (Pester): Verify prompt files contain required keywords, sections, and format patterns. Specific assertions enumerated in Step 4.
- **Limitation**: Structural tests verify presence, not semantic correctness. A test checking for `Phase Boundary` passes whether the boundary logic is correct or inverted. This is accepted as the practical ceiling for prompt file testing.
- **No functional tests needed**: Prompts are executed by Copilot at runtime, not by code we can unit-test.
- **Manual validation**: After implementation, use `/cg-plan` on a Deep-scope topic and verify phase output. Then use `/cg-work phase1` to verify phase-scoped execution.

## Documentation Checklist

- [ ] `/cg-plan` prompt contains phase structure documentation
- [ ] `/cg-work` prompt contains phase execution documentation
- [ ] Both prompts' internal comments explain the phased flow
- [ ] `docs/reference.md` updated with `/cg-work [phaseX] [plan_file]` syntax (if it documents invocation syntax)

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Phase-terminal commit suppression misapplied (wrong step identified as terminal) | Double commit or missing commit | Rule is explicit: "final step" = last `### N.` heading before next `## Phase` header or end-of-document. Deterministic from document structure |
| Long prompt file becomes unwieldy | Harder to maintain | Keep phase logic in clearly labeled, self-contained sections. Use HTML comments to delimit phase-related blocks |
| `/cg-resume` doesn't pick up new frontmatter fields | User doesn't know where they left off | Step 3 explicitly adds phase progress display |
| `phases:` frontmatter desyncs from actual `## Phase` headers after manual edit | Agent uses wrong phase count | R3+R5: authoritative count always derived from headers. `phases:` is a convenience hint only — documented as non-authoritative |

## Out of Scope

- Range syntax (`/cg-work phase2-3`) — decided against in brainstorm
- External state files — decided against
- Separate phase executor agent — decided against
- `/cg-plan-modify` prompt (referenced but not built here)
- Phase-aware `/cg-plan-review` (existing `/cg-plan-review` will work on phased plans without modification since it reviews the whole plan)
- New `paused` status value — `status: active` + non-empty `completed-phases` is sufficient to distinguish "paused" from "never started"

## Review Findings Addressed

| Finding | Resolution |
|---------|-----------|
| P1.1 — Double-commit on phase-terminal step | R7 updated: suppress per-step commit for final step of a phase; Step 2.5 subsumes it |
| P1.2 — No-arg re-runs completed phases | R11 updated: skip phases already in `completed-phases`, start from first incomplete |
| P2.1 — Phase membership parsing unspecified | R5 updated: explicit rule (headings between `## Phase K:` and next `## Phase` or EOF) |
| P2.2 — Three editing passes on same file | Steps 2-4 merged into single Step 2 with sub-sections 2a/2b/2c |
| P2.3 — Status undefined when user stops mid-phases | R13 added: stays `status: active`; `/cg-resume` uses `completed-phases` list to distinguish |
| P2.4 — Test assertions unmeasurable | Step 4 now enumerates every specific regex/string assertion |
| P3.1 — `phases: N` redundant | R3 updated: marked as convenience hint, headers are authoritative |
| P3.2 — `phaseX` pattern underspecified | R4 updated: `phase1`, `phase 1`, `Phase 1` all accepted; normalize by stripping spaces + lowercasing |
