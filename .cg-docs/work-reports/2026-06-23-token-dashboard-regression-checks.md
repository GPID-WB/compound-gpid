# Token Dashboard and Regression Checks Execution Report

Plan reference: `.cg-docs/plans/2026-06-23-token-dashboard-regression-checks.md`

Active deviation policy: stored `autonomous`; runtime override `autonomous` from `/cg-work review:auto deviate:auto`.

## Run: 2026-06-23

Status: completed

### Completed Steps/Phases

- Phase 1: added `TOKEN-DASHBOARD.md` and `regression-check.json` to the existing `.cg-docs/token/` audit artifact family.
- Phase 2: updated `/cg-token-audit`, `docs/reference.md`, and `docs/workflow.md` to document dashboard/regression interpretation.
- Phase 3: regenerated audit artifacts, ran focused and full validation, recorded review evidence, and linked the roadmap feature as done.

### Deviations

- Bound regression failure semantics to existing `build_guardrails` output after plan review. The JSON status now fails only on deterministic guardrail failures, reports `baseline` when no comparable baseline is supplied, and reports `pass` only for a comparable no-failure run.

### Accepted Exceptions

- The final regenerated audit has 3 warnings, all classified as `docs-only`; `regression-check.json` reports zero failures and status `baseline` because no previous comparable audit was supplied.
- The first post-roadmap full safe run exposed one roadmap schema mismatch: all Phase 1 features were done but the parent milestone was still `in-progress`. Updating the milestone to the derived `done` status fixed the failure.

### Evidence Table

| ID | Phase | Evidence Required | Status | Evidence |
|----|-------|-------------------|--------|----------|
| V1 | 1 | Focused Python artifact tests pass. | passed | `python3 -m pytest scripts/tests/test_audit_context.py -q` -> `97 passed`. |
| V2 | 1 | Generated artifacts include dashboard and regression summary. | passed | `.cg-docs/token/TOKEN-DASHBOARD.md`; `.cg-docs/token/regression-check.json`; audit command wrote both. |
| V3 | 2 | Prompt/docs checks pass. | passed | `pwsh -NoProfile -Command ". ./tests/Run-Tests.ps1 -File prompt-tools"` -> `1339 passed, 0 failed`. |
| V4 | final | Broader Python tests pass. | passed | `python3 -m pytest scripts/tests scripts/brain/tests scripts/team_brain/tests -q` -> `659 passed, 17 warnings, 5 subtests passed`. |
| V5 | final | Brain rebuild completes. | passed | `./bin/cg-index --brain` -> `530 entities, 2 topics, 213 edges` with existing frontmatter/scanner warnings. |
| V6 | final | Roadmap schema passes after closure. | passed | `pwsh -NoProfile -Command ". ./tests/Run-Tests.ps1 -File roadmap"` -> `100 passed, 0 failed`. |
| V7 | final | Full safe runner passes. | passed | `pwsh -NoProfile -Command ". ./tests/Run-Tests.ps1"` -> `2210 passed, 0 failed`. |
| V8 | final | Roadmap feature is done and linked to this plan. | passed | `roadmap.json` feature status `done`, parent milestone status `done`, plan `.cg-docs/plans/2026-06-23-token-dashboard-regression-checks.md`. |

### Constraints Check

| ID | Constraint | Status | Check |
|----|------------|--------|-------|
| C1 | No token-saving claim without comparable measurements. | passed | Dashboard and docs state observability/baseline semantics only. |
| C2 | No external backend, adapter, or snapshot work. | passed | Diff review: audit artifacts, prompt/docs, tests, roadmap, and evidence only. |
| C3 | Safe Pester runner only. | passed | Pester validation used `tests/Run-Tests.ps1`; no direct unsafe `Invoke-Pester`. |

### Evidence Runs

- `python3 -m pytest scripts/tests/test_audit_context.py -q` -> `97 passed`.
- `python3 scripts/cg_audit_context.py --root . --output-dir .cg-docs/cost --format both --recommendations` -> wrote `.cg-docs/cost/*` and `.cg-docs/token/*`; final regression status `baseline`, failures `0`, warnings `3`, comparison `not_supplied`, source files `90`, estimated source tokens `438352`.
- `pwsh -NoProfile -Command ". ./tests/Run-Tests.ps1 -File prompt-tools"` -> `1339 passed, 0 failed`.
- `python3 -m pytest scripts/tests scripts/brain/tests scripts/team_brain/tests -q` -> `659 passed, 17 warnings, 5 subtests passed`.
- `./bin/cg-index --brain` -> `530 entities, 2 topics, 213 edges`; existing frontmatter/scanner warnings only.
- `pwsh -NoProfile -Command ". ./tests/Run-Tests.ps1 -File roadmap"` -> `100 passed, 0 failed`.
- `pwsh -NoProfile -Command ". ./tests/Run-Tests.ps1"` -> `2210 passed, 0 failed`.

### Remaining Uncertainty

- The regression artifact is a static audit check. It does not instrument live transcript token use or command output size beyond the existing observed/not_observed fields.

### Final Status

Completed.
