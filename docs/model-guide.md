# Model Guide

Reference for model assignments across all 26 Compound GPID prompt and agent files.
Covers the tier classification criteria, per-file rationale, manual override guidance,
and approximate token cost reference.

> **Drift protection**: Pester tests in `tests/model-assignments.Tests.ps1` ("Model assignments — prompt
> files" and "Model assignments — agent files" describe blocks) validate all 26 files for model:
> frontmatter presence, and count sentinels detect unexpected additions. The tests validate
> against inline constants — update both the file's frontmatter **and** the inline constants when
> changing a tier intentionally.

---

## Model Assignment Table

### Prompts

| File | Assigned Model | Task Description | Tier Rationale | Status |
|------|---------------|------------------|----------------|--------|
| `cg-strategy.prompt.md` | Claude Opus 4.6 | Full project visioning and milestone structuring | Orchestration 5, reasoning 5, creativity 4 — Opus required | confirmed |
| `cg-brainstorm.prompt.md` | Claude Opus 4.6 | Guided Q&A to clarify fuzzy requirements with pushback | Reasoning 4, creativity 4, multi-round dialogue — borderline Opus/Sonnet; kept Opus pending empirical test | borderline-pending |
| `cg-plan.prompt.md` | Claude Opus 4.6 | Deep codebase research + structured implementation plan | Reasoning 4, precision 4, multi-step orchestration — borderline Opus/Sonnet; kept Opus pending empirical test | borderline-pending |
| `cg-work.prompt.md` | Claude Sonnet 4.6 | Step-by-step implementation from a plan | Precision 5, tool use 5, reasoning 3 — Sonnet sufficient | confirmed |
| `cg-review.prompt.md` | Claude Sonnet 4.6 | Multi-agent review orchestrator (dispatches up to 10 agents: 8 standard + 2 thorough-only) | Orchestration 5, precision 5 — must coordinate subagents reliably | confirmed |
| `cg-fixbug.prompt.md` | Claude Sonnet 4.6 | Structured bug-fix: reproduce, diagnose, fix, verify | Reasoning 4, precision 5 — test-driven diagnosis needs Sonnet | confirmed |
| `cg-release.prompt.md` | Claude Sonnet 4.6 | Create GitHub Release with curated notes (developer-only) | Reasoning 4, creativity 4, multi-step — Sonnet appropriate | confirmed |
| `cg-compound.prompt.md` | Claude Sonnet 4.6 | Capture solved problems as reusable knowledge | Creativity 4 for generalisation — Haiku risks shallow lessons | confirmed |
| `cg-fix-triage.prompt.md` | Claude Sonnet 4.6 | Apply saved review findings by ID or priority | Fix quality directly affects review loop length — keep Sonnet | confirmed |
| `cg-setup.prompt.md` | Claude Haiku 4.5 | Configure project or load context for returning projects | Reasoning 2, creativity 1 — mechanical scaffolding with conditional logic Haiku handles well | **changed** |
| `cg-devtag.prompt.md` | Claude Haiku 4.5 | Create a pre-release dev tag and push to origin (developer-only) | 3 git commands with clear rules — Haiku sufficient | **changed** |
| `cg-resume.prompt.md` | Claude Haiku 4.5 | Load context, scan pending work, resume interrupted sessions | Reasoning 3, mechanical context scanning — Haiku appropriate | confirmed |
| `cg-compound-refresh.prompt.md` | Claude Sonnet 4.6 | Audit `.cg-docs/solutions/` for staleness, drift, and consolidation | Orchestration 3, precision 4 — multi-step audit with conditional actions needs Sonnet | confirmed |
| `cg-ideate.prompt.md` | Claude Opus 4.6 | Generate, critique, and filter project improvement ideas | Creativity 5, reasoning 4 — divergent idea generation and adversarial filtering needs Opus | confirmed |
| `cg-diagnose.prompt.md` | Claude Sonnet 4.6 | Diagnose VS Code crashes — inspect logs, classify crash category, recommend recovery | Reasoning 4, precision 4 — log analysis and decision-tree classification needs Sonnet | confirmed |

### Agents

| File | Assigned Model | Task Description | Tier Rationale | Status |
|------|---------------|------------------|----------------|--------|
| `cg-architecture.agent.md` | Claude Sonnet 4.6 | Review project structure, modularity, dependencies | Reasoning 5, creativity 4 — architectural judgment needs Sonnet | confirmed |
| `cg-performance.agent.md` | Claude Sonnet 4.6 | Review vectorisation, memory efficiency, algorithm complexity | Reasoning 5, creativity 4 — performance diagnosis needs Sonnet | confirmed |
| `cg-data-quality.agent.md` | Claude Sonnet 4.6 | Review input validation, types, missing values | Reasoning 5, creativity 4 — data correctness risks need Sonnet | confirmed |
| `cg-code-quality.agent.md` | Claude Haiku 4.5 | Review style, linting, DRY, naming | Reasoning 4, creativity 3; checklist-style — Haiku sufficient | confirmed |
| `cg-testing.agent.md` | Claude Haiku 4.5 | Review test coverage, edge cases, quality | Reasoning 4, creativity 3; structured review — Haiku sufficient | confirmed |
| `cg-documentation.agent.md` | Claude Haiku 4.5 | Review roxygen2/docstrings, README, comments | Reasoning 3, creativity 2; pattern-matching — Haiku appropriate | confirmed |
| `cg-version-control.agent.md` | Claude Haiku 4.5 | Review commit hygiene, branching, secrets | Reasoning 3, creativity 2; checklist review — Haiku appropriate | confirmed |
| `cg-reproducibility.agent.md` | Claude Haiku 4.5 | Review lockfiles, relative paths, seeds | Reasoning 4, creativity 3; structured review — Haiku sufficient | confirmed |
| `cg-learnings-researcher.agent.md` | Claude Haiku 4.5 | Cross-reference past solutions in `.cg-docs/solutions/` | Reasoning 3; primarily search and retrieval — Haiku appropriate | confirmed |
| `cg-roadmap.agent.md` | Claude Haiku 4.5 | Manage `roadmap.json`: add/remove milestones, update statuses | Reasoning 3; JSON manipulation with clear schema — Haiku sufficient | confirmed |
| `cg-adversarial.agent.md` | Claude Sonnet 4.6 | Adversarial code reviewer — finds race conditions, edge cases, security vulnerabilities | Reasoning 4, precision 5 — attack-vector analysis and proof-of-concept generation needs Sonnet | confirmed |

---

## Tier Classification Criteria

These criteria were used during the 2026-04-07 audit. Reuse them for future file additions
or tier reassessments.

| Criterion | Haiku 4.5 | Sonnet 4.6 | Opus 4.6 |
|-----------|-----------|------------|----------|
| Reasoning depth (1–5) | 1–3 | 3–4 | 5 |
| Creative judgment (1–5) | 1–2 | 3–4 | 4–5 |
| Multi-step orchestration (1–5) | 1–2 | 3–4 | 5 |
| Subagent dispatch | none | light | heavy |
| Instruction-following precision | any tier handles this well | any | any |

**Decision logic:**
- `max(reasoning, creativity) ≤ 3` AND `orchestration ≤ 2` → **Haiku candidate**
- `max(reasoning, creativity) ≥ 5` AND `orchestration ≥ 5` → **Opus required**
- Everything else → **Sonnet**

**Tiebreaker rules applied in this audit:**
- `cg-fix-triage`: Even though reasoning is low, kept on Sonnet — fix quality directly affects the
  review-fix-review loop. Degraded fixes lengthen the loop and cost more overall.
- `cg-compound`: Creativity score of 4 for lesson generalisation is risky on Haiku — shallow
  lessons reduce the compound-docs value proposition.
- `cg-code-quality`, `cg-testing`, `cg-reproducibility`: Kept on Haiku. Second reviews sometimes
  find new issues, but this is caused by fresh code introduced during fixing, not Haiku missing
  issues in unchanged lines. Monitor; if second reviews consistently flag unchanged lines, revisit.

---

## Manual Override Guidance

VS Code lets you switch models per-session using the model picker in the Copilot Chat
toolbar. This is the correct escape hatch — **do not change frontmatter for temporary overrides**.

### When to override

| Symptom | Action |
|---------|--------|
| `/cg-brainstorm` isn't pushing back enough | Switch to Opus in the model picker |
| `/cg-plan` misses codebase connections | Switch to Opus in the model picker |
| `/cg-setup` is unexpectedly slow | Confirm it's on Haiku (check frontmatter); if already Haiku, it's a network issue |
| A review agent produces an empty or garbled output | Re-run `/cg-review` and switch that specific agent to Sonnet in the picker |
| `/cg-work` misses the intent of a complex step | Switch to Opus for the session |
| Lesson in `/cg-compound` output feels generic | Switch to Sonnet or Opus in the picker |

### How to switch

1. Open a new Copilot Chat panel (or the existing one).
2. Click the model name in the toolbar (top-right of the chat input area).
3. Select the desired model from the dropdown.
4. Re-run the prompt.

The override applies only to that session. Frontmatter defaults persist across sessions.

---

## Token Cost Reference

Approximate relative cost ratios. Exact pricing changes; use these only for order-of-magnitude reasoning.

| Model | Relative Cost | Best For |
|-------|--------------|----------|
| Claude Haiku 4.5 | ~1× (cheapest) | Checklist reviews, mechanical tasks, JSON manipulation, short structured outputs |
| Claude Sonnet 4.6 | ~5× | Implementation, multi-agent orchestration, reasoning-heavy reviews |
| Claude Opus 4.6 | ~25× | Strategic thinking, complex architecture, creative problem-solving at depth |

For current Claude pricing, see [Anthropic pricing](https://www.anthropic.com/pricing).

**Practical implication**: A full `/cg-review standard` run dispatches 8 agents. With 5 on Haiku
and 3 on Sonnet, the blended cost is far lower than if all 8 were on Sonnet. This is the primary
token saving from the 2026-04-07 audit.

---

## Version Mapping

The Copilot display names used in frontmatter map to Anthropic API versions as follows:

| Copilot display name | Anthropic model family | Notes |
|----------------------|------------------------|-------|
| `Claude Haiku 4.5 (copilot)` | claude-haiku-4-5 | Fastest, cheapest tier |
| `Claude Sonnet 4.6 (copilot)` | claude-sonnet-4-6 | Balanced performance/cost |
| `Claude Opus 4.6 (copilot)` | claude-opus-4-6 | Highest capability |

**Maintenance**: If Copilot renames or upgrades models (e.g., Haiku 4.5 → 4.6), all frontmatter
strings and count sentinels in `tests/model-assignments.Tests.ps1` must be updated together.
Check the Copilot model picker dropdown for current available names.

---

## Audit Maintenance

| Field | Value |
|-------|-------|
| Last validated | 2026-04-07 |
| Next validation due | 2026-10-07 (6-month cadence) |

**Triggers for early re-audit**:
- A Claude model in the frontmatter is sunset or renamed by Anthropic/Copilot
- Copilot announces a new model tier that could replace an existing tier
- Empirical validation of borderline candidates (cg-brainstorm, cg-plan) produces results
- Second `/cg-review` runs consistently flag issues in unchanged lines (monitor cg-code-quality, cg-testing, cg-reproducibility)

---

## Borderline Candidates (Pending Empirical Validation)

These files were intentionally kept at their current tier pending side-by-side output comparison.
See the empirical validation protocol in `.cg-docs/plans/2026-04-07-full-model-audit.md` Step 7.

| File | Current | Proposed | Test Criterion |
|------|---------|----------|----------------|
| `cg-brainstorm.prompt.md` | Opus 4.6 | Sonnet 4.6 | Does Sonnet push back as critically? Does Q&A depth hold? |
| `cg-plan.prompt.md` | Opus 4.6 | Sonnet 4.6 | Does the plan cover the same codebase connections? Same step granularity? |

To run a validation test, follow the protocol in the plan: run both tiers on the same representative
task, compare on (1) instruction compliance, (2) finding/question depth, (3) nothing missed, (4) output structure.

**Current status**: Testing not yet started (scheduled for a future session). Until then, use
these files normally — their current Opus 4.6 tiers are safe. They may be downgraded to Sonnet
if empirical testing confirms parity. Results will be documented here when available.
