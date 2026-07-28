# Common Python Anti-Patterns

Patterns Copilot generates incorrectly. Read this before reviewing any
Copilot-generated Python output.

---

## Data Manipulation Anti-Patterns

| Anti-Pattern | Problem | Fix |
|-------------|---------|-----|
| `.apply()` / `.map_elements()` in polars | Python loop under the hood — 10-100× slower | Use native expressions: `pl.col()`, `pl.when()` |
| `.to_pandas()` for simple operations | Unnecessary round-trip, loses lazy evaluation | Stay in polars. **Exception**: visualization libraries (`seaborn`, `matplotlib`) require pandas input — `df.to_pandas()` at the visualization boundary is acceptable. |
| Iterating over DataFrame rows (`iter_rows`) | O(n) Python loop | Use vectorized expressions |
| Growing list then `pl.from_records()` | O(n²) reallocation | Use `pl.concat()` with a list of frames |
| Collecting inside a loop | Executes plan on every iteration | Build lazy plan first, collect once |
| Chaining multiple `.with_columns()` calls | Multiple passes over data | Combine into one `.with_columns()` with multiple expressions |
| `pandas` for new code | Missing polars performance, lazy eval | Use `polars` for all new tabular work |
| Forgetting `validate=` on joins | Silent row multiplication from m:m joins | Always use `validate="m:1"` or `"1:1"` when cardinality is known |
| `fill_null(0)` on welfare/income columns | Creates spurious zero-welfare households, inflates poverty rates | Drop nulls and log weight share lost |

---

## General Python Anti-Patterns

| Anti-Pattern | Problem | Fix |
|-------------|---------|-----|
| Bare `except:` | Catches `KeyboardInterrupt`, `SystemExit`, everything | Use specific exception types |
| `except Exception as e: pass` | Silently swallows errors, hides bugs | Handle or re-raise with `raise` |
| Mutable default arguments `def f(x=[])` | Shared state across calls | Use `None` default + `x = x or []` |
| `import *` | Pollutes namespace, hides where names come from | Explicit imports always |
| `print()` for logging | No levels, no context, can't disable | Use `loguru` |
| `os.path.join()` | String-based, error-prone on Windows | Use `pathlib.Path` |
| Global variables for state | Hidden dependencies, impossible to test | Pass as arguments or use dependency injection |
| `== None` / `!= None` | Doesn't use identity check | Use `is None` / `is not None` |
| `type(x) == int` | Doesn't handle subclasses | Use `isinstance(x, int)` |
| Deeply nested code (3+ levels) | Hard to read, hard to test | Use early returns, extract functions |
| Magic numbers (`if n > 47`) | Unclear meaning | Use named constants (`MIN_SAMPLE_SIZE = 100`) |
| `eval()` / `exec()` | Security risk, hard to debug | Find alternatives |
| f-strings for log messages | Computed even when log level disabled | Use loguru's `logger.info("msg", key=val)` pattern |

---

## Async Anti-Patterns

| Anti-Pattern | Problem | Fix |
|-------------|---------|-----|
| `time.sleep()` in async function | Blocks event loop — all other requests freeze | Use `await asyncio.sleep()` |
| Sync I/O in async endpoint | Blocks event loop during file/DB read | Use `await run_in_threadpool(sync_fn)` (releases event loop during I/O wait) |
| `run_in_threadpool` for CPU-bound work | GIL is NOT released for pure Python CPU computation — threads serialize on the GIL | Use `ProcessPoolExecutor` via `loop.run_in_executor()` (separate process, bypasses GIL) |
| Creating `httpx.Client` (sync) in async route | Wrong client type | Use `httpx.AsyncClient` with `async with` |
| `asyncio.run()` inside async function | Nested event loops error | Just `await` the coroutine directly |
| `async def` on CPU-bound functions | Python GIL prevents threads from running in parallel; CPU work still serializes | Use `run_in_executor(ProcessPoolExecutor())` or a task queue (Celery, RQ) |
| New `AsyncClient` per request | Connection overhead on every call | Create once in lifespan, reuse via `app.state` |
| Not awaiting coroutines | Coroutine created but never executed | Always `await` async calls |

```python
# WRONG — blocks the entire event loop
@router.get("/data")
async def get_data():
    import time
    time.sleep(2)       # freezes all concurrent requests for 2 seconds
    return {"data": "..."}

# RIGHT — non-blocking sleep
@router.get("/data")
async def get_data():
    await asyncio.sleep(2)  # yields control; other requests run during this
    return {"data": "..."}

# WRONG — sync I/O in async endpoint
@router.get("/read")
async def read_file():
    with open("large_file.csv") as f:    # blocks event loop
        data = f.read()
    return {"lines": data.count("\n")}

# RIGHT — offload blocking I/O to thread pool
from fastapi.concurrency import run_in_threadpool

@router.get("/read")
async def read_file():
    data = await run_in_threadpool(Path("large_file.csv").read_text)
    return {"lines": data.count("\n")}
```

---

## FastAPI / pydantic Anti-Patterns

| Anti-Pattern | Problem | Fix |
|-------------|---------|-----|
| Raw `dict` as request/response body | No validation, no docs, no type safety | Use `pydantic.BaseModel` |
| `HTTPException` raised from service layer | Couples business logic to HTTP | Raise domain exceptions; map to HTTP in handlers |
| No `status_code` on POST endpoints | Defaults to 200 — should be 201 for creation | Add `status_code=status.HTTP_201_CREATED` |
| `response_model=None` | No response validation, no OpenAPI docs | Always specify `response_model` |
| Secrets in `Settings` without env var | Hardcoded secrets in source | Use `pydantic-settings`; no defaults for secrets |
| `global` for shared state in FastAPI | Not safe across workers | Use `app.state` or dependency injection |
| Validating input manually in route function | Bypasses pydantic, duplicates logic | Put all validation in the pydantic model |

```python
# WRONG — raw dict, no validation
@router.post("/estimate")
async def estimate(body: dict):
    country = body.get("country")   # could be None, wrong type, anything
    year = body.get("year")
    ...

# RIGHT — pydantic model validates at the boundary
class EstimateRequest(BaseModel):
    country: Annotated[str, Field(min_length=3, max_length=3)]
    year: Annotated[int, Field(ge=1990, le=2030)]

@router.post("/estimate", response_model=EstimateResponse)
async def estimate(body: EstimateRequest):
    # body.country and body.year are guaranteed valid here
    ...
```

---

## Testing Anti-Patterns

| Anti-Pattern | Problem | Fix |
|-------------|---------|-----|
| No assertions | Test always passes | Add specific `assert` statements |
| `assert True` | Meaningless | Assert specific values and types |
| Testing implementation details | Tests break on refactoring | Test observable behavior and outputs |
| Shared mutable state between tests | Tests affect each other | Use fixtures with function scope |
| External API calls in tests | Slow, flaky, dependent on network | Mock with `pytest-mock` or `httpx.MockTransport` |
| Giant test functions (multiple behaviors) | Hard to diagnose failures | One behavior per test function |
| Missing edge case: empty input | Function silently breaks on empty data | Always add `test_empty_*` variant |
| Missing edge case: null/None values | Function raises unhandled `NoneType` | Always add `test_null_*` variant |

---

## Environment Anti-Patterns

| Anti-Pattern | Problem | Fix |
|-------------|---------|-----|
| `pip install` without lockfile | Non-reproducible — installs different versions over time | Use `uv` with `uv.lock` |
| No `pyproject.toml` | Missing metadata, hard to distribute | Create one |
| `requirements.txt` without pins | Version drift across machines | Use lockfile or pin all versions |
| Committing `.venv/` | Bloats repo, platform-specific | Add to `.gitignore` |
| Committing `.env` | Exposes secrets | `.gitignore` + `.env.example` template |
| System Python for project work | Package conflicts across projects | Always use virtual environments via `uv` |
| `pip install -r requirements.txt` in CI | Not reproducible — pip resolves differently | Use `uv sync` with committed `uv.lock` |
