# Fix All Review Findings — roadmap feature branch

## Context

I am on the `roadmap` branch of the `compound-gpid` project (PowerShell tool).
I implemented the roadmap feature (plan: `.cg-docs/plans/2026-03-26-roadmap-json-and-agent.md`)
but the review session was cut off before all fixes were applied. The changes have NOT
been committed yet.

## What was implemented

The following files were created or modified as part of the roadmap feature:

**New files:**
- `.github/agents/cg-roadmap.agent.md` — new `@cg-roadmap` agent
- `tests/roadmap.Tests.ps1` — Pester tests for schema validation and milestone status logic

**Modified files:**
- `.cg-docs/plans/2026-03-26-roadmap-json-and-agent.md` — plan updated
- `.github/prompts/cg-brainstorm.prompt.md` — added Roadmap Registration section
- `.github/prompts/cg-plan.prompt.md` — added Step 5: Register in Roadmap (renumbered old Step 5 to Step 6)
- `.github/prompts/cg-resume.prompt.md` — added milestone progress section (Step 2d) and roadmap display template
- `.github/prompts/cg-setup.prompt.md` — added roadmap.json scaffolding in Modes A and B
- `.github/prompts/cg-work.prompt.md` — added roadmap.json read permission and Step 5: Update Roadmap Status
- `docs/reference.md` — documented @cg-roadmap agent
- `docs/workflow.md` — documented roadmap workflow

## Your task

Please do the following:

1. Run a standard `/cg-review` on ALL the files listed above (the 10 changed/new files).
2. Fix **all** findings — P1 (critical) first, then P2 (important), then P3 (minor).
3. Run `Invoke-Pester tests/roadmap.Tests.ps1` to confirm tests pass after fixes.
4. Summarize what was fixed.

Do not ask for confirmation on individual findings — fix everything.
