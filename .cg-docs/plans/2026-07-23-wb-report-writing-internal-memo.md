---
date: 2026-07-23
title: "WB report writing: Internal memos and decision notes"
status: active
scope: "Standard"
brainstorm: ".cg-docs/brainstorms/2026-07-23-wb-institutional-report-writing-skill.md"
language: "both"
estimated-effort: "medium"
deviation-policy: "ask"
phases: 2
parent-plan: ".cg-docs/plans/2026-07-23-wb-institutional-report-writing-skill.md"
tags: [skill, writing, world-bank, memo, decision-note]
---

# Plan: Internal Memo and Decision Note Pattern

## Objective

Add and evaluate an operational internal memo/decision-note pattern that never
invents management decisions, endorsements, or recommendations.

## Context

Parent Phase 1 is required. This child owns memo exemplars, internal-audience
rules, authorization/status tests, and fixed acceptance evidence.

## Requirements

| ID | Requirement | Source |
|----|-------------|--------|
| R1 | Record 2-3 approved memo/decision-note exemplars and internal terminology. | Parent R6 |
| R2 | Encode purpose, decision requested, context, options, tradeoffs, risks, authorized recommendation, and next steps. | Brainstorm: Internal Memos |
| R3 | Cover all seven operations and cross-document adaptation. | Parent R2 |
| R4 | Preserve confidentiality/data status and separate author-only notes from circulated prose. | Parent R3-R4, R9 |
| R5 | Evaluate authorization boundaries, decision structure, status marking, and human acceptance. | Parent R10 |
| R6 | Keep v1 English/basic `.qmd` only. | Parent R12 |

## Implementation Steps

## Phase 1: Approved Pattern

### 1. Approve the Memo Source Pack

- **Requirements**: R1, R4
- **Files**: `.github/skills/cg-skill-wb-report-writing/references/source-packs/internal-memo.json`
- **Details**: Record approved exemplars, internal audience, decision owner requirements, confidentiality/status handling, authority rationale, and retrieval dates.
- **Test Scenarios**: Missing audience/owner; unclear confidentiality; inaccessible exemplar.
- **Tests**: `python scripts/validate_wb_writing_skill.py --type internal-memo --require-approved`
- **Acceptance criteria**: The source pack passes validation.

### 2. Implement and Behavior-Test the Memo Reference

- **Requirements**: R2, R3, R4, R6
- **Files**: `.github/skills/cg-skill-wb-report-writing/references/internal-memo.md`; `.github/skills/cg-skill-wb-report-writing/evals/types/internal-memo.json`; `scripts/tests/test_wb_writing_internal_memo.py`
- **Details**: Encode decision structure, authorization boundaries, status propagation, author-note separation, all operations, and language/full-Quarto negative cases.
- **Test Scenarios**: Draft from options; missing decision owner; infer recommendation; confidential preliminary evidence; revise for concision; memo-to-brief adaptation.
- **Tests**: `python -m pytest scripts/tests/test_wb_writing_internal_memo.py -q`
- **Acceptance criteria**: Focused tests pass and unauthorized recommendations/endorsements are never invented.

## Phase 2: Evaluation and Acceptance

### 3. Evaluate Memo Fidelity and Guardrails

- **Requirements**: R3, R4, R5, R6
- **Files**: `.github/skills/cg-skill-wb-report-writing/evals/results/internal-memo.json`; `.github/skills/cg-skill-wb-report-writing-internal-memo-workspace/**`
- **Details**: Run paired evals, grade decision structure, authorization, status propagation, and note separation; collect human review and persist fixed results.
- **Test Scenarios**: Invented endorsement; leaked author note; missing owner; unpublished evidence; multilingual/full-Quarto near misses.
- **Tests**: `python scripts/validate_wb_writing_skill.py --type internal-memo --require-eval-pass`
- **Acceptance criteria**: Assertions pass and human review accepts operational usefulness and boundaries.

## Testing Strategy

Use source validation, focused per-type Python checks, paired adversarial evals,
authorization/status grading, and human review.

## Documentation Checklist

- [ ] Record exemplar authority and retrieval dates.
- [ ] Document audience/owner, status, and author-note requirements.
- [ ] Verify nested links.

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Skill invents a recommendation or endorsement | Authorization preflight and adversarial checks |
| Author notes leak into circulated prose | Distinct marker assertions |
| Preliminary/confidential status disappears | Propagation grading |

## Out of Scope

Management approval, clearance, access control, language translation, data
retrieval, and full Quarto execution.

## Completion Contract

### Outcome

The memo/decision-note pattern is source-approved, authorization-aware, tested,
evaluated, and accepted with status and author-note boundaries intact.

### Verification Surface

| ID | Phase | Evidence Required | Command/Artifact | Required |
|----|-------|-------------------|------------------|----------|
| V1 | 1 | Approved memo source pack | `python scripts/validate_wb_writing_skill.py --type internal-memo --require-approved` | yes |
| V2 | 1 | Memo behavior passes | `python -m pytest scripts/tests/test_wb_writing_internal_memo.py -q` | yes |
| V3 | 2 | Memo eval and acceptance pass | `python scripts/validate_wb_writing_skill.py --type internal-memo --require-eval-pass` | yes |
| V4 | final | Fixed memo evidence is complete | `python scripts/validate_wb_writing_skill.py --type internal-memo --require-approved --require-eval-pass` | yes |

### Constraints

| ID | Phase | Constraint | Check |
|----|-------|------------|-------|
| C1 | final | No invented decisions, endorsements, or recommendations. | Fixed adversarial result record |
| C2 | final | Status markers and author-note separation remain. | Eval grading record |
| C3 | final | English/basic `.qmd` only. | Negative eval record |

### Boundaries

- Allowed: memo source pack, reference, evals/results, and tests.
- Out of scope: other type references and parent integration.

### Iteration Policy

1. Stop if source, audience, or authorization inputs are incomplete.
2. Iterate until objective and human gates pass.
3. Ask before changing shared contracts.

### Blocked-Stop Conditions

- Parent Phase 1 is incomplete.
- Memo exemplars, audience, or decision owner are incomplete.
- An eval invents authorization or leaks author notes.
- Required validator or focused Python contract checks fail after local recovery.