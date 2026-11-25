# tidyverse Anti-Patterns

Common mistakes in tidyverse R code for GPID projects.

---

### Using group_by() without ungroup()

**Problem:** A forgotten `ungroup()` means downstream operations still run by group, producing unexpected results — often with no error.

**Wrong:**
```r
dt |>
  group_by(region) |>
  mutate(centered = welfare - mean(welfare))
# Result is still grouped — next summarize/mutate operates within groups
```

**Right (use `.by` to avoid the issue entirely):**
```r
dt |> mutate(centered = welfare - mean(welfare), .by = region)
```

**Right (if group_by is needed):**
```r
dt |>
  group_by(region) |>
  mutate(centered = welfare - mean(welfare)) |>
  ungroup()  # Always ungroup when done
```

---

### Using base R `weighted.mean()` for grouped weighted statistics

**Problem:** There is no direct tidyverse grouped weighted mean — `summarize(m = weighted.mean(x, w))` works but is slow and requires a `group_by()` dance. Use `collapse::fmean()` instead — it works on tibbles and is much faster.

**Wrong (slow for large data):**
```r
dt |>
  group_by(region) |>
  summarize(mean_welfare = weighted.mean(welfare, weight)) |>
  ungroup()
```

**Right:**
```r
dt |>
  summarize(mean_welfare = fmean(welfare, w = weight), .by = region)
```

---

### Using the magrittr pipe `%>%` instead of native `|>`

**Problem:** `%>%` requires the `magrittr` package. `|>` is built into R 4.1+ and is faster (no function call).

**Wrong:**
```r
dt %>% filter(x > 0) %>% mutate(y = log(x))
```

**Right:**
```r
dt |> filter(x > 0) |> mutate(y = log(x))
```

---

### Using `.` as placeholder in native pipe

**Problem:** The native pipe `|>` does not support `.` as a placeholder (unlike `%>%`).

**Wrong:**
```r
dt |> lm(welfare ~ income, data = .)  # Error: . is not defined
```

**Right (use a lambda):**
```r
dt |> (\(x) lm(welfare ~ income, data = x))()

# Or just be explicit:
lm(welfare ~ income, data = dt)
```

---

### Using deprecated `recode()` instead of `case_match()` / `recode_values()`

**Problem:** `dplyr::recode()` is deprecated. Use `case_match()` for value recoding.

**Wrong:**
```r
mutate(dt, region_abbr = recode(region,
  "East Asia & Pacific"  = "EAP",
  "South Asia"           = "SAR"
))
```

**Right:**
```r
mutate(dt, region_abbr = case_match(region,
  "East Asia & Pacific" ~ "EAP",
  "South Asia"          ~ "SAR",
  .default = region
))
```

---

### Unsafe vectorized `ifelse()` — use `if_else()`

**Problem:** `base::ifelse()` coerces types (drops Date, converts integer to double) and can return unexpected types.

**Wrong:**
```r
mutate(dt, category = ifelse(income > 50000, "high", "low"))
mutate(dt, date_clipped = ifelse(date > cutoff, cutoff, date))  # Drops Date class
```

**Right:**
```r
mutate(dt, category    = if_else(income > 50000, "high", "low"))
mutate(dt, date_clipped = if_else(date > cutoff, cutoff, date))  # Preserves Date
```

---

### Missing `.default` in `case_when()`

**Problem:** `case_when()` returns `NA` for unmatched rows unless `.default` is specified. This can silently introduce NAs.

**Wrong:**
```r
mutate(dt, label = case_when(
  income > 100000 ~ "high",
  income >  50000 ~ "medium"
  # Unmatched rows become NA silently
))
```

**Right:**
```r
mutate(dt, label = case_when(
  income > 100000 ~ "high",
  income >  50000 ~ "medium",
  .default         = "low"
))
```

---

### Using `select(-col)` to delete a column when `mutate(col = NULL)` is needed in a pipe

**Problem:** Using `select()` to remove a column that was just added in the same pipe is verbose.

**Wrong:**
```r
dt |>
  mutate(temp_col = log(welfare)) |>
  mutate(final_col = temp_col * 2) |>
  select(-temp_col)  # Extra step
```

**Right:**
```r
dt |>
  mutate(
    temp_col  = log(welfare),
    final_col = temp_col * 2,
    temp_col  = NULL   # Deletes temp_col at the end of mutate
  )
```
