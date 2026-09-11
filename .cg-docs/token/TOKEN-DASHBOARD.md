# Token Dashboard

_Generated: 2026-09-03T00:03:52+02:00@1ef12277141b_

> Token estimates are heuristic (chars/4) and intended for directional audit use.

This dashboard is an observability artifact, not evidence of token
savings. Treat savings claims as hypotheses until measured with
comparable repository probes.

## Regression Status

- Status: `fail`
- Reason: Deterministic guardrail failures are present.
- Guardrail failures: 60
- Guardrail warnings: 11
- Baseline comparison: not_supplied

## Source Scope

- Source files counted: 161
- Source estimated tokens: 663963
- Workflow rows: 9

## Highest Workflow Budgets

| Workflow | Path | Tokens | Refs | Context Risk | Budget Status |
| --- | --- | --- | --- | --- | --- |
| /cg-work | .github/prompts/cg-work.prompt.md | 5315 | 57 | 0 | warn |
| /cg-review | .github/prompts/cg-review.prompt.md | 5032 | 58 | 0 | warn |
| /cg-brainstorm | .github/prompts/cg-brainstorm.prompt.md | 3965 | 34 | 0 | pass |
| /cg-plan | .github/prompts/cg-plan.prompt.md | 3507 | 26 | 0 | pass |
| /cg-resume | .github/prompts/cg-resume.prompt.md | 3152 | 19 | 0 | pass |

## Context and Warning Summary

- Context loading signals: risk=9, justified=17, targeted=112
- Reviewed warnings: fix=8, accept=0, docs-only=3

## Observability Boundaries

- `baseline`: no comparable baseline was supplied.
- `pass`: comparable baseline supplied and no deterministic guardrail failures were found.
- `fail`: deterministic guardrail failures are present.
- Runtime command-output size and summary size remain explicit observed/not_observed fields.
