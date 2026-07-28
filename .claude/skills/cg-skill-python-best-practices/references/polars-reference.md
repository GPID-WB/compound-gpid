# polars Quick Reference

## Core Operations

| Operation | Code |
|-----------|------|
| Read CSV | `pl.read_csv("file.csv")` |
| Read Parquet | `pl.read_parquet("file.parquet")` |
| Lazy read | `pl.scan_csv("file.csv")` |
| Write CSV | `df.write_csv("file.csv")` |
| Write Parquet | `df.write_parquet("file.parquet")` |
| Select columns | `df.select("a", "b")` |
| Filter rows | `df.filter(pl.col("x") > 5)` |
| Add column | `df.with_columns(pl.col("x").alias("y"))` |
| Drop column | `df.drop("col")` |
| Rename | `df.rename({"old": "new"})` |
| Sort | `df.sort("col", descending=True)` |
| Group + agg | `df.group_by("g").agg(pl.col("x").mean())` |
| Unique rows | `df.unique(subset=["key"])` |
| Sample rows | `df.sample(n=100)` or `df.sample(fraction=0.1)` |
| Head / tail | `df.head(10)` / `df.tail(10)` |
| Explode lists | `df.explode("list_col")` |
| Unnest struct | `df.unnest("struct_col")` |
| Row count | `df.height` or `len(df)` |
| Column count | `df.width` |
| Dimensions | `df.shape` |
| Schema | `df.schema` |
| Print plan | `lf.explain()` |
| Collect lazy | `lf.collect()` |
| Sink to file | `lf.sink_parquet("out.parquet")` |

## Expressions

| Expression | Code |
|-----------|------|
| Column reference | `pl.col("name")` |
| Literal value | `pl.lit(42)` |
| Multiple columns | `pl.col("a", "b", "c")` |
| Regex columns | `pl.col("^income_.*$")` |
| All columns | `pl.all()` |
| Exclude | `pl.exclude("temp")` |
| By dtype | `pl.col(pl.Float64)` |

## Aggregations

| Function | Code |
|----------|------|
| Mean | `pl.col("x").mean()` |
| Sum | `pl.col("x").sum()` |
| Min / Max | `pl.col("x").min()` / `.max()` |
| Std Dev | `pl.col("x").std()` |
| Count rows | `pl.len()` |
| Count non-null | `pl.col("x").count()` |
| First / Last | `pl.col("x").first()` / `.last()` |
| Quantile | `pl.col("x").quantile(0.5)` |
| N unique | `pl.col("x").n_unique()` |
| Median | `pl.col("x").median()` |

## Conditional Logic

```python
pl.when(condition).then(value).otherwise(default)
```

## Joins

| Type | Code |
|------|------|
| Left | `a.join(b, on="k", how="left")` |
| Inner | `a.join(b, on="k", how="inner")` |
| Outer | `a.join(b, on="k", how="full")` |
| Anti | `a.join(b, on="k", how="anti")` |
| Semi | `a.join(b, on="k", how="semi")` |
| Cross | `a.join(b, how="cross")` |
| Validated | `a.join(b, on="k", how="left", validate="m:1")` |

## Null Handling

| Operation | Code |
|-----------|------|
| Fill null | `pl.col("x").fill_null(0)` |
| Forward fill | `pl.col("x").fill_null(strategy="forward")` |
| Drop nulls | `df.drop_nulls(subset=["x"])` |
| Is null | `pl.col("x").is_null()` |
| Is not null | `pl.col("x").is_not_null()` |
| Null count | `pl.col("x").null_count()` |
| All null counts | `df.select(pl.all().null_count())` |

## Type Casting

```python
pl.col("x").cast(pl.Float64)
pl.col("date_str").str.to_date("%Y-%m-%d")
pl.col("x").cast(pl.String)
pl.col("x").cast(pl.Int32)
```

## String Operations

```python
pl.col("name").str.to_lowercase()
pl.col("name").str.contains("pattern")
pl.col("name").str.replace("old", "new")
pl.col("name").str.split(",")
pl.col("name").str.strip_chars()
pl.col("name").str.len_chars()
```

## Window Functions

```python
pl.col("x").mean().over("group")       # group mean broadcast to each row
pl.col("x").rank().over("group")       # rank within group
pl.col("x").shift(1).over("id")        # lag within id
pl.col("x").cum_sum().over("group")    # cumulative sum within group
```

## Testing polars Output

```python
from polars.testing import assert_frame_equal

assert_frame_equal(result, expected)
assert_frame_equal(result, expected, check_row_order=False)  # order-agnostic
```

---

## NumPy Interoperability

Use at boundaries with libraries that require numpy (statsmodels, sklearn, etc.).
Keep conversions localized; stay in polars for everything else.

```python
import numpy as np
import polars as pl
import numpy.typing as npt

# polars Series → numpy array
series = pl.Series("x", [1.0, 2.0, 3.0])
arr: npt.NDArray[np.float64] = series.to_numpy()

# numpy array → polars Series
arr = np.array([1.0, 2.0, 3.0])
series = pl.Series("x", arr)

# polars DataFrame column → numpy (for linalg, sklearn, etc.)
X: npt.NDArray[np.float64] = df.select(["income", "age", "weight"]).to_numpy()

# numpy array → polars DataFrame
df = pl.from_numpy(X, schema=["income", "age", "weight"])
```
