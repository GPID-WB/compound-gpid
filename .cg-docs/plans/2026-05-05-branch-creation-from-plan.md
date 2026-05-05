---
date: 2026-05-05
title: "Branch creation from /cg-plan"
status: active
scope: "Lightweight"
brainstorm: null
language: "PowerShell"
estimated-effort: "small"
tags: [cg-plan, branch-offer, git, workflow-maturity]
---

# Plan: Branch Creation from /cg-plan

## Objective

Add a branch-offer step to `/cg-plan` so users can create a feature branch at plan time — not just from `/cg-brainstorm`. This mirrors the proven Step 1.7 pattern from `cg-brainstorm.prompt.md` and follows the design principle that branch selection must precede user-investment steps.

## Context

- `/cg-brainstorm` already offers branch creation at Step 1.7 (before clarifying questions).
- `/cg-plan` currently has no branch offer. Users who skip brainstorming and go straight to `/cg-plan` end up planning on `main` with no prompt to switch.
- The solution in `.cg-docs/solutions/testing-patterns/2026-05-01-branch-offer-must-precede-user-investment-steps.md` establishes the principle: branch offers must appear before the user invests work.
- In `/cg-plan`, the user's investment starts at Step 1 (Gather Context) but the first *interactive* moment is Step 1.5 (Scope Assessment). The branch offer should come between Step 0.5 (Check for Prior Work) and Step 1 (Gather Context) — i.e., **Step 0.7**.

## Requirements

| ID  | Requirement                          | Source           |
|-----|--------------------------------------|------------------|
| R1  | Add branch-offer step to cg-plan.prompt.md between Step 0.5 and Step 1 | strategy session |
| R2  | Use same UX pattern as cg-brainstorm Step 1.7 (suggested name, yes/no, uncommitted-changes warning) | existing pattern |
| R3  | Add File Permissions entry allowing branch creation | prompt design |
| R4  | Skip branch offer if already on a non-main feature branch | usability |
| R5  | Add Pester test asserting step ordering (branch offer before Step 1) | testing conventions |

## Implementation Steps

### 1. Add Step 0.7: Branch Offer to `cg-plan.prompt.md`

- **Requirements**: R1, R2, R3, R4
- **Files**: `.github/prompts/cg-plan.prompt.md`
- **Details**:
  - Add to File Permissions: `- You may create a git branch if the user explicitly accepts at Step 0.7.`
  - Insert `### Step 0.7: Branch Offer` between Step 0.5 and Step 1 with this content:
    ```
    ### Step 0.7: Branch Offer

    Before gathering context, check if the user is on a feature branch:

    - If already on a non-default branch (not `main`/`master`): skip silently.
    - If on the default branch, offer:

    > "Before we start planning, would you like to work on a new branch?
    > Suggested name: `feat/<short-description-from-request>`
    >
    > 1. **Yes** — I'll create the branch now
    > 2. **No** — Stay on the current branch"

    - Derive branch name from the user's feature description using project convention: `type/short-description`.
    - If accepted: `git checkout -b <branch-name>` and confirm.
    - If declined: proceed silently.
    - If uncommitted changes exist, warn: "You have uncommitted changes. Stash them first, or branch anyway?"
    ```
- **Test Scenarios**:
  - ✅ Happy path: User is on `main`, accepts branch creation
  - ✅ Skip path: User is already on `feat/something`
  - 🛑 Edge case: Uncommitted changes present
  - ❌ Error path: Branch name conflicts with existing branch
- **Acceptance criteria**: Step 0.7 exists in the prompt between Step 0.5 and Step 1; File Permissions includes branch creation allowance.

### 2. Add Pester test for step ordering

- **Requirements**: R5
- **Files**: `tests/prompt-tools.Tests.ps1`
- **Details**:
  - Add a Describe block: `"cg-plan.prompt.md - Step 0.7 Branch Offer ordering"`
  - Assert that `### Step 0.7: Branch Offer` appears in the file
  - Assert it appears after `### Step 0.5` and before `### Step 1:`
  - Follow the IndexOf guard pattern from `compound-gpid.context.md` (assert both index values before substring extraction)
- **Test Scenarios**:
  - ✅ Happy path: Step 0.7 exists between Step 0.5 and Step 1
  - ❌ Error path: Step 0.7 missing or misordered
- **Acceptance criteria**: Test passes via `. tests\Run-Tests.ps1`

## Testing Strategy

Structural test only — verify the step exists in the right position. Same pattern used for `cg-brainstorm.prompt.md - Step 1.7 Branch Offer ordering` test at line 1704 of `prompt-tools.Tests.ps1`.

## Documentation Checklist

- [x] Inline comments in the prompt step (self-documenting)
- [ ] No README update needed (user-facing behavior is self-evident)
- [ ] No function docs needed (prompt modification, not code)

## Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| Step numbering conflicts with existing steps | Use 0.7 (between 0.5 and 1), consistent with brainstorm's 1.7 pattern |
| Branch offer feels intrusive for quick plans | Skip silently when already on a feature branch (R4) |

## Out of Scope

- Modifying `/cg-work` to check branch state (separate concern)
- Adding branch deletion or PR creation (future GitHub Issues feature)
- Changing `/cg-brainstorm`'s existing branch offer
