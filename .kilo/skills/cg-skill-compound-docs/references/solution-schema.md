# Solution Document Schema

## YAML Frontmatter

Every solution document must have this YAML frontmatter:

```yaml
---
date: 2026-03-02                    # Date the solution was captured
title: "Descriptive Title"          # Searchable, specific title
category: "performance-issues"      # One of the 6 categories
language: "R"                       # R | Python | both
tags: [data.table, join, setkey]    # Searchable tags (3-5 recommended)
root-cause: "brief root cause"     # One-sentence root cause
severity: "P2"                      # P0 | P1 | P2 | P3
---
```

### Required Fields

| Field | Type | Values |
|-------|------|--------|
| `date` | Date | `YYYY-MM-DD` |
| `title` | String | Descriptive, specific |
| `category` | String | `bugs`, `build-errors`, `performance-issues`, `testing-patterns`, `data-quality`, `environment-issues`, `git-workflows` |
| `language` | String | `R`, `Python`, `both` |
| `tags` | Array | 3-5 searchable keywords |
| `root-cause` | String | One-sentence summary |
| `severity` | String | `P0`, `P1`, `P2`, `P3` |

### Optional Fields

| Field | Type | Description |
|-------|------|-------------|
| `plan` | String | Relative path to the `.cg-docs/plans/` file this solution originated from (e.g., `.cg-docs/plans/2026-06-09-my-plan.md`) |
| `reviewed-in` | String | Relative path to the `.cg-docs/reviews/` report where this finding was first surfaced. Omit for solutions produced as design-pattern documents rather than through a review. |
| `related` | Array | Cross-links to related solution files or cost artifacts (e.g., `[".cg-docs/solutions/bugs/other.md"]`) |

## Document Body

```markdown
# Title

## Problem
What went wrong? What were the symptoms? Include error messages if applicable.

## Root Cause
Why did it happen? Explain the underlying issue, not just the surface symptom.

## Solution
What fixed it? Include exact code, configuration changes, or steps.

\```r
# Include the actual fix with context
setkey(dt, id)  # This was the missing step
result <- dt[other_dt, on = "id"]
\```

## Prevention
How to avoid this in the future:
- Pattern to follow
- Anti-pattern to avoid
- Standard or convention to adopt

## Related
- \[Link to related solution\]\(../category/related-file.md\)
- \[External documentation\]\(https://example.com\)
```

## Naming Convention

```
YYYY-MM-DD-brief-description.md
```

- Use lowercase
- Use hyphens for spaces
- Keep it short but descriptive
- Include the key concept

### Good Examples
- `2026-03-02-data-table-setkey-for-joins.md`
- `2026-03-05-renv-restore-fails-on-windows.md`
- `2026-03-10-pytest-fixture-scope-confusion.md`

### Bad Examples
- `fix.md` (too vague)
- `2026-03-02-solution.md` (not descriptive)
- `data-table-issue-that-took-me-3-hours-to-debug.md` (too long, no date)
