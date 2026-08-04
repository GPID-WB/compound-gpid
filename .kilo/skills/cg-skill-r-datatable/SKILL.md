---
name: cg-skill-r-datatable
description: "data.table patterns for R data manipulation. Load when r-syntax is 'data.table-collapse' in compound-gpid.local.md, or when writing/reviewing R code using DT[i,j,by] syntax, :=, fread/fwrite, joins, reshaping, or any data.table manipulation. Covers filtering, column creation by reference, joins (equi, non-equi, rolling), melt/dcast reshaping, fifelse/fcase, .SD/.SDcols, set()/setkey(), performance patterns, and data.table anti-patterns. Use alongside cg-skill-r-collapse for statistical computing."
user-invocable: false
---

# data.table Data Manipulation

`data.table` is the team's primary tool for data manipulation when using the `data.table-collapse` dialect. All operations flow through one unified `DT[i, j, by]` syntax. Use `collapse` functions (from `cg-skill-r-collapse`) for all grouped/weighted statistical computing inside or alongside data.table.

## Core Paradigm

```r
DT[i, j, by]
#   |  |  |
#   |  |  └── GROUP BY what?
#   |  └───── SELECT/compute what?
#   └──────── WHERE (filter rows) / JOIN (when i is a data.table)
```

**Key rules:**
- `:=` and `set*()` functions modify in-place — **never assign back** (`DT[, x := 1]`, not `DT <- DT[, x := 1]`)
- `.()` is alias for `list()` inside `DT[...]`
- `.N` = row count, `.SD` = subset of data, `.I` = row indices, `.GRP` = group number, `.BY` = group values
- Chain with `[][]` rather than pipes when natural

## Quick Reference

| Task | Pattern |
|------|---------|
| Filter rows | `dt[cond]` or `fsubset(dt, cond)` |
| Add/modify column | `dt[, new := expr]` |
| Multiple columns | `dt[, ':='(a = x, b = y)]` or `dt[, let(a = x, b = y)]` |
| Delete column | `dt[, col := NULL]` |
| Aggregate | `dt[, .(mean = fmean(x, w = w)), by = grp]` |
| Rename | `setnames(dt, "old", "new")` |
| Read CSV | `fread("file.csv")` |
| Write CSV | `fwrite(dt, "file.csv")` |
| Left join | `Y[X, on = "key"]` |
| Inner join | `X[Y, on = "key", nomatch = NULL]` |
| Anti join | `X[!Y, on = "key"]` |
| Wide to long | `melt(dt, id.vars = ..., measure.vars = ...)` |
| Long to wide | `dcast(dt, formula, value.var = ...)` |
| Fast if-else | `fifelse(test, yes, no)` |
| Fast case when | `fcase(cond1, val1, cond2, val2, default = val)` |

## References

- [data.table Reference](references/datatable-reference.md) — Complete API: I/O, joins, reshaping, `.SD`, keys, rolling, NA functions, performance patterns, common errors, full function lookup table
- [data.table Anti-Patterns](references/datatable-anti-patterns.md) — Common mistakes: assigning back after `:=`, `ifelse()` vs `fifelse()`, character column lookups, copy semantics

---

> For grouped/weighted statistics, use `cg-skill-r-collapse` — collapse functions work directly inside `dt[, j, by]`.
> For dplyr/tidyverse manipulation, use `cg-skill-r-tidyverse`.
> For analytical domain knowledge (welfare, econometrics), use `cg-skill-r-analytical`.
