---
date: 2026-07-23
title: "WB report writing: Policy Research Working Papers"
status: completed
scope: "Standard"
brainstorm: ".cg-docs/brainstorms/2026-07-23-wb-institutional-report-writing-skill.md"
language: "both"
estimated-effort: "medium"
deviation-policy: "ask"
phases: 2
parent-plan: ".cg-docs/plans/2026-07-23-wb-institutional-report-writing-skill.md"
completed-date: 2026-07-24
tags: [skill, writing, world-bank, prwp]
---

# Plan: Policy Research Working Paper Pattern

## Objective

Add and evaluate the PRWP reference for `cg-skill-wb-report-writing` without
blocking any other document type.

## Context

Parent Phase 1 must be complete before this plan starts. This child owns the
PRWP source pack, reference, eval cases, and fixed result record. Missing source
approval blocks this plan only.

## Requirements

| ID | Requirement | Source |
|----|-------------|--------|
| R1 | Record 2-3 approved PRWP exemplars and required terminology at the fixed source-pack path. | Parent R6 |
| R2 | Encode academic audience, contribution, literature, methods, results, limitations, citations, figures, tables, and basic `.qmd`/`.bib` conventions. | Brainstorm: PRWP |
| R3 | Cover drafting, expansion, revision, summarization, cross-document adaptation, review, and end-to-end production. | Parent R2 |
| R4 | Preserve supplied methods and results exactly; mark every missing fact, figure, citation, or position. | Parent R3-R4, R9 |
| R5 | Evaluate ordinary and adversarial PRWP behavior against a no-skill baseline and record accepted human review. | Parent R10 |
| R6 | Remain English-only and reject/defer Quarto execution/data binding. | Parent R12 |

## Implementation Steps

## Phase 1: Approved Pattern

### 1. Approve the PRWP Source Pack

- **Requirements**: R1, R4
- **Files**: `.github/skills/cg-skill-wb-report-writing/references/source-packs/policy-research-working-paper.json`
- **Details**: Record 2-3 stable exemplar URLs/paths, approval metadata, relevant sections, authority rationale, retrieval dates, and terminology/disclaimer dependencies. Do not reproduce substantial exemplar prose.
- **Test Scenarios**: Two exemplars only; inaccessible source; missing approval; unresolved terminology.
- **Tests**: `python scripts/validate_wb_writing_skill.py --type policy-research-working-paper --require-approved`
- **Acceptance criteria**: The validator confirms an approved, complete source pack.

### 2. Implement and Behavior-Test the PRWP Reference

- **Requirements**: R2, R3, R4, R6
- **Files**: `.github/skills/cg-skill-wb-report-writing/references/policy-research-working-paper.md`; `.github/skills/cg-skill-wb-report-writing/evals/types/policy-research-working-paper.json`; `scripts/tests/test_wb_writing_policy_research_working_paper.py`
- **Details**: Distill source-grounded structure, tone, anti-patterns, and all seven operations. Add negative cases for invented methods/results, fake citations, non-English output, and Quarto execution/data binding.
- **Test Scenarios**: Expand methods bullets; revise overstated causality; missing sample size; fake citation; PRWP-to-summary adaptation.
- **Tests**: `python -m pytest scripts/tests/test_wb_writing_policy_research_working_paper.py -q`
- **Acceptance criteria**: Focused behavioral tests pass and the reference preserves exact supplied methods/results.

## Phase 2: Evaluation and Acceptance

### 3. Evaluate PRWP Fidelity and Guardrails

- **Requirements**: R3, R4, R5, R6
- **Files**: `.github/skills/cg-skill-wb-report-writing/evals/results/policy-research-working-paper.json`; `.github/skills/cg-skill-wb-report-writing-policy-research-working-paper-workspace/**`
- **Details**: Run paired with-skill/no-skill cases, grade structure and source fidelity, collect qualitative review, and write the fixed result record with benchmark, grading, feedback paths, assertion status, and `human_accepted: true` only after explicit approval.
- **Test Scenarios**: Complete outline; grounded methods/results; unsupported statistic; missing `.bib`; non-English and code-binding near misses.
- **Tests**: `python scripts/validate_wb_writing_skill.py --type policy-research-working-paper --require-eval-pass`
- **Acceptance criteria**: Objective guardrails pass and human review accepts PRWP fidelity.

## Testing Strategy

Combine source-pack validation, focused per-type Python contract checks, paired
skill-creator evals, objective grading, and recorded human review.

## Documentation Checklist

- [ ] Cite source-pack authority and retrieval dates.
- [ ] Document PRWP structure, citation, figure/table, and `.qmd` limits.
- [ ] Verify nested links from the reference directory.

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Academic prose sounds plausible but changes methods/results | Exact-value assertions and source traceability |
| Citation structure looks verified when it is not | `.bib` lookup or visible verification marker |
| Reference copies exemplar language | Distill patterns and require human source review |

## Out of Scope

Language translation, journal submission, new analysis, data retrieval, and
Quarto code execution/data binding.

## Completion Contract

### Outcome

The PRWP pattern is source-approved, behavior-tested, adversarially evaluated,
and accepted without affecting readiness of other document types.

### Verification Surface

| ID | Phase | Evidence Required | Command/Artifact | Required |
|----|-------|-------------------|------------------|----------|
| V1 | 1 | Approved PRWP source pack | `python scripts/validate_wb_writing_skill.py --type policy-research-working-paper --require-approved` | yes |
| V2 | 1 | PRWP reference behavior passes | `python -m pytest scripts/tests/test_wb_writing_policy_research_working_paper.py -q` | yes |
| V3 | 2 | PRWP eval and human acceptance pass | `python scripts/validate_wb_writing_skill.py --type policy-research-working-paper --require-eval-pass` | yes |
| V4 | final | Fixed PRWP evidence is complete | `python scripts/validate_wb_writing_skill.py --type policy-research-working-paper --require-approved --require-eval-pass` | yes |

### Constraints

| ID | Phase | Constraint | Check |
|----|-------|------------|-------|
| C1 | final | No invented methods, results, figures, citations, or positions. | Fixed adversarial result record |
| C2 | final | English/basic `.qmd` only. | Negative eval record |
| C3 | final | No substantial exemplar copying. | Human source review |

### Boundaries

- Allowed: PRWP source pack, reference, eval definitions/results, and behavioral tests.
- Out of scope: other document-type references and parent integration work.

### Iteration Policy

1. Stop Phase 1 if source approval is incomplete.
2. Revise until objective assertions pass and human review accepts fidelity.
3. Ask before changing shared marker or source-authority rules.

### Blocked-Stop Conditions

- Parent Phase 1 is incomplete.
- PRWP source approval or terminology is incomplete.
- Any output invents or silently strengthens source content.
- Required validator or focused Python contract checks fail after local recovery.