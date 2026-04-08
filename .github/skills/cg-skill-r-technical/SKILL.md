---
name: cg-skill-r-technical
user-invokable: false
description: "R patterns for technical work: roxygen2, package development, plumber APIs (with API testing in references/testing-apis.md), Shiny apps, targets pipelines, httr2 HTTP clients, and renv/pak environment management."
---

# R Technical Practices

Reference skill for technical R development in the GPID team. Covers the full stack for building R packages, REST APIs, Shiny applications, and data pipelines.

For data manipulation and statistical computing, consult the dialect skills loaded via `r.instructions.md` based on your project's `r-syntax` setting in `compound-gpid.local.md`.

## Quick Reference

| Task | Package | Key Pattern |
|------|---------|-------------|
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

> For data manipulation and statistical computing patterns, load `cg-skill-r-collapse`, `cg-skill-r-datatable`, or `cg-skill-r-tidyverse` based on your project's `r-syntax` setting.
> For comprehensive R testing patterns (testthat, fixtures, mocking, snapshots, BDD), load `cg-skill-r-testing`.
> For analytical workflows (survey analysis, welfare measurement, fixest, modelsummary, wbplot), use `cg-skill-r-analytical`.
