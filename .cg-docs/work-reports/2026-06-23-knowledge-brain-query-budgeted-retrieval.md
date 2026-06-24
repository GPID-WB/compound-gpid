# Knowledge Brain Query and Budgeted Retrieval Execution Report

Plan reference: `.cg-docs/plans/2026-06-23-knowledge-brain-query-budgeted-retrieval.md`

Active deviation policy: stored `autonomous`; runtime override `autonomous` from `/cg-work review:auto deviate:auto`.

## Run: 2026-06-23

Status: completed

### Completed Steps/Phases

- Phase 1: added deterministic local Brain query core in `scripts/brain/query.py`.
- Phase 2: wired `cg-index query` CLI with JSON/Markdown formats, budget validation, and legacy mode preservation.
- Phase 3: updated `cg-skill-brain-query`, prompt contract tests, and docs to prefer budgeted query with `BRAIN.md` fallback.
- Phase 4: ran validation, review, verify, and compounding records; linked roadmap feature as done.

### Deviations

- Implemented query warning capture after smoke testing showed raw Brain build warnings would otherwise flood stderr. This stays within scope and improves token-bounded output.
- Enforced budget using rendered JSON/Markdown estimates rather than only snippet estimates after self-review found the initial estimate undercounted final output.

### Accepted Exceptions

- None.

### Evidence Table

| ID | Phase | Evidence Required | Status | Evidence |
|----|-------|-------------------|--------|----------|
| V1 | 1 | Query core ranks relevant Brain artifacts and respects token budget. | passed | `python3 -m pytest scripts/brain/tests/test_query.py -q` passed `14 passed`; real-repo smoke showed JSON/Markdown estimates under a 600-token budget. |
| V2 | 2 | `cg-index query` accepts valid args, rejects invalid args, and renders JSON/Markdown. | passed | CLI tests in `test_query.py`; representative JSON and Markdown commands passed. |
| V3 | 3 | `cg-skill-brain-query` prefers `cg-index query` and preserves `BRAIN.md` fallback/no-wholesale rules. | passed | `pwsh -NoProfile -Command ". ./tests/Run-Tests.ps1 -File prompt-tools"` passed `1330/1330`. |
| V4 | 3 | Query benchmarks select expected prior artifacts under budget. | passed | Fixture benchmark tests in `scripts/brain/tests/test_query.py` passed. |
| V5 | final | Existing Brain generation and legacy `cg-index` modes remain compatible. | passed | `python3 -m pytest scripts/brain/tests scripts/tests scripts/team_brain/tests -q` passed `640 passed, 5 subtests passed`. |
| V6 | final | Repository Pester safe runner passes. | passed | `pwsh -NoProfile -Command ". ./tests/Run-Tests.ps1"` passed `2201/2201`, `filteredFiles: null`, `ranAt: 2026-06-23T17:21:34Z`. |
| V7 | final | No external retrieval backend, vector service, or token-saving claim is introduced. | passed | Diff review: stdlib-only local query, no network calls, docs state heuristic retrieval is not savings evidence. |

### Constraints Check

| ID | Constraint | Status | Check |
|----|------------|--------|-------|
| C1 | Keep retrieval stdlib/native and local. | passed | `scripts/brain/query.py` uses stdlib and existing Brain entities only. |
| C2 | Preserve generated Brain artifacts and `cg-index --brain`. | passed | Existing Brain tests and safe runner passed. |
| C3 | Preserve manual `BRAIN.md` fallback in the skill. | passed | Skill wording and Pester contract test cover fallback. |
| C4 | Do not implement Phase 1.3+ wrappers/backends/snapshots. | passed | No command-output wrappers, adapters, optional backends, or snapshots added. |
| C5 | Treat token estimates as heuristic and non-savings evidence. | passed | Query warnings and docs include the no-savings disclaimer. |
| C6 | Preserve Pester safety. | passed | Safe runner only; no unsafe `Invoke-Pester` recipes added. |
| C7 | Preserve roadmap write discipline. | passed | Roadmap feature was linked/updated through the local roadmap manager contract. |

### Evidence Runs

- `python3 -m pytest scripts/brain/tests/test_query.py -q` -> `14 passed`.
- `python3 -m pytest scripts/brain/tests/test_query.py scripts/brain/tests/test_scanner.py scripts/brain/tests/test_extractor.py scripts/brain/tests/test_renderer.py -q` -> `147 passed`.
- `python3 -m pytest scripts/brain/tests scripts/tests scripts/team_brain/tests -q` -> `640 passed, 5 subtests passed`.
- `python3 -m py_compile scripts/cg_index.py scripts/brain/query.py` -> passed.
- `python3 scripts/cg_index.py query --root . --intent plan --query "workflow token baseline" --budget 600 --format json` -> valid JSON, stderr length `0`.
- `python3 scripts/cg_index.py query --root . --intent review --query "Pester safe runner" --changed-file tests/Run-Tests.ps1 --budget 600 --format md` -> bounded Markdown output.
- `pwsh -NoProfile -Command ". ./tests/Run-Tests.ps1 -File prompt-tools"` -> `1330 passed`.
- `pwsh -NoProfile -Command ". ./tests/Run-Tests.ps1"` -> `2201 passed, 0 failed`.
- `python3 scripts/cg_index.py --brain --root .` -> regenerated Brain artifacts with `514 entities`, `2 topics`, and `206 edges`.
- Final query smoke: `cg-index query` JSON output parsed successfully, stderr length `0`, estimated output `454` under a `600` token budget.
- `git diff --check` -> passed.

### Remaining Uncertainty

- Query ranking is deterministic keyword scoring, not semantic/vector retrieval. That is intentional for Phase 1.2; optional backends remain out of scope.
- `cg-index query` captures and summarizes existing Brain build warnings in the payload. Cleaning older warning sources such as unknown `.cg-docs/inbox` or `.cg-docs/work-reports` classifications is separate maintenance unless later phases require it.

### Final Status

Completed.
