# Stata Migration with haven

## Reading Stata Files

```r
library(haven)
library(data.table)

# Read .dta file — preserves Stata labels as attributes
dt <- as.data.table(read_dta("data/survey.dta"))

# Check what you have
str(dt)                 # shows haven_labelled types
head(dt)
attributes(dt$educ)     # see labels for a variable
```

## Handling Labelled Variables

```r
# Convert labelled to factor (preserves label text as levels)
dt[, educ_f := as_factor(educ)]

# Convert labelled to numeric (drops labels)
dt[, educ_n := zap_labels(educ)]

# Get the label dictionary
val_labels(dt$educ)     # named vector: label -> value
var_label(dt$educ)      # variable label (metadata)

# Apply to all labelled columns at once
labelled_cols <- names(dt)[sapply(dt, haven::is.labelled)]
dt[, (labelled_cols) := lapply(.SD, as_factor), .SDcols = labelled_cols]
```

## Common Stata → R Translation

| Stata | R (data.table) |
|-------|----------------|
| `use "file.dta"` | `dt <- as.data.table(read_dta("file.dta"))` |
| `gen x = y * 2` | `dt[, x := y * 2]` |
| `replace x = 0 if y == .` | `dt[is.na(y), x := 0]` |
| `egen mean_x = mean(x), by(group)` | `dt[, mean_x := mean(x, na.rm = TRUE), by = group]` |
| `keep if condition` | `dt <- dt[condition]` |
| `drop varlist` | `dt[, c("var1", "var2") := NULL]` |
| `collapse (mean) x, by(group)` | `dt[, .(x = mean(x)), by = group]` |
| `merge 1:1 id using "other.dta"` | `dt_b[dt_a, on = "id"]` (left join) |
| `tab var` | `dt[, .N, by = var][order(var)]` |
| `sum var` | `dt[, .(mean = mean(var), sd = sd(var), n = .N)]` |
| `xtile decile = income, nq(10)` | `dt[, decile := cut(income, quantile(income, 0:10/10), labels = FALSE, include.lowest = TRUE)]` |

## Missing Values

```r
# Stata uses . for missing; haven reads these as NA
# Stata uses .a, .b, ... for extended missing; haven reads as NA with label

# Check for missing
dt[, n_missing := sum(is.na(income)), by = country]

# Stata's "missing" in conditions
dt[!is.na(income)]          # equivalent to Stata: keep if income != .
```

## Writing Back to Stata

```r
# Preserve labelled format for Stata users
write_dta(dt, "data/output.dta")
```

## Common Traps

- `as_factor()` creates ordered factor levels in value-label order, not alphabetical. Use `fct_relevel()` to reorder if needed.
- `read_dta()` returns a tibble by default. Always wrap in `as.data.table()`.
- Stata string variables have a maximum width. `haven` imports them as character without truncation.
- Stata dates are days since 1960-01-01. Convert with `as.Date(x, origin = "1960-01-01")`.
