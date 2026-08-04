---
name: cg-skill-compound-docs
description: "Knowledge capture system. Categorizes solved problems, tags with metadata, and links related findings for team reuse."
---

# Compound Docs

The compound docs skill powers the `/cg-compound` prompt — the step that makes every solved problem a reusable asset.

## How It Works

When you solve a non-trivial problem, `/cg-compound` captures it as a structured document in `.cg-docs/solutions/[category]/` with YAML frontmatter for discoverability. Over time, this builds a searchable knowledge base that the `cg-learnings-researcher` agent queries before starting new work.

## Categories

| Category | Directory | Use When |
|----------|-----------|----------|
| Build Errors | `.cg-docs/solutions/build-errors/` | Build failures, compilation, package installation |
| Bugs | `.cg-docs/solutions/bugs/` | Bug reproduction, diagnosis, fix verification |
| Performance Issues | `.cg-docs/solutions/performance-issues/` | Slow code, memory, optimization |
| Testing Patterns | `.cg-docs/solutions/testing-patterns/` | Testing strategies, fixtures, mocking |
| Data Quality | `.cg-docs/solutions/data-quality/` | Validation, cleaning, type handling |
| Environment Issues | `.cg-docs/solutions/environment-issues/` | R/Python/Stata environment, dependencies |
| Git Workflows | `.cg-docs/solutions/git-workflows/` | Git operations, branching, CI/CD |

## Workflows

- [Capture a Solution](workflows/capture-solution.md)
- [Search Past Solutions](workflows/search-solutions.md)

## References

- [Solution Document Schema](references/solution-schema.md)
