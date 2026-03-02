# Commit Conventions

## Format

```
type(scope): description
```

- **type**: Category of change (see table below)
- **scope**: Module or area affected (optional but recommended)
- **description**: Short imperative statement (lowercase, no period)

## Types

| Type | When to Use | Example |
|------|-------------|---------|
| `feat` | New feature or functionality | `feat(cleaning): add income harmonization` |
| `fix` | Bug fix | `fix(model): correct standard error clustering` |
| `docs` | Documentation changes | `docs(readme): add data source description` |
| `test` | Adding or modifying tests | `test(cleaning): add edge case for missing values` |
| `refactor` | Code restructuring (no behavior change) | `refactor(utils): extract date parsing function` |
| `chore` | Build, CI, dependency updates | `chore(deps): update data.table to 1.16.0` |
| `data` | Data pipeline changes | `data(survey): add 2023 harmonization` |
| `analysis` | Analysis code changes | `analysis(poverty): add regional decomposition` |
| `style` | Formatting, no code change | `style(cleaning): apply consistent indentation` |
| `perf` | Performance improvement | `perf(merge): use setkey for binary search join` |

## Rules

1. **Use imperative mood**: "add feature" not "added feature" or "adds feature"
2. **Lowercase**: Don't capitalize the description
3. **No period**: Don't end with a period
4. **Short**: Keep under 72 characters total
5. **Focused**: Each commit should be one logical change

## Body (Optional)

For complex changes, add a body after a blank line:

```
feat(model): add fixed effects specification

Add country and year fixed effects to the baseline regression model.
This addresses reviewer comment #3 about controlling for time-invariant
country characteristics.

Closes #42
```

## Breaking Changes

If a commit introduces breaking changes, add `!` after the type:

```
feat(api)!: change return type of aggregate_poverty()
```

## Multiple Files, One Commit

Group related changes in a single commit:

```
feat(cleaning): add income variable harmonization

- Add clean_income() function in R/cleaning.R
- Add tests in tests/testthat/test-cleaning.R
- Update documentation in man/clean_income.Rd
```

## Anti-Patterns

| Bad | Good |
|-----|------|
| `update code` | `fix(cleaning): handle NA in income column` |
| `WIP` | `feat(model): add preliminary regression specification` |
| `fix` | `fix(io): correct file encoding for Latin-1 csvs` |
| `changes` | `refactor(utils): extract PPP conversion to helper` |
| `Friday commit` | `feat(viz): add poverty trend line chart` |
