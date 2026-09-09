# Decision Document Template

Use this template when saving brainstorm decisions to `.cg-docs/brainstorms/`.

## Filename Convention

```
YYYY-MM-DD-brief-description.md
```

Examples:
- `2026-03-02-income-harmonization-approach.md`
- `2026-03-15-dashboard-framework-selection.md`

## Template

```yaml
---
date: YYYY-MM-DD
title: "Descriptive Title"
status: decided
scope: "<Lightweight|Standard|Deep|Focused|Extended|Strategic>"
artifact-schema-version: 1
chosen-approach: "Approach Name"
tags: [tag1, tag2]
---
<!-- Valid status values: decided, in-progress, abandoned -->
```

```markdown
# Title

## Context
What prompted this discussion? What is the problem or opportunity?

## Requirements
Summarized requirements gathered during brainstorming.

- Requirement 1
- Requirement 2
- Requirement 3

## Approaches Considered

### Approach 1: Name
Description of the approach.

**Pros**: ...
**Cons**: ...
**Effort**: Small / Medium / Large

<!-- Add another Approach heading only for each additional materially different
approach that was actually considered. Omit it when only one viable path existed. -->

### Approach 2: Name (optional)
Description of the approach.

**Pros**: ...
**Cons**: ...
**Effort**: Small / Medium / Large

## Decision
Which approach was chosen and why. Reference specific requirements that drove the decision.

## Next Steps
For Software/Data work, list concrete actions for handoff to `/cg-plan`. For
Thinking Partner work, list follow-up decisions, experiments, or stakeholder
consultations instead.

1. Action 1
2. Action 2
3. Action 3
```
