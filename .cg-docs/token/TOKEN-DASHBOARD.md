# Token Dashboard

_Generated: 2026-07-31T10:58:19-04:00@c80f66e6828f_

> Token estimates are heuristic (chars/4) and intended for directional audit use.

This dashboard is an observability artifact, not evidence of token
savings. Treat savings claims as hypotheses until measured with
comparable repository probes.

## Regression Status

- Status: `baseline`
- Reason: No baseline comparison was supplied; current audit is the baseline.
- Guardrail failures: 0
- Guardrail warnings: 4
- Baseline comparison: not_supplied

## Source Scope

- Source files counted: 118
- Source estimated tokens: 495800
- Workflow rows: 9

## Highest Workflow Budgets

| Workflow | Path | Tokens | Refs | Context Risk | Budget Status |
| --- | --- | --- | --- | --- | --- |
| /cg-work | .github/prompts/cg-work.prompt.md | 5117 | 56 | 0 | warn |
| /cg-review | .github/prompts/cg-review.prompt.md | 4889 | 58 | 0 | pass |
| /cg-brainstorm | .github/prompts/cg-brainstorm.prompt.md | 3798 | 34 | 0 | pass |
| /cg-plan | .github/prompts/cg-plan.prompt.md | 3345 | 25 | 0 | pass |
| /cg-resume | .github/prompts/cg-resume.prompt.md | 3153 | 19 | 0 | pass |

## Context and Warning Summary

- Context loading signals: risk=3, justified=17, targeted=102
- Reviewed warnings: fix=1, accept=0, docs-only=3

## Observability Boundaries

- `baseline`: no comparable baseline was supplied.
- `pass`: comparable baseline supplied and no deterministic guardrail failures were found.
- `fail`: deterministic guardrail failures are present.
- Runtime command-output size and summary size remain explicit observed/not_observed fields.
