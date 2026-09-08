---
date: 2026-06-23
title: "Budgeted Knowledge Brain query needs rendered-output budget gates"
category: "testing-patterns"
language: "Python/Markdown"
tags: [knowledge-brain, token-efficiency, cg-index, retrieval, testing]
root-cause: "The initial budget check counted selected snippets but not the final JSON/Markdown metadata, excluded notes, or captured warnings"
severity: "P2"
plan: ".cg-docs/plans/2026-06-23-knowledge-brain-query-budgeted-retrieval.md"
---

# Budgeted Knowledge Brain Query Needs Rendered-Output Budget Gates

## Problem

Phase 1.2 added `cg-index query` so workflow prompts can retrieve bounded Knowledge Brain context. The first implementation bounded selected snippets, but a real-repo smoke check showed final Markdown and JSON output could still exceed the requested budget after adding metadata, excluded notes, and Brain build warnings.

## Root Cause

The budget gate was applied before rendering. That undercounted output overhead and allowed raw Brain build warnings to escape the intended bounded context path.

## Solution

Budget the rendered JSON/Markdown representations, not only snippets. Query mode now captures Brain build warnings, truncates warning text, caps excluded notes, and trims selected snippets/items until the larger rendered representation fits the requested budget. If only one selected item remains, its path and reason are preserved before its snippet is removed.

## Prevention

For future token-bounded tools, test the final rendered output size. A payload-level estimate is not enough when the renderer adds headings, reasons, warnings, or excluded-item sections.

## Related

- `.cg-docs/plans/2026-06-23-knowledge-brain-query-budgeted-retrieval.md`
- `.cg-docs/solutions/testing-patterns/2026-06-08-token-optimization-benchmark-guardrails.md`
- `.cg-docs/solutions/testing-patterns/2026-06-22-workflow-telemetry-source-path-tool-extraction.md`
- `.cg-docs/solutions/data-quality/2026-08-28-exact-json-registry-mutation-boundaries.md` - applies the final-rendered-size rule to a persistent JSON registry
