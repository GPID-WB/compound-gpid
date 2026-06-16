---
date: 2026-06-09
title: "Token Optimization Release Follow-ups"
status: active
plan: ".cg-docs/plans/2026-06-09-token-optimization-phase7-release-validation.md"
---

# Token Optimization Release Follow-ups

This file separates non-blocking follow-up work from release blockers for the
Phase 2-7 token-optimization effort. Items here do not approve new roadmap work
and do not process `.cg-docs/inbox/` ideas.

## Release Blockers

No blocker is currently recorded. Add a blocker here only if final validation
finds a failed guardrail, broken model-picker behavior, broken review routing,
broken `/cg-work review:*` behavior, broad ordinary-prompt context loading, or
durable `_tmp/` artifact usage.

## Deferred Manual Validation

These items must be completed before declaring the release final when they
cannot be proven by static audit output.

| Item | Source | Requirement |
|------|--------|-------------|
| Run the safe Pester suite in VS Code/PowerShell | Project Pester safety rules | Passed on 2026-06-16 via `. tests\Run-Tests.ps1`: 2194 passed, 0 failed. Re-run after any further prompt, script, or test changes. Do not use ad hoc `Invoke-Pester`. |
| Complete manual VS Code/Copilot runtime validation | Phase 7 validation checklist | Sign off all 12 rows in the End-to-End Manual Validation table with validator initials and date. Codex static checks cannot prove model-picker selection or Copilot agent dispatch behavior. |

## Non-Blocking Follow-ups

| Item | Source | Why non-blocking |
|------|--------|------------------|
| Re-check token/context warning classifications after future prompt changes | #93/#94 closure | Current final audit has `fix=0`, `accept=19`, `docs-only=3`. Any future ordinary prompt broad-read warning should be fixed or explicitly classified before release. |
| Keep documentation wording warnings as docs-only unless they become runtime instructions | #93/#94 closure | Documentation may describe `.cg-docs/`, `BRAIN*.md`, or context files without causing runtime loading. Change only wording that could mislead prompts or users into broad default reads. |
| Leave `.cg-docs/inbox/cg-knowledge-index-roadmap.md` unprocessed until a separate strategy/roadmap session | Phase 7 non-goal | Inbox ideas are not approved roadmap items and should not be promoted during release validation |

## Completion Notes

Update this section after final validation:

- Python audit tests: passed in Codex, `82 passed`.
- Context/model audit: passed in Codex; see `.cg-docs/cost/context-audit.json` for the generated timestamp.
- Benchmark/guardrail command: passed in Codex through `python3 scripts/cg_audit_context.py --root . --output-dir .cg-docs/cost --format both --recommendations`; failures 0, warnings 22, reviewed warnings `fix=0`, `accept=19`, `docs-only=3`, premium usage 0, ordinary model-picker violations 0.
- Git diff check: passed in Codex with `git diff --check`.
- Pester safe runner: passed in Codex/PowerShell on 2026-06-16, `2194 passed, 0 failed`.
- Manual VS Code/Copilot checklist: external validation required for model-picker behavior and routed dispatch.
