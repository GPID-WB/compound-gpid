---
date: 2026-07-23
title: "WB report writing: Country and regional narratives"
status: active
scope: "Standard"
brainstorm: ".cg-docs/brainstorms/2026-07-23-wb-institutional-report-writing-skill.md"
language: "both"
estimated-effort: "medium"
deviation-policy: "ask"
phases: 2
parent-plan: ".cg-docs/plans/2026-07-23-wb-institutional-report-writing-skill.md"
tags: [skill, writing, world-bank, country, regional]
---

# Plan: Country and Regional Analytical Narrative Pattern

## Objective

Add and evaluate a statistically precise, sensitivity-aware country/regional
narrative pattern independently from other document types.

## Context

Parent Phase 1 is required. This child owns current approved country terminology,
source approval, analytical behavior, evals, and fixed acceptance evidence.

## Requirements

| ID | Requirement | Source |
|----|-------------|--------|
| R1 | Record 2-3 approved exemplars plus current country names, territorial notes, sensitivity terms, and disclaimers. | Parent R6 |
| R2 | Encode trend interpretation, comparisons, heterogeneity, uncertainty, and careful attribution. | Brainstorm: Country/Regional Narratives |
| R3 | Cover all seven operations and cross-document adaptation. | Parent R2 |
| R4 | Preserve geography, year, PPP vintage, welfare concept, population basis, data status, and sensitivity flags. | Parent R3-R5, R9 |
| R5 | Evaluate statistical comparability, causal restraint, terminology prompts, and human acceptance. | Parent R10 |
| R6 | Keep v1 English/basic `.qmd` only. | Parent R12 |

## Implementation Steps

## Phase 1: Approved Pattern

### 1. Approve the Country/Regional Source Pack

- **Requirements**: R1, R4
- **Files**: `.github/skills/cg-skill-wb-report-writing/references/source-packs/country-analytical-narrative.json`
- **Details**: Record approved exemplars, retrieval dates, current country/territory terminology, sensitivity/disclaimer sources, and statistical metadata requirements.
- **Test Scenarios**: Missing territorial terminology; stale disclaimer; inaccessible source; absent PPP requirements.
- **Tests**: `python scripts/validate_wb_writing_skill.py --type country-analytical-narrative --require-approved`
- **Acceptance criteria**: The source pack passes approval and terminology validation.

### 2. Implement and Behavior-Test the Country/Regional Reference

- **Requirements**: R2, R3, R4, R6
- **Files**: `.github/skills/cg-skill-wb-report-writing/references/country-analytical-narrative.md`; `.github/skills/cg-skill-wb-report-writing/evals/types/country-analytical-narrative.json`; `scripts/tests/test_wb_writing_country_analytical_narrative.py`
- **Details**: Encode comparability, interpretation, sensitivity preflight, all operations, and prompts for approved wording rather than guessed language. Add non-English/full-Quarto negative cases.
- **Test Scenarios**: Regional trends; contested territory; conflict framing; absent PPP vintage; incomparable years; narrative-to-summary adaptation.
- **Tests**: `python -m pytest scripts/tests/test_wb_writing_country_analytical_narrative.py -q`
- **Acceptance criteria**: Focused tests pass and sensitive/statistical gaps trigger explicit prompts.

## Phase 2: Evaluation and Acceptance

### 3. Evaluate Country/Regional Fidelity and Guardrails

- **Requirements**: R3, R4, R5, R6
- **Files**: `.github/skills/cg-skill-wb-report-writing/evals/results/country-analytical-narrative.json`; `.github/skills/cg-skill-wb-report-writing-country-analytical-narrative-workspace/**`
- **Details**: Run paired evals, grade metadata preservation, terminology handling, uncertainty, and causal restraint; collect human review and write the fixed result record.
- **Test Scenarios**: Sensitive naming; missing year/geography; causal overreach; preliminary estimate; multilingual/full-Quarto near misses.
- **Tests**: `python scripts/validate_wb_writing_skill.py --type country-analytical-narrative --require-eval-pass`
- **Acceptance criteria**: Assertions pass and human review accepts analytical and sensitivity handling.

## Testing Strategy

Use source/terminology validation, focused per-type Python checks, paired adversarial
evals, statistical metadata grading, and explicit human acceptance.

## Documentation Checklist

- [ ] Record terminology/disclaimer authority and retrieval dates.
- [ ] Document comparability and sensitivity preflights.
- [ ] Verify nested links.

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Sensitive terminology becomes stale | Require current approved source metadata |
| Comparisons mix vintages/concepts | Explicit comparability assertions |
| Narrative implies unsupported causality | Attribution and causal-restraint evals |

## Out of Scope

Map clearance, political judgment, language translation, data retrieval, and
full Quarto execution.

## Completion Contract

### Outcome

The country/regional pattern is source-approved, statistically comparable,
sensitivity-aware, tested, evaluated, and accepted.

### Verification Surface

| ID | Phase | Evidence Required | Command/Artifact | Required |
|----|-------|-------------------|------------------|----------|
| V1 | 1 | Approved country/regional source pack | `python scripts/validate_wb_writing_skill.py --type country-analytical-narrative --require-approved` | yes |
| V2 | 1 | Country/regional behavior passes | `python -m pytest scripts/tests/test_wb_writing_country_analytical_narrative.py -q` | yes |
| V3 | 2 | Country/regional eval and acceptance pass | `python scripts/validate_wb_writing_skill.py --type country-analytical-narrative --require-eval-pass` | yes |
| V4 | final | Fixed country/regional evidence is complete | `python scripts/validate_wb_writing_skill.py --type country-analytical-narrative --require-approved --require-eval-pass` | yes |

### Constraints

| ID | Phase | Constraint | Check |
|----|-------|------------|-------|
| C1 | final | No guessed sensitive terminology or unsupported causality. | Fixed adversarial result record |
| C2 | final | Statistical scope metadata and data-status markers remain. | Eval grading record |
| C3 | final | English/basic `.qmd` only. | Negative eval record |

### Boundaries

- Allowed: country/regional source pack, reference, evals/results, and tests.
- Out of scope: other type references and parent integration.

### Iteration Policy

1. Stop if source or terminology approval is incomplete.
2. Iterate until statistical, sensitivity, and human gates pass.
3. Ask before changing shared guardrails.

### Blocked-Stop Conditions

- Parent Phase 1 is incomplete.
- Approved terminology/disclaimers or exemplars are incomplete.
- An eval guesses sensitive language or creates invalid comparisons.
- Required validator or focused Python contract checks fail after local recovery.