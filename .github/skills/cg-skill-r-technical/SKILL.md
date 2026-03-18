---
name: cg-skill-r-technical
description: "R patterns for technical work: data.table, ggplot2, testthat, roxygen2, package development, plumber APIs, Shiny apps, targets pipelines, httr2 HTTP clients, and renv/pak environment management. ALWAYS load this skill when building R packages, plumber APIs, Shiny apps, or targets pipelines, or when any .R/.Rmd/.qmd file is open for technical/infrastructure work involving devtools, usethis, plumber, targets, or shiny."
---

# R Technical Practices

Reference skill for technical R development in the GPID team. Covers the full stack for building R packages, REST APIs, Shiny applications, and data pipelines — the infrastructure the analytical team depends on.

> **Choosing between R skills**: Use this skill for package/infrastructure work. Use `cg-skill-r-analytical` for statistical analysis, survey data, econometrics, and World Bank visualizations. Some plans require both.

## Quick Reference

| Task | Package | Key Pattern |
|------|---------|-------------|
| Data manipulation | `data.table` | `DT[i, j, by]` syntax, `:=` for in-place ops |
| Visualization | `ggplot2` | Layered grammar of graphics; for WB themes (`theme_wb`, `WBCOLORS`), see `cg-skill-r-analytical` |
| Testing | `testthat` | `test_that()` + `expect_*()`, edition 3 |
| Documentation | `roxygen2` | `@param`, `@return`, `@export`, `@examples` |
| Error handling | `rlang` + `cli` | `cli::cli_abort()`, `rlang::try_fetch()` |
| REST APIs | `plumber` | `pr()`, endpoint annotations, OpenAPI spec |
| Web apps | `shiny` | `moduleServer()` / `moduleUI()`, `ns()` |
| Pipelines | `targets` | `tar_target()`, `tar_make()`, dynamic branching |
| HTTP clients | `httr2` | `request() |> req_perform()`, pagination |
| Fast installs | `pak` | `pak::pkg_install()` for development |
| Reproducibility | `renv` | `renv::init()`, `renv::snapshot()`, lockfiles |

## Workflows

- [data.table Patterns](workflows/data-table-patterns.md) — Core data manipulation
- [Package Development](workflows/package-development.md) — roxygen2, usethis, devtools, renv
- [Plumber APIs](workflows/plumber-api.md) — REST endpoints, middleware, OpenAPI
- [Shiny Apps](workflows/shiny-apps.md) — Modules, reactivity, deployment
- [Targets Pipelines](workflows/targets-pipelines.md) — Reproducible pipelines, dynamic branching

## References

- [Anti-Patterns](references/r-technical-anti-patterns.md) — Common mistakes in technical R code
- [Testing with testthat](references/testing-testthat.md) — Test structure, assertions, fixtures
