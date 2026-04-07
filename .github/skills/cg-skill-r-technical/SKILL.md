---
name: cg-skill-r-technical
description: "R patterns for technical work: collapse for fast statistical computing, data.table for manipulation, roxygen2, package development, plumber APIs (with API testing in references/testing-apis.md), Shiny apps, targets pipelines, httr2 HTTP clients, and renv/pak environment management. Preference hierarchy: collapse > data.table > tidyverse."
---

# R Technical Practices

Reference skill for technical R development in the GPID team. Covers the full stack for building R packages, REST APIs, Shiny applications, and data pipelines. The team's preferred tool hierarchy:

1. **collapse** — for all grouped, weighted, and statistical computations
2. **data.table** — for data manipulation, filtering, joins, reshaping, column creation
3. **tidyverse** — only as fallback when collapse and data.table cannot do the job

No masking — always use explicit `f`-prefixed function names from collapse.

## Quick Reference

| Task | Package | Key Pattern |
|------|---------|-------------|
| Grouped/weighted stats | `collapse` | `fmean(x, g, w)`, `fsum()`, `collap()` |
| Transformations | `collapse` | `fwithin()`, `fbetween()`, `fscale()`, `TRA()` |
| Data manipulation | `data.table` | `DT[i, j, by]` syntax, `:=` for in-place ops |
| Testing | `testthat` | `test_that()` + `expect_*()`, edition 3 |
| Documentation | `roxygen2` | `@param`, `@return`, `@export`, `@examples` |
| Error handling | `rlang` + `cli` | `cli::cli_abort()`, `rlang::try_fetch()` |
| REST APIs | `plumber` | `pr()`, endpoint annotations, OpenAPI spec |
| Web apps | `shiny` | `moduleServer()` / `moduleUI()`, `ns()` |
| Pipelines | `targets` | `tar_target()`, `tar_make()`, dynamic branching |
| HTTP clients | `httr2` | `request() \|> req_perform()`, pagination |
| Fast installs | `pak` | `pak::pkg_install()` for development |
| Reproducibility | `renv` | `renv::init()`, `renv::snapshot()`, lockfiles |

## Workflows

- [data.table + collapse Patterns](workflows/data-table-patterns.md) — Data manipulation and statistical computing
- [Package Development](workflows/package-development.md) — roxygen2, usethis, devtools, renv, pak
- [Plumber APIs](workflows/plumber-api.md) — REST endpoints, middleware, OpenAPI
- [Shiny Apps](workflows/shiny-apps.md) — Modules, reactivity, deployment
- [Targets Pipelines](workflows/targets-pipelines.md) — Reproducible pipelines, dynamic branching
- [HTTP Clients](workflows/http-clients.md) — httr2: authentication, retry, pagination, parallel requests

## References

- [Anti-Patterns](references/r-technical-anti-patterns.md) — Common mistakes in technical R code
- [Testing APIs](references/testing-apis.md) — Plumber endpoint testing and httr2 mock testing
- [renv Reference](references/renv-reference.md) — Dependency isolation, snapshot/restore, lockfile conventions

---

> For comprehensive R testing patterns (testthat, fixtures, mocking, snapshots, BDD, collapse/data.table testing), load `cg-skill-r-testing`.
> For analytical workflows (survey analysis, welfare measurement, fixest, modelsummary, wbplot), use `cg-skill-r-analytical`.
> For the full collapse API (global options, `use.g.names`, all 10 TRA types, GRP structure, attribute preservation), see `cg-skill-r-analytical/references/collapse-reference.md`.
