---
name: cg-skill-r-analytical
description: "R patterns for analytical work: haven for Stata migration, srvyr/survey for complex surveys, fixest for econometrics, modelsummary for tables, ggplot2+wbplot for World Bank visualizations, and welfare/poverty measurement patterns. ALWAYS load this skill when writing R code involving survey weights, Stata data migration, welfare measurement, econometrics (fixest), or WB visualization (wbplot)."
---

# R Analytical Practices

Reference skill for analytical R work in the GPID team. Oriented toward senior economists migrating from Stata to R. Covers survey analysis, econometrics, publication-quality output, World Bank visualization standards, and welfare measurement — the patterns GPID uses daily to produce official poverty and inequality statistics.

> **Choosing between R skills**: Use this skill for analytical/statistical work. Use `cg-skill-r-technical` for package/infrastructure work (data.table core mechanics, package development, APIs, pipelines). Some plans require both.

## Quick Reference

| Task | Package | Key Pattern |
|------|---------|-------------|
| Read .dta files | `haven` | `read_dta()`, `as_factor()`, `zap_labels()` |
| Survey analysis | `srvyr` / `survey` | `as_survey_design()` declared ONCE, used everywhere |
| Econometrics | `fixest` | `feols()`, `feglm()`, `sunab()` for staggered DiD |
| Output tables | `modelsummary` | `msummary()` to Word/LaTeX/HTML |
| Visualization | `ggplot2` + `wbplot` | `theme_wb()`, `WBCOLORS`, `scale_color_wb_d()`; for core ggplot2 mechanics, see `cg-skill-r-technical` |
| Research docs | Quarto | Parametrized reports, cross-references, multi-format |
| Welfare measures | Custom + `srvyr` | FGT indices, Gini, PPP unit tracking |

## Workflows

- [Stata Migration](workflows/stata-migration.md) — haven, label handling, common traps
- [Survey Analysis](workflows/survey-analysis.md) — srvyr/survey, design propagation
- [Econometrics](workflows/econometrics.md) — fixest, modelsummary, output tables
- [Visualization](workflows/visualization.md) — ggplot2 + wbplot conventions
- [Welfare Patterns](workflows/welfare-patterns.md) — FGT, PPP, inequality (GPID-specific)

## References

- [Anti-Patterns](references/r-analytical-anti-patterns.md) — Common mistakes in analytical R code
- [Quarto for Research](references/quarto-research.md) — Parametrized reports, cross-references
