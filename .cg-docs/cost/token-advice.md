# Token Efficiency Advice

_Generated: 2026-06-16T18:20:22_

> Token estimates are heuristic (chars/4) and intended for directional audit use.

## Current Audit

- Guardrail failures: 0
- Guardrail warnings: 22
- Warning classification: fix=0, accept=19, docs-only=3

## Recommended Actions

- **medium / project-context**: Use query-first project context. Evidence: context=16009, brain=66483, brain_index=147666 estimated tokens. Advice: Use the Brain meta-index and targeted sections; avoid loading full context, Brain partitions, or brain-index records by default.
- **low / documentation**: Treat docs size as opt-in cost. Evidence: docs category is estimated at 50551 tokens. Advice: Do not optimize docs for runtime unless prompts or skills load them automatically.
- **medium / review-routing**: Match review depth to risk. Evidence: /cg-review dispatch burden is conditional with 10 referenced agents. Advice: Use light or standard reviews for low-risk changes; reserve full review for broad, risky, or explicitly requested checks.
- **low / model-selection**: Use cheaper models for planning and advisory work when quality allows. Evidence: Model governance keeps ordinary planning prompts on the model picker. Advice: Use stronger models for implementation, high-risk review, and architecture; use lighter models for simple planning or documentation passes.

## Warning Review

- **accept** `.github/agents/cg-learnings-researcher.agent.md`: Maintenance, roadmap, setup, release, or research workflow intentionally inspects broad project state. Action: Keep the read and document the maintenance rationale.
- **accept** `.github/agents/cg-learnings-researcher.agent.md`: Maintenance, roadmap, setup, release, or research workflow intentionally inspects broad project state. Action: Keep the read and document the maintenance rationale.
- **accept** `.github/agents/cg-release-scanner.agent.md`: Maintenance, roadmap, setup, release, or research workflow intentionally inspects broad project state. Action: Keep the read and document the maintenance rationale.
- **accept** `.github/agents/cg-release-scanner.agent.md`: Maintenance, roadmap, setup, release, or research workflow intentionally inspects broad project state. Action: Keep the read and document the maintenance rationale.
- **accept** `.github/agents/cg-roadmap-view.agent.md`: Reviewed warning has no ordinary always-on or broad-loading action attached. Action: Keep under review in future audits.
- **accept** `.github/agents/cg-roadmap-view.agent.md`: Reviewed warning has no ordinary always-on or broad-loading action attached. Action: Keep under review in future audits.
- **accept** `.github/agents/cg-roadmap.agent.md`: Maintenance, roadmap, setup, release, or research workflow intentionally inspects broad project state. Action: Keep the read and document the maintenance rationale.
- **accept** `.github/agents/cg-roadmap.agent.md`: Maintenance, roadmap, setup, release, or research workflow intentionally inspects broad project state. Action: Keep the read and document the maintenance rationale.
- **accept** `.github/prompts/cg-compound-refresh.prompt.md`: Maintenance, roadmap, setup, release, or research workflow intentionally inspects broad project state. Action: Keep the read and document the maintenance rationale.
- **accept** `.github/prompts/cg-compound-refresh.prompt.md`: Maintenance, roadmap, setup, release, or research workflow intentionally inspects broad project state. Action: Keep the read and document the maintenance rationale.
- **accept** `.github/prompts/cg-issues.prompt.md`: Maintenance, roadmap, setup, release, or research workflow intentionally inspects broad project state. Action: Keep the read and document the maintenance rationale.
- **accept** `.github/prompts/cg-issues.prompt.md`: Maintenance, roadmap, setup, release, or research workflow intentionally inspects broad project state. Action: Keep the read and document the maintenance rationale.
- **accept** `.github/prompts/cg-review-repos.prompt.md`: Maintenance, roadmap, setup, release, or research workflow intentionally inspects broad project state. Action: Keep the read and document the maintenance rationale.
- **accept** `.github/prompts/cg-setup.prompt.md`: Maintenance, roadmap, setup, release, or research workflow intentionally inspects broad project state. Action: Keep the read and document the maintenance rationale.
- **accept** `.github/prompts/cg-strategy.prompt.md`: Maintenance, roadmap, setup, release, or research workflow intentionally inspects broad project state. Action: Keep the read and document the maintenance rationale.
- **accept** `.github/prompts/cg-strategy.prompt.md`: Maintenance, roadmap, setup, release, or research workflow intentionally inspects broad project state. Action: Keep the read and document the maintenance rationale.
- **accept** `.github/prompts/cg-token-audit.prompt.md`: Maintenance, roadmap, setup, release, or research workflow intentionally inspects broad project state. Action: Keep the read and document the maintenance rationale.
- **accept** `.github/prompts/cg-token-audit.prompt.md`: Maintenance, roadmap, setup, release, or research workflow intentionally inspects broad project state. Action: Keep the read and document the maintenance rationale.
- **accept** `.github/prompts/cg-work.prompt.md`: The flagged line is a safety or goal-execution guard, not a read directive. Action: Retain the guardrail wording.
- **docs-only** `docs/context-files.md`: Documentation wording can mention broad artifacts without causing runtime prompt loading. Action: Keep as documentation unless wording misleads users.
- **docs-only** `docs/reference.md`: Documentation wording can mention broad artifacts without causing runtime prompt loading. Action: Keep as documentation unless wording misleads users.
- **docs-only** `docs/workflow.md`: Documentation wording can mention broad artifacts without causing runtime prompt loading. Action: Keep as documentation unless wording misleads users.
