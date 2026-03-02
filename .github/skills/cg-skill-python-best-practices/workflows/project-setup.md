# Python Project Setup

## Analysis Project (Flat Layout)

```
project-name/
├── src/
│   ├── cleaning.py
│   ├── analysis.py
│   └── utils.py
├── scripts/
│   └── run_analysis.py
├── tests/
│   ├── test_cleaning.py
│   └── test_analysis.py
├── data/                  # gitignored if large
├── output/
│   ├── figures/
│   └── tables/
├── pyproject.toml
├── README.md
└── .gitignore
```

## Package (src Layout)

```
package-name/
├── src/
│   └── package_name/
│       ├── __init__.py
│       ├── cleaning.py
│       ├── analysis.py
│       └── utils.py
├── tests/
│   ├── conftest.py
│   ├── test_cleaning.py
│   └── test_analysis.py
├── pyproject.toml
├── README.md
└── .gitignore
```

## pyproject.toml (uv)

```toml
[project]
name = "project-name"
version = "0.1.0"
description = "Brief project description"
readme = "README.md"
requires-python = ">=3.11"
dependencies = [
    "polars>=1.0,<2.0",
    "numpy>=1.26,<3.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "ruff>=0.4",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-v --tb=short"

[tool.ruff]
line-length = 88
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "W", "UP"]
```

## Environment Setup with uv

```bash
# Initialize project
uv init project-name
cd project-name

# Add dependencies
uv add polars numpy
uv add --dev pytest ruff

# Sync environment
uv sync

# Run commands
uv run pytest
uv run ruff check .
uv run python scripts/run_analysis.py
```

## Environment Setup with poetry

```bash
# Initialize project
poetry new project-name
cd project-name

# Add dependencies
poetry add polars numpy
poetry add --group dev pytest ruff

# Install
poetry install

# Run commands
poetry run pytest
poetry run ruff check .
```

## .gitignore for Python Projects

```gitignore
# Python
__pycache__/
*.py[cod]
*.egg-info/
dist/
build/

# Virtual environments
.venv/
venv/

# IDE
.vscode/
.idea/

# OS
.DS_Store
Thumbs.db

# Data (uncomment if large)
# data/

# Environment
.env
*.env.local

# Compound GPID
compound-gpid.local.md
```

## Docstring Convention (Google Style)

```python
def clean_income(
    df: pl.DataFrame,
    income_col: str,
    ppp: float = 1.0,
) -> pl.DataFrame:
    """Clean and harmonize income variable.

    Converts income to PPP-adjusted values and handles missing data.

    Args:
        df: Input DataFrame with raw survey data.
        income_col: Name of the income column.
        ppp: PPP conversion factor. Defaults to 1.0.

    Returns:
        DataFrame with cleaned `income_ppp` column added.

    Raises:
        ValueError: If income_col is not found in df.

    Example:
        >>> df = pl.DataFrame({"id": [1, 2], "hh_income": [1000.0, 2000.0]})
        >>> clean_income(df, "hh_income", ppp=1.9)
    """
    if income_col not in df.columns:
        raise ValueError(f"Column '{income_col}' not found in DataFrame")

    return df.with_columns(
        (pl.col(income_col) / ppp).alias("income_ppp")
    )
```
