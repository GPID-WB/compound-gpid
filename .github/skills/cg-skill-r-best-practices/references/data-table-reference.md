# data.table Quick Reference

## Syntax: `DT[i, j, by]`

| Component | Purpose | Example |
|-----------|---------|---------|
| `i` | Row filter | `dt[age > 30]` |
| `j` | Column select/compute | `dt[, .(mean_val = mean(x))]` |
| `by` | Group by | `dt[, .N, by = region]` |

## Special Symbols

| Symbol | Meaning | Example |
|--------|---------|---------|
| `.N` | Number of rows (in group) | `dt[, .N, by = group]` |
| `.SD` | Subset of Data (all columns) | `dt[, lapply(.SD, mean)]` |
| `.SDcols` | Columns for .SD | `dt[, lapply(.SD, mean), .SDcols = cols]` |
| `.GRP` | Group number | `dt[, grp_id := .GRP, by = group]` |
| `.BY` | Current group value | `dt[, f(.BY), by = group]` |
| `.I` | Row indices | `dt[, .I[1], by = group]` |
| `:=` | Assign by reference | `dt[, new := x * 2]` |

## Common Operations

| Operation | Code |
|-----------|------|
| Add column | `dt[, new_col := expr]` |
| Remove column | `dt[, col := NULL]` |
| Rename column | `setnames(dt, "old", "new")` |
| Reorder columns | `setcolorder(dt, c("a", "b", "c"))` |
| Sort | `setorder(dt, col1, -col2)` |
| Unique rows | `unique(dt, by = "key")` |
| Duplicated rows | `duplicated(dt, by = "key")` |
| Count by group | `dt[, .N, by = group]` |
| First/last per group | `dt[, .SD[1], by = group]` |

## Joins

| Join Type | Code |
|-----------|------|
| Left join | `Y[X, on = "key"]` |
| Inner join | `X[Y, on = "key", nomatch = 0]` |
| Anti join | `X[!Y, on = "key"]` |
| Semi join | `X[unique(Y[, .(key)]), on = "key", nomatch = 0]` |
| Cross join | `CJ(a = 1:3, b = c("x", "y"))` |
| Rolling join | `X[Y, on = "date", roll = TRUE]` |

## I/O

| Operation | Code |
|-----------|------|
| Read CSV | `fread("file.csv")` |
| Read selected cols | `fread("file.csv", select = c("a", "b"))` |
| Write CSV | `fwrite(dt, "file.csv")` |

## Performance Tips

1. Use `setkey()` for repeated binary-search lookups
2. Use `setindex()` for secondary indices
3. Use `:=` instead of `<-` for column operations (avoids copy)
4. Use `.SDcols` to limit columns processed by `.SD`
5. Use `fifelse()` / `fcase()` instead of `ifelse()`
6. Use `set()` in loops instead of `:=`
7. Use `fread(select = ...)` to read only needed columns
