---
name: cg-skill-r-analytical
description: "R patterns for analytical work: collapse for fast grouped/weighted statistics and aggregation, data.table for manipulation, haven for Stata migration, fixest for econometrics, modelsummary for tables, ggplot2+wbplot for World Bank visualizations, and welfare/poverty measurement patterns. Preference hierarchy: collapse > data.table > tidyverse."
---

# R Analytical Practices

Reference skill for analytical R work in the GPID team. Oriented toward senior economists migrating from Stata to R. The team's preferred tool hierarchy is:

1. **collapse** — for all grouped, weighted, and statistical computations (fastest, most explicit)
2. **data.table** — for data manipulation, filtering, joins, reshaping, column creation
3. **tidyverse** — only as fallback when collapse and data.table cannot do the job

Both `collapse` and `data.table` are class-agnostic and interoperable: collapse functions work directly on data.table objects. No masking (`set_collapse(mask = ...)` is never used) — always use explicit `f`-prefixed function names.

## Quick Reference

| Task | Package | Key Pattern |
|------|---------|-------------|
| Grouped/weighted stats | `collapse` | `fmean(x, g, w)`, `fsum()`, `fmedian()`, `fnth()` |
| Aggregation | `collapse` | `collap(dt, ~ group, fmean, w = ~ weight)` |
| Transformations | `collapse` | `fwithin()`, `fbetween()`, `fscale()`, `TRA()` |
| Panel operations | `collapse` | `flag()`, `fdiff()`, `fgrowth()`, `findex_by()` |
| Data manipulation | `data.table` | `DT[i, j, by]` syntax, `:=` for in-place ops |
| Read .dta files | `haven` | `read_dta()`, `as_factor()`, `zap_labels()` |
| Econometrics | `fixest` | `feols()`, `feglm()`, `sunab()` for staggered DiD |
| Output tables | `modelsummary` | `msummary()` to Word/LaTeX/HTML |
| Visualization | `ggplot2` + `wbplot` | `theme_wb()`, `WBCOLORS`, `scale_color_wb_d()` |
| Research docs | Quarto | Parametrized reports, cross-references, multi-format |
| Welfare measures | `collapse` + `data.table` | FGT indices, Gini, PPP unit tracking |

## Decision Rule: When to Use What

| Operation | Use | Why |
|-----------|-----|-----|
| Weighted mean, sum, median, variance | `collapse` | Fastest, native weight support |
| Grouped statistics | `collapse` (`fmean(x, g, w)` or `collap()`) | Single C call, no split-apply-combine |
| Row filtering, conditional logic | `data.table` (`dt[cond]`, `fifelse`, `fcase`) | Flexible syntax, reference semantics |
| Joins | `data.table` (`X[Y, on=]`) or `collapse` (`join()`) | data.table for complex; collapse for simple |
| Column creation | `data.table` (`:=`) | Reference semantics, in-place |
| Reshaping | `collapse` (`pivot()`) or `data.table` (`melt`/`dcast`) | collapse for simple; data.table for complex |
| Scaling, centering | `collapse` (`fscale`, `fwithin`, `fbetween`) | Optimized C, supports groups + weights |
| Lags, differences, growth | `collapse` (`flag`, `fdiff`, `fgrowth`) | Panel-aware, irregular series |
| I/O | `data.table` (`fread`, `fwrite`) | Fastest CSV reader/writer |
| Summary statistics | `collapse` (`qsu`, `descr`, `qtab`) | Fast, weighted, panel-decomposed |
| Survey SEs (complex cases) | `srvyr` (fallback only) | When explicit collapse code is insufficient |

## Workflows

- [Stata Migration](workflows/stata-migration.md) — haven, label handling, common traps
- [Survey Analysis](workflows/survey-analysis.md) — collapse for weighted stats, explicit SE computation
- [Econometrics](workflows/econometrics.md) — fixest, modelsummary, output tables
- [Visualization](workflows/visualization.md) — ggplot2 + wbplot conventions
- [Welfare Patterns](workflows/welfare-patterns.md) — FGT, PPP, inequality (GPID-specific, collapse-first)

## References

- [collapse Quick Reference](references/collapse-reference.md) — Fast statistical functions, aggregation, transformations, global options
- [Anti-Patterns](references/r-analytical-anti-patterns.md) — Common mistakes in analytical R code
- [Quarto for Research](references/quarto-research.md) — Parametrized reports, cross-references

---

> For infrastructure workflows (package development, Shiny, targets, httr2), use `cg-skill-r-technical`.
> For testthat patterns including collapse output testing, see `cg-skill-r-technical/references/testing-testthat.md`.
