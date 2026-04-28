---
date: 2026-04-28
title: "Optimize /cg-release: 60-day scan window + Haiku/Sonnet model split"
status: decided
scope: "Standard"
chosen-approach: "New @cg-release-scanner agent (Haiku) + refactored prompt (Sonnet)"
tags: [performance, cg-release, model-split, scan-window, haiku, sonnet, agents]
---
<!-- Valid status values: decided, in-progress, abandoned -->

# Optimize /cg-release: 60-day Scan Window + Haiku/Sonnet Model Split

## Context

The Performance milestone has two remaining idea-stage features:
1. `/cg-release` scan scope limited to last 60 days
2. Split `/cg-release` into Haiku scan + Sonnet drafting

These two features are designed together as a single coherent change because
the scan window naturally feeds into the scan phase of the split architecture.
Completing both closes the Performance milestone entirely.

### Platform Constraint

The model audit (2026-04-07) established that VS Code Copilot's `model:` field
is static YAML resolved before prompt execution — there is no mid-prompt model
switching API. Therefore the Haiku+Sonnet split must be two separate invocations:
a prompt dispatching an agent with a different `model:` field.

## Requirements

### Scan Window (Feature 1)

1. **Default window**: 60 days from today OR since the last release tag, whichever is **longer**. The 60-day value is a minimum — all changes since the last tag are always included.
2. **First release**: No window cap. Scan everything when no prior tag exists.
3. **Excluded entries**: When the window excludes older `.cg-docs/` entries, include a summary line in the scan output: "N additional changes older than 60 days were excluded from this scan."
4. **Configurable via `--since`**: User can override the window with `/cg-release --since 90` (days) or `/cg-release --since 2026-03-01` (date).

### Model Split (Feature 2)

5. **Single user action**: User runs `/cg-release` once. The prompt internally dispatches a Haiku-tier scan agent and processes the output with Sonnet for prose.
6. **New agent**: `cg-release-scanner.agent.md` with `model: Claude Haiku 4.5 (copilot)`.
7. **Handoff format**: Structured markdown returned in the agent's response text (not a file artifact). Matches existing agent dispatch patterns from `/cg-review`.
8. **Agent scope**: Determine latest tag, compute time window, run `git log`, scan `.cg-docs/` entries within window, classify commits by semver impact, return categorized report.
9. **Prompt scope**: Parse `--since` argument, dispatch agent, receive structured output, suggest semver bump, check SCHEMA_VERSION, draft prose, confirmation flow, execute script.

### Out of Scope

- Automated model fallback (no API support)
- Persistent scan artifacts on disk
- Changes to `create-release.ps1`

## Approaches Considered

### Approach 1: New @cg-release-scanner agent + refactored prompt ✅

Create a `cg-release-scanner.agent.md` (Haiku 4.5) for scan/categorization.
Refactor `cg-release.prompt.md` (Sonnet) to dispatch the agent, then use its
structured markdown output for release notes drafting.

- **Pros**: Clean separation. Haiku handles mechanical scanning (ideal for its tier). Sonnet focuses on prose. Matches existing agent dispatch patterns. Single user action.
- **Cons**: New agent file to maintain. One extra round-trip per release.
- **Effort**: Medium

### Approach 2: Two-phase prompt with intermediate file

Split into `/cg-release-scan` (Haiku prompt) and `/cg-release` (Sonnet prompt)
with a `release-scan.md` intermediate file.

- **Pros**: Each phase independently debuggable.
- **Cons**: Two user actions. Intermediate file to manage.
- **Effort**: Medium

### Approach 3: Keep single Sonnet prompt, add only the time window

Just add the 60-day window and `--since` argument. No model split.

- **Pros**: Minimal change. Reduces input tokens.
- **Cons**: Doesn't address model cost objective. Leaves milestone incomplete.
- **Effort**: Small

## Decision

**Approach 1** — New `@cg-release-scanner` agent (Haiku 4.5) dispatched by the
refactored `cg-release.prompt.md` (Sonnet 4.6). The scan agent handles tag
detection, time window computation, git log scanning, `.cg-docs/` scanning, and
commit classification. It returns structured markdown. The prompt handles argument
parsing, agent dispatch, semver suggestion, SCHEMA_VERSION checks, prose drafting,
confirmation flow, and script execution.

Devil's advocate pushback was acknowledged — the per-invocation savings are modest
for a low-frequency prompt, but the 60-day window has standalone token reduction
value and the combined design avoids rework. It also establishes a model-split
pattern reusable in higher-frequency workflows.

## Next Steps

1. Create `cg-release-scanner.agent.md` with Haiku 4.5 model, scan logic instructions, and structured markdown output format.
2. Refactor `cg-release.prompt.md` — add `--since` argument parsing, replace Steps 1–2 with agent dispatch, add output consumption logic for Steps 3–4.
3. Update the model guide (`docs/model-guide.md`) with the new agent assignment.
4. Add tests for the argument parsing and window logic.
5. Update `roadmap.json` — both features to `planned` with a shared plan reference.
