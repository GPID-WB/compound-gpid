# Logging and Error Handling

Never use `print()` for diagnostic output in production code. Never use bare
`except:`. This file covers the correct patterns for structured logging,
custom exceptions, and performance profiling.

---

## 1. Logging with `loguru`

`loguru` replaces the stdlib `logging` module. One import, no configuration
boilerplate, structured output out of the box.

### Setup — once per application

```python
# src/your_package/logging.py  (or in main.py / app factory)
import sys
from loguru import logger


def configure_logging(level: str = "INFO") -> None:
    """Configure loguru for the application. Call once at startup."""
    logger.remove()   # remove default stderr handler

    # Human-readable format for development
    logger.add(
        sys.stderr,
        level=level,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{line}</cyan> | "
            "{message}"
        ),
        colorize=True,
    )

    # JSON format for production / log aggregation (add alongside stderr or replace)
    # logger.add(
    #     "logs/app.log",
    #     level="INFO",
    #     format="{time} {level} {message}",
    #     serialize=True,     # outputs JSON
    #     rotation="100 MB",
    #     retention="30 days",
    # )
```

```python
# In FastAPI: call in lifespan
from gpid_api.logging import configure_logging
from gpid_api.config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging(level=settings.log_level)
    yield
```

### Usage throughout the codebase

```python
from loguru import logger

# Basic levels
logger.debug("Reading parquet file", path=str(path))
logger.info("Poverty estimate computed", country="ETH", year=2022, rate=0.42)
logger.warning("Sample size below threshold", n=47, minimum=100)
logger.error("PPP factor missing", country="ZZZ", year=2022)

# Structured key=value pairs — always prefer over f-strings in log messages
# WRONG — hard to parse, hard to query in log aggregation
logger.info(f"Processing country={country}, year={year}, n={n_obs}")

# RIGHT — key=value pairs are structured and queryable
logger.info("Processing survey", country=country, year=year, n_obs=n_obs)

# Context binding — attach fields for the duration of a function/request
def process_survey(country: str, year: int) -> pl.DataFrame:
    log = logger.bind(country=country, year=year)
    log.info("Survey processing started")
    # ... work ...
    log.info("Survey processing complete", rows=result.height)
    return result

# Exception logging — captures full traceback automatically
try:
    result = risky_operation()
except Exception as e:
    logger.exception("Risky operation failed", context="some_value")
    # logger.exception captures the traceback; don't use logger.error for exceptions
    raise
```

### Suppressing loguru in tests

```python
# conftest.py
import pytest
from loguru import logger

@pytest.fixture(autouse=True)
def suppress_logging():
    """Suppress loguru output during tests."""
    logger.remove()
    yield
```

---

## 2. Custom Exceptions

Define a typed exception hierarchy. This lets callers catch specific errors
and lets FastAPI exception handlers map them to HTTP status codes cleanly.

```python
# src/your_package/exceptions.py


class AppError(Exception):
    """Base class for all application errors. Never raise directly."""


# --- Data errors ---

class DataNotFoundError(AppError):
    """Requested data does not exist in the reference database."""

    def __init__(self, entity: str, identifier: str) -> None:
        self.entity = entity
        self.identifier = identifier
        super().__init__(f"{entity} not found: {identifier!r}")


class DataQualityError(AppError):
    """Data fails a quality check required for computation."""

    def __init__(self, message: str, n_failing: int | None = None) -> None:
        self.n_failing = n_failing
        detail = f" ({n_failing} failing rows)" if n_failing else ""
        super().__init__(f"Data quality check failed: {message}{detail}")


# --- Computation errors ---

class InsufficientSampleError(AppError):
    """Sample size is too small for reliable estimates."""

    def __init__(self, n: int, minimum: int) -> None:
        self.n = n
        self.minimum = minimum
        super().__init__(f"Insufficient sample: {n} observations (minimum: {minimum})")


class ConfigurationError(AppError):
    """Application configuration is missing or invalid."""
```

```python
# Usage
from your_package.exceptions import DataNotFoundError, InsufficientSampleError

def get_welfare_data(country: str, year: int) -> pl.DataFrame:
    df = load_from_database(country, year)
    if df is None:
        raise DataNotFoundError("welfare_data", f"{country}-{year}")

    if df.height < 100:
        raise InsufficientSampleError(n=df.height, minimum=100)

    return df
```

---

## 3. Exception Handling Patterns

```python
# WRONG — bare except swallows everything including KeyboardInterrupt
try:
    result = compute()
except:
    pass

# WRONG — too broad, hides bugs
try:
    result = compute()
except Exception:
    return None

# RIGHT — catch specific exceptions, handle or re-raise with context
try:
    result = compute_poverty_index(df, poverty_line=2.15)
except InsufficientSampleError as e:
    logger.warning("Skipping estimate due to small sample", n=e.n, country=country)
    return None
except DataNotFoundError:
    raise   # let it propagate — caller decides what to do
except Exception as e:
    logger.exception("Unexpected error in poverty computation", country=country)
    raise RuntimeError(f"Poverty computation failed for {country}") from e
```

```python
# Context managers for resource cleanup
from contextlib import contextmanager

@contextmanager
def timer(label: str):
    """Log elapsed time for a block of code."""
    import time
    start = time.perf_counter()
    try:
        yield
    finally:
        elapsed = time.perf_counter() - start
        logger.debug(f"{label} completed", elapsed_ms=round(elapsed * 1000, 1))

# Usage
with timer("welfare aggregation"):
    result = aggregate_welfare(df)
```

---

## 4. Input Validation Pattern

Validate at the boundary. Once data is inside your function, trust it.

```python
import polars as pl
from loguru import logger


def compute_poverty_rate(
    df: pl.DataFrame,
    welfare_col: str,
    weight_col: str,
    poverty_line: float,
) -> float:
    """Compute headcount poverty rate.

    Args:
        df: DataFrame with welfare and weight columns.
        welfare_col: Name of the per-capita welfare column.
        weight_col: Name of the survey weight column.
        poverty_line: Poverty line in the same units as welfare.

    Returns:
        Headcount poverty rate in [0, 1].

    Raises:
        ValueError: If required columns are missing or poverty_line <= 0.
        InsufficientSampleError: If sample has fewer than 100 observations.
    """
    # Validate inputs at the top — fail fast with clear messages
    missing = [c for c in [welfare_col, weight_col] if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns: {missing}. Available: {df.columns}")

    if poverty_line <= 0:
        raise ValueError(f"poverty_line must be positive, got {poverty_line}")

    if df.height < 100:
        raise InsufficientSampleError(n=df.height, minimum=100)

    # Check weight quality — null or non-positive weights silently corrupt the rate
    null_weights = df[weight_col].null_count()
    if null_weights > 0:
        raise DataQualityError(
            f"Weight column {weight_col!r} contains {null_weights} null values",
            n_failing=null_weights,
        )
    if not (df[weight_col] > 0).all():
        n_bad = (df[weight_col] <= 0).sum()
        raise DataQualityError(
            f"Weight column {weight_col!r} has non-positive values",
            n_failing=n_bad,
        )

    # Drop null welfare rows explicitly before computing
    # null welfare ≠ zero consumption; silently excluding from numerator but not
    # denominator would understate the poverty rate
    n_null_welfare = df[welfare_col].null_count()
    if n_null_welfare > 0:
        dropped_weight_share = (
            df.filter(pl.col(welfare_col).is_null())[weight_col].sum()
            / df[weight_col].sum()
        )
        logger.warning(
            "Dropping null welfare rows before poverty computation",
            n_dropped=n_null_welfare,
            dropped_weight_share=round(dropped_weight_share, 4),
        )
        df = df.drop_nulls(subset=[welfare_col])

    # Compute
    poor = df.filter(pl.col(welfare_col) < poverty_line)
    rate = poor[weight_col].sum() / df[weight_col].sum()

    logger.debug(
        "Poverty rate computed",
        poverty_line=poverty_line,
        rate=round(rate, 4),
        n_obs=df.height,
    )
    return rate
```

---

## 5. Performance Profiling

Profile before optimizing. Always measure.

```bash
# Install profiling tools
uv add --dev memray snakeviz line_profiler

# CPU profiling — which functions take the most time?
python -m cProfile -o profile.prof src/my_script.py
snakeviz profile.prof                # opens visual browser

# Memory profiling — what's allocating memory?
python -m memray run -o memory.bin src/my_script.py
python -m memray flamegraph memory.bin    # generates HTML flamegraph
python -m memray summary memory.bin       # text summary

# Line-by-line profiling — which lines in a function are slow?
# Add @profile decorator, then run with kernprof
```

```python
# Line profiler usage
from line_profiler import profile   # requires line_profiler

@profile
def slow_function(df: pl.DataFrame) -> pl.DataFrame:
    # ... code you want to profile line by line ...
    pass

# Run: kernprof -l -v my_script.py
```

```python
# In-code timing for quick checks
import time
from loguru import logger


def timed(fn):
    """Decorator that logs function execution time."""
    import functools

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = fn(*args, **kwargs)
        elapsed = time.perf_counter() - start
        logger.debug("function completed", name=fn.__name__, elapsed_ms=round(elapsed * 1000, 1))
        return result

    return wrapper


@timed
def aggregate_welfare(df: pl.DataFrame) -> pl.DataFrame:
    return df.group_by("country", "year").agg(pl.col("welfare").mean())
```
