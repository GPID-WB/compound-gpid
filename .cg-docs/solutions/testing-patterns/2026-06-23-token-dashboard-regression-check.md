---
date: 2026-06-23
title: "Token dashboards need explicit baseline/pass/fail semantics"
category: "testing-patterns"
language: "Python/Markdown/PowerShell"
tags: [token-efficiency, dashboard, regression, audit, measurement]
root-cause: "Machine-readable token audit outputs can be misread as savings evidence unless no-baseline, comparable-pass, and deterministic-fail states are separated"
severity: "P2"
plan: ".cg-docs/plans/2026-06-23-token-dashboard-regression-checks.md"
---

# Token Dashboards Need Explicit Baseline/Pass/Fail Semantics

## Problem

Workflow token artifacts made static prompt/context pressure visible, but a
maintainer still had to inspect multiple files to know whether the current run
was just a baseline, a comparable clean run, or a deterministic regression.

## Root Cause

The audit already had guardrails and optional `--baseline` deltas, but those
signals were not collected into a compact dashboard or a stable
machine-readable regression status. Without explicit status semantics, a
no-comparison audit can be mistaken for evidence that token usage improved.

## Solution

Write two additive artifacts from the existing `scripts/cg_audit_context.py`
pipeline:

- `.cg-docs/token/TOKEN-DASHBOARD.md` for maintainer-facing status, top workflow
  budgets, context signals, warning classifications, and observability
  boundaries.
- `.cg-docs/token/regression-check.json` for automation-friendly status.

Use these status meanings:

- `baseline`: no comparable previous audit was supplied.
- `pass`: a comparable baseline was supplied and deterministic guardrails have
  no failures.
- `fail`: deterministic guardrail failures are present.

Advisory warnings remain warnings. Do not turn token-saving hypotheses into
claims unless a comparable repository probe supports them.

## Prevention

Add tests for artifact writing and for each status state. The tests should use
small fabricated reports for status semantics so fixture-specific guardrail
warnings do not make the assertions brittle.

## Related

- `.cg-docs/token/TOKEN-DASHBOARD.md`
- `.cg-docs/token/regression-check.json`
- `.cg-docs/plans/2026-06-23-workflow-token-baseline.md`
- `.cg-docs/solutions/testing-patterns/2026-06-22-workflow-telemetry-source-path-tool-extraction.md`
