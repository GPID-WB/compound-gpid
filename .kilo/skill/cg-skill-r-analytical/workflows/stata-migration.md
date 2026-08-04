# Stata Migration

Patterns for reading Stata files, handling labels, and avoiding the traps that catch economists migrating from Stata to R. Data stays in data.table; statistical computing uses collapse.

## Reading .dta Files with haven

```r
library(haven)
library(data.table)
library(collapse)

# Read a Stata .dta file into a data.table
dt <- as.data.table(read_dta("data/survey_2023.dta"))
```

`read_dta()` preserves Stata metadata: variable labels, value labels, and display formats. This is useful but creates objects that behave differently from plain R vectors.

## Understanding Labelled Vectors

When you read a .dta file, numeric columns with value labels become `haven_labelled` vectors. They look like numbers but carry label metadata.

```r
class(dt$urban)
# [1] "haven_labelled" "vctrs_vcl"      "double"

# See the labels
print_labels(dt$urban)
# value label
#     0 Rural
#     1 Urban

# The values are still numeric — math works
fmean(dt$urban, w = dt$weight)  # weighted proportion urban (collapse)
```

**Note:** collapse functions work on `haven_labelled` vectors — they treat them as numeric. But it's cleaner to strip labels explicitly for variables you'll compute with.

## The as_factor() Trap

`as_factor()` converts labelled vectors to R factors using the label text. This silently destroys numeric information.

```r
# DANGER: as_factor() on a variable you need as numeric
dt[, urban_factor := as_factor(urban)]
fmean(dt$urban_factor)  # Error or NA — can't average a factor

# SAFE: as_factor() on a genuinely categorical variable
dt[, region_name := as_factor(region)]
qtab(dt$region_name)  # collapse cross-tabulation
```

**Rule:** Use `as_factor()` only for variables you will treat as categories. Never for variables entering calculations.

## zap_labels() — When You Want Plain Numbers

```r
# Remove labels from specific columns
dt[, welfare := zap_labels(welfare)]
dt[, weight := zap_labels(weight)]

# Remove labels from all columns at once
dt <- as.data.table(zap_labels(read_dta("data/survey.dta")))
```

## Common Reading Pattern

```r
# Read, convert categories, strip labels from numerics
dt <- as.data.table(read_dta("data/hh_survey.dta"))

# Convert categorical variables to factors
cat_vars <- c("region", "education", "sector")
dt[, (cat_vars) := lapply(.SD, as_factor), .SDcols = cat_vars]

# Strip labels from numeric variables
num_vars <- c("welfare", "weight", "hhsize", "age")
dt[, (num_vars) := lapply(.SD, zap_labels), .SDcols = num_vars]

# Quick weighted summary with collapse
qsu(dt, cols = num_vars, w = ~ weight)
```

## Round-Tripping Back to Stata

```r
# Write a data.table back to .dta
write_dta(dt, "output/cleaned_data.dta")

# Preserve variable labels
attr(dt$welfare, "label") <- "Per capita consumption (2017 PPP USD)"
write_dta(dt, "output/cleaned_data.dta")
```

## Variable Label Utilities

```r
var_label(dt$welfare)           # Get variable label
var_label(dt$welfare) <- "text" # Set variable label
var_label(dt)                   # All labels as named list
val_labels(dt$region)           # Value labels for a labelled vector

# collapse also reads labels: namlab() shows names + labels
namlab(dt)
```

## Stata-to-R Translation Quick Reference

| Stata | R (data.table + haven + collapse) | Notes |
|-------|----------------------------------|-------|
| `use "file.dta"` | `dt <- as.data.table(read_dta("file.dta"))` | |
| `save "file.dta", replace` | `write_dta(dt, "file.dta")` | |
| `describe` | `str(dt)` or `namlab(dt)` | `namlab` from collapse |
| `summarize var [aw=wt]` | `qsu(dt, cols = "var", w = ~ wt)` | collapse |
| `tab var [aw=wt]` | `qtab(dt$var, w = dt$wt)` | collapse |
| `collapse (mean) y [aw=wt], by(g)` | `collap(dt, ~ g, fmean, w = ~ wt, cols = "y")` | collapse |
| `egen mean = mean(y), by(g)` | `fmean(dt$y, g = dt$g, TRA = "replace")` | collapse TRA |
| `bysort g: egen sd = sd(y)` | `fsd(dt$y, g = dt$g, TRA = "replace")` | collapse TRA |
| `xtset id year` | `pdt <- findex_by(dt, id, year)` | collapse panel |
| `L.y` | `flag(pdt$y, 1)` or `L(pdt, 1)` | collapse lag |
| `D.y` | `fdiff(pdt$y)` or `D(pdt)` | collapse diff |
| `decode var, gen(var_str)` | `dt[, var_str := as_factor(var)]` | haven |
| `label list` | `val_labels(dt$var)` | haven |
