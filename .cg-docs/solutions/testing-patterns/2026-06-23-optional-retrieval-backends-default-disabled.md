---
date: 2026-06-23
title: "Optional retrieval backends must stay default-disabled during evaluation"
category: "testing-patterns"
language: "JSON/Python/Markdown"
tags: [retrieval, opt-in, privacy, token-efficiency, governance]
root-cause: "Evaluating retrieval candidates can be mistaken for approving or enabling them unless status, opt-in, and gate fields are tested"
severity: "P2"
plan: ".cg-docs/plans/2026-06-23-optional-retrieval-backend-evaluation.md"
---

# Optional Retrieval Backends Must Stay Default-Disabled During Evaluation

## Problem

Phase 1.2 added a deterministic local Brain query backend. Future retrieval
candidates are tempting, but adding a registry without guardrails can silently
turn evaluation into runtime configuration.

## Root Cause

Retrieval backend choices affect privacy, dependencies, offline behavior,
token budgets, and validation semantics. External or semantic retrieval can
also introduce credentials and network failure modes.

## Solution

Represent future candidates in `.github/shared/retrieval-backends.json` with
explicit status and gate fields:

- current backend: `native-brain-query`
- optional candidates: `default_enabled: false`
- opt-in required: `requires_explicit_opt_in: true`
- external candidates: `status: "deferred"` and `network_required: true`

Add tests that fail if an optional backend becomes default-enabled or if an
external backend is not deferred.

## Prevention

Keep retrieval backend evaluation separate from implementation. A future
backend needs its own roadmap item, privacy review, dependency review,
deterministic validation, rollback plan, and measured token-budget comparison.

## Related

- `.github/shared/retrieval-backends.json`
- `docs/retrieval-backends.md`
- `.cg-docs/plans/2026-06-23-knowledge-brain-query-budgeted-retrieval.md`
