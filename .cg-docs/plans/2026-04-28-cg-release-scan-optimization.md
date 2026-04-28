---
date: 2026-04-28
title: "Optimize /cg-release: scan window + Haiku/Sonnet model split"
status: completed
completed-date: 2026-04-28
scope: "Standard"
brainstorm: ".cg-docs/brainstorms/2026-04-28-cg-release-scan-optimization.md"
language: "PowerShell"
estimated-effort: "medium"
tags: [performance, cg-release, model-split, scan-window, haiku, sonnet, agents]
---

# Plan: Optimize /cg-release — Scan Window + Haiku/Sonnet Model Split

## Objective

Reduce token cost and session latency for `/cg-release` by (1) limiting the
scan window to 60 days minimum (configurable via `--since`), and (2) splitting
the workflow into a Haiku-tier scan agent + Sonnet-tier prose drafting prompt.
Completing both features closes the Performance milestone.

## Context

- **Current state**: `cg-release.prompt.md` (Sonnet 4.6) does everything in
  one pass — tag detection, git log scanning, `.cg-docs/` scanning, commit
  classification, SCHEMA_VERSION check, prose drafting, and script execution.
- **Platform constraint**: `model:` is static YAML resolved before prompt
  execution. No mid-prompt model switching. The split must be prompt→agent
  dispatch (established in model audit, 2026-04-07).
- **Existing pattern**: `/cg-review` dispatches `@cg-*` agents via
  `runSubagent`. Agents return text; the orchestrator consolidates. The new
  scanner follows this exact pattern.
- **Agent file location**: `.github/agents/` — this directory IS junctioned
  into user projects, but the agent is `user-invocable: false` and only
  dispatched by the developer-only `cg-release.prompt.md` at the repo root.
- **Test sentinels**: `model-assignments.Tests.ps1` has count sentinels
  (currently 18 prompts, 13 agents) and stem lists that must be updated
  when adding a new agent.

## Requirements

| ID  | Requirement                                              | Source      |
|-----|----------------------------------------------------------|-------------|
| R1  | Default scan window: 60 days OR since last tag, whichever is **longer** | brainstorm  |
| R2  | First release (no prior tag): scan everything, no window cap | brainstorm  |
| R3  | Excluded entries: summary line "N additional changes older than X days were excluded" | brainstorm  |
| R4  | `--since` argument: accepts day count (`--since 90`) or ISO date (`--since 2026-03-01`) | brainstorm  |
| R5  | Single user action: `/cg-release` dispatches Haiku agent internally | brainstorm  |
| R6  | New agent `cg-release-scanner.agent.md` with `model: Claude Haiku 4.5 (copilot)` | brainstorm  |
| R7  | Handoff via structured markdown in agent response text (no file artifact) | brainstorm  |
| R8  | Agent scope: commit classification (from log text passed by prompt), `.cg-docs/` scan, structured report | brainstorm  |
| R9  | Prompt scope: argument parsing, tag detection, git log execution, window computation, agent dispatch, semver suggestion, SCHEMA_VERSION, prose, confirmation, execution | brainstorm  |
| R10 | Update model guide with new agent entry | convention  |
| R11 | Update test sentinels (agent count 13→14, add stem to lists) | convention  |

## Implementation Steps

### 1. Create `cg-release-scanner.agent.md`

- **Requirements**: R6, R7, R8, R1, R2, R3
- **Files**: Create `.github/agents/cg-release-scanner.agent.md`
- **Details**:

  Frontmatter:
  ```yaml
  ---
  description: "Scans git history and .cg-docs/ entries within a time window to produce a categorized change report for /cg-release. Developer-only — dispatched by cg-release.prompt.md, not invoked directly."
  model: Claude Haiku 4.5 (copilot)
  tools: ['read', 'search']
  user-invocable: false
  ---
  ```

  Body instructions:
  1. **Receive inputs** from the dispatching prompt: `latest-tag` (string or `null`), `window-start` (ISO date), `commit-log` (raw text from `git log`, already executed by the prompt).
  2. **Parse commit log**: The prompt has already run `git log` and passed the output as text. Parse it to extract conventional commit prefixes and messages. If `latest-tag` is null, all commits are in scope (R2).
  3. **Classify commits** by conventional commit prefix → semver impact table (same table currently in Step 2 of the prompt).
  4. **Scan `.cg-docs/`**: Read filenames in `brainstorms/`, `plans/`, `solutions/` subdirectories. Match by date prefix (YYYY-MM-DD) against the window. For entries outside the window, count them for R3.
  5. **Return structured markdown** in this format:

  ```markdown
  ## Scan Summary
  - Latest tag: <tag or "none">
  - Scan window: <start-date> to <today>
  - Commits scanned: <N>
  - .cg-docs entries scanned: <N>
  - Excluded (older than window): <N> commits, <M> .cg-docs entries

  ## Suggested Semver Impact
  - Highest impact: <major|minor|patch>
  - Reasoning: <which commit(s) triggered this>

  ## New Features
  | Commit | .cg-docs Reference | Summary |
  |--------|-------------------|---------|
  | <sha> <msg> | <plan or brainstorm filename> | <one-line summary> |

  ## Bug Fixes
  | Commit | .cg-docs Reference | Summary |
  |--------|-------------------|---------|

  ## Under the Hood
  | Commit | .cg-docs Reference | Summary |
  |--------|-------------------|---------|

  ## SCHEMA_VERSION Signals
  - <list any commits touching link.ps1 $ManagedDirs, update.ps1 migrations, .cg-docs/ structure, or compound-gpid.local.md fields>
  ```

- **Test Scenarios**:
  - ✅ Happy path: agent produces well-formed markdown with all sections
  - 🛑 Edge case: no commits since tag → empty tables, patch bump suggested
  - 🛑 Edge case: first release (no tag) → full scan, no exclusion line
  - ❌ Error path: commit log text is empty → agent reports "no commits found" clearly
- **Tests**: Structural tests in `model-assignments.Tests.ps1` (Step 4). Agent output format is tested indirectly via manual invocation.
- **Acceptance criteria**: Agent file exists, has correct frontmatter, instructions cover classification and `.cg-docs/` scan (no terminal execution), output format is documented.

  > **Review finding [P1.1]**: The agent has `tools: ['read', 'search']` — no terminal
  > execution capability. Git commands (`git log`, `git describe`) are executed by the
  > orchestrating prompt (Step 2) and passed as text, matching the established review-agent
  > pattern where prompts run commands and agents analyze results.

### 2. Refactor `cg-release.prompt.md` — argument parsing + agent dispatch

- **Requirements**: R4, R5, R9, R1, R2
- **Files**: Modify `cg-release.prompt.md`
- **Details**:

  **A. Add argument parsing block** (new section after the intro, before Step 1):

  ```markdown
  ## Arguments

  Parse optional arguments from the user's invocation message:
  - `--since <value>`: Override the default 60-day scan window floor.
    - If value matches `^\d+$` (digits only, e.g., `--since 90`): treat as days.
    - If value matches `^\d{4}-\d{2}-\d{2}$` (e.g., `--since 2026-03-01`): treat as ISO cutoff date.
    - If value doesn't match either pattern: warn the user and fall back to 60-day default.
    - If absent: default to 60 days.
  - **Precedence rule**: `--since` sets the scan window *floor*. The effective
    window is always `max(--since value, tag age)` when a prior tag exists.
    This ensures release notes never omit work done since the last release.
  ```

  **B. Replace current Steps 1–2** with a new Step 1 that:
  1. Runs `git describe --tags --abbrev=0` to get the latest tag (same as current Step 1).
  2. If a tag was found, runs `git log -1 --format=%ci <tag>` to get `tag_date`.
  3. Computes the effective window cutoff: `max(today - window_days, tag_date)`. For first release (no tag), passes `null` for latest-tag and scans everything.
  4. Runs `git log <tag>..HEAD --oneline` (or `git log --oneline` if no tag) to get the raw commit log text.
  5. Dispatches `@cg-release-scanner` with: latest-tag, window-start (cutoff date), and the raw commit log text.
  6. Receives the structured markdown response.
  7. If the scan summary shows excluded entries, preserves the count for inclusion in release notes: "N older items not shown in this release."

  > **Review findings [P1.1, P2.2]**: Git commands (`git describe`, `git log -1 --format=%ci`,
  > `git log ..HEAD`) are all executed here in the prompt — not in the agent. The agent
  > receives text inputs only, matching the established pattern where agents have
  > `tools: ['read', 'search']` and never execute terminal commands.

  **C. Adapt current Step 3 (SCHEMA_VERSION)**: Instead of scanning changes directly, read the "SCHEMA_VERSION Signals" section from the agent's output. Apply the same warning logic.

  **D. Adapt current Step 4 (draft release notes)**: Use the agent's categorized tables (New Features, Bug Fixes, Under the Hood) as the structured input. For each entry with a `.cg-docs` reference, read the referenced file to get prose context. Write the narrative `RELEASE_NOTES.md` as before.

  **E. Steps 5–6 remain unchanged** (confirmation + execution).

- **Test Scenarios**:
  - ✅ Happy path: `/cg-release` with no args → 60-day default, agent dispatched
  - ✅ Happy path: `/cg-release --since 90` → 90-day window passed to agent
  - ✅ Happy path: `/cg-release --since 2026-03-01` → date cutoff passed to agent
  - 🛑 Edge case: first release → agent receives null tag, scans everything
  - 🛑 Edge case: last tag is 30 days old → window expands to 60 days (60 > 30, so `--since` floor wins)
  - 🛑 Edge case: `--since 30` but tag is 90 days old → window expands to 90 days (tag age > 30, `max(--since, tag age)` rule)
  - 🛑 Edge case: `--since 0` → effective window is `max(0 days, tag age)` = tag age (tag age always wins)
  - ❌ Error path: invalid `--since` value (e.g., `--since abc`, `--since 90-`) → warn user, fall back to 60-day default
- **Tests**: Prompt structural tests (see Step 4 below). Argument parsing is tested via prompt inspection, not runtime.
- **Acceptance criteria**: Prompt dispatches `@cg-release-scanner`, uses its output for notes, `--since` argument is documented and handled.

### 3. Update `docs/model-guide.md`

- **Requirements**: R10
- **Files**: Modify `docs/model-guide.md`
- **Details**:

  Two changes:

  1. **Update header count**: `31` → `32` in the opening line ("across all N Compound GPID prompt and agent files").

  2. **Add a new row** to the **Agents** table:

  | File | Assigned Model | Task Description | Tier Rationale | Status |
  |------|---------------|------------------|----------------|--------|
  | `cg-release-scanner.agent.md` | Claude Haiku 4.5 | Classify commits and scan .cg-docs entries within a time window for /cg-release | Reasoning 3, creativity 1; mechanical classification and categorization — Haiku appropriate | confirmed |

  Tier justification: The scanner parses pre-collected commit log text, reads filenames/dates, and categorizes by prefix — all mechanical/checklist tasks. No creative judgment or complex reasoning. Firmly Haiku territory.

- **Test Scenarios**:
  - ✅ Happy path: guide contains new agent row
  - 🛑 Edge case: N/A
  - ❌ Error path: N/A
- **Tests**: `model-assignments.Tests.ps1` stem-check will validate (Step 4).
- **Acceptance criteria**: Model guide has the new agent entry with correct tier rationale.

### 4. Update test sentinels and stem lists

- **Requirements**: R11
- **Files**: Modify `tests/model-assignments.Tests.ps1`
- **Details**:

  Three changes:
  1. **Agent count sentinel**: `13` → `14` in the "contains exactly N agent files" test.
  2. **Agent stem list**: Add `'cg-release-scanner'` to the `$agentStems` array in the "docs/model-guide.md - structure and sync" describe block.
  3. No prompt count change (still 18 — the prompt is modified, not added).

- **Test Scenarios**:
  - ✅ Happy path: all tests pass with updated sentinels
  - 🛑 Edge case: N/A
  - ❌ Error path: sentinel mismatch produces clear failure message
- **Tests**: Self-validating — run the test suite after changes.
- **Acceptance criteria**: `Invoke-Pester tests/model-assignments.Tests.ps1` passes with 0 failures.

### 5. Validate end-to-end

- **Requirements**: All
- **Files**: None (validation only)
- **Details**:

  1. Run the full test suite via `. tests\Run-Tests.ps1`.
  2. Verify `tests/last-run.json` shows 0 failures.
  3. Do a dry-run of `/cg-release` to verify the agent dispatch works and produces well-formed output (manual verification — this is a developer-only prompt with side effects).

- **Test Scenarios**:
  - ✅ All Pester tests pass
  - ✅ `/cg-release` dry-run produces structured scan output → release notes
- **Acceptance criteria**: Full test suite green. Manual dry-run confirms agent dispatch.

## Testing Strategy

- **Structural tests** (automated): `model-assignments.Tests.ps1` validates agent count, frontmatter, and model guide sync. These are the primary automated guard.
- **Prompt structural tests**: `prompt-tools.Tests.ps1` validates frontmatter delimiters for all prompt/agent files — the new agent file will be picked up automatically by the glob discovery.
- **Manual validation**: `/cg-release` is a developer-only prompt with real side effects (creates GitHub releases). A dry-run (stop before Step 6 execution) is the appropriate validation method.
- **No new test file needed**: The existing test infrastructure covers the new agent file via discovery patterns.

## Documentation Checklist

- [ ] Agent file has descriptive `description:` frontmatter
- [ ] Model guide updated with new agent entry, tier rationale, and header count (31→32)
- [ ] `cg-release.prompt.md` documents `--since` argument syntax with explicit regex patterns
- [ ] `--since` precedence rule documented: `max(--since, tag age)` when a tag exists
- [ ] Structured markdown output format documented in agent instructions

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Agent output is malformed or incomplete | Sonnet drafts poor release notes | Agent instructions include explicit output template with all required sections. Summary line counts provide a completeness check. |
| `--since` parsing ambiguity (is `2026` a year or 2026 days?) | Wrong scan window | Explicit regex: `^\d+$` → days, `^\d{4}-\d{2}-\d{2}$` → ISO date, otherwise → warn and fall back to 60-day default. No ambiguous "contains `-`" heuristic. |
| Agent dispatch adds latency | Slower releases | Acceptable trade-off: Haiku is fast, and the scan is the lightest phase. The prose drafting (Sonnet) dominates wall time anyway. |
| New agent is junctioned into user projects via `.github/agents/` | User confusion | `user-invocable: false` prevents direct invocation. Description clarifies it's developer-only. |

## Out of Scope

- Changes to `create-release.ps1` (script stays as-is)
- Persistent scan artifacts on disk (agent returns text, no files)
- Automated model fallback (no API support)
- Configurable default window in `compound-gpid.local.md` (hardcoded 60 days in prompt; override via `--since`)
- New Pester test file for the agent (covered by existing discovery tests)
