---
date: 2026-04-06
title: "Full backlog structuring into five milestones"
trigger: "mid-project"
outcome: "roadmap-updated"
---

# Strategy Session: Full Backlog Structuring

## Context at Session Start

- Project charter and roadmap.json already in place.
- Roadmap had 1 milestone (Quality Loop) with 6 idea-stage features.
- Most recent plans completed; one active plan (fix-triage-prompt).
- Current Focus in charter was unset (TODO placeholder).

## Discussion Summary

The user arrived with a fully articulated five-milestone structure covering
the plugin's entire near-term backlog. Each milestone had a clear objective
and enumerated features. The session was about encoding an existing vision,
not discovering one.

## Proposed Changes

Five milestones, all `planned`, all features `idea`:

**Milestone 1 — Quality Loop** (existing, enriched)
- @cg-fix-problems agent (auto-dispatched by /cg-work)
- /cg-fix-problems user-facing prompt
- Testing skill for R (testthat/mockery)
- Testing skill for Python (pytest/parametrize/monkeypatch)
- Testing skill for Stata (assert-based/reprun)
- Per-step test enforcement in /cg-work

**Milestone 2 — Performance** (new)
- Full model audit across prompts and agents
- /cg-release scan scope limited to last 60 days
- Split /cg-release into Haiku scan + Sonnet drafting

**Milestone 3 — Skills Enhancement** (new)
- collapse syntax expansion in cg-skill-r-technical
- data.table expansion in cg-skill-r-technical
- tidymodels addition to cg-skill-r-analytical

**Milestone 4 — Architecture Research** (new)
- Study OpenAI Codex plugin for Claude Code
- Evaluate GitHub Copilot hooks for compound-gpid
- copilot-instructions.md restructuring (blocked on hooks evaluation)

**Milestone 5 — Evals** (new)
- roadmap.json schema validation after @cg-roadmap writes
- Required frontmatter field checks from /cg-plan output
- status:completed verification from /cg-work output
- .cg-docs/evals/ scaffold with probe-and-check pairs

**Sequencing constraints:**
- M5 (Evals) gated on M1 (Quality Loop) — do not activate until M1 is done.
- M4 (Architecture Research) must complete before copilot-instructions.md feature starts.
- M1, M2, M3 can proceed in parallel.

## Decision

All five milestones approved and written to roadmap.json. Feature titles on
Quality Loop enriched with implementation detail. Total: 5 milestones,
19 features.

## Charter Updates

- **Current Focus** updated to: "Structuring the full plugin backlog across
  five milestones — Quality Loop, Performance, Skills Enhancement,
  Architecture Research, and Evals. Immediate priority: Quality Loop
  (auto-fix diagnostics, test enforcement, testing skills)."
- **last-reviewed** updated to 2026-04-06.
