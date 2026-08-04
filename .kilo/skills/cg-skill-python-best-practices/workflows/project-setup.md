# Python Project Setup

## Analysis Project (flat layout)

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

## Package (src layout)

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

## REST API (FastAPI)

```
api-name/
├── src/
│   └── api_name/
│       ├── __init__.py
│       ├── main.py          # App factory + lifespan
│       ├── config.py        # pydantic-settings
│       ├── dependencies.py  # Shared FastAPI dependencies
│       ├── exceptions.py    # Custom exception hierarchy
│       ├── logging.py       # loguru configuration
│       ├── routers/
│       │   ├── __init__.py
│       │   ├── health.py
│       │   └── data.py
│       ├── models/
│       │   ├── requests.py  # Pydantic request models
│       │   └── responses.py # Pydantic response models
│       └── services/        # Business logic — no FastAPI imports here
│           └── compute.py
├── tests/
│   ├── conftest.py          # TestClient fixture
│   └── test_routes.py
├── pyproject.toml
├── .env.example             # Template — never commit .env
└── .gitignore
```

See [API Patterns](api-patterns.md) for the full FastAPI conventions.

---

## pyproject.toml — Analysis Project

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
    "plotnine>=0.13",
    "loguru>=0.7",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-cov",
    "ruff>=0.4",
    "memray",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-v --tb=short"

[tool.ruff]
line-length = 88
target-version = "py311"

[tool.ruff.lint]
select = [
    "E",    # pycodestyle errors
    "F",    # pyflakes (undefined names, unused imports)
    "I",    # isort (import ordering)
    "W",    # pycodestyle warnings
    "UP",   # pyupgrade (rewrites to modern Python syntax — can be surprising)
    "B",    # flake8-bugbear (opinionated anti-patterns)
    "SIM",  # flake8-simplify
]
ignore = ["E501"]  # line length handled by formatter

[tool.ruff.format]
quote-style = "double"

[tool.pyright]
pythonVersion = "3.11"
typeCheckingMode = "basic"   # upgrade to "strict" for published packages
include = ["src"]
```

## pyproject.toml — FastAPI Project

```toml
[project]
name = "gpid-api"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.110",
    "uvicorn[standard]>=0.27",
    "pydantic>=2.0",
    "pydantic-settings>=2.0",
    "httpx>=0.27",           # async HTTP client
    "polars>=1.0,<2.0",
    "loguru>=0.7",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.23",
    "ruff>=0.4",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"        # required for async tests
addopts = "-v --tb=short"

[tool.ruff]
line-length = 88
target-version = "py311"

[tool.ruff.lint]
select = [
    "E",    # pycodestyle errors
    "F",    # pyflakes
    "I",    # isort
    "W",    # pycodestyle warnings
    "UP",   # pyupgrade
    "B",    # flake8-bugbear
    "SIM",  # flake8-simplify
]
ignore = ["E501"]

[tool.ruff.format]
quote-style = "double"

[tool.pyright]
pythonVersion = "3.11"
typeCheckingMode = "basic"
include = ["src"]
```

---

## Lockfile and Reproducibility

**Always commit `uv.lock` to version control.** This ensures every team member
and CI pipeline uses identical package versions. Never add `uv.lock` to
`.gitignore`.

For stochastic analyses, set random seeds explicitly to ensure reproducibility:

```python
import random
import numpy as np

# Set at the entry point of each analysis script
SEED = 42
random.seed(SEED)
np.random.seed(SEED)   # legacy API; prefer Generator for new code:
rng = np.random.default_rng(SEED)
```

---

## Environment Setup with uv

```bash
# Initialize a new project
uv init project-name
cd project-name

# Add runtime dependencies
uv add polars numpy loguru

# Add dev dependencies
uv add --dev pytest ruff memray

# For FastAPI projects
uv add fastapi "uvicorn[standard]" pydantic pydantic-settings httpx
uv add --dev pytest pytest-asyncio

# Sync environment (installs from uv.lock)
uv sync

# In CI/CD — use --frozen to prevent accidental lockfile updates
uv sync --frozen

# Run commands within the venv
uv run pytest
uv run ruff check .
uv run ruff format .
uv run python scripts/run_analysis.py

# Start FastAPI dev server
uv run uvicorn src.api_name.main:app --reload --port 8000
```

## .gitignore for Python Projects

```gitignore
# Python
__pycache__/
*.py[cod]
*.egg-info/
dist/
build/
.eggs/

# Virtual environments
.venv/
venv/
# DO NOT ignore uv.lock — commit it for reproducibility

# IDE
.vscode/
.idea/
*.swp

# OS
.DS_Store
Thumbs.db

# Testing & profiling
.pytest_cache/
.coverage
htmlcov/
*.prof
*.bin           # memray output

# Data (uncomment if large)
# data/

# Secrets — never commit
.env
*.env.local
*.pem
*.key

# Compound GPID
compound-gpid.local.md
```

---

## Docstring Convention (Google Style)

Use Google-style docstrings consistently across the project.

```python
def compute_poverty_rate(
    df: pl.DataFrame,
    welfare_col: str,
    poverty_line: float = 2.15,
    weight_col: str | None = None,
) -> float:
    """Compute headcount poverty rate from microdata.

    Args:
        df: DataFrame with one row per individual/household.
        welfare_col: Column name for per-capita welfare (PPP USD).
        poverty_line: Poverty threshold in same units as welfare_col.
            Defaults to the international extreme poverty line (2.15).
        weight_col: Survey weight column. If None, equal weights assumed.

    Returns:
        Headcount poverty rate in [0, 1].

    Raises:
        ValueError: If welfare_col is not in df or poverty_line <= 0.
        InsufficientSampleError: If df has fewer than 100 observations.

    Example:
        >>> df = pl.DataFrame({"welfare": [1.0, 3.0, 5.0], "weight": [1.0, 1.0, 1.0]})
        >>> compute_poverty_rate(df, "welfare", poverty_line=2.15, weight_col="weight")
        0.3333333333333333
    """
```
