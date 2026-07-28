# Search Past Solutions

## When to Search

Search the knowledge base before:
- Starting a new feature (might reuse past patterns)
- Debugging an issue (might be a known problem)
- Making architectural decisions (might have been discussed before)
- Setting up a new environment (might have past configuration notes)

## Search Strategy

### 1. Check Relevant Category

Start by scanning the most relevant `.cg-docs/solutions/` subdirectory:

| If you're dealing with... | Check |
|--------------------------|-------|
| Build or install failures | `build-errors/` |
| Slow or memory-heavy code | `performance-issues/` |
| Testing questions | `testing-patterns/` |
| Data validation problems | `data-quality/` |
| Environment/dependency issues | `environment-issues/` |
| Git workflow questions | `git-workflows/` |

### 2. Search YAML Frontmatter

Solutions have searchable metadata:

```yaml
---
tags: [data.table, join, performance]
language: R
category: performance-issues
root-cause: "missing setkey before binary search join"
---
```

Search by:
- **Tags**: Specific keywords related to the issue
- **Language**: Filter to R, Python, or both
- **Root cause**: Similar root causes often have similar solutions

### 3. Check Brainstorms

`.cg-docs/brainstorms/` contains past architectural decisions. Relevant when:
- Making similar design choices
- Revisiting a decision that might need updating
- Understanding why something was built a certain way

### 4. Check Plans

`.cg-docs/plans/` contains past implementation plans. Relevant when:
- Building something similar to a past feature
- Looking for testing strategies used before
- Understanding the intended design of existing code

## Reporting

When reporting search results, include:
- Direct link to the relevant document
- One-sentence summary of relevance
- Key takeaway that applies to the current task
- Any anti-patterns identified in past solutions
