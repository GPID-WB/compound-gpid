---
date: 2026-04-29
title: "Onboarding & Setup milestone expansion"
trigger: "post-milestone"
outcome: "roadmap-updated"
---

# Strategy Session: Onboarding & Setup Milestone Expansion

## Context at Session Start

Performance milestone completed (6/6 done). Quality Loop (12/12) and Context Layer (5/5) also done. Skills Enhancement paused at 1/6 (planned status) per yesterday's strategy session. Onboarding & Setup had 3 idea-stage features and status `planned`. Current Focus in charter still referenced Performance and Skills Enhancement.

## Discussion Summary

User confirmed post-milestone trigger. Skills Enhancement stays paused — R dialect architecture is done and remaining features aren't urgent. Focus shifts fully to Onboarding & Setup.

Reviewed the existing 3 features (project scanner, smart setup, skip questions) and discussed 9 potential additions. User approved 6 of them, creating a comprehensive first-run experience:

1. **First-run welcome and health check after cg-link** — print actionable next-step guidance after linking.
2. **Migration path from vanilla Copilot** — detect existing `.github/copilot-instructions.md` or `.github/instructions/`, offer merge/replace/keep-alongside options.
3. **Charter quality gate** — validate no leftover `<!-- TODO -->` markers, all required fields populated, `last-reviewed` is a real date.
4. **Roadmap bootstrap from charter** — seed `roadmap.json` with an initial milestone derived from Current Focus and Key Deliverables.
5. **/cg-setup --refresh mode** — non-destructive re-configuration for existing projects to pick up new config keys.
6. **Onboarding tour prompt /cg-tour** — guided 2-minute walkthrough of the workflow loop with project-specific next-action suggestions.

Declined additions: team onboarding doc generator (future milestone), interactive language wizard (redundant), visual setup UI (too costly).

## Proposed Changes

1. Add 6 new features to Onboarding & Setup milestone
2. Change Onboarding & Setup status: `planned` → `in-progress`
3. Change Skills Enhancement status: `in-progress` → `planned` (paused)
4. Update charter Current Focus to reflect expanded onboarding scope
5. Archive previous Current Focus to charter-history.md

## Decision

All 5 changes approved and applied.

## Charter Updates

- `Current Focus` updated to: "Onboarding & Setup — making the first interaction with compound-gpid intelligent by scanning existing projects, drafting a charter from scanner results, validating charter quality, bootstrapping the roadmap, and guiding new users through the workflow with a tour prompt."
- `last-reviewed` updated to `2026-04-29`
- Previous focus archived to `.cg-docs/archive/charter-history.md`
