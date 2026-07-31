# Token Efficiency Advice

_Generated: 2026-07-31T10:58:19-04:00@c80f66e6828f_

> Token estimates are heuristic (chars/4) and intended for directional audit use.

## Current Audit

- Guardrail failures: 0
- Guardrail warnings: 4
- Warning classification: fix=1, accept=0, docs-only=3

## Recommended Actions

- **high / context-loading**: Reduce prompt warnings classified as fix. Evidence: 1 warning(s) classified as fix: .github/prompts/cg-work.prompt.md. Advice: Slim the named entrypoints or convert broad reads to staged, targeted, on-demand loading.
- **high / entrypoint-size**: Slim /cg-work. Evidence: .github/prompts/cg-work.prompt.md is estimated at 5117 tokens. Advice: Keep safety-critical routing inline, but move rarely used workflow detail behind explicit skills or targeted contracts.
- **medium / project-context**: Use query-first project context. Evidence: context=17750, brain=79628, brain_index=175470 estimated tokens. Advice: Use the Brain meta-index and targeted sections; avoid loading full context, Brain partitions, or brain-index records by default.
- **low / documentation**: Treat docs size as opt-in cost. Evidence: docs category is estimated at 75172 tokens. Advice: Do not optimize docs for runtime unless prompts or skills load them automatically.
- **medium / review-routing**: Match review depth to risk. Evidence: /cg-review dispatch burden is conditional with 10 referenced agents. Advice: Use light or standard reviews for low-risk changes; reserve full review for broad, risky, or explicitly requested checks.
- **low / model-advisory**: Choose capability and effort by process stage. Evidence: The shared advisory contract provides five stage profiles and dated examples. Advice: Prioritize effective completion first, then choose an economical option only when the task is bounded and the user considers it appropriate.

## Warning Review

- **fix** `.github/prompts/cg-work.prompt.md`: High-frequency entrypoints directly affect routine token cost. Action: Slim the prompt or split only with an explicit caller load point.
- **docs-only** `docs/philosophy.md`: Documentation wording can mention broad artifacts without causing runtime prompt loading. Action: Keep as documentation unless wording misleads users.
- **docs-only** `docs/reference.md`: Documentation wording can mention broad artifacts without causing runtime prompt loading. Action: Keep as documentation unless wording misleads users.
- **docs-only** `docs/workflow.md`: Documentation wording can mention broad artifacts without causing runtime prompt loading. Action: Keep as documentation unless wording misleads users.
