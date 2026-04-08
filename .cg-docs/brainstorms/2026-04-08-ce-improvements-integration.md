---
date: 2026-04-08
title: "CE-inspired improvements integration from worktree"
status: decided
chosen-approach: "Reimplementation in 3 phases on dev branch"
tags: [workflow, architecture, review-pipeline, prompts]
---

# CE-Inspired Improvements Integration

## Context

In worktree `copilot-worktree-2026-04-07T14-48-38`, several improvement phases
inspired by Compound Engineering (CE) philosophy were implemented. These are
captured in 2 monolithic commits (27 files, +1,019/-425 lines) on branch
`copilot/worktree-2026-04-07T14-48-38` forked from `7f0f794` (before v0.4.3).

Meanwhile, main advanced 13 commits past the same base — adding v0.4.3 (model
audit, Pester safety), v0.4.3+ (R dialect skills architecture), and associated
review fixes. ~69 files changed on main with substantial overlap in agents,
prompts, skills, and tests.

Direct merge would be unmanageable and lose phase traceability. The user wants
each phase isolated as a clean, reviewable commit on a `dev` branch.

## Requirements

- Preserve every improvement from the worktree — nothing dropped without
  explicit evaluation
- Preserve every feature on current main — no regressions
- Each phase as a separate commit for traceability
- Work on a `dev` branch; merge to main only after verification
- Accuracy over speed — thorough reimplementation, not mechanical patching

## Approaches Considered

### Approach 1: Cherry-pick & conflict-resolve

Summary: Cherry-pick the 2 worktree commits onto main, resolve conflicts.
Pros: Fast, preserves original commit metadata.
Cons: Monolithic commits remain unsplit; conflicts would be massive (69 files
diverged); merge noise makes review impossible; no phase isolation.

### Approach 2: Rebase & split commits

Summary: Interactive rebase to split the 2 commits into phase-specific ones.
Pros: Preserves git history linkage.
Cons: Splitting already-committed changes is error-prone; rebase against a
diverged main produces cascading conflicts; still mechanical conflict
resolution rather than intentional reimplementation.

### Approach 3: Reimplementation in 3 phases on dev branch (CHOSEN)

Summary: Branch `dev` from current main. Use the worktree as a specification
document. For each phase, read the worktree intent, understand it, and
implement it fresh against main's current file structure.
Pros: Clean commits; each phase coherent against current codebase; no conflict
noise; improvements adapted to main's newer architecture (R dialect skills etc.).
Cons: More effort; doesn't preserve original commit hashes.
Effort: Medium-large.
Recommended: Yes — maximizes accuracy, avoids regression, provides clean
traceability.

## Decision

Approach 3 selected. The worktree serves as the specification (what to
implement), and current main serves as the target (where to implement it).

### Phase breakdown

1. **P0 Priority System & Review Agent Hardening** (small) — Add P0 severity
   tier across agents, instructions, review prompt, docs, and tests.

2. **New Prompts, Agent & Template Extraction** (medium) — Add cg-adversarial,
   cg-ideate, cg-compound-refresh; extract templates from cg-resume and
   cg-setup into docs/; trim cg-skill-r-testing; update registries.

3. **Existing Prompt Enhancements** (medium-large) — Add prior-work checks,
   scope assessment, auto-escalation, self-review, autofix mode, protected
   artifacts, and structured handoffs to cg-brainstorm, cg-plan, cg-work,
   and cg-review.

## Next Steps

- Create implementation plan with `/cg-plan`
- Create `dev` branch from current main
- Implement phase by phase with tests after each
- Verify full test suite passes on dev before merging to main
