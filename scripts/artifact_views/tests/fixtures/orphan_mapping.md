---
artifact-schema-version: 1
date: 2026-07-31
title: "Orphan Mapping"
status: active
scope: "Standard"
deviation-policy: "ask"
---

# Plan: Orphan Mapping

## Objective
Reject unknown requirement mappings.
## Context
Negative fixture.
## Requirements
| ID | Requirement | Source |
|----|-------------|--------|
| R1 | Declared requirement. | Test |
## Implementation Steps
### 1. Implement validation
- **Requirements**: R2
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
Orphans fail.
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
1. Reject orphans.
### Blocked-Stop Conditions
- Tests cannot run.
