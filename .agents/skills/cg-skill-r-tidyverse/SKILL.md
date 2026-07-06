---
name: cg-skill-r-tidyverse
description: "Modern tidyverse patterns for R. Load when r-syntax is 'tidyverse' in compound-gpid.local.md, or when writing/reviewing R code using dplyr, tidyr, readr, stringr, or purrr. Covers dplyr 1.2+ patterns (.by grouping, join_by, pick/across/reframe), native pipe |>, pivot_longer/pivot_wider, stringr, readr I/O, and GPID-specific patterns in tidyverse style. Note: even in tidyverse mode, collapse functions (fmean, fsum, etc.) are used for weighted statistics since they work natively on tibbles."
user-invocable: false
---

# tidyverse Data Manipulation

For projects with external coauthors or where tidyverse readability is required. Uses dplyr for manipulation, tidyr for reshaping, readr for I/O. Always use the **native pipe** `|>` (not magrittr `%>%`).

**Important**: Even in tidyverse mode, use `collapse` functions (`fmean`, `fsum`, `fmedian`, etc.) for weighted grouped statistics — they work directly on tibbles and there is no native tidyverse equivalent for weighted grouped stats.

## Quick Reference

| Task | Package | Pattern |
|------|---------|---------|
| Filter rows | `dplyr` | `filter(dt, income > 0)` |
| Add/modify column | `dplyr` | `mutate(dt, log_inc = log(income))` |
| Select columns | `dplyr` | `select(dt, id, income, region)` |
| Rename column | `dplyr` | `rename(dt, welfare = welf)` |
| Sort rows | `dplyr` | `arrange(dt, desc(income))` |
| Group + summarize | `dplyr` | `summarize(dt, mean = fmean(x, w = w), .by = group)` |
| Group + mutate | `dplyr` | `mutate(dt, centered = fwithin(x), .by = group)` |
| Left join | `dplyr` | `left_join(x, y, by = join_by(id))` |
| Wide to long | `tidyr` | `pivot_longer(dt, cols = starts_with("y"))` |
| Long to wide | `tidyr` | `pivot_wider(dt, names_from = year, values_from = value)` |
| Read CSV | `readr` | `read_csv("file.csv")` |
| Write CSV | `readr` | `write_csv(dt, "file.csv")` |
| Read Stata | `haven` | `read_dta("file.dta")` |
| Weighted mean (grouped) | `collapse` | `fmean(x, g = group, w = weight)` |
| Fast if-else | `dplyr` | `if_else(cond, true, false)` |
| Case when | `dplyr` | `case_when(cond1 ~ val1, .default = val)` |

## References

- [tidyverse Reference](references/tidyverse-reference.md) — Core patterns: dplyr 1.2+ (.by, join_by, across/pick/reframe), tidyr, readr, stringr, purrr, GPID-specific workflows
- [tidyverse Style](references/tidyverse-style.md) — Naming, spacing, pipe style, error messages, function conventions
- [tidyverse Anti-Patterns](references/tidyverse-anti-patterns.md) — Common mistakes: old-style grouping, deprecated functions, magrittr pipe, type-unsafe operations
- [tidyverse Migration](references/tidyverse-migration.md) — Load only when translating existing data.table or base R code to tidyverse equivalents. Side-by-side: data.table/collapse → tidyverse equivalents

---

> For weighted grouped statistics (fmean, fsum, fmedian), load `cg-skill-r-collapse` — these work on tibbles and are the recommended approach even in tidyverse projects.
> For analytical domain knowledge (welfare, econometrics), load `cg-skill-r-analytical`.
