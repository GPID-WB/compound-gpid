# collapse Quick Reference

`collapse` is the team's primary tool for statistical computing. It provides fast C/C++-based grouped and weighted operations that work directly on data.table objects. Always use explicit `f`-prefixed names — never use `set_collapse(mask = ...)`.

## Fast Statistical Functions

All accept the same signature: `f*(x, g = NULL, w = NULL, TRA = NULL, na.rm = TRUE)`

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
| `fmode()` | Weighted mode | `fmode(dt$sector, g = dt$region, w = dt$weight)` |

### Key Arguments

- `g` — grouping: a vector, list of vectors, or `GRP` object
- `w` — weights: a numeric vector
- `TRA` — transform instead of aggregate: `"replace"`, `"-"` (center), `"/"` (scale), `"%"` (percentage), `"%%"` (modulus), `"+"`, `"*"`, `"replace_fill"`
- `na.rm` — default `TRUE` in collapse (unlike base R)

### TRA: Grouped Replace and Sweep

```r
# Replace each value with its group mean (like Stata's egen mean)
fmean(dt$welfare, g = dt$region, TRA = "replace")

# Center within groups (demean)
fmean(dt$welfare, g = dt$region, TRA = "-")

# Compute percentage of group total
fsum(dt$welfare, g = dt$region, TRA = "%")

# Scale by group standard deviation
fsd(dt$welfare, g = dt$region, TRA = "/")
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

## Grouping

```r
# Pre-compute grouping for repeated use (faster than passing raw vectors)
g <- GRP(dt, ~ region + year)

# Use with any fast function
fmean(dt$welfare, g = g, w = dt$weight)
fsd(dt$welfare, g = g, w = dt$weight)
fnobs(dt$welfare, g = g)

# Pipe-style grouping (returns grouped data frame, collapse functions auto-detect)
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
