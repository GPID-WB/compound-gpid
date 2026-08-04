# Approach Comparison

## When to Compare Approaches

After gathering requirements, propose 2-3 approaches when:
- Multiple valid solutions exist
- There are significant trade-offs to consider
- The choice affects architecture or long-term maintainability

## Comparison Template

For each approach, evaluate:

| Dimension | Questions to Answer |
|-----------|-------------------|
| **Feasibility** | Can we build this with current skills and tools? |
| **Effort** | How long will it take? (small: hours, medium: days, large: weeks) |
| **Maintainability** | How easy will this be to modify in the future? |
| **Performance** | Will it handle the expected data size? |
| **Simplicity** | How complex is the implementation? |
| **Reusability** | Can parts be reused in other projects? |
| **Risk** | What could go wrong? How recoverable? |

## Presentation Format

```markdown
### Approach 1: <Name>

**Summary**: One-sentence description.

**How it works**: Brief technical description.

**Pros**:
- Pro 1
- Pro 2

**Cons**:
- Con 1
- Con 2

**Effort**: Small / Medium / Large

**Recommended?**: Yes / No — <reasoning>
```

## Decision Criteria

When recommending an approach, prioritize:

1. **Correctness** — Does it solve the problem correctly?
2. **Simplicity** — Is it the simplest solution that works?
3. **Maintainability** — Can the team maintain it?
4. **Performance** — Does it handle the data scale?
5. **Reusability** — Can parts be reused?

When in doubt, recommend the simpler approach. Complexity can always be added later; it's hard to remove.
