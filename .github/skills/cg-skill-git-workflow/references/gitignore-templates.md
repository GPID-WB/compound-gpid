# .gitignore Templates

## R Project

```gitignore
# R
.Rhistory
.RData
.Rproj.user/
*.Rproj
.Renviron

# renv
renv/library/
renv/local/
renv/cellar/
renv/lock/
renv/python/
renv/staging/

# Data (uncomment if large)
# data/
# *.csv
# *.xlsx
# *.dta
# *.sav
# *.parquet

# Output
output/

# OS
.DS_Store
Thumbs.db

# IDE
.vscode/
.idea/

# Compound GPID
compound-gpid.local.md
```

## Python Project

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.egg-info/
dist/
build/
*.egg

# Virtual environments
.venv/
venv/

# Data (uncomment if large)
# data/
# *.csv
# *.xlsx
# *.dta
# *.parquet

# Output
output/

# Environment variables
.env
*.env.local

# Jupyter
.ipynb_checkpoints/

# OS
.DS_Store
Thumbs.db

# IDE
.vscode/
.idea/

# Compound GPID
compound-gpid.local.md
```

## Mixed R + Python Project

Combine both templates above.

## What to Always Commit

- `renv.lock` / `uv.lock` / `poetry.lock`
- `DESCRIPTION` / `pyproject.toml`
- `README.md`
- `.gitignore`
- Configuration files
- Small reference data (< 1MB)
- Documentation

## What to Never Commit

- API keys, passwords, tokens, credentials
- `.Renviron` / `.env` with secrets
- Large data files (> 1MB unless reference data)
- Database files
- Personal IDE settings
- Compiled binaries
- Virtual environments / `renv/library/`
