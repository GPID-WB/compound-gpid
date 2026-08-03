# Token Dashboard

_Generated: 2026-07-31T12:11:16-04:00@3cc58d7d3ba3_

> Token estimates are heuristic (chars/4) and intended for directional audit use.

This dashboard is an observability artifact, not evidence of token
savings. Treat savings claims as hypotheses until measured with
comparable repository probes.

## Regression Status

- Status: `fail`
- Reason: Deterministic guardrail failures are present.
- Guardrail failures: 4
- Guardrail warnings: 24
- Baseline comparison: not_supplied

## Source Scope

- Source files counted: 150
- Source estimated tokens: 593412
- Workflow rows: 9

## Highest Workflow Budgets

| Workflow | Path | Tokens | Refs | Context Risk | Budget Status |
| --- | --- | --- | --- | --- | --- |
| /cg-work | .github/prompts/cg-work.prompt.md | 5091 | 54 | 0 | warn |
| /cg-review | .github/prompts/cg-review.prompt.md | 5036 | 60 | 0 | warn |
| /cg-brainstorm | .github/prompts/cg-brainstorm.prompt.md | 3798 | 34 | 0 | pass |
| /cg-plan | .github/prompts/cg-plan.prompt.md | 3218 | 23 | 0 | pass |
| /cg-resume | .github/prompts/cg-resume.prompt.md | 3159 | 19 | 0 | pass |

## Context and Warning Summary

- Context loading signals: risk=20, justified=17, targeted=110
- Reviewed warnings: fix=7, accept=14, docs-only=3

## Observability Boundaries

- `baseline`: no comparable baseline was supplied.
- `pass`: comparable baseline supplied and no deterministic guardrail failures were found.
- `fail`: deterministic guardrail failures are present.
- Runtime command-output size and summary size remain explicit observed/not_observed fields.
