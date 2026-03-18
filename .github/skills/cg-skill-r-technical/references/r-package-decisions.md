# Package Decisions

When multiple packages solve the same problem, this reference documents which to use and why. These are the GPID team standards — not general R recommendations.

## Data Manipulation

| Task | Use | Not |
|------|-----|-----|
| Data wrangling, joins, reshaping | `data.table` | `dplyr`, base R `merge()` |
| In-place column creation | `data.table` `:=` | `dplyr::mutate()` |
| Fast conditional replacement | `data.table::fifelse()`, `fcase()` | `base::ifelse()` |
| File reading (CSV, fixed-width) | `data.table::fread()` | `readr::read_csv()`, `utils::read.csv()` |
| Read Stata `.dta` files | `haven::read_dta()` | `foreign::read.dta()` |

**Why data.table over dplyr:** ~5–10× faster on large datasets, lower memory through reference semantics, no tibble footprint complications. The GPID team works with datasets of tens of millions of rows where this matters.

## Package Management

| Task | Use | Not |
|------|-----|-----|
| Install packages in development | `pak::pkg_install()` | `install.packages()` |
| Install from GitHub | `pak::pkg_install("owner/repo")` | `devtools::install_github()` |
| Environment lockfile | `renv` | `packrat`, manual tracking |
| Check if package available | `pak::pkg_is_installed()` | `requireNamespace()` ad hoc |

**Why pak over install.packages:** `pak` resolves dependencies faster, handles GitHub installs, shows cleaner progress, and integrates with `renv`.

## Error Handling and Messaging

| Task | Use | Not |
|------|-----|-----|
| User-facing errors | `cli::cli_abort()` | `stop()` |
| User-facing warnings | `cli::cli_warn()` | `warning()` |
| Informational messages | `cli::cli_inform()` | `message()`, `cat()`, `print()` |
| Catch errors | `rlang::try_fetch()` | `tryCatch()` |
| Check inputs | `rlang::check_required()`, `cli::cli_abort()` | `stopifnot()` |

**Why cli over base:** `cli` formats messages with color, bolding, bullet lists, and inline variable interpolation. `stopifnot()` produces cryptic messages; `cli::cli_abort()` produces actionable ones.

## Testing

| Task | Use | Not |
|------|-----|-----|
| Unit tests | `testthat` (edition 3) | `tinytest`, `RUnit` |
| Test data fixtures | Inline `data.table()` in test | External CSVs for small tests |
| Code coverage | `covr` | manual tracking |

## Web APIs

| Task | Use | Not |
|------|-----|-----|
| Build a REST API | `plumber` | `RestRserve`, `ambiorix` |
| Make HTTP requests | `httr2` | `httr` (deprecated), `curl` directly |

**Why httr2 over httr:** `httr2` has a pipeline interface, retry logic, rate limiting, and OAuth2 support built in. `httr` is no longer actively developed.

## Pipelines

| Task | Use | Not |
|------|-----|-----|
| Reproducible analysis pipeline | `targets` | numbered `source()` scripts, `drake` |
| Dynamic branching | `targets` dynamic branching | shell scripts |

**Why targets over drake:** `targets` is the official successor to `drake`, actively maintained, with better performance and cleaner syntax. `drake` is deprecated.

## Shiny

| Task | Use | Not |
|------|-----|-----|
| Interactive web app | `shiny` with modules | `flexdashboard` for non-trivial apps |
| Production deployment | `shiny` + `rsconnect` | `RMarkdown` runtime: shiny |

## Econometrics (cross-reference)

For econometric package decisions (`fixest` vs `lm()`, `srvyr` vs `survey`, `convey` for inequality), see the [Analytical R Anti-Patterns](../../cg-skill-r-analytical/references/r-analytical-anti-patterns.md) and [Survey Analysis workflow](../../cg-skill-r-analytical/workflows/survey-analysis.md).
