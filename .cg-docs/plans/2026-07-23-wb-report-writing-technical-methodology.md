---
date: 2026-07-23
title: "WB report writing: Technical methodology"
status: active
scope: "Standard"
brainstorm: ".cg-docs/brainstorms/2026-07-23-wb-institutional-report-writing-skill.md"
language: "both"
estimated-effort: "medium"
deviation-policy: "ask"
phases: 2
parent-plan: ".cg-docs/plans/2026-07-23-wb-institutional-report-writing-skill.md"
tags: [skill, writing, world-bank, methodology]
---

# Plan: Technical Methodology Pattern

## Objective

Add and evaluate an auditable technical/methodology documentation pattern that
never fills missing methodological details.

## Context

Parent Phase 1 is required. This child owns methodology exemplars, reference
rules, completeness evals, and fixed acceptance evidence.

## Requirements

| ID | Requirement | Source |
|----|-------------|--------|
| R1 | Record 2-3 approved methodology/technical-annex exemplars and terminology. | Parent R6 |
| R2 | Encode scope, definitions, data, transformations, estimands, assumptions, validation, limitations, reproducibility, and version changes. | Brainstorm: Technical Documentation |
| R3 | Cover all seven operations and nontechnical cross-document adaptation. | Parent R2 |
| R4 | Treat missing parameters, formulas, sample rules, vintages, weights, and validation results as placeholders. | Parent R3-R4, R9 |
| R5 | Evaluate completeness, exact parameter fidelity, caveat retention, and human acceptance. | Parent R10 |
| R6 | Keep v1 English/basic `.qmd` only. | Parent R12 |

## Implementation Steps

## Phase 1: Approved Pattern

### 1. Approve the Methodology Source Pack

- **Requirements**: R1, R4
- **Files**: `.github/skills/cg-skill-wb-report-writing/references/source-packs/technical-methodology.json`
- **Details**: Record approved exemplars, relevant sections, authority rationale, retrieval dates, terminology, and minimum method-input checklist.
- **Test Scenarios**: Missing method inputs; inaccessible exemplar; unresolved terminology.
- **Tests**: `python scripts/validate_wb_writing_skill.py --type technical-methodology --require-approved`
- **Acceptance criteria**: The source pack passes validation.

### 2. Implement and Behavior-Test the Methodology Reference

- **Requirements**: R2, R3, R4, R6
- **Files**: `.github/skills/cg-skill-wb-report-writing/references/technical-methodology.md`; `.github/skills/cg-skill-wb-report-writing/evals/types/technical-methodology.json`; `scripts/tests/test_wb_writing_technical_methodology.py`
- **Details**: Encode auditable structure, all operations, missing-detail placeholders, reproducibility expectations, and adaptation caveat retention. Add language/full-Quarto negative cases.
- **Test Scenarios**: Complete specification; missing weight treatment; ambiguous denominator; revise for reproducibility; annex-to-blog; unsupported validation claim.
- **Tests**: `python -m pytest scripts/tests/test_wb_writing_technical_methodology.py -q`
- **Acceptance criteria**: Focused tests pass and missing technical details are never inferred.

## Phase 2: Evaluation and Acceptance

### 3. Evaluate Methodology Fidelity and Guardrails

- **Requirements**: R3, R4, R5, R6
- **Files**: `.github/skills/cg-skill-wb-report-writing/evals/results/technical-methodology.json`; `.github/skills/cg-skill-wb-report-writing-technical-methodology-workspace/**`
- **Details**: Run paired evals, grade completeness, exact parameters, limitations, and adaptation fidelity; collect human review and persist the fixed result record.
- **Test Scenarios**: Missing formula; false validation claim; dropped caveat; absent vintage/weight; multilingual/full-Quarto near misses.
- **Tests**: `python scripts/validate_wb_writing_skill.py --type technical-methodology --require-eval-pass`
- **Acceptance criteria**: Objective checks pass and human review accepts technical fidelity.

## Testing Strategy

Use source validation, focused per-type Python tests, paired evals, exact parameter
grading, and human technical review.

## Documentation Checklist

- [ ] Record exemplar authority and retrieval dates.
- [ ] Document minimum method inputs and placeholder behavior.
- [ ] Verify nested links.

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Missing parameters are plausibly inferred | Required placeholders and adversarial evals |
| Adaptation strips limitations | Caveat-retention grading |
| Documentation implies unrun validation | Verification markers and exact claims |

## Out of Scope

Method design, analysis execution, language translation, data retrieval, and
Quarto code execution/data binding.

## Completion Contract

### Outcome

The technical-methodology pattern is source-approved, auditable, tested,
evaluated, and accepted without inferred method details.

### Verification Surface

| ID | Phase | Evidence Required | Command/Artifact | Required |
|----|-------|-------------------|------------------|----------|
| V1 | 1 | Approved methodology source pack | `python scripts/validate_wb_writing_skill.py --type technical-methodology --require-approved` | yes |
| V2 | 1 | Methodology behavior passes | `python -m pytest scripts/tests/test_wb_writing_technical_methodology.py -q` | yes |
| V3 | 2 | Methodology eval and acceptance pass | `python scripts/validate_wb_writing_skill.py --type technical-methodology --require-eval-pass` | yes |
| V4 | final | Fixed methodology evidence is complete | `python scripts/validate_wb_writing_skill.py --type technical-methodology --require-approved --require-eval-pass` | yes |

### Constraints

| ID | Phase | Constraint | Check |
|----|-------|------------|-------|
| C1 | final | No inferred formulas, parameters, validation, or results. | Fixed adversarial result record |
| C2 | final | Limitations survive adaptation. | Eval grading record |
| C3 | final | English/basic `.qmd` only. | Negative eval record |

### Boundaries

- Allowed: methodology source pack, reference, evals/results, and tests.
- Out of scope: other type references and parent integration.

### Iteration Policy

1. Stop if source or method-input approval is incomplete.
2. Iterate until objective and human technical gates pass.
3. Ask before changing shared contracts.

### Blocked-Stop Conditions

- Parent Phase 1 is incomplete.
- Methodology exemplars or required inputs are incomplete.
- An eval infers a missing method detail or validation result.
- Required validator or focused Python contract checks fail after local recovery.