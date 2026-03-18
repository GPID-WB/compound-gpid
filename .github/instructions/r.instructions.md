---
applyTo: "**/*.R,**/*.r,**/*.Rmd"
---

# R Coding Standards

## Package Preference Hierarchy

1. **collapse** — for all grouped, weighted, and statistical computations
2. **data.table** — for data manipulation, filtering, joins, reshaping, column creation
3. **tidyverse** — only as fallback when collapse and data.table cannot do the job

## collapse

- All Fast Statistical Functions share the canonical signature: `FUN(x, g = NULL, w = NULL, TRA = NULL, na.rm = .op[["na.rm"]], use.g.names = TRUE, ...)`.
  - `FUN` is any of: `fsum`, `fprod`, `fmean`, `fmedian`, `fmode`, `fvar`, `fsd`, `fmin`, `fmax`, `fnth`, `ffirst`, `flast`, `fnobs`, `fndistinct`.
- Use `collapse` for grouped and weighted statistics (`fmean`, `fsum`, `fmedian`, `fvar`, `fsd`, `fnth`).
- Use `collap()` for multi-function aggregation with native weight support.
- Use `fwithin()`, `fbetween()`, `fscale()` for group centering/scaling.
- Use `flag()`, `fdiff()`, `fgrowth()` for panel/time-series operations.
- Use `qsu()`, `descr()`, `qtab()` for quick summary statistics.
- Use `GRP()` to pre-compute grouping objects when reusing groups across multiple calls. GRP objects contain 9 elements (group.id, group.sizes, groups, etc.) and avoid redundant recomputation.
- Use `TRA` argument on any Fast Statistical Function for in-place transformation: 10 types (`"replace"`, `"replace_fill"`, `"-"`, `"-+"`, `"/"`, `"%"`, `"+"`, `"*"`, `"%%"`, `"-%%"`). Use `TRA()` as a standalone function to sweep precomputed statistics.
- Use `fselect()`, `fsubset()`, `ftransform()`, `fmutate()` for data manipulation on data frames. `ftransform()` evaluates all RHS simultaneously; `fmutate()` evaluates sequentially (can reference new columns).
- Use `settransform()` or `%=%` for by-reference in-place column creation.
- Use `join()` for simple merges; prefer `data.table` `X[Y, on=]` for complex joins.
- Use `pivot()` for simple reshaping; prefer `data.table` `melt`/`dcast` for complex cases.
- Fast Statistical Functions dispatch via S3 to `.default` (vectors), `.matrix`, `.data.frame`, and hidden `.list` (→ `.data.frame`) methods. They work on vectors, matrices, data frames, and data.tables without conversion.
- collapse preserves attributes on dimension-preserving operations; may drop/adjust on dimension-changing operations (aggregation, `typeof()` change).
- **Never** use `set_collapse(mask = ...)`. Always use explicit `f`-prefixed function names.
- `collapse` and `data.table` are fully interoperable: collapse functions operate directly on data.table objects.

## data.table

- Use `data.table` as the primary data manipulation framework.
- Prefer `data.table` syntax over `dplyr`/`tidyverse` verbs.
- Use `:=` for assignment by reference. Prefer in-place modification over copies.
- Use `.SD`, `.SDcols`, `.N`, `.GRP`, `.BY` idioms fluently.
- Chain operations with `[][]` rather than pipes when natural.
- Use `setkey()` / `setindex()` for performance on repeated lookups and joins.
- Use `fread()` / `fwrite()` for file I/O.
- For joins, use `X[Y]` syntax with `on=` argument. Be explicit about join type with `nomatch=`.
- Use `fifelse()` and `fcase()` instead of `ifelse()` and nested `if/else`.
- Use `set()` for loop-based column assignment when performance matters.

## ggplot2

- Use `ggplot2` for all visualizations.
- Build plots layer by layer: `ggplot() + geom_*() + scale_*() + labs() + theme()`.
- Always label axes and provide a title with `labs()`.
- For published outputs, prefer `wbplot` theme functions (`theme_wb()`, `scale_color_wb_d()`) over generic themes. See `cg-skill-r-analytical` visualization workflow for full guidance.
- For exploratory work, use `theme_minimal()` or a consistent custom theme.
- Use `ggsave()` for saving plots. Specify width, height, and dpi.
- For color scales, prefer colorblind-friendly palettes (e.g., `viridis`, `scale_color_brewer()`).
- Avoid `qplot()`.

## Testing with testthat

- Place tests in `tests/testthat/`.
- Name test files `test-<module>.R` matching source files.
- Use `test_that("descriptive name", { ... })` for each test.
- Use `expect_equal()`, `expect_true()`, `expect_error()`, `expect_warning()`.
- For data.table comparisons, use `expect_identical()` or convert to data.frame first.
- Use `withr::local_tempdir()` or `withr::local_tempfile()` for file-based tests.
- Keep test data inline or in `tests/testthat/fixtures/`.

## Documentation with roxygen2

- Every exported function must have roxygen2 documentation.
- Required tags: `@param`, `@return`, `@export`, `@examples`.
- Use `@importFrom` for selective imports. Avoid `@import` of entire packages.
- Document datasets with `@format` and `@source`.
- Use `@family` to group related functions.
- Write examples that run without external data or side effects.

## Package Development

- Use `devtools` and `usethis` for package scaffolding.
- Manage dependencies with `renv` for project-level isolation.
- Use `renv::snapshot()` after adding/removing packages.
- Commit `renv.lock` to version control. Do NOT commit `renv/library/`.
- NAMESPACE is generated by roxygen2 — never edit manually.
- Use `.Rbuildignore` to exclude non-package files (data, notebooks, docs).

## Error Handling

- Use `rlang::abort()`, `rlang::warn()`, `rlang::inform()` instead of `stop()`, `warning()`, `message()`.
- Use `tryCatch()` or `rlang::try_fetch()` for error recovery.
- Provide informative error messages with context about what went wrong.
- Use `cli::cli_abort()` for user-facing error messages with formatting.

## Style

- Follow a consistent style. Use `styler` or `lintr` for enforcement.
- Use `<-` for assignment, not `=`.
- Use snake_case for function and variable names.
- Limit lines to 80 characters where practical.
- Use explicit `return()` at the end of functions.
- Use `TRUE` / `FALSE`, never `T` / `F`.
