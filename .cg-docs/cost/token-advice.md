# Token Efficiency Advice

_Generated: 2026-07-31T12:11:16-04:00@3cc58d7d3ba3_

> Token estimates are heuristic (chars/4) and intended for directional audit use.

## Current Audit

- Guardrail failures: 4
- Guardrail warnings: 24
- Warning classification: fix=7, accept=14, docs-only=3

## Recommended Actions

- **high / guardrails**: Fix audit failures before optimizing cost. Evidence: 4 guardrail failure(s) are present. Advice: Resolve failures first; they are stronger than advisory token recommendations.
- **high / context-loading**: Reduce prompt warnings classified as fix. Evidence: 7 warning(s) classified as fix: .github/prompts/cg-review.prompt.md, .github/prompts/cg-work.prompt.md, .github/prompts/cr-brainstorm.prompt.md, .github/prompts/cr-plan.prompt.md, .github/prompts/cr-work.prompt.md. Advice: Slim the named entrypoints or convert broad reads to staged, targeted, on-demand loading.
- **high / entrypoint-size**: Slim /cg-work. Evidence: .github/prompts/cg-work.prompt.md is estimated at 5091 tokens. Advice: Keep safety-critical routing inline, but move rarely used workflow detail behind explicit skills or targeted contracts.
- **high / entrypoint-size**: Slim /cg-review. Evidence: .github/prompts/cg-review.prompt.md is estimated at 5036 tokens. Advice: Keep safety-critical routing inline, but move rarely used workflow detail behind explicit skills or targeted contracts.
- **medium / project-context**: Use query-first project context. Evidence: context=17852, brain=84657, brain_index=188672 estimated tokens. Advice: Use the Brain meta-index and targeted sections; avoid loading full context, Brain partitions, or brain-index records by default.
- **low / documentation**: Treat docs size as opt-in cost. Evidence: docs category is estimated at 77711 tokens. Advice: Do not optimize docs for runtime unless prompts or skills load them automatically.
- **medium / review-routing**: Match review depth to risk. Evidence: /cg-review dispatch burden is conditional with 10 referenced agents. Advice: Use light or standard reviews for low-risk changes; reserve full review for broad, risky, or explicitly requested checks.
- **low / model-selection**: Use cheaper models for planning and advisory work when quality allows. Evidence: Model governance keeps ordinary planning prompts on the model picker. Advice: Use stronger models for implementation, high-risk review, and architecture; use lighter models for simple planning or documentation passes.

## Warning Review

- **accept** `.github/prompts/cr-work.prompt.md`: Governance warning documents an external support check, not context loading. Action: Keep until exact model frontmatter support is validated.
- **fix** `.github/prompts/cg-review.prompt.md`: High-frequency entrypoints directly affect routine token cost. Action: Slim the prompt or split only with an explicit caller load point.
- **fix** `.github/prompts/cg-work.prompt.md`: High-frequency entrypoints directly affect routine token cost. Action: Slim the prompt or split only with an explicit caller load point.
- **accept** `(always-on instructions)`: Reviewed warning has no ordinary always-on or broad-loading action attached. Action: Keep under review in future audits.
- **accept** `.github/agents/cr-econometric-reasoning.agent.md`: Reviewed warning has no ordinary always-on or broad-loading action attached. Action: Keep under review in future audits.
- **accept** `.github/agents/cr-econometric-reasoning.agent.md`: Reviewed warning has no ordinary always-on or broad-loading action attached. Action: Keep under review in future audits.
- **accept** `.github/agents/cr-identification-audit.agent.md`: Reviewed warning has no ordinary always-on or broad-loading action attached. Action: Keep under review in future audits.
- **accept** `.github/agents/cr-mathematical-verification.agent.md`: Reviewed warning has no ordinary always-on or broad-loading action attached. Action: Keep under review in future audits.
- **accept** `.github/agents/cr-mathematical-verification.agent.md`: Reviewed warning has no ordinary always-on or broad-loading action attached. Action: Keep under review in future audits.
- **accept** `.github/agents/cr-ml-methodology.agent.md`: Reviewed warning has no ordinary always-on or broad-loading action attached. Action: Keep under review in future audits.
- **accept** `.github/agents/cr-provenance-audit.agent.md`: Reviewed warning has no ordinary always-on or broad-loading action attached. Action: Keep under review in future audits.
- **accept** `.github/agents/cr-publication-output.agent.md`: Reviewed warning has no ordinary always-on or broad-loading action attached. Action: Keep under review in future audits.
- **accept** `.github/agents/cr-research-integrity.agent.md`: Reviewed warning has no ordinary always-on or broad-loading action attached. Action: Keep under review in future audits.
- **accept** `.github/agents/cr-specification-analysis.agent.md`: Reviewed warning has no ordinary always-on or broad-loading action attached. Action: Keep under review in future audits.
- **fix** `.github/prompts/cr-brainstorm.prompt.md`: Prompt-level broad context warning needs targeted wording unless proven maintenance-only. Action: Narrow the read or add an explicit accepted rationale.
- **fix** `.github/prompts/cr-plan.prompt.md`: Prompt-level broad context warning needs targeted wording unless proven maintenance-only. Action: Narrow the read or add an explicit accepted rationale.
- **fix** `.github/prompts/cr-plan.prompt.md`: Prompt-level broad context warning needs targeted wording unless proven maintenance-only. Action: Narrow the read or add an explicit accepted rationale.
- **fix** `.github/prompts/cr-work.prompt.md`: Prompt-level broad context warning needs targeted wording unless proven maintenance-only. Action: Narrow the read or add an explicit accepted rationale.
- **fix** `.github/prompts/cr-work.prompt.md`: Prompt-level broad context warning needs targeted wording unless proven maintenance-only. Action: Narrow the read or add an explicit accepted rationale.
- **accept** `.github/skills/cr-skill-research-integrity/SKILL.md`: Reviewed warning has no ordinary always-on or broad-loading action attached. Action: Keep under review in future audits.
- **accept** `.github/skills/cr-skill-research-integrity/SKILL.md`: Reviewed warning has no ordinary always-on or broad-loading action attached. Action: Keep under review in future audits.
- **docs-only** `docs/philosophy.md`: Documentation wording can mention broad artifacts without causing runtime prompt loading. Action: Keep as documentation unless wording misleads users.
- **docs-only** `docs/reference.md`: Documentation wording can mention broad artifacts without causing runtime prompt loading. Action: Keep as documentation unless wording misleads users.
- **docs-only** `docs/workflow.md`: Documentation wording can mention broad artifacts without causing runtime prompt loading. Action: Keep as documentation unless wording misleads users.
