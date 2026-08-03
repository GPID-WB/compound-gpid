# Large Context Warnings

_Generated: 2026-07-31T12:11:16-04:00@3cc58d7d3ba3_

> Token estimates are heuristic (chars/4) and intended for directional audit use.

This file lists large or repeated context signals by path and reason only.
It intentionally avoids copying large prompt, instruction, skill, or
duplicate block bodies.

## Immediate

- `.github/prompts/cg-brainstorm.prompt.md` (prompts): prompt estimated tokens >= 3000; reference count >= 5
- `.github/prompts/cg-commit-push-pr.prompt.md` (prompts): prompt estimated tokens >= 3000; reference count >= 5
- `.github/prompts/cg-fixbug.prompt.md` (prompts): prompt estimated tokens >= 3000; reference count >= 5
- `.github/prompts/cg-plan.prompt.md` (prompts): prompt estimated tokens >= 3000; reference count >= 5
- `.github/prompts/cg-resume.prompt.md` (prompts): prompt estimated tokens >= 3000; reference count >= 5
- `.github/prompts/cg-review-repos.prompt.md` (prompts): prompt estimated tokens >= 3000
- `.github/prompts/cg-review.prompt.md` (prompts): prompt estimated tokens >= 3000; reference count >= 5
- `.github/prompts/cg-setup.prompt.md` (prompts): prompt estimated tokens >= 3000; reference count >= 5
- `.github/prompts/cg-work.prompt.md` (prompts): prompt estimated tokens >= 3000; reference count >= 5
- `.github/skills/cg-skill-brain-query/SKILL.md` (skills): skill estimated tokens >= 2000
- `.github/skills/cg-skill-pester-safety/SKILL.md` (skills): skill estimated tokens >= 2000
- `.github/skills/cg-skill-project-scanner/SKILL.md` (skills): skill estimated tokens >= 2000
- `.github/skills/cg-skill-r-testing/SKILL.md` (skills): skill estimated tokens >= 2000
- `.github/skills/cg-skill-wiki/SKILL.md` (skills): skill estimated tokens >= 2000
- `.github/skills/cr-skill-academic-writing/SKILL.md` (skills): skill estimated tokens >= 2000
- `.github/skills/cr-skill-identification-strategies/SKILL.md` (skills): skill estimated tokens >= 2000
- `.github/skills/cr-skill-mathematical-derivation/SKILL.md` (skills): skill estimated tokens >= 2000
- `.github/skills/cr-skill-ml-economics/SKILL.md` (skills): skill estimated tokens >= 2000
- `.github/skills/cr-skill-publication-output/SKILL.md` (skills): skill estimated tokens >= 2000
- `.github/skills/cr-skill-replication-standards/SKILL.md` (skills): skill estimated tokens >= 2000
- `.github/skills/cr-skill-research-eda/SKILL.md` (skills): skill estimated tokens >= 2000
- `.github/skills/cr-skill-research-integrity/SKILL.md` (skills): skill estimated tokens >= 2000
- `.github/skills/cr-skill-research-workflow/SKILL.md` (skills): skill estimated tokens >= 2000
- `.github/skills/cr-skill-structural-econometrics/SKILL.md` (skills): skill estimated tokens >= 2000
- `.github/skills/cr-skill-symbolic-verification/SKILL.md` (skills): skill estimated tokens >= 2000
- `.github/skills/cr-skill-theory-data-dialogue/SKILL.md` (skills): skill estimated tokens >= 2000
- `.github/instructions/stata.instructions.md` (instructions): instruction estimated tokens >= 1500

## Needs Review

- `.github/prompts/cg-brain-rebuild.prompt.md` (prompts): reference count >= 5
- `.github/prompts/cg-compound-refresh.prompt.md` (prompts): prompt size exceeds review threshold; reference count >= 5
- `.github/prompts/cg-compound.prompt.md` (prompts): prompt size exceeds review threshold; reference count >= 5
- `.github/prompts/cg-diagnose.prompt.md` (prompts): prompt size exceeds review threshold; reference count >= 5
- `.github/prompts/cg-fix-problems.prompt.md` (prompts): reference count >= 5
- `.github/prompts/cg-fix-triage.prompt.md` (prompts): prompt size exceeds review threshold; reference count >= 5
- `.github/prompts/cg-ideate.prompt.md` (prompts): reference count >= 5
- `.github/prompts/cg-issues.prompt.md` (prompts): prompt size exceeds review threshold; reference count >= 5
- `.github/prompts/cg-plan-review.prompt.md` (prompts): reference count >= 5
- `.github/prompts/cg-roadmap-view.prompt.md` (prompts): reference count >= 5
- `.github/prompts/cg-strategy.prompt.md` (prompts): prompt size exceeds review threshold; reference count >= 5
- `.github/prompts/cg-token-audit.prompt.md` (prompts): reference count >= 5
- `.github/prompts/cg-verify-pr.prompt.md` (prompts): prompt size exceeds review threshold; reference count >= 5
- `.github/prompts/cg-wiki.prompt.md` (prompts): prompt size exceeds review threshold; reference count >= 5
- `.github/prompts/cr-brainstorm.prompt.md` (prompts): prompt size exceeds review threshold; reference count >= 5
- `.github/prompts/cr-compound.prompt.md` (prompts): reference count >= 5
- `.github/prompts/cr-plan.prompt.md` (prompts): reference count >= 5
- `.github/prompts/cr-review.prompt.md` (prompts): prompt size exceeds review threshold; reference count >= 5
- `.github/prompts/cr-work.prompt.md` (prompts): prompt size exceeds review threshold; reference count >= 5
- `.github/agents/cg-architecture.agent.md` (agents): reference count >= 5
- `.github/agents/cg-code-quality.agent.md` (agents): reference count >= 5
- `.github/agents/cg-data-quality.agent.md` (agents): reference count >= 5
- `.github/agents/cg-documentation.agent.md` (agents): reference count >= 5
- `.github/agents/cg-fix-problems.agent.md` (agents): agent estimated tokens >= 1500; reference count >= 5
- `.github/agents/cg-performance.agent.md` (agents): reference count >= 5
- `.github/agents/cg-project-scanner.agent.md` (agents): reference count >= 5
- `.github/agents/cg-roadmap-view.agent.md` (agents): agent estimated tokens >= 1500; reference count >= 5
- `.github/agents/cg-roadmap.agent.md` (agents): agent estimated tokens >= 1500; reference count >= 5
- `.github/agents/cg-testing.agent.md` (agents): reference count >= 5
- `.github/agents/cg-wiki.agent.md` (agents): agent estimated tokens >= 1500; reference count >= 5
- `.github/agents/cr-academic-writing.agent.md` (agents): agent estimated tokens >= 1500
- `.github/agents/cr-econometric-reasoning.agent.md` (agents): agent estimated tokens >= 1500
- `.github/agents/cr-identification-audit.agent.md` (agents): agent estimated tokens >= 1500
- `.github/agents/cr-mathematical-verification.agent.md` (agents): agent estimated tokens >= 1500
- `.github/agents/cr-ml-methodology.agent.md` (agents): agent estimated tokens >= 1500
- `.github/agents/cr-publication-output.agent.md` (agents): agent estimated tokens >= 1500; reference count >= 5
- `.github/agents/cr-replication-package.agent.md` (agents): agent estimated tokens >= 1500
- `.github/agents/cr-research-integrity.agent.md` (agents): agent estimated tokens >= 1500; reference count >= 5
- `.github/agents/cr-specification-analysis.agent.md` (agents): agent estimated tokens >= 1500
- `.github/skills/cg-skill-setup/SKILL.md` (skills): skill estimated tokens >= 1200
- `.github/skills/cg-skill-stata-best-practices/SKILL.md` (skills): skill estimated tokens >= 1200
- `.github/skills/cg-skill-windows-cmd-python-detection/SKILL.md` (skills): skill estimated tokens >= 1200
- `.github/skills/cr-skill-research-scoping/SKILL.md` (skills): skill estimated tokens >= 1200

## Repeated Context Blocks

| Preview | Files | Estimated Redundant Tokens |
| --- | --- | --- |
| > **Untrusted-content note**: All data read from `.cg-docs/research/` files
> is | 3 | 383 |
