---
date: 2026-06-22
depth: light
parent-review: .cg-docs/reviews/2026-06-12-goal-driven-execution-review.md
type: verification
findings:
  P2.1: fixed
---

## Review Report

**Review mode**: light (verify pass)
**Parent review**: `.cg-docs/reviews/2026-06-12-goal-driven-execution-review.md`
**Files reviewed**: 4 current Phase 1 token-baseline files:

- `scripts/cg_audit_context.py`
- `scripts/tests/test_audit_context.py`
- `.cg-docs/plans/2026-06-22-workflow-token-baseline.md`
- `.cg-docs/work-reports/2026-06-22-workflow-token-baseline.md`

Pre-existing dirty files were not treated as part of this review scope:
`.cg-docs/archive/charter-history.md`, `compound-gpid.md`, and `roadmap.json`.

**Findings**: 1 (P0: 0, P1: 0, P2: 1, P3: 0)

### P2 - IMPORTANT (should fix)

- **[P2.1]** [cg-code-quality/cg-testing] `scripts/cg_audit_context.py:77` and `scripts/cg_audit_context.py:84` - workflow telemetry undercounts real file reads and tool references.
  **Why**: Phase 1.1 is supposed to baseline deterministically observable workflow context, including files read and MCP/tool usage. The new telemetry fields are named `file_references`, `likely_file_reads`, and `tool_references`, but they still use the older narrow `FILE_REF_RE` and `TOOL_REF_RE`. As a result, real prompt reads such as `.github/shared/context-loading.contract.md`, `.github/shared/goal-execution.contract.md`, and `.github/shared/review-routing.contract.md` are omitted, and `/cg-work` reports `tool_references=[]` even though it contains `execution_subagent` test-runner blocks. A local check against the generated report showed `/cg-work` file references limited to `compound-gpid*` and `roadmap.json` despite explicit shared-contract load/read instructions.
  **Fix**: Expand workflow telemetry extraction separately from the legacy context-risk reference regex. Add a repo-relative path extractor for quoted/backticked paths such as `.github/shared/*.md`, `.github/prompts/*.md`, `.github/skills/**/SKILL.md`, `tests/Run-Tests.ps1`, and `.cg-docs/plans/*.md`, while keeping output artifacts excluded from source-token totals. Expand tool detection to include `execution_subagent` and other deterministic workflow tool/MCP names used in prompts. Add tests using real or fixture prompt text proving `/cg-work` captures shared contract paths and `execution_subagent`.

### Passed

- **@cg-testing**: Existing validation passed:
  - `python3 -m pytest scripts/tests/test_audit_context.py -q` -> 87 passed.
  - `. ./tests/Run-Tests.ps1` through PowerShell safe runner -> 2194 passed, 0 failed, `filteredFiles: null`.
- **@cg-code-quality**: The new registry shape is stable, unique, and keeps legacy benchmark output available. No parallel analyzer was introduced.

### Verification Notes

- `mode:verify` selected the most recent eligible parent review by the prompt rule. The current changed files are Phase 1 token-baseline work, not direct edits from the parent review; therefore the suppression policy did not suppress the new P2 finding.
- P0/P1 and cross-file breakage were not suppressed.
