# Token Dashboard

_Generated: 2026-06-23T14:16:06_

> Token estimates are heuristic (chars/4) and intended for directional audit use.

This dashboard is an observability artifact, not evidence of token
savings. Treat savings claims as hypotheses until measured with
comparable repository probes.

## Regression Status

- Status: `baseline`
- Reason: No baseline comparison was supplied; current audit is the baseline.
- Guardrail failures: 0
- Guardrail warnings: 3
- Baseline comparison: not_supplied

## Source Scope

- Source files counted: 90
- Source estimated tokens: 440352
- Workflow rows: 9

## Highest Workflow Budgets

| Workflow | Path | Tokens | Refs | Context Risk | Budget Status |
| --- | --- | --- | --- | --- | --- |
| /cg-work | .github/prompts/cg-work.prompt.md | 5000 | 54 | 0 | pass |
| /cg-review | .github/prompts/cg-review.prompt.md | 4739 | 56 | 0 | pass |
| /cg-brainstorm | .github/prompts/cg-brainstorm.prompt.md | 3798 | 34 | 0 | pass |
| /cg-plan | .github/prompts/cg-plan.prompt.md | 3218 | 23 | 0 | pass |
| /cg-resume | .github/prompts/cg-resume.prompt.md | 3159 | 19 | 0 | pass |

## Context and Warning Summary

- Context loading signals: risk=3, justified=20, targeted=102
- Reviewed warnings: fix=0, accept=0, docs-only=3

## Observability Boundaries

- `baseline`: no comparable baseline was supplied.
- `pass`: comparable baseline supplied and no deterministic guardrail failures were found.
- `fail`: deterministic guardrail failures are present.
- Runtime command-output size and summary size remain explicit observed/not_observed fields.
