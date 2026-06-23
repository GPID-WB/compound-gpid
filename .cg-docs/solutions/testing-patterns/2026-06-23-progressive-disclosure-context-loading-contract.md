---
date: 2026-06-23
title: "Progressive-disclosure prompt cleanup should preserve semantics with explicit expansion rationale"
category: "testing-patterns"
language: "Markdown/Python/PowerShell"
tags: [token-efficiency, context-loading, prompts, audit, progressive-disclosure]
root-cause: "Prompt and agent wording can accidentally imply broad default reads even when the intended behavior is structured or maintenance-only"
severity: "P2"
plan: ".cg-docs/plans/2026-06-23-progressive-disclosure-scoped-instructions.md"
---

# Progressive-Disclosure Prompt Cleanup Should Preserve Semantics With Explicit Expansion Rationale

## Problem

Broad phrases such as "read roadmap.json" or "scan .cg-docs" can be interpreted as default whole-artifact loading. That increases context pressure and makes static audit findings harder to distinguish from intentional maintenance reads.

## Root Cause

Some prompts and agents had correct behavior but ambiguous wording. Maintenance workflows legitimately need full structured artifacts, while ordinary workflows should use Stage 0-4 context loading, budgeted Brain query, and targeted headings/snippets.

## Solution

Use the shared context-loading contract language directly:

- For ordinary workflows, prefer targeted headings, selected snippets, and structured fields.
- For maintenance workflows that require full artifacts, write `Context expansion: reading <artifact/section> because <reason>.`
- For release and learning workflows, list filenames or search selected categories before opening full documents.
- Keep existing prompt semantics intact and validate with prompt-tools plus the deterministic token audit.

## Prevention

Add tests around the wording patterns that matter. Phase 1.4 added audit tests for explicit expansion rationale and structured roadmap-field parsing, then regenerated `.cg-docs/cost/*` and `.cg-docs/token/*` artifacts to prove guardrail behavior.

## Related

- `.github/shared/context-loading.contract.md`
- `.cg-docs/plans/2026-06-23-progressive-disclosure-scoped-instructions.md`
- `.cg-docs/solutions/testing-patterns/2026-06-23-budgeted-knowledge-brain-query.md`
- `.cg-docs/solutions/testing-patterns/2026-06-23-command-output-summary-wrappers.md`
