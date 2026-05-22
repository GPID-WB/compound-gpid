# Compound GPID — Project Instructions

## ⚠️ Pester Safety Rules (CRITICAL — violating these crashes VS Code)

Running Pester incorrectly in this project causes VS Code to freeze and crash. These rules are **mandatory** in every terminal command that invokes Pester. Load `cg-skill-pester-safety` before writing any `Invoke-Pester` command.

1. **Never run the full test suite as a directory**: `Invoke-Pester tests/` crashes VS Code. Always specify individual files.
2. **Never pipeline `-PassThru` output through `Select-Object -ExpandProperty TestResult`**: This pattern (`Invoke-Pester ... -PassThru | Select-Object -ExpandProperty TestResult | ...`) reliably freezes VS Code.
3. **Safe pattern — single file**:
   ```powershell
   Invoke-Pester tests/roadmap.Tests.ps1 -Quiet
   ```
   > ⚠️ **Pester version**: This project requires **Pester 4.10.1**. All test assertions use `Should -Be` (Pester 4+ syntax). The Windows built-in Pester 3.4.0 cannot run this suite. Install with: `Install-Module Pester -RequiredVersion 4.10.1 -Force -SkipPublisherCheck -Scope CurrentUser`. `-Output Minimal` and `-Output None` are Pester 5 flags — use `-Quiet` with Pester 4.
4. **Safe pattern — check for failures only** (if `-PassThru` is needed):
   ```powershell
   $r = Invoke-Pester tests/roadmap.Tests.ps1 -PassThru -Quiet
   $r | Select-Object TotalCount, PassedCount, FailedCount
   ```
   Assign to variable first — do **not** pipeline directly into `Select-Object` or `Where-Object`.
5. **NEVER use `2>&1 | ...` pipelines from Invoke-Pester**:
   ```powershell
   # ❌ CRASHES VS CODE
   Invoke-Pester tests/foo.Tests.ps1 2>&1 | Select-String -Pattern 'FAIL|fail' | ...
   ```
   To inspect failures, re-run without `-Quiet`: `if ($r.FailedCount -gt 0) { Invoke-Pester tests/foo.Tests.ps1 }`
6. **Never run Pester mid-stream in a long fix-triage session**: In a long session (brainstorm + plan + review accumulated), Pester output floods the agent context window and crashes VS Code even when PowerShell exits cleanly. Apply ALL fixes first, then run ONE test pass at the very end. For pure markdown edits that don't change frontmatter/tool lists, skip the test run entirely.
7. **Use `execution_subagent` for Pester in long sessions — not `run_in_terminal`**: Even `-Quiet -PassThru` via `run_in_terminal` injects terminal output into agent context and crashes VS Code in long sessions (crashes #15+16, 2026-04-15). Use `execution_subagent` which returns only a summary. Rule: any session + `prompt-tools.Tests.ps1` → always `execution_subagent`.
8. **Canonical full-suite runner** — use this instead of writing a `foreach` loop:
   ```powershell
   . tests\Run-Tests.ps1
   ```
   Results are written to `tests/last-run.json` — read this artifact via `execution_subagent` rather than parsing terminal output directly.
   Or via VS Code: `Ctrl+Shift+P` → **Tasks: Run Task** → **Run all Pester tests (safe)**
9. **Agent test workflow**: Agents must use `execution_subagent` to run `. tests\Run-Tests.ps1` and read `tests/last-run.json` for results. Never compose `Invoke-Pester` commands directly — use the canonical pattern in `cg-skill-pester-safety`.

See `.cg-docs/solutions/testing-patterns/2026-04-02-invoke-pester-full-suite-passthru-crashes-vscode.md` for full diagnosis.

---

You are working in a data science project maintained by the DECDG team at the World Bank. Follow these standards in all interactions.

## Language Preferences

- Check `compound-gpid.local.md` in the project root for the user's preferred language(s).
- Default: R, Python, and Stata are all acceptable. Ask the user if unclear.
- R style: dialect is set by `r-syntax` in `compound-gpid.local.md`. Default (`data.table-collapse`): use `collapse` for statistics/aggregation, `data.table` for data manipulation. When `r-syntax: "tidyverse"`: use tidyverse verbs; still use `collapse` for weighted statistics (no native tidyverse equivalent). Always use `ggplot2` + `wbplot` for visualization.
  - **Eight R skills**: R work is covered by eight skills. `cg-skill-r-collapse` covers the collapse statistical computing API. `cg-skill-r-datatable` covers data.table manipulation (`:=`, joins, melt/dcast). `cg-skill-r-tidyverse` covers dplyr 1.2+ patterns for tidyverse projects. `cg-skill-r-visualization` covers ggplot2 + wbplot for all dialects. `cg-skill-r-technical` covers package/infrastructure work (plumber, shiny, targets, renv). `cg-skill-r-analytical` covers domain knowledge (fixest, modelsummary, wbplot, welfare measurement). `cg-skill-r-testing` covers testing R code with testthat. `cg-skill-r-shared` provides universal base R style rules (`<-` assignment, `snake_case`, `TRUE`/`FALSE`) that apply regardless of dialect. The `r.instructions.md` file (auto-applied to all `.R` files) routes to the correct dialect skills based on `r-syntax`. Load additional skills based on work type.
- Python style: polars/numpy/pandas for data, seaborn/plotnine for visualization.
- Stata style: `local` macros, `repkit` for reproducibility, `///` for continuation. Always load `cg-skill-stata-best-practices` when writing or reviewing `.do`/`.ado` files. Load `cg-skill-stata-testing` when writing, reviewing, or debugging test blocks, assertion patterns, or reproducibility checks.
  - **Stata skills**: `cg-skill-stata-best-practices` covers all general coding, repkit API, and community packages; `cg-skill-stata-testing` is an additive layer for assertion patterns, data validation, result verification, and reprun testing workflows.

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
| Review a plan before implementing | `/cg-plan-review` |
| Direct roadmap edit | `@cg-roadmap` |
| View roadmap progress | `/cg-roadmap-view` |
| Discover what to work on next | `/cg-ideate` |
| Resume interrupted work | `/cg-resume` |
| Diagnose VS Code crash | `/cg-diagnose` |
| Implement a plan | `/cg-work` |
| Implement a specific phase | `/cg-work phaseX` |
| Code review | `/cg-review` |
| Apply review findings | `/cg-fix-triage` |
| Fix VS Code problems | `/cg-fix-problems` |
| Capture a solution | `/cg-compound` |
| Refresh knowledge base | `/cg-compound-refresh` |

> **Prompt design convention**: Each prompt file is intentionally self-contained and repeats the "Step 0: Get Bearings" charter-reading pattern verbatim. This duplication is deliberate — prompts must work standalone without requiring the user to have loaded any prior context. Do not factor out this boilerplate.

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
- **thorough**: Runs all 8 review agents + `cg-learnings-researcher` to cross-reference past solutions and `cg-adversarial` for adversarial edge-case analysis. Use for major features and refactors.

## Priority System for Review Findings

- **P0 — BLOCKING**: Immediate remediation required. Exploitable security vulnerability, PII/credential exposure, silent data corruption, incorrect statistical results.
- **P1 — CRITICAL**: Must fix before merge. Bugs causing incorrect behavior, missing critical validation, error handling gaps.
- **P2 — IMPORTANT**: Should fix. Performance problems, missing tests, poor documentation.
- **P3 — MINOR**: Nice to have. Style improvements, minor refactors, suggestions.

## Compound Research (CR) Skills

When the `modules: [research]` flag is set in `compound-gpid.local.md`, these research-specific skills are loaded by `/cr-*` commands:

- `cr-skill-research-workflow` — task taxonomy, P0–P3 priority system, `.cg-docs/research/` layout (always loaded)
- `cr-skill-research-integrity` — P0 silent-error catalog (always loaded by CR agents)
- `cr-skill-structural-econometrics` — discrete choice, DP, GMM, MLE (Theory/Modeling)
- `cr-skill-mathematical-derivation` — LaTeX notation, FOC derivation, code-math mapping (Theory/Modeling)
- `cr-skill-symbolic-verification` — SymPy gradient/Hessian checks (Theory/Modeling)
- `cr-skill-identification-strategies` — IV, RDD, DiD, event studies, synthetic control (Identification)
- `cr-skill-theory-data-dialogue` — distributional tests, moment checks, support analysis (Specification Analysis)
- `cr-skill-research-eda` — research-framed EDA, weighted descriptives, outlier analysis (EDA)
- `cr-skill-ml-economics` — LASSO, random forests, CV correctness, double ML/DML, OOS assessment, reproducibility seeds, survey-weighted ML for complex-design survey data, missing value handling in ML pipelines, class imbalance and rare events, data leakage detection, hyperparameter search transparency, and economic interpretation of ML output (ML/Prediction)
- `cr-skill-academic-writing` — journal style (AER, JPE, QJE, Econometrica), section structure, abstract writing, equation exposition, notation discipline, citation style, response-to-referee patterns (Writing)
- `cr-skill-publication-output` — `modelsummary`/`fixest::etable` for regression tables, `kableExtra` for LaTeX tables, ggplot2+wbplot for figures, font/size conventions, figure-caption discipline, table-note discipline (loaded by `@cr-publication-output` for Tables/Figures tasks)
- `cr-skill-replication-standards` — AEA/AER replication package standards: archive structure, README templates, dependency lockfiles, seed registries, data documentation (codebook + PII checklist), path portability rules, sensitive-data handling, archive packaging checklists (loaded by `@cr-replication-package` for Reproducibility tasks)

All CR skills declare `module: research` and are loaded only when the research module is enabled.

## Knowledge Compounding

After solving a non-trivial problem, use `/cg-compound` to capture the solution in `.cg-docs/solutions/[category]/`. This makes the solution findable for future work. Categories: `bugs`, `build-errors`, `data-quality`, `environment-issues`, `git-workflows`, `performance-issues`, `testing-patterns`.

<!-- Pester Safety Rules appear at the top of this file -->
