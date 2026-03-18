# Common R Anti-Patterns — Analytical

## Survey Analysis Anti-Patterns

| Anti-Pattern | Problem | Fix |
|-------------|---------|-----|
| Subsetting data before declaring design | Drops obs, distorts variance estimates | Declare full design first; use `filter()` after |
| `weighted.mean()` without survey package | Gives point estimate only, no SE | Use `srvyr::survey_mean()` |
| Computing SE manually from weighted data | Wrong — ignores cluster/strata structure | Always use design-aware functions |
| Ignoring `nest = TRUE` in PSU designs | Wrong variance if PSU IDs repeat across strata | Always set `nest = TRUE` for clustered designs |
| Using `lm()` for survey regression | No design-based inference | Use `survey::svyglm()` or `fixest` with weights |
| Forgetting `na.rm = TRUE` in weighted means | Returns NA silently | Always pass `na.rm = TRUE` |
| Using unweighted sample counts as population totals | Estimates are unweighted | Use `survey_total()` → weighted total |

## Stata Migration Anti-Patterns

| Anti-Pattern | Problem | Fix |
|-------------|---------|-----|
| `read_dta()` without `as.data.table()` | Returns tibble; behaves differently | Wrap: `as.data.table(read_dta(...))` |
| Treating `NA` like Stata's `.` extended missing | Extended missing (`.a`, `.b`) coerced to `NA` | Check `haven::is.na.labelled()` if distinctions matter |
| Converting all labelled → factor immediately | Loses original numeric codes | Hold off; convert only analysis-ready variables |
| Ignoring variable labels | Rich Stata metadata lost | `haven::var_label(dt$x)` for documentation |
| Replicating Stata loops with `for` | Very slow in R | Vectorize with data.table or `lapply()` |

## Econometrics Anti-Patterns

| Anti-Pattern | Problem | Fix |
|-------------|---------|-----|
| `lm()` with fixed effects as dummies | O(n×k) matrix inversion; slow | Use `fixest::feols()` with `|` syntax |
| Homoskedastic SE by default | Invalid for survey/panel data | Always specify `cluster` or use `se = "hetero"` |
| `summary(lm())` in a loop | Hard to aggregate and export | Collect in list; export with `modelsummary()` |
| Not absorbing FE correctly | Biased estimates if FE correlated with X | Use `feols()` which partials out FE efficiently |
| Forgetting `stage = 1` check in IV | Weak instruments undetected | Always inspect first stage F-statistic |
| `coef(model)` for table building | Tedious; inconsistent formatting | Use `modelsummary::msummary()` |
| Hard-coding standard error type | Different papers need different SEs | Parameterize the SE type; document the choice |

## Welfare Measurement Anti-Patterns

| Anti-Pattern | Problem | Fix |
|-------------|---------|-----|
| Computing poverty with unweighted data | Ignores sampling design | Always use survey weights |
| Comparing poverty across years without PPP deflation | Nominal changes misread as real | Use consistent price base (2017 PPP) |
| Mixing LCU and PPP in same computation | Unit error; nonsensical results | Use `_lcu` / `_ppp` naming convention rigorously |
| `mean(income < line)` instead of weighted poverty | Unweighted headcount | `weighted.mean(income < line, wgt)` |
| Ignoring household size in per-capita measures | Household welfare ≠ individual welfare | Use `hh_income / hh_size` and individual weights |
| Gini from grouped data | Approximation error | Use micro data with individual observations |

## Visualization Anti-Patterns

| Anti-Pattern | Problem | Fix |
|-------------|---------|-----|
| Default ggplot2 theme on WB outputs | Doesn't meet WB visual identity | Use `theme_wb()` |
| Not citing data source | Readers can't verify | Always add `caption = "Source: ..."` to `labs()` |
| Pie charts | Hard to compare values; WB discourages them | Use bar charts or dot plots |
| Dual y-axes | Misleading; easy to manipulate scale | Use facets or separate plots |
| Too many colors | Confusing; fails accessibility | Max 6–7 categorical colors; use `scale_color_wb_d()` |
| Non-zero y-axis origin on bar charts | Exaggerates differences | Bar charts must start at 0 |
| Saving with low DPI | Blurry in reports | Always `ggsave(..., dpi = 300)` |
