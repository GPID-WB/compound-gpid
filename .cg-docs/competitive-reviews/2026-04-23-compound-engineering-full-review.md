---
date: 2026-04-23
repo: "compound-engineering"
repo-url: "https://github.com/EveryInc/compound-engineering-plugin"
release-reviewed: "compound-engineering-v3.0.1"
review-type: "full"
features-found: 18
directly-applicable: 6
needs-adaptation: 5
not-applicable: 7
---

# CE Assessment — compound-engineering-v3.0.1

## Overview

Compound Engineering is the most architecturally similar project to compound-gpid. It follows an identical philosophy: brainstorm → plan → work → review → compound. It ships 36 skills and 51 agents across Claude Code, Codex, Cursor, Copilot, and other platforms. v3.0.0 (2026-04-22) was a breaking release renaming all skills/agents to a consistent `ce-` prefix. The project is maintained by Every Inc (15.3k stars, 57 contributors) and is TypeScript-based.

## Concept Mapping

CE's slash commands (`/ce-brainstorm`, `/ce-plan`, `/ce-work`, `/ce-code-review`, `/ce-compound`) map directly to compound-gpid's prompts. CE "skills" provide domain expertise (like our SKILL.md files), and CE "agents" delegate specialized review work (like our `cg-*` agents). CE stores compounded knowledge in `.ce-docs/` which parallels our `.cg-docs/`.

## Features — Directly Applicable

### Feature: Per-Finding Judgment Loop in Interactive Review
- **Source**: CE v3.0.0 — [#590](https://github.com/EveryInc/compound-engineering-plugin/issues/590)
- **What it does**: In interactive review mode, the reviewer pauses after each finding and lets the user accept, reject, or modify it before moving on — rather than dumping all findings at once.
- **How source implements it**: `ce-review` prompt has an "Interactive mode" that loops through findings one at a time, presenting each with context and waiting for user judgment.
- **Compatibility**: Directly applicable
- **Why this verdict**: Our `/cg-review` dispatches agents and collects findings into a report. Adding an interactive mode where users triage findings inline would improve signal-to-noise.
- **How we'd adapt it**: Add a `mode:interactive` flag to `/cg-review` that presents findings one at a time via `vscode_askQuestions`, letting the user accept/dismiss each before moving to the next agent.
- **Maps to**: prompt
- **Effort**: Medium
- **Priority**: High
- **Decision criteria check**:
  - Implementable in Copilot model? Yes
  - Benefits GPID team workflows? Yes
  - Duplicates existing feature? No
  - Effort proportional to value? Yes
- **Notes**: This pairs well with our existing `/cg-fix-triage` which already does post-hoc triage. Interactive mode moves triage inline with review.

### Feature: End-to-End ID Traceability (Brainstorm → Plan)
- **Source**: CE v3.0.0 — [#629](https://github.com/EveryInc/compound-engineering-plugin/issues/629), [#632](https://github.com/EveryInc/compound-engineering-plugin/issues/632)
- **What it does**: Requirements from brainstorming get unique IDs (R-IDs) that carry through to plan items (U-IDs), creating a traceable chain from requirement to implementation task.
- **How source implements it**: `ce-brainstorm` assigns R-IDs to requirements in the output doc. `ce-plan` reads these and generates U-IDs with origin traces back to the R-IDs.
- **Compatibility**: Directly applicable
- **Why this verdict**: Our brainstorm → plan pipeline currently has no formal traceability. Adding IDs would help verify plan completeness against requirements.
- **How we'd adapt it**: Modify `/cg-brainstorm` output template to include numbered requirement IDs. Modify `/cg-plan` to reference these IDs in task descriptions and add a coverage matrix.
- **Maps to**: prompt
- **Effort**: Small
- **Priority**: High
- **Decision criteria check**:
  - Implementable in Copilot model? Yes
  - Benefits GPID team workflows? Yes — especially for complex data pipeline plans
  - Duplicates existing feature? No
  - Effort proportional to value? Yes
- **Notes**: This is a template change, not a code change. Low risk, high traceability benefit.

### Feature: Release Notes Browsing Skill
- **Source**: CE v2.68.0 — [#589](https://github.com/EveryInc/compound-engineering-plugin/issues/589)
- **What it does**: A skill that lets users browse the plugin's own release history to understand what changed and when.
- **How source implements it**: `ce-release-notes` skill provides structured access to the CHANGELOG/release history.
- **Compatibility**: Directly applicable
- **Why this verdict**: We have `RELEASE_NOTES.md` and a release system but no way for users to browse history from within a session.
- **How we'd adapt it**: Create a `/cg-releases` prompt or skill that reads `RELEASE_NOTES.md` and presents version history, or fetches from GitHub releases.
- **Maps to**: prompt
- **Effort**: Small
- **Priority**: Low
- **Decision criteria check**:
  - Implementable in Copilot model? Yes
  - Benefits GPID team workflows? Yes — helps onboarding and awareness
  - Duplicates existing feature? No
  - Effort proportional to value? Yes
- **Notes**: Low priority but trivial to implement. Could be a simple prompt that reads RELEASE_NOTES.md.

### Feature: Skill Description Length Cap
- **Source**: CE v3.0.0 — [#643](https://github.com/EveryInc/compound-engineering-plugin/issues/643)
- **What it does**: Caps skill descriptions at the harness limit to prevent context overflow from overly verbose descriptions.
- **How source implements it**: Enforces a max character count on skill SKILL.md description fields during validation.
- **Compatibility**: Directly applicable
- **Why this verdict**: Some of our skill descriptions are quite long (e.g., `cg-skill-pester-safety`). A cap would enforce discipline and reduce context budget waste.
- **How we'd adapt it**: Add a test in `prompt-tools.Tests.ps1` that validates all SKILL.md description lengths are under a threshold (e.g., 500 chars).
- **Maps to**: skill
- **Effort**: Small
- **Priority**: Medium
- **Decision criteria check**:
  - Implementable in Copilot model? Yes
  - Benefits GPID team workflows? Yes — reduces context waste
  - Duplicates existing feature? No
  - Effort proportional to value? Yes
- **Notes**: Check current Copilot harness limits. Our `cg-skill-pester-safety` description is ~600+ chars.

### Feature: HITL Review-Loop Mode
- **Source**: CE v2.68.0 — [#580](https://github.com/EveryInc/compound-engineering-plugin/issues/580)
- **What it does**: Adds a human-in-the-loop review loop to brainstorm, plan, and ideate prompts — the agent presents output in chunks for user approval before proceeding.
- **How source implements it**: `proof`, `ce-brainstorm`, `ce-plan`, `ce-ideate` all support a review-loop mode where output is presented section-by-section.
- **Compatibility**: Directly applicable
- **Why this verdict**: Our brainstorm and plan prompts generate full documents. Chunked review would catch issues earlier.
- **How we'd adapt it**: Add optional `--review` flag to `/cg-brainstorm` and `/cg-plan` that pauses after each major section for user approval before continuing.
- **Maps to**: prompt
- **Effort**: Medium
- **Priority**: Medium
- **Decision criteria check**:
  - Implementable in Copilot model? Yes
  - Benefits GPID team workflows? Yes — prevents wasted work on wrong assumptions
  - Duplicates existing feature? No — `/cg-plan-review` reviews after the fact, not during
  - Effort proportional to value? Yes
- **Notes**: This is complementary to `/cg-plan-review`, not a replacement. Review-loop catches issues during generation; plan-review catches issues after.

### Feature: Mode-Aware Ideation
- **Source**: CE v2.68.0 — [#588](https://github.com/EveryInc/compound-engineering-plugin/issues/588)
- **What it does**: Ideation adapts its depth and output format based on whether the user is in dev-repo mode vs. consumer-project mode.
- **How source implements it**: `ce-ideate` detects the project type and adjusts ideation strategy — plugin-development ideation focuses on cross-platform compatibility, while consumer-project ideation focuses on domain goals.
- **Compatibility**: Directly applicable
- **Why this verdict**: Our `/cg-ideate` doesn't currently vary behavior based on project type. Adapting to tool vs. data-science project types would improve relevance.
- **How we'd adapt it**: Read `project-type` from `compound-gpid.local.md` and adjust ideation prompts accordingly (tool projects focus on extensibility; analysis projects focus on methodology).
- **Maps to**: prompt
- **Effort**: Small
- **Priority**: Low
- **Decision criteria check**:
  - Implementable in Copilot model? Yes
  - Benefits GPID team workflows? Yes
  - Duplicates existing feature? No
  - Effort proportional to value? Yes
- **Notes**: Already have `project-type` in local config. Just needs prompt branching.

## Features — Needs Adaptation

### Feature: PR Feedback Resolution with Bot Noise Filtering
- **Source**: CE v3.0.0 — [#610](https://github.com/EveryInc/compound-engineering-plugin/issues/610), [#611](https://github.com/EveryInc/compound-engineering-plugin/issues/611), [#617](https://github.com/EveryInc/compound-engineering-plugin/issues/617)
- **What it does**: Reads PR review comments, filters out bot noise (CI bots, linters), clusters related feedback, and generates a resolution plan.
- **How source implements it**: `ce-resolve-pr-feedback` prompt fetches PR comments via GitHub tools, deduplicates across review rounds, drops bot-generated noise, and produces an actionable checklist.
- **Compatibility**: Needs adaptation
- **Why this verdict**: Copilot has GitHub PR tools available. Would need adaptation because our review workflow is prompt-file based, not PR-based.
- **How we'd adapt it**: Create a `/cg-resolve-feedback` prompt that reads the active PR's review comments, filters bot noise, and generates a fix list compatible with `/cg-fix-triage` format.
- **Maps to**: prompt
- **Effort**: Medium
- **Priority**: Medium
- **Decision criteria check**:
  - Implementable in Copilot model? Yes — Copilot has PR tools
  - Benefits GPID team workflows? Yes — PR feedback loops are common
  - Duplicates existing feature? Partially overlaps with `/cg-fix-triage`
  - Effort proportional to value? Yes
- **Notes**: Depends on `github-pull-request` tools being available. Would complement existing `/cg-fix-triage`.

### Feature: Inline Handoff Menu After Plan/Brainstorm
- **Source**: CE v3.0.0 — [#615](https://github.com/EveryInc/compound-engineering-plugin/issues/615); CE v2.67.0 — [#575](https://github.com/EveryInc/compound-engineering-plugin/issues/575)
- **What it does**: After brainstorm or plan completion, presents an inline menu of next actions (implement, review, revise, archive) so the user doesn't have to remember which command to run next.
- **How source implements it**: Handoff menus are inlined at the end of `ce-plan` and `ce-brainstorm` output, using the question tool for user selection.
- **Compatibility**: Needs adaptation
- **Why this verdict**: Our prompts end with a suggestion but don't offer structured handoff. Need to adapt for `vscode_askQuestions`.
- **How we'd adapt it**: Add a handoff step at the end of `/cg-brainstorm` and `/cg-plan` that uses `vscode_askQuestions` to offer: "Implement → /cg-work", "Review → /cg-plan-review", "Revise", "Done".
- **Maps to**: prompt
- **Effort**: Small
- **Priority**: Medium
- **Decision criteria check**:
  - Implementable in Copilot model? Yes
  - Benefits GPID team workflows? Yes — reduces friction in workflow transitions
  - Duplicates existing feature? No
  - Effort proportional to value? Yes
- **Notes**: The Copilot `vscode_askQuestions` tool makes this straightforward.

### Feature: Plan Ambiguity Gate
- **Source**: CE v3.0.0 — [#598](https://github.com/EveryInc/compound-engineering-plugin/issues/598)
- **What it does**: Runs an ambiguity check on plan inputs before planning begins. If requirements are too vague, routes to brainstorming first instead of producing a weak plan.
- **How source implements it**: `ce-plan` has a pre-check step that evaluates input clarity and redirects to `ce-brainstorm` if below threshold.
- **Compatibility**: Needs adaptation
- **Why this verdict**: Our `/cg-plan` accepts whatever the user provides. Adding a vagueness gate would improve plan quality but needs calibration for data-science tasks.
- **How we'd adapt it**: Add a Step 0.5 to `/cg-plan` that evaluates the input. If it lacks specific outcomes, data sources, or methodology, suggest `/cg-brainstorm` first.
- **Maps to**: prompt
- **Effort**: Small
- **Priority**: Medium
- **Decision criteria check**:
  - Implementable in Copilot model? Yes
  - Benefits GPID team workflows? Yes
  - Duplicates existing feature? No
  - Effort proportional to value? Yes
- **Notes**: Calibration matters. Data science tasks naturally have more ambiguity than software tasks.

### Feature: PR Description Generator with Size Cap
- **Source**: CE v3.0.0 — [#605](https://github.com/EveryInc/compound-engineering-plugin/issues/605)
- **What it does**: Generates PR descriptions from git diff with a size cap, and shows a preview before applying.
- **How source implements it**: `ce-pr-description` reads staged changes, generates a structured description, caps its length, and lets the user preview before applying.
- **Compatibility**: Needs adaptation
- **Why this verdict**: We don't have a PR description generator. Would need adaptation to work with Copilot's PR creation tools.
- **How we'd adapt it**: Create a skill that generates PR descriptions from `get_changed_files` output, following conventional commit format, and feeds into `github-pull-request_create_pull_request`.
- **Maps to**: prompt
- **Effort**: Medium
- **Priority**: Low
- **Decision criteria check**:
  - Implementable in Copilot model? Yes
  - Benefits GPID team workflows? Yes — standardizes PR descriptions
  - Duplicates existing feature? No
  - Effort proportional to value? Yes
- **Notes**: Lower priority since many teams have PR templates already.

### Feature: Reject Plan Re-Scoping Into Human-Time Phases
- **Source**: CE v3.0.0 — [#600](https://github.com/EveryInc/compound-engineering-plugin/issues/600)
- **What it does**: Prevents the planner from expanding a single-session task into multi-phase, multi-week plans that require human scheduling.
- **How source implements it**: `ce-work` detects when a plan has been re-scoped beyond one agent session and rejects it.
- **Compatibility**: Needs adaptation
- **Why this verdict**: Relevant problem — our planner can generate over-ambitious plans. Needs calibration for data science where multi-session work is more common.
- **How we'd adapt it**: Add a scope check to `/cg-work` that warns if the plan contains more tasks than can fit in one session, and suggests splitting.
- **Maps to**: prompt
- **Effort**: Small
- **Priority**: Low
- **Decision criteria check**:
  - Implementable in Copilot model? Yes
  - Benefits GPID team workflows? Yes
  - Duplicates existing feature? No
  - Effort proportional to value? Yes
- **Notes**: Data science plans legitimately span multiple sessions. Gate should warn, not block.

## Features — Not Applicable

### Feature: Multi-Platform Plugin Install Manifests
- **Source**: CE v3.0.0 — [#616](https://github.com/EveryInc/compound-engineering-plugin/issues/616)
- **What it does**: Generates native plugin install manifests for Codex, Cursor, and other platforms alongside the Claude Code manifest.
- **Compatibility**: Not applicable
- **Why this verdict**: compound-gpid targets VS Code Copilot only. We don't need multi-platform support.

### Feature: Pi First-Class Support
- **Source**: CE v3.0.0 — [#651](https://github.com/EveryInc/compound-engineering-plugin/issues/651)
- **What it does**: Adds support for the Pi SDK runtime via pi-subagents and pi-ask-user.
- **Compatibility**: Not applicable
- **Why this verdict**: Requires Pi SDK platform capabilities not available in Copilot.

### Feature: Demo Reel with Local Save
- **Source**: CE v3.0.0 — [#647](https://github.com/EveryInc/compound-engineering-plugin/issues/647)
- **What it does**: Creates visual demo reels of feature implementations with local save option.
- **Compatibility**: Not applicable
- **Why this verdict**: Requires image generation/capture capabilities not available in Copilot. Not relevant to GPID workflows.

### Feature: ast-grep CLI Integration
- **Source**: CE v3.0.0 — [#653](https://github.com/EveryInc/compound-engineering-plugin/issues/653)
- **What it does**: Setup checks for ast-grep CLI availability and uses it for structural code search.
- **Compatibility**: Not applicable
- **Why this verdict**: ast-grep is a CLI tool that would need shell integration. Our projects are R/Python/Stata — ast-grep primarily targets JS/TS/Rust.

### Feature: Consistent ce- Prefix Rename
- **Source**: CE v3.0.0 — [#503](https://github.com/EveryInc/compound-engineering-plugin/issues/503)
- **What it does**: Renames all skills and agents to a consistent `ce-` prefix.
- **Compatibility**: Not applicable
- **Why this verdict**: We already use a consistent `cg-` prefix for all prompts, agents, and skills.

### Feature: ce-debug Environment Sanity + Assumption Audit
- **Source**: CE v3.0.0 — [#649](https://github.com/EveryInc/compound-engineering-plugin/issues/649)
- **What it does**: Structured debugging workflow with environment checks and assumption auditing.
- **Compatibility**: Not applicable
- **Why this verdict**: Duplicates existing `/cg-diagnose` and `/cg-fixbug` functionality.

### Feature: Polish Phase Between Review and Merge
- **Source**: CE v2.67.0 — [#568](https://github.com/EveryInc/compound-engineering-plugin/issues/568)
- **What it does**: Adds a human-in-the-loop polish step between code review and merge.
- **Compatibility**: Not applicable
- **Why this verdict**: Our `/cg-fix-triage` already serves this purpose — it takes review findings and applies fixes before merge.

## Summary

CE v3.0.0 is a mature release with strong architectural parallels to compound-gpid. The most valuable features to adopt are:

1. **Per-finding judgment loop** (High/Medium) — transforms batch review into interactive triage
2. **End-to-end ID traceability** (High/Small) — cheap template change with high traceability payoff
3. **HITL review-loop mode** (Medium/Medium) — chunked output review during generation
4. **Plan ambiguity gate** (Medium/Small) — prevents weak plans from vague inputs
5. **Inline handoff menus** (Medium/Small) — reduces workflow friction

The multi-platform and Pi features are not relevant since we're VS Code Copilot only.
