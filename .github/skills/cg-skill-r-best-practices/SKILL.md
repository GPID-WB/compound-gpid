---
name: cg-skill-r-best-practices
description: "Best practices for R development with data.table, ggplot2, testthat, roxygen2, and renv."
---

# R Best Practices

Reference skill for R development in the DECDG team. Covers `data.table` for data manipulation, `ggplot2` for visualization, `testthat` for testing, `roxygen2` for documentation, and `renv` for environment management.

## Quick Reference

| Task | Package | Key Pattern |
|------|---------|-------------|
| Data manipulation | `data.table` | `DT[i, j, by]` syntax, `:=` for in-place ops |
| Visualization | `ggplot2` | Layered grammar of graphics |
| Testing | `testthat` | `test_that()` + `expect_*()` |
| Documentation | `roxygen2` | `@param`, `@return`, `@export`, `@examples` |
| Error handling | `rlang` + `cli` | `cli::cli_abort()`, `rlang::try_fetch()` |
| Environment | `renv` | `renv::init()`, `renv::snapshot()`, `renv::restore()` |

## Workflows

- [data.table Patterns](workflows/data-table-patterns.md)
- [ggplot2 Conventions](workflows/ggplot2-conventions.md)
- [Testing with testthat](workflows/testing-testthat.md)
- [Package Development](workflows/package-development.md)

## References

- [data.table Cheat Sheet](references/data-table-reference.md)
- [Common Anti-Patterns](references/r-anti-patterns.md)
