---
date: 2026-06-12
title: "Goal-driven execution for /cg-plan and /cg-work"
status: decided
scope: "Deep"
chosen-approach: "Shared Contract + Thin Prompt Hooks"
tags: [workflow, cg-plan, cg-work, goal-driven-execution, validation, completion-contract]
---
<!-- Valid status values: decided, in-progress, abandoned -->

# Goal-Driven Execution for /cg-plan and /cg-work

## Context

The `workflow-maturity` roadmap feature `goal-driven-execution` should make
`/cg-plan` and `/cg-work` work like a Compound GPID-native version of Codex
Goals. `/cg-plan` should create a completion contract, and `/cg-work` should
execute against that contract until verified completion or a principled blocked
stop.

This feature must preserve existing phased plan behavior, safe Pester runner
rules, review routing behavior, and the recent prompt-slimming work for
`/cg-plan` and `/cg-work`.

## Requirements

1. `/cg-plan` produces a completion contract, not only an implementation
   checklist.
2. The contract defines outcome, verification surface, constraints, boundaries,
   iteration policy, blocked-stop condition, and deviation policy.
3. The contract is required for all saved plans, scaled down for Lightweight
   plans.
4. `/cg-plan` and `/cg-work` share the same deviation argument:
   `deviate:ask`, `deviate:auto`, and `deviate:strict`.
5. Default deviation behavior is `ask`. `deviate:auto` is accepted as a CLI
   shorthand but stored as `autonomous` in plan frontmatter.
6. `/cg-work` follows the plan's `deviation-policy` unless explicitly
   overridden at runtime.
7. Deviations must be durably recorded, not only mentioned in chat.
8. Execution reporting should use a separate artifact for accountability:
   the plan remains the contract, and the report records what was executed.
9. The plan may store minimal status metadata and a pointer to the execution
   report, but should not duplicate substantive report content.
10. Execution reports are created early and updated incrementally during work,
    then finalized at completion or blocked stop.
11. Completion uses a strict evidence gate: `/cg-work` may not mark work
    completed unless every required verification item has passing evidence or
    an explicit user-accepted exception.
12. Verification surface uses a table with stable IDs; the execution report
    mirrors those IDs with gathered evidence.
13. Constraints use checkable IDs in a table. Boundaries, iteration policy, and
    blocked-stop condition can remain concise bullets.
14. Phased plans use one authoritative whole-plan contract, with optional
    phase-level verification rows when useful.
15. Contract tables should be parsed by header name, not column position.
    Optional `Phase` columns are accepted for phased plans.
16. `/cg-plan` may generate default blocked-stop rules, but the user must see
    and approve the contract before the plan is written. Approving the plan is
    treated as approving the completion contract.
17. `/cg-review` remains available for adversarial or cross-model review but is
    no longer required as the default post-work step.

## Approaches Considered

### Approach 1: Inline Prompt Expansion

Add the full goal-contract behavior directly into `.github/prompts/cg-plan.prompt.md`
and `.github/prompts/cg-work.prompt.md`.

**Pros**: Simple file structure. Behavior is visible in the two workflow
prompts.

**Cons**: Bloats both prompts, duplicates schema and parser rules, and risks
undoing the recent prompt-slimming work.

### Approach 2: Shared Contract + Thin Prompt Hooks

Create a shared contract document, likely
`.github/shared/goal-execution.contract.md`, that defines the completion
contract schema, accepted table variants, deviation semantics, execution report
schema, evidence gate, and blocked-stop defaults. Update `/cg-plan` and
`/cg-work` with compact hooks to load and follow that shared contract.

**Pros**: Preserves compact prompts, gives one canonical schema, reduces drift
between `/cg-plan` and `/cg-work`, supports focused tests, and matches the
existing shared-contract pattern used for review routing.

**Cons**: `/cg-work` must reliably load the shared contract, and tests must
cover both the prompt hooks and the shared contract contents.

### Approach 3: New Dedicated Goal Prompt

Add a new `/cg-goal` or `/cg-execute-goal` workflow and gradually migrate
`/cg-plan` and `/cg-work` toward it.

**Pros**: Clean experimental surface and lower immediate risk to existing
workflows.

**Cons**: Splits the workflow, creates another command for users to learn, and
does not satisfy the roadmap intent of transforming the existing
`/cg-plan` -> `/cg-work` loop.

## Decision

Choose **Approach 2: Shared Contract + Thin Prompt Hooks**.

The implementation should create a canonical shared goal-execution contract and
keep `/cg-plan` and `/cg-work` as compact workflow routers. `/cg-plan` should
generate and preview the completion contract before writing the plan.
`/cg-work` should load the contract, create/update a separate execution report,
apply strict evidence gating, and record any deviations or accepted exceptions.

The preferred artifact boundary is:

- **Plan**: stable completion contract plus minimal operational metadata.
- **Execution report**: actual execution record, deviations, evidence, and
  remaining uncertainty.

## Next Steps

1. Create a `/cg-plan` for this feature using this brainstorm as input.
2. Plan likely touch points:
   - `.github/shared/goal-execution.contract.md`
   - `.github/prompts/cg-plan.prompt.md`
   - `.github/prompts/cg-work.prompt.md`
   - `.github/shared/context-loading.contract.md` if shared-contract loading
     conventions need updating
   - `docs/workflow.md`, `docs/reference.md`, or related docs
   - `tests/prompt-tools.Tests.ps1`
3. Preserve the phased execution parser contract and phase frontmatter behavior.
4. Preserve Pester safety rules: never add direct `Invoke-Pester` recipes; keep
   using the canonical safe runner pattern.
5. Add tests for prompt hooks, `deviate:` argument documentation, contract
   schema expectations, execution report artifact path, and evidence-gate
   language.
