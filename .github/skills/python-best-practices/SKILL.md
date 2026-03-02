---
name: python-best-practices
description: "Best practices for Python development with polars, numpy, pytest, type hints, and uv/poetry."
---

# Python Best Practices

Reference skill for Python development in the DECDG team. Covers `polars` for data manipulation, `numpy` for numerical computing, `pytest` for testing, type hints for safety, and `uv`/`poetry` for environment management.

## Quick Reference

| Task | Package | Key Pattern |
|------|---------|-------------|
| Data manipulation | `polars` | Lazy evaluation, expressions, method chaining |
| Numerical computing | `numpy` | Vectorized operations, broadcasting |
| Visualization | `plotnine` / `seaborn` | Grammar of graphics / statistical plots |
| Testing | `pytest` | Fixtures, parametrize, `tmp_path` |
| Linting & formatting | `ruff` | Fast, comprehensive Python linter |
| Environment | `uv` / `poetry` | Lockfiles, `pyproject.toml` |

## Workflows

- [polars Patterns](workflows/polars-patterns.md)
- [Testing with pytest](workflows/testing-pytest.md)
- [Project Setup](workflows/project-setup.md)

## References

- [polars Quick Reference](references/polars-reference.md)
- [Common Anti-Patterns](references/python-anti-patterns.md)
