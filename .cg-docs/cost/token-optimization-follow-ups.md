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

## Deferred to VS Code/PowerShell — Required Before Merge

These items cannot run in Codex but must be completed in VS Code/PowerShell
before the release is declared final.

| Item | Source | Requirement |
|------|--------|-------------|
| Run the safe Pester suite in VS Code/PowerShell | Project Pester safety rules | Run `. tests\Run-Tests.ps1`; inspect `tests/last-run.json` and confirm `FailedCount` is `0`. Requires Pester 4.10.1: `Install-Module Pester -RequiredVersion 4.10.1 -Force -SkipPublisherCheck -Scope CurrentUser`. Do not use ad hoc `Invoke-Pester`. |
| Complete manual VS Code/Copilot runtime validation | Phase 7 validation checklist | Sign off all 12 rows in the End-to-End Manual Validation table with validator initials and date. Codex static checks cannot prove model-picker selection or Copilot agent dispatch behavior. |

## Non-Blocking Follow-ups

| Item | Source | Why non-blocking |
|------|--------|------------------|
| Review staged context wording in `/cg-diagnose`, `/cg-fix-problems`, `/cg-fixbug`, `/cg-ideate`, `/cg-plan-review`, and `/cg-strategy` | Phase 6 audit warnings | Current warnings are visible and do not show guardrail failures; Phase 7 is release validation, not another prompt-slimming pass |
| Consider reducing documentation wording warnings in `docs/context-files.md`, `docs/reference.md`, and `docs/workflow.md` | Phase 6 audit warnings | Documentation warnings are not runtime behavior unless they instruct ordinary prompts to broaden context loading |
| Leave `.cg-docs/inbox/cg-knowledge-index-roadmap.md` unprocessed until a separate strategy/roadmap session | Phase 7 non-goal | Inbox ideas are not approved roadmap items and should not be promoted during release validation |

## Completion Notes

Update this section after final validation:

- Python audit tests: passed in Codex, `67 passed`.
- Context/model audit: passed in Codex; see `.cg-docs/cost/context-audit.json` for the generated timestamp.
- Benchmark/guardrail command: passed in Codex through `python3 scripts/cg_audit_context.py --root . --format both`; failures 0, warnings 28, premium usage 0, ordinary model-picker violations 0.
- Git diff check: passed in Codex with `git diff --check`.
- Pester safe runner: external validation required because no `pwsh` or `powershell` executable is available on PATH in this Codex environment.
- Manual VS Code/Copilot checklist: external validation required for model-picker behavior and routed dispatch.
