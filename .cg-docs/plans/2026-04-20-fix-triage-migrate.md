---
date: 2026-04-20
title: "/cg-fix-triage --migrate mode"
status: completed
brainstorm: null
language: "powershell"
estimated-effort: "small"
tags: [workflow, fix-triage, prompts, skills]
---

# Plan: `/cg-fix-triage --migrate` Mode

## Objective

Add `--migrate` mode to `/cg-fix-triage` that backfills `findings:` tracking
frontmatter on legacy review files that predate the findings-status feature.
The implementation delegates to a companion skill (`cg-skill-fix-triage-migrate`)
to keep the main prompt clean and focused.

## Context

This feature was a byproduct of the 2026-04-20 prompt-prose-compression
work. The full implementation lives in
`.github/skills/cg-skill-fix-triage-migrate/SKILL.md`.

## Implementation

- Add `--migrate` guard at top of Step 0.5 in `cg-fix-triage.prompt.md`
- Add `--migrate` delegation block at bottom of `cg-fix-triage.prompt.md`
- Create `cg-skill-fix-triage-migrate/SKILL.md` with companion-plan heuristic
