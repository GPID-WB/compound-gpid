# Workflow Token Budget Baseline

_Generated: 2026-07-23T18:00:10_

> Token estimates are heuristic (chars/4) and intended for directional audit use.

This is a baseline artifact, not evidence of token savings. Treat any
token-saving claim as a hypothesis until measured with comparable
repository probes.

## Source Scope

- Source files counted: 95
- Source estimated tokens: 445697
- Workflow rows: 9
- Workflows with prompt source observed: 9
- Workflows without prompt source observed: 0

Generated `.cg-docs/cost/` and `.cg-docs/token/` outputs are audit
artifacts. They are not part of the normal workflow source-pressure scan.

## Workflow Budgets

| Workflow | Path | Tokens | Refs | Context Risk | Dispatch | Command Output | Summary |
| --- | --- | --- | --- | --- | --- | --- | --- |
| /cg-brainstorm | .github/prompts/cg-brainstorm.prompt.md | 3798 | 34 | 0 | limited | not_observed | not_observed |
| /cg-plan | .github/prompts/cg-plan.prompt.md | 3218 | 23 | 0 | limited | not_observed | not_observed |
| /cg-work | .github/prompts/cg-work.prompt.md | 5000 | 54 | 0 | conditional | not_observed | not_observed |
| /cg-review | .github/prompts/cg-review.prompt.md | 4739 | 56 | 0 | conditional | not_observed | not_observed |
| /cg-fix-triage | .github/prompts/cg-fix-triage.prompt.md | 2100 | 20 | 0 | none | not_observed | not_observed |
| /cg-compound | .github/prompts/cg-compound.prompt.md | 2404 | 28 | 0 | limited | not_observed | not_observed |
| /cg-resume | .github/prompts/cg-resume.prompt.md | 3159 | 19 | 0 | limited | not_observed | not_observed |
| /cg-diagnose | .github/prompts/cg-diagnose.prompt.md | 2647 | 16 | 0 | none | not_observed | not_observed |
| /cg-token-audit | .github/prompts/cg-token-audit.prompt.md | 790 | 14 | 0 | none | not_observed | not_observed |

## Observability Boundaries

- `observed`: measured from repository source files.
- `partially_observed`: statically visible in prompt text, but actual
  runtime behavior depends on the execution path.
- `not_observed`: not instrumented in Phase 1.1 and not inferred.

Command-output size and summary size are intentionally `not_observed`
until command-output summary wrappers or transcript instrumentation exist.
