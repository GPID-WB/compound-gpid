---
date: 2026-04-13
title: "Workflow automation and external patterns research"
trigger: "mid-project"
outcome: "roadmap-updated"
---

# Strategy Session: Workflow Automation and External Patterns Research

## Context at Session Start

- Quality Loop: 2 done, 1 active, 7 ideas (3 features actually done but roadmap not updated)
- Performance: 1 done, 3 ideas
- Skills Enhancement: 1 done, 2 ideas
- Architecture Research: 5 ideas, planned status
- Evals: 4 ideas, planned status

## Discussion Summary

Three ideas surfaced:

1. **External workflow research**: Assess GSD-2 (gsd-build/gsd-2) and Superpowers (obra/superpowers) for features and patterns to adopt. Key findings from initial review:
   - GSD-2: standalone CLI with autonomous `/gsd auto` mode (state machine, fresh context per task, crash recovery, verification enforcement, per-phase model selection, token optimization profiles)
   - Superpowers: skills framework with auto-triggering skills, subagent-driven development, two-stage review, batch execution with checkpoints

2. **Stage control knobs**: User-configurable depth/thoroughness for brainstorm, work, and review stages (e.g., how much research during brainstorm, how much testing during work, which agents during review)

3. **Autonomous pipeline (/cg-autopilot)**: Hands-off plan-to-PR execution: work → review → fix-triage → review light → fix-triage → commit → compound → commit → PR

Discussion on placement: considered Performance milestone (rejected — different axis), new milestone (considered), and Architecture Research (chosen). Option B selected: keep Architecture Research's research-first identity but add the three features, with stage control knobs and autopilot explicitly blocked on research conclusions.

## Proposed Changes

1. **Architecture Research** objective updated to include external workflow patterns and implementation
2. Three new features added:
   - `study-gsd2-superpowers-patterns` — analyze GSD-2 and Superpowers, produce decision doc
   - `stage-control-knobs` — configurable depth for workflow stages (blocked on research)
   - `autonomous-pipeline-autopilot` — /cg-autopilot command (blocked on research + hooks)
3. Three Quality Loop features corrected from `idea`/`active` to `done`:
   - `cg-fix-problems-agent` (artifact exists, plan completed 2026-04-13)
   - `cg-fix-problems-prompt` (artifact exists, plan completed 2026-04-13)
   - `ce-improvements-integration` (plan completed 2026-04-09)

## Decision

All changes approved and applied to roadmap.json. Identified a workflow gap: `/cg-work` does not update roadmap.json when features are completed — plan status and roadmap status drift apart silently.

## Charter Updates

- **Current Focus** updated to reflect Quality Loop progress (5/10 done) and Architecture Research expansion
- **last-reviewed** updated to 2026-04-13
- Old Current Focus archived to `.cg-docs/archive/charter-history.md`
