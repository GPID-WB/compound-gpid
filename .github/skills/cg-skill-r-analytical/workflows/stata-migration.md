# Stata Migration

Patterns for reading Stata files, handling labels, and avoiding the traps that catch economists migrating from Stata to R.

## Reading .dta Files with haven

```r
library(haven)
library(data.table)

# Read a Stata .dta file into a data.table
dt <- as.data.table(read_dta("data/survey_2023.dta"))
```

`read_dta()` preserves Stata metadata: variable labels, value labels, and display formats. This is useful but creates objects that behave differently from plain R vectors.

## Understanding Labelled Vectors

When you read a .dta file, numeric columns with value labels become `haven_labelled` vectors. They look like numbers but carry label metadata.

```r
# After reading a .dta file, check what you have
dt <- as.data.table(read_dta("data/survey.dta"))

# This column looks numeric but has labels attached
class(dt$urban)
# [1] "haven_labelled" "vctrs_vcl"      "double"

# See the labels
print_labels(dt$urban)
# value label
#     0 Rural
#     1 Urban

# The values are still numeric — math works
mean(dt$urban)  # proportion urban
```

### Stata comparison

In Stata, `encode` and value labels are seamless — you never think about them. In R, you must decide: do you want the numeric values or the label text?

## The as_factor() Trap

`as_factor()` converts labelled vectors to R factors using the label text. This is often what you want for categorical variables, but it silently destroys numeric information.

```r
# DANGER: as_factor() on a variable you need as numeric
dt[, urban_factor := as_factor(urban)]
mean(dt$urban_factor)
# Warning: argument is not numeric or logical: returning NA

# SAFE: as_factor() on a genuinely categorical variable
dt[, region_name := as_factor(region)]
table(dt$region_name)
# East Asia    Europe    LAC    MENA    South Asia    SSA
#     1204      892    1567     443          2103   3201
```

**Rule:** Use `as_factor()` only for variables you will treat as categories (region, education level, survey round). Never use it on variables you will use in calculations (urban dummy, income quintile as numeric).

## zap_labels() — When You Want Plain Numbers

When you want clean numeric vectors without any Stata metadata:

```r
# Remove labels from specific columns
dt[, welfare := zap_labels(welfare)]
dt[, weight := zap_labels(weight)]

# Remove labels from all columns at once
dt <- as.data.table(zap_labels(read_dta("data/survey.dta")))
```

**When to use zap_labels():** When the column is purely numeric and you don't need the label metadata. This is the safest approach for welfare aggregates, weights, continuous variables, and any column entering a regression.

## Common Reading Patterns

### Read and immediately clean labels

```r
# Pattern: read, convert categories, strip labels from numerics
dt <- as.data.table(read_dta("data/hh_survey.dta"))

# Convert categorical variables to factors
cat_vars <- c("region", "education", "sector")
dt[, (cat_vars) := lapply(.SD, as_factor), .SDcols = cat_vars]

# Strip labels from numeric variables
num_vars <- c("welfare", "weight", "hhsize", "age")
dt[, (num_vars) := lapply(.SD, zap_labels), .SDcols = num_vars]
```

### Read specific columns only

```r
# haven doesn't support column selection directly — read then subset
dt <- as.data.table(read_dta("data/large_survey.dta"))
dt <- dt[, .(hhid, welfare, weight, region, year)]
```

**Stata comparison:** This is like `use var1 var2 using "file.dta"`. R reads the whole file first, then subsets. For very large .dta files, consider converting to .parquet or .fst for faster I/O.

## Round-Tripping Back to Stata

When you need to send data back to Stata colleagues:

```r
# Write a data.table back to .dta
write_dta(dt, "output/cleaned_data.dta")

# Preserve variable labels if you set them
attr(dt$welfare, "label") <- "Per capita consumption (2017 PPP USD)"
attr(dt$weight, "label") <- "Household survey weight"
write_dta(dt, "output/cleaned_data.dta")
```

### Limitations of write_dta()

- Factor variables are written as labelled numeric (Stata value labels)
- Character strings longer than 2045 characters are truncated
- Date/time handling differs between R and Stata — always verify dates round-trip correctly
- data.table columns with class `IDate` or `POSIXct` should be converted before writing

## Variable Label Utilities

```r
# Get variable label (what Stata shows as "Variable label" in describe)
var_label(dt$welfare)
# [1] "Per capita daily consumption"

# Set variable labels
var_label(dt$welfare) <- "Per capita consumption (2017 PPP USD)"

# Get all variable labels as a named list
var_label(dt)

# Get value labels for a labelled vector
val_labels(dt$region)
```

## Stata-to-R Translation Quick Reference

| Stata | R (data.table + haven) | Notes |
|-------|----------------------|-------|
| `use "file.dta"` | `dt <- as.data.table(read_dta("file.dta"))` | |
| `use var1 var2 using "file.dta"` | Read full, then `dt[, .(var1, var2)]` | |
| `save "file.dta", replace` | `write_dta(dt, "file.dta")` | |
| `describe` | `str(dt)` or `var_label(dt)` | |
| `codebook var` | `summary(dt$var)` + `val_labels(dt$var)` | |
| `tab var` | `table(as_factor(dt$var))` | |
| `decode var, gen(var_str)` | `dt[, var_str := as_factor(var)]` | |
| `encode var, gen(var_num)` | `dt[, var_num := as.integer(as_factor(var))]` | |
| `label list` | `val_labels(dt$var)` | Per variable |
| `label define` | `val_labels(dt$var) <- c(...)` | |
