---
date: 2026-06-04
title: "Context and model-governance audit infrastructure"
status: decided
scope: "Standard"
chosen-approach: "Lightweight heuristic inventory (chars/4, reference counting, threshold classification)"
tags: [performance, tokens, model-governance, audit, cost-efficiency]
---
<!-- Valid status values: decided, in-progress, abandoned -->

# Context and Model-Governance Audit Infrastructure

## Context

GitHub Copilot's token-based pricing model makes context burden and model
selection directly cost-relevant. Compound GPID has 22 prompts, 17 agents,
20 skills, 3 instructions, a template, 4 brain files, and supporting docs —
all of which contribute to session token consumption. Prior work (April 2026)
completed a model audit and prose compression pass, but no reusable tooling
exists to measure context cost going forward.

Two prior brainstorms are related:
- `2026-04-07-full-model-audit.md` — classified model tiers heuristically
- `2026-04-20-reduce-late-sequence-token-cost.md` — compressed prompt prose

Neither produced a persistent measurement tool. This brainstorm fills that gap.

## Requirements

1. Produce a Python script (`scripts/cg_audit_context.py`) that inventories
   all context-contributing files with heuristic token estimates.
2. Use `chars / 4` for token estimation — no `tiktoken` dependency.
3. Generate a **Prompt Reference Matrix** by counting references (file names,
   agent dispatches, skill loads, tool mentions) — NOT a forced-read parser.
4. Inventory model declarations, flag missing declarations, and identify
   premium-model usage.
5. Apply predefined decision thresholds to classify optimization candidates.
6. Output both machine-readable (`.cg-docs/cost/context-audit.json`) and
   human-readable (`.cg-docs/cost/context-audit.md`) reports.
7. No refactoring of prompts, agents, skills, or instructions in this phase.
8. Implementation by Codex; validation in VS Code Copilot.

## Approaches Considered

### Approach 1: Full Semantic Forced-Read Analyzer

Parse prompt bodies semantically to determine exactly which files Copilot
will load at runtime for every execution path.

**Pros**: Precise mapping of runtime context.
**Cons**: High complexity. Requires interpreting prompt conditional logic,
skill loading patterns, and agent dispatch chains. Brittle to prompt edits.
**Effort**: Large
**Recommended?**: No — too complex for Phase 1. Reserve for Phase 2 on
top-cost workflows only.

### Approach 2: Lightweight Heuristic Inventory (CHOSEN)

Count characters, estimate tokens, count references by pattern-matching,
inventory model declarations, apply fixed thresholds.

**Pros**: Low complexity, fast to implement, immediately actionable output.
Stdlib-only Python, consistent with existing `cg_index.py` patterns.
**Cons**: Doesn't prove runtime context — only approximates. Can miss
dynamic context loading.
**Effort**: Small–Medium
**Recommended?**: Yes.

### Approach 3: tiktoken-Based Precise Counter

Same as Approach 2 but with `tiktoken` for exact token counts.

**Pros**: Accurate token counts.
**Cons**: Adds third-party dependency. False precision (Claude tokenizer
differs from OpenAI's). Marginal value over chars/4 for relative ranking.
**Effort**: Small (incremental over Approach 2)
**Recommended?**: No — unnecessary for Phase 1 goals.

## Decision

Approach 2 chosen. The audit should answer five questions with simple
heuristics:

1. Where are the biggest files?
2. Which prompts accumulate the most references?
3. Where are expensive models declared?
4. Where is model policy missing?
5. What should we optimize first?

## Decision Thresholds

### Immediate optimization candidate

- Always-on instruction file > 1,500 estimated tokens
- Always-on instruction file > 3,000 estimated tokens: critical
- Prompt file > 3,000 estimated tokens
- Prompt references 5+ context sources, agents, or skills
- Prompt references .cg-docs or BRAIN.md by default
- Prompt or agent declares premium model without escalation condition
- Agent declares broad tools and premium/reasoning model
- Skill landing page > 2,000 estimated tokens
- Duplicate paragraph block appears in 3+ files
- Duplicate text accounts for >1,000 estimated tokens across the repo

### Needs review

- Prompt file between 1,500–3,000 estimated tokens
- Agent file between 1,500–3,000 estimated tokens
- Skill landing page between 1,200–2,000 estimated tokens
- Model declaration missing from high-use prompt
- Model declaration unclear or inconsistent with docs/model-guide.md

### Probably acceptable

- Large reference file loaded only on demand
- Large Knowledge Brain artifact not read by default
- Long docs file not referenced by prompts or agents
- Large skill reference file that is not a SKILL.md landing page

## Next Steps

Create an implementation plan for Codex specifying files to add, tests to
write, output format, and validation steps.
