# Welfare and Poverty Patterns

This is the highest-risk area for AI-assisted code in GPID. Copilot frequently generates poverty and inequality code that looks correct but silently produces wrong numbers — wrong weights, wrong units, wrong formula. Every pattern here uses `collapse` for speed and explicitness, with `data.table` for manipulation.

## PPP Adjustment Pipeline

Poverty measurement requires tracking monetary units through every transformation:

```
LCU nominal → LCU real → PPP USD
```

### The Unit Tracking Rule

Every welfare variable name must encode its unit. This is a safety mechanism, not style.

```r
# WRONG — what unit is "welfare" in?
dt[, welfare := consumption / hhsize]

# RIGHT — unit is explicit
# Validate deflators before applying them (zero or NA corrupts all welfare values)
stopifnot(
  !anyNA(dt$cpi_deflator), all(dt$cpi_deflator > 0),
  !anyNA(dt$ppp_factor),   all(dt$ppp_factor   > 0)
)
dt[, welf_pc_lcu_nom := consumption_lcu_nom / hhsize]
dt[, welf_pc_lcu_real := welf_pc_lcu_nom / cpi_deflator]
dt[, welf_pc_ppp := welf_pc_lcu_real / ppp_factor]
dt[, welf_pc_ppp_day := welf_pc_ppp / 365]
```

### Common PPP Mistakes

```r
# WRONG — PPP before deflating
dt[, welfare_ppp := welfare_lcu_nom / ppp_factor]

# RIGHT — deflate to base year, then PPP
dt[, welfare_lcu_real := welfare_lcu_nom / cpi_deflator]
dt[, welfare_ppp := welfare_lcu_real / ppp_factor]

# WRONG — mixing PPP vintages
dt[, poor := welfare_2011ppp < 2.15]  # $2.15 is a 2017 PPP line

# RIGHT — same vintage
dt[, poor := welfare_2017ppp < 2.15]
```

## FGT Poverty Indices with collapse

The Foster-Greer-Thorbecke (FGT) family. All computed with survey weights using `collapse`.

> **NA handling**: collapse defaults to `na.rm = TRUE` — NA welfare values are silently excluded from all aggregations. Before any FGT block, validate that your welfare and weight columns are complete:
> ```r
> stopifnot(
>   !anyNA(dt$welf_pc_ppp_day), !anyNA(dt$weight),
>   all(dt$weight > 0),
>   all(dt$welf_pc_ppp_day > 0)  # negative/zero welfare inflates FGT(1) beyond 1
> )
> ```
> If NAs are expected (e.g., item non-response), document the exclusion explicitly before computing.

### FGT(0) — Headcount Ratio

```r
poverty_line <- 2.15

# National headcount
fgt0 <- fmean(dt$welf_pc_ppp_day < poverty_line, w = dt$weight)

# By region
fgt0_region <- fmean(dt$welf_pc_ppp_day < poverty_line,
                     g = dt$region, w = dt$weight)
```

### FGT(1) — Poverty Gap

Average normalized gap over the ENTIRE population. Non-poor contribute 0.

```r
# Compute gap (0 for non-poor)
dt[, gap := fifelse(welf_pc_ppp_day < poverty_line,
                    (poverty_line - welf_pc_ppp_day) / poverty_line,
                    0)]

# National FGT(1)
fgt1 <- fmean(dt$gap, w = dt$weight)

# By region
fgt1_region <- fmean(dt$gap, g = dt$region, w = dt$weight)
```

**Critical:** The gap is averaged over ALL households (not just the poor). Copilot frequently filters to poor only, which gives the Income Gap Ratio — a different statistic.

```r
# WRONG — averages only among the poor (Income Gap Ratio, not FGT(1))
wrong <- fmean(dt[welf_pc_ppp_day < poverty_line]$gap, w = dt[welf_pc_ppp_day < poverty_line]$weight)

# RIGHT — averages over entire population
right <- fmean(dt$gap, w = dt$weight)
```

### FGT(2) — Poverty Severity

```r
dt[, gap_sq := fifelse(welf_pc_ppp_day < poverty_line,
                       ((poverty_line - welf_pc_ppp_day) / poverty_line)^2,
                       0)]

fgt2 <- fmean(dt$gap_sq, w = dt$weight)
fgt2_region <- fmean(dt$gap_sq, g = dt$region, w = dt$weight)
```

### Complete FGT with SEs

```r
poverty_line <- 2.15

# Variables
dt[, `:=`(
  poor   = welf_pc_ppp_day < poverty_line,
  gap    = fifelse(welf_pc_ppp_day < poverty_line,
                   (poverty_line - welf_pc_ppp_day) / poverty_line, 0),
  gap_sq = fifelse(welf_pc_ppp_day < poverty_line,
                   ((poverty_line - welf_pc_ppp_day) / poverty_line)^2, 0)
)]

# Point estimates (national)
fgt <- c(
  fgt0 = fmean(dt$poor, w = dt$weight),
  fgt1 = fmean(dt$gap, w = dt$weight),
  fgt2 = fmean(dt$gap_sq, w = dt$weight)
)

# Point estimates by region (pre-compute GRP to avoid 4 redundant grouping passes)
g_region <- GRP(dt, ~ region)
fgt_region <- data.table(
  region = g_region$groups$region,
  fgt0   = fmean(dt$poor,   g = g_region, w = dt$weight),
  fgt1   = fmean(dt$gap,    g = g_region, w = dt$weight),
  fgt2   = fmean(dt$gap_sq, g = g_region, w = dt$weight),
  n      = fnobs(dt$poor,   g = g_region)
)

# SEs using the helper from survey-analysis.md
fgt0_with_se <- survey_mean_se(
  x = as.numeric(dt$poor), w = dt$weight,
  psu = dt$psu, stratum = dt$stratum
)
fgt1_with_se <- survey_mean_se(
  x = dt$gap, w = dt$weight,
  psu = dt$psu, stratum = dt$stratum
)
```

### Verification Tests

FGT and Gini are highest-risk for silent errors. Always have tests for these functions:

```r
library(testthat)
library(collapse)
library(data.table)

test_that("FGT denominator covers entire population (not just poor)", {
  dt <- data.table(
    welfare = c(1, 1.5, 2, 3, 5),
    weight  = c(1, 1, 1, 1, 1)
  )
  poverty_line <- 2.15
  dt[, gap := fifelse(welfare < poverty_line,
                      (poverty_line - welfare) / poverty_line, 0)]
  fgt1 <- fmean(dt$gap, w = dt$weight)
  # 3 of 5 are poor; gaps: 1.15/2.15, 0.65/2.15, 0.15/2.15, 0, 0 → mean ≈ 0.182
  expect_equal(fgt1, fmean(c(1.15, 0.65, 0.15, 0, 0) / 2.15), tolerance = 1e-10)
})

test_that("weighted_gini() returns 0 for perfect equality", {
  expect_equal(weighted_gini(c(10, 10, 10), c(1, 1, 1)), 0, tolerance = 1e-10)
})

test_that("weighted_gini() returns value in [0, 1]", {
  g <- weighted_gini(c(1, 5, 10, 50), c(1, 1, 1, 1))
  expect_true(g >= 0 && g <= 1)
})

test_that("weighted_gini() warns and drops NA welfare", {
  expect_warning(
    weighted_gini(c(10, NA, 30), c(1, 1, 1)),
    "1 observation.*dropped"
  )
})

test_that("FGT handles single observation", {
  dt <- data.table(welfare = 1.5, weight = 1)
  dt[, gap := fifelse(welfare < 2.15, (2.15 - welfare) / 2.15, 0)]
  expect_equal(fmean(dt$gap, w = dt$weight), (2.15 - 1.5) / 2.15, tolerance = 1e-10)
})

test_that("FGT is 1 when all are poor", {
  dt <- data.table(welfare = c(0.5, 1, 1.5), weight = c(1, 1, 1))
  expect_equal(fmean(dt$welfare < 2.15, w = dt$weight), 1.0)
})

test_that("FGT is 0 when none are poor", {
  dt <- data.table(welfare = c(3, 4, 5), weight = c(1, 1, 1))
  expect_equal(fmean(dt$welfare < 2.15, w = dt$weight), 0.0)
})
```

> Run the pre-checks from the FGT section above before this block (`stopifnot(!anyNA(dt$welf_pc_ppp_day), all(dt$welf_pc_ppp_day > 0), !anyNA(dt$weight), all(dt$weight > 0))`).

## Multiple Poverty Lines

GPID reports at three international poverty lines. Compute all in one pass:

```r
dt[, `:=`(
  poor_215 = welf_pc_ppp_day < 2.15,
  poor_365 = welf_pc_ppp_day < 3.65,
  poor_685 = welf_pc_ppp_day < 6.85,
  gap_215  = fifelse(welf_pc_ppp_day < 2.15, (2.15 - welf_pc_ppp_day) / 2.15, 0),
  gap_365  = fifelse(welf_pc_ppp_day < 3.65, (3.65 - welf_pc_ppp_day) / 3.65, 0),
  gap_685  = fifelse(welf_pc_ppp_day < 6.85, (6.85 - welf_pc_ppp_day) / 6.85, 0)
)]

# All headcounts at once using collap
poverty_cols <- c("poor_215", "poor_365", "poor_685",
                  "gap_215", "gap_365", "gap_685")
collap(dt, ~ region, fmean, w = ~ weight, cols = poverty_cols)
```

## Gini Coefficient with collapse

Weighted Gini using collapse primitives for speed:

```r
#' Weighted Gini coefficient using collapse
#'
#' @param y Numeric vector (welfare)
#' @param w Numeric vector (weights)
#' @return Scalar Gini coefficient (0 = perfect equality, 1 = perfect inequality)
weighted_gini <- function(y, w) {
  # Remove NA and non-positive weights before computation
  keep <- !is.na(y) & !is.na(w) & w > 0
  if (any(!keep))
    warning(sum(!keep), " observation(s) dropped (NA welfare or non-positive weight)")
  y <- y[keep]
  w <- w[keep]
  # Sort by welfare
  ord <- radixorder(y)
  ys  <- y[ord]
  ws  <- w[ord]

  # Cumulative shares (using collapse::fcumsum for speed on large vectors)
  cum_w  <- fcumsum(ws) / fsum(ws)
  cum_wy <- fcumsum(ws * ys) / fsum(ws * ys)

  # Trapezoidal Lorenz area
  n <- length(ys)
  lorenz_area <- fsum((cum_w[2:n] - cum_w[1:(n-1)]) *
                      (cum_wy[2:n] + cum_wy[1:(n-1)])) / 2
  gini <- 1 - 2 * lorenz_area
  gini
}

# National Gini
gini_national <- weighted_gini(dt$welf_pc_ppp_day, dt$weight)

# Gini by region
gini_by_region <- dt[, .(gini = weighted_gini(welf_pc_ppp_day, weight)),
                     by = region]
```

## Welfare Shares by Decile

> Run the pre-checks from the FGT section above before this block (`stopifnot(!anyNA(dt$welf_pc_ppp_day), all(dt$welf_pc_ppp_day > 0), !anyNA(dt$weight), all(dt$weight > 0))`).

```r
# Assign weighted deciles using collapse
dt_sorted <- dt[radixorder(welf_pc_ppp_day)]
dt_sorted[, cum_wt := fcumsum(weight) / fsum(weight)]
dt_sorted[, decile := fcase(
  cum_wt <= 0.1, 1L,
  cum_wt <= 0.2, 2L,
  cum_wt <= 0.3, 3L,
  cum_wt <= 0.4, 4L,
  cum_wt <= 0.5, 5L,
  cum_wt <= 0.6, 6L,
  cum_wt <= 0.7, 7L,
  cum_wt <= 0.8, 8L,
  cum_wt <= 0.9, 9L,
  default = 10L
)]

# Welfare share by decile
decile_shares <- dt_sorted[, .(
  total_welfare = fsum(welf_pc_ppp_day * weight),
  pop_share     = fsum(weight)
), by = decile]
decile_shares[, welfare_share := total_welfare / fsum(total_welfare)]
setorder(decile_shares, decile)
```

## Fast Descriptive Statistics

```r
# Quick weighted summary of welfare
qsu(dt, cols = "welf_pc_ppp_day", w = ~ weight)

# By region with higher moments
qsu(dt, ~ region, cols = "welf_pc_ppp_day", w = ~ weight, higher = TRUE)

# Weighted pairwise correlations
pwcor(dt[, .(welf_pc_ppp_day, income, hhsize)], w = dt$weight, P = TRUE)

# Detailed statistical description
descr(dt[, .(welf_pc_ppp_day, income, hhsize)], w = dt$weight)
```

## Poverty Trends with Panel Operations

```r
# Index the panel (country-year)
pdt <- findex_by(dt_all, country, year)

# Year-over-year change in poverty headcount
D(pdt, cols = "headcount")   # First difference

# Growth rate of mean welfare
G(pdt, cols = "mean_welfare")

# Within-country demeaning (for fixed effects analysis)
W(pdt, cols = "headcount")

# Lags for dynamic analysis
L(pdt, 1:2, cols = "headcount")
```

## Verification Checklist

Before publishing any poverty or inequality number:

1. **Unit check:** What unit is the welfare variable in? Is it daily PPP? Annual LCU?
2. **Weight check:** Is the statistic weighted? Are you using `w = weight` in every collapse function call?
3. **Population check:** Are FGT indices averaged over the ENTIRE population (including non-poor)?
4. **PPP vintage check:** Is the poverty line in the same PPP vintage as the welfare variable?
5. **Reasonableness check:** Is poverty at $2.15 lower than at $6.85? Is Gini between 0 and 1?
6. **Cross-check:** Can you reproduce the number in Stata? If not, investigate before publishing.
