---
date: 2026-07-23
title: "WB report writing: Executive summaries"
status: active
scope: "Standard"
brainstorm: ".cg-docs/brainstorms/2026-07-23-wb-institutional-report-writing-skill.md"
language: "both"
estimated-effort: "medium"
deviation-policy: "ask"
phases: 2
parent-plan: ".cg-docs/plans/2026-07-23-wb-institutional-report-writing-skill.md"
tags: [skill, writing, world-bank, executive-summary]
---

# Plan: Executive Summary Pattern

## Objective

Add and evaluate an executive-summary pattern that creates concise,
standalone, source-traceable synthesis for senior readers.

## Context

Parent Phase 1 is required. This independently executable child owns executive
summary source approval, behavior, evaluation, and acceptance evidence.

## Requirements

| ID | Requirement | Source |
|----|-------------|--------|
| R1 | Record 2-3 approved executive-summary exemplars and senior-reader context. | Parent R6 |
| R2 | Encode purpose, headline findings, significance, caveats, and grounded decisions/actions. | Brainstorm: Executive Summaries |
| R3 | Cover all seven operations, especially long-form summarization and cross-document adaptation. | Parent R2 |
| R4 | Trace every statistic and substantive claim to supplied source material and retain data-status/sensitivity markers. | Parent R3-R4, R9 |
| R5 | Evaluate omission risk, traceability, standalone readability, and human acceptance. | Parent R10 |
| R6 | Keep v1 English/basic `.qmd` only. | Parent R12 |

## Implementation Steps

## Phase 1: Approved Pattern

### 1. Approve the Executive-Summary Source Pack

- **Requirements**: R1, R4
- **Files**: `.github/skills/cg-skill-wb-report-writing/references/source-packs/executive-summary.json`
- **Details**: Record approved exemplars, intended senior audience, authority rationale, relevant sections, retrieval dates, and terminology/disclaimers.
- **Test Scenarios**: Missing audience; inaccessible exemplar; unresolved disclaimer.
- **Tests**: `python scripts/validate_wb_writing_skill.py --type executive-summary --require-approved`
- **Acceptance criteria**: The source pack passes validation.

### 2. Implement and Behavior-Test the Executive-Summary Reference

- **Requirements**: R2, R3, R4, R6
- **Files**: `.github/skills/cg-skill-wb-report-writing/references/executive-summary.md`; `.github/skills/cg-skill-wb-report-writing/evals/types/executive-summary.json`; `scripts/tests/test_wb_writing_executive_summary.py`
- **Details**: Encode standalone synthesis, traceability, caveat retention, contradictions, all operations, and negative language/full-Quarto boundaries.
- **Test Scenarios**: Summarize grounded report; contradictory estimates; missing conclusion; unpublished figure; requested over-certainty; brief-to-summary adaptation.
- **Tests**: `python -m pytest scripts/tests/test_wb_writing_executive_summary.py -q`
- **Acceptance criteria**: Focused tests pass and no summary introduces or strengthens a claim.

## Phase 2: Evaluation and Acceptance

### 3. Evaluate Executive-Summary Fidelity and Guardrails

- **Requirements**: R3, R4, R5, R6
- **Files**: `.github/skills/cg-skill-wb-report-writing/evals/results/executive-summary.json`; `.github/skills/cg-skill-wb-report-writing-executive-summary-workspace/**`
- **Details**: Run paired evals, grade claim traceability/caveat retention/standalone structure, collect human review, and persist fixed result evidence.
- **Test Scenarios**: Long report synthesis; unsupported headline; omitted limitation; preliminary status; multilingual/full-Quarto near misses.
- **Tests**: `python scripts/validate_wb_writing_skill.py --type executive-summary --require-eval-pass`
- **Acceptance criteria**: Objective checks pass and senior-reader fidelity is accepted.

## Testing Strategy

Use source validation, per-type Python behavior checks, paired evals, traceability
grading, and explicit human acceptance.

## Documentation Checklist

- [ ] Document source authority, audience, and retrieval dates.
- [ ] Define standalone structure and traceability expectations.
- [ ] Verify nested links.

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Concision drops material limitations | Required caveat-retention grading |
| Headlines overstate evidence | Traceability and certainty assertions |
| Summary introduces new facts | Exact source comparison |

## Out of Scope

New management decisions, language translation, source-document correction,
data retrieval, and full Quarto execution.

## Completion Contract

### Outcome

The executive-summary pattern is source-approved, traceable, tested, evaluated,
and accepted for senior-reader synthesis.

### Verification Surface

| ID | Phase | Evidence Required | Command/Artifact | Required |
|----|-------|-------------------|------------------|----------|
| V1 | 1 | Approved executive-summary source pack | `python scripts/validate_wb_writing_skill.py --type executive-summary --require-approved` | yes |
| V2 | 1 | Executive-summary behavior passes | `python -m pytest scripts/tests/test_wb_writing_executive_summary.py -q` | yes |
| V3 | 2 | Executive-summary eval and acceptance pass | `python scripts/validate_wb_writing_skill.py --type executive-summary --require-eval-pass` | yes |
| V4 | final | Fixed executive-summary evidence is complete | `python scripts/validate_wb_writing_skill.py --type executive-summary --require-approved --require-eval-pass` | yes |

### Constraints

| ID | Phase | Constraint | Check |
|----|-------|------------|-------|
| C1 | final | No new facts, positions, or certainty. | Traceability grading record |
| C2 | final | Material caveats and status markers remain. | Eval result record |
| C3 | final | English/basic `.qmd` only. | Negative eval record |

### Boundaries

- Allowed: executive-summary source pack, reference, evals/results, and tests.
- Out of scope: other type references and parent integration.

### Iteration Policy

1. Stop if source approval is incomplete.
2. Iterate until traceability and human acceptance pass.
3. Ask before changing shared contracts.

### Blocked-Stop Conditions

- Parent Phase 1 is incomplete.
- Executive-summary source approval is incomplete.
- An eval loses a caveat or introduces a claim.
- Required validator or focused Python contract checks fail after local recovery.