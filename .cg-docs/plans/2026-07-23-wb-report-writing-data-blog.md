---
date: 2026-07-23
title: "WB report writing: Data blog posts"
status: completed
scope: "Standard"
brainstorm: ".cg-docs/brainstorms/2026-07-23-wb-institutional-report-writing-skill.md"
language: "both"
estimated-effort: "medium"
deviation-policy: "ask"
phases: 2
parent-plan: ".cg-docs/plans/2026-07-23-wb-institutional-report-writing-skill.md"
completed-date: 2026-07-24
tags: [skill, writing, world-bank, data-blog]
---

# Plan: Data Blog Post Pattern

## Objective

Add and evaluate an accessible World Bank Data Blog pattern whose engagement
comes from explanation and structure, never invented hooks or facts.

## Context

Parent Phase 1 is required. This child owns Data Blog exemplar approval,
public-reader rules, factual-fidelity evals, and fixed acceptance evidence.

## Requirements

| ID | Requirement | Source |
|----|-------------|--------|
| R1 | Record 2-3 approved Data Blog exemplars and publication status requirements. | Parent R6 |
| R2 | Encode accessible headline, grounded hook, explanatory arc, chart integration, plain-language methods, limitations, sources, and conclusion. | Brainstorm: Data Blog Posts |
| R3 | Cover all seven operations and technical-to-blog adaptation. | Parent R2 |
| R4 | Ban invented anecdotes, quotes, figures, dates, causal explanations, and stronger claims than the source. | Parent R3-R4, R9 |
| R5 | Evaluate accessibility, factual fidelity, source visibility, caveat retention, and human acceptance. | Parent R10 |
| R6 | Keep v1 English/basic `.qmd` only. | Parent R12 |

## Implementation Steps

## Phase 1: Approved Pattern

### 1. Approve the Data-Blog Source Pack

- **Requirements**: R1, R4
- **Files**: `.github/skills/cg-skill-wb-report-writing/references/source-packs/data-blog-post.json`
- **Details**: Record approved exemplars, relevant sections, publication-status requirements, authority rationale, and retrieval dates.
- **Test Scenarios**: Missing publication status; inaccessible exemplar; unresolved terminology.
- **Tests**: `python scripts/validate_wb_writing_skill.py --type data-blog-post --require-approved`
- **Acceptance criteria**: The source pack passes validation.

### 2. Implement and Behavior-Test the Data-Blog Reference

- **Requirements**: R2, R3, R4, R6
- **Files**: `.github/skills/cg-skill-wb-report-writing/references/data-blog-post.md`; `.github/skills/cg-skill-wb-report-writing/evals/types/data-blog-post.json`; `scripts/tests/test_wb_writing_data_blog_post.py`
- **Details**: Encode public-reader structure, chart/source rules, all operations, accessible method explanation, caveat retention, and language/full-Quarto negative cases.
- **Test Scenarios**: Draft from chart notes; absent chart source; catchy invented statistic; simplify uncertainty; technical-to-blog adaptation; preliminary estimate.
- **Tests**: `python -m pytest scripts/tests/test_wb_writing_data_blog_post.py -q`
- **Acceptance criteria**: Focused tests pass and engagement never relies on invented specifics.

## Phase 2: Evaluation and Acceptance

### 3. Evaluate Data-Blog Fidelity and Guardrails

- **Requirements**: R3, R4, R5, R6
- **Files**: `.github/skills/cg-skill-wb-report-writing/evals/results/data-blog-post.json`; `.github/skills/cg-skill-wb-report-writing-data-blog-post-workspace/**`
- **Details**: Run paired evals, grade accessibility, factual fidelity, source visibility, and caveat retention; collect public-reader quality review and persist fixed results.
- **Test Scenarios**: Invented hook/quote; missing source; overstated causality; preliminary number; multilingual/full-Quarto near misses.
- **Tests**: `python scripts/validate_wb_writing_skill.py --type data-blog-post --require-eval-pass`
- **Acceptance criteria**: Assertions pass and human review accepts accessibility and fidelity.

## Testing Strategy

Use source validation, focused per-type Python checks, paired adversarial evals,
factual/accessibility grading, and human review.

## Documentation Checklist

- [ ] Record exemplar authority and retrieval dates.
- [ ] Document hook, chart, source, method, and caveat rules.
- [ ] Verify nested links.

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Engaging prose invents facts or anecdotes | Explicit prohibition and adversarial grading |
| Simplification drops uncertainty | Caveat-retention assertions |
| Chart prose loses source/status | Required source and publication-status checks |

## Out of Scope

Image production, web publishing, language translation, data retrieval, and
full Quarto execution.

## Completion Contract

### Outcome

The Data Blog pattern is source-approved, accessible, factual, tested,
evaluated, and accepted without invented hooks or weakened caveats.

### Verification Surface

| ID | Phase | Evidence Required | Command/Artifact | Required |
|----|-------|-------------------|------------------|----------|
| V1 | 1 | Approved Data Blog source pack | `python scripts/validate_wb_writing_skill.py --type data-blog-post --require-approved` | yes |
| V2 | 1 | Data Blog behavior passes | `python -m pytest scripts/tests/test_wb_writing_data_blog_post.py -q` | yes |
| V3 | 2 | Data Blog eval and acceptance pass | `python scripts/validate_wb_writing_skill.py --type data-blog-post --require-eval-pass` | yes |
| V4 | final | Fixed Data Blog evidence is complete | `python scripts/validate_wb_writing_skill.py --type data-blog-post --require-approved --require-eval-pass` | yes |

### Constraints

| ID | Phase | Constraint | Check |
|----|-------|------------|-------|
| C1 | final | No invented facts, anecdotes, quotes, dates, or causality. | Fixed adversarial result record |
| C2 | final | Sources, status markers, and caveats remain visible. | Eval grading record |
| C3 | final | English/basic `.qmd` only. | Negative eval record |

### Boundaries

- Allowed: Data Blog source pack, reference, evals/results, and tests.
- Out of scope: other type references and parent integration.

### Iteration Policy

1. Stop if source or publication-status approval is incomplete.
2. Iterate until objective and human gates pass.
3. Ask before changing shared contracts.

### Blocked-Stop Conditions

- Parent Phase 1 is incomplete.
- Data Blog exemplars or publication status are incomplete.
- An eval invents a hook/fact or loses a caveat/source.
- Required validator or focused Python contract checks fail after local recovery.