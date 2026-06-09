---
date: 2026-06-09
title: "Token Optimization Release Candidate Checklist"
status: active
scope: release-candidate
plan: ".cg-docs/plans/2026-06-09-token-optimization-phase7-release-validation.md"
---

# Token Optimization Release Candidate Checklist

Use this checklist before merging or releasing the Phase 2-7 token-optimization
work. It combines static guardrails, Codex-side checks, and manual
GitHub Copilot / VS Code runtime checks. Runtime-only items must be validated
in Copilot because static audit output cannot prove model-picker selection or
agent dispatch behavior.

## Release Gates

| Gate | Evidence | Status |
|------|----------|--------|
| Context/model audit generated successfully | `python3 scripts/cg_audit_context.py --root . --format both` exits 0 and writes `.cg-docs/cost/context-audit.md` plus `.cg-docs/cost/context-audit.json` | Passed in Codex; see generated audit timestamp |
| Phase 6 benchmark summary reviewed | Audit `Benchmark Summary` includes `/cg-plan`, `/cg-work`, `/cg-review`, `/cg-compound`, `/cg-resume`, and Knowledge Brain/context lookup | Passed in Codex |
| Guardrail failures are zero | Audit `Guardrails` section reports `Failures: 0` | Passed in Codex |
| Guardrail warnings are classified | See warning triage below | Passed in Codex, 28 warnings classified |
| Premium model usage is absent or explicitly justified | Audit model governance shows `premium_usage_count: 0`, or every nonzero item has a release-approved rationale | Passed in Codex, count 0 |
| Ordinary model-picker prompts omit `model:` | Audit shows `ordinary_model_picker_violations: 0` | Passed in Codex, count 0 |
| `/cg-plan` model-context note is present | Static prompt inspection confirms the model-picker note and Copilot Auto guidance | Passed in Codex through audit guardrails; Pester prompt-contract tests remain external |
| `/cg-review` routed modes remain intact | Shared routing contract and audit review-agent counts match light 2, standard 8, data-risk 8, architecture 8, full 10 | Passed in Codex |
| `/cg-work review:*` modes remain intact | Prompt and audit guardrails preserve `review:auto`, `review:manual`, `review:none`, and explicit `review:<mode>` behavior | Passed in Codex |
| Knowledge Brain retrieval remains selective | `cg-skill-brain-query` keeps the BRAIN.md index, matched-topic, and no-wholesale `brain-index.json` rules | Passed in Codex |
| Broad context loading is not reintroduced in ordinary prompts | Audit has no guardrail failures for ordinary-prompt broad reads | Passed in Codex |
| `_tmp/` is not durable project storage | `rg -n "_tmp/" . --glob '!_tmp/**'` finds no documentation or workflow instruction treating `_tmp/` as durable | Passed in Codex; only a negative policy statement was found |
| Python audit tests pass | `python3 -m pytest scripts/tests/test_audit_context.py` exits 0 | Passed in Codex, 67 tests |
| Safe Pester runner passes | `. tests\Run-Tests.ps1` passes in VS Code/PowerShell and `tests/last-run.json` confirms success | External validation required |
| Manual VS Code/Copilot runtime checklist is complete | Manual checklist below has all items checked | External validation required |
| Follow-up items are separate from blockers | `.cg-docs/cost/token-optimization-follow-ups.md` lists non-blockers separately | Passed in Codex |

## Command Set

Run these from the repository root.

```bash
python3 -m pytest scripts/tests/test_audit_context.py
python3 scripts/cg_audit_context.py --root . --format both
git diff --check
```

If comparing against a saved pre-change audit:

```bash
python3 scripts/cg_audit_context.py --root . --format both --baseline <baseline-json>
```

Run Pester only in VS Code/PowerShell through the safe runner:

```powershell
. tests\Run-Tests.ps1
Get-Content tests\last-run.json | ConvertFrom-Json
```

Do not run ad hoc `Invoke-Pester` commands for this release check.

## End-to-End Manual Validation

| Surface | Harness | Expected result | Status |
|---------|---------|-----------------|--------|
| `/cg-plan` | VS Code/Copilot | Starts with the model-context note, respects branch-offer behavior, creates a plan under `.cg-docs/plans/`, uses staged context loading, and does not infer the hidden model when Copilot Auto is selected | External validation required |
| `/cg-work` | VS Code/Copilot | Loads the active plan, respects phase gates, preserves Pester safe-runner guidance, performs mechanical self-review, and defaults to review recommendation only | External validation required |
| `/cg-work review:auto` | VS Code/Copilot | Resolves review mode through `.github/shared/review-routing.contract.md` and dispatches only route-appropriate agents | External validation required |
| `/cg-work review:manual` | VS Code/Copilot | Dispatches no review agents and emits a structured `/cg-review <mode>` recommendation | External validation required |
| `/cg-work review:none` | VS Code/Copilot | Dispatches no review agents and suppresses review handoff verbosity | External validation required |
| `/cg-review light` | VS Code/Copilot | Resolves to `@cg-code-quality` plus `@cg-testing` only | External validation required |
| `/cg-review data-risk` | VS Code/Copilot | Resolves to the standard eight agents with mandatory data-quality, reproducibility, and testing emphasis | External validation required |
| `/cg-review full` | VS Code/Copilot | Resolves to all ten agents, including `@cg-learnings-researcher` and `@cg-adversarial` | External validation required |
| `/cg-compound` | VS Code/Copilot | Captures a solution, rebuilds Knowledge Brain when tooling is available, and enriches context/wiki only through documented maintenance behavior | External validation required |
| `/cg-resume` | VS Code/Copilot | Loads pending work and roadmap health without carrying unrelated roadmap or Brain records into the session summary | External validation required |
| Knowledge Brain selective retrieval | VS Code/Copilot | Uses `.cg-docs/BRAIN.md` as the entry point, selects matched topics, opens only relevant `BRAIN-NN.md` sections, and does not consume the tooling JSON wholesale | External validation required |
| Model-picker behavior | VS Code/Copilot | Ordinary model-picker prompts use the selected Copilot model; Auto is not described as a named hidden model; premium model use is user-initiated or explicitly justified | External validation required |

## Audit Warning Triage

Warnings are acceptable only when they are classified and not release blockers.
The final Codex audit still reports 28 warnings and zero failures. See
`.cg-docs/cost/context-audit.json` for the generated timestamp.

| Warning group | Count in Phase 6 audit | Classification | Release decision |
|---------------|------------------------|----------------|------------------|
| `.github/agents/cg-learnings-researcher.agent.md` over `.cg-docs/` | 2 | Intentional maintenance/review lookup | Non-blocking; reviewer intentionally searches prior learning artifacts |
| `.github/agents/cg-release-scanner.agent.md` over `.cg-docs/` | 2 | Intentional release scanning | Non-blocking; release notes require bounded scan-window knowledge artifacts |
| `.github/agents/cg-roadmap-view.agent.md` over `roadmap.json` | 2 | Intentional roadmap rendering | Non-blocking; read-only renderer needs roadmap fields |
| `.github/agents/cg-roadmap.agent.md` over `roadmap.json` | 1 | Intentional roadmap write workflow | Non-blocking; write agent must inspect current roadmap before edits |
| `.github/agents/cg-wiki.agent.md` over `compound-gpid.context.md` | 1 | Intentional wiki/context maintenance | Non-blocking; wiki update workflow needs context placement checks |
| `.github/prompts/cg-compound-refresh.prompt.md` over `compound-gpid.context.md` and `.cg-docs/` | 2 | Intentional maintenance workflow | Non-blocking; refresh audits existing solution corpus |
| `.github/prompts/cg-diagnose.prompt.md` over `compound-gpid.context.md` | 1 | Follow-up | Non-blocking; review later for staged context wording |
| `.github/prompts/cg-fix-problems.prompt.md` over `compound-gpid.context.md` | 1 | Follow-up | Non-blocking; review later for staged context wording |
| `.github/prompts/cg-fixbug.prompt.md` over `compound-gpid.context.md` | 1 | Follow-up | Non-blocking; review later for staged context wording |
| `.github/prompts/cg-ideate.prompt.md` over `roadmap.json`, `compound-gpid.context.md`, and `.cg-docs/` | 4 | Follow-up | Non-blocking; future context-selectivity cleanup candidate |
| `.github/prompts/cg-plan-review.prompt.md` over `roadmap.json` and `compound-gpid.context.md` | 2 | Follow-up | Non-blocking; future context-selectivity cleanup candidate |
| `.github/prompts/cg-review-repos.prompt.md` over `.cg-docs/` | 1 | Intentional competitive-review maintenance | Non-blocking; bounded registry/review workflow |
| `.github/prompts/cg-setup.prompt.md` over `compound-gpid.context.md` | 1 | Intentional setup/context curation | Non-blocking; setup creates and validates context artifacts |
| `.github/prompts/cg-strategy.prompt.md` over `compound-gpid.context.md` and `roadmap.json` | 2 | Follow-up | Non-blocking; future staged-read cleanup candidate |
| `.github/prompts/cg-wiki.prompt.md` over `compound-gpid.context.md` | 1 | Intentional wiki maintenance | Non-blocking; wiki configuration and enrichment need context placement checks |
| `.github/prompts/cg-work.prompt.md` over `.cg-docs/` | 1 | Intentional plan loading | Non-blocking; work prompt must load the selected plan thoroughly |
| `docs/context-files.md`, `docs/reference.md`, and `docs/workflow.md` | 3 | Documentation wording warning | Non-blocking unless wording instructs ordinary prompts to perform broad runtime loading |

## Blockers

No Phase 6 audit blocker is known at plan start. Treat any of these as a
release blocker if they appear in the final run:

- guardrail failure count is nonzero;
- premium model usage is introduced without explicit approved rationale;
- any ordinary model-picker prompt regains `model:` frontmatter;
- `/cg-review` route precedence, full route, or review-agent counts drift;
- `/cg-work review:auto`, `review:manual`, or `review:none` disappears or changes dispatch semantics;
- Knowledge Brain instructions allow wholesale default reads of the tooling JSON;
- an ordinary workflow reintroduces unqualified broad context loading;
- `_tmp/` is documented or used as durable project storage.

## Inbox Policy

`.cg-docs/inbox/` is a holding area for unprocessed strategy ideas. Phase 7
does not approve, prioritize, link, or convert inbox documents into roadmap
items. Release notes may mention that inbox items remain unprocessed, but they
must not treat those ideas as committed work.
