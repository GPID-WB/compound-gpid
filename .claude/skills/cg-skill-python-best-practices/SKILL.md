---
name: cg-skill-python-best-practices
description: "Best practices for Python development on the GPID technical team. Covers polars for data manipulation (never pandas for new code), FastAPI and pydantic for REST APIs, pytest for testing, loguru for structured logging, type hints, async patterns, performance profiling with memray and cProfile, and uv for environment management. ALWAYS load this skill when: (1) any .py file is open or being created, (2) the code contains print() or import logging — both must be replaced with loguru, (3) polars .apply() or .map_elements() is used — replace with native expressions, (4) a FastAPI endpoint, pydantic model, or async function is being written. Includes package selection guidance (when to use polars vs numpy, plotnine vs seaborn, FastAPI vs Flask), anti-patterns catalog, and API development conventions. Consumed by cg-code-quality, cg-performance, and cg-architecture agents on .py files."
---

# Python Best Practices

Reference skill for Python development on the GPID technical team. Covers the full
spectrum: data pipelines, REST APIs, Shiny-equivalent dashboards, and reusable packages.

---

## Quick Reference

| Task | Tool | Key Pattern |
|------|------|-------------|
| Data manipulation | `polars` | Lazy evaluation, expressions — never `.apply()` |
| Numerical computing | `numpy` | Vectorized operations, avoid Python loops |
| REST APIs | `FastAPI` + `pydantic` | Router modules, typed request/response models |
| Data validation | `pydantic` | `BaseModel`, `Field`, validators |
| Visualization | `plotnine` / `seaborn` | Grammar of graphics / statistical plots |
| Testing | `pytest` | Fixtures, parametrize, `tmp_path`, `httpx` for APIs |
| Linting & formatting | `ruff` | Replaces flake8, isort, black |
| Logging | `loguru` | Structured logs, `logger.bind()`, no `print()` |
| Error handling | Custom exceptions + `loguru` | Typed errors, never bare `except:` |
| Profiling | `cProfile` / `memray` | Profile before optimizing |
| Environment | `uv` (preferred) | `uv add`, `uv.lock`, `uv run` |
| Type safety | Type hints + `pyright` | All public signatures annotated; use `str \| None` (3.10+), `Annotated` for pydantic |

## When to Use Which Tool

See [Package Decisions](references/package-decisions.md) for the full decision
guide. Quick rules:

- `polars` for any tabular data — never `pandas` for new code
- `numpy` for array math, linear algebra, and when polars has no expression
- `plotnine` for publication-quality / ggplot-style charts; `seaborn` for quick EDA
- `FastAPI` for any HTTP API; `pydantic` for any data model that crosses a boundary
- `loguru` for all logging — never `print()`, never the stdlib `logging` module directly

---

## Workflows

- [polars Patterns](workflows/polars-patterns.md) — lazy evaluation, expressions, joins, window functions, performance
- [API Patterns](workflows/api-patterns.md) — FastAPI structure, pydantic models, async, dependency injection, error handling
- [Logging and Errors](workflows/logging-and-errors.md) — loguru setup, structured logging, custom exceptions, profiling
- [Testing with pytest](workflows/testing-pytest.md) — fixtures, parametrize, API testing with httpx, polars assertions
- [Project Setup](workflows/project-setup.md) — uv, pyproject.toml, project layouts for analysis vs package vs API

## References

- [polars Quick Reference](references/polars-reference.md) — cheat sheet for common operations
- [Package Decisions](references/package-decisions.md) — when to use what and why
- [Common Anti-Patterns](references/python-anti-patterns.md) — what Copilot gets wrong; read before reviewing any output

---

## When to Load This Skill

Load whenever:
- Any `.py` or `.ipynb` file is open or being created
- Writing or reviewing FastAPI routes, pydantic models, or async functions
- Building data pipelines with polars
- Setting up a new Python project (package, API, analysis)
- Reviewing Python code for performance, correctness, or maintainability
- The `cg-code-quality`, `cg-performance`, or `cg-architecture` agents are running on a Python project
