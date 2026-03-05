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
status: decided        # draft | decided | superseded
chosen-approach: "Approach Name"
participants:
  - Name 1
  - Name 2
tags: [tag1, tag2]
---
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

### Approach 2: Name
Description of the approach.

**Pros**: ...
**Cons**: ...
**Effort**: Small / Medium / Large

## Decision
Which approach was chosen and why. Reference specific requirements that drove the decision.

## Consequences
What are the implications of this decision? What trade-offs are we accepting?

## Next Steps
Concrete actions for handoff to `/cg-plan`:
1. Action 1
2. Action 2
3. Action 3
```
