---
date: 2026-07-23
title: "WB report writing: Flagship report sections"
status: active
scope: "Standard"
brainstorm: ".cg-docs/brainstorms/2026-07-23-wb-institutional-report-writing-skill.md"
language: "both"
estimated-effort: "medium"
deviation-policy: "ask"
phases: 2
parent-plan: ".cg-docs/plans/2026-07-23-wb-institutional-report-writing-skill.md"
tags: [skill, writing, world-bank, flagship-report]
---

# Plan: Flagship Report Section Pattern

## Objective

Add and evaluate a source-grounded flagship-section pattern for premium World
Bank publications without blocking other document types.

## Context

Parent Phase 1 is required. This child owns flagship source approval, narrative
rules, publication conventions, evals, and fixed acceptance evidence.

## Requirements

| ID | Requirement | Source |
|----|-------------|--------|
| R1 | Record 2-3 approved flagship-section exemplars and report-specific terminology. | Parent R6 |
| R2 | Encode narrative architecture, evidence-to-interpretation transitions, boxes, figures, tables, and measured institutional voice. | Brainstorm: Flagship Sections |
| R3 | Cover all seven operations and cross-document adaptation. | Parent R2 |
| R4 | Require grounded report-level claims and figure titles/sources that follow WBG conventions. | Parent R3-R5, R9 |
| R5 | Evaluate narrative fidelity, source integrity, publication claims, and human acceptance. | Parent R10 |
| R6 | Keep v1 English/basic `.qmd` only. | Parent R12 |

## Implementation Steps

## Phase 1: Approved Pattern

### 1. Approve the Flagship Source Pack

- **Requirements**: R1, R4
- **Files**: `.github/skills/cg-skill-wb-report-writing/references/source-packs/flagship-report-section.json`
- **Details**: Record approved exemplars, relevant sections, report framing, terminology, authority rationale, and retrieval dates.
- **Test Scenarios**: Missing report framing; inaccessible exemplar; unresolved terminology.
- **Tests**: `python scripts/validate_wb_writing_skill.py --type flagship-report-section --require-approved`
- **Acceptance criteria**: The source pack passes validation.

### 2. Implement and Behavior-Test the Flagship Reference

- **Requirements**: R2, R3, R4, R6
- **Files**: `.github/skills/cg-skill-wb-report-writing/references/flagship-report-section.md`; `.github/skills/cg-skill-wb-report-writing/evals/types/flagship-report-section.json`; `scripts/tests/test_wb_writing_flagship_report_section.py`
- **Details**: Encode narrative structure, type anti-patterns, all operations, figure What/Where/When titles, valid source lines, boxes, and unsupported-claim handling. Add language/full-Quarto negative cases.
- **Test Scenarios**: Expand analytical bullets; integrate chart notes; incomplete figure metadata; uncleared global claim; unsupported trend explanation; section-to-brief adaptation.
- **Tests**: `python -m pytest scripts/tests/test_wb_writing_flagship_report_section.py -q`
- **Acceptance criteria**: Focused tests pass and publication claims remain source-grounded.

## Phase 2: Evaluation and Acceptance

### 3. Evaluate Flagship Fidelity and Guardrails

- **Requirements**: R3, R4, R5, R6
- **Files**: `.github/skills/cg-skill-wb-report-writing/evals/results/flagship-report-section.json`; `.github/skills/cg-skill-wb-report-writing-flagship-report-section-workspace/**`
- **Details**: Run paired evals, grade narrative and figure/table conventions, test institutional-position handling, collect qualitative review, and persist the fixed result record.
- **Test Scenarios**: Grounded narrative; invented global claim; bad source line; missing year/geography; multilingual/full-Quarto near misses.
- **Tests**: `python scripts/validate_wb_writing_skill.py --type flagship-report-section --require-eval-pass`
- **Acceptance criteria**: Assertions pass and human review accepts flagship-section fidelity.

## Testing Strategy

Use approved-source validation, per-type Python checks, paired evals, objective
publication-convention grading, and human review.

## Documentation Checklist

- [ ] Record exemplar authority and retrieval dates.
- [ ] Document narrative, box, figure, table, and source-line conventions.
- [ ] Verify nested links.

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Generic prose lacks flagship coherence | Exemplar-derived narrative rules and review |
| Figures omit scope/source details | What/Where/When and source-line assertions |
| Skill invents report-level positions | Position markers and adversarial evals |

## Out of Scope

Whole-report project management, typesetting, clearance, language translation,
data retrieval, and full Quarto execution.

## Completion Contract

### Outcome

The flagship-section pattern is source-approved, publication-aware, tested,
evaluated, and accepted without unsupported institutional claims.

### Verification Surface

| ID | Phase | Evidence Required | Command/Artifact | Required |
|----|-------|-------------------|------------------|----------|
| V1 | 1 | Approved flagship source pack | `python scripts/validate_wb_writing_skill.py --type flagship-report-section --require-approved` | yes |
| V2 | 1 | Flagship behavior passes | `python -m pytest scripts/tests/test_wb_writing_flagship_report_section.py -q` | yes |
| V3 | 2 | Flagship eval and acceptance pass | `python scripts/validate_wb_writing_skill.py --type flagship-report-section --require-eval-pass` | yes |
| V4 | final | Fixed flagship evidence is complete | `python scripts/validate_wb_writing_skill.py --type flagship-report-section --require-approved --require-eval-pass` | yes |

### Constraints

| ID | Phase | Constraint | Check |
|----|-------|------------|-------|
| C1 | final | No invented publication claims, figures, citations, or positions. | Fixed adversarial result record |
| C2 | final | Figure/table/source conventions remain intact. | Eval grading record |
| C3 | final | English/basic `.qmd` only. | Negative eval record |

### Boundaries

- Allowed: flagship source pack, reference, evals/results, and tests.
- Out of scope: other type references and parent integration.

### Iteration Policy

1. Stop if source approval is incomplete.
2. Iterate until objective and human gates pass.
3. Ask before changing shared publication or safety rules.

### Blocked-Stop Conditions

- Parent Phase 1 is incomplete.
- Flagship source approval or report framing is incomplete.
- An eval invents a claim or violates figure/source conventions.
- Required validator or focused Python contract checks fail after local recovery.