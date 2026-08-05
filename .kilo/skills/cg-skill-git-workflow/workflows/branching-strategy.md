# Branching Strategy

## Main Branch

- `main` is the primary branch. It should always be in a deployable/working state.
- Never commit directly to `main`. Always use feature branches and PRs.

## Feature Branches

### Naming Convention

```
type/short-description
```

| Type | Use When |
|------|----------|
| `feat` | Adding new functionality |
| `fix` | Fixing a bug |
| `refactor` | Restructuring code without changing behavior |
| `docs` | Documentation only changes |
| `test` | Adding or modifying tests |
| `chore` | Build, CI, dependency updates |
| `data` | Data pipeline changes |
| `analysis` | Analysis code changes |

### Examples

```
feat/poverty-decomposition
fix/missing-survey-weights
refactor/clean-income-pipeline
docs/update-readme
test/add-cleaning-tests
data/harmonize-2023-survey
```

## Workflow

```
1. Create branch from main
   git checkout main
   git pull
   git checkout -b feat/my-feature

2. Work on the feature
   git add .
   git commit -m "feat(scope): description"

3. Push and create PR
   git push -u origin feat/my-feature

4. After review and merge, clean up
   git checkout main
   git pull
   git branch -d feat/my-feature
```

## Rules

- Keep branches short-lived (days, not weeks).
- One feature per branch. Don't mix unrelated changes.
- Rebase on `main` before merging if there are conflicts.
- Delete branches after merging.
- Use descriptive branch names that convey intent.
