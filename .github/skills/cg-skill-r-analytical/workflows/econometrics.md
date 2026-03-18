# Econometrics

Regression analysis using `fixest` for estimation and `modelsummary` for publication-ready tables. `fixest` is the R package closest to Stata's `reghdfe` — fast, multi-way fixed effects, flexible clustering.

## fixest Basics

### OLS with Fixed Effects

```r
library(fixest)
library(data.table)

# Simple OLS
m1 <- feols(log_welfare ~ education + age + hhsize, data = dt)

# With fixed effects (equivalent to Stata's areg or reghdfe)
m2 <- feols(log_welfare ~ education + age + hhsize | region, data = dt)

# Two-way fixed effects
m3 <- feols(log_welfare ~ education + age + hhsize | region + year, data = dt)

# Three-way fixed effects
m4 <- feols(log_welfare ~ education + age + hhsize | region + year + sector, data = dt)
```

### Stata comparison

| Stata | fixest |
|-------|--------|
| `reg y x1 x2` | `feols(y ~ x1 + x2, data = dt)` |
| `areg y x1 x2, absorb(fe)` | `feols(y ~ x1 + x2 \| fe, data = dt)` |
| `reghdfe y x1 x2, absorb(fe1 fe2)` | `feols(y ~ x1 + x2 \| fe1 + fe2, data = dt)` |

The `|` separates the linear part from the fixed effects — everything after `|` is absorbed.

## Clustering Standard Errors

```r
# Cluster at one level (equivalent to Stata's vce(cluster var))
m1 <- feols(log_welfare ~ education + age | region + year,
            vcov = ~psu, data = dt)

# Two-way clustering
m2 <- feols(log_welfare ~ education + age | region + year,
            vcov = ~psu + year, data = dt)

# Change clustering after estimation (no re-estimation needed)
summary(m1, vcov = ~region)
summary(m1, vcov = ~psu + year)
```

### Stata comparison

| Stata | fixest |
|-------|--------|
| `reghdfe y x, absorb(fe) vce(cluster v)` | `feols(y ~ x \| fe, vcov = ~v, data = dt)` |
| `reghdfe y x, absorb(fe) vce(cluster v1 v2)` | `feols(y ~ x \| fe, vcov = ~v1 + v2, data = dt)` |

A major advantage of fixest: you can change the variance-covariance structure after estimation without re-running the model:

```r
summary(m1, vcov = ~region)
summary(m1, vcov = ~psu + year)
```

## Interactions and Factor Variables with i()

`fixest` uses `i()` for factor interactions, similar to Stata's factor variable notation.

```r
# Interact a continuous variable with a factor
m1 <- feols(log_welfare ~ i(education_level, age) | region,
            data = dt)

# Interaction between two factors
m2 <- feols(log_welfare ~ i(region, education_level) | year,
            data = dt)

# Reference category control
m3 <- feols(log_welfare ~ i(education_level, ref = "primary") + age | region,
            data = dt)
```

### Stata comparison

| Stata | fixest |
|-------|--------|
| `reg y i.group` | `feols(y ~ i(group), data = dt)` |
| `reg y i.group#c.x` | `feols(y ~ i(group, x), data = dt)` |
| `reg y ib2.group` | `feols(y ~ i(group, ref = 2), data = dt)` |

## Difference-in-Differences

### Standard Two-Period DiD

```r
# Classic 2x2 DiD
m_did <- feols(outcome ~ treated * post | unit + time,
               data = dt)
```

### Staggered DiD with Sun & Abraham (sunab)

For staggered treatment adoption (units treated at different times), the standard TWFE estimator is biased. Use `sunab()`:

```r
# sunab() implements Sun & Abraham (2021) interaction-weighted estimator
# cohort: the period when unit was first treated (Inf if never treated)
# period: the time period
m_sa <- feols(outcome ~ sunab(cohort, period) | unit + period,
              data = dt)

# View the event-study coefficients
summary(m_sa)

# Plot the event study
iplot(m_sa,
      xlab = "Periods since treatment",
      ylab = "Effect",
      main = "Event Study — Sun & Abraham")
```

The `cohort` variable must be the year/period of first treatment for each unit. Units never treated should have `cohort = Inf` (or a value larger than any period in the data).

### Event Study Plots with iplot()

```r
# Estimate event study with i() syntax
m_es <- feols(outcome ~ i(time_to_treat, ref = -1) | unit + period,
              data = dt)

# Basic event study plot
iplot(m_es)

# Customized event study plot
iplot(m_es,
      xlab = "Periods relative to treatment",
      ylab = "Coefficient estimate",
      main = "Event Study",
      col = "steelblue",
      ci_col = "steelblue",
      ci_lwd = 1.5)
```

## Generalized Linear Models

```r
# Logit with fixed effects
m_logit <- feglm(poor ~ education + age + hhsize | region + year,
                 family = binomial(link = "logit"),
                 data = dt)

# Poisson regression
m_pois <- feglm(count ~ treatment + controls | region,
                family = poisson(),
                data = dt)
```

## Multiple Estimations

`fixest` can run multiple models in a single call with `sw()` (stepwise) and `csw()` (cumulative stepwise):

```r
# Stepwise: swap RHS variables one at a time
m_sw <- feols(log_welfare ~ age + sw(education, hhsize, urban) | region,
              data = dt)

# Cumulative stepwise: build up the specification
m_csw <- feols(log_welfare ~ age + csw(education, hhsize, urban) | region,
               data = dt)

# Multiple dependent variables
m_multi <- feols(c(log_welfare, log_income) ~ education + age | region,
                 data = dt)

# Multiple fixed effect specifications
m_fe <- feols(log_welfare ~ education + age | csw(region, year, sector),
              data = dt)

# Display all results
etable(m_csw)
```

## etable() — Quick Regression Tables

```r
# Compare models side by side in the console
etable(m1, m2, m3)

# Control what's displayed
etable(m1, m2, m3,
       se.below  = TRUE,       # SEs below coefficients
       keep      = c("education", "age"),  # show only these
       order     = c("education", "age"),  # order rows
       dict      = c(education = "Years of education",
                      age = "Age (years)"),
       fitstat   = ~ r2 + n)   # which fit statistics to show
```

## modelsummary — Publication-Ready Tables

`modelsummary` produces tables that go directly into papers and reports. It works seamlessly with `fixest` output.

### Basic Usage

```r
library(modelsummary)

# Table to console
msummary(list("(1)" = m1, "(2)" = m2, "(3)" = m3))

# Table to Word document
msummary(list("(1)" = m1, "(2)" = m2, "(3)" = m3),
         output = "output/tables/regression_table.docx")

# Table to LaTeX
msummary(list("(1)" = m1, "(2)" = m2, "(3)" = m3),
         output = "output/tables/regression_table.tex")

# Table to HTML
msummary(list("(1)" = m1, "(2)" = m2, "(3)" = m3),
         output = "output/tables/regression_table.html")
```

### Customized Tables

```r
msummary(
  list("Baseline" = m1, "With FE" = m2, "Full" = m3),
  stars     = c("*" = 0.1, "**" = 0.05, "***" = 0.01),
  coef_map  = c(
    "education"    = "Years of Education",
    "age"          = "Age",
    "hhsize"       = "Household Size",
    "urban"        = "Urban"
  ),
  gof_map   = c("nobs", "r.squared", "adj.r.squared",
                 "FE: region", "FE: year"),
  title     = "Determinants of Welfare",
  notes     = "Standard errors clustered at PSU level.",
  output    = "output/tables/welfare_determinants.docx"
)
```

### Summary Statistics Tables with datasummary()

```r
# Descriptive statistics table
datasummary(
  welfare + income + hhsize + age ~ Mean + SD + Min + Max + N,
  data = dt,
  output = "output/tables/summary_stats.docx",
  title = "Summary Statistics"
)

# Summary statistics by group
datasummary(
  welfare + income + hhsize ~ region * (Mean + SD),
  data = dt,
  output = "output/tables/summary_by_region.docx"
)

# Balance table (treatment vs control)
datasummary_balance(
  ~ treated,
  data = dt,
  dinm_statistic = "p.value",
  output = "output/tables/balance_table.docx"
)
```

## Workflow: From Estimation to Paper Table

```r
library(fixest)
library(modelsummary)

# 1. Estimate models
m1 <- feols(log_welfare ~ education + age + hhsize,
            vcov = ~psu, data = dt)
m2 <- feols(log_welfare ~ education + age + hhsize | region,
            vcov = ~psu, data = dt)
m3 <- feols(log_welfare ~ education + age + hhsize | region + year,
            vcov = ~psu, data = dt)

# 2. Produce table for the paper
msummary(
  list("OLS" = m1, "Region FE" = m2, "Region + Year FE" = m3),
  stars     = c("*" = 0.1, "**" = 0.05, "***" = 0.01),
  coef_map  = c(
    "education" = "Education (years)",
    "age"       = "Age (years)",
    "hhsize"    = "Household size"
  ),
  gof_map   = c("nobs", "r.squared", "FE: region", "FE: year"),
  title     = "Table 1: Welfare Determinants",
  notes     = list("Standard errors clustered at PSU level.",
                    "Dependent variable: log per capita consumption (2017 PPP)."),
  output    = "output/tables/table1_welfare.docx"
)

# 3. Also save as LaTeX for the working paper
msummary(
  list("OLS" = m1, "Region FE" = m2, "Region + Year FE" = m3),
  stars     = c("*" = 0.1, "**" = 0.05, "***" = 0.01),
  coef_map  = c(
    "education" = "Education (years)",
    "age"       = "Age (years)",
    "hhsize"    = "Household size"
  ),
  gof_map   = c("nobs", "r.squared", "FE: region", "FE: year"),
  output    = "output/tables/table1_welfare.tex"
)
```
