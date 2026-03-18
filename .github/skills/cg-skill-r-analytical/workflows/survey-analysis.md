# Survey Analysis with srvyr / survey

## The Golden Rule

**Declare the survey design ONCE. Use it everywhere.**

Never compute weighted means by hand. Always pass the survey design object to `srvyr` or `survey` functions.

## Declaring a Survey Design

```r
library(srvyr)
library(data.table)

dt <- as.data.table(read_dta("survey.dta"))

# Simple random sampling
svy <- dt |> as_survey_design(weights = wgt)

# Stratified sampling
svy <- dt |> as_survey_design(
  strata = stratum,
  weights = wgt
)

# Clustered sampling (PSU + strata)
svy <- dt |> as_survey_design(
  ids = psu,          # primary sampling unit
  strata = stratum,
  weights = wgt,
  nest = TRUE         # PSU IDs are nested within strata
)

# Two-stage with population size
svy <- dt |> as_survey_design(
  ids = ~ psu + hh,   # two levels: PSU then household
  strata = stratum,
  weights = wgt,
  fpc = ~ n_psu + n_hh  # finite population corrections
)
```

## Computing Estimates

```r
# Weighted mean
svy |>
  summarise(mean_income = survey_mean(income, na.rm = TRUE))

# Weighted mean by group
svy |>
  group_by(region) |>
  summarise(mean_income = survey_mean(income, vartype = "ci"))

# Weighted proportion
svy |>
  group_by(poor) |>
  summarise(prop = survey_mean(vartype = "se"))

# Weighted total
svy |>
  summarise(total_pop = survey_total(vartype = "ci"))

# Multiple statistics
svy |>
  group_by(country, year) |>
  summarise(
    mean_cons = survey_mean(consumption, na.rm = TRUE),
    poverty_rate = survey_mean(poor, vartype = c("se", "ci")),
    n = survey_total(one = 1)   # weighted N
  )
```

## Subpopulations (Not Subsets)

```r
# WRONG — drops observations, distorts variance
svy_rural <- dt[rural == 1] |> as_survey_design(weights = wgt)

# CORRECT — use subset() to preserve design information
svy_rural <- svy |> filter(rural == 1)
```

## survey Package (Lower-Level)

```r
library(survey)

svy_obj <- svydesign(
  ids = ~psu,
  strata = ~stratum,
  weights = ~wgt,
  data = dt,
  nest = TRUE
)

# Mean with SE
svymean(~income, svy_obj, na.rm = TRUE)

# Ratio estimate
svyratio(~income, ~hh_size, svy_obj)

# Quantile
svyquantile(~income, svy_obj, quantiles = c(0.25, 0.5, 0.75))
```

## Calibration and Post-Stratification

```r
# Post-stratify to known population totals
pop_totals <- data.frame(stratum = c("A", "B"), Freq = c(1000000, 2000000))
svy_cal <- postStratify(svy_obj, ~stratum, pop_totals)
```

## Design Effects

```r
# Check design effect (ratio of actual variance to SRS variance)
svymean(~income, svy_obj, deff = TRUE)
```
