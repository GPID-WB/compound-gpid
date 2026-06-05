# Context and Model-Governance Audit

_Generated: 2026-06-05T10:04:23_

> Token estimates are heuristic (chars/4) and intended for directional audit use.

## Summary

- Total files: 80
- Total characters: 1466193
- Total estimated tokens: 366522

| Category | Files | Characters | Estimated Tokens |
| --- | --- | --- | --- |
| prompts | 22 | 225586 | 56389 |
| agents | 17 | 86220 | 21550 |
| skills | 20 | 97496 | 24367 |
| instructions | 3 | 13658 | 3414 |
| shared | 1 | 0 | 0 |
| template | 1 | 1633 | 408 |
| docs | 10 | 178310 | 44574 |
| brain | 3 | 234552 | 58636 |
| brain_index | 1 | 520073 | 130018 |
| context | 1 | 55881 | 13970 |
| roadmap | 1 | 52784 | 13196 |

## Top 15 Largest Files

| Path | Category | Characters | Estimated Tokens |
| --- | --- | --- | --- |
| .cg-docs/brain-index.json | brain_index | 520073 | 130018 |
| .cg-docs/BRAIN-log.md | brain | 123178 | 30794 |
| .cg-docs/BRAIN-01.md | brain | 110055 | 27513 |
| compound-gpid.context.md | context | 55881 | 13970 |
| docs/workflow.md | docs | 53392 | 13348 |
| roadmap.json | roadmap | 52784 | 13196 |
| docs/reference.md | docs | 33781 | 8445 |
| docs/troubleshooting.md | docs | 25049 | 6262 |
| .github/prompts/cg-setup.prompt.md | prompts | 21833 | 5458 |
| .github/prompts/cg-work.prompt.md | prompts | 21115 | 5278 |
| .github/prompts/cg-review-repos.prompt.md | prompts | 18301 | 4575 |
| docs/model-guide.md | docs | 15613 | 3903 |
| .github/prompts/cg-review.prompt.md | prompts | 15417 | 3854 |
| .github/prompts/cg-brainstorm.prompt.md | prompts | 14793 | 3698 |
| .github/prompts/cg-plan.prompt.md | prompts | 14217 | 3554 |

## Prompt Reference Matrix

| Path | File | Agent | Skill | Tool | Load | Total |
| --- | --- | --- | --- | --- | --- | --- |
| .github/prompts/cg-setup.prompt.md | 59 | 7 | 0 | 0 | 5 | 71 |
| .github/prompts/cg-review.prompt.md | 8 | 20 | 5 | 0 | 13 | 46 |
| .github/prompts/cg-work.prompt.md | 10 | 13 | 5 | 0 | 13 | 41 |
| .github/prompts/cg-brainstorm.prompt.md | 16 | 6 | 1 | 0 | 7 | 30 |
| .github/prompts/cg-wiki.prompt.md | 9 | 9 | 0 | 0 | 11 | 29 |
| .github/prompts/cg-compound.prompt.md | 15 | 5 | 2 | 0 | 6 | 28 |
| .github/prompts/cg-plan.prompt.md | 11 | 7 | 1 | 0 | 8 | 27 |
| .github/prompts/cg-plan-review.prompt.md | 6 | 11 | 0 | 0 | 6 | 23 |
| .github/prompts/cg-strategy.prompt.md | 13 | 5 | 0 | 0 | 4 | 22 |
| .github/agents/cg-wiki.agent.md | 11 | 0 | 8 | 0 | 1 | 20 |
| .github/prompts/cg-resume.prompt.md | 14 | 3 | 0 | 0 | 1 | 18 |
| .github/prompts/cg-fix-triage.prompt.md | 4 | 0 | 8 | 0 | 3 | 15 |
| .github/agents/cg-roadmap-view.agent.md | 11 | 3 | 0 | 0 | 0 | 14 |
| .github/prompts/cg-brain-rebuild.prompt.md | 14 | 0 | 0 | 0 | 0 | 14 |
| .github/prompts/cg-fix-problems.prompt.md | 4 | 4 | 0 | 0 | 6 | 14 |
| .github/agents/cg-fix-problems.agent.md | 0 | 0 | 5 | 0 | 8 | 13 |
| .github/prompts/cg-ideate.prompt.md | 10 | 2 | 0 | 0 | 1 | 13 |
| .github/prompts/cg-fixbug.prompt.md | 4 | 0 | 5 | 0 | 2 | 11 |
| .github/prompts/cg-verify-pr.prompt.md | 4 | 3 | 0 | 0 | 4 | 11 |
| .github/agents/cg-data-quality.agent.md | 1 | 0 | 6 | 0 | 2 | 9 |
| .github/agents/cg-roadmap.agent.md | 8 | 0 | 0 | 0 | 1 | 9 |
| .github/prompts/cg-diagnose.prompt.md | 7 | 0 | 1 | 0 | 1 | 9 |
| .github/agents/cg-code-quality.agent.md | 2 | 0 | 3 | 0 | 3 | 8 |
| .github/agents/cg-testing.agent.md | 0 | 0 | 5 | 0 | 2 | 7 |
| .github/prompts/cg-compound-refresh.prompt.md | 7 | 0 | 0 | 0 | 0 | 7 |
| .github/prompts/cg-roadmap-view.prompt.md | 2 | 3 | 0 | 0 | 2 | 7 |
| .github/agents/cg-architecture.agent.md | 0 | 0 | 4 | 0 | 2 | 6 |
| .github/agents/cg-performance.agent.md | 1 | 0 | 3 | 0 | 2 | 6 |
| .github/agents/cg-documentation.agent.md | 0 | 0 | 3 | 0 | 2 | 5 |
| .github/agents/cg-project-scanner.agent.md | 0 | 0 | 3 | 0 | 2 | 5 |
| .github/prompts/cg-commit-push-pr.prompt.md | 5 | 0 | 0 | 0 | 0 | 5 |
| .github/agents/cg-reproducibility.agent.md | 0 | 0 | 2 | 0 | 2 | 4 |
| .github/prompts/cg-review-repos.prompt.md | 3 | 1 | 0 | 0 | 0 | 4 |
| .github/agents/cg-version-control.agent.md | 0 | 0 | 2 | 0 | 1 | 3 |
| .github/agents/cg-release-scanner.agent.md | 1 | 0 | 0 | 0 | 0 | 1 |
| .github/prompts/cg-devtag.prompt.md | 1 | 0 | 0 | 0 | 0 | 1 |
| .github/agents/cg-adversarial.agent.md | 0 | 0 | 0 | 0 | 0 | 0 |
| .github/agents/cg-learnings-researcher.agent.md | 0 | 0 | 0 | 0 | 0 | 0 |
| .github/agents/cg-plan-critic.agent.md | 0 | 0 | 0 | 0 | 0 | 0 |

## Model Inventory

| Path | Category | Model | Tier |
| --- | --- | --- | --- |
| .github/prompts/cg-brain-rebuild.prompt.md | prompts | Claude Sonnet 4.6 (copilot) | standard |
| .github/prompts/cg-brainstorm.prompt.md | prompts | Claude Opus 4.6 (copilot) | premium |
| .github/prompts/cg-commit-push-pr.prompt.md | prompts | Claude Sonnet 4.6 (copilot) | standard |
| .github/prompts/cg-compound-refresh.prompt.md | prompts | Claude Sonnet 4.6 (copilot) | standard |
| .github/prompts/cg-compound.prompt.md | prompts | Claude Sonnet 4.6 (copilot) | standard |
| .github/prompts/cg-devtag.prompt.md | prompts | Claude Haiku 4.5 (copilot) | economy |
| .github/prompts/cg-diagnose.prompt.md | prompts | Claude Sonnet 4.6 (copilot) | standard |
| .github/prompts/cg-fix-problems.prompt.md | prompts | Claude Sonnet 4.6 (copilot) | standard |
| .github/prompts/cg-fix-triage.prompt.md | prompts | Claude Sonnet 4.6 (copilot) | standard |
| .github/prompts/cg-fixbug.prompt.md | prompts | Claude Sonnet 4.6 (copilot) | standard |
| .github/prompts/cg-ideate.prompt.md | prompts | Claude Opus 4.6 (copilot) | premium |
| .github/prompts/cg-plan-review.prompt.md | prompts | Claude Opus 4.6 (copilot) | premium |
| .github/prompts/cg-plan.prompt.md | prompts | Claude Opus 4.6 (copilot) | premium |
| .github/prompts/cg-resume.prompt.md | prompts | Claude Haiku 4.5 (copilot) | economy |
| .github/prompts/cg-review-repos.prompt.md | prompts | Claude Opus 4.6 (copilot) | premium |
| .github/prompts/cg-review.prompt.md | prompts | Claude Sonnet 4.6 (copilot) | standard |
| .github/prompts/cg-roadmap-view.prompt.md | prompts | Claude Haiku 4.5 (copilot) | economy |
| .github/prompts/cg-setup.prompt.md | prompts | Claude Haiku 4.5 (copilot) | economy |
| .github/prompts/cg-strategy.prompt.md | prompts | Claude Opus 4.6 (copilot) | premium |
| .github/prompts/cg-verify-pr.prompt.md | prompts | Claude Sonnet 4.6 (copilot) | standard |
| .github/prompts/cg-wiki.prompt.md | prompts | Claude Sonnet 4.6 (copilot) | standard |
| .github/prompts/cg-work.prompt.md | prompts | Claude Sonnet 4.6 (copilot) | standard |
| .github/agents/cg-adversarial.agent.md | agents | Claude Sonnet 4.6 (copilot) | standard |
| .github/agents/cg-architecture.agent.md | agents | Claude Sonnet 4.6 (copilot) | standard |
| .github/agents/cg-code-quality.agent.md | agents | Claude Haiku 4.5 (copilot) | economy |
| .github/agents/cg-data-quality.agent.md | agents | Claude Sonnet 4.6 (copilot) | standard |
| .github/agents/cg-documentation.agent.md | agents | Claude Haiku 4.5 (copilot) | economy |
| .github/agents/cg-fix-problems.agent.md | agents | Claude Sonnet 4.6 (copilot) | standard |
| .github/agents/cg-learnings-researcher.agent.md | agents | Claude Haiku 4.5 (copilot) | economy |
| .github/agents/cg-performance.agent.md | agents | Claude Sonnet 4.6 (copilot) | standard |
| .github/agents/cg-plan-critic.agent.md | agents | Claude Sonnet 4.6 (copilot) | standard |
| .github/agents/cg-project-scanner.agent.md | agents | Claude Haiku 4.5 (copilot) | economy |
| .github/agents/cg-release-scanner.agent.md | agents | Claude Haiku 4.5 (copilot) | economy |
| .github/agents/cg-reproducibility.agent.md | agents | Claude Haiku 4.5 (copilot) | economy |
| .github/agents/cg-roadmap-view.agent.md | agents | Claude Haiku 4.5 (copilot) | economy |
| .github/agents/cg-roadmap.agent.md | agents | Claude Haiku 4.5 (copilot) | economy |
| .github/agents/cg-testing.agent.md | agents | Claude Haiku 4.5 (copilot) | economy |
| .github/agents/cg-version-control.agent.md | agents | Claude Haiku 4.5 (copilot) | economy |
| .github/agents/cg-wiki.agent.md | agents | Claude Sonnet 4.6 (copilot) | standard |

## Missing Model Declarations

- None

## Model Drift

- None

## Premium Model Usage

- .github/prompts/cg-brainstorm.prompt.md: Claude Opus 4.6 (copilot) (escalation condition: False)
- .github/prompts/cg-ideate.prompt.md: Claude Opus 4.6 (copilot) (escalation condition: False)
- .github/prompts/cg-plan-review.prompt.md: Claude Opus 4.6 (copilot) (escalation condition: False)
- .github/prompts/cg-plan.prompt.md: Claude Opus 4.6 (copilot) (escalation condition: False)
- .github/prompts/cg-review-repos.prompt.md: Claude Opus 4.6 (copilot) (escalation condition: False)
- .github/prompts/cg-strategy.prompt.md: Claude Opus 4.6 (copilot) (escalation condition: False)

## Duplicate Paragraphs

| Preview | Files | Estimated Tokens |
| --- | --- | --- |
| 1. Read `compound-gpid.md` in the project root for project context (objective,
c | 4 | 469 |

## Immediate Optimization Candidates

- .github/prompts/cg-brainstorm.prompt.md (prompts): prompt estimated tokens >= 3000; premium model without escalation condition; reference count >= 5
- .github/prompts/cg-fixbug.prompt.md (prompts): prompt estimated tokens >= 3000; reference count >= 5
- .github/prompts/cg-ideate.prompt.md (prompts): premium model without escalation condition; prompt size exceeds review threshold; reference count >= 5
- .github/prompts/cg-plan-review.prompt.md (prompts): premium model without escalation condition; prompt size exceeds review threshold; reference count >= 5
- .github/prompts/cg-plan.prompt.md (prompts): prompt estimated tokens >= 3000; premium model without escalation condition; reference count >= 5
- .github/prompts/cg-review-repos.prompt.md (prompts): prompt estimated tokens >= 3000; premium model without escalation condition
- .github/prompts/cg-review.prompt.md (prompts): prompt estimated tokens >= 3000; reference count >= 5
- .github/prompts/cg-setup.prompt.md (prompts): prompt estimated tokens >= 3000; reference count >= 5
- .github/prompts/cg-strategy.prompt.md (prompts): premium model without escalation condition; prompt size exceeds review threshold; reference count >= 5
- .github/prompts/cg-work.prompt.md (prompts): prompt estimated tokens >= 3000; reference count >= 5
- .github/skills/cg-skill-brain-query/SKILL.md (skills): skill estimated tokens >= 2000
- .github/skills/cg-skill-pester-safety/SKILL.md (skills): skill estimated tokens >= 2000
- .github/skills/cg-skill-project-scanner/SKILL.md (skills): skill estimated tokens >= 2000
- .github/skills/cg-skill-r-testing/SKILL.md (skills): skill estimated tokens >= 2000
- .github/skills/cg-skill-wiki/SKILL.md (skills): skill estimated tokens >= 2000
- .github/instructions/stata.instructions.md (instructions): instruction estimated tokens >= 1500

## Needs Review

- .github/prompts/cg-brain-rebuild.prompt.md (prompts): prompt size exceeds review threshold; reference count >= 5
- .github/prompts/cg-commit-push-pr.prompt.md (prompts): prompt size exceeds review threshold; reference count >= 5
- .github/prompts/cg-compound-refresh.prompt.md (prompts): prompt size exceeds review threshold; reference count >= 5
- .github/prompts/cg-compound.prompt.md (prompts): prompt size exceeds review threshold; reference count >= 5
- .github/prompts/cg-devtag.prompt.md (prompts): prompt size exceeds review threshold
- .github/prompts/cg-diagnose.prompt.md (prompts): prompt size exceeds review threshold; reference count >= 5
- .github/prompts/cg-fix-problems.prompt.md (prompts): prompt size exceeds review threshold; reference count >= 5
- .github/prompts/cg-fix-triage.prompt.md (prompts): prompt size exceeds review threshold; reference count >= 5
- .github/prompts/cg-resume.prompt.md (prompts): prompt size exceeds review threshold; reference count >= 5
- .github/prompts/cg-roadmap-view.prompt.md (prompts): prompt size exceeds review threshold; reference count >= 5
- .github/prompts/cg-verify-pr.prompt.md (prompts): prompt size exceeds review threshold; reference count >= 5
- .github/prompts/cg-wiki.prompt.md (prompts): prompt size exceeds review threshold; reference count >= 5
- .github/agents/cg-architecture.agent.md (agents): reference count >= 5
- .github/agents/cg-code-quality.agent.md (agents): reference count >= 5
- .github/agents/cg-data-quality.agent.md (agents): reference count >= 5
- .github/agents/cg-documentation.agent.md (agents): reference count >= 5
- .github/agents/cg-fix-problems.agent.md (agents): agent estimated tokens >= 1500; reference count >= 5
- .github/agents/cg-performance.agent.md (agents): reference count >= 5
- .github/agents/cg-project-scanner.agent.md (agents): reference count >= 5
- .github/agents/cg-roadmap-view.agent.md (agents): agent estimated tokens >= 1500; reference count >= 5
- .github/agents/cg-roadmap.agent.md (agents): reference count >= 5
- .github/agents/cg-testing.agent.md (agents): reference count >= 5
- .github/agents/cg-wiki.agent.md (agents): agent estimated tokens >= 1500; reference count >= 5
- .github/skills/cg-skill-setup/SKILL.md (skills): skill estimated tokens >= 1200
- .github/skills/cg-skill-stata-best-practices/SKILL.md (skills): skill estimated tokens >= 1200
