---
date: 2026-06-23
depth: architecture
type: standard
plan: .cg-docs/plans/2026-06-23-knowledge-brain-query-budgeted-retrieval.md
findings: {}
---

# Review Report: Knowledge Brain Query and Budgeted Retrieval

**Review mode**: architecture  
**Files reviewed**: `scripts/cg_index.py`, `scripts/brain/query.py`, `scripts/brain/tests/test_query.py`, `.github/skills/cg-skill-brain-query/SKILL.md`, `tests/prompt-tools.Tests.ps1`, `docs/reference.md`, `docs/workflow.md`, `roadmap.json`.

## Findings

No significant issues found after the rendered-budget fix. The implementation is local/stdlib-only, preserves existing `cg-index` modes, captures Brain build warnings instead of emitting raw stderr from query mode, and keeps manual `BRAIN.md` fallback instructions.

## Passed

- `cg-index query` validates intent, budget, and format.
- JSON and Markdown outputs are parseable/bounded and include selection reasons, stale/conflict flags, confidence, and heuristic token estimates.
- Prompt/skill contract preserves no-wholesale `brain-index.json` and `BRAIN-NN.md` rules.
- No external retrieval backend, vector dependency, command-output wrapper, or token-saving claim was introduced.

