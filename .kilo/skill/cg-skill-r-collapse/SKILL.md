---
name: cg-skill-r-collapse
description: "collapse fast statistical computing for R. Load when writing or reviewing grouped/weighted statistics, aggregation, or panel data operations with the collapse package. Covers fmean/fsum/fmedian/fnth and all Fast Statistical Functions, GRP objects, TRA transformation types, fwithin/fbetween/fscale, flag/fdiff/fgrowth, collap(), fsummarise/fmutate, qsu/descr, and collapse anti-patterns. Dialect-neutral: collapse works on data.table, tibble, and data.frame equally."
user-invocable: false
---

# collapse Statistical Computing

`collapse` is the team's primary tool for statistical computing. It provides fast C/C++-based grouped and weighted operations that are class-agnostic — functions work identically on `data.table`, `tibble`, and `data.frame`. Always use explicit `f`-prefixed names — never use `set_collapse(mask = ...)`.

## Quick Reference

| Task | Function | Pattern |
|------|----------|---------|
| Weighted mean (grouped) | `fmean` | `fmean(x, g = group, w = weight)` |
| Weighted sum | `fsum` | `fsum(x, g = group, w = weight)` |
| Weighted median | `fmedian` | `fmedian(x, g = group, w = weight)` |
| Weighted nth quantile | `fnth` | `fnth(x, 0.25, g = group, w = weight)` |
| Grouped variance/SD | `fvar`/`fsd` | `fsd(x, g = group, w = weight)` |
| Multi-function aggregation | `collap` | `collap(dt, ~ group, fmean, w = ~ weight)` |
| Demean (within-transform) | `fwithin` | `fwithin(x, g = group, w = weight)` |
| Group mean broadcast | `fbetween` | `fbetween(x, g = group)` |
| Standardize | `fscale` | `fscale(x, g = group, w = weight)` |
| Lag/lead | `flag` | `flag(x, n = 1, g = id, t = time)` |
| First difference | `fdiff` | `fdiff(x, g = id, t = time)` |
| Growth rate | `fgrowth` | `fgrowth(x, g = id, t = time)` |
| Summary stats | `qsu` | `qsu(dt, ~ group, w = ~ weight)` |
| Pre-compute groups | `GRP` | `g <- GRP(dt, ~ region + year)` |
| Grouped transform/summarise | `fmutate`/`fsummarise` | `dt \|> fgroup_by(region) \|> fmutate(...)` |

## When to Use This Skill

Load alongside `cg-skill-r-datatable` (for `data.table-collapse` dialect) or `cg-skill-r-tidyverse` (for tidyverse dialect — collapse is still recommended for weighted statistical computing even in tidyverse projects).

## References

- [collapse Reference](references/collapse-reference.md) — Core daily-use API: Fast Statistical Functions, TRA types, GRP structure, `collap()`, `fwithin`/`fbetween`/`fscale`, panel operations (`flag`/`fdiff`/`fgrowth`), pipe-friendly patterns, global options
- [collapse Advanced Reference](references/collapse-advanced.md) — Load for lookup of: data manipulation verbs (`fselect`, `fsubset`, `ftransform`), summary stats (`qsu`, `descr`, `qtab`), joins (`join()`), pivoting (`pivot()`), quick conversion (`qDT`/`qTBL`), S3 dispatch table, short aliases, common errors
- [collapse Anti-Patterns](references/collapse-anti-patterns.md) — Common mistakes: masking, forgotten `qDT()`, repeated grouping recomputation

---

> For data manipulation (filtering, joining, reshaping with data.table), use `cg-skill-r-datatable`.
> For dplyr/tidyverse manipulation patterns, use `cg-skill-r-tidyverse`.
> For analytical domain knowledge (welfare measurement, survey analysis, econometrics), use `cg-skill-r-analytical`.
