---
artifact-schema-version: 1
date: 2026-07-31
title: "Strict Deep Plan"
status: active
scope: "Deep"
brainstorm: null
language: "Python"
estimated-effort: "large"
deviation-policy: "autonomous"
phases: 2
tags: [plan, phased]
---

# Plan: Strict Deep Plan

## Objective

Validate a phased Plan with complete mappings.

## Context

Deep Plans require phase-aware evidence and requirement coverage.

## Requirements

| ID | Requirement | Source |
|----|-------------|--------|
| R1 | Define the schema. | Contract |
| R2 | Validate the schema. | Contract |

## Phase 1: Contract

### 1. Define the schema

- **Requirements**: R1
- **Files**: `scripts/artifact_views/schema.py`
- **Details**: Define immutable schema data.
- **Test Scenarios**: happy path, edge case, error path
- **Tests**: `pytest -q scripts/artifact_views/tests/test_contract.py`
- **Acceptance criteria**: Contract tests pass.

## Phase 2: Validation

### 2. Validate the schema

- **Requirements**: R2
- **Files**: `scripts/artifact_views/validator.py`
- **Details**: Validate all declared mappings.
- **Test Scenarios**: happy path, edge case, error path
- **Tests**: `pytest -q scripts/artifact_views/tests/test_validator.py`
- **Acceptance criteria**: Validator tests pass.

## Testing Strategy

Run focused pytest files for each phase.

## Documentation Checklist

- [ ] Document strict and legacy behavior.

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Mapping drift | Invalid execution | Centralize invariant names. |

## Out of Scope

- Generic Markdown parsing.

## Completion Contract

### Outcome

The phased Plan validates with complete mappings.

### Verification Surface

| ID | Phase | Evidence Required | Command/Artifact | Required |
|----|-------|-------------------|------------------|----------|
| V1 | 1 | Contract tests pass. | `pytest -q scripts/artifact_views/tests/test_contract.py` | yes |
| V2 | 2 | Validator tests pass. | `pytest -q scripts/artifact_views/tests/test_validator.py` | yes |

### Constraints

| ID | Phase | Constraint | Check |
|----|-------|------------|-------|
| C1 | 1 | Markdown remains authoritative. | Contract tests |
| C2 | 2 | Validation is renderer-independent. | Import test |

### Boundaries

- Allowed: schema, model, parser, and validator.
- Out of scope: HTML rendering.

### Iteration Policy

1. Validate after each implementation step.

### Blocked-Stop Conditions

- Required evidence cannot run.
