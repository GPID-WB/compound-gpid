---
date: 2026-06-08
title: "Token optimization needs benchmark guardrails, not one-off audits"
category: "testing-patterns"
language: "Python/PowerShell/Markdown"
tags: [token-optimization, benchmark, guardrails, audit, model-governance, context-loading, review-routing]
root-cause: "Prompt and context optimizations can drift after implementation unless benchmark output and regression guardrails are generated and tested as part of the audit workflow"
severity: "P2"
plan: ".cg-docs/plans/2026-06-08-token-optimization-phase6-benchmarks-guardrails.md"
reviewed-in: ".cg-docs/reviews/2026-06-08-token-optimization-phase6-benchmarks-guardrails-review.md"
---

# Token Optimization Needs Benchmark Guardrails, Not One-Off Audits

## Problem

Phases 2-5 reduced token and model-cost risk by removing ordinary-workflow
premium defaults, making `/cg-review` and `/cg-work` routing conditional,
slimming high-frequency prompts, and making Knowledge Brain/context loading
selective. Those improvements were easy to regress because most of the behavior
lived in prompt text and generated audit output rather than conventional code
paths.

The release-readiness question for Phase 6 was therefore not "can we run another
manual prompt slimming pass?" It was "can maintainers repeatedly measure the
same risk surface and catch drift before merge?"

## Root Cause

The earlier audit established the context/model inventory, but it did not yet
act as a benchmark suite. Without generated benchmark rows and explicit
guardrail severities, maintainers had to manually inspect prompts for prompt
token growth, ordinary prompt model drift, model-picker regressions, broad
context loading, `/cg-review` route precedence drift, `/cg-work review:*`
ambiguity, and review-agent dispatch burden.

Manual inspection is too brittle for token optimization because a small wording
change can restore costly always-on context or dispatch behavior without
breaking any functional test.

## Solution

Extend the existing audit tooling instead of creating a separate benchmark
architecture.

The Phase 6 implementation added benchmark and guardrail output to
`scripts/cg_audit_context.py`:

- a static workflow benchmark for `/cg-plan`, `/cg-work`, `/cg-review`,
  `/cg-compound`, `/cg-resume`, and Knowledge Brain/context lookup behavior;
- prompt estimated tokens, character counts, reference counts, model-picker
  state, context-loading signals, review-routing signals, and review-agent
  counts where statically measurable;
- optional `--baseline <context-audit.json>` comparison for before/after
  summaries, including compatibility with older audit JSON that lacks a
  `benchmark` section;
- guardrail failures for policy-breaking regressions such as ordinary workflow
  premium models, model-picker explicit `model:` declarations, broad ordinary
  prompt context loading, lost `/cg-review` route precedence, and missing
  `/cg-work review:*` modes;
- guardrail warnings for intentional maintenance broad-read behavior and prompt
  size thresholds that should be reviewed but do not automatically block.

Regression coverage now has two layers:

```text
python3 -m pytest scripts/tests/test_audit_context.py
```

validates benchmark construction, baseline deltas, guardrail classification,
review-agent count parsing, and Markdown/JSON rendering.

```powershell
. tests\Run-Tests.ps1
```

keeps the Pester prompt-contract checks for model governance, model-picker
handling, context-loading language, review routing, and `/cg-work` review modes.

The generated audit report is now the release-readiness artifact:

```text
python3 scripts/cg_audit_context.py --root . --output-dir .cg-docs/cost --format both
python3 scripts/cg_audit_context.py --root . --output-dir .cg-docs/cost --format both --baseline <baseline-json>
```

Review `Benchmark Summary`, `Guardrails`, `Before/After Comparison`,
`Top Remaining Optimization Candidates`, `Release-Readiness Checklist`, and the
manual VS Code/Copilot checklist before merging token-optimization changes.

## Prevention

Treat token optimization as a benchmarked contract, not a one-time cleanup.

When changing prompts, context-loading rules, model governance, or review
routing:

1. Extend the existing audit script if the measurement derives from the same
   prompt/context inventory. Create a separate benchmark script only if the
   audit script becomes structurally too broad.
2. Add a Python test for every new audit metric or guardrail severity.
3. Add or update Pester prompt-contract tests for prompt-visible behavior.
4. Run the audit and inspect both machine-readable JSON and Markdown output.
5. Avoid documentation wording that trips the audit itself. In Phase 6, a docs
   line that mentioned both `.cg-docs/cost/context-audit.md` and
   `Context Loading Risks` looked like a broad-load instruction and created a
   self-warning. Keep path references and broad-load labels separated unless the
   line is intentionally describing a load rule.
6. Leave runtime validation to VS Code/Copilot where static checks cannot prove
   behavior: model-picker behavior, `/cg-work review:auto|manual|none`,
   `/cg-review light|data-risk|full`, and Knowledge Brain selective retrieval.

## Related

- `.cg-docs/plans/2026-06-08-token-optimization-phase6-benchmarks-guardrails.md` - implementation plan for Phase 6 benchmarks, guardrails, and release readiness
- `.cg-docs/reviews/2026-06-08-token-optimization-phase6-benchmarks-guardrails-review.md` - review report and fixed self-warning finding
- `.cg-docs/solutions/testing-patterns/2026-04-28-prompt-guard-conditions-need-immediate-pester-coverage.md` - prompt guard text needs regression coverage
- `.cg-docs/solutions/performance-issues/2026-04-07-model-audit-classification.md` - earlier model audit classification and drift-prevention pattern
- `.cg-docs/solutions/testing-patterns/2026-05-14-classification-step-must-exhaustively-cover-enum-values.md` - classification logic must cover every declared value
- `.cg-docs/solutions/testing-patterns/2026-05-12-source-scanning-regression-guard-for-scripting-anti-patterns.md` - source scanning as a regression guard for textual anti-patterns
- `.cg-docs/solutions/testing-patterns/2026-06-15-inherited-model-picker-drift-equivalence.md` - inherited model-picker prompts need semantic equivalence in model-guide drift checks
