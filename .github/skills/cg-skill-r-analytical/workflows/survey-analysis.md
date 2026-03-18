# Survey Analysis

Weighted survey analysis using `collapse` as the primary tool. `collapse` provides the fastest grouped and weighted statistics in R, working directly on data.table objects. For standard errors under complex survey designs (stratification + clustering), we compute them explicitly using collapse primitives.

## Why collapse for Survey Work

Household surveys used by GPID (LSMS, HIES, LFS) require weighted computations throughout. `collapse` functions natively support weights as a core argument — `fmean(x, g, w)` computes a grouped weighted mean in a single C call, directly on any R object including data.table. No design object declaration, no method dispatch overhead.

### Stata comparison

In Stata, you `svyset` once and `svy:` everything. With collapse, there is no design object — you pass `w = weight` to every function explicitly. This is more verbose but completely transparent: you always see exactly what weights and groups are being used.

## Point Estimates with collapse

### Weighted Means

```r
library(collapse)
library(data.table)

# Overall weighted mean
fmean(dt$welfare, w = dt$weight)

# By region
fmean(dt$welfare, g = dt$region, w = dt$weight)

# Multiple variables at once
collap(dt, ~ region, fmean, w = ~ weight, cols = c("welfare", "income", "hhsize"))
```

### Weighted Totals

```r
# Population total
fsum(dt$weight)

# Weighted total of welfare
fsum(dt$welfare, w = dt$weight)

# By region
fsum(dt$welfare, g = dt$region, w = dt$weight)
```

### Weighted Proportions (Headcounts)

```r
poverty_line <- 2.15

# National poverty headcount
fmean(dt$welfare < poverty_line, w = dt$weight)

# By region
fmean(dt$welfare < poverty_line, g = dt$region, w = dt$weight)
```

### Weighted Quantiles

```r
# Weighted median
fmedian(dt$welfare, w = dt$weight)

# Weighted 25th percentile by region
fnth(dt$welfare, 0.25, g = dt$region, w = dt$weight)

# Decile thresholds
vapply(seq(0.1, 0.9, 0.1), function(p) {
  fnth(dt$welfare, p, w = dt$weight)
}, numeric(1))
```

## Standard Errors Under Complex Survey Designs

For published statistics, point estimates need standard errors that account for stratification and clustering. Below is the explicit Taylor linearization approach using collapse.

### The Variance Formula

For a weighted mean θ̂ under stratified, clustered sampling:

```
V(θ̂) = Σ_h [ n_h / (n_h - 1) ] * Σ_k (e_hk - ē_h)²
```

Where `e_hk` is the sum of linearized scores in PSU k of stratum h, and `ē_h` is the stratum mean of PSU totals.

### Helper Function: Survey SE for a Weighted Mean

```r
#' Compute survey SE for a weighted mean under stratified clustered design
#'
#' @param x Numeric vector (variable of interest)
#' @param w Numeric vector (survey weights)
#' @param psu Integer/factor vector (primary sampling unit / cluster)
#' @param stratum Integer/factor vector (stratification variable)
#' @return Named numeric vector: estimate, se, ci_lower, ci_upper
survey_mean_se <- function(x, w, psu, stratum) {
  # Point estimate: weighted mean
  theta <- fmean(x, w = w)

  # Total weight
  N <- fsum(w)

  # Linearized scores
  z <- w * (x - theta)

  # Sum scores by PSU (within stratum, but PSU nests within stratum)
  # Create a PSU-stratum interaction for unique PSU identification
  psu_id <- finteraction(stratum, psu)
  z_psu <- fsum(z, g = psu_id)
  strat_of_psu <- ffirst(stratum, g = psu_id)

  # Number of PSUs per stratum
  n_h <- fnobs(z_psu, g = strat_of_psu)

  # Variance of PSU totals within each stratum
  # v_h = n_h/(n_h-1) * Σ_k (z_hk - z̄_h)² = n_h/(n_h-1) * (n_h-1) * var(z_hk)
  #      = n_h * var(z_hk)
  # But we need the sum of squared deviations, not the variance
  z_psu_mean <- fbetween(z_psu, g = strat_of_psu)  # group means, expanded
  ssq_by_stratum <- fsum((z_psu - z_psu_mean)^2, g = strat_of_psu)

  # Get unique stratum-level values
  strat_unique <- funique(strat_of_psu)
  n_h_unique <- fnobs(z_psu, g = strat_of_psu)
  n_h_unique <- fsum(rep(1L, length(z_psu)), g = strat_of_psu)

  # Degrees of freedom adjustment: n_h / (n_h - 1)
  # Use collap for clean stratum-level computation
  psu_dt <- data.table(z_psu = z_psu, stratum = strat_of_psu)
  strat_stats <- psu_dt[, .(
    n_psu = .N,
    ssq   = fsum((z_psu - fmean(z_psu))^2)
  ), by = stratum]

  # V(θ̂) = (1/N²) * Σ_h [n_h/(n_h-1)] * ssq_h
  strat_stats[, v_h := (n_psu / (n_psu - 1)) * ssq]
  V <- fsum(strat_stats$v_h) / N^2

  se <- sqrt(V)
  c(estimate = theta, se = se,
    ci_lower = theta - 1.96 * se,
    ci_upper = theta + 1.96 * se)
}
```

### Usage

```r
# National poverty headcount with SE
result <- survey_mean_se(
  x       = as.numeric(dt$welfare < 2.15),
  w       = dt$weight,
  psu     = dt$psu,
  stratum = dt$stratum
)
# estimate       se ci_lower ci_upper
#   0.2530   0.0124   0.2287   0.2773

# By region: apply to each subset
regions <- funique(dt$region)
region_results <- rbindlist(lapply(regions, function(r) {
  idx <- dt$region == r
  res <- survey_mean_se(
    x       = as.numeric(dt$welfare[idx] < 2.15),
    w       = dt$weight[idx],
    psu     = dt$psu[idx],
    stratum = dt$stratum[idx]
  )
  data.table(region = r, t(res))
}))
```

### When to Fall Back to srvyr

Use `srvyr` when:
- You need complex ratio estimators (`survey_ratio()`)
- You need replicate weight methods (BRR, jackknife) that are cumbersome to implement manually
- You need `svyglm()` for survey-weighted regressions with proper design-based inference
- The survey has a multi-stage design with finite population corrections at each stage

```r
# srvyr fallback for complex cases
library(srvyr)
svy <- dt |>
  as_survey_design(ids = psu, strata = stratum, weights = weight, nest = TRUE)

svy |>
  group_by(region) |>
  summarise(ratio = survey_ratio(food_exp, total_exp, vartype = "ci"))
```

## Aggregation Patterns

### Multi-Variable Aggregation

```r
# Weighted means of multiple variables by region
collap(dt, ~ region, fmean, w = ~ weight, cols = c("welfare", "income", "hhsize"))

# Multiple functions
collap(dt, ~ region, list(fmean, fsd, fnobs), w = ~ weight, cols = c("welfare", "income"))

# Summary statistics table
dt |> fgroup_by(region) |>
  fsummarise(
    mean_welf = fmean(welfare, w = weight),
    med_welf  = fmedian(welfare, w = weight),
    sd_welf   = fsd(welfare, w = weight),
    p10_welf  = fnth(welfare, 0.10, w = weight),
    p90_welf  = fnth(welfare, 0.90, w = weight),
    n         = fnobs(welfare)
  )
```

### Weighted Cross-Tabulations

```r
# Population counts by region and urban/rural
qtab(dt$region, dt$urban, w = dt$weight)

# Proportions
qtab(dt$region, dt$urban, w = dt$weight) |> proportions(margin = 1)
```

### Fast Summary Statistics

```r
# One-pass weighted summary
qsu(dt, cols = c("welfare", "income"), w = ~ weight)

# By group with higher moments
qsu(dt, ~ region, cols = c("welfare", "income"), w = ~ weight, higher = TRUE)
```

## Working with Multiple Survey Rounds

```r
# Stack rounds and compute trends
dt_all <- rbindlist(lapply(c(2015, 2018, 2021), function(yr) {
  d <- as.data.table(haven::read_dta(sprintf("data/survey_%d.dta", yr)))
  d[, year := yr]
  d
}))

# Poverty trends: weighted headcount by year
dt_all[, poor := welfare < 2.15]
collap(dt_all, ~ year, fmean, w = ~ weight, cols = "poor")

# With collapse panel indexing for growth rates
pdt <- findex_by(dt_all, country, year)
G(pdt, cols = "welfare")  # Growth rate of welfare by country-year panel
```

## Weighted vs Unweighted: When Each Is Appropriate

| Statistic | Weighted? | Tool |
|-----------|-----------|------|
| National poverty rate | Yes | `fmean(poor, w = weight)` |
| Regional poverty rate | Yes | `fmean(poor, g = region, w = weight)` |
| Mean welfare | Yes | `fmean(welfare, w = weight)` |
| Sample size | No | `fnobs(welfare)` or `dt[, .N]` |
| Data quality checks | No | `fmean(welfare)` (no w argument) |
| Correlation for EDA | Usually no | `pwcor(num_vars(dt))` |

**The default for GPID published statistics is always weighted.** Unweighted analysis is for diagnostics and data exploration only.
