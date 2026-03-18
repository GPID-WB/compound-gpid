---
name: cg-skill-r-technical
description: "R patterns for technical work: data.table, ggplot2, testthat, roxygen2, package development, plumber APIs, Shiny apps, targets pipelines, httr2 HTTP clients, and renv/pak environment management."
---

# R Technical Practices

Reference skill for technical R development in the GPID team. Covers the full stack for building R packages, REST APIs, Shiny applications, and data pipelines — the infrastructure the analytical team depends on.

*For analytical work (survey analysis, econometrics, welfare measurement, ggplot2 + wbplot), see [`cg-skill-r-analytical`](../cg-skill-r-analytical/SKILL.md).*

## Quick Reference

| Task | Package | Key Pattern |
|------|---------|-------------|
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

*For ggplot2 and World Bank visualization standards (`wbplot`, `theme_wb()`, `WBCOLORS`), load `cg-skill-r-analytical`.*

## Workflows

- [Project Setup](workflows/project-setup.md) — Analysis project layout, renv, .Rprofile
- [data.table Patterns](workflows/data-table-patterns.md) — Core data manipulation
- [Package Development](workflows/package-development.md) — roxygen2, usethis, devtools, renv
- [Plumber APIs](workflows/plumber-api.md) — REST endpoints, middleware, OpenAPI
- [Shiny Apps](workflows/shiny-apps.md) — Modules, reactivity, deployment
- [Targets Pipelines](workflows/targets-pipelines.md) — Reproducible pipelines, dynamic branching
- [Testing with testthat](workflows/testing-testthat.md) — Test structure, assertions, fixtures

## References

- [Anti-Patterns](references/r-technical-anti-patterns.md) — Common mistakes in technical R code
- [Package Decisions](references/r-package-decisions.md) — When to use which package

## When to Load This Skill

Load `cg-skill-r-technical` when working on:
- Data manipulation with `data.table` (`:=`, `DT[i, j, by]`, joins, reshaping)
- R package development (roxygen2, devtools, `R CMD check`, NAMESPACE)
- REST APIs with `plumber` (endpoints, middleware, OpenAPI spec)
- Shiny web applications (modules, reactivity, deployment)
- Reproducible pipelines with `targets` (dependency tracking, dynamic branching)
- HTTP clients with `httr2` (pagination, authentication, retry)
- Writing tests with `testthat` (fixtures, expectations, edition 3)
- Environment management with `renv` or `pak`
- Standard analysis project setup and infrastructure

For survey analysis, econometrics, wbplot visualizations, and welfare measurement, load `cg-skill-r-analytical` instead (or in addition for mixed work).
