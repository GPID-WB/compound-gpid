---
date: 2026-06-23
title: "Command-output summary wrappers should preserve raw evidence without replacing validation"
category: "testing-patterns"
language: "Python/Shell/Markdown"
tags: [token-efficiency, summaries, validation, pester-safety, git]
root-cause: "Noisy validation, diff, log, tree, and diagnostics surfaces can flood agent context when raw output is copied directly into chat"
severity: "P2"
plan: ".cg-docs/plans/2026-06-23-command-output-summarization-wrappers.md"
---

# Command-Output Summary Wrappers Should Preserve Raw Evidence Without Replacing Validation

## Problem

Compound GPID workflows often need evidence from tests, diffs, logs, repository trees, and diagnostics. Copying raw output into the agent context is noisy, but discarding raw output loses auditability.

## Root Cause

Before Phase 1.3, the repo had workflow token baselines and budgeted Brain retrieval, but no native helper for compact command-output summaries. Agents had to choose between broad raw output reads and hand-written ad hoc summaries.

## Solution

Add local stdlib summary tooling in `scripts/cg_summary.py` with thin shell wrappers:

- `cg-test-summary`
- `cg-diff-summary`
- `cg-log-summary`
- `cg-tree-summary`
- `cg-problems-summary`

The wrappers emit compact JSON or Markdown summaries to stdout and write redacted raw/source artifacts under `.cg-docs/token/outputs/YYYYMMDD-HHMMSS-<kind>/`. `cg-test-summary` only reads `tests/last-run.json`; it never runs Pester or replaces `tests/Run-Tests.ps1`.

## Prevention

For future token-efficiency tooling, keep these boundaries explicit:

- Summaries are evidence views, not validation commands.
- Raw/source artifacts must be redacted before writing.
- Transient raw-output directories belong under `.cg-docs/token/outputs/` and should not be committed.
- Token-saving or cost-saving impact remains a hypothesis until measured with the same workflow probe.

## Related

- `.cg-docs/plans/2026-06-23-command-output-summarization-wrappers.md`
- `.cg-docs/solutions/testing-patterns/2026-06-23-budgeted-knowledge-brain-query.md`
- `.cg-docs/solutions/testing-patterns/2026-06-22-workflow-telemetry-source-path-tool-extraction.md`
