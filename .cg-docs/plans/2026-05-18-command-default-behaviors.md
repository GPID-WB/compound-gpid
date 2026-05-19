---
date: 2026-05-18
title: "Command default behaviors for main workflow commands"
status: completed
completed-date: 2026-05-18
scope: "Standard"
brainstorm: ".cg-docs/brainstorms/2026-05-18-command-default-behaviors.md"
language: "both"
estimated-effort: "medium"
tags: [workflow, ux, defaults, prompts, flags]
phases: 2
---

# Plan: Command Default Behaviors

## Objective

Flip the five main workflow commands to opinionated defaults so users get the most common behavior without flags. Each command gets a new default plus an opt-out flag for the rare case where the old behavior is preferred.

## Context

Currently `/cg-brainstorm` asks about branching, `/cg-plan` gates phasing on scope, `/cg-review` requires `mode:autofix` to enable auto-fixing, and `/cg-compound` asks before enriching context.md. Users almost always want: branch on main, phased plans, autofix safe findings, and auto-enrich context+wiki. The brainstorm decided on Approach 1: modify each prompt file directly with opt-out flags.

## Requirements

| ID  | Requirement                          | Source           |
|-----|--------------------------------------|------------------|
| R1  | `/cg-brainstorm` auto-creates branch on main/default (no prompt) | brainstorm |
| R2  | `/cg-brainstorm` prompts stay/new on feature branch | brainstorm |
| R3  | `/cg-brainstorm` offers `git init` on non-git workspace | brainstorm |
| R4  | `/cg-brainstorm` supports `--no-branch` flag to skip | brainstorm |
| R5  | `/cg-plan` always produces phased output regardless of scope | brainstorm |
| R6  | `/cg-plan` supports `--no-phases` flag to skip phasing | brainstorm |
| R7  | `/cg-review` defaults to autofix behavior (safe_auto applied, manual presented) | brainstorm |
| R8  | `/cg-review` supports `--report-only` flag to disable autofix | brainstorm |
| R9  | `/cg-review` preserves statistical/welfare/weight guardrail | brainstorm |
| R10 | `/cg-compound` auto-writes context.md without prompting | brainstorm |
| R11 | `/cg-compound` auto-updates wiki without prompting | brainstorm |
| R12 | `/cg-compound` still asks before editing instructions/skills files | brainstorm |
| R13 | `/cg-compound` supports `--no-enrich` flag to skip auto-enrichment | brainstorm |

## Implementation Steps

## Phase 1: Core prompt modifications

### 1. Modify `/cg-brainstorm` Step 1.7 — auto-branch default
- **Requirements**: R1, R2, R3, R4
- **Files**: `.github/prompts/cg-brainstorm.prompt.md`
- **Details**:
  - Add `--no-branch` flag parsing at the top of Step 1.7 (before any git commands).
  - If `--no-branch` is present: skip Step 1.7 entirely.
  - If not a git repo (`git branch --show-current` fails): offer `git init` → then proceed with branch creation.
  - Determine the default branch (same logic as `/cg-plan` Step 0.7: `git symbolic-ref refs/remotes/origin/HEAD --short`, fallback to `main`/`master`).
  - If on default branch: auto-create the branch silently (no prompt). Confirm: "Created branch `<name>`. Let's continue."
  - If on a feature branch: prompt "You're on `<branch>`. Stay here or create a new branch?" (default: stay).
  - Preserve existing: uncommitted changes warning, Thinking Partner skip.
- **Test Scenarios**:
  - ✅ On main → branch auto-created without prompt
  - ✅ On feature branch → prompted, can stay
  - ✅ `--no-branch` → step skipped entirely
  - 🛑 Non-git workspace → offered git init
  - 🛑 Uncommitted changes → warned before auto-branch
  - ❌ Branch name already exists → handle gracefully
- **Tests**: Pester assertions in `prompt-tools.Tests.ps1` verifying:
  - Step 1.7 contains "auto-create" or "automatically create" language
  - `--no-branch` flag is documented
  - `git init` offer text is present
  - Default branch detection logic is present
- **Acceptance criteria**: Step 1.7 no longer shows a "1. Yes / 2. No" offer when on the default branch.

### 2. Modify `/cg-plan` Step 3.5 — always-phase default
- **Requirements**: R5, R6
- **Files**: `.github/prompts/cg-plan.prompt.md`
- **Details**:
  - Add `--no-phases` flag parsing in Step 1 (argument parsing block, alongside scope detection).
  - If `--no-phases` is present: skip Step 3.5 entirely.
  - Remove scope-gating in Step 3.5: replace conditional offers with "All plans are organized into phases by default" language.
  - Keep the Lightweight exception: if only 1-2 steps, phasing is meaningless — auto-skip with a note: "Plan has only N steps — phasing skipped (too short to benefit)."
  - Retain: pre-flight completed-phases check, phase structure rules, frontmatter `phases:` field.
- **Test Scenarios**:
  - ✅ Standard plan → automatically phased (no offer)
  - ✅ Deep plan → automatically phased (no offer)
  - ✅ `--no-phases` → flat plan produced
  - 🛑 1-step plan → phasing skipped with note
  - ❌ Existing completed-phases → pre-flight warning preserved
- **Tests**: Pester assertions verifying:
  - Step 3.5 no longer contains "Would you like to organize" conditional offer
  - `--no-phases` flag is documented
  - Minimum-step threshold text exists
- **Acceptance criteria**: Step 3.5 phases without asking for all scopes; only skips for trivial 1-2 step plans.

### 3. Modify `/cg-review` Step 1 + Step 4 — autofix default
- **Requirements**: R7, R8, R9
- **Files**: `.github/prompts/cg-review.prompt.md`
- **Details**:
  - In Step 1 argument parsing: flip default so autofix is ON unless:
    - `--report-only` is passed (new flag)
    - `mode:verify` is passed (existing exclusion)
  - Add `--report-only` as a recognized argument alongside existing ones.
  - In Step 2 agent dispatches: always include tagging instructions (`[safe_auto]`/`[manual]`/`[advisory]`) by default.
  - In Step 4: default path is now the autofix path. The "present findings one at a time" path becomes the `--report-only` path.
  - Preserve: statistical/welfare/weight exclusion rule, `mode:verify` mutual exclusion, content-based depth overrides.
  - Deprecation note: `mode:autofix` becomes a no-op (already the default) — document this so users who type it don't get an error.
- **Test Scenarios**:
  - ✅ No args → autofix behavior (tagging instructions sent)
  - ✅ `--report-only` → findings presented one-at-a-time
  - ✅ `mode:autofix` (explicit) → still works (no-op, same as default)
  - ✅ `mode:verify` → forces verify mode, no autofix
  - 🛑 Statistical function finding → escalated to manual (not safe_auto)
  - ❌ `--report-only` + `mode:verify` → verify wins
- **Tests**: Pester assertions verifying:
  - `--report-only` flag is documented
  - Tagging instructions are mentioned in the default path (not gated by `mode:autofix`)
  - Statistical guardrail text preserved
  - `mode:autofix` noted as default/no-op
- **Acceptance criteria**: Running `/cg-review` with no arguments behaves identically to current `/cg-review mode:autofix`.

### 4. Modify `/cg-compound` Step 5 + Step 3c — auto-enrich default
- **Requirements**: R10, R11, R12, R13
- **Files**: `.github/prompts/cg-compound.prompt.md`
- **Details**:
  - Add `--no-enrich` flag parsing in Step 0.5 (alongside `--propose`).
  - If `--no-enrich` is present: skip Step 5 (context enrichment) and Step 3c wiki auto-update entirely.
  - In Step 5: remove the "Should I add it?" prompt. Change to: assess → write directly → report what was added. Keep the "does not exist → suggest creating" path.
  - In Step 3c: wiki update already fires automatically based on trigger criteria. Ensure no additional confirmation prompt exists (verify current behavior is correct).
  - In Step 4 (cross-reference): when suggesting updates to instructions/skills files, KEEP the ask — "This pattern could be added to `<file>`. Should I update it?"
- **Test Scenarios**:
  - ✅ Context.md enrichment → writes directly without asking
  - ✅ Wiki update → fires automatically (no new prompt)
  - ✅ Instructions/skills suggestion → still asks
  - ✅ `--no-enrich` → skips context.md and wiki
  - 🛑 context.md doesn't exist → offers to create (still asks)
  - ❌ Enrichment adds duplicate content → handled gracefully
- **Tests**: Pester assertions verifying:
  - Step 5 does not contain "Should I add it?" prompt
  - `--no-enrich` flag is documented
  - Instructions/skills still have ask-first language
- **Acceptance criteria**: `/cg-compound` enriches context.md and wiki silently; only asks for instructions/skills edits.

## Phase 2: Tests and documentation

### 5. Add Pester tests for all new defaults and flags
- **Requirements**: R1–R13
- **Files**: `tests/prompt-tools.Tests.ps1`
- **Details**:
  - Add a new Describe block: "Command default behaviors"
  - Sub-contexts for each command's changes
  - Assertions per test scenario listed above (content-match based)
  - Use `Get-Content -Raw` + `-match` pattern (existing convention)
  - Include IndexOf guard pattern for block-scoped extractions if needed
- **Test Scenarios**:
  - ✅ All assertions pass on the modified prompt files
  - 🛑 A flag name is misspelled in the prompt → test catches it
- **Tests**: The tests themselves
- **Acceptance criteria**: `Invoke-Pester tests/prompt-tools.Tests.ps1 -Quiet` passes with 0 failures.

### 6. Update docs/reference.md with new flags
- **Requirements**: R4, R6, R8, R13
- **Files**: `docs/reference.md`
- **Details**:
  - Add `--no-branch`, `--no-phases`, `--report-only`, `--no-enrich` to the command reference entries
  - Note that `mode:autofix` is now the default behavior
  - Brief description of each flag's effect
- **Test Scenarios**:
  - ✅ All four flags appear in reference.md
- **Tests**: Optional Pester assertion in prompt-tools or a dedicated docs test
- **Acceptance criteria**: `docs/reference.md` documents all new flags.

## Testing Strategy

All tests are Pester-based content assertions against prompt file text. No runtime execution needed — we verify the prompt files contain the correct language, flags, and behavioral descriptions. Follow existing patterns in `tests/prompt-tools.Tests.ps1`.

## Documentation Checklist
- [ ] Each prompt file self-documents its default behavior and opt-out flag
- [ ] `docs/reference.md` updated with new flags
- [ ] No README changes needed (plugin-level docs already reference the commands)

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Auto-branch on main surprises users who don't want branches | Medium | `--no-branch` flag; branch name clearly reported |
| Auto-phase clutters trivial 1-step plans | Low | Minimum-step threshold (skip for 1-2 steps) |
| Autofix default applies incorrect changes | High | Statistical/welfare guardrail preserved; `[safe_auto]` classification unchanged |
| `mode:autofix` users confused by deprecation | Low | Document as no-op, not error; same behavior |

## Out of Scope

- Centralized config in `compound-gpid.local.md` (Approach 2/3 — deferred)
- Changes to `/cg-work` (already has correct defaults)
- Changes to how `[safe_auto]`/`[manual]`/`[advisory]` classification works
- New guardrails beyond the existing statistical exclusion
