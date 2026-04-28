---
date: 2026-04-23
repo: "gsd-2"
repo-url: "https://github.com/gsd-build/gsd-2"
release-reviewed: "v2.77.0"
review-type: "full"
features-found: 22
directly-applicable: 4
needs-adaptation: 5
not-applicable: 13
---

# GSD Assessment — v2.77.0

## Overview

GSD-2 is a standalone CLI application (not a prompt framework) built on the Pi SDK. It is the most feature-rich project in this comparison (6.5k stars, 86 contributors, 113 releases, 24 bundled extensions), but most of its value comes from runtime capabilities (state machines, crash recovery, parallel orchestration, SQLite databases) that cannot be replicated in a Copilot prompt/agent model. GSD structures work as Milestone → Slice → Task, with the iron rule that a task must fit in one context window. It supports 20+ LLM providers, headless CI mode, and cost tracking.

## Concept Mapping

GSD's "commands" (`/gsd auto`, `/gsd discuss`, `/gsd status`) are runtime commands for its CLI, not prompt files. Its "extensions" are TypeScript modules with tool registration and lifecycle hooks — far richer than our skills. GSD's `.gsd/` directory stores state files (STATE.md, DECISIONS.md, KNOWLEDGE.md) which parallel our `.cg-docs/` but are machine-managed. GSD "skills" are similar to ours — markdown documents with trigger conditions. The key difference: GSD controls the agent runtime; compound-gpid provides instructions to Copilot's runtime.

## Features — Directly Applicable

### Feature: Decisions Register (Append-Only)
- **Source**: GSD v2.77.0 — DECISIONS.md
- **What it does**: Maintains an append-only register of architectural decisions made during a project, automatically captured during discussion and planning phases. Each decision has context, rationale, and alternatives considered.
- **How source implements it**: `.gsd/DECISIONS.md` file automatically populated during `/gsd discuss` and planning phases. Injected into every dispatch prompt for context.
- **Compatibility**: Directly applicable
- **Why this verdict**: We have `.cg-docs/solutions/` for capturing solutions but no running decisions register. This would help maintain project-level decision history.
- **How we'd adapt it**: Add a `DECISIONS.md` section to brainstorm and plan outputs that captures key architectural decisions. Accumulate across sessions via `/cg-compound` or automatically.
- **Maps to**: prompt
- **Effort**: Small
- **Priority**: High
- **Decision criteria check**:
  - Implementable in Copilot model? Yes — it's a file convention
  - Benefits GPID team workflows? Yes — economists frequently need to document methodology decisions
  - Duplicates existing feature? No — our `.cg-docs/solutions/` captures bugs/patterns, not decisions
  - Effort proportional to value? Yes
- **Notes**: This is particularly valuable for GPID work where methodology choices (poverty line, deflator, survey weights) need documented rationale.

### Feature: Knowledge Extraction Across Sessions
- **Source**: GSD v2.76.0 — `/gsd extract-learnings`
- **What it does**: Extracts patterns, lessons, and reusable knowledge from completed work and stores it in a structured KNOWLEDGE.md file that is injected into future sessions.
- **How source implements it**: `/gsd extract-learnings` command reads completed task summaries, extracts cross-cutting lessons, and writes to `.gsd/KNOWLEDGE.md`. Also builds a knowledge graph.
- **Compatibility**: Directly applicable
- **Why this verdict**: Our `/cg-compound` already captures solutions. Adding automatic extraction from completed work would increase capture rate.
- **How we'd adapt it**: Enhance `/cg-compound` or add a `/cg-extract` prompt that reads recent session history and `.cg-docs/` to identify undocumented patterns worth capturing.
- **Maps to**: prompt
- **Effort**: Small
- **Priority**: Medium
- **Decision criteria check**:
  - Implementable in Copilot model? Yes
  - Benefits GPID team workflows? Yes — captures institutional knowledge
  - Duplicates existing feature? Enhances existing `/cg-compound`
  - Effort proportional to value? Yes
- **Notes**: The key insight is automated extraction vs. manual `/cg-compound` invocation. Could be offered at the end of `/cg-work`.

### Feature: Verification Commands (Post-Task Enforcement)
- **Source**: GSD v2.77.0 — `verification_commands` preference
- **What it does**: Configurable shell commands (lint, test, type-check) that run automatically after each task execution. Failures trigger auto-fix retries before advancing.
- **How source implements it**: `verification_commands` preference lists commands. After each task, GSD runs them. If any fail, it retries up to `verification_max_retries` times.
- **Compatibility**: Directly applicable
- **Why this verdict**: Our `/cg-work` doesn't enforce verification between tasks. Adding configurable checks would catch regressions early.
- **How we'd adapt it**: Add a `verification-commands` section to `compound-gpid.local.md` (e.g., `["Rscript -e 'testthat::test_dir(\"tests\")'"]`). After each task in `/cg-work`, run these via `execution_subagent` and retry on failure.
- **Maps to**: prompt + instruction
- **Effort**: Medium
- **Priority**: Medium
- **Decision criteria check**:
  - Implementable in Copilot model? Yes — via execution_subagent
  - Benefits GPID team workflows? Yes — catches regressions in data pipelines
  - Duplicates existing feature? No
  - Effort proportional to value? Yes
- **Notes**: Different from SP's verification-before-completion — this is configurable per-project, not a generic "prove it works" step.

### Feature: Rapid Codebase Assessment (/gsd scan)
- **Source**: GSD v2.76.0
- **What it does**: Quick structural assessment of a codebase — file counts, language distribution, architecture patterns, potential issues — without deep analysis.
- **How source implements it**: `/gsd scan` command that reads the codebase structure and produces a summary report.
- **Compatibility**: Directly applicable
- **Why this verdict**: We have no quick codebase overview tool. This would help when onboarding to a new project.
- **How we'd adapt it**: Could be a mode of `/cg-setup` or a standalone `/cg-scan` prompt that produces a quick structural overview using `list_dir`, `file_search`, and `grep_search`.
- **Maps to**: prompt
- **Effort**: Small
- **Priority**: Low
- **Decision criteria check**:
  - Implementable in Copilot model? Yes
  - Benefits GPID team workflows? Yes — useful for new project onboarding
  - Duplicates existing feature? No
  - Effort proportional to value? Yes
- **Notes**: Lower priority since Copilot already has good codebase exploration tools.

## Features — Needs Adaptation

### Feature: Context Mode (Automatic Context Assembly)
- **Source**: GSD v2.77.0
- **What it does**: Automatically assembles task-ready context before each dispatch — pulls relevant artifacts, prior session state, milestone signals, and execution metadata. Reduces manual prompt assembly.
- **How source implements it**: `context_mode` preference enables automatic context building. GSD reads `.gsd/` state files, task plans, and prior summaries to construct the optimal prompt.
- **Compatibility**: Needs adaptation
- **Why this verdict**: This is partially achieved by our `compound-gpid.context.md` but it's manual. Automatic context assembly requires runtime control we don't have. Could partially implement via instruction files.
- **How we'd adapt it**: Expand `compound-gpid.context.md` with a conventions section that prompts auto-read project context at session start. Add a `/cg-resume` enhancement that pre-loads relevant `.cg-docs/` files.
- **Maps to**: instruction
- **Effort**: Medium
- **Priority**: Medium
- **Decision criteria check**:
  - Implementable in Copilot model? Partially — Copilot reads context files but doesn't do dynamic assembly
  - Benefits GPID team workflows? Yes
  - Duplicates existing feature? Enhances existing context files
  - Effort proportional to value? Yes
- **Notes**: We can approximate this via better instruction files and context files, even without GSD's runtime control.

### Feature: Token Optimization Profiles (Budget/Balanced/Quality)
- **Source**: GSD v2.77.0 — `token_profile` preference
- **What it does**: Three preset profiles that coordinate model selection, phase skipping, and context compression to reduce token usage by 40-60%.
- **How source implements it**: `token_profile: budget` selects cheaper models, skips research phases, and minimizes context inlining. `quality` does the opposite. `balanced` is the default.
- **Compatibility**: Needs adaptation
- **Why this verdict**: Copilot doesn't let us select models per-task. But the concept of review depth tiers (which we already have as light/standard/thorough) could be extended to other prompts.
- **How we'd adapt it**: Extend our existing `review-depth` concept to `/cg-brainstorm` and `/cg-plan` with depth tiers that control how many sub-steps are executed.
- **Maps to**: prompt
- **Effort**: Medium
- **Priority**: Low
- **Decision criteria check**:
  - Implementable in Copilot model? Partially — can't control model, but can control thoroughness
  - Benefits GPID team workflows? Yes — some tasks need quick output, not thorough analysis
  - Duplicates existing feature? Extends existing review-depth concept
  - Effort proportional to value? Marginal
- **Notes**: Our review-depth tiers (light/standard/thorough) already implement part of this for code review.

### Feature: Dashboard / Status Command
- **Source**: GSD v2.77.0 — `/gsd status`
- **What it does**: Real-time overlay showing current milestone, slice, and task progress; auto mode elapsed time; per-unit cost; and token breakdown.
- **How source implements it**: TUI dashboard with `Ctrl+Alt+G` shortcut and `/gsd status` command. Reads state from `.gsd/` files and SQLite database.
- **Compatibility**: Needs adaptation
- **Why this verdict**: Requires TUI capabilities not available in Copilot. But a status summary from roadmap/plan files could provide similar value.
- **How we'd adapt it**: Enhance `/cg-resume` to provide a structured status summary: what's done, what's in progress, what's next. Read from `roadmap.json` and recent `.cg-docs/` files.
- **Maps to**: prompt
- **Effort**: Small
- **Priority**: Low
- **Decision criteria check**:
  - Implementable in Copilot model? Partially — text-based summary, not real-time overlay
  - Benefits GPID team workflows? Yes — project orientation
  - Duplicates existing feature? Enhances existing `/cg-resume`
  - Effort proportional to value? Yes
- **Notes**: Our `/cg-resume` already provides session recovery. A status mode would add project-level awareness.

### Feature: Structured Memory System
- **Source**: GSD v2.76.0–v2.77.0 — ADR-013
- **What it does**: Typed memory system with capture, query, relationships/knowledge graph, hybrid retrieval, and maintenance. Memories persist across sessions with scope tags and structured fields.
- **How source implements it**: SQLite `memories` table as single source of truth. Capture via `capture_thought` tool, query via `memory_query`, graph via `gsd_graph`. Decay, export/import, cap cascade.
- **Compatibility**: Needs adaptation
- **Why this verdict**: Copilot already has its own memory system (`/memories/`). But GSD's structured fields and knowledge graph concepts could enhance how we use our memory files.
- **How we'd adapt it**: Use our existing `/memories/repo/` for project-scoped knowledge. Create structured conventions for memory file format (YAML frontmatter with tags, scope, decay date).
- **Maps to**: instruction
- **Effort**: Medium
- **Priority**: Low
- **Decision criteria check**:
  - Implementable in Copilot model? Partially — we have memory but not structured query
  - Benefits GPID team workflows? Marginal — our memory usage is already functional
  - Duplicates existing feature? Enhances existing memory system
  - Effort proportional to value? No — Medium effort for marginal improvement
- **Notes**: The Copilot memory system is simpler but adequate. GSD's complexity comes from its standalone runtime needs.

### Feature: Remote Questions (Slack/Discord)
- **Source**: GSD v2.77.0
- **What it does**: When auto-mode needs human input in headless/CI mode, routes the question to Slack or Discord for remote answering.
- **How source implements it**: Remote questions extension with Slack and Discord integrations. Headless mode detects blocking questions and routes them.
- **Compatibility**: Needs adaptation
- **Why this verdict**: Copilot doesn't run headless, but the concept of routing questions to external channels during long-running work could be useful for team coordination.
- **How we'd adapt it**: Not directly applicable to Copilot. Could potentially route via GitHub issues or PR comments for async team decisions.
- **Maps to**: script
- **Effort**: Large
- **Priority**: Low
- **Decision criteria check**:
  - Implementable in Copilot model? No — Copilot is interactive, not headless
  - Benefits GPID team workflows? Marginal
  - Duplicates existing feature? No
  - Effort proportional to value? No
- **Notes**: This is fundamentally a headless/CI feature. Not relevant to Copilot's interactive model.

## Features — Not Applicable

### Feature: Auto Mode (Autonomous State Machine)
- **Source**: GSD v2.77.0 — `/gsd auto`
- **Compatibility**: Not applicable
- **Why this verdict**: Requires a standalone runtime with state machine, fresh sessions per task, crash recovery, and PID monitoring. Copilot cannot control its own session lifecycle.

### Feature: Fresh Session Per Task
- **Source**: GSD v2.77.0
- **Compatibility**: Not applicable
- **Why this verdict**: Copilot maintains a single conversation session. Cannot create fresh context windows per task.

### Feature: Crash Recovery with Lock Files
- **Source**: GSD v2.77.0
- **Compatibility**: Not applicable
- **Why this verdict**: Requires background process monitoring and session forensics. Copilot sessions don't crash in the same way — they just end.

### Feature: Cost Tracking Per-Unit Ledger
- **Source**: GSD v2.77.0 — `metrics.json`
- **Compatibility**: Not applicable
- **Why this verdict**: Token/cost tracking requires API-level access to model usage. Copilot doesn't expose token counts to prompts.

### Feature: Stuck Detection (Sliding Window)
- **Source**: GSD v2.77.0
- **Compatibility**: Not applicable
- **Why this verdict**: Requires runtime monitoring of dispatch patterns. Not possible in a prompt-based system.

### Feature: Timeout Supervision
- **Source**: GSD v2.77.0 — soft/idle/hard timeouts
- **Compatibility**: Not applicable
- **Why this verdict**: Requires process-level timeout management. Copilot manages its own timeouts.

### Feature: Dynamic Model Routing
- **Source**: GSD v2.77.0 — complexity-based routing
- **Compatibility**: Not applicable
- **Why this verdict**: Copilot doesn't let prompts select models. Model selection is user-controlled in VS Code.

### Feature: Headless Mode for CI
- **Source**: GSD v2.77.0 — `gsd headless`
- **Compatibility**: Not applicable
- **Why this verdict**: Copilot is an interactive tool. No headless/CI execution model.

### Feature: HTML Reports
- **Source**: GSD v2.77.0 — self-contained milestone reports
- **Compatibility**: Not applicable
- **Why this verdict**: Requires runtime generation of HTML with inlined CSS/JS, SVG dependency graphs, and cost metrics. Overkill for our prompt-based workflow.

### Feature: Parallel Orchestration
- **Source**: GSD v2.77.0
- **Compatibility**: Not applicable
- **Why this verdict**: Multi-worker parallel milestone execution requires standalone runtime coordination. Copilot subagents are sequential.

### Feature: Git Worktree Isolation with Squash Merge
- **Source**: GSD v2.77.0
- **Compatibility**: Not applicable
- **Why this verdict**: Complex worktree lifecycle management with automated squash merge. Too complex for prompt-based implementation and not needed for GPID workflows.

### Feature: 24 Bundled Extensions (Browser, MCP, Voice, etc.)
- **Source**: GSD v2.77.0
- **Compatibility**: Not applicable
- **Why this verdict**: Extensions are TypeScript modules with tool registration. Copilot's tool system is platform-managed, not user-extensible.

### Feature: Progressive Planning (ADR-011)
- **Source**: GSD v2.76.0 — sketch-then-refine with mid-execution escalation
- **Compatibility**: Not applicable
- **Why this verdict**: Requires runtime state machine to detect mid-execution issues and escalate to replanning. Not possible in a single Copilot session.

## Summary

GSD-2 is the most technically ambitious project in this review, but its value comes primarily from runtime capabilities (state machine, crash recovery, cost tracking, parallel execution) that are fundamentally impossible in Copilot's prompt/agent model. The transferable ideas are conceptual rather than implementable:

1. **Decisions register** (High/Small) — append-only decision log is a file convention, not a runtime feature
2. **Knowledge extraction** (Medium/Small) — automatic learning capture enhances existing `/cg-compound`
3. **Verification commands** (Medium/Medium) — configurable post-task checks via `execution_subagent`
4. **Codebase assessment scan** (Low/Small) — quick structural overview for onboarding

GSD demonstrates what a standalone AI development tool can achieve, but most of its innovations require runtime control that Copilot prompts don't have. The conceptual takeaways (decisions registers, verification enforcement, context assembly) are the main value.

+ 4 additional minor features noted but not carded: two-terminal workflow pattern, doctor health checks, workflow templates, and skill staleness decay.
