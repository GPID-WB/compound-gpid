---
date: 2026-04-14
title: "Honest pushback, plan review, side-idea capture, and schema bypass"
status: decided
scope: "Standard"
chosen-approach: "Full Layered Pushback"
tags: [quality-loop, brainstorm, plan, pushback, roadmap, schema, cg-resume]
---
<!-- Valid status values: decided, in-progress, abandoned -->

# Honest Pushback, Plan Review, Side-Idea Capture, and Schema Bypass

## Context

Four related items from the Quality Loop milestone need coordinated design:
three features (`honest-pushback-in-brainstorm-strategy`, `side-idea-capture-in-brainstorm`,
and a new plan-review feature) plus a bug fix in `/cg-resume` where the schema
check always reports outdated when running in the compound-gpid repo itself.

The user noted that pushback serves different purposes at different stages —
requirement validity during brainstorming vs. plan quality during planning — and
that the mechanism should differ accordingly.

## Requirements

### R1: Brainstorm pushback (inline, always-on)
- New Step 3.5 in `cg-brainstorm.prompt.md`, after approaches are proposed.
- Devil's advocate checklist: Is the problem real? Does a simpler solution exist?
  Is this worth building? Does any approach conflict with charter constraints?
- Unconditional — always runs, conversational tone.
- User can respond and refine; not a gate, a dialogue.
- NOT dispatched to `@cg-adversarial` — that agent is tuned for code-level
  attack vectors, not idea-level scrutiny.

### R2: Plan review (separate agent + prompt, opt-in)
- New agent `@cg-plan-critic` — structurally separate voice from the planner.
- New prompt `cg-plan-review.prompt.md` → `/cg-plan-review`.
- Can review existing plans (standalone) or be suggested at `/cg-plan` handoff.
- Reviews for: risks, over-engineering, unnecessary steps, flawed assumptions,
  missing edge cases, scope creep.
- `/cg-plan` handoff step adds suggestion: "Run `/cg-plan-review` to challenge
  this plan."
- Separate from Step 4.5 Confidence Check (which stays as-is for structural
  completeness validation).

### R3: Side-idea capture (organic + context-aware closing)
- **Mid-conversation (trigger 1)**: Instruction in pushback steps — if the user
  identifies an adjacent idea worth tracking, offer to dispatch `@cg-roadmap`.
- **Closing question (trigger 2)**: Context-aware, two variants:
  - No pushback exchange: "No adjacent ideas surfaced during this session. Want
    to add anything to the roadmap anyway?"
  - Had pushback exchange: "During pushback, we discussed [X, Y, Z]. These
    could be added as ideas to [milestone]. Want me to add any of them? Or
    capture a different idea?"
- Applies to both `/cg-brainstorm` Step 5 and `/cg-plan` Step 6.

### R4: Schema bypass in `/cg-resume`
- In Step 1 (Schema Version Check), before comparing versions: check if the
  workspace root contains a `SCHEMA_VERSION` file.
- If yes → this IS the compound-gpid repo → skip schema comparison, proceed
  silently.
- Detection based on file presence, NOT charter name matching (avoids false
  positives from projects named similarly).

## Approaches Considered

### Approach 1: Full Layered Pushback (Chosen)
Inline devil's advocate in brainstorm, dedicated agent + prompt for plan review,
organic + context-aware side-idea capture, file-based schema bypass.

| # | Change | Mechanism |
|---|--------|-----------|
| 1 | Brainstorm pushback | New Step 3.5 in `cg-brainstorm.prompt.md` |
| 2 | Plan review | New `@cg-plan-critic` agent + `cg-plan-review.prompt.md` |
| 3 | Side-idea capture | Mid-conversation instruction + context-aware closing question |
| 4 | Schema bypass | Guard in `cg-resume.prompt.md` Step 1 |

**Pros**: Each feature is independent and testable. Brainstorm pushback catches
requirement problems early. Plan review is opt-in. Side-idea capture is natural.
Structural separation between planner and critic makes review feel genuine.

**Cons**: Adds one prompt + one agent to the surface area. Users need to discover
`/cg-plan-review` (mitigated by handoff suggestion).

### Approach 2: Minimal — Inline Everything
Pushback in both brainstorm and plan as inline prompt logic, no new agent/prompt.

**Pros**: Zero surface area growth.

**Cons**: Plan review can't run independently on existing plans. Same voice for
planning and critique (less credible). No way to deepen review for Deep-scope plans.

## Decision

Approach 1 — Full Layered Pushback. The structural separation between planner
and critic is the key differentiator: the critic should not be the same voice as
the planner. The standalone `/cg-plan-review` prompt also solves the "review
yesterday's plan today" use case cleanly.

## Next Steps

1. Modify `cg-brainstorm.prompt.md` — add Step 3.5 (devil's advocate) and update
   Step 5 with side-idea capture (both organic and closing question).
2. Create `@cg-plan-critic` agent (`cg-plan-critic.agent.md`). Compare with
   `/create-agent` output side-by-side.
3. Create `cg-plan-review.prompt.md` — standalone plan review prompt that
   dispatches `@cg-plan-critic`.
4. Modify `cg-plan.prompt.md` — add `/cg-plan-review` suggestion in Step 6
   handoff + side-idea closing question.
5. Modify `cg-resume.prompt.md` — add `SCHEMA_VERSION` file guard in Step 1.
6. Update `roadmap.json` — link features, add plan-review feature.
7. Update `docs/reference.md` — document `/cg-plan-review`.
8. Update `copilot-instructions.md` — add `/cg-plan-review` to workflow table.
