---
artifact-schema-version: 1
date: 2026-07-31
title: "Malformed Completion Table"
status: active
scope: "Standard"
deviation-policy: "ask"
---

# Plan: Malformed Completion Table

## Objective
Reject malformed completion evidence.
## Context
Negative fixture.
## Requirements
| ID | Requirement | Source |
|----|-------------|--------|
| R1 | Validate evidence. | Test |
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
Malformed evidence fails.
### Verification Surface
| ID | Evidence Required | Required |
|----|-------------------|----------|
| V1 | Tests pass. | yes |
### Constraints
| ID | Constraint | Check |
|----|------------|-------|
| C1 | Fail loudly. | Test |
### Boundaries
- Validation only.
### Iteration Policy
1. Reject malformed tables.
### Blocked-Stop Conditions
- Tests cannot run.
