# Econometrics

Regression analysis using `fixest` for estimation and `modelsummary` for publication-ready tables. Data preparation and transformations use `collapse`. `fixest` is the R package closest to Stata's `reghdfe`.

## Data Preparation with collapse

Before running regressions, prepare variables using collapse for speed:

```r
library(collapse)
library(fixest)
library(modelsummary)
library(data.table)

# Demean within groups (collapse is faster than fixest's internal demeaning for data prep)
dt[, welfare_within := fwithin(welfare, region, weight)]

# Standardize
dt[, welfare_z := fscale(welfare, region, weight)]

# Lags for dynamic models (panel data)
pdt <- findex_by(dt, country, year)
pdt$welfare_lag1 <- flag(pdt$welfare, 1)
pdt$welfare_growth <- fgrowth(pdt$welfare)

# Group means for Hausman-type tests
dt[, welfare_between := fbetween(welfare, region, weight)]
```

## fixest Basics

### OLS with Fixed Effects

```r
m1 <- feols(log_welfare ~ education + age + hhsize, data = dt)
m2 <- feols(log_welfare ~ education + age + hhsize | region, data = dt)
m3 <- feols(log_welfare ~ education + age + hhsize | region + year, data = dt)
```

### Stata comparison

| Stata | fixest |
|-------|--------|
| `reg y x1 x2` | `feols(y ~ x1 + x2, data = dt)` |
| `reghdfe y x1 x2, absorb(fe1 fe2)` | `feols(y ~ x1 + x2 \| fe1 + fe2, data = dt)` |

## Clustering Standard Errors

```r
m1 <- feols(log_welfare ~ education + age | region + year,
            vcov = ~psu, data = dt)

# Two-way clustering
m2 <- feols(log_welfare ~ education + age | region + year,
            vcov = ~psu + year, data = dt)

# Change clustering after estimation
summary(m1, vcov = ~region)
```

## Interactions with i()

```r
m1 <- feols(log_welfare ~ i(education_level, age) | region, data = dt)
m2 <- feols(log_welfare ~ i(education_level, ref = "primary") + age | region, data = dt)
```

## Staggered DiD with sunab()

```r
m_sa <- feols(outcome ~ sunab(cohort, period) | unit + period, data = dt)
iplot(m_sa, xlab = "Periods since treatment", ylab = "Effect")
```

## Multiple Estimations

```r
m_csw <- feols(log_welfare ~ age + csw(education, hhsize, urban) | region, data = dt)
etable(m_csw)
```

## modelsummary — Publication-Ready Tables

```r
msummary(
  list("OLS" = m1, "Region FE" = m2, "Full" = m3),
  stars     = c("*" = 0.1, "**" = 0.05, "***" = 0.01),
  coef_map  = c(education = "Education (years)", age = "Age (years)",
                hhsize = "Household size"),
  gof_map   = c("nobs", "r.squared", "FE: region", "FE: year"),
  title     = "Table 1: Welfare Determinants",
  notes     = "Standard errors clustered at PSU level.",
  output    = "output/tables/table1_welfare.docx"
)

# Summary statistics table
datasummary(
  welfare + income + hhsize + age ~ Mean + SD + Min + Max + N,
  data = dt, output = "output/tables/summary_stats.docx"
)

# Balance table
datasummary_balance(~ treated, data = dt, output = "output/tables/balance.docx")
```

## Workflow: collapse Prep → fixest Estimation → modelsummary Output

```r
# 1. Prepare data with collapse
dt[, log_welfare := log(welfare)]
qsu(dt, cols = c("log_welfare", "education", "age"), w = ~ weight)

# 2. Estimate with fixest
m1 <- feols(log_welfare ~ education + age + hhsize, vcov = ~psu, data = dt)
m2 <- feols(log_welfare ~ education + age + hhsize | region, vcov = ~psu, data = dt)
m3 <- feols(log_welfare ~ education + age + hhsize | region + year, vcov = ~psu, data = dt)

# 3. Output with modelsummary
msummary(list("OLS" = m1, "Region FE" = m2, "Region+Year FE" = m3),
         stars = c("*" = 0.1, "**" = 0.05, "***" = 0.01),
         output = "output/tables/table1.docx")
```
