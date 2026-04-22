---
date: 2026-04-21
title: "Competitive repo review system for feature discovery"
status: decided
scope: "Standard"
chosen-approach: "Registry file + review prompt"
tags: [architecture-research, competitive-analysis, workflow, prompt-design]
---
<!-- Valid status values: decided, in-progress, abandoned -->

# Competitive Repo Review System for Feature Discovery

## Context

The compound-gpid plugin draws inspiration from three external repos that solve
similar problems (AI-assisted development workflows):

| Repo | Stars | Latest Release | Focus |
|------|-------|----------------|-------|
| [EveryInc/compound-engineering-plugin](https://github.com/EveryInc/compound-engineering-plugin) | 15k | v2.68.1 | Claude Code/Codex/Cursor plugin — brainstorm→plan→work→review→compound cycle |
| [obra/superpowers](https://github.com/obra/superpowers) | 163k | v5.0.7 | Agentic skills framework — composable skills, TDD-first, subagent-driven development |
| [gsd-build/gsd-2](https://github.com/gsd-build/gsd-2) | 6.3k | v2.77.0 | Standalone CLI agent — auto mode, context engineering, crash recovery, cost tracking |

These repos are actively developed (daily commits, frequent releases). The
developer has been manually skimming them but has not done a systematic
assessment or tracked new features over time.

The Architecture Research milestone in `roadmap.json` already anticipated this
work with several idea-stage features ("Study GSD-2 and Superpowers workflow
patterns", "Include /ce:ideate-style prompt", etc.).

## Requirements

### Core Needs

1. **Systematic initial assessment** of all three repos — full feature
   inventory mapped to compound-gpid's architecture
2. **Recurring review mechanism** — a prompt (`/cg-review-repos`) invoked
   every 1–2 weeks that identifies new features from recent releases
3. **Implementation-ready output** — each identified feature must contain
   enough context (what it does, how the source implements it, how we'd adapt
   it, effort estimate) to flow directly into `/cg-brainstorm` → `/cg-plan`
   → `/cg-work` without re-discovery
4. **Extensible repo list** — the system must support adding/removing repos
   over time

### Decision Criteria for Feature Inclusion

A feature is worth considering if it meets ALL of:

- **Implementable**: Can be built within GitHub Copilot's prompt/agent/skill
  model (no standalone CLI, no session lifecycle control, no background
  processes)
- **Beneficial**: Improves the GPID team's workflows — data science,
  Stata-to-R migration, official statistics, or general development
  efficiency/reliability
- **Non-duplicate**: Does not replicate functionality compound-gpid already
  has
- **Proportional effort**: Implementation cost is justified by the
  improvement delivered

### Concept Mapping

These repos use different terminology for similar concepts:

| compound-gpid | CE Plugin | Superpowers | GSD-2 |
|---------------|-----------|-------------|-------|
| Prompts (`.github/prompts/`) | Slash commands (`.claude/commands/`) | Skills (auto-triggered) | Commands (`/gsd`, `/gsd auto`) |
| Agents (`.github/agents/`) | Agents (`.agents/`) | Agents (`agents/`) | Extensions (`src/resources/extensions/`) |
| Skills (`.github/skills/`) | Skills (plugin skills) | Skills (`skills/`) | Skills (within extensions) |
| Instructions (`.github/instructions/`) | — | Hooks (`hooks/`) | AGENTS.md / CLAUDE.md |
| `.cg-docs/` (knowledge) | `.ce-docs/` | Design docs | `.gsd/` (state files) |
| `roadmap.json` | — | — | `M001-ROADMAP.md` (per-milestone) |

### Guardrails

- The `/cg-review-repos` prompt must verify it is running inside the
  compound-gpid development repo (by checking for `compound-gpid.md` with
  `project-name: "Compound GPID"`). If run in a consumer project, display:
  > "This prompt is for compound-gpid development only. It reviews external
  > repos for feature ideas. It does not apply to consumer projects."
- Review output must clearly separate "directly applicable" from "needs
  adaptation" from "not applicable (requires runtime we don't have)"

### Technical Constraints

- **No automation**: GitHub Copilot has no cron/hook mechanism. Reviews are
  always user-initiated.
- **Web fetching limits**: `fetch_webpage` has content size limits. For repos
  with large changelogs (GSD-2: 113 releases), the recurring review must
  fetch the **releases page filtered to recent tags**, not the full changelog.
  The prompt should fetch `https://github.com/<owner>/<repo>/releases` and
  scope to releases after the last-reviewed tag.
- **Release-based tracking**: Recurring reviews track by release tag (not
  commits). The initial assessment reviews the full repo; subsequent reviews
  only cover new releases since the last-reviewed tag.

## Approaches Considered

### Approach 1: Registry File + Review Prompt (CHOSEN)

**Summary**: A tracked-repos registry (`repos.json` in
`.cg-docs/competitive-reviews/`), per-repo assessment files with feature
cards, and a `/cg-review-repos` prompt for recurring delta reviews.

**Components**:

1. **Registry** — `.cg-docs/competitive-reviews/repos.json`:
   ```json
   {
     "repos": [
       {
         "id": "compound-engineering",
         "url": "https://github.com/EveryInc/compound-engineering-plugin",
         "shortName": "CE",
         "lastReviewedRelease": "v2.68.1",
         "lastReviewDate": "2026-04-21"
       }
     ]
   }
   ```

2. **Initial assessments** — One file per repo:
   `.cg-docs/competitive-reviews/YYYY-MM-DD-<repo-short-name>-assessment.md`
   with full feature inventory, concept mapping, compatibility verdicts, and
   implementation sketches.

3. **Feature card format** (within assessment files):
   ```markdown
   ### Feature: <name>
   - **Source**: <repo> — <link to relevant file/doc>
   - **What it does**: <1–2 sentence description>
   - **How source implements it**: <brief technical description>
   - **Compatibility**: Directly applicable / Needs adaptation / Not applicable
   - **How we'd adapt it**: <implementation sketch for compound-gpid>
   - **Maps to**: <prompt|agent|skill|instruction|script>
   - **Effort**: Small / Medium / Large
   - **Priority**: High / Medium / Low
   - **Notes**: <edge cases, dependencies, related features>
   ```

4. **Recurring review prompt** — `/cg-review-repos`:
   - Reads `repos.json` for repo list and last-reviewed releases
   - Fetches each repo's releases page
   - Identifies new releases since last review
   - For each new release, analyzes release notes and produces feature cards
   - Updates `repos.json` with new last-reviewed release
   - Saves delta report to
     `.cg-docs/competitive-reviews/YYYY-MM-DD-delta-review.md`

**Pros**: Clean separation of state and analysis. Extensible. Release-based
tracking avoids re-reviewing old content. Feature cards are directly usable
by `/cg-brainstorm`.

**Cons**: Manual invocation required. Web fetching may miss details from very
long release notes.

**Effort**: Medium (2–3 days for initial assessment + prompt + registry +
tests)

### Approach 2: Single Living Document

**Summary**: One large markdown file tracking all features and review history.

**Pros**: Everything in one place.

**Cons**: Grows unbounded. Mixes state and analysis. Hard to feed individual
features into `/cg-brainstorm`. No structured registry for programmatic use.

**Effort**: Small (1–2 days)

### Approach 3: Roadmap-Integrated Review

**Summary**: Review prompt writes directly to `roadmap.json`.

**Pros**: Zero duplication — features go straight to planning pipeline.

**Cons**: Pollutes roadmap with unvetted ideas. Loses curation step.
No structured comparison across repos.

**Effort**: Medium (2–3 days)

## Decision

**Approach 1: Registry File + Review Prompt** selected.

**Key reasons**:
- Clean separation of state (registry) and analysis (markdown)
- Release-based tracking is efficient for recurring reviews
- Feature cards contain enough context for downstream `/cg-brainstorm`
  sessions to skip re-discovery
- Extensible — add repos by editing `repos.json`
- Guardrails prevent misuse in consumer projects

**Devil's advocate resolutions**:
- The prompt earns its keep over manual scanning by producing
  *implementation-ready feature cards* with concept mapping and adaptation
  sketches — not just awareness of what's new
- For GSD-2's large release history, the prompt must fetch the releases page
  (not the full changelog) and scope to recent tags. This should be validated
  during implementation.
- The initial deep assessment is the primary value; the recurring prompt keeps
  the investment current

## Next Steps

### Phase 1: Infrastructure (Day 1)

1. Create `.cg-docs/competitive-reviews/repos.json` with the three repos
2. Create the `/cg-review-repos` prompt with:
   - Dev-repo guardrail (checks `compound-gpid.md` project-name)
   - Two modes: `--full` (initial assessment) and default (delta review)
   - Feature card template
   - Registry update logic
3. Add tests for the prompt (frontmatter, guardrail, required sections)

### Phase 2: Initial Assessment (Days 1–2)

4. Run `/cg-review-repos --full` for each of the three repos
5. Produce per-repo assessment files with full feature inventories
6. Update `repos.json` with current release tags

### Phase 3: Validation (Day 3)

7. Run a delta review to validate the recurring mechanism works
8. Review feature cards for completeness — ensure they have enough context
   for a future `/cg-brainstorm` session to proceed without extensive
   re-discovery
9. Register relevant roadmap items via `@cg-roadmap`

### Separate Task: Prompt Enhancement

10. Modify `/cg-brainstorm` to offer creating a new git branch before
    drafting the brainstorm document (Step 3.75)
