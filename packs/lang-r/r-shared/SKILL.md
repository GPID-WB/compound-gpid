---
name: r-shared
description: "Read first for any R work: before writing, reviewing or debugging R code in .R, .Rmd or .qmd files. Says which R skills to load for the project's dialect (the r-syntax setting: data.table-collapse or tidyverse) and for the kind of work, and holds the base R rules every dialect shares: assignment and naming style, line length, TRUE/FALSE, and rlang/cli error handling."
---

# R: Where to Start, and Base Style

Read this skill before any R work. It says which other R skills to load, and then gives the style rules that apply in all projects regardless of the `r-syntax` setting.

## Which R Skills to Load

Ported from version 1's `r.instructions.md`, which applied to `*.R`, `*.r` and `*.Rmd` files.

Check the project's `r-syntax` setting: `settings` → `lang-r` → `r-syntax` in `.cg-docs/config.json`, which `cg.py status` prints as `lang-r.r-syntax=...` (in a version 1 project, the `r-syntax` field of `compound-gpid.local.md`). Then load the appropriate dialect skill(s):

- `r-syntax: "data.table-collapse"` (or field absent → default): load `r-collapse` AND `r-datatable`
- `r-syntax: "tidyverse"`: load `r-tidyverse`
- Any other value: default to `data.table-collapse` behavior and warn the user. Accepted values: `"data.table-collapse"` and `"tidyverse"`.

Regardless of dialect, also load:

- `r-visualization` when writing or reviewing visualization code (`ggplot2`, `wbplot`)
- `r-analytical` for domain-specific analytical work (survey analysis, welfare measurement, econometrics, Stata migration)
- `r-technical` for infrastructure work (packages, plumber, Shiny, targets, httr2, renv)
- `r-testing` when writing, reviewing, or debugging R tests

## Assignment and Naming

- Use `<-` for assignment, not `=` (except in function argument defaults).
- Use `snake_case` for function and variable names.
- Use `UPPER_SNAKE_CASE` for global constants.
- Avoid abbreviations unless domain-standard (`dt` for data.table, `df` for data frame are acceptable).
- Use `TRUE` / `FALSE`, never `T` / `F`.

## Formatting

- Limit lines to 80 characters where practical.
- Use `styler` or `lintr` for automated enforcement.
- Use explicit `return()` at the end of non-trivial functions.
- One statement per line — do not chain multiple assignments on one line.

## Error Handling

- Use `rlang::abort()`, `rlang::warn()`, `rlang::inform()` instead of `stop()`, `warning()`, `message()`.
- Use `tryCatch()` or `rlang::try_fetch()` for error recovery.
- Provide informative error messages with context about what went wrong and what was expected.
- Use `cli::cli_abort()` for user-facing error messages with formatting.

## Documentation

- Every exported function needs roxygen2 documentation: `@param`, `@return`, `@export`, `@examples`.
- Use `@importFrom` for selective imports. Avoid `@import` of entire packages.
- Document datasets with `@format` and `@source`.
- Use `@family` to group related functions.
- Write examples that run without external data or side effects.
