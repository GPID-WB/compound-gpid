# tidyverse Style Guide

Style conventions for tidyverse R code in GPID projects.

## Pipe

Always use the **native pipe** `|>` (R 4.1+). Never use magrittr `%>%`.

```r
# Right
dt |> filter(x > 0) |> mutate(y = log(x))

# Wrong
dt %>% filter(x > 0) %>% mutate(y = log(x))
```

## Line Length and Breaking

Break long pipes onto multiple lines. Each verb on its own line, indented 2 spaces:

```r
result <- input_data |>
  filter(year >= 2010, !is.na(welfare)) |>
  mutate(
    log_welfare = log(welfare),
    poor        = welfare < 2.15
  ) |>
  summarize(
    headcount = fmean(poor, w = weight),
    n         = n(),
    .by       = c(region, year)
  )
```

## Naming

Follow snake_case throughout:

```r
# Right
welfare_per_capita <- ...
compute_headcount <- function(x, w) ...

# Wrong
welfarePerCapita <- ...
ComputeHeadcount <- function(x, w) ...
```

- **Functions**: verb + noun — `compute_poverty_gap()`, `read_survey()`, `filter_outliers()`
- **Data frames/tibbles**: noun — `survey_data`, `poverty_estimates`, `country_metadata`
- **Boolean columns**: start with `is_` or `has_` — `is_poor`, `has_welfare`

## Grouping

Prefer `.by` over `group_by()/ungroup()`:

```r
# Right
dt |> summarize(mean_y = mean(y), .by = group)

# Acceptable (when multiple operations share the same group)
dt |>
  group_by(region, year) |>
  summarize(mean_y = mean(y), .groups = "drop")

# Wrong (forgetting ungroup)
dt |>
  group_by(region) |>
  mutate(centered = y - mean(y))
# Result is still grouped! Causes unexpected behavior downstream.
```

## Function Signatures

```r
# Document with roxygen2
#' Compute weighted poverty headcount
#'
#' @param dt A tibble with columns `welfare`, `weight`, `region`.
#' @param line Poverty line in daily PPP USD. Default 2.15.
#' @return A tibble with columns `region`, `headcount`, `n`.
#' @examples
#' compute_headcount(survey_data)
#' compute_headcount(survey_data, line = 3.65)
compute_headcount <- function(dt, line = 2.15) {
  dt |>
    mutate(poor = welfare < line) |>
    summarize(
      headcount = fmean(poor, w = weight),
      n         = n(),
      .by       = region
    )
}
```

## Error Handling

```r
# Use cli + rlang for informative errors
library(cli)
library(rlang)

# Input validation at function boundaries
validate_welfare <- function(dt) {
  if (!all(c("welfare", "weight") %in% names(dt))) {
    cli::cli_abort("Column {.field welfare} and {.field weight} must exist in {.arg dt}.")
  }
  if (any(dt$welfare < 0, na.rm = TRUE)) {
    cli::cli_abort("Negative welfare values detected. PPP unit mismatch?")
  }
}
```

## Spacing and Indentation

```r
# Spaces around =, <-, |>, ~
x <- 1
f(x = 1, y = 2)
dt |> filter(x > 0)

# No space before :
list(a = 1, b = 2)

# Align = in multi-line function calls for readability
dt |>
  mutate(
    log_welfare = log(welfare),
    poor        = welfare < 2.15,
    year_group  = year %/% 5 * 5
  )
```
