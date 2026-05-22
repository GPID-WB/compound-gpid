---
name: cr-skill-publication-output
module: research
description: "Publication-quality output for economics research. Covers
  modelsummary/fixest::etable for regression tables, kableExtra for LaTeX
  tables, ggplot2+wbplot for paper figures, font/size conventions for journal
  submission, figure-caption discipline (self-contained), and table-note
  discipline (variable definitions in notes). Loaded by @cr-academic-writing
  and /cr-work for Tables/Figures tasks."
---

# Publication Output for Economics Research

Reference skill for producing publication-quality tables, figures, and output
files for economics papers. Load for Tables/Figures task types and when
reviewing output code.

---

## 1. Regression Tables

### `modelsummary` — Preferred for Multi-Model Tables

```r
library(modelsummary)

# Basic multi-model table
models <- list(
  "OLS"    = lm(log_wage ~ education + experience, data = df),
  "IV"     = ivreg(log_wage ~ education | proximity, data = df),
  "FE"     = feols(log_wage ~ education | worker_id, data = df)
)

modelsummary(
  models,
  stars    = c("*" = 0.1, "**" = 0.05, "***" = 0.01),
  gof_map  = c("nobs", "r.squared", "adj.r.squared"),
  coef_map = c("education" = "Years of education",
               "experience" = "Work experience (years)"),
  notes    = "Standard errors in parentheses. OLS: robust SE. IV: 2SLS.
              FE: clustered by worker.",
  output   = "output/tables/table-2-wage-regressions.tex"
)
```

**Key options**:
- `coef_map` — rename and reorder coefficients (only listed coefficients appear)
- `gof_map` — control which goodness-of-fit statistics appear
- `stars` — use consistent significance levels across the paper
- `fmt` — control decimal places: `fmt = "%.3f"` for three decimals
- `vcov` — pass custom variance-covariance matrices: `vcov = list(~cluster_var)`

### `fixest::etable` — Preferred for `feols` Output

```r
library(fixest)

m1 <- feols(log_wage ~ education | worker_id, data = df)
m2 <- feols(log_wage ~ education + experience | worker_id + year, data = df)
m3 <- feols(log_wage ~ education + experience | worker_id + year,
            cluster = ~industry, data = df)

etable(
  m1, m2, m3,
  se       = "cluster",
  tex      = TRUE,
  file     = "output/tables/table-3-fe-regressions.tex",
  digits   = 3,
  signif.code = c("***" = 0.01, "**" = 0.05, "*" = 0.10),
  headers  = c("Baseline", "+ Controls", "Industry Cluster"),
  notes    = "Dependent variable: log hourly wage. All specifications include
              worker fixed effects. Standard errors (clustered) in parentheses."
)
```

**`etable` advantages over `modelsummary`**:
- Native `feols` output: FE counts, Wald tests, first-stage F-stats displayed automatically
- `se` argument controls SE type natively (robust, cluster, twoway)
- `keep` / `drop` arguments filter coefficients without renaming

### `stargazer` — Legacy Only

Use only when maintaining existing code. For new tables, prefer `modelsummary`
or `etable`.

### Standards for All Regression Tables

- Standard errors always in parentheses (not t-statistics)
- Report significance stars but note they are advisory, not the primary result
- Always report N (number of observations)
- Always report the SE type in table notes
- Column headers should label what varies (estimator, specification, sample)
- Do not omit control variables without explaining why

---

## 2. LaTeX Tables — `kableExtra`

### Descriptive Statistics Table

```r
library(kableExtra)
library(dplyr)

desc_stats <- df |>
  summarise(
    across(c(log_wage, education, experience, age),
           list(Mean = mean, SD = sd, Min = min, Max = max,
                N = ~sum(!is.na(.))),
           .names = "{.col}_{.fn}")
  ) |>
  pivot_longer(everything(), names_to = c("Variable", ".value"),
               names_sep = "_(?=[^_]+$)")

kbl(
  desc_stats,
  format  = "latex",
  booktabs = TRUE,
  digits  = 2,
  col.names = c("Variable", "Mean", "SD", "Min", "Max", "N"),
  caption = "Descriptive Statistics",
  label   = "tab:desc-stats"
) |>
  kable_styling(latex_options = c("hold_position")) |>
  add_footnote(
    "Sample: employed workers aged 25–60. Log wage is the natural log
     of hourly earnings. Education measured in completed years.",
    notation = "none"
  ) |>
  save_kable("output/tables/table-1-descriptives.tex")
```

### Balance Table

```r
kbl(
  balance_df,
  format   = "latex",
  booktabs = TRUE,
  digits   = 3,
  col.names = c("Variable", "Control Mean", "Treated Mean",
                "Difference", "SE", "p-value"),
  caption  = "Balance Table: Baseline Characteristics",
  label    = "tab:balance"
) |>
  kable_styling() |>
  pack_rows("Demographics", 1, 4) |>
  pack_rows("Labor market", 5, 8) |>
  add_footnote(
    "Difference column reports OLS coefficient on treatment indicator.
     Robust standard errors. *p<0.10, **p<0.05, ***p<0.01.",
    notation = "none"
  ) |>
  save_kable("output/tables/appendix-balance-table.tex")
```

### `gt` — HTML-First Output

Use `gt` when the primary output is HTML (slides, web reports). For journal
submission, prefer `kableExtra` (LaTeX-native).

```r
library(gt)

desc_stats |>
  gt() |>
  tab_header(title = "Descriptive Statistics") |>
  fmt_number(columns = c(Mean, SD), decimals = 2) |>
  tab_source_note("Sample: employed workers 25–60.")
```

---

## 3. Figures — ggplot2 + wbplot

### World Bank Style (wbplot)

For papers and reports destined for World Bank publication:

```r
library(ggplot2)
library(wbplot)

p <- ggplot(df, aes(x = year, y = poverty_rate, color = region)) +
  geom_line(linewidth = 0.8) +
  geom_point(size = 2) +
  scale_color_wb_d() +
  theme_wb() +
  labs(
    title   = "Poverty Rate Trends by Region",
    x       = "Year",
    y       = "Poverty rate (%, $2.15/day)",
    color   = NULL,
    caption = "Source: PovcalNet. Sample: 45 countries with consistent data 2000–2020."
  )

ggsave("output/figures/figure-1-poverty-trends.pdf",
       plot = p, width = 6.5, height = 4, units = "in")
ggsave("output/figures/figure-1-poverty-trends.png",
       plot = p, width = 6.5, height = 4, units = "in", dpi = 300)
```

### Common Plot Types

**Event study / Coefficient plot**:
```r
library(ggplot2)

coef_df |>  # data frame with columns: term, estimate, conf.low, conf.high
  ggplot(aes(x = term, y = estimate, ymin = conf.low, ymax = conf.high)) +
  geom_hline(yintercept = 0, linetype = "dashed", color = "grey50") +
  geom_errorbar(width = 0.2) +
  geom_point(size = 2.5) +
  coord_flip() +
  theme_wb() +
  labs(x = NULL, y = "Coefficient estimate (95% CI)")
```

**Distribution overlay**:
```r
ggplot(df, aes(x = log_wage, fill = group)) +
  geom_density(alpha = 0.4) +
  scale_fill_wb_d() +
  theme_wb() +
  labs(x = "Log hourly wage", y = "Density", fill = NULL)
```

**Binned scatter (non-parametric relationship)**:
```r
library(binsreg)
binsreg(y = df$log_wage, x = df$education, data = df,
        line   = c(3, 3),
        ci     = c(3, 3),
        plotxrange = c(0, 20))
```

---

## 4. Font and Size Conventions

### Journal Submission Standards

| Element | Size | Format |
|---------|------|--------|
| Figure body text | 10–11pt | Match surrounding text |
| Axis labels | 9–10pt | Sans-serif acceptable |
| Legend text | 8–10pt | Same font as axis labels |
| Title (if included) | 11–12pt | Bold discouraged |

### Output Formats

- **Primary**: PDF (vector) — required for journal submission
- **Secondary**: PNG at 300 DPI — for slide decks and working papers
- **Never**: JPEG for plots with text or thin lines

### Color Considerations

- Verify every figure is legible in **grayscale** (many journals print in black and white)
- Use `scale_color_wb_d()` / `scale_fill_wb_d()` from `wbplot` — these palettes are
  colorblind-safe and print well in grayscale
- Never rely on color alone to distinguish categories — add shape or linetype

### `ggsave()` Standard Dimensions

| Format | Width | Height | Note |
|--------|-------|--------|------|
| Full-page figure | 6.5 in | 4.5 in | Single column in two-column layout |
| Half-page / narrow | 3.25 in | 3.0 in | Two-column figure in paper |
| Presentation slide | 8 in | 5 in | 16:9 ratio |

Always specify `units = "in"` explicitly. Never rely on `ggsave()` defaults.

---

## 5. Figure-Caption Discipline

### Self-Contained Captions

Every caption must stand alone — a reader who sees only the figure + caption
must understand it without reading the body text.

**Required elements**:
1. What is plotted (dependent variable, X axis, unit)
2. Sample (population, period, restrictions)
3. Key takeaway (what the figure shows)

**Template**:
> "Figure N. [Descriptive title]. [What is plotted, with units]. [Sample and
> period]. [One sentence stating the key takeaway]. [Data source.]"

**Example**:
> "Figure 1. Poverty trends by region, 2000–2020. Each line plots the annual
> headcount poverty rate (%) using the $2.15/day international line.
> Sample: 45 countries with comparable welfare surveys in every year.
> All regions show declining poverty, with Sub-Saharan Africa converging toward
> East Asian levels after 2010. Source: PovcalNet."

### Anti-Patterns

| Anti-pattern | Fix |
|-------------|-----|
| "Poverty rates by region." | Add sample, period, and key takeaway |
| "See text for details." | All relevant details belong in the caption |
| Caption longer than the figure is tall | Trim to essential information |
| Referring to colors without showing a legend | Add a legend or identify in caption |

---

## 6. Table-Note Discipline

### Required Table Notes

Every regression table must include notes that define:
1. **Variables**: full name and unit for every variable in the table
2. **Sample**: how observations were selected
3. **SE type**: "Robust standard errors in parentheses" / "Standard errors
   clustered by [unit] in parentheses"
4. **Significance levels**: "* p < 0.10, ** p < 0.05, *** p < 0.01"
5. **Fixed effects** (if any): "All specifications include worker × year FE"

### Formatting Notes in LaTeX

In `modelsummary` / `kableExtra`, use `add_footnote(..., notation = "none")` to
avoid numbering notes (economics convention — no numbered footnotes in tables).

```r
# modelsummary
modelsummary(models, notes = "Notes: [your text here]")

# kableExtra
kbl(...) |>
  add_footnote("Notes: [your text here]", notation = "none")
```

### Short Descriptive Statistics Tables

For descriptive statistics tables, notes should state:
- Sample definition
- Source of data
- Any transformations applied (e.g., "log-transformed")
- Whether sample weights were used

---

## 7. Output File Management

### Directory Convention

```
output/
├── tables/
│   ├── table-1-descriptives.tex
│   ├── table-2-main-results.tex
│   └── appendix-table-a1-robustness.tex
└── figures/
    ├── figure-1-poverty-trends.pdf
    ├── figure-1-poverty-trends.png
    └── figure-2-event-study.pdf
```

### Filename Convention

- Use **descriptive, self-documenting** names: `table-2-main-regressions.tex`
  not `tab2.tex` or `table_final_v3.tex`
- Use hyphens, not underscores or spaces
- Number matches the paper: `table-1`, `figure-3`, `appendix-table-a2`

### Deterministic Output

Table and figure code must produce **identical output** on every run:
- Never rely on system locale for number formatting — use `fmt` arguments
- Save with explicit dimensions, not device defaults
- Commit output files to git only if they are small LaTeX/PDF and tracked in `renv.lock`

### `ggsave()` Anti-Patterns

```r
# ❌ Relies on active graphics device size
ggsave("figure-1.pdf")

# ✅ Explicit dimensions, format, dpi
ggsave("output/figures/figure-1-main.pdf",
       plot = p, width = 6.5, height = 4, units = "in")
```
