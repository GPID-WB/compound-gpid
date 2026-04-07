# collapse Quick Reference

`collapse` is a high-performance C/C++-based R package for statistical computing and data transformation. Functions are **class-agnostic** — they work identically on `data.table`, `tibble`, and `data.frame` without conversion. Always use explicit `f`-prefixed names — never use `set_collapse(mask = ...)`.

**Core mental model:** Everything revolves around the **GRP object** and the `g` + `TRA` pattern. All Fast Statistical Functions accept `g` for grouped computation and `TRA` for in-place grouped transformation — enabling aggregation and transformation in a single C-level pass.

## Global Options

```r
# Set global options on load
set_collapse(
  nthreads = 4L,   # OpenMP threads (default: 1)
  na.rm    = TRUE, # Skip NA by default (default: TRUE)
  sort     = TRUE, # Sort groups (default: TRUE)
  mask     = NULL  # NEVER use mask — always use explicit f* names
)

# View all current options
get_collapse()
```

**Warning for welfare work**: All FGT, Gini, and weighted mean patterns assume `na.rm = TRUE` (default). If you change `set_collapse(na.rm = FALSE)`, welfare calculations return `NA` silently. Do not change global `na.rm` in scripts with welfare calculations.

## Fast Statistical Functions

All share the canonical signature:

```r
FUN(x, g = NULL, w = NULL, TRA = NULL, na.rm = .op[["na.rm"]], use.g.names = TRUE, ...)
```

Where `FUN` is: `fsum`, `fprod`, `fmean`, `fmedian`, `fmode`, `fvar`, `fsd`, `fmin`, `fmax`, `fnth`, `ffirst`, `flast`, `fnobs`, `fndistinct`.

- `g` — grouping: vector, list of vectors, or `GRP` object
- `w` — weights: numeric vector
- `TRA` — transform instead of aggregate (10 types, see below)
- `use.g.names = TRUE` — adds group labels as names when aggregating. Set `FALSE` for programmatic use.

S3 methods exist for: `default` (vectors), `matrix`, `data.frame` (+ `data.table`, `tibble`), `grouped_df`, `zoo`, `pdata.frame`, `pseries`.

| Function | Purpose | Example |
|----------|---------|---------|
| `fmean()` | Weighted mean | `fmean(dt$welfare, g = dt$region, w = dt$weight)` |
| `fmedian()` | Weighted median | `fmedian(dt$welfare, w = dt$weight)` |
| `fsum()` | Weighted sum | `fsum(dt$welfare, g = dt$region, w = dt$weight)` |
| `fvar()` | Weighted variance | `fvar(dt$welfare, g = dt$region, w = dt$weight)` |
| `fsd()` | Weighted SD | `fsd(dt$welfare, g = dt$region, w = dt$weight)` |
| `fnth()` | Weighted nth quantile | `fnth(dt$welfare, 0.25, g = dt$region, w = dt$weight)` |
| `fquantile()` | Multiple weighted quantiles | `fquantile(dt$welfare, probs = seq(0.1, 0.9, 0.1), w = dt$weight)` |
| `fmin()`/`fmax()` | Grouped min/max | `fmin(dt$welfare, g = dt$region)` |
| `ffirst()`/`flast()` | Grouped first/last | `ffirst(dt$welfare, g = dt$region)` |
| `fnobs()` | Observation count | `fnobs(dt$welfare, g = dt$region)` |
| `fndistinct()` | Distinct value count | `fndistinct(dt$region)` |
| `fprod()` | Grouped product | `fprod(dt$growth_factor, g = dt$region)` |
| `fmode()` | Weighted mode | `fmode(dt$sector, g = dt$region, w = dt$weight)` |

## TRA: Grouped Transformation

The `TRA` argument performs in-place transformation instead of aggregation. Available on all Fast Statistical Functions. 10 types:

| Code | Operation |
|------|-----------|
| `"replace_fill"` | Replace all values (incl. NA) with group statistic |
| `"replace"` | Replace non-NA values with group statistic |
| `"-"` | Center: `x - stat` |
| `"-+"` | Subtract group stat, add overall stat (preserves level) |
| `"/"` | Scale: `x / stat` |
| `"%"` | Percentage: `x / stat * 100` |
| `"+"` | Add: `x + stat` |
| `"*"` | Multiply: `x * stat` |
| `"%%"` | Modulus: `x %% stat` |
| `"-%%"` | Subtract modulus |

```r
# Center within groups (demean)
fmean(dt$welfare, g = dt$region, TRA = "-")

# Replace each value with its group mean (broadcast)
fmean(dt$welfare, g = dt$region, TRA = "replace_fill")

# Compute percentage of group total
fsum(dt$welfare, g = dt$region, TRA = "%")

# Scale by group standard deviation
fsd(dt$welfare, g = dt$region, TRA = "/")

# Subtract group mean, add back overall mean
fmean(dt$welfare, g = dt$region, TRA = "-+")

# Standalone TRA: sweep precomputed statistics back
group_means <- fmean(dt$welfare, g = dt$region)
TRA(dt$welfare, group_means, FUN = "-", g = dt$region)
```

## Aggregation with collap()

```r
# Simple aggregation
collap(dt, ~ region, fmean, w = ~ weight)

# Multiple grouping variables
collap(dt, ~ region + year, fmean, w = ~ weight)

# Multiple functions
collap(dt, ~ region, list(fmean, fsd, fnobs))

# Custom: different functions per column
collap(dt, ~ region,
       custom = list(fmean = c("welfare", "income"),
                     fsd   = "welfare",
                     fnobs = "welfare"),
       w = ~ weight)

# Auto-split numeric/categorical columns
collap(dt, ~ region, fmean, catFUN = fmode, w = ~ weight)

# Select columns by position
collap(dt, ~ region, fmean, w = ~ weight, cols = 5:10)
```

## Transformations

```r
# Within transformation (group centering / demeaning)
fwithin(dt$welfare, g = dt$region)
fwithin(dt$welfare, g = dt$region, w = dt$weight)   # weighted
fwithin(dt$welfare, g = dt$region, mean = "overall.mean")  # preserve overall mean

# Between transformation (group averaging, expanded to original rows)
fbetween(dt$welfare, g = dt$region)
fbetween(dt$welfare, g = dt$region, w = dt$weight)

# Scaling and standardizing
fscale(dt$welfare)                                 # z-score
fscale(dt$welfare, g = dt$region, w = dt$weight)  # grouped weighted z-score

# High-dimensional within/between (partial out multiple fixed effects)
fhdwithin(dt$welfare, list(dt$region, dt$year))   # Demean by region + year FE
fhdbetween(dt$welfare, list(dt$region, dt$year))  # Predict from region + year FE
```

## Panel Data Operations

```r
# Index the panel (enables automatic lag/diff handling)
pdt <- findex_by(dt, country, year)

# Lags and leads
flag(pdt$welfare, 1)          # Lag 1
flag(pdt$welfare, -1)         # Lead 1
flag(pdt$welfare, 1:3)        # Lags 1, 2, 3
L(pdt, 1:3, cols = "welfare") # Operator shorthand

# Differences
fdiff(pdt$welfare)                # First difference
fdiff(pdt$welfare, 2)             # Second difference
fdiff(pdt$welfare, log = TRUE)    # Log difference
D(pdt, cols = "welfare")          # Operator shorthand

# Growth rates
fgrowth(pdt$welfare)              # Growth rate (%)
fgrowth(pdt$welfare, logdiff = TRUE)  # Log-difference growth rate
G(pdt, cols = "welfare")          # Operator shorthand

# Within/between operators
W(pdt, cols = "welfare")  # Within (demean by panel id)
B(pdt, cols = "welfare")  # Between (panel id means)

# Formula interface for operator functions
W(dt, ~ welfare + income | country)         # Within-transform by country
L(dt, 1, by = ~ country, t = ~ year, cols = c("welfare", "income"))
```

## Grouping and GRP Objects

GRP objects store precomputed grouping metadata so multiple operations reuse it without recomputation.

```r
# Create a GRP object
g <- GRP(dt, ~ region + year)
g <- GRP(dt$region)                   # Single vector
g <- GRP(list(dt$region, dt$year))    # Multiple vectors

# sort = FALSE uses hashing (faster for many groups)
g <- GRP(dt, ~ region, sort = FALSE)

# Use with any Fast Statistical Function
fmean(dt$welfare, g = g, w = dt$weight)
fsd(dt$welfare, g = g, w = dt$weight)
fnobs(dt$welfare, g = g)
```

GRP object structure (list with 9 elements):

| Element | Content |
|---------|---------|
| `N.groups` | Number of groups |
| `group.id` | Integer vector mapping each row to its group |
| `group.sizes` | Integer vector of group sizes |
| `groups` | Data frame of unique group combinations |
| `group.vars` | Character vector of grouping variable names |
| `ordered` | Logical: sorted? |
| `order` | Ordering vector (or NULL) |
| `group.starts` | Integer vector of first row in each group |
| `call` | The call that created the GRP object |

## Pipe-Friendly: fgroup_by + fmutate + fsummarise

```r
# Grouped summarization
dt |>
  fgroup_by(region, year) |>
  fsummarise(
    mean_welf = fmean(welfare, w = weight),
    sd_welf   = fsd(welfare, w = weight),
    n         = fnobs(welfare)
  ) |>
  fungroup()

# Grouped transformation
dt |>
  fgroup_by(country) |>
  fmutate(
    gdp_lag1     = flag(welfare, 1),
    welf_growth  = fgrowth(welfare, 1),
    welf_centered = fwithin(welfare),
    welf_scaled  = fscale(welfare)
  ) |>
  fungroup()

# across() works inside fmutate/fsummarise
dt |>
  fgroup_by(region) |>
  fsummarise(across(c(welfare, income), fmean))
```

**Note**: After piping through `fgroup_by()`, call `qDT()` before `:=` to avoid the "over-allocation" warning:

```r
result <- dt |> fgroup_by(region) |> fmean(w = weight) |> qDT()
result[, new_col := 1]  # Works cleanly
```

## Data Manipulation Verbs

```r
# Column selection (NSE)
fselect(dt, region, welfare, weight)
fselect(dt, 1:5)
num_vars(dt)   # All numeric columns
cat_vars(dt)   # All categorical/character columns

# Row subsetting
fsubset(dt, region == "EAP" & year > 2010)
fsubset(dt, welfare > 0, region, welfare, weight)  # Subset rows + select cols

# Column transformation (simultaneous evaluation)
ftransform(dt, log_welfare = log(welfare), poor = welfare < 2.15)

# Sequential mutation (can reference new columns)
fmutate(dt,
  welf_log  = log(welfare),
  welf_log2 = welf_log^2
)

# In-place transformation
settransform(dt, log_welfare = log(welfare))
dt %=% list(log_welfare = log(welfare))  # Equivalent shorthand

# Renaming
frename(dt, welf = welfare, wt = weight)
setrename(dt, welf = welfare)  # In-place
```

### ftransform vs fmutate

| | `ftransform()` | `fmutate()` |
|--|--|--|
| Evaluation | All RHS simultaneously | Sequential |
| Reference new cols | Cannot | Can (each expr can use the previous) |

## Summary Statistics

```r
# Fast summary (one-pass, with weights)
qsu(dt, w = ~ weight)                              # Overall
qsu(dt, ~ region, w = ~ weight)                    # By region
qsu(dt, ~ region, w = ~ weight, higher = TRUE)     # + skewness, kurtosis

# Panel decomposition (between/within)
qsu(pdt, pid = ~ country, cols = c("welfare", "income"), higher = TRUE)

# Detailed description
descr(dt)

# Fast cross-tabulation (weighted)
qtab(dt$region, dt$year, w = dt$weight)

# Pairwise correlations
pwcor(num_vars(dt), w = dt$weight, N = TRUE, P = TRUE)
```

## Quick Conversion

```r
qDT(x)   # Anything to data.table (fast, minimal checks)
qDF(x)   # To data.frame
qTBL(x)  # To tibble
qM(x)    # To matrix
```

## Row/Column Sweeping

```r
X %c-% fmean(X)     # Subtract column means from each row
X %c/% fsd(X)       # Divide each column by its SD
X %r-% rowSums(X)   # Subtract row sums from each column
X %r/% rowMeans(X)  # Divide each row by its mean
```

## Joins, Pivoting, Binding

```r
# Fast join (all types supported)
join(x, y, on = "id", how = "left")             # Left join
join(x, y, on = "id", how = "inner")            # Inner join
join(x, y, on = c("id" = "key"), how = "anti")  # Anti join with renamed key
join(x, y, on = "id", validate = "1:1", column = ".join")  # Add join indicator

# Reshape
pivot(dt, ids = "id", values = c("y2020", "y2021"), how = "longer",
      names = list(variable = "year", value = "value"))
pivot(dt, ids = "id", values = "income", names = "year", how = "wider")

# Row binding
rowbind(dt1, dt2)        # Fast rbind
rowbind(dt1, dt2, fill = TRUE)  # Fill missing columns with NA
```

## Using collapse Inside data.table

collapse functions work directly inside `dt[, j, by]`:

```r
dt[, .(mean_welf = fmean(welfare, w = weight),
       sd_welf   = fsd(welfare, w = weight),
       n         = fnobs(welfare)),
   by = region]

# Column creation
dt[, welfare_centered := fwithin(welfare, region, weight)]
dt[, welfare_scaled   := fscale(welfare, region, weight)]
dt[, welfare_pct      := fsum(welfare, region, TRA = "%")]
dt[, region_mean      := fmean(welfare, region, weight, TRA = "replace")]
```

## Object Type System

collapse operates on 3 principal types: atomic vectors, matrices, and lists (assumed to be data frames). Fast Statistical Functions dispatch via S3:

| Method | Used for |
|--------|----------|
| `.default` | Atomic vectors |
| `.matrix` | Matrices |
| `.data.frame` | Data frames, data.tables, tibbles |
| `.grouped_df` | `dplyr::group_by()` output |

## Short Aliases

| Full name | Alias |
|-----------|-------|
| `fselect` | `slt` |
| `fsubset` | `sbt` |
| `fgroup_by` | `gby` |
| `findex_by` | `iby` |
| `fmutate` | `mtt` |
| `fsummarise` | `smr` |
| `ftransform` | `tfm` |
| `frename` | `rnm` |
| `get_vars` | `gv` |
| `num_vars` | `nv` |
| `finteraction` | `itn` |

## Common Errors

```r
# Error: result of fgroup_by pipe cannot use :=
result <- dt |> fgroup_by(region) |> fmean(w = weight)
result[, new_col := 1]  # Warning about over-allocation
# Fix: add qDT()
result <- dt |> fgroup_by(region) |> fmean(w = weight) |> qDT()

# Error: na.rm global option changed, welfare returns NA
set_collapse(na.rm = FALSE)
fmean(dt$welfare, g = dt$region, w = dt$weight)  # Returns NA silently
# Fix: restore default
set_collapse(na.rm = TRUE)
# OR override per call:
fmean(dt$welfare, g = dt$region, w = dt$weight, na.rm = TRUE)
```
