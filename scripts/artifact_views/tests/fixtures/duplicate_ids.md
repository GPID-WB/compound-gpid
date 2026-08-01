---
artifact-schema-version: 1
date: 2026-07-31
title: "Duplicate IDs"
status: active
scope: "Standard"
deviation-policy: "ask"
---

# Plan: Duplicate IDs

## Objective
Reject duplicate IDs.
## Context
Negative fixture.
## Requirements

| ID | Requirement | Source |
|----|-------------|--------|
| R1 | First requirement. | Test |
| R1 | Duplicate requirement. | Test |

## Implementation Steps
### 1. Implement validation
- **Requirements**: R1
- **Tests**: `pytest`

## Testing Strategy
Focused tests.
## Documentation Checklist
- [ ] Document errors.
## Risks & Mitigations
No material risk.
## Out of Scope
Rendering.
## Completion Contract
### Outcome
Duplicates fail.
### Verification Surface
| ID | Evidence Required | Command/Artifact | Required |
|----|-------------------|------------------|----------|
| V1 | Tests pass. | `pytest` | yes |
### Constraints
| ID | Constraint | Check |
|----|------------|-------|
| C1 | Fail loudly. | Test |
### Boundaries
- Validation only.
### Iteration Policy
1. Reject duplicates.
### Blocked-Stop Conditions
- Tests cannot run.
