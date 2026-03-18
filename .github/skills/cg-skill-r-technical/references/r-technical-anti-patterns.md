# Common R Anti-Patterns — Technical

## data.table Anti-Patterns

| Anti-Pattern | Problem | Fix |
|-------------|---------|-----|
| `ifelse()` on data.table | Slow, coerces types | Use `fifelse()` or `fcase()` |
| `for` loop over rows | Extremely slow | Use vectorized `:=` or `set()` |
| `dt$col <- value` | Creates copy, breaks reference semantics | Use `dt[, col := value]` |
| `apply(dt, 1, fun)` | Converts to matrix, slow | Vectorize or use `dt[, fun(.SD), by = .I]` |
| Repeated `dt[condition]` | Multiple passes | Combine into one `dt[condition, j, by]` |
| Not using keys for joins | Hash join instead of binary search | `setkey()` on join columns |
| `copy()` everywhere | Wastes memory | Only copy when truly needed |
| `dt[, .SD, .SDcols = all_cols]` | Loads full dataset | Specify only needed columns in `.SDcols` |
| `rbindlist()` inside a loop | O(n²) reallocation | Pre-collect a list, then `rbindlist(list_of_dts)` |

## General R Anti-Patterns

| Anti-Pattern | Problem | Fix |
|-------------|---------|-----|
| `T` / `F` | Can be overwritten by user | Always use `TRUE` / `FALSE` |
| `1:length(x)` | Fails when `length(x) == 0` | Use `seq_along(x)` |
| `sapply()` | Unpredictable return type | Use `vapply()` or `lapply()` |
| Nested `if/else` chains | Hard to read | Use `fcase()` or early returns |
| `library()` inside functions | Side effect, pollutes namespace | Use `::` or `@importFrom` |
| Growing vectors in loops | O(n²) reallocation | Pre-allocate or use `lapply()` |
| `setwd()` | Non-reproducible, affects global state | Use `here::here()` or relative paths |
| `rm(list = ls())` | Not reproducible — hides state | Use clean R sessions instead |
| `options(stringsAsFactors)` | Global side effect | Handle per-call; data.table never coerces |
| Suppressing all warnings | Hides real problems | Address root cause |
| `source()` in package `R/` files | Breaks package loading | Use `DESCRIPTION` imports |

## Package Development Anti-Patterns

| Anti-Pattern | Problem | Fix |
|-------------|---------|-----|
| Editing `man/` files directly | Overwritten by roxygen2 | Edit `R/` source only |
| Editing `NAMESPACE` manually | Overwritten by `devtools::document()` | Use `@export`, `@importFrom` |
| Committing `renv/library/` | Large binary files, OS-specific | Only commit `renv.lock` |
| No `.Rbuildignore` for `.cg-docs/` | Knowledge artifacts bundled in package | Add `^\.cg-docs$` to `.Rbuildignore` |
| `devtools::install()` in CI | Installs from local state | Use `devtools::check()` + CRAN-like install |
| Hard-coded paths in tests | Fails on other machines | Use `withr::local_tempdir()` / `testthat::test_path()` |

## API (Plumber) Anti-Patterns

| Anti-Pattern | Problem | Fix |
|-------------|---------|-----|
| No input validation | Crashes on bad input; security risk | Validate all parameters; return 400 on invalid input |
| Business logic in endpoint file | Untestable | Extract to `handlers.R`, test handlers directly |
| Secrets in source code | Security vulnerability | Use `Sys.getenv()` and `.Renviron` |
| No error handling | 500 with stack trace exposed | `tryCatch()` around risky operations |

## Shiny Anti-Patterns

| Anti-Pattern | Problem | Fix |
|-------------|---------|-----|
| Logic in `server()` directly | Bloats server, untestable | Extract to modules and plain functions |
| Forgetting `req()` | Downstream errors on NULL input | `req(input$x)` at start of reactive |
| `reactive()` that returns nothing | Should be `observe()` | Use `observe()` for side effects |
| `<<-` inside Shiny | Breaks reactive graph | Use `reactiveValues()` or module returns |
