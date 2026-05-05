---
date: 2026-05-05
title: "Workflow Maturity milestone — branch management, phased execution, smart debugging, team coordination"
trigger: "mid-project"
outcome: "roadmap-updated"
---

# Strategy Session: Workflow Maturity

## Context at Session Start

- 8 milestones, 58 features (28 done, 0 active, 30 unstarted)
- Two milestones in-progress: Skills Enhancement, Onboarding & Setup
- Recent work: Stata testing skill completed, onboarding features (scanner, smart setup, charter quality gate) shipped
- User reported urgent need for workflow improvements based on daily usage friction

## Discussion Summary

User presented 6 feature ideas. After clarification:
- Item 3 ("Make sure that cg-work...") was incomplete — dropped
- Item 5 (Copilot execution mode) was a VS Code configuration question, not a plugin feature — dropped
- 4 features retained for roadmap

Key design decisions surfaced during discussion:
1. **Phased plans** — granularity is task-dependent, not fixed. Agent asks user for breakdown or suggests one. Last phase always defaults to testing/validation/polish. User can override. `/cg-work` without args runs all phases; `/cg-work phase1` runs one and stops.
2. **Dependencies** — Branch creation from `/cg-plan` should precede phased execution (natural flow: plan → branch → work phase). The other two features are independent.
3. **GitHub Issues** — additive, not essential. Uses `gh` CLI. Graceful fallback to current roadmap-only workflow.

## Proposed Changes

New milestone: **Workflow Maturity** (status: in-progress)
- Branch creation from /cg-plan
- Phased plan structure in /cg-plan
- Phased execution in /cg-work
- /cg-fixbug test-correctness assessment
- GitHub Issues integration (optional, via gh CLI)

Deprioritized:
- Skills Enhancement: in-progress → planned
- Onboarding & Setup: in-progress → planned

## Decision

Approved as proposed. All 5 features added with descriptions. Milestone set to in-progress, other non-done milestones set to planned.

## Charter Updates

- **Current Focus** updated to reflect Workflow Maturity as the active priority
- **last-reviewed** updated to 2026-05-05
- Previous focus archived to `.cg-docs/archive/charter-history.md`
