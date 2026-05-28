---
date: 2026-05-28
title: "Mid-project idea capture — brainstorm depth, confidence, model strategy, help, outcome verification, goal-driven execution"
trigger: "mid-project"
outcome: "roadmap-updated"
---

# Strategy Session: Mid-Project Idea Capture

## Context at Session Start

- Knowledge Brain milestone at 62% (Batch D team brain active on `feat/knowledge-brain-engine` branch)
- Workflow Maturity at 78%, Current Focus unchanged
- 45 features done, 5 active, 36 unstarted across 11 milestones
- User came with 8 concrete ideas to capture as future work

## Discussion Summary

User presented 8 ideas spanning brainstorm quality, model strategy, help system, and outcome verification. Key clarifications:

- **Scope vs. sequencing**: User confirmed these are future ideas (scope), not immediate next work.
- **Overlap with existing features**: Ideas 7 and 8 overlap with existing "outcome-criteria-in-plans" — user chose to keep all three as complementary features rather than replace.
- **Inspiration source**: Idea 1 inspired by mattpocock/skills `grill-with-docs` pattern (relentless questioning, domain glossary challenge, concrete scenario stress-testing).

## Proposed Changes

8 new features added across 4 existing milestones:

### Competitive Prompt Enhancements
1. **brainstorm-depth-grill-mode** — Grill-me + grill-with-docs modes for /cg-brainstorm
2. **cg-confidence-prompt** — `/cg-confidence` for honest confidence/assumptions/unknowns assessment

### Architecture Research
3. **mattpocock-skills-review-source** — Add mattpocock/skills to competitive review sources
4. **cross-model-adversarial-review** — Use different model family for review than for work
5. **tiered-model-escalation** — Dispatch frontier models when task demands it or agent gets stuck

### Onboarding & Setup
6. **cg-help-interactive** — `/cg-help` comprehensive interactive help system

### Ongoing Ideas
7. **planning-stage-test-strategy** — Plan defines test strategy + human review facilitation
8. **agent-verified-outcome-evals** — Outcome definitions verified by reviewer agents

### Workflow Maturity
9. **goal-driven-execution** — Plan-as-completion-contract with integrated validation (inspired by Codex Goals)

## Decision

All 9 features approved and added to roadmap as ideas. No existing features modified or retired. No charter update needed (Current Focus remains Workflow Maturity).
