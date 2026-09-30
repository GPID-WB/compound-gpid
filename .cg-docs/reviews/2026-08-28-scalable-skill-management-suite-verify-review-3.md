---
date: 2026-09-08
depth: light
parent-review: .cg-docs/reviews/2026-08-28-scalable-skill-management-suite-review.md
type: verification
findings:
  P1.1: skipped
  P1.2: skipped
  P1.3: skipped
  P1.4: skipped
  P1.5: skipped
  P1.6: skipped
  P2.1: skipped
  P2.2: fixed
  P2.3: fixed
---

# Verification Review: Unified /cg-light-work Command

## Review Context

- **Review mode**: verify (light-only)
- **Parent review**: `.cg-docs/reviews/2026-08-28-scalable-skill-management-suite-review.md`
- **Current Plan**: `.cg-docs/plans/2026-09-04-cg-light-work-unified-small-task-workflow.md`
- **Files reviewed**: 48 changed and untracked paths
- **Reviewers**: `@cg-code-quality`, `@cg-testing`
- **Suppression**: none; the parent review's fixed blocks are unrelated to this change. P0/P1 and cross-file breakage remained reportable.
- **Findings**: 9 (P0: 0, P1: 6, P2: 3, P3: 0)

## P0 - Blocking

No P0 findings.

## P1 - Critical

- **[P1.1]** [cg-code-quality, cg-testing] `.github/prompts/cg-work.prompt.md:34` - Free-text tasks can select an unrelated recent Plan.
  **Why**: The command selects the most recent Plan before it parses the task payload. An inline task can therefore execute an unrelated Plan instead of returning the required `/cg-light-work` redirect.
  **Fix**: Parse intent first. For task text, permit only an explicit or user-confirmed keyword match; otherwise return `/cg-light-work -- <verbatim task>`. Add matching, nonmatching, absent, and ambiguous Plan tests.

- **[P1.2]** [cg-code-quality] `.github/prompts/cg-light-work.prompt.md:79` - CG-only installations receive an unavailable CR route.
  **Why**: H2 always routes to `/cr-brainstorm`, but a CG-only projection includes `/cg-light-work` and excludes CR commands.
  **Fix**: Check the active suite or capability manifest. Route to `/cr-brainstorm` only when CR is active; otherwise use the capability router's structured hard stop and remedy. Add a CG-only leak test.

- **[P1.3]** [cg-code-quality] `.github/prompts/cg-light-work.prompt.md:62` - The snapshot assumes `.tmp/` is ignored.
  **Why**: The command writes its initial snapshot before it confirms that the exact run directory is ignored. In a consumer repository without that rule, the snapshot changes the status it is meant to measure.
  **Fix**: Require `git check-ignore` for the exact run directory before writing and stop with a setup remedy if the directory is not ignored. Add a consumer fixture without a `.tmp/` rule.

- **[P1.4]** [cg-code-quality, cg-testing] `.github/prompts/cg-light-work.prompt.md:12` - File permissions conflict with required stage writes.
  **Why**: The allowlist does not authorize preapproval branch/stash mutations, derived Plan rendering, or consent-approved Solution, Brain, context, wiki, and Team Brain effects.
  **Fix**: Add narrow stage-specific permissions for branch safety, derived rendering, and post-convergence compounding. Distinguish prohibited Git push from an approved Team Brain push. Add permission-versus-stage tests.

- **[P1.5]** [cg-testing] `.github/prompts/cg-light-work.prompt.md:166` - Source edits can begin before the Work Report and active state exist.
  **Why**: Stage 3 permits source edits after Plan validation, while Stage 4 creates durable execution state later.
  **Fix**: Move the source-edit boundary after Work Report creation, Plan linking, and initial active-state creation. Assert the complete order.

- **[P1.6]** [cg-testing] `.github/prompts/cg-light-work.prompt.md:183` - The command omits mandatory Pester safety mechanics.
  **Why**: Stage 5 can run PowerShell tests but does not require `cg-skill-pester-safety`, `execution_subagent`, `tests/Run-Tests.ps1`, `tests/last-run.json`, or the direct `Invoke-Pester` prohibition.
  **Fix**: Add the canonical conditional Pester workflow and crash-prevention contract tests for `/cg-light-work`.

## P2 - Important

- **[P2.1]** [cg-code-quality] `.github/shared/goal-execution.contract.md:173` - Light Work is absent from operational lifecycle clauses.
  **Why**: The introduction permits `/cg-light-work`, but report identity, collision, resume, strict evidence, and active-state completion clauses still assign key duties only to `/cg-work`.
  **Fix**: Define a shared executor term or name both workflows in every applicable operational clause. Add content tests for the lifecycle clauses.

- **[P2.2]** [cg-code-quality] `scripts/cg_audit_context.py:1106` - Registry validation accepts duplicate command identities.
  **Why**: Duplicate `workflow` values are accepted even though derived maps use `workflow` as a key, which can silently remove one guarded path.
  **Fix**: Validate unique non-empty string values for `workflow_id`, `workflow`, and `path` before constructing derived maps. Add a duplicate-workflow test.

- **[P2.3]** [cg-code-quality] `tests/prompt-tools.Tests.ps1:1630` - Safety-gate tests do not verify exact limits.
  **Why**: S1-S10 row-label tests remain green if a numerical threshold or route is weakened.
  **Fix**: Parse each row and compare its normalized signal, route, and exact limit to a table-driven expected value.

## Passed Checks

- Python: 280 passed, 17 skipped.
- Pester full gate: 2,863 passed, 0 failed, 2 skipped, unfiltered.
- Docs automation: 28 passed; generated docs current.
- Module ownership and dependency validation passed.
- `git diff --check` passed.

## Incomplete Reviews

- None. Both required reviewers returned usable output.
