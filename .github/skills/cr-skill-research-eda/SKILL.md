---
name: cr-skill-research-eda
module: research
description: "Research-framed exploratory data analysis for economics research.
  Covers targeted distributional checks, conditional moment plots, weighted
  descriptive statistics using collapse (fmean/fsd/fmedian with w argument),
  missingness patterns, outlier analysis, sample restriction documentation,
  subgroup analysis, and EDA anti-patterns. Loaded for EDA and Specification
  Analysis tasks."
---

# Research-Framed EDA

Reference skill for exploratory data analysis in economics research. EDA is
not a free-form exercise — each check should be motivated by a hypothesis,
model assumption, or identification concern. Document what you looked for,
what you found, and what it implies for modeling.

---

## 1. Research-Framed EDA Philosophy

**Principle**: Every EDA table or plot must answer a question that matters
for the model or identification strategy.

Before running any EDA, write down:
1. What assumption or hypothesis am I checking?
2. What would "consistent with the model" look like?
3. What would "inconsistent" look like?
4. What action will I take for each outcome?

Store EDA outputs in `.cg-docs/research/eda/YYYY-MM-DD-[topic].md` with
the question-result-action structure above.

**EDA roadmap** for a typical structural model:
1. Sample restrictions + missingness (Section 2 below)
2. Distributional checks of key variables (Section 3)
3. Conditional moment plots for key relationships (Section 4)
4. Weighted descriptive statistics (Section 5)
5. Outlier analysis (Section 6)
6. Subgroup analysis for heterogeneity (Section 8)

---

## 2. Targeted Distributional Checks

**When to use**: Before modeling any continuous variable, understand its
distribution. Motivate by the model: what distribution does the model assume?

```r
library(data.table)
library(collapse)
library(ggplot2)
library(wbplot)

# Histogram with density overlay
ggplot(df, aes(x = log_wage)) +
  geom_histogram(aes(y = after_stat(density)), bins = 50,
                 fill = WBCOLORS["navy"], alpha = 0.7) +
  geom_density(color = WBCOLORS["red"], linewidth = 1) +
  theme_wb() +
  labs(title = "Distribution of Log Wages",
       subtitle = "Model assumes normality — check Q-Q plot next")

# Q-Q plot
qqnorm(df$log_wage, main = "Q-Q Plot: Log Wage vs. Normal")
qqline(df$log_wage)

# Key quantiles + moments
qsu(df$log_wage, w = df$weight)  # collapse: weighted N, mean, sd, min, p25, p50, p75, max
```

**For discrete variables**:
```r
# Frequency table with proportions
tabulate_var <- function(x, w = NULL) {
  if (is.null(w)) table(x) / length(x)
  else             wtd.table(x, weights = w) / sum(w)  # see Hmisc::wtd.table
}
```

**Anti-patterns**:
- Plotting without weights (when data are from surveys)
- Summary statistics without noting N and the weight variable used

---

## 3. Conditional Moment Plots

**When to use**: Verify that the conditional expectation function $E[Y|X]$
matches the shape assumed by the model (linearity, log-linearity, etc.).

```r
# Binned scatter plot (non-parametric conditional mean)
library(binsreg)
binsreg(y = df$log_wage, x = df$education,
        w = as.matrix(df[, .(age, female)]),  # residualize on controls
        weights = df$weight,
        nbins = 20)

# Alternatively: LOESS with ggplot
ggplot(df, aes(x = education, y = log_wage)) +
  geom_point(alpha = 0.1, size = 0.5) +
  geom_smooth(method = "loess", se = TRUE,
              color = WBCOLORS["navy"]) +
  geom_smooth(method = "lm", se = FALSE,
              color = WBCOLORS["red"], linetype = "dashed") +
  theme_wb() +
  labs(title = "E[log wage | education]: LOESS vs. Linear",
       subtitle = "Red dashed = OLS fit; check for non-linearity")

# Stata
binsreg log_wage education [pw=weight], controls(age female) nbins(20)
```

**Interpretation**: If LOESS deviates substantially from OLS, the linear
model is misspecified. Consider: polynomial terms, splines, or log transformation.

---

## 4. Weighted Descriptive Statistics

**When to use**: Survey or administrative data with sampling weights.
Always weight descriptive statistics; unweighted statistics are
representative of the sample, not the population.

```r
library(collapse)

# --- Weighted univariate statistics ---
fmean(df$log_wage, w = df$weight)     # weighted mean
fsd(df$log_wage,   w = df$weight)     # weighted SD
fmedian(df$log_wage, w = df$weight)   # weighted median
fnth(df$log_wage, n = 0.9, w = df$weight)  # weighted 90th percentile

# --- Weighted by group ---
fmean(df$log_wage, g = df$region, w = df$weight)   # weighted mean per region

# --- qsu: weighted summary statistics table ---
qsu(df[, .(log_wage, education, age)], w = df$weight, higher = TRUE)
# Returns: N, weighted mean, weighted SD, skewness, kurtosis, min, max

# --- Weighted two-way descriptive table ---
descr(df[, .(log_wage, education)],
      by = ~ gender,
      w = df$weight,
      Fstat = TRUE)
```

**For non-numeric weighted statistics**:
```r
# Weighted frequency table
props <- fmean(model.matrix(~ factor(region) - 1, data = df),
               w = df$weight)
# Or: wtd.table from Hmisc
```

**Stata**:
```stata
svyset psu [pw=weight], strata(strata) vce(linearized)
svy: mean log_wage
svy: mean log_wage, over(region)
svy: tabulate region gender, pearson
```

---

## 5. Missingness Patterns

**When to use**: Before any analysis, understand the missing data structure.
Missing at random (MAR) vs. missing not at random (MNAR) has major
implications for identification.

```r
# Count and proportion missing per variable
miss_summary <- sapply(df, function(x)
  c(n_miss = sum(is.na(x)), pct_miss = mean(is.na(x))))
t(miss_summary)

# Check if missingness is random with respect to key variables
miss_model <- lm(is.na(log_wage) ~ education + age + female + region,
                  data = df)
summary(miss_model)
# H0: missingness is uncorrelated with X → if significant, MNAR risk

# Missing pattern visualization
library(naniar)
vis_miss(df[, .(log_wage, education, age)])
gg_miss_upset(df[, .(log_wage, education, age)])  # co-missingness patterns
```

**Documentation**: For each variable with > 5% missing:
1. State the mechanism (why is this variable missing?)
2. State the assumption (MAR? MNAR? Structural?)
3. State the action (complete case, imputation, structural model for selection)

---

## 6. Outlier Analysis

**When to use**: Identify influential observations that may distort estimation.
Do not drop outliers silently — document each decision.

```r
# Leverage and Cook's distance (OLS)
fit <- lm(log_wage ~ education + age + female, data = df)
plot(fit, which = c(4, 5))  # Cook's distance + leverage-residual plot

# Standardized residuals (flag > 3 or < -3)
df[, std_resid := rstandard(fit)]
outliers <- df[abs(std_resid) > 3]
message(nrow(outliers), " observations with |std_resid| > 3")

# Weighted boxplot of key variables
boxplot(df$log_wage, weights = df$weight, main = "Log Wage — Outliers")

# Rule: document all outliers considered; state whether dropped, capped, or retained
# If dropped: sensitivity check with full sample in appendix
```

**For panel data**:
```r
# Check for impossible values (wages < 0, age < 15, etc.)
df[log_wage < log(min_wage_threshold)]  # below minimum wage
df[age < 16 & employed == 1]            # impossible age-employment combination
```

---

## 7. Sample Restriction Documentation

**When to use**: Before any estimation, document every sample restriction.
Each restriction should have an economic or data-quality justification.

```markdown
## Sample Restrictions — Wage Analysis

| Step | Restriction | N Dropped | N Remaining | Justification |
|------|------------|-----------|-------------|---------------|
| 1 | Full PUMS sample | — | 2,845,231 | — |
| 2 | Age 25–55 | 1,102,445 | 1,742,786 | Prime-age workers; avoid schooling/retirement |
| 3 | Employed, not self-employed | 487,221 | 1,255,565 | Wage equation for wage workers only |
| 4 | Non-missing wage, education, age | 44,321 | 1,211,244 | Listwise deletion; MCAR tested |
| 5 | Wage > min wage | 12,885 | 1,198,359 | Remove miscoded wages; see outlier check |
| **Final** | — | — | **1,198,359** | |
```

Store the R/Stata code for each step in `data/clean/sample-restrictions.R`.
Never apply restrictions silently in the middle of analysis code.

---

## 8. Subgroup Analysis

**When to use**: Investigate heterogeneity in key relationships across
theoretically-motivated subgroups.

```r
library(collapse)

# Weighted mean wages by education-gender cells
fmean(df$log_wage,
      g = interaction(df$educ_group, df$female),
      w = df$weight)

# Heterogeneous returns to education by gender
by_gender <- split(df, df$female)
lapply(by_gender, function(d) {
  fit <- lm(log_wage ~ education + age, data = d, weights = d$weight)
  coef(fit)["education"]
})

# Or: interaction term approach
feols(log_wage ~ education * female + age | region,
      data = df, weights = ~weight, cluster = ~psu)

# Stata
bysort female: reg log_wage education age [pw=weight], vce(cluster psu)
```

**Documentation**: State the hypothesis motivating each subgroup analysis.
Distinguish confirmatory subgroups (pre-specified) from exploratory ones
(discovered in EDA). Exploratory subgroups require multiple-testing correction
or explicit caveat.

---

## 9. Anti-Patterns

| Anti-Pattern | Why It's Wrong | Fix |
|-------------|----------------|-----|
| Unweighted statistics for survey data | Not representative of population | Always use `fmean(x, w = weight)` etc. |
| EDA without research question | Fishing expedition | State question before each plot |
| Dropping outliers without documentation | Silent data manipulation | Document + sensitivity check |
| Missing data treated as missing at random without test | MNAR → biased estimates | Test with `lm(is.na(y) ~ X)` |
| Only looking at marginal distributions | Misses joint structure | Always do conditional moment plots |
| Sample restrictions applied in analysis code | Not reproducible; easy to miss | Use dedicated `sample-restrictions.R` |
| Exploratory subgroups presented as confirmatory | False discovery inflation | Label clearly; apply correction |
| Summary statistics without N | Reader cannot assess precision | Always report N (weighted and unweighted) |
