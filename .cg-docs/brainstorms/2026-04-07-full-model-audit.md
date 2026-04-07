---
date: 2026-04-07
title: "Full model audit across prompts and agents"
status: decided
chosen-approach: "Heuristic classification + targeted empirical validation"
tags: [performance, model-audit, tokens, prompts, agents]
---

# Full Model Audit Across Prompts and Agents

## Context

The Performance milestone includes a "Full model audit across prompts and agents" feature.
The plugin has 22 files with model assignments (12 prompts + 10 agents) spread across
three Claude tiers: Opus 4.6 (3 prompts), Sonnet 4.6 (8 prompts + 4 agents), and
Haiku 4.5 (1 prompt + 6 agents). No quality problems have been observed, but token
consumption and session latency are concerns. The user's priority order: quality >
tokens > speed.

## Requirements

1. **Audit all 22 model-assigned files** — classify each by task complexity and determine
   whether the current model tier is appropriate, over-tiered (wasteful), or under-tiered
   (quality risk).
2. **Apply frontmatter changes** — update `model:` fields where the audit identifies savings
   with no quality risk.
3. **Create a model selection guide** — reference document for users explaining which models
   are assigned to which tasks, rationale, and manual override guidance (via VS Code model
   picker).
4. **Add retry guidance to `/cg-review`** — for subagent dispatch cases, instruct the
   orchestrator to note incomplete subagent output in the review report so the user can
   re-run at a higher tier manually.
5. **No automated fallback mechanism** — the `model:` field is static YAML resolved before
   prompt execution; VS Code Copilot has no retry/fallback API. Automated model switching
   is not feasible.
6. **No GPT model fallbacks** — prompts are tuned for Claude's instruction-following style.
   Recommending GPT models without empirical testing per-prompt would be promising untested
   behavior. GPT models are out of scope for this audit.
7. **No `compound-gpid.local.md` model overrides** — runtime config cannot override frontmatter
   model selection. A config field would be misleading.
8. **Protect quality** — never downgrade a model tier without either (a) strong heuristic
   justification that the task is mechanical/checklist-style, or (b) empirical validation
   on a representative task.

## Approaches Considered

### Approach 1: Heuristic Task-Complexity Classification

Classify each file by cognitive tier (reasoning depth, creativity, multi-step orchestration),
map to cheapest adequate model, apply changes.

**Pros**: Fast, single session.
**Cons**: Subjective, no empirical validation, risk of quality regression on edge cases.
**Effort**: Small.

### Approach 2: Empirical Test-Driven Audit

Test each file at current tier and proposed cheaper tier on representative tasks. Only
downgrade if cheaper model produces equivalent output.

**Pros**: Evidence-based, catches quality regressions.
**Cons**: 22 files x 2+ tiers = 44+ manual test runs. No scriptable API.
**Effort**: Large.

### Approach 3: Heuristic Classification + Targeted Empirical Validation (CHOSEN)

Heuristic classification first to identify 4-6 candidates for change. Empirically test
only the borderline candidates. Ship clear-win changes immediately, gate borderline
changes on test results.

**Pros**: Best effort/confidence ratio. Protects quality on borderline cases, ships obvious
savings immediately.
**Cons**: Still requires some manual testing for borderline cases.
**Effort**: Medium (classification in one session, targeted testing in follow-up).

## Decision

Approach 3 chosen. Quality is non-negotiable — any model downgrade must be justified by
either clear heuristic reasoning (task is mechanical/checklist) or empirical evidence.
Token efficiency is the primary optimization target; computing time can be sacrificed
for token savings.

### Deliverables

1. **Model assignment table** — audit document with current model, recommended model,
   rationale, and confidence level for each of the 22 files. Lives in `.cg-docs/`.
2. **Frontmatter changes** — update `model:` fields in prompts/agents where audit finds
   savings with high confidence.
3. **Model selection guide section** — user-facing notes in documentation explaining tier
   assignments and manual override guidance.
4. **Retry guidance in `/cg-review`** — lightweight instruction for the review orchestrator
   to flag incomplete subagent output, recommending manual re-run at higher tier.

### Explored and rejected

- **Automated fallback** (platform limitation — no retry API)
- **GPT model fallbacks** (untested cross-model prompt compatibility)
- **`compound-gpid.local.md` overrides** (config cannot override frontmatter at runtime)
- **Duplicated escalation agents** (file proliferation + maintenance burden outweighs benefit)

## Next Steps

1. Hand off to `/cg-plan` to create a detailed implementation plan.
2. Plan should include the heuristic classification criteria, candidate identification
   process, empirical test protocol for borderline cases, and the three deliverable formats.

## Side Ideas Captured During Brainstorm

These were registered in the Quality Loop milestone as separate `idea` features:

- **Honest pushback mode in `/cg-brainstorm` and `/cg-strategy`** — add critical, honest
  evaluation of user ideas (not pushback for its own sake, but genuine assessment of
  feasibility and trade-offs).
- **Side-idea capture during brainstorming (save to roadmap)** — mechanism within
  `/cg-brainstorm` to save tangential ideas that emerge during discussion to the roadmap
  without derailing the current brainstorm.
