---
date: 2026-04-23
repo: "superpowers"
repo-url: "https://github.com/obra/superpowers"
release-reviewed: "v5.0.7"
review-type: "full"
features-found: 16
directly-applicable: 5
needs-adaptation: 4
not-applicable: 7
---

# SP Assessment — v5.0.7

## Overview

Superpowers is a software development methodology framework built as composable skills with automatic triggering via hooks. It has 166k stars and 28 contributors, making it the most popular project in this comparison. It works across Claude Code, Codex, Cursor, Copilot CLI, OpenCode, and Gemini CLI. The philosophy emphasizes TDD, systematic debugging, and subagent-driven development. Skills auto-trigger based on context rather than requiring explicit invocation.

## Concept Mapping

Superpowers' "skills" are auto-triggered behavioral modules (equivalent to our instructions + skills). Their "hooks" inject context at session start (equivalent to our `.github/instructions/` files). They don't have a concept of "prompts" or "agents" in the compound-gpid sense — everything is skill-based with automatic triggering. Their brainstorm server is a unique browser-based design review tool with no compound-gpid equivalent.

## Features — Directly Applicable

### Feature: Inline Self-Review Replacing Subagent Review Loops
- **Source**: SP v5.0.6
- **What it does**: Replaced slow subagent-dispatched review loops (~25 min overhead) with inline self-review checklists that catch 3–5 real bugs per run in ~30 seconds, with comparable defect rates.
- **How source implements it**: Brainstorming and writing-plans skills now include an inline "Self-Review checklist" (placeholder scan, internal consistency, scope check, ambiguity check) instead of spawning a fresh agent for review.
- **Compatibility**: Directly applicable
- **Why this verdict**: Our `/cg-plan-review` dispatches `cg-plan-critic` as a separate agent. An inline self-review step within `/cg-plan` itself could catch obvious issues faster without the overhead of a separate agent dispatch.
- **How we'd adapt it**: Add a "Self-Review" step at the end of `/cg-brainstorm` and `/cg-plan` that runs a quick checklist (placeholder scan, scope check, completeness check) before presenting output. Keep `/cg-plan-review` for thorough multi-agent review.
- **Maps to**: prompt
- **Effort**: Small
- **Priority**: High
- **Decision criteria check**:
  - Implementable in Copilot model? Yes
  - Benefits GPID team workflows? Yes — catches low-hanging issues without extra dispatch
  - Duplicates existing feature? Partially — lighter version of /cg-plan-review
  - Effort proportional to value? Yes
- **Notes**: SP's regression testing showed subagent review added time without quality improvement. This is a data point, not proof our `/cg-plan-review` is wasteful — our review agents do different things (architecture, testing, performance). But an inline pre-check is free.

### Feature: Verification-Before-Completion Skill
- **Source**: SP v5.0.7 — skill: `verification-before-completion`
- **What it does**: Before declaring any task complete, requires the agent to verify its work actually works — run tests, check output, validate behavior. Prevents "it should work" claims without evidence.
- **How source implements it**: A skill that activates before any completion declaration, requiring the agent to run verification steps and present evidence.
- **Compatibility**: Directly applicable
- **Why this verdict**: Our `/cg-work` doesn't systematically verify each task before marking it done. Adding verification would catch incomplete implementations.
- **How we'd adapt it**: Add a verification step to `/cg-work` that runs relevant checks (tests, lint, type-check) after each task and before marking it complete. Use `get_errors` tool.
- **Maps to**: prompt
- **Effort**: Small
- **Priority**: High
- **Decision criteria check**:
  - Implementable in Copilot model? Yes — `get_errors` and `execution_subagent` are available
  - Benefits GPID team workflows? Yes
  - Duplicates existing feature? No
  - Effort proportional to value? Yes
- **Notes**: This is essentially "run tests after implementing" codified as a mandatory step rather than optional.

### Feature: Systematic Debugging Skill (4-Phase Root Cause)
- **Source**: SP v5.0.7 — skill: `systematic-debugging`
- **What it does**: Enforces a 4-phase debugging process: reproduce → isolate → identify root cause → fix with defense-in-depth. Includes root-cause-tracing, defense-in-depth, and condition-based-waiting techniques.
- **How source implements it**: A skill with detailed methodology for each phase, including anti-patterns (e.g., "don't guess and fix — reproduce first").
- **Compatibility**: Directly applicable
- **Why this verdict**: Our `/cg-fixbug` and `/cg-diagnose` exist but lack the structured 4-phase methodology. Adding the systematic approach as a skill would improve debugging quality.
- **How we'd adapt it**: Enhance `/cg-fixbug` with a structured 4-phase approach: (1) reproduce, (2) isolate, (3) root cause, (4) fix + verify. Add as skill content.
- **Maps to**: skill
- **Effort**: Small
- **Priority**: Medium
- **Decision criteria check**:
  - Implementable in Copilot model? Yes
  - Benefits GPID team workflows? Yes — debugging data pipelines benefits from systematic approach
  - Duplicates existing feature? Partially — enhances existing /cg-fixbug
  - Effort proportional to value? Yes
- **Notes**: SP's approach is language-agnostic and would work for R/Python/Stata debugging.

### Feature: Auto-Triggered Skills via Hooks
- **Source**: SP v5.0.7 — core architecture
- **What it does**: Skills activate automatically based on context (e.g., "brainstorming" triggers before writing code, "test-driven-development" triggers during implementation). No explicit user invocation needed.
- **How source implements it**: Session-start hooks inject context about available skills. The agent checks for relevant skills before any task. Skills have trigger conditions in their frontmatter.
- **Compatibility**: Directly applicable
- **Why this verdict**: Our skills require explicit loading via `read_file`. Copilot's `applyTo` instruction mechanism could partially automate this.
- **How we'd adapt it**: Expand our `.github/instructions/` files with more specific trigger patterns. Add `applyTo` patterns that match common task contexts (e.g., testing instructions auto-apply when test files are open).
- **Maps to**: instruction
- **Effort**: Small
- **Priority**: Medium
- **Decision criteria check**:
  - Implementable in Copilot model? Yes — Copilot supports `applyTo` in instructions
  - Benefits GPID team workflows? Yes — reduces skill discovery friction
  - Duplicates existing feature? Enhances existing — we already have `applyTo` for R/Python/Stata
  - Effort proportional to value? Yes
- **Notes**: We already auto-apply R/Python/Stata instructions by file extension. Could expand to auto-apply testing, visualization, and data quality skills.

### Feature: Writing-Skills Skill (Meta-Skill for Creating Skills)
- **Source**: SP v5.0.7 — skill: `writing-skills`
- **What it does**: A skill that teaches how to create new skills — structure, frontmatter, testing methodology. Ensures consistent quality across the skill library.
- **How source implements it**: A SKILL.md file with templates, best practices, and testing requirements for new skill creation.
- **Compatibility**: Directly applicable
- **Why this verdict**: We create skills ad hoc. A meta-skill would standardize the process.
- **How we'd adapt it**: Create a `cg-skill-writing-skills` that documents our SKILL.md format, required sections, description length limits, and testing expectations.
- **Maps to**: skill
- **Effort**: Small
- **Priority**: Low
- **Decision criteria check**:
  - Implementable in Copilot model? Yes
  - Benefits GPID team workflows? Yes — standardizes skill creation
  - Duplicates existing feature? No
  - Effort proportional to value? Yes
- **Notes**: Low priority since we don't create skills frequently, but useful documentation.

## Features — Needs Adaptation

### Feature: Subagent-Driven Development with Two-Stage Review
- **Source**: SP v5.0.7 — skill: `subagent-driven-development`
- **What it does**: Dispatches a fresh subagent per task with two-stage review: first checks spec compliance, then code quality. Provides fast iteration with isolated context per task.
- **How source implements it**: Each task gets a fresh subagent. After completion, two review passes check (1) does the output match the spec? and (2) is the code quality acceptable?
- **Compatibility**: Needs adaptation
- **Why this verdict**: Our `/cg-work` doesn't use subagents per task. Copilot's `runSubagent` could enable this pattern but context injection differs from Claude Code.
- **How we'd adapt it**: Add an optional `--subagent` mode to `/cg-work` where each task is dispatched to a `runSubagent` call with focused context. Review happens inline after each task.
- **Maps to**: prompt
- **Effort**: Large
- **Priority**: Low
- **Decision criteria check**:
  - Implementable in Copilot model? Partially — `runSubagent` exists but context management differs
  - Benefits GPID team workflows? Yes — isolation prevents context pollution
  - Duplicates existing feature? No
  - Effort proportional to value? No — Large effort for uncertain benefit in Copilot
- **Notes**: The SP approach relies heavily on Claude Code's session management. Copilot subagents are stateless, making this harder.

### Feature: Brainstorm Server (Browser-Based Design Review)
- **Source**: SP v5.0.6 — `brainstorm-server`
- **What it does**: Launches a local web server that presents the brainstorm design document in a browser for easier reading and section-by-section approval. Restructured to separate content from state.
- **How source implements it**: Node.js server that serves HTML pages with the brainstorm output. Agent writes to `content/`, server state in `state/`. Owner-PID monitoring for lifecycle management.
- **Compatibility**: Needs adaptation
- **Why this verdict**: Requires launching a local server and browser, which Copilot can do via `run_in_terminal` and `open_browser_page`. But the value prop is weaker in VS Code where you already have the editor.
- **How we'd adapt it**: Could render brainstorm output as a VS Code webview or formatted markdown preview instead of a standalone server. Lighter-weight approach.
- **Maps to**: script
- **Effort**: Large
- **Priority**: Low
- **Decision criteria check**:
  - Implementable in Copilot model? Partially
  - Benefits GPID team workflows? Marginal — VS Code already has good markdown preview
  - Duplicates existing feature? No
  - Effort proportional to value? No
- **Notes**: The browser approach makes sense for CLI-based tools. In VS Code, markdown preview is sufficient.

### Feature: Execution Handoff (User Choice Between Subagent and Inline)
- **Source**: SP v5.0.5
- **What it does**: After plan writing, gives the user a choice between subagent-driven execution (automated, fresh context per task) and inline execution (manual, same session).
- **How source implements it**: A menu after plan completion with two options, with subagent-driven recommended but not mandatory.
- **Compatibility**: Needs adaptation
- **Why this verdict**: Our `/cg-work` always runs inline. Offering a choice would give users more control. Needs adaptation for Copilot's subagent model.
- **How we'd adapt it**: After plan acceptance in `/cg-work`, offer via `vscode_askQuestions`: "Execute inline (same session)" vs "Execute per-task (fresh context each)".
- **Maps to**: prompt
- **Effort**: Medium
- **Priority**: Low
- **Decision criteria check**:
  - Implementable in Copilot model? Partially
  - Benefits GPID team workflows? Marginal
  - Duplicates existing feature? No
  - Effort proportional to value? No — Medium effort for uncertain UX benefit
- **Notes**: The subagent execution model is less proven in Copilot than in Claude Code.

### Feature: Copilot CLI SessionStart Context Injection
- **Source**: SP v5.0.7
- **What it does**: Detects `COPILOT_CLI` environment and injects bootstrap context via the SDK-standard `additionalContext` format at session start.
- **How source implements it**: Session-start hook checks for `COPILOT_CLI` env var and emits `{ "additionalContext": "..." }` with full skills bootstrap.
- **Compatibility**: Needs adaptation
- **Why this verdict**: This is relevant for Copilot CLI users, but compound-gpid currently targets VS Code only. Would need exploration of Copilot CLI plugin model.
- **How we'd adapt it**: Investigate whether compound-gpid could support Copilot CLI alongside VS Code. Would require exploring the plugin format compatibility.
- **Maps to**: script
- **Effort**: Large
- **Priority**: Low
- **Decision criteria check**:
  - Implementable in Copilot model? Unknown — CLI plugin model may differ
  - Benefits GPID team workflows? Marginal — team primarily uses VS Code
  - Duplicates existing feature? No
  - Effort proportional to value? No
- **Notes**: Low priority unless team starts using Copilot CLI.

## Features — Not Applicable

### Feature: Git Worktree Isolation
- **Source**: SP v5.0.7 — skill: `using-git-worktrees`
- **Compatibility**: Not applicable
- **Why this verdict**: Requires native git worktree management which is complex in Copilot. Our `cg-skill-git-workflow` handles branching conventionally. Worktrees add complexity without clear benefit for data science workflows.

### Feature: Test-Driven Development Enforcement
- **Source**: SP v5.0.7 — skill: `test-driven-development`
- **Compatibility**: Not applicable
- **Why this verdict**: TDD enforcement (delete code written before tests) is too aggressive for data science workflows where exploratory coding is common. Our testing requirements are already documented in testing skills.

### Feature: Dispatching Parallel Agents
- **Source**: SP v5.0.7 — skill: `dispatching-parallel-agents`
- **Compatibility**: Not applicable
- **Why this verdict**: Copilot subagents don't support true parallel dispatch the way Claude Code does. Our multi-agent review already runs agents sequentially via `runSubagent`.

### Feature: Finishing a Development Branch
- **Source**: SP v5.0.7 — skill: `finishing-a-development-branch`
- **Compatibility**: Not applicable
- **Why this verdict**: This handles worktree cleanup and merge decisions. We don't use worktrees and our git workflow is simpler.

### Feature: Receiving Code Review Skill
- **Source**: SP v5.0.7 — skill: `receiving-code-review`
- **Compatibility**: Not applicable
- **Why this verdict**: Teaches the agent how to respond to human code review feedback. Our `/cg-fix-triage` already handles applying review findings systematically.

### Feature: Using Superpowers (Intro Skill)
- **Source**: SP v5.0.7 — skill: `using-superpowers`
- **Compatibility**: Not applicable
- **Why this verdict**: Meta-documentation about the Superpowers system itself. Not transferable.

### Feature: OpenCode One-Line Plugin Install
- **Source**: SP v5.0.4
- **Compatibility**: Not applicable
- **Why this verdict**: Platform-specific installation mechanism for OpenCode. Not relevant to our Copilot-only distribution.

## Summary

Superpowers' most valuable contribution is its emphasis on verification and self-review as mandatory workflow steps. Top recommendations:

1. **Inline self-review in plan/brainstorm** (High/Small) — proven to catch issues without subagent overhead
2. **Verification-before-completion** (High/Small) — mandatory "prove it works" step before task completion
3. **Systematic debugging methodology** (Medium/Small) — structured 4-phase approach enhances /cg-fixbug
4. **Expanded auto-triggering skills** (Medium/Small) — leverage existing `applyTo` mechanism more broadly
5. **Meta-skill for writing skills** (Low/Small) — standardize skill creation process

The browser-based brainstorm server and subagent-driven development are interesting but don't translate well to Copilot's model.
