# Token Efficiency Advice

_Generated: 2026-09-03T00:03:52+02:00@1ef12277141b_

> Token estimates are heuristic (chars/4) and intended for directional audit use.

## Current Audit

- Guardrail failures: 60
- Guardrail warnings: 11
- Warning classification: fix=8, accept=0, docs-only=3

## Recommended Actions

- **high / guardrails**: Fix audit failures before optimizing cost. Evidence: 60 guardrail failure(s) are present. Advice: Resolve failures first; they are stronger than advisory token recommendations.
- **high / context-loading**: Reduce prompt warnings classified as fix. Evidence: 8 warning(s) classified as fix: .github/prompts/cg-release.prompt.md, .github/prompts/cg-review.prompt.md, .github/prompts/cg-work.prompt.md, .github/prompts/cr-brainstorm.prompt.md, .github/prompts/cr-plan.prompt.md, .github/prompts/cr-work.prompt.md. Advice: Slim the named entrypoints or convert broad reads to staged, targeted, on-demand loading.
- **high / entrypoint-size**: Slim /cg-work. Evidence: .github/prompts/cg-work.prompt.md is estimated at 5315 tokens. Advice: Keep safety-critical routing inline, but move rarely used workflow detail behind explicit skills or targeted contracts.
- **high / entrypoint-size**: Slim /cg-review. Evidence: .github/prompts/cg-review.prompt.md is estimated at 5032 tokens. Advice: Keep safety-critical routing inline, but move rarely used workflow detail behind explicit skills or targeted contracts.
- **medium / project-context**: Use query-first project context. Evidence: context=19049, brain=97862, brain_index=218330 estimated tokens. Advice: Use the Brain meta-index and targeted sections; avoid loading full context, Brain partitions, or brain-index records by default.
- **low / documentation**: Treat docs size as opt-in cost. Evidence: docs category is estimated at 89610 tokens. Advice: Do not optimize docs for runtime unless prompts or skills load them automatically.
- **medium / review-routing**: Match review depth to risk. Evidence: /cg-review dispatch burden is conditional with 10 referenced agents. Advice: Use light or standard reviews for low-risk changes; reserve full review for broad, risky, or explicitly requested checks.
- **low / model-selection**: Use cheaper models for planning and advisory work when quality allows. Evidence: Model governance keeps ordinary planning prompts on the model picker. Advice: Use stronger models for implementation, high-risk review, and architecture; use lighter models for simple planning or documentation passes.

## Warning Review

- **fix** `.github/prompts/cg-review.prompt.md`: High-frequency entrypoints directly affect routine token cost. Action: Slim the prompt or split only with an explicit caller load point.
- **fix** `.github/prompts/cg-work.prompt.md`: High-frequency entrypoints directly affect routine token cost. Action: Slim the prompt or split only with an explicit caller load point.
- **fix** `.github/prompts/cg-release.prompt.md`: Prompt-level broad context warning needs targeted wording unless proven maintenance-only. Action: Narrow the read or add an explicit accepted rationale.
- **fix** `.github/prompts/cg-release.prompt.md`: Prompt-level broad context warning needs targeted wording unless proven maintenance-only. Action: Narrow the read or add an explicit accepted rationale.
- **fix** `.github/prompts/cg-release.prompt.md`: Prompt-level broad context warning needs targeted wording unless proven maintenance-only. Action: Narrow the read or add an explicit accepted rationale.
- **fix** `.github/prompts/cr-brainstorm.prompt.md`: Prompt-level broad context warning needs targeted wording unless proven maintenance-only. Action: Narrow the read or add an explicit accepted rationale.
- **fix** `.github/prompts/cr-plan.prompt.md`: Prompt-level broad context warning needs targeted wording unless proven maintenance-only. Action: Narrow the read or add an explicit accepted rationale.
- **fix** `.github/prompts/cr-work.prompt.md`: Prompt-level broad context warning needs targeted wording unless proven maintenance-only. Action: Narrow the read or add an explicit accepted rationale.
- **docs-only** `docs/philosophy.md`: Documentation wording can mention broad artifacts without causing runtime prompt loading. Action: Keep as documentation unless wording misleads users.
- **docs-only** `docs/reference.md`: Documentation wording can mention broad artifacts without causing runtime prompt loading. Action: Keep as documentation unless wording misleads users.
- **docs-only** `docs/workflow.md`: Documentation wording can mention broad artifacts without causing runtime prompt loading. Action: Keep as documentation unless wording misleads users.
