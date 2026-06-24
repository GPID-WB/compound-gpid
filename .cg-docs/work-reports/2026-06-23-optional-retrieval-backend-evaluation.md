# Optional Retrieval Backend Evaluation Execution Report

Plan reference: `.cg-docs/plans/2026-06-23-optional-retrieval-backend-evaluation.md`

Active deviation policy: stored `autonomous`; runtime override `autonomous` from `/cg-work review:auto deviate:auto`.

## Run: 2026-06-23

Status: completed

### Completed Steps/Phases

- Phase 1: added `.github/shared/retrieval-backends.json` as an evaluation-only backend registry.
- Phase 2: added `docs/retrieval-backends.md`, reference/workflow docs, and focused Python registry tests.
- Phase 3: linked roadmap Phase 2.2 as done and recorded review/evidence artifacts.

### Deviations

- Kept this phase strictly evaluation-only. No runtime backend switch, dependency, vector store, embedding model, snapshot, or external service was introduced.

### Accepted Exceptions

- External retrieval remains explicitly deferred. The registry includes it only as a candidate whose status is `deferred`, with `default_enabled: false` and required privacy/offline gates.

### Evidence Table

| ID | Phase | Evidence Required | Status | Evidence |
|----|-------|-------------------|--------|----------|
| V1 | 1 | Retrieval registry tests pass. | passed | `python3 -m pytest scripts/tests/test_retrieval_backends.py -q` -> `5 passed`. |
| V2 | 2 | Prompt/docs checks pass. | passed | `pwsh -NoProfile -Command ". ./tests/Run-Tests.ps1 -File prompt-tools"` -> `1339 passed, 0 failed`. |
| V3 | final | Broader Python tests pass. | passed | `python3 -m pytest scripts/tests scripts/brain/tests scripts/team_brain/tests -q` -> `669 passed, 17 warnings, 5 subtests passed`. |
| V4 | final | Full safe runner passes. | passed | `pwsh -NoProfile -Command ". ./tests/Run-Tests.ps1"` -> `2210 passed, 0 failed`. |
| V5 | final | Roadmap feature is done and linked to this plan. | passed | `roadmap.json` feature status `done`, plan `.cg-docs/plans/2026-06-23-optional-retrieval-backend-evaluation.md`. |
| V6 | final | Brain and token audit artifacts are refreshed. | passed | `./bin/cg-index --brain` -> `538 entities, 2 topics, 216 edges`; audit -> `baseline`, failures `0`, warnings `3`, estimated source tokens `443153`. |

### Constraints Check

| ID | Constraint | Status | Check |
|----|------------|--------|-------|
| C1 | No optional backend is default-enabled. | passed | Registry tests assert only `native-brain-query` is enabled. |
| C2 | No external service, vector DB, snapshot, or runtime switch is implemented. | passed | Diff review: registry/docs/tests/evidence only. |
| C3 | Safe Pester runner only. | passed | Pester validation used `tests/Run-Tests.ps1`; no direct unsafe `Invoke-Pester`. |

### Evidence Runs

- `python3 -m pytest scripts/tests/test_retrieval_backends.py -q` -> `5 passed`.
- `pwsh -NoProfile -Command ". ./tests/Run-Tests.ps1 -File prompt-tools"` -> `1339 passed, 0 failed`.
- `python3 -m pytest scripts/tests scripts/brain/tests scripts/team_brain/tests -q` -> `669 passed, 17 warnings, 5 subtests passed`.
- `pwsh -NoProfile -Command ". ./tests/Run-Tests.ps1"` -> `2210 passed, 0 failed`.
- `./bin/cg-index --brain` -> `538 entities, 2 topics, 216 edges`; existing frontmatter/scanner warnings only.
- `python3 scripts/cg_audit_context.py --root . --output-dir .cg-docs/cost --format both --recommendations` -> final regression status `baseline`, failures `0`, warnings `3`, comparison `not_supplied`, source files `92`, estimated source tokens `443153`.

### Remaining Uncertainty

- The registry is not a quality benchmark. Any future backend still needs measured retrieval-quality and token-budget evidence before adoption.

### Final Status

Completed.
