# Econometrics with fixest and modelsummary

## OLS with fixest

```r
library(fixest)

# Basic OLS
m1 <- feols(log_consumption ~ educ + age + I(age^2), data = dt)

# With fixed effects
m2 <- feols(log_consumption ~ educ + age | country + year, data = dt)

# Clustered standard errors
m3 <- feols(log_consumption ~ educ + age | country + year,
            cluster = ~country, data = dt)

# Multiple SEs in one call
summary(m3, se = "hetero")      # heteroskedasticity-robust
summary(m3, se = "cluster")     # default clustered se
summary(m3, se = "twoway")      # two-way clustering
```

## Fixed Effects Shorthand

```r
# Single FE
feols(y ~ x | fe1, data = dt)

# Two-way FE
feols(y ~ x | fe1 + fe2, data = dt)

# Interacted FE
feols(y ~ x | fe1^fe2, data = dt)   # fe1 × fe2 combination

# IV with FE
feols(y ~ 1 | fe1 | x ~ instrument, data = dt)
```

## Panel Models

```r
# Within estimator (equivalent to including unit FE)
feols(y ~ x | unit_id + time, data = panel_dt)

# First differences
dt[, y_fd := y - shift(y), by = unit_id]
feols(y_fd ~ x_fd, data = dt)
```

## Staggered DiD (Sun & Abraham 2021)

```r
# sunab() for heterogeneity-robust staggered DiD
m_sa <- feols(y ~ sunab(cohort_var, time_var) | unit + time,
              data = dt,
              cluster = ~unit)

# Aggregate: average treatment effect
summary(m_sa, agg = "att")

# Plot event study
iplot(m_sa)
```

## Output Tables with modelsummary

```r
library(modelsummary)

# Console output
msummary(list(m1, m2, m3))

# Export to Word
msummary(list("No FE" = m1, "Country FE" = m2, "Country+Year FE" = m3),
         output = "output/tables/results.docx",
         stars = c("*" = 0.1, "**" = 0.05, "***" = 0.01),
         coef_rename = c(educ = "Education (years)", age = "Age"),
         gof_omit = "AIC|BIC|Log|RMSE|Std")

# Export to LaTeX
msummary(list(m1, m2, m3),
         output = "output/tables/results.tex",
         booktabs = TRUE,
         title = "Determinants of Household Consumption")

# modelplot for coefficient plots
modelplot(list(m1, m2, m3),
          coef_omit = "Intercept") +
  ggplot2::geom_vline(xintercept = 0, linetype = "dashed")
```

## Diagnostic Tests

```r
# Heteroskedasticity test (car package)
car::ncvTest(lm(y ~ x, data = dt))

# F-test for joint significance
wald(m2, c("educ", "age"))

# Check first stage in IV
summary(m_iv, stage = 1)   # fixest IV first stage

# Fit statistics
fitstat(m2, ~ r2 + ar2 + f)
```

## Multiple Outcomes Pattern

```r
# Estimate same specification across multiple outcomes
outcomes <- c("log_consumption", "log_food", "log_nonfood")

models <- lapply(outcomes, function(y) {
  feols(as.formula(paste(y, "~ educ + age | country + year")),
        cluster = ~country, data = dt)
})
names(models) <- outcomes

msummary(models, output = "output/tables/multi_outcomes.docx")
```
