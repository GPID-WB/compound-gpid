---
date: 2026-06-09
title: "Token optimization release candidates need end-to-end validation evidence"
category: "testing-patterns"
language: "Python/PowerShell/Markdown"
tags: [token-optimization, release-readiness, validation, model-governance, review-routing, context-loading, knowledge-capture]
root-cause: "Static prompt and audit improvements are not release-ready until maintainers have evidence that model governance, routed review, context selectivity, and runtime workflows still work together"
severity: "P2"
plan: ".cg-docs/plans/2026-06-09-token-optimization-phase7-release-validation.md"
reviewed-in: ".cg-docs/reviews/2026-06-09-token-optimization-phase7-release-validation-review-2.md"
related: [".cg-docs/solutions/testing-patterns/2026-06-08-token-optimization-benchmark-guardrails.md", ".cg-docs/cost/token-optimization-release-checklist.md"]
---

# Token Optimization Release Candidates Need End-to-End Validation Evidence

## Problem

Phases 2-6 reduced token and model-cost risk across ordinary model-picker
prompts, `/cg-review`, `/cg-work`, Knowledge Brain retrieval, context loading,
and audit tooling. Each improvement could pass its own local check while still
leaving maintainers uncertain about release readiness: static audit output does
not prove Copilot model-picker behavior, route-aware dispatch, or manual
VS Code runtime behavior.

The Phase 7 release-candidate question was therefore not whether to slim more
prompts. It was whether the completed optimization work had a clear evidence
trail for merge and release.

## Root Cause

Token optimization spans prompt metadata, shared routing contracts,
documentation, generated knowledge artifacts, and manual Copilot behavior. A
single test type cannot verify the whole surface:

- Python audit tests verify benchmark and guardrail logic.
- The generated context/model audit verifies static prompt and model-governance
  state.
- Pester prompt-contract tests verify Copilot prompt text, but must run through
  the project safe runner in VS Code/PowerShell.
- Manual VS Code/Copilot checks verify model-picker inheritance and actual
  routed dispatch behavior.
- Knowledge capture verifies that future maintainers can find the pattern.

Without a release checklist, those evidence types remain scattered and easy to
skip.

## Solution

Treat token-optimization release readiness as a checklist-backed validation
contract.

Phase 7 added:

- `.cg-docs/cost/token-optimization-release-checklist.md`, a reusable release
  candidate checklist with static, Codex-side, and VS Code/Copilot validation
  gates;
- `.cg-docs/cost/token-optimization-follow-ups.md`, a separate ledger for
  non-blocking follow-ups so release blockers do not get mixed with future
  cleanup;
- documentation updates in `docs/model-guide.md`, `docs/workflow.md`, and
  `docs/reference.md` covering model-picker policy, routed review behavior,
  `/cg-work review:*`, Knowledge Brain/context selectivity, audit commands,
  `.cg-docs/inbox/` holding-area status, and known runtime-validation limits;
- this solution entry, which captures the release-validation pattern for future
  prompt/context optimization work.

The final Codex-side validation evidence for Phase 7 was:

```text
python3 -m pytest scripts/tests/test_audit_context.py
# 67 passed

python3 scripts/cg_audit_context.py --root . --format both
# guardrail failures: 0
# guardrail warnings: 28
# premium usage: 0
# ordinary model-picker violations: 0
# missing model declarations: 0
# model drift: 0

git diff --check
# passed
```

The audit benchmark still reports the expected review-agent counts:

| Mode | Count |
|------|-------|
| light | 2 |
| standard | 8 |
| data-risk | 8 |
| architecture | 8 |
| full | 10 |

PowerShell was not available in the Codex environment, so the Pester safe
runner and runtime Copilot checks remain external validation items for
VS Code/PowerShell.

## Prevention

For future token, prompt, context-loading, or model-governance changes:

1. Keep model governance explicit: ordinary model-picker prompts omit `model:`,
   and premium usage must be user-initiated or justified by a dedicated
   workflow.
2. Keep review routing centralized: `/cg-review` and `/cg-work review:*` should
   continue to use `.github/shared/review-routing.contract.md`.
3. Keep context loading staged: ordinary workflows should query targeted
   context and Knowledge Brain topics instead of consuming broad generated
   artifacts by default.
4. Run static audit and Python tests before release, then complete manual
   VS Code/Copilot validation for model-picker and dispatch behavior.
5. Separate release blockers from follow-up ideas. `.cg-docs/inbox/` is a
   holding area, not an approved roadmap.
6. Capture the release pattern in `.cg-docs/solutions/` only after available
   validation has run and any skipped checks are documented.

## Related

- `.cg-docs/plans/phase2-model-governance-cleanup.md`
- `.cg-docs/plans/2026-06-05-cg-review-token-cost-phase3.md`
- `.cg-docs/plans/2026-06-06-cg-plan-work-context-slimming-phase4.md`
- `.cg-docs/plans/2026-06-07-token-optimization-phase5-brain-context-selectivity.md`
- `.cg-docs/plans/2026-06-08-token-optimization-phase6-benchmarks-guardrails.md`
- `.cg-docs/plans/2026-06-09-token-optimization-phase7-release-validation.md`
- `.cg-docs/cost/token-optimization-release-checklist.md`
- `.cg-docs/cost/token-optimization-follow-ups.md`
- `.cg-docs/solutions/testing-patterns/2026-06-08-token-optimization-benchmark-guardrails.md`
- `.cg-docs/solutions/testing-patterns/2026-06-15-inherited-model-picker-drift-equivalence.md`
- `.cg-docs/solutions/testing-patterns/2026-06-16-reviewed-warning-classifications-close-token-work.md`
