---
name: cg-skill-compound-docs
description: "Knowledge capture system. Categorizes solved problems, tags with metadata, and links related findings for team reuse."
---

# Compound Docs

The compound docs skill powers the `/cg-compound` prompt — the step that makes every solved problem a reusable asset.

## How It Works

When you solve a non-trivial problem, `/cg-compound` captures it as a structured document in `docs/solutions/[category]/` with YAML frontmatter for discoverability. Over time, this builds a searchable knowledge base that the `cg-learnings-researcher` agent queries before starting new work.

## Categories

| Category | Directory | Use When |
|----------|-----------|----------|
| Build Errors | `docs/solutions/build-errors/` | Build failures, compilation, package installation |
| Performance Issues | `docs/solutions/performance-issues/` | Slow code, memory, optimization |
| Testing Patterns | `docs/solutions/testing-patterns/` | Testing strategies, fixtures, mocking |
| Data Quality | `docs/solutions/data-quality/` | Validation, cleaning, type handling |
| Environment Issues | `docs/solutions/environment-issues/` | R/Python environment, dependencies |
| Git Workflows | `docs/solutions/git-workflows/` | Git operations, branching, CI/CD |

## Workflows

- [Capture a Solution](workflows/capture-solution.md)
- [Search Past Solutions](workflows/search-solutions.md)

## References

- [Solution Document Schema](references/solution-schema.md)
