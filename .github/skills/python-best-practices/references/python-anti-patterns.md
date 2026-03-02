# Common Python Anti-Patterns

## Data Manipulation Anti-Patterns

| Anti-Pattern | Problem | Fix |
|-------------|---------|-----|
| `.apply()` in polars | Slow, defeats vectorization | Use expressions: `pl.col()`, `pl.when()` |
| `.map_elements()` everywhere | Python loop under the hood | Use native polars expressions |
| `.to_pandas()` for simple ops | Unnecessary conversion | Stay in polars |
| Iterating over DataFrame rows | O(n) Python loop | Use vectorized operations |
| Growing list then `pl.from_records()` | O(n²) reallocation | Use `pl.concat()` with list of frames |
| `pandas` for new code | Missing polars performance | Use `polars` for new projects |

## General Python Anti-Patterns

| Anti-Pattern | Problem | Fix |
|-------------|---------|-----|
| Bare `except:` | Catches everything including `KeyboardInterrupt` | Use specific exceptions |
| `except Exception as e: pass` | Silently swallows errors | Handle or re-raise |
| Mutable default arguments | `def f(x=[])` shares state | Use `None` default + `x = x or []` |
| `import *` | Pollutes namespace, hides dependencies | Use explicit imports |
| String concatenation with `+` | Slow for multiple strings | Use f-strings |
| `os.path.join()` | String-based, error-prone | Use `pathlib.Path` |
| Global variables for state | Hidden dependencies | Pass as arguments |
| `print()` for logging | No levels, can't disable | Use `logging` module |
| No type hints | Hard to understand and maintain | Add type hints to all signatures |
| `== None` / `!= None` | Doesn't use identity check | Use `is None` / `is not None` |
| `type(x) == int` | Doesn't handle subclasses | Use `isinstance(x, int)` |
| Deeply nested code | Hard to read and test | Use early returns, extract functions |
| Long functions (>30 lines) | Low cohesion | Split into smaller functions |
| Magic numbers | Unclear meaning | Use named constants |
| `eval()` / `exec()` | Security risk | Find alternatives |

## Testing Anti-Patterns

| Anti-Pattern | Problem | Fix |
|-------------|---------|-----|
| No assertions | Test always passes | Add specific assertions |
| `assert True` | Meaningless test | Assert specific values |
| Testing implementation | Brittle tests | Test behavior and outputs |
| Shared mutable state | Tests affect each other | Use fixtures with proper scope |
| External dependencies in tests | Slow, flaky | Mock or use fixtures |
| Giant test functions | Hard to debug | One assertion per test |

## Environment Anti-Patterns

| Anti-Pattern | Problem | Fix |
|-------------|---------|-----|
| `pip install` without lockfile | Non-reproducible | Use `uv` or `poetry` with lockfiles |
| No `pyproject.toml` | Missing project metadata | Create one |
| `requirements.txt` without pins | Version drift | Pin versions or use lockfile |
| Committing `.venv/` | Bloats repo | Add to `.gitignore` |
| System Python | Conflicts between projects | Use virtual environments |
