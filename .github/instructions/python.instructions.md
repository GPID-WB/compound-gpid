---
applyTo: "**/*.py"
module: shared
---

# Python Coding Standards

## Data Manipulation

- Use `polars` as the primary DataFrame library for new projects.
- Use `numpy` for numerical computing and array operations.
- Use `pandas` only when required by library compatibility (e.g., `statsmodels`, `sklearn`).
- Prefer lazy evaluation in polars (`scan_csv()`, `.lazy()`, `.collect()`).
- Use polars expressions (`pl.col()`, `pl.when()`, `pl.lit()`) over `.apply()` / `.map_elements()`.
- For joins, be explicit: `how="left"`, `how="inner"`, etc.
- Use `pl.concat()` for combining DataFrames. Avoid iterative `append()`.

## Visualization

- Use `plotnine` (grammar of graphics, ggplot2-equivalent) as the preferred visualization library.
- Alternative: `seaborn` for quick statistical plots, `matplotlib` for full control.
- Always label axes and provide titles.
- Use colorblind-friendly palettes.
- Save figures explicitly with `savefig()` or plotnine's `save()`. Specify dpi and dimensions.

## Testing with pytest

- Place tests in `tests/` directory at the project root.
- Name test files `test_<module>.py` matching source files.
- Name test functions `test_<behavior>()` — descriptive, not generic.
- Use `pytest.fixture` for reusable test setup.
- Use `pytest.mark.parametrize` for testing multiple inputs.
- Use `pytest.raises` for expected exceptions.
- Use `tmp_path` fixture for file-based tests.
- Keep test data inline or in `tests/fixtures/`.
- Run tests with `pytest -v` or `pytest --tb=short`.

## Type Hints

- Add type hints to all function signatures.
- Use `typing` module for complex types: `Optional`, `Union`, `list[str]`, `dict[str, int]`.
- Use `TypeAlias` for complex repeated types.
- Prefer built-in generics (`list[str]`) over `typing.List[str]` (Python 3.9+).
- Use `-> None` for functions that don't return a value.
- Consider `mypy` or `pyright` for static type checking.

## Documentation with Docstrings

- Every public function must have a docstring.
- Use Google-style or NumPy-style docstrings consistently within a project.
- Required sections: Args (or Parameters), Returns, Raises (if applicable).
- Include at least one Example in the docstring.
- Module-level docstrings for every `.py` file explaining its purpose.

## Project Structure

```
project-name/
├── src/
│   └── project_name/
│       ├── __init__.py
│       ├── module_a.py
│       └── module_b.py
├── tests/
│   ├── test_module_a.py
│   └── test_module_b.py
├── pyproject.toml
├── README.md
└── .gitignore
```

- Use `src/` layout for packages.
- Use flat layout for scripts/analysis projects.

## Environment Management

- Use `uv` (preferred) or `poetry` for dependency management.
- Lock dependencies with `uv.lock` or `poetry.lock`.
- Commit lockfiles to version control.
- Use `pyproject.toml` for project metadata and dependencies.
- Pin major versions in dependencies: `polars>=1.0,<2.0`.
- Do NOT commit virtual environments (`.venv/`, `venv/`).

## Error Handling

- Use specific exception types, not bare `except:`.
- Raise `ValueError` for bad inputs, `TypeError` for type mismatches.
- Create custom exceptions for domain-specific errors.
- Use `logging` module instead of `print()` for diagnostic output.
- Provide informative error messages with context.

## Style

- Follow PEP 8. Use `ruff` for linting and formatting.
- Use snake_case for functions and variables, PascalCase for classes.
- Use UPPER_SNAKE_CASE for constants.
- Limit lines to 88 characters (ruff default).
- Use f-strings for string formatting.
- Use pathlib.Path instead of string path manipulation.
- Prefer list/dict/set comprehensions over `map()`/`filter()`.
- Use `if __name__ == "__main__":` guard in scripts.
