---
date: 2026-06-23
depth: light
parent-review: .cg-docs/reviews/2026-06-12-goal-driven-execution-review.md
type: verification
findings:
  P2.1: fixed
  P2.2: fixed
---

## Review Report

**Review mode**: light (verify pass)
**Parent review**: `.cg-docs/reviews/2026-06-12-goal-driven-execution-review.md`
**Review scope**: current Phase 1.1 workflow token baseline branch, with emphasis on:

- `scripts/cg_audit_context.py`
- `scripts/tests/test_audit_context.py`
- `scripts/brain/scanner.py`
- `scripts/brain/tests/test_scanner.py`
- `.cg-docs/token/*`
- `.github/prompts/cg-token-audit.prompt.md`
- `.github/skills/cg-skill-wiki/SKILL.md`
- `docs/reference.md`
- `docs/_wiki.yml`
- `tests/prompt-tools.Tests.ps1`
- `tests/wiki.Tests.ps1`

**Findings**: 2 (P0: 0, P1: 0, P2: 2, P3: 0)

### P2 - IMPORTANT (should fix)

- **[P2.1]** [cg-code-quality] `scripts/brain/scanner.py:37` - new `.cg-docs/token/` generated Markdown artifacts are not registered with the brain scanner.
  **Why**: Phase 1.1 adds generated Markdown artifacts under `.cg-docs/token/`, including `TOKEN-BUDGET.md` and `large-context-warnings.md`. `scan_all()` warns on every unknown top-level `.cg-docs/` directory unless the directory is registered in `_DIR_TO_TYPE` with either an entity type or `None`. A local verification run of `python3 scripts/cg_index.py --brain --root .` emitted two warnings for `Unknown .cg-docs/ subdirectory 'token'`. These token artifacts are generated audit outputs, so they should either be deliberately indexed or deliberately skipped without warning. Leaving the new directory unknown adds warning noise to routine Knowledge Brain rebuilds and makes validation output look suspect even when the audit artifacts are expected.
  **Fix**: Add `token: None` to `_DIR_TO_TYPE` so generated token reports are intentionally skipped, and add scanner tests proving `.cg-docs/token/*.md` is skipped without an unknown-directory warning. Consider the same treatment for pre-existing generated `.cg-docs/cost/` warnings in a separate or adjacent cleanup if that is within scope.

- **[P2.2]** [cg-testing] `scripts/cg_audit_context.py:2504` - the documented `--no-token-artifacts` compatibility path has no direct regression coverage.
  **Why**: The implementation exposes `--no-token-artifacts` to preserve legacy `.cg-docs/cost/`-only behavior, and `docs/reference.md` documents it as the way to run without additive `.cg-docs/token/` outputs. Existing tests cover default token artifact emission (`scripts/tests/test_audit_context.py:1040`) and custom token output location in the integration run (`scripts/tests/test_audit_context.py:587`), but there is no assertion that `--no-token-artifacts` suppresses all five `.cg-docs/token/` artifacts while still writing the legacy `context-audit.json`. Because backward compatibility is a stated Phase 1.1 guardrail, this side-effect boundary should be covered before execution.
  **Fix**: Add a pytest case invoking `audit.main(["--root", <fixture-root>, "--output-dir", <legacy-dir>, "--format", "json", "--no-token-artifacts"])`, then assert legacy `.cg-docs/cost` output exists and `.cg-docs/token/TOKEN-BUDGET.md`, `token-audit.json`, `context-map.json`, `workflow-costs.csv`, and `large-context-warnings.md` are absent.

### Passed

- **@cg-code-quality**: The workflow-token baseline extends `scripts/cg_audit_context.py` rather than introducing a parallel analyzer, keeps `.cg-docs/cost/` outputs additive-compatible, and keeps token-saving claims framed as measurements/hypotheses.
- **@cg-testing**: Prior validation for this branch passed:
  - `python3 -m pytest scripts/tests/test_audit_context.py -q` -> 91 passed.
  - `python3 -m py_compile scripts/cg_audit_context.py` -> passed.
  - `python3 scripts/cg_audit_context.py --root . --output-dir .cg-docs/cost --format both --recommendations` -> wrote legacy cost reports and five token artifacts.
  - Token artifact parse check -> 9 workflow rows for the required `/cg-*` workflows.
  - Guarded Pester through `tests/Run-Tests.ps1` -> 2200 passed, 0 failed, `filteredFiles: null`.
  - `git diff --check` -> clean.

### Verification Notes

- `mode:verify` selected the most recent eligible parent review by the prompt rule. The parent review is not a current Phase 1.1 review, so no current-file issue was suppressed as already fixed.
- The previous `docs/reference.md` managed-section conflict appears addressed: `docs/_wiki.yml` now registers the `shell-commands` managed section, `docs/reference.md` wraps the shell-command table in `cg:auto:shell-commands`, and `tests/wiki.Tests.ps1` covers both.
- P0/P1 and cross-file breakage were not suppressed.
