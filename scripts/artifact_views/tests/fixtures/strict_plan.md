---
artifact-schema-version: 1
date: 2026-07-31
title: "Strict Plan"
status: active
scope: "Standard"
brainstorm: null
language: "Python"
estimated-effort: "medium"
deviation-policy: "ask"
tags: [plan, parser]
---

# Plan: Strict Plan

## Objective

Validate one canonical Plan before rendering.

## Context

The validator must operate without renderer dependencies.

## Requirements

| ID | Requirement | Source |
|----|-------------|--------|
| R1 | Parse the supported grammar. | Contract |
| R2 | Validate complete requirement coverage. | Contract |

## Implementation Steps

### 1. Implement parsing and validation

- **Requirements**: R1, R2
- **Files**: `scripts/artifact_views/parser.py`
- **Details**: Parse blocks and validate mappings.
- **Test Scenarios**: happy path, edge case, error path
- **Tests**: `pytest -q scripts/artifact_views/tests/test_parser.py`
- **Acceptance criteria**: Both requirements validate.

## Testing Strategy

Use focused pytest fixtures.

## Documentation Checklist

- [ ] Document the public validation API.

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Ambiguous input | Missing content | Fail with a source span. |

## Out of Scope

- Rendering HTML.

## Completion Contract

### Outcome

One Plan validates independently of rendering.

### Verification Surface

| ID | Evidence Required | Command/Artifact | Required |
|----|-------------------|------------------|----------|
| V1 | Parser tests pass. | `pytest -q scripts/artifact_views/tests/test_parser.py` | yes |

### Constraints

| ID | Constraint | Check |
|----|------------|-------|
| C1 | Markdown remains authoritative. | Contract tests |

### Boundaries

- Allowed: parser and validator code.
- Out of scope: HTML rendering.

### Iteration Policy

1. Reject ambiguous structures.

### Blocked-Stop Conditions

- Required source coverage cannot be proven.
