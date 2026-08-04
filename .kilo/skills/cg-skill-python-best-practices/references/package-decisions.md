# Package Decisions

When to reach for which tool. These are team conventions, not universal truths.
When in doubt, default to the simpler option and upgrade when you hit its limits.

---

## Data Manipulation: `polars` vs `numpy` vs `pandas`

| Situation | Use |
|-----------|-----|
| Any tabular data (rows × columns) | `polars` |
| Linear algebra, matrix operations | `numpy` |
| Array math on non-tabular data | `numpy` |
| Library forces it (`statsmodels`, `sklearn`) | `pandas` (convert at boundary only) |
| Legacy code that uses `pandas` | `pandas` (don't mix in new functions) |
| Streaming / larger-than-RAM datasets | `polars` lazy + `sink_parquet` |

**Never use `pandas` for new code.** If a library requires `pandas`, convert at
the function boundary: `polars_df.to_pandas()` going in, `pl.from_pandas(pd_df)`
coming out. Keep the conversion localized so it can be removed if the library
adds polars support.

**When `numpy` instead of polars:**
- You need `linalg` operations (eigenvalues, matrix decomposition, dot products)
- You're working with multi-dimensional arrays (3D+), not tables
- You're doing signal processing, FFT, or convolution
- The computation is purely mathematical with no row/column semantics

```python
# numpy is right here — this is linear algebra, not tabular data
import numpy as np

weights = np.array([0.3, 0.5, 0.2])
values  = np.array([100, 200, 150])
weighted_sum = weights @ values   # dot product

# polars is right here — this is tabular aggregation
import polars as pl
df.group_by("region").agg(
    (pl.col("welfare") * pl.col("weight")).sum() / pl.col("weight").sum()
)
```

---

## Visualization: `plotnine` vs `seaborn` vs `matplotlib`

| Situation | Use |
|-----------|-----|
| Publication-quality charts for reports/papers | `plotnine` |
| ggplot2 conventions (team familiarity) | `plotnine` |
| Quick EDA, statistical plots in notebooks | `seaborn` |
| Full layout control, custom figure assembly | `matplotlib` |
| Interactive charts (notebooks) | `plotly` (if needed — not default) |

**`plotnine` is the default** because the team knows ggplot2 from R. The
grammar is identical: `ggplot() + geom_*() + scale_*() + theme()`.

**Use `seaborn` when:** you want a quick distribution plot, regression plot, or
pair plot during EDA and don't need publication formatting. `seaborn` is faster
to write for exploratory work.

**Use `matplotlib` directly when:** you need subplots with complex layouts,
custom tick formatters, or insets that plotnine/seaborn can't produce cleanly.

```python
# plotnine — publication quality, ggplot2-identical grammar
from plotnine import ggplot, aes, geom_line, geom_ribbon, scale_x_continuous, labs, theme_minimal

chart = (
    ggplot(df, aes(x="year", y="poverty_rate", color="region"))
    + geom_line(size=1)
    + geom_ribbon(aes(ymin="lower", ymax="upper", fill="region"), alpha=0.2)
    + scale_x_continuous(breaks=range(2010, 2024, 2))
    + labs(title="Poverty trends by region", y="Headcount ratio", x=None)
    + theme_minimal()
)
chart.save("output/poverty_trends.pdf", width=8, height=5, dpi=300)

# seaborn — quick EDA
import seaborn as sns
sns.histplot(df.to_pandas(), x="welfare", hue="region", bins=50)
```

---

## APIs: `FastAPI` vs `Flask` vs nothing

| Situation | Use |
|-----------|-----|
| New REST API | `FastAPI` |
| Async I/O, high concurrency | `FastAPI` |
| Auto OpenAPI docs needed | `FastAPI` |
| Legacy Flask codebase | `Flask` (don't mix) |
| Script called by another script | No HTTP — direct function call |
| Internal CLI tool | No HTTP — use `argparse` or `typer` |

Always `FastAPI` for new APIs. The automatic OpenAPI spec generation, pydantic
integration, and native async support make it the clear choice.

---

## Data Validation: `pydantic` vs manual validation

| Situation | Use |
|-----------|-----|
| API request/response models | `pydantic` always |
| Config loaded from env/files | `pydantic-settings` |
| Data crossing a system boundary | `pydantic` |
| Internal function arguments | Type hints + `ValueError` in body |
| DataFrame schemas | `polars` schema + assertion |

**Rule:** validate with pydantic at boundaries (HTTP, config, files). Validate
with plain Python inside module boundaries.

```python
# pydantic for boundary validation (HTTP body, config)
from pydantic import BaseModel, Field

class SurveyConfig(BaseModel):
    country: str
    year: int = Field(ge=1990, le=2030)
    poverty_line: float = Field(gt=0, default=2.15)

# plain Python for internal validation
def aggregate_welfare(df: pl.DataFrame, weight_col: str) -> pl.DataFrame:
    if weight_col not in df.columns:
        raise ValueError(f"Column '{weight_col}' not found")
    # ...
```

---

## Logging: `loguru` vs stdlib `logging` vs `print()`

**Always `loguru`.** Never `print()` in production code. Never configure stdlib
`logging` directly (loguru intercepts it automatically).

```python
# WRONG — can't filter, can't redirect, can't add context
print(f"Processing {country} for year {year}")

# WRONG — verbose configuration, less ergonomic
import logging
logging.getLogger(__name__).info("Processing %s for year %d", country, year)

# RIGHT — loguru: zero config, structured, contextual
from loguru import logger
logger.info("Processing survey", country=country, year=year)
```

---

## Environment Management: `uv` vs `poetry` vs `pip`

**Default: `uv`** — it is significantly faster than poetry and pip, and the
lockfile and API are compatible with the team's workflow.

**Use `poetry` only if:** a project already uses it and migration isn't worth
the cost. New projects always use `uv`.

**Never use bare `pip` without a lockfile** for project work. `pip install`
without pinned versions creates non-reproducible environments.

```bash
# uv — preferred
uv add polars            # add dependency + update uv.lock
uv sync                  # install from uv.lock (reproducible)
uv run pytest            # run in project venv

# poetry — only for existing poetry projects
poetry add polars
poetry install
poetry run pytest
```

---

## HTTP Clients: `httpx` vs `requests`

| Situation | Use |
|-----------|-----|
| Inside a FastAPI async endpoint | `httpx` async (`AsyncClient`) |
| Script or sync context | `httpx` sync (`Client`) — same API |
| Legacy code | `requests` (don't introduce in new code) |

`httpx` has an identical API to `requests` but supports async natively. Use it
everywhere so async and sync contexts use the same library.

```python
# sync context
import httpx

with httpx.Client() as client:
    response = client.get("https://api.example.org/data")
    data = response.json()

# async context (inside FastAPI endpoint)
async with httpx.AsyncClient() as client:
    response = await client.get("https://api.example.org/data")
    data = response.json()
```
