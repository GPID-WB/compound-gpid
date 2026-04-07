# Compound GPID — Project Instructions

## ⚠️ Pester Safety Rules (CRITICAL — violating these crashes VS Code)

Running Pester incorrectly in this project causes VS Code to freeze and crash. These rules are **mandatory** in every terminal command that invokes Pester. Load `cg-skill-pester-safety` before writing any `Invoke-Pester` command.

1. **Never run the full test suite as a directory**: `Invoke-Pester tests/` crashes VS Code. Always specify individual files.
2. **Never pipeline `-PassThru` output through `Select-Object -ExpandProperty TestResult`**: This pattern (`Invoke-Pester ... -PassThru | Select-Object -ExpandProperty TestResult | ...`) reliably freezes VS Code.
3. **Safe pattern — single file**:
   ```powershell
   Invoke-Pester tests/roadmap.Tests.ps1 -Output Minimal
   ```
4. **Safe pattern — check for failures only** (if `-PassThru` is needed):
   ```powershell
   $r = Invoke-Pester tests/roadmap.Tests.ps1 -PassThru -Output None
   $r | Select-Object TotalCount, PassedCount, FailedCount
   ```
   Assign to variable first — do **not** pipeline directly into `Select-Object` or `Where-Object`.

See `.cg-docs/solutions/testing-patterns/2026-04-02-invoke-pester-full-suite-passthru-crashes-vscode.md` for full diagnosis.

---

You are working in a data science project maintained by the DECDG team at the World Bank. Follow these standards in all interactions.

## Language Preferences

- Check `compound-gpid.local.md` in the project root for the user's preferred language(s).
- Default: R, Python, and Stata are all acceptable. Ask the user if unclear.
- R style: `collapse` for statistics/aggregation, `data.table` for data manipulation, `ggplot2` for visualization. Preference hierarchy: collapse > data.table > tidyverse.
  - **Three R skills**: R work is covered by three skills. `cg-skill-r-technical` covers package/infrastructure work (collapse, data.table, plumber, shiny, targets, renv). `cg-skill-r-analytical` covers statistical/econometric work (collapse, data.table, fixest, modelsummary, wbplot, welfare measurement). `cg-skill-r-testing` covers testing R code with testthat (test structure, expectations, fixtures, mocking, snapshots, BDD). Load `cg-skill-r-testing` when writing, reviewing, or debugging R tests (also load `cg-skill-r-technical` if tests cover plumber endpoints or httr2 clients). Load the appropriate skill(s) based on work type.
- Python style: polars/numpy/pandas for data, seaborn/plotnine for visualization.
- Stata style: `local` macros, `repkit` for reproducibility, `///` for continuation. Always load `cg-skill-stata-best-practices` when writing or reviewing `.do`/`.ado` files.

## Project Context

- Read `compound-gpid.md` in the project root for project objective, key deliverables,
  constraints, and current focus. This file is the authoritative source of
  what this project is building and why.
- If `compound-gpid.md` does not exist, suggest the user run `/cg-setup`.
- Do not modify the **body** of `compound-gpid.md` (Objective, Key
  Deliverables, Constraints, Current Focus sections) without explicit user
  approval. The `last-reviewed` frontmatter field is metadata — update it
  automatically whenever the user explicitly approves a charter change.
- Never remove body content from `compound-gpid.md` without first archiving
  it to `.cg-docs/archive/charter-history.md` (create the directory if it
  doesn't exist). The full archiving procedure is in `/cg-strategy`.

## Workflow Entry Points

> **Entry points only.** For all commands, see [docs/reference.md](../docs/reference.md).

| Situation | Command |
|---|---|
| Full project vision to structure | `/cg-strategy` |
| Mid-project direction question | `/cg-strategy` |
| One fuzzy task to clarify | `/cg-brainstorm` |
| Known task to plan | `/cg-plan` |
| Direct roadmap edit | `@cg-roadmap` |
| Resume interrupted work | `/cg-resume` |
| Implement a plan | `/cg-work` |
| Code review | `/cg-review` |
| Apply review findings | `/cg-fix-triage` |
| Capture a solution | `/cg-compound` |

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
- Use consistent project structure (see `cg-skill-r-technical`, `cg-skill-r-analytical`, `cg-skill-python-best-practices`, or `cg-skill-stata-best-practices` skills).

## Testing Requirements

- All functions must have corresponding tests.
- R: use `testthat`. Python: use `pytest`. Stata: use `assert` statements and validation do-files.
- Tests should cover: normal cases, edge cases, error conditions.
- Test data should be minimal and self-contained (no dependency on external files).
- Aim for meaningful coverage, not 100% line coverage.
- **PowerShell/Pester**: Always load `cg-skill-pester-safety` before writing any `Invoke-Pester` terminal command. See Pester Safety Rules at the top of this file.

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

<!-- Pester Safety Rules appear at the top of this file -->
