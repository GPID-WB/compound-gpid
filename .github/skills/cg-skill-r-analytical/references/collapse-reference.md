# collapse Quick Reference

`collapse` is the team's primary tool for statistical computing. It provides fast C/C++-based grouped and weighted operations that work directly on data.table objects. Always use explicit `f`-prefixed names — never use `set_collapse(mask = ...)`.

## Global Options

collapse uses an internal options environment (`.op`) that all Fast Statistical Functions read from. The most important option is `na.rm`:

```r
# All f* functions default to na.rm = .op[["na.rm"]] — TRUE by default
fmean(c(1, 2, NA, 4))          # Returns 2.333... (NA skipped)

# Change the global default for the whole session
set_collapse(na.rm = FALSE)
fmean(c(1, 2, NA, 4))          # Returns NA (NA propagates, like base R)

# Override per call
fmean(c(1, 2, NA, 4), na.rm = TRUE)   # Returns 2.333...
fmean(c(1, 2, NA, 4), na.rm = FALSE)  # Returns NA

# Restore default
set_collapse(na.rm = TRUE)
```

**Warning for welfare work**: All FGT, Gini, and weighted mean patterns in these skills assume `na.rm = TRUE` (the default). If you call `set_collapse(na.rm = FALSE)`, those patterns will silently return `NA` instead of estimates. Do not change the global `na.rm` setting in scripts that contain welfare calculations.

Other useful global options:

```r
# View all current options
get_collapse()

# Set multiple options at once
set_collapse(na.rm = TRUE, sort = TRUE, nthreads = 4)

# Common options:
# na.rm     — default NA handling for all f* functions (default TRUE)
# sort      — whether grouped results are sorted by group (default TRUE)
# nthreads  — number of OpenMP threads for parallel computation (default 1)
# digits    — rounding digits for print methods (default 4)
```

## Fast Statistical Functions

All Fast Statistical Functions share the same canonical signature:

```r
FUN(x, g = NULL, w = NULL, TRA = NULL, na.rm = .op[["na.rm"]], use.g.names = TRUE, ...)
```

Where `FUN` is any of: `fsum`, `fprod`, `fmean`, `fmedian`, `fmode`, `fvar`, `fsd`, `fmin`, `fmax`, `fnth`, `ffirst`, `flast`, `fnobs`, `fndistinct`.

- `use.g.names = TRUE` — when aggregating and `g` is a single vector, adds group labels as names to the result. Set to `FALSE` to suppress names for programmatic use.

| Function | Purpose | Example |
|----------|---------|---------|
| `fmean()` | Weighted mean | `fmean(dt$welfare, g = dt$region, w = dt$weight)` |
| `fmedian()` | Weighted median | `fmedian(dt$welfare, w = dt$weight)` |
| `fsum()` | Weighted sum (total) | `fsum(dt$welfare, g = dt$region, w = dt$weight)` |
| `fvar()` | Weighted variance | `fvar(dt$welfare, g = dt$region, w = dt$weight)` |
| `fsd()` | Weighted std deviation | `fsd(dt$welfare, g = dt$region, w = dt$weight)` |
| `fnth()` | Weighted n-th quantile | `fnth(dt$welfare, 0.25, g = dt$region, w = dt$weight)` |
| `fmin()` / `fmax()` | Grouped min/max | `fmin(dt$welfare, g = dt$region)` |
| `ffirst()` / `flast()` | Grouped first/last | `ffirst(dt$welfare, g = dt$region)` |
| `fnobs()` | Observation count | `fnobs(dt$welfare, g = dt$region)` |
| `fndistinct()` | Distinct value count | `fndistinct(dt$region)` |
| `fprod()` | Grouped product | `fprod(dt$growth_factor, g = dt$region)` |
| `fmode()` | Weighted mode | `fmode(dt$sector, g = dt$region, w = dt$weight)` |

### Key Arguments

- `g` — grouping: a vector, list of vectors, or `GRP` object
- `w` — weights: a numeric vector
- `TRA` — transform instead of aggregate (10 types, see TRA table below)
- `na.rm` — default `TRUE` in collapse (unlike base R)
- `use.g.names` — add group labels as names when aggregating (default `TRUE`)

### TRA: Grouped Replace and Sweep

The `TRA` argument performs in-place transformation instead of aggregation. Available on all Fast Statistical Functions. There are 10 transformation types:

| Code | Name | Operation |
|------|------|-----------|
| `"replace_fill"` | Replace (fill) | Replace all values with group statistic (incl. NA) |
| `"replace"` | Replace | Replace non-NA values with group statistic |
| `"-"` | Subtract | Center: `x - stat` |
| `"-+"` | Subtract-add | Subtract group stat, add overall stat |
| `"/"` | Divide | Scale: `x / stat` |
| `"%"` | Percentage | `x / stat * 100` |
| `"+"` | Add | `x + stat` |
| `"*"` | Multiply | `x * stat` |
| `"%%"` | Modulus | `x %% stat` |
| `"-%%"` | Subtract modulus | `x - (x %% stat)` |

`TRA()` can also be called as a standalone function:

```r
# Standalone TRA: sweep precomputed statistics back
group_means <- fmean(dt$welfare, g = dt$region)
TRA(dt$welfare, group_means, FUN = "-", g = dt$region)  # Center using precomputed means
```

Common patterns via Fast Statistical Functions:

```r
# Replace each value with its group mean (like Stata's egen mean)
fmean(dt$welfare, g = dt$region, TRA = "replace")

# Center within groups (demean)
fmean(dt$welfare, g = dt$region, TRA = "-")

# Compute percentage of group total
fsum(dt$welfare, g = dt$region, TRA = "%")

# Scale by group standard deviation
fsd(dt$welfare, g = dt$region, TRA = "/")

# Subtract group mean, add back overall mean (preserves level)
fmean(dt$welfare, g = dt$region, TRA = "-+")
```

## Aggregation with collap()

```r
# Simple aggregation — weighted mean by region
collap(dt, ~ region, fmean, w = ~ weight)

# Multiple grouping variables
collap(dt, ~ region + year, fmean, w = ~ weight)

# Multiple functions
collap(dt, ~ region, list(fmean, fsd, fnobs))

# Custom: different functions for different columns
collap(dt, ~ region,
       custom = list(fmean = c("welfare", "income"),
                     fsd = "welfare",
                     fnobs = "welfare"),
       w = ~ weight)

# Unweighted sum alongside weighted mean
collap(dt, ~ region,
       custom = list(fmean = "welfare", fsum_uw = "hhsize"),
       w = ~ weight)

# Select columns by position
collap(dt, ~ region, fmean, w = ~ weight, cols = 5:10)
```

## Transformations

```r
# Within transformation (group centering / demeaning)
fwithin(dt$welfare, g = dt$region)                    # Simple centering
fwithin(dt$welfare, g = dt$region, w = dt$weight)     # Weighted centering
fwithin(dt$welfare, g = dt$region, mean = "overall.mean")  # Preserve overall mean

# Between transformation (group averaging)
fbetween(dt$welfare, g = dt$region)                   # Group means, expanded
fbetween(dt$welfare, g = dt$region, w = dt$weight)    # Weighted group means

# Scaling and standardizing
fscale(dt$welfare)                                     # z-score (mean=0, sd=1)
fscale(dt$welfare, g = dt$region, w = dt$weight)       # Grouped, weighted z-score

# Higher-dimensional: partial out fixed effects + continuous covariates
fhdwithin(dt$welfare, list(dt$region, dt$year))        # Demean by region + year FE
fhdbetween(dt$welfare, list(dt$region, dt$year))       # Predict from region + year FE
```

## Panel Data Operations

```r
# Index the panel
pdt <- findex_by(dt, country, year)

# Lags and leads
flag(pdt$welfare, 1)         # Lag 1
flag(pdt$welfare, -1)        # Lead 1
flag(pdt$welfare, 1:3)       # Lags 1, 2, 3

# Differences
fdiff(pdt$welfare)           # First difference
fdiff(pdt$welfare, 2)        # Second difference
fdiff(pdt$welfare, log = TRUE)  # Log difference

# Growth rates
fgrowth(pdt$welfare)         # Growth rate (%)
fgrowth(pdt$welfare, logdiff = TRUE)  # Log-difference growth rate

# Operators (shorter names, same functionality)
L(pdt, 1:3, cols = "welfare")  # Lags
D(pdt, cols = "welfare")       # Difference
G(pdt, cols = "welfare")       # Growth
W(pdt, cols = "welfare")       # Within (demean by panel id)
B(pdt, cols = "welfare")       # Between (panel id means)
```

## Grouping and GRP Objects

GRP objects are collapse's efficient grouping metadata. They store precomputed information so multiple operations reuse the same grouping without recomputation.

### Creating GRP Objects

```r
# From formula (most common)
g <- GRP(dt, ~ region + year)

# From vectors
g <- GRP(dt$region)                      # Single vector
g <- GRP(list(dt$region, dt$year))       # Multiple vectors

# From a dplyr grouped_df
grp <- GRP(dplyr::group_by(dt, region)) # Extracts grouping from grouped_df

# Control sorting: sort = FALSE uses hashing (faster for many groups)
g <- GRP(dt, ~ region, sort = FALSE)
```

### GRP Object Structure

A GRP object is a list with 9 elements:

| Element | Name | Content |
|---------|------|---------|
| 1 | `N.groups` | Number of groups (integer) |
| 2 | `group.id` | Integer vector mapping each row to its group |
| 3 | `group.sizes` | Integer vector of group sizes |
| 4 | `groups` | Data frame of unique group combinations |
| 5 | `group.vars` | Character vector of grouping variable names |
| 6 | `ordered` | Logical vector: sorted? |
| 7 | `order` | Ordering vector (or `NULL` if unsorted) |
| 8 | `group.starts` | Integer vector of first row in each group |
| 9 | `call` | The call that created the GRP object |

### Using GRP Objects

```r
# Use with any Fast Statistical Function (grouping computed once, reused many times)
fmean(dt$welfare, g = g, w = dt$weight)
fsd(dt$welfare, g = g, w = dt$weight)
fnobs(dt$welfare, g = g)

# Pipe-style grouping via fgroup_by (attaches GRP to data frame as attribute)
dt |> fgroup_by(region, year) |> fmean(w = weight)
dt |> fgroup_by(region) |> fsummarise(
  mean_welf = fmean(welfare, w = weight),
  sd_welf   = fsd(welfare, w = weight),
  n         = fnobs(welfare)
)
```

## Summary Statistics

```r
# Fast summary (one-pass, with weights)
qsu(dt, w = ~ weight)                     # Overall
qsu(dt, ~ region, w = ~ weight)           # By region
qsu(dt, ~ region, w = ~ weight, higher = TRUE)  # + skewness, kurtosis

# Detailed description
descr(dt)

# Fast cross-tabulation (weighted)
qtab(dt$region, dt$year, w = dt$weight)

# Pairwise correlations
pwcor(num_vars(dt), w = dt$weight, N = TRUE, P = TRUE)
```

## Quick Data Conversion

```r
qDT(x)    # Convert anything to data.table (fast, no checks)
qDF(x)    # Convert to data.frame
qM(x)     # Convert to matrix
qTBL(x)   # Convert to tibble
```

## Data Manipulation Functions

collapse provides `f`-prefixed equivalents of base R data manipulation operations. These preserve object attributes and classes throughout.

```r
# Column selection (NSE — no quotes needed)
fselect(dt, region, welfare, weight)
fselect(dt, 1:5)           # By position
get_vars(dt, "welfare")    # Standard evaluation
num_vars(dt)               # All numeric columns
cat_vars(dt)               # All categorical/character columns

# Row subsetting (faster than dt[condition])
fsubset(dt, region == "EAP" & year > 2010)
fsubset(dt, welfare > 0, region, welfare, weight)  # Subset rows + select cols

# Column transformation (simultaneous evaluation — all RHS evaluated before assignment)
ftransform(dt, log_welfare = log(welfare), poor = welfare < 2.15)

# Sequential mutation (each expression can reference the previous)
fmutate(dt,
  welf_log = log(welfare),
  welf_log2 = welf_log^2   # Can reference welf_log immediately
)

# In-place transformation (reference semantics, no copy)
settransform(dt, log_welfare = log(welfare))
# Equivalent shorthand:
dt %=% list(log_welfare = log(welfare))

# Renaming
frename(dt, welf = welfare, wt = weight)
setrename(dt, welf = welfare)  # In-place
```

### Difference: ftransform vs fmutate

| | `ftransform()` | `fmutate()` |
|--|--|--|
| Evaluation | All RHS at once (like `transform()`) | Sequential (like `dplyr::mutate()`) |
| Reference new cols | Cannot reference new cols in same call | Can reference cols created in same call |
| Use when | Multiple independent columns | Chain of derived columns |

## Aggregation with collap() for Mixed Data

`collap()` handles numeric and categorical columns differently via `catFUN`:

```r
# Default: fmean for numeric, fmode for categorical
collap(dt, ~ region, fmean, catFUN = fmode, w = ~ weight)

# Explicit control
collap(dt, ~ region,
       FUN    = list(fmean, fsd),    # For numeric columns
       catFUN = fmode,               # For character/factor columns
       w      = ~ weight)

# Select only numeric columns (skip categorical)
collap(dt, ~ region, fmean, w = ~ weight, cols = is.numeric)
```

## Row/Column Sweeping Operators

For element-wise sweeping operations across rows or columns of a matrix/data frame:

```r
# Column-wise sweeping (subtract column means from each row)
X %c-% fmean(X)             # Equivalent to sweep(X, 2, fmean(X), "-")
X %c/% fsd(X)               # Divide each column by its sd
X %c*% weights              # Multiply each column by a vector

# Row-wise sweeping (subtract row totals from each column)
X %r-% rowSums(X)           # Subtract row sums from each column
X %r/% rowMeans(X)          # Divide each row by its mean

# In-place arithmetic
dt$welfare %-=% fmean(dt$welfare)   # Subtract scalar in-place
dt$welfare %/=% fsd(dt$welfare)     # Divide in-place
```

## Object Type System and Class-Agnostic Dispatch

To collapse's R and C code, there are 3 principal object types:

1. **Atomic vectors** — numeric, integer, character, logical vectors
2. **Matrices** — 2D atomic objects with `dim` attribute
3. **Lists** — generally assumed to be data frames (including data.table, tibble)

Most data manipulation functions (`fmutate()`, `fselect()`, `fsubset()`, etc.) only support lists/data frames. Statistical functions (all Fast Statistical Functions like `fmean()`) support all 3 types.

### S3 Method Dispatch

Fast Statistical Functions dispatch to 4 methods:

| Method | Used for |
|--------|----------|
| `.default` | Atomic vectors |
| `.matrix` | Matrices |
| `.data.frame` | Data frames, data.tables |
| `.list` (hidden) | Lists → dispatches to `.data.frame` |

The `.grouped_df` method additionally handles `dplyr::group_by()` output.

```r
# Same function, different inputs — collapse handles each optimally
fmean(dt$welfare)               # .default → scalar
fmean(as.matrix(dt[, 3:6]))    # .matrix → named vector of column means
fmean(dt)                       # .data.frame → named vector of column means
fmean(grouped_df)               # .grouped_df → data.frame of group means

# Grouping works the same way on all types
fmean(dt, g = dt$region)       # Returns data.frame/data.table of group means
```

### Attribute Preservation Rules

collapse preserves attributes and classes of R objects **unless** preservation would risk yielding something wrong or useless. The key rule:

- **Dimension-preserving operations** (e.g., `fscale(x)`, `fmutate(data, across(a:c, log))`) — all attributes fully preserved via shallow copy of the attribute list.
- **Dimension-changing operations** (e.g., aggregation reducing rows, or operations changing `typeof()`) — attributes may be dropped or adjusted to reflect the new structure.

Shallow copy means the attribute list pointer is copied, not the attributes themselves — this is memory-efficient. You can do this manually with:

```r
copyAttrib(target, source)       # Copy all attributes
copyMostAttrib(target, source)   # Copy all except names, dim, dimnames
setAttrib(x, attributes)         # Set attribute list directly (by reference)
setattrib(x, attributes)         # Same, alias
```

## Using collapse Inside data.table

collapse functions work directly inside `dt[, j, by]`:

```r
# collapse functions in j
dt[, .(mean_welf = fmean(welfare, w = weight),
       sd_welf   = fsd(welfare, w = weight),
       med_welf  = fmedian(welfare, w = weight),
       n         = fnobs(welfare)),
   by = region]

# collapse for column creation
dt[, welfare_centered := fwithin(welfare, region, weight)]
dt[, welfare_scaled := fscale(welfare, region, weight)]
dt[, welfare_pct := fsum(welfare, region, TRA = "%")]
```
