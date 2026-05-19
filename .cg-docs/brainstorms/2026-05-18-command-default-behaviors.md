---
date: 2026-05-18
title: "Command default behaviors for main workflow commands"
status: decided
scope: "Standard"
chosen-approach: "Prompt-level defaults"
tags: [workflow, ux, defaults, prompts]
---

# Command Default Behaviors

## Context

The five main workflow commands (`/cg-brainstorm`, `/cg-plan`, `/cg-work`, `/cg-review`, `/cg-compound`) currently ask users questions or require flags for behaviors that are almost always desired. This brainstorm establishes opinionated defaults so users get the most common behavior without flags.

## Requirements

1. `/cg-brainstorm`: On main/default branch → auto-create feature branch (no prompt). On feature branch → prompt stay/new. If workspace is not a git repo → offer `git init`. Opt-out: `--no-branch`.
2. `/cg-plan`: Always produce phased output (numbered phases with self-contained task lists) regardless of scope. Opt-out: `--no-phases`.
3. `/cg-work`: No change needed — already runs all phases sequentially by default.
4. `/cg-review`: Default to autofix mode — auto-apply `[safe_auto]` findings, present `[manual]` for approval. Existing guardrail preserved: never auto-fix statistical functions, welfare/income variables, or weight parameters. Opt-out: `--report-only`.
5. `/cg-compound`: Auto-enrich `compound-gpid.context.md` + auto-update wiki (no prompting). For `.github/instructions/` and `.github/skills/` edits → still ask the user. Opt-out: `--no-enrich`.

## Approaches Considered

### Approach 1: Prompt-level defaults (modify each prompt file directly)

Edit the 4 prompt files that need changes to flip the default behavior inline. Each prompt documents its own defaults. Opt-out flags added via argument parsing in each prompt.

**Pros**: Simple, self-contained, easy to test, no new infrastructure.
**Cons**: Opt-out flags need argument parsing; no centralized config.
**Effort**: Medium.

### Approach 2: Centralized defaults in compound-gpid.local.md

Add a `## Command Defaults` section to `compound-gpid.local.md`.

**Pros**: One place to see/change all defaults, future extensibility.
**Cons**: Over-engineering, config drift risk, more complexity.
**Effort**: Large.

### Approach 3: Hybrid — prompt-level + optional local override

Approach 1 plus optional config overrides in `compound-gpid.local.md`.

**Pros**: Best of both worlds.
**Cons**: Can be added later if needed.
**Effort**: Medium-Large.

## Decision

Approach 1 — Prompt-level defaults. Modify the 4 prompt files directly (`cg-brainstorm`, `cg-plan`, `cg-review`, `cg-compound`). `/cg-work` is already correct and needs no changes.

## Next Steps

1. Modify `/cg-brainstorm` Step 1.7: auto-branch on main, prompt on feature branch, offer git init on non-git workspace. Add `--no-branch` flag parsing.
2. Modify `/cg-plan` Step 3.5: always phase (remove scope-gating), skip silently if user passes `--no-phases`. Add flag parsing.
3. Modify `/cg-review` Step 1 + Step 4: default to `mode:autofix` behavior. Add `--report-only` flag. Preserve statistical guardrails.
4. Modify `/cg-compound` Step 5 + Step 3c: auto-write context.md and wiki without prompting. Ask only for instructions/skills. Add `--no-enrich` flag.
5. Add Pester tests for the new default behaviors and opt-out flags.
