# Compound GPID — Project Instructions

You are working in a data science project maintained by the DECDG team at the World Bank. Follow these standards in all interactions.

## Language Preferences

- Check `compound-gpid.local.md` in the project root for the user's preferred language(s).
- Default: R, Python, and Stata are all acceptable. Ask the user if unclear.
- R style: `data.table` for data manipulation, `ggplot2` for visualization.
  - **Two R skills**: R work is covered by two skills. `cg-skill-r-technical` covers package/infrastructure work (data.table, plumber, shiny, targets, renv). `cg-skill-r-analytical` covers statistical/econometric work (survey analysis, fixest, modelsummary, wbplot, welfare measurement). Load the appropriate skill based on work type; load both for mixed work.
- Python style: polars/numpy/pandas for data, seaborn/plotnine for visualization.
- Stata style: `local` macros, `repkit` for reproducibility, `///` for continuation. Always load `cg-skill-stata-core` when writing or reviewing `.do`/`.ado` files.

## Coding Standards

### General
- Write clean, readable, well-documented code.
- Prefer explicit over implicit. Avoid magic numbers and unnamed constants.
- Functions should do one thing. Keep them short and focused.
- Use meaningful variable and function names. Avoid abbreviations unless domain-standard.
- DRY: Don't Repeat Yourself. Extract common patterns into reusable functions.
- Handle errors gracefully. Never silently swallow errors.
- Avoid hardcoded file paths. Use relative paths or configuration.

### Code Organization
- Separate data loading, processing, analysis, and visualization into distinct modules/scripts.
- Keep scripts under 300 lines. Split larger files by responsibility.
- Use consistent project structure (see `cg-skill-r-technical`, `cg-skill-r-analytical`, `cg-skill-python-best-practices`, or `cg-skill-stata-core` skills).

## Testing Requirements

- All functions must have corresponding tests.
- R: use `testthat`. Python: use `pytest`. Stata: use `assert` statements and validation do-files.
- Tests should cover: normal cases, edge cases, error conditions.
- Test data should be minimal and self-contained (no dependency on external files).
- Aim for meaningful coverage, not 100% line coverage.

## Documentation Standards

- Every function must have documentation (roxygen2 for R, docstrings for Python, `*!` version comments and header blocks for Stata `.ado` files).
- Document parameters, return values, and provide at least one example.
- Every project must have a README.md explaining: purpose, setup, usage, data sources.
- Complex logic should have inline comments explaining *why*, not *what*.
- Update documentation when changing code behavior.

## Version Control

- **Commit messages**: Use conventional commits format: `type(scope): description`
  - Types: `feat`, `fix`, `docs`, `test`, `refactor`, `chore`, `data`, `analysis`
  - Example: `feat(cleaning): add income variable harmonization`
  - Example: `fix(model): correct standard error clustering`
- **Branching**: Use feature branches off `main`. Name them `type/short-description`.
  - Example: `feat/poverty-decomposition`, `fix/missing-weights`
- **Never commit**: data files (unless small reference data), credentials, API keys, `.Rhistory`, `__pycache__`, `.DS_Store`.
- **Always commit**: lockfiles (`renv.lock`, `poetry.lock`, `uv.lock`), `code/ado/` (Stata package cache via `repado`), configuration files, documentation.

## Review Depth Tiers

When the `/cg-review` prompt is invoked, it checks `compound-gpid.local.md` for the configured depth:

- **light**: Runs `cg-code-quality` + `cg-testing` agents only. Use for quick fixes and small changes.
- **standard**: Runs all 8 review agents. Default for most work.
- **thorough**: Runs all 8 review agents + `cg-learnings-researcher` to cross-reference past solutions. Use for major features and refactors.

## Priority System for Review Findings

- **P1 — CRITICAL**: Must fix before merge. Security issues, data corruption risks, incorrect results.
- **P2 — IMPORTANT**: Should fix. Performance problems, missing tests, poor documentation.
- **P3 — MINOR**: Nice to have. Style improvements, minor refactors, suggestions.

## Knowledge Compounding

After solving a non-trivial problem, use `/cg-compound` to capture the solution in `.cg-docs/solutions/[category]/`. This makes the solution findable for future work. Categories: `bugs`, `build-errors`, `data-quality`, `environment-issues`, `git-workflows`, `performance-issues`, `testing-patterns`.
