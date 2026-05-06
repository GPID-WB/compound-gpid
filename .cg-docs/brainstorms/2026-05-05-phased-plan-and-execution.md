---
date: 2026-05-05
title: "Phased plan structure and phased execution in /cg-work"
status: decided
scope: "Standard"
chosen-approach: "Unified Prompt Modification"
tags: [workflow, cg-plan, cg-work, phased-execution, cross-session]
---

# Phased Plan Structure and Phased Execution

## Context

Large plans (8+ steps, Deep scope) cannot always be completed in a single Copilot session. The context window fills up, sessions crash, or the user needs to stop mid-way. Two roadmap features address this: "Phased plan structure in /cg-plan" and "Phased execution in /cg-work".

## Requirements

1. **Inspection checkpoints** — Allow the user to inspect progress after each phase and make adjustments (modify the plan with `/cg-plan-review` or a future `/cg-plan-modify`).
2. **Scalable decomposition** — Design larger plans as groups of phases, each a coherent "mini-plan."
3. **Cross-session resume** — Support `/cg-work phase2` in a new session so the user can pick up where they left off.
4. **Backward-compatible full execution** — `/cg-work` with no phase argument executes the entire plan sequentially (identical to current behavior).
5. **Compact plan format** — Phase completion tracked in frontmatter (`completed-phases`, `current-phase`). The agent reads the full plan and uses markers to know where to start — phases are NOT self-contained documents.
6. **No range syntax** — Single-phase addressing only (`/cg-work phase2`), no `/cg-work phase2-3`.
7. **Phase boundary behavior** — Commit checkpoint → summary → offer "Continue to phase N+1? Or stop here and resume with `/cg-work phaseN+1`."
8. **Non-phased backward compat** — Plans without `## Phase` sections run as today (single implicit phase).
9. **Phase out-of-bounds error** — Lists available phases with their status and suggests next `/cg-work phaseX`.
10. **Sequential enforcement** — Cannot skip phases. Error if phase N requested but N-1 not completed. Suggest the natural next phase or `/cg-plan-review`.

### Full invocation syntax

```
/cg-work [phaseX] [plan_file]
```

- `phaseX` — optional, 1-indexed. If omitted, execute all phases sequentially.
- `plan_file` — optional. Defaults to most recent plan in `.cg-docs/plans/`.

### Plan file format (phased)

```markdown
---
date: 2026-05-05
title: "Example phased plan"
status: active
scope: Deep
phases: 3
completed-phases: [1]
current-phase: 2
---

## Phase 1: Core Implementation
### 1. Step one...
### 2. Step two...

## Phase 2: Integration
### 3. Step three...
### 4. Step four...

## Phase 3: Testing & Polish
### 5. Step five...
### 6. Step six...
```

### /cg-plan changes

- Add "Step 2.5: Phase Structure" for Deep-scope plans (recommend for Standard, optional).
- Ask user if they have a phase breakdown in mind; if not, suggest one.
- Last phase defaults to testing/validation/polish unless user overrides.
- Output uses `## Phase N: <title>` wrapper sections around step groups.
- Frontmatter adds `phases: N` (integer count).

### /cg-work changes

- Argument parsing at Step 1 for `phaseX`.
- Phase-scoping: if `phaseX` specified, execute only steps within that phase.
- Track `completed-phases: [1, 2]` and `current-phase: 3` in plan frontmatter.
- At phase boundary: commit checkpoint → summary → offer continue or stop.
- Error handling: out-of-bounds → list phases. Skip → error + suggest next.

## Approaches Considered

### Approach 1: Unified Prompt Modification (chosen)

Modify `cg-plan.prompt.md` and `cg-work.prompt.md` in place. Phase awareness as conditional logic within the existing flow. Thin layer around the step loop.

**Pros**: Minimal new files. Keeps two-prompt architecture. Existing tests pass. `/cg-resume` naturally picks up `current-phase`.
**Cons**: Makes long prompts longer (~80 lines each).

### Approach 2: Separate Phase Executor Agent

New `@cg-phase-executor` agent dispatched per phase. `/cg-work` becomes orchestrator.

**Pros**: Smaller context per phase.
**Cons**: Latency, duplication, over-engineered.

### Approach 3: External State File

`.cg-docs/state/<plan>.json` for progress tracking instead of frontmatter.

**Pros**: Richer state, doesn't touch plan file.
**Cons**: Two sources of truth, extra complexity.

## Decision

Approach 1 — Unified Prompt Modification. Phase detection and frontmatter tracking as a thin layer around the existing step loop in `/cg-work`. Phase structure as an optional output format in `/cg-plan` (triggered for Deep scope, recommended for Standard).

## Next Steps

1. Modify `/cg-plan` — add Step 2.5 (Phase Structure) with phase-aware output template.
2. Modify `/cg-work` — add argument parsing, phase scoping, frontmatter tracking, phase-boundary checkpoint behavior, and error handling.
3. Update `/cg-resume` if needed to surface `current-phase` when resuming work.
4. Write Pester tests for the new frontmatter fields and plan format.
