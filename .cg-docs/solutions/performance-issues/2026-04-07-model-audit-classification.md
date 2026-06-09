---
date: 2026-04-07
title: "Full model audit — classification methodology and results"
category: "performance-issues"
language: "both"
tags: [model-audit, tokens, performance, prompts, agents, haiku, sonnet, opus]
root-cause: "All prompts and agents launched with default model assignments that were never systematically reviewed, causing over-spend on Opus and under-utilization of Haiku"
severity: "P2"
status: applied
plan: ".cg-docs/plans/2026-04-07-full-model-audit.md"
brainstorm: ".cg-docs/brainstorms/2026-04-07-full-model-audit.md"
---

# Full Model Audit — Classification Methodology and Results

> **Decision rationale**: The hybrid approach used in this audit (tier matrix with tiebreaker
> rules rather than per-file empirical testing first) was chosen during the brainstorm session
> in `.cg-docs/brainstorms/2026-04-07-full-model-audit.md`. The key insight was that high-confidence
> decisions (clearly Haiku or clearly Opus) could be applied immediately; borderline cases
> (cg-brainstorm, cg-plan) were deferred to empirical validation.

## Problem

All 12 prompts and 10 agents in Compound GPID launched with default model
assignments that were never systematically reviewed. Several high-complexity
prompts (cg-strategy, cg-plan, cg-brainstorm) were on Opus when the task
didn't require it, and several mechanical prompts (cg-setup, cg-devtag) were
on Sonnet when Haiku would suffice. The result was unnecessary token spend and
slower responses.

## Classification Framework

The audit used a 5-axis task complexity scoring matrix:

| Axis | What it measures | Haiku range | Sonnet range | Opus range |
|------|-----------------|-------------|--------------|------------|
| Reasoning depth | Multi-step inference, causal chains | 1–3 | 3–4 | 5 |
| Creative judgment | Generating novel framings, synthesis | 1–2 | 3–4 | 4–5 |
| Instruction precision | Following conditional/branching rules | any | any | any |
| Multi-step orchestration | Coordinating sub-tasks or agents | 1–2 | 3–4 | 5 |
| Tool use complexity | File I/O, git ops, JSON manipulation | any | any | any |

**Decision rule:**
- `max(reasoning, creativity) ≤ 3` AND `orchestration ≤ 2` → Haiku candidate
- `max(reasoning, creativity) ≥ 5` AND `orchestration ≥ 5` → Opus required
- Everything else → Sonnet

**Critical override rule:** When fix quality directly affects an iterative
loop (review → fix → re-review), the fixer should stay at Sonnet regardless
of raw complexity scores, because degraded fixes lengthen the loop and cost
more total tokens.

## Per-File Scores

### Prompts

| File | Reasoning | Creativity | Orchestration | Assigned | Rationale |
|------|:---------:|:----------:|:-------------:|----------|-----------|
| cg-strategy | 5 | 4 | 5 | Opus 4.6 | All three axes at max — Opus justified |
| cg-brainstorm | 4 | 4 | 4 | Opus 4.6 | Borderline; kept pending empirical test |
| cg-plan | 4 | 3 | 4 | Opus 4.6 | Borderline; kept pending empirical test |
| cg-work | 3 | 2 | 4 | Sonnet 4.6 | Precision 5, tool use 5 — Sonnet confirmed |
| cg-review | 4 | 3 | 5 | Sonnet 4.6 | Orchestration 5, dispatches 9 agents |
| cg-fixbug | 4 | 3 | 4 | Sonnet 4.6 | Reasoning 4, precision 5 — Sonnet confirmed |
| cg-release | 4 | 4 | 4 | Sonnet 4.6 | Creativity 4, multi-step — Sonnet confirmed |
| cg-compound | 3 | 4 | 3 | Sonnet 4.6 | Creativity 4 for lesson generalisation — Haiku risky |
| cg-fix-triage | 2 | 2 | 4 | Sonnet 4.6 | Loop-quality override: fix quality affects review-fix-review cycle |
| cg-setup | 2 | 1 | 5 | **Haiku 4.5** | Reasoning 2, creativity 1 — mechanical scaffolding **CHANGED** |
| cg-devtag | 2 | 1 | 3 | **Haiku 4.5** | 3 git commands, clear rules — Haiku sufficient **CHANGED** |
| cg-resume | 3 | 2 | 3 | Haiku 4.5 | Mechanical context scanning — already Haiku, confirmed |

### Agents

| File | Reasoning | Creativity | Orchestration | Assigned | Rationale |
|------|:---------:|:----------:|:-------------:|----------|-----------|
| cg-architecture | 5 | 4 | 1 | Sonnet 4.6 | Reasoning 5, creativity 4 — Sonnet confirmed |
| cg-performance | 5 | 4 | 1 | Sonnet 4.6 | Reasoning 5, creativity 4 — Sonnet confirmed |
| cg-data-quality | 5 | 4 | 1 | Sonnet 4.6 | Reasoning 5, creativity 4 — Sonnet confirmed |
| cg-code-quality | 4 | 3 | 1 | Haiku 4.5 | Checklist-style — Haiku confirmed |
| cg-testing | 4 | 3 | 1 | Haiku 4.5 | Structured review — Haiku confirmed |
| cg-reproducibility | 4 | 3 | 1 | Haiku 4.5 | Structured review — Haiku confirmed |
| cg-learnings-researcher | 3 | 4 | 2 | Haiku 4.5 | Mostly search/retrieval, not reasoning — Haiku confirmed |
| cg-roadmap | 3 | 2 | 2 | Haiku 4.5 | JSON manipulation with clear schema — Haiku confirmed |
| cg-documentation | 3 | 2 | 1 | Haiku 4.5 | Pattern-matching review — Haiku confirmed |
| cg-version-control | 3 | 2 | 1 | Haiku 4.5 | Checklist review — Haiku confirmed |

## Changes Applied (2026-04-07)

**High-confidence downgrades:**

| File | From | To | Reasoning |
|------|------|----|-----------|
| `cg-setup.prompt.md` | Sonnet 4.6 | Haiku 4.5 | Reasoning 2, creativity 1 — all conditional logic is structural (if/else on project state), not inference-heavy. Haiku handles this well. |
| `cg-devtag.prompt.md` | Sonnet 4.6 | Haiku 4.5 | 3 git commands: git fetch, parse tags, git tag + push. Clear rules, no creative judgment needed. |

**Documentation fix (reference.md discrepancy resolved):**

| Agent | Was documented as | Actual file value | Corrected to |
|-------|-------------------|-------------------|--------------|
| `cg-learnings-researcher` | Sonnet 4.6 in reference.md | Haiku 4.5 in agent file | Haiku 4.5 |

## Borderline Candidates (Not Changed)

These files were reviewed and intentionally left at their current tier.
Re-test using the empirical validation protocol in the plan (Step 7) before changing.

| File | Current | Proposed | Hold Reason |
|------|---------|----------|-------------|
| `cg-brainstorm.prompt.md` | Opus 4.6 | Sonnet 4.6 | Pushback quality and multi-turn dialogue depth not yet empirically tested at Sonnet |
| `cg-plan.prompt.md` | Opus 4.6 | Sonnet 4.6 | Codebase connection depth and plan granularity not yet tested at Sonnet |

## Tiebreaker Decisions

**`cg-fix-triage` kept on Sonnet despite low complexity scores:**
The user observed that running `/cg-review light` after `/cg-fix-triage` still surfaces
new findings. Investigation showed this is caused by new code introduced during fixing,
not Haiku-quality fixes. However, the risk is real: a poor fix on Haiku could introduce
subtler issues that only surface in the next cycle. The loop-quality override rule was
applied: keep the fixer at Sonnet.

**`cg-code-quality`, `cg-testing`, `cg-reproducibility` kept on Haiku:**
Same second-review pattern observed. Conclusion: second reviews find issues in *new code*,
not in code that Haiku previously reviewed and missed. Monitor: if future second reviews
consistently flag issues in *unchanged* lines that Haiku previously cleared, revisit.

## Drift Prevention

A parametrised Pester test (`tests/prompt-tools.Tests.ps1` — "Model assignments")
validates all 22 files against expected model strings. The test catches any unannounced
model change. When intentionally changing a tier:

Phase 6 generalized this drift-prevention pattern into generated benchmark and
guardrail output for prompt token size, model-picker behavior, broad context
loading, Knowledge Brain retrieval, and review-routing burden. See
`.cg-docs/solutions/testing-patterns/2026-06-08-token-optimization-benchmark-guardrails.md`.
1. Update the file's `model:` frontmatter.
2. Update the expected value in the Pester test.
3. Update `docs/model-guide.md` — change "confirmed" to "changed" in the Status column.
4. Add an entry to this solutions file in the "Changes Applied" table.
