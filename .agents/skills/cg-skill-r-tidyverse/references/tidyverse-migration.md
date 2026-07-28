# tidyverse ↔ data.table Migration Reference

Side-by-side equivalents for translating between data.table/collapse and tidyverse.

## Data Manipulation

| Operation | data.table | tidyverse |
|-----------|-----------|----------|
| Filter rows | `dt[income > 0]` | `filter(dt, income > 0)` |
| Select columns | `dt[, .(id, income, region)]` | `select(dt, id, income, region)` |
| Add column | `dt[, log_inc := log(income)]` | `mutate(dt, log_inc = log(income))` |
| Delete column | `dt[, col := NULL]` | `select(dt, -col)` |
| Rename column | `setnames(dt, "old", "new")` | `rename(dt, new = old)` |
| Sort rows | `setorder(dt, -income)` | `arrange(dt, desc(income))` |
| Conditional column | `dt[, cat := fcase(x > 5, "hi", default = "lo")]` | `mutate(dt, cat = case_when(x > 5 ~ "hi", .default = "lo"))` |
| Fast if-else | `fifelse(x > 0, "pos", "neg")` | `if_else(x > 0, "pos", "neg")` |

## Aggregation (grouped)

| Operation | data.table + collapse | tidyverse + collapse |
|-----------|----------------------|---------------------|
| Group + weighted mean | `dt[, fmean(x, w=w), by=g]` | `summarize(dt, m=fmean(x,w=w), .by=g)` |
| Multi-function aggregation | `collap(dt, ~g, list(fmean, fsd))` | `summarize(dt, across(cols, list(mean=fmean, sd=fsd)), .by=g)` |
| Row count by group | `dt[, .N, by = g]` | `count(dt, g)` |
| Group + filter | `dt[, .SD[x == max(x)], by = g]` | `slice_max(dt, x, .by = g)` |

Note: `fmean(x, g, w)` syntax with explicit `g` argument works identically in both — you can pass a vector or use `.by` wrapping.

## Joining

| Operation | data.table | tidyverse |
|-----------|-----------|----------|
| Left join | `Y[X, on = "key"]` | `left_join(x, y, by = join_by(key))` |
| Inner join | `X[Y, on = "key", nomatch = NULL]` | `inner_join(x, y, by = join_by(key))` |
| Anti-join | `X[!Y, on = "key"]` | `anti_join(x, y, by = join_by(key))` |
| Renamed keys | `X[Y, on = .(a = b)]` | `left_join(x, y, by = join_by(a == b))` |
| Update join | `X[Y, on="key", col := i.col]` | `left_join(x, select(y, key, col))` |

## Reshaping

| Operation | data.table | tidyverse |
|-----------|-----------|----------|
| Wide to long | `melt(dt, id.vars="id", measure.vars=c("y2020","y2021"))` | `pivot_longer(dt, cols=c(y2020,y2021), names_to="year")` |
| Long to wide | `dcast(dt, id ~ year, value.var="value")` | `pivot_wider(dt, names_from=year, values_from=value)` |

## I/O

| Operation | data.table | tidyverse |
|-----------|-----------|----------|
| Read CSV | `fread("file.csv")` | `read_csv("file.csv")` |
| Write CSV | `fwrite(dt, "file.csv")` | `write_csv(dt, "file.csv")` |
| Read Stata | `haven::read_dta()` | `haven::read_dta()` (same) |
| Read multiple files | `rbindlist(lapply(files, fread))` | `read_csv(files, id="source")` |

## Statistical Computing (use collapse regardless of dialect)

These work identically in both dialects since collapse is class-agnostic:

```r
# Weighted mean — same call in both data.table and tidyverse
fmean(dt$welfare, g = dt$region, w = dt$weight)

# Inside aggregation
# data.table:
dt[, .(mean_welf = fmean(welfare, w = weight)), by = region]

# tidyverse:
dt |> summarize(mean_welf = fmean(welfare, w = weight), .by = region)
```

## Setting Up a Tidyverse Project

```r
# Load packages
library(dplyr)
library(tidyr)
library(readr)
library(stringr)
library(purrr)
library(haven)
library(collapse)  # Always load — for weighted stats
library(ggplot2)
library(wbplot)

# Read data
dt <- read_dta("data/survey.dta") |>
  as_factor() |>
  zap_labels()

# Process
result <- dt |>
  filter(!is.na(welfare), welfare > 0) |>
  mutate(
    poor         = welfare < 2.15,
    welf_log     = log(welfare)
  ) |>
  summarize(
    headcount    = fmean(poor, w = weight),
    mean_welfare = fmean(welfare, w = weight),
    n            = fnobs(welfare),
    .by          = c(region, year)
  )
```
