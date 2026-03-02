# Common R Anti-Patterns

## data.table Anti-Patterns

| Anti-Pattern | Problem | Fix |
|-------------|---------|-----|
| `ifelse()` on data.table | Slow, coerces types | Use `fifelse()` or `fcase()` |
| `for` loop over rows | Extremely slow | Use vectorized `:=` or `set()` |
| `dt$col <- value` | Creates copy, breaks reference semantics | Use `dt[, col := value]` |
| `apply(dt, 1, fun)` | Converts to matrix, slow | Use `dt[, fun(.SD), by = .I]` or vectorize |
| Repeated `dt[condition]` | Multiple passes over data | Combine in one `dt[condition, j, by]` |
| Not using keys for joins | Hash join instead of binary search | `setkey()` on join columns |
| `copy()` everywhere | Wastes memory | Only copy when truly needed |

## General R Anti-Patterns

| Anti-Pattern | Problem | Fix |
|-------------|---------|-----|
| `T` / `F` | Can be overwritten | Always use `TRUE` / `FALSE` |
| `1:length(x)` | Fails when `length(x) == 0` | Use `seq_along(x)` |
| `sapply()` | Unpredictable return type | Use `vapply()` or `lapply()` |
| Nested `if/else` | Hard to read | Use `fcase()` or early returns |
| `library()` in functions | Side effect, pollutes namespace | Use `::` or `@importFrom` |
| Growing vectors in loop | O(n²) reallocation | Pre-allocate or use `lapply()` |
| `setwd()` | Non-reproducible, affects global state | Use `here::here()` or relative paths |
| `rm(list = ls())` | Nuclear option, not reproducible | Use clean R sessions instead |
| `options(stringsAsFactors)` | Global side effect | Handle per-call or use data.table |
| Suppressing warnings blanketly | Hides real problems | Address root cause |
