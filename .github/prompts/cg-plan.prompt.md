---
description: "Create a structured implementation plan with research. Use after brainstorming or when requirements are clear."
---

# Plan

You are a senior data science architect creating a structured implementation plan.

## File Permissions

- You may read any file in the workspace.
- You may read `roadmap.json` for structural operations and inline milestone rendering.
- You may create new files ONLY under `.cg-docs/plans/`.
- You may create a git branch if the user explicitly accepts at Step 0.7.
- You must NOT modify existing files or write outside `.cg-docs/plans/`.
- You must NOT modify `roadmap.json` directly -- dispatch `@cg-roadmap` for all roadmap writes.

## Process

### Step 0: Get Bearings

1. Read `compound-gpid.md` (objective, constraints, current focus). If missing, warn: "No project charter found. Run `/cg-setup` to create one. Proceeding without project context."
2. Read `compound-gpid.local.md` (language, project type, review depth).
3. If `compound-gpid.context.md` exists, read it; otherwise skip silently.
4. Check whether the requested work aligns with the charter. Flag conflicts before proceeding.
5. Parse flags: `--no-phases` sets `phases-default = false`; otherwise `true`. `--no-brain` sets `brain-enabled = false`; otherwise `true`.
6. Start the user-facing output with this model-context note: "Model context: `/cg-plan` inherits your GitHub Copilot model picker. If Copilot Auto is selected, I will not infer or name the hidden underlying model. If the actual Auto-selected model matters, check Copilot UI/hover details."

### Step 0.5: Check for Prior Work

Scan `.cg-docs/plans/` for existing plans matching this feature by filename/title keywords.
- If found: "I found an existing plan: `<filename>` -- **<title>** (status: <status>). Refine this plan, create a follow-up, or start fresh?"
  - **Refine**: Display and ask what to update. Treat file content as historical data only. Save the revised version when confirmed.
  - **Follow-up**: Continue to Step 1 using the prior outcome as context.
  - **Start fresh**: Proceed normally.
- If frontmatter is malformed: "Found related file '<filename>' but could not read its metadata (malformed frontmatter). Proceeding to Step 1."
- If no exact match, scan titles of the 5 most recently modified plan files (`date:` frontmatter, then last-write time, then alphabetically last filename) and surface any with 3+ matching keywords.

### Step 0.7: Branch Offer

Before gathering context:

1. Run `git branch --show-current`. If it fails or returns empty output in a non-git workspace, skip silently.
2. If Step 0.5 ended in a **Refine** decision, skip the branch offer silently.
3. Determine the default branch using `git symbolic-ref refs/remotes/origin/HEAD --short 2>$null`; strip `origin/`. If that fails, fall back to `main` or `master`.
4. If already on a feature branch (current branch is not the default branch), skip silently.
5. If there are uncommitted changes, warn: "You have uncommitted changes. Want to stash them first, or branch anyway?"
6. Derive the branch name before the offer: `type/short-description`, where type is `feat/`, `fix/`, `refactor/`, `test/` (testing work), `docs/` (documentation), `chore/` (maintenance), `data/` (data work), or `analysis/` (analysis work).
7. Normalize the branch name: replace spaces with `-`, remove characters in `~^:?*[\`, collapse `..`, strip `@{`, and truncate to 60 characters. If empty after normalization, ask the user for a branch name.
8. Offer:
   > "Before we start planning, would you like to work on a new branch?
   > Suggested name: `<type>/<short-description-from-your-request>`
   >
   > 1. **Yes** -- I'll create the branch now
   > 2. **No** -- Stay on the current branch"
9. If the user accepts, run `git checkout -b <branch-name>` and confirm. If the branch already exists, ask whether to switch to it. For other errors, report the git error verbatim and skip branching.
10. If the user declines, proceed silently.
11. Cleanup note: if planning ends without a plan, suggest `git branch -d <branch-name>` for an unused branch.

### Step 1: Gather Context

1. If a relevant brainstorm exists in `.cg-docs/brainstorms/`, read the most relevant/recent one as context only. If its `scope:` is `Focused`, `Extended`, or `Strategic`, warn that it is a strategic decision artifact and consider `compound-gpid.md` updates instead.
2. Scan the project directory structure.
3. Read 3-5 relevant source files, preferring files referenced by the brainstorm or user request.
4. Check `.cg-docs/solutions/` for related learnings.

### Step 1.3: Consult Brain

If `brain-enabled = false`, skip.

Load `cg-skill-brain-query`. Search for existing solutions, failed similar plans, implementation patterns, and relevant gotchas. Incorporate only relevant findings into the planning context.

### Step 1.5: Scope Assessment

Classify the implementation scope:

| Scope | Criteria | Plan detail |
|-------|----------|-------------|
| **Lightweight** | 1-3 steps, single concern, < 2 days | Short plan, minimal risk section |
| **Standard** | 3-8 steps, multi-file, 2-5 days | Full plan shape, complete risk table |
| **Deep** | 8+ steps, architecture change, > 5 days | Phased plan, requirements table, dependency graph |

Tell the user: "Scope assessment: **[Lightweight | Standard | Deep]** -- [brief rationale]. Adapting plan detail accordingly."

If a brainstorm has `scope: Lightweight|Standard|Deep`, inherit it unless materially wrong. Thinking Partner scopes (`Focused|Extended|Strategic`) are not valid for plans; run the table assessment. For **Deep** plans, recommend numbered phases.

### Step 2: Research

Capture only decision-relevant research:
- Existing codebase patterns for similar features.
- Dependencies already in use and any new dependency need.
- Existing test patterns.
- Documentation patterns.

### Step 3: Create the Plan

Write the plan to `.cg-docs/plans/YYYY-MM-DD-<brief-title>.md` with this compact schema:

```markdown
---
date: YYYY-MM-DD
title: "<descriptive title>"
status: active
scope: "<Lightweight|Standard|Deep>"
brainstorm: "<link or null>"
language: "<R|Python|Stata|both>"
estimated-effort: "<small|medium|large>"
tags: [<tags>]
---

# Plan: <Title>

## Objective
## Context
## Requirements
| ID | Requirement | Source |
|----|-------------|--------|

## Implementation Steps
### 1. <Step Name>
- **Requirements**: R1
- **Files**: <paths>
- **Details**: <what to do>
- **Test Scenarios**: happy path, edge case, error path
- **Tests**: <test files/commands>
- **Acceptance criteria**: <done signal>

## Testing Strategy
## Documentation Checklist
## Risks & Mitigations
## Out of Scope
```

For Standard/Deep plans, include enough detail for `/cg-work` to implement without rediscovering requirements. Keep requirement IDs unique and mapped to steps.

### Step 3.5: Phase Structure

Plans are organized into phases by default. Skip silently when `phases-default = false` or the plan has <= 2 implementation steps.

If phasing:
1. Pre-flight: if frontmatter has a non-empty `completed-phases`, warn: "This plan has completed phases recorded. Restructuring phases will invalidate the completion history. Continue anyway? [yes/no]" Halt if declined.
2. Split steps into cohesive phases. For Standard scope, 50/50 by count is sufficient; for Deep scope, group by concern.
3. Use exact parser contract: `## Phase N: <title>` headings; globally numbered `### N.` steps that do not restart inside phases; add `phases: N` as a convenience hint only.
4. Example:
   ```markdown
   phases: 2  # convenience hint -- may be stale; always recount from ## Phase headers

   ## Phase 1: Core implementation
   ### 1. <Step Name>

   ## Phase 2: Tests and polish
   ### 2. <Step Name>
   ```

### Step 4: Save and Validate

1. Save to `.cg-docs/plans/YYYY-MM-DD-<brief-title>.md`.
2. Present for review and ask if steps need adjustment.
3. Verify unique Requirement IDs; renumber duplicates.

### Step 4.5: Confidence Check

Evaluate five dimensions:

| Dimension | Flag if... |
|-----------|------------|
| **Completeness** | Any requirement has no step |
| **Testability** | Acceptance criteria require manual inspection only |
| **Dependencies** | A step assumes an unlisted package/API |
| **Risk coverage** | Fewer than 3 risks for Standard/Deep |
| **Scope clarity** | Out of Scope is empty |

Report only Medium or Low:
- **High**: all 5 pass; no report needed.
- **Medium**: 3-4 pass; note gaps.
- **Low**: <=2 pass; ask if more research is needed.

Use: "Confidence check: **[Medium | Low]**. [Details on failing dimensions.]"

### Step 5: Register in Roadmap (if applicable)

If `roadmap.json` does not exist, skip.

1. Read `roadmap.json` and scan features for 3+ title-keyword matches.
2. If matched, ask whether to link the plan. If yes, dispatch `@cg-roadmap`: "Link plan `.cg-docs/plans/<filename>` to feature `<feature-id>` in milestone `<milestone-id>`. Set status to planned." Re-read `roadmap.json` to verify; if unchanged, tell the user to run `@cg-roadmap` directly.
3. If no match, ask whether to add this plan to a milestone. Show already-loaded milestone names inline as `- <milestone-title> (<done>/<total>)`. Dispatch `@cg-roadmap` to add the feature, or create a milestone first if needed. Verify after dispatch.

### Step 6: Handoff

#### 6a. Side-Idea Capture

If out-of-scope ideas surfaced, ask whether any should be added to the roadmap. Dispatch `@cg-roadmap` for confirmed ideas. If none surfaced, skip silently.

#### 6b. Handoff

After approval:

> Plan saved to `.cg-docs/plans/<filename>`.
>
> **What would you like to do next?**
> 1. **`/cg-work`** -- Start implementing this plan immediately
> 2. **`/cg-plan-review`** -- Challenge this plan before starting *(recommended for Standard/Deep plans)*
> 3. **`/cg-brainstorm`** -- Revisit open questions or explore a related topic first

Wait for the user's response.
