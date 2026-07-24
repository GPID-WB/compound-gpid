---
date: 2026-07-23
title: "WB report writing: Policy briefs"
status: active
scope: "Standard"
brainstorm: ".cg-docs/brainstorms/2026-07-23-wb-institutional-report-writing-skill.md"
language: "both"
estimated-effort: "medium"
deviation-policy: "ask"
phases: 2
parent-plan: ".cg-docs/plans/2026-07-23-wb-institutional-report-writing-skill.md"
tags: [skill, writing, world-bank, policy-brief]
---

# Plan: Policy Brief Pattern

## Objective

Add and evaluate the policy-note/brief reference independently from the other
World Bank document patterns.

## Context

Parent Phase 1 is a prerequisite. This plan owns a fixed policy-brief source
pack and result record; unavailable inputs block only this child.

## Requirements

| ID | Requirement | Source |
|----|-------------|--------|
| R1 | Record 2-3 approved policy-note/brief exemplars and practice terminology. | Parent R6 |
| R2 | Encode a 2-4 page decision-maker structure with issue, evidence, implications, grounded options/recommendations, caveats, and sources. | Brainstorm: Policy Notes |
| R3 | Cover all seven operations, including technical-to-brief adaptation. | Parent R2 |
| R4 | Distinguish evidence-grounded options from invented Bank recommendations and preserve all figures/caveats. | Parent R3-R4, R9 |
| R5 | Evaluate fidelity and guardrails against a baseline with human acceptance. | Parent R10 |
| R6 | Keep v1 English/basic `.qmd` only. | Parent R12 |

## Implementation Steps

## Phase 1: Approved Pattern

### 1. Approve the Policy-Brief Source Pack

- **Requirements**: R1, R4
- **Files**: `.github/skills/cg-skill-wb-report-writing/references/source-packs/policy-brief.json`
- **Details**: Record approved exemplars, authority rationale, relevant sections, retrieval dates, and practice-specific terminology/disclaimers.
- **Test Scenarios**: Missing approval; inaccessible exemplar; unresolved recommendation terminology.
- **Tests**: `python scripts/validate_wb_writing_skill.py --type policy-brief --require-approved`
- **Acceptance criteria**: The fixed source pack passes validation.

### 2. Implement and Behavior-Test the Policy-Brief Reference

- **Requirements**: R2, R3, R4, R6
- **Files**: `.github/skills/cg-skill-wb-report-writing/references/policy-brief.md`; `.github/skills/cg-skill-wb-report-writing/evals/types/policy-brief.json`; `scripts/tests/test_wb_writing_policy_brief.py`
- **Details**: Encode concise decision-maker structure, type-specific anti-patterns, all operations, and explicit position/clearance handling. Add unsupported language/Quarto negative cases.
- **Test Scenarios**: Draft from evidence bullets; compress technical prose; unsupported recommendation; preliminary estimate; jargon; brief-to-blog adaptation.
- **Tests**: `python -m pytest scripts/tests/test_wb_writing_policy_brief.py -q`
- **Acceptance criteria**: Focused tests pass and ungrounded recommendations are flagged, not authored as cleared positions.

## Phase 2: Evaluation and Acceptance

### 3. Evaluate Policy-Brief Fidelity and Guardrails

- **Requirements**: R3, R4, R5, R6
- **Files**: `.github/skills/cg-skill-wb-report-writing/evals/results/policy-brief.json`; `.github/skills/cg-skill-wb-report-writing-policy-brief-workspace/**`
- **Details**: Run paired evals, grade structure/length guidance/source fidelity, collect qualitative review, and write the fixed result record only after explicit acceptance.
- **Test Scenarios**: Grounded options; invented recommendation; unpublished number; absent citation; multilingual/full-Quarto near misses.
- **Tests**: `python scripts/validate_wb_writing_skill.py --type policy-brief --require-eval-pass`
- **Acceptance criteria**: Assertions pass and human review accepts decision-maker calibration.

## Testing Strategy

Validate the source pack, run focused per-type Python behavior checks, compare paired
outputs, grade objective contracts, and record human review.

## Documentation Checklist

- [ ] Record source authority and retrieval dates.
- [ ] Document length, structure, recommendation, and citation boundaries.
- [ ] Verify nested links.

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Skill invents Bank recommendations | Position markers and adversarial assertions |
| Compression drops caveats | Caveat-retention grading |
| Generic summary is mislabeled as a brief | Type-specific structure and human review |

## Out of Scope

Clearance decisions, new policy recommendations, language translation, data
retrieval, and full Quarto execution.

## Completion Contract

### Outcome

The policy-brief pattern is source-approved, tested, evaluated, and accepted as
a concise decision-maker format without invented recommendations.

### Verification Surface

| ID | Phase | Evidence Required | Command/Artifact | Required |
|----|-------|-------------------|------------------|----------|
| V1 | 1 | Approved policy-brief source pack | `python scripts/validate_wb_writing_skill.py --type policy-brief --require-approved` | yes |
| V2 | 1 | Policy-brief behavior passes | `python -m pytest scripts/tests/test_wb_writing_policy_brief.py -q` | yes |
| V3 | 2 | Policy-brief eval and acceptance pass | `python scripts/validate_wb_writing_skill.py --type policy-brief --require-eval-pass` | yes |
| V4 | final | Fixed policy-brief evidence is complete | `python scripts/validate_wb_writing_skill.py --type policy-brief --require-approved --require-eval-pass` | yes |

### Constraints

| ID | Phase | Constraint | Check |
|----|-------|------------|-------|
| C1 | final | No invented recommendations, figures, citations, or positions. | Fixed adversarial result record |
| C2 | final | Caveats and data-status markers survive compression/adaptation. | Eval grading record |
| C3 | final | English/basic `.qmd` only. | Negative eval record |

### Boundaries

- Allowed: policy-brief source pack, reference, evals/results, and tests.
- Out of scope: other type references and parent integration.

### Iteration Policy

1. Stop Phase 1 if approval inputs are incomplete.
2. Iterate until objective and human acceptance gates pass.
3. Ask before changing shared guardrails.

### Blocked-Stop Conditions

- Parent Phase 1 is incomplete.
- Policy-brief source approval is incomplete.
- An eval invents a recommendation or drops a material caveat.
- Required validator or focused Python contract checks fail after local recovery.