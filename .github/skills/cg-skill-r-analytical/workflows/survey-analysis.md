# Survey Analysis

Complex survey analysis using `srvyr` and `survey`. The critical principle: declare the survey design ONCE and use it consistently through ALL downstream computations. Never redeclare, never bypass.

## Why This Matters

Household surveys used by GPID (LSMS, HIES, LFS) use complex sampling: stratification, clustering, and unequal probability weights. If you ignore the design, standard errors are wrong. If you apply weights inconsistently, estimates are biased. If you redeclare the design differently at different points, your results are internally inconsistent.

### Stata comparison

In Stata, you `svyset` once and `svy:` everything. In R with `srvyr`, the pattern is identical — `as_survey_design()` once, then pipe everything through the survey object. The danger is that R makes it easy to accidentally bypass the design and compute unweighted statistics.

## Declaring the Survey Design

```r
library(srvyr)
library(data.table)
library(haven)

# Read and clean the data
dt <- as.data.table(read_dta("data/hh_survey.dta"))
dt[, welfare := zap_labels(welfare)]
dt[, weight := zap_labels(weight)]

# Declare the survey design ONCE
svy <- dt |>
  as_survey_design(
    ids     = psu,         # primary sampling unit (cluster)
    strata  = stratum,     # stratification variable
    weights = weight,      # sampling weights
    nest    = TRUE         # PSUs are nested within strata
  )
```

### Stata comparison

```
* Stata equivalent
svyset psu [pw=weight], strata(stratum)
```

The `nest = TRUE` argument means PSU IDs only need to be unique within strata, not globally — matching Stata's default behavior.

## Computing Survey Statistics

### Means

```r
# Weighted mean of welfare, overall
svy |>
  summarise(
    mean_welfare = survey_mean(welfare, vartype = "ci")
  )

# Weighted mean by region
svy |>
  group_by(region) |>
  summarise(
    mean_welfare = survey_mean(welfare, vartype = c("se", "ci"))
  )
```

**Stata comparison:** `svy: mean welfare` and `svy: mean welfare, over(region)`.

### Totals

```r
# Weighted population total
svy |>
  summarise(
    total_pop = survey_total(1, vartype = "ci")
  )

# Total welfare by region
svy |>
  group_by(region) |>
  summarise(
    total_welfare = survey_total(welfare, vartype = "se")
  )
```

### Proportions

```r
# Poverty headcount (proportion below poverty line)
svy |>
  summarise(
    headcount = survey_mean(welfare < 2.15, vartype = "ci")
  )

# Poverty headcount by region
svy |>
  group_by(region) |>
  summarise(
    headcount = survey_mean(welfare < 2.15, vartype = "ci")
  )
```

### Ratios

```r
# Ratio of food expenditure to total expenditure
svy |>
  summarise(
    food_share = survey_ratio(food_exp, total_exp, vartype = "ci")
  )
```

### Quantiles

```r
# Weighted median welfare
svy |>
  summarise(
    median_welfare = survey_median(welfare, vartype = "ci")
  )

# Welfare decile thresholds
svy |>
  summarise(
    survey_quantile(welfare, quantiles = seq(0.1, 0.9, 0.1), vartype = "ci")
  )
```

## The Design Propagation Rule

Every computation that uses survey data must flow through the `svy` object. Never go back to the raw `dt` for calculations that should be weighted.

```r
# WRONG — bypasses survey design, gives unweighted mean
wrong_mean <- dt[, mean(welfare)]

# WRONG — applies weights manually, ignores clustering and stratification
also_wrong <- dt[, weighted.mean(welfare, weight)]

# RIGHT — uses the declared survey design
right_mean <- svy |>
  summarise(mean_welfare = survey_mean(welfare))
```

The second example (`weighted.mean()`) gives the correct point estimate but wrong standard errors because it ignores the cluster structure. This is dangerous because the number looks right but the uncertainty around it is wrong.

## Subsetting the Design (Not the Data)

When you need statistics for a subpopulation, subset the survey design, not the raw data. Subsetting the raw data and re-declaring a design changes the variance estimation.

```r
# WRONG — subsets data, then redeclares design
dt_urban <- dt[urban == 1]
svy_urban_wrong <- dt_urban |>
  as_survey_design(ids = psu, strata = stratum, weights = weight, nest = TRUE)

# RIGHT — filter the survey object
svy_urban <- svy |>
  filter(urban == 1)

# Now compute on the correctly subsetted design
svy_urban |>
  summarise(mean_welfare = survey_mean(welfare, vartype = "ci"))
```

**Stata comparison:** This is the difference between `svy, subpop(urban): mean welfare` (correct) and dropping non-urban observations before `svyset` (wrong).

## Adding Variables to the Design

If you need to create new variables after declaring the design, use `mutate()` on the survey object:

```r
# Add a poverty indicator to the survey design
svy <- svy |>
  mutate(
    poor_215 = welfare < 2.15,
    poor_685 = welfare < 6.85,
    log_welfare = log(welfare)
  )
```

Do NOT go back to the raw `dt`, add columns, and re-declare the design. That's a redeclaration and risks inconsistency.

## Standard Error Types

```r
# Default: linearization (Taylor series) — matches Stata's svy default
svy |>
  summarise(mean_welfare = survey_mean(welfare, vartype = "se"))

# Confidence intervals
svy |>
  summarise(mean_welfare = survey_mean(welfare, vartype = "ci"))

# Both standard errors and confidence intervals
svy |>
  summarise(mean_welfare = survey_mean(welfare, vartype = c("se", "ci")))

# Design effect (DEFF)
svy |>
  summarise(mean_welfare = survey_mean(welfare, vartype = "se", deff = TRUE))
```

## Working with Multiple Survey Rounds

When combining surveys across years, declare the design with a year indicator and use `group_by()`:

```r
# Read and stack multiple rounds
rounds <- c(2015, 2018, 2021)
dt_all <- rbindlist(lapply(rounds, function(yr) {
  d <- as.data.table(read_dta(sprintf("data/survey_%d.dta", yr)))
  d[, year := yr]
  d
}))

# Declare design on the combined data
svy_all <- dt_all |>
  as_survey_design(
    ids     = psu,
    strata  = interaction(stratum, year),  # strata are year-specific
    weights = weight,
    nest    = TRUE
  )

# Poverty trends over time
svy_all |>
  group_by(year) |>
  summarise(
    headcount = survey_mean(welfare < 2.15, vartype = "ci")
  )
```

## Converting Results to data.table

`srvyr` functions return tibbles. Convert to data.table for downstream work:

```r
poverty_by_region <- svy |>
  group_by(region) |>
  summarise(
    headcount = survey_mean(welfare < 2.15, vartype = c("se", "ci"))
  ) |>
  as.data.table()
```
