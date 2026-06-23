# Token Efficiency Advice

_Generated: 2026-06-23T14:09:10_

> Token estimates are heuristic (chars/4) and intended for directional audit use.

## Current Audit

- Guardrail failures: 0
- Guardrail warnings: 3
- Warning classification: fix=0, accept=0, docs-only=3

## Recommended Actions

- **medium / project-context**: Use query-first project context. Evidence: context=16141, brain=70822, brain_index=156783 estimated tokens. Advice: Use the Brain meta-index and targeted sections; avoid loading full context, Brain partitions, or brain-index records by default.
- **low / documentation**: Treat docs size as opt-in cost. Evidence: docs category is estimated at 52269 tokens. Advice: Do not optimize docs for runtime unless prompts or skills load them automatically.
- **medium / review-routing**: Match review depth to risk. Evidence: /cg-review dispatch burden is conditional with 10 referenced agents. Advice: Use light or standard reviews for low-risk changes; reserve full review for broad, risky, or explicitly requested checks.
- **low / model-selection**: Use cheaper models for planning and advisory work when quality allows. Evidence: Model governance keeps ordinary planning prompts on the model picker. Advice: Use stronger models for implementation, high-risk review, and architecture; use lighter models for simple planning or documentation passes.

## Warning Review

- **docs-only** `docs/context-files.md`: Documentation wording can mention broad artifacts without causing runtime prompt loading. Action: Keep as documentation unless wording misleads users.
- **docs-only** `docs/reference.md`: Documentation wording can mention broad artifacts without causing runtime prompt loading. Action: Keep as documentation unless wording misleads users.
- **docs-only** `docs/workflow.md`: Documentation wording can mention broad artifacts without causing runtime prompt loading. Action: Keep as documentation unless wording misleads users.
