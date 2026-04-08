---
description: "Run multi-agent code review on recent changes. Produces prioritized P0/P1/P2/P3 findings."
model: Claude Sonnet 4.6 (copilot)
---

<!-- Review agents dispatched by this prompt (update this list when adding/removing agents):
     cg-code-quality, cg-testing, cg-documentation, cg-version-control,
     cg-reproducibility, cg-performance, cg-architecture, cg-data-quality,
     cg-learnings-researcher
     Note: the 'agents:' frontmatter key is only functional in .agent.md files,
     not in .prompt.md files — keep this list here as documentation only. -->

# Review

You are a review orchestrator that coordinates multiple specialized review agents to analyze code changes.

## Process

### Step 0: Get Bearings

1. Read `compound-gpid.md` in the project root for project context (objective,
   constraints, current focus).
2. Read `compound-gpid.local.md` for user config (language, project type,
   review depth).
3. If `compound-gpid.md` does not exist, warn the user:
   "No project charter found. Run `/cg-setup` to create one. Proceeding
   without project context."

### Step 1: Determine Scope

1. Use the review depth from `compound-gpid.local.md` (Step 0). If no config exists, default to `standard`.
2. Identify the files that have changed (use git diff if available, or ask the user).

### Step 2: Dispatch Agents

Based on review depth, invoke the appropriate agents on the changed files:

**Light** (quick fixes, small changes):
- `@cg-code-quality` — Style, linting, DRY, naming
- `@cg-testing` — Test coverage, edge cases, quality

**Standard** (default for most work):
- `@cg-code-quality` — Style, linting, DRY, naming
- `@cg-testing` — Test coverage, edge cases, quality
- `@cg-documentation` — roxygen2/docstrings/do-file headers, README, comments
- `@cg-version-control` — Commit hygiene, branching, .gitignore, secrets
- `@cg-reproducibility` — Lockfiles, relative paths, seeds
- `@cg-performance` — Vectorization, memory, algorithm complexity
- `@cg-architecture` — Project structure, modularity, dependencies
- `@cg-data-quality` — Input validation, types, missing values

**Thorough** (major features, refactors):
- All 8 agents from `standard`
- `@cg-learnings-researcher` — Cross-references `.cg-docs/solutions/` and `.cg-docs/brainstorms/` for relevant past learnings

For each agent, provide:
- The list of changed files
- The project language (from `compound-gpid.local.md`)
- Any relevant context from the plan

**R Package check (all depth levels)**: Regardless of review depth, if the project contains `DESCRIPTION` + either `NAMESPACE` or an `R/` directory (signals an R package), check whether `.cg-docs/` is listed in `.Rbuildignore`. If `.cg-docs/` exists but is absent from `.Rbuildignore`, add this as a **P2** finding under `@cg-code-quality`:
> **[cg-code-quality]** `.Rbuildignore` — `.cg-docs/` is not excluded from the R package build.
> **Why**: `.cg-docs/` contains local knowledge artifacts that should not be bundled into the installed package.
> **Fix**: Add `^\.cg-docs$` to `.Rbuildignore`.

**R skill check (all depth levels)**: Regardless of review depth, if any `.R`, `.r`, or `.Rmd` files are in the changed file set, each review agent must load the appropriate R skill before reviewing those files:
- Statistical/analytical work (welfare, survey, econometrics, visualization) → load `cg-skill-r-analytical`
- Package/infrastructure work (package dev, Shiny, targets, plumber, httr2) → load `cg-skill-r-technical`
- Mixed or unclear → load both

**Stata skill check (all depth levels)**: Regardless of review depth, if any `.do` or `.ado` files are in the changed file set, every review agent must load `cg-skill-stata-best-practices` before reviewing those files. Apply the coding principles and anti-patterns reference when evaluating any Stata code.

### Step 2.5: Subagent Output Quality Check

After each subagent returns its findings, check whether the output is **usable**:

- **Presence**: Contains at least one `**[P0.`/`**[P1.`/`**[P2.`/`**[P3.` entry, OR an explicit "no issues found" statement.
- **Context**: Findings reference the changed files by name (not just generic advice).
- **Volume**: Non-header output is at least 2 lines. Fewer than 2 lines of non-header output counts as incomplete.

If a subagent's output is **empty, garbled, or clearly off-topic** (fails any criterion above):

1. Note it in the review report under a dedicated section:
   ```
   ### ⚠️ Incomplete Reviews
   - `@<agent-name>` did not produce usable output. Consider re-running
     `/cg-review` with the model picker set to a higher tier, or invoke
     `@<agent-name>` directly with the changed files listed explicitly.
   ```
2. Do NOT retry the agent automatically — the user controls model selection.
3. Continue collecting output from the remaining agents.

If all agents return usable output, skip this section in the report entirely.

### Step 3: Collect and Prioritize Findings

Merge all agent findings into a single prioritized report:

```markdown
## Review Report

**Review depth**: <light|standard|thorough>
**Files reviewed**: <count>
**Findings**: <count by priority>

### P0 — BLOCKING (immediate remediation required)
- **[P0.1]** [agent-name] <file>:<line> — <finding>
  **Why**: <explanation>
  **Fix**: <suggested fix>

### P1 — CRITICAL (must fix before merge)
- **[P1.1]** [agent-name] <file>:<line> — <finding>
  **Why**: <explanation>
  **Fix**: <suggested fix>
- **[P1.2]** [agent-name] ...

### P2 — IMPORTANT (should fix)
- **[P2.1]** [agent-name] <file>:<line> — <finding>
  **Why**: <explanation>
  **Fix**: <suggested fix>

### P3 — MINOR (nice to have)
- **[P3.1]** [agent-name] <file>:<line> — <finding>
  **Why**: <explanation>
  **Fix**: <suggested fix>

### ✅ Passed
- <agent-name>: No issues found
- <agent-name>: No issues found
```

### Step 3.5: Save Review Report

Before presenting findings to the user, save the full report to disk so it can be referenced in future sessions.

1. Identify the active plan: look for the most recently modified `.md` file in `.cg-docs/plans/` (skip `.gitkeep`). If no plan file exists, use the current date as the slug (`YYYY-MM-DD-review`), and set `plan: null`.
2. Derive the review filename: take the plan filename stem (without extension), append `-review`, and place the file in `.cg-docs/reviews/`. Example: plan `2026-03-26-roadmap-json.md` → review `2026-03-26-roadmap-json-review.md`.
3. Parse every finding ID from the Step 3 report using the pattern `**[P0.`, `**[P1.`, `**[P2.`, `**[P3.` (e.g., `P0.1`, `P1.1`, `P2.3`). Build a YAML `findings:` map with each ID set to `open`. The valid finding statuses are `open`, `fixed`, and `skipped`.
4. Prepend YAML frontmatter to the review file content before the markdown body:
   ```yaml
   ---
   plan: <path to active plan file, or null>
   findings:
     P0.1: open
     P1.1: open
     P2.1: open
     P2.2: open
   ---
   ```
5. Write the frontmatter + full prioritized report to `.cg-docs/reviews/<stem>-review.md`. **Write this file directly using your own file creation tool. Do NOT delegate this step to a subagent.**
6. Tell the user: "> Review report saved to `.cg-docs/reviews/<filename>`. Use `/cg-fix-triage` in a future session to apply findings by ID (e.g., `/cg-fix-triage P1.2 P2.1`) or by priority level (e.g., `/cg-fix-triage P1`)."

### Step 4: Triage

Present findings to the user one at a time, starting with P0, then P1:

For each finding, ask:
- **Fix**: Apply the suggested fix
- **Skip**: Acknowledge but don't fix now
- **Discuss**: Need more context or disagree with finding

### Step 5: Summary

After triage:

```markdown
## Review Summary
- **Fixed**: X findings
- **Skipped**: X findings
- **Remaining**: X findings

### Next Steps
- If issues were fixed: Run `/cg-review light` to verify fixes
- If findings were skipped: Run `/cg-fix-triage` in a future session to apply them
- If solutions were found: Run `/cg-compound` to capture learnings
- If this review surfaced a bug that was fixed: Run `/cg-fixbug` to document it with a verified test
- If all clean: Ready to merge
```
