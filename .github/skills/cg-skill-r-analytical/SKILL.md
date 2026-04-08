---
name: cg-skill-r-analytical
description: "R patterns for analytical work: haven for Stata migration, fixest for econometrics, modelsummary for tables, ggplot2+wbplot for World Bank visualizations, and welfare/poverty measurement patterns. Covers domain knowledge for survey analysis, FGT poverty indices, inequality measures, and econometric workflows."
---

# R Analytical Practices

Reference skill for analytical R work in the GPID team. Oriented toward senior economists working on survey data, poverty measurement, and econometrics.

For data manipulation and statistical computing, consult the dialect skills loaded via `r.instructions.md` based on your project's `r-syntax` setting in `compound-gpid.local.md`.

## Quick Reference

| Task | Package | Key Pattern |
|------|---------|-------------|
| Read .dta files | `haven` | `read_dta()`, `as_factor()`, `zap_labels()` |
| Econometrics | `fixest` | `feols()`, `feglm()`, `sunab()` for staggered DiD |
| Output tables | `modelsummary` | `msummary()` to Word/LaTeX/HTML |
| Visualization | `ggplot2` + `wbplot` | see `cg-skill-r-visualization` |
| Research docs | Quarto | Parametrized reports, cross-references, multi-format |
| Welfare measures | FGT indices, Gini, PPP unit tracking — see Welfare Patterns workflow |

## Workflows

- [Stata Migration](workflows/stata-migration.md) — haven, label handling, common traps
- [Survey Analysis](workflows/survey-analysis.md) — weighted stats, explicit SE computation
- [Econometrics](workflows/econometrics.md) — fixest, modelsummary, output tables
- [Welfare Patterns](workflows/welfare-patterns.md) — FGT, PPP, inequality (GPID-specific)

## References

- [Anti-Patterns](references/r-analytical-anti-patterns.md) — Common mistakes in analytical R code
- [Quarto for Research](references/quarto-research.md) — Parametrized reports, cross-references

---

> For data manipulation and statistical computing patterns, load `cg-skill-r-collapse`, `cg-skill-r-datatable`, or `cg-skill-r-tidyverse` based on your project's `r-syntax` setting.
> For visualization (`theme_wb()`, `WBCOLORS`), load `cg-skill-r-visualization`.
> For infrastructure workflows (package development, Shiny, targets, httr2), use `cg-skill-r-technical`.
> For comprehensive testthat patterns, load `cg-skill-r-testing`.
