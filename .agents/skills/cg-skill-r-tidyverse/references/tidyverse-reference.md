# tidyverse Reference

Modern tidyverse patterns for R 4.1+ and dplyr 1.2+. Always use the native pipe `|>`.

## Core dplyr Verbs

```r
library(dplyr)
library(tidyr)
library(readr)
library(collapse)  # Still used for weighted stats — works on tibbles

# Filter rows
dt |> filter(income > 0, !is.na(region))
dt |> filter(region %in% c("EAP", "SAR"))

# Select columns
dt |> select(id, income, region, year)
dt |> select(starts_with("welfare"), ends_with("_ppp"))
dt |> select(where(is.numeric))

# Add/modify columns
dt |> mutate(log_income = log(income), poor = income < 2.15)

# Rename
dt |> rename(welfare = welf, weight = wt)

# Sort
dt |> arrange(country, year)
dt |> arrange(desc(income))

# Slice
dt |> slice_head(n = 10)
dt |> slice_max(income, n = 5)
dt |> slice_sample(n = 100)
```

## Grouping: Modern .by Argument (dplyr 1.2+)

**Use `.by` inside `mutate()` and `summarize()` instead of `group_by()/ungroup()`.**

```r
# Modern: .by in summarize (no group_by/ungroup needed)
dt |> summarize(
  mean_welfare = fmean(welfare, w = weight),
  n = n(),
  .by = c(region, year)
)

# Modern: .by in mutate
dt |> mutate(
  welfare_centered = fwithin(welfare),
  region_mean      = fmean(welfare, w = weight, TRA = "replace_fill"),
  .by = region
)

# Old pattern (still works, but verbose):
dt |>
  group_by(region, year) |>
  summarize(mean_welfare = fmean(welfare, w = weight), .groups = "drop")
```

**Key rule**: `.by` is transient — the result is never grouped. `group_by()` returns a grouped tibble that must be explicitly `ungroup()`-ed. Prefer `.by`.

## Weighted Statistics with collapse (use in all R dialects)

collapse functions work natively on tibbles:

```r
# Weighted mean by group (use collapse — no tidyverse native equivalent)
dt |>
  summarize(
    mean_welfare = fmean(welfare, w = weight),
    sd_welfare   = fsd(welfare, w = weight),
    median_welf  = fmedian(welfare, w = weight),
    n            = fnobs(welfare),
    .by = region
  )

# Weighted transformation (collapse functions work natively on tibbles)
dt |> mutate(
  welf_centered = fwithin(welfare, w = weight),
  welf_lag1     = flag(welfare, 1, t = year),   # t= required for correct time-lag
  .by = country
)
```

> **Note**: Load `cg-skill-r-collapse` for the full weighted statistics reference. `fmean`, `fsum`, `fmedian`, and `flag` work identically on tibbles and are the recommended approach for weighted/panel operations even in tidyverse projects.

## Joining: join_by() (dplyr 1.2+)

```r
# Left join (preferred — all rows from x)
left_join(orders, customers, by = join_by(cust_id))

# Inner join
inner_join(x, y, by = join_by(id))

# Anti-join
anti_join(x, y, by = join_by(id))

# Multiple keys
left_join(x, y, by = join_by(country, year))

# Renamed keys
left_join(x, y, by = join_by(id == customer_id))

# Non-equi join (dplyr 1.2+)
left_join(x, y, by = join_by(between(date, start, end)))

# Inequality join
left_join(x, y, by = join_by(date >= start, date <= end))
```

**Note**: Old `by = c("key" = "key2")` still works but `join_by()` is more readable.

## across() and pick()

```r
# Apply a function to multiple columns
dt |> mutate(across(starts_with("welfare"), log))
dt |> mutate(across(where(is.numeric), ~ . / 1000))

# Apply with naming
dt |> mutate(across(c(welfare, income), list(log = log, sq = ~ .^2),
                    .names = "{.col}_{.fn}"))

# Summarize multiple columns
dt |> summarize(across(c(welfare, income), fmean), .by = region)

# pick(): select columns without reducing (replacement for across()+c())
dt |> mutate(row_mean = rowMeans(pick(starts_with("y_"))))
```

## Reshaping with tidyr

```r
# Wide to long
dt |> pivot_longer(
  cols           = starts_with("welfare_"),
  names_to       = "year",
  names_prefix   = "welfare_",
  values_to      = "welfare"
)

# Long to wide
dt |> pivot_wider(
  names_from  = year,
  values_from = welfare
)

# Multiple value columns
dt |> pivot_wider(
  names_from   = indicator,
  values_from  = c(value, se)
)
```

## I/O with readr

```r
# Read CSV (returns tibble by default)
dt <- read_csv("file.csv")
dt <- read_csv("file.csv", col_types = cols(id = col_character()))

# Read multiple files
files <- list.files("data/", pattern = "\\.csv$", full.names = TRUE)
dt    <- read_csv(files, id = "source_file")

# Write
write_csv(dt, "output.csv")
write_csv(dt, "output.csv.gz")  # Auto-compresses from extension

# Read Stata (dialect-neutral — same in both tidyverse and data.table projects)
dt <- haven::read_dta("file.dta")
dt <- haven::read_dta("file.dta") |> haven::as_factor()  # Convert labeled vars to factor
```

## Conditional Logic

```r
# if_else() — type-safe vectorized if-else (both arms must be same type)
mutate(dt, category = if_else(income > 50000, "high", "low"))
mutate(dt, value    = if_else(is.na(x), 0, x))

# case_when() — CASE WHEN equivalent
mutate(dt, category = case_when(
  income > 100000 ~ "high",
  income >  50000 ~ "medium",
  income >  20000 ~ "low",
  .default         = "very_low"
))

# coalesce() — replace NAs
mutate(dt, filled = coalesce(primary, secondary, 0))
```

## String Manipulation with stringr

```r
library(stringr)

# Detect pattern
filter(dt, str_detect(name, "^World"))

# Extract portion
mutate(dt, code = str_sub(id, 1, 3))
mutate(dt, code = str_extract(id, "[A-Z]{3}"))

# Replace
mutate(dt, name = str_replace_all(name, "_", " "))
mutate(dt, name = str_to_lower(name))

# Trim
mutate(dt, name = str_trim(name))

# Combine
mutate(dt, label = str_glue("{country} ({year})"))
```

## Iteration with purrr

```r
library(purrr)

# Apply function to each element of a list
results <- map(country_list, ~ read_csv(paste0("data/", .x, ".csv")))

# Return data frame
results_df <- map_dfr(country_list, ~ {
  read_csv(paste0("data/", .x, ".csv")) |>
    mutate(country = .x)
})

# Apply function to two arguments in parallel
map2(x_list, y_list, ~ .x + .y)

# Filter list elements
keep(results, ~ nrow(.) > 0)
discard(results, ~ is.null(.))

# Safely handle errors
safe_read <- safely(read_csv)
results   <- map(files, safe_read)
good      <- keep(results, ~ is.null(.$error))
```

## GPID-Specific Patterns in Tidyverse

### PPP Welfare Calculation

```r
# Validate before transforming (same logic as data.table mode)
stopifnot(
  !anyNA(dt$cpi_deflator), all(dt$cpi_deflator > 0),
  !anyNA(dt$ppp_factor),   all(dt$ppp_factor   > 0)
)

dt <- dt |>
  mutate(
    welf_pc_lcu_nom  = consumption_lcu_nom / hhsize,
    welf_pc_lcu_real = welf_pc_lcu_nom / cpi_deflator,
    welf_pc_ppp      = welf_pc_lcu_real / ppp_factor,
    welf_pc_ppp_day  = welf_pc_ppp / 365
  )
```

### Poverty Aggregation

```r
# FGT(0) headcount ratio (weighted) — use collapse even in tidyverse mode
dt |>
  summarize(
    headcount = fmean(poor, w = weight),
    n_poor    = fsum(poor, w = weight),
    n_total   = fsum(weight),
    .by = c(region, year)
  )
```
